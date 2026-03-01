"""
Line Art Converter UI Panel - PyQt6 Version
Provides UI for converting images to line art and stencils
"""


from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Optional

try:
    from ui import IMAGE_EXTENSIONS
except ImportError:
    IMAGE_EXTENSIONS = frozenset({'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.dds', '.tga', '.gif'})
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFileDialog, QMessageBox, QProgressBar, QComboBox,
        QSlider, QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox,
        QScrollArea, QFrame, QTextEdit, QColorDialog, QSplitter
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QPixmap, QImage, QColor
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
    QPushButton = object
    QSlider = object
    QSpinBox = object
    QTextEdit = object
    QVBoxLayout = object
try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, OSError, RuntimeError):
    HAS_PIL = False


try:
    from tools.lineart_converter import (
        LineArtConverter, LineArtSettings,
        ConversionMode, BackgroundMode, MorphologyOperation
    )
    _LINEART_TOOL_AVAILABLE = True
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"lineart_converter tool not available: {_e}")
    LineArtConverter = None  # type: ignore[assignment,misc]
    LineArtSettings = ConversionMode = BackgroundMode = MorphologyOperation = None  # type: ignore[assignment]
    _LINEART_TOOL_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from ui.live_preview_slider_qt import ComparisonSliderWidget
    SLIDER_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    try:
        from live_preview_slider_qt import ComparisonSliderWidget
        SLIDER_AVAILABLE = True
    except (ImportError, OSError, RuntimeError):
        SLIDER_AVAILABLE = False
        ComparisonSliderWidget = None

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")

