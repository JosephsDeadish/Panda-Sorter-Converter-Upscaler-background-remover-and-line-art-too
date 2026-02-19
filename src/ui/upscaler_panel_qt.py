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
    QComboBox, QSpinBox, QGroupBox, QCheckBox, QDoubleSpinBox,
    QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2

logger = logging.getLogger(__name__)

# Try to import model manager
try:
    from src.upscaler.model_manager import AIModelManager, ModelStatus
    MODEL_MANAGER_AVAILABLE = True
except ImportError:
    try:
        from upscaler.model_manager import AIModelManager, ModelStatus
        MODEL_MANAGER_AVAILABLE = True
    except ImportError:
        logger.debug("Model manager not available")
        MODEL_MANAGER_AVAILABLE = False
        AIModelManager = None
        ModelStatus = None


def apply_post_processing(img, settings):
    """Apply post-processing effects to an image.
    
    Args:
        img: PIL Image
        settings: Dictionary with post-processing settings
    
    Returns:
        Processed PIL Image
    """
    # Sharpen using ImageEnhance.Sharpness
    if settings.get('sharpen', False):
        amount = settings.get('sharpen_amount', 1.0)
        # ImageEnhance.Sharpness: 0=blurred, 1=original, >1=sharpened
        # Convert our 0-3 scale to 1-4 scale
        sharpness_factor = 1.0 + amount
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpness_factor)
    
    # Denoise using cv2
    if settings.get('denoise', False):
        strength = settings.get('denoise_strength', 2)
        img_array = np.array(img)
        if len(img_array.shape) == 3:
            img_array = cv2.fastNlMeansDenoisingColored(img_array, None, strength, strength, 7, 21)
        else:
            img_array = cv2.fastNlMeansDenoising(img_array, None, strength, 7, 21)
        img = Image.fromarray(img_array)
    
    # Auto-contrast
    if settings.get('auto_contrast', False):
        enhancer = ImageEnhance.Contrast(img)
        factor = settings.get('contrast_factor', 1.0)
        img = enhancer.enhance(factor)
    
    # Custom resolution
    if settings.get('custom_resolution', False):
        width = settings.get('custom_width', img.width)
        height = settings.get('custom_height', img.height)
        img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    return img

try:
    from preprocessing.upscaler import TextureUpscaler
    UPSCALER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Upscaler not available: {e}")
    UPSCALER_AVAILABLE = False

try:
    from ui.live_preview_slider_qt import ComparisonSliderWidget
    SLIDER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Comparison slider not available: {e}")
    SLIDER_AVAILABLE = False
    ComparisonSliderWidget = None

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except ImportError:
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}

# Quality presets for upscaling
UPSCALER_PRESETS = {
    "🔷 Lanczos (Sharpest)": {
        "method": "lanczos",
        "sharpen": 1.5,
        "denoise": False,
        "auto_contrast": False,
        "desc": "Maximum sharpness with Lanczos interpolation"
    },
    "🟢 Bicubic (Smooth)": {
        "method": "bicubic",
        "sharpen": 0.8,
        "denoise": True,
        "auto_contrast": False,
        "desc": "Smooth upscaling with light sharpening"
    },
    "🟡 Bicubic Fast": {
        "method": "bicubic",
        "sharpen": 0.0,
        "denoise": False,
        "auto_contrast": False,
        "desc": "Fast upscaling, minimal processing"
    },
    "🔶 Bicubic Balanced": {
        "method": "bicubic",
        "sharpen": 1.0,
        "denoise": True,
        "auto_contrast": True,
        "desc": "Balanced quality and speed with bicubic"
    },
    "🟣 Bicubic Pixel Art": {
        "method": "bicubic",
        "sharpen": 0.0,
        "denoise": False,
        "auto_contrast": False,
        "desc": "Bicubic for pixel art (Note: Use 2x/4x scales for best results)"
    },
    "⬜ Bicubic Clean": {
        "method": "bicubic",
        "sharpen": 0.0,
        "denoise": False,
        "auto_contrast": False,
        "desc": "Pure bicubic interpolation, no post-processing"
    }
}


