"""
PyInstaller hook for pillow-avif-plugin.

pillow-avif-plugin provides AVIF image encoding/decoding for Pillow by
bundling a pre-built libaom shared library.  The plugin self-registers with
Pillow on import (side-effect import), so PyInstaller must bundle both the
Python package AND the native libaom DLL.

This hook ensures:
1. The AvifImagePlugin module is included so the codec is registered at
   runtime when pillow_avif is imported.
2. All binary files (libaom.dll / libaom.so) are collected so the codec
   can actually encode and decode AVIF images.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

try:
    from PyInstaller.utils.hooks import collect_dynamic_libs
    binaries = collect_dynamic_libs('pillow_avif')
except Exception:
    binaries = []

hiddenimports = [
    'pillow_avif',
    'pillow_avif.AvifImagePlugin',
] + collect_submodules('pillow_avif')

datas = collect_data_files('pillow_avif')
