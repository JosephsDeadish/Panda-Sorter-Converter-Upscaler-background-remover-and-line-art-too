"""
Qt implementation of the background remover panel.
Pure PyQt6 UI for AI-powered background removal.
"""

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                  QLabel, QSlider, QFileDialog, QSpinBox, QCheckBox,
                                  QGroupBox, QComboBox)
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QPixmap
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    class QWidget: pass
    class pyqtSignal: pass

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
        """Load an image file."""
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
        """Save the processed image."""
        if not self.current_image:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        
        if file_path:
            # Implement save logic
            pass
    
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
        """Automatically remove background."""
        if not self.current_image:
            return
        
        # TODO: Implement actual background removal using rembg
        # For now, just notify that feature is not yet implemented
        # Once implemented, update preview with processed image
        if SLIDER_AVAILABLE and hasattr(self, 'preview_widget'):
            # Note: This is a placeholder. The actual background removal
            # will be implemented when rembg integration is complete.
            # For now, we just show the original image in both views.
            pass
        
        if self.processing_complete:
            self.processing_complete.emit()
    
    def clear_all(self):
        """Clear all edits."""
        pass
    
    def undo(self):
        """Undo last action."""
        pass
    
    def redo(self):
        """Redo last undone action."""
        pass
    
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
