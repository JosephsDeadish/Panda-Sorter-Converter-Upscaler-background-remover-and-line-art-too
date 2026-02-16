"""
Image Upscaler UI Panel - PyQt6 Version
Provides UI for upscaling images using various methods (bicubic, lanczos, etc.)
"""

import logging
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
    QComboBox, QSpinBox, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

try:
    from preprocessing.upscaler import TextureUpscaler
    UPSCALER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Upscaler not available: {e}")
    UPSCALER_AVAILABLE = False

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}


class UpscaleWorker(QThread):
    """Worker thread for upscaling images."""
    progress = pyqtSignal(float, str)  # progress, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, upscaler, files, output_dir, scale_factor, method):
        super().__init__()
        self.upscaler = upscaler
        self.files = files
        self.output_dir = output_dir
        self.scale_factor = scale_factor
        self.method = method
        self._is_cancelled = False
    
    def run(self):
        """Execute upscaling in background thread."""
        try:
            total = len(self.files)
            for i, file_path in enumerate(self.files):
                if self._is_cancelled:
                    self.finished.emit(False, "Cancelled")
                    return
                
                # Update progress
                progress = (i / total) * 100
                self.progress.emit(progress, f"Upscaling: {Path(file_path).name}")
                
                # Load image
                img = Image.open(file_path)
                img_array = np.array(img)
                
                # Upscale
                upscaled = self.upscaler.upscale(
                    img_array,
                    scale_factor=self.scale_factor,
                    method=self.method
                )
                
                # Save
                output_path = Path(self.output_dir) / Path(file_path).name
                Image.fromarray(upscaled).save(output_path)
            
            self.finished.emit(True, f"Successfully upscaled {total} images")
        except Exception as e:
            logger.error(f"Upscaling failed: {e}", exc_info=True)
            self.finished.emit(False, f"Upscaling failed: {str(e)}")
    
    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True


