"""
Batch Normalizer UI Panel - PyQt6 Version
Provides UI for batch format normalization with live preview
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
    QComboBox, QSpinBox, QCheckBox, QLineEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path
from typing import List, Optional
import logging
from PIL import Image

from tools.batch_normalizer import (
    BatchFormatNormalizer, NormalizationSettings,
    PaddingMode, ResizeMode, OutputFormat, NamingPattern
)

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}


class NormalizationWorker(QThread):
    """Worker thread for batch normalization."""
    progress = pyqtSignal(float, str)  # progress, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, normalizer, files, output_dir, settings):
        super().__init__()
        self.normalizer = normalizer
        self.files = files
        self.output_dir = output_dir
        self.settings = settings
    
    def run(self):
        """Execute normalization in background thread."""
        try:
            def progress_callback(current, total, filename):
                progress = (current / total) * 100
                self.progress.emit(progress, f"Processing: {filename}")
            
            self.normalizer.normalize_batch(
                self.files,
                self.output_dir,
                self.settings,
                progress_callback=progress_callback
            )
            
            self.finished.emit(True, f"Successfully normalized {len(self.files)} images")
        except Exception as e:
            self.finished.emit(False, f"Normalization failed: {str(e)}")


class BatchNormalizerPanelQt(QWidget):
    """PyQt6 panel for batch format normalization."""
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.normalizer = BatchFormatNormalizer()
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.worker_thread = None
        self.preview_pixmap = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("📏 Batch Format Normalizer")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Resize, pad, and normalize images to consistent format")
        subtitle_label.setStyleSheet("color: gray; font-size: 12pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Main container with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        main_layout = QHBoxLayout(container)
        
        # Left side - Settings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        
        self._create_file_selection(left_layout)
        self._create_size_settings(left_layout)
        self._create_format_settings(left_layout)
        self._create_naming_settings(left_layout)
        self._create_action_buttons(left_layout)
        
        left_layout.addStretch()
        main_layout.addWidget(left_widget, 1)
        
        # Right side - Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self._create_preview_section(right_layout)
        main_layout.addWidget(right_widget, 1)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _create_file_selection(self, layout):
        """Create file selection section."""
        group = QGroupBox("📁 File Selection")
        group_layout = QVBoxLayout()
        
        # Selected files label
        self.files_label = QLabel("No files selected")
        self.files_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.files_label)
        
        # Select files button
        select_btn = QPushButton("Select Images")
        select_btn.clicked.connect(self._select_files)
        group_layout.addWidget(select_btn)
        
        # Output directory
        output_label = QLabel("Output Directory:")
        group_layout.addWidget(output_label)
        
        self.output_label = QLabel("Not set")
        self.output_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.output_label)
        
        output_btn = QPushButton("Set Output Directory")
        output_btn.clicked.connect(self._select_output)
        group_layout.addWidget(output_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_size_settings(self, layout):
        """Create size settings section."""
        group = QGroupBox("📐 Size Settings")
        group_layout = QVBoxLayout()
        
        # Target size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Target Size:"))
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 8192)
        self.width_spin.setValue(512)
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("×"))
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 8192)
        self.height_spin.setValue(512)
        size_layout.addWidget(self.height_spin)
        
        group_layout.addLayout(size_layout)
        
        # Resize mode
        group_layout.addWidget(QLabel("Resize Mode:"))
        self.resize_combo = QComboBox()
        self.resize_combo.addItems(["Fit (preserve aspect)", "Fill (crop)", "Stretch"])
        group_layout.addWidget(self.resize_combo)
        
        # Padding mode
        group_layout.addWidget(QLabel("Padding Mode:"))
        self.padding_combo = QComboBox()
        self.padding_combo.addItems(["Transparent", "Black", "White", "Blur Edge"])
        group_layout.addWidget(self.padding_combo)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_format_settings(self, layout):
        """Create format settings section."""
        group = QGroupBox("💾 Format Settings")
        group_layout = QVBoxLayout()
        
        # Output format
        group_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "WebP"])
        group_layout.addWidget(self.format_combo)
        
        # Quality (for JPEG/WebP)
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        quality_layout.addWidget(self.quality_spin)
        group_layout.addLayout(quality_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_naming_settings(self, layout):
        """Create naming settings section."""
        group = QGroupBox("🏷️ Naming Settings")
        group_layout = QVBoxLayout()
        
        # Naming pattern
        group_layout.addWidget(QLabel("Naming Pattern:"))
        self.naming_combo = QComboBox()
        self.naming_combo.addItems(["Keep Original", "Sequential", "Custom Prefix"])
        group_layout.addWidget(self.naming_combo)
        
        # Custom prefix (optional)
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Prefix:"))
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("Optional prefix")
        prefix_layout.addWidget(self.prefix_edit)
        group_layout.addLayout(prefix_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        buttons_layout = QHBoxLayout()
        
        # Normalize button
        self.normalize_btn = QPushButton("🚀 Start Normalization")
        self.normalize_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
        self.normalize_btn.clicked.connect(self._start_normalization)
        buttons_layout.addWidget(self.normalize_btn)
        
        layout.addLayout(buttons_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: gray;")
        layout.addWidget(self.progress_label)
    
    def _create_preview_section(self, layout):
        """Create preview section."""
        group = QGroupBox("👁️ Preview")
        group_layout = QVBoxLayout()
        
        # Preview label
        self.preview_label = QLabel("Select files to see preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setStyleSheet("border: 2px dashed gray; background-color: #f0f0f0;")
        group_layout.addWidget(self.preview_label)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.info_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _select_files(self):
        """Open file dialog to select images."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All Files (*.*)"
        )
        
        if files:
            self.selected_files = files
            self.files_label.setText(f"{len(files)} files selected")
            self.files_label.setStyleSheet("color: green;")
            self._update_preview()
    
    def _select_output(self):
        """Select output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        
        if directory:
            self.output_directory = directory
            self.output_label.setText(directory)
            self.output_label.setStyleSheet("color: green;")
    
    def _update_preview(self):
        """Update preview with first selected image."""
        if not self.selected_files:
            return
        
        try:
            # Load first image
            first_file = self.selected_files[0]
            image = Image.open(first_file)
            
            # Resize for preview
            image.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            data = image.convert("RGBA").tobytes("raw", "RGBA")
            qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            
            self.preview_label.setPixmap(pixmap)
            self.info_label.setText(f"Original: {Image.open(first_file).size[0]}×{Image.open(first_file).size[1]}")
        except Exception as e:
            self.preview_label.setText(f"Error loading preview: {str(e)}")
    
    def _start_normalization(self):
        """Start the normalization process."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to normalize")
            return
        
        if not self.output_directory:
            QMessageBox.warning(self, "No Output", "Please select an output directory")
            return
        
        # Create settings
        settings = NormalizationSettings(
            target_width=self.width_spin.value(),
            target_height=self.height_spin.value(),
            resize_mode=self._get_resize_mode(),
            padding_mode=self._get_padding_mode(),
            output_format=self._get_output_format(),
            quality=self.quality_spin.value(),
            naming_pattern=self._get_naming_pattern(),
            prefix=self.prefix_edit.text() if self.prefix_edit.text() else None
        )
        
        # Disable button
        self.normalize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting...")
        
        # Start worker thread
        self.worker_thread = NormalizationWorker(
            self.normalizer,
            self.selected_files,
            self.output_directory,
            settings
        )
        self.worker_thread.progress.connect(self._on_progress)
        self.worker_thread.finished.connect(self._on_finished)
        self.worker_thread.start()
    
    def _on_progress(self, progress, message):
        """Handle progress updates."""
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(message)
    
    def _on_finished(self, success, message):
        """Handle completion."""
        self.progress_bar.setVisible(False)
        self.normalize_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Complete", message)
            self.progress_label.setText("✓ Normalization complete")
        else:
            QMessageBox.critical(self, "Error", message)
            self.progress_label.setText("✗ Normalization failed")
    
    def _get_resize_mode(self):
        """Get resize mode from combo box."""
        modes = {
            0: ResizeMode.FIT,
            1: ResizeMode.FILL,
            2: ResizeMode.STRETCH
        }
        return modes.get(self.resize_combo.currentIndex(), ResizeMode.FIT)
    
    def _get_padding_mode(self):
        """Get padding mode from combo box."""
        modes = {
            0: PaddingMode.TRANSPARENT,
            1: PaddingMode.BLACK,
            2: PaddingMode.WHITE,
            3: PaddingMode.BLUR_EDGE
        }
        return modes.get(self.padding_combo.currentIndex(), PaddingMode.TRANSPARENT)
    
    def _get_output_format(self):
        """Get output format from combo box."""
        formats = {
            0: OutputFormat.PNG,
            1: OutputFormat.JPEG,
            2: OutputFormat.WEBP
        }
        return formats.get(self.format_combo.currentIndex(), OutputFormat.PNG)
    
    def _get_naming_pattern(self):
        """Get naming pattern from combo box."""
        patterns = {
            0: NamingPattern.KEEP_ORIGINAL,
            1: NamingPattern.SEQUENTIAL,
            2: NamingPattern.CUSTOM_PREFIX
        }
        return patterns.get(self.naming_combo.currentIndex(), NamingPattern.KEEP_ORIGINAL)