# Line art presets  (tattoo presets always first)
LINEART_PRESETS = {
    # ── Tattoo presets ─────────────────────────────────────────────────────
    "🪡 Tattoo — Black on Transparent": {
        "desc": "Ultra-clean black lines on a fully transparent background. "
                "Best for tattoo reference sheets, layering in Photoshop, or printing on stencil film.",
        "mode": "pure_black", "threshold": 118, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 192, "contrast": 2.5, "sharpen": True,
        "sharpen_amount": 1.9, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 1,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🪡 Tattoo — Black on White (Stencil Print)": {
        "desc": "Solid black lines on white — ready to print as a tattoo stencil "
                "or thermal transfer sheet.",
        "mode": "pure_black", "threshold": 122, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 190, "contrast": 2.3, "sharpen": True,
        "sharpen_amount": 1.7, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🪡 Tattoo — Fine Line": {
        "desc": "Delicate hairline strokes for contemporary fine-line tattoo artwork. "
                "Preserves thin details; erodes stray noise.",
        "mode": "pure_black", "threshold": 108, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 222, "contrast": 1.9, "sharpen": True,
        "sharpen_amount": 2.6, "morphology": "erode", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 0,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🪡 Tattoo — Bold Traditional": {
        "desc": "Thick bold outlines in American-traditional style. "
                "High contrast, heavily dilated strokes that hold up at any scale.",
        "mode": "pure_black", "threshold": 128, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 172, "contrast": 3.1, "sharpen": True,
        "sharpen_amount": 1.4, "morphology": "dilate", "morph_iter": 2,
        "kernel": 5, "denoise": True, "denoise_size": 3,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    # ── General-purpose presets ────────────────────────────────────────────
    "⭐ Clean Ink Lines": {
        "desc": "Crisp black ink lines — the go-to for most art & game textures",
        "mode": "pure_black", "threshold": 135, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 210, "contrast": 1.6, "sharpen": True,
        "sharpen_amount": 1.3, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "✏️ Pencil Sketch": {
        "desc": "Soft graphite pencil look with natural tonal gradation. "
                "Smooth lines enabled to produce organic, hand-drawn feel.",
        "mode": "sketch", "threshold": 140, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": False,
        "midtone_threshold": 200, "contrast": 1.1, "sharpen": False,
        "sharpen_amount": 1.0, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 1,
        "smooth_lines": True, "smooth_amount": 1.2,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🖊️ Bold Outlines": {
        "desc": "Thick, punchy outlines — great for stickers or cartoon style",
        "mode": "pure_black", "threshold": 145, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 170, "contrast": 2.2, "sharpen": True,
        "sharpen_amount": 1.6, "morphology": "dilate", "morph_iter": 3,
        "kernel": 5, "denoise": True, "denoise_size": 4,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🔍 Fine Detail Lines": {
        "desc": "Preserve intricate details in technical or detailed artwork",
        "mode": "pure_black", "threshold": 125, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 230, "contrast": 1.9, "sharpen": True,
        "sharpen_amount": 2.2, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 0,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "💥 Comic Book Inks": {
        "desc": "High-contrast inks like professional comic book art",
        "mode": "pure_black", "threshold": 115, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 185, "contrast": 2.7, "sharpen": True,
        "sharpen_amount": 2.0, "morphology": "close", "morph_iter": 2,
        "kernel": 3, "denoise": True, "denoise_size": 3,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "📖 Manga Lines": {
        "desc": "Clean adaptive lines suited for manga / anime styles. "
                "Gaussian adaptive threshold preserves panel-boundary precision.",
        "mode": "adaptive", "threshold": 130, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 215, "contrast": 1.7, "sharpen": True,
        "sharpen_amount": 1.5, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🖍️ Coloring Book": {
        "desc": "Thick outlines perfect for coloring books and children's art",
        "mode": "pure_black", "threshold": 140, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 1.5, "sharpen": True,
        "sharpen_amount": 1.0, "morphology": "dilate", "morph_iter": 4,
        "kernel": 7, "denoise": True, "denoise_size": 5,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "📐 Blueprint / Technical": {
        "desc": "Precise technical drawings with clean lines",
        "mode": "pure_black", "threshold": 128, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 1.2, "sharpen": True,
        "sharpen_amount": 1.8, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 1,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "✂️ Stencil / Vinyl Cut": {
        "desc": "Clean shapes optimized for vinyl cutting and stencils",
        "mode": "stencil_1bit", "threshold": 140, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 2.3, "sharpen": True,
        "sharpen_amount": 1.5, "morphology": "close", "morph_iter": 3,
        "kernel": 5, "denoise": True, "denoise_size": 6,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🎨 Watercolor Edges": {
        "desc": "Soft edges with artistic watercolor appearance. "
                "Sketch mode with smoothing gives organic washes and soft detail.",
        "mode": "sketch", "threshold": 135, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": False,
        "midtone_threshold": 190, "contrast": 1.3, "sharpen": False,
        "sharpen_amount": 0.8, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 3,
        "smooth_lines": True, "smooth_amount": 1.8,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🔲 Pixel Art Lines": {
        "desc": "Preserve pixel-perfect edges for retro/pixel art",
        "mode": "threshold", "threshold": 128, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 1.0, "sharpen": False,
        "sharpen_amount": 0.0, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 0,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🌟 High Contrast Edges": {
        "desc": "Maximum contrast with Canny edge detection. "
                "High thresholds pick out the sharpest, most prominent outlines.",
        "mode": "edge_detect", "threshold": 120, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 180, "contrast": 3.0, "sharpen": True,
        "sharpen_amount": 2.5, "morphology": "dilate", "morph_iter": 2,
        "kernel": 3, "denoise": False, "denoise_size": 0,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 80, "edge_high": 200, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🖤 Inverted Lines (White on Black)": {
        "desc": "White lines on black background for dark themes",
        "mode": "pure_black", "threshold": 135, "auto_threshold": False,
        "background": "black", "invert": True, "remove_midtones": True,
        "midtone_threshold": 210, "contrast": 1.6, "sharpen": True,
        "sharpen_amount": 1.3, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🎭 Dramatic Shadows": {
        "desc": "Heavy shadows with strong contrast for dramatic effect. "
                "Mean adaptive threshold with large block size for sweeping dark regions.",
        "mode": "adaptive", "threshold": 110, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": False,
        "midtone_threshold": 170, "contrast": 2.5, "sharpen": True,
        "sharpen_amount": 1.8, "morphology": "dilate", "morph_iter": 2,
        "kernel": 5, "denoise": True, "denoise_size": 2,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 15, "adaptive_c": 4.0, "adaptive_method": "mean",
    },
    "📝 Handwriting / Script": {
        "desc": "Preserve delicate script and handwriting details",
        "mode": "pure_black", "threshold": 130, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 220, "contrast": 1.4, "sharpen": True,
        "sharpen_amount": 1.0, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 1,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "⚡ Speed Lines / Action": {
        "desc": "Dynamic speed lines for action and motion effects. "
                "Fine aperture Canny edges catch directional motion strokes.",
        "mode": "edge_detect", "threshold": 140, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 2.0, "sharpen": True,
        "sharpen_amount": 2.0, "morphology": "erode", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 0,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 40, "edge_high": 120, "edge_aperture": 5,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🏞️ Landscape Outlines": {
        "desc": "Natural flowing lines for landscape and environment art. "
                "Gaussian adaptive with smoothing gives organic, rolling edges.",
        "mode": "adaptive", "threshold": 140, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 205, "contrast": 1.5, "sharpen": True,
        "sharpen_amount": 1.2, "morphology": "close", "morph_iter": 1,
        "kernel": 5, "denoise": True, "denoise_size": 3,
        "smooth_lines": True, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 13, "adaptive_c": 3.0, "adaptive_method": "gaussian",
    },
    "🎯 Logo / Icon Prep": {
        "desc": "Clean vectorization-ready lines for logos and icons",
        "mode": "stencil_1bit", "threshold": 135, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 2.0, "sharpen": True,
        "sharpen_amount": 1.5, "morphology": "close", "morph_iter": 2,
        "kernel": 3, "denoise": True, "denoise_size": 4,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
    },
    "🔬 Scientific Illustration": {
        "desc": "Precise lines for scientific diagrams and illustrations",
        "mode": "pure_black", "threshold": 125, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 215, "contrast": 1.3, "sharpen": True,
        "sharpen_amount": 1.6, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 1,
        "smooth_lines": False, "smooth_amount": 1.0,
        "edge_low": 50, "edge_high": 150, "edge_aperture": 3,
        "adaptive_block": 11, "adaptive_c": 2.0, "adaptive_method": "gaussian",
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
                if self.isInterruptionRequested():
                    self.finished.emit(False, f"Cancelled after converting {i} image(s)")
                    return
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


class _FormatConversionWorker(QThread):
    """Worker thread for batch conversion with configurable output format and optional colour layer."""
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(bool, str, int)  # success, message, files_processed

    # PIL save kwargs per extension
    _SAVE_KWARGS: dict = {
        'jpg':  {'quality': 92, 'optimize': True},
        'jpeg': {'quality': 92, 'optimize': True},
        'tiff': {'compression': 'tiff_lzw'},
        'webp': {'quality': 90, 'method': 4},
    }

    def __init__(self, converter, files, output_dir, settings,
                 out_ext: str = 'png', save_color_layer: bool = False,
                 skip_existing: bool = False):
        super().__init__()
        self.converter = converter
        self.files = files
        self.output_dir = Path(output_dir)
        self.settings = settings
        self.out_ext = out_ext.lstrip('.').lower()
        self.save_color_layer = save_color_layer
        self.skip_existing = skip_existing

    def run(self):
        """Execute conversion in background."""
        try:
            done = 0
            skipped = 0
            for i, filepath in enumerate(self.files):
                if self.isInterruptionRequested():
                    self.finished.emit(False, f"Cancelled after converting {done} image(s)", done)
                    return
                src = Path(filepath)
                self.progress.emit(i + 1, len(self.files), src.name)

                original = Image.open(src)
                converted = self.converter.convert(original, self.settings)

                # Ensure correct mode for target format
                out_stem = src.stem
                out_name = f"{out_stem}.{self.out_ext}"
                out_path = self.output_dir / out_name

                if self.skip_existing and out_path.exists():
                    skipped += 1
                    continue

                img_to_save = converted
                if self.out_ext in ('jpg', 'jpeg', 'bmp'):
                    # These formats don't support transparency — flatten to white
                    if img_to_save.mode in ('RGBA', 'LA', 'P'):
                        bg = Image.new('RGB', img_to_save.size, (255, 255, 255))
                        if img_to_save.mode == 'P':
                            img_to_save = img_to_save.convert('RGBA')
                        bg.paste(img_to_save, mask=img_to_save.split()[-1] if img_to_save.mode == 'RGBA' else None)
                        img_to_save = bg
                    elif img_to_save.mode != 'RGB':
                        img_to_save = img_to_save.convert('RGB')

                save_kwargs = self._SAVE_KWARGS.get(self.out_ext, {})
                img_to_save.save(out_path, **save_kwargs)
                done += 1

                # Optionally also save the original colour layer
                if self.save_color_layer:
                    color_name = f"{out_stem}_color.{self.out_ext}"
                    color_path = self.output_dir / color_name
                    color_img = original
                    if self.out_ext in ('jpg', 'jpeg', 'bmp') and color_img.mode != 'RGB':
                        color_img = color_img.convert('RGB')
                    color_img.save(color_path, **save_kwargs)

            parts = [f"Converted {done} image{'s' if done != 1 else ''}"]
            if skipped:
                parts.append(f"{skipped} skipped (already existed)")
            self.finished.emit(True, ", ".join(parts) + " successfully", done)
        except Exception as e:
            logger.error(f"Batch conversion failed: {e}")
            self.finished.emit(False, f"Conversion failed: {str(e)}", 0)


class LineArtConverterPanelQt(QWidget):
    """PyQt6 panel for line art conversion."""

    finished = pyqtSignal(bool, str, int)  # success, message, files_processed
    error = pyqtSignal(str)           # error message

    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.converter = LineArtConverter() if LineArtConverter is not None else None
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
        self._set_tooltip(select_btn, 'lineart_input')
        self._set_tooltip(select_btn, 'la_select_preview')

        select_multiple_btn = QPushButton("Select Multiple")
        select_multiple_btn.clicked.connect(self._select_files)
        self._set_tooltip(select_multiple_btn, 'la_select_files')
        self._set_tooltip(select_multiple_btn, 'la_select_folder')
        btn_layout.addWidget(select_multiple_btn)

        add_folder_btn = QPushButton("📂 Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        self._set_tooltip(add_folder_btn, "Add all images from a folder to the selection")
        btn_layout.addWidget(add_folder_btn)

        group_layout.addLayout(btn_layout)

        # Recursive checkbox
        self.recursive_cb = QCheckBox("Process subfolders")
        self.recursive_cb.setChecked(False)
        self._set_tooltip(self.recursive_cb, "When adding a folder, also include images in sub-folders")
        group_layout.addWidget(self.recursive_cb)
        
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
        group_layout.addLayout(archive_layout)
        
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
        self._set_tooltip(self.preset_combo, 'la_preset')
        self._set_tooltip(self.preset_combo, 'la_save_preset')
        
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

        # Conversion Mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        _mode_items = [
            ("Pure Black Lines",    "pure_black"),
            ("Edge Detection",      "edge_detect"),
            ("Adaptive Threshold",  "adaptive"),
            ("Sketch / Pencil",     "sketch"),
            ("Simple Threshold",    "threshold"),
            ("1-bit Stencil",       "stencil_1bit"),
        ]
        for label, data in _mode_items:
            self.mode_combo.addItem(label, data)
        self.mode_combo.currentIndexChanged.connect(self._schedule_preview_update)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo, 1)
        self._set_tooltip(self.mode_combo, 'la_mode')
        group_layout.addLayout(mode_layout)

        # Invert checkbox
        inv_layout = QHBoxLayout()
        self.invert_cb = QCheckBox("Invert (white lines on dark bg)")
        self.invert_cb.setChecked(False)
        self.invert_cb.stateChanged.connect(self._schedule_preview_update)
        inv_layout.addWidget(self.invert_cb)
        inv_layout.addStretch()
        group_layout.addLayout(inv_layout)
        self._set_tooltip(self.invert_cb, 'la_invert')
        self._set_tooltip(self.invert_cb, 'la_style')

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
        self._set_tooltip(self.threshold_slider, 'la_threshold')
        
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
        self._set_tooltip(self.contrast_spin, 'la_contrast')
        
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
        self._set_tooltip(self.morphology_combo, 'la_morphology')
        
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
        self._set_tooltip(self.morphology_iterations, 'la_morph_iterations')
        
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
        self._set_tooltip(self.kernel_size_spin, 'la_kernel_size')
        
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
        self._set_tooltip(self.sharpen_cb, 'la_sharpen')
        self._set_tooltip(self.sharpen_spin, 'la_sharpen_amount')
        
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
        self._set_tooltip(self.denoise_cb, 'la_denoise')
        self._set_tooltip(self.denoise_size, 'la_denoise_size')
        
        # Checkboxes
        self.auto_threshold_cb = QCheckBox("Auto Threshold")
        self.auto_threshold_cb.stateChanged.connect(self._schedule_preview_update)
        group_layout.addWidget(self.auto_threshold_cb)
        self._set_tooltip(self.auto_threshold_cb, 'la_auto_threshold')
        
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
        self._set_tooltip(self.midtone_spin, 'la_midtone_threshold')
        
        # Remove Midtones
        self.remove_midtones_cb = QCheckBox("Remove midtones")
        self.remove_midtones_cb.setChecked(True)
        self.remove_midtones_cb.stateChanged.connect(self._schedule_preview_update)
        group_layout.addWidget(self.remove_midtones_cb)
        self._set_tooltip(self.remove_midtones_cb, 'la_remove_midtones')

        # ── Background colour ──────────────────────────────────────────────
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background:"))
        self.bg_mode_combo = QComboBox()
        self.bg_mode_combo.addItem("⬜ Transparent (PNG/WebP only)", "transparent")
        self.bg_mode_combo.addItem("⬜ White", "white")
        self.bg_mode_combo.addItem("⬛ Black", "black")
        self.bg_mode_combo.addItem("🎨 Custom colour…", "custom")
        self.bg_mode_combo.currentIndexChanged.connect(self._on_bg_mode_changed)
        bg_layout.addWidget(self.bg_mode_combo, 1)
        self._bg_custom_color = "#ffffff"   # remembered custom colour
        self.bg_custom_swatch = QPushButton()
        self.bg_custom_swatch.setFixedSize(28, 28)
        self._set_tooltip(self.bg_custom_swatch, "Click to pick a custom background colour")
        self.bg_custom_swatch.setStyleSheet(f"background:{self._bg_custom_color}; border:1px solid #888; border-radius:3px;")
        self.bg_custom_swatch.setVisible(False)
        self.bg_custom_swatch.clicked.connect(self._pick_custom_bg_color)
        bg_layout.addWidget(self.bg_custom_swatch)
        group_layout.addLayout(bg_layout)
        self._set_tooltip(self.bg_mode_combo, 'la_background')

        # ── Mode-specific advanced controls (shown/hidden by _on_mode_changed) ─────
        # Edge Detection controls
        self._edge_group = QWidget()
        _eg_layout = QVBoxLayout(self._edge_group)
        _eg_layout.setContentsMargins(0, 0, 0, 0)
        _eg_layout.setSpacing(4)
        _eg_label = QLabel("Edge Detection Controls:")
        _eg_label.setStyleSheet("font-weight:bold; font-size:9pt; color:#8fc; margin-top:4px;")
        _eg_layout.addWidget(_eg_label)
        _el_lo = QHBoxLayout()
        _el_lo.addWidget(QLabel("Low Threshold:"))
        self.edge_low_spin = QSpinBox()
        self.edge_low_spin.setRange(1, 255)
        self.edge_low_spin.setValue(50)
        self.edge_low_spin.valueChanged.connect(self._schedule_preview_update)
        _el_lo.addWidget(self.edge_low_spin)
        _el_lo.addStretch()
        _eg_layout.addLayout(_el_lo)
        self._set_tooltip(self.edge_low_spin, 'lineart_edge_low')
        _eh_lo = QHBoxLayout()
        _eh_lo.addWidget(QLabel("High Threshold:"))
        self.edge_high_spin = QSpinBox()
        self.edge_high_spin.setRange(1, 255)
        self.edge_high_spin.setValue(150)
        self.edge_high_spin.valueChanged.connect(self._schedule_preview_update)
        _eh_lo.addWidget(self.edge_high_spin)
        _eh_lo.addStretch()
        _eg_layout.addLayout(_eh_lo)
        self._set_tooltip(self.edge_high_spin, 'lineart_edge_high')
        _ea_lo = QHBoxLayout()
        _ea_lo.addWidget(QLabel("Aperture:"))
        self.edge_aperture_combo = QComboBox()
        self.edge_aperture_combo.addItem("3 (fine)", 3)
        self.edge_aperture_combo.addItem("5 (medium)", 5)
        self.edge_aperture_combo.addItem("7 (coarse)", 7)
        self.edge_aperture_combo.currentIndexChanged.connect(self._schedule_preview_update)
        _ea_lo.addWidget(self.edge_aperture_combo)
        _ea_lo.addStretch()
        _eg_layout.addLayout(_ea_lo)
        self._set_tooltip(self.edge_aperture_combo, 'lineart_edge_aperture')
        group_layout.addWidget(self._edge_group)
        self._edge_group.setVisible(False)

        # Adaptive Threshold controls
        self._adaptive_group = QWidget()
        _ag_layout = QVBoxLayout(self._adaptive_group)
        _ag_layout.setContentsMargins(0, 0, 0, 0)
        _ag_layout.setSpacing(4)
        _ag_label = QLabel("Adaptive Threshold Controls:")
        _ag_label.setStyleSheet("font-weight:bold; font-size:9pt; color:#8fc; margin-top:4px;")
        _ag_layout.addWidget(_ag_label)
        _ab_lo = QHBoxLayout()
        _ab_lo.addWidget(QLabel("Block Size:"))
        self.adaptive_block_spin = QSpinBox()
        self.adaptive_block_spin.setRange(3, 99)
        self.adaptive_block_spin.setValue(11)
        self.adaptive_block_spin.setSingleStep(2)  # must be odd
        self.adaptive_block_spin.valueChanged.connect(self._ensure_odd_block_size)
        self.adaptive_block_spin.valueChanged.connect(self._schedule_preview_update)
        _ab_lo.addWidget(self.adaptive_block_spin)
        _ab_lo.addStretch()
        _ag_layout.addLayout(_ab_lo)
        self._set_tooltip(self.adaptive_block_spin, 'lineart_adaptive_block')
        _ac_lo = QHBoxLayout()
        _ac_lo.addWidget(QLabel("C Constant:"))
        self.adaptive_c_spin = QDoubleSpinBox()
        self.adaptive_c_spin.setRange(-20.0, 20.0)
        self.adaptive_c_spin.setValue(2.0)
        self.adaptive_c_spin.setSingleStep(0.5)
        self.adaptive_c_spin.valueChanged.connect(self._schedule_preview_update)
        _ac_lo.addWidget(self.adaptive_c_spin)
        _ac_lo.addStretch()
        _ag_layout.addLayout(_ac_lo)
        self._set_tooltip(self.adaptive_c_spin, 'lineart_adaptive_c')
        _am_lo = QHBoxLayout()
        _am_lo.addWidget(QLabel("Method:"))
        self.adaptive_method_combo = QComboBox()
        self.adaptive_method_combo.addItem("Gaussian (smooth)", "gaussian")
        self.adaptive_method_combo.addItem("Mean (sharp)", "mean")
        self.adaptive_method_combo.currentIndexChanged.connect(self._schedule_preview_update)
        _am_lo.addWidget(self.adaptive_method_combo)
        _am_lo.addStretch()
        _ag_layout.addLayout(_am_lo)
        self._set_tooltip(self.adaptive_method_combo, 'lineart_adaptive_method')
        group_layout.addWidget(self._adaptive_group)
        self._adaptive_group.setVisible(False)

        # Smooth Lines controls (for Sketch / Pencil mode)
        self._smooth_group = QWidget()
        _sg_layout = QVBoxLayout(self._smooth_group)
        _sg_layout.setContentsMargins(0, 0, 0, 0)
        _sg_layout.setSpacing(4)
        _sg_label = QLabel("Sketch / Smooth Controls:")
        _sg_label.setStyleSheet("font-weight:bold; font-size:9pt; color:#8fc; margin-top:4px;")
        _sg_layout.addWidget(_sg_label)
        _sl_lo = QHBoxLayout()
        self.smooth_lines_cb = QCheckBox("Smooth Lines")
        self.smooth_lines_cb.setChecked(False)
        self.smooth_lines_cb.stateChanged.connect(self._schedule_preview_update)
        _sl_lo.addWidget(self.smooth_lines_cb)
        self.smooth_amount_spin = QDoubleSpinBox()
        self.smooth_amount_spin.setRange(0.5, 5.0)
        self.smooth_amount_spin.setValue(1.0)
        self.smooth_amount_spin.setSingleStep(0.5)
        self.smooth_amount_spin.valueChanged.connect(self._schedule_preview_update)
        _sl_lo.addWidget(self.smooth_amount_spin)
        _sl_lo.addStretch()
        _sg_layout.addLayout(_sl_lo)
        self._set_tooltip(self.smooth_lines_cb, 'lineart_smooth_lines')
        self._set_tooltip(self.smooth_amount_spin, 'lineart_smooth_amount')
        group_layout.addWidget(self._smooth_group)
        self._smooth_group.setVisible(False)

        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_preview_section(self, layout):
        """Create preview section with zoom/pan controls."""
        group = QGroupBox("👁️ Preview")
        group_layout = QVBoxLayout()

        # ── Zoom / pan toolbar ─────────────────────────────────────────────
        zoom_bar = QHBoxLayout()
        zoom_bar.setSpacing(4)
        self._preview_zoom = 1.0          # current zoom factor

        def _zoom_in():
            self._preview_zoom = min(self._preview_zoom * 1.25, 8.0)
            self._apply_preview_zoom()

        def _zoom_out():
            self._preview_zoom = max(self._preview_zoom / 1.25, 0.25)
            self._apply_preview_zoom()

        def _zoom_fit():
            self._preview_zoom = 1.0
            self._apply_preview_zoom()

        btn_in  = QPushButton("🔍+")
        btn_out = QPushButton("🔍−")
        btn_fit = QPushButton("Fit")
        for b in (btn_in, btn_out, btn_fit):
            b.setFixedWidth(44)
            b.setFixedHeight(24)
        self._set_tooltip(btn_in, 'upscale_zoom_in')
        self._set_tooltip(btn_out, 'upscale_zoom_out')
        self._set_tooltip(btn_fit, 'upscale_zoom_fit')
        btn_in.clicked.connect(_zoom_in)
        btn_out.clicked.connect(_zoom_out)
        btn_fit.clicked.connect(_zoom_fit)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(45)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        zoom_bar.addWidget(btn_out)
        zoom_bar.addWidget(self._zoom_label)
        zoom_bar.addWidget(btn_in)
        zoom_bar.addWidget(btn_fit)
        zoom_bar.addStretch()

        refresh_btn = QPushButton("🔄 Update Preview")
        refresh_btn.setFixedHeight(24)
        refresh_btn.clicked.connect(self._schedule_preview_update)
        self._set_tooltip(refresh_btn, 'la_update_preview')
        zoom_bar.addWidget(refresh_btn)

        group_layout.addLayout(zoom_bar)

        # ── Preview area (scrollable) ──────────────────────────────────────
        if SLIDER_AVAILABLE:
            self.preview_widget = ComparisonSliderWidget()
            self.preview_widget.setMinimumHeight(400)
            # Wrap in QScrollArea for zoom/pan
            from PyQt6.QtWidgets import QScrollArea as _SA
            self._preview_scroll = _SA()
            self._preview_scroll.setWidgetResizable(False)
            self._preview_scroll.setWidget(self.preview_widget)
            self._preview_scroll.setMinimumHeight(400)
            group_layout.addWidget(self._preview_scroll)
            # Scroll-wheel zoom works for both paths
            self._preview_scroll.wheelEvent = self._preview_wheel_event
        else:
            # Fallback: scrollable label
            from PyQt6.QtWidgets import QScrollArea as _SA
            self.preview_label = QLabel("Select an image to see preview")
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setMinimumSize(400, 400)
            self.preview_label.setStyleSheet(
                "border: 2px dashed gray; background-color: #f0f0f0;"
            )
            self._preview_scroll = _SA()
            self._preview_scroll.setWidgetResizable(True)
            self._preview_scroll.setWidget(self.preview_label)
            self._preview_scroll.setMinimumHeight(400)
            group_layout.addWidget(self._preview_scroll)
            self._preview_scroll.wheelEvent = self._preview_wheel_event

        # Live-update note
        preview_note = QLabel("💡 Preview updates live • Scroll to zoom • Drag to pan")
        preview_note.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
        group_layout.addWidget(preview_note)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def _apply_preview_zoom(self):
        """Scale the preview to the current zoom level (works for both label and slider)."""
        pct = int(self._preview_zoom * 100)
        if hasattr(self, '_zoom_label'):
            self._zoom_label.setText(f"{pct}%")
        try:
            if hasattr(self, 'preview_label'):
                pm = self.preview_label.property('_original_pixmap')
                if pm and not pm.isNull():
                    w = max(1, int(pm.width() * self._preview_zoom))
                    h = max(1, int(pm.height() * self._preview_zoom))
                    self.preview_label.setPixmap(pm.scaled(
                        w, h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    ))
                    self.preview_label.resize(w, h)
            elif hasattr(self, 'preview_widget') and SLIDER_AVAILABLE:
                # Scale the ComparisonSliderWidget inside its scroll area.
                # Use a fixed 600-px base so zoom works even before the widget is first shown.
                pw = self.preview_widget
                base_w = getattr(pw, '_base_w', 600)
                base_h = getattr(pw, '_base_h', 450)
                nw = max(200, int(base_w * self._preview_zoom))
                nh = max(200, int(base_h * self._preview_zoom))
                pw.setFixedSize(nw, nh)
        except Exception:
            pass

    def _preview_wheel_event(self, event):
        """Zoom the preview on Ctrl+Scroll (or plain scroll)."""
        try:
            delta = event.angleDelta().y()
            if delta > 0:
                self._preview_zoom = min(self._preview_zoom * 1.15, 8.0)
            elif delta < 0:
                self._preview_zoom = max(self._preview_zoom / 1.15, 0.25)
            self._apply_preview_zoom()
            event.accept()
        except Exception:
            pass

    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        # Output format selector
        fmt_group = QGroupBox("📤 Output Format")
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel("Save as:"))
        self.output_format_combo = QComboBox()
        for label, ext in [
            ("PNG (lossless, transparency)", "png"),
            ("JPEG (small file size)", "jpg"),
            ("TIFF (professional, lossless)", "tiff"),
            ("BMP (uncompressed)", "bmp"),
            ("WebP (modern, small size)", "webp"),
        ]:
            self.output_format_combo.addItem(label, ext)
        fmt_layout.addWidget(self.output_format_combo, 1)
        self._set_tooltip(self.output_format_combo, 'la_export')

        self.save_color_layer_cb = QCheckBox("Also save colour layer")
        self._set_tooltip(
            self.save_color_layer_cb,
            "In addition to the line art output, also save the original colour image "
            "in the same folder with a '_color' suffix."
        )
        fmt_layout.addWidget(self.save_color_layer_cb)
        fmt_group.setLayout(fmt_layout)
        layout.addWidget(fmt_group)

        # Convert + cancel button row
        _conv_row = QHBoxLayout()
        self.convert_button = QPushButton("🚀 Convert Selected Files")
        self.convert_button.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        self.convert_button.clicked.connect(self._convert_batch)
        _conv_row.addWidget(self.convert_button)
        self._set_tooltip(self.convert_button, 'la_convert')

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self._cancel_btn.clicked.connect(self._cancel_batch)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setVisible(False)
        self._set_tooltip(self._cancel_btn, 'stop_button')
        _conv_row.addWidget(self._cancel_btn)
        layout.addLayout(_conv_row)

        # Browse output directory
        self.browse_output_btn = QPushButton("📂 Browse Output Folder")
        self.browse_output_btn.clicked.connect(self._browse_output_dir)
        self._set_tooltip(self.browse_output_btn, 'la_browse_output')
        layout.addWidget(self.browse_output_btn)

        self._skip_existing = QCheckBox("Skip if output file already exists")
        self._skip_existing.setChecked(False)
        self._set_tooltip(self._skip_existing, "When checked, files are not re-converted if the output already exists")
        layout.addWidget(self._skip_existing)

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
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.tga *.dds *.gif);;All Files (*.*)"
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
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.tga *.dds *.gif);;All Files (*.*)"
        )

        if files:
            self.selected_files = files
            self.selected_file = files[0]
            self.file_label.setText(f"{len(files)} files selected")
            self.file_label.setStyleSheet("color: green; font-weight: bold;")
            self._schedule_preview_update()

    def _add_folder(self):
        """Add all images from a folder (optionally recursive) to the selection."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        recursive = hasattr(self, 'recursive_cb') and self.recursive_cb.isChecked()
        folder_path = Path(folder)
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
        self.file_label.setText(f"{count} file{'s' if count != 1 else ''} selected")
        self.file_label.setStyleSheet("color: green; font-weight: bold;")
        if added and not self.selected_file:
            self.selected_file = added[0]
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
            self.sharpen_spin.setValue(preset.get("sharpen_amount", 1.3))
            self.denoise_cb.setChecked(preset["denoise"])
            self.denoise_size.setValue(preset.get("denoise_size", 2))

            # Conversion mode
            if hasattr(self, 'mode_combo'):
                mode_val = preset.get("mode", "pure_black")
                for i in range(self.mode_combo.count()):
                    if self.mode_combo.itemData(i) == mode_val:
                        self.mode_combo.setCurrentIndex(i)
                        break

            # Invert
            if hasattr(self, 'invert_cb'):
                self.invert_cb.setChecked(bool(preset.get("invert", False)))

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

            # Background mode
            if hasattr(self, 'bg_mode_combo'):
                bg_val = preset.get("background", "transparent")
                for i in range(self.bg_mode_combo.count()):
                    if self.bg_mode_combo.itemData(i) == bg_val:
                        self.bg_mode_combo.setCurrentIndex(i)
                        break

            # Edge detection params
            if hasattr(self, 'edge_low_spin'):
                self.edge_low_spin.setValue(preset.get("edge_low", 50))
            if hasattr(self, 'edge_high_spin'):
                self.edge_high_spin.setValue(preset.get("edge_high", 150))
            if hasattr(self, 'edge_aperture_combo'):
                ap = preset.get("edge_aperture", 3)
                for i in range(self.edge_aperture_combo.count()):
                    if self.edge_aperture_combo.itemData(i) == ap:
                        self.edge_aperture_combo.setCurrentIndex(i)
                        break
            # Adaptive threshold params
            if hasattr(self, 'adaptive_block_spin'):
                self.adaptive_block_spin.setValue(preset.get("adaptive_block", 11))
            if hasattr(self, 'adaptive_c_spin'):
                self.adaptive_c_spin.setValue(preset.get("adaptive_c", 2.0))
            if hasattr(self, 'adaptive_method_combo'):
                meth = preset.get("adaptive_method", "gaussian")
                for i in range(self.adaptive_method_combo.count()):
                    if self.adaptive_method_combo.itemData(i) == meth:
                        self.adaptive_method_combo.setCurrentIndex(i)
                        break
            # Smooth lines params
            if hasattr(self, 'smooth_lines_cb'):
                self.smooth_lines_cb.setChecked(bool(preset.get("smooth_lines", False)))
            if hasattr(self, 'smooth_amount_spin'):
                self.smooth_amount_spin.setValue(preset.get("smooth_amount", 1.0))

            # Trigger mode-specific panel visibility update, then preview update
            self._on_mode_changed()
            self._schedule_preview_update()
    
    def _on_bg_mode_changed(self, index: int):
        """Show/hide the custom colour swatch, then trigger a preview update."""
        is_custom = (self.bg_mode_combo.currentData() == "custom") if hasattr(self, 'bg_mode_combo') else False
        if hasattr(self, 'bg_custom_swatch'):
            self.bg_custom_swatch.setVisible(is_custom)
        self._schedule_preview_update()

    def _on_mode_changed(self, _index: int = 0):
        """Show/hide mode-specific advanced control groups."""
        mode = self.mode_combo.currentData() if hasattr(self, 'mode_combo') else "pure_black"
        if hasattr(self, '_edge_group'):
            self._edge_group.setVisible(mode == "edge_detect")
        if hasattr(self, '_adaptive_group'):
            self._adaptive_group.setVisible(mode == "adaptive")
        if hasattr(self, '_smooth_group'):
            self._smooth_group.setVisible(mode == "sketch")

    def _ensure_odd_block_size(self, value: int):
        """Adaptive block size must be an odd integer ≥ 3."""
        if hasattr(self, 'adaptive_block_spin') and value % 2 == 0:
            self.adaptive_block_spin.setValue(value + 1)

    def _pick_custom_bg_color(self):
        """Open a colour-picker dialog for custom background colour."""
        try:
            from PyQt6.QtWidgets import QColorDialog as _QCD
            from PyQt6.QtGui import QColor as _QC
            initial = _QC(self._bg_custom_color)
            color = _QCD.getColor(initial, self, "Pick Background Colour")
            if color.isValid():
                self._bg_custom_color = color.name()
                self.bg_custom_swatch.setStyleSheet(
                    f"background:{self._bg_custom_color}; border:1px solid #888; border-radius:3px;"
                )
                self._schedule_preview_update()
        except Exception:
            pass

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
        # Conversion mode from combo
        _MODE_MAP = {
            "pure_black":  getattr(ConversionMode, 'PURE_BLACK',   None) if ConversionMode else None,
            "edge_detect": getattr(ConversionMode, 'EDGE_DETECT',  None) if ConversionMode else None,
            "adaptive":    getattr(ConversionMode, 'ADAPTIVE',     None) if ConversionMode else None,
            "sketch":      getattr(ConversionMode, 'SKETCH',       None) if ConversionMode else None,
            "threshold":   getattr(ConversionMode, 'THRESHOLD',    None) if ConversionMode else None,
            "stencil_1bit":getattr(ConversionMode, 'STENCIL_1BIT', None) if ConversionMode else None,
        }
        mode_key = "pure_black"
        if hasattr(self, 'mode_combo') and ConversionMode:
            mode_key = self.mode_combo.currentData() or "pure_black"
        conv_mode = _MODE_MAP.get(mode_key) or (ConversionMode.PURE_BLACK if ConversionMode else None)

        # Background mode
        _BG_MAP = {
            "transparent": BackgroundMode.TRANSPARENT if BackgroundMode else None,
            "white":       getattr(BackgroundMode, 'WHITE',  None) if BackgroundMode else None,
            "black":       getattr(BackgroundMode, 'BLACK',  None) if BackgroundMode else None,
            "custom":      getattr(BackgroundMode, 'CUSTOM', None) if BackgroundMode else None,
        }
        bg_key = "transparent"
        if hasattr(self, 'bg_mode_combo'):
            bg_key = self.bg_mode_combo.currentData() or "transparent"
        bg_mode = _BG_MAP.get(bg_key) or (BackgroundMode.TRANSPARENT if BackgroundMode else None)
        # Fall back to WHITE if CUSTOM enum member not yet present in the installed backend
        if bg_mode is None and bg_key == "custom":
            bg_mode = getattr(BackgroundMode, 'WHITE', None) if BackgroundMode else None

        # Custom background colour (used when BackgroundMode.CUSTOM)
        custom_bg = getattr(self, '_bg_custom_color', '#ffffff')

        # Invert
        invert = self.invert_cb.isChecked() if hasattr(self, 'invert_cb') else False

        # Edge detection params (active when mode == edge_detect)
        edge_low  = self.edge_low_spin.value()  if hasattr(self, 'edge_low_spin')  else 50
        edge_high = self.edge_high_spin.value() if hasattr(self, 'edge_high_spin') else 150
        edge_ap   = self.edge_aperture_combo.currentData() if hasattr(self, 'edge_aperture_combo') else 3

        # Adaptive threshold params (active when mode == adaptive)
        ada_block = self.adaptive_block_spin.value() if hasattr(self, 'adaptive_block_spin') else 11
        ada_c     = self.adaptive_c_spin.value()     if hasattr(self, 'adaptive_c_spin')     else 2.0
        ada_meth  = self.adaptive_method_combo.currentData() if hasattr(self, 'adaptive_method_combo') else 'gaussian'

        # Smooth lines params (active when mode == sketch)
        smooth    = self.smooth_lines_cb.isChecked()  if hasattr(self, 'smooth_lines_cb')  else False
        smooth_am = self.smooth_amount_spin.value()   if hasattr(self, 'smooth_amount_spin') else 1.0

        return LineArtSettings(
            mode=conv_mode,
            threshold=self.threshold_slider.value(),
            auto_threshold=self.auto_threshold_cb.isChecked(),
            background_mode=bg_mode,
            invert=invert,
            remove_midtones=self.remove_midtones_cb.isChecked(),
            midtone_threshold=self.midtone_spin.value(),
            contrast_boost=self.contrast_spin.value(),
            sharpen=self.sharpen_cb.isChecked(),
            sharpen_amount=self.sharpen_spin.value(),
            morphology_operation=self._get_morphology_operation(),
            morphology_iterations=self.morphology_iterations.value(),
            morphology_kernel_size=self.kernel_size_spin.value(),
            denoise=self.denoise_cb.isChecked(),
            denoise_size=self.denoise_size.value(),
            edge_low_threshold=edge_low,
            edge_high_threshold=edge_high,
            edge_aperture_size=edge_ap,
            adaptive_block_size=ada_block,
            adaptive_c_constant=ada_c,
            adaptive_method=ada_meth,
            smooth_lines=smooth,
            smooth_amount=smooth_am,
            custom_bg_color=custom_bg,
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
                # Record image dimensions as zoom base so zoom buttons work correctly
                if not orig_pixmap.isNull():
                    self.preview_widget._base_w = max(200, orig_pixmap.width())
                    self.preview_widget._base_h = max(200, orig_pixmap.height())
                    # Apply current zoom
                    self._apply_preview_zoom()
            elif hasattr(self, 'preview_label'):
                # Fallback to scrollable/zoomable label
                processed_rgb = processed.convert("RGBA")
                data = processed_rgb.tobytes("raw", "RGBA")
                qimage = QImage(data, processed_rgb.width, processed_rgb.height, QImage.Format.Format_RGBA8888)

                # Store full-resolution pixmap so zoom can re-scale it
                pixmap = QPixmap.fromImage(qimage)
                self.preview_label.setProperty('_original_pixmap', pixmap)

                # Apply current zoom level
                zoom = getattr(self, '_preview_zoom', 1.0)
                w = int(pixmap.width()  * zoom)
                h = int(pixmap.height() * zoom)
                scaled = pixmap.scaled(
                    w, h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)
                self.preview_label.resize(scaled.width(), scaled.height())
            
        except Exception as e:
            logger.error(f"Error displaying preview: {e}")
            if hasattr(self, 'preview_label'):
                self.preview_label.setText(f"Error: {str(e)}")

    
    def _pil_to_pixmap(self, img, max_size=600):
        """Convert PIL Image to QPixmap (600 px max for quality preview)."""
        img = img.copy()
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        data = img.tobytes("raw", "RGBA")
        qimage = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimage)
    
    def _preview_error(self, error_msg):
        """Handle preview error."""
        if hasattr(self, 'preview_label'):
            self.preview_label.setText(f"Error: {error_msg}")

    def _browse_output_dir(self):
        """Let the user pre-select the output directory for conversions."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
            if path:
                self._preset_output_dir = path
                logger.info(f"Lineart output directory pre-set to: {path}")
        except Exception as e:
            logger.error(f"_browse_output_dir: {e}", exc_info=True)
    
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
            # Resolve selected output format (from combo, default png)
            out_ext = "png"
            try:
                out_ext = self.output_format_combo.currentData() or "png"
            except Exception:
                pass

            save_color = False
            try:
                save_color = self.save_color_layer_cb.isChecked()
            except Exception:
                pass

            # Create settings from current controls
            settings = self._create_settings_from_controls()

            # Start conversion worker with format args
            self.conversion_worker = _FormatConversionWorker(
                self.converter,
                self.selected_files,
                output_dir,
                settings,
                out_ext=out_ext,
                save_color_layer=save_color,
                skip_existing=self._skip_existing.isChecked(),
            )
            self.conversion_worker.progress.connect(self._on_conversion_progress)
            self.conversion_worker.finished.connect(self._on_conversion_finished)
            self.conversion_worker.start()

            self.convert_button.setEnabled(False)
            if hasattr(self, '_cancel_btn'):
                self._cancel_btn.setEnabled(True)
                self._cancel_btn.setVisible(True)
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
    
    def _on_conversion_finished(self, success, message, files_processed: int = 0):
        """Handle conversion completion."""
        self.progress_bar.setVisible(False)
        self.convert_button.setEnabled(True)
        if hasattr(self, '_cancel_btn'):
            self._cancel_btn.setEnabled(False)
            self._cancel_btn.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Complete", message)
            self.progress_label.setText("✓ Conversion complete")
        else:
            QMessageBox.critical(self, "Error", message)
            self.progress_label.setText("✗ Conversion failed")
        self.finished.emit(success, message, files_processed)

    def _cancel_batch(self):
        """Cancel the running batch conversion."""
        if hasattr(self, 'conversion_worker') and self.conversion_worker and self.conversion_worker.isRunning():
            self.conversion_worker.requestInterruption()
            if hasattr(self, '_cancel_btn'):
                self._cancel_btn.setEnabled(False)
            self.progress_label.setText("Cancelling…")

    def _set_tooltip(self, widget, widget_id_or_text):
        """Set tooltip on a widget using tooltip manager if available."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'register'):
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
