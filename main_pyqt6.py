"""
PyQt6 Main Window - Modern UI replacement for CustomTkinter
Provides hardware-accelerated, modern UI with proper threading and styling
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QMenuBar, QMenu, QToolBar, QStatusBar, QTabWidget, QLabel,
        QPushButton, QFileDialog, QMessageBox, QProgressBar, QDockWidget
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
    from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QMainWindow = object
    QWidget = object

logger = logging.getLogger(__name__)


class PyQt6MainWindow(QMainWindow):
    """
    Modern PyQt6 main window replacing CustomTkinter.
    
    Features:
    - Hardware-accelerated rendering
    - Native OS integration
    - Proper threading support
    - CSS-like stylesheets
    - High DPI support
    - Modern dark theme
    - Smooth animations
    """
    
    # Signals for cross-thread communication
    status_message = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)  # current, total
    
    def __init__(self):
        """Initialize PyQt6 main window."""
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for modern UI")
        
        super().__init__()
        
        # Window settings
        self.setWindowTitle("PS2 Texture Sorter - PyQt6")
        self.setGeometry(100, 100, 1400, 900)
        
        # Enable high DPI support
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # Settings persistence
        self.settings = QSettings('JosephsDeadish', 'PS2TextureSorter')
        
        # Setup UI components
        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        self._apply_stylesheet()
        self._restore_state()
        
        # Connect signals
        self.status_message.connect(self._update_status)
        self.progress_update.connect(self._update_progress)
        
        logger.info("PyQt6 main window initialized")
    
    def _setup_ui(self):
        """Setup main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Tab widget for different sections
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        main_layout.addWidget(self.tabs)
        
        # Create initial tabs
        self._create_main_tab()
        self._create_tools_tab()
        self._create_settings_tab()
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
    
    def _create_main_tab(self):
        """Create main sorting tab."""
        main_tab = QWidget()
        layout = QVBoxLayout(main_tab)
        
        # Input section
        input_layout = QHBoxLayout()
        input_label = QLabel("Input Folder:")
        self.input_path_label = QLabel("No folder selected")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_input)
        
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_path_label, 1)
        input_layout.addWidget(browse_button)
        layout.addLayout(input_layout)
        
        # Output section
        output_layout = QHBoxLayout()
        output_label = QLabel("Output Folder:")
        self.output_path_label = QLabel("No folder selected")
        output_browse_button = QPushButton("Browse...")
        output_browse_button.clicked.connect(self._browse_output)
        
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path_label, 1)
        output_layout.addWidget(output_browse_button)
        layout.addLayout(output_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.sort_button = QPushButton("Sort Textures")
        self.sort_button.clicked.connect(self._start_sorting)
        self.sort_button.setMinimumHeight(40)
        
        self.classify_button = QPushButton("Classify Only")
        self.classify_button.clicked.connect(self._start_classification)
        self.classify_button.setMinimumHeight(40)
        
        button_layout.addWidget(self.sort_button)
        button_layout.addWidget(self.classify_button)
        layout.addLayout(button_layout)
        
        # Stretch to push everything to top
        layout.addStretch()
        
        self.tabs.addTab(main_tab, "Main")
    
    def _create_tools_tab(self):
        """Create tools tab."""
        tools_tab = QWidget()
        layout = QVBoxLayout(tools_tab)
        
        # Placeholder for tools
        label = QLabel("Tool panels will be added here")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        self.tabs.addTab(tools_tab, "Tools")
    
    def _create_settings_tab(self):
        """Create settings tab."""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # Placeholder for settings
        label = QLabel("Settings will be added here")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        self.tabs.addTab(settings_tab, "Settings")
    
    def _setup_menubar(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Folder...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._browse_input)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        lineart_action = QAction("Line Art Converter", self)
        lineart_action.triggered.connect(lambda: self._show_tool("lineart"))
        tools_menu.addAction(lineart_action)
        
        bg_remove_action = QAction("Background Remover", self)
        bg_remove_action.triggered.connect(lambda: self._show_tool("bg_remove"))
        tools_menu.addAction(bg_remove_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        dark_mode_action = QAction("Toggle Dark Mode", self)
        dark_mode_action.setCheckable(True)
        dark_mode_action.setChecked(True)
        dark_mode_action.triggered.connect(self._toggle_dark_mode)
        view_menu.addAction(dark_mode_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add common actions
        open_action = QAction("Open", self)
        open_action.triggered.connect(self._browse_input)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        sort_action = QAction("Sort", self)
        sort_action.triggered.connect(self._start_sorting)
        toolbar.addAction(sort_action)
    
    def _setup_statusbar(self):
        """Setup status bar."""
        self.statusbar = self.statusBar()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.statusbar.addWidget(self.status_label)
        
        # Progress indicator (for long operations)
        self.statusbar_progress = QProgressBar()
        self.statusbar_progress.setMaximumWidth(200)
        self.statusbar_progress.setVisible(False)
        self.statusbar.addPermanentWidget(self.statusbar_progress)
    
    def _apply_stylesheet(self):
        """Apply modern dark theme stylesheet."""
        stylesheet = """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }
        
        QPushButton {
            background-color: #0d7377;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #14a085;
        }
        
        QPushButton:pressed {
            background-color: #0a5a5c;
        }
        
        QPushButton:disabled {
            background-color: #555555;
            color: #999999;
        }
        
        QLabel {
            color: #ffffff;
            background-color: transparent;
        }
        
        QTabWidget::pane {
            border: 1px solid #333333;
            background-color: #252525;
        }
        
        QTabBar::tab {
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 8px 20px;
            border: 1px solid #333333;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: #0d7377;
        }
        
        QTabBar::tab:hover {
            background-color: #3d3d3d;
        }
        
        QMenuBar {
            background-color: #2d2d2d;
            color: #ffffff;
            border-bottom: 1px solid #333333;
        }
        
        QMenuBar::item:selected {
            background-color: #0d7377;
        }
        
        QMenu {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #333333;
        }
        
        QMenu::item:selected {
            background-color: #0d7377;
        }
        
        QToolBar {
            background-color: #2d2d2d;
            border-bottom: 1px solid #333333;
            spacing: 3px;
            padding: 4px;
        }
        
        QStatusBar {
            background-color: #2d2d2d;
            color: #ffffff;
            border-top: 1px solid #333333;
        }
        
        QProgressBar {
            border: 1px solid #333333;
            border-radius: 4px;
            text-align: center;
            background-color: #252525;
            color: #ffffff;
        }
        
        QProgressBar::chunk {
            background-color: #0d7377;
            border-radius: 3px;
        }
        """
        
        self.setStyleSheet(stylesheet)
    
    def _restore_state(self):
        """Restore window state from settings."""
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.value('windowState')
        if state:
            self.restoreState(state)
    
    def _save_state(self):
        """Save window state to settings."""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
    
    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    def _browse_input(self):
        """Browse for input folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Input Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.input_path_label.setText(folder)
            self.status_message.emit(f"Input folder selected: {folder}")
    
    def _browse_output(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.output_path_label.setText(folder)
            self.status_message.emit(f"Output folder selected: {folder}")
    
    def _start_sorting(self):
        """Start texture sorting."""
        input_path = self.input_path_label.text()
        output_path = self.output_path_label.text()
        
        if input_path == "No folder selected":
            QMessageBox.warning(self, "Warning", "Please select an input folder")
            return
        
        if output_path == "No folder selected":
            QMessageBox.warning(self, "Warning", "Please select an output folder")
            return
        
        # Placeholder for actual sorting logic
        self.status_message.emit("Starting texture sorting...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # In real implementation, this would start a worker thread
        QMessageBox.information(self, "Info", "Sorting functionality will be integrated here")
    
    def _start_classification(self):
        """Start texture classification."""
        self.status_message.emit("Starting classification...")
        QMessageBox.information(self, "Info", "Classification functionality will be integrated here")
    
    def _show_tool(self, tool_name: str):
        """Show tool panel."""
        self.status_message.emit(f"Opening {tool_name} tool...")
        # Placeholder for tool panels
    
    def _toggle_dark_mode(self, checked: bool):
        """Toggle dark mode."""
        if checked:
            self._apply_stylesheet()
        else:
            self.setStyleSheet("")  # Use default style
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About PS2 Texture Sorter",
            "PS2 Texture Sorter - PyQt6 Edition\n\n"
            "Modern, hardware-accelerated UI for texture sorting\n\n"
            "Author: Dead On The Inside / JosephsDeadish"
        )
    
    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_label.setText(message)
    
    def _update_progress(self, current: int, total: int):
        """Update progress bar."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.statusbar_progress.setValue(percentage)
    
    # ========================================================================
    # Window Events
    # ========================================================================
    
    def closeEvent(self, event):
        """Handle window close event."""
        self._save_state()
        event.accept()


def create_pyqt_application():
    """
    Create and run PyQt6 application.
    
    Returns:
        Exit code
    """
    if not PYQT_AVAILABLE:
        print("PyQt6 is not available. Install with: pip install PyQt6")
        return 1
    
    # Create application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("PS2 Texture Sorter")
    app.setOrganizationName("JosephsDeadish")
    app.setOrganizationDomain("github.com/JosephsDeadish")
    
    # Enable high DPI support
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    # Create main window
    window = PyQt6MainWindow()
    window.show()
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(create_pyqt_application())
