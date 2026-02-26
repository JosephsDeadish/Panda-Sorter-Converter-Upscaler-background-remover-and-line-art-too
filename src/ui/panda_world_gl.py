"""
panda_world_gl.py
─────────────────
3-D outside world the panda explores.

Scene layout (top-down, Z axis = depth, X = left/right)
  Panda's house (back-left), pathway, street with a car, shop front (back-right)
  Otter shopkeeper inside the shop (visible through window).

Signals
    destination_selected(str)  – 'home' | 'shop' | 'park'
    otter_clicked()            – user clicked on the otter → open shop panel
    back_to_bedroom()          – back button pressed
"""
from __future__ import annotations

import math
import random
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

# ── Optional PyQt6 / OpenGL imports ──────────────────────────────────────────
try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QColorDialog
    from PyQt6.QtCore import pyqtSignal, QTimer, Qt
    from PyQt6.QtGui import QColor, QSurfaceFormat
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False

try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    QOGL_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    QOGL_AVAILABLE = False

# Disable C accelerate BEFORE importing OpenGL.GL so pure-Python mode is used.
try:
    import OpenGL as _ogl_pre; _ogl_pre.USE_ACCELERATE = False
except Exception:
    pass

try:
    from OpenGL.GL import (
        glClearColor, glEnable, glDisable, GL_DEPTH_TEST, GL_LIGHTING,
        GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_BLEND, GL_COLOR_MATERIAL,
        glLightfv, glLightf, GL_POSITION, GL_DIFFUSE, GL_SPECULAR,
        GL_AMBIENT, GL_AMBIENT_AND_DIFFUSE, GL_SHININESS, GL_FRONT,
        glMaterialfv, glMaterialf, GL_FRONT_AND_BACK,
        GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, glBlendFunc,
        glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
        glMatrixMode, GL_PROJECTION, GL_MODELVIEW,
        glLoadIdentity, glViewport, glPushMatrix, glPopMatrix,
        glTranslatef, glRotatef, glScalef, glColor3f, glColor4f,
        glBegin, glEnd, glVertex3f, glNormal3f,
        GL_QUADS, GL_TRIANGLES, GL_LINES, GL_LINE_LOOP, GL_LINE_STRIP, GL_POINTS,
        glLineWidth, glPointSize, glShadeModel, GL_SMOOTH,
        GL_MULTISAMPLE, GL_LINE_SMOOTH, glHint, GL_LINE_SMOOTH_HINT, GL_NICEST,
        GL_DEPTH_COMPONENT,
    )
    from OpenGL.GLU import gluPerspective, gluNewQuadric, gluQuadricNormals
    from OpenGL.GLU import GLU_SMOOTH, gluSphere, gluCylinder, gluDisk, gluDeleteQuadric
    GL_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    GL_AVAILABLE = False

# Set default GL surface format at module load time if Qt is available.
# This ensures CompatibilityProfile (legacy GL) is requested before any
# QOpenGLWidget in this module is instantiated.
if PYQT_AVAILABLE and QOGL_AVAILABLE:
    try:
        import os as _os_world
        _os_world.environ.setdefault('QT_OPENGL', 'desktop')  # force native GL, not ANGLE
        _wfmt = QSurfaceFormat()
        _wfmt.setVersion(2, 1)
        _wfmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
        _wfmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)  # desktop GL
        _wfmt.setSamples(4)
        _wfmt.setDepthBufferSize(24)
        QSurfaceFormat.setDefaultFormat(_wfmt)
    except Exception:
        pass

# ── Colours ───────────────────────────────────────────────────────────────────
_SKY    = (0.53, 0.81, 0.92)
_GRASS  = (0.35, 0.65, 0.28)
_PATH   = (0.72, 0.68, 0.58)
_ROAD   = (0.32, 0.32, 0.32)
_HOUSE  = (0.88, 0.82, 0.72)
_ROOF   = (0.60, 0.35, 0.25)
_SHOP   = (0.92, 0.88, 0.80)
_SHOPRF = (0.08, 0.52, 0.52)   # Livy's turquoise shop roof
_CAR_R  = (0.80, 0.15, 0.15)
_CAR_W  = (0.95, 0.95, 0.95)
# Livy the otter — layered fur colours
_OTTER_BACK  = (0.52, 0.38, 0.22)   # darker dorsal fur
_OTTER_SIDE  = (0.64, 0.50, 0.33)   # mid fur
_OTTER_BELLY = (0.88, 0.78, 0.60)   # light cream belly
_OTTER_SNOUT = (0.80, 0.68, 0.50)   # muzzle pad
_OTTER_NOSE  = (0.18, 0.12, 0.12)   # dark nose
_OTTER_PAWS  = (0.46, 0.33, 0.18)   # darker paw pads
# Livy's turquoise favourite colour
_LIVY_TURQ   = (0.08, 0.72, 0.72)   # apron / scarf / eyes
_LIVY_TURQ_D = (0.04, 0.52, 0.55)   # darker turquoise trim
_GOLD        = (0.85, 0.72, 0.12)
_WOOD        = (0.55, 0.38, 0.20)
_SIGN        = (0.95, 0.88, 0.55)
# Shop name displayed on sign
_SHOP_NAME   = "Cosmic Otter Supply Co."

# ── Named screen-position offsets for otter tooltip placement
OTTER_SCREEN_OFFSET_X = 60
OTTER_SCREEN_OFFSET_Y = -40

# ── Otter animation tuning constants ─────────────────────────────────────────
# Breathing: sine frequency (radians/frame at ~30fps ≈ 0.30 Hz) and amplitude
# (±2.2% X/Z torso scale, subtle but clearly visible).
_OTTER_BREATH_FREQ  = 0.019   # ~0.30 Hz at 33ms/tick
_OTTER_BREATH_AMP   = 0.022   # ±2.2% scale pulse
# Probability that a new look-event aims at a random angle (vs. back at center)
_OTTER_LOOK_RANDOM_PROB = 0.70

# ── Hit-test regions (world x/z bounding box, y ignored) ─────────────────────
_CLICK_REGIONS = {
    'car':      (-3.5, -1.5, -3.0, -0.5),   # (x_min, x_max, z_min, z_max)
    'shop':     ( 2.0,  6.0, -5.5, -2.0),
    'otter':    ( 3.5,  5.5, -5.0, -3.5),
    'home':     (-6.0, -2.0, -5.5, -2.0),
    'park_btn': (-1.5,  1.5,  3.0,  5.0),
}


