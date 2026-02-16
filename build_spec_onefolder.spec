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
    pathex=[str(SCRIPT_DIR), str(SRC_DIR)],  # Include src directory for module imports
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
        # Core application modules from src/
        'config',
        'classifier',
        'lod_detector',
        'file_handler',
        'database',
        'organizer',
        'preprocessing',
        'preprocessing.alpha_correction',
        'preprocessing.alpha_handler',
        'preprocessing.preprocessing_pipeline',
        'preprocessing.upscaler',
        'preprocessing.filters',
        # Core image processing
        'PIL',
        'PIL.Image',
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
        # Qt6 UI framework
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.QtSvg',
        'PyQt6.sip',
        # OpenGL for 3D rendering
        'OpenGL',
        'OpenGL.GL',
        'OpenGL.GLU',
        'OpenGL.GLUT',
        'OpenGL.arrays',
        'OpenGL.arrays.vbo',
        'OpenGL.GL.shaders',
        'OpenGL.platform',
        'OpenGL.platform.glx',
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
        # Background removal and AI tools
        # Note: rembg is collected by hook-rembg.py with proper dependency handling
        'onnxruntime',  # Required for rembg background removal
        'pooch',  # Required for rembg model downloads
        'requests',
        # PyTorch - Core deep learning
        'torch',
        'torch._C',
        # 'torch._six',  # REMOVED - deprecated module no longer exists in PyTorch 1.9+
        'torch.nn',
        'torch.nn.functional',
        'torch.optim',
        'torch.autograd',
        'torch.cuda',
        'torch.jit',
        'torch.onnx',  # ONNX export support for model export/import
        'torchvision',
        'torchvision.transforms',
        # Vision models - CLIP, DINOv2
        'transformers',
        'transformers.models.clip',
        'transformers.models.clip.modeling_clip',
        'transformers.models.clip.configuration_clip',
        'transformers.models.clip.processing_clip',
        'open_clip',
        'timm',
        'timm.models',
        # Vision model utilities
        'huggingface_hub',
        'tokenizers',
        'safetensors',
        'regex',
    ],
    hookspath=[
        str(SCRIPT_DIR),  # Use hooks in project root (hook-torch.py, hook-*.py files)
        str(SCRIPT_DIR / '.github' / 'hooks'),  # Use additional hooks in .github/hooks
    ],
    hooksconfig={},
    runtime_hooks=[
        str(SCRIPT_DIR / 'runtime-hook-onnxruntime.py'),  # Disable CUDA providers for onnxruntime
        str(SCRIPT_DIR / 'runtime-hook-torch.py'),  # Graceful CUDA handling for torch
    ],
    excludes=[
        # Exclude tkinter
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'tkinter.constants',
        'tkinter.font',
        'customtkinter',
        'tkinterdnd2',
        '_tkinter',
        'PIL.ImageTk',
        
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
        'torch.distributed._sharding_spec',  # Deprecated - now uses torch.distributed._shard.sharding_spec
        'torch.distributed._sharded_tensor',
        # Note: torch.distributed._shard is NOT excluded - it's needed for new sharding spec path
        'torch.distributed._shard.checkpoint',
        'torch._inductor',
        'torch._inductor.compile_fx',
        
        # ONNX: Exclude problematic modules that cause isolated subprocess crashes
        # These modules cause DLL initialization failures during PyInstaller analysis
        'onnx.reference',  # Causes exit code 3221225477 (DLL initialization failure)
        'onnx.reference.ops',
        'onnx.reference.ops._op_list',
        'onnxscript',  # Optional scripting extension
        'onnxscript.onnx_opset',
        
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

# Filter out problematic DLLs
print("Filtering DLLs...")
print("  - Legacy OpenGL DLLs (gle*.vc9.dll, gle*.vc10.dll, freeglut*.vc9.dll, freeglut*.vc10.dll)")
print("  - CUDA DLLs (nvcuda.dll, cudart*.dll, cublas*.dll, etc.)")

a.binaries = [
    (dest, src, typ) for (dest, src, typ) in a.binaries
    if not (
        # Exclude legacy GLE DLLs
        ('gle32.vc9.dll' in dest.lower()) or
        ('gle64.vc9.dll' in dest.lower()) or
        ('gle32.vc10.dll' in dest.lower()) or
        ('gle64.vc10.dll' in dest.lower()) or
        # Exclude legacy freeglut DLLs (Visual C++ 9.0 and 10.0 versions)
        ('freeglut32.vc9.dll' in dest.lower()) or
        ('freeglut64.vc9.dll' in dest.lower()) or
        ('freeglut32.vc10.dll' in dest.lower()) or
        ('freeglut64.vc10.dll' in dest.lower()) or
        # Exclude CUDA DLLs
        ('nvcuda' in dest.lower()) or
        ('cudart' in dest.lower()) or
        ('cublas' in dest.lower()) or
        ('cudnn' in dest.lower()) or
        ('cufft' in dest.lower()) or
        ('curand' in dest.lower()) or
        ('cusparse' in dest.lower()) or
        ('cusolver' in dest.lower()) or
        ('nvrtc' in dest.lower()) or
        ('tensorrt' in dest.lower()) or
        # Exclude CUDA execution provider DLL from onnxruntime
        ('onnxruntime_providers_cuda' in dest.lower()) or
        ('onnxruntime_providers_tensorrt' in dest.lower())
    )
]
print(f"Binary count after filtering: {len(a.binaries)}")

# No tcl/tk filtering needed - Qt6-only application
# (Removed tcl/tk checks - not needed anymore)

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