class UpscaleWorker(QThread):
    """Worker thread for upscaling images."""
    progress = pyqtSignal(float, str)  # progress, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, upscaler, files, output_dir, scale_factor, method, 
                 post_process_settings=None):
        super().__init__()
        self.upscaler = upscaler
        self.files = files
        self.output_dir = output_dir
        self.scale_factor = scale_factor
        self.method = method
        self.post_process_settings = post_process_settings or {}
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
                
                # Post-processing
                upscaled_img = Image.fromarray(upscaled)
                upscaled_img = apply_post_processing(upscaled_img, self.post_process_settings)
                
                # Save
                output_path = Path(self.output_dir) / Path(file_path).name
                upscaled_img.save(output_path)
            
            self.finished.emit(True, f"Successfully upscaled {total} images")
        except Exception as e:
            logger.error(f"Upscaling failed: {e}", exc_info=True)
            self.finished.emit(False, f"Upscaling failed: {str(e)}")
    
    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True


class PreviewWorker(QThread):
    """Worker thread for generating live preview."""
    finished = pyqtSignal(object, object)  # original, processed
    error = pyqtSignal(str)
    
    def __init__(self, upscaler, file_path, scale_factor, method, post_process_settings=None):
        super().__init__()
        self.upscaler = upscaler
        self.file_path = file_path
        self.scale_factor = scale_factor
        self.method = method
        self.post_process_settings = post_process_settings or {}
        self._should_cancel = False
    
    def run(self):
        """Generate preview in background."""
        try:
            if self._should_cancel:
                return
            
            # Load original
            orig_img = Image.open(self.file_path)
            orig_array = np.array(orig_img)
            
            # Upscale
            upscaled = self.upscaler.upscale(
                orig_array,
                scale_factor=self.scale_factor,
                method=self.method
            )
            
            # Post-processing
            processed_img = Image.fromarray(upscaled)
            processed_img = apply_post_processing(processed_img, self.post_process_settings)
            
            if not self._should_cancel:
                self.finished.emit(orig_img, processed_img)
                
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            self.error.emit(str(e))
    
    def cancel(self):
        """Cancel the preview generation."""
        self._should_cancel = True


