"""
PyInstaller hook for onnxruntime
Handles DLL dependencies that fail to load on Windows

This hook ensures that onnxruntime's DLL dependencies are properly
collected and bundled with the application.

Note: This hook avoids importing onnxruntime during analysis to prevent
DLL initialization issues on the build machine.
"""

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files
import os
import sys
import glob

# Initialize collections
binaries = []
datas = []

# Hidden imports needed by onnxruntime
hiddenimports = [
    'onnxruntime.capi',
    'onnxruntime.capi._pybind_state',
    'onnxruntime.capi.onnxruntime_pybind11_state',
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
]

try:
    # Try to collect binaries without importing onnxruntime
    binaries = collect_dynamic_libs('onnxruntime')
    
    # Also collect data files if any
    datas = collect_data_files('onnxruntime', include_py_files=False)
    
    # On Windows, manually collect DLLs from the package directory
    if sys.platform == 'win32':
        try:
            # Find onnxruntime package directory without importing it
            import site
            import sysconfig
            
            # Check all possible package locations
            search_paths = []
            search_paths.extend(site.getsitepackages())
            search_paths.append(sysconfig.get_path('purelib'))
            search_paths.append(sysconfig.get_path('platlib'))
            
            for search_path in search_paths:
                onnx_path = os.path.join(search_path, 'onnxruntime')
                if os.path.exists(onnx_path):
                    capi_path = os.path.join(onnx_path, 'capi')
                    
                    # Collect all DLLs and PYD files from capi directory
                    if os.path.exists(capi_path):
                        for pattern in ['*.dll', '*.pyd']:
                            for file_path in glob.glob(os.path.join(capi_path, pattern)):
                                file_name = os.path.basename(file_path)
                                # Add to binaries with destination in onnxruntime/capi
                                binaries.append((file_path, 'onnxruntime/capi'))
                                print(f"  [onnxruntime hook] Collecting: {file_name}")
                    
                    # Also collect DLLs from main onnxruntime directory
                    for pattern in ['*.dll']:
                        for file_path in glob.glob(os.path.join(onnx_path, pattern)):
                            file_name = os.path.basename(file_path)
                            binaries.append((file_path, 'onnxruntime'))
                            print(f"  [onnxruntime hook] Collecting: {file_name}")
                    
                    break  # Found the package, no need to check other paths
                    
        except Exception as e:
            print(f"  [onnxruntime hook] Warning: Could not collect Windows DLLs: {e}")
    
    print(f"[onnxruntime hook] Collected {len(binaries)} binary files")
    print(f"[onnxruntime hook] Collected {len(datas)} data files")
    
except Exception as e:
    # If onnxruntime is not available, that's OK
    # The application will handle it as an optional dependency
    print(f"[onnxruntime hook] Warning: onnxruntime not fully available during build: {e}")
    print(f"[onnxruntime hook] Application will handle onnxruntime as optional dependency")
