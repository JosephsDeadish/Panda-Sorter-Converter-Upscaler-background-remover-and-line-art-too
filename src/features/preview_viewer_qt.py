"""
PyQt6 Preview Viewer
Replaces canvas-based preview with QGraphicsView
"""

try:
    from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QWidget, QVBoxLayout
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPixmap, QPainter, QImage
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class PreviewViewer(QGraphicsView):
    """Image preview with zoom and pan"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        self.pixmap_item = None
        self.zoom_factor = 1.0
        
        # Enable drag to pan
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
    def set_image(self, path):
        """Load image from path"""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return False
            
        if self.pixmap_item:
            self.scene.removeItem(self.pixmap_item)
            
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(self.pixmap_item.boundingRect())
        self.fit_to_window()
        return True
        
    def set_pixmap(self, pixmap):
        """Set pixmap directly"""
        if pixmap.isNull():
            return False
            
        if self.pixmap_item:
            self.scene.removeItem(self.pixmap_item)
            
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.scene.setSceneRect(self.pixmap_item.boundingRect())
        return True
        
    def fit_to_window(self):
        """Fit image to window"""
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self.zoom_factor = 1.0
            
    def reset_zoom(self):
        """Reset to actual size"""
        self.resetTransform()
        self.zoom_factor = 1.0
        
    def zoom_in(self):
        """Zoom in"""
        self.zoom_factor *= 1.2
        self.scale(1.2, 1.2)
        
    def zoom_out(self):
        """Zoom out"""
        self.zoom_factor /= 1.2
        self.scale(1/1.2, 1/1.2)
        
    def wheelEvent(self, event):
        """Mouse wheel zoom"""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()


class PreviewViewerWidget(QWidget):
    """Complete preview widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.viewer = PreviewViewer()
        layout.addWidget(self.viewer)
        layout.setContentsMargins(0, 0, 0, 0)
        
    def set_image(self, path):
        return self.viewer.set_image(path)
        
    def set_pixmap(self, pixmap):
        return self.viewer.set_pixmap(pixmap)


def create_preview_viewer(parent=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return PreviewViewerWidget(parent)
