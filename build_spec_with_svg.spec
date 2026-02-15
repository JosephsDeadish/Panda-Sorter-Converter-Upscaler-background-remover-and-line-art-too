# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Game Texture Sorter WITH SVG SUPPORT
Author: Dead On The Inside / JosephsDeadish

This spec file creates an application for Windows with SVG support
by bundling Cairo DLLs and dependencies.

For standard builds without SVG, use: build_spec_onefolder.spec
"""

import sys
import os
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

# ============================================================================
# SVG SUPPORT: Cairo DLL Detection and Bundling
# ============================================================================

print("\n" + "="*70)
print("CAIRO DLL DETECTION FOR SVG SUPPORT")
print("="*70)

# List of required Cairo DLLs
REQUIRED_CAIRO_DLLS = [
    'libcairo-2.dll',
    'libcairo-gobject-2.dll',
    'libpng16.dll',
    'zlib1.dll',
    'libfreetype-6.dll',
    'libfontconfig-1.dll',
    'libexpat-1.dll',
    'libbz2-1.dll',
    'libharfbuzz-0.dll',
    'libglib-2.0-0.dll',
    'libintl-8.dll',
    'libiconv-2.dll',
    'libpixman-1-0.dll',
]

# Alternative DLL names (some systems use different versions)
ALTERNATIVE_DLLS = {
    'libffi-8.dll': 'libffi-7.dll',
}

# DLL detection paths (in order of priority)
CAIRO_SEARCH_PATHS = [
    r'C:\Program Files\GTK3-Runtime Win64\bin',
    r'C:\msys64\mingw64\bin',
    os.environ.get('CAIRO_DLL_PATH', ''),
    str(SCRIPT_DIR / 'cairo_dlls'),
]

# Clean up empty paths
CAIRO_SEARCH_PATHS = [p for p in CAIRO_SEARCH_PATHS if p and Path(p).exists()]

def find_cairo_dlls():
    """
    Search for Cairo DLLs in common installation paths.
    Returns dict mapping DLL names to their full paths.
    """
    found_dlls = {}
    missing_dlls = []
    
    print(f"\nSearching for Cairo DLLs in:")
    for path in CAIRO_SEARCH_PATHS:
        print(f"  - {path}")
    
    if not CAIRO_SEARCH_PATHS:
        print("\n⚠ WARNING: No Cairo DLL search paths found!")
        print("  SVG support will NOT be available in the built executable.")
        print("  See docs/SVG_BUILD_GUIDE.md for installation instructions.")
        return found_dlls, REQUIRED_CAIRO_DLLS
    
    # Search for each required DLL
    for dll_name in REQUIRED_CAIRO_DLLS:
        found = False
        for search_path in CAIRO_SEARCH_PATHS:
            dll_path = Path(search_path) / dll_name
            if dll_path.exists():
                found_dlls[dll_name] = str(dll_path)
                found = True
                break
        
        if not found:
            missing_dlls.append(dll_name)
    
    # Try alternative DLL names for missing ones
    for primary_dll, alternative_dll in ALTERNATIVE_DLLS.items():
        if primary_dll not in found_dlls:
            for search_path in CAIRO_SEARCH_PATHS:
                dll_path = Path(search_path) / alternative_dll
                if dll_path.exists():
                    found_dlls[primary_dll] = str(dll_path)
                    if primary_dll in missing_dlls:
                        missing_dlls.remove(primary_dll)
                    break
    
    return found_dlls, missing_dlls

# Detect Cairo DLLs
cairo_dlls_dict, missing_cairo_dlls = find_cairo_dlls()

# Build binaries list for PyInstaller
cairo_binaries = []
if cairo_dlls_dict:
    print(f"\n✓ Found {len(cairo_dlls_dict)} Cairo DLLs:")
    for dll_name, dll_path in cairo_dlls_dict.items():
        print(f"  ✓ {dll_name}")
        # Add to binaries list (source, destination)
        cairo_binaries.append((dll_path, '.'))

if missing_cairo_dlls:
    print(f"\n⚠ Missing {len(missing_cairo_dlls)} Cairo DLLs:")
    for dll_name in missing_cairo_dlls:
        print(f"  ✗ {dll_name}")
    print("\n⚠ SVG support will be LIMITED or NON-FUNCTIONAL!")
    print("  To enable full SVG support:")
    print("  1. Install GTK3 runtime or MSYS2 with mingw-w64-x86_64-gtk3")
    print("  2. Or run: python scripts/setup_cairo_dlls.py")
    print("  3. See docs/SVG_BUILD_GUIDE.md for detailed instructions")
else:
    print("\n✓ All required Cairo DLLs found! SVG support will be available.")

print("="*70 + "\n")

# ============================================================================
# PyInstaller Configuration
# ============================================================================

# Collect all Python files
a = Analysis(
    ['main.py'],
    pathex=[str(SCRIPT_DIR), str(SRC_DIR)],  # Include src directory for module imports
    binaries=cairo_binaries,  # Include Cairo DLLs
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
        # Core application modules from src/
        'config',
        'classifier',
        'lod_detector',
        'file_handler',
        'database',
        'organizer',
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
        # Qt6 UI framework (REQUIRED - ONLY SUPPORTED UI)
        # NO TKINTER - Full Qt6 migration complete
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.sip',
        # OpenGL for 3D rendering (panda, skeletal animations)
        'OpenGL',
        'OpenGL.GL',
        'OpenGL.GLU',
        'OpenGL.GLUT',
        'OpenGL.arrays',
        'OpenGL.arrays.vbo',
        'OpenGL.GL.shaders',
        'darkdetect',
        # Utilities
        'psutil',
        'colorama',
        'yaml',  # pyyaml package imports as 'yaml'
        'tqdm',
        'xxhash',
        # Archive support
        'py7zr',
        'rarfile',
        # Hotkeys
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        # SVG Support - NOW INCLUDED!
        'cairosvg',
        'cairocffi',
        'cairocffi._ffi',
        'cairocffi.constants',
        'cairocffi.surfaces',
        'cairocffi.patterns',
        'cairocffi.fonts',
        # Optional: Include if installed
        'onnxruntime',
        'rembg',
        'requests',
    ],
    hookspath=[str(SCRIPT_DIR)],  # Use hooks in project root (hook-*.py files)
    hooksconfig={},
    runtime_hooks=[],  # Removed tkinter runtime hook - not needed for Qt6
    excludes=[
        # Tkinter/CustomTkinter - NO LONGER USED (full Qt6 migration complete)
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'customtkinter',
        'tkinterdnd2',
        '_tkinter',
        
        # Heavy scientific libraries (not needed)
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'IPython',
        
        # PyTorch: Exclude unused/problematic submodules to suppress build warnings
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
