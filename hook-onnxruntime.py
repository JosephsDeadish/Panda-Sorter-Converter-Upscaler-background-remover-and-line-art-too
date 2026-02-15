"""
PyInstaller hook for onnxruntime
Handles DLL dependencies that fail to load on Windows

This hook ensures that onnxruntime's DLL dependencies are properly
collected and bundled with the application.
"""

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files
import os
import sys

# Collect all DLL files from onnxruntime package
binaries = collect_dynamic_libs('onnxruntime')

# Also collect data files (models, etc.) if any
datas = collect_data_files('onnxruntime', include_py_files=False)

# On Windows, ensure onnxruntime.capi directory is included
if sys.platform == 'win32':
    try:
        import onnxruntime
        onnx_path = os.path.dirname(onnxruntime.__file__)
        capi_path = os.path.join(onnx_path, 'capi')
        
        # Collect all DLLs from capi directory
        if os.path.exists(capi_path):
            for file in os.listdir(capi_path):
                if file.endswith('.dll') or file.endswith('.pyd'):
                    src = os.path.join(capi_path, file)
                    # Add to binaries with destination in onnxruntime/capi
                    binaries.append((src, 'onnxruntime/capi'))
                    print(f"  [onnxruntime hook] Collecting: {file}")
    except ImportError:
        # onnxruntime not installed, skip
        pass

# Hidden imports needed by onnxruntime
hiddenimports = [
    'onnxruntime.capi',
    'onnxruntime.capi._pybind_state',
    'onnxruntime.capi.onnxruntime_pybind11_state',
    'numpy',
    'numpy.core',
]

print(f"[onnxruntime hook] Collected {len(binaries)} binary files")
