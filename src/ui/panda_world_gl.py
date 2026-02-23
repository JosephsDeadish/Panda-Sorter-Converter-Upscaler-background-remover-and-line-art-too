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
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

# ── Optional PyQt6 / OpenGL imports ──────────────────────────────────────────
try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QColorDialog
    from PyQt6.QtCore import pyqtSignal, QTimer, Qt
    from PyQt6.QtGui import QColor
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False

try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    QOGL_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    QOGL_AVAILABLE = False

try:
    from OpenGL.GL import (
        glClearColor, glEnable, glDisable, GL_DEPTH_TEST, GL_LIGHTING,
        GL_LIGHT0, GL_LIGHT1, GL_BLEND, GL_COLOR_MATERIAL,
        glLightfv, glLightf, GL_POSITION, GL_DIFFUSE, GL_SPECULAR,
        GL_AMBIENT, GL_AMBIENT_AND_DIFFUSE, GL_SHININESS, GL_FRONT,
        glMaterialfv, glMaterialf,
        GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, glBlendFunc,
        glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
        glMatrixMode, GL_PROJECTION, GL_MODELVIEW,
        glLoadIdentity, glViewport, glPushMatrix, glPopMatrix,
        glTranslatef, glRotatef, glScalef, glColor3f, glColor4f,
        glBegin, glEnd, glVertex3f, glNormal3f,
        GL_QUADS, GL_TRIANGLES, GL_LINES, GL_LINE_LOOP,
        glLineWidth, glPointSize,
    )
    from OpenGL.GLU import gluPerspective, gluNewQuadric, gluQuadricNormals
    from OpenGL.GLU import GLU_SMOOTH, gluSphere, gluCylinder, gluDisk, gluDeleteQuadric
    GL_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    GL_AVAILABLE = False

# ── Colours ───────────────────────────────────────────────────────────────────
_SKY    = (0.53, 0.81, 0.92)
_GRASS  = (0.35, 0.65, 0.28)
_PATH   = (0.72, 0.68, 0.58)
_ROAD   = (0.32, 0.32, 0.32)
_HOUSE  = (0.88, 0.82, 0.72)
_ROOF   = (0.60, 0.35, 0.25)
_SHOP   = (0.92, 0.88, 0.80)
_SHOPRF = (0.25, 0.50, 0.35)
_CAR_R  = (0.80, 0.15, 0.15)
_CAR_W  = (0.95, 0.95, 0.95)
_OTTER  = (0.62, 0.48, 0.32)
_GOLD   = (0.85, 0.72, 0.12)
_WOOD   = (0.55, 0.38, 0.20)
_SIGN   = (0.95, 0.88, 0.55)

