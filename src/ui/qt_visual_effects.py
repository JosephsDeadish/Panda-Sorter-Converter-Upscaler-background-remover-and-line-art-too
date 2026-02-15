"""
Qt Visual Effects Renderer - Replaces canvas-based visual effects
Uses OpenGL for 3D effects and QPainter for 2D effects
"""

from PyQt6.QtWidgets import QWidget, QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QPainterPath
from PyQt6.QtOpenGLWidgets import QOpenGLWidget as GLWidget
from typing import List, Tuple, Optional
import math

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False


class VisualEffectsWidget(QWidget):
    """2D visual effects using QPainter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wounds = []
        self.projectiles = []
        self.stuck_projectiles = []
        self.show_debug = False
        self.setMinimumSize(400, 400)
        
    def set_wounds(self, wounds: List):
        """Set wounds to render"""
        self.wounds = wounds
        self.update()
    
    def set_projectiles(self, projectiles: List):
        """Set flying projectiles to render"""
        self.projectiles = projectiles
        self.update()
    
    def set_stuck_projectiles(self, stuck: List):
        """Set stuck projectiles to render"""
        self.stuck_projectiles = stuck
        self.update()
    
    def paintEvent(self, event):
        """Paint visual effects"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw wounds
        for wound in self.wounds:
            self._draw_wound(painter, wound)
        
        # Draw stuck projectiles
        for proj in self.stuck_projectiles:
            self._draw_stuck_projectile(painter, proj)
        
        # Draw flying projectiles
        for proj in self.projectiles:
            if hasattr(proj, 'active') and proj.active and not getattr(proj, 'stuck', False):
                self._draw_projectile(painter, proj)
    
    def _draw_wound(self, painter: QPainter, wound):
        """Draw a wound"""
        x, y = wound.position if hasattr(wound, 'position') else (wound.get('x', 0), wound.get('y', 0))
        size = getattr(wound, 'size', wound.get('size', 10))
        color = getattr(wound, 'color', wound.get('color', '#FF0000'))
        wound_type = getattr(wound, 'wound_type', wound.get('type', 'generic'))
        severity = getattr(wound, 'severity', wound.get('severity', 1.0))
        
        if wound_type == "gash":
            self._draw_gash(painter, x, y, size, color, severity)
        elif wound_type == "bruise":
            self._draw_bruise(painter, x, y, size, color, severity)
        elif wound_type == "hole":
            self._draw_hole(painter, x, y, size, color)
        elif wound_type == "burn":
            self._draw_burn(painter, x, y, size, color, severity)
        elif wound_type == "frostbite":
            self._draw_frostbite(painter, x, y, size, color)
        else:
            self._draw_generic_wound(painter, x, y, size, color)
    
    def _draw_gash(self, painter: QPainter, x: int, y: int, size: int, color: str, severity: float):
        """Draw a gash wound"""
        painter.setPen(QPen(QColor(color), max(2, int(severity * 3))))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw irregular cut
        points = []
        for i in range(5):
            angle = (i / 5) * math.pi + math.sin(i) * 0.3
            px = x + math.cos(angle) * size
            py = y + math.sin(angle) * size * 0.5
            points.append(QPointF(px, py))
        
        path = QPainterPath()
        path.moveTo(points[0])
        for point in points[1:]:
            path.lineTo(point)
        painter.drawPath(path)
    
    def _draw_bruise(self, painter: QPainter, x: int, y: int, size: int, color: str, severity: float):
        """Draw a bruise"""
        # Draw gradient circles for bruise effect
        base_color = QColor(color)
        base_color.setAlpha(int(150 * severity))
        
        painter.setBrush(QBrush(base_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x, y), size, size * 0.8)
        
        # Add darker center
        dark_color = base_color.darker(150)
        dark_color.setAlpha(int(100 * severity))
        painter.setBrush(QBrush(dark_color))
        painter.drawEllipse(QPointF(x, y), size * 0.5, size * 0.4)
    
    def _draw_hole(self, painter: QPainter, x: int, y: int, size: int, color: str):
        """Draw a penetration hole"""
        painter.setPen(QPen(QColor(color), 2))
        painter.setBrush(QBrush(QColor("#8B0000")))  # Dark red
        painter.drawEllipse(QPointF(x, y), size, size)
        
        # Add dark center
        painter.setBrush(QBrush(QColor("#000000")))
        painter.drawEllipse(QPointF(x, y), size * 0.3, size * 0.3)
    
    def _draw_burn(self, painter: QPainter, x: int, y: int, size: int, color: str, severity: float):
        """Draw a burn wound"""
        # Irregular burn shape
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Outer charred area
        painter.setBrush(QBrush(QColor("#2F1B0C")))
        painter.drawEllipse(QPointF(x, y), size * 1.2, size)
        
        # Inner burned area
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(QPointF(x, y), size * 0.7, size * 0.6)
    
    def _draw_frostbite(self, painter: QPainter, x: int, y: int, size: int, color: str):
        """Draw frostbite"""
        # Blue-purple discoloration
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#9370DB")))
        painter.drawEllipse(QPointF(x, y), size, size * 0.8)
        
        # Add ice crystals
        painter.setPen(QPen(QColor("#E0FFFF"), 1))
        for i in range(8):
            angle = (i / 8) * 2 * math.pi
            x1 = x + math.cos(angle) * size * 0.3
            y1 = y + math.sin(angle) * size * 0.3
            x2 = x + math.cos(angle) * size * 0.8
            y2 = y + math.sin(angle) * size * 0.8
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    
    def _draw_generic_wound(self, painter: QPainter, x: int, y: int, size: int, color: str):
        """Draw generic wound"""
        painter.setPen(QPen(QColor(color), 2))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(QPointF(x, y), size, size)
    
    def _draw_stuck_projectile(self, painter: QPainter, proj):
        """Draw a stuck projectile"""
        x = getattr(proj, 'x', proj.get('x', 0)) if hasattr(proj, 'x') else proj.get('x', 0)
        y = getattr(proj, 'y', proj.get('y', 0)) if hasattr(proj, 'y') else proj.get('y', 0)
        proj_type = getattr(proj, 'projectile_type', proj.get('type', 'arrow'))
        
        if proj_type == "arrow":
            self._draw_arrow_stuck(painter, x, y)
        elif proj_type == "bolt":
            self._draw_bolt_stuck(painter, x, y)
        elif proj_type == "spear":
            self._draw_spear_stuck(painter, x, y)
    
    def _draw_arrow_stuck(self, painter: QPainter, x: int, y: int):
        """Draw stuck arrow"""
        painter.setPen(QPen(QColor("#8B4513"), 2))
        painter.drawLine(x, y, x + 20, y - 10)
        
        # Arrowhead
        points = [QPointF(x + 20, y - 10), QPointF(x + 25, y - 8), QPointF(x + 25, y - 12)]
        painter.setBrush(QBrush(QColor("#696969")))
        painter.drawPolygon(QPolygonF(points))
        
        # Fletching
        painter.setPen(QPen(QColor("#FF0000"), 1))
        painter.drawLine(x - 2, y + 1, x + 2, y + 3)
        painter.drawLine(x - 2, y - 1, x + 2, y - 3)
    
    def _draw_bolt_stuck(self, painter: QPainter, x: int, y: int):
        """Draw stuck crossbow bolt"""
        painter.setPen(QPen(QColor("#654321"), 3))
        painter.drawLine(x, y, x + 15, y - 5)
        
        # Bolt head
        painter.setBrush(QBrush(QColor("#808080")))
        painter.drawEllipse(QPointF(x + 15, y - 5), 3, 3)
    
    def _draw_spear_stuck(self, painter: QPainter, x: int, y: int):
        """Draw stuck spear"""
        painter.setPen(QPen(QColor("#8B4513"), 4))
        painter.drawLine(x, y, x + 30, y - 15)
        
        # Spearhead
        points = [
            QPointF(x + 30, y - 15),
            QPointF(x + 38, y - 12),
            QPointF(x + 35, y - 18)
        ]
        painter.setBrush(QBrush(QColor("#696969")))
        painter.drawPolygon(QPolygonF(points))
    
    def _draw_projectile(self, painter: QPainter, proj):
        """Draw flying projectile"""
        x = getattr(proj, 'x', 0)
        y = getattr(proj, 'y', 0)
        
        # Draw trail
        if hasattr(proj, 'trail_positions') and proj.trail_positions:
            painter.setPen(QPen(QColor("#FFFF00"), 2))
            for i in range(len(proj.trail_positions) - 1):
                p1 = proj.trail_positions[i]
                p2 = proj.trail_positions[i + 1]
                painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1]))
        
        # Draw projectile
        painter.setBrush(QBrush(QColor("#FF4500")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(x, y), 4, 4)


class VisualEffectsGLWidget(GLWidget):
    """OpenGL-based 3D visual effects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wounds = []
        self.projectiles = []
        self.stuck_projectiles = []
        self.rotation = 0.0
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(16)  # ~60 FPS
    
    def initializeGL(self):
        """Initialize OpenGL"""
        if not OPENGL_AVAILABLE:
            return
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.0, 0.0, 0.0, 0.0)
    
    def resizeGL(self, w, h):
        """Handle resize"""
        if not OPENGL_AVAILABLE:
            return
        
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h != 0 else 1, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render OpenGL effects"""
        if not OPENGL_AVAILABLE:
            return
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)
        
        # Render effects
        self._render_wounds_3d()
        self._render_projectiles_3d()
    
    def _render_wounds_3d(self):
        """Render 3D wounds"""
        for wound in self.wounds:
            x = getattr(wound, 'x', 0) / 100.0
            y = getattr(wound, 'y', 0) / 100.0
            size = getattr(wound, 'size', 10) / 100.0
            
            glPushMatrix()
            glTranslatef(x, y, 0)
            
            # Draw wound as sphere
            glColor4f(1.0, 0.0, 0.0, 0.7)
            self._draw_sphere(size, 10, 10)
            
            glPopMatrix()
    
    def _render_projectiles_3d(self):
        """Render 3D projectiles"""
        for proj in self.projectiles:
            if hasattr(proj, 'active') and proj.active:
                x = getattr(proj, 'x', 0) / 100.0
                y = getattr(proj, 'y', 0) / 100.0
                
                glPushMatrix()
                glTranslatef(x, y, 0)
                
                # Draw projectile
                glColor4f(1.0, 0.5, 0.0, 1.0)
                self._draw_sphere(0.05, 8, 8)
                
                glPopMatrix()
    
    def _draw_sphere(self, radius: float, slices: int, stacks: int):
        """Draw a sphere"""
        if not OPENGL_AVAILABLE:
            return
        quadric = gluNewQuadric()
        gluSphere(quadric, radius, slices, stacks)
        gluDeleteQuadric(quadric)
    
    def _update_animation(self):
        """Update animation"""
        self.rotation += 1.0
        if self.rotation >= 360.0:
            self.rotation = 0.0
        self.update()
    
    def set_wounds(self, wounds: List):
        """Set wounds"""
        self.wounds = wounds
    
    def set_projectiles(self, projectiles: List):
        """Set projectiles"""
        self.projectiles = projectiles
    
    def set_stuck_projectiles(self, stuck: List):
        """Set stuck projectiles"""
        self.stuck_projectiles = stuck


# Factory function
def create_visual_effects_widget(use_3d: bool = False, parent=None):
    """
    Create visual effects widget
    
    Args:
        use_3d: If True, use OpenGL 3D widget. If False, use 2D QPainter widget
        parent: Parent widget
    
    Returns:
        VisualEffectsWidget or VisualEffectsGLWidget
    """
    if use_3d and OPENGL_AVAILABLE:
        return VisualEffectsGLWidget(parent)
    else:
        return VisualEffectsWidget(parent)
