"""
Color Correction Panel UI - PyQt6 Version

Pure PyQt6 implementation with NO tkinter .after() calls.
Uses Qt signals/slots for threading and UI updates.
"""

import logging
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSlider, QSpinBox, QFileDialog,
    QMessageBox, QProgressBar, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap
from PIL import Image

logger = logging.getLogger(__name__)

try:
    from src.tools.color_corrector import ColorCorrector
    COLOR_CORRECTOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Color corrector not available: {e}")
    COLOR_CORRECTOR_AVAILABLE = False


class ColorCorrectionWorker(QThread):
    """Worker thread for color correction processing."""
    
    progress_updated = pyqtSignal(int, str)  # progress, status
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, corrector, input_files, output_dir, settings):
        super().__init__()
        self.corrector = corrector
        self.input_files = input_files
        self.output_dir = output_dir
        self.settings = settings
        self._is_cancelled = False
    
    def run(self):
        """Run color correction in background thread."""
        try:
            total = len(self.input_files)
            for i, file_path in enumerate(self.input_files):
                if self._is_cancelled:
                    self.finished.emit(False, "Cancelled")
                    return
                
                # Update progress
                progress = int((i / total) * 100)
                self.progress_updated.emit(progress, f"Processing {file_path.name}...")
                
                # Process file
                output_path = Path(self.output_dir) / file_path.name
                self.corrector.correct_file(
                    str(file_path),
                    str(output_path),
                    **self.settings
                )
            
            self.finished.emit(True, f"✅ Corrected {total} images successfully!")
        
        except Exception as e:
            logger.error(f"Color correction failed: {e}")
            self.finished.emit(False, f"❌ Error: {str(e)}")
    
    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True