class ImageUpscalerPanelQt(QWidget):
    """PyQt6 panel for image upscaling."""
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        if not UPSCALER_AVAILABLE:
            self._show_unavailable()
            return
        
        self.tooltip_manager = tooltip_manager
        self.upscaler = TextureUpscaler()
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.worker_thread = None
        self.preview_worker = None
        
        # Initialize model manager
        if MODEL_MANAGER_AVAILABLE:
            self.model_manager = AIModelManager()
        else:
            self.model_manager = None
        
        # Preview debounce timer
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._update_live_preview)
        
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
        
        # Archive options
        archive_layout = QHBoxLayout()
        
        self.archive_input_cb = QCheckBox("📦 Input is Archive")
        if not ARCHIVE_AVAILABLE:
            self.archive_input_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_input_cb.setStyleSheet("color: gray;")
        else:
            self._set_tooltip(self.archive_input_cb, 'input_archive_checkbox')
        archive_layout.addWidget(self.archive_input_cb)
        
        self.archive_output_cb = QCheckBox("📦 Export to Archive")
        if not ARCHIVE_AVAILABLE:
            self.archive_output_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_output_cb.setStyleSheet("color: gray;")
        else:
            self._set_tooltip(self.archive_output_cb, 'output_archive_checkbox')
        archive_layout.addWidget(self.archive_output_cb)
        
        archive_layout.addStretch()
        file_layout.addLayout(archive_layout)
        
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
        
        # Quality Presets group
        preset_group = QGroupBox("🎨 Quality Presets")
        preset_layout = QVBoxLayout()
        
        self.preset_combo = QComboBox()
        for preset_name in UPSCALER_PRESETS.keys():
            self.preset_combo.addItem(preset_name)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        
        self.preset_desc_label = QLabel(UPSCALER_PRESETS["🔷 Lanczos (Sharpest)"]["desc"])
        self.preset_desc_label.setStyleSheet("color: gray; font-size: 10pt;")
        self.preset_desc_label.setWordWrap(True)
        preset_layout.addWidget(self.preset_desc_label)
        
        preset_group.setLayout(preset_layout)
        main_layout.addWidget(preset_group)
        
        # Advanced Settings group
        advanced_group = QGroupBox("⚙️ Advanced Post-Processing")
        advanced_layout = QVBoxLayout()
        
        # Sharpen
        sharpen_layout = QHBoxLayout()
        self.sharpen_cb = QCheckBox("Sharpen after upscale")
        self.sharpen_cb.setChecked(False)
        self.sharpen_cb.stateChanged.connect(self._schedule_preview_update)
        sharpen_layout.addWidget(self.sharpen_cb)
        self.sharpen_spin = QSpinBox()
        self.sharpen_spin.setMinimum(0)
        self.sharpen_spin.setMaximum(3)
        self.sharpen_spin.setValue(1)
        self.sharpen_spin.setSuffix("x")
        self.sharpen_spin.valueChanged.connect(self._schedule_preview_update)
        sharpen_layout.addWidget(self.sharpen_spin)
        sharpen_layout.addStretch()
        advanced_layout.addLayout(sharpen_layout)
        
        # Denoise
        denoise_layout = QHBoxLayout()
        self.denoise_cb = QCheckBox("Denoise")
        self.denoise_cb.setChecked(False)
        self.denoise_cb.stateChanged.connect(self._schedule_preview_update)
        denoise_layout.addWidget(self.denoise_cb)
        self.denoise_strength = QSpinBox()
        self.denoise_strength.setMinimum(1)
        self.denoise_strength.setMaximum(5)
        self.denoise_strength.setValue(2)
        self.denoise_strength.valueChanged.connect(self._schedule_preview_update)
        denoise_layout.addWidget(self.denoise_strength)
        denoise_layout.addStretch()
        advanced_layout.addLayout(denoise_layout)
        
        # Auto-contrast
        contrast_layout = QHBoxLayout()
        self.auto_contrast_cb = QCheckBox("Auto-contrast")
        self.auto_contrast_cb.setChecked(False)
        self.auto_contrast_cb.stateChanged.connect(self._schedule_preview_update)
        contrast_layout.addWidget(self.auto_contrast_cb)
        self.contrast_spin = QDoubleSpinBox()
        self.contrast_spin.setMinimum(0.5)
        self.contrast_spin.setMaximum(2.0)
        self.contrast_spin.setValue(1.0)
        self.contrast_spin.setSingleStep(0.1)
        self.contrast_spin.valueChanged.connect(self._schedule_preview_update)
        contrast_layout.addWidget(self.contrast_spin)
        contrast_layout.addStretch()
        advanced_layout.addLayout(contrast_layout)
        
        # Custom resolution
        self.custom_res_cb = QCheckBox("Custom output resolution")
        self.custom_res_cb.setChecked(False)
        self.custom_res_cb.stateChanged.connect(self._schedule_preview_update)
        advanced_layout.addWidget(self.custom_res_cb)
        
        custom_res_layout = QHBoxLayout()
        custom_res_layout.addWidget(QLabel("Width:"))
        self.custom_width = QSpinBox()
        self.custom_width.setMinimum(32)
        self.custom_width.setMaximum(8192)
        self.custom_width.setValue(1024)
        self.custom_width.valueChanged.connect(self._schedule_preview_update)
        custom_res_layout.addWidget(self.custom_width)
        custom_res_layout.addWidget(QLabel("Height:"))
        self.custom_height = QSpinBox()
        self.custom_height.setMinimum(32)
        self.custom_height.setMaximum(8192)
        self.custom_height.setValue(1024)
        self.custom_height.valueChanged.connect(self._schedule_preview_update)
        custom_res_layout.addWidget(self.custom_height)
        custom_res_layout.addStretch()
        advanced_layout.addLayout(custom_res_layout)
        
        advanced_group.setLayout(advanced_layout)
        main_layout.addWidget(advanced_group)
        
        # Live Preview group
        if SLIDER_AVAILABLE:
            preview_group = QGroupBox("👁️ Live Preview")
            preview_layout = QVBoxLayout()
            
            # Preview file selector
            preview_file_layout = QHBoxLayout()
            preview_file_layout.addWidget(QLabel("Preview file:"))
            self.preview_file_combo = QComboBox()
            self.preview_file_combo.currentTextChanged.connect(self._schedule_preview_update)
            preview_file_layout.addWidget(self.preview_file_combo)
            preview_layout.addLayout(preview_file_layout)
            
            # Preview scale
            preview_scale_layout = QHBoxLayout()
            preview_scale_layout.addWidget(QLabel("Preview scale:"))
            self.preview_scale_spin = QSpinBox()
            self.preview_scale_spin.setMinimum(2)
            self.preview_scale_spin.setMaximum(8)
            self.preview_scale_spin.setValue(2)
            self.preview_scale_spin.setSuffix("x")
            self.preview_scale_spin.valueChanged.connect(self._schedule_preview_update)
            preview_scale_layout.addWidget(self.preview_scale_spin)
            preview_scale_layout.addStretch()
            preview_layout.addLayout(preview_scale_layout)
            
            # Comparison slider widget
            self.preview_widget = ComparisonSliderWidget()
            self.preview_widget.setMinimumHeight(300)
            preview_layout.addWidget(self.preview_widget)
            
            preview_group.setLayout(preview_layout)
            main_layout.addWidget(preview_group)
        
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
        
        # Initialize method description with current selection
        self._update_method_description(self.method_combo.currentText())
    
    def _update_method_description(self, method):
        """Update the method description based on selection."""
        # Import to check availability
        try:
            from preprocessing.upscaler import REALESRGAN_AVAILABLE, NATIVE_AVAILABLE
        except ImportError:
            REALESRGAN_AVAILABLE = False
            NATIVE_AVAILABLE = False
        except Exception:
            REALESRGAN_AVAILABLE = False
            NATIVE_AVAILABLE = False
        
        # Helper function for availability status
        def get_status(available):
            return '✅ Available' if available else '⚠️ Native acceleration not available'
        
        def get_realesrgan_status(available):
            return '✅ Available' if available else '❌ Not installed - pip install basicsr realesrgan'
        
        descriptions = {
            "bicubic": "Bicubic: Fast, good quality for most images (always available)",
            "lanczos": f"Lanczos: Sharp results, best for textures with fine details {get_status(NATIVE_AVAILABLE)}",
            "realesrgan": f"Real-ESRGAN: Best for retro/PS2 textures, slower {get_realesrgan_status(REALESRGAN_AVAILABLE)}",
            "esrgan": "ESRGAN: High quality (currently uses bicubic as fallback)"
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
            
            # Update preview file combo
            if SLIDER_AVAILABLE and hasattr(self, 'preview_file_combo'):
                self.preview_file_combo.clear()
                for f in files:
                    self.preview_file_combo.addItem(Path(f).name, f)
                self._schedule_preview_update()
            
            self._check_ready()
    
    def _on_preset_changed(self, preset_name):
        """Handle preset selection."""
        if preset_name in UPSCALER_PRESETS:
            preset = UPSCALER_PRESETS[preset_name]
            self.preset_desc_label.setText(preset["desc"])
            
            # Update controls
            self.method_combo.setCurrentText(preset["method"])
            self.sharpen_cb.setChecked(preset["sharpen"] > 0)
            if preset["sharpen"] > 0:
                self.sharpen_spin.setValue(int(preset["sharpen"]))
            self.denoise_cb.setChecked(preset["denoise"])
            self.auto_contrast_cb.setChecked(preset["auto_contrast"])
            
            # Trigger preview update
            self._schedule_preview_update()
    
    def _schedule_preview_update(self):
        """Schedule preview update with debouncing."""
        if not hasattr(self, 'preview_timer'):
            return
        
        # Cancel any pending preview
        if self.preview_worker and self.preview_worker.isRunning():
            self.preview_worker.cancel()
        
        # Restart debounce timer (500ms delay for responsive feedback)
        self.preview_timer.stop()
        self.preview_timer.start(500)
    
    def _update_live_preview(self):
        """Generate and display live preview."""
        if not SLIDER_AVAILABLE or not hasattr(self, 'preview_widget'):
            return
        
        if not hasattr(self, 'preview_file_combo') or self.preview_file_combo.count() == 0:
            return
        
        file_path = self.preview_file_combo.currentData()
        if not file_path:
            return
        
        try:
            scale_factor = self.preview_scale_spin.value()
            method = self.method_combo.currentText()
            
            # Gather post-processing settings
            post_process_settings = {
                'sharpen': self.sharpen_cb.isChecked(),
                'sharpen_amount': self.sharpen_spin.value(),
                'denoise': self.denoise_cb.isChecked(),
                'denoise_strength': self.denoise_strength.value(),
                'auto_contrast': self.auto_contrast_cb.isChecked(),
                'contrast_factor': self.contrast_spin.value(),
                'custom_resolution': self.custom_res_cb.isChecked(),
                'custom_width': self.custom_width.value(),
                'custom_height': self.custom_height.value()
            }
            
            # Start preview worker
            self.preview_worker = PreviewWorker(
                self.upscaler,
                file_path,
                scale_factor,
                method,
                post_process_settings
            )
            self.preview_worker.finished.connect(self._display_preview)
            self.preview_worker.error.connect(self._preview_error)
            self.preview_worker.start()
            
        except Exception as e:
            logger.error(f"Error starting preview: {e}")
    
    def _display_preview(self, original, processed):
        """Display the preview in comparison slider."""
        try:
            # Ensure preview widget exists
            if not hasattr(self, 'preview_widget') or self.preview_widget is None:
                logger.warning("Preview widget not available")
                return
            
            # Convert to QPixmap
            orig_pixmap = self._pil_to_pixmap(original)
            proc_pixmap = self._pil_to_pixmap(processed)
            
            # Display in comparison widget
            self.preview_widget.set_before_image(orig_pixmap)
            self.preview_widget.set_after_image(proc_pixmap)
            
        except Exception as e:
            logger.error(f"Error displaying preview: {e}")
    
    def _preview_error(self, error_msg):
        """Handle preview error."""
        logger.error(f"Preview error: {error_msg}")
    
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
        
        # Check if Real-ESRGAN model is available (if needed)
        if method == 'realesrgan':
            if not self._ensure_realesrgan_model(scale_factor):
                return
        
        # Gather post-processing settings
        post_process_settings = {
            'sharpen': self.sharpen_cb.isChecked(),
            'sharpen_amount': self.sharpen_spin.value(),
            'denoise': self.denoise_cb.isChecked(),
            'denoise_strength': self.denoise_strength.value(),
            'auto_contrast': self.auto_contrast_cb.isChecked(),
            'contrast_factor': self.contrast_spin.value(),
            'custom_resolution': self.custom_res_cb.isChecked(),
            'custom_width': self.custom_width.value(),
            'custom_height': self.custom_height.value()
        }
        
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
            method,
            post_process_settings
        )
        self.worker_thread.progress.connect(self._update_progress)
        self.worker_thread.finished.connect(self._upscaling_finished)
        self.worker_thread.start()
    
    def _ensure_realesrgan_model(self, scale_factor: int) -> bool:
        """
        Ensure Real-ESRGAN model is available, prompt to download if not.
        
        Returns:
            True if model is available or successfully downloaded
        """
        if not MODEL_MANAGER_AVAILABLE or not self.model_manager:
            QMessageBox.warning(
                self,
                "Model Manager Not Available",
                "Model manager is not available. Real-ESRGAN upscaling requires model downloads.\n\n"
                "Please use bicubic or lanczos methods instead."
            )
            return False
        
        # Determine which model is needed
        model_name = 'RealESRGAN_x2plus' if scale_factor == 2 else 'RealESRGAN_x4plus'
        
        # Check if model exists
        if self.model_manager.get_model_status(model_name) == ModelStatus.INSTALLED:
            return True
        
        # Ask user if they want to download
        model_info = self.model_manager.MODELS.get(model_name, {})
        size_mb = model_info.get('size_mb', '?')
        
        reply = QMessageBox.question(
            self,
            "Download Real-ESRGAN Model?",
            f"Real-ESRGAN {scale_factor}x model ({size_mb}MB) is required for upscaling.\n\n"
            "Download now? You can also download from Settings → AI Models later.",
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return False
        
        # Download the model
        return self._download_model(model_name)
    
    def _download_model(self, model_name: str) -> bool:
        """
        Download model with progress dialog using QThread.
        
        Returns:
            True if successfully downloaded
        """
        # Create download thread (reuse from ai_models_settings_tab)
        try:
            from .ai_models_settings_tab import ModelDownloadThread
        except ImportError:
            # Fallback to simple blocking download
            return self._download_model_blocking(model_name)
        
        # Create progress dialog
        progress = QProgressDialog(
            f"Downloading {model_name}...",
            "Cancel",
            0,
            100,
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        
        download_success = [False]
        
        def on_progress(downloaded, total):
            if progress.wasCanceled():
                return
            if total > 0:
                progress.setValue(int((downloaded / total) * 100))
        
        def on_finished(success):
            download_success[0] = success
            progress.close()
        
        # Start download thread
        thread = ModelDownloadThread(self.model_manager, model_name)
        thread.progress.connect(on_progress)
        thread.finished.connect(on_finished)
        thread.start()
        
        # Wait for completion
        thread.wait()
        
        if progress.wasCanceled():
            QMessageBox.information(
                self,
                "Download Cancelled",
                "Model download was cancelled."
            )
            return False
        
        if download_success[0]:
            QMessageBox.information(
                self,
                "Success",
                f"{model_name} downloaded successfully! Ready to upscale."
            )
            return True
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to download {model_name}. Please check your internet connection and try again."
            )
            return False
    
    def _download_model_blocking(self, model_name: str) -> bool:
        """
        Fallback blocking download (used when QThread not available).
        
        Returns:
            True if successfully downloaded
        """
        # Create progress dialog
        progress = QProgressDialog(
            f"Downloading {model_name}...",
            "Cancel",
            0,
            100,
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setAutoClose(True)
        progress.setAutoReset(True)
        
        cancelled = [False]
        
        def on_progress(downloaded, total):
            if cancelled[0]:
                return
            if progress.wasCanceled():
                cancelled[0] = True
                return
            if total > 0:
                progress.setValue(int((downloaded / total) * 100))
        
        # Download (blocking)
        try:
            success = self.model_manager.download_model(model_name, on_progress)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            success = False
        
        progress.close()
        
        if cancelled[0]:
            QMessageBox.information(
                self,
                "Download Cancelled",
                "Model download was cancelled."
            )
            return False
        
        if success:
            QMessageBox.information(
                self,
                "Success",
                f"{model_name} downloaded successfully! Ready to upscale."
            )
            return True
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to download {model_name}. Please check your internet connection and try again."
            )
            return False
    
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
    
    def _set_tooltip(self, widget, text):
        """Set tooltip on a widget using tooltip manager if available."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'set_tooltip'):
            self.tooltip_manager.set_tooltip(widget, text)
        else:
            widget.setToolTip(text)
