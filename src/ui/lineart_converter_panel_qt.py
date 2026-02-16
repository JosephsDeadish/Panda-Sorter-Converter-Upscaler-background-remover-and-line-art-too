"""
Line Art Converter UI Panel - PyQt6 Version
Provides UI for converting images to line art and stencils
"""

import logging
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QComboBox,
    QSlider, QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox,
    QScrollArea, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image

from tools.lineart_converter import (
    LineArtConverter, LineArtSettings,
    ConversionMode, BackgroundMode, MorphologyOperation
)

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}

# Line art presets
LINEART_PRESETS = {
    "⭐ Clean Ink Lines": {
        "desc": "Crisp black ink lines — the go-to for most art & game textures",
        "mode": "pure_black", "threshold": 135, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 210, "contrast": 1.6, "sharpen": True,
        "sharpen_amount": 1.3, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
    },
    "✏️ Pencil Sketch": {
        "desc": "Soft graphite pencil look with natural tonal gradation",
        "mode": "sketch", "threshold": 140, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": False,
        "midtone_threshold": 200, "contrast": 1.1, "sharpen": False,
        "sharpen_amount": 1.0, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 1,
    },
    "🖊️ Bold Outlines": {
        "desc": "Thick, punchy outlines — great for stickers or cartoon style",
        "mode": "pure_black", "threshold": 145, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 170, "contrast": 2.2, "sharpen": True,
        "sharpen_amount": 1.6, "morphology": "dilate", "morph_iter": 3,
        "kernel": 5, "denoise": True, "denoise_size": 4,
    },
    "💥 Comic Book Inks": {
        "desc": "High-contrast inks like professional comic book art",
        "mode": "pure_black", "threshold": 115, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 185, "contrast": 2.7, "sharpen": True,
        "sharpen_amount": 2.0, "morphology": "close", "morph_iter": 2,
        "kernel": 3, "denoise": True, "denoise_size": 3,
    },
    "📖 Manga Lines": {
        "desc": "Clean adaptive lines suited for manga / anime styles",
        "mode": "adaptive", "threshold": 130, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 215, "contrast": 1.7, "sharpen": True,
        "sharpen_amount": 1.5, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
    },
}


class PreviewWorker(QThread):
    """Worker thread for generating preview."""
    finished = pyqtSignal(object, object)  # original, processed
    error = pyqtSignal(str)
    
    def __init__(self, converter, image_path, settings):
        super().__init__()
        self.converter = converter
        self.image_path = image_path
        self.settings = settings
        self._should_cancel = False
    
    def run(self):
        """Generate preview in background."""
        try:
            if self._should_cancel:
                return
            
            # Load and convert
            original = Image.open(self.image_path)
            processed = self.converter.convert(original, self.settings)
            
            if not self._should_cancel:
                self.finished.emit(original, processed)
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            self.error.emit(str(e))
    
    def cancel(self):
        """Cancel the preview generation."""
        self._should_cancel = True


class ConversionWorker(QThread):
    """Worker thread for batch conversion."""
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, converter, files, output_dir, settings):
        super().__init__()
        self.converter = converter
        self.files = files
        self.output_dir = output_dir
        self.settings = settings
    
    def run(self):
        """Execute conversion in background."""
        try:
            for i, filepath in enumerate(self.files):
                filename = Path(filepath).name
                self.progress.emit(i + 1, len(self.files), filename)
                
                # Load, convert, save
                image = Image.open(filepath)
                converted = self.converter.convert(image, self.settings)
                
                output_path = Path(self.output_dir) / filename
                converted.save(output_path)
            
            self.finished.emit(True, f"Successfully converted {len(self.files)} images")
        except Exception as e:
            logger.error(f"Batch conversion failed: {e}")
            self.finished.emit(False, f"Conversion failed: {str(e)}")


