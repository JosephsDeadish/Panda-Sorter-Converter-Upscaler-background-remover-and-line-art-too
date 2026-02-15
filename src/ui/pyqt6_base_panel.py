"""
PyQt6 Base Panel - Base class for all PyQt6 panels
Provides common functionality for tool panels
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from typing import Optional, Callable

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QSpinBox, QDoubleSpinBox, QSlider, QCheckBox,
        QComboBox, QGroupBox, QScrollArea, QFileDialog, QProgressBar
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QThread
    from PyQt6.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QWidget = object

logger = logging.getLogger(__name__)


class BasePyQtPanel(QWidget):
    """
    Base class for all PyQt6 panels.
    
    Provides common functionality:
    - Consistent styling
    - Signal/slot connections
    - Progress tracking
    - Thread management
    - Error handling
    """
    
    # Signals
    status_changed = pyqtSignal(str)
    progress_changed = pyqtSignal(int, int)  # current, total
    operation_complete = pyqtSignal()
    operation_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize base panel."""
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required")
        
        super().__init__(parent)
        
        # Worker thread for background operations
        self.worker_thread: Optional[QThread] = None
        
        # Setup UI
        self._setup_base_ui()
        
        # Connect signals
        self.status_changed.connect(self._on_status_changed)
        self.progress_changed.connect(self._on_progress_changed)
        self.operation_complete.connect(self._on_operation_complete)
        self.operation_error.connect(self._on_operation_error)
    
    def _setup_base_ui(self):
        """Setup base UI structure."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Title
        self.title_label = QLabel("Panel Title")
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.main_layout.addWidget(self.title_label)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self.content_widget)
        
        self.main_layout.addWidget(scroll)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888888;")
        self.main_layout.addWidget(self.status_label)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def set_title(self, title: str):
        """Set panel title."""
        self.title_label.setText(title)
    
    def add_section(self, title: str, layout=None) -> QGroupBox:
        """
        Add a titled section to the panel.
        
        Args:
            title: Section title
            layout: Optional layout (defaults to VBoxLayout)
            
        Returns:
            QGroupBox for the section
        """
        group = QGroupBox(title)
        if layout is None:
            layout = QVBoxLayout()
        group.setLayout(layout)
        self.content_layout.addWidget(group)
        return group
    
    def add_stretch(self):
        """Add stretch to push content to top."""
        self.content_layout.addStretch()
    
    def show_progress(self, visible: bool = True):
        """Show or hide progress bar."""
        self.progress_bar.setVisible(visible)
    
    def set_progress(self, current: int, total: int):
        """
        Set progress.
        
        Args:
            current: Current progress
            total: Total items
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_changed.emit(current, total)
    
    def set_status(self, message: str):
        """Set status message."""
        self.status_label.setText(message)
        self.status_changed.emit(message)
    
    def clear_status(self):
        """Clear status message."""
        self.status_label.setText("")
    
    # ========================================================================
    # File Dialog Helpers
    # ========================================================================
    
    def browse_file(self, title: str = "Select File", 
                   file_filter: str = "All Files (*)") -> Optional[str]:
        """
        Show file selection dialog.
        
        Args:
            title: Dialog title
            file_filter: File filter string
            
        Returns:
            Selected file path or None
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            file_filter
        )
        return file_path if file_path else None
    
    def browse_files(self, title: str = "Select Files",
                    file_filter: str = "All Files (*)") -> list:
        """
        Show multiple file selection dialog.
        
        Args:
            title: Dialog title
            file_filter: File filter string
            
        Returns:
            List of selected file paths
        """
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            title,
            "",
            file_filter
        )
        return file_paths
    
    def browse_folder(self, title: str = "Select Folder") -> Optional[str]:
        """
        Show folder selection dialog.
        
        Args:
            title: Dialog title
            
        Returns:
            Selected folder path or None
        """
        folder_path = QFileDialog.getExistingDirectory(
            self,
            title,
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        return folder_path if folder_path else None
    
    def save_file(self, title: str = "Save File",
                 file_filter: str = "All Files (*)") -> Optional[str]:
        """
        Show save file dialog.
        
        Args:
            title: Dialog title
            file_filter: File filter string
            
        Returns:
            Selected file path or None
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            "",
            file_filter
        )
        return file_path if file_path else None
    
    # ========================================================================
    # Widget Creation Helpers
    # ========================================================================
    
    def create_labeled_widget(self, label_text: str, widget: QWidget) -> QHBoxLayout:
        """
        Create a horizontal layout with label and widget.
        
        Args:
            label_text: Label text
            widget: Widget to place next to label
            
        Returns:
            QHBoxLayout containing label and widget
        """
        layout = QHBoxLayout()
        label = QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        return layout
    
    def create_button_row(self, *button_configs) -> QHBoxLayout:
        """
        Create a row of buttons.
        
        Args:
            *button_configs: Tuples of (text, callback)
            
        Returns:
            QHBoxLayout containing buttons
        """
        layout = QHBoxLayout()
        for text, callback in button_configs:
            button = QPushButton(text)
            button.clicked.connect(callback)
            layout.addWidget(button)
        return layout
    
    # ========================================================================
    # Signal Handlers
    # ========================================================================
    
    def _on_status_changed(self, message: str):
        """Handle status change (override in subclass)."""
        pass
    
    def _on_progress_changed(self, current: int, total: int):
        """Handle progress change (override in subclass)."""
        pass
    
    def _on_operation_complete(self):
        """Handle operation completion (override in subclass)."""
        self.show_progress(False)
    
    def _on_operation_error(self, error: str):
        """Handle operation error (override in subclass)."""
        self.show_progress(False)
        logger.error(f"Operation error: {error}")
    
    # ========================================================================
    # Thread Management
    # ========================================================================
    
    def start_worker(self, worker_func: Callable, *args, **kwargs):
        """
        Start a worker thread for background operations.
        
        Args:
            worker_func: Function to run in background
            *args: Arguments for worker function
            **kwargs: Keyword arguments for worker function
        """
        # TODO: Implement proper worker thread management
        # This is a placeholder for the threading system
        pass
    
    def stop_worker(self):
        """Stop the worker thread if running."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()


class ExamplePanel(BasePyQtPanel):
    """Example panel demonstrating BasePyQtPanel usage."""
    
    def __init__(self, parent=None):
        """Initialize example panel."""
        super().__init__(parent)
        self.set_title("Example Tool Panel")
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup panel-specific UI."""
        # Input section
        input_section = self.add_section("Input")
        input_layout = input_section.layout()
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("No file selected")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_input_file)
        
        file_layout.addWidget(QLabel("Input File:"))
        file_layout.addWidget(self.file_input, 1)
        file_layout.addWidget(browse_btn)
        input_layout.addLayout(file_layout)
        
        # Settings section
        settings_section = self.add_section("Settings")
        settings_layout = settings_section.layout()
        
        # Slider example
        slider_layout = QHBoxLayout()
        self.value_slider = QSlider(Qt.Orientation.Horizontal)
        self.value_slider.setRange(0, 100)
        self.value_slider.setValue(50)
        self.value_label = QLabel("50")
        self.value_slider.valueChanged.connect(
            lambda v: self.value_label.setText(str(v))
        )
        
        slider_layout.addWidget(QLabel("Value:"))
        slider_layout.addWidget(self.value_slider, 1)
        slider_layout.addWidget(self.value_label)
        settings_layout.addLayout(slider_layout)
        
        # Checkbox example
        self.enable_option = QCheckBox("Enable Option")
        settings_layout.addWidget(self.enable_option)
        
        # Actions section
        actions_section = self.add_section("Actions")
        actions_layout = actions_section.layout()
        
        # Button row
        button_layout = self.create_button_row(
            ("Process", self._process),
            ("Reset", self._reset)
        )
        actions_layout.addLayout(button_layout)
        
        # Add stretch at bottom
        self.add_stretch()
    
    def _browse_input_file(self):
        """Browse for input file."""
        file_path = self.browse_file(
            "Select Input File",
            "Images (*.png *.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            self.file_input.setText(file_path)
            self.set_status(f"Selected: {file_path}")
    
    def _process(self):
        """Process example."""
        self.show_progress(True)
        self.set_status("Processing...")
        
        # Simulate progress
        for i in range(101):
            self.set_progress(i, 100)
        
        self.set_status("Processing complete!")
        self.operation_complete.emit()
    
    def _reset(self):
        """Reset panel."""
        self.file_input.clear()
        self.value_slider.setValue(50)
        self.enable_option.setChecked(False)
        self.clear_status()
        self.show_progress(False)


if __name__ == "__main__":
    """Test the base panel."""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Apply dark theme
    app.setStyleSheet("""
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QPushButton {
            background-color: #0d7377;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #14a085;
        }
    """)
    
    panel = ExamplePanel()
    panel.resize(600, 400)
    panel.show()
    
    sys.exit(app.exec())
