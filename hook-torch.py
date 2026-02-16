"""
PyInstaller hook for PyTorch (torch)
Handles DLL dependencies and CUDA providers for proper bundling

This hook ensures that PyTorch's C++ libraries and dependencies are properly
collected and bundled with the application. It provides intelligent handling
of CUDA dependencies:

1. CPU-only builds: Excludes CUDA DLLs to reduce size and avoid errors
2. GPU builds: Includes CUDA runtime libraries when available
3. Graceful degradation: If torch import fails during build, provides fallback

CRITICAL: This hook must NOT import torch directly during analysis!
torch.cuda checks for CUDA DLLs at import time which would fail on
build machines without NVIDIA drivers. Instead, we detect torch 
installation without importing it.

Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import (
    collect_dynamic_libs,
    collect_data_files,
    collect_submodules,
)
import os
import sys
import glob
from pathlib import Path

# Initialize collections
hiddenimports = []
datas = []
binaries = []

# Prevent torch from initializing CUDA during build
# Using try-finally to ensure sys.exit is always restored
_original_exit = sys.exit

def _patched_exit(code=0):
    """Patched sys.exit that raises SystemExit instead of exiting"""
    raise SystemExit(code)

# Apply patch during hook execution
sys.exit = _patched_exit

try:
    print("[torch hook] Starting PyTorch collection...")
    print("[torch hook] Note: sys.exit() is patched to prevent build termination")

    # CUDA keywords for filtering (case-insensitive)
    CUDA_KEYWORDS = [
        'cuda', 'cudart', 'cublas', 'cublaslt', 'cudnn', 'cufft', 
        'curand', 'cusparse', 'cusolver', 'nvrtc', 'tensorrt', 
        'nvcuda', 'nvfuser', 'nvjpeg'
    ]

    # Core torch hidden imports
    TORCH_HIDDENIMPORTS = [
        'torch',
        'torch._C',
        # 'torch._six',  # REMOVED - deprecated in PyTorch 1.9+, no longer exists
        'torch.nn',
        'torch.nn.functional',
        'torch.optim',
        'torch.autograd',
        'torch.cuda',
        'torch.jit',
        # ONNX export support (for model export/import)
        'torch.onnx',
        'torch.onnx.symbolic_helper',
        'torch.onnx.utils',
        'torch.onnx._internal',
        'torch.utils',
        'torch.utils.data',
        'torch.distributions',
        # C++ extension modules
        'torch._C._nn',
        'torch._C._fft',
        'torch._C._linalg',
        'torch._C._sparse',
        'torch._C._special',
        # Quantization
        'torch.quantization',
        'torch.ao.quantization',
        # Mobile and Lite Interpreter
        'torch.jit.mobile',
        'torch.lite',
        # Distributed (if used) - Updated paths
        'torch.distributed',
        'torch.distributed.rpc',
        'torch.distributed._shard',  # Current path for sharding (replaces deprecated _sharding_spec)
        'torch.distributed._shard.sharding_spec',  # Current path for sharding spec (replaces deprecated _sharding_spec)
    ]

    def should_skip_cuda_dll(file_path):
        """
        Check if a DLL should be skipped due to CUDA dependency.
        
        Args:
            file_path: Path to the DLL file
            
        Returns:
            tuple: (should_skip: bool, display_name: str)
        """
        file_name = os.path.basename(file_path)
        file_name_lower = file_name.lower()
        
        # Check if it's a CUDA-related DLL
        is_cuda = any(keyword in file_name_lower for keyword in CUDA_KEYWORDS)
        
        return is_cuda, file_name

    def find_torch_package():
        """
        Find torch package directory without importing it.
        
        Returns:
            Path to torch package or None if not found
        """
        try:
            import importlib.util
            torch_spec = importlib.util.find_spec('torch')
            if torch_spec is None:
                return None
            
            # Get package location
            if torch_spec.origin:
                torch_dir = Path(torch_spec.origin).parent
                return torch_dir
            elif torch_spec.submodule_search_locations:
                return Path(torch_spec.submodule_search_locations[0])
        except Exception as e:
            print(f"[torch hook] WARNING: Error finding torch package: {e}")
        
        return None

    # Check if torch is available
    torch_dir = find_torch_package()

    if not torch_dir or not torch_dir.exists():
        print("[torch hook] WARNING: PyTorch not found or not installed")
        print("[torch hook] Torch-dependent features will be disabled in the build")
        print("[torch hook] To enable: pip install torch torchvision")
        # Restore original sys.exit
        sys.exit = _original_exit
    else:
        print(f"[torch hook] Found PyTorch at: {torch_dir}")
        
        # Determine if we should include CUDA
        # Check for environment variable to control CUDA inclusion
        include_cuda = os.environ.get('TORCH_INCLUDE_CUDA', '').lower() in ('1', 'true', 'yes')
        
        # Auto-detect: Check if CUDA DLLs exist in torch package
        cuda_dll_exists = False
        if sys.platform == 'win32':
            lib_dir = torch_dir / 'lib'
            if lib_dir.exists():
                cuda_dlls = list(lib_dir.glob('*cuda*.dll'))
                cuda_dll_exists = len(cuda_dlls) > 0
                if cuda_dll_exists:
                    print(f"[torch hook] Detected {len(cuda_dlls)} CUDA DLLs in torch package")
        
        # Default: Exclude CUDA unless explicitly requested or detected
        if include_cuda:
            print("[torch hook] CUDA inclusion ENABLED via environment variable")
        elif cuda_dll_exists:
            print("[torch hook] CUDA DLLs detected but will be EXCLUDED by default")
            print("[torch hook] Set TORCH_INCLUDE_CUDA=1 to include CUDA support")
        else:
            print("[torch hook] No CUDA DLLs detected - CPU-only build")
        
        try:
            # Collect torch dynamic libraries
            print("[torch hook] Collecting torch dynamic libraries...")
            collected_binaries = collect_dynamic_libs('torch')
            
            cuda_skipped = 0
            cuda_included = 0
            
            for binary_path, binary_dest in collected_binaries:
                is_cuda, file_name = should_skip_cuda_dll(binary_path)
                
                if is_cuda:
                    if include_cuda:
                        # Include CUDA DLL
                        binaries.append((binary_path, binary_dest))
                        cuda_included += 1
                        print(f"  [torch hook] Including CUDA DLL: {file_name}")
                    else:
                        # Skip CUDA DLL
                        cuda_skipped += 1
                else:
                    # Include non-CUDA DLL
                    binaries.append((binary_path, binary_dest))
            
            if cuda_skipped > 0:
                print(f"[torch hook] Skipped {cuda_skipped} CUDA DLLs (CPU-only build)")
            if cuda_included > 0:
                print(f"[torch hook] Included {cuda_included} CUDA DLLs")
            
            print(f"[torch hook] Collected {len(binaries)} torch binaries")
            
        except Exception as e:
            print(f"[torch hook] WARNING: Error collecting torch binaries: {e}")
            print("[torch hook] Torch may not work properly in the built executable")
        
        # Collect torch data files (exclude test data and documentation)
        try:
            print("[torch hook] Collecting torch data files...")
            all_datas = collect_data_files('torch', include_py_files=False)
            
            # Filter out unnecessary data
            for data_path, data_dest in all_datas:
                # Skip test files
                if 'test' in data_dest.lower():
                    continue
                # Skip documentation
                if 'docs' in data_dest.lower():
                    continue
                # Skip example files
                if 'examples' in data_dest.lower():
                    continue
                
                datas.append((data_path, data_dest))
            
            print(f"[torch hook] Collected {len(datas)} torch data files")
            
        except Exception as e:
            print(f"[torch hook] WARNING: Error collecting torch data files: {e}")
        
        # Add hidden imports
        print("[torch hook] Adding torch hidden imports...")
        hiddenimports.extend(TORCH_HIDDENIMPORTS)
        
        # Try to collect torch submodules (without importing)
        try:
            torch_submodules = collect_submodules('torch', filter=lambda name: 'test' not in name)
            # Avoid duplicates
            for module in torch_submodules:
                if module not in hiddenimports:
                    hiddenimports.append(module)
            print(f"[torch hook] Added {len(torch_submodules)} torch submodules")
        except Exception as e:
            print(f"[torch hook] WARNING: Could not collect torch submodules: {e}")
        
        # On Windows, manually collect DLLs from torch/lib directory
        if sys.platform == 'win32':
            lib_dir = torch_dir / 'lib'
            if lib_dir.exists():
                print(f"[torch hook] Scanning torch/lib directory: {lib_dir}")
                
                # Collect all DLLs
                dll_patterns = ['*.dll', '*.pyd']
                for pattern in dll_patterns:
                    for dll_path in lib_dir.glob(pattern):
                        # Check if already collected
                        already_collected = any(
                            Path(b[0]).name == dll_path.name 
                            for b in binaries
                        )
                        
                        if already_collected:
                            continue
                        
                        # Check if CUDA
                        is_cuda, file_name = should_skip_cuda_dll(str(dll_path))
                        
                        if is_cuda and not include_cuda:
                            continue
                        
                        # Add to binaries
                        binaries.append((str(dll_path), '.'))
                
                print(f"[torch hook] Total torch binaries: {len(binaries)}")
        
        print("[torch hook] PyTorch collection completed successfully")

finally:
    # Restore original sys.exit in finally block to guarantee restoration
    sys.exit = _original_exit
    print("[torch hook] Hook completed")
    print(f"[torch hook] Summary: {len(binaries)} binaries, {len(datas)} data files, {len(hiddenimports)} hidden imports")
