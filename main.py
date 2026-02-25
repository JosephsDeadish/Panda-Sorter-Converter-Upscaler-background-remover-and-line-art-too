#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game Texture Sorter - Qt Main Application
A Qt6-based application with OpenGL rendering.
Author: Dead On The Inside / JosephsDeadish
"""

import sys
import os
import importlib
import logging
import functools
import types as _types
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
            from config import APP_NAME, APP_VERSION
        except Exception:
            APP_NAME, APP_VERSION = "Game Texture Sorter", "1.0.0"
        print(f"{APP_NAME} v{APP_VERSION}")
        print("Author: Dead On The Inside / JosephsDeadish")
        print("https://github.com/JosephsDeadish/Panda-Sorter-Converter-Upscaler-background-remover-and-line-art-too")
        sys.exit(0)

    if arg in ('--help', '-h'):
        try:
            from config import APP_NAME
        except Exception:
            APP_NAME = "Game Texture Sorter"
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
            APP_NAME, APP_VERSION = "Game Texture Sorter", "1.0.0"

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
        QScrollArea, QDockWidget, QToolBar, QInputDialog
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QByteArray
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
from config import config, APP_NAME, APP_VERSION

# Import core modules
from classifier import TextureClassifier, ALL_CATEGORIES
from lod_detector import LODDetector
from file_handler import FileHandler
from database import TextureDatabase
from organizer import OrganizationEngine, ORGANIZATION_STYLES

# Import UI components
PANDA_WIDGET_AVAILABLE = False
try:
    from ui.panda_widget_gl import PandaOpenGLWidget
    PANDA_WIDGET_AVAILABLE = True
    logger.info("✅ Panda OpenGL widget module loaded")
except (ImportError, OSError, RuntimeError) as e:
    logger.warning(f"Panda widget not available: {e}")
    PandaOpenGLWidget = None

# Runtime sanity-check: verify that OpenGL constants are actually accessible.
# In a frozen EXE the Python wrapper may import fine but the underlying DLL
# lookup can still fail.  We probe one constant (GL_DEPTH_TEST = 0x0B71) to
# surface any such failure early, so we fall back to 2D gracefully instead of
# crashing inside initializeGL later.
_OPENGL_RUNTIME_OK: bool = False
if PANDA_WIDGET_AVAILABLE:
    try:
        from OpenGL.GL import GL_DEPTH_TEST as _GL_DEPTH_TEST_PROBE  # noqa: F401
        _OPENGL_RUNTIME_OK = True
        logger.info("✅ PyOpenGL runtime check passed")
    except Exception as _gle:
        logger.warning(f"PyOpenGL runtime check failed ({_gle}); using 2D panda fallback")
        PANDA_WIDGET_AVAILABLE = False
        PandaOpenGLWidget = None

# 2-D panda fallback (QPainter — no OpenGL required)
try:
    from ui.panda_widget_2d import PandaWidget2D
    logger.info("✅ Panda 2D fallback widget loaded")
except (ImportError, OSError, RuntimeError) as e:
    PandaWidget2D = None
    logger.warning(f"Panda 2D widget not available: {e}")

# Import each UI panel independently so one bad import does not disable all tools.
# Each name is set to None on failure; callers guard with `if PanelClass is not None`.
def _try_import(module_path: str, class_name: str):
    """Return the named class from module_path, or None on import/attribute failure."""
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)
    except Exception as _e:
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
    Main application window for Game Texture Sorter.
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
        self._backpack_merged_panel = None  # Merged Inventory+Widgets QTabWidget (built once)
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

        # Paths
        self.input_path = None
        self.output_path = None
        
        # Tooltip manager (will be initialized later)
        self.tooltip_manager = None
        self.log_text = None           # QTextEdit for activity log (created in create_tools_tab)

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

        # Apply performance settings from config
        self.apply_performance_settings()
        
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
        
        # ── Panda sidebar widget ─────────────────────────────────────────────
        # Try OpenGL 3-D widget first; fall back to 2-D QPainter widget.
        # IMPORTANT: create panda_widget HERE — before create_panda_features_tab()
        # so that panda_char is available when the Customisation tab is built.
        # Only ONE panda widget is ever shown: the GL widget if hardware OpenGL is
        # available, or the 2D QPainter widget as a transparent fallback.
        # The two are NEVER shown simultaneously.
        _panda_sidebar_widget = None   # will be added to splitter after content_widget

        if PANDA_WIDGET_AVAILABLE:
            try:
                self.panda_widget = PandaOpenGLWidget()
                self.panda_widget.setMinimumWidth(280)
                self.panda_widget.setMaximumWidth(420)
                self.panda_widget.clicked.connect(self.on_panda_clicked)
                self.panda_widget.mood_changed.connect(self.on_panda_mood_changed)
                self.panda_widget.animation_changed.connect(self.on_panda_animation_changed)
                # Wire gl_failed so we can swap in the 2D widget if initializeGL fails
                if hasattr(self.panda_widget, 'gl_failed'):
                    self.panda_widget.gl_failed.connect(self._on_panda_gl_failed)
                _panda_sidebar_widget = self.panda_widget
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
                self.panda_widget = PandaWidget2D()
                self.panda_widget.setMinimumWidth(280)
                self.panda_widget.setMaximumWidth(420)
                self.panda_widget.clicked.connect(self.on_panda_clicked)
                self.panda_widget.mood_changed.connect(self.on_panda_mood_changed)
                self.panda_widget.animation_changed.connect(self.on_panda_animation_changed)
                _panda_sidebar_widget = self.panda_widget
                logger.info("✅ Panda 2D QPainter widget created (OpenGL unavailable)")
            except Exception as e2:
                logger.error(f"Panda 2D fallback also failed: {e2}")
                self.panda_widget = None

        # Keep a reference to the splitter so _on_panda_gl_failed can swap in 2D
        self._panda_splitter = splitter
        self._panda_splitter_idx = 1  # right pane (0 = content, 1 = panda)

        # Create draggable tabs
        self.tabs = DraggableTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tab_detached.connect(self.on_tab_detached)
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

        # ── Add panda sidebar to splitter ─────────────────────────────────────
        if _panda_sidebar_widget is not None:
            splitter.addWidget(_panda_sidebar_widget)
            splitter.setStretchFactor(0, 3)  # content gets 75 %
            splitter.setStretchFactor(1, 1)  # panda sidebar gets 25 %
        else:
            # No panda widget at all — show a gentle placeholder
            ph = QWidget()
            ph_layout = QVBoxLayout(ph)
            ph_label = QLabel(
                "🐼\n\nPanda companion\nunavailable\n\n"
                "Install PyOpenGL for\n3-D panda rendering"
            )
            ph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ph_label.setStyleSheet("color: #aaa; font-size: 10pt;")
            ph_label.setWordWrap(True)
            ph_layout.addWidget(ph_label)
            splitter.addWidget(ph)
            splitter.setStretchFactor(0, 3)
            splitter.setStretchFactor(1, 1)
            logger.warning("No panda widget available — placeholder shown")
    
    def create_main_tab(self):
        """Create the main tab with welcome/dashboard and quick-launch buttons."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # Welcome message
        welcome_label = QLabel("🎮 PS2 Texture Toolkit")
        welcome_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)

        layout.addSpacing(10)

        subtitle = QLabel("A comprehensive toolkit for managing, organising, and enhancing game textures.")
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
            ("📁 Organizer",       "organizer"),
            ("🎭 Background Remover","bg_remover"),
            ("✨ Alpha Fixer",      "alpha_fixer"),
            ("🎨 Color Correction", "color"),
            ("⚙️ Batch Normalizer", "normalizer"),
            ("✓ Quality Checker",  "quality"),
            ("🔍 Image Upscaler",  "upscaler"),
            ("✏️ Line Art",         "lineart"),
            ("📝 Batch Rename",    "rename"),
            ("🔧 Image Repair",    "repair"),
            ("📁 Organizer",       "organizer"),
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

        layout.addSpacing(16)

        # ── Activity Log at bottom of home page ─────────────────────────────
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
        clear_log_btn.setFixedWidth(70)
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
                alpha_panel.finished.connect(lambda ok, msg, _tid='alpha_fixer': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Alpha Fixer: {msg}", 4000),
                    self._on_tool_finished(ok, _tid),
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
                color_panel.finished.connect(lambda ok, msg, _tid='color': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Color Correction: {msg}", 4000),
                    self._on_tool_finished(ok, _tid),
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
                norm_panel.finished.connect(lambda ok, msg, _tid='normalizer': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Batch Normalizer: {msg}", 4000),
                    self._on_tool_finished(ok, _tid),
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
                upscaler_panel.finished.connect(lambda ok, msg, _tid='upscaler': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Upscaler: {msg}", 4000),
                    self._on_tool_finished(ok, _tid),
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
                line_panel.finished.connect(lambda ok, msg, _tid='lineart': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Line Art: {msg}", 4000),
                    self._on_tool_finished(ok, _tid),
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
                    self._on_tool_finished(bool(ok), _tid),
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
                repair_panel.finished.connect(lambda ok, msg, _tid='repair': (
                    self.statusBar().showMessage(f"{'✅' if ok else '❌'} Image Repair: {msg}", 4000),
                    self._on_tool_finished(ok, _tid),
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
                conv_panel.finished.connect(lambda ok, msg, _tid='converter': (
                    self.statusBar().showMessage(f"{'✅' if ok else '⚠️'} Converter: {msg}", 4000),
                    self._on_tool_finished(ok, _tid),
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
                        int(_stats.get('files_moved', _stats.get('files_processed', 0)))
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
            btn.setFixedHeight(34)
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
        
        # Create dock widget
        dock = QDockWidget(title, self)
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
            'rename':     "📝 Batch Rename",
            'repair':     "🔧 Image Repair",
            'organizer':  "📁 Organizer",
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
                bedroom_gl.gl_failed.connect(_on_bedroom_gl_failed)
            stack.addWidget(bedroom_gl)   # index 0

            # Page 1: placeholder — real sub-panel inserted dynamically
            _ph = QLabel("")
            stack.addWidget(_ph)          # index 1 (replaced on demand)

            home_vbox.addWidget(back_bar)
            home_vbox.addWidget(stack, 1)

            # Save refs
            self._bedroom_widget = bedroom_gl
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

            panda_tabs.addTab(home_container, "🏠 Panda Home")
            self._home_tab_index = panda_tabs.indexOf(home_container)
            logger.info("✅ 3D Panda Home panel added to panda tab")

        except Exception as e:
            logger.error(f"Could not load Panda Home panel: {e}", exc_info=True)
            label = QLabel("⚠️ 3D Panda Home not available\n\nRequires PyQt6 + OpenGL")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "🏠 Panda Home")
            self._home_tab_index = panda_tabs.indexOf(label)

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
            label = QLabel("⚔️ Adventure Mode\n\nDungeon exploration coming soon!\nInstall PyQt6 to enable.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            # Wire easter_egg_found → fun status bar message
            if hasattr(self.quest_system, 'easter_egg_found') and self.quest_system.easter_egg_found:
                self.quest_system.easter_egg_found.connect(
                    lambda eid: self.statusBar().showMessage(f"🥚 Easter egg found: {eid}!", 5000)
                )
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
                                        self.statusBar().showMessage(f"🌳 Skill unlocked!", 3000)
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
        
        self.tabs.addTab(tab, "Settings")
    
    def setup_menubar(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # ── File menu ────────────────────────────────────────────────────────
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Input Folder…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.browse_input)
        file_menu.addAction(open_action)

        open_out_action = QAction("Open &Output Folder…", self)
        open_out_action.setShortcut("Ctrl+Shift+O")
        open_out_action.triggered.connect(self.browse_output)
        file_menu.addAction(open_out_action)

        file_menu.addSeparator()

        # Profiles sub-menu (uses ProfileManager)
        profile_menu = file_menu.addMenu("&Profiles")
        save_profile_action = QAction("&Save Current Profile…", self)
        save_profile_action.triggered.connect(self._save_profile)
        profile_menu.addAction(save_profile_action)
        load_profile_action = QAction("&Load Profile…", self)
        load_profile_action.triggered.connect(self._load_profile)
        profile_menu.addAction(load_profile_action)

        # Backup sub-menu (uses BackupManager)
        backup_menu = file_menu.addMenu("&Backup")
        create_restore_action = QAction("Create &Restore Point…", self)
        create_restore_action.triggered.connect(self._create_restore_point)
        backup_menu.addAction(create_restore_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ── View menu ────────────────────────────────────────────────────────
        view_menu = menubar.addMenu("&View")
        self.view_menu = view_menu  # Store reference for dynamic updates

        popout_action = QAction("Pop Out Current Tab", self)
        popout_action.setShortcut("Ctrl+Shift+P")
        popout_action.triggered.connect(self.popout_current_tab)
        view_menu.addAction(popout_action)

        view_menu.addSeparator()

        # Submenu for restoring docked tabs
        self.restore_menu = view_menu.addMenu("Restore Docked Tab")
        self.restore_menu.setEnabled(False)  # Disabled until tabs are popped out

        view_menu.addSeparator()

        reset_layout_action = QAction("Reset Window Layout", self)
        reset_layout_action.triggered.connect(self.reset_window_layout)
        view_menu.addAction(reset_layout_action)

        # ── Tools menu ────────────────────────────────────────────────────────
        tools_menu = menubar.addMenu("&Actions")

        find_dupes_action = QAction("🔍 Find Duplicate Textures…", self)
        find_dupes_action.triggered.connect(self._find_duplicate_textures)
        tools_menu.addAction(find_dupes_action)

        analyze_action = QAction("🔬 Analyze Selected Texture…", self)
        analyze_action.triggered.connect(self._analyze_selected_texture)
        tools_menu.addAction(analyze_action)

        # ── Help menu ────────────────────────────────────────────────────────
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
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
    
    def apply_theme(self):
        """Apply theme stylesheet based on config."""
        theme = config.get('ui', 'theme', default='dark')
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
            stylesheet = f"""
            QMainWindow {{
                background-color: #2e3440;
            }}
            QWidget {{
                background-color: #2e3440;
                color: #d8dee9;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QPushButton {{
                background-color: {accent};
                color: #eceff4;
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
                background-color: #434c5e;
                color: #616e88;
            }}
            QLabel {{
                color: #d8dee9;
                background-color: transparent;
            }}
            QTabWidget::pane {{
                border: 1px solid #3b4252;
                background-color: #3b4252;
            }}
            QTabBar::tab {{
                background-color: #434c5e;
                color: #d8dee9;
                padding: 8px 20px;
                border: 1px solid #3b4252;
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {accent};
                color: #eceff4;
            }}
            QTabBar::tab:hover {{
                background-color: #4c566a;
            }}
            QMenuBar {{
                background-color: #3b4252;
                color: #d8dee9;
                border-bottom: 1px solid #434c5e;
            }}
            QMenuBar::item:selected {{
                background-color: {accent};
                color: #eceff4;
            }}
            QMenu {{
                background-color: #3b4252;
                color: #d8dee9;
                border: 1px solid #434c5e;
            }}
            QMenu::item:selected {{
                background-color: {accent};
                color: #eceff4;
            }}
            QProgressBar {{
                border: 1px solid #434c5e;
                border-radius: 3px;
                text-align: center;
                background-color: #3b4252;
                color: #d8dee9;
            }}
            QProgressBar::chunk {{
                background-color: {accent};
            }}
            QFrame {{
                background-color: #3b4252;
                border: 1px solid #434c5e;
                border-radius: 4px;
            }}
            QTextEdit {{
                background-color: #3b4252;
                color: #d8dee9;
                border: 1px solid #434c5e;
            }}
            QScrollBar:vertical {{
                background-color: #3b4252;
                width: 12px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #4c566a;
                border-radius: 6px;
            }}
            QDockWidget {{
                color: #d8dee9;
                titlebar-close-icon: none;
            }}
            QDockWidget::title {{
                background-color: #434c5e;
                padding: 4px;
            }}
            """
        elif theme == 'dracula':
            stylesheet = f"""
            QMainWindow {{
                background-color: #282a36;
            }}
            QWidget {{
                background-color: #282a36;
                color: #f8f8f2;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QPushButton {{
                background-color: {accent};
                color: #f8f8f2;
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
                background-color: #44475a;
                color: #6272a4;
            }}
            QLabel {{
                color: #f8f8f2;
                background-color: transparent;
            }}
            QTabWidget::pane {{
                border: 1px solid #44475a;
                background-color: #44475a;
            }}
            QTabBar::tab {{
                background-color: #383a4a;
                color: #f8f8f2;
                padding: 8px 20px;
                border: 1px solid #44475a;
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {accent};
                color: #f8f8f2;
            }}
            QTabBar::tab:hover {{
                background-color: #44475a;
            }}
            QMenuBar {{
                background-color: #383a4a;
                color: #f8f8f2;
                border-bottom: 1px solid #44475a;
            }}
            QMenuBar::item:selected {{
                background-color: {accent};
            }}
            QMenu {{
                background-color: #383a4a;
                color: #f8f8f2;
                border: 1px solid #44475a;
            }}
            QMenu::item:selected {{
                background-color: {accent};
            }}
            QProgressBar {{
                border: 1px solid #44475a;
                border-radius: 3px;
                text-align: center;
                background-color: #383a4a;
                color: #f8f8f2;
            }}
            QProgressBar::chunk {{
                background-color: {accent};
            }}
            QFrame {{
                background-color: #383a4a;
                border: 1px solid #44475a;
                border-radius: 4px;
            }}
            QTextEdit {{
                background-color: #383a4a;
                color: #f8f8f2;
                border: 1px solid #44475a;
            }}
            QScrollBar:vertical {{
                background-color: #383a4a;
                width: 12px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #44475a;
                border-radius: 6px;
            }}
            QDockWidget {{
                color: #f8f8f2;
                titlebar-close-icon: none;
            }}
            QDockWidget::title {{
                background-color: #44475a;
                padding: 4px;
            }}
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
            QScrollBar:vertical {{ background-color: #073642; width: 12px; }}
            QScrollBar::handle:vertical {{ background-color: #586e75; border-radius: 6px; }}
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
            QScrollBar:vertical {{ background-color: #1e381e; width: 12px; }}
            QScrollBar::handle:vertical {{ background-color: #4a7a4a; border-radius: 6px; }}
            """
        elif theme in ('ocean', 'ocean_blue'):
            stylesheet = f"""
            QMainWindow {{ background-color: #0a1628; }}
            QWidget {{ background-color: #0a1628; color: #b3d9f7; font-family: 'Segoe UI', Arial, sans-serif; }}
            QPushButton {{ background-color: {accent}; color: #ffffff; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {hover_color.name()}; }}
            QPushButton:pressed {{ background-color: {pressed_color.name()}; }}
            QPushButton:disabled {{ background-color: #0d2240; color: #3a6080; }}
            QLabel {{ color: #b3d9f7; background-color: transparent; }}
            QTabWidget::pane {{ border: 1px solid #1a4060; background-color: #0d1e38; }}
            QTabBar::tab {{ background-color: #0d1e38; color: #80bcd8; padding: 8px 20px; border: 1px solid #1a4060; border-bottom: none; }}
            QTabBar::tab:selected {{ background-color: {accent}; color: #ffffff; }}
            QTabBar::tab:hover {{ background-color: #152840; }}
            QMenuBar {{ background-color: #0d1e38; color: #b3d9f7; border-bottom: 1px solid #1a4060; }}
            QMenuBar::item:selected {{ background-color: {accent}; color: #ffffff; }}
            QMenu {{ background-color: #0d1e38; color: #b3d9f7; border: 1px solid #1a4060; }}
            QMenu::item:selected {{ background-color: {accent}; color: #ffffff; }}
            QProgressBar {{ border: 1px solid #1a4060; border-radius: 3px; text-align: center; background-color: #0d1e38; color: #b3d9f7; }}
            QProgressBar::chunk {{ background-color: {accent}; }}
            QFrame {{ background-color: #0d1e38; border: 1px solid #1a4060; border-radius: 4px; }}
            QTextEdit {{ background-color: #0a1628; color: #b3d9f7; border: 1px solid #1a4060; }}
            QScrollBar:vertical {{ background-color: #0d1e38; width: 12px; }}
            QScrollBar::handle:vertical {{ background-color: #2a6090; border-radius: 6px; }}
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
            QScrollBar:vertical {{ background-color: #321e0f; width: 12px; }}
            QScrollBar::handle:vertical {{ background-color: #8a5030; border-radius: 6px; }}
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
            QScrollBar:vertical {{ background-color: #0d0d1a; width: 12px; }}
            QScrollBar::handle:vertical {{ background-color: #00ffcc; border-radius: 2px; }}
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
            """
        self.setStyleSheet(stylesheet)
        self.apply_cursor()

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
                    'forest': 'bamboo_grove',
                    'ocean': 'ocean_explorer',
                    'sunset': 'golden_hour',
                    'cyberpunk': 'neon_rider',
                }
                ach_id = _theme_ach.get(theme)
                if ach_id:
                    self.achievement_system.unlock_achievement(ach_id)
        except Exception:
            pass

    def apply_cursor(self):
        """Apply the cursor style saved in config to the whole application."""
        try:
            from PyQt6.QtGui import QCursor
            from PyQt6.QtCore import Qt
            cursor_name = str(config.get('ui', 'cursor', default='default')).lower().strip()
            _cursor_map = {
                'default':   Qt.CursorShape.ArrowCursor,
                'arrow':     Qt.CursorShape.ArrowCursor,
                'hand':      Qt.CursorShape.PointingHandCursor,
                'cross':     Qt.CursorShape.CrossCursor,
                'wait':      Qt.CursorShape.WaitCursor,
                'text':      Qt.CursorShape.IBeamCursor,
                'forbidden': Qt.CursorShape.ForbiddenCursor,
                'move':      Qt.CursorShape.SizeAllCursor,
                'zoom_in':   Qt.CursorShape.PointingHandCursor,  # "click to zoom in"
                'zoom_out':  Qt.CursorShape.ArrowCursor,          # no native zoom-out cursor in Qt
            }
            shape = _cursor_map.get(cursor_name, Qt.CursorShape.ArrowCursor)
            app = QApplication.instance()
            if app:
                # Restore any previous override so we don't stack overrides
                while app.overrideCursor():
                    app.restoreOverrideCursor()
                # For non-default cursors set an application-wide override
                if cursor_name not in ('default', 'arrow'):
                    app.setOverrideCursor(QCursor(shape))
            logger.debug(f"Cursor applied: {cursor_name} → {shape.name if hasattr(shape, 'name') else shape}")
        except Exception as e:
            logger.warning(f"Could not apply cursor: {e}")

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

            # Initialize transparent panda overlay (floating panda that reacts to UI events).
            # DISABLED BY DEFAULT: the overlay covers the entire window with WA_TransparentForMouseEvents=False.
            # On systems where the GL context fails silently, the overlay becomes an opaque
            # full-screen rectangle that intercepts all mouse events, making the app appear frozen.
            # Users can enable the overlay via Settings → Panda → "Enable floating overlay".
            _overlay_enabled = False
            try:
                _overlay_enabled = bool(
                    self.config and self.config.get('panda', 'overlay_enabled', default=False)
                )
            except Exception:
                pass

            if _overlay_enabled:
                try:
                    from ui.transparent_panda_overlay import create_transparent_overlay
                    self.panda_overlay = create_transparent_overlay(self, main_window=self)
                    if self.panda_overlay:
                        # Wire panda overlay signals to main window handlers
                        if hasattr(self.panda_overlay, 'panda_clicked_widget') and self.panda_overlay.panda_clicked_widget:
                            self.panda_overlay.panda_clicked_widget.connect(
                                lambda w: logger.debug(f"Panda clicked widget: {w}")
                            )
                        if hasattr(self.panda_overlay, 'panda_moved') and self.panda_overlay.panda_moved:
                            self.panda_overlay.panda_moved.connect(
                                lambda x, y: logger.debug(f"Panda moved to ({x}, {y})")
                            )
                        if hasattr(self.panda_overlay, 'panda_triggered_button') and self.panda_overlay.panda_triggered_button:
                            self.panda_overlay.panda_triggered_button.connect(
                                lambda w: logger.debug(f"Panda triggered button: {w}")
                            )
                        logger.info("Transparent panda overlay created and signals wired")
                    else:
                        logger.info("Panda overlay not available (PyOpenGL not installed)")
                except Exception as e:
                    logger.debug(f"Could not create panda overlay: {e}")
            else:
                logger.debug("Transparent panda overlay disabled (enable via Settings → Panda → floating overlay)")

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

    def _tick_panda_interaction(self) -> None:
        """Advance PandaInteractionBehavior AI by one frame."""
        if self.panda_interaction is None:
            return
        try:
            self.panda_interaction.update(self._INTERACTION_TICK_DT)
        except Exception as _e:
            logger.debug(f"Panda interaction tick failed: {_e}")

        # Update panda mood label in status bar (every tick is fine — it's a cheap QLabel.setText)
        try:
            if self._panda_mood_label and self.panda_widget:
                state = getattr(self.panda_widget, 'animation_state', 'idle')
                # Also surface the active idle sub-state if present (via public getter)
                sub = self.panda_widget.get_idle_sub_state() if hasattr(self.panda_widget, 'get_idle_sub_state') else ''
                display_state = sub if sub else state
                emoji = _PANDA_STATE_EMOJI.get(display_state, _PANDA_STATE_EMOJI.get(state, '🐼'))
                label_text = f"{emoji} {display_state.replace('_', ' ')}"
                if self._panda_mood_label.text() != label_text:
                    self._panda_mood_label.setText(label_text)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Shared helper: react to a tool-panel completion (panda + quest + sound)
    # ------------------------------------------------------------------
    def _on_tool_finished(self, success: bool, tool_id: str = 'tool') -> None:
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
        # XP
        try:
            if self.level_system:
                self.level_system.add_xp(2, reason='tool_used')
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

    def operation_finished(self, success: bool, message: str, files_processed: int = 0):
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
                    summary = self.statistics_tracker.get_summary()
                    elapsed = summary.get('total_time', 0)
                    rate = summary.get('files_per_second', 0)
                    errors = summary.get('error_count', 0)
                    self.log(
                        f"📊 Stats: {files_processed} files in {elapsed:.1f}s"
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
            
            # Handle cursor changes — apply immediately
            elif setting_key == "ui.cursor":
                self.apply_cursor()

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

        except Exception as e:
            logger.error(f"Error handling panda click: {e}", exc_info=True)
    
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
            logger.error("2D panda fallback not available; sidebar will be empty")
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
            w2d = PandaWidget2D()
            w2d.setMinimumWidth(280)
            w2d.setMaximumWidth(420)
            w2d.clicked.connect(self.on_panda_clicked)
            w2d.mood_changed.connect(self.on_panda_mood_changed)
            w2d.animation_changed.connect(self.on_panda_animation_changed)
            if self.panda_character is not None:
                w2d.panda = self.panda_character
        except Exception as e:
            logger.error(f"2D panda fallback creation failed: {e}")
            return

        # Swap into the splitter — replaceWidget keeps the same position/sizes
        try:
            splitter = getattr(self, '_panda_splitter', None)
            idx = getattr(self, '_panda_splitter_idx', 1)
            if splitter is not None and idx < splitter.count():
                splitter.replaceWidget(idx, w2d)
                splitter.setStretchFactor(0, 3)
                splitter.setStretchFactor(idx, 1)
            elif splitter is not None:
                logger.warning(f"splitter.count()={splitter.count()}, idx={idx} — cannot replaceWidget")
                return
        except Exception as e:
            logger.error(f"Could not swap panda widget in splitter: {e}")
            return

        self.panda_widget = w2d

        # Schedule deletion of the old GL widget (safe — already removed from splitter)
        if old_widget is not None:
            try:
                old_widget.deleteLater()
            except Exception:
                pass

        logger.info("✅ Panda 2D fallback active (GL init failed)")

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
            
            # Apply the trail change to the panda widget if it has the method
            if hasattr(self.panda_widget, 'set_trail'):
                self.panda_widget.set_trail(trail_type, trail_data)
            
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
                self.achievement_system.unlock_achievement('minigame_player')
                if score >= 100:
                    self.achievement_system.unlock_achievement('minigame_master')
            if self.quest_system:
                self.quest_system.update_quest_progress('minigame_enjoyer')
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
            elif destination == 'home':
                self._go_back_to_bedroom()
        except Exception as _e:
            logger.debug(f"_on_world_destination_selected({destination}): {_e}")

    def _on_go_to_park(self) -> None:
        """Show the park sub-panel (currently minigames / free play area)."""
        try:
            from ui.minigame_panel_qt import MinigamePanelQt
            from features.minigame_system import MiniGameManager
            mgr = MiniGameManager()
            panel = MinigamePanelQt(minigame_manager=mgr, tooltip_manager=self.tooltip_manager)
            self._home_stack_owned.append(panel)
            self._show_home_sub_panel(panel, '🌲 Panda Park')
            if self.panda_widget:
                QTimer.singleShot(800, lambda: self.panda_widget.set_animation_state('celebrating'))
        except Exception as _e:
            logger.debug(f"_on_go_to_park: {_e}")
            park_label = QLabel(
                "🌲 Panda Park\n\n"
                "🐼 Panda romps around the park!\n\n"
                "Minigames coming soon…"
            )
            park_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            park_label.setStyleSheet("background:#1a2a1a; color:#aaddaa; font-size:14px;")
            self._home_stack_owned.append(park_label)
            self._show_home_sub_panel(park_label, '🌲 Panda Park')

    def _show_home_sub_panel(self, widget: 'QWidget', title: str) -> None:
        """Slide *widget* into page 1 of the Home stack, update tab + back-bar labels."""
        try:
            if not self._home_stack:
                return
            # Remove page-1 widget — only delete it if WE created it AND it isn't the
            # same widget we're about to show (persistent panels like backpack are re-used).
            old = self._home_stack.widget(1)
            if old is not None and old is not widget:
                self._home_stack.removeWidget(old)
                if old in self._home_stack_owned:
                    self._home_stack_owned.remove(old)
                    old.deleteLater()
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
        2. After arrival delay → play open_furniture animation.
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
            'trophy_stand':'🏆 Achievements',
            'backpack':    '🎒 Inventory & Items',
        }
        sub_title = _TITLES.get(furniture_id, furniture_id.replace('_', ' ').title())

        # ── Walk panda to furniture first ─────────────────────────────────────
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

        try:
            if self.panda_widget and hasattr(self.panda_widget, 'walk_to_position'):
                self.panda_widget.walk_to_position(
                    walk_x, 0.0, walk_z,
                    callback=functools.partial(_safe_open, self.panda_widget, furniture_id),
                )
        except Exception as _e:
            logger.debug(f"Bedroom walk: {_e}")

        # ── Trophy stand → show Achievements panel ─────────────────────────────
        if furniture_id == 'trophy_stand':
            def _open_achievements():
                try:
                    ach_widget = getattr(self, '_achievement_panel', None)
                    if ach_widget is None:
                        ach_widget = QLabel("🏆 Achievements\n\n(Loading…)")
                        ach_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self._home_stack_owned.append(ach_widget)
                    self._show_home_sub_panel(ach_widget, '🏆 Achievements')
                except Exception as _e2:
                    logger.debug(f"Trophy panel: {_e2}")
            QTimer.singleShot(500, _open_achievements)
            self.statusBar().showMessage("🏆 Panda is checking their trophies…", 3000)
            return

        # ── Wardrobe → show Closet panel ──────────────────────────────────────
        if furniture_id == 'wardrobe':
            def _open_closet():
                try:
                    cp = getattr(self, '_closet_panel', None)
                    if cp is None:
                        cp = QLabel("👔 Closet\n\n(Not available — check dependencies)")
                        cp.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self._home_stack_owned.append(cp)
                    self._show_home_sub_panel(cp, '👗 Wardrobe / Closet')
                except Exception as _e2:
                    logger.debug(f"Closet panel open: {_e2}")
            QTimer.singleShot(500, _open_closet)
            self.statusBar().showMessage("👔 Panda is browsing the wardrobe…", 3000)
            return

        # ── Backpack → show merged Inventory + Widgets panel ─────────────────
        if furniture_id == 'backpack':
            def _open_backpack():
                try:
                    inv = getattr(self, '_inventory_panel', None)
                    wid = getattr(self, '_widgets_panel', None)
                    if inv is None and wid is None:
                        placeholder = QLabel("🎒 Inventory & Items\n\n(Not available)")
                        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self._home_stack_owned.append(placeholder)
                        self._show_home_sub_panel(placeholder, '🎒 Inventory & Items')
                        return
                    # Build the merged tab widget once; re-use on subsequent opens
                    # to avoid re-parenting the same panels into a new container each click.
                    if self._backpack_merged_panel is None:
                        from PyQt6.QtWidgets import QTabWidget as _TW
                        merged = _TW()
                        merged.setDocumentMode(True)
                        if inv is not None:
                            merged.addTab(inv, "📦 Inventory")
                        if wid is not None:
                            merged.addTab(wid, "🧸 Toys & Items")
                        self._backpack_merged_panel = merged
                        # NOT added to _home_stack_owned — it's a persistent panel
                        # that must survive across multiple opens.  It will be cleaned
                        # up automatically when the main window is closed (Qt parent
                        # ownership transfers to the home_stack on insertWidget).
                    self._show_home_sub_panel(self._backpack_merged_panel, '🎒 Inventory & Items')
                except Exception as _e2:
                    logger.debug(f"Backpack panel open: {_e2}")
            QTimer.singleShot(500, _open_backpack)
            self.statusBar().showMessage("🎒 Panda is checking their backpack…", 3000)
            return

        # ── All other furniture → show filtered Inventory panel ───────────────
        def _open_inventory():
            try:
                inv = self._inventory_panel
                if inv is None:
                    label = QLabel(f"📦 {sub_title}\n\n(Inventory not available)")
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._home_stack_owned.append(label)
                    self._show_home_sub_panel(label, sub_title)
                    return
                if hasattr(inv, 'set_category_filter'):
                    inv.set_category_filter(category)
                elif hasattr(inv, 'refresh_inventory'):
                    inv.refresh_inventory()
                self._show_home_sub_panel(inv, sub_title)
            except Exception as _e2:
                logger.debug(f"Inventory panel open: {_e2}")

        QTimer.singleShot(500, _open_inventory)
        self.statusBar().showMessage(
            f"🐼 Panda is going to the {furniture_id.replace('_', ' ').title()}…", 3000
        )


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
        """Show/hide the panda overlay when environment events require it."""
        try:
            overlay = getattr(self, 'panda_overlay', None)
            if overlay and hasattr(overlay, 'setVisible'):
                overlay.setVisible(not should_hide)
            logger.debug(f"Panda overlay hide={should_hide}")
        except Exception as _e:
            logger.debug(f"panda_should_hide callback error: {_e}")

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
        )

    # ── App-level event filter: button hover → panda peek/poke ──────────────
    def eventFilter(self, obj: 'QObject', event: 'QEvent') -> bool:
        """Intercept mouse-enter events on QPushButton widgets so the panda
        can react (peek / poke) when the cursor hovers over a button."""
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

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("JosephsDeadish")
    app.setOrganizationDomain("github.com/JosephsDeadish")

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
    
    # Create and show main window
    window = TextureSorterMainWindow()
    window.show()
    
    # Show first-run tutorial if this is a new installation.
    # Deferred 800 ms so the main window is fully painted and the event loop is
    # running before we create the overlay / dialog — avoids race conditions where
    # master.isVisible() returns False or geometry() is still (0,0) during startup.
    try:
        from features.tutorial_system import TutorialManager
        _tm = TutorialManager(master_window=window, config=config)
        if _tm.should_show_tutorial():
            QTimer.singleShot(800, lambda: _tm.start_tutorial(window))
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
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
