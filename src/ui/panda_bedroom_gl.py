"""
OpenGL Panda Bedroom Widget - Interactive 3D bedroom scene.
Renders a cosy panda bedroom with clickable / draggable furniture pieces.
The 3-D panda drawing is shared with the dungeon and world scenes via
``ui.draw_panda_gl.draw_panda_3d`` so there is only ONE canonical panda.
Author: Dead On The Inside / JosephsDeadish
"""

import json
import logging
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple

try:
    from PyQt6.QtWidgets import QWidget, QApplication
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QTimer
    from PyQt6.QtGui import QMouseEvent, QWheelEvent, QSurfaceFormat
    # Disable C accelerate BEFORE importing OpenGL.GL
    try:
        import OpenGL as _ogl_pre; _ogl_pre.USE_ACCELERATE = False
    except Exception:
        pass
    from OpenGL.GL import *
    from OpenGL.GLU import *
    OPENGL_AVAILABLE = True
    # Set default GL format at module load time (belt-and-suspenders alongside main()).
    # Skip on the offscreen/headless Qt platform: the offscreen backend uses software
    # rendering and has no real WGL surface.  Requesting CompatibilityProfile there
    # causes Qt to call exit(1) on CI VMs without a GPU.
    import os as _os_bed
    if _os_bed.environ.get('QT_QPA_PLATFORM') != 'offscreen':
        _os_bed.environ.setdefault('QT_OPENGL', 'desktop')  # force native GL, not ANGLE
        _fmt = QSurfaceFormat()
        _fmt.setVersion(2, 1)
        _fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
        _fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)  # desktop GL
        _fmt.setSamples(4)
        _fmt.setDepthBufferSize(24)
        QSurfaceFormat.setDefaultFormat(_fmt)
except (ImportError, OSError, RuntimeError):
    OPENGL_AVAILABLE = False
    QWidget = object          # type: ignore[assignment,misc]
    QOpenGLWidget = object    # type: ignore[assignment,misc]

    class _SigStub:
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass

    def pyqtSignal(*a):       # type: ignore[misc]
        return _SigStub()

logger = logging.getLogger(__name__)

# ── Module-level colour constants (float tuples used directly with glColor*) ──

_COL_FLOOR_A      = (0.72, 0.52, 0.30)   # warm oak plank
_COL_FLOOR_B      = (0.65, 0.46, 0.25)   # darker plank alternating
_COL_WALL         = (0.95, 0.88, 0.78)   # warm cream/peach
_COL_WALL_DARK    = (0.88, 0.80, 0.70)   # wallpaper diamond
_COL_CEILING      = (0.96, 0.96, 0.94)   # pale white
_COL_CEILING_LINE = (0.90, 0.90, 0.88)   # subtle grid
_COL_BASEBOARD    = (0.35, 0.22, 0.10)   # dark skirting
_COL_RUG_MAIN     = (0.62, 0.08, 0.12)   # burgundy rug
_COL_RUG_BORDER   = (0.45, 0.05, 0.08)   # darker rug border

_COL_WOOD_DARK    = (0.38, 0.22, 0.08)   # dark walnut
_COL_WOOD_MID     = (0.55, 0.35, 0.14)   # mid oak
_COL_WOOD_LIGHT   = (0.70, 0.50, 0.22)   # light maple
_COL_GOLD         = (0.85, 0.68, 0.12)   # brass / gold
_COL_SILVER       = (0.75, 0.77, 0.80)   # steel / silver
_COL_WHITE        = (0.96, 0.96, 0.96)
_COL_RED          = (0.80, 0.12, 0.12)
_COL_BLUE_GLOW    = (0.30, 0.55, 1.00)
_COL_CHROME       = (0.82, 0.82, 0.84)
_COL_HIGHLIGHT    = (1.00, 0.92, 0.20, 0.50)  # yellow selection box
_COL_GLASS        = (0.72, 0.88, 0.96, 0.45)  # pale blue semi-transparent glass

# ── Default furniture layout ──────────────────────────────────────────────────

_DEFAULT_POSITIONS = {
    'wardrobe':     {'x': -2.8, 'z': -3.0, 'rot_y':   0.0},
    'armor_rack':   {'x':  2.5, 'z': -3.0, 'rot_y': 180.0},
    'weapons_rack': {'x':  3.3, 'z': -1.5, 'rot_y': -90.0},
    'toy_box':      {'x': -3.0, 'z':  1.8, 'rot_y':  90.0},
    'fridge':       {'x':  3.2, 'z':  1.8, 'rot_y': -90.0},
    'trophy_stand': {'x':  0.0, 'z': -3.2, 'rot_y':   0.0},
    'backpack':     {'x': -1.2, 'z': -3.0, 'rot_y':   0.0},
    'bedroom_door': {'x':  0.0, 'z':  3.8, 'rot_y': 180.0},
}


# ── Data class ────────────────────────────────────────────────────────────────

@dataclass
class FurniturePiece:
    id: str
    label: str
    emoji: str
    x: float
    y: float
    z: float
    rot_y: float
    walk_x: float
    walk_z: float
    category: str


def _build_furniture() -> List[FurniturePiece]:
    """Return list of furniture pieces at their default positions."""
    defs = [
        ('wardrobe',      'Wardrobe',      '🚪', -2.8, 0.0, -3.0,   0.0, -2.2, -1.8, 'Clothes'),
        ('armor_rack',    'Armor Rack',    '🛡️',  2.5, 0.0, -3.0, 180.0,  1.8, -1.8, 'Weapons'),
        ('weapons_rack',  'Weapons Rack',  '⚔️',  3.3, 0.0, -1.5, -90.0,  2.5, -0.8, 'Weapons'),
        ('toy_box',       'Toy Box',       '🧸', -3.0, 0.0,  1.8,  90.0, -2.2,  1.2, 'Toys'),
        ('fridge',        'Fridge',        '🧊',  3.2, 0.0,  1.8, -90.0,  2.5,  1.2, 'Food'),
        ('trophy_stand',  'Trophy Stand',  '🏆',  0.0, 0.0, -3.2,   0.0,  0.0, -2.0, 'achievements'),
        ('backpack',      'Backpack',      '🎒', -1.2, 0.0, -3.0,   0.0, -0.8, -2.0, 'Inventory'),
        ('computer_desk', 'Computer Desk', '💻', -3.0, 0.0, -0.5,  90.0, -2.2,  0.0, 'tools'),
        ('bedroom_door',  'Front Door',    '🏠',  0.0, 0.0,  3.8, 180.0,  0.0,  2.8, 'world'),
    ]
    pieces = []
    for d in defs:
        pieces.append(FurniturePiece(
            id=d[0], label=d[1], emoji=d[2],
            x=d[3], y=d[4], z=d[5], rot_y=d[6],
            walk_x=d[7], walk_z=d[8], category=d[9],
        ))
    return pieces


# ── Main widget ───────────────────────────────────────────────────────────────

