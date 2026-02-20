from __future__ import annotations
"""
PyQt6 QGraphicsView-based dungeon renderer.
Pure PyQt6 graphics rendering for dungeon visualization.
"""

try:
    from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem
    from PyQt6.QtCore import Qt, QRectF, QPointF
    from PyQt6.QtGui import QColor, QPen, QBrush, QPainter
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QGraphicsView = object
    QGraphicsScene = object
    QGraphicsEllipseItem = object
    QGraphicsRectItem = object
    QGraphicsTextItem = object
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
    class QPainter:
        def __init__(self, *a): pass
    class QPen:
        def __init__(self, *a): pass
    class QBrush:
        def __init__(self, *a): pass
    class QPoint:
        def __init__(self, x=0, y=0): self.x_=x; self.y_=y
        def x(self): return self.x_
        def y(self): return self.y_
    QPointF = QPoint
    class QRect:
        def __init__(self, *a): pass
    QRectF = QRect
from typing import Optional, Tuple, List


class DungeonGraphicsView(QGraphicsView):
    """
    PyQt6-based dungeon renderer using QGraphicsView/QGraphicsScene.
    
    Features:
    - Smooth scrolling
    - Zooming
    - Layered drawing
    - Collision detection ready
    - Hardware accelerated
    """
    
    def __init__(self, dungeon_data, parent=None):
        super().__init__(parent)
        
        self.dungeon = dungeon_data
        self.current_floor = 0
        self.camera_x = 0
        self.camera_y = 0
        self.tile_size = 32
        self.show_fog = True
        self.show_minimap = True
        
        # Create scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Set background
        self.setBackgroundBrush(QBrush(QColor("#1a1a1a")))
        
        # Initial render
        self.render_dungeon()
    
    def set_floor(self, floor_index: int):
        """Set current floor to display."""
        self.current_floor = floor_index
        self.render_dungeon()
    
    def center_camera_on_tile(self, x: int, y: int):
        """Center camera on specific tile."""
        self.camera_x = x
        self.camera_y = y
        self.centerOn(x * self.tile_size, y * self.tile_size)
    
    def render_dungeon(self):
        """Render the dungeon to the scene."""
        self.scene.clear()
        
        if not self.dungeon or self.current_floor >= len(self.dungeon):
            return
        
        floor_data = self.dungeon[self.current_floor]
        rows = len(floor_data)
        cols = len(floor_data[0]) if rows > 0 else 0
        
        # Tile colors
        tile_colors = {
            0: QColor("#1a1a1a"),  # Wall/void
            1: QColor("#3a3a3a"),  # Floor
            2: QColor("#00aa00"),  # Start
            3: QColor("#aa0000"),  # End/stairs
            4: QColor("#0000aa"),  # Water
            5: QColor("#aa5500"),  # Lava
        }
        
        # Draw tiles
        for row in range(rows):
            for col in range(cols):
                tile_type = floor_data[row][col]
                
                x = col * self.tile_size
                y = row * self.tile_size
                
                # Create tile rect
                color = tile_colors.get(tile_type, QColor("#1a1a1a"))
                rect = QGraphicsRectItem(x, y, self.tile_size, self.tile_size)
                rect.setBrush(QBrush(color))
                rect.setPen(QPen(QColor("#000000"), 1))
                self.scene.addItem(rect)
        
        # Set scene rect
        self.scene.setSceneRect(0, 0, cols * self.tile_size, rows * self.tile_size)
    
    def render_player(self, x: int, y: int):
        """Render player at position."""
        px = x * self.tile_size + self.tile_size / 2
        py = y * self.tile_size + self.tile_size / 2
        radius = self.tile_size / 3
        
        # Draw player circle
        player = QGraphicsEllipseItem(
            px - radius, py - radius,
            radius * 2, radius * 2
        )
        player.setBrush(QBrush(QColor("#ffff00")))
        player.setPen(QPen(QColor("#000000"), 2))
        self.scene.addItem(player)
    
    def render_enemies(self, enemies: List):
        """Render enemies on current floor."""
        for enemy in enemies:
            if enemy.get('floor') == self.current_floor and enemy.get('alive', True):
                ex = enemy['x'] * self.tile_size + self.tile_size / 2
                ey = enemy['y'] * self.tile_size + self.tile_size / 2
                radius = self.tile_size / 4
                
                # Draw enemy circle
                enemy_item = QGraphicsEllipseItem(
                    ex - radius, ey - radius,
                    radius * 2, radius * 2
                )
                enemy_item.setBrush(QBrush(QColor("#ff0000")))
                enemy_item.setPen(QPen(QColor("#000000"), 2))
                self.scene.addItem(enemy_item)
    
    def render_loot(self, loot_items: List):
        """Render loot items on current floor."""
        for loot in loot_items:
            if loot.get('floor') == self.current_floor and not loot.get('collected', False):
                lx = loot['x'] * self.tile_size + self.tile_size / 2
                ly = loot['y'] * self.tile_size + self.tile_size / 2
                size = self.tile_size / 5
                
                # Draw loot diamond
                loot_item = QGraphicsRectItem(
                    lx - size, ly - size,
                    size * 2, size * 2
                )
                loot_item.setBrush(QBrush(QColor("#ffaa00")))
                loot_item.setPen(QPen(QColor("#000000"), 1))
                loot_item.setRotation(45)  # Diamond shape
                self.scene.addItem(loot_item)
    
    def toggle_fog(self):
        """Toggle fog of war."""
        self.show_fog = not self.show_fog
        self.render_dungeon()
    
    def toggle_minimap(self):
        """Toggle minimap display."""
        self.show_minimap = not self.show_minimap
        self.render_dungeon()
    
    def wheelEvent(self, event):
        """Handle zoom with mouse wheel."""
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)
