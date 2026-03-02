from __future__ import annotations
"""
Dungeon3DWidget — Full 3D OpenGL dungeon where the 3D panda is the player.

Architecture
------------
- QOpenGLWidget renders walls/floor/ceiling in 3-D using OpenGL fixed-function.
- The same _draw_panda_in_room() GL routines from panda_bedroom_gl are reused
  here so the player sees their own panda running through corridors.
- WASD / Arrow-key controls move the panda; mouse-drag rotates the camera.
- The dungeon map comes from features.integrated_dungeon.IntegratedDungeon so
  the same generated layouts used by the 2-D view work here too.
- Falls back gracefully to a QLabel placeholder when OpenGL is unavailable.
"""

import logging
import math
import random
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

# ── Qt / OpenGL imports ───────────────────────────────────────────────────────
try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                  QPushButton, QStackedWidget)
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF
    from PyQt6.QtGui import QColor, QPainter, QFont, QKeyEvent, QMouseEvent
    _QT = True
except (ImportError, OSError, RuntimeError):
    _QT = False
    QOpenGLWidget = object
    QWidget = object

try:
    from OpenGL.GL import (
        glEnable, glDisable, glClearColor, glClear, glLoadIdentity, glMatrixMode,
        glViewport, glTranslatef, glRotatef, glScalef, glPushMatrix, glPopMatrix,
        glColor3f, glColor4f, glBegin, glEnd, glVertex3f, glNormal3f,
        glLightfv, glMaterialfv, glColorMaterial,
        GL_DEPTH_TEST, GL_LIGHTING, GL_LIGHT0, GL_COLOR_MATERIAL,
        GL_AMBIENT_AND_DIFFUSE, GL_AMBIENT, GL_DIFFUSE, GL_SPECULAR, GL_POSITION,
        GL_PROJECTION, GL_MODELVIEW, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
        GL_FRONT_AND_BACK, GL_QUADS, GL_TRIANGLES, GL_LINES, GL_FOG,
        GL_FOG_MODE, GL_FOG_COLOR, GL_FOG_START, GL_FOG_END, GL_LINEAR,
        glFogi, glFogf, glFogfv,
    )
    from OpenGL.GLU import gluPerspective, gluNewQuadric, gluSphere
    _GL = True
except (ImportError, OSError, RuntimeError):
    _GL = False

# ── Colours ───────────────────────────────────────────────────────────────────
_COL_FLOOR   = (0.29, 0.22, 0.16)   # warm stone
_COL_WALL    = (0.20, 0.18, 0.14)   # dark stone
_COL_CEIL    = (0.12, 0.11, 0.10)   # near-black ceiling
_COL_TORCH   = (1.0,  0.65, 0.15)   # torch flicker
_COL_WHITE   = (0.92, 0.92, 0.90)
_COL_BLACK   = (0.08, 0.06, 0.06)

# Tile size in world units
_TILE = 2.0
_WALL_H = 3.0  # wall height

# Movement speed (world units per tick)
_MOVE_SPEED = 0.08
_COLLISION_MARGIN = 0.4   # world-unit margin for wall-slide collision checks

# ── Helpers ───────────────────────────────────────────────────────────────────

def _gl_quad(x0, y0, z0, x1, y1, z1, x2, y2, z2, x3, y3, z3, nx, ny, nz):
    glNormal3f(nx, ny, nz)
    glVertex3f(x0, y0, z0)
    glVertex3f(x1, y1, z1)
    glVertex3f(x2, y2, z2)
    glVertex3f(x3, y3, z3)


# ── Main 3-D dungeon GL widget ────────────────────────────────────────────────

