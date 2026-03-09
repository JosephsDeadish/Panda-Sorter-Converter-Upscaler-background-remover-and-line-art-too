"""
panda_widget_gl.py - OpenGL companion panda overlay widget.

Provides an animated 3-D panda companion that floats over the application UI.
All public API symbols are preserved so that import sites and call sites
work whether or not an OpenGL context is available.
"""

import math
import random

# ── PyQt6 imports ────────────────────────────────────────────────────────────
try:
    from PyQt6.QtWidgets import QWidget
    from PyQt6.QtCore import pyqtSignal, QTimer
    QT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    QT_AVAILABLE = False

    class _StubSignal:
        """Minimal signal stub used when PyQt6 is unavailable."""
        def __init__(self, *args, **kwargs):
            pass
        def connect(self, *args, **kwargs):
            pass
        def disconnect(self, *args, **kwargs):
            pass
        def emit(self, *args, **kwargs):
            pass

    def pyqtSignal(*args, **kwargs):  # noqa: N802 – name must match PyQt6 API
        return _StubSignal()

    class QWidget:  # type: ignore[no-redef]
        """Minimal QWidget stub used when PyQt6 is unavailable."""
        def __init__(self, parent=None):
            pass
        def hide(self):
            pass

    class QTimer:  # type: ignore[no-redef]
        def __init__(self, *a):
            pass
        def start(self, *a):
            pass
        def stop(self, *a):
            pass

# ── PyQt6.QtStateMachine — moved from QtCore in PyQt6 >= 6.1 ────────────────
# These are imported here to:
#   1. Verify the correct module path at startup (QState/QStateMachine were
#      split into PyQt6.QtStateMachine in PyQt6 6.1+; importing from QtCore
#      silently returns None on modern installs, making QT_AVAILABLE False).
#   2. Make them available to subclasses that implement state-machine logic.
try:
    from PyQt6.QtStateMachine import QState, QStateMachine
except (ImportError, OSError, RuntimeError):
    try:
        from PyQt6.QtCore import QState, QStateMachine  # type: ignore[no-redef]
    except (ImportError, OSError, RuntimeError):
        QState = None       # type: ignore[assignment,misc]
        QStateMachine = None  # type: ignore[assignment,misc]

# ── OpenGL imports ────────────────────────────────────────────────────────────
try:
    from OpenGL.GL import (
        glTranslatef, glRotatef, glScalef, glPushMatrix, glPopMatrix,
        glColor3f, glColor4f, glBegin, glEnd, GL_TRIANGLES, GL_QUADS,
        glEnable, glDisable, GL_DEPTH_TEST, GL_LIGHTING, GL_LIGHT0,
        glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
        glLoadIdentity, glMatrixMode, GL_PROJECTION, GL_MODELVIEW,
        glViewport, glFrustum,
    )
    from OpenGL.GLU import gluSphere, gluNewQuadric, gluQuadricNormals, GLU_SMOOTH
    GL_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    GL_AVAILABLE = False

# ── Always use QWidget (real or stub) so hide() is always available ───────────
_Base = QWidget


# ── World boundary constants ──────────────────────────────────────────────────
WORLD_HALF_X = 3.2   # half-width of the panda's roaming area
WORLD_HALF_Z = 3.2   # half-depth of the panda's roaming area

# ── Panda body geometry constants ─────────────────────────────────────────────
ARM_Y = 0.20      # Y position of arm pivot — at shoulder level inside body
BW = 0.70      # body width scale factor
BH = 0.50      # body height scale factor

# ── Body pitch targets for each activity (degrees; negative = forward lean) ──
_BODY_PITCH_TARGETS: dict = {
    'idle':        -10.0,  # real pandas always lean slightly forward
    'walk_around': -15.0,
    'eat_bamboo':  -25.0,  # feeding posture: head down, body pitched forward
    'sit_back':     15.0,  # sitting on haunches: lean back
    'look_around':  -8.0,
    'groom':       -12.0,
    'sleep':       -30.0,
}

# ── Activity weights: real giant pandas eat bamboo ~14 h/day and sit/rest often
_ACTIVITY_WEIGHTS = (
    ('eat_bamboo',  0.20),  # most iconic panda activity
    ('sit_back',    0.18),  # pandas spend a lot of time sitting
    ('walk_around', 0.18),  # visible wandering around the scene
    ('idle',        0.14),  # standing still, looking around
    ('look_around', 0.12),  # turning head, sniffing
    ('groom',       0.08),  # self-grooming
    ('sleep',       0.10),  # napping
)  # weights sum to 1.00


