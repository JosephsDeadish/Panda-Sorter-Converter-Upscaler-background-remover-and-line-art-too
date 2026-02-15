"""
PyInstaller hook for rembg
Handles AI background removal tool and its dependencies

This hook ensures that rembg and its model files are properly
collected and bundled with the application.

Note: This hook collects metadata without importing rembg to avoid
DLL initialization issues during PyInstaller analysis phase.

IMPORTANT: rembg must be installed with [cpu] or [gpu] extras:
    pip install "rembg[cpu]"  # for CPU
    pip install "rembg[gpu]"  # for GPU
"""

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
import os
import sys

# Initialize collections
hiddenimports = []
datas = []
binaries = []

# Check if onnxruntime is available (required by rembg)
try:
    import onnxruntime
    has_onnxruntime = True
except ImportError:
    has_onnxruntime = False
    print("[rembg hook] WARNING: onnxruntime not found!")
    print("[rembg hook] rembg requires onnxruntime backend.")
    print("[rembg hook] Install with: pip install 'rembg[cpu]'")

# Try to collect rembg data, but don't fail if it's not importable
try:
    # Manually specify hidden imports without importing rembg
    # This avoids the DLL initialization issue during build
    hiddenimports = [
        'rembg',
        'rembg.bg',
        'rembg.session_factory',
        'rembg.sessions',
        'rembg.session_base',
        'rembg.session_simple',
        'rembg.sessions.base',
        'rembg.sessions.u2net',
        'rembg.sessions.u2netp',
        'rembg.sessions.u2net_human_seg',
        'rembg.sessions.u2net_cloth_seg',
        'rembg.sessions.silueta',
        'rembg.sessions.isnet',
        'PIL',
        'PIL.Image',
        'numpy',
        'numpy.core',
        'pooch',
        'tqdm',
    ]
    
    # Only add onnxruntime if it's available
    if has_onnxruntime:
        hiddenimports.extend([
            'onnxruntime',
            'onnxruntime.capi',
            'onnxruntime.capi._pybind_state',
        ])
    
    # Try to collect data files (model files, config, etc.)
    try:
        datas = collect_data_files('rembg', include_py_files=False)
    except Exception as e:
        print(f"[rembg hook] Warning: Could not collect data files: {e}")
        datas = []
    
    # Try to collect DLLs
    try:
        binaries = collect_dynamic_libs('rembg')
    except Exception as e:
        print(f"[rembg hook] Warning: Could not collect binaries: {e}")
        binaries = []
    
    # Try to collect onnxruntime DLLs
    if has_onnxruntime:
        try:
            onnx_binaries = collect_dynamic_libs('onnxruntime')
            if onnx_binaries:
                binaries.extend(onnx_binaries)
        except Exception as e:
            print(f"[rembg hook] Warning: Could not collect onnxruntime binaries: {e}")
    
    print(f"[rembg hook] Collected {len(hiddenimports)} hidden imports")
    print(f"[rembg hook] Collected {len(datas)} data files")
    print(f"[rembg hook] Collected {len(binaries)} binary files")
    
except Exception as e:
    # If rembg is not available or fails to import, that's OK
    # The application will handle the ImportError at runtime
    print(f"[rembg hook] Warning: rembg not fully available during build: {e}")
    print(f"[rembg hook] Application will handle rembg as optional dependency")
    hiddenimports = []
    datas = []
    binaries = []