class ImageUpscalerPanelQt(QWidget):
    """PyQt6 panel for image upscaling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not UPSCALER_AVAILABLE:
            self._show_unavailable()
            return
        
        self.upscaler = TextureUpscaler()
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.worker_thread = None
        
        self._create_widgets()
    
    def _show_unavailable(self):
        """Show message when upscaler is not available."""
        layout = QVBoxLayout(self)
        label = QLabel(
            "⚠️ Image Upscaler Unavailable\n\n"
            "Required dependencies not installed."
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(14)
        label.setFont(font)
        layout.addWidget(label)
    
    def _create_widgets(self):
        """Create the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("🔍 Image Upscaler")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Upscale images using various interpolation methods")
        subtitle_label.setStyleSheet("color: gray; font-size: 12pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Main container with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        
        # File selection group
        file_group = QGroupBox("📁 File Selection")
        file_layout = QVBoxLayout()
        
        # Select files button
        select_btn_layout = QHBoxLayout()
        self.select_files_btn = QPushButton("Select Files")
        self.select_files_btn.clicked.connect(self._select_files)
        select_btn_layout.addWidget(self.select_files_btn)
        
        self.file_count_label = QLabel("No files selected")
        self.file_count_label.setStyleSheet("color: gray;")
        select_btn_layout.addWidget(self.file_count_label)
        select_btn_layout.addStretch()
        
        file_layout.addLayout(select_btn_layout)
        
        # Output directory button
        output_btn_layout = QHBoxLayout()
        self.select_output_btn = QPushButton("Select Output Directory")
        self.select_output_btn.clicked.connect(self._select_output_directory)
        output_btn_layout.addWidget(self.select_output_btn)
        
        self.output_dir_label = QLabel("No output directory selected")
        self.output_dir_label.setStyleSheet("color: gray;")
        output_btn_layout.addWidget(self.output_dir_label)
        output_btn_layout.addStretch()
        
        file_layout.addLayout(output_btn_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Settings group
        settings_group = QGroupBox("⚙️ Upscaling Settings")
        settings_layout = QVBoxLayout()
        
        # Scale factor
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Scale Factor:"))
        self.scale_spin = QSpinBox()
        self.scale_spin.setMinimum(2)
        self.scale_spin.setMaximum(8)
        self.scale_spin.setValue(4)
        self.scale_spin.setSuffix("x")
        scale_layout.addWidget(self.scale_spin)
        scale_layout.addStretch()
        settings_layout.addLayout(scale_layout)
        
        # Upscaling method
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "bicubic",
            "lanczos",
            "realesrgan",
            "esrgan"
        ])
        self.method_combo.setCurrentText("bicubic")
        method_layout.addWidget(self.method_combo)
        method_layout.addStretch()
        settings_layout.addLayout(method_layout)
        
        # Method description
        self.method_desc_label = QLabel(
            "Bicubic: Fast, good quality for most images"
        )
        self.method_desc_label.setStyleSheet("color: gray; font-size: 10pt;")
        self.method_desc_label.setWordWrap(True)
        self.method_combo.currentTextChanged.connect(self._update_method_description)
        settings_layout.addWidget(self.method_desc_label)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.setVisible(False)
        main_layout.addWidget(self.status_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("🚀 Start Upscaling")
        self.process_btn.clicked.connect(self._start_upscaling)
        self.process_btn.setEnabled(False)
        button_layout.addWidget(self.process_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _update_method_description(self, method):
        """Update the method description based on selection."""
        descriptions = {
            "bicubic": "Bicubic: Fast, good quality for most images",
            "lanczos": "Lanczos: Sharp results, best for textures with fine details (requires native support)",
            "realesrgan": "Real-ESRGAN: Best for retro/PS2 textures, slower (requires model download)",
            "esrgan": "ESRGAN: High quality for general images (not fully implemented)"
        }
        self.method_desc_label.setText(descriptions.get(method, ""))
    
    def _select_files(self):
        """Open file dialog to select input files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images to Upscale",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All Files (*)"
        )
        
        if files:
            self.selected_files = files
            count = len(files)
            self.file_count_label.setText(f"{count} file(s) selected")
            self.file_count_label.setStyleSheet("color: green;")
            self._check_ready()
    
    def _select_output_directory(self):
        """Open directory dialog to select output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        
        if directory:
            self.output_directory = directory
            self.output_dir_label.setText(f"Output: {directory}")
            self.output_dir_label.setStyleSheet("color: green;")
            self._check_ready()
    
    def _check_ready(self):
        """Check if ready to process."""
        ready = bool(self.selected_files and self.output_directory)
        self.process_btn.setEnabled(ready)
    
    def _start_upscaling(self):
        """Start the upscaling process."""
        if not self.selected_files or not self.output_directory:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please select input files and output directory."
            )
            return
        
        # Get settings
        scale_factor = self.scale_spin.value()
        method = self.method_combo.currentText()
        
        # Create output directory if it doesn't exist
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
        
        # Disable UI
        self.process_btn.setEnabled(False)
        self.select_files_btn.setEnabled(False)
        self.select_output_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setVisible(True)
        
        # Show progress
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Processing...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        self.status_label.setVisible(True)
        
        # Start worker thread
        self.worker_thread = UpscaleWorker(
            self.upscaler,
            self.selected_files,
            self.output_directory,
            scale_factor,
            method
        )
        self.worker_thread.progress.connect(self._update_progress)
        self.worker_thread.finished.connect(self._upscaling_finished)
        self.worker_thread.start()
    
    def _cancel_processing(self):
        """Cancel the processing."""
        if self.worker_thread:
            self.worker_thread.cancel()
            self.status_label.setText("Cancelling...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
    
    def _update_progress(self, progress, message):
        """Update progress bar and status."""
        self.progress_bar.setValue(int(progress))
        self.status_label.setText(message)
    
    def _upscaling_finished(self, success, message):
        """Handle upscaling completion."""
        # Re-enable UI
        self.process_btn.setEnabled(True)
        self.select_files_btn.setEnabled(True)
        self.select_output_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        
        # Update status
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.warning(self, "Error", message)
        
        self.worker_thread = None
