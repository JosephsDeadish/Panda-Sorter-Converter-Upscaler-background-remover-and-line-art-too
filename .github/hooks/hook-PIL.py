"""
PyInstaller hook for PIL/Pillow
Ensures PIL (Pillow) image processing library is properly bundled
This hook ensures ALL PIL modules, plugins, and data files are bundled correctly
Author: Dead On The Inside / JosephsDeadish
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys

print("[PIL hook] Starting PIL/Pillow collection...")

# Initialize required hook attributes
datas = []
binaries = []
excludedimports = []

# Collect all PIL submodules
hiddenimports = collect_submodules('PIL')

# Explicitly add critical PIL modules including binary extensions
hiddenimports.extend([
    # Core PIL modules
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
    # Binary modules - CRITICAL for PIL to work
    'PIL._imaging',  # Core C extension module
    'PIL._imagingft',  # FreeType font rendering
    'PIL._imagingmath',  # Math operations
    'PIL._imagingmorph',  # Morphological operations
    'PIL._imagingcms',  # Color management
    # Image format plugins - CRITICAL for image loading
    'PIL.PngImagePlugin',  # PNG support
    'PIL.JpegImagePlugin',  # JPEG support
    'PIL.TiffImagePlugin',  # TIFF support
    'PIL.BmpImagePlugin',  # BMP support
    'PIL.GifImagePlugin',  # GIF support
    'PIL.WebPImagePlugin',  # WebP support
    'PIL.IcoImagePlugin',  # ICO support
    'PIL.PpmImagePlugin',  # PPM support
    'PIL.TgaImagePlugin',  # TGA support
    'PIL.DdsImagePlugin',  # DDS support (game textures)
])

# Collect PIL data files including Python files
# include_py_files=True ensures plugins and encoders are included
datas = collect_data_files('PIL', include_py_files=True)

# Note: We already collect PIL data above with include_py_files=True
# This should be sufficient for PyInstaller to bundle all necessary files.
# If specific files are still missing, they can be added to hiddenimports.

print(f"[PIL hook] Collected {len(hiddenimports)} PIL modules and {len(datas)} data files")
print("[PIL hook] PIL/Pillow collection completed successfully")
