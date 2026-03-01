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
except (ImportError, OSError, RuntimeError):
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

    def __init__(self, dungeon_data=None, parent=None, tooltip_manager=None):
        if not PYQT_AVAILABLE:
            raise ImportError(
                "DungeonGraphicsView requires PyQt6.\n"
                "Install with: pip install PyQt6"
            )
        super().__init__(parent)
        
        self.dungeon = dungeon_data
        self.tooltip_manager = tooltip_manager
        self.current_floor = 0
        self.camera_x = 0
        self.camera_y = 0
        self.tile_size = 32
        self.show_fog = True
        self.show_minimap = True

        # Player position (tile coordinates)
        self._player_x: int = 1
        self._player_y: int = 1
        self._player_item: 'Optional[QGraphicsTextItem]' = None
        
        # Create scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Set background
        self.setBackgroundBrush(QBrush(QColor("#0a0a1a")))
        
        # Initial render
        self.render_dungeon()

    def set_dungeon(self, dungeon):
        """Set the dungeon data and re-render."""
        self.dungeon = dungeon
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
        """Render the dungeon to the scene.

        Supports two dungeon data shapes:
        1. ``list[list[list[int]]]`` — a raw ``floors[floor][row][col]`` grid
           (legacy / test data).
        2. ``IntegratedDungeon`` / any object with a ``.dungeon`` attribute that
           has a ``get_floor(n)`` method returning a ``DungeonFloor`` with a
           ``collision_map`` 2-D list.
        """
        self.scene.clear()

        if not self.dungeon:
            return

        # ── Resolve floor_data ────────────────────────────────────────────
        floor_data = None
        floor_obj  = None  # DungeonFloor when available (used for stair drawing)

        # Shape 1: plain list-of-floors (each floor is a 2-D list)
        if isinstance(self.dungeon, list):
            if self.current_floor < len(self.dungeon):
                floor_data = self.dungeon[self.current_floor]

        # Shape 2: IntegratedDungeon wrapper (has .dungeon with get_floor())
        elif hasattr(self.dungeon, 'dungeon') and hasattr(self.dungeon.dungeon, 'get_floor'):
            dg = self.dungeon.dungeon  # DungeonGenerator
            floor_obj = dg.get_floor(self.current_floor)
            if floor_obj is not None:
                floor_data = floor_obj.collision_map  # list[list[int]], 1=wall 0=walkable

        # Shape 3: DungeonGenerator directly (has get_floor())
        elif hasattr(self.dungeon, 'get_floor'):
            floor_obj = self.dungeon.get_floor(self.current_floor)
            if floor_obj is not None:
                floor_data = floor_obj.collision_map

        if floor_data is None:
            return

        rows = len(floor_data)
        cols = len(floor_data[0]) if rows > 0 else 0

        # Tile colors — collision_map: 0=walkable floor, 1=wall
        # Using distinctly visible colors so the dungeon is not all-black.
        tile_colors = {
            0: QColor("#4a3828"),  # Walkable floor — warm stone brown
            1: QColor("#1c1c2e"),  # Wall — deep indigo-black (visibly darker)
            2: QColor("#2e7d32"),  # Start (legacy)
            3: QColor("#b71c1c"),  # End / stairs down (legacy)
            4: QColor("#0d47a1"),  # Water (legacy)
            5: QColor("#bf360c"),  # Lava (legacy)
        }
        wall_pen   = QPen(QColor("#0d0d1a"), 1)  # hairline grid on walls
        floor_pen  = QPen(QColor("#5a4838"), 1)  # subtle grout lines on floor

        # Find player starting position: first walkable tile
        start_row, start_col = 1, 1
        if floor_obj is not None:
            for (sr, sc) in getattr(floor_obj, 'start_positions', []):
                start_row, start_col = sr, sc
                break
        # If start_positions is empty or points to a wall, scan for first walkable tile
        in_bounds = (0 <= start_row < rows
                     and 0 <= start_col < len(floor_data[start_row]))
        on_floor  = in_bounds and floor_data[start_row][start_col] == 0
        if not on_floor:
            start_row, start_col = None, None
            found_walkable = False
            for sr in range(rows):
                if found_walkable:
                    break
                for sc in range(len(floor_data[sr])):
                    if floor_data[sr][sc] == 0:
                        start_row, start_col = sr, sc
                        found_walkable = True
                        break
            if start_row is None:
                start_row, start_col = 1, 1

        # Draw tiles
        for row in range(rows):
            for col in range(cols):
                tile_type = floor_data[row][col]

                x = col * self.tile_size
                y = row * self.tile_size

                color = tile_colors.get(tile_type, QColor("#1c1c2e"))
                rect = QGraphicsRectItem(x, y, self.tile_size, self.tile_size)
                rect.setBrush(QBrush(color))
                rect.setPen(floor_pen if tile_type == 0 else wall_pen)
                self.scene.addItem(rect)

        # Draw stairs markers — reuse floor_obj already resolved above
        if floor_obj is not None:
            stair_color = QColor("#ffd700")
            stair_pen   = QPen(QColor("#b8860b"), 2)
            for (sx, sy) in getattr(floor_obj, 'stairs_down', []):
                rect = QGraphicsRectItem(sx * self.tile_size + 4, sy * self.tile_size + 4,
                                        self.tile_size - 8, self.tile_size - 8)
                rect.setBrush(QBrush(stair_color))
                rect.setPen(stair_pen)
                self.scene.addItem(rect)
                # Stair label
                lbl = QGraphicsTextItem("▼")
                lbl.setDefaultTextColor(QColor("#0a0a0a"))
                lbl.setPos(sx * self.tile_size + 6, sy * self.tile_size + 4)
                self.scene.addItem(lbl)

        # Place player panda at starting position
        if self._player_x == 1 and self._player_y == 1:
            # Initialise to starting tile on first render
            self._player_x = start_col
            self._player_y = start_row
        self._draw_player()

        # Set scene rect and centre on player
        self.scene.setSceneRect(0, 0, cols * self.tile_size, rows * self.tile_size)
        self.centerOn(self._player_x * self.tile_size, self._player_y * self.tile_size)
    
    def _draw_player(self) -> None:
        """Draw the panda player emoji at the current player position."""
        if self._player_item is not None:
            try:
                self.scene.removeItem(self._player_item)
            except Exception:
                pass

        lbl = QGraphicsTextItem("🐼")
        font = lbl.font()
        font.setPixelSize(max(16, self.tile_size - 6))
        lbl.setFont(font)
        lbl.setPos(
            self._player_x * self.tile_size,
            self._player_y * self.tile_size - 4,
        )
        lbl.setZValue(10)   # above tiles
        self.scene.addItem(lbl)
        self._player_item = lbl

    def _get_floor_data(self):
        """Return (floor_data, floor_obj) for the current floor, or (None, None)."""
        if isinstance(self.dungeon, list):
            if self.current_floor < len(self.dungeon):
                return self.dungeon[self.current_floor], None
        elif hasattr(self.dungeon, 'dungeon') and hasattr(self.dungeon.dungeon, 'get_floor'):
            floor_obj = self.dungeon.dungeon.get_floor(self.current_floor)
            if floor_obj is not None:
                return floor_obj.collision_map, floor_obj
        elif hasattr(self.dungeon, 'get_floor'):
            floor_obj = self.dungeon.get_floor(self.current_floor)
            if floor_obj is not None:
                return floor_obj.collision_map, floor_obj
        return None, None

    def _is_walkable(self, col: int, row: int) -> bool:
        """Return True if tile (col, row) is walkable (not a wall)."""
        floor_data, _ = self._get_floor_data()
        if floor_data is None:
            return False
        if row < 0 or row >= len(floor_data):
            return False
        if col < 0 or col >= len(floor_data[row]):
            return False
        return floor_data[row][col] == 0  # 0 = walkable

    def keyPressEvent(self, event) -> None:
        """WASD / arrow key movement for the dungeon panda."""
        dx, dy = 0, 0
        key = event.key()
        if key in (Qt.Key.Key_W, Qt.Key.Key_Up):
            dy = -1
        elif key in (Qt.Key.Key_S, Qt.Key.Key_Down):
            dy = 1
        elif key in (Qt.Key.Key_A, Qt.Key.Key_Left):
            dx = -1
        elif key in (Qt.Key.Key_D, Qt.Key.Key_Right):
            dx = 1
        else:
            super().keyPressEvent(event)
            return

        nx = self._player_x + dx
        ny = self._player_y + dy
        if self._is_walkable(nx, ny):
            self._player_x = nx
            self._player_y = ny
            self._draw_player()
            self.centerOn(nx * self.tile_size, ny * self.tile_size)

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
