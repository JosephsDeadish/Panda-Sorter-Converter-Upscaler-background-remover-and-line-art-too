"""
Qt implementation of the background remover panel.
Pure PyQt6 UI for AI-powered background removal.
"""

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
except ImportError:
    PYQT_AVAILABLE = False
    class QWidget: pass
    class pyqtSignal: pass

# Import PIL for image handling
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except ImportError:
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")

# Try to import comparison slider
try:
    from ui.live_preview_slider_qt import ComparisonSliderWidget
    SLIDER_AVAILABLE = True
except ImportError:
    try:
        from live_preview_slider_qt import ComparisonSliderWidget
        SLIDER_AVAILABLE = True
    except ImportError:
        SLIDER_AVAILABLE = False
        ComparisonSliderWidget = None


class BackgroundRemoverPanelQt(QWidget):
    """Qt-based background remover panel with paint tools."""
    
    # Signals
    image_loaded = pyqtSignal(str) if PYQT_AVAILABLE else None
    processing_complete = pyqtSignal() if PYQT_AVAILABLE else None
    
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
        
        # Processing options
        process_layout = QHBoxLayout()
        
        auto_btn = QPushButton("🤖 Auto Remove")
        auto_btn.clicked.connect(self.auto_remove_background)
        self._set_tooltip(auto_btn, "Automatically remove background using AI")
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
        """
        Automatically remove background using AI (rembg).
        
        FUTURE FEATURE: This requires the 'rembg' library to be installed.
        
        Installation: pip install rembg
        
        When implemented, this will:
        1. Load the current image
        2. Use rembg to remove the background
        3. Save the result with alpha transparency
        4. Update the preview with the processed image
        5. Add to edit history for undo/redo
        
        For now, shows a message to the user that this feature is planned.
        """
        if not self.current_image:
            return
        
        # Check if rembg is available
        try:
            import rembg
            rembg_available = True
        except ImportError:
            rembg_available = False
        
        if not rembg_available:
            QMessageBox.information(
                self,
                "Feature Not Available",
                "Automatic background removal requires the 'rembg' library.\n\n"
                "To enable this feature, install it with:\n"
                "pip install 'rembg[cpu]'\n\n"
                "For GPU support:\n"
                "pip install 'rembg[gpu]'"
            )
            return
        
        # Implement actual background removal
        if not self.current_image:
            QMessageBox.warning(
                self,
                "No Image",
                "Please load an image first before removing background."
            )
            return
        
        try:
            from PyQt6.QtWidgets import QProgressDialog
            from PyQt6.QtCore import Qt, QBuffer
            from PyQt6.QtGui import QImage
            from PIL import Image
            import io
            
            # Show progress dialog
            progress = QProgressDialog("Removing background...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Processing")
            progress.show()
            
            # Convert QImage to PIL Image
            buffer = QBuffer()
            buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            self.current_image.save(buffer, "PNG")
            pil_image = Image.open(io.BytesIO(buffer.data()))
            
            # Process with rembg
            output = rembg.remove(pil_image)
            
            # Convert back to QImage
            output_buffer = io.BytesIO()
            output.save(output_buffer, format='PNG')
            output_buffer.seek(0)
            
            result_image = QImage()
            result_image.loadFromData(output_buffer.read())
            
            # Update current image
            self.current_image = result_image
            
            # Update preview
            if hasattr(self, 'update_preview'):
                self.update_preview()
            
            # Add to undo history
            if hasattr(self, 'undo_stack'):
                self.undo_stack.append(result_image.copy())
            
            progress.close()
            
            QMessageBox.information(
                self,
                "Success",
                "Background removed successfully!"
            )
            
            if self.processing_complete:
                self.processing_complete.emit()
                
        except Exception as e:
            logger.error(f"Error removing background: {e}", exc_info=True)
            
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to remove background:\n{str(e)}"
            )

    
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
    
    def _set_tooltip(self, widget, text):
        """Set tooltip on a widget using tooltip manager if available."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'set_tooltip'):
            self.tooltip_manager.set_tooltip(widget, text)
        else:
            widget.setToolTip(text)
