"""
PyInstaller hook for ONNX
Handles ONNX model format library to prevent isolated subprocess crashes

This hook prevents PyInstaller from attempting to import and analyze
problematic ONNX submodules that cause DLL initialization failures during
the build process. ONNX is bundled as data instead of being introspected.

Key issues this hook solves:
1. onnx.reference module causes DLL initialization failure (exit code 3221225477)
2. onnxscript integration causes import issues
3. Prevents isolated subprocess crash during build time

The application will load ONNX at runtime if available, allowing for
graceful degradation if ONNX is not installed.

Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files
import sys

# Initialize collections
hiddenimports = []
datas = []
binaries = []

# Exclude problematic ONNX submodules that cause build-time crashes
excludedimports = [
    'onnx.reference',  # Causes DLL initialization failure in isolated subprocess
    'onnx.reference.ops',
    'onnx.reference.ops._op_list',
    'onnxscript',  # Optional scripting extension that may not be available
    'onnxscript.onnx_opset',
]

print("[onnx hook] Starting ONNX collection...")

try:
    # Try to collect ONNX data files without importing problematic modules
    # This bundles ONNX as data rather than trying to introspect it
    datas = collect_data_files('onnx', include_py_files=False)
    
    # Add core ONNX hidden imports (safe modules only)
    hiddenimports.extend([
        'onnx',
        'onnx.helper',
        'onnx.checker',
        'onnx.shape_inference',
        'onnx.version_converter',
        'google.protobuf',  # Required by ONNX
    ])
    
    print(f"[onnx hook] Collected {len(datas)} ONNX data files")
    print(f"[onnx hook] Added {len(hiddenimports)} hidden imports")
    print(f"[onnx hook] Excluded {len(excludedimports)} problematic modules")
    
except Exception as e:
    # ONNX is optional - if not available, that's OK
    print(f"[onnx hook] ONNX not available during build: {e}")
    print(f"[onnx hook] Application will handle ONNX as optional dependency")

print("[onnx hook] Hook completed")
