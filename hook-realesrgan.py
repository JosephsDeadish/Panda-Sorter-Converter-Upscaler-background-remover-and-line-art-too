"""
PyInstaller hook for realesrgan (Real-ESRGAN super-resolution models).

realesrgan depends on basicsr and torchvision.  This hook collects all
realesrgan submodules so that the frozen exe can perform upscaling without
requiring the user to install realesrgan separately.

Model weights (.pth files) are NOT bundled here — they are downloaded at
runtime via the AI Model Manager the first time the user requests Real-ESRGAN
upscaling (to keep the EXE size reasonable).
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all Python submodules
hiddenimports = collect_submodules('realesrgan')

# Collect non-Python data files
datas = collect_data_files('realesrgan')
