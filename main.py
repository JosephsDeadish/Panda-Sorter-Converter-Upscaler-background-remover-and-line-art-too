#!/usr/bin/env python3
"""
Game Texture Sorter - Qt Main Application
A Qt6-based application with OpenGL rendering.
Author: Dead On The Inside / JosephsDeadish
"""

import sys
import os
import logging
from pathlib import Path

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
        QSplitter, QFrame, QComboBox
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
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
try:
    from ui.panda_widget_gl import PandaOpenGLWidget
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
    UI_PANELS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some UI panels not available: {e}")
    UI_PANELS_AVAILABLE = False


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
        
        # Worker thread
        self.worker = None
        
        # Paths
        self.input_path = None
        self.output_path = None
        
        # Tooltip manager (will be initialized later)
        self.tooltip_manager = None
        
        # Setup UI
        self.setup_ui()
        self.setup_menubar()
        self.setup_statusbar()
        self.apply_theme()
        
        # Initialize components
        self.initialize_components()
        
        logger.info("Qt Main Window initialized successfully")
    
    def setup_ui(self):
        """Setup the main UI layout."""
        self.setWindowTitle(f"🐼 {APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(900, 650)
        
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
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        content_layout.addWidget(self.tabs)
        
        # Create main tab (dashboard/welcome)
        self.create_main_tab()
        
        # Create tools tab (includes sorting + all tools)
        self.create_tools_tab()
        
        # Create settings tab
        self.create_settings_tab()
        
        # Progress bar (at bottom of content)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        content_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(content_widget)
        
        # Right side: Panda 3D widget (OpenGL-accelerated)
        if UI_PANELS_AVAILABLE:
            try:
                self.panda_widget = PandaOpenGLWidget()
                self.panda_widget.setMinimumWidth(300)
                self.panda_widget.setMaximumWidth(400)
                splitter.addWidget(self.panda_widget)
                splitter.setStretchFactor(0, 3)  # Content gets 75%
                splitter.setStretchFactor(1, 1)  # Panda gets 25%
                logger.info("✅ Panda 3D OpenGL widget loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load panda widget: {e}")
                # Create fallback placeholder
                fallback_widget = QWidget()
                fallback_layout = QVBoxLayout(fallback_widget)
                fallback_label = QLabel("🐼 Panda Widget\n\nOpenGL not available\n\nThe 3D panda companion\ncould not be loaded.")
                fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                fallback_label.setStyleSheet("color: gray; font-size: 11pt;")
                fallback_layout.addWidget(fallback_label)
                splitter.addWidget(fallback_widget)
                splitter.setStretchFactor(0, 3)
                splitter.setStretchFactor(1, 1)
                self.panda_widget = None
                logger.info("Using fallback placeholder for panda widget")
        else:
            self.panda_widget = None
    
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
        """Create tools tab with Qt-based tool panels."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Create tool tabs
        tool_tabs = QTabWidget()
        tool_tabs.setDocumentMode(True)
        layout.addWidget(tool_tabs)
        
        # Add Texture Sorter as first tool
        sorting_widget = self.create_sorting_tab_widget()
        tool_tabs.addTab(sorting_widget, "🗂️ Texture Sorter")
        
        # Add tool panels if available
        if UI_PANELS_AVAILABLE:
            try:
                # Background Remover
                bg_panel = BackgroundRemoverPanelQt()
                tool_tabs.addTab(bg_panel, "🎭 Background Remover")
                
                # Alpha Fixer
                alpha_panel = AlphaFixerPanelQt()
                tool_tabs.addTab(alpha_panel, "✨ Alpha Fixer")
                
                # Color Correction
                color_panel = ColorCorrectionPanelQt()
                tool_tabs.addTab(color_panel, "🎨 Color Correction")
                
                # Batch Normalizer
                norm_panel = BatchNormalizerPanelQt()
                tool_tabs.addTab(norm_panel, "⚙️ Batch Normalizer")
                
                # Quality Checker
                quality_panel = QualityCheckerPanelQt()
                tool_tabs.addTab(quality_panel, "✓ Quality Checker")
                
                # Image Upscaler
                upscaler_panel = ImageUpscalerPanelQt()
                tool_tabs.addTab(upscaler_panel, "🔍 Image Upscaler")
                
                # Line Art Converter
                line_panel = LineArtConverterPanelQt()
                tool_tabs.addTab(line_panel, "✏️ Line Art Converter")
                
                # Batch Rename
                rename_panel = BatchRenamePanelQt()
                tool_tabs.addTab(rename_panel, "📝 Batch Rename")
                
                # Image Repair
                repair_panel = ImageRepairPanelQt()
                tool_tabs.addTab(repair_panel, "🔧 Image Repair")
                
                # Texture Organizer
                organizer_panel = OrganizerPanelQt()
                tool_tabs.addTab(organizer_panel, "📁 Texture Organizer")
                
                # Customization (only if panda character is available)
                panda_char = getattr(getattr(self, 'panda_widget', None), 'panda', None)
                if panda_char is not None:
                    custom_panel = CustomizationPanelQt(panda_char, self.panda_widget)
                    tool_tabs.addTab(custom_panel, "🎨 Customization")
                
                self.log("✅ All tool panels loaded successfully")
                
            except Exception as e:
                logger.error(f"Error loading tool panels: {e}", exc_info=True)
                # Fallback to placeholder
                label = QLabel(f"⚠️ Error loading tool panels: {e}")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                tool_tabs.addTab(label, "Error")
        else:
            # Fallback message
            label = QLabel(
                "🔧 Tool panels require additional dependencies.\n\n"
                "Available tools:\n"
                "• Texture Sorter\n"
                "• Background Remover\n"
                "• Alpha Fixer\n"
                "• Color Correction\n"
                "• Batch Normalizer\n"
                "• Quality Checker\n"
                "• Image Upscaler\n"
                "• Line Art Converter\n"
                "• Batch Rename\n"
                "• Image Repair\n"
                "• Customization"
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Arial", 11))
            tool_tabs.addTab(label, "Info")
        
        self.tabs.addTab(tab, "Tools")
    
    def create_settings_tab(self):
        """Create settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            # Create comprehensive settings panel
            self.settings_panel = SettingsPanelQt(config, self)
            
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
        else:  # Dark theme
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
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}", exc_info=True)
            self.log(f"⚠️ Warning: Some components failed to initialize: {e}")
    
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
        # TODO: Implement actual sorting logic
        import time
        for i in range(10):
            if check_cancelled():
                log_callback("Operation cancelled by user")
                return
            progress_callback(i + 1, 10, f"Processing item {i + 1}/10")
            time.sleep(0.5)
        
        log_callback("✅ Sorting completed successfully")
    
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
    
    def operation_finished(self, success: bool, message: str):
        """Handle operation completion."""
        self.set_operation_running(False)
        
        if success:
            self.log(f"✅ {message}")
            QMessageBox.information(self, "Success", message)
        else:
            self.log(f"❌ {message}")
            QMessageBox.critical(self, "Error", message)
    
    def log(self, message: str):
        """Add message to log."""
        self.log_text.append(message)
        logger.info(message)
    
    def on_settings_changed(self, setting_key: str, value):
        """Handle settings changes in real-time"""
        try:
            logger.info(f"Setting changed: {setting_key} = {value}")
            
            # Handle theme changes
            if setting_key == "ui.theme":
                self.apply_theme()
            
            # Handle opacity changes
            elif setting_key == "ui.window_opacity":
                self.setWindowOpacity(value)
            
            # Handle tooltip mode changes
            elif setting_key == "ui.tooltip_mode":
                if self.tooltip_manager:
                    from features.tutorial_system import TooltipMode
                    mode_map = {
                        'normal': TooltipMode.NORMAL,
                        'dumbed_down': TooltipMode.DUMBED_DOWN,
                        'vulgar_panda': TooltipMode.UNHINGED_PANDA
                    }
                    if value in mode_map:
                        self.tooltip_manager.set_mode(mode_map[value])
            
            # Handle font changes
            elif setting_key in ["ui.font_family", "ui.font_size"]:
                font_family = config.get('ui', 'font_family', default='Segoe UI')
                font_size = config.get('ui', 'font_size', default=12)
                app = QApplication.instance()
                if app:
                    app.setFont(QFont(font_family, font_size))
            
        except Exception as e:
            logger.error(f"Error handling settings change: {e}", exc_info=True)
    
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
    except Exception:
        pass
    
    # Check ONNX
    try:
        import onnx
        features['onnx'] = True
    except Exception:
        pass
    
    # Check ONNX Runtime
    try:
        import onnxruntime
        features['onnxruntime'] = True
    except Exception:
        pass
    
    # Check transformers
    try:
        import transformers
        features['transformers'] = True
    except Exception:
        pass
    
    # Check open_clip
    try:
        import open_clip
        features['open_clip'] = True
    except Exception:
        pass
    
    # Check timm
    try:
        import timm
        features['timm'] = True
    except Exception:
        pass
    
    # Check Real-ESRGAN upscaling
    try:
        from preprocessing.upscaler import REALESRGAN_AVAILABLE
        features['upscaler'] = REALESRGAN_AVAILABLE
        features['realesrgan'] = REALESRGAN_AVAILABLE  # DEPRECATED: Kept for backward compatibility
    except Exception:
        pass
    
    # Check native Rust Lanczos upscaling
    try:
        from native_ops import NATIVE_AVAILABLE
        features['native_lanczos'] = NATIVE_AVAILABLE
    except Exception:
        pass
    
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
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("JosephsDeadish")
    app.setOrganizationDomain("github.com/JosephsDeadish")
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = TextureSorterMainWindow()
    window.show()
    
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
