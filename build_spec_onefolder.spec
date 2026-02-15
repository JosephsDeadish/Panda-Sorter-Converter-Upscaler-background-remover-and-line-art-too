# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Game Texture Sorter (One-Folder Build)
Author: Dead On The Inside / JosephsDeadish

This spec file creates a one-folder application for Windows with all
resources extracted to separate folders for faster startup performance.

Benefits of one-folder build:
- Faster startup time (no extraction on every launch)
- Easier access to assets and configuration
- Better performance with large resource files
- Users can modify themes, sounds, and other assets

Usage: pyinstaller build_spec_onefolder.spec --clean --noconfirm
       Or: build.bat folder
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
        # Include entire assets directory
        (str(ASSETS_DIR), 'assets'),
        # Include resources
        (str(RESOURCES_DIR / 'icons'), 'resources/icons'),
        (str(RESOURCES_DIR / 'cursors'), 'resources/cursors'),
        (str(RESOURCES_DIR / 'sounds'), 'resources/sounds'),
        (str(RESOURCES_DIR / 'translations'), 'resources/translations'),
    ],
    hiddenimports=[
        # Core image processing
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageFile',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        # Scientific computing
        'numpy',
        'numpy.core',
        'cv2',
        'sklearn',
        'sklearn.metrics',
        'sklearn.cluster',
        # Database and file handling
        'sqlite3',
        'send2trash',
        'watchdog',
        # Qt6 UI framework (REQUIRED - replaces tkinter)
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.sip',
        # OpenGL for 3D rendering
        'OpenGL',
        'OpenGL.GL',
        'OpenGL.GLU',
        'OpenGL.GLUT',
        'OpenGL.arrays',
        'OpenGL.arrays.vbo',
        'OpenGL.GL.shaders',
        # Legacy UI framework (optional fallback only)
        # 'tkinter',
        # 'tkinter.ttk',
        # 'customtkinter',
        # Note: tkinter/customtkinter are now optional fallbacks.
        # The application uses Qt6 as primary UI.
        'darkdetect',
        # Utilities
        'psutil',
        'colorama',
        'yaml',
        'pyyaml',
        'tqdm',
        'xxhash',
        # Archive support
        'py7zr',
        'rarfile',
        # Hotkeys
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        # Optional: Include if installed
        # Note: PyInstaller will skip if not available
        'onnxruntime',
        'rembg',
        'requests',
    ],
    hookspath=[str(SCRIPT_DIR)],  # Use hooks in project root (hook-*.py files)
    hooksconfig={},
    runtime_hooks=[],  # Removed tkinter runtime hook - not needed for Qt
    excludes=[
        # Heavy scientific libraries (not needed)
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'IPython',
        
        # PyTorch: Exclude unused/problematic submodules to suppress build warnings
        # Note: Main torch module is included if available, but these internals cause issues
        'torch.testing',
        'torch.testing._internal',
        'torch.testing._internal.opinfo',
        'torch.testing._internal.common_utils',
        'torch.distributed.elastic',
        'torch.distributed.elastic.multiprocessing',
        'torch.distributed._sharding_spec',
        'torch.distributed._sharded_tensor',
        'torch.distributed._shard',
        'torch.distributed._shard.checkpoint',
        'torch._inductor',
        'torch._inductor.compile_fx',
        
        # Cairo SVG: cairosvg/cairocffi require native Cairo DLL not available on Windows CI
        # SVG support is optional - the application handles missing cairosvg gracefully
        'cairosvg',
        'cairocffi',
        
        # Platform-specific modules
        'darkdetect._mac_detect',  # macOS-only, not needed on Windows
        'importlib_resources.trees',  # Internal module that causes issues
        
        # Performance libraries that cause bloat (optional features)
        'numba',
        'llvmlite',
        
        # Parser tables that regenerate and cause issues
        'pycparser.lextab',
        'pycparser.yacctab',
        
        # Additional heavy/unused libraries
        'pytest',
        'hypothesis',
        'sphinx',
        'setuptools',
        'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files but keep essential tcl/tk data
# Note: We filter demos and timezone data to reduce size, but keep core tcl/tk files
a.datas = [x for x in a.datas if not x[0].startswith('tk/demos')]
a.datas = [x for x in a.datas if not x[0].startswith('tcl/tzdata')]

# Ensure we keep critical TCL/Tk initialization files
# These are required for tkinter to work properly
print("\n" + "="*70)
print("TCL/TK DATA FILES CHECK")
print("="*70)
tcl_files = [x for x in a.datas if x[0].startswith(('tcl/', 'tk/'))]
print(f"Found {len(tcl_files)} TCL/Tk data files")
if tcl_files:
    print("✓ TCL/Tk data files are included")
else:
    print("⚠ WARNING: No TCL/Tk data files found!")
    print("  Tkinter may not work properly in the built executable.")
print("="*70 + "\n")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # KEY DIFFERENCE: Don't bundle binaries in EXE
    name=EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress EXE
    console=False,  # No console window (GUI application)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific options
    version='file_version_info.txt',  # Version info file
    icon=str(ICON_PATH) if ICON_PATH else None,  # Application icon
    uac_admin=False,  # Don't require admin
    uac_uiaccess=False,
)

# Create the folder collection (COLLECT) for one-folder distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=EXE_NAME,
)