class ColorCorrectionPanelQt(QWidget):
    """PyQt6 panel for color correction and enhancement."""
    
    def __init__(self, parent=None, unlockables_system=None, tooltip_manager=None):
        super().__init__(parent)
        
        if not COLOR_CORRECTOR_AVAILABLE:
            self._show_unavailable()
            return
        
        self.unlockables_system = unlockables_system
        self.tooltip_manager = tooltip_manager
        self.corrector = ColorCorrector()
        self.input_files = []
        self.output_dir = ""
        self.current_lut = None
        self.worker = None
        
        self._create_ui()
    
    def _show_unavailable(self):
        """Show message when color corrector is not available."""
        layout = QVBoxLayout(self)
        label = QLabel(
            "⚠️ Color Correction Tool Unavailable\n\n"
            "Required dependencies not installed."
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(14)
        label.setFont(font)
        layout.addWidget(label)
    
    def _create_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Title
        title = QLabel("🎨 Color Correction & Enhancement")
        font = title.font()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)
        container_layout.addWidget(title)
        container_layout.addSpacing(20)
        
        # File selection section
        self._create_file_section(container_layout)
        
        # Adjustment controls section
        self._create_controls_section(container_layout)
        
        # Actions section
        self._create_actions_section(container_layout)
        
        container_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _create_file_section(self, layout):
        """Create file selection controls."""
        group = QGroupBox("📁 File Selection")
        group_layout = QVBoxLayout()
        
        # Input files
        input_layout = QHBoxLayout()
        self.input_label = QLabel("No files selected")
        input_layout.addWidget(self.input_label, 1)
        
        self.select_btn = QPushButton("Select Images...")
        self.select_btn.clicked.connect(self._select_files)
        input_layout.addWidget(self.select_btn)
        
        group_layout.addLayout(input_layout)
        
        # Output directory
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output: Not set")
        output_layout.addWidget(self.output_label, 1)
        
        self.output_btn = QPushButton("Set Output...")
        self.output_btn.clicked.connect(self._select_output)
        output_layout.addWidget(self.output_btn)
        
        group_layout.addLayout(output_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_controls_section(self, layout):
        """Create adjustment controls."""
        group = QGroupBox("⚙️ Adjustments")
        group_layout = QVBoxLayout()
        
        # Brightness
        self.brightness_slider = self._create_slider(
            group_layout, "Brightness", -100, 100, 0
        )
        
        # Contrast
        self.contrast_slider = self._create_slider(
            group_layout, "Contrast", -100, 100, 0
        )
        
        # Saturation
        self.saturation_slider = self._create_slider(
            group_layout, "Saturation", -100, 100, 0
        )
        
        # Sharpness
        self.sharpness_slider = self._create_slider(
            group_layout, "Sharpness", 0, 200, 100
        )
        
        # LUT selection
        lut_layout = QHBoxLayout()
        lut_layout.addWidget(QLabel("LUT:"))
        self.lut_combo = QComboBox()
        self.lut_combo.addItems(["None", "Warm", "Cool", "Cinematic", "Vintage"])
        lut_layout.addWidget(self.lut_combo, 1)
        group_layout.addLayout(lut_layout)
        
        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_controls)
        group_layout.addWidget(reset_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_slider(self, layout, label, min_val, max_val, default):
        """Create a labeled slider with value display."""
        row = QHBoxLayout()
        
        label_widget = QLabel(f"{label}:")
        label_widget.setMinimumWidth(80)
        row.addWidget(label_widget)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)
        row.addWidget(slider, 1)
        
        value_label = QLabel(str(default))
        value_label.setMinimumWidth(40)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(value_label)
        
        slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
        
        layout.addLayout(row)
        return slider
    
    def _create_actions_section(self, layout):
        """Create action buttons and progress display."""
        group = QGroupBox("🚀 Actions")
        group_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        group_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        group_layout.addWidget(self.status_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("🎨 Apply Color Correction")
        self.process_btn.clicked.connect(self._start_processing)
        self.process_btn.setEnabled(False)
        btn_layout.addWidget(self.process_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_processing)
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.cancel_btn)
        
        group_layout.addLayout(btn_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _select_files(self):
        """Select input files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)"
        )
        
        if files:
            self.input_files = [Path(f) for f in files]
            self.input_label.setText(f"Selected: {len(self.input_files)} files")
            self._update_ui_state()
    
    def _select_output(self):
        """Select output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        
        if directory:
            self.output_dir = directory
            self.output_label.setText(f"Output: {directory}")
            self._update_ui_state()
    
    def _update_ui_state(self):
        """Update button states based on current state."""
        can_process = (
            len(self.input_files) > 0 and
            self.output_dir and
            self.worker is None
        )
        self.process_btn.setEnabled(can_process)
    
    def _reset_controls(self):
        """Reset all controls to defaults."""
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.saturation_slider.setValue(0)
        self.sharpness_slider.setValue(100)
        self.lut_combo.setCurrentIndex(0)
    
    def _start_processing(self):
        """Start color correction processing."""
        if self.worker is not None:
            return
        
        # Get settings from UI
        settings = {
            'brightness': self.brightness_slider.value(),
            'contrast': self.contrast_slider.value(),
            'saturation': self.saturation_slider.value(),
            'sharpness': self.sharpness_slider.value(),
            'lut': self.lut_combo.currentText() if self.lut_combo.currentIndex() > 0 else None
        }
        
        # Create and start worker
        self.worker = ColorCorrectionWorker(
            self.corrector,
            self.input_files,
            self.output_dir,
            settings
        )
        
        # Connect signals
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        
        # Update UI
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("Starting color correction...")
        
        # Start processing
        self.worker.start()
    
    def _cancel_processing(self):
        """Cancel current processing."""
        if self.worker:
            self.worker.cancel()
            self.status_label.setText("Cancelling...")
            self.cancel_btn.setEnabled(False)
    
    def _on_progress(self, progress, status):
        """Handle progress updates from worker thread."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def _on_finished(self, success, message):
        """Handle completion from worker thread."""
        # Clean up worker
        if self.worker:
            self.worker.wait()
            self.worker = None
        
        # Update UI
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        # Show message
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Error", message)
    
    def cleanup(self):
        """Clean up resources."""
        if self.worker:
            self.worker.cancel()
            self.worker.wait()
            self.worker = None
