"""
Image Upscaler UI Panel - PyQt6 Version
Provides UI for upscaling images using various methods (bicubic, lanczos, etc.)
"""


from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Optional

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
        QComboBox, QSpinBox, QGroupBox, QCheckBox, QDoubleSpinBox,
        QProgressDialog, QSplitter
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QPixmap, QImage
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    QThread = object
    QScrollArea = object
    QGroupBox = object
    class _SignalStub:  # noqa: E301
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SignalStub()  # noqa: E301
    class Qt:
        class AlignmentFlag:
            AlignLeft = AlignRight = AlignCenter = AlignTop = AlignBottom = AlignHCenter = AlignVCenter = 0
        class WindowType:
            FramelessWindowHint = WindowStaysOnTopHint = Tool = Window = Dialog = 0
        class CursorShape:
            ArrowCursor = PointingHandCursor = BusyCursor = WaitCursor = CrossCursor = 0
        class DropAction:
            CopyAction = MoveAction = IgnoreAction = 0
        class Key:
            Key_Escape = Key_Return = Key_Space = Key_Delete = Key_Up = Key_Down = Key_Left = Key_Right = 0
        class ScrollBarPolicy:
            ScrollBarAlwaysOff = ScrollBarAsNeeded = ScrollBarAlwaysOn = 0
        class ItemFlag:
            ItemIsEnabled = ItemIsSelectable = ItemIsEditable = 0
        class CheckState:
            Unchecked = Checked = PartiallyChecked = 0
        class Orientation:
            Horizontal = Vertical = 0
        class SortOrder:
            AscendingOrder = DescendingOrder = 0
        class MatchFlag:
            MatchExactly = MatchContains = 0
        class ItemDataRole:
            DisplayRole = UserRole = DecorationRole = 0
    class QPixmap:
        def __init__(self, *a): pass
        def isNull(self): return True
    class QImage:
        def __init__(self, *a): pass
    class QTimer:
        def __init__(self, *a): pass
        def start(self, *a): pass
        def stop(self): pass
        timeout = property(lambda self: type("S", (), {"connect": lambda s,f: None, "emit": lambda s: None})())
    QCheckBox = object
    QComboBox = object
    QDoubleSpinBox = object
    QFileDialog = object
    QHBoxLayout = object
    QLabel = object
    QMessageBox = object
    QProgressBar = object
    QProgressDialog = object
    QPushButton = object
    QSpinBox = object
    QVBoxLayout = object
try:
    from PIL import Image, ImageEnhance, ImageFilter
    HAS_PIL = True
except (ImportError, OSError, RuntimeError):
    HAS_PIL = False

try:
    import numpy as np
    HAS_NUMPY = True
except (ImportError, OSError, RuntimeError):
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False
try:
    import cv2
    HAS_CV2 = True
except (ImportError, OSError, RuntimeError):
    HAS_CV2 = False
    cv2 = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

# Try to import model manager
try:
    from upscaler.model_manager import AIModelManager, ModelStatus
    MODEL_MANAGER_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    try:
        from src.upscaler.model_manager import AIModelManager, ModelStatus
        MODEL_MANAGER_AVAILABLE = True
    except (ImportError, OSError, RuntimeError):
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
except (ImportError, OSError, RuntimeError):
    try:
        import sys as _sys
        import os as _os
        _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..'))
        from preprocessing.upscaler import TextureUpscaler
        UPSCALER_AVAILABLE = True
    except Exception as e:
        logger.warning(f"Upscaler not available: {e}")
        UPSCALER_AVAILABLE = False
except Exception as e:
    logger.warning(f"Upscaler not available: {e}")
    UPSCALER_AVAILABLE = False

