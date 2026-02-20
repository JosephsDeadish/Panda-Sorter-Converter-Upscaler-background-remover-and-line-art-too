from __future__ import annotations
"""
PyQt6-based visual effects renderer using QGraphicsScene.
Pure PyQt6 graphics rendering for visual effects and animations.
"""

try:
    from PyQt6.QtWidgets import QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPolygonItem
    from PyQt6.QtCore import Qt, QPointF, QLineF
    from PyQt6.QtGui import QColor, QPen, QBrush, QPolygonF
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QGraphicsScene = object
    QGraphicsEllipseItem = object
    QGraphicsLineItem = object
    class Qt:
        class AlignmentFlag:
            AlignLeft = AlignRight = AlignCenter = AlignTop = AlignBottom = AlignHCenter = AlignVCenter = 0
        class WindowType:
            FramelessWindowHint = WindowStaysOnTopHint = Tool = Window = Dialog = 0
        class CursorShape:
            ArrowCursor = PointingHandCursor = BusyCursor = WaitCursor = CrossCursor = 0
        class DropAction:
            CopyAction = MoveAction = IgnoreAction = 0
        class Key:
            Key_Escape = Key_Return = Key_Space = Key_Delete = Key_Up = Key_Down = Key_Left = Key_Right = 0
        class ScrollBarPolicy:
            ScrollBarAlwaysOff = ScrollBarAsNeeded = ScrollBarAlwaysOn = 0
        class ItemFlag:
            ItemIsEnabled = ItemIsSelectable = ItemIsEditable = 0
        class CheckState:
            Unchecked = Checked = PartiallyChecked = 0
        class Orientation:
            Horizontal = Vertical = 0
        class SortOrder:
            AscendingOrder = DescendingOrder = 0
        class MatchFlag:
            MatchExactly = MatchContains = 0
        class ItemDataRole:
            DisplayRole = UserRole = DecorationRole = 0
    class QColor:
        def __init__(self, *a): pass
        def name(self): return "#000000"
        def isValid(self): return False
    class QPen:
        def __init__(self, *a): pass
    class QBrush:
        def __init__(self, *a): pass
    class QPoint:
        def __init__(self, x=0, y=0): self.x_=x; self.y_=y
        def x(self): return self.x_
        def y(self): return self.y_
    QPointF = QPoint
    QGraphicsPolygonItem = object
    QLineF = object
    QPolygonF = object
import math
from typing import List, Tuple, Optional


