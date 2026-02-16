"""
PyInstaller hook for onnxruntime
Handles DLL dependencies and excludes CUDA providers

This hook ensures that onnxruntime's CPU DLL dependencies are properly
collected and bundled with the application, while excluding CUDA/GPU
providers to prevent nvcuda.dll loading errors.

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
    collected_binaries = collect_dynamic_libs('onnxruntime')
    
    # Filter out CUDA and GPU-related DLLs to prevent nvcuda.dll errors
    cuda_keywords = [
        'cuda', 'cudart', 'cublas', 'cudnn', 'cufft', 'curand',
        'cusparse', 'cusolver', 'nvrtc', 'tensorrt', 'nvcuda',
        'onnxruntime_providers_cuda', 'onnxruntime_providers_tensorrt'
    ]
    
    for binary_path, binary_dest in collected_binaries:
        file_name = os.path.basename(binary_path).lower()
        # Skip if it's a CUDA-related DLL
        if not any(keyword in file_name for keyword in cuda_keywords):
            binaries.append((binary_path, binary_dest))
        else:
            print(f"  [onnxruntime hook] Skipping CUDA DLL: {os.path.basename(binary_path)}")
    
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
                                file_name = os.path.basename(file_path).lower()
                                # Skip CUDA-related DLLs
                                if any(keyword in file_name for keyword in cuda_keywords):
                                    print(f"  [onnxruntime hook] Skipping CUDA DLL: {os.path.basename(file_path)}")
                                    continue
                                # Add to binaries with destination in onnxruntime/capi
                                binaries.append((file_path, 'onnxruntime/capi'))
                                print(f"  [onnxruntime hook] Collecting: {os.path.basename(file_path)}")
                    
                    # Also collect DLLs from main onnxruntime directory
                    for pattern in ['*.dll']:
                        for file_path in glob.glob(os.path.join(onnx_path, pattern)):
                            file_name = os.path.basename(file_path).lower()
                            # Skip CUDA-related DLLs
                            if any(keyword in file_name for keyword in cuda_keywords):
                                print(f"  [onnxruntime hook] Skipping CUDA DLL: {os.path.basename(file_path)}")
                                continue
                            binaries.append((file_path, 'onnxruntime'))
                            print(f"  [onnxruntime hook] Collecting: {os.path.basename(file_path)}")
                    
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
