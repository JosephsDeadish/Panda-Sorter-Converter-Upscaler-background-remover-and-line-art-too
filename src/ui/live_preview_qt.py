"""
PyQt6 Live Preview
Replaces canvas-based live preview widget
"""

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                 QLabel, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                                 QSlider, QComboBox)
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPixmap, QPainter
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class LivePreviewWidget(QWidget):
    """Live preview with before/after comparison"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = None
        self.processed_pixmap = None
        self.current_mode = "side_by_side"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls = QHBoxLayout()
        
        # Mode selector
        controls.addWidget(QLabel("View Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Side by Side", "Toggle", "Overlay", "Single"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        controls.addWidget(self.mode_combo)
        
        # Toggle button
        self.toggle_btn = QPushButton("Toggle View")
        self.toggle_btn.clicked.connect(self.toggle_view)
        self.toggle_btn.setEnabled(False)
        controls.addWidget(self.toggle_btn)
        
        layout.addLayout(controls)
        
        # Preview area
        self.preview_view = QGraphicsView()
        self.preview_scene = QGraphicsScene()
        self.preview_view.setScene(self.preview_scene)
        self.preview_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.preview_view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        layout.addWidget(self.preview_view)
        
        # Status
        self.status_label = QLabel("No images loaded")
        layout.addWidget(self.status_label)
        
        self.showing_original = True
        
    def set_original(self, pixmap):
        """Set original image"""
        if isinstance(pixmap, str):
            pixmap = QPixmap(pixmap)
        self.original_pixmap = pixmap
        self.update_preview()
        
    def set_processed(self, pixmap):
        """Set processed image"""
        if isinstance(pixmap, str):
            pixmap = QPixmap(pixmap)
        self.processed_pixmap = pixmap
        self.update_preview()
        
    def update_preview(self):
        """Update preview display"""
        self.preview_scene.clear()
        
        if not self.original_pixmap and not self.processed_pixmap:
            self.status_label.setText("No images loaded")
            return
            
        mode = self.mode_combo.currentText().lower().replace(" ", "_")
        
        if mode == "side_by_side":
            self.show_side_by_side()
        elif mode == "toggle":
            self.show_toggle()
            self.toggle_btn.setEnabled(True)
        elif mode == "overlay":
            self.show_overlay()
        else:  # Single
            self.show_single()
            
    def show_side_by_side(self):
        """Show original and processed side by side"""
        x_offset = 0
        
        if self.original_pixmap:
            item = QGraphicsPixmapItem(self.original_pixmap)
            item.setPos(x_offset, 0)
            self.preview_scene.addItem(item)
            x_offset += self.original_pixmap.width() + 10
            
        if self.processed_pixmap:
            item = QGraphicsPixmapItem(self.processed_pixmap)
            item.setPos(x_offset, 0)
            self.preview_scene.addItem(item)
            
        self.status_label.setText("Side by Side: Original (left) | Processed (right)")
        
    def show_toggle(self):
        """Show one image (toggleable)"""
        pixmap = self.original_pixmap if self.showing_original else self.processed_pixmap
        
        if pixmap:
            item = QGraphicsPixmapItem(pixmap)
            self.preview_scene.addItem(item)
            
        label = "Original" if self.showing_original else "Processed"
        self.status_label.setText(f"Toggle Mode: Showing {label}")
        
    def show_overlay(self):
        """Show images overlaid"""
        if self.original_pixmap:
            item = QGraphicsPixmapItem(self.original_pixmap)
            self.preview_scene.addItem(item)
            
        if self.processed_pixmap:
            item = QGraphicsPixmapItem(self.processed_pixmap)
            item.setOpacity(0.5)
            self.preview_scene.addItem(item)
            
        self.status_label.setText("Overlay Mode: Original (full) + Processed (50%)")
        
    def show_single(self):
        """Show processed only"""
        pixmap = self.processed_pixmap if self.processed_pixmap else self.original_pixmap
        
        if pixmap:
            item = QGraphicsPixmapItem(pixmap)
            self.preview_scene.addItem(item)
            
        self.status_label.setText("Single Mode: Processed image")
        
    def toggle_view(self):
        """Toggle between original and processed"""
        self.showing_original = not self.showing_original
        self.update_preview()
        
    def on_mode_changed(self, mode):
        """Handle mode change"""
        self.toggle_btn.setEnabled(mode == "Toggle")
        self.update_preview()


def create_live_preview(parent=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return LivePreviewWidget(parent)
