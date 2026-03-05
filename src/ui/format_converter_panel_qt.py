"""
Format Converter Panel — PyQt6
Batch-converts images between formats with quality, resize, and colour-space options.
"""
from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTextEdit, QFileDialog, QProgressBar, QGroupBox, QComboBox,
        QSpinBox, QDoubleSpinBox, QCheckBox, QSplitter, QScrollArea,
        QFrame, QLineEdit, QGridLayout, QSizePolicy, QMessageBox,
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
    from PyQt6.QtGui import QPixmap, QImageReader
    _PYQT = True
except (ImportError, OSError, RuntimeError):
    _PYQT = False
    QWidget = object
    QThread = object
    QFrame = object
    QSplitter = object
    QGroupBox = object
    QScrollArea = object
    class _Stub:
        def __init__(self, *a, **k): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _Stub()  # noqa: E302
    class Qt:  # noqa: E302
        class AlignmentFlag:
            AlignLeft = AlignRight = AlignCenter = AlignTop = AlignHCenter = AlignVCenter = 0
        class Orientation:
            Horizontal = Vertical = 0

try:
    from PIL import Image
    _PIL = True
except (ImportError, OSError):
    _PIL = False

# ── SVG rasterisation via Qt ───────────────────────────────────────────────────
# Qt ships an SVG renderer in PyQt6.QtSvg (no extra package needed).
# We rasterise the SVG at a user-specified DPI and return a PIL Image.
# Falls back gracefully to cairosvg when available, then to a placeholder.
_SVG_AVAILABLE: bool = False
try:
    from PyQt6.QtSvg import QSvgRenderer as _QSvgRenderer
    from PyQt6.QtGui import QImage as _QImage, QPainter as _QPainter
    from PyQt6.QtCore import QByteArray as _QByteArray
    _SVG_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    _QSvgRenderer = None  # type: ignore

_SVG_NOTE_MSG = (
    "⚠️ SVG rasterisation uses Qt's built-in renderer.\n"
    "For better accuracy install cairosvg:  pip install cairosvg"
)


def _rasterise_svg(path: Path, dpi: int = 96) -> "Image.Image":
    """Convert an SVG file to a PIL RGBA Image at *dpi* dots-per-inch.

    Strategy (in priority order):
    1. cairosvg — if installed, highest accuracy for complex SVGs.
    2. PyQt6.QtSvg.QSvgRenderer — built-in, no extra dependency.
    3. Raise RuntimeError so the caller can report a friendly message.
    """
    # 1 — cairosvg (optional, best quality)
    try:
        import cairosvg as _cairosvg  # type: ignore
        import io as _io
        png_bytes = _cairosvg.svg2png(url=str(path), dpi=dpi)
        return Image.open(_io.BytesIO(png_bytes)).convert("RGBA")
    except (ImportError, Exception):
        pass

    # 2 — Qt SVG renderer
    if _QSvgRenderer is not None:
        renderer = _QSvgRenderer(str(path))
        if not renderer.isValid():
            raise RuntimeError(f"Qt SVG renderer could not parse '{path.name}'")
        size = renderer.defaultSize()
        # Scale from the SVG's logical 96-dpi grid to the requested DPI
        scale = dpi / 96.0
        w = max(1, round(size.width() * scale))
        h = max(1, round(size.height() * scale))
        qi = _QImage(w, h, _QImage.Format.Format_ARGB32_Premultiplied)
        qi.fill(0)  # transparent
        p = _QPainter(qi)
        renderer.render(p)
        p.end()
        # Convert QImage → PIL Image via raw bytes
        ptr = qi.bits()
        ptr.setsize(qi.sizeInBytes())
        buf = bytes(ptr)
        pil = Image.frombytes("RGBA", (w, h), buf, "raw", "BGRA")
        # Qt stores pixels as BGRA (B in the lowest byte), while PIL expects RGBA.
        # Passing "BGRA" as the raw decoder mode tells Pillow to swap the channel
        # order, converting Qt's native layout into a standard RGBA PIL Image.
        return pil

    raise RuntimeError(
        "SVG rasterisation unavailable.\n"
        "Install cairosvg:  pip install cairosvg\n"
        "or ensure PyQt6.QtSvg is importable."
    )

# ── AVIF plugin: auto-register when pillow-avif-plugin is installed ────────────
# pillow-avif-plugin ships a pre-built libaom wheel (Windows/macOS/Linux).
# Importing it registers the AVIF codec with Pillow automatically, so
# Image.save(…, format="AVIF") works without any extra steps.
_AVIF_AVAILABLE: bool = False
if _PIL:
    try:
        import pillow_avif  # noqa: F401 — side-effect: registers AVIF codec
        _AVIF_AVAILABLE = True
    except (ImportError, OSError, Exception):
        _AVIF_AVAILABLE = False

# ─── Format definitions ──────────────────────────────────────────────────────
_INPUT_EXTS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif",
    ".webp", ".tga", ".gif", ".ico", ".psd",
    # Vector formats (rasterised at runtime)
    ".svg",
    # Additional game/HDR/modern formats
    ".dds", ".hdr", ".exr", ".avif", ".jp2", ".j2k",
    ".pbm", ".pgm", ".ppm", ".pnm", ".xbm", ".xpm",
    ".cur", ".pcx", ".sgi", ".rgb", ".rgba", ".im",
    # Modern lossless and icon formats
    ".qoi", ".icns", ".apng", ".jfif",
}

# User-facing message shown when AVIF encoding is unavailable.
_AVIF_UNAVAILABLE_MSG = (
    "AVIF encoder not available.\n"
    "Pillow needs to be built with libaom support.\n"
    "Run  python setup_models.py  or:  pip install pillow-avif-plugin\n"
    "Alternatively, convert to WebP or PNG."
)
# Shorter version for UI labels
_AVIF_NOTE_MSG = (
    "⚠️ AVIF requires Pillow built with libaom.\n"
    "Run  python setup_models.py  or install:  pip install pillow-avif-plugin"
)