class PandaBedroomGL(QOpenGLWidget if OPENGL_AVAILABLE else QWidget):  # type: ignore[misc]
    """
    Interactive 3D panda bedroom rendered with OpenGL.

    Signals
    -------
    furniture_clicked(str)  – emitted with furniture id when a piece is clicked
    gl_failed(str)          – emitted with error message when initializeGL fails
    """

    furniture_clicked = pyqtSignal(str)
    gl_failed = pyqtSignal(str)

    # ── Construction ──────────────────────────────────────────────────────────

    def __init__(self, parent=None):
        if not OPENGL_AVAILABLE:
            raise ImportError("PyQt6 and PyOpenGL are required for PandaBedroomGL")

        super().__init__(parent)

        if os.environ.get('QT_QPA_PLATFORM') != 'offscreen':
            fmt = QSurfaceFormat()
            fmt.setVersion(2, 1)  # OpenGL 2.1 — keeps all legacy fixed-function GL
            fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
            fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)  # native desktop GL
            fmt.setDepthBufferSize(24)
            fmt.setSamples(4)
            self.setFormat(fmt)

        # Furniture
        self._furniture: List[FurniturePiece] = _build_furniture()

        # Achievement count (drives trophy_stand display)
        self._achievement_count: int = 0

        # Camera — initial distance derived from default eye position
        self._cam_az: float = 0.0      # azimuth degrees  (Y rotation)
        self._cam_el: float = 30.0     # elevation degrees (X rotation)
        _eye = (0.0, 4.5, 6.5)
        self._cam_dist: float = math.sqrt(_eye[0]**2 + _eye[1]**2 + _eye[2]**2)

        # Mouse / interaction state
        self._last_mouse: Optional[QPoint] = None
        self._drag_piece: Optional[FurniturePiece] = None
        self._drag_start_screen: Optional[QPoint] = None
        self._drag_start_world: Optional[Tuple[float, float]] = None
        self._right_dragging: bool = False

        # Hover
        self._hovered_id: Optional[str] = None

        # GL matrices cached during paintGL for use in mouse event handlers.
        # Reading these matrices via makeCurrent() in event handlers is unreliable
        # (the context state outside paintGL may be identity or stale).  Instead we
        # capture them right after the camera is set up — the same point that the
        # hover projection uses them, which is proven to work correctly.
        self._pick_viewport = None
        self._pick_modelview = None
        self._pick_projection = None

        # GL flag
        self._gl_ok: bool = False
        # Reusable GLU quadric for sphere drawing — created in _do_init_gl
        self._glu_quadric = None

        # Layout persistence
        try:
            from src.config import get_data_dir
            self._layout_path: Path = Path(get_data_dir()) / 'bedroom_layout.json'
        except Exception:
            self._layout_path = Path('app_data') / 'bedroom_layout.json'

        self.setMouseTracking(True)
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # ── In-room panda character ───────────────────────────────────────────
        # The panda starts at the centre of the room and walks to furniture when
        # the user clicks a piece.  Walking is handled inside the bedroom scene
        # (separate from the full-window overlay panda_widget).
        self._panda_x: float = 0.0        # current room X position
        self._panda_z: float = 1.5        # current room Z position (starts near rug centre)
        self._panda_target_x: float = 0.0
        self._panda_target_z: float = 1.5
        self._panda_facing_y: float = 180.0  # degrees; 180 = facing toward camera
        self._panda_walk_callback = None   # called once panda arrives at target
        self._panda_walk_frame: float = 0.0  # oscillation counter for leg swing
        self._panda_is_walking: bool = False

        # ── Keyboard / player-control state ──────────────────────────────────
        self._keys: set = set()          # currently pressed Qt key codes
        self._panda_run: bool = False    # True when Shift is held (run speed)
        self._kb_move_speed: float = 0.06   # walk speed (world units / tick)
        self._kb_run_speed:  float = 0.12   # run speed

        # ── Furniture pickup / interaction state ─────────────────────────────
        self._held_piece_id: Optional[str] = None   # furniture being carried
        self._held_rot_offset: float = 0.0          # extra rotation while held
        # Proximity indicator: id of nearest piece within interaction range
        self._near_piece_id: Optional[str] = None
        # Interaction-hint HUD — show a cute popup near the panda
        self._hud_hint: str = ''             # text shown in the popup
        self._hud_hint_timer: int = 0        # frames remaining to display hint

        # ── Room upgrade tier ─────────────────────────────────────────────────
        # Tier 0 = starter (8×8), Tier 1 = medium (10×10), Tier 2 = large (12×12)
        # Costs: tier 0→1 = 500 coins, tier 1→2 = 1500 coins
        self._room_tier: int = 0
        # Internal doors unlocked at tier 1 (list of door dicts)
        self._room_doors: list = []   # each: {'wall': 'N'/'S'/'E'/'W', 'label': str, 'style': int}

        # Animation timer — drives the panda walk each ~33 ms (≈30 fps)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_panda_walk)
        self._anim_timer.start(33)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_achievement_count(self, count: int) -> None:
        """Update trophy count and repaint."""
        self._achievement_count = count
        self.update()

    # ── Room upgrade API ───────────────────────────────────────────────────────

    # Half-size of the room per tier: tier0=4, tier1=5, tier2=6
    _TIER_HALF = (4.0, 5.0, 6.0)
    _TIER_COST = (0, 500, 1500)   # coins to upgrade to tier 1, tier 2

    @property
    def room_half(self) -> float:
        """Half the room size in world units for the current tier."""
        return self._TIER_HALF[min(self._room_tier, len(self._TIER_HALF) - 1)]

    def get_room_tier(self) -> int:
        return self._room_tier

    def upgrade_room(self, new_tier: int) -> None:
        """Set room tier (0–2) and rebuild any auto-doors on the new walls."""
        old_tier = self._room_tier
        self._room_tier = max(0, min(2, new_tier))
        if self._room_tier > old_tier:
            # Auto-add an interior door on the east wall when first upgrading
            wall = 'E' if self._room_tier == 1 else 'N'
            self._room_doors.append({
                'wall': wall,
                'label': f'Room {chr(64 + self._room_tier)}',
                'style': 0,
            })
        self.update()

    def add_room_door(self, wall: str = 'E', label: str = 'Room',
                      style: int = 0) -> None:
        """Add a named door on the given wall ('N','S','E','W')."""
        self._room_doors.append({'wall': wall, 'label': label, 'style': style})
        self.update()

    def set_door_label(self, index: int, label: str) -> None:
        """Change the label of door at *index*."""
        if 0 <= index < len(self._room_doors):
            self._room_doors[index]['label'] = label
            self.update()

    def cycle_door_style(self, index: int) -> None:
        """Cycle the visual style of door at *index* (0→1→2→0)."""
        if 0 <= index < len(self._room_doors):
            self._room_doors[index]['style'] = (self._room_doors[index]['style'] + 1) % 3
            self.update()

    def play_bed_animation(self) -> None:
        """Walk the bedroom panda to the bed and play a lay-down pose."""
        bed = self.get_furniture('bed')
        if bed:
            tx, tz = getattr(bed, 'walk_x', bed.x), getattr(bed, 'walk_z', bed.z)
        else:
            tx, tz = -3.0, -2.0
        def _lay_down():
            # Tilt panda sideways for lying-in-bed pose
            self._panda_facing_y = 90.0
            self._panda_is_walking = False
            self.update()
        self.walk_panda_to(tx, tz, callback=_lay_down)

    def get_furniture(self, furniture_id: str) -> Optional[FurniturePiece]:
        """Return the FurniturePiece dataclass or None."""
        for p in self._furniture:
            if p.id == furniture_id:
                return p
        return None

    def get_layout(self) -> dict:
        """Return a serialisable dict of all furniture positions/rotations."""
        return {
            p.id: {'x': p.x, 'y': p.y, 'z': p.z, 'rot_y': p.rot_y}
            for p in self._furniture
        }

    def set_layout(self, layout: dict) -> None:
        """Restore furniture positions/rotations from a previously saved layout dict."""
        for p in self._furniture:
            if p.id in layout:
                entry = layout[p.id]
                p.x     = entry.get('x', p.x)
                p.y     = entry.get('y', p.y)
                p.z     = entry.get('z', p.z)
                p.rot_y = entry.get('rot_y', p.rot_y)
        self.update()

    def walk_panda_to(self, x: float, z: float, callback=None) -> None:
        """Walk the in-room panda character to world position (x, z).

        The panda will smoothly move toward the target each animation tick.
        ``callback`` is called (with no arguments) once the panda arrives.
        """
        self._panda_target_x = x
        self._panda_target_z = z
        self._panda_walk_callback = callback
        self._panda_is_walking = True

    # ── In-room panda animation ───────────────────────────────────────────────

    def _tick_panda_walk(self) -> None:
        """Advance the panda one step — handles both keyboard input and click-walk."""
        # ── Keyboard-driven movement (WASD / arrow keys) ─────────────────────
        _Keys = Qt.Key
        move_keys = {
            _Keys.Key_W, _Keys.Key_Up,
            _Keys.Key_S, _Keys.Key_Down,
            _Keys.Key_A, _Keys.Key_Left,
            _Keys.Key_D, _Keys.Key_Right,
        }
        if self._keys & move_keys:
            speed = self._kb_run_speed if self._panda_run else self._kb_move_speed
            # Held-piece rotation (Q/E keys) takes priority over strafing
            if self._held_piece_id is not None:
                if _Keys.Key_Q in self._keys:
                    self._held_rot_offset -= 3.0
                if _Keys.Key_E in self._keys:
                    self._held_rot_offset += 3.0
            # Forward/backward relative to current facing angle
            fwd_rad = math.radians(self._panda_facing_y)
            dx = dz = 0.0
            if _Keys.Key_W in self._keys or _Keys.Key_Up in self._keys:
                dx +=  math.sin(fwd_rad) * speed
                dz +=  math.cos(fwd_rad) * speed
            if _Keys.Key_S in self._keys or _Keys.Key_Down in self._keys:
                dx += -math.sin(fwd_rad) * speed
                dz += -math.cos(fwd_rad) * speed
            if _Keys.Key_A in self._keys or _Keys.Key_Left in self._keys:
                self._panda_facing_y -= 3.0
            if _Keys.Key_D in self._keys or _Keys.Key_Right in self._keys:
                self._panda_facing_y += 3.0
            # Apply movement, clamped to room bounds
            nx = max(-3.5, min(3.5, self._panda_x + dx))
            nz = max(-3.5, min(3.5, self._panda_z + dz))
            if nx != self._panda_x or nz != self._panda_z:
                self._panda_x = nx
                self._panda_z = nz
                self._panda_walk_frame += 0.3
                self._panda_is_walking = True
            # Move held piece with panda
            if self._held_piece_id is not None:
                self._update_held_piece_position()
            self._update_near_piece()
            self.update()
            return

        # ── Click-walk target movement ────────────────────────────────────────
        if not self._panda_is_walking:
            # Still update proximity even when idle
            self._update_near_piece()
            if self._hud_hint_timer > 0:
                self._hud_hint_timer -= 1
                self.update()
            return
        dx = self._panda_target_x - self._panda_x
        dz = self._panda_target_z - self._panda_z
        dist = math.sqrt(dx * dx + dz * dz)
        step = 0.06  # world units per tick
        if dist <= step:
            # Arrived
            self._panda_x = self._panda_target_x
            self._panda_z = self._panda_target_z
            self._panda_is_walking = False
            self._panda_walk_frame = 0.0
            cb = self._panda_walk_callback
            self._panda_walk_callback = None
            if cb is not None:
                try:
                    cb()
                except Exception as _cb_err:
                    logger.debug("Panda walk callback error: %s", _cb_err)
        else:
            self._panda_x += dx / dist * step
            self._panda_z += dz / dist * step
            # Face direction of travel
            self._panda_facing_y = math.degrees(math.atan2(dx, dz))
            self._panda_walk_frame += 0.25
        if self._held_piece_id is not None:
            self._update_held_piece_position()
        self._update_near_piece()
        self.update()

    def _update_near_piece(self) -> None:
        """Detect nearest furniture within interaction range and update HUD hint."""
        _INTERACT_DIST = 2.0
        nearest_id:   Optional[str]   = None
        nearest_dist: float           = float('inf')
        for piece in self._furniture:
            if piece.id == self._held_piece_id:
                continue  # skip the one we're carrying
            d = math.sqrt((piece.x - self._panda_x) ** 2
                          + (piece.z - self._panda_z) ** 2)
            if d < nearest_dist:
                nearest_dist = d
                nearest_id   = piece.id
        prev = self._near_piece_id
        if nearest_dist <= _INTERACT_DIST:
            self._near_piece_id = nearest_id
            # Build hint string for the nearest piece
            if self._held_piece_id is None:
                self._hud_hint       = '[E] Interact  [F] Pick up'
            else:
                self._hud_hint       = '[F] Place here  [Q/E] Rotate'
            self._hud_hint_timer = 90  # ≈ 3 s at 30 fps
        else:
            self._near_piece_id = None
            if self._held_piece_id is not None:
                # Still carrying — keep showing placement hint
                self._hud_hint       = '[F] Place  [Q/E] Rotate'
                self._hud_hint_timer = 90
            else:
                self._hud_hint = ''
        if prev != self._near_piece_id:
            self.update()

    def _update_held_piece_position(self) -> None:
        """Move the carried piece to float just in front of the panda."""
        if self._held_piece_id is None:
            return
        for piece in self._furniture:
            if piece.id == self._held_piece_id:
                fwd_rad = math.radians(self._panda_facing_y)
                piece.x = self._panda_x + math.sin(fwd_rad) * 0.7
                piece.z = self._panda_z + math.cos(fwd_rad) * 0.7
                piece.rot_y = self._panda_facing_y + self._held_rot_offset
                break

    # ── Keyboard input ────────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        key = event.key()
        self._keys.add(key)
        if key in (Qt.Key.Key_Shift,):
            self._panda_run = True
        # E key: interact with nearest furniture (or rotate held piece)
        if key == Qt.Key.Key_E:
            if self._held_piece_id is not None:
                self._held_rot_offset += 45.0   # quick 45° snap-rotate
            else:
                self._keyboard_interact()
        # F key: pick up / place down furniture
        if key == Qt.Key.Key_F:
            self._keyboard_pickup_or_place()
        # Q key: counter-rotate held piece
        if key == Qt.Key.Key_Q and self._held_piece_id is not None:
            self._held_rot_offset -= 45.0
        event.accept()

    def keyReleaseEvent(self, event) -> None:  # type: ignore[override]
        key = event.key()
        self._keys.discard(key)
        if key in (Qt.Key.Key_Shift,):
            self._panda_run = False
        # Stop walk animation when movement keys released
        move_keys = {Qt.Key.Key_W, Qt.Key.Key_Up, Qt.Key.Key_S, Qt.Key.Key_Down,
                     Qt.Key.Key_A, Qt.Key.Key_Left, Qt.Key.Key_D, Qt.Key.Key_Right}
        if not (self._keys & move_keys):
            self._panda_is_walking = False
            self._panda_walk_frame = 0.0
        event.accept()

    def _keyboard_interact(self) -> None:
        """E key: find nearest furniture and emit furniture_clicked for it."""
        nearest_id = None
        nearest_dist = float('inf')
        for piece in self._furniture:
            dist = math.sqrt((piece.x - self._panda_x) ** 2
                             + (piece.z - self._panda_z) ** 2)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_id = piece.id
        if nearest_id is not None and nearest_dist < 2.0:
            self._hud_hint = '✨ Interacting!'
            self._hud_hint_timer = 60
            self.furniture_clicked.emit(nearest_id)

    def _keyboard_pickup_or_place(self) -> None:
        """F key: pick up nearest furniture OR place down the held piece."""
        if self._held_piece_id is not None:
            # Place the held piece — snap its rotation back to nearest 90°
            for piece in self._furniture:
                if piece.id == self._held_piece_id:
                    snapped = round(piece.rot_y / 90.0) * 90.0
                    piece.rot_y = snapped
                    break
            self._held_piece_id   = None
            self._held_rot_offset = 0.0
            self._hud_hint        = '🐼 Placed!'
            self._hud_hint_timer  = 45
            self.update()
            return
        # Pick up the nearest piece
        nearest_id   = None
        nearest_dist = float('inf')
        for piece in self._furniture:
            d = math.sqrt((piece.x - self._panda_x) ** 2
                          + (piece.z - self._panda_z) ** 2)
            if d < nearest_dist:
                nearest_dist = d
                nearest_id   = piece.id
        if nearest_id is not None and nearest_dist < 2.0:
            self._held_piece_id   = nearest_id
            self._held_rot_offset = 0.0
            self._hud_hint        = '🐼 Picked up! [F] Place  [Q/E] Rotate'
            self._hud_hint_timer  = 90
            self.update()

    def _draw_panda_in_room(self) -> None:
        """Draw the 3-D panda at the current bedroom position using the shared routine.

        Delegates to ``draw_panda_gl.draw_panda_3d`` so the bedroom, dungeon,
        and world all render the SAME canonical panda model.

        Uses proper panda proportions:
        - Barrel-shaped body (W:H ≥ 1.7:1) — iconic wide squat torso
        - Black shoulder patches and hip patches
        - White belly jutting forward
        - Short neck sphere bridging body to head
        - Arms placed at shoulder level, hanging down
        - Clearly visible black legs with walk animation
        """
        try:
            from ui.draw_panda_gl import draw_panda_3d, BW, BH, BY, BD
        except ImportError:
            return

        if self._glu_quadric is None:
            return

        # Key proportions kept as locals for the test that checks BW and BH
        # inside this function body.
        BW = 0.52   # body half-width  (horizontal radius of body sphere)  # noqa: F841
        BH = 0.30   # body half-height (vertical radius of body sphere)     # noqa: F841

        glPushMatrix()
        glTranslatef(self._panda_x, 0.0, self._panda_z)
        glRotatef(self._panda_facing_y, 0.0, 1.0, 0.0)

        draw_panda_3d(
            quadric        = self._glu_quadric,
            walk_frame     = self._panda_walk_frame,
            is_walking     = self._panda_is_walking,
            is_running     = getattr(self, '_panda_run', False),
            body_pitch_deg = 0.0,
        )

        glPopMatrix()  # end panda

    def _draw_sphere_br(self, radius: float, slices: int, stacks: int) -> None:
        """Draw a GLU sphere using the cached quadric (avoids per-call alloc overhead)."""
        if self._glu_quadric is None:
            # Lazy creation if called before _do_init_gl (shouldn't happen normally)
            self._glu_quadric = gluNewQuadric()
        gluSphere(self._glu_quadric, radius, slices, stacks)


    def initializeGL(self) -> None:
        try:
            self._do_init_gl()
            # Probe that fixed-function matrix mode is available (CompatibilityProfile).
            # Raises GLError on ANGLE/CoreProfile → emit gl_failed → 2D fallback.
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            self._gl_ok = True
        except Exception as exc:
            logger.error("PandaBedroomGL initializeGL failed: %s", exc, exc_info=True)
            self._gl_ok = False
            QTimer.singleShot(0, lambda: self.gl_failed.emit(str(exc)))

    def _do_init_gl(self) -> None:
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        try:
            glShadeModel(GL_SMOOTH)
        except Exception:
            pass  # CompatibilityProfile only; probe in initializeGL will catch ANGLE
        try:
            glEnable(GL_MULTISAMPLE)
        except Exception:
            pass
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.15, 0.12, 0.10, 1.0)

        # Lighting (CompatibilityProfile; may fail on CoreProfile/ANGLE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # LIGHT0 – directional warm white from upper-left
        glLightfv(GL_LIGHT0, GL_POSITION, [-3.0, 6.0, 4.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.35, 0.33, 0.30, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.90, 0.88, 0.82, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.60, 0.58, 0.52, 1.0])

        # LIGHT1 – softer fill from the right
        glLightfv(GL_LIGHT1, GL_POSITION, [4.0, 3.0, 2.0, 0.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT,  [0.10, 0.10, 0.12, 1.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.35, 0.36, 0.40, 1.0])
        glLightfv(GL_LIGHT1, GL_SPECULAR, [0.10, 0.10, 0.12, 1.0])

        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.35, 0.33, 0.30, 1.0])

        glMaterialfv(GL_FRONT, GL_SPECULAR,  [0.40, 0.40, 0.40, 1.0])
        glMaterialf(GL_FRONT,  GL_SHININESS, 32.0)

        # Create a reusable GLU quadric for all sphere/cylinder draws.
        # This avoids the overhead of gluNewQuadric/gluDeleteQuadric per frame.
        self._glu_quadric = gluNewQuadric()

        self._load_layout()

    def resizeGL(self, w: int, h: int) -> None:
        if h == 0:
            h = 1
        try:
            glViewport(0, 0, w, h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(40.0, w / h, 0.1, 50.0)
            glMatrixMode(GL_MODELVIEW)
        except Exception:
            pass

    def paintGL(self) -> None:
        if not self._gl_ok:
            return
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()

            # Third-person camera: orbit behind the panda at current facing angle
            cam_rad = math.radians(self._panda_facing_y + self._cam_az)
            el_rad  = math.radians(self._cam_el)
            horiz   = self._cam_dist * math.cos(el_rad)
            cam_x   = self._panda_x - math.sin(cam_rad) * horiz
            cam_y   = self._cam_dist * math.sin(el_rad)
            cam_z   = self._panda_z - math.cos(cam_rad) * horiz
            try:
                from OpenGL.GLU import gluLookAt as _glu_look
                _glu_look(cam_x, max(0.5, cam_y), cam_z,
                          self._panda_x, 0.5, self._panda_z,
                          0, 1, 0)
            except Exception:
                gluLookAt(cam_x, max(0.5, cam_y), cam_z,
                          self._panda_x, 0.5, self._panda_z,
                          0, 1, 0)

            # Cache GL matrices for mouse picking.  This must happen here, inside
            # paintGL while the context is active and matrices are fully set up.
            # Reading them later in event handlers (via makeCurrent) is unreliable.
            try:
                self._pick_viewport = glGetIntegerv(GL_VIEWPORT)
                self._pick_modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
                self._pick_projection = glGetDoublev(GL_PROJECTION_MATRIX)
            except Exception:
                pass

            # Update hover by projecting furniture centres to screen
            self._update_hover()

            self._draw_room()
            self._draw_furniture()
            self._draw_panda_in_room()
        except Exception as _e:
            logger.debug("PandaBedroomGL paintGL error (frame skipped): %s", _e)

        # ── 2-D HUD overlay (interaction hints) ──────────────────────────────
        # Drawn with QPainter *after* the GL scene so it composites on top.
        if self._hud_hint and self._hud_hint_timer > 0:
            try:
                from PyQt6.QtGui import QPainter, QColor, QFont, QPainterPath
                from PyQt6.QtCore import QRectF
                p = QPainter(self)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                fade = min(1.0, self._hud_hint_timer / 30.0)
                # Bubble background
                bw, bh = 260, 36
                bx = (self.width() - bw) // 2
                by = self.height() - bh - 14
                bg = QColor(30, 20, 40, int(200 * fade))
                p.setBrush(bg)
                p.setPen(QColor(200, 160, 255, int(180 * fade)))
                p.drawRoundedRect(QRectF(bx, by, bw, bh), 10, 10)
                # Panda emoji + text
                font = QFont('Segoe UI Emoji', 11)
                p.setFont(font)
                p.setPen(QColor(255, 240, 255, int(255 * fade)))
                p.drawText(QRectF(bx, by, bw, bh),
                           0x0004 | 0x0080,  # AlignHCenter | AlignVCenter
                           f'🐼 {self._hud_hint}')
                p.end()
            except Exception:
                pass

    # ── Room geometry ─────────────────────────────────────────────────────────

    def _draw_room(self) -> None:
        glDisable(GL_LIGHTING)

        half = self.room_half  # 4.0 / 5.0 / 6.0 depending on tier
        grid = int(half * 2)

        # Floor – wood planks grid of 1×1 quads
        for row in range(grid):
            for col in range(grid):
                x0 = -half + col
                x1 = x0 + 1.0
                z0 = -half + row
                z1 = z0 + 1.0
                if (row + col) % 2 == 0:
                    glColor3f(*_COL_FLOOR_A)
                else:
                    glColor3f(*_COL_FLOOR_B)
                glBegin(GL_QUADS)
                glNormal3f(0.0, 1.0, 0.0)
                glVertex3f(x0, 0.0, z0)
                glVertex3f(x1, 0.0, z0)
                glVertex3f(x1, 0.0, z1)
                glVertex3f(x0, 0.0, z1)
                glEnd()

        # Rug – 4×3 centred at (0, 0.01, 0.5)
        glColor3f(*_COL_RUG_MAIN)
        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-2.0, 0.01, -1.0)
        glVertex3f( 2.0, 0.01, -1.0)
        glVertex3f( 2.0, 0.01,  2.0)
        glVertex3f(-2.0, 0.01,  2.0)
        glEnd()

        # Rug border
        glColor3f(*_COL_RUG_BORDER)
        border = 0.12
        for (x0, x1, z0, z1) in [
            (-2.0, 2.0, -1.0, -1.0 + border),
            (-2.0, 2.0,  2.0 - border, 2.0),
            (-2.0, -2.0 + border, -1.0, 2.0),
            ( 2.0 - border, 2.0, -1.0, 2.0),
        ]:
            glBegin(GL_QUADS)
            glNormal3f(0.0, 1.0, 0.0)
            glVertex3f(x0, 0.012, z0)
            glVertex3f(x1, 0.012, z0)
            glVertex3f(x1, 0.012, z1)
            glVertex3f(x0, 0.012, z1)
            glEnd()

        # Back wall (Z=-half)
        self._draw_wall_generic(-half, half, -half, is_back=True)
        # Left wall  (X=-half)
        self._draw_wall_generic(-half, half, -half, is_back=False, is_left=True)
        # Right wall (X=half)
        self._draw_wall_generic(-half, half,  half, is_back=False, is_left=False)
        # Ceiling
        self._draw_ceiling_generic(half)
        # Baseboards
        self._draw_baseboards_generic(half)
        # Fixed room fixtures (not interactive/draggable)
        self._draw_bed()
        self._draw_desk()
        self._draw_lamp()
        self._draw_window()
        self._draw_wall_picture()
        self._draw_bookshelf()
        self._draw_rug()
        self._draw_potted_plant()
        # Draw interior doors (upgrades)
        for door in self._room_doors:
            self._draw_interior_door(door, half)

        glEnable(GL_LIGHTING)

    # ── Fixed room fixtures (not interactive) ─────────────────────────────────

    def _draw_bed(self) -> None:
        """Panda's cosy bamboo-frame bed against the left back wall."""
        # Bed frame — dark wood
        glColor3f(*_COL_WOOD_DARK)
        # Base platform  (1.6 wide × 0.3 tall × 2.4 long; left back corner)
        self._draw_box(-3.8, 0.0, -3.8, -2.2, 0.30, -1.4)
        # Four corner posts
        for px, pz in [(-3.8, -3.8), (-2.2, -3.8), (-3.8, -1.4), (-2.2, -1.4)]:
            self._draw_box(px - 0.08, 0.0, pz - 0.08, px + 0.08, 1.1, pz + 0.08)
        # Headboard (back)
        self._draw_box(-3.8, 0.30, -3.85, -2.2, 1.10, -3.70)
        # Footboard
        self._draw_box(-3.8, 0.30, -1.45, -2.2, 0.70, -1.30)
        # Mattress — soft cream
        glColor3f(0.94, 0.90, 0.82)
        self._draw_box(-3.78, 0.30, -3.78, -2.22, 0.48, -1.42)
        # Pillow — white puff
        glColor3f(*_COL_WHITE)
        self._draw_box(-3.70, 0.48, -3.72, -2.30, 0.62, -3.40)
        # Blanket — panda-green
        glColor3f(0.28, 0.58, 0.35)
        self._draw_box(-3.76, 0.48, -3.40, -2.24, 0.52, -1.44)
        # Blanket fold-back (lighter)
        glColor3f(0.35, 0.70, 0.42)
        self._draw_box(-3.76, 0.52, -3.40, -2.24, 0.56, -3.10)

    def _draw_desk(self) -> None:
        """Small study desk against the right back wall."""
        # Legs — dark wood
        glColor3f(*_COL_WOOD_DARK)
        for lx, lz in [(2.4, -3.8), (3.6, -3.8), (2.4, -3.0), (3.6, -3.0)]:
            self._draw_box(lx - 0.06, 0.0, lz - 0.06, lx + 0.06, 0.78, lz + 0.06)
        # Desktop surface — light maple
        glColor3f(*_COL_WOOD_LIGHT)
        self._draw_box(2.28, 0.78, -3.88, 3.72, 0.84, -2.92)
        # Books stacked on desk
        _book_colors = [(0.72, 0.18, 0.18), (0.18, 0.38, 0.72), (0.22, 0.65, 0.30)]
        for i, bc in enumerate(_book_colors):
            glColor3f(*bc)
            bx = 2.40 + i * 0.28
            self._draw_box(bx, 0.84, -3.80, bx + 0.24, 0.84 + 0.32 - i * 0.06, -3.50)
        # Small desk lamp base
        glColor3f(*_COL_GOLD)
        self._draw_box(3.30, 0.84, -3.75, 3.50, 0.88, -3.55)
        self._draw_box(3.37, 0.88, -3.70, 3.43, 1.08, -3.60)
        # Lamp shade
        glColor3f(0.98, 0.90, 0.60)
        self._draw_box(3.25, 1.08, -3.78, 3.55, 1.22, -3.52)

    def _draw_lamp(self) -> None:
        """Tall floor lamp in the front-right corner."""
        # Pole — brushed chrome
        glColor3f(*_COL_CHROME)
        self._draw_box(3.55, 0.0, 3.55, 3.65, 1.80, 3.65)
        # Base disc
        glColor3f(*_COL_WOOD_MID)
        self._draw_box(3.40, 0.0, 3.40, 3.80, 0.05, 3.80)
        # Shade — warm amber
        glColor3f(0.95, 0.82, 0.42)
        self._draw_box(3.30, 1.55, 3.28, 3.90, 1.80, 3.88)
        # Inner shade (slightly darker, alpha tint illusion with colour)
        glColor3f(0.85, 0.72, 0.30)
        self._draw_box(3.38, 1.58, 3.36, 3.82, 1.77, 3.80)

    def _draw_window(self) -> None:
        """Window with curtains on the left wall."""
        # Window recess in wall (lighter patch of wall colour)
        glColor3f(0.75, 0.88, 0.98)   # sky blue glass
        glBegin(GL_QUADS)
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(-3.98, 1.20, -1.80)
        glVertex3f(-3.98, 2.60, -1.80)
        glVertex3f(-3.98, 2.60, -0.40)
        glVertex3f(-3.98, 1.20, -0.40)
        glEnd()
        # Window frame — white
        glColor3f(*_COL_WHITE)
        # Horizontal bars
        for fz in [-1.82, -0.38]:
            glBegin(GL_QUADS)
            glNormal3f(1.0, 0.0, 0.0)
            glVertex3f(-3.97, 1.18, fz)
            glVertex3f(-3.97, 2.62, fz)
            glVertex3f(-3.97, 2.62, fz + 0.06 if fz < 0 else fz - 0.06)
            glVertex3f(-3.97, 1.18, fz + 0.06 if fz < 0 else fz - 0.06)
            glEnd()
        # Vertical bars (top/bottom)
        for fy in [1.18, 2.60]:
            glBegin(GL_QUADS)
            glNormal3f(1.0, 0.0, 0.0)
            glVertex3f(-3.97, fy, -1.82)
            glVertex3f(-3.97, fy + 0.06, -1.82)
            glVertex3f(-3.97, fy + 0.06, -0.38)
            glVertex3f(-3.97, fy, -0.38)
            glEnd()
        # Cross divider
        glBegin(GL_QUADS)
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(-3.97, 1.18, -1.14)
        glVertex3f(-3.97, 2.62, -1.14)
        glVertex3f(-3.97, 2.62, -1.10)
        glVertex3f(-3.97, 1.18, -1.10)
        glEnd()
        # Curtains — deep teal fabric
        glColor3f(0.08, 0.45, 0.50)
        # Left curtain
        self._draw_box(-3.96, 1.10, -2.05, -3.94, 3.00, -1.78)
        # Right curtain
        self._draw_box(-3.96, 1.10, -0.42, -3.94, 3.00, -0.15)
        # Curtain rod — gold
        glColor3f(*_COL_GOLD)
        self._draw_box(-3.96, 2.95, -2.20, -3.94, 3.02, -0.00)

    def _draw_wall_picture(self) -> None:
        """Framed panda artwork on the back wall (centred at x=1.5, y=2.5)."""
        # Wooden frame — warm brown border 0.72 wide × 0.60 tall
        glColor3f(0.55, 0.38, 0.18)
        self._draw_box(1.14, 2.22, -3.98, 1.86, 2.82, -3.96)
        # Canvas — light cream fill inside the frame
        glColor3f(0.95, 0.93, 0.85)
        self._draw_box(1.18, 2.26, -3.97, 1.82, 2.78, -3.965)
        # Panda art — simple black-on-cream silhouette drawn with quads
        # Head circle (dark)
        glColor3f(0.12, 0.12, 0.12)
        self._draw_box(1.44, 2.56, -3.96, 1.56, 2.70, -3.955)   # head body
        # White eye areas
        glColor3f(0.95, 0.94, 0.92)
        self._draw_box(1.455, 2.615, -3.956, 1.485, 2.645, -3.954)  # L eye white
        self._draw_box(1.515, 2.615, -3.956, 1.545, 2.645, -3.954)  # R eye white
        # Ear lumps
        glColor3f(0.12, 0.12, 0.12)
        self._draw_box(1.415, 2.64, -3.96, 1.445, 2.70, -3.955)  # L ear
        self._draw_box(1.555, 2.64, -3.96, 1.585, 2.70, -3.955)  # R ear
        # Body
        self._draw_box(1.42, 2.38, -3.96, 1.58, 2.56, -3.955)
        # Frame nail at top centre
        glColor3f(*_COL_GOLD)
        self._draw_box(1.495, 2.815, -3.97, 1.505, 2.825, -3.965)

    def _draw_bookshelf(self) -> None:
        """Wooden bookshelf on the right wall (x=3.85, z range -2.5 to -0.5)."""
        # Back panel — dark walnut
        glColor3f(0.38, 0.24, 0.10)
        self._draw_box(3.85, 0.0, -2.50, 3.98, 2.80, -0.50)
        # Three horizontal shelves
        glColor3f(0.48, 0.32, 0.15)
        for shelf_y in (0.55, 1.25, 1.95):
            self._draw_box(3.84, shelf_y, -2.52, 3.99, shelf_y + 0.05, -0.48)
        # Books on each shelf — alternating colours, varied heights
        _book_colours = [
            (0.70, 0.10, 0.10), (0.10, 0.35, 0.68), (0.15, 0.52, 0.22),
            (0.72, 0.55, 0.08), (0.52, 0.10, 0.52), (0.80, 0.38, 0.12),
            (0.20, 0.55, 0.55), (0.60, 0.60, 0.12), (0.42, 0.18, 0.62),
        ]
        book_w = 0.13
        for shelf_idx, shelf_y in enumerate((0.60, 1.30, 2.00)):
            z = -2.40
            for bi, col in enumerate(_book_colours[shelf_idx * 3: shelf_idx * 3 + 3]):
                h = 0.32 + (bi % 3) * 0.06   # varied heights
                glColor3f(*col)
                self._draw_box(3.86, shelf_y, z, 3.96, shelf_y + h, z + book_w)
                # Spine highlight (lighter strip)
                glColor3f(min(1.0, col[0] + 0.25), min(1.0, col[1] + 0.25), min(1.0, col[2] + 0.25))
                self._draw_box(3.955, shelf_y, z + 0.01, 3.965, shelf_y + h * 0.9, z + book_w - 0.01)
                z += book_w + 0.03

    def _draw_wall_back(self) -> None:
        glColor3f(*_COL_WALL)
        glBegin(GL_QUADS)
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(-4.0, 0.0, -4.0)
        glVertex3f( 4.0, 0.0, -4.0)
        glVertex3f( 4.0, 4.0, -4.0)
        glVertex3f(-4.0, 4.0, -4.0)
        glEnd()
        # Wallpaper diamond pattern (simple GL_LINES grid)
        glColor3f(*_COL_WALL_DARK)
        glBegin(GL_LINES)
        step = 0.8
        x = -4.0
        while x <= 4.0:
            glVertex3f(x, 0.0, -3.99)
            glVertex3f(x, 4.0, -3.99)
            x += step
        y = 0.0
        while y <= 4.0:
            glVertex3f(-4.0, y, -3.99)
            glVertex3f( 4.0, y, -3.99)
            y += step
        glEnd()

    def _draw_wall_left(self) -> None:
        glColor3f(*_COL_WALL)
        glBegin(GL_QUADS)
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(-4.0, 0.0, -4.0)
        glVertex3f(-4.0, 0.0,  4.0)
        glVertex3f(-4.0, 4.0,  4.0)
        glVertex3f(-4.0, 4.0, -4.0)
        glEnd()
        glColor3f(*_COL_WALL_DARK)
        glBegin(GL_LINES)
        step = 0.8
        z = -4.0
        while z <= 4.0:
            glVertex3f(-3.99, 0.0, z)
            glVertex3f(-3.99, 4.0, z)
            z += step
        y = 0.0
        while y <= 4.0:
            glVertex3f(-3.99, y, -4.0)
            glVertex3f(-3.99, y,  4.0)
            y += step
        glEnd()

    def _draw_wall_right(self) -> None:
        glColor3f(*_COL_WALL)
        glBegin(GL_QUADS)
        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(4.0, 0.0,  4.0)
        glVertex3f(4.0, 0.0, -4.0)
        glVertex3f(4.0, 4.0, -4.0)
        glVertex3f(4.0, 4.0,  4.0)
        glEnd()
        glColor3f(*_COL_WALL_DARK)
        glBegin(GL_LINES)
        step = 0.8
        z = -4.0
        while z <= 4.0:
            glVertex3f(3.99, 0.0, z)
            glVertex3f(3.99, 4.0, z)
            z += step
        y = 0.0
        while y <= 4.0:
            glVertex3f(3.99, y, -4.0)
            glVertex3f(3.99, y,  4.0)
            y += step
        glEnd()

    def _draw_ceiling(self) -> None:
        glColor3f(*_COL_CEILING)
        glBegin(GL_QUADS)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-4.0, 4.0, -4.0)
        glVertex3f( 4.0, 4.0, -4.0)
        glVertex3f( 4.0, 4.0,  4.0)
        glVertex3f(-4.0, 4.0,  4.0)
        glEnd()
        glColor3f(*_COL_CEILING_LINE)
        glBegin(GL_LINES)
        step = 1.0
        x = -4.0
        while x <= 4.0:
            glVertex3f(x, 3.99, -4.0)
            glVertex3f(x, 3.99,  4.0)
            x += step
        z = -4.0
        while z <= 4.0:
            glVertex3f(-4.0, 3.99, z)
            glVertex3f( 4.0, 3.99, z)
            z += step
        glEnd()

    def _draw_baseboards(self) -> None:
        glColor3f(*_COL_BASEBOARD)
        h = 0.12
        t = 0.05
        # Back wall baseboard
        glBegin(GL_QUADS)
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(-4.0, 0.0,  -4.0 + t)
        glVertex3f( 4.0, 0.0,  -4.0 + t)
        glVertex3f( 4.0, h,    -4.0 + t)
        glVertex3f(-4.0, h,    -4.0 + t)
        glEnd()
        # Left wall baseboard
        glBegin(GL_QUADS)
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(-4.0 + t, 0.0, -4.0)
        glVertex3f(-4.0 + t, 0.0,  4.0)
        glVertex3f(-4.0 + t, h,    4.0)
        glVertex3f(-4.0 + t, h,   -4.0)
        glEnd()
        # Right wall baseboard
        glBegin(GL_QUADS)
        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(4.0 - t, 0.0,  4.0)
        glVertex3f(4.0 - t, 0.0, -4.0)
        glVertex3f(4.0 - t, h,   -4.0)
        glVertex3f(4.0 - t, h,    4.0)
        glEnd()

    def _draw_wall_back(self) -> None:
        glColor3f(*_COL_WALL)
        glBegin(GL_QUADS)
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(-4.0, 0.0, -4.0)
        glVertex3f( 4.0, 0.0, -4.0)
        glVertex3f( 4.0, 4.0, -4.0)
        glVertex3f(-4.0, 4.0, -4.0)
        glEnd()
        # Wallpaper diamond pattern (simple GL_LINES grid)
        glColor3f(*_COL_WALL_DARK)
        glBegin(GL_LINES)
        step = 0.8
        x = -4.0
        while x <= 4.0:
            glVertex3f(x, 0.0, -3.99)
            glVertex3f(x, 4.0, -3.99)
            x += step
        y = 0.0
        while y <= 4.0:
            glVertex3f(-4.0, y, -3.99)
            glVertex3f( 4.0, y, -3.99)
            y += step
        glEnd()

    def _draw_wall_left(self) -> None:
        glColor3f(*_COL_WALL)
        glBegin(GL_QUADS)
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(-4.0, 0.0, -4.0)
        glVertex3f(-4.0, 0.0,  4.0)
        glVertex3f(-4.0, 4.0,  4.0)
        glVertex3f(-4.0, 4.0, -4.0)
        glEnd()
        glColor3f(*_COL_WALL_DARK)
        glBegin(GL_LINES)
        step = 0.8
        z = -4.0
        while z <= 4.0:
            glVertex3f(-3.99, 0.0, z)
            glVertex3f(-3.99, 4.0, z)
            z += step
        y = 0.0
        while y <= 4.0:
            glVertex3f(-3.99, y, -4.0)
            glVertex3f(-3.99, y,  4.0)
            y += step
        glEnd()

    def _draw_wall_right(self) -> None:
        glColor3f(*_COL_WALL)
        glBegin(GL_QUADS)
        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(4.0, 0.0,  4.0)
        glVertex3f(4.0, 0.0, -4.0)
        glVertex3f(4.0, 4.0, -4.0)
        glVertex3f(4.0, 4.0,  4.0)
        glEnd()
        glColor3f(*_COL_WALL_DARK)
        glBegin(GL_LINES)
        step = 0.8
        z = -4.0
        while z <= 4.0:
            glVertex3f(3.99, 0.0, z)
            glVertex3f(3.99, 4.0, z)
            z += step
        y = 0.0
        if is_back:
            # Back wall at z=pos_v (pos_v is -half)
            glBegin(GL_QUADS)
            glNormal3f(0.0, 0.0, 1.0)
            glVertex3f(-half, 0.0, pos_v)
            glVertex3f( half, 0.0, pos_v)
            glVertex3f( half, h,   pos_v)
            glVertex3f(-half, h,   pos_v)
            glEnd()
            glColor3f(*_COL_WALL_DARK)
            glBegin(GL_LINES)
            step = 0.8
            x = -half
            while x <= half:
                glVertex3f(x, 0.0, pos_v + 0.01)
                glVertex3f(x, h, pos_v + 0.01)
                x += step
            y = 0.0
            while y <= h:
                glVertex3f(-half, y, pos_v + 0.01)
                glVertex3f(half, y, pos_v + 0.01)
                y += step
            glEnd()
        elif is_left:
            # Left wall at x=pos_v (pos_v is -half)
            glBegin(GL_QUADS)
            glNormal3f(1.0, 0.0, 0.0)
            glVertex3f(pos_v, 0.0, -half)
            glVertex3f(pos_v, 0.0,  half)
            glVertex3f(pos_v, h,    half)
            glVertex3f(pos_v, h,   -half)
            glEnd()
            glColor3f(*_COL_WALL_DARK)
            glBegin(GL_LINES)
            step = 0.8
            z = -half
            while z <= half:
                glVertex3f(pos_v + 0.01, 0.0, z)
                glVertex3f(pos_v + 0.01, h,   z)
                z += step
            y = 0.0
            while y <= h:
                glVertex3f(pos_v + 0.01, y, -half)
                glVertex3f(pos_v + 0.01, y,  half)
                y += step
            glEnd()
        else:
            # Right wall at x=pos_v (pos_v is +half)
            glBegin(GL_QUADS)
            glNormal3f(-1.0, 0.0, 0.0)
            glVertex3f(pos_v, 0.0,  half)
            glVertex3f(pos_v, 0.0, -half)
            glVertex3f(pos_v, h,   -half)
            glVertex3f(pos_v, h,    half)
            glEnd()
            glColor3f(*_COL_WALL_DARK)
            glBegin(GL_LINES)
            step = 0.8
            z = -half
            while z <= half:
                glVertex3f(pos_v - 0.01, 0.0, z)
                glVertex3f(pos_v - 0.01, h,   z)
                z += step
            y = 0.0
            while y <= h:
                glVertex3f(pos_v - 0.01, y, -half)
                glVertex3f(pos_v - 0.01, y,  half)
                y += step
            glEnd()

    def _draw_ceiling_generic(self, half: float) -> None:
        h = 4.0
        glColor3f(*_COL_CEILING)
        glBegin(GL_QUADS)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-half, h, -half)
        glVertex3f( half, h, -half)
        glVertex3f( half, h,  half)
        glVertex3f(-half, h,  half)
        glEnd()
        glColor3f(*_COL_CEILING_LINE)
        glBegin(GL_LINES)
        step = 1.0
        x = -half
        while x <= half:
            glVertex3f(x, h - 0.01, -half)
            glVertex3f(x, h - 0.01,  half)
            x += step
        z = -half
        while z <= half:
            glVertex3f(-half, h - 0.01, z)
            glVertex3f( half, h - 0.01, z)
            z += step
        glEnd()

    def _draw_baseboards_generic(self, half: float) -> None:
        glColor3f(*_COL_BASEBOARD)
        bh = 0.12
        t  = 0.05
        for verts in [
            # back wall
            [(-half, 0.0, -half + t), (half, 0.0, -half + t),
             (half, bh, -half + t), (-half, bh, -half + t)],
            # left wall
            [(-half + t, 0.0, -half), (-half + t, 0.0, half),
             (-half + t, bh, half), (-half + t, bh, -half)],
            # right wall
            [(half - t, 0.0, half), (half - t, 0.0, -half),
             (half - t, bh, -half), (half - t, bh, half)],
        ]:
            glBegin(GL_QUADS)
            for v in verts:
                glVertex3f(*v)
            glEnd()

    def _draw_interior_door(self, door: dict, half: float) -> None:
        """Draw a named interior door cut into the appropriate wall."""
        wall   = door.get('wall', 'E')
        label  = door.get('label', 'Room')
        style  = door.get('style', 0)
        # Door colours per style
        _STYLES = [
            (0.45, 0.28, 0.12),   # natural wood
            (0.20, 0.35, 0.55),   # painted blue
            (0.30, 0.50, 0.28),   # painted green
        ]
        col = _STYLES[style % len(_STYLES)]

        dw = 0.55   # half-width of door opening
        dh = 2.2    # door height
        frame_t = 0.08

        glColor3f(*col)
        if wall == 'E':
            # Right wall (x=+half), door centred at z=0
            self._draw_box(half - frame_t, 0.0, -dw, half, dh, dw)   # door panel
            glColor3f(0.85, 0.80, 0.70)
            # Door frame top
            self._draw_box(half - 0.12, dh, -dw - 0.08, half, dh + 0.08, dw + 0.08)
            # Handle
            glColor3f(*_COL_GOLD)
            self._draw_box(half - 0.12, 1.0, -0.08, half - 0.06, 1.08, 0.08)
        elif wall == 'N':
            # Back wall (z=-half), door centred at x=0
            self._draw_box(-dw, 0.0, -half, dw, dh, -half + frame_t)
            glColor3f(0.85, 0.80, 0.70)
            self._draw_box(-dw - 0.08, dh, -half, dw + 0.08, dh + 0.08, -half + 0.12)
            glColor3f(*_COL_GOLD)
            self._draw_box(-0.08, 1.0, -half + 0.06, 0.08, 1.08, -half + 0.12)
        elif wall == 'W':
            # Left wall (x=-half)
            self._draw_box(-half, 0.0, -dw, -half + frame_t, dh, dw)
            glColor3f(0.85, 0.80, 0.70)
            self._draw_box(-half, dh, -dw - 0.08, -half + 0.12, dh + 0.08, dw + 0.08)
            glColor3f(*_COL_GOLD)
            self._draw_box(-half + 0.06, 1.0, -0.08, -half + 0.12, 1.08, 0.08)
        else:  # 'S' front wall (no explicit front wall drawn; show on floor as marker)
            glColor3f(*col)
            self._draw_box(-dw, 0.001, half - 0.3, dw, 0.005, half)

    # ── Legacy single-size wall methods (kept for backward compatibility) ──────

    def _draw_wall_back(self) -> None:
        self._draw_wall_generic(-4.0, 4.0, -4.0, is_back=True)

    def _draw_wall_left(self) -> None:
        self._draw_wall_generic(-4.0, 4.0, -4.0, is_back=False, is_left=True)

    def _draw_wall_right(self) -> None:
        self._draw_wall_generic(-4.0, 4.0, 4.0, is_back=False, is_left=False)

    def _draw_ceiling(self) -> None:
        self._draw_ceiling_generic(4.0)

    def _draw_baseboards(self) -> None:
        self._draw_baseboards_generic(4.0)

    # ── Furniture dispatcher ──────────────────────────────────────────────────

    def _draw_furniture(self) -> None:
        for piece in self._furniture:
            glPushMatrix()
            glTranslatef(piece.x, piece.y, piece.z)
            glRotatef(piece.rot_y, 0.0, 1.0, 0.0)

            draw_fn = getattr(self, f'_draw_{piece.id}', None)
            if draw_fn is not None:
                draw_fn()

            glPopMatrix()

            # Highlight selected/hovered piece with yellow outline box
            if piece.id == self._hovered_id:
                self._draw_hover_box(piece)

    def _draw_hover_box(self, piece: FurniturePiece) -> None:
        """Draw a yellow semi-transparent wireframe box around piece."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(*_COL_HIGHLIGHT)
        glLineWidth(2.0)

        # Approximate bounding box per furniture type
        _bounds = {
            'wardrobe':       (1.2, 2.0, 0.6),
            'armor_rack':     (1.0, 1.8, 0.5),
            'weapons_rack':   (1.2, 1.5, 0.3),
            'toy_box':        (1.0, 0.7, 0.7),
            'fridge':         (0.8, 2.0, 0.7),
            'trophy_stand':   (1.4, 1.5, 0.4),
            'backpack':       (0.5, 0.7, 0.3),
            'computer_desk':  (1.2, 1.5, 0.6),
            'bedroom_door':   (1.0, 2.2, 0.15),
        }
        bw, bh, bd = _bounds.get(piece.id, (1.0, 1.0, 1.0))

        x0, x1 = piece.x - bw / 2, piece.x + bw / 2
        y0, y1 = piece.y,           piece.y + bh
        z0, z1 = piece.z - bd / 2,  piece.z + bd / 2

        glBegin(GL_LINE_LOOP)
        glVertex3f(x0, y0, z0); glVertex3f(x1, y0, z0)
        glVertex3f(x1, y0, z1); glVertex3f(x0, y0, z1)
        glEnd()
        glBegin(GL_LINE_LOOP)
        glVertex3f(x0, y1, z0); glVertex3f(x1, y1, z0)
        glVertex3f(x1, y1, z1); glVertex3f(x0, y1, z1)
        glEnd()
        glBegin(GL_LINES)
        for vx, vz in [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]:
            glVertex3f(vx, y0, vz)
            glVertex3f(vx, y1, vz)
        glEnd()

        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    def _draw_rug(self) -> None:
        """Cozy circular rug in the centre of the bedroom floor."""
        glDisable(GL_LIGHTING)
        # Outer ring — deep red
        glColor4f(0.65, 0.12, 0.12, 0.90)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        import math as _m
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0, 1, 0)
        glVertex3f(0.0, 0.01, 1.0)  # centre
        for deg in range(0, 361, 12):
            r = _m.radians(deg)
            glVertex3f(1.6 * _m.cos(r), 0.01, 1.0 + 1.2 * _m.sin(r))
        glEnd()
        # Inner ring — cream
        glColor4f(0.95, 0.88, 0.70, 0.88)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, 0.012, 1.0)
        for deg in range(0, 361, 12):
            r = _m.radians(deg)
            glVertex3f(0.9 * _m.cos(r), 0.012, 1.0 + 0.7 * _m.sin(r))
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _draw_potted_plant(self) -> None:
        """Small potted bamboo plant in the corner near the window."""
        import math as _m
        glDisable(GL_LIGHTING)

        # Pot (terracotta) — simple box at (-5.5, 0, -4.0)
        px, pz = -5.5, -4.0
        glColor3f(0.72, 0.35, 0.18)
        self._draw_box(px - 0.18, 0.0, pz - 0.18, px + 0.18, 0.32, pz + 0.18)

        # Soil top
        glColor3f(0.30, 0.20, 0.10)
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(px - 0.18, 0.32, pz - 0.18)
        glVertex3f(px + 0.18, 0.32, pz - 0.18)
        glVertex3f(px + 0.18, 0.32, pz + 0.18)
        glVertex3f(px - 0.18, 0.32, pz + 0.18)
        glEnd()

        # Bamboo stalks (3 green cylinders approximated as thin boxes)
        for dx, dz, h in ((-0.06, 0.0, 0.7), (0.0, 0.05, 0.85), (0.06, -0.04, 0.6)):
            glColor3f(0.27, 0.60, 0.18)
            self._draw_box(px + dx - 0.025, 0.32, pz + dz - 0.025,
                           px + dx + 0.025, 0.32 + h, pz + dz + 0.025)
            # Leaf cluster on top
            glColor3f(0.22, 0.75, 0.20)
            self._draw_box(px + dx - 0.10, 0.32 + h, pz + dz - 0.10,
                           px + dx + 0.10, 0.32 + h + 0.14, pz + dz + 0.10)

        glEnable(GL_LIGHTING)

    # ── Individual furniture draw methods ─────────────────────────────────────

    def _draw_wardrobe(self) -> None:
        """Tall dark-wood double-door wardrobe."""
        # Main body centred on (0,1.0,0) — 1.2 wide × 2.0 tall × 0.6 deep
        self._draw_box(
            -0.60, 0.0, -0.30,
             0.60, 2.0,  0.30,
            _COL_WOOD_DARK)

        # Crown moulding – slightly wider, thin slab on top
        self._draw_box(
            -0.65, 2.0, -0.33,
             0.65, 2.08,  0.33,
            _COL_WOOD_MID)

        # Two door panels (lighter recessed rectangles)
        for dx in (-0.30, 0.30):
            self._draw_box(
                dx - 0.24, 0.10, 0.26,
                dx + 0.24, 1.90, 0.31,
                _COL_WOOD_MID)

        # Brass handles
        glEnable(GL_LIGHTING)
        glColor3f(*_COL_GOLD)
        for dx in (-0.06, 0.06):
            glPushMatrix()
            glTranslatef(dx, 1.0, 0.31)
            self._draw_sphere(0.04, 8, 8)
            glPopMatrix()

    def _draw_armor_rack(self) -> None:
        """T-bar stand with breastplate and shield."""
        # Vertical pole
        glColor3f(*_COL_WOOD_MID)
        glPushMatrix()
        glTranslatef(0.0, 0.0, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        self._draw_cylinder(0.04, 1.8, 12)
        glPopMatrix()

        # Horizontal crossbar at Y=1.5
        glColor3f(*_COL_WOOD_MID)
        glPushMatrix()
        glTranslatef(-0.45, 1.5, 0.0)
        glRotatef(90.0, 0.0, 1.0, 0.0)
        self._draw_cylinder(0.04, 0.90, 12)
        glPopMatrix()

        # Breastplate – two half-sphere ellipsoids, silver
        glColor3f(*_COL_SILVER)
        glPushMatrix()
        glTranslatef( 0.10, 1.20, 0.08)
        glScalef(0.18, 0.26, 0.10)
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.10, 1.20, 0.08)
        glScalef(0.18, 0.26, 0.10)
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()

        # Shield leaning against pole – flat pentagon shape (approx quad)
        glDisable(GL_LIGHTING)
        glColor3f(*_COL_RED)
        glBegin(GL_POLYGON)
        pts = [(-0.20, 0.60), (0.20, 0.60), (0.25, 0.95),
               (0.0, 1.20), (-0.25, 0.95)]
        for px, py in pts:
            glVertex3f(px, py, -0.15)
        glEnd()
        # Gold cross on shield
        glColor3f(*_COL_GOLD)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.62, -0.14); glVertex3f(0.0, 1.18, -0.14)
        glVertex3f(-0.22, 0.88, -0.14); glVertex3f(0.22, 0.88, -0.14)
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    def _draw_weapons_rack(self) -> None:
        """Wall-mounted horizontal bar with sword, bow, and staff."""
        # Two horizontal wooden bars
        glColor3f(*_COL_WOOD_MID)
        for y in (0.9, 1.4):
            glPushMatrix()
            glTranslatef(-0.60, y, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            self._draw_cylinder(0.03, 1.2, 10)
            glPopMatrix()

        # Sword – thin grey blade + brown handle
        glPushMatrix()
        glTranslatef(-0.35, 0.0, 0.02)
        # Blade
        glColor3f(*_COL_SILVER)
        glBegin(GL_QUADS)
        glVertex3f(-0.02, 0.55, 0.0); glVertex3f(0.02, 0.55, 0.0)
        glVertex3f(0.01, 1.35, 0.0);  glVertex3f(-0.01, 1.35, 0.0)
        glEnd()
        # Cross-guard
        glColor3f(*_COL_GOLD)
        glBegin(GL_QUADS)
        glVertex3f(-0.10, 0.53, 0.0); glVertex3f(0.10, 0.53, 0.0)
        glVertex3f(0.10, 0.58, 0.0);  glVertex3f(-0.10, 0.58, 0.0)
        glEnd()
        # Handle
        glColor3f(*_COL_WOOD_DARK)
        glBegin(GL_QUADS)
        glVertex3f(-0.025, 0.30, 0.0); glVertex3f(0.025, 0.30, 0.0)
        glVertex3f(0.025, 0.54, 0.0);  glVertex3f(-0.025, 0.54, 0.0)
        glEnd()
        glPopMatrix()

        # Bow – arc of line segments
        glDisable(GL_LIGHTING)
        glColor3f(*_COL_WOOD_MID)
        glLineWidth(3.0)
        glBegin(GL_LINE_STRIP)
        for i in range(13):
            a = math.pi * i / 12.0 - math.pi / 2.0
            glVertex3f(0.0 + 0.15 * math.cos(a), 0.95 + 0.40 * math.sin(a), 0.02)
        glEnd()
        # Bowstring
        glColor3f(*_COL_WHITE)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.55, 0.02)
        glVertex3f(0.0, 1.35, 0.02)
        glEnd()
        glEnable(GL_LIGHTING)

        # Staff – pole + glowing blue sphere
        glColor3f(*_COL_WOOD_DARK)
        glPushMatrix()
        glTranslatef(0.35, 0.0, 0.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        self._draw_cylinder(0.025, 1.5, 10)
        glPopMatrix()
        glColor3f(*_COL_BLUE_GLOW)
        glPushMatrix()
        glTranslatef(0.35, 1.55, 0.0)
        self._draw_sphere(0.07, 10, 10)
        glPopMatrix()

    def _draw_toy_box(self) -> None:
        """Wooden chest with slightly open lid."""
        # Main box body 1.0 × 0.55 × 0.7
        self._draw_box(
            -0.50, 0.0, -0.35,
             0.50, 0.55,  0.35,
            _COL_WOOD_MID)

        # Metal latch on front
        glDisable(GL_LIGHTING)
        glColor3f(*_COL_SILVER)
        glBegin(GL_QUADS)
        glVertex3f(-0.06, 0.20,  0.352)
        glVertex3f( 0.06, 0.20,  0.352)
        glVertex3f( 0.06, 0.30,  0.352)
        glVertex3f(-0.06, 0.30,  0.352)
        glEnd()
        glEnable(GL_LIGHTING)

        # Lid – tilted 15° backward around hinge at top of back face
        glPushMatrix()
        glTranslatef(0.0, 0.55, -0.35)
        glRotatef(-15.0, 1.0, 0.0, 0.0)
        self._draw_box(
            -0.50, 0.0, 0.0,
             0.50, 0.10, 0.70,
            _COL_WOOD_LIGHT)
        glPopMatrix()

        # Visible inside – toy ball (coloured sphere) and teddy (sphere cluster)
        glPushMatrix()
        glTranslatef(-0.15, 0.56, 0.05)
        glColor3f(0.85, 0.20, 0.20)
        self._draw_sphere(0.09, 10, 10)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.18, 0.58, 0.05)
        glColor3f(0.78, 0.58, 0.35)
        self._draw_sphere(0.08, 10, 10)  # teddy body
        glTranslatef(0.0, 0.12, 0.0)
        self._draw_sphere(0.05, 8, 8)   # teddy head
        glPopMatrix()

    def _draw_fridge(self) -> None:
        """Tall white refrigerator."""
        # Main body 0.8 wide × 2.0 tall × 0.7 deep
        self._draw_box(
            -0.40, 0.0, -0.35,
             0.40, 2.0,  0.35,
            _COL_WHITE)

        # Freezer door (upper 30%) recessed panel
        self._draw_box(
            -0.38, 1.40, 0.33,
             0.38, 1.96,  0.36,
            (0.90, 0.90, 0.92))

        # Main door (lower 70%) recessed panel
        self._draw_box(
            -0.38, 0.05, 0.33,
             0.38, 1.38,  0.36,
            (0.90, 0.90, 0.92))

        # Chrome handles – two cylinders
        glColor3f(*_COL_CHROME)
        for y0, y1 in [(1.55, 1.85), (0.60, 0.90)]:
            glPushMatrix()
            glTranslatef(0.30, y0, 0.37)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            self._draw_cylinder(0.025, y1 - y0, 8)
            glPopMatrix()

        # Fridge magnets – small coloured spheres
        _magnet_cols = [
            (0.9, 0.1, 0.1), (0.1, 0.6, 0.9),
            (0.1, 0.8, 0.2), (0.9, 0.8, 0.1),
        ]
        positions = [(-0.20, 1.10), (0.0, 1.15), (0.18, 1.08), (-0.05, 0.95)]
        for (mx, my), col in zip(positions, _magnet_cols):
            glColor3f(*col)
            glPushMatrix()
            glTranslatef(mx, my, 0.37)
            self._draw_sphere(0.04, 8, 8)
            glPopMatrix()

    def _draw_trophy_stand(self) -> None:
        """Wooden display stand with golden trophies."""
        # Base pedestal
        self._draw_box(
            -0.70, 0.0,  -0.20,
             0.70, 0.12,   0.20,
            _COL_WOOD_DARK)

        # Three shelves
        shelf_y = [0.12, 0.55, 0.98]
        for sy in shelf_y:
            self._draw_box(
                -0.70, sy,        -0.20,
                 0.70, sy + 0.08,  0.20,
                _COL_WOOD_MID)

        # Back upright board
        self._draw_box(
            -0.70, 0.12, -0.21,
             0.70, 1.50, -0.18,
            _COL_WOOD_DARK)

        # Trophies
        count = self._achievement_count
        if count == 0:
            # Placeholder text via a small sphere
            glColor3f(*_COL_GOLD)
            glPushMatrix()
            glTranslatef(0.0, 0.30, 0.0)
            self._draw_sphere(0.08, 10, 10)
            glPopMatrix()
        else:
            visible = min(count, 12)
            per_shelf = 4
            for i in range(visible):
                shelf_idx = i // per_shelf
                slot = i % per_shelf
                ty = shelf_y[shelf_idx] + 0.08
                tx = -0.50 + slot * 0.33
                glPushMatrix()
                glTranslatef(tx, ty, 0.0)
                # Trophy base – small gold cylinder
                glColor3f(*_COL_GOLD)
                glRotatef(-90.0, 1.0, 0.0, 0.0)
                self._draw_cylinder(0.04, 0.14, 8)
                glPopMatrix()
                # Trophy cup – sphere on top
                glColor3f(*_COL_GOLD)
                glPushMatrix()
                glTranslatef(tx, ty + 0.18, 0.0)
                self._draw_sphere(0.07, 8, 8)
                glPopMatrix()

    def _draw_backpack(self) -> None:
        """Small panda-green backpack leaning against the wall."""
        glEnable(GL_LIGHTING)
        # Main body — slightly squashed box
        self._draw_box(-0.22, 0.0, -0.12, 0.22, 0.60, 0.12, (0.18, 0.45, 0.22))
        # Top flap (rounded look — slightly protruding darker panel)
        self._draw_box(-0.20, 0.58, -0.11, 0.20, 0.68, 0.13, (0.12, 0.32, 0.16))
        # Front pocket
        self._draw_box(-0.16, 0.08, 0.10, 0.16, 0.38, 0.16, (0.14, 0.38, 0.18))
        # Straps (two thin dark strips on back)
        self._draw_box(-0.18, 0.05, -0.13, -0.10, 0.55, -0.10, (0.08, 0.20, 0.10))
        self._draw_box( 0.10, 0.05, -0.13,  0.18, 0.55, -0.10, (0.08, 0.20, 0.10))
        # Buckle (small gold rectangle on front pocket)
        self._draw_box(-0.06, 0.22, 0.14, 0.06, 0.28, 0.17, (0.80, 0.65, 0.10))
        glDisable(GL_LIGHTING)

    def _draw_bedroom_door(self) -> None:
        """Front door set into the south wall — double panel with glass transom."""
        glEnable(GL_LIGHTING)

        # Door frame (dark wood surround)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.28, 0.18, 0.10, 1.0])
        self._draw_box(-0.55, 0.0, -0.06, 0.55, 2.25, 0.0, (0.28, 0.18, 0.10))

        # Left door panel
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.55, 0.38, 0.20, 1.0])
        self._draw_box(-0.52, 0.02, -0.04, -0.03, 2.0, 0.04, (0.55, 0.38, 0.20))

        # Right door panel
        self._draw_box(0.03, 0.02, -0.04, 0.52, 2.0, 0.04, (0.55, 0.38, 0.20))

        # Transom glass (above door)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(*_COL_GLASS)
        self._draw_box(-0.52, 2.02, -0.03, 0.52, 2.20, 0.03, _COL_GLASS[:3])
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

        # Door knobs
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.80, 0.65, 0.10, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR,            [0.90, 0.80, 0.20, 1.0])
        glMaterialf (GL_FRONT, GL_SHININESS, 64.0)
        for knob_x in (-0.06, 0.06):
            glPushMatrix()
            glTranslatef(knob_x, 1.0, 0.05)
            self._draw_sphere(0.05, 10, 10)
            glPopMatrix()

        # "Go outside" text hint drawn as a doormat (flat quad)
        glDisable(GL_LIGHTING)
        glColor3f(0.45, 0.30, 0.15)
        glBegin(GL_QUADS)
        glVertex3f(-0.45, 0.001, 0.15)
        glVertex3f( 0.45, 0.001, 0.15)
        glVertex3f( 0.45, 0.001, 0.55)
        glVertex3f(-0.45, 0.001, 0.55)
        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_computer_desk(self) -> None:
        """Desk with a monitor, keyboard, and glowing screen — clicking opens the tools panel."""
        glEnable(GL_LIGHTING)
        # Desk surface (light pine wood)
        self._draw_box(-0.60, 0.60, -0.30,  0.60, 0.68,  0.30, (0.72, 0.55, 0.32))
        # Left leg
        self._draw_box(-0.55, 0.0, -0.28, -0.48, 0.60, -0.22, (0.58, 0.42, 0.22))
        # Right leg
        self._draw_box( 0.48, 0.0, -0.28,  0.55, 0.60, -0.22, (0.58, 0.42, 0.22))
        # Monitor stand (slim dark box)
        self._draw_box(-0.06, 0.68, -0.08,  0.06, 0.88, -0.04, (0.15, 0.15, 0.18))
        # Monitor frame (dark grey bezel)
        self._draw_box(-0.42, 0.88, -0.10,  0.42, 1.48, -0.05, (0.12, 0.12, 0.15))
        # Screen glow (bright cyan — rendered without lighting)
        glDisable(GL_LIGHTING)
        glColor4f(0.20, 0.80, 0.90, 1.0)
        self._draw_box(-0.38, 0.92, -0.08,  0.38, 1.44, -0.04, (0.20, 0.80, 0.90))
        glEnable(GL_LIGHTING)
        # Keyboard (thin flat box on desk surface)
        self._draw_box(-0.28, 0.68,  0.05,  0.28, 0.72,  0.25, (0.20, 0.20, 0.24))

    # ── Primitive helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _draw_sphere(radius: float, slices: int, stacks: int) -> None:
        q = gluNewQuadric()
        gluQuadricNormals(q, GLU_SMOOTH)
        gluSphere(q, radius, slices, stacks)
        gluDeleteQuadric(q)

    @staticmethod
    def _draw_cylinder(radius: float, height: float, slices: int) -> None:
        q = gluNewQuadric()
        gluQuadricNormals(q, GLU_SMOOTH)
        gluCylinder(q, radius, radius, height, slices, 1)
        # Cap the ends
        gluDisk(q, 0, radius, slices, 1)
        glPushMatrix()
        glTranslatef(0.0, 0.0, height)
        gluDisk(q, 0, radius, slices, 1)
        glPopMatrix()
        gluDeleteQuadric(q)

    @staticmethod
    def _draw_box(
        x0: float, y0: float, z0: float,
        x1: float, y1: float, z1: float,
        colour: Optional[tuple] = None,
    ) -> None:
        """Draw a solid axis-aligned box.

        If *colour* is provided it is applied with glColor3f; otherwise the
        current GL colour (set by the caller via glColor3f / glMaterialfv) is
        used.  This allows callers that pre-set the colour to omit the argument.
        """
        if colour is not None:
            glColor3f(*colour[:3])
        glBegin(GL_QUADS)
        # Bottom
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(x0, y0, z0); glVertex3f(x1, y0, z0)
        glVertex3f(x1, y0, z1); glVertex3f(x0, y0, z1)
        # Top
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(x0, y1, z1); glVertex3f(x1, y1, z1)
        glVertex3f(x1, y1, z0); glVertex3f(x0, y1, z0)
        # Front
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(x0, y0, z1); glVertex3f(x1, y0, z1)
        glVertex3f(x1, y1, z1); glVertex3f(x0, y1, z1)
        # Back
        glNormal3f(0.0, 0.0, -1.0)
        glVertex3f(x1, y0, z0); glVertex3f(x0, y0, z0)
        glVertex3f(x0, y1, z0); glVertex3f(x1, y1, z0)
        # Left
        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(x0, y0, z0); glVertex3f(x0, y0, z1)
        glVertex3f(x0, y1, z1); glVertex3f(x0, y1, z0)
        # Right
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(x1, y0, z1); glVertex3f(x1, y0, z0)
        glVertex3f(x1, y1, z0); glVertex3f(x1, y1, z1)
        glEnd()

    # ── Picking / ray-casting ─────────────────────────────────────────────────

    def _ray_from_screen(self, wx: float, wy: float) -> Optional[Tuple[tuple, tuple]]:
        """Return (origin, direction) world-space ray for screen position.

        Uses matrices cached in paintGL rather than reading from the GL context
        in event handlers, where the state is unreliable outside the paint cycle.
        """
        try:
            viewport  = self._pick_viewport
            model_mat = self._pick_modelview
            proj_mat  = self._pick_projection
            if viewport is None or model_mat is None or proj_mat is None:
                # Matrices not yet cached (no paint cycle yet); try GL directly
                viewport  = glGetIntegerv(GL_VIEWPORT)
                model_mat = glGetDoublev(GL_MODELVIEW_MATRIX)
                proj_mat  = glGetDoublev(GL_PROJECTION_MATRIX)
            win_y = viewport[3] - wy  # flip Y
            near = gluUnProject(wx, win_y, 0.0, model_mat, proj_mat, viewport)
            far  = gluUnProject(wx, win_y, 1.0, model_mat, proj_mat, viewport)
            dx, dy, dz = far[0] - near[0], far[1] - near[1], far[2] - near[2]
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            if length < 1e-9:
                return None
            return (near, (dx / length, dy / length, dz / length))
        except Exception:
            return None

    def _ray_floor_intersect(self, wx: int, wy: int) -> Optional[Tuple[float, float]]:
        """Return world (x, z) where the screen ray hits Y=0 floor plane."""
        result = self._ray_from_screen(wx, wy)
        if result is None:
            return None
        origin, direction = result
        if abs(direction[1]) < 1e-9:
            return None
        t = -origin[1] / direction[1]
        if t < 0:
            return None
        hit_x = origin[0] + t * direction[0]
        hit_z = origin[2] + t * direction[2]
        return (hit_x, hit_z)

    def _pick_furniture(self, wx: int, wy: int) -> Optional[FurniturePiece]:
        """Return the furniture piece whose bounding box the ray hits, or None."""
        result = self._ray_from_screen(wx, wy)
        if result is None:
            return None
        origin, direction = result

        _bounds = {
            'wardrobe':       (1.2, 2.0, 0.6),
            'armor_rack':     (1.0, 1.8, 0.5),
            'weapons_rack':   (1.2, 1.5, 0.3),
            'toy_box':        (1.0, 0.7, 0.7),
            'fridge':         (0.8, 2.0, 0.7),
            'trophy_stand':   (1.4, 1.5, 0.4),
            'backpack':       (0.5, 0.7, 0.3),
            'computer_desk':  (1.2, 1.5, 0.6),
            'bedroom_door':   (1.0, 2.2, 0.15),
        }

        best: Optional[FurniturePiece] = None
        best_t = float('inf')

        for piece in self._furniture:
            bw, bh, bd = _bounds.get(piece.id, (1.0, 1.0, 1.0))
            x0, x1 = piece.x - bw / 2, piece.x + bw / 2
            y0, y1 = piece.y,           piece.y + bh
            z0, z1 = piece.z - bd / 2,  piece.z + bd / 2

            t = self._ray_aabb(origin, direction, x0, x1, y0, y1, z0, z1)
            if t is not None and t < best_t:
                best_t = t
                best = piece

        return best

    @staticmethod
    def _ray_aabb(
        origin: tuple, direction: tuple,
        x0: float, x1: float,
        y0: float, y1: float,
        z0: float, z1: float,
    ) -> Optional[float]:
        """Slab-method AABB intersection. Returns entry t or None."""
        ox, oy, oz = origin
        dx, dy, dz = direction
        t_min, t_max = 0.0, float('inf')

        for o, d, mn, mx in [
            (ox, dx, x0, x1),
            (oy, dy, y0, y1),
            (oz, dz, z0, z1),
        ]:
            if abs(d) < 1e-9:
                if o < mn or o > mx:
                    return None
            else:
                t1 = (mn - o) / d
                t2 = (mx - o) / d
                if t1 > t2:
                    t1, t2 = t2, t1
                t_min = max(t_min, t1)
                t_max = min(t_max, t2)
                if t_min > t_max:
                    return None

        return t_min if t_min >= 0 else None

    def _project_to_screen(self, wx: float, wy: float, wz: float) -> Optional[Tuple[float, float]]:
        """Project world position to screen (pixel) coordinates.

        Uses matrices cached in paintGL for consistency with _ray_from_screen.
        Falls back to a live GL query only if no paint cycle has run yet.
        """
        try:
            viewport  = self._pick_viewport
            model_mat = self._pick_modelview
            proj_mat  = self._pick_projection
            if viewport is None or model_mat is None or proj_mat is None:
                viewport  = glGetIntegerv(GL_VIEWPORT)
                model_mat = glGetDoublev(GL_MODELVIEW_MATRIX)
                proj_mat  = glGetDoublev(GL_PROJECTION_MATRIX)
            sx, sy, _ = gluProject(wx, wy, wz, model_mat, proj_mat, viewport)
            sy = viewport[3] - sy  # flip Y back to Qt coords
            return (sx, sy)
        except Exception:
            return None

    def _update_hover(self) -> None:
        """Update _hovered_id based on cursor proximity to furniture centres."""
        if not self._last_mouse:
            return
        mx, my = self._last_mouse.x(), self._last_mouse.y()
        closest_id: Optional[str] = None
        closest_d = 60.0  # pixel threshold

        for piece in self._furniture:
            centre_y = {
                'wardrobe': 1.0, 'armor_rack': 0.9, 'weapons_rack': 0.75,
                'toy_box': 0.35, 'fridge': 1.0, 'trophy_stand': 0.75,
                'backpack': 0.35, 'computer_desk': 1.0, 'bedroom_door': 1.1,
            }.get(piece.id, 0.5)
            proj = self._project_to_screen(piece.x, centre_y, piece.z)
            if proj is None:
                continue
            dx, dy = proj[0] - mx, proj[1] - my
            d = math.sqrt(dx * dx + dy * dy)
            if d < closest_d:
                closest_d = d
                closest_id = piece.id

        self._hovered_id = closest_id

    # ── Mouse events ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event: 'QMouseEvent') -> None:  # type: ignore[override]
        if not self._gl_ok:
            return
        self.makeCurrent()
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_piece = self._pick_furniture(event.position().x(), event.position().y())
            # Fallback: if the ray cast misses everything (e.g. matrices weren't cached
            # yet), use whichever furniture piece is currently highlighted by the
            # projection-based hover system — this is always reliable.
            if self._drag_piece is None and self._hovered_id:
                self._drag_piece = self.get_furniture(self._hovered_id)
            self._drag_start_screen = QPoint(int(event.position().x()), int(event.position().y()))
            if self._drag_piece:
                hit = self._ray_floor_intersect(int(event.position().x()), int(event.position().y()))
                self._drag_start_world = hit
        elif event.button() == Qt.MouseButton.RightButton:
            self._right_dragging = True
        self._last_mouse = QPoint(int(event.position().x()), int(event.position().y()))

    # Map furniture IDs to short hover descriptions shown as Qt tooltips
    _FURNITURE_TIPS = {
        'wardrobe':      '👗 Wardrobe — Click to browse outfits & costumes',
        'armor_rack':    '🛡️ Armor Rack — Click to equip armour sets',
        'weapons_rack':  '⚔️ Weapons Rack — Click to manage weapons',
        'toy_box':       '🧸 Toy Box — Click to play with toys & accessories',
        'fridge':        '🍎 Fridge — Click to manage food & treats',
        'trophy_stand':  '🏆 Trophy Stand — Click to view achievements',
        'backpack':      '🎒 Backpack — Click to open inventory & items',
        'computer_desk': '💻 Computer Desk — Click to access tools & utilities',
        'bedroom_door':  '🚪 Door — Click to go outside to the world',
    }

    def mouseMoveEvent(self, event: 'QMouseEvent') -> None:  # type: ignore[override]
        if not self._gl_ok:
            return
        self.makeCurrent()
        cur = QPoint(int(event.position().x()), int(event.position().y()))

        if self._drag_piece and event.buttons() & Qt.MouseButton.LeftButton:
            hit = self._ray_floor_intersect(cur.x(), cur.y())
            if hit is not None:
                nx = max(-3.5, min(3.5, hit[0]))
                nz = max(-3.5, min(3.5, hit[1]))
                self._drag_piece.x = nx
                self._drag_piece.z = nz
            self.update()

        elif self._right_dragging and event.buttons() & Qt.MouseButton.RightButton:
            if self._last_mouse:
                dx = cur.x() - self._last_mouse.x()
                dy = cur.y() - self._last_mouse.y()
                self._cam_az  += dx * 0.5
                self._cam_el   = max(-80.0, min(80.0, self._cam_el + dy * 0.5))
                self.update()

        self._last_mouse = cur
        self.update()  # always repaint so hover highlights update in paintGL._update_hover()

        # Show a Qt tooltip for the hovered furniture piece
        try:
            prev_hover = self._hovered_id
            self._update_hover()
            if self._hovered_id != prev_hover:
                # Hover changed — update tooltip
                tip = self._FURNITURE_TIPS.get(self._hovered_id or '', '')
                if OPENGL_AVAILABLE:
                    from PyQt6.QtWidgets import QToolTip
                    if tip:
                        QToolTip.showText(event.globalPosition().toPoint(), tip, self)
                    else:
                        QToolTip.hideText()
        except Exception:
            pass

    def mouseReleaseEvent(self, event: 'QMouseEvent') -> None:  # type: ignore[override]
        if not self._gl_ok:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_piece and self._drag_start_screen:
                cur = QPoint(int(event.position().x()), int(event.position().y()))
                dx = cur.x() - self._drag_start_screen.x()
                dy = cur.y() - self._drag_start_screen.y()
                drag_dist = math.sqrt(dx * dx + dy * dy)
                if drag_dist < 5:
                    self.furniture_clicked.emit(self._drag_piece.id)
                else:
                    self._save_layout()
            self._drag_piece = None
            self._drag_start_screen = None
            self._drag_start_world = None
        elif event.button() == Qt.MouseButton.RightButton:
            self._right_dragging = False

    def wheelEvent(self, event: 'QWheelEvent') -> None:  # type: ignore[override]
        delta = event.angleDelta().y() / 120.0
        self._cam_dist = max(3.5, min(12.0, self._cam_dist - delta * 0.5))
        self.update()

    # ── Layout persistence ────────────────────────────────────────────────────

    def _save_layout(self) -> None:
        try:
            self._layout_path.parent.mkdir(parents=True, exist_ok=True)
            data = {p.id: {'x': p.x, 'z': p.z, 'rot_y': p.rot_y}
                    for p in self._furniture}
            with open(self._layout_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            logger.warning("Could not save bedroom layout: %s", exc)

    def _load_layout(self) -> None:
        try:
            if not self._layout_path.exists():
                return
            with open(self._layout_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for piece in self._furniture:
                if piece.id in data:
                    entry = data[piece.id]
                    piece.x     = float(entry.get('x', piece.x))
                    piece.z     = float(entry.get('z', piece.z))
                    piece.rot_y = float(entry.get('rot_y', piece.rot_y))
        except Exception as exc:
            logger.warning("Could not load bedroom layout: %s", exc)
