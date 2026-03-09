"""
draw_panda_gl.py — Shared 3-D panda drawing routine.

This module provides a single authoritative function for rendering the
3-D panda character using OpenGL fixed-function calls.  It is used by:

  * ``panda_bedroom_gl.PandaBedroomGL._draw_panda_in_room()``
  * ``dungeon_3d_widget._Dungeon3DGL._draw_panda()``
  * ``panda_world_gl.PandaWorldGL._draw_world_panda()``

All three scenes render the SAME panda this way — there is only one 3-D
panda in the entire application.

Usage
-----
::

    from ui.draw_panda_gl import draw_panda_3d

    # Inside a paintGL / render method that already has a GLU quadric:
    draw_panda_3d(
        quadric       = self._glu_quadric,
        walk_frame    = self._panda_walk_frame,
        is_walking    = self._panda_is_walking,
        is_running    = False,
        body_pitch_deg= 0.0,
    )

The caller is responsible for:
  * Setting up the modelview matrix (position + facing rotation) before
    calling this function.
  * Providing a valid GLU quadric object (or None — the function guards).
"""

from __future__ import annotations

import math

# ── OpenGL imports ────────────────────────────────────────────────────────────
try:
    from OpenGL.GL import (
        glPushMatrix, glPopMatrix,
        glTranslatef, glRotatef, glScalef,
        glColor3f,
    )
    from OpenGL.GLU import gluSphere
    _GL_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    _GL_AVAILABLE = False

# ── Colour palette ────────────────────────────────────────────────────────────
_COL_WHITE = (0.92, 0.92, 0.90)
_COL_BLACK = (0.08, 0.06, 0.06)
_COL_BELLY = (0.96, 0.95, 0.93)   # slightly brighter white for belly

# ── Body proportions — barrel body: BW:BH ≈ 1.73:1 ──────────────────────────
BW = 0.52   # body half-width  (horizontal radius of body sphere)
BH = 0.30   # body half-height (vertical radius of body sphere)
BD = 0.38   # body depth       (Z radius — slightly elongated forward)
BY = 0.31   # body centre Y (body bottom ≈ 0, just above floor)


def _sphere(quadric, radius: float, slices: int = 12, stacks: int = 12) -> None:
    """Draw a GLU sphere.  No-op when quadric is None or GL is unavailable."""
    if quadric is None or not _GL_AVAILABLE:
        return
    gluSphere(quadric, radius, slices, stacks)


