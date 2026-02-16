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

try:
    from ui.live_preview_slider_qt import ComparisonSliderWidget
    SLIDER_AVAILABLE = True
except ImportError:
    SLIDER_AVAILABLE = False
    ComparisonSliderWidget = None

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
    "🔍 Fine Detail Lines": {
        "desc": "Preserve intricate details in technical or detailed artwork",
        "mode": "pure_black", "threshold": 125, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 230, "contrast": 1.9, "sharpen": True,
        "sharpen_amount": 2.2, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 0,
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
    "🖍️ Coloring Book": {
        "desc": "Thick outlines perfect for coloring books and children's art",
        "mode": "pure_black", "threshold": 140, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 1.5, "sharpen": True,
        "sharpen_amount": 1.0, "morphology": "dilate", "morph_iter": 4,
        "kernel": 7, "denoise": True, "denoise_size": 5,
    },
    "📐 Blueprint / Technical": {
        "desc": "Precise technical drawings with clean lines",
        "mode": "pure_black", "threshold": 128, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 1.2, "sharpen": True,
        "sharpen_amount": 1.8, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 1,
    },
    "✂️ Stencil / Vinyl Cut": {
        "desc": "Clean shapes optimized for vinyl cutting and stencils",
        "mode": "stencil", "threshold": 140, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 2.3, "sharpen": True,
        "sharpen_amount": 1.5, "morphology": "close", "morph_iter": 3,
        "kernel": 5, "denoise": True, "denoise_size": 6,
    },
    "🎨 Watercolor Edges": {
        "desc": "Soft edges with artistic watercolor appearance",
        "mode": "sketch", "threshold": 135, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": False,
        "midtone_threshold": 190, "contrast": 1.3, "sharpen": False,
        "sharpen_amount": 0.8, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 3,
    },
    "🔲 Pixel Art Lines": {
        "desc": "Preserve pixel-perfect edges for retro/pixel art",
        "mode": "threshold", "threshold": 128, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 1.0, "sharpen": False,
        "sharpen_amount": 0.0, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 0,
    },
    "🌟 High Contrast Edges": {
        "desc": "Maximum contrast with edge detection emphasis",
        "mode": "edge", "threshold": 120, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 180, "contrast": 3.0, "sharpen": True,
        "sharpen_amount": 2.5, "morphology": "dilate", "morph_iter": 2,
        "kernel": 3, "denoise": False, "denoise_size": 0,
    },
    "🖤 Inverted Lines (White on Black)": {
        "desc": "White lines on black background for dark themes",
        "mode": "pure_black", "threshold": 135, "auto_threshold": False,
        "background": "white", "invert": True, "remove_midtones": True,
        "midtone_threshold": 210, "contrast": 1.6, "sharpen": True,
        "sharpen_amount": 1.3, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
    },
    "🎭 Dramatic Shadows": {
        "desc": "Heavy shadows with strong contrast for dramatic effect",
        "mode": "adaptive", "threshold": 110, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": False,
        "midtone_threshold": 170, "contrast": 2.5, "sharpen": True,
        "sharpen_amount": 1.8, "morphology": "dilate", "morph_iter": 2,
        "kernel": 5, "denoise": True, "denoise_size": 2,
    },
    "📝 Handwriting / Script": {
        "desc": "Preserve delicate script and handwriting details",
        "mode": "pure_black", "threshold": 130, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 220, "contrast": 1.4, "sharpen": True,
        "sharpen_amount": 1.0, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 1,
    },
    "⚡ Speed Lines / Action": {
        "desc": "Dynamic speed lines for action and motion effects",
        "mode": "edge", "threshold": 140, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 2.0, "sharpen": True,
        "sharpen_amount": 2.0, "morphology": "erode", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 0,
    },
    "🏞️ Landscape Outlines": {
        "desc": "Natural flowing lines for landscape and environment art",
        "mode": "adaptive", "threshold": 140, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 205, "contrast": 1.5, "sharpen": True,
        "sharpen_amount": 1.2, "morphology": "close", "morph_iter": 1,
        "kernel": 5, "denoise": True, "denoise_size": 3,
    },
    "🎯 Logo / Icon Prep": {
        "desc": "Clean vectorization-ready lines for logos and icons",
        "mode": "stencil", "threshold": 135, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 2.0, "sharpen": True,
        "sharpen_amount": 1.5, "morphology": "close", "morph_iter": 2,
        "kernel": 3, "denoise": True, "denoise_size": 4,
    },
    "🔬 Scientific Illustration": {
        "desc": "Precise lines for scientific diagrams and illustrations",
        "mode": "pure_black", "threshold": 125, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 215, "contrast": 1.3, "sharpen": True,
        "sharpen_amount": 1.6, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 1,
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
        
        # Track whether widgets have been fully initialized
        self._widgets_initialized = False
        
        # Debounce timer for preview updates
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._update_preview)
        
        self._create_widgets()
        
        # Mark widgets as initialized after creation
        self._widgets_initialized = True
        
        # Now apply the default preset (widgets are guaranteed to exist)
        self._on_preset_changed(self.preset_combo.currentText())
    
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
        
        # Note: preset will be loaded after all widgets are initialized (see __init__)
        
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
        
        # Morphology Operation
        morph_layout = QHBoxLayout()
        morph_layout.addWidget(QLabel("Morphology:"))
        self.morphology_combo = QComboBox()
        self.morphology_combo.addItems([
            "None",
            "Close (fill gaps)",
            "Open (remove noise)",
            "Dilate (thicken)",
            "Erode (thin)"
        ])
        self.morphology_combo.setCurrentText("Close (fill gaps)")
        self.morphology_combo.currentTextChanged.connect(self._schedule_preview_update)
        morph_layout.addWidget(self.morphology_combo)
        morph_layout.addStretch()
        group_layout.addLayout(morph_layout)
        
        # Morphology Iterations
        iter_layout = QHBoxLayout()
        iter_layout.addWidget(QLabel("Iterations:"))
        self.morphology_iterations = QSpinBox()
        self.morphology_iterations.setMinimum(1)
        self.morphology_iterations.setMaximum(5)
        self.morphology_iterations.setValue(1)
        self.morphology_iterations.valueChanged.connect(self._schedule_preview_update)
        iter_layout.addWidget(self.morphology_iterations)
        iter_layout.addStretch()
        group_layout.addLayout(iter_layout)
        
        # Kernel Size
        kernel_layout = QHBoxLayout()
        kernel_layout.addWidget(QLabel("Kernel Size:"))
        self.kernel_size_spin = QSpinBox()
        self.kernel_size_spin.setMinimum(3)
        self.kernel_size_spin.setMaximum(15)
        self.kernel_size_spin.setValue(3)
        self.kernel_size_spin.setSingleStep(2)
        self.kernel_size_spin.valueChanged.connect(self._schedule_preview_update)
        kernel_layout.addWidget(self.kernel_size_spin)
        kernel_layout.addStretch()
        group_layout.addLayout(kernel_layout)
        
        # Sharpen
        sharpen_layout = QHBoxLayout()
        self.sharpen_cb = QCheckBox("Sharpen")
        self.sharpen_cb.setChecked(True)
        self.sharpen_cb.stateChanged.connect(self._schedule_preview_update)
        sharpen_layout.addWidget(self.sharpen_cb)
        self.sharpen_spin = QDoubleSpinBox()
        self.sharpen_spin.setMinimum(0.5)
        self.sharpen_spin.setMaximum(3.0)
        self.sharpen_spin.setValue(1.3)
        self.sharpen_spin.setSingleStep(0.1)
        self.sharpen_spin.valueChanged.connect(self._schedule_preview_update)
        sharpen_layout.addWidget(self.sharpen_spin)
        sharpen_layout.addStretch()
        group_layout.addLayout(sharpen_layout)
        
        # Denoise
        denoise_layout = QHBoxLayout()
        self.denoise_cb = QCheckBox("Denoise")
        self.denoise_cb.setChecked(True)
        self.denoise_cb.stateChanged.connect(self._schedule_preview_update)
        denoise_layout.addWidget(self.denoise_cb)
        self.denoise_size = QSpinBox()
        self.denoise_size.setMinimum(0)
        self.denoise_size.setMaximum(5)
        self.denoise_size.setValue(2)
        self.denoise_size.valueChanged.connect(self._schedule_preview_update)
        denoise_layout.addWidget(self.denoise_size)
        denoise_layout.addStretch()
        group_layout.addLayout(denoise_layout)
        
        # Checkboxes
        self.auto_threshold_cb = QCheckBox("Auto Threshold")
        self.auto_threshold_cb.stateChanged.connect(self._schedule_preview_update)
        group_layout.addWidget(self.auto_threshold_cb)
        
        # Midtone Threshold
        midtone_layout = QHBoxLayout()
        midtone_layout.addWidget(QLabel("Midtone Threshold:"))
        self.midtone_spin = QSpinBox()
        self.midtone_spin.setMinimum(50)
        self.midtone_spin.setMaximum(255)
        self.midtone_spin.setValue(210)
        self.midtone_spin.valueChanged.connect(self._schedule_preview_update)
        midtone_layout.addWidget(self.midtone_spin)
        midtone_layout.addStretch()
        group_layout.addLayout(midtone_layout)
        
        # Remove Midtones
        self.remove_midtones_cb = QCheckBox("Remove midtones")
        self.remove_midtones_cb.setChecked(True)
        self.remove_midtones_cb.stateChanged.connect(self._schedule_preview_update)
        group_layout.addWidget(self.remove_midtones_cb)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_preview_section(self, layout):
        """Create preview section."""
        group = QGroupBox("👁️ Preview")
        group_layout = QVBoxLayout()
        
        if SLIDER_AVAILABLE:
            # Use comparison slider widget
            self.preview_widget = ComparisonSliderWidget()
            self.preview_widget.setMinimumHeight(400)
            group_layout.addWidget(self.preview_widget)
        else:
            # Fallback to simple label
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
            
            # Only update controls if widgets are fully initialized
            if not self._widgets_initialized:
                return
            
            # Update all controls from preset
            self.threshold_slider.setValue(preset["threshold"])
            self.contrast_spin.setValue(preset["contrast"])
            self.auto_threshold_cb.setChecked(preset["auto_threshold"])
            self.sharpen_cb.setChecked(preset["sharpen"])
            if preset["sharpen"]:
                self.sharpen_spin.setValue(preset["sharpen_amount"])
            self.denoise_cb.setChecked(preset["denoise"])
            if preset["denoise"]:
                self.denoise_size.setValue(preset["denoise_size"])
            
            # Morphology settings
            morph_map = {
                "none": "None",
                "close": "Close (fill gaps)",
                "open": "Open (remove noise)",
                "dilate": "Dilate (thicken)",
                "erode": "Erode (thin)"
            }
            morph_text = morph_map.get(preset["morphology"], "None")
            self.morphology_combo.setCurrentText(morph_text)
            self.morphology_iterations.setValue(preset["morph_iter"])
            self.kernel_size_spin.setValue(preset["kernel"])
            
            # Midtone settings
            self.midtone_spin.setValue(preset["midtone_threshold"])
            self.remove_midtones_cb.setChecked(preset["remove_midtones"])
            
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
    
    def _get_morphology_operation(self):
        """Get morphology operation from combo box."""
        morph_map = {
            "None": MorphologyOperation.NONE,
            "Close (fill gaps)": MorphologyOperation.CLOSE,
            "Open (remove noise)": MorphologyOperation.OPEN,
            "Dilate (thicken)": MorphologyOperation.DILATE,
            "Erode (thin)": MorphologyOperation.ERODE
        }
        return morph_map.get(self.morphology_combo.currentText(), MorphologyOperation.NONE)
    
    def _create_settings_from_controls(self):
        """Create LineArtSettings from current control values."""
        return LineArtSettings(
            mode=ConversionMode.PURE_BLACK,
            threshold=self.threshold_slider.value(),
            auto_threshold=self.auto_threshold_cb.isChecked(),
            background_mode=BackgroundMode.TRANSPARENT,
            invert=False,
            remove_midtones=self.remove_midtones_cb.isChecked(),
            midtone_threshold=self.midtone_spin.value(),
            contrast_boost=self.contrast_spin.value(),
            sharpen=self.sharpen_cb.isChecked(),
            sharpen_amount=self.sharpen_spin.value(),
            morphology_operation=self._get_morphology_operation(),
            morphology_iterations=self.morphology_iterations.value(),
            morphology_kernel_size=self.kernel_size_spin.value(),
            denoise=self.denoise_cb.isChecked(),
            denoise_size=self.denoise_size.value()
        )
    
    def _update_preview(self):
        """Update the preview image."""
        if not self.selected_file:
            return
        
        try:
            # Create settings from current controls
            settings = self._create_settings_from_controls()
            
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
            if SLIDER_AVAILABLE and hasattr(self, 'preview_widget'):
                # Use comparison slider
                orig_pixmap = self._pil_to_pixmap(original)
                proc_pixmap = self._pil_to_pixmap(processed)
                
                self.preview_widget.set_before_image(orig_pixmap)
                self.preview_widget.set_after_image(proc_pixmap)
            elif hasattr(self, 'preview_label'):
                # Fallback to simple label
                processed_rgb = processed.convert("RGBA")
                data = processed_rgb.tobytes("raw", "RGBA")
                qimage = QImage(data, processed_rgb.width, processed_rgb.height, QImage.Format.Format_RGBA8888)
                
                # Scale to fit preview
                pixmap = QPixmap.fromImage(qimage)
                scaled = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                self.preview_label.setPixmap(scaled)
            
        except Exception as e:
            logger.error(f"Error displaying preview: {e}")
            if hasattr(self, 'preview_label'):
                self.preview_label.setText(f"Error: {str(e)}")
        finally:
            self.update_preview_btn.setEnabled(True)
            self.update_preview_btn.setText("🔄 Update Preview")
    
    def _pil_to_pixmap(self, img, max_size=400):
        """Convert PIL Image to QPixmap"""
        # Resize for display
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Convert to QImage
        data = img.tobytes("raw", "RGBA")
        qimage = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        
        return QPixmap.fromImage(qimage)
    
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
            # Create settings from current controls
            settings = self._create_settings_from_controls()
            
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