_OUTPUT_FORMATS: List[Tuple[str, str, str]] = [
    # (display_label, extension, PIL_save_format)
    ("PNG (lossless, alpha)",          ".png",  "PNG"),
    ("JPEG / JPG (lossy, no alpha)",   ".jpg",  "JPEG"),
    ("WebP (lossy+lossless)",          ".webp", "WEBP"),
    ("TIFF (lossless, layered)",       ".tiff", "TIFF"),
    ("BMP (uncompressed)",             ".bmp",  "BMP"),
    ("TGA / Targa (game-ready)",       ".tga",  "TGA"),
    ("ICO (icon, max 256×256)",        ".ico",  "ICO"),
    ("ICNS (macOS icon bundle)",       ".icns", "ICNS"),
    ("GIF (256 colours)",              ".gif",  "GIF"),
    ("QOI (fast lossless)",            ".qoi",  "QOI"),
    ("JPEG 2000 (lossless)",           ".jp2",  "JPEG2000"),
    ("AVIF (modern, very small)",      ".avif", "AVIF"),
]

_COLOUR_SPACES: List[Tuple[str, str]] = [
    ("Keep original",   "keep"),
    ("RGBA (32-bit)",   "RGBA"),
    ("RGB (24-bit)",    "RGB"),
    ("Grayscale (L)",   "L"),
    ("1-bit B&W",       "1"),
]

_RESIZE_MODES: List[Tuple[str, str]] = [
    ("Keep original size",      "keep"),
    ("Scale by percentage",     "percent"),
    ("Scale to max dimension",  "max_dim"),
    ("Fixed width × height",    "fixed"),
    ("Power-of-two (up)",       "pot_up"),
    ("Power-of-two (down)",     "pot_down"),
]

# Shared stylesheet for informational format notes in _on_fmt_changed
_INFO_NOTE_STYLE = "color: #5588cc; font-size: 9pt; font-style: italic;"


def _make_square(img: "Image.Image") -> "Image.Image":
    """Return a square version of *img* by centre-padding the shorter side.

    Used by the ICNS encoder which requires a 1:1 aspect ratio.
    If the image is already square, it is returned unchanged.
    """
    if img.width == img.height:
        return img
    side = max(img.width, img.height)
    mode = img.mode if img.mode in ("RGBA", "LA") else "RGBA"
    if _PIL:
        sq = Image.new(mode, (side, side), (0, 0, 0, 0))
        sq.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
        return sq
    return img


