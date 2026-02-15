"""
PyQt6 Paint Tools
Replaces canvas-based paint tools with QGraphicsView painting
"""

try:
    from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPathItem,
                                 QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                 QSlider, QLabel, QColorDialog)
    from PyQt6.QtCore import Qt, QPointF
    from PyQt6.QtGui import QPainter, QPainterPath, QPen, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class PaintView(QGraphicsView):
    """Paint canvas with drawing support"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        self.drawing = False
        self.current_path = None
        self.current_path_item = None
        self.brush_size = 5
        self.brush_color = QColor(0, 0, 0)
        
        self.setSceneRect(-250, -250, 500, 500)
        self.setBackgroundBrush(QColor(255, 255, 255))
        
    def set_brush_size(self, size):
        """Set brush size"""
        self.brush_size = max(1, min(50, size))
        
    def set_brush_color(self, color):
        """Set brush color"""
        if isinstance(color, tuple):
            self.brush_color = QColor(*color)
        elif isinstance(color, QColor):
            self.brush_color = color
        else:
            self.brush_color = QColor(color)
            
    def clear_canvas(self):
        """Clear all drawings"""
        self.scene.clear()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            pos = self.mapToScene(event.pos())
            
            self.current_path = QPainterPath()
            self.current_path.moveTo(pos)
            
            pen = QPen(self.brush_color, self.brush_size, 
                      Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                      Qt.PenJoinStyle.RoundJoin)
            
            self.current_path_item = QGraphicsPathItem(self.current_path)
            self.current_path_item.setPen(pen)
            self.scene.addItem(self.current_path_item)
            
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.drawing and self.current_path:
            pos = self.mapToScene(event.pos())
            self.current_path.lineTo(pos)
            self.current_path_item.setPath(self.current_path)
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.current_path = None
            self.current_path_item = None
        super().mouseReleaseEvent(event)


class PaintToolsWidget(QWidget):
    """Complete paint tools widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Paint view
        self.paint_view = PaintView()
        layout.addWidget(self.paint_view)
        
        # Controls
        controls = QHBoxLayout()
        
        # Brush size
        controls.addWidget(QLabel("Size:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(1, 50)
        self.size_slider.setValue(5)
        self.size_slider.valueChanged.connect(self.paint_view.set_brush_size)
        controls.addWidget(self.size_slider)
        
        # Color button
        self.color_btn = QPushButton("Color...")
        self.color_btn.clicked.connect(self.choose_color)
        controls.addWidget(self.color_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.paint_view.clear_canvas)
        controls.addWidget(clear_btn)
        
        layout.addLayout(controls)
        
    def choose_color(self):
        """Choose brush color"""
        color = QColorDialog.getColor(self.paint_view.brush_color, self, "Select Brush Color")
        if color.isValid():
            self.paint_view.set_brush_color(color)
            self.color_btn.setStyleSheet(f"background-color: {color.name()};")


def create_paint_tools(parent=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return PaintToolsWidget(parent)
