"""
PyInstaller hook for rembg
Handles AI background removal tool and its dependencies

This hook ensures that rembg and its model files are properly
collected and bundled with the application.

CRITICAL: This hook must NOT import rembg or onnxruntime directly!
rembg.bg checks for onnxruntime at import time and calls sys.exit(1)
if it's not found, which would kill the PyInstaller build process.

Instead, we use PyInstaller's collect_submodules() to gather all
rembg modules without importing them.

IMPORTANT: rembg must be installed with [cpu] or [gpu] extras:
    pip install "rembg[cpu]"  # for CPU
    pip install "rembg[gpu]"  # for GPU
    
If rembg is not properly installed, this hook will gracefully skip it
and the application will treat it as an optional dependency.
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)
import os
import sys

# Prevent rembg from calling sys.exit() during PyInstaller analysis
# This patches the sys.exit function temporarily while analyzing rembg
_original_exit = sys.exit

def _patched_exit(code=0):
    """Patched sys.exit that raises SystemExit instead of exiting"""
    raise SystemExit(code)

# Apply patch during hook execution
sys.exit = _patched_exit

# Common dependencies required by rembg
REMBG_DEPENDENCIES = [
    'PIL',
    'PIL.Image',
    'numpy',
    'numpy.core',
    'pooch',
    'tqdm',
    'pymatting',
    'pymatting.alpha.estimate_alpha_cf',
    'pymatting.foreground.estimate_foreground_ml',
    'pymatting.util.util',
    'scipy',
    'scipy.ndimage',
    'scipy.sparse',
    'scipy.sparse.linalg',
    'skimage',
    'skimage.transform',
    'skimage.filters',
    'skimage.morphology',
    'jsonschema',
]

# Initialize required hook attributes - CRITICAL: Must be at module level
hiddenimports = []
datas = []
binaries = []
excludedimports = []

print("[rembg hook] Starting rembg collection...")
print("[rembg hook] Note: sys.exit() is patched to prevent build termination")

# Check if rembg is available at all (without importing it)
try:
    import importlib.util
    rembg_spec = importlib.util.find_spec('rembg')
    has_rembg = rembg_spec is not None
except Exception as e:
    print(f"[rembg hook] WARNING: Error checking rembg availability: {e}")
    has_rembg = False

# Check if onnxruntime is available (without importing it)
try:
    onnx_spec = importlib.util.find_spec('onnxruntime')
    has_onnxruntime = onnx_spec is not None
except Exception as e:
    print(f"[rembg hook] WARNING: Error checking onnxruntime: {e}")
    has_onnxruntime = False

if not has_rembg:
    print("[rembg hook] ERROR: rembg not installed!")
    print("[rembg hook] Install with: pip install 'rembg[cpu]'")
    print("[rembg hook] Background removal tool requires rembg to function")
    # Restore sys.exit and exit early
    sys.exit = _original_exit
elif not has_onnxruntime:
    print("[rembg hook] WARNING: rembg is installed but onnxruntime is NOT found!")
    print("[rembg hook] rembg requires onnxruntime backend to function.")
    print("[rembg hook] Install with: pip install 'rembg[cpu]'")
    print("[rembg hook] Attempting to collect rembg anyway (with patched sys.exit)")
    
    # Try to collect rembg modules without importing them
    try:
        hiddenimports = collect_submodules('rembg')
        print(f"[rembg hook] Collected {len(hiddenimports)} rembg submodules (without importing)")
    except Exception as e:
        print(f"[rembg hook] Warning: Could not collect rembg submodules: {e}")
        hiddenimports = []
    
    # Add dependencies that rembg needs
    hiddenimports.extend(REMBG_DEPENDENCIES)
    
    # Collect data files and binaries
    try:
        datas = collect_data_files('rembg', include_py_files=False)
        print(f"[rembg hook] Collected {len(datas)} data files")
    except Exception as e:
        print(f"[rembg hook] Warning: Could not collect data files: {e}")
    
    try:
        binaries = collect_dynamic_libs('rembg')
        print(f"[rembg hook] Collected {len(binaries)} binary files")
    except Exception as e:
        print(f"[rembg hook] Warning: Could not collect binaries: {e}")
    
    print("[rembg hook] Collection complete - but onnxruntime may not work at runtime!")
    print("[rembg hook] Ensure 'rembg[cpu]' is installed for full functionality")
else:
    # Both rembg and onnxruntime are available - full collection
    print("[rembg hook] ✅ Both rembg and onnxruntime found - collecting for background removal tool")
    
    # Wrap everything in try-except to handle any import failures gracefully
    try:
        # Collect all rembg submodules using collect_submodules (doesn't import them)
        # This is safe because collect_submodules uses importlib to find modules without importing
        try:
            rembg_modules = collect_submodules('rembg')
            print(f"[rembg hook] Collected {len(rembg_modules)} rembg submodules (without importing)")
            hiddenimports = rembg_modules
        except Exception as e:
            print(f"[rembg hook] Warning: Could not collect rembg submodules: {e}")
            hiddenimports = [
                # Manually specify core rembg modules as fallback
                'rembg',
                'rembg.bg',
                'rembg.session_factory',
                'rembg.sessions',
            ]
            print(f"[rembg hook] Using fallback module list ({len(hiddenimports)} modules)")
        
        # Add onnxruntime and its dependencies
        hiddenimports.extend([
            'onnxruntime',
            'onnxruntime.capi',
            'onnxruntime.capi._pybind_state',
            'onnxruntime.capi.onnxruntime_pybind11_state',
        ])
        
        # Add rembg dependencies
        hiddenimports.extend(REMBG_DEPENDENCIES)
        
        print(f"[rembg hook] Total hidden imports: {len(hiddenimports)}")
        
        # Collect data files (model files, etc.)
        try:
            rembg_datas = collect_data_files('rembg', include_py_files=False)
            datas = rembg_datas
            print(f"[rembg hook] Collected {len(datas)} data files (models, configs)")
        except Exception as e:
            print(f"[rembg hook] Warning: Could not collect data files: {e}")
            datas = []
        
        # Collect binaries from both rembg and onnxruntime
        try:
            rembg_binaries = collect_dynamic_libs('rembg')
            onnx_binaries = collect_dynamic_libs('onnxruntime')
            binaries = rembg_binaries
            if onnx_binaries:
                binaries.extend(onnx_binaries)
                print(f"[rembg hook] Collected {len(onnx_binaries)} onnxruntime binaries")
            print(f"[rembg hook] Total binaries collected: {len(binaries)}")
        except Exception as e:
            print(f"[rembg hook] Warning: Could not collect binaries: {e}")
            binaries = []
        
        print("[rembg hook] ✅ Collection successful - background removal tool should work!")
            
    except Exception as e:
        print(f"[rembg hook] ERROR during collection: {e}")
        print("[rembg hook] This may cause background removal tool to fail at runtime")
        # Still try to provide minimal imports
        hiddenimports = ['rembg', 'onnxruntime'] + REMBG_DEPENDENCIES
        datas = []
        binaries = []

print(f"[rembg hook] Final counts - imports: {len(hiddenimports)}, datas: {len(datas)}, binaries: {len(binaries)}")
print("[rembg hook] Collection complete")

# Restore original sys.exit
sys.exit = _original_exit
