"""
PyInstaller hook for rembg
Handles AI background removal tool and its dependencies

This hook ensures that rembg and its model files are properly
collected and bundled with the application.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

# Collect all submodules
hiddenimports = collect_submodules('rembg')

# Add specific imports that might be missed
hiddenimports += [
    'rembg.bg',
    'rembg.session_factory',
    'rembg.sessions',
    'onnxruntime',
    'onnxruntime.capi',
]

# Collect data files (model files, config, etc.)
datas = collect_data_files('rembg', include_py_files=False)

# Collect any DLLs from rembg
binaries = collect_dynamic_libs('rembg')

print(f"[rembg hook] Collected {len(hiddenimports)} hidden imports")
print(f"[rembg hook] Collected {len(datas)} data files")
print(f"[rembg hook] Collected {len(binaries)} binary files")
