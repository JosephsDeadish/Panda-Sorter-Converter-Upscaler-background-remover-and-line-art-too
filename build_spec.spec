# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Game Texture Sorter
Author: Dead On The Inside / JosephsDeadish

This spec file creates a single-EXE application for Windows
with all resources embedded and proper metadata.
"""

import sys
from pathlib import Path

block_cipher = None

# Application metadata
APP_NAME = "Game Texture Sorter"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Dead On The Inside / JosephsDeadish"
EXE_NAME = "GameTextureSorter"

# Determine paths
SCRIPT_DIR = Path(SPECPATH)
SRC_DIR = SCRIPT_DIR / 'src'
RESOURCES_DIR = SRC_DIR / 'resources'
ASSETS_DIR = SCRIPT_DIR / 'assets'

# Check for icon in assets directory first, then resources
ICON_PATH = ASSETS_DIR / 'icon.ico'
if not ICON_PATH.exists():
    ICON_PATH = RESOURCES_DIR / 'icons' / 'panda_icon.ico'
    if not ICON_PATH.exists():
        ICON_PATH = None  # Will use default PyInstaller icon

# Convert to absolute path string for PyInstaller
if ICON_PATH:
    ICON_PATH = str(ICON_PATH.absolute())

# Collect all Python files
a = Analysis(
    ['main.py'],
    pathex=[str(SCRIPT_DIR)],
    binaries=[],
    datas=[
        # Include assets (icon files)
        (str(ASSETS_DIR / 'icon.ico'), 'assets'),
        (str(ASSETS_DIR / 'icon.png'), 'assets'),
        # Include resources
        (str(RESOURCES_DIR / 'icons'), 'resources/icons'),
        (str(RESOURCES_DIR / 'cursors'), 'resources/cursors'),
        (str(RESOURCES_DIR / 'themes'), 'resources/themes'),
        (str(RESOURCES_DIR / 'sounds'), 'resources/sounds'),
    ],
    hiddenimports=[
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'numpy',
        'cv2',
        'sklearn',
        'sqlite3',
        'tkinter',
        'customtkinter',
        'send2trash',
        'psutil',
        'colorama',
        'yaml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'IPython',
        # Torch: exclude unused/problematic submodules to suppress build warnings
        'torch.testing',
        'torch.testing._internal',
        'torch.testing._internal.opinfo',
        'torch.distributed.elastic',
        'torch.distributed._sharding_spec',
        'torch.distributed._sharded_tensor',
        'torch.distributed._shard.checkpoint',
        'torch._inductor',
        # Cairo: cairosvg/cairocffi require native Cairo DLL not available on Windows CI;
        # SVG support is optional (app handles missing cairosvg gracefully)
        'cairosvg',
        'cairocffi',
        # macOS-only modules not needed on Windows
        'darkdetect._mac_detect',
        # Misc unused
        'importlib_resources.trees',
        'numba',
        'llvmlite',
        'pycparser.lextab',
        'pycparser.yacctab',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files
a.datas = [x for x in a.datas if not x[0].startswith('tk/demos')]
a.datas = [x for x in a.datas if not x[0].startswith('tcl/tzdata')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress EXE
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI application)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific options
    version='file_version_info.txt',  # Version info file
    icon=str(ICON_PATH) if ICON_PATH else None,  # Application icon (use default if not found)
    uac_admin=False,  # Don't require admin
    uac_uiaccess=False,
)