class VisualEffectsGraphicsRenderer:
    """
    PyQt6-based visual effects renderer.
    
    Uses QGraphicsScene for rendering visual effects:
    - Wounds
    - Stuck projectiles
    - Flying projectiles
    - Damage indicators
    - Bleeding effects
    
    Pure PyQt implementation with hardware acceleration.
    """
    
    def __init__(self):
        """Initialize visual effects renderer."""
        self.show_debug = False
    
    def render_wounds(self, scene: QGraphicsScene, wounds: List,
                     offset_x: int = 0, offset_y: int = 0,
                     scale: float = 1.0):
        """
        Render visual wounds on a QGraphicsScene.
        
        Args:
            scene: QGraphicsScene to draw on (NOT canvas!)
            wounds: List of VisualWound objects from DamageTracker
            offset_x: X offset for positioning
            offset_y: Y offset for positioning
            scale: Scale factor for wound sizes
        """
        for wound in wounds:
            # Calculate position
            wx = offset_x + wound.position[0]
            wy = offset_y + wound.position[1]
            
            # Scale size based on severity
            size = int(wound.size * scale)
            
            # Render based on wound type
            if wound.wound_type == "gash":
                self._draw_gash(scene, wx, wy, size, wound.color, wound.severity)
            elif wound.wound_type == "bruise":
                self._draw_bruise(scene, wx, wy, size, wound.color, wound.severity)
            elif wound.wound_type == "hole":
                self._draw_hole(scene, wx, wy, size, wound.color)
            elif wound.wound_type == "burn":
                self._draw_burn(scene, wx, wy, size, wound.color, wound.severity)
            elif wound.wound_type == "frostbite":
                self._draw_frostbite(scene, wx, wy, size, wound.color)
            else:
                # Generic wound
                self._draw_generic_wound(scene, wx, wy, size, wound.color)
    
    def render_stuck_projectiles(self, scene: QGraphicsScene, projectiles: List,
                                 offset_x: int = 0, offset_y: int = 0,
                                 scale: float = 1.0):
        """
        Render projectiles stuck in body.
        
        Args:
            scene: QGraphicsScene to draw on (NOT canvas!)
            projectiles: List of ProjectileStuck objects
            offset_x: X offset for positioning
            offset_y: Y offset for positioning
            scale: Scale factor
        """
        for proj in projectiles:
            px = offset_x + int(proj.position[0] * scale)
            py = offset_y + int(proj.position[1] * scale)
            
            if proj.projectile_type == "arrow":
                self._draw_arrow_stuck(scene, px, py, scale)
            elif proj.projectile_type == "bolt":
                self._draw_bolt_stuck(scene, px, py, scale)
            elif proj.projectile_type == "spear":
                self._draw_spear_stuck(scene, px, py, scale)
    
    def render_projectile(self, scene: QGraphicsScene, projectile,
                         offset_x: int = 0, offset_y: int = 0):
        """
        Render a flying projectile.
        
        Args:
            scene: QGraphicsScene to draw on (NOT canvas!)
            projectile: Projectile object with position, velocity
            offset_x: X offset
            offset_y: Y offset
        """
        px = offset_x + projectile.position[0]
        py = offset_y + projectile.position[1]
        
        # Draw projectile based on type
        if projectile.projectile_type == "arrow":
            self._draw_flying_arrow(scene, px, py, projectile.angle)
        elif projectile.projectile_type == "fireball":
            self._draw_fireball(scene, px, py)
        else:
            # Generic projectile
            item = QGraphicsEllipseItem(px - 3, py - 3, 6, 6)
            item.setBrush(QBrush(QColor(255, 200, 0)))
            scene.addItem(item)
    
    def _draw_gash(self, scene: QGraphicsScene, x: int, y: int, size: int,
                   color: Tuple[int, int, int], severity: float):
        """Draw gash wound using QGraphicsScene."""
        qcolor = QColor(*color)
        
        # Draw as irregular line
        width = int(size * 0.3)
        line = QGraphicsLineItem(x - size/2, y, x + size/2, y + width/2)
        line.setPen(QPen(qcolor, width, Qt.PenStyle.SolidLine))
        scene.addItem(line)
    
    def _draw_bruise(self, scene: QGraphicsScene, x: int, y: int, size: int,
                    color: Tuple[int, int, int], severity: float):
        """Draw bruise using QGraphicsScene."""
        qcolor = QColor(*color)
        qcolor.setAlpha(int(180 * severity))
        
        # Draw as semi-transparent oval
        item = QGraphicsEllipseItem(x - size/2, y - size/3, size, size * 0.66)
        item.setBrush(QBrush(qcolor))
        item.setPen(QPen(Qt.PenStyle.NoPen))
        scene.addItem(item)
    
    def _draw_hole(self, scene: QGraphicsScene, x: int, y: int, size: int,
                   color: Tuple[int, int, int]):
        """Draw hole wound using QGraphicsScene."""
        # Outer dark ring
        outer = QGraphicsEllipseItem(x - size/2, y - size/2, size, size)
        outer.setBrush(QBrush(QColor(50, 0, 0)))
        outer.setPen(QPen(QColor(*color), 2))
        scene.addItem(outer)
        
        # Inner black hole
        inner_size = size * 0.6
        inner = QGraphicsEllipseItem(
            x - inner_size/2, y - inner_size/2,
            inner_size, inner_size
        )
        inner.setBrush(QBrush(QColor(0, 0, 0)))
        inner.setPen(QPen(Qt.PenStyle.NoPen))
        scene.addItem(inner)
    
    def _draw_burn(self, scene: QGraphicsScene, x: int, y: int, size: int,
                   color: Tuple[int, int, int], severity: float):
        """Draw burn mark using QGraphicsScene."""
        # Dark burn with orange edges
        burn_color = QColor(30, 20, 10)
        edge_color = QColor(200, 100, 0, int(150 * severity))
        
        # Center dark area
        center = QGraphicsEllipseItem(x - size/2, y - size/2, size, size)
        center.setBrush(QBrush(burn_color))
        center.setPen(QPen(edge_color, 3))
        scene.addItem(center)
    
    def _draw_frostbite(self, scene: QGraphicsScene, x: int, y: int, size: int,
                       color: Tuple[int, int, int]):
        """Draw frostbite using QGraphicsScene."""
        # Blue-white frozen area
        frost_color = QColor(200, 220, 255, 180)
        
        item = QGraphicsEllipseItem(x - size/2, y - size/2, size, size)
        item.setBrush(QBrush(frost_color))
        item.setPen(QPen(QColor(150, 180, 255), 2))
        scene.addItem(item)
    
    def _draw_generic_wound(self, scene: QGraphicsScene, x: int, y: int,
                           size: int, color: Tuple[int, int, int]):
        """Draw generic wound using QGraphicsScene."""
        qcolor = QColor(*color)
        
        item = QGraphicsEllipseItem(x - size/2, y - size/2, size, size)
        item.setBrush(QBrush(qcolor))
        item.setPen(QPen(QColor(100, 0, 0), 2))
        scene.addItem(item)
    
    def _draw_arrow_stuck(self, scene: QGraphicsScene, x: int, y: int, scale: float):
        """Draw stuck arrow using QGraphicsScene."""
        length = 20 * scale
        
        # Arrow shaft
        shaft = QGraphicsLineItem(x, y, x + length, y - length/2)
        shaft.setPen(QPen(QColor(139, 69, 19), int(2 * scale)))
        scene.addItem(shaft)
        
        # Arrow head
        head_size = 5 * scale
        head_points = QPolygonF([
            QPointF(x + length, y - length/2),
            QPointF(x + length - head_size, y - length/2 - head_size/2),
            QPointF(x + length - head_size, y - length/2 + head_size/2),
        ])
        head = QGraphicsPolygonItem(head_points)
        head.setBrush(QBrush(QColor(150, 150, 150)))
        scene.addItem(head)
    
    def _draw_bolt_stuck(self, scene: QGraphicsScene, x: int, y: int, scale: float):
        """Draw stuck crossbow bolt using QGraphicsScene."""
        length = 15 * scale
        
        # Bolt shaft (shorter than arrow)
        shaft = QGraphicsLineItem(x, y, x + length, y - length/3)
        shaft.setPen(QPen(QColor(100, 50, 0), int(3 * scale)))
        scene.addItem(shaft)
    
    def _draw_spear_stuck(self, scene: QGraphicsScene, x: int, y: int, scale: float):
        """Draw stuck spear using QGraphicsScene."""
        length = 30 * scale
        
        # Spear shaft
        shaft = QGraphicsLineItem(x, y, x + length, y - length/4)
        shaft.setPen(QPen(QColor(120, 80, 40), int(3 * scale)))
        scene.addItem(shaft)
        
        # Spear head
        head_size = 8 * scale
        head_points = QPolygonF([
            QPointF(x + length, y - length/4),
            QPointF(x + length - head_size, y - length/4 - head_size/3),
            QPointF(x + length - head_size, y - length/4 + head_size/3),
        ])
        head = QGraphicsPolygonItem(head_points)
        head.setBrush(QBrush(QColor(180, 180, 180)))
        scene.addItem(head)
    
    def _draw_flying_arrow(self, scene: QGraphicsScene, x: int, y: int, angle: float):
        """Draw flying arrow using QGraphicsScene."""
        length = 25
        
        # Calculate end point based on angle
        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        
        # Arrow shaft
        shaft = QGraphicsLineItem(x, y, end_x, end_y)
        shaft.setPen(QPen(QColor(139, 69, 19), 2))
        scene.addItem(shaft)
    
    def _draw_fireball(self, scene: QGraphicsScene, x: int, y: int):
        """Draw fireball using QGraphicsScene."""
        # Outer glow
        outer = QGraphicsEllipseItem(x - 8, y - 8, 16, 16)
        outer.setBrush(QBrush(QColor(255, 150, 0, 150)))
        outer.setPen(QPen(Qt.PenStyle.NoPen))
        scene.addItem(outer)
        
        # Inner fire
        inner = QGraphicsEllipseItem(x - 5, y - 5, 10, 10)
        inner.setBrush(QBrush(QColor(255, 255, 0)))
        inner.setPen(QPen(QColor(255, 0, 0), 1))
        scene.addItem(inner)