# ─── Worker thread ────────────────────────────────────────────────────────────
class _ConvertWorker(QThread):
    """Runs the conversion in a background thread."""
    progress   = pyqtSignal(int, int, str)   # done, total, filename
    log_msg    = pyqtSignal(str)
    finished   = pyqtSignal(bool, str, int)  # success, message, count

    def __init__(self, files: List[Path], settings: dict, parent=None):
        super().__init__(parent)
        self._files    = files
        self._settings = settings
        self._cancel   = False

    def cancel(self):
        self._cancel = True

    def run(self):
        if not _PIL:
            self.finished.emit(False, "Pillow not installed — cannot convert images", 0)
            return
        s         = self._settings
        out_dir   = Path(s["out_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        out_ext   = s["out_ext"]
        pil_fmt   = s["pil_fmt"]
        colour    = s["colour"]
        resize_md = s["resize_mode"]
        jpeg_q    = s["jpeg_quality"]
        png_cmp   = s["png_compress"]
        webp_q    = s["webp_quality"]
        webp_ll   = s["webp_lossless"]
        strip_xmp = s["strip_metadata"]
        skip_existing = s.get("skip_existing", False)
        name_tpl  = s["name_template"]  # e.g. "{stem}{ext}"
        suffix    = s.get("name_suffix", "")
        svg_dpi   = s.get("svg_dpi", 96)
        total     = len(self._files)
        done      = 0
        errors    = 0
        skipped   = 0

        for fp in self._files:
            if self._cancel:
                break
            try:
                # Build output path first so we can skip early if needed
                stem = fp.stem + suffix
                out_name = (name_tpl
                            .replace("{stem}", stem)
                            .replace("{ext}", out_ext)
                            .replace("{name}", fp.name))
                out_path = out_dir / out_name
                # Guard: never overwrite the source file
                if out_path.resolve() == fp.resolve():
                    out_path = out_dir / (fp.stem + "_converted" + out_ext)

                if skip_existing and out_path.exists():
                    skipped += 1
                    self.log_msg.emit(f"⏭️ Skipped (exists): {out_path.name}")
                    self.progress.emit(done + errors + skipped, total, fp.name)
                    continue

                # ── Load image (SVG rasterised via Qt/cairosvg) ──────────
                if fp.suffix.lower() == ".svg":
                    try:
                        img = _rasterise_svg(fp, dpi=svg_dpi)
                    except Exception as svg_exc:
                        raise RuntimeError(
                            f"SVG rasterisation failed for '{fp.name}': {svg_exc}"
                        )
                else:
                    img = Image.open(fp)
                    img.load()  # force decode (catches lazy errors)

                # ── Colour conversion ─────────────────────────────────────
                if colour != "keep":
                    if colour == "RGBA" and pil_fmt in ("JPEG", "BMP"):
                        # JPEG/BMP cannot store alpha — flatten to RGB
                        bg = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode in ("RGBA", "LA", "PA"):
                            bg.paste(img, mask=img.split()[-1])
                        else:
                            bg.paste(img.convert("RGB"))
                        img = bg
                    else:
                        target_mode = colour
                        if target_mode == "RGB" and pil_fmt in ("PNG", "TIFF", "WEBP", "TGA"):
                            pass  # allow
                        img = img.convert(target_mode)
                elif pil_fmt == "JPEG" and img.mode in ("RGBA", "LA", "P", "1"):
                    # Auto-flatten alpha for JPEG even when "keep"
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode in ("RGBA", "LA"):
                        bg.paste(img, mask=img.split()[-1])
                    else:
                        bg.paste(img.convert("RGB"))
                    img = bg
                elif pil_fmt == "ICO":
                    img = img.convert("RGBA")
                elif pil_fmt == "ICNS":
                    # ICNS requires a square RGBA image — pad shorter side if needed
                    img = _make_square(img.convert("RGBA"))
                elif pil_fmt == "GIF":
                    # GIF supports only palette / P mode (256 colours)
                    if img.mode not in ("P", "L"):
                        img = img.convert("RGB").quantize(colors=256)

                # ── Resize ────────────────────────────────────────────────
                img = _resize_image(img, resize_md, s)

                # ── Watermark ─────────────────────────────────────────────
                if s.get("watermark_enabled") and s.get("watermark_text"):
                    img = _apply_watermark(img, s)

                # ── ICO size cap ──────────────────────────────────────────
                if pil_fmt == "ICO":
                    img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                elif pil_fmt == "ICNS":
                    # Recommended ICNS sizes: 16, 32, 64, 128, 256, 512, 1024
                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

                # ── Save kwargs ───────────────────────────────────────────
                save_kw: dict = {}
                if pil_fmt == "JPEG":
                    save_kw = {"quality": jpeg_q, "optimize": True}
                    if strip_xmp:
                        save_kw["exif"] = b""
                elif pil_fmt == "PNG":
                    save_kw = {"compress_level": png_cmp, "optimize": True}
                elif pil_fmt == "WEBP":
                    save_kw = {"quality": webp_q, "lossless": webp_ll}
                elif pil_fmt == "TIFF":
                    save_kw = {"compression": "tiff_lzw"}
                elif pil_fmt == "AVIF":
                    save_kw = {"quality": webp_q}
                elif pil_fmt == "JPEG2000":
                    save_kw = {"quality_mode": "lossless"}

                # ── Early AVIF check — skip inference if plugin absent ───────
                if pil_fmt == "AVIF" and not _AVIF_AVAILABLE:
                    raise RuntimeError(_AVIF_UNAVAILABLE_MSG)

                try:
                    img.save(out_path, format=pil_fmt, **save_kw)
                except Exception as save_exc:
                    # Provide a friendlier message for the very common "no AVIF encoder" error
                    exc_str = str(save_exc)
                    if pil_fmt == "AVIF" and (
                        "encoder avif not available" in exc_str.lower()
                        or "libaom" in exc_str.lower()
                        or "avif" in exc_str.lower()
                    ):
                        raise RuntimeError(_AVIF_UNAVAILABLE_MSG) from save_exc
                    raise
                done += 1
                self.log_msg.emit(f"✅ {fp.name}  →  {out_path.name}")
            except Exception as exc:
                errors += 1
                self.log_msg.emit(f"❌ {fp.name}: {exc}")
                logger.warning(f"Format convert: {fp}: {exc}")

            self.progress.emit(done + errors + skipped, total, fp.name)

        ok  = errors == 0
        _parts = [f"{done} converted", f"{errors} errors"]
        if skipped:
            _parts.append(f"{skipped} skipped")
        msg = f"Done — {', '.join(_parts)}"
        self.progress.emit(total, total, "Done")
        self.finished.emit(ok, msg, done)


def _resize_image(img: "Image.Image", mode: str, s: dict) -> "Image.Image":
    """Resize `img` according to settings dict `s`."""
    if mode == "keep":
        return img
    w, h = img.size
    if mode == "percent":
        pct = s.get("resize_percent", 100) / 100.0
        nw, nh = max(1, int(w * pct)), max(1, int(h * pct))
    elif mode == "max_dim":
        mx = s.get("resize_max_dim", 1024)
        scale = mx / max(w, h) if max(w, h) > 0 else 1.0
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    elif mode == "fixed":
        nw = s.get("resize_fixed_w", w)
        nh = s.get("resize_fixed_h", h)
    elif mode == "pot_up":
        nw = 1 << ((w - 1).bit_length())
        nh = 1 << ((h - 1).bit_length())
    elif mode == "pot_down":
        nw = 1 << (max(1, w).bit_length() - 1)
        nh = 1 << (max(1, h).bit_length() - 1)
    else:
        return img
    # LANCZOS is not supported for palette (P) mode — convert to RGB first, resize, then re-quantize
    if img.mode == "P":
        img_rgb = img.convert("RGB")
        resized_rgb = img_rgb.resize((nw, nh), Image.Resampling.LANCZOS)
        return resized_rgb.quantize(colors=256)
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def _apply_watermark(img: "Image.Image", s: dict) -> "Image.Image":
    """Stamp a semi-transparent text watermark onto *img*."""
    try:
        from PIL import Image as _Img, ImageDraw, ImageFont
        text    = s.get("watermark_text", "")
        pos_key = s.get("watermark_pos", "Bottom-right")
        opacity = int(s.get("watermark_opacity", 60) / 100 * 255)

        # Work on an RGBA copy so we can composite
        base = img.convert("RGBA")
        layer = _Img.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        try:
            font = ImageFont.truetype("arial.ttf", max(12, min(base.width, base.height) // 20))
        except OSError:
            font = ImageFont.load_default()

        # Measure text
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except AttributeError:
            tw, th = draw.textsize(text, font=font)  # type: ignore[attr-defined]

        pad = 8
        w, h = base.size
        _positions = {
            "Bottom-right": (w - tw - pad, h - th - pad),
            "Bottom-left":  (pad, h - th - pad),
            "Top-right":    (w - tw - pad, pad),
            "Top-left":     (pad, pad),
            "Center":       ((w - tw) // 2, (h - th) // 2),
        }
        x, y = _positions.get(pos_key, (w - tw - pad, h - th - pad))

        # Draw shadow, then white text
        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, opacity))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))

        combined = _Img.alpha_composite(base, layer)
        # Return in the original mode if it wasn't RGBA
        if img.mode != "RGBA":
            combined = combined.convert(img.mode if img.mode in ("RGB", "L", "P") else "RGB")
        return combined
    except Exception:
        return img  # watermark is optional — never fail the conversion


# ─── Panel ────────────────────────────────────────────────────────────────────
if _PYQT:
    class FormatConverterPanelQt(QWidget):
        """Batch image format converter panel."""

        finished = pyqtSignal(bool, str, int)

        def __init__(self, tooltip_manager=None, parent=None):
            super().__init__(parent)
            self._tooltip_mgr  = tooltip_manager
            self._files: List[Path] = []
            self._worker: Optional[_ConvertWorker] = None
            self.setAcceptDrops(True)  # drag-and-drop files directly onto panel
            self._setup_ui()

        # ── Drag-and-drop support ──────────────────────────────────────────
        def dragEnterEvent(self, event) -> None:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()

        def dropEvent(self, event) -> None:
            """Accept dropped image files and add them to the conversion queue."""
            _EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif',
                     '.webp', '.avif', '.ico', '.svg'}
            added = 0
            for url in event.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.is_file() and path.suffix.lower() in _EXTS:
                    if path not in self._files:
                        self._files.append(path)
                        added += 1
                elif path.is_dir():
                    for child in path.iterdir():
                        if child.suffix.lower() in _EXTS and child not in self._files:
                            self._files.append(child)
                            added += 1
            if added:
                self._file_count_lbl.setText(f"{len(self._files)} file(s) selected")
            event.acceptProposedAction()

        # ── UI construction ────────────────────────────────────────────────
        def _setup_ui(self):
            root = QVBoxLayout(self)
            root.setContentsMargins(8, 8, 8, 8)
            root.setSpacing(6)
            self.setMinimumSize(500, 400)  # prevent squashed layout

            # Title
            title = QLabel("🔄 Format Converter")
            title.setStyleSheet("font-size:15px; font-weight:bold; color:#aee4ff;")
            root.addWidget(title)

            # Splitter: left = settings, right = log
            splitter = QSplitter(Qt.Orientation.Horizontal)
            root.addWidget(splitter, stretch=1)

            # ── Left column (inside a scroll area so it never gets squished) ──
            left_inner = QWidget()
            lv = QVBoxLayout(left_inner)
            lv.setContentsMargins(0, 0, 4, 0)
            lv.setSpacing(6)

            # Input
            inp_box = QGroupBox("📂 Input")
            inp_lay = QVBoxLayout(inp_box)
            inp_lay.setSpacing(4)

            h = QHBoxLayout()
            self._in_dir_edit = QLineEdit()
            self._in_dir_edit.setPlaceholderText("Input folder or drag files here…")
            self._in_dir_edit.setReadOnly(True)
            self._set_tooltip(self._in_dir_edit, 'convert_from_format')
            h.addWidget(self._in_dir_edit, stretch=1)
            btn_pick_dir = QPushButton("📁 Folder")
            btn_pick_dir.setFixedWidth(76)
            btn_pick_dir.clicked.connect(self._pick_input_folder)
            self._set_tooltip(btn_pick_dir, 'input_browse')
            h.addWidget(btn_pick_dir)
            btn_pick_files = QPushButton("🖼 Files")
            btn_pick_files.setFixedWidth(70)
            btn_pick_files.clicked.connect(self._pick_input_files)
            self._set_tooltip(btn_pick_files, 'input_files_browse')
            h.addWidget(btn_pick_files)
            inp_lay.addLayout(h)

            # Recursive checkbox
            self._recursive_cb = QCheckBox("📂 Process subfolders recursively")
            self._recursive_cb.setChecked(False)
            self._set_tooltip(self._recursive_cb,
                "When enabled, the selected folder and all its subfolders are scanned for images")
            inp_lay.addWidget(self._recursive_cb)

            file_row = QHBoxLayout()
            self._file_count_lbl = QLabel("No files selected")
            self._file_count_lbl.setStyleSheet("color:#888; font-size:11px;")
            file_row.addWidget(self._file_count_lbl, stretch=1)
            btn_clear_files = QPushButton("✖ Clear")
            btn_clear_files.setFixedWidth(65)
            btn_clear_files.setFixedHeight(22)
            btn_clear_files.clicked.connect(self._clear_files)
            self._set_tooltip(btn_clear_files, "Remove all selected files from the list")
            file_row.addWidget(btn_clear_files)
            inp_lay.addLayout(file_row)
            lv.addWidget(inp_box)

            # Output format
            fmt_box = QGroupBox("🎯 Output Format")
            fmt_lay = QGridLayout(fmt_box)
            fmt_lay.setSpacing(4)
            # Ensure the label column has a fixed minimum width so it is never
            # cut off when the panel is narrow.  The value column gets all
            # remaining space via setColumnStretch.
            fmt_lay.setColumnMinimumWidth(0, 110)
            fmt_lay.setColumnStretch(1, 1)
            fmt_lay.addWidget(QLabel("Format:"), 0, 0)
            self._fmt_combo = QComboBox()
            for label, _, _ in _OUTPUT_FORMATS:
                self._fmt_combo.addItem(label)
            self._set_tooltip(self._fmt_combo, 'convert_to_format')
            fmt_lay.addWidget(self._fmt_combo, 0, 1)

            # AVIF availability note
            self._avif_note = QLabel(_AVIF_NOTE_MSG)
            self._avif_note.setStyleSheet("color: #e67e00; font-size: 9pt; font-style: italic;")
            self._avif_note.setWordWrap(True)
            self._avif_note.setVisible(False)
            fmt_lay.addWidget(self._avif_note, 0, 2)
            self._fmt_combo.currentIndexChanged.connect(self._on_fmt_changed)

            # Output directory
            fmt_lay.addWidget(QLabel("Output:"), 1, 0)
            out_h = QHBoxLayout()
            self._out_dir_edit = QLineEdit()
            self._out_dir_edit.setPlaceholderText("(same as input)")
            self._set_tooltip(self._out_dir_edit, 'output_browse')
            out_h.addWidget(self._out_dir_edit, stretch=1)
            btn_out = QPushButton("📁")
            btn_out.setFixedWidth(30)
            btn_out.clicked.connect(self._pick_output_dir)
            self._set_tooltip(btn_out, 'output_browse')
            out_h.addWidget(btn_out)
            fmt_lay.addLayout(out_h, 1, 1)

            fmt_lay.addWidget(QLabel("Name template:"), 2, 0)
            self._name_tpl_edit = QLineEdit("{stem}{ext}")
            self._set_tooltip(
                self._name_tpl_edit,
                "Use {stem} = filename without extension, {ext} = new extension, {name} = original filename"
            )
            fmt_lay.addWidget(self._name_tpl_edit, 2, 1)

            fmt_lay.addWidget(QLabel("Suffix:"), 3, 0)
            self._suffix_edit = QLineEdit("")
            self._suffix_edit.setPlaceholderText("e.g. _converted (optional)")
            self._set_tooltip(self._suffix_edit, 'output_suffix')
            fmt_lay.addWidget(self._suffix_edit, 3, 1)
            lv.addWidget(fmt_box)

            # Quality / compression
            qual_box = QGroupBox("⚙️ Quality & Compression")
            qual_lay = QGridLayout(qual_box)
            qual_lay.setSpacing(4)
            qual_lay.setColumnMinimumWidth(0, 110)
            qual_lay.setColumnStretch(1, 1)

            qual_lay.addWidget(QLabel("JPEG quality:"), 0, 0)
            self._jpeg_q = QSpinBox()
            self._jpeg_q.setRange(1, 100)
            self._jpeg_q.setValue(92)
            self._jpeg_q.setSuffix(" %")
            self._set_tooltip(self._jpeg_q, 'jpeg_quality')
            qual_lay.addWidget(self._jpeg_q, 0, 1)
            _rec_jpeg = QLabel("⭐ Recommended: 85–95 %")
            _rec_jpeg.setStyleSheet(_INFO_NOTE_STYLE)
            qual_lay.addWidget(_rec_jpeg, 0, 2)

            qual_lay.addWidget(QLabel("PNG compress:"), 1, 0)
            self._png_cmp = QSpinBox()
            self._png_cmp.setRange(0, 9)
            self._png_cmp.setValue(6)
            qual_lay.addWidget(self._png_cmp, 1, 1)
            self._set_tooltip(self._png_cmp, "0 = fastest (larger file), 9 = smallest (slower)")
            _rec_png = QLabel("⭐ Recommended: 6  (0 = faster, 9 = smaller)")
            _rec_png.setStyleSheet(_INFO_NOTE_STYLE)
            qual_lay.addWidget(_rec_png, 1, 2)

            qual_lay.addWidget(QLabel("WebP quality:"), 2, 0)
            self._webp_q = QSpinBox()
            self._webp_q.setRange(1, 100)
            self._webp_q.setValue(90)
            self._webp_q.setSuffix(" %")
            self._set_tooltip(self._webp_q, 'webp_quality')
            qual_lay.addWidget(self._webp_q, 2, 1)
            _rec_webp = QLabel("⭐ Recommended: 80–95 %")
            _rec_webp.setStyleSheet(_INFO_NOTE_STYLE)
            qual_lay.addWidget(_rec_webp, 2, 2)

            self._webp_ll = QCheckBox("WebP lossless")
            self._set_tooltip(self._webp_ll, 'webp_lossless')
            qual_lay.addWidget(self._webp_ll, 3, 0, 1, 2)

            self._strip_meta = QCheckBox("Strip metadata (EXIF / XMP)")
            self._strip_meta.setChecked(True)
            self._set_tooltip(self._strip_meta, 'convert_keep_original')
            qual_lay.addWidget(self._strip_meta, 4, 0, 1, 2)

            self._skip_existing = QCheckBox("Skip if output file already exists")
            self._skip_existing.setChecked(False)
            self._set_tooltip(self._skip_existing, "When checked, files are not overwritten if the output already exists")
            qual_lay.addWidget(self._skip_existing, 5, 0, 1, 2)

            # SVG rasterisation DPI — only relevant when SVG files are selected
            qual_lay.addWidget(QLabel("SVG raster DPI:"), 6, 0)
            self._svg_dpi = QSpinBox()
            self._svg_dpi.setRange(36, 600)
            self._svg_dpi.setValue(96)
            self._svg_dpi.setSuffix(" dpi")
            self._set_tooltip(self._svg_dpi,
                "Dots-per-inch used when rasterising SVG vector files to pixels.\n"
                "96 dpi = screen resolution (default).  192 = 2× HiDPI.  300 = print quality.")
            qual_lay.addWidget(self._svg_dpi, 6, 1)
            _svg_note_lbl = QLabel("⭐ Recommended: 96 (screen)  ·  192 (HiDPI)  ·  300 (print)")
            _svg_note_lbl.setStyleSheet(_INFO_NOTE_STYLE)
            qual_lay.addWidget(_svg_note_lbl, 6, 2)
            lv.addWidget(qual_box)

            # Colour space
            col_box = QGroupBox("🎨 Colour Space")
            col_lay = QHBoxLayout(col_box)
            col_lay.addWidget(QLabel("Convert to:"))
            self._colour_combo = QComboBox()
            for label, _ in _COLOUR_SPACES:
                self._colour_combo.addItem(label)
            self._set_tooltip(self._colour_combo, 'colour_space')
            col_lay.addWidget(self._colour_combo, stretch=1)
            lv.addWidget(col_box)

            # Resize
            rsz_box = QGroupBox("📐 Resize")
            rsz_lay = QVBoxLayout(rsz_box)
            rsz_lay.setSpacing(4)

            mode_h = QHBoxLayout()
            mode_h.addWidget(QLabel("Mode:"))
            self._resize_combo = QComboBox()
            for label, _ in _RESIZE_MODES:
                self._resize_combo.addItem(label)
            self._resize_combo.currentIndexChanged.connect(self._on_resize_mode_changed)
            self._set_tooltip(self._resize_combo, 'resize_mode')
            mode_h.addWidget(self._resize_combo, stretch=1)
            rsz_lay.addLayout(mode_h)

            # Sub-controls as container widgets for clean show/hide
            self._rsz_row_pct = QWidget()
            pct_h = QHBoxLayout(self._rsz_row_pct)
            pct_h.setContentsMargins(0, 0, 0, 0)
            pct_h.addWidget(QLabel("Percent:"))
            self._rsz_pct = QSpinBox()
            self._rsz_pct.setRange(1, 800)
            self._rsz_pct.setValue(100)
            self._rsz_pct.setSuffix(" %")
            pct_h.addWidget(self._rsz_pct, stretch=1)
            rsz_lay.addWidget(self._rsz_row_pct)
            self._rsz_row_pct.hide()

            self._rsz_row_max = QWidget()
            max_h = QHBoxLayout(self._rsz_row_max)
            max_h.setContentsMargins(0, 0, 0, 0)
            max_h.addWidget(QLabel("Max dim px:"))
            self._rsz_max = QSpinBox()
            self._rsz_max.setRange(16, 16384)
            self._rsz_max.setValue(1024)
            max_h.addWidget(self._rsz_max, stretch=1)
            rsz_lay.addWidget(self._rsz_row_max)
            self._rsz_row_max.hide()

            self._rsz_row_fixed = QWidget()
            fix_h = QHBoxLayout(self._rsz_row_fixed)
            fix_h.setContentsMargins(0, 0, 0, 0)
            fix_h.addWidget(QLabel("W:"))
            self._rsz_fw = QSpinBox(); self._rsz_fw.setRange(1, 16384); self._rsz_fw.setValue(512)
            fix_h.addWidget(self._rsz_fw)
            fix_h.addWidget(QLabel("H:"))
            self._rsz_fh = QSpinBox(); self._rsz_fh.setRange(1, 16384); self._rsz_fh.setValue(512)
            fix_h.addWidget(self._rsz_fh)
            rsz_lay.addWidget(self._rsz_row_fixed)
            self._rsz_row_fixed.hide()
            lv.addWidget(rsz_box)

            # Watermark
            wm_box = QGroupBox("💧 Watermark (optional)")
            wm_lay = QGridLayout(wm_box)
            wm_lay.setSpacing(4)
            wm_lay.setColumnMinimumWidth(0, 80)
            wm_lay.setColumnStretch(1, 1)

            self._wm_enable = QCheckBox("Add text watermark")
            wm_lay.addWidget(self._wm_enable, 0, 0, 1, 2)

            wm_lay.addWidget(QLabel("Text:"), 1, 0)
            self._wm_text = QLineEdit()
            self._wm_text.setPlaceholderText("© Your Name")
            wm_lay.addWidget(self._wm_text, 1, 1)

            wm_lay.addWidget(QLabel("Position:"), 2, 0)
            self._wm_pos = QComboBox()
            for _pos in ("Bottom-right", "Bottom-left", "Top-right", "Top-left", "Center"):
                self._wm_pos.addItem(_pos)
            wm_lay.addWidget(self._wm_pos, 2, 1)

            wm_lay.addWidget(QLabel("Opacity:"), 3, 0)
            self._wm_opacity = QSpinBox()
            self._wm_opacity.setRange(10, 100)
            self._wm_opacity.setValue(60)
            self._wm_opacity.setSuffix(" %")
            wm_lay.addWidget(self._wm_opacity, 3, 1)

            lv.addWidget(wm_box)

            lv.addStretch()

            # Wrap the settings column in a scroll area so it is accessible
            # even when the panel is narrower than its natural content height.
            left_scroll = QScrollArea()
            left_scroll.setWidgetResizable(True)
            left_scroll.setWidget(left_inner)
            left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            left_scroll.setMinimumWidth(320)
            left_scroll.setMaximumWidth(520)
            left_scroll.setFrameShape(QFrame.Shape.NoFrame)
            splitter.addWidget(left_scroll)

            # ── Right column (log + progress) ──────────────────────────────
            right = QWidget()
            rv = QVBoxLayout(right)
            rv.setContentsMargins(4, 0, 0, 0)
            rv.setSpacing(6)

            self._log = QTextEdit()
            self._log.setReadOnly(True)
            self._log.setStyleSheet(
                "background:#0d1117; color:#c9d1d9; font-family:Consolas,monospace; font-size:11px;")
            self._log.setPlaceholderText("Conversion log will appear here…")
            rv.addWidget(self._log, stretch=1)

            self._progress = QProgressBar()
            self._progress.setVisible(False)
            rv.addWidget(self._progress)

            btn_row = QHBoxLayout()
            self._convert_btn = QPushButton("▶ Convert")
            self._convert_btn.setFixedHeight(36)
            self._convert_btn.setStyleSheet(
                "QPushButton{background:#1f6feb; color:white; font-weight:bold; border-radius:6px;}"
                "QPushButton:disabled{background:#30363d; color:#6e7681;}")
            self._convert_btn.clicked.connect(self._start_conversion)
            self._set_tooltip(self._convert_btn, 'convert_button')
            self._cancel_btn = QPushButton("⬛ Cancel")
            self._cancel_btn.setFixedHeight(36)
            self._cancel_btn.setEnabled(False)
            self._cancel_btn.clicked.connect(self._cancel_conversion)
            self._set_tooltip(self._cancel_btn, 'stop_button')
            self._clear_btn = QPushButton("🗑 Clear Log")
            self._clear_btn.setFixedHeight(36)
            self._clear_btn.clicked.connect(self._log.clear)
            self._set_tooltip(self._clear_btn, 'clear_log_button')
            self._save_log_btn = QPushButton("💾 Save Log")
            self._save_log_btn.setFixedHeight(36)
            self._save_log_btn.clicked.connect(self._save_log)
            self._set_tooltip(self._save_log_btn, "Save the conversion log to a text file")
            btn_row.addWidget(self._convert_btn)
            btn_row.addWidget(self._cancel_btn)
            btn_row.addStretch()
            btn_row.addWidget(self._clear_btn)
            btn_row.addWidget(self._save_log_btn)
            rv.addLayout(btn_row)

            self._status_lbl = QLabel("Ready")
            self._status_lbl.setStyleSheet("color:#58a6ff; font-size:11px;")
            rv.addWidget(self._status_lbl)
            splitter.addWidget(right)
            # Give the left (settings) panel a reasonable initial width.
            splitter.setSizes([360, 400])
            splitter.setStretchFactor(0, 0)
            splitter.setStretchFactor(1, 1)

        # ── Tooltip helper ────────────────────────────────────────────────
        def _set_tooltip(self, widget, widget_id_or_text: str):
            """Set tooltip via manager (cycling) when available, else plain text."""
            tm = self._tooltip_mgr
            if tm and hasattr(tm, 'register'):
                if ' ' not in widget_id_or_text:
                    try:
                        tip = tm.get_tooltip(widget_id_or_text)
                        if tip:
                            widget.setToolTip(tip)
                            tm.register(widget, widget_id_or_text)
                            return
                    except Exception:
                        pass
            widget.setToolTip(str(widget_id_or_text))

        # ── Resize sub-control visibility ─────────────────────────────────
        def _on_resize_mode_changed(self, idx: int):
            mode_key = _RESIZE_MODES[idx][1]
            self._rsz_row_pct.setVisible(mode_key == "percent")
            self._rsz_row_max.setVisible(mode_key == "max_dim")
            self._rsz_row_fixed.setVisible(mode_key == "fixed")

        def _on_fmt_changed(self, idx: int):
            """Show format-specific notes when the output format is changed."""
            try:
                _, _ext, pil_fmt = _OUTPUT_FORMATS[idx]
                if pil_fmt == "AVIF":
                    if _AVIF_AVAILABLE:
                        # Plugin loaded — AVIF is fully functional
                        self._avif_note.setText("✅ AVIF encoder ready (pillow-avif-plugin loaded)")
                        self._avif_note.setStyleSheet("color: #44aa44; font-size: 9pt;")
                    else:
                        self._avif_note.setText(_AVIF_NOTE_MSG)
                        self._avif_note.setStyleSheet(
                            "color: #e67e00; font-size: 9pt; font-style: italic;"
                        )
                    self._avif_note.setVisible(True)
                elif pil_fmt == "JPEG2000":
                    self._avif_note.setStyleSheet(_INFO_NOTE_STYLE)
                    self._avif_note.setText(
                        "ℹ️ JPEG 2000 requires the 'openjpeg' codec in Pillow.\n"
                        "Most pip wheels include it — if it fails, try a different format."
                    )
                    self._avif_note.setVisible(True)
                elif pil_fmt == "GIF":
                    self._avif_note.setStyleSheet(_INFO_NOTE_STYLE)
                    self._avif_note.setText(
                        "ℹ️ GIF is limited to 256 colours. Animated GIFs are not preserved."
                    )
                    self._avif_note.setVisible(True)
                elif pil_fmt == "ICNS":
                    self._avif_note.setStyleSheet(_INFO_NOTE_STYLE)
                    self._avif_note.setText(
                        "ℹ️ ICNS (macOS icon) requires a square input. "
                        "Sizes 16, 32, 64, 128, 256, 512 px are recommended."
                    )
                    self._avif_note.setVisible(True)
                elif pil_fmt == "QOI":
                    self._avif_note.setStyleSheet(_INFO_NOTE_STYLE)
                    self._avif_note.setText(
                        "ℹ️ QOI (Quite OK Image) — fast lossless format. "
                        "Requires Pillow 9.3+ (included in requirements)."
                    )
                    self._avif_note.setVisible(True)
                else:
                    self._avif_note.setVisible(False)
            except Exception:
                pass

        # ── File / dir pickers ────────────────────────────────────────────
        def _clear_files(self):
            """Clear the current file selection."""
            self._files = []
            self._in_dir_edit.clear()
            self._file_count_lbl.setText("No files selected")
            self._file_count_lbl.setStyleSheet("color:#888; font-size:11px;")

        def _pick_input_folder(self):
            d = QFileDialog.getExistingDirectory(self, "Select Input Folder")
            if not d:
                return
            exts = _INPUT_EXTS
            recursive = hasattr(self, '_recursive_cb') and self._recursive_cb.isChecked()
            if recursive:
                self._files = sorted(
                    p for p in Path(d).rglob('*')
                    if p.is_file() and p.suffix.lower() in exts
                )
            else:
                self._files = sorted(
                    p for p in Path(d).iterdir()
                    if p.is_file() and p.suffix.lower() in exts
                )
            self._in_dir_edit.setText(d)
            self._file_count_lbl.setText(f"{len(self._files)} image(s) found")
            if not self._out_dir_edit.text():
                self._out_dir_edit.setText(d)

        def _pick_input_files(self):
            exts_str = " ".join(f"*{e}" for e in sorted(_INPUT_EXTS))
            paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Images", "",
                f"Images ({exts_str});;All files (*.*)")
            if not paths:
                return
            self._files = [Path(p) for p in paths]
            if self._files:
                self._in_dir_edit.setText(str(self._files[0].parent))
                if not self._out_dir_edit.text():
                    self._out_dir_edit.setText(str(self._files[0].parent))
            self._file_count_lbl.setText(f"{len(self._files)} file(s) selected")

        def _pick_output_dir(self):
            d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
            if d:
                self._out_dir_edit.setText(d)

        # ── Build settings dict ───────────────────────────────────────────
        def _build_settings(self) -> dict:
            fmt_idx  = self._fmt_combo.currentIndex()
            _, ext, pil_fmt = _OUTPUT_FORMATS[fmt_idx]
            colour_idx = self._colour_combo.currentIndex()
            _, colour = _COLOUR_SPACES[colour_idx]
            resize_idx = self._resize_combo.currentIndex()
            _, resize_mode = _RESIZE_MODES[resize_idx]

            out_dir = self._out_dir_edit.text().strip()
            if not out_dir and self._files:
                out_dir = str(self._files[0].parent)
            name_tpl = self._name_tpl_edit.text().strip() or "{stem}{ext}"

            return {
                "out_dir":        out_dir,
                "out_ext":        ext,
                "pil_fmt":        pil_fmt,
                "colour":         colour,
                "resize_mode":    resize_mode,
                "resize_percent": self._rsz_pct.value(),
                "resize_max_dim": self._rsz_max.value(),
                "resize_fixed_w": self._rsz_fw.value(),
                "resize_fixed_h": self._rsz_fh.value(),
                "jpeg_quality":   self._jpeg_q.value(),
                "png_compress":   self._png_cmp.value(),
                "webp_quality":   self._webp_q.value(),
                "webp_lossless":  self._webp_ll.isChecked(),
                "strip_metadata": self._strip_meta.isChecked(),
                "skip_existing":  self._skip_existing.isChecked(),
                "svg_dpi":        self._svg_dpi.value() if hasattr(self, '_svg_dpi') else 96,
                "name_template":  name_tpl,
                "name_suffix":    self._suffix_edit.text(),
                "watermark_enabled": self._wm_enable.isChecked(),
                "watermark_text":    self._wm_text.text().strip(),
                "watermark_pos":     self._wm_pos.currentText(),
                "watermark_opacity": self._wm_opacity.value(),
            }

        # ── Conversion control ────────────────────────────────────────────
        def _start_conversion(self):
            if not _PIL:
                QMessageBox.critical(self, "Pillow missing",
                    "Pillow (PIL) is not installed.\n\npip install Pillow")
                return
            if not self._files:
                QMessageBox.information(self, "No files", "Please select input files or a folder first.")
                return
            settings = self._build_settings()
            if not settings["out_dir"]:
                QMessageBox.warning(self, "No output folder", "Please select an output folder.")
                return

            self._log.clear()
            self._progress.setMaximum(len(self._files))
            self._progress.setValue(0)
            self._progress.setVisible(True)
            self._convert_btn.setEnabled(False)
            self._cancel_btn.setEnabled(True)
            self._status_lbl.setText("Converting…")

            self._worker = _ConvertWorker(self._files, settings, parent=self)
            self._worker.progress.connect(self._on_progress)
            self._worker.log_msg.connect(self._log.append)
            self._worker.finished.connect(self._on_finished)
            self._worker.start()

        def _cancel_conversion(self):
            if self._worker and self._worker.isRunning():
                self._worker.cancel()
                self._status_lbl.setText("Cancelling…")

        def _save_log(self):
            """Save the conversion log to a text file chosen by the user."""
            text = self._log.toPlainText()
            if not text:
                QMessageBox.information(self, "Empty Log", "There is nothing in the log to save.")
                return
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Conversion Log",
                "conversion_log.txt",
                "Text Files (*.txt);;All Files (*.*)",
            )
            if not path:
                return
            try:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(text)
                self._status_lbl.setText(f"💾 Log saved to {Path(path).name}")
            except Exception as _e:
                QMessageBox.critical(self, "Save Failed", f"Could not save log:\n{_e}")

        def _on_progress(self, done: int, total: int, filename: str):
            self._progress.setMaximum(total)
            self._progress.setValue(done)
            self._status_lbl.setText(f"Processing: {filename}  ({done}/{total})")

        def _on_finished(self, success: bool, message: str, count: int):
            self._convert_btn.setEnabled(True)
            self._cancel_btn.setEnabled(False)
            self._progress.setVisible(False)
            icon = "✅" if success else "⚠️"
            self._status_lbl.setText(f"{icon} {message}")
            self._log.append(f"\n{icon} {message}")
            self.finished.emit(success, message, count)

else:
    class FormatConverterPanelQt(object):  # type: ignore[no-redef]
        """Stub when PyQt6 is absent."""
        finished = None
        def __init__(self, *a, **k): pass
