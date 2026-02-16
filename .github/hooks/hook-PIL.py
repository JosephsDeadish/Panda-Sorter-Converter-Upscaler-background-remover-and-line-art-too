"""
PyInstaller hook for PIL/Pillow
Ensures PIL (Pillow) image processing library is properly bundled
Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all PIL submodules
hiddenimports = collect_submodules('PIL')

# Explicitly add critical PIL modules
hiddenimports.extend([
    'PIL.Image',
    'PIL.ImageFile',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageFilter',
    'PIL.ImageOps',
    'PIL.ImageEnhance',
    'PIL.ImageChops',
    'PIL.ImageMode',
    'PIL.ImagePalette',
    'PIL.ImageSequence',
    'PIL.ImageTransform',
])

# Collect PIL data files
datas = collect_data_files('PIL')

print(f"[PIL hook] Collected {len(hiddenimports)} PIL modules and {len(datas)} data files")