class PandaWorldGL(
    (QOpenGLWidget if QOGL_AVAILABLE else (QWidget if PYQT_AVAILABLE else object))
):
    """3-D outside world the panda can visit."""

    if PYQT_AVAILABLE:
        destination_selected = pyqtSignal(str)
        otter_clicked        = pyqtSignal()
        back_to_bedroom      = pyqtSignal()
        gl_failed            = pyqtSignal(str)

    def __init__(self, parent=None):
        if not PYQT_AVAILABLE:
            return
        super().__init__(parent)
        # Request OpenGL 2.1 CompatibilityProfile so all legacy GL functions
        # (glShadeModel, glBegin/glEnd, glLightfv, etc.) remain available.
        # Without CompatibilityProfile, strict drivers issue GL_INVALID_OPERATION
        # for every fixed-function call, causing initializeGL to fail and the
        # 2D fallback to appear instead of the 3D world.
        if QOGL_AVAILABLE and PYQT_AVAILABLE:
            _fmt = QSurfaceFormat()
            _fmt.setVersion(2, 1)
            _fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
            _fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)  # native desktop GL
            _fmt.setSamples(4)
            _fmt.setDepthBufferSize(24)
            _fmt.setStencilBufferSize(8)
            self.setFormat(_fmt)

        self._gl_ready = False
        self._frame    = 0
        # Car animation
        self._car_bob   = 0.0
        self._car_color = list(_CAR_R)  # mutable — changed by set_car_color()
        self._hover     = ''    # region currently under cursor
        # Livy the otter animation state
        self._otter_blink      = 180    # countdown frames to next blink
        self._otter_eye_close  = 0      # frames to keep eyes shut
        self._otter_happy_t    = 0      # turquoise flash frames when clicked
        self._otter_wave_t     = 0      # arm-wave countdown
        self._otter_head_bob   = 0.0    # idle head-bob phase
        self._otter_tail_angle = 0.0    # tail sway angle
        self._otter_shuffle_t  = 0      # counter-shuffle animation timer
        self._otter_look_x     = 0.0    # current head-turn angle (eased)
        self._otter_look_tgt   = 0.0    # target look angle for smooth blending
        self._otter_look_phase = 0      # countdown to next random look

        self.setMinimumSize(400, 300)
        if PYQT_AVAILABLE:
            self.setMouseTracking(True)

        if QOGL_AVAILABLE and GL_AVAILABLE:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._tick)
            self._timer.start(33)

    # ── Qt GL lifecycle ───────────────────────────────────────────────────────
    def initializeGL(self):
        if not GL_AVAILABLE:
            return
        try:
            glClearColor(*_SKY, 1.0)
            glEnable(GL_DEPTH_TEST)
            try:
                glShadeModel(GL_SMOOTH)
            except Exception:
                pass  # CompatibilityProfile only
            try:
                glEnable(GL_MULTISAMPLE)
            except Exception:
                pass
            try:
                glEnable(GL_LINE_SMOOTH)
                glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
            except Exception:
                pass
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_LIGHT1)
            glEnable(GL_COLOR_MATERIAL)

            glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 5.0, 1.0])
            glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.35, 0.33, 0.30, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.85, 0.82, 0.78, 1.0])
            glLightfv(GL_LIGHT0, GL_SPECULAR, [0.4,  0.4,  0.3,  1.0])
            glLightfv(GL_LIGHT1, GL_POSITION, [-4.0, 6.0, -2.0, 1.0])
            glLightfv(GL_LIGHT1, GL_AMBIENT,  [0.08, 0.08, 0.10, 1.0])
            glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.25, 0.30, 0.40, 1.0])
            # LIGHT2 — warm rim/back light to bring out fur edges
            glEnable(GL_LIGHT2)
            glLightfv(GL_LIGHT2, GL_POSITION, [0.0, 8.0, -6.0, 1.0])
            glLightfv(GL_LIGHT2, GL_AMBIENT,  [0.0,  0.0,  0.0,  1.0])
            glLightfv(GL_LIGHT2, GL_DIFFUSE,  [0.12, 0.14, 0.16, 1.0])
            glLightfv(GL_LIGHT2, GL_SPECULAR, [0.05, 0.05, 0.06, 1.0])

            # Probe fixed-function matrix mode (CompatibilityProfile check)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            self._gl_ready = True
        except Exception as e:
            self._gl_ready = False
            if PYQT_AVAILABLE:
                self.gl_failed.emit(str(e))

    def resizeGL(self, w: int, h: int):
        if not GL_AVAILABLE or not self._gl_ready:
            return
        try:
            glViewport(0, 0, max(1, w), max(1, h))
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(50.0, w / max(1, h), 0.1, 60.0)
            glMatrixMode(GL_MODELVIEW)
        except Exception:
            pass

    def paintGL(self):
        if not GL_AVAILABLE or not self._gl_ready:
            return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        # Camera: slightly elevated, looking into the scene
        glTranslatef(0.0, -2.5, -10.0)
        glRotatef(18.0, 1.0, 0.0, 0.0)

        self._draw_world()

    # ── Animation tick ────────────────────────────────────────────────────────
    def _tick(self):
        self._frame += 1
        # Car gentle suspension bob
        self._car_bob = math.sin(self._frame * 0.04) * 0.02

        # Livy blink cycle
        if self._otter_blink <= 0:
            self._otter_blink     = random.randint(100, 280)
            self._otter_eye_close = 4
        else:
            self._otter_blink -= 1
        if self._otter_eye_close > 0:
            self._otter_eye_close -= 1

        # Livy happy flash countdown
        if self._otter_happy_t > 0:
            self._otter_happy_t -= 1

        # Livy wave countdown
        if self._otter_wave_t > 0:
            self._otter_wave_t -= 1

        # Livy idle head-bob (smooth sine)
        self._otter_head_bob = math.sin(self._frame * 0.025) * 4.0

        # Livy tail sway
        self._otter_tail_angle = math.sin(self._frame * 0.04) * 18.0

        # Livy random look-around — smooth exponential blend toward target
        if self._otter_look_phase <= 0:
            # 30 % of the time glance back at center (player); otherwise look around
            self._otter_look_tgt = (
                random.uniform(-14.0, 14.0) if random.random() < _OTTER_LOOK_RANDOM_PROB else 0.0
            )
            self._otter_look_phase = random.randint(80, 200)
        else:
            self._otter_look_phase -= 1
        # Smooth approach toward target every tick (never snaps)
        self._otter_look_x += (self._otter_look_tgt - self._otter_look_x) * 0.07

        # Livy counter-shuffle (occasional item rearrange)
        if self._otter_shuffle_t > 0:
            self._otter_shuffle_t -= 1
        elif random.random() < 0.003:
            self._otter_shuffle_t = random.randint(20, 50)

        if QOGL_AVAILABLE:
            self.update()

    # ── World drawing ─────────────────────────────────────────────────────────
    def _draw_world(self):
        self._draw_ground()
        self._draw_sky_objects()
        self._draw_panda_house()
        self._draw_road()
        self._draw_car()
        self._draw_shop()
        self._draw_park_area()
        self._draw_trees()
        self._draw_hover_highlights()

    def _draw_ground(self):
        glDisable(GL_LIGHTING)
        glColor3f(*_GRASS)
        glBegin(GL_QUADS)
        glVertex3f(-15.0, 0.0, -12.0)
        glVertex3f( 15.0, 0.0, -12.0)
        glVertex3f( 15.0, 0.0,  10.0)
        glVertex3f(-15.0, 0.0,  10.0)
        glEnd()
        # Pathway from house to shop (gravel strip)
        glColor3f(*_PATH)
        glBegin(GL_QUADS)
        glVertex3f(-1.2, 0.01, -5.5)
        glVertex3f( 1.2, 0.01, -5.5)
        glVertex3f( 1.2, 0.01,  2.0)
        glVertex3f(-1.2, 0.01,  2.0)
        glEnd()
        glEnable(GL_LIGHTING)   # restore after all unlit ground drawing

    def _draw_sky_objects(self):
        """Clouds + sun."""
        glDisable(GL_LIGHTING)
        # Sun
        glColor3f(1.0, 0.92, 0.30)
        glPushMatrix()
        glTranslatef(8.0, 7.0, -8.0)
        self._sphere(0.6, 10, 10)
        glPopMatrix()
        # Clouds (simple white blobs)
        glColor4f(1.0, 1.0, 1.0, 0.8)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        for cx, cy, cz in [(-5.0, 6.5, -9.0), (3.0, 7.0, -8.5), (-1.0, 7.5, -10.0)]:
            glPushMatrix()
            glTranslatef(cx, cy, cz)
            self._sphere(0.55, 8, 8)
            glTranslatef(0.55, 0.0, 0.0)
            self._sphere(0.40, 8, 8)
            glTranslatef(-1.1, 0.0, 0.0)
            self._sphere(0.42, 8, 8)
            glPopMatrix()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _draw_panda_house(self):
        """A cute cottage — panda's home visible on the left."""
        glEnable(GL_LIGHTING)
        # Walls
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_HOUSE, 1.0])
        self._box(-6.5, 0.0, -5.5, -2.5, 2.8, -2.0)
        # Roof (triangle prism) using quads
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_ROOF, 1.0])
        self._box(-6.8, 2.8, -5.8, -2.2, 3.0, -1.7)   # roof base plate
        # Gable triangles
        glDisable(GL_LIGHTING)
        glColor3f(*_ROOF)
        for z_face in [-5.8, -1.7]:
            glBegin(GL_TRIANGLES)
            glVertex3f(-6.8, 3.0, z_face)
            glVertex3f(-2.2, 3.0, z_face)
            glVertex3f(-4.5, 4.5, z_face)
            glEnd()
        # Roof slopes
        glBegin(GL_QUADS)
        glVertex3f(-6.8, 3.0, -5.8); glVertex3f(-4.5, 4.5, -5.8)
        glVertex3f(-4.5, 4.5, -1.7); glVertex3f(-6.8, 3.0, -1.7)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(-2.2, 3.0, -5.8); glVertex3f(-4.5, 4.5, -5.8)
        glVertex3f(-4.5, 4.5, -1.7); glVertex3f(-2.2, 3.0, -1.7)
        glEnd()
        glEnable(GL_LIGHTING)
        # Front door
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_WOOD, 1.0])
        self._box(-5.0, 0.0, -2.05, -4.0, 2.0, -1.95)
        # Windows
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.55, 0.75, 0.90, 0.6)
        self._box(-6.2, 0.8, -2.05, -5.4, 1.8, -1.95)
        self._box(-3.6, 0.8, -2.05, -2.8, 1.8, -1.95)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        # "Home" sign
        glDisable(GL_LIGHTING)
        glColor3f(*_SIGN)
        self._box(-5.2, 2.2, -2.05, -3.8, 2.6, -1.9)
        glEnable(GL_LIGHTING)

    def _draw_road(self):
        glDisable(GL_LIGHTING)
        glColor3f(*_ROAD)
        glBegin(GL_QUADS)
        glVertex3f(-10.0, 0.005, -1.8)
        glVertex3f( 10.0, 0.005, -1.8)
        glVertex3f( 10.0, 0.005,  1.0)
        glVertex3f(-10.0, 0.005,  1.0)
        glEnd()
        # Road centre dashes
        glColor3f(0.95, 0.85, 0.15)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        for x in range(-9, 10, 2):
            glVertex3f(float(x), 0.01, -0.4)
            glVertex3f(float(x + 1), 0.01, -0.4)
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    def _draw_car(self):
        """A small red car parked on the road."""
        glEnable(GL_LIGHTING)
        y = self._car_bob
        glPushMatrix()
        glTranslatef(-2.5, y, -0.5)

        # Body
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*self._car_color, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR,            [0.6, 0.6, 0.6, 1.0])
        glMaterialf (GL_FRONT, GL_SHININESS, 48.0)
        self._box(-0.9, 0.3, -0.45,  0.9, 0.9,  0.45)
        # Cabin
        _cab = [max(0.0, c * 0.80) for c in self._car_color]
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_cab, 1.0])
        self._box(-0.55, 0.9, -0.42,  0.55, 1.45,  0.42)
        # Windows
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.55, 0.80, 0.90, 0.65)
        self._box(-0.52, 0.93, -0.43,  0.52, 1.40, -0.41)  # front
        self._box(-0.52, 0.93,  0.41,  0.52, 1.40,  0.43)  # rear
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        # Wheels
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.12, 0.12, 0.12, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR,            [0.30, 0.30, 0.30, 1.0])
        glMaterialf (GL_FRONT, GL_SHININESS, 20.0)
        for wx, wz in [(-0.65, -0.48), (-0.65, 0.48), (0.65, -0.48), (0.65, 0.48)]:
            glPushMatrix()
            glTranslatef(wx, 0.3, wz)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            self._cylinder(0.28, 0.15, 12)
            glPopMatrix()
        # Headlights
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.95, 0.6)
        for hz in [-0.30, 0.30]:
            glPushMatrix()
            glTranslatef(-0.91, 0.55, hz)
            self._sphere(0.10, 8, 8)
            glPopMatrix()
        glEnable(GL_LIGHTING)

        glPopMatrix()

        # Hover highlight
        if self._hover == 'car':
            glDisable(GL_LIGHTING)
            glColor3f(1.0, 1.0, 0.2)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            for vx, vz in [(-3.4, -1.0), (-1.6, -1.0), (-1.6, 0.0), (-3.4, 0.0)]:
                glVertex3f(vx, 1.6, vz)
            glEnd()
            glLineWidth(1.0)
            glEnable(GL_LIGHTING)

    def _draw_shop(self):
        """Cosmic Otter Supply Co. — Livy's galactic shop."""
        glEnable(GL_LIGHTING)
        # ── Walls (warm cream) ────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_SHOP, 1.0])
        self._box(2.0, 0.0, -5.5,  6.5, 3.2, -2.0)
        # ── Roof (Livy's turquoise) ───────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_SHOPRF, 1.0])
        self._box(1.8, 3.2, -5.8,  6.8, 3.55, -1.7)
        # roof ridge
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_LIVY_TURQ_D, 1.0])
        self._box(1.7, 3.55, -5.9,  6.9, 3.70, -1.6)
        # ── Awning (turquoise stripes) ────────────────────────────────────────
        glDisable(GL_LIGHTING)
        for i in range(6):
            t = i / 5.0
            x0 = 1.8 + t * 5.0
            x1 = x0 + 5.0 / 5.0
            col = _LIVY_TURQ if i % 2 == 0 else _LIVY_TURQ_D
            glColor3f(*col)
            glBegin(GL_QUADS)
            glVertex3f(x0, 3.0, -2.0);  glVertex3f(x1, 3.0, -2.0)
            glVertex3f(x1, 2.45, -1.15); glVertex3f(x0, 2.45, -1.15)
            glEnd()
        # Awning fringe (tiny pendants)
        glColor3f(*_GOLD)
        glBegin(GL_LINES)
        for i in range(12):
            fx = 1.9 + i * (4.6 / 11.0)
            glVertex3f(fx, 2.45, -1.15)
            glVertex3f(fx, 2.22, -1.15)
        glEnd()
        glEnable(GL_LIGHTING)
        # ── Big glass window ──────────────────────────────────────────────────
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.55, 0.88, 0.90, 0.45)   # turquoise-tinted glass
        self._box(2.3, 0.3, -2.05, 6.2, 2.7, -1.95)
        # Window frame bars
        glColor4f(0.95, 0.95, 0.95, 0.95)
        self._box(4.22, 0.3, -2.06, 4.28, 2.7, -1.94)   # vertical centre bar
        self._box(2.3, 1.48, -2.06, 6.2, 1.54, -1.94)   # horizontal bar
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        # ── Wooden door ───────────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_WOOD, 1.0])
        self._box(3.85, 0.0, -2.07, 4.65, 2.15, -1.93)
        # door knob
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_GOLD, 1.0])
        glPushMatrix()
        glTranslatef(4.62, 1.05, -1.94)
        self._sphere(0.05, 6, 6)
        glPopMatrix()
        # ── Shop sign ─────────────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.12, 0.08, 0.20, 1.0])
        self._box(2.1, 3.5, -4.8, 6.4, 4.05, -4.45)
        # Sign stars (gold dots as decoration)
        glDisable(GL_LIGHTING)
        glColor3f(*_GOLD)
        glPointSize(4.0)
        glBegin(GL_POINTS)
        for sx, sz in [(2.4, -4.62), (2.9, -4.58), (5.8, -4.62), (6.1, -4.57),
                       (3.8, -4.72), (4.5, -4.68), (5.1, -4.72)]:
            glVertex3f(sx, 3.78, sz)
        glEnd()
        glPointSize(1.0)
        glEnable(GL_LIGHTING)
        # ── Counter ───────────────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_WOOD, 1.0])
        self._box(3.0, 0.0, -3.5, 5.4, 1.02, -2.2)
        # counter front panel
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.65, 0.45, 0.25, 1.0])
        self._box(3.0, 0.0, -2.22, 5.4, 1.02, -2.1)
        # items on counter
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_LIVY_TURQ, 1.0])
        glPushMatrix(); glTranslatef(3.4, 1.12, -2.9); self._sphere(0.12, 8, 8); glPopMatrix()
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_GOLD, 1.0])
        glPushMatrix(); glTranslatef(5.1, 1.12, -2.7); self._sphere(0.09, 6, 6); glPopMatrix()
        # ── Draw Livy ─────────────────────────────────────────────────────────
        self._draw_otter()

    def _draw_otter(self):
        """Livy — highly detailed, realistic animated otter shopkeeper.

        Livy is a cute girl otter running "Cosmic Otter Supply Co."
        Her favourite colour is turquoise.  Anatomically correct otter
        proportions: long flexible body, wide hips, narrow shoulders,
        flat muscular tail, webbed paws, round head with prominent whisker pad.
        """
        if not GL_AVAILABLE:
            return
        import math as _math

        glPushMatrix()
        glTranslatef(4.2, 0.0, -3.8)
        glRotatef(self._otter_look_x * 0.35, 0.0, 1.0, 0.0)

        t = self._frame
        head_bob = self._otter_head_bob   # ±4° from idle sine

        # ── Helper: set fur material ──────────────────────────────────────
        def _mat(col, alpha=1.0):
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*col, alpha])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [0.10, 0.09, 0.07, 1.0])
            glMaterialf(GL_FRONT, GL_SHININESS, 8.0)

        def _mat_shiny(col, spec=0.7, shin=60.0):
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*col, 1.0])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [spec, spec, spec * 0.9, 1.0])
            glMaterialf(GL_FRONT, GL_SHININESS, shin)

        # ── Tail — flat, muscular, tapered ───────────────────────────────
        glPushMatrix()
        glTranslatef(0.0, 0.90, -0.55)
        glRotatef(self._otter_tail_angle, 0.0, 0.0, 1.0)
        glRotatef(-30.0, 1.0, 0.0, 0.0)   # angle back and down
        _mat(_OTTER_BACK)
        # 4 segments: wide base tapering to flat tip
        for i, (ty, sx, sy, sz) in enumerate([
            (0.00, 0.42, 0.14, 0.28),   # base — wide, flat
            (0.24, 0.36, 0.11, 0.24),
            (0.46, 0.26, 0.08, 0.18),
            (0.64, 0.16, 0.055, 0.12),  # tip — narrow
        ]):
            glPushMatrix()
            glTranslatef(0.0, -ty, 0.0)
            glScalef(sx, sy, sz)
            self._sphere(1.0, 10, 8)
            glPopMatrix()
        # Dorsal darker stripe along tail
        _mat([max(0.0, c - 0.08) for c in _OTTER_BACK])
        for i, (ty, sx, sz) in enumerate([(0.0, 0.18, 0.10), (0.24, 0.14, 0.08), (0.46, 0.10, 0.06)]):
            glPushMatrix()
            glTranslatef(0.0, -ty, -0.02)
            glScalef(sx, 0.10, sz)
            self._sphere(1.0, 8, 6)
            glPopMatrix()
        glPopMatrix()

        # ── Hind legs ─────────────────────────────────────────────────────
        for fx in [-0.28, 0.28]:
            # Upper thigh
            _mat(_OTTER_SIDE)
            glPushMatrix()
            glTranslatef(fx, 0.55, 0.0)
            glScalef(0.52, 0.88, 0.58)
            self._sphere(0.30, 10, 10)
            glPopMatrix()
            # Lower leg
            glPushMatrix()
            glTranslatef(fx, 0.28, 0.08)
            glScalef(0.42, 0.72, 0.50)
            self._sphere(0.24, 10, 10)
            glPopMatrix()
            # Webbed foot (flat, wide)
            _mat(_OTTER_PAWS)
            glPushMatrix()
            glTranslatef(fx, 0.065, 0.24)
            glScalef(1.70, 0.22, 1.25)
            self._sphere(0.22, 10, 8)
            glPopMatrix()
            # Webbed toe bumps — 5 small rounded bumps across top of foot
            for ti in range(5):
                tx2 = (ti - 2.0) * 0.062
                glPushMatrix()
                glTranslatef(fx + tx2, 0.085, 0.34)
                glScalef(0.55, 0.35, 0.42)
                self._sphere(0.055, 7, 7)
                glPopMatrix()
            # Paw pad (pink)
            _mat([0.78, 0.50, 0.55])
            glPushMatrix()
            glTranslatef(fx, 0.058, 0.22)
            glScalef(0.95, 0.16, 0.65)
            self._sphere(0.18, 8, 8)
            glPopMatrix()
            _mat(_OTTER_SIDE)

        # ── Body ──────────────────────────────────────────────────────────
        # Subtle breathing: ±2% X/Z scale pulse on the torso (~0.3 Hz at 30fps)
        _breath = 1.0 + _math.sin(t * _OTTER_BREATH_FREQ) * _OTTER_BREATH_AMP
        # Lower torso — wide hips (otter body plan)
        _mat(_OTTER_SIDE)
        glPushMatrix()
        glTranslatef(0.0, 1.10, 0.0)
        glScalef(0.72 * _breath, 0.70, 0.58 * _breath)
        self._sphere(1.0, 14, 14)
        glPopMatrix()
        # Upper torso — slightly narrower, forward lean
        glPushMatrix()
        glTranslatef(0.0, 1.72, 0.06)
        glScalef(0.58 * _breath, 0.62, 0.52 * _breath)
        self._sphere(1.0, 14, 14)
        glPopMatrix()
        # Back dorsal — darker stripe
        _mat([max(0.0, c - 0.06) for c in _OTTER_BACK])
        glPushMatrix()
        glTranslatef(0.0, 1.38, -0.28)
        glScalef(0.40, 0.72, 0.22)
        self._sphere(1.0, 10, 10)
        glPopMatrix()
        # Belly cream patch
        _mat(_OTTER_BELLY)
        glPushMatrix()
        glTranslatef(0.0, 1.18, 0.34)
        glScalef(0.42, 0.60, 0.18)
        self._sphere(1.0, 12, 12)
        glPopMatrix()
        # Fur shells — 2 alpha-blended shells for fur depth
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_OTTER_SIDE, 0.18])
        glPushMatrix()
        glTranslatef(0.0, 1.10, 0.0)
        glScalef(0.76, 0.74, 0.62)
        self._sphere(1.0, 10, 10)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_OTTER_SIDE, 0.09])
        glPushMatrix()
        glTranslatef(0.0, 1.10, 0.0)
        glScalef(0.80, 0.78, 0.66)
        self._sphere(1.0, 8, 8)
        glPopMatrix()
        glDisable(GL_BLEND)

        # ── Turquoise apron ────────────────────────────────────────────────
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        _mat(_LIVY_TURQ, 0.92)
        # Apron bib
        glPushMatrix()
        glTranslatef(0.0, 1.52, 0.38)
        glScalef(0.38, 0.55, 0.10)
        self._sphere(1.0, 10, 10)
        glPopMatrix()
        # Apron skirt
        glPushMatrix()
        glTranslatef(0.0, 1.12, 0.38)
        glScalef(0.44, 0.48, 0.10)
        self._sphere(1.0, 10, 10)
        glPopMatrix()
        # Apron pocket (darker turquoise)
        _mat(_LIVY_TURQ_D, 0.95)
        glPushMatrix()
        glTranslatef(0.0, 1.00, 0.45)
        glScalef(0.18, 0.14, 0.07)
        self._sphere(1.0, 8, 8)
        glPopMatrix()
        # Gold star badge on apron bib
        _mat(_GOLD)
        glPushMatrix()
        glTranslatef(-0.20, 1.62, 0.44)
        self._sphere(0.052, 8, 8)
        glPopMatrix()
        # Small secondary star badge
        glPushMatrix()
        glTranslatef(0.15, 1.58, 0.43)
        self._sphere(0.032, 6, 6)
        glPopMatrix()
        glDisable(GL_BLEND)

        # ── Arms ──────────────────────────────────────────────────────────
        wave_bob = _math.sin(t * 0.08) * 8.0
        for ax, side in [(-0.56, 1.0), (0.56, -1.0)]:
            base_angle = -40.0 + wave_bob * side * 0.5
            if self._otter_wave_t > 0:
                phase = self._otter_wave_t / 90.0
                base_angle = -100.0 + _math.sin(t * 0.22) * 35.0 * side * (1.0 + phase)
            # Shoulder joint
            _mat(_OTTER_SIDE)
            glPushMatrix()
            glTranslatef(ax, 1.80, 0.04)
            glScalef(0.55, 0.55, 0.55)
            self._sphere(0.25, 10, 10)
            glPopMatrix()
            # Upper arm
            glPushMatrix()
            glTranslatef(ax, 1.80, 0.04)
            glRotatef(base_angle, 0.0, 0.0, 1.0)
            glPushMatrix()
            glTranslatef(0.0, -0.26, 0.0)
            glScalef(0.30, 0.48, 0.30)
            self._sphere(1.0, 10, 10)
            glPopMatrix()
            # Elbow
            glTranslatef(0.0, -0.50, 0.0)
            _mat([min(1.0, c + 0.03) for c in _OTTER_SIDE])
            self._sphere(0.14, 8, 8)
            # Forearm
            _mat(_OTTER_SIDE)
            glRotatef(10.0 * side, 0.0, 0.0, 1.0)
            glPushMatrix()
            glTranslatef(0.0, -0.22, 0.0)
            glScalef(0.25, 0.42, 0.25)
            self._sphere(1.0, 10, 10)
            glPopMatrix()
            # Paw
            glTranslatef(0.0, -0.38, 0.0)
            _mat(_OTTER_PAWS)
            glScalef(1.40, 0.52, 1.30)
            self._sphere(0.15, 10, 8)
            # Webbed toe bumps on front paws
            for ti in range(4):
                tx3 = (ti - 1.5) * 0.055
                glPushMatrix()
                glTranslatef(tx3, 0.04, 0.07)
                glScalef(0.45, 0.32, 0.38)
                self._sphere(0.055, 7, 7)
                glPopMatrix()
            glPopMatrix()

        # ── Neck ──────────────────────────────────────────────────────────
        _mat(_OTTER_SIDE)
        glPushMatrix()
        glTranslatef(0.0, 2.24, 0.07)
        glScalef(0.38, 0.42, 0.38)
        self._sphere(1.0, 10, 10)
        glPopMatrix()
        # Turquoise scarf with bow
        _mat(_LIVY_TURQ)
        glPushMatrix()
        glTranslatef(0.0, 2.30, 0.06)
        glScalef(0.48, 0.13, 0.46)
        self._sphere(1.0, 10, 10)
        glPopMatrix()
        # Scarf bow (two lobes + knot)
        for bx, bsc in [(-0.22, (0.26, 0.16, 0.14)), (0.22, (0.26, 0.16, 0.14))]:
            glPushMatrix()
            glTranslatef(bx, 2.34, 0.36)
            glScalef(*bsc)
            self._sphere(1.0, 8, 8)
            glPopMatrix()
        _mat(_LIVY_TURQ_D)
        glPushMatrix()
        glTranslatef(0.0, 2.34, 0.38)
        self._sphere(0.06, 8, 8)
        glPopMatrix()

        # ── Head ──────────────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.0, 2.78, 0.06)
        glRotatef(head_bob, 1.0, 0.0, 0.0)
        glRotatef(self._otter_look_x * 0.25, 0.0, 1.0, 0.0)

        # Skull — wide, round forehead, slightly flattened sides
        _mat(_OTTER_BACK)
        glPushMatrix()
        glScalef(1.0, 0.95, 0.90)
        self._sphere(0.42, 16, 16)
        glPopMatrix()
        # Forehead lighter highlight
        _mat(_OTTER_SIDE)
        glPushMatrix()
        glTranslatef(0.0, 0.12, 0.26)
        glScalef(0.75, 0.52, 0.52)
        self._sphere(0.36, 12, 12)
        glPopMatrix()
        # Cheekbones — slight rounding at sides
        _mat(_OTTER_SIDE)
        for cx in [-0.24, 0.24]:
            glPushMatrix()
            glTranslatef(cx, -0.04, 0.28)
            glScalef(0.65, 0.52, 0.55)
            self._sphere(0.22, 10, 10)
            glPopMatrix()
        # Head fur shell
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_OTTER_BACK, 0.15])
        glPushMatrix()
        glScalef(1.04, 0.99, 0.94)
        self._sphere(0.42, 10, 10)
        glPopMatrix()
        glDisable(GL_BLEND)

        # ── Ears (small, rounded, close to head) ──────────────────────────
        _mat(_OTTER_BACK)
        for ex in [-0.32, 0.32]:
            glPushMatrix()
            glTranslatef(ex, 0.30, -0.12)
            glScalef(0.75, 0.90, 0.62)
            self._sphere(0.155, 10, 10)
            glPopMatrix()
            # Inner ear concha — warm pink
            _mat([0.88, 0.58, 0.62])
            glPushMatrix()
            glTranslatef(ex * 0.90, 0.30, -0.06)
            glScalef(0.48, 0.58, 0.30)
            self._sphere(0.125, 8, 8)
            glPopMatrix()
            # Ear canal depth dot
            _mat([0.18, 0.12, 0.14])
            glPushMatrix()
            glTranslatef(ex * 0.88, 0.28, -0.03)
            glScalef(0.28, 0.28, 0.18)
            self._sphere(0.075, 6, 6)
            glPopMatrix()
            _mat(_OTTER_BACK)

        # ── Snout — prominent otter muzzle ────────────────────────────────
        # Muzzle pad (rounded trapezoid shape)
        _mat(_OTTER_SNOUT)
        glPushMatrix()
        glTranslatef(0.0, -0.06, 0.36)
        glScalef(1.08, 0.75, 0.78)
        self._sphere(0.24, 12, 12)
        glPopMatrix()
        # Muzzle underside (cream)
        _mat(_OTTER_BELLY)
        glPushMatrix()
        glTranslatef(0.0, -0.20, 0.42)
        glScalef(0.88, 0.48, 0.58)
        self._sphere(0.20, 10, 10)
        glPopMatrix()
        # Whisker pad bumps — raised oval areas
        _mat(_OTTER_SNOUT)
        for wpx in [-0.12, 0.12]:
            glPushMatrix()
            glTranslatef(wpx, -0.06, 0.48)
            glScalef(0.62, 0.52, 0.35)
            self._sphere(0.14, 10, 10)
            glPopMatrix()
        # Lower jaw
        _mat(_OTTER_SNOUT)
        glPushMatrix()
        glTranslatef(0.0, -0.22, 0.38)
        glScalef(0.78, 0.38, 0.60)
        self._sphere(0.18, 10, 10)
        glPopMatrix()
        # Nose — dark, slightly heart-shaped
        _mat_shiny(_OTTER_NOSE, spec=0.85, shin=90.0)
        glPushMatrix()
        glTranslatef(0.0, 0.06, 0.57)
        glScalef(1.25, 0.82, 0.72)
        self._sphere(0.068, 10, 10)
        glPopMatrix()
        # Nostril dots
        _mat([0.08, 0.05, 0.05])
        for nx in [-0.028, 0.028]:
            glPushMatrix()
            glTranslatef(nx, 0.048, 0.610)
            glScalef(0.42, 0.38, 0.30)
            self._sphere(0.032, 7, 7)
            glPopMatrix()
        # Wet nose specular catch-light
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 1.0, 1.0)
        glPushMatrix()
        glTranslatef(0.012, 0.075, 0.622)
        self._sphere(0.010, 5, 5)
        glPopMatrix()
        glEnable(GL_LIGHTING)
        # Philtrum groove
        _mat([0.35, 0.22, 0.24])
        glPushMatrix()
        glTranslatef(0.0, -0.048, 0.565)
        glScalef(0.22, 0.75, 0.22)
        self._sphere(0.020, 6, 6)
        glPopMatrix()
        # Smile lines
        glDisable(GL_LIGHTING)
        glColor3f(*_OTTER_NOSE)
        glLineWidth(1.8)
        glBegin(GL_LINES)
        glVertex3f(-0.042, -0.14, 0.54);  glVertex3f(0.0, -0.185, 0.570)
        glVertex3f( 0.042, -0.14, 0.54);  glVertex3f(0.0, -0.185, 0.570)
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

        # ── Eyes — sclera + iris + pupil + specular ────────────────────────
        # Eye socket fur surround (dark ring)
        _mat([max(0.0, c - 0.10) for c in _OTTER_BACK])
        for ex in [-0.175, 0.175]:
            glPushMatrix()
            glTranslatef(ex, 0.11, 0.37)
            eye_sy = 0.15 if self._otter_eye_close > 2 else 1.0
            glScalef(1.0, eye_sy, 0.55)
            self._sphere(0.092, 12, 12)
            glPopMatrix()

        happy = self._otter_happy_t > 0
        for ex in [-0.175, 0.175]:
            eye_sy = 0.15 if self._otter_eye_close > 2 else 1.0
            # Sclera (white)
            glPushMatrix()
            glTranslatef(ex, 0.112, 0.415)
            glScalef(1.0, eye_sy, 1.0)
            _mat([0.98, 0.98, 0.98])
            self._sphere(0.068, 12, 12)
            glPopMatrix()
            # Iris (turquoise — Livy's signature colour; gold when happy/excited)
            iris_col = _LIVY_TURQ if not happy else _GOLD
            glPushMatrix()
            glTranslatef(ex, 0.112, 0.460)
            glScalef(1.0, eye_sy, 1.0)
            _mat(iris_col)
            self._sphere(0.050, 12, 12)
            glPopMatrix()
            # Limbal ring (dark edge of iris)
            _mat([0.04, 0.18, 0.20])
            glPushMatrix()
            glTranslatef(ex, 0.112, 0.455)
            glScalef(1.08, eye_sy, 1.08)
            self._sphere(0.050, 10, 10)
            glPopMatrix()
            # Pupil
            _mat([0.04, 0.04, 0.06])
            glPushMatrix()
            glTranslatef(ex, 0.112, 0.478)
            glScalef(1.0, eye_sy, 1.0)
            self._sphere(0.030, 10, 10)
            glPopMatrix()
            # Corneal specular highlight — turns off lighting for clean white dot
            glDisable(GL_LIGHTING)
            glColor3f(1.0, 1.0, 1.0)
            glPushMatrix()
            glTranslatef(ex + 0.022, 0.132, 0.488)
            glScalef(1.0, eye_sy, 1.0)
            self._sphere(0.014, 6, 6)
            glPopMatrix()
            # Secondary smaller highlight
            glPushMatrix()
            glTranslatef(ex - 0.010, 0.096, 0.484)
            self._sphere(0.007, 5, 5)
            glPopMatrix()
            glEnable(GL_LIGHTING)

        # ── Whiskers — 5 per side, varying lengths ────────────────────────
        glDisable(GL_LIGHTING)
        glLineWidth(1.5)
        glColor3f(0.92, 0.90, 0.85)
        glBegin(GL_LINES)
        for side, wx_base in [(-1.0, -0.26), (1.0, 0.26)]:
            for angle_deg, length in [(-14.0, 0.13), (-5.0, 0.15), (5.0, 0.16), (15.0, 0.14), (25.0, 0.10)]:
                rad = _math.radians(angle_deg)
                lx = _math.sin(rad) * length * side
                ly = _math.cos(rad) * length * 0.30
                glVertex3f(wx_base, -0.07, 0.44)
                glVertex3f(wx_base + lx, -0.07 + ly, 0.44 + length * 0.85)
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

        # ── Counter-shuffle sparkle effect ────────────────────────────────
        if self._otter_shuffle_t > 0:
            glDisable(GL_LIGHTING)
            glColor3f(*_LIVY_TURQ)
            glPointSize(3.5)
            glBegin(GL_POINTS)
            t2 = self._otter_shuffle_t / 50.0
            for i in range(6):
                px = -0.35 + i * 0.14
                py = 0.38 + _math.sin(t2 * _math.pi + i) * 0.09
                glVertex3f(px, py, 0.62)
            glEnd()
            glPointSize(1.0)
            glEnable(GL_LIGHTING)

        glPopMatrix()  # end head

        glPopMatrix()  # end otter world transform

        # ── Click / hover highlight (turquoise glow) ──────────────────────────
        if self._hover == 'otter' or self._otter_happy_t > 0:
            glDisable(GL_LIGHTING)
            glColor3f(*_LIVY_TURQ)
            glLineWidth(2.5)
            glPushMatrix()
            glTranslatef(4.2, 0.0, -3.8)
            glBegin(GL_LINE_LOOP)
            for vx, vz in [(-1.1, -0.8), (1.1, -0.8), (1.1, 0.8), (-1.1, 0.8)]:
                glVertex3f(vx, 3.4, vz)
            glEnd()
            if self._hover == 'otter':
                glColor3f(*_GOLD)
                glPointSize(5.0)
                glBegin(GL_POINTS)
                for sx, sy in [(-0.8, 3.55), (0.0, 3.65), (0.8, 3.55)]:
                    glVertex3f(sx, sy, 0.0)
                glEnd()
                glPointSize(1.0)
            glPopMatrix()
            glLineWidth(1.0)
            glEnable(GL_LIGHTING)

    def _draw_park_area(self):
        """Bench, pond, flowers, play equipment for the park destination."""
        glEnable(GL_LIGHTING)

        # ── Bench ──────────────────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_WOOD, 1.0])
        self._box(-0.8, 0.6, 4.0,  0.8, 0.7, 4.6)   # seat
        self._box(-0.8, 0.0, 4.0, -0.7, 0.6, 4.15)  # left leg
        self._box( 0.7, 0.0, 4.0,  0.8, 0.6, 4.15)  # right leg
        self._box(-0.8, 0.7, 4.0,  0.8, 1.1, 4.1)   # back-rest

        # ── Pond ───────────────────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.15, 0.55, 0.85, 0.85])
        # Flat ellipse approximated with a scaled cylinder (pancake shape)
        glPushMatrix()
        glTranslatef(-3.5, 0.01, 5.5)
        glScalef(1.6, 0.05, 1.1)
        self._sphere(1.0, 12, 6)
        glPopMatrix()
        # Pond rim (lighter grey stones)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.65, 0.65, 0.65, 1.0])
        for ang in range(0, 360, 45):
            rx = math.cos(math.radians(ang)) * 1.6
            rz = math.sin(math.radians(ang)) * 1.1
            glPushMatrix()
            glTranslatef(-3.5 + rx, 0.05, 5.5 + rz)
            self._sphere(0.18, 6, 4)
            glPopMatrix()

        # ── Flowers ────────────────────────────────────────────────────────────
        _FLOWER_POSITIONS = [
            (-2.0, 3.8), (-2.3, 4.5), (-1.6, 4.2),
            (1.8, 3.9),  (2.1, 4.6),  (1.5, 4.1),
            (-4.0, 4.8), (3.5, 4.5),
        ]
        for fx, fz in _FLOWER_POSITIONS:
            # Stem
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.25, 0.65, 0.25, 1.0])
            glPushMatrix()
            glTranslatef(fx, 0.0, fz)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            self._cylinder(0.03, 0.45, 5)
            glPopMatrix()
            # Petals (pink/yellow alternating)
            col = [1.0, 0.4, 0.7, 1.0] if int(fx * 10) % 2 == 0 else [1.0, 0.9, 0.2, 1.0]
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, col)
            glPushMatrix()
            glTranslatef(fx, 0.45, fz)
            self._sphere(0.12, 6, 5)
            glPopMatrix()

        # ── Play equipment: swing frame ────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.7, 0.35, 0.1, 1.0])
        # Left post
        glPushMatrix()
        glTranslatef(2.5, 0.0, 6.5)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        self._cylinder(0.08, 1.8, 6)
        glPopMatrix()
        # Right post
        glPushMatrix()
        glTranslatef(3.5, 0.0, 6.5)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        self._cylinder(0.08, 1.8, 6)
        glPopMatrix()
        # Top bar
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.6, 0.3, 0.1, 1.0])
        self._box(2.45, 1.75, 6.45,  3.55, 1.85, 6.55)
        # Swing seat
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_WOOD, 1.0])
        self._box(2.8, 0.8, 6.4,  3.2, 0.9, 6.6)
        # Swing chains (thin vertical rods)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.7, 0.7, 0.7, 1.0])
        self._box(2.82, 0.9, 6.48,  2.86, 1.78, 6.52)
        self._box(3.14, 0.9, 6.48,  3.18, 1.78, 6.52)

        # ── Park sign ─────────────────────────────────────────────────────────
        # Post
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_WOOD, 1.0])
        self._box(-0.06, 0.0, 4.1,  0.06, 1.3, 4.2)
        # Sign board
        glDisable(GL_LIGHTING)
        glColor3f(*_SIGN)
        self._box(-0.55, 1.3, 4.1,  0.55, 1.7, 4.2)
        glEnable(GL_LIGHTING)

        # ── Grass patch (darker green squares) ────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.18, 0.52, 0.18, 1.0])
        self._box(-5.0, 0.0, 3.0,   5.0, 0.01, 8.0)  # park grass zone


    def _draw_trees(self):
        """A few simple GL trees."""
        for tx, tz in [(-1.8, -5.0), (1.5, -4.8), (-5.5, 0.5), (7.0, -3.0)]:
            glPushMatrix()
            glTranslatef(tx, 0.0, tz)
            # Trunk
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.45, 0.28, 0.15, 1.0])
            glPushMatrix()
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            self._cylinder(0.15, 1.2, 8)
            glPopMatrix()
            # Canopy
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.22, 0.55, 0.22, 1.0])
            glPushMatrix()
            glTranslatef(0.0, 1.8, 0.0)
            self._sphere(0.7, 10, 10)
            glPopMatrix()
            glPopMatrix()

    def _draw_hover_highlights(self):
        """Draw GL line-loop outlines for whichever region is hovered.

        Car and otter highlights are drawn inline (inside their own draw methods)
        so we only need to cover the remaining three regions here.
        """
        if self._hover not in ('home', 'shop', 'park_btn'):
            return

        glDisable(GL_LIGHTING)
        glColor3f(1.0, 1.0, 0.2)
        glLineWidth(2.5)

        if self._hover == 'home':
            # Outline around the house façade (west side)
            glBegin(GL_LINE_LOOP)
            for vx, vz in [(-5.8, -5.4), (-2.2, -5.4), (-2.2, -2.1), (-5.8, -2.1)]:
                glVertex3f(vx, 3.5, vz)
            glEnd()

        elif self._hover == 'shop':
            # Outline around the shop front (east side)
            glBegin(GL_LINE_LOOP)
            for vx, vz in [(2.1, -5.4), (5.9, -5.4), (5.9, -2.1), (2.1, -2.1)]:
                glVertex3f(vx, 3.5, vz)
            glEnd()

        elif self._hover == 'park_btn':
            # Outline around the park sign / far-back area
            glBegin(GL_LINE_LOOP)
            for vx, vz in [(-1.4, 3.1), (1.4, 3.1), (1.4, 4.9), (-1.4, 4.9)]:
                glVertex3f(vx, 2.0, vz)
            glEnd()

        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    # ── Mouse interaction ─────────────────────────────────────────────────────
    def mouseMoveEvent(self, event):
        if PYQT_AVAILABLE:
            wx, wz = self._screen_to_ground(event.position().x(), event.position().y())
            self._hover = self._hit_region(wx, wz)
            try:
                self.setCursor(Qt.CursorShape.PointingHandCursor if self._hover else Qt.CursorShape.ArrowCursor)
            except Exception:
                pass
            if QOGL_AVAILABLE:
                self.update()  # repaint immediately so hover glow appears without waiting for _tick

    def mousePressEvent(self, event):
        if not PYQT_AVAILABLE:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        wx, wz = self._screen_to_ground(event.position().x(), event.position().y())
        region = self._hit_region(wx, wz)
        if region == 'car':
            self._show_destination_picker()
        elif region in ('shop', 'otter'):
            self._otter_happy_t = 80
            self._otter_wave_t  = 90   # Livy waves when clicked
            self.otter_clicked.emit()
        elif region == 'home':
            self.back_to_bedroom.emit()
        elif region == 'park_btn':
            self.destination_selected.emit('park')

    def get_car_color(self) -> list:
        """Return current car colour as [r, g, b] float list."""
        return list(self._car_color)

    def set_car_color(self, r: float, g: float, b: float) -> None:
        """Change the car body colour (0–1 float components). Triggers repaint."""
        self._car_color = [float(r), float(g), float(b)]
        self.update()

    def _show_destination_picker(self) -> None:
        """Show a small dialog letting the user choose where to drive."""
        if not PYQT_AVAILABLE:
            self.destination_selected.emit('shop')
            return
        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel as _QLabel
            dlg = QDialog(self)
            dlg.setWindowTitle("🚗 Where to?")
            dlg.setModal(True)
            dlg.setFixedSize(240, 180)
            dlg.setStyleSheet(
                "QDialog{background:#1a2a3a;color:#ddddff;}"
                "QPushButton{background:#2a3a5a;color:#eeeeff;border:1px solid #445;border-radius:6px;"
                "padding:6px 14px;font-size:13px;}"
                "QPushButton:hover{background:#3a4a7a;}"
            )
            vbox = QVBoxLayout(dlg)
            vbox.addWidget(_QLabel("🐼 Where shall we go?", dlg))
            for dest, label in (('shop', '🛒  Otter Shop'), ('park', '🌲  Panda Park'), ('home', '🏠  Back Home')):
                btn = QPushButton(label, dlg)
                btn.clicked.connect(lambda _, d=dest: (dlg.accept(), self.destination_selected.emit(d)))
                vbox.addWidget(btn)
            dlg.exec()
        except Exception:
            self.destination_selected.emit('shop')

    # ── Coordinate helpers ────────────────────────────────────────────────────
    def _screen_to_ground(self, sx: float, sy: float) -> Tuple[float, float]:
        """Approximate screen→ground-plane mapping for hit testing."""
        if not PYQT_AVAILABLE:
            return 0.0, 0.0
        w = max(1, self.width())
        h = max(1, self.height())
        # Rough inverse perspective at y=0 (good enough for hit testing)
        ndcx = (sx / w) * 2.0 - 1.0
        ndcy = 1.0 - (sy / h) * 2.0
        world_x = ndcx * 8.0
        world_z = -ndcy * 6.0 - 3.5
        return world_x, world_z

    @staticmethod
    def _hit_region(wx: float, wz: float) -> str:
        for name, (x0, x1, z0, z1) in _CLICK_REGIONS.items():
            if x0 <= wx <= x1 and z0 <= wz <= z1:
                return name
        return ''

    # ── GL primitive helpers ──────────────────────────────────────────────────
    @staticmethod
    def _sphere(r: float, sl: int, st: int):
        q = gluNewQuadric()
        gluQuadricNormals(q, GLU_SMOOTH)
        gluSphere(q, r, sl, st)
        gluDeleteQuadric(q)

    @staticmethod
    def _cylinder(r: float, h: float, sl: int):
        q = gluNewQuadric()
        gluQuadricNormals(q, GLU_SMOOTH)
        gluCylinder(q, r, r, h, sl, 1)
        gluDisk(q, 0, r, sl, 1)
        glPushMatrix(); glTranslatef(0, 0, h); gluDisk(q, 0, r, sl, 1); glPopMatrix()
        gluDeleteQuadric(q)

    @staticmethod
    def _box(x0: float, y0: float, z0: float,
             x1: float, y1: float, z1: float) -> None:
        faces = [
            # (normal, v0, v1, v2, v3)
            (( 0, 0, 1), (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)),
            (( 0, 0,-1), (x1,y0,z0),(x0,y0,z0),(x0,y1,z0),(x1,y1,z0)),
            (( 0, 1, 0), (x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)),
            (( 0,-1, 0), (x0,y0,z1),(x1,y0,z1),(x1,y0,z0),(x0,y0,z0)),
            (( 1, 0, 0), (x1,y0,z0),(x1,y0,z1),(x1,y1,z1),(x1,y1,z0)),
            ((-1, 0, 0), (x0,y0,z1),(x0,y0,z0),(x0,y1,z0),(x0,y1,z1)),
        ]
        glBegin(GL_QUADS)
        for n, v0, v1, v2, v3 in faces:
            glNormal3f(*n)
            for v in (v0, v1, v2, v3):
                glVertex3f(*v)
        glEnd()

    def set_achievement_count(self, count: int) -> None:
        """Called from main.py when achievements change (no trophy stand here, so no-op)."""
        pass

    def get_otter_screen_pos(self):
        """Return approximate screen position of the otter for tooltip placement."""
        if PYQT_AVAILABLE:
            from PyQt6.QtCore import QPoint
            return QPoint(self.width() // 2 + OTTER_SCREEN_OFFSET_X, self.height() // 2 + OTTER_SCREEN_OFFSET_Y)
        return None


# ── Wrapper widget with back button ──────────────────────────────────────────
class PandaWorldWidget(QWidget if PYQT_AVAILABLE else object):
    """QWidget container: world GL scene + back button at top."""

    if PYQT_AVAILABLE:
        destination_selected = pyqtSignal(str)
        otter_clicked        = pyqtSignal()
        back_to_bedroom      = pyqtSignal()
        gl_failed            = pyqtSignal(str)

    def __init__(self, parent=None):
        if not PYQT_AVAILABLE:
            return
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Back bar
        back_bar = QWidget()
        back_bar.setStyleSheet("background:#2a2a2a;")
        back_bar.setFixedHeight(36)
        bb_layout = QHBoxLayout(back_bar)
        bb_layout.setContentsMargins(6, 4, 6, 4)
        btn = QPushButton("← Back to Bedroom")
        btn.setStyleSheet(
            "QPushButton{background:#3a5a3a;color:white;border:none;padding:4px 12px;border-radius:4px;}"
            "QPushButton:hover{background:#4a7a4a;}"
        )
        lbl = QLabel("🌍 Outside World")
        lbl.setStyleSheet("color:#dddddd;font-size:13px;font-weight:bold;")
        bb_layout.addWidget(btn)
        bb_layout.addWidget(lbl)
        bb_layout.addStretch()
        # Car colour picker button
        self._car_color_btn = QPushButton("🎨 Paint Car")
        self._car_color_btn.setStyleSheet(
            "QPushButton{background:#3a3a6a;color:white;border:none;padding:4px 10px;border-radius:4px;}"
            "QPushButton:hover{background:#5a5a9a;}"
        )
        self._car_color_btn.clicked.connect(self.show_car_color_picker)
        bb_layout.addWidget(self._car_color_btn)
        layout.addWidget(back_bar)

        # GL world
        if QOGL_AVAILABLE and GL_AVAILABLE:
            self._world_gl = PandaWorldGL(self)
            self._world_gl.destination_selected.connect(self.destination_selected)
            self._world_gl.otter_clicked.connect(self.otter_clicked)
            self._world_gl.back_to_bedroom.connect(self.back_to_bedroom)
            self._world_gl.gl_failed.connect(self.gl_failed)
            layout.addWidget(self._world_gl, 1)
        else:
            fallback = QLabel(
                "🌍 Outside World\n\n"
                "OpenGL required for the 3D world view.\n"
                "Install PyQt6 and PyOpenGL to enable."
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet("background:#1a2a1a;color:#aaaaaa;font-size:14px;")
            layout.addWidget(fallback, 1)
            self._world_gl = None

        btn.clicked.connect(self.back_to_bedroom)

    def set_achievement_count(self, n: int) -> None:
        if hasattr(self, '_world_gl') and self._world_gl:
            self._world_gl.set_achievement_count(n)

    def set_car_color(self, r: float, g: float, b: float) -> None:
        """Change the car colour visible in the 3D world scene."""
        if hasattr(self, '_world_gl') and self._world_gl:
            self._world_gl.set_car_color(r, g, b)

    def show_car_color_picker(self) -> None:
        """Open a colour-picker dialog so the user can paint their car."""
        if not PYQT_AVAILABLE:
            return
        try:
            gl = getattr(self, '_world_gl', None)
            current = gl.get_car_color() if gl and hasattr(gl, 'get_car_color') else [0.8, 0.15, 0.15]
            initial = QColor.fromRgbF(*current)
            color = QColorDialog.getColor(initial, self, "Choose Car Colour")
            if color.isValid():
                self.set_car_color(color.redF(), color.greenF(), color.blueF())
        except Exception:
            pass
