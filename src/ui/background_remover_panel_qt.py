"""
Qt implementation of the background remover panel.
Pure PyQt6 UI for AI-powered background removal.
"""


from __future__ import annotations
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                  QLabel, QSlider, QFileDialog, QSpinBox, QCheckBox,
                                  QGroupBox, QComboBox, QMessageBox)
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QPixmap
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    class QWidget: pass
    class _SigStub:
        """Minimal signal stub so .connect() never raises AttributeError."""
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SigStub()  # type: ignore[misc]

# Import PIL for image handling
try:
    from PIL import Image
    PIL_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PIL_AVAILABLE = False
    Image = None

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")

# Try to import comparison slider
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


def _remove_bg_onnx(pil_image, model_path: str):
    """Remove background using a U2-Net/ISNet ONNX model without the rembg package.

    This is used as a fallback when ``rembg`` is not importable (e.g. in the
    PyInstaller build where rembg is excluded to prevent a sys.exit crash).

    Args:
        pil_image: PIL.Image.Image in any mode.
        model_path: Absolute path to a compatible ONNX model (u2net, silueta, …).

    Returns:
        PIL.Image.Image in RGBA mode with background removed.

    Raises:
        ImportError: if onnxruntime or numpy is not available.
        FileNotFoundError: if model_path does not exist.
    """
    import os
    import numpy as np
    import onnxruntime as ort

    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"ONNX model not found: {model_path}")

    # ── Pre-process ───────────────────────────────────────────────────────────
    orig_size = pil_image.size
    rgb = pil_image.convert('RGB').resize((320, 320))
    img = np.array(rgb, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img  = (img - mean) / std
    img  = img.transpose(2, 0, 1)[np.newaxis, :].astype(np.float32)  # NCHW

    # ── Inference ─────────────────────────────────────────────────────────────
    sess_opts = ort.SessionOptions()
    sess_opts.log_severity_level = 3  # suppress verbose ort logging
    sess = ort.InferenceSession(model_path, sess_options=sess_opts,
                                providers=['CPUExecutionProvider'])
    input_name = sess.get_inputs()[0].name
    outputs    = sess.run(None, {input_name: img})

    # First output — shape may be (1,1,H,W), (1,H,W), or (H,W)
    mask = np.squeeze(outputs[0]).astype(np.float32)

    # ── Post-process ─────────────────────────────────────────────────────────
    mn, mx = mask.min(), mask.max()
    if mx - mn > 1e-6:
        mask = (mask - mn) / (mx - mn)

    from PIL import Image as _PILImage
    mask_img = _PILImage.fromarray((mask * 255).astype(np.uint8)).resize(
        orig_size, _PILImage.LANCZOS
    )

    result = pil_image.convert('RGBA')
    r, g, b, _ = result.split()
    result = _PILImage.merge('RGBA', (r, g, b, mask_img))
    return result


class BackgroundRemoverPanelQt(QWidget):
    """Qt-based background remover panel with paint tools."""
    
    # Signals
    image_loaded = pyqtSignal(str)
    processing_complete = pyqtSignal()

    # Prefix for temp directories created during background removal
    TEMP_DIR_PREFIX = "bg_remover_"
    
    def __init__(self, parent=None, tooltip_manager=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for BackgroundRemoverPanelQt")
        
        super().__init__(parent)
        self.tooltip_manager = tooltip_manager
        self.current_image = None
        self.processed_image = None
        self.brush_size = 10
        self.current_tool = "brush"
        self._temp_extract_dir = None  # Track temp directory for archive extraction
        self._rembg_temp_dirs: list = []  # Track rembg result temp dirs for cleanup
        
        # Undo/Redo history management
        self.edit_history = []
        self.history_index = -1
        self.max_history = 50
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the UI layout."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎨 Background Remover")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # File operations
        file_layout = QHBoxLayout()
        
        load_btn = QPushButton("📁 Load Image")
        load_btn.clicked.connect(self.load_image)
        self._set_tooltip(load_btn, "Load an image file to remove its background")
        file_layout.addWidget(load_btn)
        
        save_btn = QPushButton("💾 Save Result")
        save_btn.clicked.connect(self.save_image)
        self._set_tooltip(save_btn, "Save the processed image with transparent background")
        file_layout.addWidget(save_btn)
        
        layout.addLayout(file_layout)
        
        # Archive options
        archive_layout = QHBoxLayout()
        
        self.archive_input_cb = QCheckBox("📦 Input is Archive")
        if not ARCHIVE_AVAILABLE:
            self.archive_input_cb.setEnabled(False)
            self.archive_input_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_input_cb.setStyleSheet("color: gray;")
        else:
            self.archive_input_cb.setToolTip("Extract images from archive file (ZIP, 7Z, RAR, TAR)")
            self._set_tooltip(self.archive_input_cb, 'input_archive_checkbox')
        archive_layout.addWidget(self.archive_input_cb)
        
        self.archive_output_cb = QCheckBox("📦 Export to Archive")
        if not ARCHIVE_AVAILABLE:
            self.archive_output_cb.setEnabled(False)
            self.archive_output_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_output_cb.setStyleSheet("color: gray;")
        else:
            self.archive_output_cb.setToolTip("Save processed images to archive file")
            self._set_tooltip(self.archive_output_cb, 'output_archive_checkbox')
        archive_layout.addWidget(self.archive_output_cb)
        
        archive_layout.addStretch()
        layout.addLayout(archive_layout)
        
        # Tools - Using checkboxes for toggle selection
        tools_group = QGroupBox("🛠️ Tools")
        tools_layout = QVBoxLayout()
        
        # Tool selection checkboxes
        tool_select_layout = QHBoxLayout()
        
        self.brush_cb = QCheckBox("🖌️ Brush")
        self.brush_cb.setChecked(True)
        self.brush_cb.toggled.connect(lambda checked: self.select_tool("brush") if checked else None)
        self._set_tooltip(self.brush_cb, "Paint to keep areas visible")
        tool_select_layout.addWidget(self.brush_cb)
        
        self.eraser_cb = QCheckBox("🧹 Eraser")
        self.eraser_cb.toggled.connect(lambda checked: self.select_tool("eraser") if checked else None)
        self._set_tooltip(self.eraser_cb, "Erase to make areas transparent")
        tool_select_layout.addWidget(self.eraser_cb)
        
        self.fill_cb = QCheckBox("🪣 Fill")
        self.fill_cb.toggled.connect(lambda checked: self.select_tool("fill") if checked else None)
        self._set_tooltip(self.fill_cb, "Fill connected areas with transparency")
        tool_select_layout.addWidget(self.fill_cb)
        
        tools_layout.addLayout(tool_select_layout)
        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)
        
        # Brush size
        size_group = QGroupBox("✏️ Brush Size")
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))
        
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setMinimum(1)
        self.size_slider.setMaximum(50)
        self.size_slider.setValue(10)
        self.size_slider.valueChanged.connect(self.on_size_changed)
        self._set_tooltip(self.size_slider, "Adjust brush size (1-50 pixels)")
        size_layout.addWidget(self.size_slider)
        
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setMinimum(1)
        self.size_spinbox.setMaximum(50)
        self.size_spinbox.setValue(10)
        self.size_spinbox.valueChanged.connect(self.on_size_changed)
        self._set_tooltip(self.size_spinbox, "Brush size value")
        size_layout.addWidget(self.size_spinbox)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # AI Model selection — shown above the process buttons
        model_group = QGroupBox("🤖 AI Model")
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.bg_model_combo = QComboBox()
        _BG_MODELS = [
            ("u2net",            "U2Net (default, balanced)"),
            ("u2netp",           "U2Netp (fast, lightweight)"),
            ("u2net_human_seg",  "U2Net Human Seg (portraits)"),
            ("silueta",          "Silueta (compact, 43 MB)"),
            ("isnet-general-use","ISNet General (high quality)"),
            ("isnet_dis",        "ISNet-DIS (precise edges)"),
            ("birefnet-general", "BiRefNet (best quality, slow)"),
            ("u2net_cloth_seg",  "U2Net Cloth Seg (clothing)"),
        ]
        for model_id, model_label in _BG_MODELS:
            self.bg_model_combo.addItem(model_label, model_id)
        model_layout.addWidget(self.bg_model_combo, 1)
        self._set_tooltip(self.bg_model_combo, 'bg_model_selector')
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Processing options
        process_layout = QHBoxLayout()
        
        auto_btn = QPushButton("🤖 Auto Remove")
        auto_btn.clicked.connect(self.auto_remove_background)
        self._set_tooltip(auto_btn, 'bg_remove_button')
        process_layout.addWidget(auto_btn)
        
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self.clear_all)
        self._set_tooltip(clear_btn, "Clear all edits and start over")
        process_layout.addWidget(clear_btn)
        
        layout.addLayout(process_layout)
        
        # Undo/Redo
        history_layout = QHBoxLayout()
        
        undo_btn = QPushButton("↶ Undo")
        undo_btn.clicked.connect(self.undo)
        self._set_tooltip(undo_btn, "Undo last action (Ctrl+Z)")
        history_layout.addWidget(undo_btn)
        
        redo_btn = QPushButton("↷ Redo")
        redo_btn.clicked.connect(self.redo)
        self._set_tooltip(redo_btn, "Redo last undone action (Ctrl+Y)")
        history_layout.addWidget(redo_btn)
        
        layout.addLayout(history_layout)
        
        # Live Preview - Before/After Comparison
        if SLIDER_AVAILABLE:
            preview_group = QGroupBox("👁️ Live Preview (Before/After)")
            preview_layout = QVBoxLayout()
            
            # Comparison mode selector
            mode_layout = QHBoxLayout()
            mode_layout.addWidget(QLabel("Comparison Mode:"))
            self.comparison_mode_combo = QComboBox()
            self.comparison_mode_combo.addItems(["Slider", "Toggle", "Overlay"])
            self.comparison_mode_combo.currentTextChanged.connect(self._on_comparison_mode_changed)
            self._set_tooltip(self.comparison_mode_combo, "Choose how to compare before/after images")
            mode_layout.addWidget(self.comparison_mode_combo)
            mode_layout.addStretch()
            preview_layout.addLayout(mode_layout)
            
            # Comparison slider widget
            self.preview_widget = ComparisonSliderWidget()
            self.preview_widget.setMinimumHeight(300)
            self._set_tooltip(self.preview_widget, "Drag slider to compare original and processed images")
            # Log slider position changes for debugging
            if hasattr(self.preview_widget, 'slider_moved'):
                self.preview_widget.slider_moved.connect(
                    lambda pos: logger.debug(f"BG remover preview slider: {pos}%")
                )
            preview_layout.addWidget(self.preview_widget)
            
            preview_group.setLayout(preview_layout)
            layout.addWidget(preview_group)
        
        layout.addStretch()
    
    def load_image(self):
        """Load an image file or extract from archive."""
        # Check if loading from archive
        if ARCHIVE_AVAILABLE and self.archive_input_cb.isChecked():
            # Select archive file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Archive",
                "",
                "Archives (*.zip *.7z *.rar *.tar *.tar.gz)"
            )
            
            if file_path:
                try:
                    from utils.archive_handler import ArchiveHandler
                    import tempfile
                    
                    archive_handler = ArchiveHandler()
                    
                    # Extract to temp directory
                    temp_dir = Path(tempfile.mkdtemp(prefix="bg_remover_"))
                    archive_handler.extract_archive(Path(file_path), temp_dir)
                    
                    # Find first image in extracted files
                    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
                    for img_file in temp_dir.rglob('*'):
                        if img_file.suffix.lower() in image_extensions:
                            self.current_image = str(img_file)
                            self._temp_extract_dir = temp_dir  # Store for cleanup
                            
                            # Update preview
                            if SLIDER_AVAILABLE and hasattr(self, 'preview_widget'):
                                pixmap = QPixmap(str(img_file))
                                self.preview_widget.set_before_image(pixmap)
                            
                            if self.image_loaded:
                                self.image_loaded.emit(str(img_file))
                            
                            QMessageBox.information(
                                self,
                                "Archive Extracted",
                                f"Loaded image from archive: {img_file.name}"
                            )
                            return
                    
                    QMessageBox.warning(self, "No Images", "No image files found in archive")
                    
                except Exception as e:
                    logger.error(f"Error extracting archive: {e}")
                    QMessageBox.critical(self, "Error", f"Failed to extract archive:\n{str(e)}")
        else:
            # Normal file selection
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Image",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
            
            if file_path:
                self.current_image = file_path
                
                # Update preview if available
                if SLIDER_AVAILABLE and hasattr(self, 'preview_widget'):
                    pixmap = QPixmap(file_path)
                    self.preview_widget.set_before_image(pixmap)
                
                if self.image_loaded:
                    self.image_loaded.emit(file_path)
    
    def save_image(self):
        """Save the processed image with transparency."""
        if not self.current_image and not self.processed_image:
            QMessageBox.warning(self, "No Image", "No image to save. Please load an image first.")
            return
        
        # Check if saving to archive
        if ARCHIVE_AVAILABLE and self.archive_output_cb.isChecked():
            archive_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Archive",
                "",
                "ZIP Archive (*.zip);;7Z Archive (*.7z)"
            )
            
            if archive_path:
                try:
                    from utils.archive_handler import ArchiveHandler
                    import tempfile
                    
                    # Ensure proper extension
                    if not any(archive_path.lower().endswith(ext) for ext in ['.zip', '.7z']):
                        archive_path += '.zip'
                    
                    # Save image to temp file first
                    temp_dir = Path(tempfile.mkdtemp(prefix="bg_remover_save_"))
                    temp_image = temp_dir / "processed_image.png"
                    
                    if not PIL_AVAILABLE:
                        QMessageBox.critical(self, "Error", "PIL/Pillow not installed. Cannot save image.")
                        return
                    
                    img_path = self.processed_image if self.processed_image else self.current_image
                    img = Image.open(img_path)
                    img = img.convert('RGBA')
                    img.save(temp_image, 'PNG')
                    
                    # Create archive
                    archive_handler = ArchiveHandler()
                    archive_handler.create_archive(temp_dir, Path(archive_path))
                    
                    # Cleanup temp
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
                    QMessageBox.information(self, "Saved", f"Image saved to archive: {archive_path}")
                    if self.processing_complete:
                        self.processing_complete.emit()
                        
                except Exception as e:
                    logger.error(f"Error creating archive: {e}")
                    QMessageBox.critical(self, "Error", f"Failed to create archive:\n{str(e)}")
        else:
            # Normal file save
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Image",
                "",
                "PNG Image (*.png);;JPEG Image (*.jpg)"
            )
            
            if file_path:
                try:
                    # Ensure proper file extension
                    if not any(file_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg']):
                        file_path += '.png'
                    
                    # Load the image to save (processed if available, else current)
                    if not PIL_AVAILABLE:
                        QMessageBox.critical(self, "Error", "PIL/Pillow not installed. Cannot save image.")
                        return
                    
                    img_path = self.processed_image if self.processed_image else self.current_image
                    img = Image.open(img_path)
                    
                    # Convert to RGBA if saving as PNG
                    if file_path.lower().endswith('.png') and img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # Save
                    img.save(file_path, optimize=True)
                    
                    QMessageBox.information(self, "Success", f"Image saved to:\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save image:\n{str(e)}")
    
    def select_tool(self, tool):
        """Select a paint tool."""
        self.current_tool = tool
        
        # Block signals to prevent recursive calls
        # Update checkbox states (only one can be checked at a time)
        if hasattr(self, 'brush_cb'):
            self.brush_cb.blockSignals(True)
            self.brush_cb.setChecked(tool == "brush")
            self.brush_cb.blockSignals(False)
        if hasattr(self, 'eraser_cb'):
            self.eraser_cb.blockSignals(True)
            self.eraser_cb.setChecked(tool == "eraser")
            self.eraser_cb.blockSignals(False)
        if hasattr(self, 'fill_cb'):
            self.fill_cb.blockSignals(True)
            self.fill_cb.setChecked(tool == "fill")
            self.fill_cb.blockSignals(False)
    
    def on_size_changed(self, value):
        """Handle brush size change."""
        self.brush_size = value
        self.size_slider.setValue(value)
        self.size_spinbox.setValue(value)
    
    def auto_remove_background(self):
        """Automatically remove background using AI.

        Uses rembg when available; falls back to a direct onnxruntime inference
        path using pre-downloaded ONNX models (U2-Net, IS-Net, etc.) so the
        feature works in the PyInstaller build even though rembg is excluded from
        the bundle.
        """
        if not self.current_image:
            return

        # ── Check available backends ─────────────────────────────────────────
        rembg_available = False
        ort_available   = False
        try:
            import rembg  # noqa: F401
            rembg_available = True
        except (ImportError, Exception, SystemExit):
            pass

        try:
            import onnxruntime  # noqa: F401
            import numpy  # noqa: F401
            ort_available = True
        except (ImportError, Exception):
            pass

        if not rembg_available and not ort_available:
            QMessageBox.information(
                self,
                "Feature Not Available",
                "Automatic background removal requires the 'rembg' library OR "
                "'onnxruntime' + a pre-downloaded ONNX model.\n\n"
                "Install rembg with:\n"
                "  pip install 'rembg[cpu]'\n\n"
                "Or ensure onnxruntime is installed and a model has been downloaded "
                "via Settings → AI Models."
            )
            return

        try:
            from PyQt6.QtWidgets import QProgressDialog
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QPixmap
            import tempfile

            if not PIL_AVAILABLE:
                QMessageBox.critical(self, "Error", "PIL/Pillow not installed. Cannot process image.")
                return

            from PIL import Image

            # Show progress dialog
            progress = QProgressDialog("Removing background...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Processing")
            progress.show()

            # Open image (self.current_image is always a path string)
            pil_image = Image.open(self.current_image)

            # Determine which model to use
            selected_model = 'u2net'
            bg_combo = getattr(self, 'bg_model_combo', None)
            if bg_combo is not None and hasattr(bg_combo, 'currentData'):
                model_data = bg_combo.currentData()
                if model_data:
                    selected_model = model_data

            output: Image.Image | None = None

            # ── Path 1: rembg ────────────────────────────────────────────────
            if rembg_available:
                import rembg
                try:
                    session = rembg.new_session(selected_model)
                    output = rembg.remove(pil_image, session=session)
                except Exception as _me:
                    logger.warning(f"rembg session failed for '{selected_model}': {_me}")
                    try:
                        output = rembg.remove(pil_image)
                    except Exception as _me2:
                        logger.warning(f"rembg.remove() also failed: {_me2}")
                        rembg_available = False  # fall through to onnxruntime

            # ── Path 2: direct onnxruntime (fallback / build mode) ───────────
            if output is None and ort_available:
                # Locate the ONNX model — check U2NET_HOME, AIModelManager, app data
                import os
                model_filename = f"{selected_model}.onnx"
                search_dirs = []
                u2home = os.environ.get('U2NET_HOME', '')
                if u2home:
                    search_dirs.append(u2home)
                try:
                    from config import get_data_dir as _gdd
                    search_dirs.append(str(_gdd() / 'models'))
                except Exception:
                    pass
                try:
                    from upscaler.model_manager import AIModelManager as _AMM
                    search_dirs.append(str(_AMM().models_dir))
                except Exception:
                    pass
                # Also check next to the EXE (for PyInstaller bundles)
                import sys
                exe_dir = Path(sys.executable).parent
                search_dirs.append(str(exe_dir / 'app_data' / 'models'))
                # Deduplicate while preserving insertion order
                seen_dirs: set = set()
                unique_dirs = []
                for d in search_dirs:
                    if d not in seen_dirs:
                        seen_dirs.add(d)
                        unique_dirs.append(d)
                search_dirs = unique_dirs

                model_path: str | None = None
                for d in search_dirs:
                    candidate = os.path.join(d, model_filename)
                    if os.path.isfile(candidate):
                        model_path = candidate
                        break
                # If requested model not found, try u2net as fallback
                if model_path is None and selected_model != 'u2net':
                    for d in search_dirs:
                        candidate = os.path.join(d, 'u2net.onnx')
                        if os.path.isfile(candidate):
                            model_path = candidate
                            break

                if model_path is None:
                    progress.close()
                    QMessageBox.warning(
                        self, "Model Not Found",
                        f"ONNX model '{model_filename}' not found in:\n"
                        + "\n".join(f"  • {d}" for d in search_dirs)
                        + "\n\nDownload models via Settings → AI Models."
                    )
                    return

                logger.info(f"Using direct onnxruntime inference: {model_path}")
                output = _remove_bg_onnx(pil_image, model_path)

            if output is None:
                progress.close()
                QMessageBox.critical(self, "Error", "Background removal failed with all available backends.")
                return

            # ── Save result and update UI ────────────────────────────────────
            tmp_dir = Path(tempfile.mkdtemp(prefix=self.TEMP_DIR_PREFIX))
            self._rembg_temp_dirs.append(tmp_dir)
            result_path = tmp_dir / (Path(self.current_image).stem + "_no_bg.png")
            output.save(str(result_path), format='PNG')

            self.processed_image = str(result_path)

            # Undo/redo history
            self.history_index += 1
            if self.history_index < len(self.edit_history):
                self.edit_history = self.edit_history[:self.history_index]
            self.edit_history.append(self.processed_image)
            if len(self.edit_history) > self.max_history:
                self.edit_history.pop(0)
                self.history_index = len(self.edit_history) - 1

            # Update before/after preview
            if SLIDER_AVAILABLE and hasattr(self, 'preview_widget'):
                before_px = QPixmap(self.current_image)
                after_px  = QPixmap(self.processed_image)
                self.preview_widget.set_before_image(before_px)
                self.preview_widget.set_after_image(after_px)

            progress.close()
            QMessageBox.information(self, "Success", "Background removed successfully!")

            if self.processing_complete:
                self.processing_complete.emit()

        except Exception as e:
            logger.error(f"Error removing background: {e}", exc_info=True)
            try:
                progress.close()  # type: ignore[possibly-undefined]
            except Exception:
                pass
            QMessageBox.critical(self, "Error", f"Failed to remove background:\n{e}")


    
    def clear_all(self):
        """Clear all edits and reset to original."""
        if not self.current_image:
            return
        
        reply = QMessageBox.question(
            self, "Clear All",
            "Clear all edits and reset to original image?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.processed_image = None
            self.edit_history = []
            self.history_index = -1
            
            # Update preview
            if SLIDER_AVAILABLE and hasattr(self, 'preview_widget'):
                pixmap = QPixmap(self.current_image)
                self.preview_widget.set_after_image(pixmap)
    
    def undo(self):
        """Undo last action."""
        if self.history_index > 0:
            self.history_index -= 1
            self.processed_image = self.edit_history[self.history_index]
            
            if SLIDER_AVAILABLE and hasattr(self, 'preview_widget'):
                # processed_image is a filepath, load it as QPixmap
                pixmap = QPixmap(self.processed_image)
                self.preview_widget.set_after_image(pixmap)
    
    def redo(self):
        """Redo last undone action."""
        if self.history_index < len(self.edit_history) - 1:
            self.history_index += 1
            self.processed_image = self.edit_history[self.history_index]
            
            if SLIDER_AVAILABLE and hasattr(self, 'preview_widget'):
                # processed_image is a filepath, load it as QPixmap
                pixmap = QPixmap(self.processed_image)
                self.preview_widget.set_after_image(pixmap)
    
    def _on_comparison_mode_changed(self, mode_text):
        """Handle comparison mode change."""
        if not SLIDER_AVAILABLE or not hasattr(self, 'preview_widget'):
            return
        
        mode_map = {
            "Slider": "slider",
            "Toggle": "toggle",
            "Overlay": "overlay"
        }
        self.preview_widget.set_mode(mode_map.get(mode_text, "slider"))
    
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

    def closeEvent(self, event):
        """Clean up temp directories created during background removal."""
        for tmp_dir in self._rembg_temp_dirs:
            try:
                shutil.rmtree(str(tmp_dir), ignore_errors=True)
            except Exception:
                pass
        self._rembg_temp_dirs.clear()
        super().closeEvent(event)