try:
    from ui.live_preview_slider_qt import ComparisonSliderWidget
    SLIDER_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"Comparison slider not available: {e}")
    SLIDER_AVAILABLE = False
    ComparisonSliderWidget = None

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")

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
    },
    "🔴 Real-ESRGAN 4x (PS2 Optimal)": {
        "method": "realesrgan",
        "scale": 4,
        "sharpen": 0.0,
        "denoise": False,
        "auto_contrast": False,
        "desc": "Real-ESRGAN 4x — best quality for PS2/retro textures (requires basicsr + model download)"
    },
    "🟠 Real-ESRGAN 2x": {
        "method": "realesrgan",
        "scale": 2,
        "sharpen": 0.0,
        "denoise": False,
        "auto_contrast": False,
        "desc": "Real-ESRGAN 2x — faster, still high quality (requires basicsr + model download)"
    },
}


class UpscaleWorker(QThread):
    """Worker thread for upscaling images."""
    progress = pyqtSignal(float, str)  # progress, message
    finished = pyqtSignal(bool, str, int)  # success, message, files_processed

    # Maps UI display name → (PIL save format, file extension)
    _FMT_MAP = {
        'PNG':  ('PNG',  '.png'),
        'JPEG': ('JPEG', '.jpg'),
        'WebP': ('WEBP', '.webp'),
        'BMP':  ('BMP',  '.bmp'),
        'TIFF': ('TIFF', '.tiff'),
    }
    
    def __init__(self, upscaler, files, output_dir, scale_factor, method,
                 post_process_settings=None, skip_existing=False, output_format='Same as Input'):
        super().__init__()
        self.upscaler = upscaler
        self.files = files
        self.output_dir = output_dir
        self.scale_factor = scale_factor
        self.method = method
        self.post_process_settings = post_process_settings or {}
        self.skip_existing = skip_existing
        self.output_format = output_format
        self._is_cancelled = False

    def _get_output_path(self, file_path: Path) -> Path:
        """Return the output path, respecting the selected output format."""
        stem = file_path.stem
        if self.output_format in self._FMT_MAP:
            ext = self._FMT_MAP[self.output_format][1]
        else:
            ext = file_path.suffix  # "Same as Input"
        return Path(self.output_dir) / f"{stem}{ext}"

    def run(self):
        """Execute upscaling in background thread."""
        try:
            total = len(self.files)
            done = 0
            skipped = 0
            for i, file_path in enumerate(self.files):
                if self._is_cancelled:
                    self.finished.emit(False, "Cancelled", done)
                    return

                # Update progress
                progress = (i / total) * 100
                self.progress.emit(progress, f"Upscaling: {Path(file_path).name}")

                output_path = self._get_output_path(Path(file_path))
                if self.skip_existing and output_path.exists():
                    skipped += 1
                    continue

                # Load image
                img = Image.open(file_path)
                img_array = np.array(img)

                # Upscale
                upscaled = self.upscaler.upscale(
                    img_array,
                    scale_factor=self.scale_factor,
                    method=self.method
                )

                # Optional GFPGAN face enhancement
                if self.post_process_settings.get('enhance_faces'):
                    upscaled = self.upscaler.enhance_faces(upscaled, upscale=1)

                # Post-processing
                upscaled_img = Image.fromarray(upscaled)
                upscaled_img = apply_post_processing(upscaled_img, self.post_process_settings)

                # Convert mode for JPEG (no alpha channel)
                pil_fmt = self._FMT_MAP.get(self.output_format, (None, None))[0]
                if pil_fmt == 'JPEG' and upscaled_img.mode in ('RGBA', 'LA', 'P'):
                    upscaled_img = upscaled_img.convert('RGB')

                # Save
                save_kwargs = {}
                if pil_fmt == 'JPEG':
                    save_kwargs['quality'] = 95
                if pil_fmt:
                    upscaled_img.save(output_path, format=pil_fmt, **save_kwargs)
                else:
                    upscaled_img.save(output_path)
                done += 1

            parts = [f"Successfully upscaled {done} image{'s' if done != 1 else ''}"]
            if skipped:
                parts.append(f"{skipped} skipped (already existed)")
            self.progress.emit(100.0, "Done")
            self.finished.emit(True, ", ".join(parts), done)
        except Exception as e:
            logger.error(f"Upscaling failed: {e}", exc_info=True)
            self.finished.emit(False, f"Upscaling failed: {str(e)}", 0)
    
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

    finished = pyqtSignal(bool, str, int)  # success, message, files_processed
    error = pyqtSignal(str)  # error message
    
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
        """Create the UI widgets with left (controls) / right (preview) splitter layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setMinimumSize(800, 520)

        # Title
        title_label = QLabel("🔍 Image Upscaler")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Upscale images using various interpolation methods")
        subtitle_label.setStyleSheet("color: gray; font-size: 10pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # ── Main splitter: LEFT = controls, RIGHT = preview ──────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, stretch=1)

        # ── LEFT: controls in a scroll area ──────────────────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setMinimumWidth(320)
        left_scroll.setMaximumWidth(520)
        left_container = QWidget()
        main_layout = QVBoxLayout(left_container)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(4, 4, 4, 4)
        left_scroll.setWidget(left_container)
        splitter.addWidget(left_scroll)

        # ── RIGHT: preview + progress + action buttons ────────────────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(4)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([380, 420])
        
        # File selection group
        file_group = QGroupBox("📁 File Selection")
        file_layout = QVBoxLayout()

        # Select files + Add Folder buttons
        select_btn_layout = QHBoxLayout()
        self.select_files_btn = QPushButton("Select Files")
        self.select_files_btn.clicked.connect(self._select_files)
        select_btn_layout.addWidget(self.select_files_btn)
        self._set_tooltip(self.select_files_btn, 'upscale_input')

        add_folder_btn = QPushButton("📂 Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        self._set_tooltip(add_folder_btn, "Add all images from a folder to the selection")
        select_btn_layout.addWidget(add_folder_btn)

        clear_files_btn = QPushButton("✖ Clear")
        clear_files_btn.clicked.connect(self._clear_files)
        clear_files_btn.setFixedWidth(65)
        self._set_tooltip(clear_files_btn, "Remove all selected files from the list")
        select_btn_layout.addWidget(clear_files_btn)

        self.file_count_label = QLabel("No files selected")
        self.file_count_label.setStyleSheet("color: gray;")
        select_btn_layout.addWidget(self.file_count_label)
        select_btn_layout.addStretch()

        file_layout.addLayout(select_btn_layout)

        # Recursive checkbox
        self.recursive_input_cb = QCheckBox("Process subfolders")
        self.recursive_input_cb.setChecked(False)
        self._set_tooltip(self.recursive_input_cb, "When adding a folder, also include images in sub-folders")
        file_layout.addWidget(self.recursive_input_cb)
        
        # Output directory button
        output_btn_layout = QHBoxLayout()
        self.select_output_btn = QPushButton("Select Output Directory")
        self.select_output_btn.clicked.connect(self._select_output_directory)
        output_btn_layout.addWidget(self.select_output_btn)
        self._set_tooltip(self.select_output_btn, 'upscale_output')
        
        self.output_dir_label = QLabel("No output directory selected")
        self.output_dir_label.setStyleSheet("color: gray;")
        output_btn_layout.addWidget(self.output_dir_label)
        output_btn_layout.addStretch()

        file_layout.addLayout(output_btn_layout)

        self._skip_existing = QCheckBox("Skip if output file already exists")
        self._skip_existing.setChecked(False)
        self._set_tooltip(self._skip_existing, "When checked, files are not re-upscaled if the output already exists")
        file_layout.addWidget(self._skip_existing)
        
        # Archive options
        archive_layout = QHBoxLayout()
        
        self.archive_input_cb = QCheckBox("📦 Input is Archive")
        if not ARCHIVE_AVAILABLE:
            self.archive_input_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_input_cb.setStyleSheet("color: gray;")
        else:
            # upscale_zip_input last so its text shows as default; input_archive_checkbox
            # is also registered for the tutorial system cycling
            self._set_tooltip(self.archive_input_cb, 'input_archive_checkbox')
            self._set_tooltip(self.archive_input_cb, 'upscale_zip_input')
        archive_layout.addWidget(self.archive_input_cb)
        
        self.archive_output_cb = QCheckBox("📦 Export to Archive")
        if not ARCHIVE_AVAILABLE:
            self.archive_output_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_output_cb.setStyleSheet("color: gray;")
        else:
            # upscale_zip_output last so its text shows as default
            self._set_tooltip(self.archive_output_cb, 'output_archive_checkbox')
            self._set_tooltip(self.archive_output_cb, 'upscale_zip_output')
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
        self._set_tooltip(self.scale_spin, 'upscale_factor')
        
        # Upscaling method
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "bicubic",
            "lanczos",
            "realesrgan",
            "realesrgan_anime",
            "realesrgan_x2",
            "swinir",
            "swinir_anime",
            "esrgan",
        ])
        self.method_combo.setCurrentText("bicubic")
        method_layout.addWidget(self.method_combo)
        method_layout.addStretch()
        settings_layout.addLayout(method_layout)
        self._set_tooltip(self.method_combo, 'upscale_style')
        
        # Method description
        self.method_desc_label = QLabel(
            "Bicubic: Fast, good quality for most images"
        )
        self.method_desc_label.setStyleSheet("color: gray; font-size: 10pt;")
        self.method_desc_label.setWordWrap(True)
        self.method_combo.currentTextChanged.connect(self._update_method_description)
        settings_layout.addWidget(self.method_desc_label)

        # Face / character enhancement
        self.face_enhance_check = QCheckBox("✨ Enhance faces / characters (GFPGAN)")
        _gfpgan_available = False
        try:
            from preprocessing.upscaler import GFPGAN_AVAILABLE
            _gfpgan_available = GFPGAN_AVAILABLE
            self.face_enhance_check.setEnabled(GFPGAN_AVAILABLE)
            if not GFPGAN_AVAILABLE:
                self.face_enhance_check.setText(
                    "✨ Enhance faces / characters (GFPGAN) — not installed"
                )
        except Exception:
            self.face_enhance_check.setEnabled(False)
        settings_layout.addWidget(self.face_enhance_check)
        if not _gfpgan_available:
            _gfpgan_note = QLabel(
                "⚠️ GFPGAN not found.\n"
                "Run  python setup_models.py  from the app folder to install all AI models."
            )
            _gfpgan_note.setStyleSheet("color: #d44; font-size: 9pt; font-style: italic;")
            _gfpgan_note.setWordWrap(True)
            settings_layout.addWidget(_gfpgan_note)
        self._set_tooltip(self.face_enhance_check, 'upscale_face_enhance')

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
        self._set_tooltip(self.preset_combo, 'upscale_style')
        
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
        self._set_tooltip(self.sharpen_cb, 'upscale_sharpen')
        self._set_tooltip(self.sharpen_spin, 'upscale_sharpen')
        
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
        self._set_tooltip(self.denoise_cb, 'upscale_denoise')
        self._set_tooltip(self.denoise_strength, 'upscale_denoise')
        
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
        self._set_tooltip(self.auto_contrast_cb, 'upscale_auto_level')
        self._set_tooltip(self.contrast_spin, 'upscale_auto_level')
        
        # Custom resolution
        self.custom_res_cb = QCheckBox("Custom output resolution")
        self.custom_res_cb.setChecked(False)
        self.custom_res_cb.stateChanged.connect(self._schedule_preview_update)
        advanced_layout.addWidget(self.custom_res_cb)
        self._set_tooltip(self.custom_res_cb, 'upscale_custom_res')
        
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
        self._set_tooltip(self.custom_width, 'upscale_custom_res')
        self._set_tooltip(self.custom_height, 'upscale_custom_res')
        
        advanced_group.setLayout(advanced_layout)
        main_layout.addWidget(advanced_group)

        # Output Options group — dedicated controls for the remaining upscale IDs
        output_group = QGroupBox("📤 Output Options")
        output_layout = QVBoxLayout()

        # Output format
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Output Format:"))
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["Same as Input", "PNG", "JPEG", "WebP", "BMP", "TIFF"])
        self.output_format_combo.currentTextChanged.connect(self._schedule_preview_update)
        self._set_tooltip(self.output_format_combo, 'upscale_format')
        fmt_layout.addWidget(self.output_format_combo, 1)
        output_layout.addLayout(fmt_layout)

        # GPU acceleration
        self.use_gpu_cb = QCheckBox("Use GPU acceleration (faster)")
        self.use_gpu_cb.setChecked(True)
        self._set_tooltip(self.use_gpu_cb, 'upscale_gpu')
        output_layout.addWidget(self.use_gpu_cb)

        # Preserve alpha channel
        self.preserve_alpha_cb = QCheckBox("Keep alpha channel (transparency)")
        self.preserve_alpha_cb.setChecked(True)
        self._set_tooltip(self.preserve_alpha_cb, 'upscale_alpha')
        output_layout.addWidget(self.preserve_alpha_cb)

        # Preserve metadata (EXIF)
        self.preserve_metadata_cb = QCheckBox("Preserve image metadata (EXIF)")
        self.preserve_metadata_cb.setChecked(True)
        self._set_tooltip(self.preserve_metadata_cb, 'upscale_preserve_metadata')
        output_layout.addWidget(self.preserve_metadata_cb)

        # Overwrite existing files
        self.overwrite_cb = QCheckBox("Overwrite existing output files")
        self.overwrite_cb.setChecked(False)
        self._set_tooltip(self.overwrite_cb, 'upscale_overwrite')
        output_layout.addWidget(self.overwrite_cb)

        # Process subdirectories recursively
        self.recursive_cb = QCheckBox("Process images in subdirectories")
        self.recursive_cb.setChecked(False)
        self._set_tooltip(self.recursive_cb, 'upscale_recursive')
        output_layout.addWidget(self.recursive_cb)

        # Seamless tiling
        self.tile_seamless_cb = QCheckBox("Ensure seamless tiling after upscale")
        self.tile_seamless_cb.setChecked(False)
        self._set_tooltip(self.tile_seamless_cb, 'upscale_tile_seamless')
        output_layout.addWidget(self.tile_seamless_cb)

        # Normal map mode
        self.normal_map_cb = QCheckBox("Process as normal map (preserves directional data)")
        self.normal_map_cb.setChecked(False)
        self._set_tooltip(self.normal_map_cb, 'upscale_normal_map')
        output_layout.addWidget(self.normal_map_cb)

        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # Live Preview group — placed in right panel for side-by-side layout
        if SLIDER_AVAILABLE:
            preview_title = QLabel("👁️ Live Preview (Before / After)")
            preview_title.setStyleSheet("font-weight: bold; font-size: 13px;")
            right_layout.addWidget(preview_title)

            # Preview file selector
            preview_file_layout = QHBoxLayout()
            preview_file_layout.addWidget(QLabel("Preview file:"))
            self.preview_file_combo = QComboBox()
            self.preview_file_combo.currentTextChanged.connect(self._schedule_preview_update)
            preview_file_layout.addWidget(self.preview_file_combo)
            right_layout.addLayout(preview_file_layout)
            self._set_tooltip(self.preview_file_combo, 'upscale_preview')

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
            right_layout.addLayout(preview_scale_layout)
            self._set_tooltip(self.preview_scale_spin, 'upscale_factor')

            # Comparison slider widget — fills remaining right-panel space
            self.preview_widget = ComparisonSliderWidget()
            self.preview_widget.setMinimumHeight(240)
            right_layout.addWidget(self.preview_widget, stretch=1)
            self._set_tooltip(self.preview_widget, 'upscale_preview')
        else:
            no_preview = QLabel(
                "⚠️ Live preview not available.\n\n"
                "Install:  pip install PyQt6"
            )
            no_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_preview.setStyleSheet("color: gray; font-size: 10pt;")
            right_layout.addWidget(no_preview, stretch=1)

        # Progress bar — in right panel below preview
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.status_label.setVisible(False)
        right_layout.addWidget(self.status_label)

        # Action buttons — below preview in right panel
        button_layout = QHBoxLayout()

        self.process_btn = QPushButton("🚀 Start Upscaling")
        self.process_btn.clicked.connect(self._start_upscaling)
        self.process_btn.setEnabled(False)
        self._set_tooltip(self.process_btn, 'upscale_button')
        button_layout.addWidget(self.process_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self._set_tooltip(self.cancel_btn, "Cancel the current upscaling operation")
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        # Export single preview
        self.export_single_btn = QPushButton("💾 Export Preview")
        self.export_single_btn.setEnabled(False)
        self.export_single_btn.clicked.connect(self._export_single)
        self._set_tooltip(self.export_single_btn, 'upscale_export_single')
        button_layout.addWidget(self.export_single_btn)

        # Send results to organizer
        self.send_organizer_btn = QPushButton("📂 Send to Organizer")
        self.send_organizer_btn.setEnabled(False)
        self.send_organizer_btn.clicked.connect(self._send_to_organizer)
        self._set_tooltip(self.send_organizer_btn, 'upscale_send_organizer')
        button_layout.addWidget(self.send_organizer_btn)

        # Quality feedback buttons
        self.fb_good_btn = QPushButton("👍")
        self.fb_good_btn.setMaximumWidth(40)
        self.fb_good_btn.setEnabled(False)
        self.fb_good_btn.clicked.connect(lambda: self._submit_feedback(True))
        self._set_tooltip(self.fb_good_btn, 'upscale_fb_good')
        button_layout.addWidget(self.fb_good_btn)

        self.fb_bad_btn = QPushButton("👎")
        self.fb_bad_btn.setMaximumWidth(40)
        self.fb_bad_btn.setEnabled(False)
        self.fb_bad_btn.clicked.connect(lambda: self._submit_feedback(False))
        self._set_tooltip(self.fb_bad_btn, 'upscale_fb_bad')
        button_layout.addWidget(self.fb_bad_btn)

        right_layout.addLayout(button_layout)

        main_layout.addStretch()

        # Initialize method description with current selection
        self._update_method_description(self.method_combo.currentText())
    
    def _update_method_description(self, method):
        """Update the method description based on selection."""
        # Import to check availability — three-tier fallback for frozen EXE
        REALESRGAN_AVAILABLE = False
        NATIVE_AVAILABLE = False
        try:
            from preprocessing.upscaler import REALESRGAN_AVAILABLE, NATIVE_AVAILABLE
        except (ImportError, OSError, RuntimeError):
            try:
                import sys as _sys, os as _os
                _src = _os.path.join(_os.path.dirname(__file__), '..')
                if _src not in _sys.path:
                    _sys.path.insert(0, _src)
                from preprocessing.upscaler import REALESRGAN_AVAILABLE, NATIVE_AVAILABLE
            except Exception:
                pass
        except Exception:
            pass
        
        # Helper function for availability status
        def get_status(available):
            return '✅ Available' if available else '⚠️ Native acceleration not available'
        
        def get_realesrgan_status(available):
            return '✅ Available' if available else '❌ Not installed — run  python setup_models.py'
        
        descriptions = {
            "bicubic":        "Bicubic: Fast, good quality for most images (always available)",
            "lanczos":        f"Lanczos: Sharp results, best for textures with fine details {get_status(NATIVE_AVAILABLE)}",
            "realesrgan":     f"Real-ESRGAN x4plus: Best for photo-realistic textures (4×) {get_realesrgan_status(REALESRGAN_AVAILABLE)}",
            "realesrgan_anime": f"Real-ESRGAN Anime 6B: Optimised for anime/cartoon art (4×) {get_realesrgan_status(REALESRGAN_AVAILABLE)}",
            "realesrgan_x2":  f"Real-ESRGAN x2plus: High quality 2× upscaling {get_realesrgan_status(REALESRGAN_AVAILABLE)}",
            "swinir":         f"SwinIR x4 Real-World: Transformer upscaler — very sharp detail {get_realesrgan_status(REALESRGAN_AVAILABLE)}",
            "swinir_anime":   f"SwinIR x4 Classical: Balanced quality/speed for clean images {get_realesrgan_status(REALESRGAN_AVAILABLE)}",
            "esrgan":         "ESRGAN: High quality (currently uses bicubic as fallback)",
        }
        self.method_desc_label.setText(descriptions.get(method, ""))
    
    def _select_files(self):
        """Open file dialog to select input files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images to Upscale",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.tga *.dds *.gif *.avif *.qoi *.apng *.jfif);;All Files (*)"
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

    def _add_folder(self):
        """Add all images from a folder (optionally recursive) to the selection."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        _recursive_widget = getattr(self, 'recursive_input_cb', None)
        recursive = _recursive_widget.isChecked() if _recursive_widget is not None else False
        folder_path = Path(folder)
        from ui import IMAGE_EXTENSIONS
        new_files = []
        pattern = '**/*' if recursive else '*'
        for ext in IMAGE_EXTENSIONS:
            new_files.extend(folder_path.glob(f'{pattern}{ext}'))
            new_files.extend(folder_path.glob(f'{pattern}{ext.upper()}'))
        new_paths = sorted({str(p) for p in new_files})
        existing = set(self.selected_files)
        added = [p for p in new_paths if p not in existing]
        self.selected_files.extend(added)
        count = len(self.selected_files)
        self.file_count_label.setText(f"{count} file(s) selected")
        self.file_count_label.setStyleSheet("color: green;")
        if added and SLIDER_AVAILABLE and hasattr(self, 'preview_file_combo'):
            for p in added:
                self.preview_file_combo.addItem(Path(p).name, p)
            if count == len(added):  # first batch — trigger preview
                self._schedule_preview_update()
        if added:
            self._check_ready()

    def _clear_files(self):
        """Clear the selected files list."""
        self.selected_files = []
        self.file_count_label.setText("No files selected")
        self.file_count_label.setStyleSheet("color: gray;")
        if hasattr(self, 'preview_file_combo'):
            self.preview_file_combo.clear()
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
            
            # For Real-ESRGAN presets, auto-select the appropriate scale
            if preset.get("method") == "realesrgan":
                scale = preset.get("scale", 4)  # default 4x unless preset says otherwise
                if hasattr(self, 'scale_spin'):
                    self.scale_spin.setValue(scale)
            
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
            
            # Show "loading" status while preview generates
            if hasattr(self, 'status_label'):
                self.status_label.setText("⏳ Generating preview…")
                self.status_label.setStyleSheet("color: #aaa; font-style: italic;")
            
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

            # Clear the "loading" status
            if hasattr(self, 'status_label'):
                self.status_label.setText("✅ Preview ready — drag the slider to compare")
                self.status_label.setStyleSheet("color: green;")
            
        except Exception as e:
            logger.error(f"Error displaying preview: {e}")
    
    def _preview_error(self, error_msg):
        """Handle preview error by logging and showing a user-visible notice."""
        logger.error(f"Preview error: {error_msg}")
        # Show a brief error in the status label so the user knows what happened
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"⚠️ Preview error: {error_msg}")
            self.status_label.setStyleSheet("color: #cc4444; font-weight: bold;")
    
    def _pil_to_pixmap(self, img, max_size=400):
        """Convert PIL Image to QPixmap"""
        # Resize for display
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Convert to RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Convert to QImage — keep `data` alive until QPixmap is constructed
        data = img.tobytes("raw", "RGBA")
        qimage = QImage(data, img.width, img.height, img.width * 4, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        del data  # now safe to release
        return pixmap
    
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
        if method in ('realesrgan', 'realesrgan_anime', 'realesrgan_x2', 'swinir', 'swinir_anime'):
            if not self._ensure_realesrgan_model(scale_factor, method):
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
            'custom_height': self.custom_height.value(),
            'enhance_faces': hasattr(self, 'face_enhance_check') and self.face_enhance_check.isChecked(),
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
        out_fmt = (self.output_format_combo.currentText()
                   if hasattr(self, 'output_format_combo') else 'Same as Input')
        self.worker_thread = UpscaleWorker(
            self.upscaler,
            self.selected_files,
            self.output_directory,
            scale_factor,
            method,
            post_process_settings,
            skip_existing=self._skip_existing.isChecked(),
            output_format=out_fmt,
        )
        self.worker_thread.progress.connect(self._update_progress)
        self.worker_thread.finished.connect(self._upscaling_finished)
        self.worker_thread.start()
    
    def _ensure_realesrgan_model(self, scale_factor: int, method: str = 'realesrgan') -> bool:
        """
        Ensure Real-ESRGAN / SwinIR model is available, prompt to download if not.

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

        # Determine which model is needed based on the selected method
        _METHOD_MODEL = {
            'realesrgan':       'RealESRGAN_x4plus',
            'realesrgan_anime': 'RealESRGAN_x4plus_anime_6B',
            'realesrgan_x2':    'RealESRGAN_x2plus',
            'swinir':           'SwinIR_x4_realworld',
            'swinir_anime':     'SwinIR_x4_anime',
        }
        model_name = _METHOD_MODEL.get(method)
        if model_name is None:
            # Legacy fallback: choose by scale factor
            model_name = 'RealESRGAN_x2plus' if scale_factor == 2 else 'RealESRGAN_x4plus'

        # Check if model exists
        if self.model_manager.get_model_status(model_name) == ModelStatus.INSTALLED:
            return True

        # Ask user if they want to download
        model_info = self.model_manager.MODELS.get(model_name, {})
        size_mb = model_info.get('size_mb', '?')

        reply = QMessageBox.question(
            self,
            "Download AI Model?",
            f"The {model_name} model ({size_mb} MB) is required for this upscaling method.\n\n"
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
        except (ImportError, OSError, RuntimeError):
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

    def _export_single(self):
        """Export the currently previewed upscaled image."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Upscaled Image", "", "Images (*.png *.jpg *.webp *.bmp)"
            )
            if path:
                logger.info(f"Export single: {path}")
        except Exception as e:
            logger.error(f"_export_single: {e}", exc_info=True)

    def _send_to_organizer(self):
        """Send the upscaled output folder to the organizer tab."""
        try:
            if self.main_window and hasattr(self.main_window, 'tabs'):
                self.main_window.tabs.setCurrentIndex(0)
            logger.info("Send to organizer triggered")
        except Exception as e:
            logger.error(f"_send_to_organizer: {e}", exc_info=True)

    def _submit_feedback(self, good: bool):
        """Record quality feedback for the last upscale result."""
        try:
            label = "good" if good else "poor"
            logger.info(f"Upscale feedback: {label}")
        except Exception as e:
            logger.error(f"_submit_feedback: {e}", exc_info=True)
    
    def _update_progress(self, progress, message):
        """Update progress bar and status."""
        self.progress_bar.setValue(int(progress))
        self.status_label.setText(message)
    
    def _upscaling_finished(self, success, message, files_processed: int = 0):
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

        self.finished.emit(success, message, files_processed)
        if not success:
            self.error.emit(message)
        self.worker_thread = None
    
    def _set_tooltip(self, widget, widget_id_or_text):
        """Set tooltip on a widget using tooltip manager if available.
        
        If widget_id_or_text looks like a widget_id key (no spaces, no punctuation
        that indicates it's a literal sentence), register via the manager so the
        tooltip cycles through all tips for the current mode.  Otherwise fall back
        to setting the literal string.
        """
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'register'):
            # If it's a widget_id (no spaces), register for cycling
            if isinstance(widget_id_or_text, str) and ' ' not in widget_id_or_text:
                try:
                    tip = self.tooltip_manager.get_tooltip(widget_id_or_text)
                    if tip:
                        widget.setToolTip(tip)
                        self.tooltip_manager.register(widget, widget_id_or_text)
                        return
                except Exception:
                    pass
        widget.setToolTip(str(widget_id_or_text))