def draw_panda_3d(
    quadric,
    walk_frame:     float = 0.0,
    is_walking:     bool  = False,
    is_running:     bool  = False,
    body_pitch_deg: float = 0.0,
) -> None:
    """Draw the 3-D giant panda at the current GL modelview origin.

    The caller must set up the modelview matrix (translation + rotation to
    face the correct direction) before calling this function.

    Parameters
    ----------
    quadric:
        GLU quadric object (from ``gluNewQuadric()``).  If *None* the
        function returns immediately without drawing.
    walk_frame:
        Running oscillation counter; drives leg swing via ``sin(walk_frame)``.
    is_walking:
        If *True*, apply walk-swing oscillation to legs and arms.
    is_running:
        If *True*, pitch the whole body forward and extend arms as front legs.
    body_pitch_deg:
        Additional body pitch in degrees (positive = lean back, negative =
        lean forward).  Callers can pass ``_BODY_PITCH_TARGETS[activity]``
        to make the panda lean realistically for each activity.
    """
    if not _GL_AVAILABLE or quadric is None:
        return

    swing_amp = 0.0
    if is_walking:
        swing_amp = 35.0 if is_running else 22.0

    glPushMatrix()

    # All-fours body pitch when running (leans forward)
    if is_running:
        glRotatef(-30.0, 1.0, 0.0, 0.0)
    elif body_pitch_deg != 0.0:
        glRotatef(body_pitch_deg, 1.0, 0.0, 0.0)

    # ── WHITE TORSO (barrel body, W:H ≈ 1.73:1) ──────────────────────────────
    glPushMatrix()
    glTranslatef(0.0, BY, 0.0)
    glScalef(BW, BH, BD)
    glColor3f(*_COL_WHITE)
    _sphere(quadric, 1.0, 18, 18)
    glPopMatrix()

    # ── WHITE BELLY (forward protrusion) ─────────────────────────────────────
    glPushMatrix()
    glTranslatef(0.0, BY - BH * 0.10, BD * 0.80)
    glScalef(BW * 0.72, BH * 0.80, BD * 0.42)
    glColor3f(*_COL_BELLY)
    _sphere(quadric, 1.0, 14, 14)
    glPopMatrix()

    # ── BLACK SHOULDER PATCHES ────────────────────────────────────────────────
    for sx in (-BW * 0.92, BW * 0.92):
        glPushMatrix()
        glTranslatef(sx, BY + BH * 0.30, 0.0)
        glScalef(BW * 0.42, BH * 0.50, BD * 0.40)
        glColor3f(*_COL_BLACK)
        _sphere(quadric, 1.0, 12, 12)
        glPopMatrix()

    # ── BLACK HIP PATCHES ─────────────────────────────────────────────────────
    for hx in (-BW * 0.80, BW * 0.80):
        glPushMatrix()
        glTranslatef(hx, BY - BH * 0.55, BD * 0.05)
        glScalef(BW * 0.38, BH * 0.42, BD * 0.32)
        glColor3f(*_COL_BLACK)
        _sphere(quadric, 1.0, 12, 12)
        glPopMatrix()

    # ── NECK (short "neckless" panda bridge) ──────────────────────────────────
    NECK_Y = BY + BH + 0.02
    glPushMatrix()
    glTranslatef(0.0, NECK_Y, BD * 0.08)
    glScalef(0.20, 0.14, 0.18)
    glColor3f(*_COL_WHITE)
    _sphere(quadric, 1.0, 12, 12)
    glPopMatrix()

    # ── HEAD ─────────────────────────────────────────────────────────────────
    HEAD_Y = NECK_Y + 0.22
    HR = 0.22   # head radius
    glPushMatrix()
    glTranslatef(0.0, HEAD_Y, BD * 0.12)
    glColor3f(*_COL_WHITE)
    _sphere(quadric, HR, 18, 18)

    # Ears
    for ex in (-0.15, 0.15):
        glPushMatrix()
        glTranslatef(ex, HR * 0.78, -HR * 0.12)
        glScalef(1.0, 0.82, 0.70)
        glColor3f(*_COL_BLACK)
        _sphere(quadric, 0.075, 10, 10)
        glPopMatrix()

    # Eye patches
    for ex in (-0.085, 0.085):
        glPushMatrix()
        glTranslatef(ex, HR * 0.10, HR * 0.84)
        glScalef(1.0, 0.85, 0.48)
        glColor3f(*_COL_BLACK)
        _sphere(quadric, 0.062, 10, 10)
        glPopMatrix()

    # Eyes (white sclera + black pupil)
    for ex in (-0.062, 0.062):
        glPushMatrix()
        glTranslatef(ex, HR * 0.10, HR * 0.97)
        glColor3f(0.94, 0.94, 0.92)
        _sphere(quadric, 0.020, 8, 8)
        glPushMatrix()
        glTranslatef(0.0, 0.0, 0.012)
        glColor3f(0.08, 0.06, 0.06)
        _sphere(quadric, 0.014, 6, 6)
        glPopMatrix()
        glPopMatrix()

    # Snout
    glPushMatrix()
    glTranslatef(0.0, -HR * 0.12, HR * 0.92)
    glScalef(0.80, 0.55, 0.48)
    glColor3f(0.90, 0.88, 0.86)
    _sphere(quadric, 0.075, 10, 10)
    glPopMatrix()

    # Nose
    glPushMatrix()
    glTranslatef(0.0, -HR * 0.04, HR * 1.00)
    glColor3f(0.14, 0.10, 0.10)
    _sphere(quadric, 0.026, 8, 8)
    glPopMatrix()

    glPopMatrix()  # end head

    # ── ARMS (black; extend as front legs when running) ───────────────────────
    ARM_SY = BY + BH * 0.28   # shoulder Y
    for side, ax in ((-1, -BW * 1.05), (1, BW * 1.05)):
        glPushMatrix()
        glTranslatef(ax, ARM_SY, 0.0)
        glRotatef(side * 12.0, 0.0, 0.0, 1.0)
        if is_running:
            glRotatef(-50.0, 1.0, 0.0, 0.0)  # extend forward as front legs
        # Upper arm
        glPushMatrix()
        glScalef(0.095, 0.200, 0.095)
        glTranslatef(0.0, -0.50, 0.0)
        glColor3f(*_COL_BLACK)
        _sphere(quadric, 1.0, 10, 10)
        glPopMatrix()
        # Paw
        glPushMatrix()
        glTranslatef(0.0, -0.26, 0.0)
        glScalef(1.10, 0.60, 1.05)
        glColor3f(*_COL_BLACK)
        _sphere(quadric, 0.070, 10, 10)
        glPopMatrix()
        glPopMatrix()

    # ── LEGS (with walk oscillation) ─────────────────────────────────────────
    LEG_Y = BY - BH * 0.65   # hip pivot Y
    for side, lx in ((-1, -BW * 0.58), (1, BW * 0.58)):
        swing = swing_amp * math.sin(walk_frame + side * math.pi)
        glPushMatrix()
        glTranslatef(lx, LEG_Y, 0.0)
        glRotatef(swing, 1.0, 0.0, 0.0)
        # Thigh
        glPushMatrix()
        glScalef(0.120, 0.220, 0.120)
        glTranslatef(0.0, -0.50, 0.0)
        glColor3f(*_COL_BLACK)
        _sphere(quadric, 1.0, 10, 10)
        glPopMatrix()
        # Shin
        glPushMatrix()
        glTranslatef(0.0, -0.32, 0.0)
        glScalef(0.100, 0.200, 0.100)
        glTranslatef(0.0, -0.50, 0.0)
        glColor3f(*_COL_BLACK)
        _sphere(quadric, 1.0, 10, 10)
        glPopMatrix()
        # Foot blob (flattened, slightly forward)
        glPushMatrix()
        glTranslatef(0.0, -0.58, 0.055)
        glScalef(1.30, 0.40, 1.55)
        glColor3f(*_COL_BLACK)
        _sphere(quadric, 0.072, 10, 10)
        glPopMatrix()
        glPopMatrix()

    glPopMatrix()  # end panda