# ── Named screen-position offsets for otter tooltip placement
OTTER_SCREEN_OFFSET_X = 60
OTTER_SCREEN_OFFSET_Y = -40

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
        self._gl_ready = False
        self._frame    = 0
        self._otter_blink = 0   # countdown frames to next blink
        self._otter_eye_close = 0
        self._car_bob   = 0.0
        self._car_color = list(_CAR_R)  # mutable — changed by set_car_color()
        self._hover     = ''    # region currently under cursor
        self._otter_happy_t = 0  # orange flash frames when clicked

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
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_LIGHT1)
            glEnable(GL_COLOR_MATERIAL)

            glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 5.0, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.85, 0.82, 0.78, 1.0])
            glLightfv(GL_LIGHT0, GL_SPECULAR, [0.4,  0.4,  0.3,  1.0])
            glLightfv(GL_LIGHT1, GL_POSITION, [-4.0, 6.0, -2.0, 1.0])
            glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.25, 0.30, 0.40, 1.0])
            glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.35, 0.33, 0.30, 1.0])

            self._gl_ready = True
        except Exception as e:
            self._gl_ready = False
            if PYQT_AVAILABLE:
                self.gl_failed.emit(str(e))

    def resizeGL(self, w: int, h: int):
        if not GL_AVAILABLE or not self._gl_ready:
            return
        glViewport(0, 0, max(1, w), max(1, h))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50.0, w / max(1, h), 0.1, 60.0)
        glMatrixMode(GL_MODELVIEW)

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
        self._car_bob = math.sin(self._frame * 0.04) * 0.02
        if self._otter_blink <= 0:
            import random
            self._otter_blink     = random.randint(120, 300)
            self._otter_eye_close = 5
        else:
            self._otter_blink -= 1
        if self._otter_eye_close > 0:
            self._otter_eye_close -= 1
        if self._otter_happy_t > 0:
            self._otter_happy_t -= 1
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
        """A friendly-looking shop on the right side."""
        glEnable(GL_LIGHTING)
        # Walls
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_SHOP, 1.0])
        self._box(2.0, 0.0, -5.5,  6.5, 3.2, -2.0)
        # Roof
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_SHOPRF, 1.0])
        self._box(1.8, 3.2, -5.8,  6.8, 3.5, -1.7)
        # Awning
        glDisable(GL_LIGHTING)
        glColor3f(*_SHOPRF)
        glBegin(GL_QUADS)
        glVertex3f(1.8, 3.0, -2.0)
        glVertex3f(6.8, 3.0, -2.0)
        glVertex3f(6.8, 2.5, -1.2)
        glVertex3f(1.8, 2.5, -1.2)
        glEnd()
        glEnable(GL_LIGHTING)
        # Shop window (big glass front)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.55, 0.75, 0.90, 0.55)
        self._box(2.3, 0.3, -2.05,  6.2, 2.7, -1.95)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        # Door
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_WOOD, 1.0])
        self._box(3.9, 0.0, -2.06,  4.8, 2.2, -1.94)
        # Sign
        glDisable(GL_LIGHTING)
        glColor3f(*_SIGN)
        self._box(2.5, 3.5, -5.0,  6.0, 4.0, -4.5)
        glEnable(GL_LIGHTING)
        # Draw otter inside
        self._draw_otter()

    def _draw_otter(self):
        """A simple 3-D animated otter standing behind the counter."""
        glPushMatrix()
        glTranslatef(4.2, 0.0, -4.2)

        # Counter
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_WOOD, 1.0])
        self._box(-0.8, 0.8, -0.15,  0.8, 1.0, 0.55)

        # Body (slightly taller than panda, slimmer)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_OTTER, 1.0])
        glPushMatrix()
        glTranslatef(0.0, 1.8, 0.0)
        glScalef(0.5, 0.65, 0.45)
        self._sphere(1.0, 12, 12)
        glPopMatrix()

        # Head
        glPushMatrix()
        glTranslatef(0.0, 2.75, 0.0)
        self._sphere(0.38, 12, 12)
        # Snout
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.75, 0.62, 0.45, 1.0])
        glPushMatrix()
        glTranslatef(0.0, -0.06, 0.34)
        glScalef(1.0, 0.7, 0.6)
        self._sphere(0.18, 10, 10)
        glPopMatrix()
        # Nose
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.12, 0.10, 0.10, 1.0])
        glPushMatrix()
        glTranslatef(0.0, 0.04, 0.52)
        self._sphere(0.06, 8, 8)
        glPopMatrix()
        # Ears
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_OTTER, 1.0])
        for ex in [-0.30, 0.30]:
            glPushMatrix()
            glTranslatef(ex, 0.28, -0.10)
            glScalef(0.6, 0.8, 0.5)
            self._sphere(0.16, 8, 8)
            glPopMatrix()

        # Eyes (blink support)
        if self._otter_eye_close > 2:
            eye_sy = 0.2   # squished (blinking)
        else:
            eye_sy = 1.0
        happy_col = [0.20, 0.60, 0.90] if self._otter_happy_t > 0 else [0.12, 0.10, 0.10]
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*happy_col, 1.0])
        for ex in [-0.15, 0.15]:
            glPushMatrix()
            glTranslatef(ex, 0.08, 0.34)
            glScalef(1.0, eye_sy, 1.0)
            self._sphere(0.06, 8, 8)
            glPopMatrix()
        glPopMatrix()   # end head

        # Arms raised (shopkeeper greeting pose)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_OTTER, 1.0])
        bob_arm = math.sin(self._frame * 0.04) * 4.0
        for ax, side in [(-0.5, 1.0), (0.5, -1.0)]:
            glPushMatrix()
            glTranslatef(ax, 2.0, 0.0)
            glRotatef(-50.0 + bob_arm * side, 0.0, 0.0, 1.0)
            glPushMatrix()
            glTranslatef(0.0, -0.28, 0.0)
            glScalef(0.3, 0.6, 0.3)
            self._sphere(1.0, 10, 10)
            glPopMatrix()
            glPopMatrix()

        glPopMatrix()   # end otter transform

        # Hover / click highlight
        if self._hover == 'otter' or self._otter_happy_t > 0:
            glDisable(GL_LIGHTING)
            glColor3f(1.0, 0.85, 0.2)
            glLineWidth(2.0)
            glPushMatrix()
            glTranslatef(4.2, 0.0, -4.2)
            glBegin(GL_LINE_LOOP)
            for vx, vz in [(-1.0, -0.7), (1.0, -0.7), (1.0, 0.7), (-1.0, 0.7)]:
                glVertex3f(vx, 3.2, vz)
            glEnd()
            glPopMatrix()
            glLineWidth(1.0)
            glEnable(GL_LIGHTING)

    def _draw_park_area(self):
        """Bench + pond hint for the park destination."""
        # Bench (far back centre)
        glEnable(GL_LIGHTING)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*_WOOD, 1.0])
        self._box(-0.8, 0.6, 4.0,  0.8, 0.7, 4.6)  # seat
        self._box(-0.8, 0.0, 4.0, -0.7, 0.6, 4.15) # left leg
        self._box( 0.7, 0.0, 4.0,  0.8, 0.6, 4.15) # right leg
        # Park label (sign)
        glDisable(GL_LIGHTING)
        glColor3f(*_SIGN)
        self._box(-0.6, 1.4, 4.1,  0.6, 1.8, 4.2)
        glEnable(GL_LIGHTING)

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
            if QOGL_AVAILABLE:
                self.setCursor(Qt.CursorShape.PointingHandCursor if self._hover else Qt.CursorShape.ArrowCursor)

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
            self._otter_happy_t = 60
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
