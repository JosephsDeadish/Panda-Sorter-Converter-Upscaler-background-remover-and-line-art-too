#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game Texture Sorter - Qt Main Application
A Qt6-based application with OpenGL rendering.
Author: Dead On The Inside / JosephsDeadish
"""

import sys
import os
import logging
from pathlib import Path

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

# Qt imports - REQUIRED, no fallbacks
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QProgressBar, QTextEdit, QTabWidget,
        QFileDialog, QMessageBox, QStatusBar, QMenuBar, QMenu,
        QSplitter, QFrame, QComboBox, QGridLayout, QStackedWidget,
        QScrollArea, QDockWidget, QToolBar
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QByteArray
    from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor
except ImportError as e:
    print("=" * 70)
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
except ImportError as e:
    logger.warning(f"Panda widget not available: {e}")
    PandaOpenGLWidget = None

UI_PANELS_AVAILABLE = False
try:
    from ui.background_remover_panel_qt import BackgroundRemoverPanelQt
    from ui.color_correction_panel_qt import ColorCorrectionPanelQt
    from ui.batch_normalizer_panel_qt import BatchNormalizerPanelQt
    from ui.quality_checker_panel_qt import QualityCheckerPanelQt
    from ui.lineart_converter_panel_qt import LineArtConverterPanelQt
    from ui.alpha_fixer_panel_qt import AlphaFixerPanelQt
    from ui.batch_rename_panel_qt import BatchRenamePanelQt
    from ui.image_repair_panel_qt import ImageRepairPanelQt
    from ui.customization_panel_qt import CustomizationPanelQt
    from ui.upscaler_panel_qt import ImageUpscalerPanelQt
    from ui.organizer_panel_qt import OrganizerPanelQt
    from ui.settings_panel_qt import SettingsPanelQt
    from ui.file_browser_panel_qt import FileBrowserPanelQt
    from ui.notepad_panel_qt import NotepadPanelQt
    UI_PANELS_AVAILABLE = True
    logger.info("✅ UI panels loaded successfully")
except ImportError as e:
    logger.warning(f"Some UI panels not available: {e}")
    UI_PANELS_AVAILABLE = False


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
        self.level_system = None        # UserLevelSystem – XP / levelling
        self.auto_backup = None         # AutoBackupSystem – periodic state backup
        self.unlockables_system = None  # UnlockablesSystem – cursors/themes/outfits

        # UI sub-components declared here so setup_ui() can reference them safely
        self.panda_widget = None        # PandaOpenGLWidget (3-D panda sidebar)
        self.perf_dashboard = None      # PerformanceDashboard dock panel
        self.tool_panels = {}           # {panel_id: widget}
        self.tool_dock_widgets = {}     # {panel_id: QDockWidget}
        self._last_sorted_count = 0     # files moved in last sort (for achievements)

        # Worker thread
        self.worker = None
        
        # Paths
        self.input_path = None
        self.output_path = None
        
        # Tooltip manager (will be initialized later)
        self.tooltip_manager = None
        
        # Docking system - track floating panels
        self.docked_widgets = {}  # {tab_name: QDockWidget}
        self.tab_widgets = {}  # {tab_name: widget} - original tab widgets
        
        # Setup UI
        self.setup_ui()
        self.setup_menubar()
        self.setup_statusbar()
        self.apply_theme()
        
        # Initialize components
        self.initialize_components()
        
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
        
        # Create draggable tabs
        self.tabs = DraggableTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tab_detached.connect(self.on_tab_detached)
        content_layout.addWidget(self.tabs)
        
        # Create main tab (dashboard/welcome)
        self.create_main_tab()
        
        # Create tools tab (includes sorting + all tools)
        self.create_tools_tab()
        
        # Create Panda Features tab (always shown; handles missing OpenGL gracefully)
        # NOTE: self.panda_widget is still None here — it is created later in setup_ui()
        # after the left-side content_widget is fully assembled.  create_panda_features_tab()
        # guards all panda_widget references with getattr(..., None), so None is safe.
        try:
            panda_features_tab = self.create_panda_features_tab()
            self.tabs.addTab(panda_features_tab, "🐼 Panda")
            logger.info("✅ Panda Features tab added to main tabs")
        except Exception as e:
            logger.error(f"Could not create Panda Features tab: {e}", exc_info=True)
        
        # Create file browser tab
        self.create_file_browser_tab()
        
        # Create notepad tab
        self.create_notepad_tab()
        
        # Create settings tab
        self.create_settings_tab()
        
        # Progress bar (at bottom of content)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        content_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(content_widget)
        
        # Right side: Panda 3D widget (OpenGL-accelerated)
        # Load panda widget INDEPENDENTLY of UI panels
        if PANDA_WIDGET_AVAILABLE:
            try:
                self.panda_widget = PandaOpenGLWidget()
                self.panda_widget.setMinimumWidth(300)
                self.panda_widget.setMaximumWidth(400)
                
                # Connect panda widget signals
                self.panda_widget.clicked.connect(self.on_panda_clicked)
                self.panda_widget.mood_changed.connect(self.on_panda_mood_changed)
                self.panda_widget.animation_changed.connect(self.on_panda_animation_changed)
                
                splitter.addWidget(self.panda_widget)
                splitter.setStretchFactor(0, 3)  # Content gets 75%
                splitter.setStretchFactor(1, 1)  # Panda gets 25%
                logger.info("✅ Panda 3D OpenGL widget loaded successfully")
            except Exception as e:
                logger.error(f"Could not load panda widget: {e}", exc_info=True)
                # Create fallback placeholder
                fallback_widget = QWidget()
                fallback_layout = QVBoxLayout(fallback_widget)
                fallback_label = QLabel("🐼 Panda Widget\n\nOpenGL Error\n\n" + str(e))
                fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                fallback_label.setStyleSheet("color: red; font-size: 11pt;")
                fallback_label.setWordWrap(True)
                fallback_layout.addWidget(fallback_label)
                splitter.addWidget(fallback_widget)
                splitter.setStretchFactor(0, 3)
                splitter.setStretchFactor(1, 1)
                self.panda_widget = None
        else:
            # Show clear message about what's missing
            fallback_widget = QWidget()
            fallback_layout = QVBoxLayout(fallback_widget)
            fallback_label = QLabel(
                "🐼 Panda Widget\n\n"
                "Required Dependencies Missing:\n\n"
                "• PyQt6\n"
                "• PyOpenGL\n\n"
                "Install with:\n"
                "pip install PyQt6 PyOpenGL PyOpenGL-accelerate"
            )
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_label.setStyleSheet("color: orange; font-size: 10pt;")
            fallback_label.setWordWrap(True)
            fallback_layout.addWidget(fallback_label)
            splitter.addWidget(fallback_widget)
            splitter.setStretchFactor(0, 3)
            splitter.setStretchFactor(1, 1)
            self.panda_widget = None
            logger.warning("Panda widget dependencies not installed")
    
    def create_main_tab(self):
        """Create the main tab with welcome/dashboard."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Welcome message
        welcome_label = QLabel("🎮 Welcome to PS2 Texture Toolkit")
        welcome_label.setStyleSheet("font-size: 24pt; font-weight: bold;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        layout.addSpacing(20)
        
        # Description
        desc_label = QLabel(
            "A comprehensive toolkit for managing, sorting, and enhancing PS2 game textures.\n\n"
            "Navigate to the Tools tab to access:\n"
            "• Texture Sorter - Automatically organize textures by type\n"
            "• Image Upscaler - Enhance texture resolution\n"
            "• Background Remover - Remove backgrounds from images\n"
            "• Alpha Fixer - Fix alpha channel issues\n"
            "• Color Correction - Adjust colors and enhance images\n"
            "• Line Art Converter - Convert images to line art\n"
            "• And many more tools!"
        )
        desc_label.setStyleSheet("font-size: 12pt; color: #cccccc;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Quick stats or info could go here in the future
        info_label = QLabel(f"Version: {APP_VERSION}")
        info_label.setStyleSheet("color: gray; font-size: 10pt;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        self.tabs.addTab(tab, "Home")
    
    def create_sorting_tab_widget(self):
        """Create the texture sorting widget (for use in tools tab)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Input section
        input_group = QFrame()
        input_group.setFrameShape(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_group)
        
        input_label = QLabel("📁 Input Folder:")
        input_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        input_layout.addWidget(input_label)
        
        input_row = QHBoxLayout()
        self.input_path_label = QLabel("No folder selected")
        self.input_path_label.setStyleSheet("padding: 5px; background-color: #2b2b2b; border-radius: 3px;")
        input_row.addWidget(self.input_path_label, 1)
        
        input_btn = QPushButton("Browse...")
        input_btn.clicked.connect(self.browse_input)
        input_btn.setMinimumWidth(100)
        input_row.addWidget(input_btn)
        
        input_layout.addLayout(input_row)
        layout.addWidget(input_group)
        
        # Output section
        output_group = QFrame()
        output_group.setFrameShape(QFrame.Shape.StyledPanel)
        output_layout = QVBoxLayout(output_group)
        
        output_label = QLabel("📂 Output Folder:")
        output_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        output_layout.addWidget(output_label)
        
        output_row = QHBoxLayout()
        self.output_path_label = QLabel("No folder selected")
        self.output_path_label.setStyleSheet("padding: 5px; background-color: #2b2b2b; border-radius: 3px;")
        output_row.addWidget(self.output_path_label, 1)
        
        output_btn = QPushButton("Browse...")
        output_btn.clicked.connect(self.browse_output)
        output_btn.setMinimumWidth(100)
        output_row.addWidget(output_btn)
        
        output_layout.addLayout(output_row)
        layout.addWidget(output_group)
        
        # Mode and Style selection
        options_group = QFrame()
        options_group.setFrameShape(QFrame.Shape.StyledPanel)
        options_layout = QVBoxLayout(options_group)
        
        options_label = QLabel("⚙️ Sorting Options:")
        options_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        options_layout.addWidget(options_label)
        
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("🚀 Automatic - AI classifies and moves instantly", "automatic")
        self.mode_combo.addItem("💡 Suggested - AI suggests, you confirm", "suggested")
        self.mode_combo.addItem("✍️ Manual - You type folder, AI learns", "manual")
        mode_row.addWidget(self.mode_combo, 1)
        options_layout.addLayout(mode_row)
        
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self.style_combo = QComboBox()
        for key, style_cls in ORGANIZATION_STYLES.items():
            style_instance = style_cls()
            self.style_combo.addItem(f"{style_instance.get_name()}", key)
        style_row.addWidget(self.style_combo, 1)
        options_layout.addLayout(style_row)
        
        layout.addWidget(options_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.sort_button = QPushButton("🚀 Start Sorting")
        self.sort_button.setMinimumHeight(50)
        self.sort_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.sort_button.clicked.connect(self.start_sorting)
        self.sort_button.setEnabled(False)
        button_layout.addWidget(self.sort_button)
        
        self.cancel_button = QPushButton("⏹️ Cancel")
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.clicked.connect(self.cancel_operation)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Log output
        log_label = QLabel("📋 Log:")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        layout.addWidget(self.log_text, 1)  # Stretch factor 1
        
        return tab
    
    def create_tools_tab(self):
        """Create tools tab with dockable tool panels."""
        # Create a central widget for the tools tab
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add info label at top
        info_label = QLabel("🔧 Tools can be docked/undocked via View menu")
        info_label.setStyleSheet("background: #2b2b2b; padding: 5px; color: #888;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Central widget will be empty initially - tools are all docked panels
        central_info = QLabel(
            "Tool panels are docked around the edges.\n\n"
            "Use View → Tool Panels to show/hide tools.\n"
            "Drag tool title bars to rearrange or float them."
        )
        central_info.setStyleSheet("font-size: 14pt; color: #666;")
        central_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(central_info, 1)
        
        # Create all tool panels and dock them (tool_panels / tool_dock_widgets
        # are already declared as {} in __init__ so no re-init needed here)
        self._create_tool_dock_panels()
        
        return tab
    
    def _create_tool_dock_panels(self):
        """Create all tool panels as dockable widgets."""
        # Define tools with their configurations
        tool_configs = [
            ('sorter', '🗂️ Texture Sorter', Qt.DockWidgetArea.LeftDockWidgetArea),
            ('bg_remover', '🎭 Background Remover', Qt.DockWidgetArea.LeftDockWidgetArea),
            ('alpha_fixer', '✨ Alpha Fixer', Qt.DockWidgetArea.LeftDockWidgetArea),
            ('color', '🎨 Color Correction', Qt.DockWidgetArea.RightDockWidgetArea),
            ('normalizer', '⚙️ Batch Normalizer', Qt.DockWidgetArea.RightDockWidgetArea),
            ('quality', '✓ Quality Checker', Qt.DockWidgetArea.RightDockWidgetArea),
            ('upscaler', '🔍 Image Upscaler', Qt.DockWidgetArea.BottomDockWidgetArea),
            ('lineart', '✏️ Line Art Converter', Qt.DockWidgetArea.BottomDockWidgetArea),
            ('rename', '📝 Batch Rename', Qt.DockWidgetArea.BottomDockWidgetArea),
            ('repair', '🔧 Image Repair', Qt.DockWidgetArea.BottomDockWidgetArea),
            ('organizer', '📁 Texture Organizer', Qt.DockWidgetArea.BottomDockWidgetArea),
        ]
        
        # Create Texture Sorter panel
        sorting_widget = self.create_sorting_tab_widget()
        self._add_tool_dock('sorter', '🗂️ Texture Sorter', sorting_widget, Qt.DockWidgetArea.LeftDockWidgetArea)
        
        # Create other tool panels if available
        if UI_PANELS_AVAILABLE:
            try:
                # Background Remover
                bg_panel = BackgroundRemoverPanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('bg_remover', '🎭 Background Remover', bg_panel, Qt.DockWidgetArea.LeftDockWidgetArea)
                
                # Alpha Fixer
                alpha_panel = AlphaFixerPanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('alpha_fixer', '✨ Alpha Fixer', alpha_panel, Qt.DockWidgetArea.LeftDockWidgetArea)
                
                # Color Correction
                color_panel = ColorCorrectionPanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('color', '🎨 Color Correction', color_panel, Qt.DockWidgetArea.RightDockWidgetArea)
                
                # Batch Normalizer
                norm_panel = BatchNormalizerPanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('normalizer', '⚙️ Batch Normalizer', norm_panel, Qt.DockWidgetArea.RightDockWidgetArea)
                
                # Quality Checker
                quality_panel = QualityCheckerPanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('quality', '✓ Quality Checker', quality_panel, Qt.DockWidgetArea.RightDockWidgetArea)
                
                # Image Upscaler
                upscaler_panel = ImageUpscalerPanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('upscaler', '🔍 Image Upscaler', upscaler_panel, Qt.DockWidgetArea.BottomDockWidgetArea)
                
                # Line Art Converter
                line_panel = LineArtConverterPanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('lineart', '✏️ Line Art Converter', line_panel, Qt.DockWidgetArea.BottomDockWidgetArea)
                
                # Batch Rename
                rename_panel = BatchRenamePanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('rename', '📝 Batch Rename', rename_panel, Qt.DockWidgetArea.BottomDockWidgetArea)
                
                # Image Repair
                repair_panel = ImageRepairPanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('repair', '🔧 Image Repair', repair_panel, Qt.DockWidgetArea.BottomDockWidgetArea)
                
                # Texture Organizer
                organizer_panel = OrganizerPanelQt(tooltip_manager=self.tooltip_manager)
                self._add_tool_dock('organizer', '📁 Texture Organizer', organizer_panel, Qt.DockWidgetArea.BottomDockWidgetArea)
                
                self.log("✅ All tool panels created as dockable widgets")
                
            except Exception as e:
                logger.error(f"Error creating tool dock panels: {e}", exc_info=True)
        
        # Add Performance Dashboard dock (independent of UI_PANELS_AVAILABLE)
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
            logger.info("✅ Performance dashboard added as dockable widget")
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
        
        # Add to main window
        self.addDockWidget(area, dock)
        
        logger.info(f"Added tool dock: {tool_id} - {title}")
    
    def _update_tool_panels_menu(self):
        """Update View menu with tool panel visibility toggles."""
        # Add submenu for tool panels if it doesn't exist
        if not hasattr(self, 'tool_panels_menu'):
            self.tool_panels_menu = self.view_menu.addMenu("Tool Panels")
        
        # Clear existing actions
        self.tool_panels_menu.clear()
        
        # Add toggle action for each tool
        for tool_id, dock in self.tool_dock_widgets.items():
            action = dock.toggleViewAction()
            self.tool_panels_menu.addAction(action)
    
    def switch_tool(self, tool_id):
        """Switch to a different tool panel (deprecated - tools are now dockable)."""
        # This method is kept for backward compatibility but tools are now docked
        # Instead of switching, we show/activate the tool's dock widget
        if tool_id in self.tool_dock_widgets:
            dock = self.tool_dock_widgets[tool_id]
            dock.show()
            dock.raise_()
            dock.activateWindow()
            logger.info(f"Activated tool dock: {tool_id}")
    
    def create_panda_features_tab(self):
        """Create panda features tab with shop, inventory, closet, achievements, and customization."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create sub-tabs for panda features
        panda_tabs = QTabWidget()
        panda_tabs.setDocumentMode(True)
        
        # Get panda character
        panda_char = getattr(self.panda_widget, 'panda', None)
        
        # 1. Customization Tab
        try:
            from ui.customization_panel_qt import CustomizationPanelQt
            if panda_char is not None:
                custom_panel = CustomizationPanelQt(panda_char, self.panda_widget, tooltip_manager=self.tooltip_manager)
                
                # Connect customization panel signals
                custom_panel.color_changed.connect(self.on_customization_color_changed)
                custom_panel.trail_changed.connect(self.on_customization_trail_changed)
                
                panda_tabs.addTab(custom_panel, "🎨 Customization")
                logger.info("✅ Customization panel added to panda tab")
        except Exception as e:
            logger.error(f"Could not load customization panel: {e}", exc_info=True)
        
        # 2. Shop Tab
        try:
            from ui.shop_panel_qt import ShopPanelQt
            from features.shop_system import ShopSystem
            from features.currency_system import CurrencySystem

            # Initialize systems and store as instance vars so other methods can use them
            self.shop_system = ShopSystem()
            self.currency_system = CurrencySystem()

            shop_panel = ShopPanelQt(self.shop_system, self.currency_system, tooltip_manager=self.tooltip_manager)

            # Connect shop panel signals
            shop_panel.item_purchased.connect(self.on_shop_item_purchased)

            panda_tabs.addTab(shop_panel, "🛒 Shop")
            logger.info("✅ Shop panel added to panda tab")
        except Exception as e:
            logger.error(f"Could not load shop panel: {e}", exc_info=True)
            # Add placeholder
            label = QLabel("⚠️ Shop not available\n\nInstall required dependencies")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "🛒 Shop")

        # 3. Inventory Tab
        try:
            from ui.inventory_panel_qt import InventoryPanelQt

            # Reuse self.shop_system if already created above, else create fresh
            _shop = self.shop_system
            if _shop is None:
                from features.shop_system import ShopSystem as _ShopSystem
                _shop = _ShopSystem()
            inventory_panel = InventoryPanelQt(_shop, tooltip_manager=self.tooltip_manager)

            # Connect inventory panel signals
            inventory_panel.item_selected.connect(self.on_inventory_item_selected)

            panda_tabs.addTab(inventory_panel, "📦 Inventory")
            logger.info("✅ Inventory panel added to panda tab")
        except Exception as e:
            logger.error(f"Could not load inventory panel: {e}", exc_info=True)
            # Add placeholder
            label = QLabel("⚠️ Inventory not available\n\nInstall required dependencies")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "📦 Inventory")

        # 4. Closet Tab
        try:
            from ui.closet_display_qt import ClosetDisplayWidget
            from features.panda_closet import PandaCloset

            self.panda_closet = PandaCloset()
            closet_panel = ClosetDisplayWidget(tooltip_manager=self.tooltip_manager)
            panda_tabs.addTab(closet_panel, "👔 Closet")
            logger.info("✅ Closet panel added to panda tab")
        except Exception as e:
            logger.error(f"Could not load closet panel: {e}", exc_info=True)
            # Add placeholder
            label = QLabel("⚠️ Closet not available\n\nInstall required dependencies")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "👔 Closet")

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
            panda_tabs.addTab(minigame_panel, "🎮 Minigames")
            logger.info("✅ Minigames panel added to panda tab")
        except Exception as e:
            logger.error(f"Could not load minigames panel: {e}", exc_info=True)
            # Add placeholder
            label = QLabel("⚠️ Minigames not available\n\nInstall required dependencies")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "🎮 Minigames")
        
        # 7. Widgets Tab (Interactive toys/food/accessories)
        try:
            from ui.widgets_panel_qt import WidgetsPanelQt
            from features.panda_widgets import WidgetCollection
            
            widget_collection = WidgetCollection()
            widgets_panel = WidgetsPanelQt(widget_collection, self.panda_widget, tooltip_manager=self.tooltip_manager)
            panda_tabs.addTab(widgets_panel, "🧸 Widgets")
            logger.info("✅ Widgets panel added to panda tab")
        except Exception as e:
            logger.error(f"Could not load widgets panel: {e}", exc_info=True)
            # Add placeholder
            label = QLabel("⚠️ Widgets not available\n\nInstall required dependencies")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            panda_tabs.addTab(label, "🧸 Widgets")
        
        layout.addWidget(panda_tabs)
        return tab
    
    def create_file_browser_tab(self):
        """Create file browser tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            if UI_PANELS_AVAILABLE:
                tooltip_manager = getattr(self, 'tooltip_manager', None)
                self.file_browser_panel = FileBrowserPanelQt(config, tooltip_manager)
                layout.addWidget(self.file_browser_panel)
                self.log("✅ File browser panel loaded successfully")
            else:
                label = QLabel("⚠️ File browser requires PyQt6 and PIL\n\nInstall with: pip install PyQt6 Pillow")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
        except Exception as e:
            logger.error(f"Error loading file browser panel: {e}", exc_info=True)
            label = QLabel(f"⚠️ Error loading file browser:\n{e}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        
        self.tabs.addTab(tab, "📁 File Browser")
    
    def create_notepad_tab(self):
        """Create notepad tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            if UI_PANELS_AVAILABLE:
                tooltip_manager = getattr(self, 'tooltip_manager', None)
                self.notepad_panel = NotepadPanelQt(config, tooltip_manager)
                layout.addWidget(self.notepad_panel)
                self.log("✅ Notepad panel loaded successfully")
            else:
                label = QLabel("⚠️ Notepad requires PyQt6\n\nInstall with: pip install PyQt6")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
        except Exception as e:
            logger.error(f"Error loading notepad panel: {e}", exc_info=True)
            label = QLabel(f"⚠️ Error loading notepad:\n{e}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        
        self.tabs.addTab(tab, "📝 Notepad")
    
    def create_settings_tab(self):
        """Create settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            # Create comprehensive settings panel
            self.settings_panel = SettingsPanelQt(config, self, tooltip_manager=self.tooltip_manager)
            
            # Connect settings changed signal
            self.settings_panel.settingsChanged.connect(self.on_settings_changed)
            
            layout.addWidget(self.settings_panel)
            self.log("✅ Settings panel loaded successfully")
            
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
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Input Folder...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.browse_input)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu - for docking controls
        view_menu = menubar.addMenu("&View")
        
        self.view_menu = view_menu  # Store reference for dynamic updates
        
        # Add "Pop Out Tab" action
        popout_action = QAction("Pop Out Current Tab", self)
        popout_action.setShortcut("Ctrl+Shift+P")
        popout_action.triggered.connect(self.popout_current_tab)
        view_menu.addAction(popout_action)
        
        view_menu.addSeparator()
        
        # Submenu for restoring docked tabs
        self.restore_menu = view_menu.addMenu("Restore Docked Tab")
        self.restore_menu.setEnabled(False)  # Disabled until tabs are popped out
        
        view_menu.addSeparator()
        
        # Reset layout action
        reset_layout_action = QAction("Reset Window Layout", self)
        reset_layout_action.triggered.connect(self.reset_window_layout)
        view_menu.addAction(reset_layout_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_statusbar(self):
        """Setup status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
    
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
            QMainWindow {{
                background-color: #002b36;
            }}
            QWidget {{
                background-color: #002b36;
                color: #839496;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QPushButton {{
                background-color: {accent};
                color: #fdf6e3;
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
                background-color: #073642;
                color: #586e75;
            }}
            QLabel {{
                color: #839496;
                background-color: transparent;
            }}
            QTabWidget::pane {{
                border: 1px solid #073642;
                background-color: #073642;
            }}
            QTabBar::tab {{
                background-color: #073642;
                color: #839496;
                padding: 8px 20px;
                border: 1px solid #073642;
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {accent};
                color: #fdf6e3;
            }}
            QTabBar::tab:hover {{
                background-color: #0d4251;
            }}
            QMenuBar {{
                background-color: #073642;
                color: #839496;
                border-bottom: 1px solid #073642;
            }}
            QMenuBar::item:selected {{
                background-color: {accent};
                color: #fdf6e3;
            }}
            QMenu {{
                background-color: #073642;
                color: #839496;
                border: 1px solid #073642;
            }}
            QMenu::item:selected {{
                background-color: {accent};
                color: #fdf6e3;
            }}
            QProgressBar {{
                border: 1px solid #073642;
                border-radius: 3px;
                text-align: center;
                background-color: #073642;
                color: #839496;
            }}
            QProgressBar::chunk {{
                background-color: {accent};
            }}
            QFrame {{
                background-color: #073642;
                border: 1px solid #073642;
                border-radius: 4px;
            }}
            QTextEdit {{
                background-color: #073642;
                color: #839496;
                border: 1px solid #073642;
            }}
            QScrollBar:vertical {{
                background-color: #073642;
                width: 12px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #586e75;
                border-radius: 6px;
            }}
            QDockWidget {{
                color: #839496;
                titlebar-close-icon: none;
            }}
            QDockWidget::title {{
                background-color: #073642;
                padding: 4px;
            }}
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
            # Note: OrganizationEngine requires output_dir and style_class parameters.
            # It will be created on-demand in perform_sorting() once the output directory
            # is selected by the user via browse_output().
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
        """Update button enabled states based on selected paths."""
        has_input = self.input_path is not None
        has_output = self.output_path is not None
        
        self.sort_button.setEnabled(has_input and has_output)
    
    def start_sorting(self):
        """Start texture sorting operation."""
        if not self.input_path or not self.output_path:
            QMessageBox.warning(self, "Missing Paths", "Please select both input and output folders.")
            return
        
        self.log("🚀 Starting texture sorting...")
        self.set_operation_running(True)
        
        # Create worker thread
        self.worker = WorkerThread(self.perform_sorting)
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.operation_finished)
        self.worker.start()
    
    def cancel_operation(self):
        """Cancel current operation."""
        if self.worker:
            self.log("⏹️ Cancelling operation...")
            self.worker.cancel()
    
    def perform_sorting(self, progress_callback, log_callback, check_cancelled):
        """Perform actual sorting (runs in worker thread)."""
        try:
            from pathlib import Path
            
            # Try to import AI classifier, fall back gracefully
            try:
                from organizer.combined_feature_extractor import CombinedFeatureExtractor
                feature_extractor = CombinedFeatureExtractor()
                use_ai = True
                log_callback("✓ AI classifier loaded")
            except Exception as e:
                log_callback(f"⚠️ AI classifier unavailable, using pattern-based: {e}")
                feature_extractor = None
                use_ai = False
            
            log_callback("🔍 Scanning input directory...")
            
            # Collect texture files
            extensions = {'.dds', '.png', '.jpg', '.jpeg', '.tga', '.bmp', '.tif', '.tiff'}
            files = []
            
            for ext in extensions:
                files.extend(self.input_path.rglob(f'*{ext}'))
            
            total_files = len(files)
            if total_files == 0:
                log_callback("⚠️ No texture files found in input directory")
                return
            
            log_callback(f"📊 Found {total_files} texture files")
            
            # Process and move files
            moved_count = 0
            failed_count = 0
            
            for idx, file_path in enumerate(files):
                if check_cancelled():
                    log_callback("⏹️ Operation cancelled by user")
                    break
                
                # Classify texture
                if use_ai and feature_extractor:
                    try:
                        category, confidence = feature_extractor.classify_texture(str(file_path))
                    except Exception:
                        category, confidence = self._pattern_classify(file_path.name)
                else:
                    category, confidence = self._pattern_classify(file_path.name)
                
                # Determine target folder
                target_folder = self.output_path / category
                target_folder.mkdir(parents=True, exist_ok=True)
                
                # Move file
                try:
                    target_path = target_folder / file_path.name
                    
                    # Handle duplicate filenames
                    if target_path.exists():
                        base = target_path.stem
                        ext = target_path.suffix
                        counter = 1
                        while target_path.exists():
                            target_path = target_folder / f"{base}_{counter}{ext}"
                            counter += 1
                    
                    file_path.rename(target_path)
                    moved_count += 1
                    progress_callback(idx + 1, total_files, f"Moved {file_path.name} to {category}")
                except Exception as e:
                    failed_count += 1
                    log_callback(f"⚠️ Failed to move {file_path.name}: {e}")
                    progress_callback(idx + 1, total_files, f"Failed: {file_path.name}")
            
            # Report results
            log_callback(f"\n✅ Sorting completed!")
            log_callback(f"   Successfully moved: {moved_count} files")
            if failed_count > 0:
                log_callback(f"   Failed: {failed_count} files")
            # Store for operation_finished achievement tracking
            self._last_sorted_count = moved_count
                
        except Exception as e:
            import traceback
            log_callback(f"❌ Sorting failed: {str(e)}")
            log_callback(f"Traceback: {traceback.format_exc()}")
    
    def _pattern_classify(self, filename: str) -> tuple:
        """Fallback pattern-based classification."""
        filename_lower = filename.lower()
        
        # Simple pattern matching
        patterns = {
            'character': ['char', 'body', 'face', 'skin', 'hair', 'npc', 'player'],
            'environment': ['ground', 'wall', 'floor', 'terrain', 'grass', 'rock', 'stone', 'dirt'],
            'props': ['item', 'object', 'prop', 'weapon', 'armor', 'tool'],
            'ui': ['ui', 'hud', 'icon', 'button', 'menu', 'cursor'],
            'effects': ['particle', 'effect', 'fx', 'glow', 'spark', 'fire', 'smoke'],
            'vegetation': ['tree', 'plant', 'leaf', 'flower', 'bush', 'foliage'],
            'architecture': ['building', 'house', 'door', 'window', 'roof'],
        }
        
        for category, keywords in patterns.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category, 0.6
        
        # Default category
        return 'miscellaneous', 0.3
    
    def set_operation_running(self, running: bool):
        """Update UI for operation running state."""
        self.sort_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.cancel_button.setVisible(running)
        self.progress_bar.setVisible(running)
        
        if not running:
            self.progress_bar.setValue(0)
            self.statusbar.showMessage("Ready")
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress bar and status."""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.progress_bar.setFormat(f"{current}/{total} - {message}")
        
        self.statusbar.showMessage(message)
    
    def operation_finished(self, success: bool, message: str, files_processed: int = 0):
        """Handle operation completion."""
        self.set_operation_running(False)
        # Use count stored by perform_sorting when caller doesn't supply it
        if files_processed == 0:
            files_processed = getattr(self, '_last_sorted_count', 0)
            self._last_sorted_count = 0

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
    
    def log(self, message: str):
        """Add message to log."""
        self.log_text.append(message)
        logger.info(message)
    
    def on_settings_changed(self, setting_key: str, value):
        """Handle settings changes in real-time"""
        try:
            logger.info(f"Setting changed: {setting_key} = {value}")
            
            # Update the config value
            keys = setting_key.split('.')
            if len(keys) == 2:
                config.set(keys[0], keys[1], value)
            elif len(keys) == 1:
                # Single-level key - store in general section
                config.set('general', keys[0], value)
                logger.debug(f"Single-level setting key '{setting_key}' stored in 'general' section")
            else:
                # Multi-level nested keys - only handle first two levels
                logger.warning(f"Setting key '{setting_key}' has unexpected format (expected 'section.key')")
                if len(keys) >= 2:
                    config.set(keys[0], keys[1], value)
            
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

            elif setting_key == 'ui.animation_speed':
                # Store animation speed in config; individual animated widgets read it on play.
                # 0.0 = paused/disabled, 1.0 = normal, 4.0 = maximum safe speed (above this
                # Qt timers fire too fast and animations become visually indistinguishable).
                try:
                    speed = float(value)
                    speed = max(0.0, min(4.0, speed))
                    config.set('ui', 'animation_speed', speed)
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

        except Exception as e:
            logger.error(f"Error handling panda click: {e}", exc_info=True)
    
    def on_panda_mood_changed(self, mood: str):
        """Handle panda mood changes."""
        try:
            # Log the mood change
            logger.info(f"Panda mood changed to: {mood}")
            
            # Update status bar to reflect mood
            self.statusbar.showMessage(f"🐼 Panda is feeling {mood}", 3000)
            
        except Exception as e:
            logger.error(f"Error handling panda mood change: {e}", exc_info=True)
    
    def on_panda_animation_changed(self, animation: str):
        """Handle panda animation state changes."""
        try:
            logger.debug(f"Panda animation changed to: {animation}")
            # Forward animation state to panda widget if it supports it
            if self.panda_widget and hasattr(self.panda_widget, 'set_animation'):
                self.panda_widget.set_animation(animation)
        except Exception as e:
            logger.error(f"Error handling panda animation change: {e}", exc_info=True)
    
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

        except Exception as e:
            logger.error(f"Error handling shop purchase: {e}", exc_info=True)

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
            except Exception as _e:
                logger.debug(f"Could not equip inventory item {item_id}: {_e}")

            # Preview item on the panda widget if it supports it
            try:
                if self.panda_widget and hasattr(self.panda_widget, 'preview_item'):
                    self.panda_widget.preview_item(item_id)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error handling inventory selection: {e}", exc_info=True)

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
        except Exception as _e:
            logger.debug(f"Level-up callback error: {_e}")
    
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
        
        # Create dock widget
        dock = QDockWidget(tab_name, self)
        dock.setWidget(widget)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        
        # Connect close event to restore tab
        dock.visibilityChanged.connect(
            lambda visible, name=clean_name, original_name=tab_name: 
                self._on_dock_visibility_changed(visible, name, original_name)
        )
        
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
        
        # Create dock widget
        dock = QDockWidget(tab_name, self)
        dock.setWidget(widget)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        
        # Connect close event to restore tab
        dock.visibilityChanged.connect(
            lambda visible, name=clean_name, original_name=tab_name: 
                self._on_dock_visibility_changed(visible, name, original_name)
        )
        
        # Store dock reference
        self.docked_widgets[clean_name] = dock
        
        # Add as floating dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        dock.setFloating(True)
        
        # Update restore menu
        self._update_restore_menu()
        
        self.statusbar.showMessage(f"Popped out: {clean_name}", 3000)
    
    def _on_dock_visibility_changed(self, visible: bool, name: str, original_name: str):
        """Handle dock widget visibility changes (when user closes dock)."""
        if not visible:
            # User closed the dock widget - restore to tabs
            self.restore_docked_tab(name, original_name)
    
    def restore_docked_tab(self, name: str, original_name: str = None):
        """Restore a docked tab back to the main tab widget."""
        if name not in self.docked_widgets:
            return
        
        dock = self.docked_widgets[name]
        widget = dock.widget()
        
        # Remove from dock
        dock.setWidget(None)  # Prevent widget deletion
        self.removeDockWidget(dock)
        del self.docked_widgets[name]
        
        # Restore to tabs
        if widget and widget in self.tab_widgets.values():
            tab_name = original_name if original_name else name
            self.tabs.addTab(widget, tab_name)
            self.statusbar.showMessage(f"Restored: {name}", 3000)
        
        # Update restore menu
        self._update_restore_menu()
    
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
        # Restore all docked widgets
        docked_names = list(self.docked_widgets.keys())
        for name in docked_names:
            dock = self.docked_widgets[name]
            self.restore_docked_tab(name, dock.windowTitle())
        
        self.statusbar.showMessage("Window layout reset", 3000)
    
    def save_dock_layout(self):
        """Save current dock layout to config."""
        try:
            # Save main window geometry
            geometry = self.saveGeometry()
            state = self.saveState()
            
            config.set('window', 'geometry', geometry.toHex().data().decode())
            config.set('window', 'state', state.toHex().data().decode())
            
            # Save docked tabs info
            docked_tabs = list(self.docked_widgets.keys())
            config.set('window', 'docked_tabs', ','.join(docked_tabs))
            
            # Save tool dock visibility
            tool_dock_states = {}
            for tool_id, dock in self.tool_dock_widgets.items():
                tool_dock_states[tool_id] = {
                    'visible': dock.isVisible(),
                    'floating': dock.isFloating(),
                }
            config.set('window', 'tool_dock_states', str(tool_dock_states))
            
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
            except:
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
    except ImportError:
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


def main():
    """Main entry point."""
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
    
    # Show first-run tutorial if this is a new installation
    try:
        from features.tutorial_system import TutorialManager
        _tm = TutorialManager()
        if _tm.should_show_tutorial():
            _tm.start_tutorial(window)
    except Exception as _te:
        logger.debug(f"Tutorial check skipped: {_te}")

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
