"""
PyQt6 Trail Preview
Replaces canvas-based trail preview with animated Qt graphics
"""

try:
    from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QWidget, QVBoxLayout
    from PyQt6.QtCore import Qt, QTimer, QPointF
    from PyQt6.QtGui import QBrush, QColor, QPainter
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class TrailPreviewView(QGraphicsView):
    """Animated trail preview"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        self.trail_items = []
        self.trail_color = QColor(255, 0, 0)
        self.trail_length = 20
        self.position = QPointF(0, 0)
        self.velocity = QPointF(2, 1)
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        
        self.setSceneRect(-150, -150, 300, 300)
        
    def set_trail_color(self, color):
        """Set trail color"""
        if isinstance(color, tuple):
            self.trail_color = QColor(*color)
        elif isinstance(color, QColor):
            self.trail_color = color
        else:
            self.trail_color = QColor(color)
            
    def set_trail_length(self, length):
        """Set trail length"""
        self.trail_length = max(5, min(50, length))
        
    def start_animation(self):
        """Start trail animation"""
        self.timer.start(33)  # ~30 FPS
        
    def stop_animation(self):
        """Stop animation"""
        self.timer.stop()
        
    def update_animation(self):
        """Update animation frame"""
        # Update position
        self.position += self.velocity
        
        # Bounce off edges
        if abs(self.position.x()) > 140:
            self.velocity.setX(-self.velocity.x())
        if abs(self.position.y()) > 140:
            self.velocity.setY(-self.velocity.y())
            
        # Add trail dot
        dot = QGraphicsEllipseItem(-3, -3, 6, 6)
        dot.setBrush(QBrush(self.trail_color))
        dot.setPos(self.position)
        dot.setOpacity(1.0)
        self.scene.addItem(dot)
        self.trail_items.append(dot)
        
        # Fade and remove old dots
        while len(self.trail_items) > self.trail_length:
            old_dot = self.trail_items.pop(0)
            self.scene.removeItem(old_dot)
            
        # Fade existing dots
        for i, dot in enumerate(self.trail_items):
            opacity = (i + 1) / len(self.trail_items)
            dot.setOpacity(opacity)


class TrailPreviewWidget(QWidget):
    """Complete trail preview widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.view = TrailPreviewView()
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Auto-start animation
        self.view.start_animation()
        
    def set_trail_color(self, color):
        self.view.set_trail_color(color)
        
    def set_trail_length(self, length):
        self.view.set_trail_length(length)


def create_trail_preview(parent=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return TrailPreviewWidget(parent)
