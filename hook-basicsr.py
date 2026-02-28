"""
PyInstaller hook for basicsr (super-resolution framework).

basicsr ≤ 1.4.2 imports ``torchvision.transforms.functional_tensor`` which was
removed in torchvision 0.16+.  The main application already injects a compat
shim at import time (see src/preprocessing/upscaler.py), but PyInstaller's
static analyser runs before that shim is in place, so we must suppress the
false-missing-module warning here to avoid breaking the build.

This hook also collects all basicsr submodules so that dynamically-loaded
architecture modules (basicsr.archs.*) are present in the frozen exe.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all Python submodules (archs, utils, models, losses, …)
hiddenimports = collect_submodules('basicsr')

# Collect non-Python data files (default configs, model zoo specs)
datas = collect_data_files('basicsr')

# The torchvision.transforms.functional_tensor module was removed in
# torchvision 0.16+.  Suppress the missing-module warning that PyInstaller
# would otherwise emit during Analysis; the runtime compat shim in
# upscaler.py handles this gracefully at runtime.
excludedimports = ['torchvision.transforms.functional_tensor']
