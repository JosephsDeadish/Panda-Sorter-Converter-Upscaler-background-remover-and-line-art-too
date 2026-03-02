#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Panda Sorter Converter Upscaler - Qt Main Application
A Qt6-based application with OpenGL rendering.
Author: Dead On The Inside / JosephsDeadish
"""

import sys
import os
import importlib
import logging
import functools
import types as _types
import random as _random
from pathlib import Path

# Animation ID → GL animation state mapping (mirrors _MOOD_TO_ANIMATION in panda_widget_gl)
_MOOD_TO_ANIMATION_MAP: dict = {
    'animation_dance':    'dance',
    'animation_backflip': 'backflip',
    'animation_magic':    'celebrating',
    'animation_spin':     'spin',
    'animation_juggle':   'juggle',
    'dance': 'dance', 'backflip': 'backflip', 'spin': 'spin', 'juggle': 'juggle',
}

# Fix Unicode encoding issues on Windows
# This prevents UnicodeEncodeError when printing emojis to console
if sys.platform == 'win32':
    import codecs
    # Reconfigure stdout and stderr to use UTF-8 encoding
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    # Also set environment variable for child processes
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# CRITICAL: Add src directory to sys.path BEFORE any src imports
# This ensures that all imports from src/ work correctly, particularly config.py
# Without this, you'll get "ModuleNotFoundError: No module named 'config'"
src_dir = Path(__file__).parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# ---------------------------------------------------------------------------
# torchvision compat shim — must run BEFORE any import of basicsr/realesrgan
# ---------------------------------------------------------------------------
# torchvision 0.16+ removed torchvision.transforms.functional_tensor.
# basicsr ≤ 1.4.2 imports it at module level, causing ImportError on modern
# torchvision.  Inject a thin shim so basicsr imports cleanly everywhere.
try:
    import torchvision.transforms.functional_tensor as _tvft_early  # noqa: F401
except (ImportError, ModuleNotFoundError):
    try:
        import torchvision.transforms.functional as _tvtf_early  # noqa: F401
        _compat_early = _types.ModuleType('torchvision.transforms.functional_tensor')
        for _attr_early in (
            'rgb_to_grayscale', 'adjust_brightness', 'adjust_contrast',
            'adjust_saturation', 'adjust_hue', 'normalize',
            'pad', 'crop', 'center_crop', 'resize',
            'to_tensor', 'to_pil_image',
        ):
            if hasattr(_tvtf_early, _attr_early):
                setattr(_compat_early, _attr_early, getattr(_tvtf_early, _attr_early))
        sys.modules['torchvision.transforms.functional_tensor'] = _compat_early
        del _compat_early, _tvtf_early
    except Exception:
        pass  # torchvision not installed; basicsr/realesrgan checks handle this gracefully
# ---------------------------------------------------------------------------

# Handle lightweight CLI flags BEFORE importing Qt (no display needed)
# These must run early — before any module-level Qt import — so they work
# even when PyQt6 is not installed.
def _handle_early_cli() -> None:
    """Check for --version / --check-features / --help before Qt import."""
    if len(sys.argv) < 2:
        return

    arg = sys.argv[1]

    if arg in ('--version', '-V'):
        # APP_NAME / APP_VERSION are in src/config.py; import lazily so we
        # don't pull in the full Qt stack just for a version string.
        try:
            from config import APP_NAME, APP_VERSION, PATREON_URL as _PATREON
        except Exception:
            # Fallback values — update all three PATREON_URL locations if the URL changes:
            #   1. src/config.py (PATREON_URL constant)
            #   2. main.py _PATREON fallback (here)
            #   3. src/ui/settings_panel_qt.py _PATREON_URL fallback
            APP_NAME, APP_VERSION = "Panda Sorter Converter Upscaler", "1.0.0"
            _PATREON = "https://www.patreon.com/JosephsDeadish"
        print(f"{APP_NAME} v{APP_VERSION}")
        print("Author: Dead On The Inside / JosephsDeadish")
        print(f"Support: {_PATREON}")
        sys.exit(0)

    if arg in ('--help', '-h'):
        try:
            from config import APP_NAME
        except Exception:
            APP_NAME = "Panda Sorter Converter Upscaler"
        print(f"Usage: python main.py [options]")
        print()
        print("Options:")
        print("  --version, -V        Show version and exit")
        print("  --check-features     Show which optional features are available")
        print("  --help, -h           Show this help message")
        print()
        print(f"Running without options launches the {APP_NAME} GUI.")
        sys.exit(0)

    if arg == '--check-features':
        # Import only what we need for feature detection (no Qt)
        try:
            from config import APP_NAME, APP_VERSION
        except Exception:
            APP_NAME, APP_VERSION = "Panda Sorter Converter Upscaler", "1.0.0"

        print(f"{APP_NAME} v{APP_VERSION} — Feature Check")
        print("=" * 55)

        def _line(label: str, available: bool, hint: str = "") -> None:
            status = "✅" if available else "❌"
            print(f"  {status}  {label}")
            if not available and hint:
                print(f"        Install: {hint}")

        def _try_import(mod: str) -> bool:
            try:
                __import__(mod)
                return True
            except Exception:
                return False

        _line("Image loading (Pillow)",
              _try_import('PIL'),
              "pip install pillow")
        _line("ONNX Runtime (batch inference / offline AI)",
              _try_import('onnxruntime'),
              "pip install onnxruntime")
        _line("ONNX format (model export)",
              _try_import('onnx'),
              "pip install onnx")
        _line("PyTorch (training + advanced vision models)",
              _try_import('torch'),
              "pip install torch torchvision  # see pytorch.org for CUDA")
        _line("Transformers / CLIP search",
              _try_import('transformers'),
              "pip install transformers")
        _line("Open CLIP",
              _try_import('open_clip'),
              "pip install open-clip-torch")
        _line("timm (EfficientNet, etc.)",
              _try_import('timm'),
              "pip install timm")
        _line("Background removal (rembg)",
              _try_import('rembg'),
              "pip install rembg[cpu]")
        _line("SVG support (cairosvg)",
              _try_import('cairosvg'),
              "pip install cairosvg cairocffi")
        _line("OCR text detection (pytesseract)",
              _try_import('pytesseract'),
              "pip install pytesseract  # + install Tesseract system package")
        _line("Vector similarity search (faiss)",
              _try_import('faiss'),
              "pip install faiss-cpu")
        try:
            from preprocessing.upscaler import REALESRGAN_AVAILABLE
            upscaler_ok = REALESRGAN_AVAILABLE
        except Exception:
            upscaler_ok = False
        _line("Real-ESRGAN upscaler",
              upscaler_ok,
              "pip install basicsr realesrgan")
        try:
            from native_ops import NATIVE_AVAILABLE
            native_ok = NATIVE_AVAILABLE
        except Exception:
            native_ok = False
        _line("Native Lanczos acceleration (Rust)",
              native_ok,
              "cd native && maturin develop --release")

        print("=" * 55)
        sys.exit(0)


_handle_early_cli()

# Qt imports - REQUIRED, no fallbacks
def _ensure_qt_platform():
    """
    Ensure QT_QPA_PLATFORM is set for headless / CI environments.

    On Linux, PyQt6 requires a display server or a platform plugin.
    When no display is available (e.g. CI, server, docker), we fall back to
    the 'offscreen' platform so the application can still start, process
    files, and run the GUI (rendered off-screen).

    On Windows / macOS this is a no-op because those platforms always have
    a display-compatible backend available.
    """
    if sys.platform.startswith('linux'):
        # Only set if not already configured
        if 'QT_QPA_PLATFORM' not in os.environ:
            # Prefer xcb (real display) but fall back gracefully
            display = os.environ.get('DISPLAY', '')
            wayland = os.environ.get('WAYLAND_DISPLAY', '')
            if not display and not wayland:
                os.environ['QT_QPA_PLATFORM'] = 'offscreen'
                os.environ['QT_QPA_FONTDIR'] = ''  # suppress font warnings

_ensure_qt_platform()

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QProgressBar, QTextEdit, QTabWidget,
        QFileDialog, QMessageBox, QStatusBar, QMenuBar, QMenu,
        QSplitter, QFrame, QComboBox, QGridLayout, QStackedWidget,
        QScrollArea, QDockWidget, QToolBar, QInputDialog, QGroupBox
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QByteArray, QObject, QEvent, QPoint
    from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor
except ImportError as e:
    _err = str(e)
    print("=" * 70)
    # Distinguish "not installed" from "system libraries missing"
    if 'libEGL' in _err or 'libGL' in _err or 'cannot open shared object' in _err:
        print("ERROR: PyQt6 is installed but required system libraries are missing!")
        print("=" * 70)
        print()
        print("PyQt6 is installed correctly, but a required system library is absent.")
        print()
        print("On Debian/Ubuntu, install the missing libraries with:")
        print("    sudo apt-get install -y libegl1 libgl1 libgles2")
        print("    sudo apt-get install -y libxcb-xinerama0 libxkbcommon-x11-0")
        print()
        print("Or run the application with an offscreen backend (headless):")
        print("    QT_QPA_PLATFORM=offscreen python main.py")
    else:
        print("ERROR: PyQt6 is not installed!")
        print("=" * 70)
        print()
        print("This application requires PyQt6 to run.")
        print()
        print("To install PyQt6, run:")
        print("    pip install PyQt6")
        print()
        print("Or install all dependencies:")
        print("    pip install -r requirements.txt")
    print()
    print(f"Technical details: {e}")
    print("=" * 70)
    sys.exit(1)

# Setup logging — always write to a file in the EXE so the user can debug issues.
# In the frozen EXE (console=False), there is no terminal, so all logger.warning/
# logger.error calls are invisible without a file handler.
def _setup_logging() -> None:
    _log_level = logging.INFO
    _handlers: list = []
    # Always keep the default StreamHandler (goes to console/stdout when available)
    _stream_handler = logging.StreamHandler()
    _stream_handler.setLevel(_log_level)
    _handlers.append(_stream_handler)
    # In the frozen EXE, also write to a log file next to the EXE
    if getattr(sys, 'frozen', False):
        try:
            _log_dir = Path(sys.executable).parent / 'app_data' / 'logs'
            _log_dir.mkdir(parents=True, exist_ok=True)
            _file_handler = logging.FileHandler(str(_log_dir / 'app.log'), encoding='utf-8')
            _file_handler.setLevel(_log_level)
            _file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s %(name)s: %(message)s'
            ))
            _handlers.append(_file_handler)
        except Exception as _e:
            import sys as _sys
            print(f"[logging] Could not set up file log handler: {_e!r}", file=_sys.stderr)
    logging.basicConfig(level=_log_level, handlers=_handlers)

_setup_logging()
logger = logging.getLogger(__name__)

# Module-level constant — built once, used by _tick_panda_interaction every 33 ms
_PANDA_STATE_EMOJI: dict = {
    'idle':                 '🐼',
    'walking':              '🚶',
    'running':              '🏃',
    'waving':               '👋',
    'celebrating':          '🎉',
    'sleeping':             '😴',
    'sitting_back':         '🧘',
    'crawling':             '🐾',
    'rolling':              '🔄',
    'climbing_wall':        '🧗',
    'falling_back':         '😵',
    'hanging_ceiling':      '🙃',
    'hanging_window_edge':  '🪟',
    'working':              '💻',
    'jumping':              '🦘',
    'wall_hit':             '😤',
    'clicked':              '😮',
    'sniffing':             '👃',
    'grooming':             '✨',
    'yawning':              '🥱',
    'stretching':           '🤸',
    'flopping':             '😂',
    'scratching':           '🐾',
    'daydream':             '💭',
    'dance':                '💃',
    'backflip':             '🤸',
    'spin':                 '🌀',
    'juggle':               '🎪',
}

# Import configuration (now that src is in path)
from config import config, APP_NAME, APP_VERSION, PATREON_URL

# Import core modules
from classifier import TextureClassifier, ALL_CATEGORIES
from lod_detector import LODDetector
from file_handler import FileHandler
from database import TextureDatabase
from organizer import OrganizationEngine, ORGANIZATION_STYLES

# ── EXE: configure PyOpenGL BEFORE any GL import fires ───────────────────────
# This MUST run at module level (not in main()) so that the environment is
# ready before the module-level GL probe below.  In a frozen Windows EXE the
# Python module is loaded (and all module-level code executes) before main()
# is ever called.  If USE_ACCELERATE is still True when OpenGL.GL is first
# imported, the C-accelerate extension (opengl_accelerate) is loaded; if that
# extension is absent or built against a different driver version it can
# segfault the process.  Setting USE_ACCELERATE=False first forces pure-Python
# mode which is always safe.
def _setup_opengl_for_exe() -> None:
    """Configure PyOpenGL env. Safe to call multiple times (idempotent)."""
    if not sys.platform.startswith('win'):
        return
    # Force Qt to use native opengl32.dll (desktop GL) NOT ANGLE (Direct3D).
    # ANGLE only supports OpenGL ES — CompatibilityProfile is NOT available via ANGLE.
    # Without this, glShadeModel(GL_SMOOTH) raises GLError(1282) on first initializeGL()
    # call, triggering the 2D panda fallback even on machines with good GPU drivers.
    # Must be set BEFORE QApplication is created (Qt reads it during platform init).
    os.environ.setdefault('QT_OPENGL', 'desktop')
    # Force the Windows platform backend (not GLX/EGL which don't exist on Win)
    os.environ.setdefault('PYOPENGL_PLATFORM_HANDLER', 'win32')
    # Block the C-accelerate extension before OpenGL is imported.
    # sys.modules trick: inserting a falsy sentinel causes PyOpenGL's
    # `if opengl_accelerate:` guard to evaluate False.
    import types as _tm
    _acc_stub = _tm.ModuleType('opengl_accelerate')
    _acc_stub.USE_ACCELERATE = False  # type: ignore[attr-defined]
    for _acc_name in ('opengl_accelerate', 'OpenGL_accelerate',
                      'OpenGL.arrays.numpymodule'):
        if _acc_name not in sys.modules:
            sys.modules[_acc_name] = _acc_stub  # type: ignore[assignment]
    # Tell PyOpenGL itself to skip accelerate BEFORE it is imported
    try:
        import OpenGL as _ogl
        _ogl.USE_ACCELERATE = False
    except Exception:
        pass  # OpenGL not yet importable; sys.modules stub above is enough
    # Add DLL directories so ctypes can find opengl32.dll
    _sys32 = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32')
    for _d in [_sys32]:
        try:
            if os.path.isdir(_d):
                os.add_dll_directory(_d)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
    if getattr(sys, 'frozen', False):
        _app_dir = os.path.dirname(sys.executable)
        for _d in [_app_dir, getattr(sys, '_MEIPASS', _app_dir)]:
            try:
                os.add_dll_directory(_d)  # type: ignore[attr-defined]
            except (AttributeError, OSError):
                pass
    # Set Qt's application-level AA_UseDesktopOpenGL attribute.
    # This must be called before QApplication is instantiated (it is a static
    # class method in Qt6 that can be called without a QApplication instance).
    # Belt-and-suspenders alongside QT_OPENGL=desktop.
    try:
        from PyQt6.QtWidgets import QApplication as _QApp
        from PyQt6.QtCore import Qt as _Qt6
        _QApp.setAttribute(_Qt6.ApplicationAttribute.AA_UseDesktopOpenGL)
    except Exception:
        pass  # Qt not yet imported at module-load time; main() sets it too


_setup_opengl_for_exe()

# ── Panda widget selection (delegated to panda_widget_loader) ──────────────
# panda_widget_loader selects the best available backend:
#   1. PandaOpenGLWidget  — hardware-accelerated 3D (preferred)
#   2. PandaWidget2D      — QPainter 2D fallback (no OpenGL required)
# It performs the runtime GL probe so we don't duplicate that logic here.
PandaOpenGLWidget = None
PandaWidget2D = None
PANDA_WIDGET_AVAILABLE = False
_OPENGL_RUNTIME_OK: bool = False
try:
    from ui.panda_widget_loader import (
        PandaWidget as _PandaWidgetCls,
        OPENGL_AVAILABLE as _OPENGL_AVAILABLE,
        PANDA_2D_AVAILABLE as _PANDA_2D_AVAILABLE,
    )
    if _OPENGL_AVAILABLE:
        PandaOpenGLWidget = _PandaWidgetCls
        PANDA_WIDGET_AVAILABLE = True
        _OPENGL_RUNTIME_OK = True
        logger.info("✅ panda_widget_loader selected 3D OpenGL backend")
    elif _PANDA_2D_AVAILABLE:
        PandaWidget2D = _PandaWidgetCls
        logger.info("✅ panda_widget_loader selected 2D QPainter backend (OpenGL unavailable)")
    else:
        logger.warning("No panda widget backend available")
except Exception as _loader_err:
    logger.warning(f"panda_widget_loader failed ({_loader_err}); trying direct imports")
    # Direct-import fallback (belt-and-suspenders if loader itself is broken)
    try:
        from ui.panda_widget_gl import PandaOpenGLWidget as _POWC
        from OpenGL.GL import GL_DEPTH_TEST as _GL_DEPTH_TEST_PROBE  # noqa: F401
        PandaOpenGLWidget = _POWC
        PANDA_WIDGET_AVAILABLE = True
        _OPENGL_RUNTIME_OK = True
    except Exception:
        pass
    try:
        from ui.panda_widget_2d import PandaWidget2D as _PW2D
        PandaWidget2D = _PW2D
    except Exception:
        pass

# Always ensure PandaWidget2D is loaded as a runtime fallback even when the
# 3D loader succeeded.  Without this, _on_panda_gl_failed and the line-747
# construction-failure path both see PandaWidget2D=None and leave an empty
# sidebar when the GL widget fails to initialise at runtime.
if PandaWidget2D is None:
    try:
        from ui.panda_widget_2d import PandaWidget2D as _PW2D_fallback
        PandaWidget2D = _PW2D_fallback
        logger.debug("PandaWidget2D loaded as GL runtime-failure fallback")
    except Exception as _2d_fallback_err:
        logger.debug(f"PandaWidget2D fallback unavailable: {_2d_fallback_err}")

# Import each UI panel independently so one bad import does not disable all tools.
# Each name is set to None on failure; callers guard with `if PanelClass is not None`.
def _try_import(module_path: str, class_name: str):
    """Return the named class from module_path, or None on import/attribute failure.

    Catches BaseException (not just Exception) so that modules which call
    sys.exit() or raise SystemExit during their module-level initialization
    (e.g. rembg.bg when onnxruntime DLL loading fails on Windows) cannot
    propagate a SystemExit to main.py's module-level scope and abort the
    application before it starts.
    """
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)
    except (Exception, SystemExit) as _e:
        logger.warning(f"Optional UI panel {class_name} not available: {_e}", exc_info=True)
        return None

BackgroundRemoverPanelQt  = _try_import('ui.background_remover_panel_qt',  'BackgroundRemoverPanelQt')
ColorCorrectionPanelQt    = _try_import('ui.color_correction_panel_qt',    'ColorCorrectionPanelQt')
BatchNormalizerPanelQt    = _try_import('ui.batch_normalizer_panel_qt',     'BatchNormalizerPanelQt')
QualityCheckerPanelQt     = _try_import('ui.quality_checker_panel_qt',      'QualityCheckerPanelQt')
LineArtConverterPanelQt   = _try_import('ui.lineart_converter_panel_qt',   'LineArtConverterPanelQt')
AlphaFixerPanelQt         = _try_import('ui.alpha_fixer_panel_qt',         'AlphaFixerPanelQt')
BatchRenamePanelQt        = _try_import('ui.batch_rename_panel_qt',        'BatchRenamePanelQt')
ImageRepairPanelQt        = _try_import('ui.image_repair_panel_qt',        'ImageRepairPanelQt')
FormatConverterPanelQt    = _try_import('ui.format_converter_panel_qt',    'FormatConverterPanelQt')
CustomizationPanelQt      = _try_import('ui.customization_panel_qt',       'CustomizationPanelQt')
ImageUpscalerPanelQt      = _try_import('ui.upscaler_panel_qt',            'ImageUpscalerPanelQt')
OrganizerPanelQt          = _try_import('ui.organizer_panel_qt',           'OrganizerPanelQt')
SettingsPanelQt           = _try_import('ui.settings_panel_qt',            'SettingsPanelQt')
FileBrowserPanelQt        = _try_import('ui.file_browser_panel_qt',        'FileBrowserPanelQt')
NotepadPanelQt            = _try_import('ui.notepad_panel_qt',             'NotepadPanelQt')

# UI_PANELS_AVAILABLE = True if at least the core tool panels loaded correctly.
_core_panels = [BackgroundRemoverPanelQt, AlphaFixerPanelQt, ImageUpscalerPanelQt,
                FileBrowserPanelQt, NotepadPanelQt, SettingsPanelQt]
UI_PANELS_AVAILABLE = any(p is not None for p in _core_panels)
if UI_PANELS_AVAILABLE:
    logger.info("✅ UI panels loaded (individual failures are non-fatal)")
else:
    logger.warning("⚠️  All UI panels failed to load — check PyQt6 installation")


class DraggableTabWidget(QTabWidget):
    """QTabWidget that supports drag-and-drop tab extraction."""
    
    tab_detached = pyqtSignal(int, str, QWidget)  # index, name, widget
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)  # Allow tab reordering
        self.setTabsClosable(False)  # We handle closing via detachment
        self._drag_start_pos = None
        self._dragging = False
        self._dragging_tab_index = -1
        
        # Get tab bar and enable mouse tracking
        tab_bar = self.tabBar()
        tab_bar.setMouseTracking(True)
        
    def mousePressEvent(self, event):
        """Start drag operation when clicking on tab."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on a tab
            tab_bar = self.tabBar()
            for i in range(self.count()):
                if tab_bar.tabRect(i).contains(event.pos()):
                    self._drag_start_pos = event.pos()
                    self._dragging_tab_index = i
                    break
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Detect drag motion and create floating window."""
        if (self._drag_start_pos is not None and 
            event.buttons() == Qt.MouseButton.LeftButton):
            
            # Check if drag distance is significant
            drag_distance = (event.pos() - self._drag_start_pos).manhattanLength()
            
            if drag_distance > 20 and not self._dragging:  # Threshold to start drag
                self._dragging = True
                
                # Get tab info
                index = self._dragging_tab_index
                tab_text = self.tabText(index)
                tab_widget = self.widget(index)
                
                # Emit signal to parent to handle detachment
                self.tab_detached.emit(index, tab_text, tab_widget)
                
                # Reset drag state
                self._drag_start_pos = None
                self._dragging = False
                
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """End drag operation."""
        self._drag_start_pos = None
        self._dragging = False
        super().mouseReleaseEvent(event)


class BloodSplatterLabel(QLabel):
    """Temporary blood-splatter overlay that fades out after a click (Gore theme)."""

    SPLATTERS = ["🩸💦🩸", "💉🩸💦", "🩸🔴🩸", "🔴💦🔴", "🩸🩸💉"]

    def __init__(self, parent: 'QWidget', pos: 'QPoint') -> None:
        super().__init__(parent)
        _r = _random
        self.setText(_r.choice(self.SPLATTERS))
        self.setStyleSheet(
            "QLabel { background: transparent; font-size: 26px; color: #cc0000; "
            "border: none; padding: 0; }"
        )
        self.adjustSize()
        # Centre on click point with a small random jitter
        dx = _r.randint(-12, 12)
        dy = _r.randint(-12, 12)
        self.move(pos.x() - self.width() // 2 + dx,
                  pos.y() - self.height() // 2 + dy)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.show()
        self.raise_()

        # Fade-out animation
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(900)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.finished.connect(self.deleteLater)
        anim.start()
        self._anim = anim  # keep reference alive


class GoreSplatterFilter(QObject):
    """Application-wide event filter: shows BloodSplatterLabel on every button click.

    Install with ``QApplication.instance().installEventFilter(instance)`` and
    remove with ``QApplication.instance().removeEventFilter(instance)``.
    """

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        try:
            from PyQt6.QtWidgets import QAbstractButton
            from PyQt6.QtCore import QEvent as _QEv
            if (event.type() == _QEv.Type.MouseButtonRelease
                    and isinstance(obj, QAbstractButton)
                    and obj.isEnabled()
                    and hasattr(event, 'position')):
                win = obj.window()
                if win is not None:
                    # Use event.position().toPoint() — the Qt6-correct way.
                    # The deprecated pos() method returns QPointF in newer
                    # PyQt6 builds, causing a TypeError in mapTo().
                    pos = obj.mapTo(win, event.position().toPoint())
                    BloodSplatterLabel(win, pos)
        except Exception as _e:
            import logging as _log
            _log.getLogger(__name__).debug(f"GoreSplatterFilter: {_e}")
        return False  # never consume the event


class VampireBatLabel(QLabel):
    """Temporary bat emoji that flies upward and fades out on click (Vampire theme)."""

    BATS = ["🦇", "🦇🦇", "🦇 🦇", "🦇🌙", "🦇💜🦇"]

    def __init__(self, parent: 'QWidget', pos: 'QPoint') -> None:
        super().__init__(parent)
        _r = _random
        self.setText(_r.choice(self.BATS))
        self.setStyleSheet(
            "QLabel { background: transparent; font-size: 22px; color: #cc44ff; "
            "border: none; padding: 0; }"
        )
        self.adjustSize()
        dx = _r.randint(-10, 10)
        self.move(pos.x() - self.width() // 2 + dx,
                  pos.y() - self.height() // 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.show()
        self.raise_()

        # Fly upward using geometry animation
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)

        # Opacity fade
        self._fade = QPropertyAnimation(eff, b"opacity", self)
        self._fade.setDuration(1100)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.setEasingCurve(QEasingCurve.Type.InQuad)
        self._fade.finished.connect(self.deleteLater)

        # Rise up
        start_geo = self.geometry()
        end_geo = QRect(start_geo.x() + _r.randint(-20, 20),
                        start_geo.y() - 80,
                        start_geo.width(), start_geo.height())
        self._rise = QPropertyAnimation(self, b"geometry", self)
        self._rise.setDuration(1100)
        self._rise.setStartValue(start_geo)
        self._rise.setEndValue(end_geo)
        self._rise.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._fade.start()
        self._rise.start()


class VampireBatFilter(QObject):
    """Application-wide event filter: spawns bats on every button click (Vampire theme)."""

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        try:
            from PyQt6.QtWidgets import QAbstractButton
            from PyQt6.QtCore import QEvent as _QEv
            if (event.type() == _QEv.Type.MouseButtonRelease
                    and isinstance(obj, QAbstractButton)
                    and obj.isEnabled()
                    and hasattr(event, 'position')):
                win = obj.window()
                if win is not None:
                    pos = obj.mapTo(win, event.position().toPoint())
                    VampireBatLabel(win, pos)
        except Exception as _e:
            import logging as _log
            _log.getLogger(__name__).debug(f"VampireBatFilter: {_e}")
        return False


class OceanRippleLabel(QLabel):
    """Expanding concentric ring that simulates a water ripple on click (Ocean theme)."""

    CREATURES = [
        "🌊", "🐠", "🐡", "🦀", "🐙", "🪸", "🐚", "🦑", "🐟", "🦈",
        "🐬", "🐳", "🐋", "🦞", "🦐", "🦭", "🐊", "🌺", "🪼",
        "🦀🌊", "🐚✨", "🌊🐙", "🐡🪸", "🦑🌊",
    ]

    def __init__(self, parent: 'QWidget', pos: 'QPoint') -> None:
        super().__init__(parent)
        _r = _random
        self.setText(_r.choice(self.CREATURES))
        self.setStyleSheet(
            "QLabel { background: transparent; font-size: 24px; color: #00e5ff; "
            "border: none; padding: 0; }"
        )
        self.adjustSize()
        self.move(pos.x() - self.width() // 2,
                  pos.y() - self.height() // 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.show()
        self.raise_()

        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)

        self._fade = QPropertyAnimation(eff, b"opacity", self)
        self._fade.setDuration(900)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.finished.connect(self.deleteLater)

        start_geo = self.geometry()
        expand = 26
        end_geo = QRect(start_geo.x() - expand, start_geo.y() - expand,
                        start_geo.width() + expand * 2, start_geo.height() + expand * 2)
        self._expand = QPropertyAnimation(self, b"geometry", self)
        self._expand.setDuration(900)
        self._expand.setStartValue(start_geo)
        self._expand.setEndValue(end_geo)
        self._expand.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._fade.start()
        self._expand.start()


class OceanRippleFilter(QObject):
    """Application-wide event filter: shows a ripple on every button click (Ocean theme)."""

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        try:
            from PyQt6.QtWidgets import QAbstractButton
            from PyQt6.QtCore import QEvent as _QEv
            if (event.type() == _QEv.Type.MouseButtonRelease
                    and isinstance(obj, QAbstractButton)
                    and obj.isEnabled()
                    and hasattr(event, 'position')):
                win = obj.window()
                if win is not None:
                    pos = obj.mapTo(win, event.position().toPoint())
                    OceanRippleLabel(win, pos)
        except Exception as _e:
            import logging as _log
            _log.getLogger(__name__).debug(f"OceanRippleFilter: {_e}")
        return False


class GothSkullLabel(QLabel):
    """Floating skull that rises and fades on click (Goth theme)."""

    SKULLS = [
        "💀", "🖤💀", "💀🕸️", "☠️", "🕷️💀🕷️", "💀🌑", "🖤☠️🖤",
        "🦇💀", "💀🥀", "☠️🖤", "🕯️💀", "💀⛓️", "🕸️☠️🕸️",
        "👁️💀👁️", "💀🌹", "⛧💀⛧", "🖤🩸💀", "🌑☠️🌑",
    ]

    def __init__(self, parent: 'QWidget', pos: 'QPoint') -> None:
        super().__init__(parent)
        _r = _random
        self.setText(_r.choice(self.SKULLS))
        self.setStyleSheet(
            "QLabel { background: transparent; font-size: 20px; color: #9966bb; "
            "border: none; padding: 0; }"
        )
        self.adjustSize()
        dx = _r.randint(-12, 12)
        self.move(pos.x() - self.width() // 2 + dx,
                  pos.y() - self.height() // 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.show()
        self.raise_()

        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)

        self._fade = QPropertyAnimation(eff, b"opacity", self)
        self._fade.setDuration(1300)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.setEasingCurve(QEasingCurve.Type.InQuad)
        self._fade.finished.connect(self.deleteLater)

        start_geo = self.geometry()
        end_geo = QRect(start_geo.x() + _r.randint(-15, 15),
                        start_geo.y() - 70,
                        start_geo.width(), start_geo.height())
        self._rise = QPropertyAnimation(self, b"geometry", self)
        self._rise.setDuration(1300)
        self._rise.setStartValue(start_geo)
        self._rise.setEndValue(end_geo)
        self._rise.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._fade.start()
        self._rise.start()


class GothSkullFilter(QObject):
    """Application-wide event filter: spawns skulls on every button click (Goth theme)."""

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        try:
            from PyQt6.QtWidgets import QAbstractButton
            from PyQt6.QtCore import QEvent as _QEv
            if (event.type() == _QEv.Type.MouseButtonRelease
                    and isinstance(obj, QAbstractButton)
                    and obj.isEnabled()
                    and hasattr(event, 'position')):
                win = obj.window()
                if win is not None:
                    pos = obj.mapTo(win, event.position().toPoint())
                    GothSkullLabel(win, pos)
        except Exception as _e:
            import logging as _log
            _log.getLogger(__name__).debug(f"GothSkullFilter: {_e}")
        return False


class DraculaDropLabel(QLabel):
    """Blood drop that drips down and fades on click (Dracula theme)."""

    DROPS = [
        "🩸", "🧛", "🦇🩸", "🩸💜", "🧛‍♂️",
        "🦇", "🌑🩸", "💜🧛", "🩸🦇", "🧛‍♀️🩸",
        "🦇🦇", "🌑🧛🌑", "💀🩸", "🩸🌹",
    ]

    def __init__(self, parent: 'QWidget', pos: 'QPoint') -> None:
        super().__init__(parent)
        _r = _random
        self.setText(_r.choice(self.DROPS))
        self.setStyleSheet(
            "QLabel { background: transparent; font-size: 20px; color: #cc0033; "
            "border: none; padding: 0; }"
        )
        self.adjustSize()
        dx = _r.randint(-8, 8)
        self.move(pos.x() - self.width() // 2 + dx,
                  pos.y() - self.height() // 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.show()
        self.raise_()

        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)

        self._fade = QPropertyAnimation(eff, b"opacity", self)
        self._fade.setDuration(1000)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.setEasingCurve(QEasingCurve.Type.InQuad)
        self._fade.finished.connect(self.deleteLater)

        # Drip DOWN (like blood dripping)
        start_geo = self.geometry()
        end_geo = QRect(start_geo.x() + dx // 2,
                        start_geo.y() + 60,
                        start_geo.width(), start_geo.height())
        self._drip = QPropertyAnimation(self, b"geometry", self)
        self._drip.setDuration(1000)
        self._drip.setStartValue(start_geo)
        self._drip.setEndValue(end_geo)
        self._drip.setEasingCurve(QEasingCurve.Type.InQuad)

        self._fade.start()
        self._drip.start()


class DraculaDropFilter(QObject):
    """Application-wide event filter: spawns blood drops on button click (Dracula theme)."""

    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        try:
            from PyQt6.QtWidgets import QAbstractButton
            from PyQt6.QtCore import QEvent as _QEv
            if (event.type() == _QEv.Type.MouseButtonRelease
                    and isinstance(obj, QAbstractButton)
                    and obj.isEnabled()
                    and hasattr(event, 'position')):
                win = obj.window()
                if win is not None:
                    pos = obj.mapTo(win, event.position().toPoint())
                    DraculaDropLabel(win, pos)
        except Exception as _e:
            import logging as _log
            _log.getLogger(__name__).debug(f"DraculaDropFilter: {_e}")
        return False


# ── Ambient idle-theme decorator labels ───────────────────────────────────────
# These classes are spawned by a QTimer on the main window and drift across the
# window to add "ambient personality" to themed modes.  They are transparent to
# mouse events so they never interfere with UI interaction.

class OceanAmbientCreature(QLabel):
    """A sea creature that drifts from the left edge to the right across the window.

    Spawned periodically by the Ocean theme's ambient timer to give the UI a
    sense of a living underwater environment — fish, jellyfish, coral emojis
    wander across the lower third of the window.
    """

    _ICONS = ["🐠", "🐡", "🐟", "🐙", "🦑", "🦈", "🐬", "🪼", "🦀", "🦞",
              "🐚", "🪸", "🌊", "🐳", "🐋", "🦭", "🦐"]

    def __init__(self, parent: 'QWidget') -> None:
        super().__init__(parent)
        _r = _random
        self.setText(_r.choice(self._ICONS))
        self.setStyleSheet(
            "QLabel { background: transparent; font-size: 22px; color: #00e5ff;"
            " border: none; padding: 0; }"
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.adjustSize()

        pw, ph = parent.width(), parent.height()
        # Spawn in the lower 45% of the window (y_ratio=0.55 → lower 45%)
        # so creatures swim near the ocean floor without blocking the UI header.
        _OCEAN_Y_MIN_RATIO = 0.55
        y_min = int(ph * _OCEAN_Y_MIN_RATIO)
        y_max = max(y_min + 20, ph - self.height() - 10)
        start_y = _r.randint(y_min, y_max)
        self.move(-self.width() - 10, start_y)
        self.show()
        self.raise_()

        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QPoint
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)

        # Fade: in → hold → out
        self._fade_in = QPropertyAnimation(eff, b"opacity", self)
        self._fade_in.setDuration(600)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(0.75)
        self._fade_in.setEasingCurve(QEasingCurve.Type.InQuad)

        duration = _r.randint(4500, 7000)
        self._drift = QPropertyAnimation(self, b"geometry", self)
        self._drift.setDuration(duration)
        self._drift.setStartValue(QRect(-self.width() - 10, start_y, self.width(), self.height()))
        self._drift.setEndValue(QRect(pw + 20, start_y + _r.randint(-30, 30),
                                      self.width(), self.height()))
        self._drift.setEasingCurve(QEasingCurve.Type.Linear)
        self._drift.finished.connect(self.deleteLater)

        self._fade_in.start()
        self._drift.start()


class GothAmbientSpider(QLabel):
    """A spider/skull that descends from the top of the window on a web thread.

    Appears in the Goth theme to add an ambient creepy feeling. Spawns at a
    random x position, drops down, sways, then retracts back up and vanishes.
    """

    _ICONS = ["🕷️", "💀", "🕸️", "🦇", "🌑", "💀🕷️", "🕷️🕸️", "💀💜"]

    def __init__(self, parent: 'QWidget') -> None:
        super().__init__(parent)
        _r = _random
        self.setText(_r.choice(self._ICONS))
        self.setStyleSheet(
            "QLabel { background: transparent; font-size: 20px; color: #9966bb;"
            " border: none; padding: 0; }"
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.adjustSize()

        pw = parent.width()
        x = _r.randint(30, max(31, pw - 50))
        # Drop between 8% and 35% of window height — enough to be visible
        # without permanently obscuring the tool controls.
        _SPIDER_DROP_MIN_RATIO = 0.08
        _SPIDER_DROP_MAX_RATIO = 0.35
        drop_depth = _r.randint(int(parent.height() * _SPIDER_DROP_MIN_RATIO),
                                int(parent.height() * _SPIDER_DROP_MAX_RATIO))

        self.move(x, -self.height() - 5)
        self.show()
        self.raise_()

        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        eff.setOpacity(0.85)

        hang_ms = _r.randint(1200, 2500)
        # Drop down
        self._drop = QPropertyAnimation(self, b"geometry", self)
        self._drop.setDuration(1800)
        self._drop.setStartValue(QRect(x, -self.height() - 5, self.width(), self.height()))
        self._drop.setEndValue(QRect(x, drop_depth, self.width(), self.height()))
        self._drop.setEasingCurve(QEasingCurve.Type.OutBounce)

        # Retract back up after hanging
        self._retract = QPropertyAnimation(self, b"geometry", self)
        self._retract.setDuration(1400)
        self._retract.setStartValue(QRect(x, drop_depth, self.width(), self.height()))
        self._retract.setEndValue(QRect(x, -self.height() - 5, self.width(), self.height()))
        self._retract.setEasingCurve(QEasingCurve.Type.InQuad)
        self._retract.finished.connect(self.deleteLater)

        def _start_retract():
            try:
                self._retract.start()
            except RuntimeError:
                pass

        from PyQt6.QtCore import QTimer as _QT
        self._hang_timer = _QT(self)
        self._hang_timer.setSingleShot(True)
        self._hang_timer.timeout.connect(_start_retract)

        self._drop.finished.connect(lambda: self._hang_timer.start(hang_ms))
        self._drop.start()


class DraculaAmbientBat(QLabel):
    """A bat that swoops across the top of the window in the Dracula theme.

    Adds ambient personality: dark silhouette bats fly from right to left
    near the top of the window, reinforcing the nocturnal Dracula atmosphere.
    """

    _ICONS = ["🦇", "🧛🦇", "🦇🌑", "🌑🦇", "🦇💜", "🧛‍♂️", "🦇🦇"]

    def __init__(self, parent: 'QWidget') -> None:
        super().__init__(parent)
        _r = _random
        self.setText(_r.choice(self._ICONS))
        self.setStyleSheet(
            "QLabel { background: transparent; font-size: 20px; color: #cc0033;"
            " border: none; padding: 0; }"
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.adjustSize()

        pw, ph = parent.width(), parent.height()
        # Bats fly in the top 22% of the window — above the tab bar area.
        _BAT_Y_MAX_RATIO = 0.22
        y = _r.randint(10, max(11, int(ph * _BAT_Y_MAX_RATIO)))
        # Start at the right edge, fly left
        self.move(pw + self.width() + 10, y)
        self.show()
        self.raise_()

        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)

        self._fade_in = QPropertyAnimation(eff, b"opacity", self)
        self._fade_in.setDuration(500)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(0.8)
        self._fade_in.setEasingCurve(QEasingCurve.Type.InQuad)

        duration = _r.randint(3500, 5500)
        end_y = y + _r.randint(-20, 20)
        self._swoop = QPropertyAnimation(self, b"geometry", self)
        self._swoop.setDuration(duration)
        self._swoop.setStartValue(QRect(pw + self.width() + 10, y,
                                        self.width(), self.height()))
        self._swoop.setEndValue(QRect(-self.width() - 20, end_y,
                                      self.width(), self.height()))
        self._swoop.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._swoop.finished.connect(self.deleteLater)

        self._fade_in.start()
        self._swoop.start()


class WorkerThread(QThread):
    """Background worker thread for long-running operations."""

    progress = pyqtSignal(int, int, str)  # current, total, message
    finished = pyqtSignal(bool, str)  # success, message
    log = pyqtSignal(str)  # log message
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self.cancelled = False
    
    def run(self):
        """Execute the task."""
        try:
            result = self.task_func(*self.args, **self.kwargs, 
                                   progress_callback=self.progress.emit,
                                   log_callback=self.log.emit,
                                   check_cancelled=lambda: self.cancelled)
            if not self.cancelled:
                self.finished.emit(True, "Operation completed successfully")
        except Exception as e:
            logger.error(f"Worker thread error: {e}", exc_info=True)
            self.finished.emit(False, f"Error: {str(e)}")
    
    def cancel(self):
        """Cancel the operation."""
        self.cancelled = True


class TextureSorterMainWindow(QMainWindow):
    """
    Main application window for Panda Sorter Converter Upscaler.
    Pure Qt6 implementation - no tkinter, no canvas.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.classifier = None
        self.lod_detector = None
        self.file_handler = None
        self.database = None
        self.organizer = None
        
        # Performance and resource managers
        self.performance_manager = None
        self.threading_manager = None
        self.cache_manager = None
        self.memory_manager = None
        self.hotkey_manager = None
        self.sound_manager = None

        # Gamification systems (initialised in create_panda_features_tab / initialize_components)
        self.achievement_system = None
        self.currency_system = None
        self.shop_system = None
        self.panda_closet = None
        # Bedroom + inventory panel refs (set in create_panda_features_tab)
        self._bedroom_widget = None   # PandaBedroomGL instance
        self._world_widget   = None   # PandaWorldWidget instance (lazy-created)
        self._otter_shop_panel = None  # ShopPanelQt — cached (Livy's shop)
        self._panda_tabs = None       # inner QTabWidget for panda features
        self._inventory_panel = None  # InventoryPanelQt instance
        self._widgets_panel = None    # WidgetsPanelQt instance (shown via backpack)
        self._closet_panel = None     # ClosetDisplayWidget instance (kept for grid refresh)
        self._home_tab_index = -1     # index of the "🏠 Panda Home" tab
        self._home_stack = None       # QStackedWidget: page 0=bedroom, page 1=sub-panel
        self._home_tab_widget = None  # QWidget wrapper that owns the stack
        self._home_back_btn = None    # QPushButton "← Back to Home"
        self._home_sub_label = None   # QLabel showing current sub-panel title
        self._home_back_bar = None    # QWidget back-button toolbar (shown in sub-panels)
        self._home_stack_owned = []   # list of widgets we created for page-1 (safe to delete)
        self._coin_label = None         # QLabel showing current coin balance (set in setup_statusbar)
        self._panda_mood_label = None   # QLabel showing panda mood (set in setup_statusbar)
        self._achievement_panel = None  # AchievementDisplayWidget ref (for refresh on unlock)
        self._achievement_tab_index = -1  # panda_tabs index for the Achievements tab
        self._backpack_merged_panel = None  # Merged Inventory+Widgets QTabWidget (built once)
        self._park_panel = None         # MinigamePanelQt — cached (park destination)
        self._dungeon_3d_panel = None   # Dungeon3DWidget — cached (dungeon destination)
        self.level_system = None        # UserLevelSystem – XP / levelling
        self.auto_backup = None         # AutoBackupSystem – periodic state backup
        self.unlockables_system = None  # UnlockablesSystem – cursors/themes/outfits
        self.quest_system = None        # QuestSystem – quests / easter eggs
        self.integrated_dungeon = None  # IntegratedDungeon – adventure mode
        self.enemy_manager = None       # EnemyManager – enemy spawning

        # UI sub-components declared here so setup_ui() can reference them safely
        self.panda_widget = None        # PandaOpenGLWidget (3-D panda sidebar)
        self.panda_overlay = None       # TransparentPandaOverlay (floating panda over UI)
        self.perf_dashboard = None      # PerformanceDashboard dock panel
        self.tool_panels = {}           # {panel_id: widget}
        self.tool_dock_widgets = {}     # {panel_id: QDockWidget}
        self.tool_tabs_widget = None    # QTabWidget inside the Tools tab
        self._last_sorted_count = 0     # files moved in last sort (for achievements)
        self._sort_style_key = None     # organisation style key captured before worker starts
        self.view_menu = None           # Set by setup_menubar(); guarded in _update_tool_panels_menu
        self.file_browser_panel = None  # FileBrowserPanelQt tab widget
        self.live_preview_widget = None # LivePreviewWidget side-pane in file browser tab
        self.notepad_panel = None       # NotepadPanelQt tab widget
        self.processing_queue_panel = None  # ProcessingQueueQt archive dock

        # Worker thread
        self.worker = None
        self._ai_training_thread = None     # background PyTorchTrainer QThread (prevent GC)
        self._gore_splatter_filter = None   # GoreSplatterFilter instance (Gore theme only)
        self._vampire_bat_filter = None     # VampireBatFilter instance (Vampire theme only)
        self._ocean_ripple_filter = None    # OceanRippleFilter instance (Ocean theme only)
        self._goth_skull_filter = None      # GothSkullFilter instance (Goth theme only)
        self._dracula_drop_filter = None    # DraculaDropFilter instance (Dracula theme only)
        # Ambient idle-animation timers (fire periodically to spawn drifting decorators)
        self._ocean_ambient_timer = None    # QTimer — drifts sea creatures across the window
        self._goth_ambient_timer  = None    # QTimer — drops a spider or skull at random
        self._dracula_ambient_timer = None  # QTimer — flies a bat across the window top
        
        # Drag-drop, translation, environment monitor
        self.drag_drop_handler = None
        self.translation_manager = None
        self.environment_monitor = None

        # Analytics / data systems
        self.statistics_tracker = None   # StatisticsTracker – per-op ETA/throughput
        self.search_filter = None        # SearchFilter – file search with presets
        self.profile_manager = None      # ProfileManager – org profile load/save
        self.backup_manager = None       # BackupManager – manual restore-point backups
        self.game_identifier = None      # GameIdentifier – CRC/serial game detection
        self.lod_replacer = None         # LODReplacer – LOD group scanner/replacer
        self.batch_queue = None          # BatchQueue – priority operation queue
        self.panda_character = None      # PandaCharacter – panda personality/animations
        self.panda_stats = None          # PandaStats – panda happiness/hunger/energy
        self.panda_mood_system = None    # PandaMoodSystem – mood-based behaviour
        self.skill_tree = None           # SkillTree – RPG skill progression
        self.travel_system = None        # TravelSystem – location/dungeon navigation
        self.adventure_level = None      # AdventureLevel – combat XP tracking
        self.weapon_collection = None    # WeaponCollection – panda weapons
        self.texture_analyzer = None     # TextureAnalyzer – per-file advanced analysis
        self.similarity_search = None    # SimilaritySearch – embedding-based search
        self.duplicate_detector = None   # DuplicateDetector – find near-duplicate textures
        self.widget_detector = None      # WidgetDetector – Qt hit-testing for panda overlay
        self.panda_interaction = None    # PandaInteractionBehavior – mischievous AI
        self.preview_viewer = None       # PreviewViewer – standalone non-blocking preview
        self._tutorial_manager = None   # TutorialManager – set in main() for crash recovery check

        # Paths
        self.input_path = None
        self.output_path = None
        # Path display labels — created as hidden stubs here so browse_input /
        # browse_output can always call .setText() safely.  The home tab also
        # embeds them in a visible Folder Picker section.
        self.input_path_label = QLabel("(none)")
        self.output_path_label = QLabel("(none)")
        
        # Tooltip manager (will be initialized later)
        self.tooltip_manager = None
        self.log_text = None           # QTextEdit for activity log (created in create_tools_tab)
        self._cursor_trail_overlay = None  # CursorTrailOverlay — installed when cursor trail enabled

        # Persistent data paths (stored once; reused in initialize_components and closeEvent)
        _app_data = Path(__file__).parent / 'app_data'
        self._app_data_dir = _app_data               # base dir for all app data files
        self._db_path = _app_data / 'textures.db'    # SQLite texture index
        self._adventure_level_path = _app_data / 'adventure_level.json'
        self._weapon_collection_path = _app_data / 'weapons.json'
        self._skill_tree_path = _app_data / 'skill_tree.json'
        self._closet_path = _app_data / 'panda_closet.json'   # closet persistence
        
        # Docking system - track floating panels
        self.docked_widgets = {}  # {tab_name: QDockWidget}
        self.tab_widgets = {}  # {tab_name: widget} - original tab widgets
        self._restoring_docks: set = set()  # re-entrancy guard for restore_docked_tab
        
        # Setup UI
        self.setup_ui()
        self.setup_menubar()
        self.setup_statusbar()
        self.apply_theme()
        
        # Initialize components
        self.initialize_components()

        # Start panda interaction behavior tick (33 ms ≈ 30 Hz)
        # Must run AFTER initialize_components so self.panda_interaction is set.
        self._panda_interaction_timer = QTimer(self)
        self._panda_interaction_timer.setInterval(int(self._INTERACTION_TICK_DT * 1000))
        self._panda_interaction_timer.timeout.connect(self._tick_panda_interaction)
        self._panda_interaction_timer.start()

        # Session-hour coin reward — fires every 60 minutes of active use
        _SESSION_HOUR_MS = 3_600_000  # 60 min × 60 s × 1000 ms
        self._session_hour_timer = QTimer(self)
        self._session_hour_timer.setInterval(_SESSION_HOUR_MS)
        self._session_hour_timer.timeout.connect(self._on_session_hour)
        self._session_hour_timer.start()

        # Apply performance settings from config
        self.apply_performance_settings()

        # Refresh coin display now that currency_system has been initialized
        QTimer.singleShot(200, self._update_coin_display)
        
        # Restore dock layout from previous session
        QTimer.singleShot(100, self.restore_dock_layout)  # Delay to ensure widgets are created
        
        logger.info("Qt Main Window initialized successfully")
    
    def setup_ui(self):
        """Setup the main UI layout."""
        self.setWindowTitle(f"🐼 {APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(900, 650)
        # Enable file drag-and-drop across the whole window
        self.setAcceptDrops(True)
        # Install app-level event filter to detect button hover → panda peeks/pokes
        try:
            QApplication.instance().installEventFilter(self)
        except Exception:
            pass
        # Set window icon
        icon_path = Path(__file__).parent / 'assets' / 'icon.ico'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            logger.info(f"Window icon set from: {icon_path}")
        else:
            # Try PNG icon as fallback
            icon_path = Path(__file__).parent / 'assets' / 'icon.png'
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
                logger.info(f"Window icon set from PNG: {icon_path}")
            else:
                logger.warning("Window icon file not found")
        
        # Central widget with splitter for panda
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create splitter: main content | panda widget
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)  # Prevent panels from being completely collapsed
        main_layout.addWidget(splitter)
        
        # Left side: Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        
        # ── Panda overlay widget ─────────────────────────────────────────────────
        # Try OpenGL 3-D widget first; fall back to 2-D QPainter widget.
        # IMPORTANT: create panda_widget HERE — before create_panda_features_tab()
        # so that panda_char is available when the Customisation tab is built.
        # The widget is created with parent=self so it can be shown as a
        # full-window transparent overlay over the application content.
        # Only ONE panda widget is ever active (GL preferred, 2D fallback).

        if PANDA_WIDGET_AVAILABLE:
            try:
                self.panda_widget = PandaOpenGLWidget(parent=self)
                # No min/max width — this widget is a full-window overlay, not a sidebar panel
                self.panda_widget.clicked.connect(self.on_panda_clicked)
                self.panda_widget.mood_changed.connect(self.on_panda_mood_changed)
                self.panda_widget.animation_changed.connect(self.on_panda_animation_changed)
                if hasattr(self.panda_widget, 'food_eaten'):
                    self.panda_widget.food_eaten.connect(self._on_panda_food_eaten)
                # Wire gl_failed so we can swap in the 2D widget if initializeGL fails
                if hasattr(self.panda_widget, 'gl_failed'):
                    self.panda_widget.gl_failed.connect(self._on_panda_gl_failed)
                logger.info("✅ Panda 3D OpenGL widget created")
                # Restore appearance if closet already loaded (deferred single-shot so
                # the GL context is ready before colour calls reach the GPU)
                from PyQt6.QtCore import QTimer as _QT
                _QT.singleShot(200, self._restore_panda_appearance_from_closet)
            except Exception as e:
                logger.warning(f"OpenGL panda failed ({e}), trying 2D fallback")
                self.panda_widget = None

        if self.panda_widget is None and PandaWidget2D is not None:
            try:
                self.panda_widget = PandaWidget2D(parent=self)
                # No min/max width — full-window overlay, not a sidebar panel
                self.panda_widget.clicked.connect(self.on_panda_clicked)
                self.panda_widget.mood_changed.connect(self.on_panda_mood_changed)
                self.panda_widget.animation_changed.connect(self.on_panda_animation_changed)
                if hasattr(self.panda_widget, 'food_eaten'):
                    self.panda_widget.food_eaten.connect(self._on_panda_food_eaten)
                logger.info("✅ Panda 2D QPainter widget created (OpenGL unavailable)")
            except Exception as e2:
                logger.error(f"Panda 2D fallback also failed: {e2}")
                self.panda_widget = None

        # Create draggable tabs
        self.tabs = DraggableTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tab_detached.connect(self.on_tab_detached)
        # Hide the panda overlay when switching away from the Home tab so it
        # never blocks functional UI on the Tools, Panda, or Settings tabs.
        self.tabs.currentChanged.connect(self._on_main_tab_changed)
        content_layout.addWidget(self.tabs)

        # Create main tab (dashboard/welcome)
        try:
            self.create_main_tab()
            logger.info("✅ Main (Home) tab added")
        except Exception as e:
            logger.error(f"Could not create Home tab: {e}", exc_info=True)

        # Create tools tab — creates sub-tabs for all tools and adds itself to self.tabs
        try:
            self.create_tools_tab()
            logger.info("✅ Tools tab added to main tabs")
        except Exception as e:
            logger.error(f"Could not create Tools tab: {e}", exc_info=True)

        # Create Panda Features tab — panda_widget is now set (or None) so panda_char
        # is available to CustomizationPanelQt when it is built.
        try:
            panda_features_tab = self.create_panda_features_tab()
            self.tabs.addTab(panda_features_tab, "🐼 Panda")
            logger.info("✅ Panda Features tab added to main tabs")
        except Exception as e:
            logger.error(f"Could not create Panda Features tab: {e}", exc_info=True)

        # File Browser and Notepad are now inside the Tools tab grid.

        # Create settings tab
        try:
            self.create_settings_tab()
            logger.info("✅ Settings tab added")
        except Exception as e:
            logger.error(f"Could not create Settings tab: {e}", exc_info=True)

        # Progress bar (at bottom of content)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        content_layout.addWidget(self.progress_bar)

        splitter.addWidget(content_widget)
        # panda_widget is kept as a state-management reference (mood, animations,
        # PandaCharacter) but is NOT added to the splitter/UI — the transparent
        # overlay panda (panda_overlay) is the only visible panda in the window.
    
    def create_main_tab(self):
        """Create the main tab with welcome/dashboard and quick-launch buttons."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # Welcome message — use APP_NAME from config so it stays in sync
        welcome_label = QLabel(f"🐼 {APP_NAME}")
        welcome_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)

        layout.addSpacing(10)

        subtitle = QLabel("Your all-in-one toolkit: organise, upscale, remove backgrounds, create line art, convert formats and more.")
        subtitle.setStyleSheet("font-size: 11pt; color: #aaaaaa;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Quick-launch section header
        ql_header = QLabel("⚡ Quick Launch")
        ql_header.setStyleSheet("font-size: 14pt; font-weight: bold; color: #dddddd;")
        ql_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ql_header)

        layout.addSpacing(8)

        # Quick-launch buttons grid — each navigates directly to the tool's sub-tab
        # via switch_tool(tool_id).  Layout: 4 columns x 3 rows.
        _QUICK_TOOLS = [
            ("📁 Organizer",         "organizer"),
            ("🎭 Background Remover","bg_remover"),
            ("✨ Alpha Fixer",        "alpha_fixer"),
            ("🎨 Color Correction",  "color"),
            ("⚙️ Batch Normalizer",  "normalizer"),
            ("✓ Quality Checker",   "quality"),
            ("🔍 Image Upscaler",   "upscaler"),
            ("✏️ Line Art",          "lineart"),
            ("🔄 Format Converter",  "converter"),
            ("📝 Batch Rename",     "rename"),
            ("🔧 Image Repair",     "repair"),
            ("🏠 Panda Home",       "panda_home"),
        ]
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(8)
        cols = 4
        for i, (label, tool_id) in enumerate(_QUICK_TOOLS):
            btn = QPushButton(label)
            btn.setMinimumHeight(40)
            btn.setStyleSheet(
                "QPushButton { font-size: 10pt; border-radius: 6px; "
                "background-color: #3a3a3a; color: #eeeeee; } "
                "QPushButton:hover { background-color: #4a90d9; } "
                "QPushButton:pressed { background-color: #2a70b9; }"
            )
            # Use default argument capture to avoid late-binding closure bug
            btn.clicked.connect(lambda _checked=False, tid=tool_id: self.switch_tool(tid))
            grid.addWidget(btn, i // cols, i % cols)
        layout.addWidget(grid_widget)

        layout.addSpacing(10)

        # ── Folder Picker section ────────────────────────────────────────────
        # The browse_input / browse_output methods need self.input_path_label and
        # self.output_path_label to call .setText().  We assign them here so the
        # labels shown on the home tab ARE those same objects.
        folder_group = QGroupBox("📂 Folder Selection")
        folder_group.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #aaaaaa; font-size: 11pt; "
            "border: 1px solid #333; border-radius: 6px; margin-top: 6px; padding: 6px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )
        folder_grid = QGridLayout(folder_group)
        folder_grid.setSpacing(6)

        # Input folder row
        folder_grid.addWidget(QLabel("📁 Input:"), 0, 0)
        self.input_path_label.setStyleSheet(
            "color: #aaaaaa; font-style: italic; padding: 4px 6px; "
            "background: #1e1e2e; border: 1px solid #444; border-radius: 4px;"
        )
        self.input_path_label.setMinimumWidth(200)
        folder_grid.addWidget(self.input_path_label, 0, 1)
        input_browse_btn = QPushButton("Browse…")
        input_browse_btn.setFixedWidth(90)
        input_browse_btn.clicked.connect(self.browse_input)
        folder_grid.addWidget(input_browse_btn, 0, 2)

        # Output folder row
        folder_grid.addWidget(QLabel("📂 Output:"), 1, 0)
        self.output_path_label.setStyleSheet(
            "color: #aaaaaa; font-style: italic; padding: 4px 6px; "
            "background: #1e1e2e; border: 1px solid #444; border-radius: 4px;"
        )
        self.output_path_label.setMinimumWidth(200)
        folder_grid.addWidget(self.output_path_label, 1, 1)
        output_browse_btn = QPushButton("Browse…")
        output_browse_btn.setFixedWidth(90)
        output_browse_btn.clicked.connect(self.browse_output)
        folder_grid.addWidget(output_browse_btn, 1, 2)

        folder_grid.setColumnStretch(1, 1)
        layout.addWidget(folder_group)

        layout.addSpacing(6)
        from PyQt6.QtWidgets import QTextEdit as _QTE, QSplitter as _QSpl
        log_group = QGroupBox("📋 Activity Log")
        log_group.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #aaaaaa; font-size: 11pt; "
            "border: 1px solid #333; border-radius: 6px; margin-top: 6px; padding: 6px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
        )
        log_vbox = QVBoxLayout(log_group)
        log_vbox.setContentsMargins(6, 8, 6, 6)
        log_vbox.setSpacing(4)

        self.log_text = _QTE()
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("homeActivityLog")
        self.log_text.setFixedHeight(140)
        self.log_text.setStyleSheet(
            "QTextEdit#homeActivityLog { "
            "background: #0d0d1a; color: #aaffaa; "
            "font-family: 'Consolas','Courier New',monospace; font-size: 10px; "
            "border: none; border-radius: 3px; }"
        )
        clear_log_btn = QPushButton("🗑 Clear")
        clear_log_btn.setMinimumWidth(90)
        clear_log_btn.setFixedHeight(22)
        clear_log_btn.setStyleSheet(
            "QPushButton { background:#2a2a3e; color:#888; border:1px solid #444; "
            "border-radius:3px; font-size:10px; } "
            "QPushButton:hover { background:#3a3a5e; color:#fff; }"
        )
        clear_log_btn.clicked.connect(self.log_text.clear)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(clear_log_btn)
        log_vbox.addWidget(self.log_text)
        log_vbox.addLayout(btn_row)
        layout.addWidget(log_group)

        info_label = QLabel(f"Version: {APP_VERSION}")
        info_label.setStyleSheet("color: gray; font-size: 10pt; margin-top: 4px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        self.tabs.addTab(tab, "🏠 Home")

    def create_tools_tab(self):
        """Create the Tools tab: a QTabWidget with one sub-tab per tool."""
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ── Button grid (3 columns, all tools visible at once) ──────────────
        from PyQt6.QtWidgets import QGridLayout, QScrollArea as _SA
        btn_container = QWidget()
        btn_container.setObjectName("toolBtnContainer")
        btn_container.setStyleSheet(
            "#toolBtnContainer { background: #1a1a2a; border-bottom: 1px solid #333; }"
        )
        btn_grid = QGridLayout(btn_container)
        btn_grid.setContentsMargins(8, 6, 8, 6)
        btn_grid.setSpacing(4)

        # QStackedWidget holds the actual panels
        tool_stack = QStackedWidget()

        self.tool_tabs_widget = tool_stack   # switch_tool() uses this
        self._tool_btn_group: list = []       # (tool_id, QPushButton)

        def _select_tool(idx: int, tool_id: str):
            tool_stack.setCurrentIndex(idx)
            for _tid, _btn in self._tool_btn_group:
                _btn.setChecked(_tid == tool_id)

        # Tools — each panel is guarded individually so one failure
        #    does NOT prevent the other tools from loading.
        tool_tab_defs = []  # (panel_instance, label, tool_id) triples

        def _make_error_label(cls_name: str, err) -> 'QLabel':
            """Create a visible placeholder tab when a panel fails to load."""
            if err is None:
                msg = (
                    f"<b>⚠️ {cls_name} failed to import.</b><br><br>"
                    "This panel's module could not be loaded. Check "
                    "<b>app_data/logs/app.log</b> for the exact error."
                )
            else:
                msg = (
                    f"<b>⚠️ {cls_name} could not be loaded.</b><br><br>"
                    f"<code style='color:#ff6666'>{type(err).__name__}: {err}</code><br><br>"
                    "Check <b>app_data/logs/app.log</b> for details."
                )
            lbl = QLabel(msg)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.TextFormat.RichText)
            return lbl

        if BackgroundRemoverPanelQt is not None:
            try:
                bg_panel = BackgroundRemoverPanelQt(tooltip_manager=self.tooltip_manager)
                bg_panel.processing_complete.connect(
                    lambda: self.statusBar().showMessage("🎭 Background removal complete", 4000))
                bg_panel.image_loaded.connect(
                    lambda p: self.statusBar().showMessage(f"🎭 Loaded: {p}", 3000))
                tool_tab_defs.append((bg_panel, "🎭 Background Remover", 'bg_remover'))
            except Exception as _e:
                logger.warning(f"BackgroundRemoverPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('BackgroundRemoverPanelQt', _e), "🎭 Background Remover", 'bg_remover'))
        else:
            tool_tab_defs.append((_make_error_label('BackgroundRemoverPanelQt', None), "🎭 Background Remover", 'bg_remover'))

        if AlphaFixerPanelQt is not None:
            try:
                alpha_panel = AlphaFixerPanelQt(tooltip_manager=self.tooltip_manager)
                alpha_panel.finished.connect(lambda ok, msg, cnt, _tid='alpha_fixer': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Alpha Fixer: {msg}", 4000),
                    self._on_tool_finished(ok, _tid, cnt if ok else 0),
                    self.operation_finished(ok, msg, cnt) if ok and cnt > 0 else None,
                ))
                tool_tab_defs.append((alpha_panel, "✨ Alpha Fixer", 'alpha_fixer'))
            except Exception as _e:
                logger.warning(f"AlphaFixerPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('AlphaFixerPanelQt', _e), "✨ Alpha Fixer", 'alpha_fixer'))
        else:
            tool_tab_defs.append((_make_error_label('AlphaFixerPanelQt', None), "✨ Alpha Fixer", 'alpha_fixer'))

        if ColorCorrectionPanelQt is not None:
            try:
                color_panel = ColorCorrectionPanelQt(tooltip_manager=self.tooltip_manager)
                color_panel.finished.connect(lambda ok, msg, cnt, _tid='color': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Color Correction: {msg}", 4000),
                    self._on_tool_finished(ok, _tid, cnt if ok else 0),
                    self.operation_finished(ok, msg, cnt) if ok and cnt > 0 else None,
                ))
                tool_tab_defs.append((color_panel, "🎨 Color Correction", 'color'))
            except Exception as _e:
                logger.warning(f"ColorCorrectionPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('ColorCorrectionPanelQt', _e), "🎨 Color Correction", 'color'))
        else:
            tool_tab_defs.append((_make_error_label('ColorCorrectionPanelQt', None), "🎨 Color Correction", 'color'))

        if BatchNormalizerPanelQt is not None:
            try:
                norm_panel = BatchNormalizerPanelQt(tooltip_manager=self.tooltip_manager)
                norm_panel.finished.connect(lambda ok, msg, cnt, _tid='normalizer': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Batch Normalizer: {msg}", 4000),
                    self._on_tool_finished(ok, _tid, cnt if ok else 0),
                    self.operation_finished(ok, msg, cnt) if ok and cnt > 0 else None,
                ))
                tool_tab_defs.append((norm_panel, "⚙️ Batch Normalizer", 'normalizer'))
            except Exception as _e:
                logger.warning(f"BatchNormalizerPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('BatchNormalizerPanelQt', _e), "⚙️ Batch Normalizer", 'normalizer'))
        else:
            tool_tab_defs.append((_make_error_label('BatchNormalizerPanelQt', None), "⚙️ Batch Normalizer", 'normalizer'))

        if QualityCheckerPanelQt is not None:
            try:
                quality_panel = QualityCheckerPanelQt(tooltip_manager=self.tooltip_manager)
                quality_panel.finished.connect(lambda ok, msg, _tid='quality': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Quality Check: {msg}", 4000),
                    self._on_tool_finished(ok, _tid),
                ))
                tool_tab_defs.append((quality_panel, "✓ Quality Checker", 'quality'))
            except Exception as _e:
                logger.warning(f"QualityCheckerPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('QualityCheckerPanelQt', _e), "✓ Quality Checker", 'quality'))
        else:
            tool_tab_defs.append((_make_error_label('QualityCheckerPanelQt', None), "✓ Quality Checker", 'quality'))

        if ImageUpscalerPanelQt is not None:
            try:
                upscaler_panel = ImageUpscalerPanelQt(tooltip_manager=self.tooltip_manager)
                upscaler_panel.error.connect(
                    lambda msg: self.statusBar().showMessage(f"❌ Upscaler: {msg}", 5000))
                upscaler_panel.finished.connect(lambda ok, msg, cnt, _tid='upscaler': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Upscaler: {msg}", 4000),
                    self._on_tool_finished(ok, _tid, cnt if ok else 0),
                    self.operation_finished(ok, msg, cnt) if ok and cnt > 0 else None,
                ))
                tool_tab_defs.append((upscaler_panel, "🔍 Image Upscaler", 'upscaler'))
            except Exception as _e:
                logger.warning(f"ImageUpscalerPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('ImageUpscalerPanelQt', _e), "🔍 Image Upscaler", 'upscaler'))
        else:
            tool_tab_defs.append((_make_error_label('ImageUpscalerPanelQt', None), "🔍 Image Upscaler", 'upscaler'))

        if LineArtConverterPanelQt is not None:
            try:
                line_panel = LineArtConverterPanelQt(tooltip_manager=self.tooltip_manager)
                line_panel.error.connect(
                    lambda msg: self.statusBar().showMessage(f"❌ Line Art: {msg}", 5000))
                line_panel.finished.connect(lambda ok, msg, cnt, _tid='lineart': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Line Art: {msg}", 4000),
                    self._on_tool_finished(ok, _tid, cnt if ok else 0),
                    self.operation_finished(ok, msg, cnt) if ok and cnt > 0 else None,
                ))
                tool_tab_defs.append((line_panel, "✏️ Line Art", 'lineart'))
            except Exception as _e:
                logger.warning(f"LineArtConverterPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('LineArtConverterPanelQt', _e), "✏️ Line Art", 'lineart'))
        else:
            tool_tab_defs.append((_make_error_label('LineArtConverterPanelQt', None), "✏️ Line Art", 'lineart'))

        if BatchRenamePanelQt is not None:
            try:
                rename_panel = BatchRenamePanelQt(tooltip_manager=self.tooltip_manager)
                rename_panel.finished.connect(lambda ok, errs, _tid='rename': (
                    self.statusBar().showMessage(
                        f"📝 Renamed {ok} files" + (f" ({len(errs)} errors)" if errs else ""), 4000),
                    self._on_tool_finished(bool(ok), _tid, ok),
                    self.operation_finished(bool(ok), f"Renamed {ok} files", ok) if ok > 0 else None,
                ))
                tool_tab_defs.append((rename_panel, "📝 Batch Rename", 'rename'))
            except Exception as _e:
                logger.warning(f"BatchRenamePanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('BatchRenamePanelQt', _e), "📝 Batch Rename", 'rename'))
        else:
            tool_tab_defs.append((_make_error_label('BatchRenamePanelQt', None), "📝 Batch Rename", 'rename'))

        if ImageRepairPanelQt is not None:
            try:
                repair_panel = ImageRepairPanelQt(tooltip_manager=self.tooltip_manager)
                repair_panel.error.connect(
                    lambda msg: self.statusBar().showMessage(f"❌ Image Repair: {msg}", 5000))
                repair_panel.finished.connect(lambda ok, msg, cnt, _tid='repair': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Image Repair: {msg}", 4000),
                    self._on_tool_finished(ok, _tid, cnt if ok else 0),
                    self.operation_finished(ok, msg, cnt) if ok and cnt > 0 else None,
                ))
                tool_tab_defs.append((repair_panel, "🔧 Image Repair", 'repair'))
            except Exception as _e:
                logger.warning(f"ImageRepairPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('ImageRepairPanelQt', _e), "🔧 Image Repair", 'repair'))
        else:
            tool_tab_defs.append((_make_error_label('ImageRepairPanelQt', None), "🔧 Image Repair", 'repair'))

        if FormatConverterPanelQt is not None:
            try:
                conv_panel = FormatConverterPanelQt(tooltip_manager=self.tooltip_manager)
                conv_panel.finished.connect(lambda ok, msg, cnt, _tid='converter': (
                    self.statusBar().showMessage(f"{'✅' if ok else '⚠️'} Converter: {msg} ({cnt} files)", 4000),
                    self._on_tool_finished(ok, _tid, cnt if ok else 0),
                    self.operation_finished(ok, msg, cnt) if ok and cnt > 0 else None,
                ))
                tool_tab_defs.append((conv_panel, "🔄 Format Converter", 'converter'))
            except Exception as _e:
                logger.warning(f"FormatConverterPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('FormatConverterPanelQt', _e), "🔄 Format Converter", 'converter'))
        else:
            tool_tab_defs.append((_make_error_label('FormatConverterPanelQt', None), "🔄 Format Converter", 'converter'))

        if OrganizerPanelQt is not None:
            try:
                organizer_panel = OrganizerPanelQt(tooltip_manager=self.tooltip_manager)
                organizer_panel.log.connect(lambda msg: self.log(msg))
                organizer_panel.finished.connect(lambda ok, msg, _stats, _tid='organizer': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Organizer: {msg}", 4000),
                    self._on_tool_finished(ok, _tid),
                    self.operation_finished(
                        ok, msg,
                        int(_stats.get('files_moved', _stats.get('files_processed', 0))),
                        float(_stats.get('elapsed_time', 0.0)),
                    ),
                ))
                tool_tab_defs.append((organizer_panel, "📁 Organizer", 'organizer'))
            except Exception as _e:
                logger.warning(f"OrganizerPanelQt unavailable: {_e}")
                tool_tab_defs.append((_make_error_label('OrganizerPanelQt', _e), "📁 Organizer", 'organizer'))
        else:
            tool_tab_defs.append((_make_error_label('OrganizerPanelQt', None), "📁 Organizer", 'organizer'))

        # ── File Browser and Notepad as tool entries ────────────────────────
        if FileBrowserPanelQt is not None:
            try:
                tooltip_manager = getattr(self, 'tooltip_manager', None)
                fb_panel = FileBrowserPanelQt(config, tooltip_manager)
                if hasattr(fb_panel, 'file_selected'):
                    fb_panel.file_selected.connect(self._on_file_browser_file_selected)
                if hasattr(fb_panel, 'folder_changed'):
                    fb_panel.folder_changed.connect(self._on_file_browser_folder_changed)
                self.file_browser_panel = fb_panel
                tool_tab_defs.append((fb_panel, "📁 File Browser", 'file_browser'))
            except Exception as _e:
                tool_tab_defs.append((_make_error_label('FileBrowserPanelQt', _e), "📁 File Browser", 'file_browser'))
        else:
            tool_tab_defs.append((_make_error_label('FileBrowserPanelQt', None), "📁 File Browser", 'file_browser'))

        if NotepadPanelQt is not None:
            try:
                tooltip_manager = getattr(self, 'tooltip_manager', None)
                np_panel = NotepadPanelQt(config, tooltip_manager)
                self.notepad_panel = np_panel
                tool_tab_defs.append((np_panel, "📝 Notepad", 'notepad'))
            except Exception as _e:
                tool_tab_defs.append((_make_error_label('NotepadPanelQt', _e), "📝 Notepad", 'notepad'))
        else:
            tool_tab_defs.append((_make_error_label('NotepadPanelQt', None), "📝 Notepad", 'notepad'))

        # ── Activity Log panel ───────────────────────────────────────────────
        # Shares the same QTextDocument as the home-page log so both panels
        # show identical live content without reparenting the original widget.
        from PyQt6.QtWidgets import QTextEdit as _QTE
        _log_container = QWidget()
        _log_vbox = QVBoxLayout(_log_container)
        _log_vbox.setContentsMargins(8, 8, 8, 8)
        _log_vbox.setSpacing(4)
        _log_header = QLabel("📋 Activity Log")
        _log_header.setStyleSheet("font-weight:bold; font-size:13px; color:#cccccc;")
        _log_vbox.addWidget(_log_header)
        _tools_log = _QTE()
        _tools_log.setReadOnly(True)
        _tools_log.setObjectName("toolsActivityLog")
        _tools_log.setStyleSheet(
            "QTextEdit#toolsActivityLog { background:#0d0d1a; color:#aaffaa; "
            "font-family:'Consolas','Courier New',monospace; font-size:11px; "
            "border:1px solid #333; border-radius:4px; }"
        )
        # Share document with the home-page log_text so content is identical
        if self.log_text is not None:
            _tools_log.setDocument(self.log_text.document())
        _clear_btn = QPushButton("🗑 Clear Log")
        _clear_btn.setFixedHeight(26)
        _clear_btn.setStyleSheet(
            "QPushButton { background:#2a2a3e; color:#aaaaaa; border:1px solid #444; "
            "border-radius:3px; font-size:11px; } "
            "QPushButton:hover { background:#3a3a5e; color:#ffffff; }"
        )
        _clear_btn.clicked.connect(lambda: self.log_text.clear() if self.log_text else None)
        _log_vbox.addWidget(_tools_log, 1)
        _log_vbox.addWidget(_clear_btn)
        tool_tab_defs.append((_log_container, "📋 Activity Log", 'activity_log'))

        # ── Wire buttons and stacked panels ─────────────────────────────────
        _COLS = 3
        for _idx, (panel, label, tool_id) in enumerate(tool_tab_defs):
            # Add panel to stack
            stack_idx = tool_stack.addWidget(panel)
            self.tool_panels[tool_id] = panel

            # Create grid button
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(28)   # was 34 — shorter buttons so the grid is less tall
            btn.setStyleSheet(
                "QPushButton { background:#2a2a3e; color:#cccccc; border:1px solid #444; "
                "border-radius:4px; font-size:12px; padding:0 8px; text-align:left; }"
                "QPushButton:hover { background:#3a3a5e; color:#ffffff; }"
                "QPushButton:checked { background:#0d7377; color:#ffffff; font-weight:bold; border-color:#0d9377; }"
            )
            btn.clicked.connect(lambda _chk, i=stack_idx, tid=tool_id: _select_tool(i, tid))
            self._tool_btn_group.append((tool_id, btn))
            btn_grid.addWidget(btn, _idx // _COLS, _idx % _COLS)

        # Select first tool by default
        if self._tool_btn_group:
            first_id, first_btn = self._tool_btn_group[0]
            first_btn.setChecked(True)
            tool_stack.setCurrentIndex(0)

        outer_layout.addWidget(btn_container)
        outer_layout.addWidget(tool_stack, 1)

        # ── Collapse/expand toggle for the button grid ───────────────────────
        # A single small chevron button at the bottom of the button bar lets
        # the user hide the grid to give the active panel maximum vertical room.
        collapse_btn = QPushButton("▲ Hide panel selector")
        collapse_btn.setFixedHeight(22)
        collapse_btn.setStyleSheet(
            "QPushButton { background: #1a1a2a; color: #666; border: none; "
            "border-top: 1px solid #333; font-size: 10px; }"
            "QPushButton:hover { color: #aaaaaa; }"
        )
        btn_visible = True   # tracks current visibility state

        def _toggle_btn_container():
            nonlocal btn_visible
            btn_visible = not btn_visible
            btn_container.setVisible(btn_visible)
            collapse_btn.setText(
                "▲ Hide panel selector" if btn_visible else "▼ Show panel selector"
            )

        collapse_btn.clicked.connect(_toggle_btn_container)
        outer_layout.addWidget(collapse_btn)

        # Wire up any lightweight dock panels (perf monitor, queue) — hidden by default
        self._create_tool_dock_panels()

        # Add the Tools tab to the main tab bar
        self.tabs.addTab(outer, "🛠️ Tools")
        return outer
    
    def _create_tool_dock_panels(self):
        """Create lightweight dock panels (perf monitor, processing queue).

        All interactive tool panels now live as sub-tabs inside the Tools tab
        (see create_tools_tab).  Only background/status docks are created here,
        and they are hidden by default so they don't crowd the window on startup.
        Users can show them from View → Tool Panels.
        """
        # Processing Queue dock — shows archive/batch operation progress
        try:
            from ui.archive_queue_widgets_qt import ProcessingQueueQt
            self.processing_queue_panel = ProcessingQueueQt()
            self._add_tool_dock(
                'processing_queue', '📥 Processing Queue',
                self.processing_queue_panel,
                Qt.DockWidgetArea.BottomDockWidgetArea
            )
            self.processing_queue_panel.processing_started.connect(
                lambda: self.statusBar().showMessage("⚙️ Archive processing started…", 2000)
            )
            self.processing_queue_panel.processing_paused.connect(
                lambda: self.statusBar().showMessage("⏸ Archive processing paused", 2000)
            )
            self.processing_queue_panel.processing_completed.connect(
                lambda: self.statusBar().showMessage("✅ Archive processing complete", 4000)
            )
            self.processing_queue_panel.item_completed.connect(
                lambda item_id, status: self.statusBar().showMessage(
                    f"{'✅' if status == 'completed' else '❌'} {item_id}: {status}", 3000
                )
            )
            logger.info("✅ Processing queue panel added as hidden dock")
        except Exception as _pqe:
            logger.warning(f"Could not load ProcessingQueueQt: {_pqe}")

        # Performance Dashboard dock
        try:
            from ui.performance_dashboard import PerformanceDashboard
            unlockables = getattr(self, 'unlockables_system', None)
            self.perf_dashboard = PerformanceDashboard(
                parent=self,
                unlockables_system=unlockables,
                tooltip_manager=self.tooltip_manager
            )
            self._add_tool_dock(
                'perf_dashboard', '📊 Performance Monitor',
                self.perf_dashboard,
                Qt.DockWidgetArea.RightDockWidgetArea
            )
            logger.info("✅ Performance dashboard added as hidden dock")
            self.perf_dashboard.start()
        except Exception as e:
            logger.warning(f"Performance dashboard unavailable: {e}")

        # Update View menu with tool panel toggles
        self._update_tool_panels_menu()
    
    def _add_tool_dock(self, tool_id: str, title: str, widget: QWidget, area: Qt.DockWidgetArea):
        """Add a tool panel as a dockable widget."""
        # Store panel reference
        self.tool_panels[tool_id] = widget
        
        # Create dock widget — objectName must be set so QMainWindow.saveState() can
        # serialize the dock geometry without emitting "objectName not set" warnings.
        dock = QDockWidget(title, self)
        dock.setObjectName(f"dock_{tool_id}")
        dock.setWidget(widget)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.BottomDockWidgetArea
        )
        
        # Store dock reference
        self.tool_dock_widgets[tool_id] = dock

        # Add to main window then immediately hide — docks are opt-in via View menu
        self.addDockWidget(area, dock)
        dock.hide()

        logger.info(f"Added tool dock (hidden): {tool_id} - {title}")
    
    def _update_tool_panels_menu(self):
        """Update View menu with tool panel visibility toggles AND sub-tab navigation."""
        if self.view_menu is None:
            return  # Menu bar not yet created; called too early
        # Add submenu for tool panels if it doesn't exist
        if not hasattr(self, 'tool_panels_menu'):
            self.tool_panels_menu = self.view_menu.addMenu("Tool Panels")

        # Clear existing actions
        self.tool_panels_menu.clear()

        # Sub-tab tools: clicking navigates to the tool (Tools tab → correct sub-tab)
        _TOOL_LABELS = {
            'organizer':  "📁 Organizer",
            'bg_remover': "🎭 Background Remover",
            'alpha_fixer':"✨ Alpha Fixer",
            'color':      "🎨 Color Correction",
            'normalizer': "⚙️ Batch Normalizer",
            'quality':    "✓ Quality Checker",
            'upscaler':   "🔍 Image Upscaler",
            'lineart':    "✏️ Line Art Converter",
            'converter':  "🔄 Format Converter",
            'rename':     "📝 Batch Rename",
            'repair':     "🔧 Image Repair",
        }
        for tool_id, label in _TOOL_LABELS.items():
            if tool_id in self.tool_panels:
                action = self.tool_panels_menu.addAction(label)
                action.triggered.connect(
                    lambda _checked=False, tid=tool_id: self.switch_tool(tid)
                )

        # Lightweight docks (Processing Queue, Performance Monitor): keep their
        # built-in toggleViewAction so they remain show/hide toggles
        if self.tool_dock_widgets:
            self.tool_panels_menu.addSeparator()
            for _tid, dock in self.tool_dock_widgets.items():
                self.tool_panels_menu.addAction(dock.toggleViewAction())
    
    def switch_tool(self, tool_id: str):
        """Switch to a tool: navigate to the Tools tab then select it in the grid."""
        # Special case: navigate to the Panda Features tab
        if tool_id == "panda_home":
            for i in range(self.tabs.count()):
                if "Panda" in self.tabs.tabText(i) or "🐼" in self.tabs.tabText(i):
                    self.tabs.setCurrentIndex(i)
                    # Also navigate to the Home sub-tab within the Panda panel
                    if self._panda_tabs is not None and self._home_tab_index >= 0:
                        self._panda_tabs.setCurrentIndex(self._home_tab_index)
                    return
            return

        # Find the Tools tab index in the main tab bar
        tools_tab_index = -1
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "🛠️ Tools":
                tools_tab_index = i
                break
        if tools_tab_index >= 0:
            self.tabs.setCurrentIndex(tools_tab_index)

        # Select the matching panel in the stacked widget and highlight its button
        tool_widget = self.tool_panels.get(tool_id)
        if tool_widget is not None and self.tool_tabs_widget is not None:
            idx = self.tool_tabs_widget.indexOf(tool_widget)
            if idx >= 0:
                self.tool_tabs_widget.setCurrentIndex(idx)
                # Update button highlight
                for _tid, _btn in getattr(self, '_tool_btn_group', []):
                    checked = _tid == tool_id
                    _btn.setChecked(checked)
                logger.info(f"Switched to tool: {tool_id}")
                return

        # Fall back to showing the dock if one exists
        if tool_id in self.tool_dock_widgets:
            dock = self.tool_dock_widgets[tool_id]
            dock.show()
            dock.raise_()
            logger.info(f"Showed tool dock: {tool_id}")
    
    def create_panda_features_tab(self):
        """Create panda features tab with bedroom, inventory, closet, achievements, and customization."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        try:
            self._create_panda_features_content(layout)
        except Exception as _e:
            logger.error(f"create_panda_features_tab outer error: {_e}", exc_info=True)
            err_lbl = QLabel(
                f"⚠️ Panda tab failed to load.\n\n"
                f"<b>{type(_e).__name__}</b>: {_e}\n\n"
                "Check app_data/logs/app.log for details."
            )
            err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            err_lbl.setWordWrap(True)
            layout.addWidget(err_lbl)

        return tab

    def _create_panda_features_content(self, layout):
        """Internal: populate the panda features tab. Separated so outer method can catch any crash."""

        # Create sub-tabs for panda features
        panda_tabs = QTabWidget()
        panda_tabs.setDocumentMode(True)
        self._panda_tabs = panda_tabs   # save ref so _on_bedroom_furniture_clicked can switch tabs
        
        # Get panda character
        panda_char = getattr(self.panda_widget, 'panda', None)
        
        # 1. Customization Tab
        # panda_char may be None here because PandaCharacter is created in
        # initialize_components() which runs after setup_ui().  We create the
        # panel regardless; initialize_components() will set panda_widget.panda
        # afterwards so colour/trail changes will work as expected.
        try:
            from ui.customization_panel_qt import CustomizationPanelQt
            custom_panel = CustomizationPanelQt(panda_char, self.panda_widget, tooltip_manager=self.tooltip_manager)

            # Connect customization panel signals
            custom_panel.color_changed.connect(self.on_customization_color_changed)
            custom_panel.trail_changed.connect(self.on_customization_trail_changed)

            panda_tabs.addTab(custom_panel, "🎨 Customization")
            logger.info("✅ Customization panel added to panda tab")
        except Exception as e:
            logger.error(f"Could not load customization panel: {e}", exc_info=True)
        
        # 2. Panda Home Tab — stacked widget: page 0 = 3D bedroom, page 1 = sub-panel
        try:
            from ui.panda_bedroom_gl import PandaBedroomGL
            try:
                from ui.panda_world_gl import PandaWorldWidget as _PandaWorldWidgetCls
            except (ImportError, OSError, RuntimeError):
                _PandaWorldWidgetCls = None
            try:
                from features.shop_system import ShopSystem
                from features.currency_system import CurrencySystem
                # Initialise shop/currency so Inventory still works
                self.shop_system = ShopSystem()
                self.currency_system = CurrencySystem()
                # Award daily login bonus (idempotent — no-op if already claimed today)
                try:
                    daily_bonus = self.currency_system.process_daily_login()
                    if daily_bonus > 0:
                        logger.info(f"💰 Daily login bonus: +{daily_bonus} Bamboo Bucks")
                except Exception as _dl:
                    logger.debug(f"Daily login bonus: {_dl}")
            except (ImportError, OSError, RuntimeError) as _se:
                logger.warning(f"Shop/currency system unavailable: {_se}")
                self.shop_system = None
                self.currency_system = None

            # ── Build stacked container ────────────────────────────────────
            home_container = QWidget()
            home_vbox = QVBoxLayout(home_container)
            home_vbox.setContentsMargins(0, 0, 0, 0)
            home_vbox.setSpacing(0)

            # Back-button toolbar (hidden while on bedroom page)
            back_bar = QWidget()
            back_bar.setObjectName("homeBackBar")
            back_bar.setStyleSheet(
                "#homeBackBar { background: #1a1a2e; border-bottom: 1px solid #333; }"
            )
            back_bar_layout = QHBoxLayout(back_bar)
            back_bar_layout.setContentsMargins(6, 4, 6, 4)

            back_btn = QPushButton("← Back to Home")
            back_btn.setFixedHeight(28)
            back_btn.setStyleSheet(
                "QPushButton { background: #2a2a4e; color: #aaaaff; border: 1px solid #555; "
                "border-radius: 4px; padding: 0 10px; } "
                "QPushButton:hover { background: #3a3a6e; }"
            )
            sub_label = QLabel("")
            sub_label.setStyleSheet("color: #cccccc; font-weight: bold; padding-left: 8px;")

            back_bar_layout.addWidget(back_btn)
            back_bar_layout.addWidget(sub_label)
            back_bar_layout.addStretch()
            back_bar.hide()

            # Stacked widget
            stack = QStackedWidget()

            # Page 0: 3D Bedroom
            bedroom_gl = PandaBedroomGL()
            bedroom_gl.furniture_clicked.connect(self._on_bedroom_furniture_clicked)
            if hasattr(bedroom_gl, 'gl_failed'):
                # When GL initialisation fails, swap the bedroom for a user-friendly
                # placeholder so there's no black/broken screen and no app crash.
                def _on_bedroom_gl_failed(msg: str, _stack=stack):
                    logger.warning(f"Bedroom GL failed: {msg}")
                    self.log(f"⚠️ 3D Bedroom GL init failed: {msg}")
                    placeholder = QLabel(
                        "🛏️ 3D Bedroom requires OpenGL 2.1\n\n"
                        f"Error: {msg[:120]}\n\n"
                        "Your GPU driver may not support OpenGL 2.1.\n"
                        "Try updating your graphics drivers."
                    )
                    placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    placeholder.setStyleSheet(
                        "color:#aaaaaa; background:#1a1a2e; font-size:12px; padding:20px;"
                    )
                    placeholder.setWordWrap(True)
                    try:
                        _stack.insertWidget(0, placeholder)
                        _stack.setCurrentIndex(0)
                    except Exception:
                        pass
                    # Null out the broken widget ref so _go_outside() does not query it
                    self._bedroom_widget = None
                bedroom_gl.gl_failed.connect(_on_bedroom_gl_failed)
            stack.addWidget(bedroom_gl)   # index 0

            # Page 1: placeholder — real sub-panel inserted dynamically
            _ph = QLabel("")
            stack.addWidget(_ph)          # index 1 (replaced on demand)

            home_vbox.addWidget(back_bar)
            home_vbox.addWidget(stack, 1)

            # Save refs
            self._bedroom_widget = bedroom_gl
            # Restore saved furniture layout if available
            try:
                saved_layout = config.get('ui.bedroom_layout', None)
                if saved_layout and hasattr(bedroom_gl, 'set_layout'):
                    bedroom_gl.set_layout(saved_layout)
            except Exception as _le:
                logger.debug(f"Could not restore bedroom layout: {_le}")
            self._world_widget: 'Optional[QWidget]' = None
            self._home_stack = stack
            self._home_tab_widget = home_container
            self._home_back_btn = back_btn
            self._home_sub_label = sub_label
            self._home_back_bar = back_bar
            self._home_stack_owned = [_ph]   # track widgets we own (safe to deleteLater)

            # Back button returns to bedroom
            def _go_home():
                stack.setCurrentIndex(0)
                back_bar.hide()
                if self._panda_tabs and self._home_tab_index >= 0:
                    self._panda_tabs.setTabText(
                        self._home_tab_index, "🏠 Panda Home"
                    )
            back_btn.clicked.connect(_go_home)

            # Furniture quick-access bar — shown permanently at the bottom of the
            # 3D home panel so users can jump to any room feature with one click.
            # This also satisfies the test expectation: ≥3 QPushButtons with
            # furniture labels must exist as children of the Panda Home tab widget.
            _furn_quick_bar = QWidget()
            _furn_quick_bar.setObjectName("furnitureQuickBar")
            _furn_quick_bar.setStyleSheet(
                "#furnitureQuickBar { background: #1a1a2e; border-top: 1px solid #333; }"
            )
            _furn_quick_h = QHBoxLayout(_furn_quick_bar)
            _furn_quick_h.setContentsMargins(6, 4, 6, 4)
            _furn_quick_h.setSpacing(6)
            _FURN_SHORTCUTS = [
                ("👗 Wardrobe",    "wardrobe"),
                ("🎒 Inventory",   "backpack"),
                ("🏆 Trophies",    "trophy_stand"),
                ("🍎 Food & Shop", "fridge"),
                ("🧸 Toy Box",     "toy_box"),
                ("🚪 Outside",     "bedroom_door"),
            ]
            _fshort_style = (
                "QPushButton { background: #2a2a4e; color: #ccccff; "
                "border: 1px solid #444; border-radius: 4px; "
                "font-size: 11px; padding: 4px 8px; }"
                "QPushButton:hover { background: #3a3a6e; color: #ffffff; border-color: #6666aa; }"
                "QPushButton:pressed { background: #4a4a8e; }"
            )
            for _flabel, _ffid in _FURN_SHORTCUTS:
                _fsbtn = QPushButton(_flabel)
                _fsbtn.setStyleSheet(_fshort_style)
                _fsbtn.clicked.connect(
                    lambda _checked=False, _fid=_ffid: self._on_bedroom_furniture_clicked(_fid)
                )
                _furn_quick_h.addWidget(_fsbtn)
            home_vbox.addWidget(_furn_quick_bar)

            panda_tabs.addTab(home_container, "🏠 Panda Home")
            self._home_tab_index = panda_tabs.indexOf(home_container)
            logger.info("✅ 3D Panda Home panel added to panda tab")

        except Exception as e:
            logger.error(f"Could not load Panda Home panel: {e}", exc_info=True)
            # ── 2D Panda Home fallback ────────────────────────────────────────
            # When PyOpenGL is unavailable the 3D bedroom can't be created.
            # Replace the bare error label with a styled interactive panel that
            # shows the panda character and furniture shortcut buttons so the
            # user can still open the Wardrobe, Inventory, Achievements and Shop.
            home_2d = QWidget()
            home_2d.setObjectName("pandaHome2DFallback")
            home_2d.setStyleSheet(
                "QWidget#pandaHome2DFallback { "
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                "stop:0 #0d0d1a, stop:0.6 #1a1a3e, stop:1 #14101e); }"
            )
            _h2d_layout = QVBoxLayout(home_2d)
            _h2d_layout.setContentsMargins(20, 16, 20, 16)
            _h2d_layout.setSpacing(12)

            # Header
            _h2d_title = QLabel("🏠  Panda's Home")
            _h2d_title.setStyleSheet(
                "color: #ffffff; font-size: 18px; font-weight: bold; "
                "background: transparent;"
            )
            _h2d_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            _h2d_layout.addWidget(_h2d_title)

            # Panda 2D widget embedded in the room
            _panda_area = QWidget()
            _panda_area.setObjectName("pandaHomeRoomArea")
            _panda_area.setMinimumHeight(240)
            _panda_area.setStyleSheet(
                "QWidget#pandaHomeRoomArea { "
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                "stop:0 #1a1a3e, stop:0.8 #22223e, stop:1 #111122); "
                "border-radius: 10px; border: 1px solid #333; }"
            )
            _room_vbox = QVBoxLayout(_panda_area)
            _room_vbox.setContentsMargins(0, 0, 0, 0)
            # Embed a fresh PandaWidget2D instance (independent of the overlay)
            try:
                _panda_char = getattr(self, 'panda_widget', None)
                _panda_char = getattr(_panda_char, 'panda', None)
                from ui.panda_widget_2d import PandaWidget2D as _PW2DHome
                _bedroom_panda = _PW2DHome(panda_character=_panda_char, parent=_panda_area)
                _bedroom_panda.setMinimumHeight(200)
                _room_vbox.addWidget(_bedroom_panda)
                self._bedroom_panda_2d = _bedroom_panda
            except Exception as _pw:
                logger.debug(f"2D panda in home fallback: {_pw}")
                _room_vbox.addStretch()
            _h2d_layout.addWidget(_panda_area, 1)

            # Furniture shortcut buttons grid
            _furn_label = QLabel("✨ Visit a room")
            _furn_label.setStyleSheet(
                "color: #aaaacc; font-size: 11px; background: transparent;"
            )
            _furn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            _h2d_layout.addWidget(_furn_label)

            _btn_row = QWidget()
            _btn_row.setStyleSheet("background: transparent;")
            _btn_grid = QGridLayout(_btn_row)
            _btn_grid.setContentsMargins(0, 0, 0, 0)
            _btn_grid.setSpacing(8)
            _FURN_BTNS = [
                ("👗\nWardrobe",    "wardrobe"),
                ("🎒\nInventory",   "backpack"),
                ("🏆\nTrophies",    "trophy_stand"),
                ("🍎\nFood & Shop", "fridge"),
                ("🧸\nToy Box",     "toy_box"),
                ("🚪\nGo Outside",  "bedroom_door"),
            ]
            _furn_style = (
                "QPushButton { background: #2a2a4e; color: #ccccff; "
                "border: 1px solid #444; border-radius: 8px; "
                "font-size: 13px; padding: 8px 4px; min-width: 80px; min-height: 64px; }"
                "QPushButton:hover { background: #3a3a6e; color: #ffffff; border-color: #6666aa; }"
                "QPushButton:pressed { background: #4a4a8e; }"
            )
            for _bi, (_blabel, _bfid) in enumerate(_FURN_BTNS):
                _fbtn = QPushButton(_blabel)
                _fbtn.setStyleSheet(_furn_style)
                # Capture loop variable in default arg
                _fbtn.clicked.connect(
                    lambda _checked=False, _fid=_bfid: self._on_bedroom_furniture_clicked(_fid)
                )
                _btn_grid.addWidget(_fbtn, _bi // 3, _bi % 3)
            _h2d_layout.addWidget(_btn_row)

            panda_tabs.addTab(home_2d, "🏠 Panda Home")
            self._home_tab_index = panda_tabs.indexOf(home_2d)
            # Expose refs needed by the furniture-click handler
            self._bedroom_widget = None
            self._home_stack = None
            self._home_back_bar = None
            self._home_back_btn = None
            self._home_sub_label = None
            self._home_stack_owned = []

        # 3. Inventory + Widgets — built but NOT added as a tab.
        #    Shown via Panda Home when panda clicks the backpack in the bedroom.
        try:
            from ui.inventory_panel_qt import InventoryPanelQt

            _shop = self.shop_system
            if _shop is None:
                from features.shop_system import ShopSystem as _ShopSystem
                _shop = _ShopSystem()
            inventory_panel = InventoryPanelQt(_shop, tooltip_manager=self.tooltip_manager)
            self._inventory_panel = inventory_panel

            inventory_panel.item_selected.connect(self.on_inventory_item_selected)

            # Try to embed Widgets panel as a sub-tab inside the inventory panel
            try:
                from ui.widgets_panel_qt import WidgetsPanelQt
                from features.panda_widgets import WidgetCollection
                widget_collection = WidgetCollection()
                widgets_panel = WidgetsPanelQt(widget_collection, self.panda_widget, tooltip_manager=self.tooltip_manager)
                if hasattr(widgets_panel, 'widget_selected'):
                    widgets_panel.widget_selected.connect(
                        lambda w: logger.debug(f"Widget selected: {w}")
                    )
                # Merge: add Widgets as a tab inside the inventory panel if it supports it;
                # otherwise store separately for the backpack sub-panel QTabWidget wrapper.
                self._widgets_panel = widgets_panel
            except Exception as _we:
                logger.debug(f"Widgets panel unavailable: {_we}")
                self._widgets_panel = None

            logger.info("✅ Inventory + Widgets panels built (accessible via backpack)")
        except Exception as e:
            logger.error(f"Could not build inventory panel: {e}", exc_info=True)
            self._widgets_panel = None

        # 4. Closet — built but NOT added as a tab.
        #    Shown via Panda Home when panda clicks the wardrobe in the bedroom.
        try:
            from ui.closet_display_qt import ClosetDisplayWidget
            from features.panda_closet import PandaCloset

            self.panda_closet = PandaCloset()
            try:
                if self._closet_path.exists():
                    self.panda_closet.load_from_file(str(self._closet_path))
                    logger.info("Closet state loaded from disk")
                    self._restore_panda_appearance_from_closet()
            except Exception as _ce:
                logger.debug(f"Closet load: {_ce}")
            closet_panel = ClosetDisplayWidget(tooltip_manager=self.tooltip_manager)
            self._closet_panel = closet_panel
            if hasattr(closet_panel, 'item_equipped'):
                closet_panel.item_equipped.connect(self._on_closet_item_equipped)
            try:
                closet_panel.load_clothing_items(self._build_closet_items_list())
            except Exception as _pie:
                logger.debug(f"Closet panel item population: {_pie}")
            # NOT added as tab — accessible via wardrobe in bedroom
            logger.info("✅ Closet panel built (accessible via wardrobe)")
        except Exception as e:
            logger.error(f"Could not build closet panel: {e}", exc_info=True)

        # 5. Achievements Tab
        try:
            from ui.achievement_panel_qt import AchievementDisplayWidget
            from features.achievements import AchievementSystem

            self.achievement_system = AchievementSystem()
            # Register callback to show popup + play sound when achievement unlocked
            self.achievement_system.register_unlock_callback(self._on_achievement_unlocked)
            # Count this startup as a new session
            try:
                self.achievement_system.increment_sessions()
            except Exception:
                pass
            achievement_panel = AchievementDisplayWidget(self.achievement_system, tooltip_manager=self.tooltip_manager)
            self._achievement_panel = achievement_panel   # keep ref for refresh on unlock
            panda_tabs.addTab(achievement_panel, "🏆 Achievements")
            self._achievement_tab_index = panda_tabs.indexOf(achievement_panel)
            logger.info("✅ Achievements panel added to panda tab")
        except Exception as e:
            logger.error(f"Could not load achievements panel: {e}", exc_info=True)
            # Add placeholder  
            label = QLabel("⚠️ Achievements not available\n\nInstall required dependencies")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "🏆 Achievements")
        
        # 6. Minigames Tab
        try:
            from ui.minigame_panel_qt import MinigamePanelQt
            from features.minigame_system import MiniGameManager
            
            minigame_manager = MiniGameManager()
            minigame_panel = MinigamePanelQt(minigame_manager=minigame_manager, tooltip_manager=self.tooltip_manager)
            # Wire game completion → XP reward + status bar message
            if hasattr(minigame_panel, 'game_completed'):
                minigame_panel.game_completed.connect(self._on_minigame_completed)
            panda_tabs.addTab(minigame_panel, "🎮 Minigames")
            logger.info("✅ Minigames panel added to panda tab")
        except Exception as e:
            logger.error(f"Could not load minigames panel: {e}", exc_info=True)
            # Add placeholder
            label = QLabel("⚠️ Minigames not available\n\nInstall required dependencies")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "🎮 Minigames")
        
        # 7. Widgets — built inside the inventory block above (section 3).
        #    No separate tab; accessible via backpack in bedroom.

        # 8. Adventure / Dungeon Tab
        try:
            from ui.dungeon_graphics_view import DungeonGraphicsView
            from features.integrated_dungeon import IntegratedDungeon
            from features.enemy_manager import EnemyManager

            self.integrated_dungeon = IntegratedDungeon()
            # Use a container so we can add both dungeon view and travel animation widget
            adventure_container = QWidget()
            adventure_layout = QVBoxLayout(adventure_container)
            adventure_layout.setContentsMargins(0, 0, 0, 0)

            dungeon_view = DungeonGraphicsView(tooltip_manager=self.tooltip_manager)
            dungeon_view.set_dungeon(self.integrated_dungeon)
            adventure_layout.addWidget(dungeon_view, stretch=3)

            # EnemyManager needs parent widget, panda_widget, and enemy_collection
            panda_wgt = getattr(self, 'panda_widget', None)
            self.enemy_manager = EnemyManager(
                parent=dungeon_view,
                panda_widget=panda_wgt,
                enemy_collection=self.integrated_dungeon.enemy_collection,
            )

            # Travel animation strip — wire animation_complete to advance dungeon
            try:
                from ui.qt_travel_animation import TravelAnimationWidget
                from features.travel_system import TravelSystem
                _ts = self.travel_system or TravelSystem()
                travel_widget = TravelAnimationWidget(travel_system=_ts, parent=adventure_container)
                if hasattr(travel_widget, 'animation_complete'):
                    travel_widget.animation_complete.connect(
                        lambda: logger.debug("Travel animation complete")
                    )
                adventure_layout.addWidget(travel_widget, stretch=1)
            except Exception as _te:
                logger.debug(f"Travel animation widget not available: {_te}")

            panda_tabs.addTab(adventure_container, "⚔️ Adventure")
            logger.info("✅ Adventure/Dungeon panel added to panda tab")
        except Exception as e:
            logger.warning(f"Could not load dungeon panel: {e}")
            from ui.dungeon_graphics_view import PYQT_AVAILABLE as _DUNGEON_QT
            if not _DUNGEON_QT:
                _err_msg = (
                    "⚔️ Adventure Mode\n\n"
                    "Requires PyQt6 to be installed.\n\n"
                    "Install with:\n"
                    "    pip install PyQt6\n\n"
                    "Then restart the application."
                )
            else:
                _err_msg = (
                    f"⚔️ Adventure Mode\n\n"
                    f"Failed to load dungeon panel.\n"
                    f"{type(e).__name__}: {e}"
                )
            label = QLabel(_err_msg)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            panda_tabs.addTab(label, "⚔️ Adventure")

        # 9. Quests Tab
        try:
            from features.quest_system import QuestSystem

            self.quest_system = QuestSystem()
            # Wire quest completion → achievement & currency reward
            self.quest_system.quest_completed.connect(self._on_quest_completed)
            # Wire quest started notification → status bar
            self.quest_system.quest_started.connect(
                lambda qid: self.statusBar().showMessage(f"📜 Quest started: {qid}", 3000)
            )
            # Wire quest progress → status bar so user sees progress feedback
            if hasattr(self.quest_system, 'quest_progress') and self.quest_system.quest_progress:
                self.quest_system.quest_progress.connect(self._on_quest_progress)
            # Wire achievement_unlocked (quest side) → re-use achievement handler
            if hasattr(self.quest_system, 'achievement_unlocked') and self.quest_system.achievement_unlocked:
                self.quest_system.achievement_unlocked.connect(
                    lambda aid: logger.info(f"🏆 Quest achievement: {aid}")
                )
            # Wire easter_egg_found → fun status bar message + coin reward
            if hasattr(self.quest_system, 'easter_egg_found') and self.quest_system.easter_egg_found:
                def _on_easter_egg(eid: str) -> None:
                    self.statusBar().showMessage(f"🥚 Easter egg found: {eid}!", 5000)
                    try:
                        if self.currency_system:
                            coins = self.currency_system.get_reward_for_action('easter_egg_found')
                            if coins > 0:
                                self.currency_system.earn_money(coins, f'easter_egg_{eid}')
                                self._update_coin_display()
                    except Exception:
                        pass
                self.quest_system.easter_egg_found.connect(_on_easter_egg)
            # Activate first set of quests
            self.quest_system.check_quests(0)

            # Simple quests display widget
            quests_container = QWidget()
            quests_layout = QVBoxLayout(quests_container)
            quests_label = QLabel("📜 Active Quests")
            quests_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            quests_layout.addWidget(quests_label)
            active = self.quest_system.get_active_quests() if hasattr(self.quest_system, 'get_active_quests') else []
            if active:
                for q in active[:10]:
                    name = getattr(q, 'name', str(q))
                    desc = getattr(q, 'description', '')
                    q_label = QLabel(f"• {name}\n  {desc}")
                    q_label.setWordWrap(True)
                    quests_layout.addWidget(q_label)
            else:
                quests_layout.addWidget(QLabel("No active quests — keep using the app to unlock quests!"))
            quests_layout.addStretch()
            panda_tabs.addTab(quests_container, "📜 Quests")
            logger.info("✅ Quests tab added to panda tab")
        except Exception as e:
            logger.warning(f"Could not load quests tab: {e}")
            label = QLabel("📜 Quests\n\nComplete tasks to unlock quests!")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "📜 Quests")

        # ── Skill Tree tab ────────────────────────────────────────────────────
        try:
            skill_container = QWidget()
            skill_layout = QVBoxLayout(skill_container)

            title = QLabel("🌳 Skill Tree")
            title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 6px;")
            skill_layout.addWidget(title)

            # Summary: unlocked / total
            skill_tree = getattr(self, 'skill_tree', None)
            if skill_tree is not None:
                unlocked = len(skill_tree.get_unlocked_skills())
                total = len(skill_tree.skills)
                summary = QLabel(
                    f"✨ Skills unlocked: {unlocked} / {total}   "
                    f"│  Branches: Combat · Magic · Exploration · Panda"
                )
            else:
                summary = QLabel("🌱 Skill tree will load once components initialise…")
            summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
            summary.setStyleSheet("padding:4px; color:#aaddaa;")
            skill_layout.addWidget(summary)

            # Branch filter buttons
            _branch_filter: list = ['All']
            branch_bar = QHBoxLayout()
            for _branch in ('All', 'Combat', 'Magic', 'Exploration', 'Panda'):
                _bb = QPushButton(_branch)
                _bb.setCheckable(True)
                _bb.setChecked(_branch == 'All')
                _bb.setFixedHeight(24)
                branch_bar.addWidget(_bb)
            skill_layout.addLayout(branch_bar)

            # List unlockable skills with Unlock button
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.Shape.NoFrame)
            inner = QWidget()
            inner_layout = QVBoxLayout(inner)
            inner_layout.setSpacing(4)

            _MAX_DISPLAYED_SKILLS = 40
            if skill_tree is not None:
                # Group by branch for visual clarity
                by_branch: dict = {}
                for sk in list(skill_tree.skills.values())[:_MAX_DISPLAYED_SKILLS]:
                    by_branch.setdefault(getattr(sk, 'branch', 'General'), []).append(sk)

                for branch_name, skills in by_branch.items():
                    branch_hdr = QLabel(f"── {branch_name} ──")
                    branch_hdr.setStyleSheet(
                        "color:#88ccff; font-weight:bold; padding:4px 2px 2px 2px;"
                    )
                    inner_layout.addWidget(branch_hdr)

                    for skill in skills:
                        # Card widget
                        card = QWidget()
                        card.setObjectName("skillCard")
                        card_col = "#223322" if skill.unlocked else "#1a1a2a"
                        card.setStyleSheet(
                            f"#skillCard {{ background:{card_col}; border:1px solid #444; "
                            f"border-radius:4px; padding:2px; }}"
                        )
                        card_row = QHBoxLayout(card)
                        card_row.setContentsMargins(6, 4, 6, 4)

                        # Status icon + name
                        icon = "✅" if skill.unlocked else "🔒"
                        cost = getattr(skill, 'cost', getattr(skill, 'xp_cost', 1))
                        req_lvl = getattr(skill, 'required_level', 1)
                        name_lbl = QLabel(
                            f"<b>{icon} {skill.name}</b>"
                            f"<br><small style='color:#888'>{skill.description}</small>"
                        )
                        name_lbl.setTextFormat(Qt.TextFormat.RichText)
                        name_lbl.setWordWrap(True)
                        card_row.addWidget(name_lbl, stretch=1)

                        if skill.unlocked:
                            owned_lbl = QLabel("Owned")
                            owned_lbl.setStyleSheet("color:#66dd66; font-size:9pt;")
                            card_row.addWidget(owned_lbl)
                        else:
                            cost_lbl = QLabel(f"Lv.{req_lvl}  •  {cost} SP")
                            cost_lbl.setStyleSheet("color:#ffcc44; font-size:9pt;")
                            card_row.addWidget(cost_lbl)

                            btn = QPushButton("Unlock")
                            btn.setFixedWidth(64)
                            btn.setFixedHeight(26)
                            _skill_id = skill.skill_id
                            def _make_unlock_handler(sid, card_widget, name_widget, cost_widget, btn_widget):
                                def _unlock():
                                    lvl = getattr(self.level_system, 'level', 1) if self.level_system else 1
                                    pts = getattr(self.level_system, 'skill_points', 99) if self.level_system else 99
                                    ok = self.skill_tree.unlock_skill(sid, lvl, pts)
                                    if ok:
                                        # Deduct the skill's cost from level_system
                                        skill_node = self.skill_tree.get_skill(sid)
                                        cost = getattr(skill_node, 'cost', 1) if skill_node else 1
                                        if self.level_system and hasattr(self.level_system, 'deduct_skill_points'):
                                            self.level_system.deduct_skill_points(cost)
                                        self.statusBar().showMessage(f"🌳 Skill unlocked! (-{cost} skill point{'s' if cost != 1 else ''})", 3000)
                                        name_widget.setText(
                                            name_widget.text().replace("🔒", "✅")
                                        )
                                        card_widget.setStyleSheet(
                                            "#skillCard { background:#223322; border:1px solid #444; "
                                            "border-radius:4px; padding:2px; }"
                                        )
                                        cost_widget.setText("Owned")
                                        cost_widget.setStyleSheet("color:#66dd66; font-size:9pt;")
                                        btn_widget.setVisible(False)
                                    else:
                                        self.statusBar().showMessage("❌ Not enough skill points or level too low", 3000)
                                return _unlock
                            btn.clicked.connect(_make_unlock_handler(_skill_id, card, name_lbl, cost_lbl, btn))
                            card_row.addWidget(btn)

                        inner_layout.addWidget(card)

                inner_layout.addStretch()

            scroll.setWidget(inner)
            skill_layout.addWidget(scroll)
            panda_tabs.addTab(skill_container, "🌳 Skills")
            logger.info("✅ Skill Tree tab added to panda tab")
        except Exception as e:
            logger.warning(f"Could not load skill tree tab: {e}")
            label = QLabel("🌳 Skill Tree\n\nLevel up to unlock skills!")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "🌳 Skills")


        # 11. Creative Tools tab (Paint + Weapon Positioning)
        try:
            from ui.paint_tools_qt import create_paint_tools
            from ui.weapon_positioning_qt import create_weapon_positioning_widget
            tools_container = QWidget()
            tools_layout = QVBoxLayout(tools_container)
            tools_layout.setContentsMargins(4, 4, 4, 4)
            tools_sub = QTabWidget()
            paint_widget = create_paint_tools(tools_container)
            if paint_widget:
                tools_sub.addTab(paint_widget, "🖌️ Paint")
            weapon_widget = create_weapon_positioning_widget(tools_container)
            if weapon_widget:
                tools_sub.addTab(weapon_widget, "⚔️ Weapons")
            tools_layout.addWidget(tools_sub)
            panda_tabs.addTab(tools_container, "🎨 Creative")
            logger.info("✅ Creative Tools tab added to panda tab")
        except Exception as e:
            logger.warning(f"Could not load creative tools tab: {e}")
            label = QLabel("🎨 Creative Tools\n\nRequires PyQt6 + OpenGL.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "🎨 Creative")

        layout.addWidget(panda_tabs)
        # (tab returned by the outer create_panda_features_tab)
    
    # NOTE: create_file_browser_tab and create_notepad_tab have been removed.
    # Both panels are accessible via the Tools tab grid (see create_tools_tab()).

    def create_settings_tab(self):
        """Create settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            if SettingsPanelQt is not None:
                # Create comprehensive settings panel
                self.settings_panel = SettingsPanelQt(config, self, tooltip_manager=self.tooltip_manager)
                # Connect settings changed signal
                self.settings_panel.settingsChanged.connect(self.on_settings_changed)
                layout.addWidget(self.settings_panel)
                self.log("✅ Settings panel loaded successfully")
            else:
                label = QLabel("⚠️ Settings panel requires PyQt6\n\nInstall with: pip install PyQt6")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
            
        except Exception as e:
            logger.error(f"Error loading settings panel: {e}", exc_info=True)
            # Fallback to placeholder
            label = QLabel(f"⚠️ Error loading settings panel: {e}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        
        self.tabs.addTab(tab, "⚙️ Settings")
    
    def setup_menubar(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # ── File menu ────────────────────────────────────────────────────────
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Input Folder…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Select the input folder containing images to process (Ctrl+O)")
        open_action.triggered.connect(self.browse_input)
        file_menu.addAction(open_action)

        open_out_action = QAction("Open &Output Folder…", self)
        open_out_action.setShortcut("Ctrl+Shift+O")
        open_out_action.setStatusTip("Select the output folder where processed files will be saved (Ctrl+Shift+O)")
        open_out_action.triggered.connect(self.browse_output)
        file_menu.addAction(open_out_action)

        file_menu.addSeparator()

        # Profiles sub-menu (uses ProfileManager)
        profile_menu = file_menu.addMenu("&Profiles")
        save_profile_action = QAction("&Save Current Profile…", self)
        save_profile_action.setStatusTip("Save current organizer settings as a named profile for reuse")
        save_profile_action.triggered.connect(self._save_profile)
        profile_menu.addAction(save_profile_action)
        load_profile_action = QAction("&Load Profile…", self)
        load_profile_action.setStatusTip("Load a previously saved organizer settings profile")
        load_profile_action.triggered.connect(self._load_profile)
        profile_menu.addAction(load_profile_action)

        # Backup sub-menu (uses BackupManager)
        backup_menu = file_menu.addMenu("&Backup")
        create_restore_action = QAction("Create &Restore Point…", self)
        create_restore_action.setStatusTip("Create a restore point to recover from if something goes wrong")
        create_restore_action.triggered.connect(self._create_restore_point)
        backup_menu.addAction(create_restore_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application (Ctrl+Q)")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ── View menu ────────────────────────────────────────────────────────
        view_menu = menubar.addMenu("&View")
        self.view_menu = view_menu  # Store reference for dynamic updates

        popout_action = QAction("Pop Out Current Tab", self)
        popout_action.setShortcut("Ctrl+Shift+P")
        popout_action.setStatusTip("Detach the current tool tab into its own floating window (Ctrl+Shift+P)")
        popout_action.triggered.connect(self.popout_current_tab)
        view_menu.addAction(popout_action)

        view_menu.addSeparator()

        # Submenu for restoring docked tabs
        self.restore_menu = view_menu.addMenu("Restore Docked Tab")
        self.restore_menu.setEnabled(False)  # Disabled until tabs are popped out

        view_menu.addSeparator()

        reset_layout_action = QAction("Reset Window Layout", self)
        reset_layout_action.setStatusTip("Reset all dock widgets and panels to their default positions")
        reset_layout_action.triggered.connect(self.reset_window_layout)
        view_menu.addAction(reset_layout_action)

        # ── Tools menu ────────────────────────────────────────────────────────
        tools_menu = menubar.addMenu("&Actions")

        find_dupes_action = QAction("🔍 Find Duplicate Textures…", self)
        find_dupes_action.setStatusTip("Scan the input folder for duplicate or near-duplicate texture files")
        find_dupes_action.triggered.connect(self._find_duplicate_textures)
        tools_menu.addAction(find_dupes_action)

        analyze_action = QAction("🔬 Analyze Selected Texture…", self)
        analyze_action.setStatusTip("Open a texture file and display its detailed analysis (dimensions, format, etc.)")
        analyze_action.triggered.connect(self._analyze_selected_texture)
        tools_menu.addAction(analyze_action)

        # ── Help menu ────────────────────────────────────────────────────────
        help_menu = menubar.addMenu("&Help")

        help_action = QAction("&Help / Documentation", self)
        help_action.setShortcut("F1")
        help_action.setStatusTip("Open the help documentation (F1)")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        help_menu.addSeparator()

        support_action = QAction("❤️ Support on &Patreon", self)
        support_action.setStatusTip("Open the Patreon support page")
        support_action.triggered.connect(self._open_patreon)
        help_menu.addAction(support_action)

        help_menu.addSeparator()

        about_action = QAction("&About", self)
        about_action.setStatusTip("Show version information and credits for this application")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_statusbar(self):
        """Setup status bar with permanent coin-balance and panda-mood indicators."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

        # ── Permanent right-side widgets (always visible) ─────────────────────
        try:
            # Panda mood indicator
            self._panda_mood_label = QLabel("🐼 idle")
            self._panda_mood_label.setStyleSheet(
                "color: #aaffaa; padding: 0 6px; font-size: 11px;"
            )
            self._panda_mood_label.setToolTip("Current panda mood / animation state")
            self.statusbar.addPermanentWidget(self._panda_mood_label)

            # Coin balance indicator — updated by _update_coin_display()
            self._coin_label = QLabel("💰 —")
            self._coin_label.setStyleSheet(
                "color: #ffd700; padding: 0 8px; font-weight: bold; font-size: 11px;"
            )
            self._coin_label.setToolTip("Your Bamboo Bucks balance")
            self.statusbar.addPermanentWidget(self._coin_label)
        except Exception:
            self._coin_label = None
            self._panda_mood_label = None
    
    def apply_theme(self, theme_name: str = None):
        """Apply theme stylesheet based on config.

        Args:
            theme_name: Optional theme name override.  When provided the name is
                        saved to config before applying so it persists.  When
                        omitted (normal case) the value already stored in config
                        is used.
        """
        if theme_name is not None:
            config.set('ui', 'theme', value=theme_name)
        # Normalise: map combo-box display names → internal lowercase keys
        _RAW = config.get('ui', 'theme', default='dark')
        _DISPLAY_MAP = {
            'dark': 'dark', 'light': 'light', 'nord': 'nord',
            'dracula': 'dracula', 'solarized dark': 'solarized dark',
            'solarized_dark': 'solarized dark',
            'forest': 'forest', 'ocean': 'ocean', 'sunset': 'sunset',
            'cyberpunk': 'cyberpunk', 'gore': 'gore', 'goth': 'goth',
            'vampire': 'vampire',
        }
        theme = _DISPLAY_MAP.get(_RAW.lower().strip(), _RAW.lower().strip())
        accent = config.get('ui', 'accent_color', default='#0d7377')
        
        # Calculate hover and pressed colors
        from PyQt6.QtGui import QColor
        accent_color = QColor(accent)
        h, s, v, a = accent_color.getHsv()
        
        hover_color = QColor()
        hover_color.setHsv(h, s, min(255, int(v * 1.2)), a)
        
        pressed_color = QColor()
        pressed_color.setHsv(h, s, int(v * 0.8), a)
        
        if theme == 'light':
            stylesheet = f"""
            QMainWindow {{
                background-color: #f5f5f5;
            }}
            QWidget {{
                background-color: #f5f5f5;
                color: #000000;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QPushButton {{
                background-color: {accent};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name()};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color.name()};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
            QLabel {{
                color: #000000;
                background-color: transparent;
            }}
            QTabWidget::pane {{
                border: 1px solid #cccccc;
                background-color: #ffffff;
            }}
            QTabBar::tab {{
                background-color: #e0e0e0;
                color: #000000;
                padding: 8px 20px;
                border: 1px solid #cccccc;
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {accent};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: #d0d0d0;
            }}
            QMenuBar {{
                background-color: #e0e0e0;
                color: #000000;
                border-bottom: 1px solid #cccccc;
            }}
            QMenuBar::item:selected {{
                background-color: {accent};
                color: white;
            }}
            QMenu {{
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
            }}
            QMenu::item:selected {{
                background-color: {accent};
                color: white;
            }}
            QProgressBar {{
                border: 1px solid #cccccc;
                border-radius: 3px;
                text-align: center;
                background-color: #ffffff;
                color: #000000;
            }}
            QProgressBar::chunk {{
                background-color: {accent};
            }}
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }}
            QTextEdit {{
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #cccccc;
            }}
            """
        elif theme == 'nord':
            # ⚔️  Norse Mythology / Nordic theme
            # Colour story: deep fjord midnight (#0f1923), carved runestone (#1e2d3d),
            # iron-grey steel (#2e4057), frost-white (#dde8f4), ice-blue (#88c0d0),
            # aurora green (#a3be8c), ember gold (#ebcb8b), blood iron (#bf616a).
            # Typography: 'Palatino Linotype', 'Georgia' serif — evoking ancient scrolls.
            # Borders: sharp, angular (border-radius ≤ 2px) like chiselled rune stones.
            # Decorative: runic-style angular chevrons on tabs; carved-beam dock titles.
            stylesheet = f"""
            QMainWindow {{
                background-color: #0f1923;
            }}
            QWidget {{
                background-color: #0f1923;
                color: #dde8f4;
                font-family: 'Palatino Linotype', 'Georgia', 'Times New Roman', serif;
            }}
            /* ── Rune-stone buttons — angular, iron-forged ─────────────────── */
            QPushButton {{
                background-color: {accent};
                color: #eceff4;
                border: 2px solid #4a6880;
                padding: 8px 18px;
                border-radius: 2px;
                font-weight: bold;
                font-family: 'Palatino Linotype', 'Georgia', serif;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name()};
                border-color: #88c0d0;
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: {pressed_color.name()};
                border-color: #5e81ac;
            }}
            QPushButton:disabled {{
                background-color: #1e2d3d;
                color: #4a5a6a;
                border-color: #2e3d4d;
            }}
            QLabel {{
                color: #dde8f4;
                background-color: transparent;
            }}
            /* ── Carved runestone group-boxes ───────────────────────────────── */
            QGroupBox {{
                color: #88c0d0;
                border: 2px solid #4a6880;
                border-radius: 0px;
                margin-top: 10px;
                font-weight: bold;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QGroupBox::title {{
                color: #ebcb8b;
                subcontrol-position: top left;
                padding: 2px 8px;
                background: #1e2d3d;
                border: 1px solid #4a6880;
            }}
            /* ── Fjord-plank tab bar ─────────────────────────────────────────── */
            QTabWidget::pane {{
                border: 2px solid #2e4057;
                background-color: #131f2b;
            }}
            QTabBar::tab {{
                background-color: #1e2d3d;
                color: #8aa4b8;
                padding: 8px 22px;
                border: 2px solid #2e4057;
                border-bottom: none;
                border-radius: 2px 2px 0px 0px;
                font-family: 'Palatino Linotype', 'Georgia', serif;
                letter-spacing: 1px;
            }}
            QTabBar::tab:selected {{
                background-color: {accent};
                color: #eceff4;
                border-color: #88c0d0;
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background-color: #2a3d52;
                color: #dde8f4;
                border-color: #4a6880;
            }}
            /* ── Norse menu bar ─────────────────────────────────────────────── */
            QMenuBar {{
                background-color: #0d1720;
                color: #8aa4b8;
                border-bottom: 2px solid #2e4057;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QMenuBar::item:selected {{
                background-color: #2e4057;
                color: #ebcb8b;
            }}
            QMenu {{
                background-color: #131f2b;
                color: #dde8f4;
                border: 2px solid #2e4057;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QMenu::item:selected {{
                background-color: #2e4057;
                color: #ebcb8b;
            }}
            QMenu::separator {{
                height: 1px;
                background: #2e4057;
                margin: 3px 8px;
            }}
            /* ── Ship-prow progress bar ─────────────────────────────────────── */
            QProgressBar {{
                border: 2px solid #2e4057;
                border-radius: 0px;
                text-align: center;
                background-color: #131f2b;
                color: #88c0d0;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2e4057, stop:0.5 {accent}, stop:1 #88c0d0);
                border-radius: 0px;
            }}
            QFrame {{
                background-color: #131f2b;
                border: 2px solid #2e4057;
                border-radius: 0px;
            }}
            QTextEdit {{
                background-color: #0d1720;
                color: #dde8f4;
                border: 2px solid #2e4057;
                border-radius: 0px;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QLineEdit {{
                background-color: #1e2d3d;
                color: #dde8f4;
                border: 2px solid #2e4057;
                border-radius: 2px;
                padding: 4px 6px;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QLineEdit:focus {{
                border-color: #88c0d0;
            }}
            QLineEdit:read-only {{
                background-color: #131f2b;
                color: #8aa4b8;
            }}
            /* ── Rune-carved combo boxes ─────────────────────────────────────── */
            QComboBox {{
                background-color: #1e2d3d;
                color: #dde8f4;
                border: 2px solid #2e4057;
                border-radius: 2px;
                padding: 4px 8px;
                min-height: 22px;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QComboBox:hover {{
                border-color: #88c0d0;
            }}
            QComboBox QAbstractItemView {{
                background-color: #131f2b;
                color: #dde8f4;
                border: 2px solid #2e4057;
                selection-background-color: #2e4057;
                selection-color: #ebcb8b;
            }}
            /* ── Norse check-rune ────────────────────────────────────────────── */
            QCheckBox {{
                color: #dde8f4;
                spacing: 8px;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 2px solid #4a6880;
                border-radius: 0px;
                background: #1e2d3d;
            }}
            QCheckBox::indicator:checked {{
                background: #5e81ac;
                border-color: #88c0d0;
            }}
            QCheckBox::indicator:hover {{
                border-color: #88c0d0;
            }}
            /* ── Bubbly scrollbar ────────────────────────────────────────────── */
            QScrollBar:vertical {{
                background-color: #0d1720;
                width: 14px;
                border-left: 1px solid #2e4057;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #2e4057;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #4a6880;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background-color: #0d1720;
                height: 14px;
                border-top: 1px solid #2e4057;
                border-radius: 7px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #2e4057;
                border-radius: 6px;
                min-width: 20px;
                margin: 2px 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: #4a6880;
            }}
            /* ── Thor-hammer slider ──────────────────────────────────────────── */
            QSlider::groove:horizontal {{
                height: 6px;
                background: #1e2d3d;
                border: 1px solid #2e4057;
                border-radius: 0px;
            }}
            QSlider::handle:horizontal {{
                background: #5e81ac;
                border: 2px solid #88c0d0;
                width: 18px;
                height: 18px;
                border-radius: 0px;
                margin: -6px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: #88c0d0;
                border-color: #ebcb8b;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2e4057, stop:1 #5e81ac);
                border-radius: 0px;
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: #1e2d3d;
                color: #dde8f4;
                border: 2px solid #2e4057;
                border-radius: 2px;
                padding: 3px 5px;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: #88c0d0;
            }}
            /* ── Norse longhouse dock widgets ───────────────────────────────── */
            QDockWidget {{
                color: #dde8f4;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QDockWidget::title {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0d1720, stop:0.5 #1e2d3d, stop:1 #0d1720);
                padding: 5px 10px;
                border: 2px solid #2e4057;
                color: #88c0d0;
                font-weight: bold;
                text-align: center;
            }}
            /* ── Rune-stone status bar ───────────────────────────────────────── */
            QStatusBar {{
                background-color: #0d1720;
                color: #8aa4b8;
                border-top: 2px solid #2e4057;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QStatusBar::item {{
                border: none;
            }}
            /* ── Valhalla tooltip ────────────────────────────────────────────── */
            QToolTip {{
                background-color: #1e2d3d;
                color: #ebcb8b;
                border: 2px solid #4a6880;
                border-radius: 0px;
                padding: 4px 8px;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            /* ── Runic splitter handle ───────────────────────────────────────── */
            QSplitter::handle {{
                background-color: #2e4057;
            }}
            QSplitter::handle:horizontal {{
                width: 3px;
            }}
            QSplitter::handle:vertical {{
                height: 3px;
            }}
            """
        elif theme == 'dracula':
            # 🧛 Vampiric Dracula — crimson fangs, deep purple-black, blood-drip accents
            stylesheet = f"""
            QMainWindow {{ background-color: #1a0a1e; }}
            QWidget {{
                background-color: #1a0a1e;
                color: #f8f8f2;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QPushButton {{
                background-color: {accent};
                color: #f8f8f2;
                border: 2px solid #8b0000;
                padding: 8px 16px;
                border-radius: 0px 0px 8px 8px;
                font-weight: bold;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name()};
                border-color: #ff2244;
                color: #ff9999;
            }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; border-color: #cc0022; }}
            QPushButton:disabled {{ background-color: #2a0a2e; color: #6272a4; border-color: #44174a; }}
            QLabel {{ color: #f8f8f2; background-color: transparent; }}
            QGroupBox {{
                color: #bd93f9;
                border: 2px solid #8b0000;
                border-radius: 4px;
                margin-top: 8px;
                font-weight: bold;
            }}
            QGroupBox::title {{ color: #ff7eb3; subcontrol-position: top left; padding: 2px 6px; }}
            QTabWidget::pane {{ border: 2px solid #8b0000; background-color: #22042a; }}
            QTabBar::tab {{
                background-color: #2a0a30;
                color: #bd93f9;
                padding: 8px 20px;
                border: 2px solid #8b0000;
                border-bottom: none;
                border-radius: 6px 6px 0px 0px;
            }}
            QTabBar::tab:selected {{ background-color: #8b0000; color: #f8f8f2; border-color: #cc0022; }}
            QTabBar::tab:hover {{ background-color: #3a0a40; color: #ff9999; }}
            QMenuBar {{ background-color: #2a0a30; color: #f8f8f2; border-bottom: 2px solid #8b0000; }}
            QMenuBar::item:selected {{ background-color: #8b0000; }}
            QMenu {{ background-color: #2a0a30; color: #f8f8f2; border: 2px solid #8b0000; }}
            QMenu::item:selected {{ background-color: #8b0000; color: #f8f8f2; }}
            QProgressBar {{
                border: 2px solid #8b0000;
                border-radius: 0px;
                text-align: center;
                background-color: #2a0a30;
                color: #f8f8f2;
            }}
            QProgressBar::chunk {{ background-color: #cc0022; }}
            QFrame {{ background-color: #22042a; border: 2px solid #8b0000; border-radius: 4px; }}
            QTextEdit {{ background-color: #22042a; color: #f8f8f2; border: 2px solid #8b0000; font-family: 'Palatino Linotype', 'Georgia', serif; }}
            QLineEdit {{ background-color: #2a0a30; color: #f8f8f2; border: 2px solid #8b0000; border-radius: 3px; padding: 4px 6px; }}
            QLineEdit:focus {{ border: 2px solid #cc0022; }}
            QComboBox {{ background-color: #2a0a30; color: #f8f8f2; border: 2px solid #8b0000; border-radius: 0px 0px 6px 6px; padding: 4px 6px; min-height: 22px; }}
            QComboBox:hover {{ border-color: #cc0022; }}
            QComboBox QAbstractItemView {{ background-color: #2a0a30; color: #f8f8f2; border: 2px solid #8b0000; selection-background-color: #8b0000; }}
            QCheckBox {{ color: #f8f8f2; spacing: 6px; }}
            QCheckBox::indicator {{ width: 14px; height: 14px; border: 2px solid #8b0000; border-radius: 2px; background: #2a0a30; }}
            QCheckBox::indicator:checked {{ background: #8b0000; border-color: #cc0022; }}
            QScrollBar:vertical {{ background-color: #22042a; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background-color: #8b0000; border-radius: 6px; margin: 2px 2px; }}
            QScrollBar::handle:vertical:hover {{ background-color: #cc0022; }}
            QSlider::groove:horizontal {{ height: 6px; background: #2a0a30; border: 1px solid #8b0000; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: #8b0000; border: 2px solid #cc0022; width: 16px; height: 16px; border-radius: 8px; margin: -5px 0; }}
            QSlider::sub-page:horizontal {{ background: #8b0000; border-radius: 3px; }}
            QSpinBox, QDoubleSpinBox {{ background-color: #2a0a30; color: #f8f8f2; border: 2px solid #8b0000; border-radius: 3px; padding: 3px 5px; }}
            QDockWidget {{ color: #f8f8f2; titlebar-close-icon: none; }}
            QDockWidget::title {{ background-color: #8b0000; padding: 4px; color: #f8f8f2; }}
            QStatusBar {{ background-color: #22042a; color: #bd93f9; border-top: 2px solid #8b0000; }}
            """
        elif theme in ('solarized dark', 'solarized_dark'):
            stylesheet = f"""
            QMainWindow {{ background-color: #002b36; }}
            QWidget {{ background-color: #002b36; color: #839496; font-family: 'Segoe UI', Arial, sans-serif; }}
            QPushButton {{ background-color: {accent}; color: #fdf6e3; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {hover_color.name()}; }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; }}
            QPushButton:disabled {{ background-color: #073642; color: #586e75; }}
            QLabel {{ color: #839496; background-color: transparent; }}
            QTabWidget::pane {{ border: 1px solid #073642; background-color: #073642; }}
            QTabBar::tab {{ background-color: #073642; color: #839496; padding: 8px 20px; border: 1px solid #073642; border-bottom: none; }}
            QTabBar::tab:selected {{ background-color: {accent}; color: #fdf6e3; }}
            QTabBar::tab:hover {{ background-color: #0d4251; }}
            QMenuBar {{ background-color: #073642; color: #839496; border-bottom: 1px solid #073642; }}
            QMenuBar::item:selected {{ background-color: {accent}; color: #fdf6e3; }}
            QMenu {{ background-color: #073642; color: #839496; border: 1px solid #073642; }}
            QMenu::item:selected {{ background-color: {accent}; color: #fdf6e3; }}
            QProgressBar {{ border: 1px solid #073642; border-radius: 3px; text-align: center; background-color: #073642; color: #839496; }}
            QProgressBar::chunk {{ background-color: {accent}; }}
            QFrame {{ background-color: #073642; border: 1px solid #073642; border-radius: 4px; }}
            QTextEdit {{ background-color: #073642; color: #839496; border: 1px solid #073642; }}
            QScrollBar:vertical {{ background-color: #073642; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background-color: #586e75; border-radius: 6px; margin: 2px 2px; }}
            QDockWidget {{ color: #839496; titlebar-close-icon: none; }}
            QDockWidget::title {{ background-color: #073642; padding: 4px; }}
            """
        elif theme in ('forest', 'forest_green'):
            stylesheet = f"""
            QMainWindow {{ background-color: #1a2e1a; }}
            QWidget {{ background-color: #1a2e1a; color: #c8e6c9; font-family: 'Segoe UI', Arial, sans-serif; }}
            QPushButton {{ background-color: {accent}; color: #ffffff; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {hover_color.name()}; }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; }}
            QPushButton:disabled {{ background-color: #2d4a2d; color: #5a7a5a; }}
            QLabel {{ color: #c8e6c9; background-color: transparent; }}
            QTabWidget::pane {{ border: 1px solid #2d5a2d; background-color: #1e381e; }}
            QTabBar::tab {{ background-color: #243d24; color: #a5d6a7; padding: 8px 20px; border: 1px solid #2d5a2d; border-bottom: none; }}
            QTabBar::tab:selected {{ background-color: {accent}; color: #ffffff; }}
            QTabBar::tab:hover {{ background-color: #2e4f2e; }}
            QMenuBar {{ background-color: #1e381e; color: #c8e6c9; border-bottom: 1px solid #2d5a2d; }}
            QMenuBar::item:selected {{ background-color: {accent}; color: #ffffff; }}
            QMenu {{ background-color: #1e381e; color: #c8e6c9; border: 1px solid #2d5a2d; }}
            QMenu::item:selected {{ background-color: {accent}; color: #ffffff; }}
            QProgressBar {{ border: 1px solid #2d5a2d; border-radius: 3px; text-align: center; background-color: #1e381e; color: #c8e6c9; }}
            QProgressBar::chunk {{ background-color: {accent}; }}
            QFrame {{ background-color: #1e381e; border: 1px solid #2d5a2d; border-radius: 4px; }}
            QTextEdit {{ background-color: #1a2e1a; color: #c8e6c9; border: 1px solid #2d5a2d; }}
            QScrollBar:vertical {{ background-color: #1e381e; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background-color: #4a7a4a; border-radius: 6px; margin: 2px 2px; }}
            """
        elif theme in ('ocean', 'ocean_blue'):
            # 🌊 Ocean — deep-sea blues, coral accents, wave-styled borders
            stylesheet = f"""
            QMainWindow {{ background-color: #020e1c; }}
            QWidget {{ background-color: #020e1c; color: #b3e5fc; font-family: 'Segoe UI', Arial, sans-serif; }}
            QPushButton {{ background-color: {accent}; color: #ffffff; border: 2px solid #00b4d8; padding: 8px 16px; border-radius: 16px 4px 16px 4px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {hover_color.name()}; border-color: #ff6b6b; color: #ffe0e0; }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; border-color: #00b4d8; }}
            QPushButton:disabled {{ background-color: #052040; color: #3a6080; border-color: #0a3050; }}
            QLabel {{ color: #b3e5fc; background-color: transparent; }}
            QGroupBox {{ color: #4dd0e1; border: 2px solid #00b4d8; border-radius: 8px; margin-top: 8px; font-weight: bold; }}
            QGroupBox::title {{ color: #ff6b6b; subcontrol-position: top left; padding: 2px 6px; }}
            QTabWidget::pane {{ border: 2px solid #00b4d8; background-color: #031426; }}
            QTabBar::tab {{ background-color: #052040; color: #80deea; padding: 8px 20px; border: 2px solid #00b4d8; border-bottom: none; border-radius: 10px 10px 0px 0px; }}
            QTabBar::tab:selected {{ background-color: #00b4d8; color: #ffffff; border-color: #00e5ff; }}
            QTabBar::tab:hover {{ background-color: #063050; color: #e0f7fa; }}
            QMenuBar {{ background-color: #031426; color: #b3e5fc; border-bottom: 2px solid #00b4d8; }}
            QMenuBar::item:selected {{ background-color: #00b4d8; color: #ffffff; }}
            QMenu {{ background-color: #031426; color: #b3e5fc; border: 2px solid #00b4d8; }}
            QMenu::item:selected {{ background-color: #00b4d8; color: #ffffff; }}
            QProgressBar {{ border: 2px solid #00b4d8; border-radius: 8px; text-align: center; background-color: #031426; color: #b3e5fc; }}
            QProgressBar::chunk {{ background-color: #00b4d8; border-radius: 6px; }}
            QFrame {{ background-color: #031426; border: 2px solid #00b4d8; border-radius: 8px; }}
            QTextEdit {{ background-color: #020e1c; color: #b3e5fc; border: 2px solid #00b4d8; border-radius: 4px; }}
            QLineEdit {{ background-color: #052040; color: #b3e5fc; border: 2px solid #00b4d8; border-radius: 4px; padding: 4px 6px; }}
            QLineEdit:focus {{ border-color: #00e5ff; }}
            QComboBox {{ background-color: #052040; color: #b3e5fc; border: 2px solid #00b4d8; border-radius: 12px 4px 12px 4px; padding: 4px 6px; min-height: 22px; }}
            QComboBox:hover {{ border-color: #ff6b6b; }}
            QComboBox QAbstractItemView {{ background-color: #052040; color: #b3e5fc; border: 2px solid #00b4d8; selection-background-color: #00b4d8; }}
            QCheckBox {{ color: #b3e5fc; spacing: 6px; }}
            QCheckBox::indicator {{ width: 14px; height: 14px; border: 2px solid #00b4d8; border-radius: 7px; background: #052040; }}
            QCheckBox::indicator:checked {{ background: #00b4d8; border-color: #00e5ff; }}
            QScrollBar:vertical {{ background-color: #031426; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background-color: #00b4d8; border-radius: 6px; margin: 2px 2px; }}
            QScrollBar::handle:vertical:hover {{ background-color: #00e5ff; }}
            QSlider::groove:horizontal {{ height: 6px; background: #052040; border: 1px solid #00b4d8; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: #00b4d8; border: 2px solid #00e5ff; width: 16px; height: 16px; border-radius: 8px; margin: -5px 0; }}
            QSlider::sub-page:horizontal {{ background: #00b4d8; border-radius: 3px; }}
            QSpinBox, QDoubleSpinBox {{ background-color: #052040; color: #b3e5fc; border: 2px solid #00b4d8; border-radius: 3px; padding: 3px 5px; }}
            QDockWidget {{ color: #b3e5fc; titlebar-close-icon: none; }}
            QDockWidget::title {{ background-color: #00b4d8; padding: 4px; color: #ffffff; }}
            QStatusBar {{ background-color: #031426; color: #4dd0e1; border-top: 2px solid #00b4d8; }}
            """
        elif theme in ('sunset', 'sunset_warm'):
            stylesheet = f"""
            QMainWindow {{ background-color: #2a1a0e; }}
            QWidget {{ background-color: #2a1a0e; color: #f5cba7; font-family: 'Segoe UI', Arial, sans-serif; }}
            QPushButton {{ background-color: {accent}; color: #ffffff; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {hover_color.name()}; }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; }}
            QPushButton:disabled {{ background-color: #3d2510; color: #7a5030; }}
            QLabel {{ color: #f5cba7; background-color: transparent; }}
            QTabWidget::pane {{ border: 1px solid #5a3520; background-color: #321e0f; }}
            QTabBar::tab {{ background-color: #321e0f; color: #e8b07a; padding: 8px 20px; border: 1px solid #5a3520; border-bottom: none; }}
            QTabBar::tab:selected {{ background-color: {accent}; color: #ffffff; }}
            QTabBar::tab:hover {{ background-color: #3e2614; }}
            QMenuBar {{ background-color: #321e0f; color: #f5cba7; border-bottom: 1px solid #5a3520; }}
            QMenuBar::item:selected {{ background-color: {accent}; color: #ffffff; }}
            QMenu {{ background-color: #321e0f; color: #f5cba7; border: 1px solid #5a3520; }}
            QMenu::item:selected {{ background-color: {accent}; color: #ffffff; }}
            QProgressBar {{ border: 1px solid #5a3520; border-radius: 3px; text-align: center; background-color: #321e0f; color: #f5cba7; }}
            QProgressBar::chunk {{ background-color: {accent}; }}
            QFrame {{ background-color: #321e0f; border: 1px solid #5a3520; border-radius: 4px; }}
            QTextEdit {{ background-color: #2a1a0e; color: #f5cba7; border: 1px solid #5a3520; }}
            QScrollBar:vertical {{ background-color: #321e0f; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background-color: #8a5030; border-radius: 6px; margin: 2px 2px; }}
            """
        elif theme in ('cyberpunk',):
            stylesheet = f"""
            QMainWindow {{ background-color: #0d0d1a; }}
            QWidget {{ background-color: #0d0d1a; color: #00ffcc; font-family: 'Courier New', monospace; }}
            QPushButton {{ background-color: {accent}; color: #000000; border: 1px solid #00ffcc; padding: 8px 16px; border-radius: 2px; font-weight: bold; font-family: 'Courier New', monospace; }}
            QPushButton:hover {{ background-color: {hover_color.name()}; border-color: #ff00aa; color: #ff00aa; }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; }}
            QPushButton:disabled {{ background-color: #1a1a2e; color: #336655; border-color: #336655; }}
            QLabel {{ color: #00ffcc; background-color: transparent; }}
            QTabWidget::pane {{ border: 1px solid #00ffcc; background-color: #0d0d1a; }}
            QTabBar::tab {{ background-color: #0d0d1a; color: #00ffcc; padding: 8px 20px; border: 1px solid #00ffcc; border-bottom: none; }}
            QTabBar::tab:selected {{ background-color: {accent}; color: #000000; }}
            QTabBar::tab:hover {{ background-color: #1a1a2e; color: #ff00aa; }}
            QMenuBar {{ background-color: #0d0d1a; color: #00ffcc; border-bottom: 1px solid #00ffcc; }}
            QMenuBar::item:selected {{ background-color: {accent}; color: #000000; }}
            QMenu {{ background-color: #0d0d1a; color: #00ffcc; border: 1px solid #00ffcc; }}
            QMenu::item:selected {{ background-color: {accent}; color: #000000; }}
            QProgressBar {{ border: 1px solid #00ffcc; border-radius: 1px; text-align: center; background-color: #0d0d1a; color: #00ffcc; }}
            QProgressBar::chunk {{ background-color: {accent}; }}
            QFrame {{ background-color: #0d0d1a; border: 1px solid #00ffcc; border-radius: 2px; }}
            QTextEdit {{ background-color: #0d0d1a; color: #00ffcc; border: 1px solid #00ffcc; font-family: 'Courier New', monospace; }}
            QScrollBar:vertical {{ background-color: #0d0d1a; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background-color: #00ffcc; border-radius: 6px; margin: 2px 2px; }}
            """
        elif theme in ('gore',):
            # 💀 Gore — blood-soaked, dripping, organ-coloured UI with click splatter
            stylesheet = f"""
            QMainWindow {{ background-color: #0d0000; }}
            QWidget {{
                background-color: #0d0000;
                color: #ffaaaa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QPushButton {{
                background-color: {accent};
                color: #ffdddd;
                border: 3px solid #8b0000;
                padding: 8px 16px;
                border-radius: 4px 4px 0px 0px;
                font-weight: bold;
                border-bottom: 6px solid #660000;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name()};
                border-color: #ff0000;
                border-bottom: 6px solid #cc0000;
                color: #ffffff;
            }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; border-color: #440000; }}
            QPushButton:disabled {{ background-color: #2a0000; color: #663333; border-color: #3a0000; }}
            QLabel {{ color: #ffaaaa; background-color: transparent; }}
            QGroupBox {{
                color: #ff4444;
                border: 3px solid #8b0000;
                border-radius: 2px;
                margin-top: 8px;
                font-weight: bold;
            }}
            QGroupBox::title {{ color: #ff2222; subcontrol-position: top left; padding: 2px 6px; }}
            QTabWidget::pane {{ border: 3px solid #8b0000; background-color: #140000; }}
            QTabBar::tab {{
                background-color: #1a0000;
                color: #ff6666;
                padding: 8px 20px;
                border: 2px solid #8b0000;
                border-bottom: none;
                border-radius: 4px 4px 0px 0px;
            }}
            QTabBar::tab:selected {{ background-color: #8b0000; color: #ffdddd; border-color: #cc0000; }}
            QTabBar::tab:hover {{ background-color: #260000; color: #ff9999; }}
            QMenuBar {{ background-color: #140000; color: #ffaaaa; border-bottom: 3px solid #8b0000; }}
            QMenuBar::item:selected {{ background-color: #8b0000; color: #ffffff; }}
            QMenu {{ background-color: #140000; color: #ffaaaa; border: 3px solid #8b0000; }}
            QMenu::item:selected {{ background-color: #8b0000; color: #ffffff; }}
            QProgressBar {{
                border: 3px solid #8b0000;
                border-radius: 0px;
                text-align: center;
                background-color: #140000;
                color: #ffaaaa;
            }}
            QProgressBar::chunk {{ background-color: #cc0000; }}
            QFrame {{ background-color: #140000; border: 3px solid #8b0000; border-radius: 2px; }}
            QTextEdit {{ background-color: #0d0000; color: #ffaaaa; border: 3px solid #8b0000; }}
            QLineEdit {{ background-color: #1a0000; color: #ffaaaa; border: 3px solid #8b0000; border-radius: 2px; padding: 4px 6px; }}
            QLineEdit:focus {{ border-color: #ff0000; }}
            QComboBox {{ background-color: #1a0000; color: #ffaaaa; border: 3px solid #8b0000; border-radius: 2px; padding: 4px 6px; min-height: 22px; }}
            QComboBox:hover {{ border-color: #ff0000; }}
            QComboBox QAbstractItemView {{ background-color: #1a0000; color: #ffaaaa; border: 2px solid #8b0000; selection-background-color: #8b0000; }}
            QCheckBox {{ color: #ffaaaa; spacing: 6px; }}
            QCheckBox::indicator {{ width: 14px; height: 14px; border: 3px solid #8b0000; border-radius: 2px; background: #1a0000; }}
            QCheckBox::indicator:checked {{ background: #8b0000; border-color: #ff0000; }}
            QScrollBar:vertical {{ background-color: #140000; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background-color: #8b0000; border-radius: 6px; margin: 2px 2px; }}
            QScrollBar::handle:vertical:hover {{ background-color: #cc0000; }}
            QSlider::groove:horizontal {{ height: 6px; background: #1a0000; border: 2px solid #8b0000; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: #8b0000; border: 2px solid #cc0000; width: 16px; height: 16px; border-radius: 2px; margin: -5px 0; }}
            QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4d0000, stop:1 #cc0000); border-radius: 2px; }}
            QSpinBox, QDoubleSpinBox {{ background-color: #1a0000; color: #ffaaaa; border: 3px solid #8b0000; border-radius: 2px; padding: 3px 5px; }}
            QDockWidget {{ color: #ffaaaa; titlebar-close-icon: none; }}
            QDockWidget::title {{ background-color: #8b0000; padding: 4px; color: #ffdddd; }}
            QStatusBar {{ background-color: #140000; color: #ff4444; border-top: 3px solid #8b0000; }}
            """
        elif theme in ('goth',):
            # 💀 Goth — pure black, dark purple/grey, gothic grunge aesthetic
            stylesheet = f"""
            QMainWindow {{ background-color: #000000; }}
            QWidget {{
                background-color: #000000;
                color: #c0b0d0;
                font-family: 'Palatino Linotype', 'Georgia', 'Times New Roman', serif;
            }}
            QPushButton {{
                background-color: {accent};
                color: #e0d0f0;
                border: 2px solid #4a2060;
                padding: 8px 16px;
                border-radius: 0px;
                font-weight: bold;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name()};
                border-color: #8844aa;
                color: #ffffff;
            }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; border-color: #220033; }}
            QPushButton:disabled {{ background-color: #0d0d0d; color: #443355; border-color: #221133; }}
            QLabel {{ color: #c0b0d0; background-color: transparent; }}
            QGroupBox {{
                color: #9966bb;
                border: 2px solid #4a2060;
                border-radius: 0px;
                margin-top: 8px;
                font-weight: bold;
            }}
            QGroupBox::title {{ color: #bb88dd; subcontrol-position: top left; padding: 2px 6px; }}
            QTabWidget::pane {{
                border: 2px solid #4a2060;
                background-color: #050005;
            }}
            QTabBar::tab {{
                background-color: #0a000f;
                color: #9966bb;
                padding: 8px 20px;
                border: 2px solid #4a2060;
                border-bottom: none;
                border-radius: 0px;
            }}
            QTabBar::tab:selected {{ background-color: #1a0028; color: #e0d0f0; border-color: #8844aa; }}
            QTabBar::tab:hover {{ background-color: #120018; color: #cc99ee; }}
            QMenuBar {{ background-color: #050005; color: #c0b0d0; border-bottom: 2px solid #4a2060; }}
            QMenuBar::item:selected {{ background-color: #1a0028; color: #e0d0f0; }}
            QMenu {{ background-color: #050005; color: #c0b0d0; border: 2px solid #4a2060; }}
            QMenu::item:selected {{ background-color: #1a0028; color: #e0d0f0; }}
            QProgressBar {{
                border: 2px solid #4a2060;
                border-radius: 0px;
                text-align: center;
                background-color: #0a000f;
                color: #c0b0d0;
            }}
            QProgressBar::chunk {{ background-color: #4a2060; }}
            QFrame {{ background-color: #050005; border: 2px solid #4a2060; border-radius: 0px; }}
            QTextEdit {{ background-color: #000000; color: #c0b0d0; border: 2px solid #4a2060; font-family: 'Palatino Linotype', 'Georgia', serif; }}
            QLineEdit {{ background-color: #0a000f; color: #c0b0d0; border: 2px solid #4a2060; border-radius: 0px; padding: 4px 6px; }}
            QLineEdit:focus {{ border-color: #8844aa; }}
            QComboBox {{ background-color: #0a000f; color: #c0b0d0; border: 2px solid #4a2060; border-radius: 0px; padding: 4px 6px; min-height: 22px; }}
            QComboBox:hover {{ border-color: #8844aa; }}
            QComboBox QAbstractItemView {{ background-color: #0a000f; color: #c0b0d0; border: 2px solid #4a2060; selection-background-color: #1a0028; }}
            QCheckBox {{ color: #c0b0d0; spacing: 6px; }}
            QCheckBox::indicator {{ width: 14px; height: 14px; border: 2px solid #4a2060; border-radius: 0px; background: #0a000f; }}
            QCheckBox::indicator:checked {{ background: #4a2060; border-color: #8844aa; }}
            QScrollBar:vertical {{ background-color: #050005; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background-color: #4a2060; border-radius: 6px; margin: 2px 2px; }}
            QScrollBar::handle:vertical:hover {{ background-color: #6a3090; }}
            QSlider::groove:horizontal {{ height: 6px; background: #0a000f; border: 1px solid #4a2060; border-radius: 0px; }}
            QSlider::handle:horizontal {{ background: #4a2060; border: 2px solid #8844aa; width: 16px; height: 16px; border-radius: 0px; margin: -5px 0; }}
            QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #220033, stop:1 #6a3090); border-radius: 0px; }}
            QSpinBox, QDoubleSpinBox {{ background-color: #0a000f; color: #c0b0d0; border: 2px solid #4a2060; border-radius: 0px; padding: 3px 5px; }}
            QDockWidget {{ color: #c0b0d0; titlebar-close-icon: none; }}
            QDockWidget::title {{ background-color: #1a0028; padding: 4px; color: #9966bb; }}
            QStatusBar {{ background-color: #050005; color: #9966bb; border-top: 2px solid #4a2060; }}
            """
        elif theme in ('vampire',):
            # 🦇 Vampire — crimson blood on midnight black, bat-spawn click effect
            stylesheet = f"""
            QMainWindow {{ background-color: #080010; }}
            QWidget {{
                background-color: #080010;
                color: #e8c0e8;
                font-family: 'Palatino Linotype', 'Georgia', serif;
            }}
            QPushButton {{
                background-color: {accent};
                color: #f0d0f0;
                border: 2px solid #7a0030;
                padding: 7px 16px;
                border-radius: 3px;
                font-weight: bold;
                border-bottom: 4px solid #550020;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name()};
                border-color: #cc0044;
                color: #ffffff;
            }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; border-color: #330015; }}
            QPushButton:disabled {{ background-color: #1a0022; color: #553355; border-color: #2a0035; }}
            QLabel {{ color: #e8c0e8; background-color: transparent; min-height: 18px; }}
            QGroupBox {{
                color: #cc44aa;
                border: 2px solid #7a0030;
                border-radius: 4px;
                margin-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{ color: #ff44aa; subcontrol-position: top left; padding: 2px 8px; min-width: 40px; }}
            QTabWidget::pane {{ border: 2px solid #7a0030; background-color: #0d001a; }}
            QTabBar::tab {{
                background-color: #12001e;
                color: #cc88cc;
                padding: 8px 18px;
                min-width: 70px;
                border: 2px solid #7a0030;
                border-bottom: none;
                border-radius: 4px 4px 0px 0px;
            }}
            QTabBar::tab:selected {{ background-color: #7a0030; color: #f0d0f0; border-color: #cc0044; }}
            QTabBar::tab:hover {{ background-color: #1e0030; color: #ffaaee; }}
            QMenuBar {{ background-color: #0d001a; color: #e8c0e8; border-bottom: 2px solid #7a0030; }}
            QMenuBar::item:selected {{ background-color: #7a0030; color: #ffffff; }}
            QMenu {{ background-color: #0d001a; color: #e8c0e8; border: 2px solid #7a0030; }}
            QMenu::item:selected {{ background-color: #7a0030; color: #ffffff; }}
            QProgressBar {{ border: 2px solid #7a0030; border-radius: 3px; text-align: center; background-color: #0d001a; color: #e8c0e8; }}
            QProgressBar::chunk {{ background-color: #cc0044; }}
            QFrame {{ background-color: #0d001a; border: 2px solid #7a0030; border-radius: 4px; }}
            QTextEdit {{ background-color: #080010; color: #e8c0e8; border: 2px solid #7a0030; }}
            QLineEdit {{ background-color: #12001e; color: #e8c0e8; border: 2px solid #7a0030; border-radius: 3px; padding: 4px 6px; }}
            QLineEdit:focus {{ border-color: #cc0044; }}
            QComboBox {{ background-color: #12001e; color: #e8c0e8; border: 2px solid #7a0030; border-radius: 3px; padding: 4px 6px; min-height: 22px; }}
            QComboBox:hover {{ border-color: #cc0044; }}
            QComboBox QAbstractItemView {{ background-color: #12001e; color: #e8c0e8; border: 2px solid #7a0030; selection-background-color: #7a0030; }}
            QCheckBox {{ color: #e8c0e8; spacing: 6px; }}
            QCheckBox::indicator {{ width: 14px; height: 14px; border: 2px solid #7a0030; border-radius: 2px; background: #12001e; }}
            QCheckBox::indicator:checked {{ background: #7a0030; border-color: #cc0044; }}
            QScrollBar:vertical {{ background-color: #0d001a; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background-color: #7a0030; border-radius: 6px; margin: 2px 2px; }}
            QScrollBar::handle:vertical:hover {{ background-color: #cc0044; }}
            QSlider::groove:horizontal {{ height: 6px; background: #12001e; border: 1px solid #7a0030; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: #7a0030; border: 2px solid #cc0044; width: 16px; height: 16px; border-radius: 3px; margin: -5px 0; }}
            QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a0018, stop:1 #cc0044); border-radius: 3px; }}
            QSpinBox, QDoubleSpinBox {{ background-color: #12001e; color: #e8c0e8; border: 2px solid #7a0030; border-radius: 3px; padding: 3px 5px; }}
            QDockWidget {{ color: #e8c0e8; titlebar-close-icon: none; }}
            QDockWidget::title {{ background-color: #7a0030; padding: 4px; color: #f0d0f0; }}
            QStatusBar {{ background-color: #0d001a; color: #cc44aa; border-top: 2px solid #7a0030; }}
            """
        else:  # Dark theme (default)
            stylesheet = f"""
            QMainWindow {{
                background-color: #1e1e1e;
            }}
            QWidget {{
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QPushButton {{
                background-color: {accent};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color.name()};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color.name()};
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #999999;
            }}
            QLineEdit {{
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 6px;
                selection-background-color: {accent};
            }}
            QLineEdit:focus {{
                border: 2px solid {accent};
            }}
            QLineEdit:read-only {{
                background-color: #232323;
                color: #aaaaaa;
            }}
            QComboBox {{
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 6px;
                min-height: 22px;
            }}
            QComboBox:hover {{
                border: 1px solid {accent};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #aaaaaa;
                width: 0;
                height: 0;
                margin-right: 4px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555555;
                selection-background-color: {accent};
            }}
            QCheckBox {{
                spacing: 6px;
                color: #e0e0e0;
            }}
            QCheckBox::indicator {{
                width: 15px;
                height: 15px;
                border: 2px solid #666666;
                border-radius: 3px;
                background: #2a2a2a;
            }}
            QCheckBox::indicator:checked {{
                background: {accent};
                border: 2px solid {accent};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {hover_color.name()};
            }}
            QSpinBox, QDoubleSpinBox {{
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px 5px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {accent};
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: #333333;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {accent};
                border: 2px solid {hover_color.name()};
                width: 16px;
                height: 16px;
                border-radius: 9px;
                margin: -5px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: {hover_color.name()};
            }}
            QSlider::sub-page:horizontal {{
                background: {accent};
                border-radius: 3px;
            }}
            QLabel {{
                color: #ffffff;
                background-color: transparent;
            }}
            QTabWidget::pane {{
                border: 1px solid #333333;
                background-color: #252525;
            }}
            QTabBar::tab {{
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 8px 20px;
                border: 1px solid #333333;
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {accent};
            }}
            QTabBar::tab:hover {{
                background-color: #3d3d3d;
            }}
            QMenuBar {{
                background-color: #2d2d2d;
                color: #ffffff;
                border-bottom: 1px solid #333333;
            }}
            QMenuBar::item:selected {{
                background-color: {accent};
            }}
            QMenu {{
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #333333;
            }}
            QMenu::item:selected {{
                background-color: {accent};
            }}
            QProgressBar {{
                border: 1px solid #333333;
                border-radius: 3px;
                text-align: center;
                background-color: #2d2d2d;
                color: #ffffff;
            }}
            QProgressBar::chunk {{
                background-color: {accent};
            }}
            QFrame {{
                background-color: #252525;
                border: 1px solid #333333;
                border-radius: 4px;
            }}
            QTextEdit {{
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
            }}
            QScrollBar:vertical {{
                background-color: #1a1a1a;
                width: 14px;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {hover_color.name()};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background-color: #1a1a1a;
                height: 14px;
                border-radius: 7px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #555555;
                border-radius: 6px;
                min-width: 20px;
                margin: 2px 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {hover_color.name()};
            }}
            """
        # ── Common layout-fix overrides to prevent text clipping across themes ──
        # These are appended to every theme so individual themes don't need to
        # repeat them.  They set minimum sizes on elements that Qt can otherwise
        # clip when the window is narrow or when emoji/Unicode characters in tab
        # labels require extra horizontal space.
        _LAYOUT_FIXES = """
            QTabBar::tab { min-width: 70px; }
            QGroupBox::title { min-width: 30px; }
            QLabel { min-height: 16px; }
            QToolTip { padding: 4px 6px; }
        """
        self.setStyleSheet(stylesheet + _LAYOUT_FIXES)
        self.apply_cursor()
        # Apply pointer cursor to interactive widgets application-wide after
        # the stylesheet is applied.  Qt6 QSS does not support 'cursor: pointer'
        # so we use an installEventFilter-based approach via the PointingCursorFilter
        # (see _install_pointing_cursor_filter).
        self._install_pointing_cursor_filter()
        # Re-apply cursor trail on theme change (overlay may have been covered)
        trail_enabled = bool(config.get('ui', 'cursor_trail', default=False))
        self._apply_cursor_trail(trail_enabled)

        # ── Gore theme: install/remove blood-splatter click filter ────────────
        self._update_gore_splatter(theme)

        # ── Vampire theme: install/remove bat-spawn click filter ──────────────
        self._update_vampire_bats(theme)

        # ── Ocean theme: install/remove ripple click filter ───────────────────
        self._update_ocean_ripple(theme)

        # ── Goth theme: install/remove skull-float click filter ───────────────
        self._update_goth_skulls(theme)

        # ── Dracula theme: install/remove blood-drip click filter ─────────────
        self._update_dracula_drops(theme)

        # ── Nord theme: Norse mythology window decorations ─────────────────────
        self._update_nord_runes(theme)

        # Unlock theme-related achievements
        try:
            if self.achievement_system:
                self.achievement_system.unlock_achievement('theme_switcher')
                _theme_ach = {
                    'dark': 'dark_side',
                    'nord': 'nordic_explorer',
                    'dracula': 'shadow_walker',
                    'solarized_dark': 'bamboo_sage',
                    'light': 'angelic_sorter',
                    'forest': 'bamboo_sage',
                    'ocean': 'pirate_adventure',
                    'sunset': 'golden_touch',
                    'cyberpunk': 'thunderstruck',
                    'gore': 'shadow_walker',   # closest existing dark achievement
                    'goth': 'shadow_walker',
                    'vampire': 'shadow_walker',
                }
                ach_id = _theme_ach.get(theme)
                if ach_id:
                    self.achievement_system.unlock_achievement(ach_id)
        except Exception:
            pass

    def _install_pointing_cursor_filter(self) -> None:
        """Walk all child widgets and set PointingHandCursor on interactive ones.

        Qt6 QSS does NOT support 'cursor: pointer' — that CSS property is silently
        ignored (producing 'Unknown property cursor' warnings).  The correct Qt6
        way is to call setCursor() on each widget.  We do it post-theme-application
        so the cursor sticks even after style reloads.
        """
        try:
            from PyQt6.QtWidgets import (QComboBox, QTabBar, QSlider,
                                          QAbstractButton)
            from PyQt6.QtCore import Qt
            _hand = Qt.CursorShape.PointingHandCursor
            for child in self.findChildren(QAbstractButton):
                child.setCursor(_hand)
            for child in self.findChildren(QComboBox):
                child.setCursor(_hand)
            for child in self.findChildren(QSlider):
                child.setCursor(_hand)
            for child in self.findChildren(QTabBar):
                child.setCursor(_hand)
        except Exception as e:
            logger.debug(f"_install_pointing_cursor_filter: {e}")

    def _update_gore_splatter(self, theme: str) -> None:
        """Install or remove the GoreSplatterFilter depending on the active theme."""
        try:
            from PyQt6.QtWidgets import QApplication as _QA
            _app = _QA.instance()
            if _app is None:
                return
            want_gore = (theme == 'gore')
            if want_gore and self._gore_splatter_filter is None:
                self._gore_splatter_filter = GoreSplatterFilter(self)
                _app.installEventFilter(self._gore_splatter_filter)
                logger.info("🩸 Gore splatter filter installed")
            elif not want_gore and self._gore_splatter_filter is not None:
                _app.removeEventFilter(self._gore_splatter_filter)
                self._gore_splatter_filter = None
                logger.info("Gore splatter filter removed")
        except Exception as _e:
            logger.debug(f"_update_gore_splatter: {_e}")

    def _update_vampire_bats(self, theme: str) -> None:
        """Install or remove the VampireBatFilter depending on the active theme."""
        try:
            from PyQt6.QtWidgets import QApplication as _QA
            _app = _QA.instance()
            if _app is None:
                return
            want = (theme == 'vampire')
            if want and self._vampire_bat_filter is None:
                self._vampire_bat_filter = VampireBatFilter(self)
                _app.installEventFilter(self._vampire_bat_filter)
                # Decorate window title with bat symbols
                _title = self.windowTitle()
                if not _title.startswith("🦇 "):
                    self.setWindowTitle(f"🦇 {_title.strip()} 🦇")
                logger.info("🦇 Vampire bat filter installed")
            elif not want and self._vampire_bat_filter is not None:
                _app.removeEventFilter(self._vampire_bat_filter)
                self._vampire_bat_filter = None
                # Remove bat window title decoration
                _title = self.windowTitle()
                if _title.startswith("🦇 ") or _title.endswith(" 🦇"):
                    self.setWindowTitle(
                        _title.removeprefix("🦇 ").removesuffix(" 🦇").strip()
                    )
                logger.info("Vampire bat filter removed")
        except Exception as _e:
            logger.debug(f"_update_vampire_bats: {_e}")

    def _update_ocean_ripple(self, theme: str) -> None:
        """Install or remove the OceanRippleFilter and ambient-creature timer."""
        try:
            from PyQt6.QtWidgets import QApplication as _QA
            _app = _QA.instance()
            if _app is None:
                return
            want = (theme in ('ocean', 'ocean_blue'))
            if want and self._ocean_ripple_filter is None:
                self._ocean_ripple_filter = OceanRippleFilter(self)
                _app.installEventFilter(self._ocean_ripple_filter)
                # Decorate window title with ocean creature symbols
                _title = self.windowTitle()
                if not _title.startswith("🐙 "):
                    self.setWindowTitle(f"🐙 {_title.strip()} 🐠")
                logger.info("🌊 Ocean ripple filter installed")
                # Ambient creatures — drift a sea creature across every ~14 s
                if self._ocean_ambient_timer is None:
                    self._ocean_ambient_timer = QTimer(self)
                    self._ocean_ambient_timer.setInterval(14000)
                    self._ocean_ambient_timer.timeout.connect(self._spawn_ocean_creature)
                    self._ocean_ambient_timer.start()
                    # Spawn one immediately so the effect is visible right away
                    QTimer.singleShot(1200, self._spawn_ocean_creature)
            elif not want and self._ocean_ripple_filter is not None:
                _app.removeEventFilter(self._ocean_ripple_filter)
                self._ocean_ripple_filter = None
                # Remove ocean title decoration
                _title = self.windowTitle()
                if _title.startswith("🐙 ") or _title.endswith(" 🐠"):
                    self.setWindowTitle(
                        _title.removeprefix("🐙 ").removesuffix(" 🐠").strip()
                    )
                logger.info("Ocean ripple filter removed")
                # Stop ambient timer
                if self._ocean_ambient_timer is not None:
                    self._ocean_ambient_timer.stop()
                    self._ocean_ambient_timer = None
        except Exception as _e:
            logger.debug(f"_update_ocean_ripple: {_e}")

    def _spawn_ocean_creature(self) -> None:
        """Spawn one ambient OceanAmbientCreature drifting across the window."""
        try:
            if self.isVisible() and self.width() > 200:
                OceanAmbientCreature(self)
        except Exception:
            pass

    def _update_goth_skulls(self, theme: str) -> None:
        """Install/remove the GothSkullFilter and ambient-spider timer."""
        try:
            _app = QApplication.instance()
            if _app is None:
                return
            want = (theme == 'goth')
            if want and self._goth_skull_filter is None:
                self._goth_skull_filter = GothSkullFilter(self)
                _app.installEventFilter(self._goth_skull_filter)
                # Decorate window title with skull symbols
                _title = self.windowTitle()
                if not _title.startswith("💀 "):
                    self.setWindowTitle(f"💀 {_title.strip()} 💀")
                logger.info("💀 Goth skull filter installed")
                # Ambient spiders — drop one from top every ~12 s
                if self._goth_ambient_timer is None:
                    self._goth_ambient_timer = QTimer(self)
                    self._goth_ambient_timer.setInterval(12000)
                    self._goth_ambient_timer.timeout.connect(self._spawn_goth_spider)
                    self._goth_ambient_timer.start()
                    QTimer.singleShot(2000, self._spawn_goth_spider)
            elif not want and self._goth_skull_filter is not None:
                _app.removeEventFilter(self._goth_skull_filter)
                self._goth_skull_filter = None
                # Remove skull window title decoration
                _title = self.windowTitle()
                if _title.startswith("💀 ") or _title.endswith(" 💀"):
                    self.setWindowTitle(
                        _title.removeprefix("💀 ").removesuffix(" 💀").strip()
                    )
                logger.info("Goth skull filter removed")
                if self._goth_ambient_timer is not None:
                    self._goth_ambient_timer.stop()
                    self._goth_ambient_timer = None
        except Exception as _e:
            logger.debug(f"_update_goth_skulls: {_e}")

    def _spawn_goth_spider(self) -> None:
        """Spawn one ambient GothAmbientSpider descending from the window top."""
        try:
            if self.isVisible() and self.width() > 200:
                GothAmbientSpider(self)
        except Exception:
            pass

    def _update_dracula_drops(self, theme: str) -> None:
        """Install/remove the DraculaDropFilter and ambient-bat timer."""
        try:
            _app = QApplication.instance()
            if _app is None:
                return
            want = (theme == 'dracula')
            if want and self._dracula_drop_filter is None:
                self._dracula_drop_filter = DraculaDropFilter(self)
                _app.installEventFilter(self._dracula_drop_filter)
                # Decorate window title with blood drop symbols
                _title = self.windowTitle()
                if not _title.startswith("🩸 "):
                    self.setWindowTitle(f"🩸 {_title.strip()} 🩸")
                logger.info("🩸 Dracula drop filter installed")
                # Ambient bats — fly one across the window top every ~11 s
                if self._dracula_ambient_timer is None:
                    self._dracula_ambient_timer = QTimer(self)
                    self._dracula_ambient_timer.setInterval(11000)
                    self._dracula_ambient_timer.timeout.connect(self._spawn_dracula_bat)
                    self._dracula_ambient_timer.start()
                    QTimer.singleShot(1500, self._spawn_dracula_bat)
            elif not want and self._dracula_drop_filter is not None:
                _app.removeEventFilter(self._dracula_drop_filter)
                self._dracula_drop_filter = None
                # Remove blood drop title decoration
                _title = self.windowTitle()
                if _title.startswith("🩸 ") or _title.endswith(" 🩸"):
                    self.setWindowTitle(
                        _title.removeprefix("🩸 ").removesuffix(" 🩸").strip()
                    )
                logger.info("Dracula drop filter removed")
                if self._dracula_ambient_timer is not None:
                    self._dracula_ambient_timer.stop()
                    self._dracula_ambient_timer = None
        except Exception as _e:
            logger.debug(f"_update_dracula_drops: {_e}")

    def _spawn_dracula_bat(self) -> None:
        """Spawn one ambient DraculaAmbientBat swooping across the window."""
        try:
            if self.isVisible() and self.width() > 200:
                DraculaAmbientBat(self)
        except Exception:
            pass

    def _update_nord_runes(self, theme: str) -> None:
        """Decorate the window title with Elder Futhark runes when the Nord
        theme is active; remove decorations for all other themes.

        The rune ᚱ (Raido — journey) frames the title on both sides,
        representing the user's creative journey through their textures.
        """
        _RUNE = "ᚱ"    # Raido: journey, movement — same symbol on both sides
        try:
            title = self.windowTitle()
            if theme == 'nord':
                # Add rune brackets if not already present
                if not (title.startswith(_RUNE + " ") and title.endswith(" " + _RUNE)):
                    # Strip any pre-existing ᚱ decoration before re-applying
                    clean = title.replace("ᚱ ", "").replace(" ᚱ", "")
                    self.setWindowTitle(f"{_RUNE} {clean.strip()} {_RUNE}")
                logger.debug("⚔️  Nord rune window decorations applied")
            else:
                # Remove rune decorations if they were previously added
                if title.startswith(_RUNE + " ") and title.endswith(" " + _RUNE):
                    self.setWindowTitle(title[len(_RUNE) + 1: -len(_RUNE) - 1])
        except Exception as _e:
            logger.debug(f"_update_nord_runes: {_e}")

    def apply_cursor(self):
        """Apply the cursor style saved in config to the whole application.

        Supports both Qt built-in cursors and custom emoji pixmap cursors
        (skull 💀, panda 🐼, etc.) at the configured size.
        """
        try:
            from PyQt6.QtGui import QCursor, QPixmap, QPainter, QFont, QColor
            from PyQt6.QtCore import Qt
            cursor_name = str(config.get('ui', 'cursor', default='default')).lower().strip()
            # Size mapping: Small=24, Medium=32, Large=48, Extra Large=64
            size_name = str(config.get('ui', 'cursor_size', default='medium')).lower().strip()
            # Accept both "extra large" (display text) and "extra_large" (config key)
            _size_map = {'small': 24, 'medium': 32, 'large': 48, 'extra large': 64}
            pix_size = _size_map.get(size_name.replace('_', ' '), 32)

            # Built-in Qt cursor shapes
            _cursor_map = {
                'default':   Qt.CursorShape.ArrowCursor,
                'arrow':     Qt.CursorShape.ArrowCursor,
                'hand':      Qt.CursorShape.PointingHandCursor,
                'cross':     Qt.CursorShape.CrossCursor,
                'wait':      Qt.CursorShape.WaitCursor,
                'text':      Qt.CursorShape.IBeamCursor,
                'forbidden': Qt.CursorShape.ForbiddenCursor,
                'move':      Qt.CursorShape.SizeAllCursor,
                'zoom_in':   Qt.CursorShape.PointingHandCursor,
                'zoom_out':  Qt.CursorShape.ArrowCursor,
            }
            # Emoji-based cursors — rendered to a QPixmap on the fly
            _emoji_map = {
                'skull':     '💀',
                'panda':     '🐼',
                'ghost':     '👻',
                'spider':    '🕷️',
                'sword':     '⚔️',
                'wand':      '🪄',
                'heart':     '❤️',
                'star':      '⭐',
                'diamond':   '💎',
                'crown':     '👑',
                'fire':      '🔥',
                'ice':       '❄️',
                'rainbow':   '🌈',
                'galaxy':    '🌌',
                'cat':       '🐱',
                'butterfly': '🦋',
                'moon':      '🌙',
                'lightning': '⚡',
            }
            app = QApplication.instance()
            if app is None:
                return
            # Restore any previous override so we don't stack overrides
            while app.overrideCursor():
                app.restoreOverrideCursor()

            # Strip unlock prefix if present (e.g. "🔒 Skull ⚠️" → "skull")
            clean_name = cursor_name.strip().lstrip('🔒 ').split()[0].lower()

            if clean_name in _emoji_map:
                # Render emoji into a pixmap cursor at the configured size
                emoji = _emoji_map[clean_name]
                pix = QPixmap(pix_size, pix_size)
                pix.fill(QColor(0, 0, 0, 0))  # transparent background
                painter = QPainter(pix)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                font = QFont()
                font.setPixelSize(int(pix_size * 0.85))
                painter.setFont(font)
                painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, emoji)

                # Apply user-chosen color tint via SourceIn composition.
                # Per-cursor colors take priority: config key 'cursor_color_{name}'
                # (e.g. 'cursor_color_skull').  Falls back to the global tint.
                per_cursor_key = f'cursor_color_{clean_name}'
                per_cursor_hex = str(config.get('ui', per_cursor_key, default=''))
                global_enabled = bool(config.get('ui', 'cursor_color_enabled', default=False))
                hex_color = per_cursor_hex or (
                    str(config.get('ui', 'cursor_color', default=''))
                    if global_enabled else ''
                )
                if hex_color:
                    tint = QColor(hex_color)
                    if tint.isValid() and tint.alpha() > 0:
                        painter.setCompositionMode(
                            QPainter.CompositionMode.CompositionMode_SourceIn
                        )
                        painter.fillRect(pix.rect(), tint)

                painter.end()
                app.setOverrideCursor(QCursor(pix, 0, 0))
                logger.debug(f"Emoji cursor applied: {clean_name} ({emoji}) size={pix_size}")
            elif clean_name not in ('default', 'arrow'):
                shape = _cursor_map.get(clean_name, Qt.CursorShape.ArrowCursor)
                app.setOverrideCursor(QCursor(shape))
                logger.debug(f"Cursor applied: {clean_name} → {shape}")
            else:
                logger.debug("Cursor restored to default arrow")
        except Exception as e:
            logger.warning(f"Could not apply cursor: {e}")

    def _apply_cursor_trail(self, enabled: bool) -> None:
        """Install or remove the cursor trail overlay based on *enabled*."""
        try:
            if enabled:
                if self._cursor_trail_overlay is None:
                    from ui.cursor_trail_overlay import CursorTrailOverlay
                    self._cursor_trail_overlay = CursorTrailOverlay(self)
                color_scheme = config.get('ui', 'cursor_trail_color', default='rainbow')
                self._cursor_trail_overlay.set_color_scheme(str(color_scheme))
                intensity = config.get('ui', 'cursor_trail_intensity', default=5)
                self._cursor_trail_overlay.set_intensity(int(intensity))
                self._cursor_trail_overlay.show()
                self._cursor_trail_overlay.raise_()
            else:
                if self._cursor_trail_overlay is not None:
                    self._cursor_trail_overlay.hide()
                    self._cursor_trail_overlay.deleteLater()
                    self._cursor_trail_overlay = None
        except Exception as e:
            logger.warning(f"Could not apply cursor trail: {e}")

    def initialize_components(self):
        """Initialize core components."""
        try:
            self.classifier = TextureClassifier(config=config)
            self.lod_detector = LODDetector()
            self.file_handler = FileHandler(create_backup=True, config=config)
            # OrganizationEngine requires output_dir + style_class; created on-demand in
            # _start_organization() once the user has selected an output folder and style.
            # TextureDatabase is initialized once per session — here if app_data exists,
            # or on first sort run if the directory isn't created yet.
            try:
                self._app_data_dir.mkdir(parents=True, exist_ok=True)
                self.database = TextureDatabase(self._db_path)
                logger.info("Texture database initialized at %s", self._db_path)
            except Exception as _e:
                logger.warning("Texture database unavailable: %s", _e)
                self.database = None
            self.log("✅ Core components initialized")
            
            # Initialize tooltip manager
            try:
                from features.tutorial_system import TooltipVerbosityManager
                self.tooltip_manager = TooltipVerbosityManager(config)
                logger.info("Tooltip manager initialized")
                # Propagate to all panels that were created in setup_ui() before
                # the manager existed.  Each panel stores the manager under
                # self.tooltip_manager OR self._tooltip_mgr depending on origin.
                # After injection, refresh_all() re-applies the correct tooltip
                # texts to every registered widget so cycling works immediately.
                try:
                    self._propagate_tooltip_manager()
                except Exception as _te:
                    logger.debug(f"Failed to propagate tooltip manager to panels: {_te}")
            except Exception as e:
                logger.warning(f"Could not initialize tooltip manager: {e}")
            
            # Initialize performance manager
            try:
                from core.performance_manager import PerformanceManager, PerformanceMode
                self.performance_manager = PerformanceManager(initial_mode=PerformanceMode.BALANCED)
                logger.info("Performance manager initialized")
            except Exception as e:
                logger.warning(f"Could not initialize performance manager: {e}")
            
            # Initialize threading manager
            try:
                from core.threading_manager import ThreadingManager
                thread_count = config.get('performance', 'max_threads', default=4)
                self.threading_manager = ThreadingManager(thread_count=thread_count)
                self.threading_manager.start()
                logger.info(f"Threading manager initialized with {thread_count} threads")
            except Exception as e:
                logger.warning(f"Could not initialize threading manager: {e}")
            
            # Initialize cache manager
            try:
                from utils.cache_manager import CacheManager
                cache_size = config.get('performance', 'cache_size_mb', default=512)
                self.cache_manager = CacheManager(max_size_mb=cache_size)
                logger.info(f"Cache manager initialized with {cache_size}MB cache")
            except Exception as e:
                logger.warning(f"Could not initialize cache manager: {e}")
            
            # Initialize memory manager
            try:
                from utils.memory_manager import MemoryManager
                memory_limit_mb = config.get('performance', 'memory_limit_mb', default=2048)
                self.memory_manager = MemoryManager(max_memory_mb=memory_limit_mb)
                self.memory_manager.start_monitoring()
                logger.info(f"Memory manager initialized with {memory_limit_mb}MB limit")
            except Exception as e:
                logger.warning(f"Could not initialize memory manager: {e}")
            
            # Initialize hotkey manager
            try:
                from features.hotkey_manager import HotkeyManager
                self.hotkey_manager = HotkeyManager()
                logger.info("Hotkey manager initialized")
            except Exception as e:
                logger.warning(f"Could not initialize hotkey manager: {e}")

            # Initialize sound manager
            try:
                from features.sound_manager import SoundManager
                self.sound_manager = SoundManager()
                # Apply saved volume from config
                saved_volume = config.get('ui', 'sound_volume', default=0.7)
                self.sound_manager.set_volume(float(saved_volume))
                logger.info(f"Sound manager initialized (volume={saved_volume})")
            except Exception as e:
                logger.warning(f"Could not initialize sound manager: {e}")

            # Initialize user level / XP system
            try:
                from features.level_system import UserLevelSystem
                self.level_system = UserLevelSystem()
                self.level_system.load()
                self.level_system.register_level_up_callback(self._on_level_up)
                logger.info("User level system initialized")
            except Exception as e:
                logger.warning(f"Could not initialize level system: {e}")

            # Initialize auto-backup system (backs up app_data/config on interval)
            try:
                from features.auto_backup import AutoBackupSystem, BackupConfig
                _backup_cfg = BackupConfig(
                    enabled=True,
                    interval_seconds=int(config.get('backup', 'interval_seconds', default=300)),
                    max_backups=int(config.get('backup', 'max_backups', default=10)),
                )
                _app_dir = Path(__file__).parent / 'app_data'
                _app_dir.mkdir(parents=True, exist_ok=True)
                self.auto_backup = AutoBackupSystem(app_dir=_app_dir, config=_backup_cfg)
                # Wire crash-recovery callback before calling start() so it fires
                # when start() detects a previous unclean shutdown.
                self.auto_backup.on_recovery_available = self._offer_crash_recovery
                self.auto_backup.start()
                logger.info("Auto-backup system started")
            except Exception as e:
                logger.warning(f"Could not initialize auto-backup: {e}")

            # Initialize unlockables system (cursors, themes, outfits)
            try:
                from features.unlockables_system import UnlockablesSystem
                self.unlockables_system = UnlockablesSystem()
                logger.info("Unlockables system initialized")
            except Exception as e:
                logger.warning(f"Could not initialize unlockables system: {e}")

            # Promote panda_widget to full-window overlay role.
            # The widget was created in setup_ui() with parent=self and all
            # transparency attributes set.  We resize it to cover the window,
            # show it, and raise it above all content.  panda_overlay is set to
            # panda_widget so all downstream code that references panda_overlay
            # (EnvironmentMonitor, PandaMoodSystem, resize/hide/drag events) works
            # without any further changes.
            if self.panda_widget is not None:
                try:
                    self.panda_overlay = self.panda_widget
                    self.panda_overlay.resize(self.size())
                    self.panda_overlay.move(0, 0)
                    self.panda_overlay.show()
                    self.panda_overlay.raise_()
                    logger.info("✅ panda_widget promoted to full-window transparent overlay")
                except Exception as e:
                    logger.debug(f"Could not activate panda overlay: {e}")

            # Wire drag-and-drop on the input/output path labels so users can
            # drag folders from the file manager directly onto them.
            try:
                from utils.drag_drop_handler import DragDropHandler
                self.drag_drop_handler = DragDropHandler()

                def _on_input_drop(paths):
                    folder = next((p for p in paths if Path(p).is_dir()), None)
                    if folder:
                        self.input_path = Path(folder)
                        self.input_path_label.setText(folder)
                        self.log(f"📁 Input folder (dropped): {folder}")
                        self.update_button_states()

                def _on_output_drop(paths):
                    folder = next((p for p in paths if Path(p).is_dir()), None)
                    if folder:
                        self.output_path = Path(folder)
                        self.output_path_label.setText(folder)
                        self.log(f"📂 Output folder (dropped): {folder}")
                        self.update_button_states()

                self.drag_drop_handler.enable_drop(
                    self.input_path_label, _on_input_drop, accept_folders=True, accept_files=False
                )
                self.drag_drop_handler.enable_drop(
                    self.output_path_label, _on_output_drop, accept_folders=True, accept_files=False
                )
                logger.info("Drag-and-drop wired to input/output path labels")
            except Exception as e:
                logger.warning(f"Could not wire drag-and-drop: {e}")

            # Initialize translation manager
            try:
                from features.translation_manager import TranslationManager, Language
                self.translation_manager = TranslationManager()
                saved_lang = config.get('ui', 'language', default='en')
                lang = next((l for l in Language if l.value == saved_lang), Language.ENGLISH)
                self.translation_manager.set_language(lang)
                logger.info(f"Translation manager initialized (language={saved_lang})")
            except Exception as e:
                logger.warning(f"Could not initialize translation manager: {e}")

            # Initialize EnvironmentMonitor — monitors scroll/dialog/window events
            # and triggers panda reactions.  Requires both PyQt6 and the panda overlay.
            try:
                from features.environment_monitor import EnvironmentMonitor
                _panda_overlay = getattr(self, 'panda_overlay', None)
                self.environment_monitor = EnvironmentMonitor(self, _panda_overlay)
                # Forward environment events to panda widget if it supports them
                if self.environment_monitor.environment_changed:
                    self.environment_monitor.environment_changed.connect(
                        lambda ev, data: logger.debug(f"Env event: {ev} {data}")
                    )
                # Wire panda hide/show signal to panda_overlay visibility
                if hasattr(self.environment_monitor, 'panda_should_hide') and self.environment_monitor.panda_should_hide:
                    self.environment_monitor.panda_should_hide.connect(self._on_panda_should_hide)
                # Wire panda reaction signal to mood system
                if hasattr(self.environment_monitor, 'panda_should_react') and self.environment_monitor.panda_should_react:
                    self.environment_monitor.panda_should_react.connect(self._on_panda_should_react)
                logger.info("EnvironmentMonitor initialized and event filters installed")
            except Exception as e:
                logger.warning(f"Could not initialize EnvironmentMonitor: {e}")

            # Initialize StatisticsTracker — tracks per-operation throughput/ETA/errors
            try:
                from features.statistics import StatisticsTracker
                self.statistics_tracker = StatisticsTracker()
                logger.info("StatisticsTracker initialized")
            except Exception as e:
                logger.warning(f"Could not initialize StatisticsTracker: {e}")

            # Initialize SearchFilter — file search/filter with presets and favorites
            try:
                from features.search_filter import SearchFilter
                self.search_filter = SearchFilter()
                logger.info("SearchFilter initialized")
            except Exception as e:
                logger.warning(f"Could not initialize SearchFilter: {e}")

            # Initialize ProfileManager — organization profile load/save/templates
            try:
                from features.profile_manager import ProfileManager
                self.profile_manager = ProfileManager()
                logger.info("ProfileManager initialized")
            except Exception as e:
                logger.warning(f"Could not initialize ProfileManager: {e}")

            # Initialize BackupManager — manual restore-point backups of config/data
            try:
                from features.backup_system import BackupManager
                _backup_root = Path(__file__).parent / 'app_data' / 'backups'
                _backup_root.mkdir(parents=True, exist_ok=True)
                self.backup_manager = BackupManager(backup_dir=_backup_root)
                logger.info("BackupManager initialized")
            except Exception as e:
                logger.warning(f"Could not initialize BackupManager: {e}")

            # Initialize GameIdentifier — CRC/serial-based game detection
            try:
                from features.game_identifier import GameIdentifier
                self.game_identifier = GameIdentifier()
                logger.info("GameIdentifier initialized")
            except Exception as e:
                logger.warning(f"Could not initialize GameIdentifier: {e}")

            # Initialize LODReplacer — LOD group scanning and quality replacement
            try:
                from features.lod_replacement import LODReplacer
                self.lod_replacer = LODReplacer()
                logger.info("LODReplacer initialized")
            except Exception as e:
                logger.warning(f"Could not initialize LODReplacer: {e}")

            # Initialize BatchQueue — priority queue for background operations
            try:
                from features.batch_operations import BatchQueue
                self.batch_queue = BatchQueue()
                logger.info("BatchQueue initialized")
            except Exception as e:
                logger.warning(f"Could not initialize BatchQueue: {e}")

            # Initialize PandaCharacter — drives panda personality/animations
            try:
                from features.panda_character import PandaCharacter
                self.panda_character = PandaCharacter()
                logger.info("PandaCharacter initialized")
                # Wire PandaCharacter to panda_widget so the sidebar widget
                # responds to mood/animation changes.  This must happen here
                # because setup_ui() creates panda_widget before
                # initialize_components() runs, so panda_widget.panda is None
                # when the Panda tab is first built.
                if self.panda_widget is not None:
                    self.panda_widget.panda = self.panda_character
                    logger.info("PandaCharacter wired to panda_widget")

                    # Forward any PandaCharacter.set_mood() call to the GL widget
                    # immediately so the 3D animation reacts without waiting for the
                    # next timer tick.  We wrap the original method to preserve its
                    # logic while adding the forwarding side-effect.
                    _orig_set_mood = self.panda_character.set_mood
                    _widget_ref = self.panda_widget

                    def _forwarding_set_mood(mood, _orig=_orig_set_mood, _w=_widget_ref):
                        _orig(mood)
                        try:
                            if _w and hasattr(_w, 'set_mood'):
                                _w.set_mood(mood)
                        except Exception as _fwd_err:
                            logger.debug(f"Mood forward to GL widget failed: {_fwd_err}")

                    self.panda_character.set_mood = _forwarding_set_mood
            except Exception as e:
                logger.warning(f"Could not initialize PandaCharacter: {e}")

            # Initialize PandaStats — tracks panda happiness/hunger/energy
            try:
                from features.panda_stats import PandaStats
                self.panda_stats = PandaStats()
                # Load persisted stats if they exist
                _stats_path = Path(__file__).parent / 'app_data' / 'panda_stats.json'
                if _stats_path.exists():
                    loaded = PandaStats.load_from_file(str(_stats_path))
                    if loaded is not None:
                        self.panda_stats = loaded
                logger.info("PandaStats initialized")
            except Exception as e:
                logger.warning(f"Could not initialize PandaStats: {e}")

            # Initialize PandaMoodSystem — mood-based behaviour modifiers
            try:
                from features.panda_mood_system import PandaMoodSystem
                panda_overlay = getattr(self, 'panda_overlay', None)
                self.panda_mood_system = PandaMoodSystem(panda_overlay)
                if hasattr(self.panda_mood_system, 'mood_changed'):
                    # mood_changed emits (old_mood: str, new_mood: str, reason: str)
                    # Forward new_mood to the 3D panda widget so it reacts visually.
                    def _on_mood_system_changed(old: str, new: str, reason: str):
                        logger.debug(f"Panda mood: {old} → {new} ({reason})")
                        try:
                            if self.panda_widget and hasattr(self.panda_widget, 'set_mood'):
                                self.panda_widget.set_mood(new)
                        except Exception as _ms_err:
                            logger.debug(f"Mood system → GL widget failed: {_ms_err}")
                    self.panda_mood_system.mood_changed.connect(_on_mood_system_changed)
                # Wire mood intensity → update panda widget tint/animation speed
                if hasattr(self.panda_mood_system, 'mood_intensity_changed'):
                    self.panda_mood_system.mood_intensity_changed.connect(
                        lambda intensity: logger.debug(f"Mood intensity: {intensity:.2f}")
                    )
                logger.info("PandaMoodSystem initialized")
            except Exception as e:
                logger.warning(f"Could not initialize PandaMoodSystem: {e}")

            # Initialize SkillTree — RPG skill progression system
            try:
                from features.skill_tree import SkillTree
                self.skill_tree = SkillTree()
                if self._skill_tree_path.exists():
                    import json as _json_st
                    self.skill_tree.load_from_dict(
                        _json_st.loads(self._skill_tree_path.read_text(encoding='utf-8'))
                    )
                logger.info("SkillTree initialized")
            except Exception as e:
                logger.warning(f"Could not initialize SkillTree: {e}")

            # Initialize TravelSystem — location / dungeon navigation
            try:
                from features.travel_system import TravelSystem
                self.travel_system = TravelSystem()
                logger.info("TravelSystem initialized")
            except Exception as e:
                logger.warning(f"Could not initialize TravelSystem: {e}")

            # Initialize AdventureLevel — combat XP and levelling
            try:
                from features.combat_system import AdventureLevel
                self.adventure_level = AdventureLevel(
                    save_path=self._adventure_level_path
                )
                logger.info("AdventureLevel initialized")
            except Exception as e:
                logger.warning(f"Could not initialize AdventureLevel: {e}")

            # Initialize WeaponCollection — equippable weapons for dungeon
            try:
                from features.weapon_system import WeaponCollection
                self.weapon_collection = WeaponCollection(
                    save_path=self._weapon_collection_path
                )
                logger.info("WeaponCollection initialized")
            except Exception as e:
                logger.warning(f"Could not initialize WeaponCollection: {e}")

            # Initialize TextureAnalyzer — advanced per-file analysis
            try:
                from features.texture_analysis import TextureAnalyzer
                self.texture_analyzer = TextureAnalyzer()
                logger.info("TextureAnalyzer initialized")
            except Exception as e:
                self.texture_analyzer = None
                logger.warning(f"Could not initialize TextureAnalyzer: {e}")

            # Initialize SimilaritySearch + DuplicateDetector — duplicate finding
            try:
                from similarity.similarity_search import SimilaritySearch
                from similarity.duplicate_detector import DuplicateDetector
                self.similarity_search = SimilaritySearch()
                self.duplicate_detector = DuplicateDetector(self.similarity_search)
                logger.info("SimilaritySearch and DuplicateDetector initialized")
            except Exception as e:
                self.similarity_search = None
                self.duplicate_detector = None
                logger.warning(f"Could not initialize similarity search: {e}")

            # Initialize WidgetDetector + PandaInteractionBehavior (optional, requires PyQt6)
            try:
                from features.widget_detector import WidgetDetector
                self.widget_detector = WidgetDetector(self)
                logger.info("WidgetDetector initialized")
                # Wire panda interaction behavior if overlay is available
                if self.panda_overlay:
                    try:
                        from features.panda_interaction_behavior import PandaInteractionBehavior
                        self.panda_interaction = PandaInteractionBehavior(
                            self.panda_overlay, self.widget_detector
                        )
                        logger.info("PandaInteractionBehavior initialized")
                    except Exception as _ie:
                        self.panda_interaction = None
                        logger.debug(f"PandaInteractionBehavior unavailable: {_ie}")
                else:
                    self.panda_interaction = None
            except Exception as e:
                self.widget_detector = None
                self.panda_interaction = None
                logger.debug(f"WidgetDetector unavailable: {e}")

            # Initialize PreviewViewer — non-blocking image preview window
            try:
                from features.preview_viewer import PreviewViewer
                self.preview_viewer = PreviewViewer()
                logger.info("PreviewViewer initialized")
            except Exception as e:
                self.preview_viewer = None
                logger.debug(f"PreviewViewer unavailable: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}", exc_info=True)
            self.log(f"⚠️ Warning: Some components failed to initialize: {e}")
    
    def _propagate_tooltip_manager(self):
        """Inject self.tooltip_manager into all panels created before it existed.

        ``setup_ui()`` runs before ``initialize_components()``, so all tool
        panels, the settings panel, and panda-feature panels are constructed
        with ``tooltip_manager=None``.  After the manager is created we push it
        to every panel, re-register their widgets, and call ``refresh_all()``
        so tooltip text is immediately available for the current mode.
        """
        if not self.tooltip_manager:
            return
        mgr = self.tooltip_manager

        # Collect all panel objects that may hold a tooltip_manager reference.
        # Panels use either .tooltip_manager or ._tooltip_mgr depending on implementation.
        candidates = []

        # All tool panels
        candidates.extend(self.tool_panels.values())

        # Settings panel
        if hasattr(self, 'settings_panel') and self.settings_panel is not None:
            candidates.append(self.settings_panel)

        # Panda-feature panels (achievement, closet, inventory, etc.)
        for attr in (
            '_achievement_panel', '_closet_panel', '_inventory_panel',
            '_customization_panel', '_minigame_panel', '_dungeon_view',
        ):
            obj = getattr(self, attr, None)
            if obj is not None:
                candidates.append(obj)

        injected = 0
        for panel in candidates:
            if panel is None:
                continue
            changed = False
            if hasattr(panel, 'tooltip_manager') and panel.tooltip_manager is None:
                panel.tooltip_manager = mgr
                changed = True
            if hasattr(panel, '_tooltip_mgr') and panel._tooltip_mgr is None:
                panel._tooltip_mgr = mgr
                changed = True
            if changed:
                injected += 1

        # Flush: re-apply tooltip text for every already-registered widget so
        # the current mode is immediately active without requiring a hover.
        try:
            mgr.refresh_all()
        except Exception as _re:
            logger.debug(f"Failed to refresh tooltips after propagation: {_re}")

        logger.info(
            f"Tooltip manager propagated to {injected}/{len(candidates)} panels; "
            f"refresh_all() called."
        )

    def apply_performance_settings(self):
        """Apply performance settings from config to actual system components."""
        try:
            # Get settings from config
            max_threads = config.get('performance', 'max_threads', default=4)
            memory_limit_mb = config.get('performance', 'memory_limit_mb', default=2048)
            cache_size_mb = config.get('performance', 'cache_size_mb', default=512)
            thumbnail_quality_str = config.get('performance', 'thumbnail_quality', default='high')
            
            # Convert thumbnail quality string to integer
            _tq_map = {'low': 60, 'medium': 75, 'high': 90}
            thumbnail_quality = _tq_map.get(str(thumbnail_quality_str).lower(), 85)
            
            # Apply thread count to threading manager
            if self.threading_manager:
                try:
                    self.threading_manager.set_thread_count(max_threads)
                    logger.info(f"✅ Applied thread count: {max_threads}")
                except Exception as e:
                    logger.error(f"Failed to apply thread count: {e}")
            
            # Update cache manager size
            if self.cache_manager:
                try:
                    self.cache_manager.max_size_bytes = cache_size_mb * 1024 * 1024
                    logger.info(f"✅ Applied cache size: {cache_size_mb}MB")
                except Exception as e:
                    logger.error(f"Failed to apply cache size: {e}")
            
            # Update memory manager limit
            if self.memory_manager:
                try:
                    self.memory_manager.max_memory_bytes = memory_limit_mb * 1024 * 1024
                    logger.info(f"✅ Applied memory limit: {memory_limit_mb}MB")
                except Exception as e:
                    logger.error(f"Failed to apply memory limit: {e}")
            
            # Apply thumbnail quality to image_processing module
            try:
                from utils import image_processing as _img_proc
                _img_proc.THUMBNAIL_QUALITY = thumbnail_quality
                logger.info(f"✅ Applied thumbnail quality: {thumbnail_quality_str} ({thumbnail_quality})")
            except Exception as e:
                logger.error(f"Failed to apply thumbnail quality: {e}")
            
            # Performance manager doesn't need updating - it calculates profiles dynamically
            # But we can log the current profile
            if self.performance_manager:
                profile = self.performance_manager.get_current_profile()
                logger.info(f"Performance profile: {profile.mode.value}, "
                          f"{profile.thread_count} threads, "
                          f"{profile.memory_limit_mb}MB limit")
            
            logger.info("✅ Performance settings applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply performance settings: {e}", exc_info=True)
    
    def browse_input(self):
        """Browse for input folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Input Folder",
            str(Path.home())
        )
        if folder:
            self.input_path = Path(folder)
            self.input_path_label.setText(str(self.input_path))
            self.log(f"📁 Input folder: {self.input_path}")
            self.update_button_states()
    
    def browse_output(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path.home())
        )
        if folder:
            self.output_path = Path(folder)
            self.output_path_label.setText(str(self.output_path))
            self.log(f"📂 Output folder: {self.output_path}")
            self.update_button_states()
    
    def update_button_states(self):
        """Update button enabled states based on selected paths (no-op after sorter removal)."""
        pass
    
    # ------------------------------------------------------------------
    # Panda interaction behavior tick (called at ~30 Hz by QTimer)
    # ------------------------------------------------------------------
    _INTERACTION_TICK_DT: float = 0.033  # seconds at 30 Hz
    _WELLBEING_DECAY_TICKS: int = 1800   # every ~60 s at 30 Hz tick

    def _tick_panda_interaction(self) -> None:
        """Advance PandaInteractionBehavior AI by one frame."""
        if self.panda_interaction is None:
            return
        try:
            self.panda_interaction.update(self._INTERACTION_TICK_DT)
        except Exception as _e:
            logger.debug(f"Panda interaction tick failed: {_e}")

        # Wellbeing decay — runs once per ~60 seconds
        try:
            if self.panda_stats is not None:
                _c = getattr(self, '_wellbeing_tick_counter', 0) + 1
                self._wellbeing_tick_counter = _c
                if _c >= self._WELLBEING_DECAY_TICKS:
                    self._wellbeing_tick_counter = 0
                    self.panda_stats.tick_wellbeing(60.0)
        except Exception:
            pass

        # Update panda mood label in status bar (every tick is fine — it's a cheap QLabel.setText)
        try:
            if self._panda_mood_label and self.panda_widget:
                state = getattr(self.panda_widget, 'animation_state', 'idle')
                # Also surface the active idle sub-state if present (via public getter)
                sub = self.panda_widget.get_idle_sub_state() if hasattr(self.panda_widget, 'get_idle_sub_state') else ''
                display_state = sub if sub else state
                emoji = _PANDA_STATE_EMOJI.get(display_state, _PANDA_STATE_EMOJI.get(state, '🐼'))
                # Append wellbeing indicators when stats available
                stats = getattr(self, 'panda_stats', None)
                wellbeing_str = ''
                if stats is not None:
                    hun = getattr(stats, 'hunger', None)
                    hap = getattr(stats, 'happiness', None)
                    if hun is not None and hap is not None:
                        hun_icon  = '🍎' if hun > 60 else ('🍽️' if hun > 20 else '😫')
                        hap_icon  = '😄' if hap > 60 else ('😐' if hap > 30 else '😢')
                        wellbeing_str = f"  {hun_icon}{hun}  {hap_icon}{hap}"
                label_text = f"{emoji} {display_state.replace('_', ' ')}{wellbeing_str}"
                if self._panda_mood_label.text() != label_text:
                    self._panda_mood_label.setText(label_text)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Shared helper: react to a tool-panel completion (panda + quest + sound)
    # ------------------------------------------------------------------
    def _on_tool_finished(self, success: bool, tool_id: str = 'tool', count: int = 1) -> None:
        """Called when any tool-panel `finished` signal fires.

        Triggers panda mood, quest progress, and audio feedback — all guarded
        so a missing optional component never prevents the status-bar update.
        """
        # Lazy imports pulled to module-level aliases so we don't re-import on each call
        _PandaMood = None
        _SoundEvent = None
        try:
            from features.panda_character import PandaMood as _PandaMood
        except (ImportError, OSError, RuntimeError):
            pass
        try:
            from features.sound_manager import SoundEvent as _SoundEvent
        except (ImportError, OSError, RuntimeError):
            pass

        # Panda mood
        try:
            if self.panda_character and _PandaMood:
                self.panda_character.set_mood(_PandaMood.HAPPY if success else _PandaMood.TIRED)
            elif self.panda_widget and hasattr(self.panda_widget, 'set_animation'):
                self.panda_widget.set_animation('celebrating' if success else 'idle')
        except Exception as _e:
            logger.debug(f"Panda mood update failed for {tool_id}: {_e}")
        # Quest progress — generic "tool used" quest type
        try:
            if self.quest_system:
                self.quest_system.check_quests(1)
                if hasattr(self.quest_system, 'update_quest_progress'):
                    # 'panda_friend' tracks general tool/interaction usage
                    self.quest_system.update_quest_progress('panda_friend', 1)
        except Exception as _e:
            logger.debug(f"Quest progress update failed for {tool_id}: {_e}")
        # XP — base 2 XP per tool launch + 1 XP per file processed (capped at 100)
        try:
            if self.level_system:
                xp = 2 + min(count, 100)
                self.level_system.add_xp(xp, reason='tool_used')
        except Exception as _e:
            logger.debug(f"XP award failed for {tool_id}: {_e}")
        # Sound
        try:
            if self.sound_manager and _SoundEvent:
                self.sound_manager.play_sound(
                    _SoundEvent.COMPLETE if success else _SoundEvent.ERROR)
        except Exception as _e:
            logger.debug(f"Sound playback failed for {tool_id}: {_e}")
        # Mood system
        try:
            if self.panda_mood_system and success:
                self.panda_mood_system.on_quest_completed()
        except Exception as _e:
            logger.debug(f"Mood system update failed for {tool_id}: {_e}")
        # Achievement triggers per tool
        try:
            if self.achievement_system and success:
                ach = self.achievement_system
                if tool_id == 'upscaler':
                    ach.increment_images_upscaled(count)
                elif tool_id in ('bg_remover', 'background_remover'):
                    ach.increment_bg_removed(count)
                elif tool_id == 'lineart':
                    ach.increment_lineart_converted(count)
                elif tool_id == 'converter':
                    ach.increment_files_converted(count)
                elif tool_id == 'quality':
                    ach.increment_quality_checked(count)
                elif tool_id == 'alpha_fixer':
                    ach.increment_alpha_fixed(count)
                elif tool_id == 'color':
                    ach.increment_color_corrected(count)
                elif tool_id == 'repair':
                    ach.increment_images_repaired(count)
                elif tool_id == 'rename':
                    ach.increment_files_renamed(count)
        except Exception as _e:
            logger.debug(f"Achievement trigger failed for {tool_id}: {_e}")
        # Award Panda Coins per file processed (capped at 50 files to prevent flooding)
        try:
            if self.currency_system and success:
                coins_per_file = self.currency_system.get_reward_for_action('conversion_complete')
                if coins_per_file > 0:
                    total_coins = coins_per_file * min(count, 50)
                    self.currency_system.earn_money(total_coins, f'tool_{tool_id}')
                    self._update_coin_display()
        except Exception as _e:
            logger.debug(f"Coin award failed for {tool_id}: {_e}")

    def set_operation_running(self, running: bool):
        """Update UI for operation running state (sorter widgets removed; no-op)."""
        if not running:
            self.statusbar.showMessage("Ready")
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress bar and status."""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.progress_bar.setFormat(f"{current}/{total} - {message}")
        
        self.statusbar.showMessage(message)

    def _start_ai_training_job(self, params: dict) -> None:
        """Dispatch training/export to a background QThread.

        *params* contains ``'mode'`` (display string) and ``'epochs'`` (int).
        Reads the rest of the AI settings from ``config``.
        """
        try:
            from ai.training_pytorch import is_pytorch_available, TrainingMode
        except (ImportError, OSError, RuntimeError):
            try:
                from src.ai.training_pytorch import (  # type: ignore[no-redef]
                    is_pytorch_available, TrainingMode,
                )
            except (ImportError, OSError, RuntimeError):
                self.statusBar().showMessage(
                    "⚠️ PyTorch not installed — cannot train. "
                    "Install with: pip install torch torchvision", 8000
                )
                return

        if not is_pytorch_available():
            self.statusBar().showMessage(
                "⚠️ PyTorch not installed — install with: "
                "pip install torch torchvision", 8000
            )
            return

        mode_str = params.get('mode', 'Standard')
        epochs = int(params.get('epochs', 10))
        export_path = config.get('ai', 'export_path', default='model_export.onnx')

        self.statusBar().showMessage(
            f"🏋️ AI training started: {mode_str} × {epochs} epochs…", 0
        )

        # Resolve TrainingMode enum from display text
        _mode_map: dict[str, TrainingMode] = {
            'standard': TrainingMode.STANDARD,
            'fine-tune existing': TrainingMode.FINE_TUNE,
            'incremental (continual)': TrainingMode.INCREMENTAL,
            'export to onnx': TrainingMode.EXPORT_ONNX,
            'export to pytorch': TrainingMode.EXPORT_PYTORCH,
            'custom dataset': TrainingMode.CUSTOM_DATASET,
        }
        mode = _mode_map.get(mode_str.lower(), TrainingMode.STANDARD)

        class _TrainingThread(QThread):
            done = pyqtSignal(bool, str)

            def __init__(self, mode, epochs, export_path, dataset_path=''):
                super().__init__()
                self._mode = mode
                self._epochs = epochs
                self._export_path = export_path
                self._dataset_path = dataset_path

            def run(self):
                try:
                    from ai.training_pytorch import PyTorchTrainer, TextureDataset  # type: ignore[import-untyped]
                    import torch  # type: ignore[import-untyped]

                    if self._mode in (TrainingMode.EXPORT_ONNX, TrainingMode.EXPORT_PYTORCH):
                        # Nothing to train — just a placeholder for wiring
                        self.done.emit(True, f"Export mode: {self._mode.value} — no checkpoint loaded")
                        return

                    # For CUSTOM_DATASET: try to load from configured dataset path
                    if self._mode == TrainingMode.CUSTOM_DATASET and self._dataset_path:
                        try:
                            ds = TextureDataset(self._dataset_path)
                            loader = ds.to_dataloader(batch_size=16, shuffle=True)
                            n_classes = len(ds.classes) or 4
                            model = torch.nn.Sequential(
                                torch.nn.Flatten(),
                                torch.nn.Linear(3 * 224 * 224, 256),
                                torch.nn.ReLU(),
                                torch.nn.Linear(256, n_classes),
                            )
                            trainer = PyTorchTrainer(model, loader, learning_rate=1e-3)
                            trainer.run_mode(self._mode, epochs=self._epochs)
                            self.done.emit(True, f"Custom dataset training complete: {n_classes} classes, {len(ds)} samples")
                            return
                        except Exception as _ds_exc:
                            self.done.emit(False, f"Custom dataset error: {_ds_exc}")
                            return

                    # Standard training demo with a tiny dummy model
                    model = torch.nn.Linear(16, 4)
                    X = torch.randn(32, 16)
                    y = torch.randint(0, 4, (32,))
                    ds = torch.utils.data.TensorDataset(X, y)
                    loader = torch.utils.data.DataLoader(ds, batch_size=8)
                    trainer = PyTorchTrainer(model, loader, learning_rate=1e-3)
                    trainer.run_mode(self._mode, epochs=self._epochs)
                    self.done.emit(True, f"Training complete: {self._mode.value}")
                except Exception as exc:
                    self.done.emit(False, str(exc))

        dataset_path = config.get('ai', 'custom_dataset_path', default='')
        thread = _TrainingThread(mode, epochs, export_path, dataset_path=dataset_path)

        def _on_done(ok: bool, msg: str) -> None:
            icon = "✅" if ok else "❌"
            self.statusBar().showMessage(f"{icon} AI training: {msg}", 8000)
            # Update settings panel status label
            sp = getattr(self, 'settings_panel', None)
            if sp and hasattr(sp, '_ai_train_status'):
                sp._ai_train_status.setText(f"{icon} {msg}")
            if sp and hasattr(sp, '_ai_train_progress'):
                sp._ai_train_progress.setVisible(False)
            thread.deleteLater()

        thread.done.connect(_on_done)
        self._ai_training_thread = thread   # prevent GC
        thread.start()

    def operation_finished(self, success: bool, message: str, files_processed: int = 0,
                           elapsed_time: float = 0.0):
        """Handle operation completion."""
        self.set_operation_running(False)
        # Use count stored by the previous operation when caller doesn't supply it
        if files_processed == 0:
            files_processed = getattr(self, '_last_sorted_count', 0)
            self._last_sorted_count = 0

        # Stop profiler and update performance dashboard queue status
        try:
            if self.perf_dashboard:
                self.perf_dashboard.stop_operation_profile()
                completed = files_processed if success else 0
                failed = 0 if success else files_processed
                self.perf_dashboard.update_queue_status(
                    pending=0, processing=0,
                    completed=completed, failed=failed,
                )
                if files_processed > 0:
                    # Approximate: treat average file as 256 KB
                    self.perf_dashboard.record_file_processed(files_processed * 256 * 1024)
        except Exception:
            pass

        # Run memory optimisation after every sort to release PIL/numpy allocations
        try:
            from core.performance_manager import OperationProfiler
            OperationProfiler.optimize_memory()
        except Exception:
            pass


        # Snapshot app state for auto-backup so it knows "last processed count"
        try:
            if self.auto_backup:
                self.auto_backup.update_state({
                    'last_operation_success': success,
                    'files_processed': files_processed,
                    'input_path': str(self.input_path) if self.input_path else None,
                    'output_path': str(self.output_path) if self.output_path else None,
                })
        except Exception:
            pass

        if success:
            self.log(f"✅ {message}")
            # Show statistics summary in log area
            try:
                if self.statistics_tracker and files_processed > 0:
                    # Use the actual elapsed time from the operation panel when available;
                    # fall back to computing it from the tracker's start_time.
                    import time as _time_mod
                    op_elapsed = elapsed_time if elapsed_time > 0 else (
                        _time_mod.time() - self.statistics_tracker.start_time
                    )
                    self.statistics_tracker.set_total_files(files_processed)
                    # Efficient O(1) batch update — avoids looping over every file.
                    # avg_file_size 256 KB is a reasonable approximation for texture
                    # files; actual sizes vary but this is sufficient for the log display.
                    self.statistics_tracker.record_batch_processed(
                        count=files_processed,
                        total_elapsed=op_elapsed,
                    )
                    rate = round(files_processed / op_elapsed, 1) if op_elapsed > 0 else 0
                    errors = self.statistics_tracker.error_count
                    self.log(
                        f"📊 Stats: {files_processed} files in {op_elapsed:.1f}s"
                        f" ({rate:.1f} files/sec)"
                        + (f" | {errors} error(s)" if errors else "")
                    )
            except Exception:
                pass
            QMessageBox.information(self, "Success", message)
            # Play completion sound
            try:
                if self.sound_manager:
                    from features.sound_manager import SoundEvent
                    self.sound_manager.play_sound(SoundEvent.COMPLETE)
            except Exception:
                pass
            # Update achievement progress
            try:
                if self.achievement_system and files_processed > 0:
                    self.achievement_system.increment_textures_sorted(files_processed)
                    # unlock_achievement() is idempotent — safe to call every sort;
                    # the system only fires the callback the first time it's unlocked.
                    self.achievement_system.unlock_achievement('first_sort')
                    # batch_master: fire when 500+ files processed in a single operation
                    if files_processed >= 500:
                        self.achievement_system.update_progress('batch_master', 1)
            except Exception:
                pass
            # Award XP for each file processed
            try:
                if self.level_system and files_processed > 0:
                    self.level_system.add_xp(files_processed, reason='file_processed')
                    self.level_system.save()
            except Exception:
                pass
            # Update quest progress for texture sorting
            try:
                if self.quest_system and files_processed > 0:
                    # check_quests() handles auto-start + progress update for texture_sorter/bulk_sorter
                    self.quest_system.check_quests(files_processed)
            except Exception:
                pass
            # Update panda stats with files processed
            try:
                if self.panda_stats and files_processed > 0:
                    # Increment files_processed counter directly (avoids O(N) loop for large counts)
                    self.panda_stats.files_processed = getattr(self.panda_stats, 'files_processed', 0) + files_processed
                    self.panda_stats.add_experience(files_processed * 2)
            except Exception:
                pass
            # Update panda character mood (happy after a successful sort)
            try:
                if self.panda_character:
                    from features.panda_character import PandaMood
                    self.panda_character.set_mood(PandaMood.HAPPY)
                elif self.panda_widget and hasattr(self.panda_widget, 'set_animation'):
                    # Fallback: drive widget directly when PandaCharacter not initialised
                    self.panda_widget.set_animation('celebrating')
            except Exception:
                pass
            # Award AdventureLevel XP — 1 XP per file sorted, source 'texture_sort'
            try:
                if self.adventure_level and files_processed > 0:
                    leveled_up, new_level = self.adventure_level.add_xp(files_processed, 'texture_sort')
                    if leveled_up:
                        self.statusBar().showMessage(
                            f"⚔️ Adventure level up! Now level {new_level}", 5000
                        )
            except Exception:
                pass
            # Award Panda Coins for files processed
            try:
                if self.currency_system and files_processed > 0:
                    coins = self.currency_system.get_reward_for_action('file_processed') * files_processed
                    if files_processed >= 100:
                        coins += self.currency_system.get_reward_for_action('batch_complete')
                    if coins > 0:
                        self.currency_system.earn_money(coins, 'file_processed')
                        self._update_coin_display()
            except Exception:
                pass
            # Update mood system — sort complete is a positive event
            try:
                if self.panda_mood_system:
                    self.panda_mood_system.on_quest_completed()
            except Exception:
                pass
        else:
            self.log(f"❌ {message}")
            QMessageBox.critical(self, "Error", message)
            # Play error sound
            try:
                if self.sound_manager:
                    from features.sound_manager import SoundEvent
                    self.sound_manager.play_sound(SoundEvent.ERROR)
            except Exception:
                pass
            # Track failure in panda stats
            try:
                if self.panda_stats:
                    self.panda_stats.track_operation_failure()
                if self.panda_character:
                    from features.panda_character import PandaMood
                    self.panda_character.set_mood(PandaMood.TIRED)
            except Exception:
                pass
            # Mood system — error makes panda annoyed
            try:
                if self.panda_mood_system:
                    from features.panda_mood_system import PandaMood as _PMood
                    self.panda_mood_system.force_mood(_PMood.ANNOYED)
            except Exception:
                pass
    
    def log(self, message: str):
        """Add message to activity log and Python logger."""
        if self.log_text is not None:
            try:
                self.log_text.append(message)
            except RuntimeError:
                pass  # widget deleted (during shutdown)
        logger.info(message)
    
    def on_settings_changed(self, setting_key: str, value):
        """Handle settings changes in real-time"""
        try:
            logger.info(f"Setting changed: {setting_key} = {value}")
            
            # Update the config value
            keys = setting_key.split('.')
            if len(keys) == 2:
                config.set(keys[0], keys[1], value=value)
            elif len(keys) == 1:
                # Single-level key - store in general section
                config.set('general', keys[0], value=value)
                logger.debug(f"Single-level setting key '{setting_key}' stored in 'general' section")
            else:
                # Multi-level nested keys - only handle first two levels
                logger.warning(f"Setting key '{setting_key}' has unexpected format (expected 'section.key')")
                if len(keys) >= 2:
                    config.set(keys[0], keys[1], value=value)
            
            # Handle theme / accent color changes
            if setting_key in ("ui.theme", "ui.accent_color"):
                self.apply_theme()
            
            # Handle opacity changes
            elif setting_key == "ui.window_opacity":
                self.setWindowOpacity(value)
            
            # Handle tooltip mode changes
            elif setting_key == "ui.tooltip_mode":
                if self.tooltip_manager:
                    from features.tutorial_system import TooltipMode
                    # Canonical config value is 'dumbed-down'; accept 'dumbed_down' for
                    # backward compatibility with configs written by older versions.
                    mode_map = {
                        'normal': TooltipMode.NORMAL,
                        'dumbed-down': TooltipMode.BEGINNER,   # canonical
                        'dumbed_down': TooltipMode.BEGINNER,   # legacy alias
                        'vulgar_panda': TooltipMode.PROFANE,
                    }
                    mode = mode_map.get(value)
                    if mode:
                        self.tooltip_manager.set_mode(mode)

            # Handle tooltip enabled/disabled toggle
            elif setting_key == "ui.tooltip_enabled":
                if self.tooltip_manager and hasattr(self.tooltip_manager, 'set_enabled'):
                    self.tooltip_manager.set_enabled(bool(value))
            
            # Handle cursor changes — apply immediately
            elif setting_key == "ui.cursor":
                self.apply_cursor()

            # Handle cursor size changes — re-apply cursor at new size
            elif setting_key == "ui.cursor_size":
                self.apply_cursor()

            # Handle cursor color tint changes — re-apply immediately
            elif setting_key in ("ui.cursor_color", "ui.cursor_color_enabled"):
                self.apply_cursor()

            # Handle cursor trail toggle — install or remove the overlay
            elif setting_key == "ui.cursor_trail":
                self._apply_cursor_trail(bool(value))
            elif setting_key == "ui.cursor_trail_color":
                if self._cursor_trail_overlay is not None:
                    self._cursor_trail_overlay.set_color_scheme(str(value))
            elif setting_key == "ui.cursor_trail_intensity":
                if self._cursor_trail_overlay is not None:
                    self._cursor_trail_overlay.set_intensity(int(value))

            # Handle font changes
            elif setting_key in ("ui.font_family", "ui.font_size"):
                font_family = config.get('ui', 'font_family', default='Segoe UI')
                font_size = config.get('ui', 'font_size', default=12)
                app = QApplication.instance()
                if app:
                    app.setFont(QFont(font_family, font_size))
            
            # Handle performance settings — apply immediately to live managers
            elif setting_key == 'performance.max_threads':
                if self.threading_manager:
                    try:
                        self.threading_manager.set_thread_count(int(value))
                        logger.info(f"Thread count updated to: {value}")
                    except Exception as e:
                        logger.error(f"Failed to update thread count: {e}")
            
            elif setting_key == 'performance.cache_size_mb':
                if self.cache_manager:
                    self.cache_manager.max_size_bytes = int(value) * 1024 * 1024
                    logger.info(f"Cache size updated to: {value}MB")
            
            elif setting_key == 'performance.memory_limit_mb':
                if self.memory_manager:
                    self.memory_manager.max_memory_bytes = int(value) * 1024 * 1024
                    logger.info(f"Memory limit updated to: {value}MB")
                else:
                    logger.info(f"Memory limit updated to: {value}MB (applied on next operation)")
            
            elif setting_key == 'performance.thumbnail_quality':
                try:
                    from utils import image_processing as _img_proc
                    _tq_map = {'low': 60, 'medium': 75, 'high': 90}
                    _img_proc.THUMBNAIL_QUALITY = _tq_map.get(str(value).lower(), 85)
                    logger.info(f"Thumbnail quality updated to: {value} ({_img_proc.THUMBNAIL_QUALITY})")
                except Exception as e:
                    logger.error(f"Failed to update thumbnail quality: {e}")

            elif setting_key == 'ui.sound_volume':
                # Apply live volume change to SoundManager
                if self.sound_manager:
                    try:
                        self.sound_manager.set_volume(float(value))
                        logger.info(f"Sound volume updated to: {value}")
                    except Exception as e:
                        logger.warning(f"Could not update sound volume: {e}")

            elif setting_key == 'ui.language':
                # Apply language change to TranslationManager
                if self.translation_manager:
                    try:
                        from features.translation_manager import Language
                        lang = next((l for l in Language if l.value == str(value)), None)
                        if lang:
                            self.translation_manager.set_language(lang)
                            logger.info(f"Language changed to: {value}")
                        else:
                            logger.warning(f"Unknown language code: {value}")
                    except Exception as e:
                        logger.warning(f"Could not change language: {e}")

            elif setting_key == 'ui.animation_speed':
                # Store animation speed in config; individual animated widgets read it on play.
                # 0.0 = paused/disabled, 1.0 = normal, 4.0 = maximum safe speed (above this
                # Qt timers fire too fast and animations become visually indistinguishable).
                try:
                    speed = float(value)
                    speed = max(0.0, min(4.0, speed))
                    config.set('ui', 'animation_speed', value=speed)
                    logger.info(f"Animation speed updated to: {speed}x")
                except Exception as e:
                    logger.warning(f"Could not update animation speed: {e}")

            elif setting_key.startswith('hotkeys.'):
                # Apply live hotkey rebinding to HotkeyManager when available
                action_id = setting_key[len('hotkeys.'):]
                if self.hotkey_manager:
                    try:
                        self.hotkey_manager.rebind_hotkey(action_id, str(value))
                        logger.info(f"Hotkey '{action_id}' rebound to '{value}'")
                    except Exception as e:
                        logger.warning(f"Could not rebind hotkey '{action_id}': {e}")

            elif setting_key.startswith('ai.'):
                # Persist to config (already done above); log for debugging.
                ai_key = setting_key[3:]
                logger.info(f"AI setting updated: {ai_key} = {value}")

                if ai_key == 'training_started':
                    # User clicked "Start Training / Export" in AI Settings
                    self._start_ai_training_job(value if isinstance(value, dict) else {})

                # If device changed, log GPU availability status
                elif ai_key == 'device':
                    try:
                        from ai.training_pytorch import is_pytorch_available
                        if is_pytorch_available():
                            import torch  # type: ignore[import-untyped]
                            gpu_ok = torch.cuda.is_available() or (
                                hasattr(torch.backends, 'mps')
                                and torch.backends.mps.is_available()
                            )
                            logger.info(
                                f"Device preference set to '{value}'; "
                                f"GPU available: {gpu_ok}"
                            )
                    except Exception:
                        pass

            # Save config after changes
            try:
                config.save()
                logger.debug(f"Config saved after setting change: {setting_key}")
            except Exception as save_error:
                logger.error(f"Error saving config after settings change: {save_error}", exc_info=True)
            
        except Exception as e:
            logger.error(f"Error handling settings change: {e}", exc_info=True)
    
    def on_panda_clicked(self):
        """Handle panda widget click events."""
        try:
            self.log("🐼 Panda clicked!")
            logger.info("Panda widget clicked")

            # Play panda click sound
            try:
                if self.sound_manager:
                    from features.sound_manager import SoundEvent
                    self.sound_manager.play_sound(SoundEvent.PANDA_CLICK)
            except Exception:
                pass

            # Unlock panda_lover achievement on first click
            try:
                if self.achievement_system:
                    self.achievement_system.unlock_achievement('panda_lover')
            except Exception:
                pass

            # Record click in panda stats
            try:
                if self.panda_stats:
                    self.panda_stats.increment_clicks()
                if self.panda_character:
                    self.panda_character.update_mood_from_context(files_processed=0)
            except Exception:
                pass

            # Notify mood system — click is a positive user interaction
            try:
                if self.panda_mood_system:
                    self.panda_mood_system.on_user_interaction('click')
            except Exception:
                pass
            # Award Panda Coins for petting
            try:
                if self.currency_system:
                    coins = self.currency_system.get_reward_for_action('panda_pet')
                    if coins > 0:
                        self.currency_system.earn_money(coins, 'panda_pet')
                        self._update_coin_display()
            except Exception:
                pass

            # Update wellbeing — petting raises happiness
            try:
                if self.panda_stats:
                    self.panda_stats.on_petted()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error handling panda click: {e}", exc_info=True)
    
    def _on_panda_food_eaten(self, item_id: str) -> None:
        """Award coins, update stats and mood when food is dropped onto the panda."""
        try:
            if self.currency_system:
                coins = self.currency_system.get_reward_for_action('panda_feed')
                if coins > 0:
                    self.currency_system.earn_money(coins, f'panda_feed_{item_id}')
                    self._update_coin_display()
            if self.panda_stats:
                # Use on_fed() to restore hunger and boost happiness; also calls increment_feeds()
                if hasattr(self.panda_stats, 'on_fed'):
                    self.panda_stats.on_fed(hunger_restore=20, happiness_boost=10)
                else:
                    self.panda_stats.increment_feeds()
            if self.panda_mood_system:
                self.panda_mood_system.on_user_interaction('feed')
        except Exception as _e:
            logger.debug(f"Panda feed handler: {_e}")

    def _on_session_hour(self) -> None:
        """Award session-hour coins every 60 minutes of active use."""
        try:
            if self.currency_system:
                coins = self.currency_system.get_reward_for_action('session_hour')
                if coins > 0:
                    self.currency_system.earn_money(coins, 'session_hour')
                    self._update_coin_display()
                    self.statusBar().showMessage(f"⏰ +{coins} Bamboo Bucks for playing for an hour! 🐼", 5000)
        except Exception as _e:
            logger.debug(f"Session hour coin award: {_e}")

    def _on_dungeon_coins_earned(self, coins: int) -> None:
        """Credit coins dropped by dungeon enemies to the currency system."""
        try:
            if self.currency_system and coins > 0:
                self.currency_system.earn_money(coins, 'dungeon_kill')
                self._update_coin_display()
        except Exception as _e:
            logger.debug(f"Dungeon coins earned: {_e}")

    def _on_dungeon_enemy_slain(self, enemy_type: str) -> None:
        """Update panda stats and quest progress when a dungeon enemy is slain."""
        try:
            if self.panda_stats:
                stats = self.panda_stats
                if hasattr(stats, 'monsters_slain'):
                    stats.monsters_slain += 1
            if self.quest_system:
                self.quest_system.update_quest_progress('dungeon_adventurer', 1)
        except Exception as _e:
            logger.debug(f"Dungeon enemy slain: {_e}")

    def _on_panda_gl_failed(self, error_msg: str):
        """
        Called via gl_failed signal when PandaOpenGLWidget.initializeGL() fails.

        Replaces the broken GL widget in the sidebar splitter with the 2D QPainter
        fallback.  This keeps exactly ONE panda visible at all times.
        """
        logger.warning(f"Panda GL init failed ({error_msg}), swapping in 2D fallback")

        # Log to the activity log so the user can see WHY 3D failed
        self.log(f"⚠️ 3D panda GL init failed: {error_msg}")
        self.log("ℹ️ Switched to 2D panda backup. Check that your GPU driver supports OpenGL 2.1.")
        try:
            self.statusBar().showMessage(
                f"⚠️ 3D panda unavailable ({error_msg[:60]}…) — using 2D backup", 8000
            )
        except Exception:
            pass

        if PandaWidget2D is None:
            logger.error("2D panda fallback not available; no panda character will be displayed")
            return

        # Disconnect signals from the failed GL widget before destroying it
        old_widget = self.panda_widget
        if old_widget is not None:
            if hasattr(old_widget, 'timer'):
                try:
                    old_widget.timer.stop()
                except Exception:
                    pass
            for sig_name in ('clicked', 'mood_changed', 'animation_changed'):
                sig = getattr(old_widget, sig_name, None)
                if sig is not None:
                    try:
                        sig.disconnect()
                    except Exception:
                        pass

        # Create 2D replacement
        try:
            w2d = PandaWidget2D(parent=self)
            # No min/max width — full-window overlay, not a sidebar panel
            w2d.clicked.connect(self.on_panda_clicked)
            w2d.mood_changed.connect(self.on_panda_mood_changed)
            w2d.animation_changed.connect(self.on_panda_animation_changed)
            if hasattr(w2d, 'food_eaten'):
                w2d.food_eaten.connect(self._on_panda_food_eaten)
            if self.panda_character is not None:
                w2d.panda = self.panda_character
        except Exception as e:
            logger.error(f"2D panda fallback creation failed: {e}")
            return

        # Promote the 2D widget to overlay role (same as the GL widget was)
        try:
            w2d.resize(self.size())
            w2d.move(0, 0)
            w2d.show()
            w2d.raise_()
        except Exception as e:
            logger.error(f"Could not set up 2D panda as overlay: {e}")
            return

        self.panda_widget = w2d
        self.panda_overlay = w2d

        # Schedule deletion of the old GL widget (already hidden from overlay)
        if old_widget is not None:
            try:
                old_widget.hide()
                old_widget.deleteLater()
            except Exception:
                pass

        logger.info("✅ Panda 2D fallback active as overlay (GL init failed)")

    def on_panda_mood_changed(self, mood: str):
        """Handle panda mood changes (emitted by panda_widget.mood_changed signal)."""
        try:
            logger.info(f"Panda mood changed to: {mood}")
            self.statusbar.showMessage(f"🐼 Panda is feeling {mood}", 3000)
            # Forward to the GL widget so the animation layer responds.
            # Guard against re-entry: panda_widget.set_mood() does NOT emit mood_changed,
            # so there is no signal loop, but we guard defensively anyway.
            if getattr(self, '_panda_mood_forwarding', False):
                return
            self._panda_mood_forwarding = True
            try:
                if self.panda_widget and hasattr(self.panda_widget, 'set_mood'):
                    self.panda_widget.set_mood(mood)
            finally:
                self._panda_mood_forwarding = False
        except Exception as e:
            logger.error(f"Error handling panda mood change: {e}", exc_info=True)
    
    def on_panda_animation_changed(self, animation: str):
        """Handle panda animation state changes — just log, do not call back into widget."""
        logger.debug(f"Panda animation changed to: {animation}")
    
    def on_customization_color_changed(self, color_data: dict):
        """Handle color changes from customization panel."""
        try:
            color_type = color_data.get('type', 'unknown')
            color_rgb = color_data.get('color', (255, 255, 255))
            logger.info(f"Customization: {color_type} color changed to RGB{color_rgb}")
            
            # Apply the color change to the panda widget if it has the method
            if hasattr(self.panda_widget, 'set_color'):
                self.panda_widget.set_color(color_type, color_rgb)
            
        except Exception as e:
            logger.error(f"Error handling customization color change: {e}", exc_info=True)
    
    def on_customization_trail_changed(self, trail_type: str, trail_data: dict):
        """Handle trail changes from customization panel."""
        try:
            logger.info(f"Customization: trail changed to {trail_type} with settings {trail_data}")

            # Apply to sidebar panda widget
            if hasattr(self.panda_widget, 'set_trail'):
                self.panda_widget.set_trail(trail_type, trail_data)

            # Apply to floating overlay panda (if present and different from panda_widget)
            _overlay = getattr(self, 'panda_overlay', None)
            if _overlay is not None and _overlay is not self.panda_widget:
                if hasattr(_overlay, 'set_trail'):
                    _overlay.set_trail(trail_type, trail_data)

        except Exception as e:
            logger.error(f"Error handling customization trail change: {e}", exc_info=True)
    
    def on_shop_item_purchased(self, item_id: str):
        """Handle item purchase from shop panel."""
        try:
            # The ShopPanelQt already deducted coins via currency_system.subtract().
            # Skip double-deduction by checking is_purchased status.
            if not self._deduct_coins(item_id, skip_if_already_purchased=True):
                return  # insufficient coins — _on_not_enough_coins already called
            logger.info(f"Item purchased: {item_id}")
            self.log(f"🛒 Purchased item: {item_id}")

            # Play purchase sound
            try:
                if self.sound_manager:
                    from features.sound_manager import SoundEvent
                    self.sound_manager.play_sound(SoundEvent.BUTTON_CLICK)
            except Exception:
                pass

            # If item is clothing/accessory, equip it on the panda closet
            try:
                if self.panda_closet:
                    item = self.panda_closet.get_item(item_id)
                    if item:
                        item.unlocked = True
                        self.panda_closet.equip_item(item_id)
                        logger.info(f"Equipped item on panda: {item_id}")
                        # Forward to GL widget via unified helper
                        self._apply_item_to_panda_widget(item)
                    else:
                        # Item is from shop_system (weapon/toy/food) but not in
                        # panda_closet — apply directly from shop_system lookup
                        try:
                            if self.shop_system:
                                shop_item = self.shop_system.get_item(item_id)
                                if shop_item:
                                    self._apply_item_to_panda_widget(shop_item)
                                    logger.info(f"Applied shop item directly: {item_id}")
                        except Exception as _se:
                            logger.debug(f"shop fallback for {item_id}: {_se}")
            except Exception as _e:
                logger.debug(f"Could not equip item {item_id}: {_e}")

            # Unlock fashionista achievement for any clothing purchase.
            # AchievementSystem.unlock_achievement() is idempotent — calling it
            # multiple times only unlocks once (it's a no-op if already unlocked).
            try:
                if self.achievement_system:
                    self.achievement_system.unlock_achievement('fashionista_fur')
                    self.achievement_system.unlock_achievement('closet_explorer')
            except Exception:
                pass

            # Track new closet achievements
            self._check_closet_achievements(item_id)

        except Exception as e:
            logger.error(f"Error handling shop purchase: {e}", exc_info=True)

    def _deduct_coins(self, item_id: str, skip_if_already_purchased: bool = False) -> bool:
        """Deduct item cost from currency_system.  Returns True on success.

        Pass skip_if_already_purchased=True when the purchase was handled by
        ShopPanelQt (which already deducted coins internally via subtract()).
        """
        try:
            if not self.currency_system:
                return True  # no economy → treat as free
            # If the shop panel already deducted, don't double-charge.
            if skip_if_already_purchased and self.shop_system:
                try:
                    if self.shop_system.is_purchased(item_id):
                        self._update_coin_display()
                        return True
                except Exception:
                    pass
            cost = 0
            try:
                if self.shop_system:
                    shop_item = self.shop_system.get_item(item_id)
                    if shop_item and hasattr(shop_item, 'price'):
                        cost = int(shop_item.price)
            except Exception as _e:
                logger.debug(f"_deduct_coins cost lookup: {_e}")
            if cost <= 0:
                return True  # free item
            if not self.currency_system.can_afford(cost):
                self._on_not_enough_coins()
                return False
            self.currency_system.spend_money(cost, f'purchase_{item_id}')
            self._update_coin_display()
            return True
        except Exception as _e:
            logger.debug(f"_deduct_coins({item_id}): {_e}")
            return True  # fail-open

    def _on_not_enough_coins(self) -> None:
        """Notify the user they can't afford the item."""
        try:
            self.statusBar().showMessage("Not enough coins 💰", 3000)
        except Exception:
            pass
        try:
            if self.panda_widget:
                self.panda_widget.set_animation_state('idle')
                import types as _t
                _w = self.panda_widget
                from PyQt6.QtCore import QTimer  # type: ignore[attr-defined]
                QTimer.singleShot(100, lambda: _w.set_animation_state('idle'))
        except Exception:
            pass

    def _update_coin_display(self) -> None:
        """Refresh the coin-balance label everywhere it is shown."""
        try:
            if not self.currency_system:
                return
            balance = self.currency_system.get_balance()
            txt = f"💰 {balance:,}"
            if self._coin_label and not self._coin_label.isHidden():
                try:
                    self._coin_label.setText(txt)
                except Exception:
                    pass
            # Also update shop panel if it's visible
            try:
                if self._home_stack and self._home_stack.count() > 1:
                    w = self._home_stack.widget(1)
                    if w and hasattr(w, 'update_coin_display'):
                        w.update_coin_display(balance)
            except Exception:
                pass
        except Exception as _e:
            logger.debug(f"_update_coin_display: {_e}")

    def _on_shop_purchase_completed(self, item_id: str) -> None:
        """Alias wired to ShopPanelQt.item_purchased signal (otter shop)."""
        self.on_shop_item_purchased(item_id)

    def on_inventory_item_selected(self, item_id: str):
        """Handle item selection from inventory panel."""
        try:
            logger.info(f"Inventory item selected: {item_id}")

            # Equip the selected item on the panda closet
            try:
                if self.panda_closet:
                    item = self.panda_closet.get_item(item_id)
                    if item and item.unlocked:
                        self.panda_closet.equip_item(item_id)
                        self.log(f"👔 Equipped: {item.name if hasattr(item, 'name') else item_id}")
                        logger.info(f"Equipped item from inventory: {item_id}")
                        # Forward to GL widget via unified helper
                        self._apply_item_to_panda_widget(item)
                    elif item is None:
                        # Weapon/toy/food from shop_system — apply directly
                        try:
                            if self.shop_system:
                                shop_item = self.shop_system.get_item(item_id)
                                if shop_item:
                                    self._apply_item_to_panda_widget(shop_item)
                                    self.log(f"🎮 Equipped: {shop_item.name}")
                        except Exception as _se:
                            logger.debug(f"inv shop fallback {item_id}: {_se}")
            except Exception as _e:
                logger.debug(f"Could not equip inventory item {item_id}: {_e}")

            # Preview item on the panda widget if it supports it
            try:
                if self.panda_widget and hasattr(self.panda_widget, 'preview_item'):
                    self.panda_widget.preview_item(item_id)
            except Exception:
                pass

            # Track new closet achievements on equip
            self._check_closet_achievements(item_id)

        except Exception as e:
            logger.error(f"Error handling inventory selection: {e}", exc_info=True)

    def _restore_panda_appearance_from_closet(self) -> None:
        """
        Apply the saved closet appearance (fur style, hair style, clothing) to the
        live panda widget.  Called once after the closet file is loaded on startup,
        and also after the GL widget is (re-)created.
        """
        if not self.panda_closet or not self.panda_widget:
            return
        try:
            app = self.panda_closet.get_current_appearance()
            if hasattr(self.panda_widget, 'set_fur_style') and app.fur_style:
                self.panda_widget.set_fur_style(app.fur_style)
            if hasattr(self.panda_widget, 'set_hair_style') and app.hair_style:
                self.panda_widget.set_hair_style(app.hair_style)
            # Restore all equipped clothing items
            try:
                equipped = self.panda_closet.get_equipped_items()
                for eq_item in (equipped or []):
                    self._apply_item_to_panda_widget(eq_item)
            except Exception as _ce:
                logger.debug(f"restore equipped clothing: {_ce}")
            logger.debug(f"Panda appearance restored: fur={app.fur_style} hair={app.hair_style}")
        except Exception as e:
            logger.debug(f"_restore_panda_appearance_from_closet: {e}")

    def _apply_item_to_panda_widget(self, item) -> None:
        """Forward a closet CustomizationItem (or ShopItem) to the correct panda_widget slot.

        Centralises the category→slot mapping used by both purchase and equip
        handlers so they stay in sync automatically.  Accepts both
        ``CustomizationItem`` (from panda_closet) and ``ShopItem`` (from
        shop_system) — the ShopItem→closet-category mapping is resolved via
        ``SHOP_TO_CLOSET_CATEGORY``.
        """
        if not self.panda_widget or item is None:
            return
        try:
            from features.panda_closet import CustomizationCategory as _CC
            # Resolve ShopItem → effective closet category string
            try:
                from features.shop_system import ShopItem as _SI, SHOP_TO_CLOSET_CATEGORY
                if isinstance(item, _SI):
                    cat_str = SHOP_TO_CLOSET_CATEGORY.get(item.category, '')
                    # Build a minimal proxy with .category, .id, .color
                    _cat_val = None
                    try:
                        _cat_val = _CC(cat_str) if cat_str else None
                    except ValueError:
                        pass
                    item = _types.SimpleNamespace(
                        id=item.id,
                        color=[0.7, 0.6, 0.3],
                        category=_cat_val,
                    )
            except Exception:
                pass

            cat = getattr(item, 'category', None)
            item_id = getattr(item, 'id', '')
            _color = getattr(item, 'color', [0.7, 0.6, 0.3])
            if not isinstance(_color, (list, tuple)):
                _color = [0.7, 0.6, 0.3]

            if cat == _CC.FUR_STYLE and hasattr(self.panda_widget, 'set_fur_style'):
                self.panda_widget.set_fur_style(item_id)
            elif cat == _CC.FUR_COLOR and hasattr(self.panda_widget, 'set_fur_style'):
                # FUR_COLOR items use the same _FUR_STYLE_COLORS dict keyed by item_id
                self.panda_widget.set_fur_style(item_id)
            elif cat == _CC.HAIR_STYLE and hasattr(self.panda_widget, 'set_hair_style'):
                self.panda_widget.set_hair_style(item_id)
            elif cat in (_CC.WEAPON,) and hasattr(self.panda_widget, 'equip_clothing'):
                self.panda_widget.equip_clothing('held_right', {
                    'id': item_id, 'type': item_id, 'color': _color, 'size': 0.5})
            elif cat == _CC.FOOD and hasattr(self.panda_widget, 'equip_clothing'):
                self.panda_widget.equip_clothing('held_left', {
                    'id': item_id, 'type': item_id, 'color': _color, 'size': 0.35})
            elif cat == _CC.TOY and hasattr(self.panda_widget, 'equip_clothing'):
                self.panda_widget.equip_clothing('held_right', {
                    'id': item_id, 'type': item_id, 'color': _color, 'size': 0.4})
            elif cat == _CC.GLOVES and hasattr(self.panda_widget, 'equip_clothing'):
                self.panda_widget.equip_clothing('gloves', {'id': item_id, 'type': 'gloves'})
            elif cat == _CC.ARMOR and hasattr(self.panda_widget, 'equip_clothing'):
                self.panda_widget.equip_clothing('armor', {'id': item_id, 'type': item_id})
            elif cat == _CC.BOOTS and hasattr(self.panda_widget, 'equip_clothing'):
                self.panda_widget.equip_clothing('boots', {'id': item_id, 'type': item_id})
            elif cat == _CC.BELT and hasattr(self.panda_widget, 'equip_clothing'):
                self.panda_widget.equip_clothing('belt', {'id': item_id, 'type': item_id})
            elif cat == _CC.BACKPACK and hasattr(self.panda_widget, 'equip_clothing'):
                self.panda_widget.equip_clothing('backpack', {'id': item_id, 'type': item_id})
            elif cat == _CC.HAT and hasattr(self.panda_widget, 'equip_item'):
                self.panda_widget.equip_item(item)
            elif cat in (_CC.CLOTHING, _CC.SHOES, _CC.ACCESSORY) and hasattr(self.panda_widget, 'equip_item'):
                self.panda_widget.equip_item(item)
            elif cat == _CC.CURSOR_TRAIL and hasattr(self.panda_widget, 'set_trail'):
                # Map trail item IDs to trail type strings
                trail_type = item_id.replace('trail_', '') if item_id.startswith('trail_') else item_id
                self.panda_widget.set_trail(trail_type, {'item_id': item_id})
                self.log(f"🌈 Trail activated: {item_id}")
            elif cat == _CC.ANIMATION and hasattr(self.panda_widget, 'set_animation_state'):
                # Purchased animation — play it once then return to idle
                anim_state = _MOOD_TO_ANIMATION_MAP.get(item_id, 'celebrating')
                self.panda_widget.set_animation_state(anim_state)
                _dur = {'dance': 5000, 'backflip': 3000, 'spin': 3500, 'juggle': 4000}.get(anim_state, 3000)
                from PyQt6.QtCore import QTimer as _QT
                _QT.singleShot(_dur, lambda: self.panda_widget.set_animation_state('idle')
                               if self.panda_widget and self.panda_widget.animation_state == anim_state else None)
            elif cat == _CC.SOUND:
                # Purchased sound pack — activate via sound_manager
                if self.sound_manager and hasattr(self.sound_manager, 'activate_sound_pack'):
                    self.sound_manager.activate_sound_pack(item_id)
                self.log(f"🎵 Sound pack activated: {item_id}")
            elif cat == _CC.THEME:
                # Apply app theme
                if hasattr(self, 'apply_theme'):
                    self.apply_theme(item_id)
                self.log(f"🎨 Theme applied: {item_id}")
            else:
                # Generic fallback — let equip_item heuristics sort it out
                if hasattr(self.panda_widget, 'equip_item'):
                    self.panda_widget.equip_item(item)
        except Exception as _e:
            logger.debug(f"_apply_item_to_panda_widget({getattr(item,'id','?')}): {_e}")

    def _check_closet_achievements(self, newly_equipped_id: str = '') -> None:
        """
        Check and update all closet-category achievements after an equip/purchase.

        Called from both on_shop_purchase_completed and on_inventory_item_selected.
        All operations are idempotent — safe to call redundantly.
        """
        if not self.achievement_system or not self.panda_closet:
            return
        try:
            from features.panda_closet import CustomizationCategory, ItemRarity

            ach = self.achievement_system
            closet = self.panda_closet
            # Build rare+ set once per call (not inside the inner try blocks)
            rare_plus = frozenset({ItemRarity.RARE, ItemRarity.EPIC, ItemRarity.LEGENDARY})

            # first_outfit — any clothing/hat/shoes item equipped
            try:
                item = closet.get_item(newly_equipped_id)
                if item and item.category in (
                    CustomizationCategory.CLOTHING,
                    CustomizationCategory.HAT,
                    CustomizationCategory.SHOES,
                ):
                    ach.unlock_achievement('first_outfit')
            except Exception as _e:
                logger.debug(f"first_outfit check: {_e}")

            # full_outfit — clothing + hat + shoes all equipped simultaneously
            try:
                app = closet.get_current_appearance()
                if app.clothing and app.hat and app.shoes:
                    ach.unlock_achievement('full_outfit')
            except Exception as _e:
                logger.debug(f"full_outfit check: {_e}")

            # collector_10 — 10 closet items unlocked
            try:
                unlocked_count = sum(
                    1 for it in closet.items.values() if it.unlocked
                )
                ach.update_progress('collector_10', unlocked_count)
            except Exception as _e:
                logger.debug(f"collector_10 check: {_e}")

            # rare_find — any Rare+ item unlocked
            try:
                if any(it.unlocked and it.rarity in rare_plus
                       for it in closet.items.values()):
                    ach.unlock_achievement('rare_find')
            except Exception as _e:
                logger.debug(f"rare_find check: {_e}")

            # legendary_collector — any Legendary item unlocked
            try:
                if any(it.unlocked and it.rarity == ItemRarity.LEGENDARY
                       for it in closet.items.values()):
                    ach.unlock_achievement('legendary_collector')
            except Exception as _e:
                logger.debug(f"legendary_collector check: {_e}")

            # custom_fur — 5 distinct FUR_STYLE items equipped (count unlocked fur styles)
            try:
                fur_unlocked = sum(
                    1 for it in closet.items.values()
                    if it.unlocked and it.category == CustomizationCategory.FUR_STYLE
                )
                ach.update_progress('custom_fur', fur_unlocked)
            except Exception as _e:
                logger.debug(f"custom_fur check: {_e}")

            # top_hat_owner — any hat item unlocked
            try:
                if any(it.unlocked and it.category == CustomizationCategory.HAT
                       for it in closet.items.values()):
                    ach.unlock_achievement('top_hat_owner')
            except Exception as _e:
                logger.debug(f"top_hat_owner check: {_e}")

            # hairstylist — 3 hair style items unlocked
            try:
                hair_unlocked = sum(
                    1 for it in closet.items.values()
                    if it.unlocked and it.category == CustomizationCategory.HAIR_STYLE
                )
                ach.update_progress('hairstylist', hair_unlocked)
            except Exception as _e:
                logger.debug(f"hairstylist check: {_e}")

        except Exception as e:
            logger.debug(f"_check_closet_achievements error: {e}")

    def _on_achievement_unlocked(self, achievement):
        """Callback fired by AchievementSystem when an achievement is unlocked.

        Shows a Qt achievement popup, plays the achievement sound, and awards XP.
        """
        try:
            # Play achievement sound
            if self.sound_manager:
                from features.sound_manager import SoundEvent
                self.sound_manager.play_sound(SoundEvent.ACHIEVEMENT)
        except Exception:
            pass

        try:
            # Award XP for the achievement tier
            if self.level_system:
                rarity = getattr(achievement, 'rarity', 'bronze')
                xp_reward_key = f'achievement_{rarity}'  # e.g. 'achievement_gold'
                _leveled_up, _new_xp = self.level_system.add_xp(
                    self.level_system.get_xp_reward(xp_reward_key), reason=xp_reward_key
                )
                self.level_system.save()
        except Exception:
            pass
        try:
            # Award Panda Coins for unlocking the achievement
            if self.currency_system:
                rarity = getattr(achievement, 'rarity', 'bronze')
                reward_key = f'achievement_{rarity}'
                coins = self.currency_system.get_reward_for_action(reward_key)
                if coins > 0:
                    ach_name = getattr(achievement, 'name', str(achievement))
                    self.currency_system.earn_money(coins, f'achievement_{ach_name}')
                    self._update_coin_display()
        except Exception:
            pass

        try:
            from ui.qt_achievement_popup import show_achievement_popup
            popup_data = {
                'name': getattr(achievement, 'name', str(achievement)),
                'emoji': getattr(achievement, 'icon', '🏆'),
                'description': getattr(achievement, 'description', ''),
            }
            show_achievement_popup(popup_data, parent=self, parent_geometry=self.geometry())
        except Exception as _e:
            logger.debug(f"Could not show achievement popup: {_e}")

        # Achievement = positive event → move mood toward HAPPY/MISCHIEVOUS
        try:
            if self.panda_mood_system:
                self.panda_mood_system.on_quest_completed()
        except Exception:
            pass

        # Update trophy stand in bedroom with new achievement count
        try:
            if self._bedroom_widget and self.achievement_system:
                count = len(self.achievement_system.get_unlocked_achievements())
                self._bedroom_widget.set_achievement_count(count)
        except Exception as _e:
            logger.debug(f"Trophy stand update: {_e}")

        # Refresh achievement panel grid so newly unlocked achievement card appears
        try:
            if self._achievement_panel and hasattr(self._achievement_panel, 'refresh_achievements'):
                self._achievement_panel.refresh_achievements()
        except Exception as _e:
            logger.debug("Achievement panel refresh: %s", _e)

    # Coins awarded per new level on level-up (e.g. reaching level 10 gives 500 coins)
    _COINS_PER_LEVEL = 50

    def _on_level_up(self, old_level: int, new_level: int):
        """Callback fired by UserLevelSystem when the user gains a level."""
        try:
            title = self.level_system.get_title_for_level() if self.level_system else ''
            self.statusBar().showMessage(
                f"🎉 Level up! {old_level} → {new_level}  {title}", 8000
            )
            # Award currency bonus for levelling up
            if self.currency_system:
                bonus = new_level * self._COINS_PER_LEVEL
                self.currency_system.earn_money(bonus, f'level_up_{new_level}')
                # Milestone bonus for significant level thresholds
                _MILESTONES = {5, 10, 25, 50, 100}
                if new_level in _MILESTONES:
                    milestone_bonus = self.currency_system.get_reward_for_action('milestone_reached')
                    if milestone_bonus > 0:
                        self.currency_system.earn_money(milestone_bonus, f'milestone_level_{new_level}')
                        self.statusBar().showMessage(
                            f"🏆 Milestone! Level {new_level} — +{milestone_bonus} Bamboo Bucks bonus! 🐼",
                            8000,
                        )
                self._update_coin_display()
        except Exception as _e:
            logger.debug(f"Level-up callback error: {_e}")

    def _on_quest_completed(self, quest_id: str, reward_message: str):
        """Callback fired when a quest is completed (QuestSystem.quest_completed signal)."""
        try:
            self.statusBar().showMessage(f"📜 Quest completed: {reward_message}", 6000)
            # Play sound event if sound manager available
            if self.sound_manager:
                try:
                    from features.sound_manager import SoundEvent
                    self.sound_manager.play_sound(SoundEvent.ACHIEVEMENT)
                except Exception:
                    pass
            # Award XP for quest completion
            if self.level_system:
                try:
                    self.level_system.add_xp(50, 'quest_completed')
                    self.level_system.save()
                except Exception:
                    pass
            # Award currency reward
            if self.currency_system:
                try:
                    self.currency_system.earn_money(100, f'quest_{quest_id}')
                    self._update_coin_display()
                except Exception:
                    pass
            logger.info(f"Quest completed: {quest_id} — {reward_message}")
        except Exception as _e:
            logger.debug(f"Quest completion callback error: {_e}")

    def _on_quest_progress(self, quest_id: str, current: int, goal: int):
        """Show quest progress in the status bar."""
        try:
            self.statusBar().showMessage(
                f"📜 Quest '{quest_id}': {current}/{goal}", 2000
            )
        except Exception as _e:
            logger.debug(f"Quest progress callback error: {_e}")

    def _on_minigame_completed(self, game_id: str, score: int):
        """Handle minigame completion — award XP and currency."""
        try:
            self.statusBar().showMessage(
                f"🎮 {game_id} complete! Score: {score}", 5000
            )
            self.log(f"🎮 Minigame '{game_id}' completed with score {score}")
            if self.level_system:
                xp = max(1, score // 10)
                self.level_system.add_xp(xp, f'minigame_{game_id}')
                self.level_system.save()
            if self.currency_system:
                coins = max(1, score // 5)
                self.currency_system.earn_money(coins, f'minigame_{game_id}')
                self._update_coin_display()
            if self.achievement_system:
                # 'first_game' unlocks on the first minigame completed
                self.achievement_system.unlock_achievement('first_game')
                # 'click_champion' awards a high-score badge (100+)
                if score >= 100:
                    self.achievement_system.unlock_achievement('click_champion')
                # 'minigame_addict' tracks 50+ plays — increment via progress
                self.achievement_system.update_progress('minigame_addict', 1, increment=True)
            if self.quest_system:
                # No dedicated minigame quest — mark general interaction progress
                self.quest_system.update_quest_progress('first_interaction')
        except Exception as _e:
            logger.debug(f"Minigame completed callback error: {_e}")

    # ── Home tab navigation helpers ────────────────────────────────────────────
    def _go_outside(self) -> None:
        """Show the 3D world scene (outside the bedroom)."""
        try:
            # Walk panda to the door (use door furniture piece position when available)
            _door_walk_x, _door_walk_z = 0.0, 2.8   # matches bedroom_door walk_z in _build_furniture
            try:
                if self._bedroom_widget:
                    _p = self._bedroom_widget.get_furniture('bedroom_door')
                    if _p:
                        _door_walk_x, _door_walk_z = _p.walk_x, _p.walk_z
            except Exception:
                pass
            if self.panda_widget and hasattr(self.panda_widget, 'walk_to_position'):
                self.panda_widget.walk_to_position(_door_walk_x, 0.0, _door_walk_z)
                self.panda_widget.set_animation_state('walking')

            # Build world widget if needed
            if self._world_widget is None:
                try:
                    from ui.panda_world_gl import PandaWorldWidget
                    self._world_widget = PandaWorldWidget(self)
                    self._world_widget.back_to_bedroom.connect(self._go_back_to_bedroom)
                    self._world_widget.otter_clicked.connect(self._on_otter_clicked)
                    self._world_widget.destination_selected.connect(self._on_world_destination_selected)
                    if hasattr(self._world_widget, 'gl_failed'):
                        def _on_world_gl_failed(msg: str) -> None:
                            logger.warning(f"World GL failed: {msg}")
                            self.log(f"⚠️ 3D World GL init failed: {msg}")
                            # Replace world widget with placeholder so user sees something useful
                            ph = QLabel(
                                "🌍 Outside World\n\n"
                                f"3D rendering unavailable: {msg[:80]}\n\n"
                                "Requires OpenGL 2.1+."
                            )
                            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            ph.setStyleSheet("background:#1a2a1a;color:#aaaaaa;font-size:12px;padding:20px;")
                            ph.setWordWrap(True)
                            self._world_widget = ph
                        self._world_widget.gl_failed.connect(_on_world_gl_failed)
                    # NOT added to _home_stack_owned — persistent panel re-used across visits.
                except (ImportError, OSError, RuntimeError, Exception) as _e:
                    logger.warning(f"World widget not available: {_e}")
                    self._world_widget = QLabel(
                        "🌍 Outside World\n\n"
                        "The 3D world requires PyQt6 + OpenGL.\n"
                        "Please install them and restart."
                    )
                    self._world_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._world_widget.setStyleSheet("background:#1a2a1a;color:#aaaaaa;font-size:13px;")
                    # NOT added to _home_stack_owned — persistent label re-used across visits.

            if self._world_widget:
                self._show_home_sub_panel(self._world_widget, '🌍 Outside World')
            self.statusBar().showMessage("🐼 Panda goes outside…", 3000)
        except Exception as _e:
            logger.debug(f"_go_outside: {_e}")

    def _go_back_to_bedroom(self) -> None:
        """Return from the world to the bedroom."""
        try:
            if self._home_stack:
                self._home_stack.setCurrentIndex(0)
            if self._home_back_bar:
                self._home_back_bar.hide()
            if self._panda_tabs and self._home_tab_index >= 0:
                self._panda_tabs.setTabText(self._home_tab_index, "🏠 Panda Home")
            if self.panda_widget:
                self.panda_widget.set_animation_state('idle')
        except Exception as _e:
            logger.debug(f"_go_back_to_bedroom: {_e}")

    def _on_otter_clicked(self) -> None:
        """Livy the otter was clicked — open Cosmic Otter Supply Co."""
        try:
            from ui.shop_panel_qt import ShopPanelQt
            if self._otter_shop_panel is None:
                self._otter_shop_panel = ShopPanelQt(
                    self.shop_system,
                    getattr(self, 'currency_system', None),
                    tooltip_manager=self.tooltip_manager,
                )
                self._otter_shop_panel.item_purchased.connect(self._on_shop_purchase_completed)
                # NOT added to _home_stack_owned — persistent panel re-used across visits.
            # Refresh coin balance every time the shop opens
            try:
                bal = self.currency_system.get_balance()
                self._otter_shop_panel.update_coin_display(bal)
            except Exception:
                pass
            self._show_home_sub_panel(self._otter_shop_panel, '🦦 Cosmic Otter Supply Co.')
            if self.panda_widget:
                self.panda_widget.set_animation_state('waving')
        except Exception as _e:
            logger.debug(f"_on_otter_clicked: {_e}")
            label = QLabel("🛒 Cosmic Otter Supply Co.\n\n(Shop panel not available)")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._home_stack_owned.append(label)
            self._show_home_sub_panel(label, '🦦 Cosmic Otter Supply Co.')

    def _on_world_destination_selected(self, destination: str) -> None:
        """Handle car/park/shop destination selection from the world scene."""
        try:
            self.statusBar().showMessage(f"🚗 Heading to {destination}…", 3000)
            if self.panda_widget:
                self.panda_widget.set_animation_state('walking')
            if destination == 'shop':
                self._on_otter_clicked()
            elif destination == 'park':
                self._on_go_to_park()
            elif destination == 'dungeon':
                self._on_go_to_dungeon()
            elif destination == 'home':
                self._go_back_to_bedroom()
        except Exception as _e:
            logger.debug(f"_on_world_destination_selected({destination}): {_e}")

    def _on_go_to_dungeon(self) -> None:
        """Drive the panda to the dungeon: play a car-travel animation then show the 3-D dungeon."""
        try:
            # Show travel animation first, then switch to 3-D dungeon when complete
            from ui.qt_travel_animation import TravelAnimationWidget, TravelScene, SceneType
            from features.travel_system import TravelSystem

            dungeon_scenes = [
                TravelScene(
                    scene_type=SceneType.GET_IN_CAR,
                    sky_color="#1a1a2a", ground_color="#2a2a1a",
                    road_color="#555555", detail_emoji="🌑",
                    description="🐼 Panda gets in the car…",
                    duration_ms=1500,
                ),
                TravelScene(
                    scene_type=SceneType.DRIVING,
                    sky_color="#0d0d1a", ground_color="#1a1a0d",
                    road_color="#444444", detail_emoji="🌲",
                    description="🚗 Driving to the dungeon…",
                    duration_ms=2500,
                ),
                TravelScene(
                    scene_type=SceneType.ARRIVE,
                    sky_color="#0a0505", ground_color="#1a0a0a",
                    road_color="#333333", detail_emoji="🏰",
                    description="⚔️ Arriving at the dungeon!",
                    duration_ms=1800,
                ),
            ]
            _ts = getattr(self, 'travel_system', None) or TravelSystem()
            travel_anim = TravelAnimationWidget(scenes=dungeon_scenes, travel_system=_ts)
            self._show_home_sub_panel(travel_anim, '🚗 Driving to Dungeon…')
            self.statusBar().showMessage("🚗 Panda is driving to the dungeon…", 4000)
            if self.panda_widget:
                self.panda_widget.set_animation_state('walking')

            def _enter_dungeon():
                try:
                    if self._dungeon_3d_panel is None:
                        from ui.dungeon_3d_widget import Dungeon3DWidget
                        from features.integrated_dungeon import IntegratedDungeon
                        dungeon = self.integrated_dungeon or IntegratedDungeon(
                            level_system=getattr(self, 'level_system', None),
                            currency_system=getattr(self, 'currency_system', None),
                        )
                        self._dungeon_3d_panel = Dungeon3DWidget(
                            dungeon=dungeon, tooltip_manager=self.tooltip_manager
                        )
                        # Wire coin drops from dungeon kills to the currency system
                        if hasattr(self._dungeon_3d_panel, 'coins_earned'):
                            self._dungeon_3d_panel.coins_earned.connect(
                                self._on_dungeon_coins_earned
                            )
                        if hasattr(self._dungeon_3d_panel, 'enemy_slain'):
                            self._dungeon_3d_panel.enemy_slain.connect(
                                self._on_dungeon_enemy_slain
                            )
                        # NOT added to _home_stack_owned — persistent panel
                    self._show_home_sub_panel(self._dungeon_3d_panel, '⚔️ Dungeon Adventure')
                    self.statusBar().showMessage(
                        "⚔️ Dungeon! WASD: move | F/LMB: melee | R/RMB: power | M: magic | Space: jump | E: interact", 8000
                    )
                    if self.panda_widget:
                        self.panda_widget.set_animation_state('idle')
                except Exception as _de:
                    logger.warning(f"_enter_dungeon: {_de}")
                    lbl = QLabel(
                        "⚔️ Dungeon Adventure\n\n"
                        "3-D dungeon requires PyOpenGL.\n\n"
                        "Install:  pip install PyOpenGL PyOpenGL_accelerate\n\n"
                        "The 2-D dungeon view is on the ⚔️ Adventure tab."
                    )
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setWordWrap(True)
                    lbl.setStyleSheet("background:#12090a;color:#aaaaaa;font-size:12px;padding:20px;")
                    self._show_home_sub_panel(lbl, '⚔️ Dungeon Adventure')

            travel_anim.animation_complete.connect(_enter_dungeon)
            travel_anim.start_animation()
        except Exception as _e:
            logger.warning(f"_on_go_to_dungeon: {_e}")

    def _on_go_to_park(self) -> None:
        """Show the park sub-panel (minigames / free play area) — cached like shop."""
        try:
            if self._park_panel is None:
                from ui.minigame_panel_qt import MinigamePanelQt
                from features.minigame_system import MiniGameManager
                mgr = MiniGameManager()
                self._park_panel = MinigamePanelQt(
                    minigame_manager=mgr, tooltip_manager=self.tooltip_manager
                )
                # NOT added to _home_stack_owned — persistent panel re-used across visits.
            self._show_home_sub_panel(self._park_panel, '🌲 Panda Park')
            if self.panda_widget:
                QTimer.singleShot(800, lambda: self.panda_widget.set_animation_state('celebrating'))
        except Exception as _e:
            logger.debug(f"_on_go_to_park: {_e}")
            if self._park_panel is None:
                park_label = QLabel(
                    "🌲 Panda Park\n\n"
                    "🐼 Panda romps around the park!\n\n"
                    "Minigames coming soon…"
                )
                park_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                park_label.setStyleSheet("background:#1a2a1a; color:#aaddaa; font-size:14px;")
                self._park_panel = park_label
                # NOT added to _home_stack_owned — persistent label re-used across visits.
            self._show_home_sub_panel(self._park_panel, '🌲 Panda Park')

    def _show_home_sub_panel(self, widget: 'QWidget', title: str) -> None:
        """Slide *widget* into page 1 of the Home stack, update tab + back-bar labels."""
        try:
            if not self._home_stack:
                return
            # Guard against stale C++ pointers (widget deleted between creation and show)
            try:
                _ = widget.objectName()   # cheap property access; raises RuntimeError if deleted
            except RuntimeError:
                logger.debug("_show_home_sub_panel: target widget already deleted")
                return
            # Remove page-1 widget — only delete it if WE created it AND it isn't the
            # same widget we're about to show (persistent panels like backpack are re-used).
            old = self._home_stack.widget(1)
            if old is not None and old is not widget:
                try:
                    _ = old.objectName()  # check old widget is still alive
                    self._home_stack.removeWidget(old)
                    if old in self._home_stack_owned:
                        self._home_stack_owned.remove(old)
                        old.deleteLater()
                except RuntimeError:
                    pass  # old widget already deleted externally; just ignore
            if self._home_stack.indexOf(widget) == -1:
                self._home_stack.insertWidget(1, widget)
            self._home_stack.setCurrentIndex(1)

            # Show back-bar with context title
            if self._home_back_bar:
                self._home_back_bar.show()
            if self._home_sub_label:
                self._home_sub_label.setText(title)

            # Update the tab label in the outer tab bar
            if self._panda_tabs and self._home_tab_index >= 0:
                self._panda_tabs.setTabText(self._home_tab_index, f"🏠 {title}")
                self._panda_tabs.setCurrentIndex(self._home_tab_index)
        except Exception as _e:
            logger.debug(f"_show_home_sub_panel: {_e}")

    def _on_bedroom_furniture_clicked(self, furniture_id: str) -> None:
        """Handle furniture click in the 3D bedroom.

        1. Walk panda to the furniture's world position.
        2. When panda arrives → play open_furniture animation + open sub-panel.
        3. Slide the corresponding sub-panel into the Home stack (NOT a separate tab).
        """
        def _safe_open(widget, fid):
            try:
                if widget and hasattr(widget, 'open_furniture'):
                    widget.open_furniture(fid)
            except Exception:
                pass

        # ── Bedroom door → go outside to world ───────────────────────────────
        if furniture_id == 'bedroom_door':
            self._go_outside()
            return

        # ── Map furniture → sub-panel title ───────────────────────────────────
        _TITLES = {
            'wardrobe':    '👗 Wardrobe / Closet',
            'armor_rack':  '🛡️ Armor',
            'weapons_rack':'⚔️ Weapons',
            'toy_box':     '🧸 Toys',
            'fridge':      '🍎 Food',
            'trophy_stand': '🏆 Achievements',
            'backpack':     '🎒 Inventory & Items',
            'computer_desk':'💻 Tools & Utilities',
        }
        sub_title = _TITLES.get(furniture_id, furniture_id.replace('_', ' ').title())

        # ── Resolve walk target ───────────────────────────────────────────────
        walk_x, walk_z = 0.0, 0.0
        category = 'All'
        try:
            if self._bedroom_widget:
                piece = self._bedroom_widget.get_furniture(furniture_id)
                if piece:
                    walk_x, walk_z = piece.walk_x, piece.walk_z
                    category = piece.category
        except Exception:
            pass

        # ── Define each furniture's panel-open function ───────────────────────
        if furniture_id == 'trophy_stand':
            def _open_panel():
                try:
                    if self._panda_tabs is not None and self._achievement_tab_index >= 0:
                        self._panda_tabs.setCurrentIndex(self._achievement_tab_index)
                        if self._achievement_panel and hasattr(self._achievement_panel, 'refresh_achievements'):
                            self._achievement_panel.refresh_achievements()
                    else:
                        ach_widget = getattr(self, '_achievement_panel', None)
                        if ach_widget is None:
                            ach_widget = QLabel("🏆 Achievements\n\n(Loading…)")
                            ach_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            self._home_stack_owned.append(ach_widget)
                        self._show_home_sub_panel(ach_widget, '🏆 Achievements')
                except Exception as _e2:
                    logger.debug(f"Trophy panel: {_e2}")
            self.statusBar().showMessage("🏆 Panda is checking their trophies…", 3000)

        elif furniture_id == 'wardrobe':
            def _open_panel():
                try:
                    cp = getattr(self, '_closet_panel', None)
                    if cp is None:
                        cp = QLabel("👔 Closet\n\n(Not available — check dependencies)")
                        cp.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self._home_stack_owned.append(cp)
                    self._show_home_sub_panel(cp, '👗 Wardrobe / Closet')
                except Exception as _e2:
                    logger.debug(f"Closet panel open: {_e2}")
            self.statusBar().showMessage("👔 Panda is walking to the wardrobe…", 3000)

        elif furniture_id == 'backpack':
            def _open_panel():
                try:
                    inv = getattr(self, '_inventory_panel', None)
                    wid = getattr(self, '_widgets_panel', None)
                    if inv is None and wid is None:
                        placeholder = QWidget()
                        placeholder.setStyleSheet("QWidget { background: #1a1a2e; }")
                        _ph_layout = QVBoxLayout(placeholder)
                        _ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        _ph_icon = QLabel("🎒")
                        _ph_icon.setStyleSheet("font-size: 48px; background: transparent;")
                        _ph_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        _ph_title = QLabel("Inventory & Items")
                        _ph_title.setStyleSheet(
                            "color: #ccccff; font-size: 16px; font-weight: bold; background: transparent;"
                        )
                        _ph_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        _ph_msg = QLabel(
                            "Inventory panels could not be loaded.\n"
                            "Run:  pip install -r requirements.txt\n"
                            "then restart the application."
                        )
                        _ph_msg.setStyleSheet("color: #8888aa; font-size: 11px; background: transparent;")
                        _ph_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        _ph_msg.setWordWrap(True)
                        _ph_layout.addWidget(_ph_icon)
                        _ph_layout.addWidget(_ph_title)
                        _ph_layout.addWidget(_ph_msg)
                        self._home_stack_owned.append(placeholder)
                        self._show_home_sub_panel(placeholder, '🎒 Inventory & Items')
                        return
                    if self._backpack_merged_panel is None:
                        from PyQt6.QtWidgets import QTabWidget as _TW, QVBoxLayout as _VBL
                        merged = _TW()
                        merged.setDocumentMode(True)
                        if inv is not None:
                            _inv_wrap = QWidget()
                            _inv_vb = QVBoxLayout(_inv_wrap)
                            _inv_vb.setContentsMargins(0, 0, 0, 0)
                            _inv_vb.addWidget(inv)
                            merged.addTab(_inv_wrap, "📦 Inventory")
                        if wid is not None:
                            _wid_wrap = QWidget()
                            _wid_vb = QVBoxLayout(_wid_wrap)
                            _wid_vb.setContentsMargins(0, 0, 0, 0)
                            _wid_vb.addWidget(wid)
                            merged.addTab(_wid_wrap, "🧸 Toys & Items")
                        self._backpack_merged_panel = merged
                    self._show_home_sub_panel(self._backpack_merged_panel, '🎒 Inventory & Items')
                except Exception as _e2:
                    logger.debug(f"Backpack panel open: {_e2}")
            self.statusBar().showMessage("🎒 Panda is walking to the backpack…", 3000)

        elif furniture_id == 'computer_desk':
            def _open_panel():
                try:
                    # Switch to the main tools tab if available
                    main_tabs = getattr(self, '_main_tabs', None) or getattr(self, 'tab_widget', None)
                    if main_tabs is not None:
                        main_tabs.setCurrentIndex(0)
                        self._show_home_sub_panel(None, '💻 Tools & Utilities')
                    else:
                        label = QLabel("💻 Tools & Utilities\n\nOpen the Tools tab to access image processing tools.")
                        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        label.setWordWrap(True)
                        self._home_stack_owned.append(label)
                        self._show_home_sub_panel(label, '💻 Tools & Utilities')
                except Exception as _e2:
                    logger.debug(f"Computer desk panel open: {_e2}")
            self.statusBar().showMessage("💻 Panda is sitting at the computer…", 3000)

        else:
            # All other furniture → show filtered Inventory panel
            def _open_panel():
                try:
                    inv = self._inventory_panel
                    if inv is None:
                        label = QLabel(f"📦 {sub_title}\n\n(Inventory not available)")
                        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self._home_stack_owned.append(label)
                        self._show_home_sub_panel(label, sub_title)
                        return
                    if self._backpack_merged_panel is None:
                        from PyQt6.QtWidgets import QTabWidget as _TW, QVBoxLayout as _VBL
                        merged = _TW()
                        merged.setDocumentMode(True)
                        _inv_wrap = QWidget()
                        _inv_vb = QVBoxLayout(_inv_wrap)
                        _inv_vb.setContentsMargins(0, 0, 0, 0)
                        _inv_vb.addWidget(inv)
                        merged.addTab(_inv_wrap, "📦 Inventory")
                        wid = getattr(self, '_widgets_panel', None)
                        if wid is not None:
                            _wid_wrap = QWidget()
                            _wid_vb = QVBoxLayout(_wid_wrap)
                            _wid_vb.setContentsMargins(0, 0, 0, 0)
                            _wid_vb.addWidget(wid)
                            merged.addTab(_wid_wrap, "🧸 Toys & Items")
                        self._backpack_merged_panel = merged
                    if hasattr(inv, 'set_category_filter'):
                        inv.set_category_filter(category)
                    elif hasattr(inv, 'refresh_inventory'):
                        inv.refresh_inventory()
                    self._backpack_merged_panel.setCurrentIndex(0)
                    self._show_home_sub_panel(self._backpack_merged_panel, sub_title)
                except Exception as _e2:
                    logger.debug(f"Inventory panel open: {_e2}")
            self.statusBar().showMessage(
                f"🐼 Panda is walking to the {furniture_id.replace('_', ' ').title()}…", 3000
            )

        # ── Walk panda; open panel + play animation after arrival ─────────────
        def _open_panel_after_walk():
            """Called when the bedroom panda reaches the furniture."""
            # Play overlay panda's open_furniture animation
            _safe_open(self.panda_widget, furniture_id)
            # Small buffer (200 ms) for the door-open animation before showing panel
            QTimer.singleShot(200, _open_panel)

        # Start the in-room panda walk
        _started_walk = False
        try:
            if self._bedroom_widget and hasattr(self._bedroom_widget, 'walk_panda_to'):
                self._bedroom_widget.walk_panda_to(walk_x, walk_z, callback=_open_panel_after_walk)
                _started_walk = True
        except Exception as _e:
            logger.debug(f"Bedroom panda walk: {_e}")

        # Start the overlay panda walk animation (independent, visual only)
        try:
            if self.panda_widget and hasattr(self.panda_widget, 'walk_to_position'):
                self.panda_widget.walk_to_position(walk_x, 0.0, walk_z)
        except Exception as _e:
            logger.debug(f"Overlay panda walk: {_e}")

        # Fallback: if no bedroom widget, open panel after a short delay
        if not _started_walk:
            QTimer.singleShot(400, _open_panel_after_walk)


    def _build_closet_items_list(self) -> list:
        """Return a list of item dicts from panda_closet suitable for ClosetDisplayWidget."""
        return [
            {
                'id':          it.id,
                'name':        it.name,
                'emoji':       it.emoji,
                'description': it.description,
                'category':    it.category.value,
                'rarity':      it.rarity.value if hasattr(it.rarity, 'value') else str(it.rarity),
                'cost':        it.cost,
                'unlocked':    it.unlocked,
                'equipped':    it.equipped,
                'clothing_type': getattr(it, 'clothing_type', ''),
            }
            for it in self.panda_closet.items.values()
        ]

    def _on_closet_item_equipped(self, item_data: dict):
        """Handle item equipped from closet display — forward to panda widget."""
        try:
            item_id = item_data.get('id', '')
            item_name = item_data.get('name', item_id)
            logger.info(f"Equipping closet item: {item_name}")
            self.statusBar().showMessage(f"👔 Equipped: {item_name}", 3000)
            if self.panda_widget and hasattr(self.panda_widget, 'equip_item'):
                self.panda_widget.equip_item(item_data)
            # Mark equipped in panda_closet + refresh the grid so equipped badge appears
            try:
                if self.panda_closet and item_id:
                    self.panda_closet.equip_item(item_id)
                    if hasattr(self, '_closet_panel') and self._closet_panel:
                        self._closet_panel.load_clothing_items(self._build_closet_items_list())
            except Exception as _ce:
                logger.debug(f"Closet equip/refresh error: {_ce}")
            # Check achievements after equipping
            self._check_closet_achievements(item_id)
        except Exception as _e:
            logger.debug(f"Closet item equipped callback error: {_e}")

    def _on_file_browser_file_selected(self, path):
        """Handle file selection in the file browser tab."""
        try:
            self.log(f"📄 File selected: {path}")
            self.statusBar().showMessage(f"Selected: {path}", 3000)
            # Update live preview pane if present
            if self.live_preview_widget:
                try:
                    _pix = QPixmap(str(path))
                    if not _pix.isNull():
                        self.live_preview_widget.set_original_image(_pix)
                except Exception:
                    pass
            # Show in standalone PreviewViewer when double-clicked (path non-empty)
            if self.preview_viewer and path:
                try:
                    self.preview_viewer.show_preview(path)
                except Exception:
                    pass
        except Exception as _e:
            logger.debug(f"File browser file_selected error: {_e}")

    def _on_file_browser_folder_changed(self, path):
        """Handle folder navigation in the file browser tab."""
        try:
            logger.debug(f"File browser folder changed to: {path}")
            self.statusBar().showMessage(f"📁 Browsing: {path}", 2000)
        except Exception as _e:
            logger.debug(f"File browser folder_changed error: {_e}")

    def _on_panda_should_hide(self, should_hide: bool):
        """Show/hide the panda overlay when environment events require it.

        The overlay is only ever shown on the Home tab; this method may further
        hide it (e.g. when the user minimises the window) but will never make it
        visible on a non-Home tab.
        """
        try:
            overlay = getattr(self, 'panda_overlay', None)
            if overlay is None or not hasattr(overlay, 'setVisible'):
                return
            on_home = (self.tabs.currentIndex() == 0)
            overlay.setVisible(on_home and not should_hide)
            logger.debug(f"Panda overlay hide={should_hide}, on_home={on_home}")
        except Exception as _e:
            logger.debug(f"panda_should_hide callback error: {_e}")

    def _on_main_tab_changed(self, index: int) -> None:
        """Keep the panda companion overlay visible on all tabs.

        The overlay uses WA_TransparentForMouseEvents so mouse events pass
        through to the UI elements behind it on every tab — it does not block
        interactive widgets.  The panda companion should be a persistent
        presence throughout the application, not just on the Home tab.
        """
        try:
            overlay = getattr(self, 'panda_overlay', None)
            if overlay is None or not hasattr(overlay, 'setVisible'):
                return
            # Always keep the overlay visible; raise it above other widgets in
            # case a tab change caused z-order restack.
            overlay.setVisible(True)
            overlay.raise_()
        except Exception as _e:
            logger.debug(f"_on_main_tab_changed error: {_e}")

    def _on_panda_should_react(self, event_type: str, event_data):
        """Forward environment events to the panda mood system for reactions."""
        try:
            if self.panda_mood_system:
                self.panda_mood_system.on_user_interaction(event_type)
            logger.debug(f"Panda react: {event_type}")
        except Exception as _e:
            logger.debug(f"panda_should_react callback error: {_e}")

    def _save_profile(self):
        """Save current organization settings as a named profile."""
        try:
            if not self.profile_manager:
                QMessageBox.information(self, "Profiles", "Profile manager not available.")
                return
            name, ok = QInputDialog.getText(self, "Save Profile", "Profile name:")
            if ok and name.strip():
                if self.profile_manager.save_profile(name.strip()):
                    self.statusBar().showMessage(f"✅ Profile saved: {name.strip()}", 3000)
                    logger.info(f"Profile saved: {name.strip()}")
                else:
                    QMessageBox.warning(self, "Save Profile", f"Failed to save profile '{name.strip()}'.")
        except Exception as e:
            logger.error(f"Error saving profile: {e}", exc_info=True)

    def _load_profile(self):
        """Load a named profile from the profile manager."""
        try:
            if not self.profile_manager:
                QMessageBox.information(self, "Profiles", "Profile manager not available.")
                return
            profiles = self.profile_manager.list_profiles()
            if not profiles:
                QMessageBox.information(self, "Load Profile", "No saved profiles found.")
                return
            names = [p.get('name', str(p)) for p in profiles]
            name, ok = QInputDialog.getItem(self, "Load Profile", "Select profile:", names, 0, False)
            if ok and name:
                profile = self.profile_manager.load_profile(name)
                if profile:
                    self.statusBar().showMessage(f"✅ Profile loaded: {name}", 3000)
                    logger.info(f"Profile loaded: {name}")
                else:
                    QMessageBox.warning(self, "Load Profile", f"Failed to load profile '{name}'.")
        except Exception as e:
            logger.error(f"Error loading profile: {e}", exc_info=True)

    def _create_restore_point(self):
        """Create a manual backup restore point via BackupManager."""
        try:
            if not self.backup_manager:
                QMessageBox.information(self, "Backup", "Backup manager not available.")
                return
            name, ok = QInputDialog.getText(self, "Create Restore Point", "Restore point name (optional):")
            if ok:
                label = name.strip() or "manual"
                result = self.backup_manager.create_restore_point(label=label)
                if result:
                    self.statusBar().showMessage(f"✅ Restore point created: {label}", 3000)
                    logger.info(f"Restore point created: {label}")
                else:
                    QMessageBox.warning(self, "Create Restore Point", "Failed to create restore point.")
        except Exception as e:
            logger.error(f"Error creating restore point: {e}", exc_info=True)

    def _find_duplicate_textures(self):
        """Find and display duplicate/near-duplicate textures using SimilaritySearch."""
        try:
            if not self.duplicate_detector:
                QMessageBox.information(
                    self, "Find Duplicates",
                    "SimilaritySearch not available.\n"
                    "Install torch + faiss to enable duplicate detection."
                )
                return
            if not self.input_path:
                QMessageBox.warning(self, "Find Duplicates", "Please select an input folder first.")
                return
            self.statusBar().showMessage("🔍 Scanning for duplicates…")
            groups = self.duplicate_detector.find_duplicates(threshold=0.95)
            if not groups:
                QMessageBox.information(self, "Find Duplicates", "No duplicate textures found.")
            else:
                msg = "\n".join(
                    f"Group {i + 1}: {len(g)} files ({g[0]}…)"
                    for i, g in enumerate(groups[:10])
                )
                if len(groups) > 10:
                    msg += f"\n…and {len(groups) - 10} more groups"
                QMessageBox.information(self, f"Found {len(groups)} Duplicate Group(s)", msg)
            self.statusBar().showMessage(f"✅ Duplicate scan complete — {len(groups)} group(s)", 4000)
            logger.info(f"Duplicate scan complete: {len(groups)} group(s)")
        except Exception as e:
            logger.error(f"Duplicate scan error: {e}", exc_info=True)
            QMessageBox.critical(self, "Find Duplicates", f"Error during duplicate scan:\n{e}")

    def _analyze_selected_texture(self):
        """Analyze a user-selected texture file and display results."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            path_str, _ = QFileDialog.getOpenFileName(
                self, "Select Texture to Analyze", str(self.input_path or ""),
                "Images (*.png *.dds *.tga *.jpg *.bmp *.tif *.tiff);;All Files (*)"
            )
            if not path_str:
                return
            if not self.texture_analyzer:
                QMessageBox.information(
                    self, "Analyze Texture",
                    "TextureAnalyzer not available.\n"
                    "Install Pillow to enable texture analysis."
                )
                return
            from pathlib import Path as _Path
            analysis = self.texture_analyzer.analyze(_Path(path_str))
            lines = [f"<b>{Path(path_str).name}</b>"]
            for key, val in list(analysis.items())[:20]:
                if isinstance(val, float):
                    val = f"{val:.3f}"
                lines.append(f"<b>{key}:</b> {val}")
            QMessageBox.information(
                self, "Texture Analysis",
                "<br>".join(lines)
            )
            logger.info(f"Texture analyzed: {path_str}")
        except Exception as e:
            logger.error(f"Texture analysis error: {e}", exc_info=True)
            QMessageBox.critical(self, "Analyze Texture", f"Error during analysis:\n{e}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>A professional Qt6-based texture sorting application with:</p>"
            f"<ul>"
            f"<li>Hardware-accelerated OpenGL rendering</li>"
            f"<li>Advanced AI classification</li>"
            f"<li>Modern Qt6 interface</li>"
            f"<li>No tkinter, no canvas</li>"
            f"</ul>"
            f"<p>Author: Dead On The Inside / JosephsDeadish</p>"
            f"<p>❤️ Support us on Patreon: <a href='{PATREON_URL}'>{PATREON_URL}</a></p>"
        )

    def _open_patreon(self):
        """Open the Patreon support page in the default browser."""
        try:
            import webbrowser
            webbrowser.open(PATREON_URL)
        except Exception as _e:
            logger.debug(f"_open_patreon: {_e}")

    def show_help(self):
        """Show help / documentation dialog (F1)."""
        help_text = (
            f"<h2>🐼 {APP_NAME} — Quick Help</h2>"
            "<h3>Tools</h3>"
            "<ul>"
            "<li><b>📁 Organizer</b> — Sort images into sub-folders by category, date, size or hash.</li>"
            "<li><b>🎭 Background Remover</b> — Remove backgrounds using AI (rembg/ONNX) or edge detection.</li>"
            "<li><b>✨ Alpha Fixer</b> — Repair transparent / semi-transparent alpha channels.</li>"
            "<li><b>🎨 Color Correction</b> — Batch adjust brightness, contrast, saturation and curves.</li>"
            "<li><b>⚙️ Batch Normalizer</b> — Resize, pad or crop images to a target resolution.</li>"
            "<li><b>✓ Quality Checker</b> — Detect blurry, corrupt or low-quality images.</li>"
            "<li><b>🔍 Image Upscaler</b> — Upscale via Real-ESRGAN or Pillow bicubic.</li>"
            "<li><b>✏️ Line Art</b> — Convert photos or textures to clean line-art / sketch.</li>"
            "<li><b>🔄 Format Converter</b> — Batch convert between PNG, JPEG, WebP, DDS, TGA and more.</li>"
            "<li><b>📝 Batch Rename</b> — Rename files with templates, counters, date/EXIF tags.</li>"
            "<li><b>🔧 Image Repair</b> — Fix corrupted image headers and reserialise lossy files.</li>"
            "</ul>"
            "<h3>Workflow</h3>"
            "<ol>"
            "<li>Select an <b>Input Folder</b> on the Home tab or via File → Open Input Folder.</li>"
            "<li>Choose an <b>Output Folder</b> (optional — defaults to a sub-folder of input).</li>"
            "<li>Open the desired tool from the <b>Tools</b> tab or via the Quick Launch buttons.</li>"
            "<li>Adjust options and click <b>Process</b> / <b>Start</b>.</li>"
            "</ol>"
            "<h3>Panda Features</h3>"
            "<p>The <b>🐼 Panda</b> tab contains your virtual panda companion with a bedroom, "
            "closet, shop, minigames, achievements, quests and an adventure dungeon. "
            "Interact with the panda for rewards and unlockable themes!</p>"
            "<h3>Keyboard Shortcuts</h3>"
            "<ul>"
            "<li><b>F1</b> — This help dialog</li>"
            "<li><b>Ctrl+O</b> — Open input folder</li>"
            "<li><b>Ctrl+Q</b> — Quit</li>"
            "</ul>"
            f"<p><small>Version {APP_VERSION} &bull; "
            f"Support us on Patreon: <a href='{PATREON_URL}'>{PATREON_URL}</a></small></p>"
        )
        msg = QMessageBox(self)
        msg.setWindowTitle(f"{APP_NAME} — Help")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def save_settings(self) -> bool:
        """Flush the current config to disk.

        Settings in ``SettingsPanelQt`` already persist themselves immediately
        on every widget change via ``on_setting_changed`` → ``config.save()``.
        This method exists only for programmatic callers (e.g. ``closeEvent``)
        that want a guaranteed final flush — it does **not** correspond to any
        "Save Settings" button in the UI.

        Returns
        -------
        bool
            True if the config was flushed successfully, False otherwise.
        """
        try:
            config.save()
            logger.info("Settings flushed to disk")
            return True
        except Exception as _e:
            logger.error(f"save_settings failed: {_e}", exc_info=True)
            return False

    def load_settings(self) -> bool:
        """Reload settings from disk into the UI.

        Delegates to SettingsPanelQt when available, then re-applies the
        theme so the live UI reflects the persisted values.

        Returns
        -------
        bool
            True if settings were reloaded successfully, False otherwise.
        """
        try:
            if self.settings_panel and hasattr(self.settings_panel, 'load_settings'):
                self.settings_panel.load_settings()
            self.apply_theme()
            logger.info("Settings loaded")
            return True
        except Exception as _e:
            logger.error(f"load_settings failed: {_e}", exc_info=True)
            return False

    def _offer_crash_recovery(self) -> None:
        """Called by AutoBackupSystem when a previous session crashed.

        Uses a deferred single-shot timer so the dialog appears *after* the
        main window finishes initialising (the callback may fire during
        ``auto_backup.start()`` which runs inside ``initialize_components``).

        If the first-run tutorial is currently active the dialog is re-deferred
        by 3 s each check so it never appears behind the tutorial overlay where
        the user cannot click its buttons.
        """
        def _show_dialog():
            try:
                # If the tutorial overlay is blocking input, wait for it to finish.
                _tm = self._tutorial_manager
                if _tm is not None and _tm.tutorial_active:
                    QTimer.singleShot(3000, _show_dialog)
                    return
                reply = QMessageBox.question(
                    self,
                    "⚠️ Crash Recovery",
                    "It looks like the previous session ended unexpectedly.\n\n"
                    "Would you like to restore from the last auto-backup?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    state = self.auto_backup.restore_from_backup() if self.auto_backup else None
                    if state:
                        # Re-apply any paths that were saved in the backup state
                        input_path = state.get('input_path')
                        output_path = state.get('output_path')
                        if input_path and Path(input_path).exists():
                            self.input_path_label.setText(input_path)
                        if output_path and Path(output_path).exists():
                            self.output_path_label.setText(output_path)
                        self.statusBar().showMessage("✅ Session restored from backup", 5000)
                        self.log("✅ Session restored from auto-backup after crash.")
                        logger.info("Crash recovery: session state restored")
                    else:
                        QMessageBox.information(
                            self, "Recovery",
                            "No backup data found or restore failed.\n"
                            "Starting with a clean session."
                        )
                else:
                    self.log("ℹ️ Crash recovery skipped by user.")
            except Exception as _e:
                logger.debug(f"_offer_crash_recovery dialog: {_e}")
        # Defer until after __init__ / initialize_components finishes
        QTimer.singleShot(1000, _show_dialog)

    # ── App-level event filter: button hover → panda peek/poke ──────────────
        try:
            from PyQt6.QtCore import QEvent
            from PyQt6.QtWidgets import QPushButton
            if (event.type() == QEvent.Type.Enter
                    and isinstance(obj, QPushButton)
                    and self.panda_widget
                    and hasattr(self.panda_widget, 'notify_button_nearby')):
                self.panda_widget.notify_button_nearby()
        except Exception:
            pass
        return super().eventFilter(obj, event)

    # ── Drag-and-drop file handling ──────────────────────────────────────────
    def dragEnterEvent(self, event: 'QDragEnterEvent'):
        """Accept file drag-and-drop from OS."""
        try:
            if event.mimeData().hasUrls():
                self._drag_sniff_notified = False  # reset throttle flag each new drag
                event.acceptProposedAction()
            else:
                event.ignore()
        except Exception:
            event.ignore()

    def dragMoveEvent(self, event: 'QDragMoveEvent'):
        """Keep accepting while dragging over the window; notify panda once per drag."""
        try:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                # Notify panda to sniff — throttled to once per drag operation
                if not getattr(self, '_drag_sniff_notified', False):
                    self._drag_sniff_notified = True
                    urls = event.mimeData().urls()
                    if urls:
                        file_path = urls[0].toLocalFile()
                        if self.panda_widget and hasattr(self.panda_widget, 'notify_file_dragged'):
                            self.panda_widget.notify_file_dragged(file_path)
                        elif self.panda_overlay and hasattr(self.panda_overlay, 'notify_file_dragged'):
                            self.panda_overlay.notify_file_dragged(file_path)
        except Exception:
            event.ignore()

    def dropEvent(self, event: 'QDropEvent'):
        """Handle dropped files — forward to input path selector."""
        try:
            urls = event.mimeData().urls()
            if not urls:
                return
            dropped_path = Path(urls[0].toLocalFile())
            # Reset panda sniff state
            if self.panda_widget and hasattr(self.panda_widget, 'set_animation_state'):
                self.panda_widget.set_animation_state('idle')
            # Show in status bar
            self.statusBar().showMessage(f"📄 Dropped: {dropped_path.name}", 3000)
            # Auto-fill the input path if it's a directory
            if dropped_path.is_dir():
                try:
                    self.input_folder_entry.setText(str(dropped_path))
                    self.input_path = dropped_path
                except Exception:
                    pass
            event.acceptProposedAction()
        except Exception as _e:
            logger.debug(f"dropEvent error: {_e}")
    # ─────────────────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        """Resize transparent panda overlay to always cover the full window."""
        super().resizeEvent(event)
        try:
            if self.panda_overlay is not None:
                self.panda_overlay.resize(self.size())
        except Exception:
            pass

    def closeEvent(self, event):
        """Handle window close event."""
        # Save dock layout before closing
        try:
            self.save_dock_layout()
        except Exception as e:
            logger.error(f"Error saving dock layout on exit: {e}", exc_info=True)
        
        # Save settings before closing
        try:
            config.save()
            logger.info("Settings saved on exit")
        except Exception as e:
            logger.error(f"Error saving settings on exit: {e}", exc_info=True)

        # Save bedroom furniture layout
        try:
            if hasattr(self, '_bedroom_widget') and self._bedroom_widget and hasattr(self._bedroom_widget, 'get_layout'):
                config.set('ui.bedroom_layout', self._bedroom_widget.get_layout())
                logger.info("Bedroom layout saved on exit")
        except Exception as e:
            logger.warning(f"Could not save bedroom layout: {e}")
        
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Operation in Progress",
                "An operation is currently running. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.worker:
                    self.worker.cancel()
                    self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

        if event.isAccepted():
            # Stop background services gracefully
            try:
                if self.auto_backup:
                    self.auto_backup.stop()
            except Exception:
                pass
            try:
                if self.level_system:
                    self.level_system.save()
            except Exception:
                pass
            try:
                if self.perf_dashboard:
                    self.perf_dashboard.stop()
            except Exception:
                pass
            try:
                if self.panda_stats:
                    _stats_path = Path(__file__).parent / 'app_data' / 'panda_stats.json'
                    self.panda_stats.save_to_file(str(_stats_path))
            except Exception:
                pass
            try:
                if self.batch_queue:
                    self.batch_queue.stop()
            except Exception:
                pass
            try:
                if self.threading_manager:
                    self.threading_manager.stop()
            except Exception:
                pass
            # Save skill tree progression
            try:
                if self.skill_tree:
                    import json as _json
                    self._skill_tree_path.parent.mkdir(parents=True, exist_ok=True)
                    self._skill_tree_path.write_text(
                        _json.dumps(self.skill_tree.to_dict(), indent=2), encoding='utf-8'
                    )
            except Exception:
                pass
            # Save adventure level progression
            try:
                if self.adventure_level:
                    self.adventure_level.save_to_file(self._adventure_level_path)
            except Exception:
                pass
            # Save closet state (unlocked items, appearance)
            try:
                if self.panda_closet:
                    self._closet_path.parent.mkdir(parents=True, exist_ok=True)
                    self.panda_closet.save_to_file(str(self._closet_path))
            except Exception:
                pass
            # Save weapon collection state
            try:
                if self.weapon_collection:
                    self.weapon_collection.save_to_file(self._weapon_collection_path)
            except Exception:
                pass
            # Close texture database cleanly
            try:
                if self.database:
                    self.database.close()
            except Exception:
                pass
    
    def _make_tab_dock(self, tab_name: str, clean_name: str, widget: QWidget) -> QDockWidget:
        """Create a QDockWidget for a detached tab with a 'Restore as Tab' context menu."""
        dock = QDockWidget(tab_name, self)
        # objectName must be unique for QMainWindow.saveState() to serialise
        # geometry correctly.  Build a safe ASCII name from clean_name and append
        # a counter so that two tabs with names that differ only in special
        # characters (e.g. 'My-Tab' vs 'My_Tab') don't collide.
        safe_name = ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in clean_name)
        counter = getattr(self, '_tab_dock_counter', 0) + 1
        self._tab_dock_counter = counter
        dock.setObjectName(f"dock_tab_{safe_name}_{counter}")
        dock.setWidget(widget)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        # Allow docking into all four side areas so the user can drag it back
        # to any edge; closing restores it to the tab bar.
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.BottomDockWidgetArea
        )
        # Right-click context menu on the title bar → "Restore as Tab"
        dock.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        dock.customContextMenuRequested.connect(
            lambda pos, n=clean_name, orig=tab_name: self._show_dock_context_menu(pos, n, orig)
        )
        # visibilityChanged → deferred restore (crash-safe)
        dock.visibilityChanged.connect(
            lambda visible, name=clean_name, original_name=tab_name:
                self._on_dock_visibility_changed(visible, name, original_name)
        )
        return dock

    def _show_dock_context_menu(self, pos, name: str, original_name: str):
        """Show context menu on a floating/docked dock widget."""
        dock = self.docked_widgets.get(name)
        menu = QMenu(self)
        restore_action = menu.addAction("📌 Restore as Tab")
        # pos is in dock-local coordinates; map to global for exec()
        global_pos = dock.mapToGlobal(pos) if dock is not None else self.cursor().pos()
        action = menu.exec(global_pos)
        if action == restore_action:
            self.restore_docked_tab(name, original_name)

    def on_tab_detached(self, index: int, tab_name: str, widget: QWidget):
        """Handle tab being dragged out - create floating dock widget."""
        if index < 0 or widget is None:
            return
        
        # Remove emoji and clean up name for tracking
        clean_name = tab_name.replace("🛠️", "").replace("🐼", "").replace("📁", "").replace("📝", "").strip()
        
        # Store reference
        self.tab_widgets[clean_name] = widget
        
        # Remove from tabs
        self.tabs.removeTab(index)
        
        dock = self._make_tab_dock(tab_name, clean_name, widget)
        
        # Store dock reference
        self.docked_widgets[clean_name] = dock
        
        # Add as floating dock (detached)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        dock.setFloating(True)
        
        # Position near mouse cursor
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        dock.move(self.pos().x() + cursor_pos.x(), self.pos().y() + cursor_pos.y())
        
        # Update restore menu
        self._update_restore_menu()
        
        self.statusbar.showMessage(f"Tab detached: {clean_name}", 3000)
        logger.info(f"Tab dragged out and detached: {tab_name}")
    
    def popout_current_tab(self):
        """Pop out the currently selected tab into a floating dock widget."""
        current_index = self.tabs.currentIndex()
        if current_index < 0:
            return
        
        tab_name = self.tabs.tabText(current_index)
        # Remove emoji and clean up name
        clean_name = tab_name.replace("🛠️", "").replace("🐼", "").replace("📁", "").replace("📝", "").strip()
        
        # Get the widget from the current tab
        widget = self.tabs.widget(current_index)
        
        # Store reference
        self.tab_widgets[clean_name] = widget
        
        # Remove from tabs
        self.tabs.removeTab(current_index)
        
        dock = self._make_tab_dock(tab_name, clean_name, widget)
        
        # Store dock reference
        self.docked_widgets[clean_name] = dock
        
        # Add as floating dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        dock.setFloating(True)
        
        # Update restore menu
        self._update_restore_menu()
        
        self.statusbar.showMessage(f"Popped out: {clean_name}", 3000)
    
    def _on_dock_visibility_changed(self, visible: bool, name: str, original_name: str):
        """Handle dock widget visibility changes (when user closes dock).

        visibilityChanged(False) fires in three situations:
          1. User clicks the dock's X button → we want to restore to tabs.
          2. Qt briefly hides the dock during a re-dock drag → we must ignore.
          3. App teardown / C++ object deleted → we must not touch the dock.

        Guard: only act when the dock is *closed* (isVisible() is False AND the
        widget is not being physically docked into a docking area).
        """
        if not visible and name not in self._restoring_docks:
            # Use QTimer.singleShot so Qt finishes its internal state update
            # before we touch the dock widget (avoids C++ teardown race).
            QTimer.singleShot(0, lambda: self._deferred_restore(name, original_name))

    def _deferred_restore(self, name: str, original_name: str):
        """Deferred restore: called after Qt's event loop processes dock teardown."""
        if name not in self.docked_widgets or name in self._restoring_docks:
            return
        dock = self.docked_widgets.get(name)
        if dock is None:
            return
        try:
            # If the dock is still visible or floating-but-shown, user just
            # re-docked it into a side area → do not restore to tabs.
            if dock.isVisible():
                return
        except RuntimeError:
            # C++ object already deleted (app teardown) – nothing to do.
            return
        self.restore_docked_tab(name, original_name)

    def restore_docked_tab(self, name: str, original_name: str = None):
        """Restore a docked tab back to the main tab widget."""
        if name not in self.docked_widgets or name in self._restoring_docks:
            return

        self._restoring_docks.add(name)
        try:
            dock = self.docked_widgets[name]
            try:
                # Disconnect visibilityChanged BEFORE touching the dock so that
                # removeDockWidget() doesn't fire a second visibility event and
                # cause a re-entrant restore call.
                dock.visibilityChanged.disconnect()
            except (RuntimeError, TypeError):
                pass  # Already disconnected or C++ object gone

            # Prefer the widget reference we stored at detach time because
            # dock.widget() returns None after setWidget(None) is called.
            widget = self.tab_widgets.get(name)
            try:
                if widget is None:
                    widget = dock.widget()
                dock.setWidget(None)  # Detach widget so Qt doesn't delete it
            except RuntimeError:
                widget = self.tab_widgets.get(name)  # Last resort from stored ref

            try:
                self.removeDockWidget(dock)
            except RuntimeError:
                pass

            del self.docked_widgets[name]
            # Clean up stored reference too
            self.tab_widgets.pop(name, None)

            # Restore to tabs
            if widget is not None:
                tab_name = original_name if original_name else name
                self.tabs.addTab(widget, tab_name)
                self.statusbar.showMessage(f"Restored: {name}", 3000)

            # Update restore menu
            self._update_restore_menu()
        finally:
            self._restoring_docks.discard(name)
    
    def _update_restore_menu(self):
        """Update the restore menu with currently docked tabs."""
        self.restore_menu.clear()
        
        if not self.docked_widgets:
            self.restore_menu.setEnabled(False)
            return
        
        self.restore_menu.setEnabled(True)
        
        for name, dock in self.docked_widgets.items():
            action = QAction(f"Restore {name}", self)
            action.triggered.connect(
                lambda checked, n=name, orig=dock.windowTitle(): 
                    self.restore_docked_tab(n, orig)
            )
            self.restore_menu.addAction(action)
    
    def reset_window_layout(self):
        """Reset all docked windows back to tabs."""
        # Snapshot keys so we can mutate self.docked_widgets during iteration
        docked_names = list(self.docked_widgets.keys())
        for name in docked_names:
            dock = self.docked_widgets.get(name)
            if dock is not None:
                try:
                    orig = dock.windowTitle()
                except RuntimeError:
                    orig = name
                self.restore_docked_tab(name, orig)

        self.statusbar.showMessage("Window layout reset", 3000)
    
    def save_dock_layout(self):
        """Save current dock layout to config."""
        try:
            # Save main window geometry
            geometry = self.saveGeometry()
            state = self.saveState()
            
            config.set('window', 'geometry', value=geometry.toHex().data().decode())
            config.set('window', 'state', value=state.toHex().data().decode())
            
            # Save docked tabs info
            docked_tabs = list(self.docked_widgets.keys())
            config.set('window', 'docked_tabs', value=','.join(docked_tabs))
            
            # Save tool dock visibility
            tool_dock_states = {}
            for tool_id, dock in self.tool_dock_widgets.items():
                tool_dock_states[tool_id] = {
                    'visible': dock.isVisible(),
                    'floating': dock.isFloating(),
                }
            config.set('window', 'tool_dock_states', value=str(tool_dock_states))
            
            config.save()
            logger.info("Dock layout saved")
        except Exception as e:
            logger.error(f"Error saving dock layout: {e}", exc_info=True)
    
    def restore_dock_layout(self):
        """Restore dock layout from config."""
        try:
            # Restore main window geometry and state
            geometry_hex = config.get('window', 'geometry', default=None)
            state_hex = config.get('window', 'state', default=None)
            
            if geometry_hex:
                geometry = QByteArray.fromHex(geometry_hex.encode())
                self.restoreGeometry(geometry)
            
            if state_hex:
                state = QByteArray.fromHex(state_hex.encode())
                self.restoreState(state)
            
            # Restore tool dock states
            tool_states_str = config.get('window', 'tool_dock_states', default='{}')
            try:
                import ast
                tool_states = ast.literal_eval(tool_states_str)
                for tool_id, state in tool_states.items():
                    if tool_id in self.tool_dock_widgets:
                        dock = self.tool_dock_widgets[tool_id]
                        dock.setVisible(state.get('visible', True))
                        dock.setFloating(state.get('floating', False))
            except Exception:
                pass
            
            logger.info("Dock layout restored")
        except Exception as e:
            logger.error(f"Error restoring dock layout: {e}", exc_info=True)


def check_feature_availability():
    """
    Check availability of optional features and return status dict.
    
    Returns:
        dict: Dictionary with feature availability status
    """
    features = {
        'pil': False,
        'pytorch': False,
        'pytorch_cuda': False,
        'clip': False,
        'dinov2': False,
        'transformers': False,
        'open_clip': False,
        'timm': False,
        'onnx': False,
        'onnxruntime': False,
        'upscaler': False,  # Real-ESRGAN upscaler
        'realesrgan': False,  # DEPRECATED: Use 'upscaler' instead (kept for backward compatibility)
        'native_lanczos': False,
    }
    
    # Check PIL/Pillow - CRITICAL for image loading and vision models
    try:
        from PIL import Image
        import PIL._imaging  # Check binary module
        features['pil'] = True
    except (ImportError, OSError, RuntimeError):
        pass
    except Exception as e:
        logger.warning(f"PIL check failed: {e}")
    
    # Check PyTorch
    try:
        import torch
        features['pytorch'] = True
        features['pytorch_cuda'] = torch.cuda.is_available()
        logger.info(f"✓ PyTorch available (CUDA: {features['pytorch_cuda']})")
    except Exception as e:
        features['pytorch'] = False
        features['pytorch_cuda'] = False
        logger.debug(f"PyTorch not available: {e}")
    
    # Check ONNX
    try:
        import onnx
        features['onnx'] = True
        logger.info("✓ ONNX available")
    except Exception as e:
        features['onnx'] = False
        logger.debug(f"ONNX not available: {e}")
    
    # Check ONNX Runtime
    try:
        import onnxruntime
        features['onnxruntime'] = True
        logger.info("✓ ONNX Runtime available")
    except Exception as e:
        features['onnxruntime'] = False
        logger.debug(f"ONNX Runtime not available: {e}")
    
    # Check transformers
    try:
        import transformers
        features['transformers'] = True
        logger.info("✓ Transformers available")
    except Exception as e:
        features['transformers'] = False
        logger.debug(f"Transformers not available: {e}")
    
    # Check open_clip
    try:
        import open_clip
        features['open_clip'] = True
        logger.info("✓ Open CLIP available")
    except Exception as e:
        features['open_clip'] = False
        logger.debug(f"Open CLIP not available: {e}")
    
    # Check timm
    try:
        import timm
        features['timm'] = True
        logger.info("✓ timm available")
    except Exception as e:
        features['timm'] = False
        logger.debug(f"timm not available: {e}")
    
    # Check Real-ESRGAN upscaling
    try:
        from preprocessing.upscaler import REALESRGAN_AVAILABLE
        features['upscaler'] = REALESRGAN_AVAILABLE
        features['realesrgan'] = REALESRGAN_AVAILABLE  # DEPRECATED: Kept for backward compatibility
        if REALESRGAN_AVAILABLE:
            logger.info("✓ Real-ESRGAN upscaler available")
    except Exception as e:
        features['upscaler'] = False
        features['realesrgan'] = False
        logger.debug(f"Real-ESRGAN not available: {e}")
    
    # Check native Rust Lanczos upscaling
    try:
        from native_ops import NATIVE_AVAILABLE
        features['native_lanczos'] = NATIVE_AVAILABLE
        if NATIVE_AVAILABLE:
            logger.info("✓ Native Lanczos upscaling available")
    except Exception as e:
        features['native_lanczos'] = False
        logger.debug(f"Native ops not available: {e}")
    
    # CLIP requires PIL + PyTorch + (transformers OR open_clip)
    features['clip'] = features['pil'] and features['pytorch'] and (features['transformers'] or features['open_clip'])
    
    # DINOv2 requires PIL + PyTorch
    features['dinov2'] = features['pil'] and features['pytorch']
    
    return features


def log_startup_diagnostics(window):
    """
    Log startup diagnostics showing which features are available.
    
    Args:
        window: Main window to log messages to
    """
    window.log("=" * 60)
    window.log("🔍 STARTUP DIAGNOSTICS")
    window.log("=" * 60)
    
    # Check features
    features = check_feature_availability()
    
    # Core features (always available)
    window.log("✅ Core Features:")
    if features['pil']:
        window.log("   ✅ PIL/Pillow (Image loading)")
    else:
        window.log("   ❌ PIL/Pillow not available - CRITICAL!")
        window.log("   💡 Install: pip install pillow")
        window.log("   ⚠️  Vision models will NOT work without PIL")
    window.log("   ✅ Image processing (OpenCV)")
    window.log("   ✅ Texture classification")
    window.log("   ✅ LOD detection")
    window.log("   ✅ File organization")
    window.log("   ✅ Archive support (ZIP, 7Z, RAR)")
    
    # PyTorch features
    window.log("")
    if features['pytorch']:
        window.log("✅ PyTorch Features:")
        window.log("   ✅ PyTorch available")
        if features['pytorch_cuda']:
            window.log("   ✅ CUDA GPU acceleration available")
        else:
            window.log("   ⚠️  CUDA not available (CPU-only mode)")
    else:
        window.log("⚠️  PyTorch Features:")
        window.log("   ❌ PyTorch not available")
        window.log("   💡 Install: pip install torch torchvision")
    
    # Vision models
    window.log("")
    if features['clip'] or features['dinov2']:
        window.log("✅ AI Vision Models:")
        if features['clip']:
            window.log("   ✅ CLIP model available")
            if features['transformers']:
                window.log("      ✅ Using HuggingFace transformers")
            if features['open_clip']:
                window.log("      ✅ Using OpenCLIP")
        else:
            window.log("   ❌ CLIP model not available")
            if not features['pil']:
                window.log("      ❌ Missing PIL/Pillow")
            if not features['pytorch']:
                window.log("      ❌ Missing PyTorch")
            if not (features['transformers'] or features['open_clip']):
                window.log("      ❌ Missing transformers/open_clip")
        
        if features['dinov2']:
            window.log("   ✅ DINOv2 model available")
        else:
            window.log("   ❌ DINOv2 model not available")
            if not features['pil']:
                window.log("      ❌ Missing PIL/Pillow")
            if not features['pytorch']:
                window.log("      ❌ Missing PyTorch")
    else:
        window.log("⚠️  AI Vision Models:")
        window.log("   ❌ Vision models not available")
        if not features['pil']:
            window.log("   ❌ PIL/Pillow missing (CRITICAL) - pip install pillow")
        if not features['pytorch']:
            window.log("   ❌ PyTorch missing - pip install torch")
        if not (features['transformers'] or features['open_clip']):
            window.log("   ❌ Transformers/OpenCLIP missing - pip install transformers open-clip-torch")
        window.log("   💡 AI-powered organization will be limited")
    
    # ONNX features
    window.log("")
    if features['onnxruntime'] or features['onnx']:
        window.log("✅ ONNX Features:")
        if features['onnxruntime']:
            window.log("   ✅ ONNX Runtime available (for model inference)")
        else:
            window.log("   ⚠️  ONNX Runtime not available")
        
        if features['onnx']:
            window.log("   ✅ ONNX model format available")
        else:
            window.log("   ⚠️  ONNX not available")
    else:
        window.log("⚠️  ONNX Features:")
        window.log("   ❌ ONNX not available (optional)")
        window.log("   💡 For full features: pip install onnx onnxruntime")
        window.log("   ℹ️  App will work without ONNX")
    
    # Optional features
    window.log("")
    window.log("📦 Optional Features:")
    if features['timm']:
        window.log("   ✅ timm (PyTorch Image Models)")
    else:
        window.log("   ⚠️  timm not available")
    
    # Upscaling features
    window.log("")
    window.log("🔍 Upscaling Features:")
    window.log("   ✅ Bicubic upscaling (always available)")
    if features['native_lanczos']:
        window.log("   ✅ Lanczos upscaling (native Rust acceleration)")
    else:
        window.log("   ⚠️  Lanczos native acceleration not available")
    if features['upscaler']:
        window.log("   ✅ Real-ESRGAN upscaler available")
    else:
        window.log("   ⚠️  Real-ESRGAN upscaler not available (optional)")
        window.log("   💡 Install: pip install basicsr realesrgan")
    
    window.log("=" * 60)
    logger.info("Startup diagnostics completed")


def _auto_download_models(main_window: 'TextureSorterMainWindow') -> None:
    """Download any missing required AI models in a background QThread.

    Shows a status-bar message while downloading; does NOT block the UI.
    On first run this ensures the upscaler models are ready without the user
    having to open Settings → AI Models and click "Download" manually.
    """
    try:
        from upscaler.model_manager import AIModelManager, ModelStatus
    except (ImportError, OSError, RuntimeError):
        try:
            from src.upscaler.model_manager import AIModelManager, ModelStatus  # type: ignore[no-redef]
        except (ImportError, OSError, RuntimeError):
            return

    try:
        mgr = AIModelManager()
        required = mgr.get_required_models()
        missing = [m for m in required
                   if mgr.get_model_status(m) != ModelStatus.INSTALLED]
        if not missing:
            logger.debug("All required models already installed — no auto-download needed")
            return

        logger.info(f"Auto-downloading {len(missing)} missing model(s): {missing}")
        main_window.statusBar().showMessage(
            f"⬇️  Downloading {len(missing)} AI model(s) in background…", 0
        )

        # Use a QThread so UI never freezes
        class _DownloadThread(QThread):
            done = pyqtSignal(dict)   # {model_name: success}

            def __init__(self, manager, models):
                super().__init__()
                self._mgr = manager
                self._models = models

            def run(self):
                results = {}
                for name in self._models:
                    try:
                        results[name] = self._mgr.download_model(name)
                    except Exception as exc:
                        logger.error(f"Auto-download {name} failed: {exc}")
                        results[name] = False
                self.done.emit(results)

        thread = _DownloadThread(mgr, missing)

        def _on_done(results: dict) -> None:
            ok = [n for n, v in results.items() if v]
            fail = [n for n, v in results.items() if not v]
            if ok:
                logger.info(f"Auto-downloaded: {ok}")
                main_window.statusBar().showMessage(
                    f"✅ AI models ready: {', '.join(ok)}", 6000
                )
            if fail:
                logger.warning(f"Auto-download failed: {fail}")
                main_window.statusBar().showMessage(
                    f"⚠️ Could not download: {', '.join(fail)} — "
                    "check Settings → AI Models to retry", 10000
                )
            # Keep thread alive until done
            thread.deleteLater()

        thread.done.connect(_on_done)
        # Keep a reference so GC doesn't collect the thread
        main_window._model_download_thread = thread
        thread.start()

    except Exception as exc:
        logger.debug(f"_auto_download_models: {exc}")


def main():
    """Main entry point."""
    # ── Windows EXE: configure PyOpenGL before any import touches it ──────────
    # In a frozen EXE ctypes.util.find_library() does not search the app folder,
    # so PyOpenGL would fail to locate opengl32.dll on some Windows configurations.
    # Setting PYOPENGL_PLATFORM_HANDLER=win32 forces the Windows backend and
    # os.add_dll_directory() makes the bundled DLLs visible to the OS loader.
    import sys as _sys_main
    if _sys_main.platform.startswith('win'):
        import os as _os_main
        if 'PYOPENGL_PLATFORM_HANDLER' not in _os_main.environ:
            _os_main.environ['PYOPENGL_PLATFORM_HANDLER'] = 'win32'
        if getattr(_sys_main, 'frozen', False):
            _app_dir = _os_main.path.dirname(_sys_main.executable)
            for _d in (_app_dir, getattr(_sys_main, '_MEIPASS', _app_dir)):
                try:
                    _os_main.add_dll_directory(_d)
                except (AttributeError, OSError):
                    pass
        # Always add System32 — opengl32.dll and glu32.dll live there on all
        # modern Windows installations regardless of whether the app is frozen.
        _sys32 = _os_main.path.join(
            _os_main.environ.get('SystemRoot', r'C:\Windows'), 'System32'
        )
        try:
            if _os_main.path.isdir(_sys32):
                _os_main.add_dll_directory(_sys32)
        except (AttributeError, OSError):
            pass
        # Disable C accelerate — pure-Python mode always works; the accelerate
        # wheel often fails to build on Windows and causes confusing ImportErrors.
        try:
            import OpenGL as _ogl_main
            _ogl_main.USE_ACCELERATE = False
        except Exception:
            pass

    # ── Set OpenGL surface format BEFORE creating QApplication ────────────────
    # This must be done before any QOpenGLWidget is instantiated.
    # We request OpenGL 2.1 CompatibilityProfile so that all three 3D widgets
    # (PandaOpenGLWidget, PandaBedroomGL, PandaWorldGL) can use legacy
    # fixed-function GL (glBegin/glEnd, glShadeModel, glLightfv, etc.).
    # Without this, strict drivers may give a CoreProfile context that rejects
    # every legacy call and immediately fails initializeGL, which would cause
    # the 2D fallback panda to appear instead of the intended 3D experience.
    try:
        from PyQt6.QtGui import QSurfaceFormat as _SF
        _fmt = _SF()
        _fmt.setVersion(2, 1)
        _fmt.setProfile(_SF.OpenGLContextProfile.CompatibilityProfile)
        # RenderableType.OpenGL = native desktop GL (opengl32.dll).
        # WITHOUT this, Qt may choose OpenGLES/ANGLE which does NOT support
        # CompatibilityProfile — glShadeModel/glBegin/glLightfv all raise GLError.
        _fmt.setRenderableType(_SF.RenderableType.OpenGL)
        _fmt.setSamples(4)
        _fmt.setDepthBufferSize(24)
        _fmt.setStencilBufferSize(8)
        _SF.setDefaultFormat(_fmt)
    except Exception:
        pass  # Qt not available in test environment; each widget sets its own format

    # In a frozen EXE PIL plugins are not auto-registered — call init() explicitly
    # so that all image formats (PNG, JPEG, WebP, TGA, DDS, …) are available.
    try:
        from PIL import Image as _PILImage
        _PILImage.init()
    except Exception:
        pass

    # Optimize memory before creating any Qt objects
    _startup_validation = None
    try:
        import startup_validation as _startup_validation
        _startup_validation.optimize_memory()
    except Exception:
        pass

    # Force Qt to use the native desktop OpenGL renderer BEFORE QApplication is created.
    # This is a Qt C++-level flag (not just an env var) — the most reliable way to
    # prevent Qt from choosing ANGLE (Direct3D/OpenGL ES) on Windows.
    # ANGLE only supports OpenGL ES, which lacks CompatibilityProfile functions
    # (glShadeModel, glLightfv, glBegin/glEnd) — they all raise GLError(1282) on ANGLE,
    # causing initializeGL() to fail and the 2D panda fallback to show.
    # Belt-and-suspenders: QT_OPENGL=desktop (env var, set above) + AA_UseDesktopOpenGL
    # (C++ attribute) together guarantee desktop GL on every Qt6 Windows installation.
    try:
        from PyQt6.QtCore import Qt as _Qt6Core
        QApplication.setAttribute(_Qt6Core.ApplicationAttribute.AA_UseDesktopOpenGL)
        QApplication.setAttribute(_Qt6Core.ApplicationAttribute.AA_ShareOpenGLContexts)
    except Exception:
        pass  # Qt not available in test environment; env var alone is enough

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("JosephsDeadish")
    app.setOrganizationDomain("patreon.com/JosephsDeadish")

    # ── Single-instance guard ─────────────────────────────────────────────────
    # Prevent a second copy of the application from opening.  We use a lock
    # file in the user-writable app_data directory.  QLockFile provides both
    # creation and stale-lock detection (process no longer running).
    _lock_file = None
    try:
        from PyQt6.QtCore import QLockFile
        from config import get_data_dir
        _lock_path = str(get_data_dir() / ".app.lock")
        _lock_file = QLockFile(_lock_path)
        # 5 000 ms: if the lock is older than 5 s AND the owner PID is gone,
        # Qt treats it as a stale lock from a crashed instance and removes it.
        _lock_file.setStaleLockTime(5000)
        if not _lock_file.tryLock(100):
            QMessageBox.warning(
                None,
                f"{APP_NAME} — Already Running",
                f"🐼 {APP_NAME} is already open!\n\n"
                "Only one instance can run at a time.\n"
                "Please check your taskbar or system tray.",
            )
            sys.exit(0)
    except Exception as _lock_err:
        logger.debug(f"Single-instance lock skipped: {_lock_err}")
        _lock_file = None

    # Validate frozen-EXE extraction integrity (no-op in dev mode)
    try:
        if _startup_validation and not _startup_validation.run_startup_validation():
            sys.exit(1)
    except Exception:
        pass
    
    # Set application icon for taskbar
    icon_path = Path(__file__).parent / 'assets' / 'icon.ico'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        logger.info(f"Application icon set from: {icon_path}")
    else:
        # Try PNG icon as fallback
        icon_path = Path(__file__).parent / 'assets' / 'icon.png'
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            logger.info(f"Application icon set from PNG: {icon_path}")
        else:
            logger.warning("Application icon file not found")
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # ── Startup splash screen ─────────────────────────────────────────────────
    # Show a panda-themed splash immediately so the user sees feedback while
    # the heavy module imports (torch, onnxruntime, UI panels, …) happen.
    # We draw directly onto a QPixmap using QPainter so no external image file
    # is required — the splash always works even in a fresh EXE extraction.
    _splash = None
    try:
        from PyQt6.QtWidgets import QSplashScreen
        from PyQt6.QtGui import QPixmap, QPainter, QLinearGradient, QRadialGradient, QBrush, QPen, QColor
        from PyQt6.QtCore import Qt as _SplashQt

        _W, _H = 480, 300
        _pix = QPixmap(_W, _H)
        _pix.fill(_SplashQt.GlobalColor.transparent)

        _p = QPainter(_pix)
        _p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background gradient (dark bamboo-green → near-black)
        _bg = QLinearGradient(0, 0, 0, _H)
        _bg.setColorAt(0.0, QColor("#1a2e1a"))
        _bg.setColorAt(1.0, QColor("#0a160a"))
        _p.fillRect(0, 0, _W, _H, QBrush(_bg))

        # Soft vignette
        _vig = QRadialGradient(_W / 2, _H / 2, _W * 0.7)
        _vig.setColorAt(0.0, QColor(0, 0, 0, 0))
        _vig.setColorAt(1.0, QColor(0, 0, 0, 160))
        _p.fillRect(0, 0, _W, _H, QBrush(_vig))

        # Panda face — drawn with basic circles (no image asset needed)
        _cx, _cy = _W // 2, _H // 2 - 20
        # Main head
        _p.setBrush(QBrush(QColor("#f8f8f8")))
        _p.setPen(QPen(QColor("#cccccc"), 1))
        _p.drawEllipse(_cx - 60, _cy - 55, 120, 110)
        # Ears (black patches)
        _p.setBrush(QBrush(QColor("#222222")))
        _p.setPen(QPen(_SplashQt.PenStyle.NoPen))
        _p.drawEllipse(_cx - 70, _cy - 80, 40, 40)
        _p.drawEllipse(_cx + 30, _cy - 80, 40, 40)
        # Eye patches
        _p.drawEllipse(_cx - 42, _cy - 30, 32, 28)
        _p.drawEllipse(_cx + 10, _cy - 30, 32, 28)
        # Eyes (white)
        _p.setBrush(QBrush(QColor("#ffffff")))
        _p.drawEllipse(_cx - 34, _cy - 24, 16, 16)
        _p.drawEllipse(_cx + 18, _cy - 24, 16, 16)
        # Pupils
        _p.setBrush(QBrush(QColor("#111111")))
        _p.drawEllipse(_cx - 30, _cy - 20, 8, 10)
        _p.drawEllipse(_cx + 22, _cy - 20, 8, 10)
        # Nose
        _p.setBrush(QBrush(QColor("#444444")))
        _p.drawEllipse(_cx - 8, _cy + 4, 16, 10)
        # Mouth
        _p.setPen(QPen(QColor("#555555"), 2))
        _p.setBrush(QBrush(_SplashQt.BrushStyle.NoBrush))
        from PyQt6.QtCore import QRect as _QRect
        _p.drawArc(_QRect(_cx - 14, _cy + 12, 28, 16), 200 * 16, 140 * 16)

        # Title text
        _tf = QFont("Segoe UI", 16, QFont.Weight.Bold)
        _p.setFont(_tf)
        _p.setPen(QPen(QColor("#ffffff")))
        _p.drawText(0, _H - 90, _W, 28, int(_SplashQt.AlignmentFlag.AlignHCenter), APP_NAME)

        # Subtitle
        _sf = QFont("Segoe UI", 10)
        _p.setFont(_sf)
        _p.setPen(QPen(QColor("#aaddaa")))
        _p.drawText(0, _H - 62, _W, 22, int(_SplashQt.AlignmentFlag.AlignHCenter), f"v{APP_VERSION}  ·  Starting up, please wait…")

        # Author
        _af = QFont("Segoe UI", 8)
        _p.setFont(_af)
        _p.setPen(QPen(QColor("#557755")))
        _p.drawText(0, _H - 22, _W, 18, int(_SplashQt.AlignmentFlag.AlignHCenter), "by Dead On The Inside / JosephsDeadish")
        _p.end()

        _splash = QSplashScreen(_pix, _SplashQt.WindowType.WindowStaysOnTopHint)
        _splash.show()
        app.processEvents()
    except Exception as _spl_err:
        logger.debug(f"Splash screen skipped: {_spl_err}")
        _splash = None

    # ── Point rembg's model search path at our pre-downloaded models dir ────────
    # rembg looks for ONNX files in U2NET_HOME (or ~/.u2net/ by default).
    # We pre-download them to app_data/models/ in the CI bundle AND in
    # _auto_download_models(), so setting U2NET_HOME ensures rembg finds them
    # without prompting the user to wait for a separate download.
    try:
        from config import get_data_dir as _get_data_dir
        _models_dir = str(_get_data_dir() / 'models')
        import os as _os_u2
        # Only set if not already overridden by user/environment
        _os_u2.environ.setdefault('U2NET_HOME', _models_dir)
        logger.debug(f"U2NET_HOME → {_models_dir}")
    except Exception as _u2err:
        logger.debug(f"U2NET_HOME setup skipped: {_u2err}")

    # Create and show main window
    window = TextureSorterMainWindow()
    window.show()

    # Close splash screen now that the main window is visible
    if _splash is not None:
        try:
            _splash.finish(window)
        except Exception:
            pass

    # Show first-run tutorial
    # Deferred 800 ms so the main window is fully painted and the event loop is
    # running before we create the overlay / dialog — avoids race conditions where
    # master.isVisible() returns False or geometry() is still (0,0) during startup.
    # The TutorialManager reference is stored on the window so that the crash
    # recovery dialog can check whether the tutorial is currently active before
    # showing — prevents the backup dialog from appearing behind the tutorial overlay.
    try:
        from features.tutorial_system import TutorialManager
        _tm = TutorialManager(master_window=window, config=config)
        window._tutorial_manager = _tm   # store so _offer_crash_recovery can check
        if _tm.should_show_tutorial():
            QTimer.singleShot(800, lambda: _tm.start_tutorial())
    except Exception as _te:
        logger.debug(f"Tutorial check skipped: {_te}")

    # Auto-download required AI models on first run (non-blocking — runs in background)
    # Uses a QThread so the UI stays responsive while models download.
    # 1500 ms delay: gives the main window time to finish painting and the event loop
    # to settle before we start background I/O, preventing any startup jank.
    QTimer.singleShot(1500, lambda: _auto_download_models(window))

    # Log startup
    logger.info(f"{APP_NAME} v{APP_VERSION} started with Qt6")
    window.log(f"🐼 {APP_NAME} v{APP_VERSION}")
    window.log("✅ Qt6 UI loaded successfully")
    window.log("✅ No tkinter, no canvas - pure Qt!")
    
    # Log startup diagnostics
    log_startup_diagnostics(window)
    
    # Start event loop
    _exit_code = app.exec()
    # Release the single-instance lock so the next launch can start normally
    if _lock_file is not None:
        try:
            _lock_file.unlock()
        except Exception:
            pass
    sys.exit(_exit_code)


if __name__ == "__main__":
    main()
