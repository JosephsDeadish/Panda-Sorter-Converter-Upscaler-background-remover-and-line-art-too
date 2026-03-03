"""
PyInstaller hook for torchvision.

torchvision ships compiled C++ extensions (.pyd on Windows, .so on Linux/macOS)
for image decoding and model inference acceleration.  Listing submodule names in
hiddenimports alone does NOT bundle the binaries — collect_submodules with
include_py_files=True is needed to:

1. Force-include all .py files so that TorchScript inspect.getsource() works at
   runtime (required by basicsr's compat shim).
2. Collect compiled extensions (.pyd/.so) via collect_data_files.

The spec file adds explicit hiddenimports for the most commonly needed submodules
but relies on this hook for full binary coverage.
"""

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
)

# Collect all submodule names (required for lazy imports inside torchvision)
hiddenimports = collect_submodules('torchvision')

# Collect data files (model weights lookups, version metadata, etc.)
datas = collect_data_files('torchvision')
