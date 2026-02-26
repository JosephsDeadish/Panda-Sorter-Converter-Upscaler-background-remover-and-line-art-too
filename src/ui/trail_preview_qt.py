"""
PyQt6 Trail Preview
Replaces canvas-based trail preview with animated Qt graphics.

The preview has two modes:
  • **Mouse-follow mode** (default when the cursor is inside the widget):
    moves a dot with the mouse; trail follows real cursor position.
  • **Demo/bounce mode** (auto-start when no cursor is present):
    a small ball bounces around the preview so it's never static.
"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QWidget, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt, QTimer, QPointF
    from PyQt6.QtGui import QBrush, QColor, QPainter
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    class QObject:  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class QWidget(QObject):  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class QGraphicsView(QWidget):  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass



class TrailPreviewView(QGraphicsView):
    """Trail preview that follows the mouse cursor when hovered,
    or bounces automatically when the cursor is outside."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Accept mouse tracking so we receive moves without a button pressed
        self.setMouseTracking(True)
        # Hide scrollbars — the scene is larger than the visible area by design;
        # the view fits into the fixed-height preview strip.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.trail_items = []
        self.trail_color = QColor(255, 0, 0)
        self.trail_length = 20
        # Bounce-mode state
        self.position = QPointF(0, 0)
        self.velocity = QPointF(2, 1)
        self._mouse_inside = False

        # Single timer drives both bounce and fade
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)

        self.setSceneRect(-150, -150, 300, 300)

    # ── public API ────────────────────────────────────────────────────────────

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
        """Start the timer (bounce mode active when no cursor is inside)."""
        self.timer.start(33)  # ~30 FPS
        
    def stop_animation(self):
        """Stop animation"""
        self.timer.stop()
        for item in self.trail_items:
            self.scene.removeItem(item)
        self.trail_items.clear()

    # ── Qt mouse events — mouse-follow mode ──────────────────────────────────

    def enterEvent(self, event):
        """Mouse entered the widget — switch to mouse-follow mode."""
        self._mouse_inside = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse left the widget — switch back to bounce mode."""
        self._mouse_inside = False
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        """Track cursor position for mouse-follow mode."""
        # Map widget coordinates to scene coordinates
        scene_pos = self.mapToScene(event.pos())
        if self._mouse_inside:
            self._add_dot(scene_pos)
        super().mouseMoveEvent(event)

    # ── internal tick ─────────────────────────────────────────────────────────

    def _tick(self):
        """Timer callback — advance bounce mode or just fade existing dots."""
        if not self._mouse_inside:
            # Bounce the demo dot around the scene
            self.position += self.velocity

            # Bounce off edges
            if abs(self.position.x()) > 140:
                self.velocity.setX(-self.velocity.x())
            if abs(self.position.y()) > 140:
                self.velocity.setY(-self.velocity.y())

            self._add_dot(self.position)
        else:
            # Mouse-follow mode: just fade existing dots, no new position
            self._fade_dots()

    def _add_dot(self, pos: QPointF):
        """Add a new dot at *pos* and fade/remove old ones."""
        dot = QGraphicsEllipseItem(-4, -4, 8, 8)
        dot.setBrush(QBrush(self.trail_color))
        dot.setPos(pos)
        dot.setOpacity(1.0)
        self.scene.addItem(dot)
        self.trail_items.append(dot)
        self._fade_dots()

    def _fade_dots(self):
        """Fade older dots and remove expired ones."""
        while len(self.trail_items) > self.trail_length:
            old = self.trail_items.pop(0)
            self.scene.removeItem(old)
        n = len(self.trail_items)
        for i, dot in enumerate(self.trail_items):
            dot.setOpacity((i + 1) / max(n, 1))


class TrailPreviewWidget(QWidget):
    """Complete trail preview widget with a label."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        hint = QLabel("Move mouse here to preview trail ↓")
        hint.setStyleSheet("color: #888; font-size: 10px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        self.view = TrailPreviewView()
        layout.addWidget(self.view)

        # Start the bounce demo so the widget is never fully static
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