class _Dungeon3DGL(QOpenGLWidget if (_QT and _GL) else object):  # type: ignore[misc]
    """OpenGL-rendered 3-D dungeon viewport with a controllable 3-D panda."""

    # Emitted when the player reaches stairs down (advance floor)
    floor_advanced = pyqtSignal(int)  # new floor index

    def __init__(self, dungeon=None, parent=None):
        if not (_QT and _GL):
            raise ImportError("PyQt6 and PyOpenGL are required for 3-D dungeon")
        super().__init__(parent)

        self._dungeon = dungeon       # IntegratedDungeon | None
        self._floor_idx = 0

        # ── Camera / player state ─────────────────────────────────────────────
        self._cam_x: float = 2.0
        self._cam_z: float = 2.0
        self._cam_yaw: float = 0.0    # degrees, Y-axis rotation
        self._cam_pitch: float = -10.0  # slight downward tilt

        # ── Walk animation ────────────────────────────────────────────────────
        self._walk_frame: float = 0.0
        self._is_walking: bool = False

        # ── Torch flicker ─────────────────────────────────────────────────────
        self._torch_t: float = 0.0

        # ── Mouse drag ────────────────────────────────────────────────────────
        self._last_mouse: Optional[QPointF] = None

        # ── Keys held ─────────────────────────────────────────────────────────
        self._keys: set = set()

        # ── GLU quadric ───────────────────────────────────────────────────────
        self._quadric = None

        # ── HUD ───────────────────────────────────────────────────────────────
        self._hud_msg: str = ""
        self._hud_timer: int = 0  # frames remaining

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        # Movement tick
        self._move_timer = QTimer(self)
        self._move_timer.timeout.connect(self._tick)
        self._move_timer.start(16)   # ~60 fps

    # ── Setup ─────────────────────────────────────────────────────────────────

    def set_dungeon(self, dungeon) -> None:
        """Attach an IntegratedDungeon and place the player at a walkable tile."""
        self._dungeon = dungeon
        self._floor_idx = 0
        self._place_player_at_start()
        self.update()

    def set_floor(self, floor_idx: int) -> None:
        self._floor_idx = floor_idx
        self._place_player_at_start()
        self.update()

    def _place_player_at_start(self) -> None:
        """Find a walkable tile and place the camera there."""
        grid = self._floor_grid()
        if grid is None:
            self._cam_x = 2.0
            self._cam_z = 2.0
            return
        h = len(grid)
        w = len(grid[0]) if h else 0
        for row in range(1, h - 1):
            for col in range(1, w - 1):
                if grid[row][col] == 0:
                    self._cam_x = col * _TILE + _TILE / 2
                    self._cam_z = row * _TILE + _TILE / 2
                    return

    def _floor_grid(self):
        """Return the 2-D collision map list-of-lists for the current floor."""
        if self._dungeon is None:
            return None
        try:
            fl = self._dungeon.dungeon.get_floor(self._floor_idx)
            return fl.collision_map if fl else None
        except Exception:
            return None

    def _is_wall(self, wx: float, wz: float) -> bool:
        """Return True if world position (wx, wz) is inside a wall."""
        grid = self._floor_grid()
        if grid is None:
            return False
        col = int(wx / _TILE)
        row = int(wz / _TILE)
        h = len(grid)
        w = len(grid[0]) if h else 0
        if row < 0 or row >= h or col < 0 or col >= w:
            return True
        return grid[row][col] != 0

    # ── GL lifecycle ──────────────────────────────────────────────────────────

    def initializeGL(self) -> None:
        try:
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glClearColor(0.02, 0.01, 0.03, 1.0)

            # Fog for atmosphere
            glEnable(GL_FOG)
            glFogi(GL_FOG_MODE, GL_LINEAR)
            glFogfv(GL_FOG_COLOR, [0.02, 0.01, 0.03, 1.0])
            glFogf(GL_FOG_START, 6.0)
            glFogf(GL_FOG_END, 18.0)

            self._quadric = gluNewQuadric()
        except Exception as exc:
            logger.warning(f"Dungeon3D initializeGL: {exc}")

    def resizeGL(self, w: int, h: int) -> None:
        try:
            glViewport(0, 0, w, h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(65.0, (w / h) if h else 1.0, 0.05, 50.0)
            glMatrixMode(GL_MODELVIEW)
        except Exception:
            pass

    def paintGL(self) -> None:
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()

            # Torch flicker — update ambient light colour
            flicker = 0.3 + 0.05 * math.sin(self._torch_t * 3.7)
            glLightfv(GL_LIGHT0, GL_AMBIENT,  [flicker, flicker * 0.6, 0.0, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.8,     0.5,          0.1, 1.0])
            glLightfv(GL_LIGHT0, GL_POSITION, [self._cam_x, 1.5, self._cam_z, 1.0])

            # Camera transform: pitch then yaw then translate
            glRotatef(-self._cam_pitch, 1.0, 0.0, 0.0)
            glRotatef(-self._cam_yaw,   0.0, 1.0, 0.0)
            glTranslatef(-self._cam_x, -1.0, -self._cam_z)

            self._draw_dungeon_geometry()
            self._draw_panda()
        except Exception as exc:
            logger.debug(f"Dungeon3D paintGL: {exc}")

    # ── Geometry ──────────────────────────────────────────────────────────────

    def _draw_dungeon_geometry(self) -> None:
        grid = self._floor_grid()
        if grid is None:
            self._draw_placeholder_room()
            return

        h = len(grid)
        w = len(grid[0]) if h else 0

        # Only draw tiles near player for performance
        pcol = int(self._cam_x / _TILE)
        prow = int(self._cam_z / _TILE)
        VIEW = 6  # tile radius to draw

        glBegin(GL_QUADS)
        for row in range(max(0, prow - VIEW), min(h, prow + VIEW + 1)):
            for col in range(max(0, pcol - VIEW), min(w, pcol + VIEW + 1)):
                x0 = col * _TILE
                z0 = row * _TILE
                x1 = x0 + _TILE
                z1 = z0 + _TILE

                if grid[row][col] == 0:
                    # Floor tile
                    glColor3f(*_COL_FLOOR)
                    _gl_quad(x0,0,z0, x1,0,z0, x1,0,z1, x0,0,z1, 0,1,0)
                    # Ceiling
                    glColor3f(*_COL_CEIL)
                    _gl_quad(x0,_WALL_H,z0, x0,_WALL_H,z1, x1,_WALL_H,z1, x1,_WALL_H,z0, 0,-1,0)
                    # Draw walls on solid-tile neighbours
                    for (dr, dc, nx, nz) in ((-1,0,0,-1),(1,0,0,1),(0,-1,-1,0),(0,1,1,0)):
                        nr, nc = row + dr, col + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
                            glColor3f(*_COL_WALL)
                            if dr == -1:  # north wall
                                _gl_quad(x0,0,z0, x1,0,z0, x1,_WALL_H,z0, x0,_WALL_H,z0, 0,0,1)
                            elif dr == 1:  # south wall
                                _gl_quad(x1,0,z1, x0,0,z1, x0,_WALL_H,z1, x1,_WALL_H,z1, 0,0,-1)
                            elif dc == -1:  # west wall
                                _gl_quad(x0,0,z1, x0,0,z0, x0,_WALL_H,z0, x0,_WALL_H,z1, 1,0,0)
                            elif dc == 1:  # east wall
                                _gl_quad(x1,0,z0, x1,0,z1, x1,_WALL_H,z1, x1,_WALL_H,z0, -1,0,0)
        glEnd()

    def _draw_placeholder_room(self) -> None:
        """Draw a simple room when no dungeon data is available."""
        glBegin(GL_QUADS)
        # Floor 20×20
        glColor3f(*_COL_FLOOR)
        _gl_quad(-10,0,-10, 10,0,-10, 10,0,10, -10,0,10, 0,1,0)
        # Ceiling
        glColor3f(*_COL_CEIL)
        _gl_quad(-10,_WALL_H,-10, -10,_WALL_H,10, 10,_WALL_H,10, 10,_WALL_H,-10, 0,-1,0)
        # Four walls
        glColor3f(*_COL_WALL)
        _gl_quad(-10,0,-10, 10,0,-10, 10,_WALL_H,-10, -10,_WALL_H,-10, 0,0,1)
        _gl_quad(10,0,10, -10,0,10, -10,_WALL_H,10, 10,_WALL_H,10, 0,0,-1)
        _gl_quad(-10,0,10, -10,0,-10, -10,_WALL_H,-10, -10,_WALL_H,10, 1,0,0)
        _gl_quad(10,0,-10, 10,0,10, 10,_WALL_H,10, 10,_WALL_H,-10, -1,0,0)
        glEnd()

    # ── Panda drawing (replicates bedroom panda) ──────────────────────────────

    def _draw_panda(self) -> None:
        """Draw the 3-D panda 1.5 m ahead of the camera as the player character."""
        if self._quadric is None:
            return

        # Place 1.5 m ahead of camera and facing away (forward direction)
        yaw_rad = math.radians(self._cam_yaw)
        px = self._cam_x + 1.5 * math.sin(yaw_rad)
        pz = self._cam_z + 1.5 * math.cos(yaw_rad)

        swing_amp = 20.0 if self._is_walking else 0.0

        glPushMatrix()
        glTranslatef(px, 0.0, pz)
        glRotatef(self._cam_yaw + 180.0, 0.0, 1.0, 0.0)

        # Body
        glPushMatrix()
        glTranslatef(0.0, 0.38, 0.0)
        glScalef(0.32, 0.38, 0.28)
        glColor3f(*_COL_WHITE)
        gluSphere(self._quadric, 1.0, 14, 14)
        glPopMatrix()

        # Head
        glPushMatrix()
        glTranslatef(0.0, 0.88, 0.08)
        glColor3f(*_COL_WHITE)
        gluSphere(self._quadric, 0.22, 14, 14)
        for ex in (-0.14, 0.14):
            glPushMatrix()
            glTranslatef(ex, 0.18, -0.04)
            glColor3f(*_COL_BLACK)
            gluSphere(self._quadric, 0.07, 8, 8)
            glPopMatrix()
        for ex in (-0.08, 0.08):
            glPushMatrix()
            glTranslatef(ex, 0.04, 0.19)
            glScalef(1.0, 0.9, 0.55)
            glColor3f(*_COL_BLACK)
            gluSphere(self._quadric, 0.06, 8, 8)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, -0.03, 0.21)
        glColor3f(0.15, 0.10, 0.10)
        gluSphere(self._quadric, 0.025, 6, 6)
        glPopMatrix()
        glPopMatrix()  # head

        # Arms
        for ax in (-0.30, 0.30):
            glPushMatrix()
            glTranslatef(ax, 0.44, 0.0)
            glScalef(0.12, 0.26, 0.12)
            glColor3f(*_COL_BLACK)
            gluSphere(self._quadric, 1.0, 8, 8)
            glPopMatrix()

        # Legs with walk swing
        for side, lx in ((-1, -0.14), (1, 0.14)):
            swing = swing_amp * math.sin(self._walk_frame + side * math.pi)
            glPushMatrix()
            glTranslatef(lx, 0.15, 0.0)
            glRotatef(swing, 1.0, 0.0, 0.0)
            glPushMatrix()
            glTranslatef(0.0, -0.14, 0.0)
            glScalef(0.12, 0.28, 0.12)
            glColor3f(*_COL_BLACK)
            gluSphere(self._quadric, 1.0, 8, 8)
            glPopMatrix()
            glPopMatrix()

        glPopMatrix()  # panda

    # ── Movement / tick ───────────────────────────────────────────────────────

    def _tick(self) -> None:
        self._torch_t += 0.05

        # Resolve movement from held keys
        dx = dz = 0.0
        yaw_rad = math.radians(self._cam_yaw)
        # Forward / backward
        fwd_x = math.sin(yaw_rad)
        fwd_z = math.cos(yaw_rad)
        # Strafe
        str_x = math.cos(yaw_rad)
        str_z = -math.sin(yaw_rad)

        if Qt.Key.Key_W in self._keys or Qt.Key.Key_Up in self._keys:
            dx += fwd_x * _MOVE_SPEED
            dz += fwd_z * _MOVE_SPEED
        if Qt.Key.Key_S in self._keys or Qt.Key.Key_Down in self._keys:
            dx -= fwd_x * _MOVE_SPEED
            dz -= fwd_z * _MOVE_SPEED
        if Qt.Key.Key_A in self._keys or Qt.Key.Key_Left in self._keys:
            dx -= str_x * _MOVE_SPEED
            dz -= str_z * _MOVE_SPEED
        if Qt.Key.Key_D in self._keys or Qt.Key.Key_Right in self._keys:
            dx += str_x * _MOVE_SPEED
            dz += str_z * _MOVE_SPEED
        if Qt.Key.Key_Q in self._keys:
            self._cam_yaw -= 2.0
        if Qt.Key.Key_E in self._keys:
            self._cam_yaw += 2.0

        self._is_walking = (dx != 0.0 or dz != 0.0)
        if self._is_walking:
            self._walk_frame += 0.15
            # Slide along walls (try X then Z separately)
            new_x = self._cam_x + dx
            new_z = self._cam_z + dz
            margin = _COLLISION_MARGIN
            if not self._is_wall(new_x, self._cam_z) and not self._is_wall(new_x - margin, self._cam_z) and not self._is_wall(new_x + margin, self._cam_z):
                self._cam_x = new_x
            if not self._is_wall(self._cam_x, new_z) and not self._is_wall(self._cam_x, new_z - margin) and not self._is_wall(self._cam_x, new_z + margin):
                self._cam_z = new_z

            # Check stairs
            self._check_stairs()

        if self._hud_timer > 0:
            self._hud_timer -= 1

        self.update()

    def _check_stairs(self) -> None:
        """Check if player is standing on stairs and advance floor."""
        if self._dungeon is None:
            return
        try:
            fl = self._dungeon.dungeon.get_floor(self._floor_idx)
            if fl is None:
                return
            col = int(self._cam_x / _TILE)
            row = int(self._cam_z / _TILE)
            if (col, row) in fl.stairs_down:
                next_floor = self._floor_idx + 1
                if next_floor < len(self._dungeon.dungeon.floors):
                    self._floor_idx = next_floor
                    self._place_player_at_start()
                    self._show_hud(f"⬇ Floor {next_floor + 1}")
                    self.floor_advanced.emit(next_floor)
            elif (col, row) in fl.stairs_up and self._floor_idx > 0:
                next_floor = self._floor_idx - 1
                self._floor_idx = next_floor
                self._place_player_at_start()
                self._show_hud(f"⬆ Floor {next_floor + 1}")
                self.floor_advanced.emit(next_floor)
        except Exception:
            pass

    def _show_hud(self, msg: str, frames: int = 120) -> None:
        self._hud_msg = msg
        self._hud_timer = frames

    # ── Input ─────────────────────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        self._keys.add(event.key())

    def keyReleaseEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        self._keys.discard(event.key())

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        self._last_mouse = event.position()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if self._last_mouse is not None and event.buttons() & Qt.MouseButton.LeftButton:
            pos = event.position()
            dx = pos.x() - self._last_mouse.x()
            dy = pos.y() - self._last_mouse.y()
            self._cam_yaw += dx * 0.3
            self._cam_pitch = max(-60.0, min(30.0, self._cam_pitch - dy * 0.3))
            self._last_mouse = pos

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        self._last_mouse = None

    # ── HUD overlay ───────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """QOpenGLWidget calls paintGL automatically; paintEvent is for 2-D overlay."""
        super().paintEvent(event)
        if self._hud_timer > 0:
            try:
                p = QPainter(self)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                alpha = min(255, self._hud_timer * 4)
                p.setFont(QFont("Arial", 18, QFont.Weight.Bold))
                p.setPen(QColor(255, 220, 80, alpha))
                p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._hud_msg)
                p.end()
            except Exception:
                pass


