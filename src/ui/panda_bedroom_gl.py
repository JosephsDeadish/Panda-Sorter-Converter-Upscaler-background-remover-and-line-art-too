"""
OpenGL Panda Bedroom Widget - Interactive 3D bedroom scene.
Renders a cosy panda bedroom with clickable / draggable furniture pieces.
Author: Dead On The Inside / JosephsDeadish
"""

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple

try:
    from PyQt6.QtWidgets import QWidget, QApplication
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QTimer
    from PyQt6.QtGui import QMouseEvent, QWheelEvent, QSurfaceFormat
    from OpenGL.GL import *
    from OpenGL.GLU import *
    OPENGL_AVAILABLE = True
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

# ── Default furniture layout ──────────────────────────────────────────────────

_DEFAULT_POSITIONS = {
    'wardrobe':     {'x': -2.8, 'z': -3.0, 'rot_y':   0.0},
    'armor_rack':   {'x':  2.5, 'z': -3.0, 'rot_y': 180.0},
    'weapons_rack': {'x':  3.3, 'z': -1.5, 'rot_y': -90.0},
    'toy_box':      {'x': -3.0, 'z':  1.8, 'rot_y':  90.0},
    'fridge':       {'x':  3.2, 'z':  1.8, 'rot_y': -90.0},
    'trophy_stand': {'x':  0.0, 'z': -3.2, 'rot_y':   0.0},
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
        ('wardrobe',     'Wardrobe',     '🚪', -2.8, 0.0, -3.0,   0.0, -2.2, -1.8, 'Clothes'),
        ('armor_rack',   'Armor Rack',   '🛡️',  2.5, 0.0, -3.0, 180.0,  1.8, -1.8, 'Accessories'),
        ('weapons_rack', 'Weapons Rack', '⚔️',  3.3, 0.0, -1.5, -90.0,  2.5, -0.8, 'Accessories'),
        ('toy_box',      'Toy Box',      '🧸', -3.0, 0.0,  1.8,  90.0, -2.2,  1.2, 'Toys'),
        ('fridge',       'Fridge',       '🧊',  3.2, 0.0,  1.8, -90.0,  2.5,  1.2, 'Food'),
        ('trophy_stand', 'Trophy Stand', '🏆',  0.0, 0.0, -3.2,   0.0,  0.0, -2.0, 'achievements'),
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

        fmt = QSurfaceFormat()
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

        # GL flag
        self._gl_ok: bool = False

        # Layout persistence
        try:
            from src.config import get_data_dir
            self._layout_path: Path = Path(get_data_dir()) / 'bedroom_layout.json'
        except Exception:
            self._layout_path = Path('app_data') / 'bedroom_layout.json'

        self.setMouseTracking(True)
        self.setMinimumSize(400, 300)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_achievement_count(self, count: int) -> None:
        """Update trophy count and repaint."""
        self._achievement_count = count
        self.update()

    def get_furniture(self, furniture_id: str) -> Optional[FurniturePiece]:
        """Return the FurniturePiece dataclass or None."""
        for p in self._furniture:
            if p.id == furniture_id:
                return p
        return None

    # ── OpenGL lifecycle ──────────────────────────────────────────────────────

    def initializeGL(self) -> None:
        try:
            self._do_init_gl()
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
        glShadeModel(GL_SMOOTH)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.15, 0.12, 0.10, 1.0)

        # Lighting
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

        self._load_layout()

    def resizeGL(self, w: int, h: int) -> None:
        if h == 0:
            h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, w / h, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self) -> None:
        if not self._gl_ok:
            return

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera orbit
        gluLookAt(0, 0, self._cam_dist,  0, 0, 0,  0, 1, 0)
        glRotatef(self._cam_el, 1.0, 0.0, 0.0)
        glRotatef(self._cam_az, 0.0, 1.0, 0.0)

        # Update hover by projecting furniture centres to screen
        self._update_hover()

        self._draw_room()
        self._draw_furniture()

    # ── Room geometry ─────────────────────────────────────────────────────────

    def _draw_room(self) -> None:
        glDisable(GL_LIGHTING)

        # Floor – wood planks 8×8 grid of 1×1 quads
        for row in range(8):
            for col in range(8):
                x0 = -4.0 + col
                x1 = x0 + 1.0
                z0 = -4.0 + row
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

        # Back wall (Z=-4)
        self._draw_wall_back()
        # Left wall  (X=-4)
        self._draw_wall_left()
        # Right wall (X=4)
        self._draw_wall_right()
        # Ceiling
        self._draw_ceiling()
        # Baseboards
        self._draw_baseboards()

        glEnable(GL_LIGHTING)

    def _draw_wall_back(self) -> None:
        # Main wall surface
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
            'wardrobe':     (1.2, 2.0, 0.6),
            'armor_rack':   (1.0, 1.8, 0.5),
            'weapons_rack': (1.2, 1.5, 0.3),
            'toy_box':      (1.0, 0.7, 0.7),
            'fridge':       (0.8, 2.0, 0.7),
            'trophy_stand': (1.4, 1.5, 0.4),
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
        colour: tuple,
    ) -> None:
        """Draw a solid axis-aligned box with the given colour."""
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

    def _ray_from_screen(self, wx: int, wy: int) -> Optional[Tuple[tuple, tuple]]:
        """Return (origin, direction) world-space ray for screen position."""
        try:
            viewport   = glGetIntegerv(GL_VIEWPORT)
            model_mat  = glGetDoublev(GL_MODELVIEW_MATRIX)
            proj_mat   = glGetDoublev(GL_PROJECTION_MATRIX)
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
            'wardrobe':     (1.2, 2.0, 0.6),
            'armor_rack':   (1.0, 1.8, 0.5),
            'weapons_rack': (1.2, 1.5, 0.3),
            'toy_box':      (1.0, 0.7, 0.7),
            'fridge':       (0.8, 2.0, 0.7),
            'trophy_stand': (1.4, 1.5, 0.4),
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
        """Project world position to screen (pixel) coordinates."""
        try:
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
            self._drag_start_screen = QPoint(int(event.position().x()), int(event.position().y()))
            if self._drag_piece:
                hit = self._ray_floor_intersect(int(event.position().x()), int(event.position().y()))
                self._drag_start_world = hit
        elif event.button() == Qt.MouseButton.RightButton:
            self._right_dragging = True
        self._last_mouse = QPoint(int(event.position().x()), int(event.position().y()))

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
