"""
Transparent Panda Overlay System - Hardware-Accelerated Interactive Layer

A transparent OpenGL widget that renders the Panda companion on top of the normal Qt UI layer
with full UI interaction detection, physics-based behavior, and programmatic button triggering.

Architecture:
    Main Window (Qt Widgets)
    ├── Normal UI Layer (tabs, buttons, sliders, file browser, settings)
    └── Transparent Overlay (always on top)
        ├── Panda 3D rendering (OpenGL hardware acceleration)
        ├── Items 3D rendering (toys, food, clothes with physics)
        ├── Dynamic shadows onto UI widgets
        ├── Squash effects for depth illusion
        └── Real-time collision detection with UI elements

Features:
    ✓ Full-window transparent QOpenGLWidget overlay
    ✓ Always-on-top rendering with mouse event pass-through
    ✓ Body part position tracking (head, mouth, feet)
    ✓ UI hit-testing and widget geometry detection
    ✓ Shadow rendering dynamically onto widgets below panda
    ✓ Squash effects when panda lands/presses on widgets
    ✓ Animation triggers: bites tabs, jumps on buttons, taps sliders
    ✓ Programmatic button clicks (.click()) with animation delay
    ✓ Physics + AI behavior with collision detection
    ✓ 3D items (toys, food, clothes) rendered with OpenGL NOT canvas
    ✓ Hardware acceleration at 60fps with real lighting & shadows

NO CANVAS DRAWING - Everything uses QOpenGLWidget with OpenGL rendering
"""

import logging
import math
import random
import time

try:
    from PyQt6.QtWidgets import QWidget
    # QOpenGLWidget was moved from QtWidgets → QtOpenGLWidgets in Qt6/PyQt6
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, pyqtSignal
    from PyQt6.QtGui import QPainter, QColor
    from OpenGL.GL import *
    from OpenGL.GLU import *
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QOpenGLWidget = object
    QWidget = object
    class _SignalStub:  # noqa: E301
        """Stub signal — active only when PyQt6 is absent."""
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SignalStub()  # noqa: E301

logger = logging.getLogger(__name__)