class LineArtConverterPanelQt(QWidget):
    """PyQt6 panel for line art conversion."""
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.converter = LineArtConverter()
        self.selected_file = None
        self.selected_files: List[str] = []
        self.preview_worker = None
        self.conversion_worker = None
        
        # Debounce timer for preview updates
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._update_preview)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("✏️ Line Art Converter")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Convert images to line art with various artistic styles")
        subtitle_label.setStyleSheet("color: gray; font-size: 11pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Main container with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        main_layout = QHBoxLayout(container)
        
        # Left side - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self._create_file_section(left_layout)
        self._create_preset_section(left_layout)
        self._create_settings_section(left_layout)
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
    
    def _create_file_section(self, layout):
        """Create file selection section."""
        group = QGroupBox("📁 Select Image")
        group_layout = QVBoxLayout()
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.file_label)
        
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Select Image")
        select_btn.clicked.connect(self._select_file)
        btn_layout.addWidget(select_btn)
        
        select_multiple_btn = QPushButton("Select Multiple")
        select_multiple_btn.clicked.connect(self._select_files)
        btn_layout.addWidget(select_multiple_btn)
        
        group_layout.addLayout(btn_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_preset_section(self, layout):
        """Create preset selection section."""
        group = QGroupBox("🎨 Presets")
        group_layout = QVBoxLayout()
        
        self.preset_combo = QComboBox()
        for preset_name in LINEART_PRESETS.keys():
            self.preset_combo.addItem(preset_name)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        group_layout.addWidget(self.preset_combo)
        
        # Preset description
        self.preset_desc = QLabel("")
        self.preset_desc.setWordWrap(True)
        self.preset_desc.setStyleSheet("color: gray; font-size: 10pt;")
        group_layout.addWidget(self.preset_desc)
        
        # Load first preset
        self._on_preset_changed(self.preset_combo.currentText())
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_settings_section(self, layout):
        """Create settings section."""
        group = QGroupBox("⚙️ Settings")
        group_layout = QVBoxLayout()
        
        # Threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Threshold:"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(135)
        self.threshold_slider.valueChanged.connect(self._schedule_preview_update)
        threshold_layout.addWidget(self.threshold_slider)
        self.threshold_label = QLabel("135")
        self.threshold_slider.valueChanged.connect(lambda v: self.threshold_label.setText(str(v)))
        threshold_layout.addWidget(self.threshold_label)
        group_layout.addLayout(threshold_layout)
        
        # Contrast
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Contrast:"))
        self.contrast_spin = QDoubleSpinBox()
        self.contrast_spin.setRange(0.5, 5.0)
        self.contrast_spin.setSingleStep(0.1)
        self.contrast_spin.setValue(1.6)
        self.contrast_spin.valueChanged.connect(self._schedule_preview_update)
        contrast_layout.addWidget(self.contrast_spin)
        contrast_layout.addStretch()
        group_layout.addLayout(contrast_layout)
        
        # Checkboxes
        self.auto_threshold_cb = QCheckBox("Auto Threshold")
        self.auto_threshold_cb.stateChanged.connect(self._schedule_preview_update)
        group_layout.addWidget(self.auto_threshold_cb)
        
        self.sharpen_cb = QCheckBox("Sharpen")
        self.sharpen_cb.setChecked(True)
        self.sharpen_cb.stateChanged.connect(self._schedule_preview_update)
        group_layout.addWidget(self.sharpen_cb)
        
        self.denoise_cb = QCheckBox("Denoise")
        self.denoise_cb.setChecked(True)
        self.denoise_cb.stateChanged.connect(self._schedule_preview_update)
        group_layout.addWidget(self.denoise_cb)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_preview_section(self, layout):
        """Create preview section."""
        group = QGroupBox("👁️ Preview")
        group_layout = QVBoxLayout()
        
        # Preview label
        self.preview_label = QLabel("Select an image to see preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setStyleSheet("border: 2px dashed gray; background-color: #f0f0f0;")
        group_layout.addWidget(self.preview_label)
        
        # Update preview button
        self.update_preview_btn = QPushButton("🔄 Update Preview")
        self.update_preview_btn.clicked.connect(self._schedule_preview_update)
        group_layout.addWidget(self.update_preview_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        # Convert button
        self.convert_button = QPushButton("🚀 Convert Selected Files")
        self.convert_button.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        self.convert_button.clicked.connect(self._convert_batch)
        layout.addWidget(self.convert_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: gray;")
        layout.addWidget(self.progress_label)
    
    def _select_file(self):
        """Select single file for preview."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All Files (*.*)"
        )
        
        if filename:
            self.selected_file = filename
            self.selected_files = [filename]
            self.file_label.setText(Path(filename).name)
            self.file_label.setStyleSheet("color: green; font-weight: bold;")
            self._schedule_preview_update()
    
    def _select_files(self):
        """Select multiple files for batch conversion."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All Files (*.*)"
        )
        
        if files:
            self.selected_files = files
            self.selected_file = files[0]
            self.file_label.setText(f"{len(files)} files selected")
            self.file_label.setStyleSheet("color: green; font-weight: bold;")
            self._schedule_preview_update()
    
    def _on_preset_changed(self, preset_name):
        """Handle preset selection."""
        if preset_name in LINEART_PRESETS:
            preset = LINEART_PRESETS[preset_name]
            self.preset_desc.setText(preset["desc"])
            
            # Update controls
            self.threshold_slider.setValue(preset["threshold"])
            self.contrast_spin.setValue(preset["contrast"])
            self.auto_threshold_cb.setChecked(preset["auto_threshold"])
            self.sharpen_cb.setChecked(preset["sharpen"])
            self.denoise_cb.setChecked(preset["denoise"])
            
            # Trigger preview update
            self._schedule_preview_update()
    
    def _schedule_preview_update(self):
        """Schedule preview update with debouncing."""
        # Cancel any pending preview
        if self.preview_worker and self.preview_worker.isRunning():
            self.preview_worker.cancel()
        
        # Restart debounce timer (800ms delay)
        self.preview_timer.stop()
        self.preview_timer.start(800)
    
    def _update_preview(self):
        """Update the preview image."""
        if not self.selected_file:
            return
        
        try:
            # Create settings from current controls
            settings = LineArtSettings(
                mode=ConversionMode.PURE_BLACK,
                threshold=self.threshold_slider.value(),
                auto_threshold=self.auto_threshold_cb.isChecked(),
                background_mode=BackgroundMode.TRANSPARENT,
                invert=False,
                remove_midtones=True,
                midtone_threshold=210,
                contrast_boost=self.contrast_spin.value(),
                sharpen=self.sharpen_cb.isChecked(),
                sharpen_amount=1.3,
                morphology_op=MorphologyOperation.CLOSE,
                morphology_iterations=1,
                kernel_size=3,
                denoise=self.denoise_cb.isChecked(),
                denoise_kernel_size=2
            )
            
            # Start preview worker
            self.preview_worker = PreviewWorker(self.converter, self.selected_file, settings)
            self.preview_worker.finished.connect(self._display_preview)
            self.preview_worker.error.connect(self._preview_error)
            self.preview_worker.start()
            
            self.update_preview_btn.setEnabled(False)
            self.update_preview_btn.setText("Generating...")
            
        except Exception as e:
            logger.error(f"Error starting preview: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start preview: {str(e)}")
    
    def _display_preview(self, original, processed):
        """Display the preview image."""
        try:
            # Convert to QPixmap
            processed_rgb = processed.convert("RGBA")
            data = processed_rgb.tobytes("raw", "RGBA")
            qimage = QImage(data, processed_rgb.width, processed_rgb.height, QImage.Format.Format_RGBA8888)
            
            # Scale to fit preview
            pixmap = QPixmap.fromImage(qimage)
            scaled = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            self.preview_label.setPixmap(scaled)
            
        except Exception as e:
            logger.error(f"Error displaying preview: {e}")
            self.preview_label.setText(f"Error: {str(e)}")
        finally:
            self.update_preview_btn.setEnabled(True)
            self.update_preview_btn.setText("🔄 Update Preview")
    
    def _preview_error(self, error_msg):
        """Handle preview error."""
        self.preview_label.setText(f"Error: {error_msg}")
        self.update_preview_btn.setEnabled(True)
        self.update_preview_btn.setText("🔄 Update Preview")
    
    def _convert_batch(self):
        """Convert selected files in batch."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files first")
            return
        
        # Select output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        
        if not output_dir:
            return
        
        try:
            # Create settings
            settings = LineArtSettings(
                mode=ConversionMode.PURE_BLACK,
                threshold=self.threshold_slider.value(),
                auto_threshold=self.auto_threshold_cb.isChecked(),
                background_mode=BackgroundMode.TRANSPARENT,
                invert=False,
                remove_midtones=True,
                midtone_threshold=210,
                contrast_boost=self.contrast_spin.value(),
                sharpen=self.sharpen_cb.isChecked(),
                sharpen_amount=1.3,
                morphology_op=MorphologyOperation.CLOSE,
                morphology_iterations=1,
                kernel_size=3,
                denoise=self.denoise_cb.isChecked(),
                denoise_kernel_size=2
            )
            
            # Start conversion worker
            self.conversion_worker = ConversionWorker(
                self.converter,
                self.selected_files,
                output_dir,
                settings
            )
            self.conversion_worker.progress.connect(self._on_conversion_progress)
            self.conversion_worker.finished.connect(self._on_conversion_finished)
            self.conversion_worker.start()
            
            self.convert_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_label.setText("Starting conversion...")
            
        except Exception as e:
            logger.error(f"Error starting conversion: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start conversion: {str(e)}")
    
    def _on_conversion_progress(self, current, total, filename):
        """Handle conversion progress."""
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"Converting {current}/{total}: {filename}")
    
    def _on_conversion_finished(self, success, message):
        """Handle conversion completion."""
        self.progress_bar.setVisible(False)
        self.convert_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Complete", message)
            self.progress_label.setText("✓ Conversion complete")
        else:
            QMessageBox.critical(self, "Error", message)
            self.progress_label.setText("✗ Conversion failed")