# ── Public container widget ───────────────────────────────────────────────────

class Dungeon3DWidget(QWidget if _QT else object):  # type: ignore[misc]
    """
    Container that wraps _Dungeon3DGL with a HUD bar and Q/E rotation hints.
    Falls back to a styled QLabel when OpenGL is unavailable.
    """

    # Emitted when player advances to the next floor
    floor_advanced = pyqtSignal(int)

    def __init__(self, dungeon=None, parent=None, tooltip_manager=None):
        if not _QT:
            raise ImportError("PyQt6 required for Dungeon3DWidget")
        super().__init__(parent)
        self._tooltip_mgr = tooltip_manager
        self._gl_widget: Optional[_Dungeon3DGL] = None
        self._setup_ui(dungeon)

    def _setup_ui(self, dungeon) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if _GL:
            try:
                self._gl_widget = _Dungeon3DGL(dungeon, self)
                self._gl_widget.floor_advanced.connect(self.floor_advanced)
                layout.addWidget(self._gl_widget, stretch=1)

                # HUD bar
                hud = QWidget()
                hud.setFixedHeight(36)
                hud.setStyleSheet("background:#12090a;")
                hud_row = QHBoxLayout(hud)
                hud_row.setContentsMargins(8, 0, 8, 0)
                hud_row.addWidget(QLabel("🐼 Dungeon Adventure"))
                hud_row.addStretch()
                tip = QLabel("WASD / Arrows: move  |  Q/E: turn  |  Mouse-drag: look")
                tip.setStyleSheet("color:#888;font-size:10px;")
                hud_row.addWidget(tip)
                layout.addWidget(hud)
                return
            except Exception as exc:
                logger.warning(f"Dungeon3DWidget GL init failed: {exc}")
                self._gl_widget = None

        # Fallback
        lbl = QLabel(
            "⚔️ 3-D Dungeon\n\n"
            "PyOpenGL is required for 3-D dungeon rendering.\n\n"
            "Install with:\n    pip install PyOpenGL PyOpenGL_accelerate\n\n"
            "The dungeon adventure is fully playable with the 2-D view on the ⚔️ Adventure tab."
        )
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            "background:#12090a; color:#aaaaaa; font-size:12px; padding:24px;"
        )
        layout.addWidget(lbl)

    def set_dungeon(self, dungeon) -> None:
        if self._gl_widget is not None:
            self._gl_widget.set_dungeon(dungeon)

    def set_floor(self, floor_idx: int) -> None:
        if self._gl_widget is not None:
            self._gl_widget.set_floor(floor_idx)

    def is_gl_available(self) -> bool:
        return self._gl_widget is not None
