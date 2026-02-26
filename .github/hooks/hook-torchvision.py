"""
PyInstaller hook for torchvision.

torchvision contains C extensions (_C.pyd) and lazily-loaded submodules
that PyInstaller's static analysis misses.  This hook ensures:
1. All torchvision submodules are discovered via collect_submodules().
2. Python source files are included (include_py_files=True) so that
   TorchScript's inspect.getsource() can read torchvision model definitions
   at runtime — the same fix applied to timm and transformers.
3. The torchvision._C native extension and its DLL dependencies are bundled.

Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

print("[torchvision hook] Starting torchvision collection...")

binaries = []
excludedimports = []

# All torchvision submodules (models, transforms, ops, datasets, etc.)
hiddenimports = collect_submodules("torchvision")

# Include .py source files — required for TorchScript inspect.getsource()
datas = collect_data_files("torchvision", include_py_files=True)

# Collect native extension DLLs / .so files (torchvision._C)
try:
    binaries += collect_dynamic_libs("torchvision")
except Exception as _e:
    print(f"[torchvision hook] WARNING: could not collect dynamic libs: {_e}")

print(
    f"[torchvision hook] Collected {len(hiddenimports)} submodules, "
    f"{len(datas)} data entries, {len(binaries)} binaries"
)