class TransparentPandaOverlay(QOpenGLWidget if PYQT_AVAILABLE else QWidget):
    """
    Transparent overlay widget for rendering Panda on top of Qt UI.
    
    This widget:
    - Covers the entire main window
    - Is transparent so UI below shows through
    - Renders Panda in 3D with OpenGL
    - Passes mouse events through when not on Panda
    - Tracks Panda body part positions for widget interaction
    """
    
    # Animation timing constants (milliseconds)
    BITE_ANIMATION_DELAY = 300
    JUMP_START_DELAY = 400
    JUMP_LAND_DELAY = 500
    JUMP_RECOVER_DELAY = 600
    TAP_ANIMATION_DELAY = 200
    SQUASH_EFFECT_DURATION = 100
    
    # Behavior timing constants (seconds)
    MIN_BEHAVIOR_INTERVAL = 5.0
    MAX_BEHAVIOR_INTERVAL = 15.0
    INVESTIGATION_TRIGGER_CHANCE = 0.1  # 10% chance per frame
    
    # Behavior probabilities (must sum to 1.0)
    BEHAVIOR_WEIGHTS = {
        'idle':          0.30,
        'walking':       0.28,
        'interacting':   0.18,
        'investigating': 0.08,
        'crawling':      0.10,
        'climbing_wall': 0.06,
    }
    
    # Signals for interaction events
    panda_moved = pyqtSignal(int, int) if PYQT_AVAILABLE else None
    panda_clicked_widget = pyqtSignal(object) if PYQT_AVAILABLE else None
    panda_triggered_button = pyqtSignal(object) if PYQT_AVAILABLE else None  # When panda clicks a button
    
    def __init__(self, parent=None, main_window=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 and PyOpenGL required for TransparentPandaOverlay")
        
        super().__init__(parent)
        
        # Reference to main window for widget detection
        self.main_window = main_window

        # GL initialization guard — prevents drawing before context is ready
        self._gl_initialized = False
        
        # Make transparent — use WA_AlwaysStackOnTop (child-widget stacking) instead
        # of WindowStaysOnTopHint (which promotes the widget to a separate top-level
        # window and breaks the parent→child geometry relationship on many platforms).
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
        # Start with mouse events passing through; only capture when cursor is on panda
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Window flags: frameless but NOT WindowStaysOnTopHint (that promotes to toplevel)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Panda state
        self.panda_x = 0.0
        self.panda_y = -0.5
        self.panda_z = 0.0
        self.panda_rotation = 0.0
        self.panda_scale = 1.0
        
        # Velocity for physics
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.velocity_z = 0.0
        
        # Body part positions (in overlay coordinates)
        self.head_position = QPoint(0, 0)
        self.mouth_position = QPoint(0, 0)
        self.left_foot_position = QPoint(0, 0)
        self.right_foot_position = QPoint(0, 0)
        self.left_hand_position = QPoint(0, 0)
        self.right_hand_position = QPoint(0, 0)
        
        # Animation state
        self.animation_state = 'idle'
        self.animation_phase = 0.0
        
        # Shadow rendering
        self.shadow_enabled = True
        self.shadow_opacity = 0.3
        self.shadow_blur = 10
        
        # Squash effect
        self.squash_factor = 1.0  # 1.0 = normal, <1.0 = squashed
        self.squash_target = 1.0
        
        # Camera
        self.camera_distance = 5.0
        self.camera_rotation_x = 20.0
        self.camera_rotation_y = 0.0
        
        # Reference to panda character (from main app)
        self.panda_character = None
        
        # Widget interaction system
        self.widget_below = None  # Current widget under panda
        self.collision_map = {}  # Map of widget geometries for collision detection
        self.interaction_target = None  # Widget panda is interacting with
        self.interaction_animation = None  # Current interaction animation
        self.interaction_delay = 0.0  # Delay before triggering button click
        
        # Items in overlay (toys, food, clothes) - all rendered with OpenGL
        self.items_3d = []  # List of 3D items in the scene
        self.item_positions = {}  # 3D positions of items
        
        # Physics constants
        self.gravity = 9.8
        self.friction = 0.92
        self.bounce_damping = 0.6
        
        # AI behavior
        self.behavior_state = 'idle'  # idle, walking, interacting, investigating
        self.target_position = None  # Where panda wants to go
        self.walk_speed = 1.0  # Units per second
        self.next_behavior_time = 0.0
        
        # Update timer (60 FPS)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_frame)
        self.update_timer.start(16)  # ~60 FPS
        
        # Collision detection timer
        self.collision_timer = QTimer()
        self.collision_timer.timeout.connect(self._update_collision_map)
        self.collision_timer.start(100)  # Update collision map every 100ms
        
        # Mouse tracking
        self.setMouseTracking(True)
        self.mouse_on_panda = False
    
    def initializeGL(self):
        """Initialize OpenGL context."""
        try:
            # Enable transparency
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # Enable depth testing
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LEQUAL)
            
            # Enable smooth shading (CompatibilityProfile only; ignore on CoreProfile)
            try:
                glShadeModel(GL_SMOOTH)
            except Exception as _e:
                logger.debug("Overlay: glShadeModel not available: %s", _e)
            
            # Clear color (transparent)
            glClearColor(0.0, 0.0, 0.0, 0.0)
            
            # Lighting (CompatibilityProfile; skip on CoreProfile/ANGLE)
            try:
                glEnable(GL_LIGHTING)
                glEnable(GL_LIGHT0)
                glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
                glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
                glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
            except Exception as _e:
                logger.debug("Overlay: lighting not available (CoreProfile/ANGLE): %s", _e)

            # Probe fixed-function matrix mode (fails on CoreProfile / ANGLE)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            self._gl_initialized = True
            # Create a single reusable GLU quadric for sphere drawing — avoids
            # allocating/deleting a new object on every frame.
            self._sphere_quadric = gluNewQuadric()
            gluQuadricNormals(self._sphere_quadric, GLU_SMOOTH)
        except Exception as exc:
            logger.warning("TransparentPandaOverlay GL init failed: %s — overlay hidden", exc)
            self._gl_initialized = False
            # Make overlay fully transparent for mouse events so it cannot block the UI
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    
    def resizeGL(self, w, h):
        """Handle window resize."""
        glViewport(0, 0, w, h)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        aspect = w / h if h > 0 else 1.0
        gluPerspective(45.0, aspect, 0.1, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render the overlay with hardware acceleration."""
        if not self._gl_initialized:
            return
        try:
            # Clear with transparency
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            glLoadIdentity()
            
            # Position camera
            glTranslatef(0.0, 0.0, -self.camera_distance)
            glRotatef(self.camera_rotation_x, 1.0, 0.0, 0.0)
            glRotatef(self.camera_rotation_y, 0.0, 1.0, 0.0)
            
            # Render shadow (if enabled and widget below)
            if self.shadow_enabled and self.widget_below:
                self._render_shadow()
            
            # Render all 3D items (toys, food, clothes) with OpenGL
            self._render_items_3d()
            
            # Render panda
            self._render_panda()
            
            # Update body part positions for interaction detection
            self._update_body_part_positions()
        except Exception as _e:
            logger.debug("TransparentPandaOverlay paintGL error (frame skipped): %s", _e)
    
    def _render_shadow(self):
        """Render shadow below panda onto widget."""
        glPushMatrix()
        
        # Position shadow on ground
        glTranslatef(self.panda_x, -0.8, self.panda_z)
        
        # Shadow color (semi-transparent black)
        glDisable(GL_LIGHTING)
        glColor4f(0.0, 0.0, 0.0, self.shadow_opacity)
        
        # Draw shadow as flat ellipse
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, 0.0, 0.0)
        
        num_segments = 20
        for i in range(num_segments + 1):
            angle = (i / num_segments) * 2.0 * math.pi
            x = math.cos(angle) * 0.3
            z = math.sin(angle) * 0.2
            glVertex3f(x, 0.0, z)
        
        glEnd()
        
        glEnable(GL_LIGHTING)
        glPopMatrix()
    
    def _render_panda(self):
        """Render the 3D panda with detailed body parts matching the GL sidebar panda."""
        glPushMatrix()

        # Position and orient panda
        glTranslatef(self.panda_x, self.panda_y, self.panda_z)
        glRotatef(self.panda_rotation, 0.0, 1.0, 0.0)
        glScalef(self.panda_scale, self.panda_scale * self.squash_factor, self.panda_scale)

        t = self.animation_phase
        is_walking = self.animation_state == 'walking'
        arm_swing  = math.sin(t) * 25.0 if is_walking else 0.0
        leg_swing  = math.sin(t) * 20.0 if is_walking else 0.0
        bob        = math.sin(t * 2.0) * 0.012 if is_walking else 0.0

        # ── Torso ──────────────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.0, 0.28 + bob, 0.0)

        # Belly / cream underside (ellipsoid)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 0.98, 0.93, 1.0])
        glPushMatrix()
        glScalef(0.50 * 0.65, 0.60 * 0.55, 0.50 * 0.50)
        self._draw_unit_sphere(32)
        glPopMatrix()

        # Main body (white)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glPushMatrix()
        glScalef(0.50, 0.60, 0.50 * 0.78)
        self._draw_unit_sphere(32)
        glPopMatrix()

        # Black saddle patch (lower torso)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.08, 0.08, 0.08, 1.0])
        glPushMatrix()
        glTranslatef(0.0, -0.18, 0.0)
        glScalef(0.50 * 0.95, 0.60 * 0.35, 0.50 * 0.70)
        self._draw_unit_sphere(20)
        glPopMatrix()

        # Shoulder muscle masses (black)
        for sx in (-0.35, 0.35):
            glPushMatrix()
            glTranslatef(sx, 0.12, -0.50 * 0.15)
            glScalef(0.30, 0.28, 0.24)
            self._draw_unit_sphere(12)
            glPopMatrix()

        # Chest white patch
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glPushMatrix()
        glTranslatef(0.0, 0.60 * 0.28, 0.50 * 0.55)
        glScalef(0.45, 0.38, 0.25)
        self._draw_unit_sphere(14)
        glPopMatrix()

        # Neck
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glPushMatrix()
        glTranslatef(0.0, 0.60 * 0.48, 0.0)
        glScalef(0.30, 0.32, 0.28)
        self._draw_unit_sphere(14)
        glPopMatrix()

        # ── Tail ────────────────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glPushMatrix()
        glTranslatef(0.0, -0.05, -0.50 * 0.78)
        self._draw_unit_sphere_r(0.090, 12)
        glPopMatrix()

        # ── Legs (black) ──────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.08, 0.08, 0.08, 1.0])
        for lx, phase in ((-0.18, 0.0), (0.18, math.pi)):
            glPushMatrix()
            glTranslatef(lx, -0.60 * 0.22, 0.0)
            glRotatef(math.sin(t + phase) * 18.0 if is_walking else 0.0, 1.0, 0.0, 0.0)
            # Upper leg
            glPushMatrix()
            glTranslatef(0.0, -0.10, 0.0)
            glScalef(0.14, 0.22, 0.14)
            self._draw_unit_sphere(14)
            glPopMatrix()
            # Lower leg / paw
            glPushMatrix()
            glTranslatef(0.0, -0.28, 0.05)
            glScalef(0.12, 0.18, 0.14)
            self._draw_unit_sphere(12)
            glPopMatrix()
            # Paw
            glPushMatrix()
            glTranslatef(0.0, -0.34, 0.08)
            glScalef(0.14, 0.10, 0.16)
            self._draw_unit_sphere(10)
            glPopMatrix()
            glPopMatrix()

        # ── Arms (black) ─────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.08, 0.08, 0.08, 1.0])
        for ax, phase in ((-0.28, 0.0), (0.28, math.pi)):
            glPushMatrix()
            glTranslatef(ax, 0.60 * 0.10, 0.0)
            glRotatef(math.sin(t + phase) * arm_swing, 1.0, 0.0, 0.0)
            # Upper arm
            glPushMatrix()
            glTranslatef(0.0, -0.06, 0.0)
            glScalef(0.12, 0.20, 0.12)
            self._draw_unit_sphere(12)
            glPopMatrix()
            # Lower arm / paw
            glPushMatrix()
            glTranslatef(0.0, -0.20, 0.05)
            glScalef(0.10, 0.14, 0.10)
            self._draw_unit_sphere(12)
            glPopMatrix()
            # Paw pad
            glPushMatrix()
            glTranslatef(0.0, -0.25, 0.08)
            glScalef(0.12, 0.08, 0.14)
            self._draw_unit_sphere(10)
            glPopMatrix()
            glPopMatrix()

        glPopMatrix()  # end torso matrix

        # ── Head (separate matrix for independent tilt) ───────────────────
        glPushMatrix()
        glTranslatef(0.0, 0.90 + bob * 1.1, 0.0)
        # Gentle breathing head-tilt
        head_tilt = 3.5 * math.sin(t * 0.04)
        glRotatef(head_tilt, 0.0, 0.0, 1.0)

        # Main skull (white)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        self._draw_unit_sphere_r(0.40, 32)

        # Cranial dome
        glPushMatrix()
        glTranslatef(0.0, 0.40 * 0.65, -0.40 * 0.05)
        glScalef(0.52, 0.38, 0.44)
        self._draw_unit_sphere_r(0.40, 14)
        glPopMatrix()

        # Jaw / chin mass
        glPushMatrix()
        glTranslatef(0.0, -0.40 * 0.55, 0.40 * 0.35)
        glScalef(0.70, 0.42, 0.58)
        self._draw_unit_sphere_r(0.40 * 0.65, 14)
        glPopMatrix()

        # Cheek puffs (white)
        for cx in (-0.40 * 0.68, 0.40 * 0.68):
            glPushMatrix()
            glTranslatef(cx, -0.40 * 0.22, 0.40 * 0.52)
            glScalef(0.80, 0.68, 0.55)
            self._draw_unit_sphere_r(0.40 * 0.45, 12)
            glPopMatrix()

        # ── Ears (black with pink inner) ──────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.08, 0.08, 0.08, 1.0])
        for ex in (-0.265, 0.265):
            glPushMatrix()
            glTranslatef(ex, 0.295, 0.06)
            glScalef(1.0, 0.88, 0.55)
            self._draw_unit_sphere_r(0.15, 16)
            # Inner pink concha
            glPushMatrix()
            glTranslatef(0.0, -0.005, 0.015)
            glScalef(0.58, 0.52, 0.40)
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.88, 0.60, 0.68, 1.0])
            self._draw_unit_sphere_r(0.15, 12)
            glPopMatrix()
            glPopMatrix()

        # ── Eye patches (black) ───────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.08, 0.08, 0.08, 1.0])
        patch_asym = 0.04  # slight size asymmetry for naturalism
        for side, px in ((-1, -0.158), (1, 0.158)):
            patch_r = 0.40 * (0.325 + side * patch_asym * 0.08)
            glPushMatrix()
            glTranslatef(px, 0.055, 0.40 * 0.78)
            glScalef(1.0, 1.25, 0.65)
            self._draw_unit_sphere_r(patch_r, 16)
            glPopMatrix()

        # White eyes
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.95, 0.95, 0.92, 1.0])
        for px in (-0.158, 0.158):
            glPushMatrix()
            glTranslatef(px, 0.055, 0.40 * 0.84)
            self._draw_unit_sphere_r(0.072, 14)
            glPopMatrix()

        # Black pupils
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.02, 0.02, 0.02, 1.0])
        for px in (-0.158, 0.158):
            glPushMatrix()
            glTranslatef(px, 0.055, 0.40 * 0.90)
            self._draw_unit_sphere_r(0.040, 12)
            glPopMatrix()

        # ── Tear-duct streaks (diagonal dark marks from inner eye corner down) ─
        # Each streak is 3 oval segments: eye-corner origin → mid-streak → muzzle tip.
        # Coordinates are in head-local space (head radius = 0.40).
        # tx/ty = lateral/vertical offset; tz = depth along face (positive = forward).
        # sr = sphere radius for the segment (shrinks toward tip for teardrop shape).
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.08, 0.08, 0.08, 1.0])
        for side in (-1, 1):
            for tx, ty, tz, sr in [
                (side * 0.085,  0.035, 0.40 * 0.82, 0.048),   # seg 0: eye-corner origin
                (side * 0.092, -0.018, 0.40 * 0.85, 0.036),   # seg 1: mid-streak
                (side * 0.082, -0.062, 0.40 * 0.86, 0.026),   # seg 2: lower tip
            ]:
                glPushMatrix()
                glTranslatef(tx, ty, tz)
                glScalef(sr * 0.55, sr * 0.49, sr * 0.38)
                self._draw_unit_sphere(10)
                glPopMatrix()

        # ── Snout / muzzle ────────────────────────────────────────────────
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.92, 0.88, 0.80, 1.0])
        glPushMatrix()
        glTranslatef(0.0, -0.40 * 0.18, 0.40 * 0.72)
        glScalef(0.55, 0.38, 0.32)
        self._draw_unit_sphere_r(0.40 * 0.55, 14)
        glPopMatrix()

        # Nose (black)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.05, 0.05, 0.05, 1.0])
        glPushMatrix()
        glTranslatef(0.0, -0.40 * 0.08, 0.40 * 0.96)
        glScalef(0.55, 0.40, 0.38)
        self._draw_unit_sphere_r(0.40 * 0.22, 12)
        glPopMatrix()

        glPopMatrix()  # end head matrix
    
    def _draw_sphere(self, x, y, z, radius):
        """Draw a sphere at position with radius."""
        glPushMatrix()
        glTranslatef(x, y, z)
        q = getattr(self, '_sphere_quadric', None)
        if q is not None:
            gluSphere(q, radius, 20, 20)
        else:
            quadric = gluNewQuadric()
            gluQuadricNormals(quadric, GLU_SMOOTH)
            gluSphere(quadric, radius, 20, 20)
            gluDeleteQuadric(quadric)
        glPopMatrix()

    def _draw_unit_sphere(self, slices: int = 20) -> None:
        """Draw a unit sphere (radius=1) centered at the current matrix origin.
        The caller is responsible for applying glScalef / glTranslatef first."""
        q = getattr(self, '_sphere_quadric', None)
        if q is not None:
            gluSphere(q, 1.0, slices, slices)
        else:
            quadric = gluNewQuadric()
            gluQuadricNormals(quadric, GLU_SMOOTH)
            gluSphere(quadric, 1.0, slices, slices)
            gluDeleteQuadric(quadric)

    def _draw_unit_sphere_r(self, radius: float, slices: int = 20) -> None:
        """Draw a sphere of the given *radius* centered at the current matrix origin."""
        q = getattr(self, '_sphere_quadric', None)
        if q is not None:
            gluSphere(q, radius, slices, slices)
        else:
            quadric = gluNewQuadric()
            gluQuadricNormals(quadric, GLU_SMOOTH)
            gluSphere(quadric, radius, slices, slices)
            gluDeleteQuadric(quadric)
    
    def _update_body_part_positions(self):
        """Update body part positions in screen coordinates for interaction detection."""
        try:
            # Get model-view-projection matrices
            model_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
            proj_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
            viewport = glGetIntegerv(GL_VIEWPORT)
            
            # Project 3D positions to 2D screen coordinates
            def project_point(x, y, z):
                screen_pos = gluProject(x, y, z, model_matrix, proj_matrix, viewport)
                return QPoint(int(screen_pos[0]), int(viewport[3] - screen_pos[1]))
            
            # Head position
            self.head_position = project_point(self.panda_x, self.panda_y + 0.4, self.panda_z)
            
            # Mouth position
            self.mouth_position = project_point(self.panda_x, self.panda_y + 0.35, self.panda_z + 0.23)
            
            # Feet positions
            self.left_foot_position = project_point(
                self.panda_x - 0.15, self.panda_y - 0.3, self.panda_z
            )
            self.right_foot_position = project_point(
                self.panda_x + 0.15, self.panda_y - 0.3, self.panda_z
            )
            
            # Hand positions (for tapping/grabbing interactions)
            self.left_hand_position = project_point(
                self.panda_x - 0.25, self.panda_y + 0.05, self.panda_z
            )
            self.right_hand_position = project_point(
                self.panda_x + 0.25, self.panda_y + 0.05, self.panda_z
            )
        except Exception as _e:
            logger.debug("Overlay: body-part projection failed (GL state not ready): %s", _e)
    
    def _update_frame(self):
        """Update animation, physics, AI behavior and request repaint - 60 FPS."""
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - getattr(self, '_last_update_time', current_time)
        self._last_update_time = current_time
        
        # Cap delta time to prevent huge jumps
        delta_time = min(delta_time, 0.1)
        
        # Update animation phase
        self.animation_phase += 0.1
        
        # Update squash factor (smooth transition)
        if self.squash_factor != self.squash_target:
            diff = self.squash_target - self.squash_factor
            self.squash_factor += diff * 0.1
        
        # Update AI behavior and autonomous movement
        self.autonomous_behavior_update(delta_time)
        
        # Update 3D items physics
        self._update_items_physics(delta_time)
        
        # Apply physics to panda
        self.panda_y += self.velocity_y * delta_time
        self.velocity_y -= self.gravity * delta_time
        
        # Ground collision
        if self.panda_y < -0.5:
            self.panda_y = -0.5
            self.velocity_y = 0.0
        
        # Detect widget under panda for shadow rendering
        if self.main_window:
            widget_at_panda = self._detect_widget_at_position(
                self.head_position.x(), self.head_position.y()
            )
            if widget_at_panda != self.widget_below:
                self.widget_below = widget_at_panda
        
        # Trigger redraw (OpenGL rendering at 60fps)
        self.update()
        
        # Emit panda position signal
        if self.panda_moved:
            screen_pos = self._world_to_screen(self.panda_x, self.panda_y, self.panda_z)
            self.panda_moved.emit(screen_pos.x(), screen_pos.y())
    
    def _world_to_screen(self, x, y, z):
        """Convert 3D world coordinates to 2D screen coordinates."""
        try:
            model_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
            proj_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
            viewport = glGetIntegerv(GL_VIEWPORT)
            screen_pos = gluProject(x, y, z, model_matrix, proj_matrix, viewport)
            return QPoint(int(screen_pos[0]), int(viewport[3] - screen_pos[1]))
        except Exception as _e:
            logger.debug("Overlay: world-to-screen projection failed: %s", _e)
            return QPoint(self.width() // 2, self.height() // 2)
    
    def mousePressEvent(self, event):
        """Handle mouse press - check if clicking on panda."""
        # Check if click is on panda
        click_pos = event.pos()
        
        # Simple bounding box check
        head_rect = QRect(
            self.head_position.x() - 50,
            self.head_position.y() - 50,
            100, 100
        )
        
        if head_rect.contains(click_pos):
            self.mouse_on_panda = True
            event.accept()
        else:
            # Pass through to widgets below
            self.mouse_on_panda = False
            event.ignore()
    
    def set_panda_position(self, x, y, z):
        """Set panda position in 3D space."""
        self.panda_x = x
        self.panda_y = y
        self.panda_z = z
    
    def set_animation_state(self, state):
        """Set panda animation state."""
        self.animation_state = state
        self.animation_phase = 0.0
    
    def apply_squash_effect(self, factor):
        """Apply squash effect (for landing, pressing widgets)."""
        self.squash_target = factor
    
    def set_widget_below(self, widget):
        """Set the widget currently below panda (for shadow rendering)."""
        self.widget_below = widget
    
    def get_head_position(self):
        """Get head position in screen coordinates."""
        return self.head_position
    
    def get_mouth_position(self):
        """Get mouth position in screen coordinates."""
        return self.mouth_position
    
    def get_feet_positions(self):
        """Get feet positions in screen coordinates."""
        return self.left_foot_position, self.right_foot_position

    # ── Delegation helpers: forward interaction calls to the 3D GL widget ──
    def _gl(self):
        """Return the live PandaOpenGLWidget via main_window, or None."""
        try:
            return getattr(self.main_window, 'panda_widget', None)
        except Exception:
            return None

    def start_bite_tab(self):
        """Trigger jaw-open bite animation on the 3D GL widget."""
        gl = self._gl()
        if gl and hasattr(gl, 'start_bite_tab'):
            gl.start_bite_tab()
        else:
            self.set_animation_state('waving')

    def notify_button_nearby(self):
        """Alert the 3D GL widget that a button is nearby."""
        gl = self._gl()
        if gl and hasattr(gl, 'notify_button_nearby'):
            gl.notify_button_nearby()
        else:
            self.set_animation_state('waving')

    def notify_file_dragged(self, file_path: str):
        """Alert the 3D GL widget that a file is being dragged nearby."""
        gl = self._gl()
        if gl and hasattr(gl, 'notify_file_dragged'):
            gl.notify_file_dragged(file_path)
        else:
            self.set_animation_state('crawling')

    def start_sit_on_panel(self):
        """Make the 3D GL widget sit on a panel."""
        gl = self._gl()
        if gl and hasattr(gl, 'start_sit_on_panel'):
            gl.start_sit_on_panel()
        else:
            self.set_animation_state('sitting_back')

    def start_hug_window(self):
        """Make the 3D GL widget hug a window edge."""
        gl = self._gl()
        if gl and hasattr(gl, 'start_hug_window'):
            gl.start_hug_window()
        else:
            self.set_animation_state('climbing_wall')

    def set_micro_emotion(self, emotion_name: str, weight: float = 0.8):
        """Delegate micro-emotion to the 3D GL widget."""
        gl = self._gl()
        if gl and hasattr(gl, 'set_micro_emotion'):
            gl.set_micro_emotion(emotion_name, weight)

    # ===========================
    # UI INTERACTION SYSTEM
    # ===========================
    
    def _update_collision_map(self):
        """
        Update collision map with current widget geometries.
        This allows panda to detect and interact with UI elements.
        """
        if not self.main_window:
            return
        
        self.collision_map.clear()
        
        # Recursively find all widgets in main window
        all_widgets = self.main_window.findChildren(QWidget)
        
        for widget in all_widgets:
            if not widget.isVisible():
                continue
            
            # Get widget geometry in global coordinates
            global_pos = widget.mapToGlobal(QPoint(0, 0))
            global_rect = QRect(global_pos, widget.size())
            
            # Store in collision map with widget reference
            self.collision_map[widget] = global_rect
    
    def _detect_widget_at_position(self, screen_x, screen_y):
        """
        Detect which widget is at the given screen position.
        Returns the widget or None.
        """
        test_point = QPoint(screen_x, screen_y)
        
        # Check collision map (sorted by z-order, topmost first)
        for widget, rect in self.collision_map.items():
            if rect.contains(test_point):
                return widget
        
        return None
    
    def _interact_with_widget(self, widget, interaction_type='click'):
        """
        Panda interacts with a widget.
        
        Args:
            widget: The widget to interact with
            interaction_type: 'bite', 'jump', 'tap', 'click'
        """
        if not widget or not widget.isVisible():
            return
        
        self.interaction_target = widget
        self.interaction_animation = interaction_type
        
        # Set animation based on interaction type
        if interaction_type == 'bite':
            # Panda moves mouth to widget and bites
            self.set_animation_state('biting')
            widget_center = widget.mapToGlobal(widget.rect().center())
            # Move panda mouth toward widget
            self._move_panda_to(widget_center.x(), widget_center.y())
            # Trigger click after animation delay
            QTimer.singleShot(self.BITE_ANIMATION_DELAY, lambda: self._trigger_widget_click(widget))
            
        elif interaction_type == 'jump':
            # Panda jumps on widget
            self.set_animation_state('jumping')
            self.velocity_y = 3.0  # Jump velocity
            # Apply squash effect when landing
            QTimer.singleShot(self.JUMP_LAND_DELAY, lambda: self.apply_squash_effect(0.7))
            QTimer.singleShot(self.JUMP_RECOVER_DELAY, lambda: self.apply_squash_effect(1.0))
            # Trigger click at peak of jump
            QTimer.singleShot(self.JUMP_START_DELAY, lambda: self._trigger_widget_click(widget))
            
        elif interaction_type == 'tap':
            # Panda taps widget with paw
            self.set_animation_state('tapping')
            # Playful bounce animation
            self.velocity_y = 1.0
            # Trigger click immediately
            QTimer.singleShot(self.TAP_ANIMATION_DELAY, lambda: self._trigger_widget_click(widget))
            
        else:  # Default click
            self._trigger_widget_click(widget)
    
    def _trigger_widget_click(self, widget):
        """
        Programmatically trigger a click on the widget.
        This makes panda actually interact with the UI.
        """
        try:
            if hasattr(widget, 'click'):
                # It's a button or clickable widget
                widget.click()
                logger.info(f"Panda clicked {widget.__class__.__name__}")
                
                # Emit signal
                if self.panda_triggered_button:
                    self.panda_triggered_button.emit(widget)
                
                # Visual feedback: squash effect
                self.apply_squash_effect(0.85)
                QTimer.singleShot(self.SQUASH_EFFECT_DURATION, lambda: self.apply_squash_effect(1.0))
                
            elif hasattr(widget, 'setCurrentIndex'):
                # It's a tab widget or combo box
                current = widget.currentIndex()
                next_index = (current + 1) % widget.count()
                widget.setCurrentIndex(next_index)
                logger.info(f"Panda changed tab/index on {widget.__class__.__name__}")
                
            elif hasattr(widget, 'setValue'):
                # It's a slider or spin box
                current = widget.value()
                widget.setValue(current + 1)
                logger.info(f"Panda adjusted {widget.__class__.__name__}")
                
        except Exception as e:
            logger.warning(f"Could not trigger widget: {e}")
    
    def _move_panda_to(self, screen_x, screen_y):
        """
        Move panda toward a screen position.
        This is simplified - real implementation would use pathfinding.
        """
        # Convert screen coordinates to 3D world coordinates
        # This is an approximation
        self.target_position = (
            (screen_x - self.width() / 2) / 200.0,  # Normalize to world space
            self.panda_y,
            (screen_y - self.height() / 2) / 200.0
        )
    
    def autonomous_behavior_update(self, delta_time):
        """
        Update panda's autonomous behavior and AI decision-making.
        
        Args:
            delta_time: Time since last update in seconds
        """
        current_time = time.time()
        
        # Check if it's time for a new behavior
        if current_time >= self.next_behavior_time:
            self._decide_next_behavior()
            self.next_behavior_time = current_time + random.uniform(
                self.MIN_BEHAVIOR_INTERVAL, self.MAX_BEHAVIOR_INTERVAL
            )
        
        # Execute current behavior
        if self.behavior_state == 'walking' and self.target_position:
            # Walk toward target
            dx = self.target_position[0] - self.panda_x
            dz = self.target_position[2] - self.panda_z
            distance = math.sqrt(dx * dx + dz * dz)
            
            if distance > 0.1:
                # Normalize and move
                self.panda_x += (dx / distance) * self.walk_speed * delta_time
                self.panda_z += (dz / distance) * self.walk_speed * delta_time
                self.set_animation_state('walking')
                
                # Face direction of movement
                self.panda_rotation = math.degrees(math.atan2(dx, dz))
            else:
                # Reached target
                self.behavior_state = 'idle'
                self.set_animation_state('idle')
                self.target_position = None
                
        elif self.behavior_state == 'interacting':
            # Interact with nearby widget
            head_widget = self._detect_widget_at_position(
                self.head_position.x(), self.head_position.y()
            )
            
            if head_widget:
                # Choose random interaction type
                interaction_type = random.choice(['bite', 'jump', 'tap'])
                self._interact_with_widget(head_widget, interaction_type)
                
            self.behavior_state = 'idle'
            
        elif self.behavior_state == 'investigating':
            # Look around at nearby widgets
            self.set_animation_state('curious')
            # Rotate slowly
            self.panda_rotation += 30.0 * delta_time
            
            # Check if there's something interesting nearby
            if random.random() < self.INVESTIGATION_TRIGGER_CHANCE:
                self.behavior_state = 'interacting'
        
        # crawling / climbing_wall states are driven by QTimer in _decide_next_behavior;
        # no continuous per-tick logic required here.
    
    def _decide_next_behavior(self):
        """Decide what panda should do next based on AI."""
        behaviors = list(self.BEHAVIOR_WEIGHTS.keys())
        weights = list(self.BEHAVIOR_WEIGHTS.values())
        
        self.behavior_state = random.choices(behaviors, weights=weights)[0]
        
        if self.behavior_state == 'walking':
            # Pick random target position
            self.target_position = (
                random.uniform(-2.0, 2.0),
                self.panda_y,
                random.uniform(-2.0, 2.0)
            )
        elif self.behavior_state == 'crawling':
            self.set_animation_state('crawling')
            # Return to idle after a short crawl — guard so a later state wins
            dur = int(random.uniform(1500, 3500))
            QTimer.singleShot(dur, lambda: (self.animation_state == 'crawling'
                                            and self.set_animation_state('idle')))
            self.behavior_state = 'idle'   # prevent re-entry next tick
        elif self.behavior_state == 'climbing_wall':
            self.set_animation_state('climbing_wall')
            fall_ms = int(random.uniform(1000, 2500))
            idle_ms = fall_ms + int(random.uniform(800, 1800))
            QTimer.singleShot(fall_ms, lambda: (self.animation_state == 'climbing_wall'
                                                and self.set_animation_state('falling_back')))
            QTimer.singleShot(idle_ms, lambda: (self.animation_state == 'falling_back'
                                                and self.set_animation_state('idle')))
            self.behavior_state = 'idle'   # prevent re-entry
    
    # ===========================
    # 3D ITEMS RENDERING
    # ===========================
    
    def add_item_3d(self, item_type, position=(0, 0, 0)):
        """
        Add a 3D item (toy, food, clothing) to the overlay.
        Items are rendered with OpenGL, NOT canvas.
        
        Args:
            item_type: Type of item ('toy', 'food', 'clothing')
            position: 3D position (x, y, z)
        """
        item_data = {
            'type': item_type,
            'position': list(position),
            'rotation': 0.0,
            'scale': 1.0,
            'velocity': [0.0, 0.0, 0.0],
            'physics_enabled': True
        }
        self.items_3d.append(item_data)
        logger.info(f"Added 3D {item_type} at {position} - OpenGL rendering")
    
    def remove_item_3d(self, item_index):
        """Remove a 3D item from the overlay."""
        if 0 <= item_index < len(self.items_3d):
            del self.items_3d[item_index]
    
    def _render_items_3d(self):
        """
        Render all 3D items with OpenGL hardware acceleration.
        Items include toys, food, and clothing accessories.
        """
        for item in self.items_3d:
            glPushMatrix()
            
            # Position and rotate item
            pos = item['position']
            glTranslatef(pos[0], pos[1], pos[2])
            glRotatef(item['rotation'], 0.0, 1.0, 0.0)
            glScalef(item['scale'], item['scale'], item['scale'])
            
            # Render based on type
            if item['type'] == 'toy':
                self._render_toy_3d(item)
            elif item['type'] == 'food':
                self._render_food_3d(item)
            elif item['type'] == 'clothing':
                self._render_clothing_3d(item)
            
            glPopMatrix()
    
    def _render_toy_3d(self, item):
        """Render a 3D toy with OpenGL (NOT canvas)."""
        # Example: Render a colorful ball
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 0.3, 0.3, 1.0])
        self._draw_sphere(0.0, 0.0, 0.0, 0.15)
    
    def _render_food_3d(self, item):
        """Render 3D food with OpenGL (NOT canvas)."""
        # Example: Render bamboo stick
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.4, 0.8, 0.3, 1.0])
        # Draw cylinder for bamboo
        quadric = gluNewQuadric()
        glRotatef(90, 1.0, 0.0, 0.0)
        gluCylinder(quadric, 0.05, 0.05, 0.3, 16, 1)
        gluDeleteQuadric(quadric)
    
    def _render_clothing_3d(self, item):
        """Render 3D clothing accessory with OpenGL (NOT canvas)."""
        # Example: Render a hat
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.8, 0.2, 0.8, 1.0])
        # Hat brim (flat disk)
        quadric = gluNewQuadric()
        gluDisk(quadric, 0.0, 0.2, 20, 1)
        # Hat top (cone)
        glTranslatef(0.0, 0.0, 0.05)
        gluCylinder(quadric, 0.15, 0.0, 0.2, 16, 1)
        gluDeleteQuadric(quadric)
    
    def _update_items_physics(self, delta_time):
        """Update physics for all 3D items."""
        for item in self.items_3d:
            if not item['physics_enabled']:
                continue
            
            # Apply gravity
            item['velocity'][1] -= self.gravity * delta_time
            
            # Update position
            item['position'][0] += item['velocity'][0] * delta_time
            item['position'][1] += item['velocity'][1] * delta_time
            item['position'][2] += item['velocity'][2] * delta_time
            
            # Ground collision
            if item['position'][1] < -0.8:
                item['position'][1] = -0.8
                item['velocity'][1] = -item['velocity'][1] * self.bounce_damping
                
                # Stop bouncing if velocity too low
                if abs(item['velocity'][1]) < 0.1:
                    item['velocity'][1] = 0.0
            
            # Apply friction
            item['velocity'][0] *= self.friction
            item['velocity'][2] *= self.friction
            
            # Rotate item as it moves
            if abs(item['velocity'][0]) > 0.01 or abs(item['velocity'][2]) > 0.01:
                item['rotation'] += 100.0 * delta_time

# Convenience function
def create_transparent_overlay(parent, main_window=None):
    """
    Create and configure a transparent panda overlay with full UI interaction.
    
    The overlay renders panda and all items (toys, food, clothes) using OpenGL
    with hardware acceleration. NO canvas drawing is used.
    
    Args:
        parent: Parent widget for the overlay
        main_window: Main window reference for widget detection and interaction
    
    Returns:
        TransparentPandaOverlay instance or None if PyQt6/OpenGL not available
    """
    if not PYQT_AVAILABLE:
        logger.warning("PyQt6/OpenGL not available, cannot create overlay")
        return None
    
    overlay = TransparentPandaOverlay(parent, main_window)
    overlay.resize(parent.size())
    overlay.show()
    overlay.raise_()  # Ensure it's on top
    
    return overlay