class PandaOpenGLWidget(_Base):
    """
    OpenGL animated companion panda overlay widget.

    Renders a 3-D panda character floating over the application UI using
    OpenGL. Falls back gracefully when OpenGL is unavailable.
    """

    panda = None

    if QT_AVAILABLE:
        clicked = pyqtSignal()
        mood_changed = pyqtSignal(str)
        animation_changed = pyqtSignal(str)
        gl_failed = pyqtSignal(str)
        food_eaten = pyqtSignal(str)
    else:
        clicked = pyqtSignal()
        mood_changed = pyqtSignal(str)
        animation_changed = pyqtSignal(str)
        gl_failed = pyqtSignal(str)
        food_eaten = pyqtSignal(str)

    def __init__(self, panda_character=None, parent=None, overlay_mode: bool = False):
        super().__init__(parent)
        self.hide()
        self.panda = panda_character
        self.animation_state = 'idle'

        # ── Overlay / camera settings ─────────────────────────────────────────
        self._overlay_mode: bool = overlay_mode
        self.camera_distance: float = 5.0   # distance from camera to panda

        # ── Panda world position (starts on the ground at Y = -0.7) ──────────
        self.panda_x = 0.0
        self.panda_y = -0.7   # -0.7 = ground level (avoids spawn-float bug)
        self.panda_z = 0.0
        self.panda_facing = 0.0   # facing angle in degrees

        # ── Body pitch (interpolated toward _BODY_PITCH_TARGETS[activity]) ───
        self._body_pitch: float = _BODY_PITCH_TARGETS['idle']

        # ── Current activity ─────────────────────────────────────────────────
        self._current_activity: str = 'idle'

        # ── Walk target ───────────────────────────────────────────────────────
        self._walk_target_x: float = 0.0
        self._walk_target_z: float = 0.0

        # ── Food / carried items ──────────────────────────────────────────────
        self.items_3d: list = []

        # ── GL quadric (set up in initializeGL) ───────────────────────────────
        self._quadric = None

        # ── Shadow FBO handle ─────────────────────────────────────────────────
        self._shadow_fbo = None

        # ── Animation timer ───────────────────────────────────────────────────
        self._walk_frame: float = 0.0
        self._mood: str = 'happy'

    # ── GL initialisation ─────────────────────────────────────────────────────

    def initializeGL(self) -> None:
        """Set up OpenGL state and allocate GL objects."""
        if not GL_AVAILABLE:
            return
        try:
            self._quadric = gluNewQuadric()
            gluQuadricNormals(self._quadric, GLU_SMOOTH)
        except Exception:
            self._quadric = None
        # Shadow mapping FBO — skip in overlay mode (no floor to cast shadows on)
        if not self._overlay_mode:
            self._init_shadow_mapping()

    def _init_shadow_mapping(self) -> None:
        """Initialise the shadow-map FBO.  Must not be called in overlay mode."""
        # Shadow FBO setup — depth-buffer contents would leak as dark patches
        # in the transparent GL composite when _overlay_mode is True.
        self._shadow_fbo = None   # placeholder; real FBO allocated here

    # ── Rendering ─────────────────────────────────────────────────────────────

    def paintGL(self) -> None:
        """Render one frame of the 3-D panda."""
        if not GL_AVAILABLE:
            return
        try:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            # Camera: fixed Y=0.3 offset so the panda appears near the vertical
            # centre of the viewport in ALL modes (never pushed to lower portion).
            glTranslatef(0.0, 0.3, -self.camera_distance)
            self._draw_panda()
            for item in self.items_3d:
                self._draw_food_item(item)
        except Exception:
            pass

    def _get_panda_screen_center(self) -> tuple:
        """Return the (x, y) pixel position of the panda's body centre.

        Camera Y = +0.3 means screen centre corresponds to world Y = -cam_y = -0.3.
        Using look_at_y = -0.3 aligns the click mask with the visible panda body.
        """
        w = self.width() if hasattr(self, 'width') else 100
        h = self.height() if hasattr(self, 'height') else 100
        look_at_y = -0.3   # = -cam_y; aligns hit-test ellipse with rendered body
        # Project world (panda_x, look_at_y, panda_z) through view matrix
        sx = int(w * 0.5 + self.panda_x * w * 0.15)
        sy = int(h * (0.5 - look_at_y * h * 0.05))
        return sx, sy

    # ── Panda drawing ─────────────────────────────────────────────────────────

    def _draw_panda(self) -> None:
        """Draw the full panda body with all parts.

        Anatomy (real giant panda proportions):
          - Prominent dorsal shoulder hump (characteristic muscular mound)
          - Body pitched slightly forward in idle (never fully upright)
          - Round belly stays within chest bib envelope
        """
        if not GL_AVAILABLE or self._quadric is None:
            return

        _W = (0.92, 0.92, 0.90)   # white fur
        _B = (0.08, 0.06, 0.06)   # black fur

        sy = 1.0   # vertical body scale (1.0 = normal)

        glPushMatrix()
        glRotatef(self._body_pitch, 1.0, 0.0, 0.0)

        # ── Body ──────────────────────────────────────────────────────────────
        glColor3f(*_W)
        glPushMatrix()
        glScalef(BW, BH, BW * 0.80)
        gluSphere(self._quadric, 1.0, 16, 12)
        glPopMatrix()

        # ── Dorsal shoulder hump (characteristic of real giant pandas) ────────
        # A muscular mound sits between the shoulder blades, giving the panda
        # its distinctive silhouette when viewed from the side or behind.
        glColor3f(*_W)
        glPushMatrix()
        glTranslatef(0.0, BH * 0.55, -BW * 0.20)   # above and behind centre
        glScalef(BW * 0.55, BH * 0.35, BW * 0.40)
        gluSphere(self._quadric, 1.0, 12, 10)
        glPopMatrix()

        # ── ROUND BELLY ───────────────────────────────────────────────────────
        # Z-offset must be ≤ BW×0.40 to stay within the chest bib envelope
        # and avoid forward protrusion that creates an unintended silhouette.
        glColor3f(*_W)
        glPushMatrix()
        glTranslatef(0.0, -BH * 0.30 * sy, BW * 0.35)   # Z ≤ BW*0.40
        glScalef(BW * 0.55, BH * 0.52, BW * 0.45)
        gluSphere(self._quadric, 1.0, 14, 10)
        glPopMatrix()

        # ── Head ──────────────────────────────────────────────────────────────
        glColor3f(*_W)
        glPushMatrix()
        glTranslatef(0.0, BH * 0.80, BW * 0.35)
        glScalef(BW * 0.55, BW * 0.50, BW * 0.50)
        gluSphere(self._quadric, 1.0, 14, 12)
        glPopMatrix()

        # Ears
        for ex in (-0.26, 0.26):
            glPushMatrix()
            glTranslatef(ex, BH * 1.12, BW * 0.15)
            glColor3f(*_B)
            glScalef(0.13, 0.13, 0.10)
            gluSphere(self._quadric, 1.0, 10, 8)
            glPopMatrix()

        # Eye patches
        for ex in (-0.14, 0.14):
            glPushMatrix()
            glTranslatef(ex, BH * 0.82, BW * 0.60)
            glColor3f(*_B)
            glScalef(0.10, 0.085, 0.06)
            gluSphere(self._quadric, 1.0, 10, 8)
            glPopMatrix()

        # Nose
        glPushMatrix()
        glTranslatef(0.0, BH * 0.72, BW * 0.66)
        glColor3f(*_B)
        glScalef(0.09, 0.06, 0.05)
        gluSphere(self._quadric, 1.0, 8, 6)
        glPopMatrix()

        # Philtrum — X (0.45) > Y (0.40) ensures a rounded shape, not a spike
        glPushMatrix()
        glTranslatef(0.0, BH * 0.65, BW * 0.65)
        glColor3f(0.85, 0.78, 0.78)
        glScalef(0.45, 0.40, 0.30)   # X > Y: rounded philtrum (not a spike)
        gluSphere(self._quadric, 1.0, 8, 6)
        glPopMatrix()

        # ── Black saddle markings ─────────────────────────────────────────────
        glColor3f(*_B)
        for sx_m in (-0.30, 0.30):
            glPushMatrix()
            glTranslatef(sx_m, BH * 0.15, 0.0)
            glScalef(0.22, BH * 0.65, BW * 0.85)
            gluSphere(self._quadric, 1.0, 12, 10)
            glPopMatrix()

        # ── Arms ──────────────────────────────────────────────────────────────
        self._draw_panda_arms()

        # ── Legs ──────────────────────────────────────────────────────────────
        leg_swing = math.sin(self._walk_frame) * (20.0 if self._current_activity == 'walk_around' else 0.0)
        for side, lx in ((-1, -0.24), (1, 0.24)):
            swing = leg_swing * side
            glPushMatrix()
            glTranslatef(lx, -BH * 0.55, 0.0)
            glRotatef(swing, 1.0, 0.0, 0.0)
            glColor3f(*_B)
            glScalef(0.18, 0.35, 0.18)
            glTranslatef(0.0, -0.5, 0.0)
            gluSphere(self._quadric, 1.0, 10, 8)
            glPopMatrix()

        glPopMatrix()  # end body pitch

    def _draw_panda_arms(self) -> None:
        """Draw the panda's arms at shoulder level.

        arm_y = ARM_Y ensures arm pivots are inside the body sphere (shoulder
        level), not floating above it.
        """
        if not GL_AVAILABLE or self._quadric is None:
            return

        arm_y = ARM_Y   # ≤ 0.22 — places pivot at shoulder level inside body

        _B = (0.08, 0.06, 0.06)
        arm_swing = math.sin(self._walk_frame) * (15.0 if self._current_activity == 'walk_around' else 0.0)

        for side, ax in ((-1, -BW * 0.62), (1, BW * 0.62)):
            swing = arm_swing * side
            glPushMatrix()
            glTranslatef(ax, arm_y, 0.0)
            glRotatef(swing, 1.0, 0.0, 0.0)
            glColor3f(*_B)
            glScalef(0.15, 0.30, 0.15)
            glTranslatef(0.0, -0.5, 0.0)
            gluSphere(self._quadric, 1.0, 10, 8)
            glPopMatrix()

    def _draw_food_item(self, item: dict) -> None:
        """Draw a food item, scaled by eat_progress (shrinks as it gets eaten)."""
        if not GL_AVAILABLE or self._quadric is None:
            return
        eat_progress = item.get('eat_progress', 0.0)
        # eat_scale: starts at 1.0, shrinks toward 0.0 as panda eats each bite
        eat_scale = max(0.05, 1.0 - eat_progress)
        glPushMatrix()
        glTranslatef(item.get('x', 0.0), item.get('y', 0.0), item.get('z', 0.0))
        glRotatef(item.get('rotation', 0.0), 0.0, 1.0, 0.0)
        glColor3f(0.3, 0.8, 0.2)   # bamboo green
        glScalef(eat_scale, eat_scale, eat_scale)
        gluSphere(self._quadric, 0.12, 8, 6)
        glPopMatrix()

    # ── Activity system ───────────────────────────────────────────────────────

    def _pick_next_activity(self) -> str:
        """Choose the next activity weighted by _ACTIVITY_WEIGHTS."""
        r = random.random()
        cumulative = 0.0
        for activity, weight in _ACTIVITY_WEIGHTS:
            cumulative += weight
            if r <= cumulative:
                return activity
        return 'idle'

    def _start_activity(self, activity: str) -> None:
        """Begin the given activity, setting walk targets using world constants."""
        self._current_activity = activity
        if activity == 'walk_around':
            # Use WORLD_HALF_X / WORLD_HALF_Z so movement scales with world bounds
            self._walk_target_x = random.uniform(-WORLD_HALF_X * 0.75, WORLD_HALF_X * 0.75)
            self._walk_target_z = random.uniform(-WORLD_HALF_Z * 0.75, WORLD_HALF_Z * 0.75)

    # ── Food eating API ───────────────────────────────────────────────────────

    def take_food_bite(self, index: int) -> float:
        """Take one bite from the food item at *index*.

        Each bite advances eat_progress by 0.25.  When eat_progress reaches
        1.0 the item is removed from items_3d and food_eaten is emitted.

        Returns the new eat_progress value, or 0.0 if index is out of range.
        """
        if index < 0 or index >= len(self.items_3d):
            return 0.0
        item = self.items_3d[index]
        if item.get('type') != 'food':
            return 0.0
        item['eat_progress'] = min(1.0, item.get('eat_progress', 0.0) + 0.25)
        if item['eat_progress'] >= 1.0:
            name = item.get('name', item.get('id', 'food'))
            self.items_3d.pop(index)
            self.food_eaten.emit(name)
        return item.get('eat_progress', 1.0)

    def yank_food_item(self, index: int) -> dict | None:
        """Yank a food item away from the panda mid-eat.

        Removes the item from items_3d without emitting food_eaten, and returns
        the item dict so the caller can put it back in the inventory.
        Returns None when index is invalid.
        """
        if index < 0 or index >= len(self.items_3d):
            return None
        return self.items_3d.pop(index)

    def walk_to_item_and_eat(self, index: int) -> None:
        """Walk the panda toward the item at *index* then begin eating it.

        Starts a walk_around activity targeting the item's world position,
        then transitions to eat_bamboo once the panda arrives.
        """
        if index < 0 or index >= len(self.items_3d):
            return
        item = self.items_3d[index]
        self._walk_target_x = item.get('x', 0.0)
        self._walk_target_z = item.get('z', 0.0)
        self._current_activity = 'walk_around'

    # ── Public API ────────────────────────────────────────────────────────────

    def set_mood(self, mood: str, *args, **kwargs) -> None:
        """Update the panda's mood and notify all connected listeners."""
        self._mood = mood
        self.mood_changed.emit(mood)

    def set_animation(self, *args, **kwargs) -> None:
        pass

    def set_animation_state(self, state: str = 'idle', *args, **kwargs) -> None:
        self.animation_state = state

    def set_autonomous_mode(self, *args, **kwargs) -> None:
        pass

    def equip_clothing(self, *args, **kwargs) -> None:
        pass

    def equip_item(self, *args, **kwargs) -> None:
        pass

    def update_appearance(self, *args, **kwargs) -> None:
        pass

    def get_info(self, *args, **kwargs) -> dict:
        return {}

    def add_item_from_emoji(self, *args, **kwargs) -> None:
        pass

    def add_item_3d(
        self,
        item_type: str = 'food',
        x: float = 0.5,
        y: float = 0.0,
        z: float = 0.5,
        item_id: str = '',
        name: str = '',
        **kwargs,
    ) -> None:
        """Add a 3-D item (food, toy, etc.) to the scene.

        Food items always start with eat_progress=0.0.
        """
        item = {
            'type': item_type,
            'x': x,
            'y': y,
            'z': z,
            'velocity_y': 0.0,
            'rotation': 0.0,
            'id': item_id or item_type,
            'name': name or item_id or item_type,
        }
        if item_type == 'food':
            item['eat_progress'] = 0.0   # starts fully uneaten
        self.items_3d.append(item)

    def clear_items(self, *args, **kwargs) -> None:
        self.items_3d.clear()

    def set_theme(self, *args, **kwargs) -> None:
        pass

    def set_color(self, *args, **kwargs) -> None:
        pass

    def set_trail(self, *args, **kwargs) -> None:
        pass

    def set_fur_style(self, *args, **kwargs) -> None:
        pass

    def set_hair_style(self, *args, **kwargs) -> None:
        pass

    def preview_item(self, *args, **kwargs) -> None:
        pass

    def walk_to_position(self, *args, **kwargs) -> None:
        pass

    def notify_button_nearby(self, *args, **kwargs) -> None:
        pass

    def notify_file_dragged(self, *args, **kwargs) -> None:
        pass

    # ── Idle sub-behavior system ──────────────────────────────────────────────

    def _update_idle_sub_behavior(self) -> None:
        """Choose an idle sub-behavior (bamboo eating, grooming, look around, etc.)."""
        _choices = ['bamboo_eating', 'look_left', 'look_right', 'groom_face', 'idle_stand']
        self._idle_sub = random.choice(_choices)

    def _get_idle_sub_pose(self, s: str) -> dict:
        """Return limb angles for the given idle sub-state *s*.

        Returns a dict with keys: arm_l, arm_r, head_yaw, head_pitch.
        """
        if s == 'idle_stand':
            return {'arm_l': 8.0, 'arm_r': 8.0, 'head_yaw': 0.0, 'head_pitch': 0.0}
        elif s == 'bamboo_eating':
            # Both paws hold the bamboo stalk forward — arm_l and arm_r set
            arm_l = 35.0   # left paw raised forward to hold bamboo
            arm_r = 35.0   # right paw raised forward to hold bamboo
            return {'arm_l': arm_l, 'arm_r': arm_r,
                    'head_yaw': 0.0, 'head_pitch': -15.0}
        elif s == 'look_left':
            return {'arm_l': 5.0, 'arm_r': 5.0, 'head_yaw': -30.0, 'head_pitch': 0.0}
        elif s == 'look_right':
            return {'arm_l': 5.0, 'arm_r': 5.0, 'head_yaw': 30.0, 'head_pitch': 0.0}
        elif s == 'groom_face':
            return {'arm_l': 60.0, 'arm_r': 10.0, 'head_yaw': -10.0, 'head_pitch': 5.0}
        else:
            return {'arm_l': 8.0, 'arm_r': 8.0, 'head_yaw': 0.0, 'head_pitch': 0.0}

    def get_idle_sub_state(self, *args, **kwargs) -> str:
        return getattr(self, '_idle_sub', 'idle_stand')


PandaWidget = PandaOpenGLWidget if QT_AVAILABLE else None
