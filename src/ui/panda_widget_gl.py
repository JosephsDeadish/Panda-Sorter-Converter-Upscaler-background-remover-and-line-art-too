"""
OpenGL Panda Widget - Hardware-accelerated 3D panda companion
Qt OpenGL rendering for smooth 60fps animation, real lighting, shadows, and 3D interactions.
Author: Dead On The Inside / JosephsDeadish
"""
from __future__ import annotations

import logging
import math
import random
import time
from typing import Optional, Callable, Tuple, List
from enum import Enum

try:
    from PyQt6.QtWidgets import QWidget, QApplication
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtCore import QTimer, Qt, QPoint, pyqtSignal
    # QState and QStateMachine were moved from PyQt6.QtCore → PyQt6.QtStateMachine
    # in PyQt6 6.1+.  Try the new location first, fall back to QtCore for older installs.
    try:
        from PyQt6.QtStateMachine import QState, QStateMachine
    except (ImportError, OSError, RuntimeError):
        from PyQt6.QtCore import QState, QStateMachine  # type: ignore[no-redef]
    from PyQt6.QtGui import QMouseEvent, QSurfaceFormat, QPainter, QColor, QFont
    # Disable C accelerate BEFORE importing OpenGL.GL — pure-Python mode is
    # driver-agnostic and avoids segfaults from buggy opengl_accelerate builds.
    try:
        import OpenGL as _ogl_pre; _ogl_pre.USE_ACCELERATE = False
    except Exception:
        pass
    from OpenGL.GL import *
    from OpenGL.GLU import *
    import numpy as np
    QT_AVAILABLE = True
    # Set default GL format at MODULE LOAD TIME — Qt requires this before the
    # first QOpenGLWidget is constructed (calling setDefaultFormat() in __init__
    # is too late if the GL context is created by Qt before the first paintGL).
    # Set QT_OPENGL=desktop before the format is created so Qt uses native
    # opengl32.dll (not ANGLE).  ANGLE only supports OpenGL ES — it rejects
    # glShadeModel/glLightfv/glBegin which causes initializeGL to fail.
    import os as _os
    _os.environ.setdefault('QT_OPENGL', 'desktop')
    _fmt = QSurfaceFormat()
    _fmt.setVersion(2, 1)
    _fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    _fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)  # desktop GL, not OpenGL ES
    _fmt.setSamples(4)
    _fmt.setDepthBufferSize(24)
    _fmt.setStencilBufferSize(8)
    QSurfaceFormat.setDefaultFormat(_fmt)
except (ImportError, OSError, RuntimeError):
    QT_AVAILABLE = False
    QWidget = object
    QOpenGLWidget = object
    QState = object
    QStateMachine = object
    QMouseEvent = object  # Type hint fallback
    QTimer = object
    class _SigStub:
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SigStub()  # type: ignore[misc]

logger = logging.getLogger(__name__)

# ── Module-level constants (avoid per-call allocations) ───────────────────────

# Body pitch targets for quadruped stances (degrees, X-axis rotation of torso)
_BODY_PITCH_TARGETS: dict = {
    'walking':       -20.0,   # slight forward lean for all-fours walk (was -30°, too aggressive)
    'walking_left':  -20.0,
    'walking_right': -20.0,
    'crawling':      -42.0,   # body pitched forward, nose toward ground
    'climbing_wall': -80.0,   # near-vertical, claws on wall
    'falling_back':   85.0,   # on back, legs up
    'sleeping':       12.0,   # slight slump forward
    'sitting_back': -10.0,   # slight backward lean when sitting upright
    'rolling':       30.0,   # body pitching as it rolls
    'hanging_ceiling': 175.0, # nearly inverted, gripping ceiling
    'hanging_window_edge': -55.0,  # body angled forward/down, arms reaching up
    'dance':          -5.0,   # slight forward lean while dancing
    'backflip':        0.0,   # body pitch driven by frame (applied separately)
    'spin':            0.0,   # body stays upright, yaw rotates
    'juggle':         -8.0,   # slight forward lean to look at juggled items
}

# Tail wag amplitude targets (degrees) keyed by animation state.
# Higher = more wagging; 0 = still; negative = droop.
_TAIL_WAG_AMP: dict = {
    'celebrating':      28.0,
    'waving':           22.0,
    'excited':          20.0,
    'walking':          10.0,
    'running':          14.0,
    'crawling':          8.0,
    'idle':              6.0,
    'sitting_back':      5.0,
    'sleeping':          0.0,
    'hanging_ceiling': -10.0,
}

# Amount by which 'content' micro-emotion increases each grooming frame (~30fps).
# Accumulates slowly so panda appears increasingly satisfied while grooming.
_GROOMING_CONTENT_INCREMENT: float = 0.015

# Maps every mood value used in PandaCharacter / PandaMoodSystem to an
# animation state understood by the GL renderer.
_MOOD_TO_ANIMATION: dict = {
    # PandaCharacter moods
    'happy':        'celebrating',
    'excited':      'celebrating',
    'working':      'working',
    'tired':        'sleeping',
    'celebrating':  'celebrating',
    'sleeping':     'sleeping',
    'sarcastic':    'sitting_back',   # sarcastic → relaxed sit (no specific state)
    'rage':         'wall_hit',       # rage → hit/frustrated
    'drunk':        'rolling',        # drunk → unsteady rolling
    'existential':  'idle',
    'motivating':   'celebrating',
    'tech_support': 'working',
    'sleepy':       'sleeping',
    # PandaMoodSystem moods
    'mischievous':  'jumping',
    'annoyed':      'wall_hit',
    # Legacy / generic names
    'sad':          'idle',
    'angry':        'wall_hit',
    'surprised':    'clicked',
    'playful':      'crawling',
    'bored':        'sitting_back',   # bored → sits and looks listless
    # New quadruped states accessible via mood
    'climbing':     'climbing_wall',
    'falling':      'falling_back',
    'crawling':     'crawling',
    # Purchasable animation states (from shop ShopCategory.ANIMATIONS items)
    'animation_dance':     'dance',
    'animation_backflip':  'backflip',
    'animation_magic':     'celebrating',
    'animation_spin':      'spin',
    'animation_juggle':    'juggle',
    'dance':    'dance',
    'backflip': 'backflip',
    'spin':     'spin',
    'juggle':   'juggle',
}

# Maps mood values to the internal emotion-weight key used by secondary motion.
_MOOD_TO_EMOTION: dict = {
    'happy':        'happy',
    'excited':      'excited',
    'celebrating':  'excited',
    'mischievous':  'happy',
    'playful':      'happy',
    'working':      'happy',
    'sad':          'sad',
    'tired':        'sad',
    'sleeping':     'sad',
    'sleepy':       'sad',
    'angry':        'angry',
    'rage':         'angry',
    'annoyed':      'angry',
}


class PandaOpenGLWidget(QOpenGLWidget if QT_AVAILABLE else QWidget):
    """
    Hardware-accelerated 3D panda widget using Qt OpenGL.
    
    Features:
    - Real-time 3D rendering at 60 FPS
    - Dynamic lighting with directional and ambient light
    - Real-time shadow mapping
    - Smooth animations with procedural 3D geometry
    - Physics-based interactions
    - Hardware acceleration via OpenGL
    """
    
    # Signals for communication with main app
    clicked = pyqtSignal()
    mood_changed = pyqtSignal(str)
    animation_changed = pyqtSignal(str)
    # Emitted (with error string) when initializeGL() fails so main.py can swap in 2D fallback
    gl_failed = pyqtSignal(str)
    
    # Animation constants
    TARGET_FPS = 30          # 30 fps matches perceived smoothness for a sidebar widget
    #                          # and halves the per-second GL draw calls vs 60 fps
    FRAME_TIME = 1.0 / TARGET_FPS  # 33.33ms per frame at 30 fps
    
    # Panda dimensions (3D units)
    # Real giant pandas are round/stocky: body is roughly as wide as tall,
    # with a large round head and visible sturdy legs below the belly.
    HEAD_RADIUS = 0.42   # slightly larger — pandas have big, round heads
    BODY_WIDTH = 0.56    # wider than before for a round, stocky silhouette
    BODY_HEIGHT = 0.50   # shorter than old 0.6 — pandas are squat, not tall
    ARM_LENGTH = 0.38    # slightly shorter (was 0.40) to look proportional on wider body
    ARM_Y = 0.18         # shoulder height in torso-local space (body extends ±0.25)
    LEG_LENGTH = 0.40    # longer legs so they protrude below the belly
    LEG_SPACING = 0.44   # wider stance, matches real panda hip width
    EAR_SIZE = 0.15

    # States that receive a micro-hold pause before transitioning to idle
    HOLD_STATES: frozenset = frozenset({
        'waving', 'celebrating', 'jumping',
        'crawling', 'climbing_wall', 'falling_back',
        'sitting_back', 'rolling', 'hanging_ceiling', 'hanging_window_edge',
    })

    # Weighted autonomous-activity table — tuple for immutability; weights sum to 1.0
    _ACTIVITY_WEIGHTS: tuple = (
        ('walk_around',  0.20),
        ('work',         0.16),
        ('idle',         0.12),
        ('celebrate',    0.07),
        ('crawl_around', 0.08),
        ('climb_wall',   0.06),
        ('sit_back',     0.07),
        ('hang_ceiling', 0.04),
        ('rolling',      0.06),
        ('sleeping',     0.05),
        ('dance',        0.04),
        ('spin',         0.03),
        ('backflip',     0.02),
    )

    # Physics constants
    GRAVITY = 9.8
    BOUNCE_DAMPING = 0.6
    FRICTION = 0.92
    # World boundary — panda cannot walk beyond ±WORLD_HALF in X or Z
    WORLD_HALF_X = 3.2
    WORLD_HALF_Z = 2.8
    
    def __init__(self, panda_character=None, parent=None):
        """
        Initialize OpenGL panda widget.
        
        Args:
            panda_character: PandaCharacter instance for state management
            parent: Parent Qt widget
        """
        if not QT_AVAILABLE:
            raise ImportError("PyQt6 and PyOpenGL are required for OpenGL panda widget")
        
        super().__init__(parent)
        
        # Set OpenGL surface format — use CompatibilityProfile so legacy fixed-function
        # GL (glShadeModel, glEnable(GL_LIGHTING), glBegin/End, etc.) remain available.
        # CoreProfile removes all legacy functions and would crash initializeGL().
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)  # OpenGL 2.1 — widely available, includes all legacy GL
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
        fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)  # native desktop GL, not ANGLE
        fmt.setSamples(4)  # 4x MSAA for antialiasing
        fmt.setDepthBufferSize(24)
        fmt.setStencilBufferSize(8)
        fmt.setAlphaBufferSize(8)  # needed for WA_TranslucentBackground transparency
        self.setFormat(fmt)

        # Overlay mode — transparent, always on top; mouse events are NOT
        # passed through so the panda responds to clicks and drags.
        self._overlay_mode = True
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)

        # Panda state
        self.panda = panda_character
        
        # Animation state
        self.animation_frame = 0
        self.animation_state = 'idle'
        self.facing = 'front'
        
        # Position and rotation (in 3D space)
        self.panda_x = 0.0
        self.panda_y = -0.7   # start on the ground (physics ground at -0.7)
        self.panda_z = 0.0
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0
        
        # Velocity for physics
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.velocity_z = 0.0
        self.angular_velocity = 0.0
        
        # Camera settings — camera_distance controls apparent panda size.
        # 6.5 keeps the panda comfortably visible without distorting perspective.
        # A 12° downward tilt (was 15°) gives a more front-on view.
        self.camera_distance = 6.5
        self.camera_angle_x = 12.0
        self.camera_angle_y = 0.0
        
        # Lighting
        self.light_position = [2.0, 3.0, 2.0, 1.0]
        self.ambient_light = [0.3, 0.3, 0.3, 1.0]
        self.diffuse_light = [0.8, 0.8, 0.8, 1.0]
        self.specular_light = [1.0, 1.0, 1.0, 1.0]
        
        # Shadow mapping
        self.shadow_map_size = 1024
        self.shadow_fbo = None
        self.shadow_texture = None
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.is_dragging = False
        self.drag_start_pos = None
        
        # Items (toys, food, clothes)
        self.items_3d = []  # List of 3D items in the scene
        self._preview_item_ref: dict | None = None  # Currently previewed item (tracked separately)
        
        # Clothing system (3D attachments)
        self.clothing = {
            'hat': None,        # Hat on head
            'shirt': None,      # Shirt on body
            'pants': None,      # Pants on legs
            'glasses': None,    # Glasses on face
            'accessory': None,  # Other accessories (bow, scarf, necklace, earrings)
            'held_right': None, # Item held in right paw
            'held_left': None,  # Item held in left paw
            'gloves': None,     # Gloves on paws
            'armor': None,      # Chest armour / robe / cape
            'boots': None,      # Foot coverings
            'belt': None,       # Belt / waistband accessory
            'backpack': None,   # Backpack on back
        }
        
        # Weapon system
        self.equipped_weapon = None  # Current weapon
        self.weapon_rotation = 0.0  # Weapon rotation angle
        
        # Color customization system
        self.custom_colors = {
            'body':   [1.0, 1.0, 1.0],    # Default white/natural
            'belly':  [1.0, 0.98, 0.93],   # Default cream belly
            'eyes':   [0.0, 0.0, 0.0],     # Default black
            'accent': [0.08, 0.08, 0.08],  # Default dark patches
            'glow': None                   # Optional glow effect
        }
        
        # Trail/effect system
        self.trail_enabled = False
        self.trail_type = 'none'         # 'none', 'sparkle', 'rainbow', 'fire', 'ice'
        self.trail_data = {}
        self.trail_particles = []        # List of particle positions/colors
        self.max_trail_particles = 50
        
        # Autonomous behavior
        self.autonomous_mode = True
        self.target_position = None       # Where panda is walking to
        self._walk_arrived_cb = None      # Optional[Callable] fired when target reached
        self.walking_speed = 0.5  # Units per second
        self.idle_timer = 0.0
        self.next_activity_time = random.uniform(3.0, 8.0)
        
        # Working state
        self.is_working = False
        self.work_progress = 0.0
        self.work_animation_phase = 0.0

        # ── Personality traits (per-instance random micro-variation) ──────────
        self._micro = {
            'blink_base':        random.uniform(2.2, 5.5),   # seconds between blinks
            'blink_double_prob': random.uniform(0.10, 0.30),  # double-blink probability
            'sway_speed':        random.uniform(0.88, 1.12),  # idle sway multiplier
            'breath_amp':        random.uniform(0.90, 1.10),  # breathing amplitude
            'ear_stiffness':     random.uniform(14.0, 22.0),  # ear spring stiffness
            'ear_damping':       random.uniform(0.70, 0.88),  # ear spring damping
            'reaction_delay_s':  random.uniform(0.04, 0.14),  # reaction delay seconds
        }

        # ── Time-based blink state ────────────────────────────────────────────
        self._next_blink_t   = time.time() + self._micro['blink_base']
        self._blink_phase    = 0.0      # 0.0=open … 1.0=fully closed … 2.0=open again
        self._blink_speed    = 8.0      # phases per second (close+open takes ~0.25 s)
        self._double_blink   = False    # True during second half of a double-blink
        self._double_delay_t = 0.0     # time until second blink starts

        # ── Ear spring physics (left=0, right=1) ─────────────────────────────
        self._ear_pos = [0.0, 0.0]     # current rotational offset (degrees)
        self._ear_vel = [0.0, 0.0]     # angular velocity

        # ── Tail spring physics ───────────────────────────────────────────────
        self._tail_angle = 0.0         # current wag angle (degrees, Z-axis)
        self._tail_vel   = 0.0         # angular velocity
        self._tail_droop = 0.0         # current X-axis droop (0=up, 20=down)

        # ── Cursor awareness ─────────────────────────────────────────────────
        self._cursor_wpos   = None      # QPoint in widget space (None = unknown)
        self._look_yaw      = 0.0       # horizontal head-look offset (degrees), eased
        self._look_pitch    = 0.0       # vertical offset
        self._look_yaw_tgt  = 0.0
        self._look_pitch_tgt = 0.0
        self.setMouseTracking(True)
        self.setAcceptDrops(True)   # accept food/toy drops from inventory panel

        # ── Fatigue / boredom system ─────────────────────────────────────────
        self._fatigue           = 0.0   # 0=fresh → 1=exhausted
        self._fatigue_rate      = 1.0 / (3600 * 2)     # full fatigue in ~2 h
        self._fatigue_recovery  = 1.0 / (3600 * 0.5)   # recover in ~30 min when sleeping
        self._boredom_t         = 0.0   # seconds since last interaction
        self._boredom_threshold = 45.0  # seconds of idle before boredom

        # ── Emotion layer ─────────────────────────────────────────────────────
        self._emotion = 'neutral'
        self._emotion_weights: dict = {
            'happy': 0.0, 'sad': 0.0, 'bored': 0.0,
            'excited': 0.0, 'tired': 0.0, 'neutral': 1.0,
        }
        # Micro-emotion blend weights (pairs, run concurrently with main emotion)
        self._micro_emotion: dict = {
            'curious':    0.0, 'playful': 0.0, 'annoyed': 0.0,
            'content':    0.0, 'nervous': 0.0, 'happy':   0.0,
        }

        # ── Animation blending ─────────────────────────────────────────────
        self._prev_state     = 'idle'
        self._blend_alpha    = 1.0          # 1.0 = fully in new state
        self._blend_duration = 0.20         # seconds for cross-fade
        self._blend_start_t  = time.time()

        # ── Squash-and-stretch ───────────────────────────────────────────────
        self._squash_y   = 1.0      # applied to body Y scale (>1=stretch, <1=squash)
        self._squash_vel = 0.0      # spring velocity toward rest (1.0)
        self._was_airborne = False

        # ── Anticipation before actions ──────────────────────────────────────
        self._anticipation_t      = 0.0     # countdown seconds
        self._anticipation_state  = 'idle'  # crouch-back state during anticipation
        self._pending_action      = None    # action triggered after anticipation

        # ── Per-instance asymmetry (fixed at creation) ────────────────────────
        _bias = random.randint(0, 1)
        self._asym = {
            'ear_twitch_bias':  _bias,                        # 0=left ear twitchier, 1=right
            'ear_twitch_mult':  [1.0, 1.0],
            'eye_squint_side':  random.choice([-1, 1]),       # side that squints when thinking
            'head_tilt_rest':   random.uniform(-3.5, 3.5),    # resting Z-tilt preference (deg)
            'breath_l_offset':  random.uniform(-0.002, 0.002), # left breathing uneven offset
            'breath_r_offset':  random.uniform(-0.002, 0.002),
            'mask_lr_bias':     random.uniform(-0.08, 0.08),  # eye mask size L vs R asymmetry
        }
        self._asym['ear_twitch_mult'][_bias]     = random.uniform(2.0, 3.2)
        self._asym['ear_twitch_mult'][1 - _bias] = 1.0

        # ── Follow-through springs ────────────────────────────────────────────
        # Head lag behind body motion
        self._head_lag      = 0.0       # angular offset added to head Z-tilt
        self._head_lag_vel  = 0.0
        self._body_vel_prev_x = 0.0     # track body-x velocity for acceleration

        # Belly/fur jiggle (spring oscillation on Y scale of fur layer)
        self._belly_y    = 1.0
        self._belly_vel  = 0.0

        # Per-arm follow-through overshoot
        self._arm_over   = [0.0, 0.0]   # [left, right] extra angle added to arms
        self._arm_over_vel = [0.0, 0.0]

        # Eyelid settle: tiny spring after blink re-opens
        self._eyelid_extra = 0.0        # small positive offset when overshooting open
        self._eyelid_vel   = 0.0

        # ── Micro-holds ───────────────────────────────────────────────────────
        self._hold_t      = 0.0     # remaining hold duration (seconds)
        self._idle_pause_countdown = random.uniform(10.0, 20.0)  # next idle pause
        self._reaction_delay_q: list = []   # queue of (fire_at_t, callable)

        # ── Saccades (rapid eye darts) ────────────────────────────────────────
        self._saccade_yaw   = 0.0       # current additive saccade offset (deg)
        self._saccade_pitch = 0.0
        self._saccade_tgt_yaw   = 0.0
        self._saccade_tgt_pitch = 0.0
        self._next_saccade_t  = time.time() + random.uniform(2.5, 5.5)
        self._saccade_hold_t  = 0.0     # remaining hold time at saccade target
        self._saccade_speed   = 22.0    # deg/s  (fast dart)

        # Eye-lead: eyes move first, head follows with lag
        self._eye_yaw     = 0.0
        self._eye_pitch   = 0.0
        self._eye_head_yaw    = 0.0     # head component lags eyes
        self._eye_head_pitch  = 0.0

        # ── Eyelid special states ─────────────────────────────────────────────
        self._surprised_eye_t = 0.0     # >0 = eyes wide-open (surprised)
        self._whoa_t          = 0.0     # >0 = "whoa face" (eyes wide, slight lean back)
        self._flinch_t        = 0.0     # >0 = flinch / blink (window-hit reaction)
        self._drag_vx_prev    = 0.0     # track drag velocity for whoa detection

        # ── Fur / hair style ─────────────────────────────────────────────────
        self._fur_style  = 'classic'    # current fur style id
        self._hair_style = 'none'       # current hair style id ('none' = no hair)

        # ── Quadruped locomotion: pitch/roll of torso for 4-leg stances ───────
        self._body_pitch = 0.0          # target torso X rotation (degrees); 0=upright
        self._body_pitch_cur = 0.0      # current (spring eased toward target)
        self._body_pitch_vel = 0.0      # spring velocity

        # ── Wobble / stumble (pandas are famously uncoordinated) ──────────────
        self._wobble_x       = 0.0      # current lateral sway offset (degrees)
        self._wobble_vel     = 0.0      # angular velocity of sway
        self._stumble_timer  = random.uniform(15.0, 40.0)   # s until next stumble
        self._stumble_active = False    # True during overcorrect phase

        # ── UI-interaction tracking (poke, sniff, sit-on, bite, hug) ─────────
        self._ui_interact_t      = 0.0  # countdown for current interaction (s)
        self._ui_interact_type   = ''   # 'poke', 'sniff', 'sit', 'bite', 'hug'
        self._last_drag_file     = None # last file path dragged over widget
        self._jaw_open           = 0.0  # 0=closed, 1=fully open (for bite animation)
        self._bite_duration      = 1.4  # seconds for one full bite cycle
        self._bite_chomp_played  = False  # guard so chomp only plays once per bite

        # ── Autonomous idle-behavior extras ──────────────────────────────────
        # These are thin sub-states layered on top of the main state machine
        self._idle_sub_t     = 0.0     # frame counter inside current idle sub-behavior
        self._idle_sub_state = ''      # 'grooming','stretching','flopping','scratching',
                                       # 'daydream','sniffing','yawning' (empty=normal)
        self._idle_sub_next  = random.uniform(8.0, 20.0)  # seconds until next sub-state

        # ── Audio ─────────────────────────────────────────────────────────────
        self._audio_sfx: dict = {}      # name → QSoundEffect (loaded lazily)
        self._audio_available = False
        try:
            from PyQt6.QtMultimedia import QSoundEffect   # noqa: F401
            self._audio_available = True
        except (ImportError, OSError, RuntimeError):
            pass

        # Animation timer (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(int(self.FRAME_TIME * 1000))  # Convert to ms

        # Frame timing for FPS cap
        self.last_frame_time = time.time()

        # OpenGL initialization flag
        self.gl_initialized = False
        self._has_gl_lighting = False  # set True in _do_initialize_gl if lighting available

        # Qt State Machine for animation state control
        self._setup_state_machine()

        logger.info("OpenGL panda widget initialized with hardware acceleration")
    
    def _setup_state_machine(self):
        """Setup Qt State Machine for animation state control."""
        if not QT_AVAILABLE:
            self.state_machine = None
            return
        
        # Create state machine
        self.state_machine = QStateMachine(self)
        
        # Define states
        self.idle_state = QState(self.state_machine)
        self.walking_state = QState(self.state_machine)
        self.jumping_state = QState(self.state_machine)
        self.working_state = QState(self.state_machine)
        self.celebrating_state = QState(self.state_machine)
        self.waving_state = QState(self.state_machine)
        
        # Set initial state
        self.state_machine.setInitialState(self.idle_state)
        
        # Connect state entries to animation changes
        self.idle_state.entered.connect(lambda: self._on_state_entered('idle'))
        self.walking_state.entered.connect(lambda: self._on_state_entered('walking'))
        self.jumping_state.entered.connect(lambda: self._on_state_entered('jumping'))
        self.working_state.entered.connect(lambda: self._on_state_entered('working'))
        self.celebrating_state.entered.connect(lambda: self._on_state_entered('celebrating'))
        self.waving_state.entered.connect(lambda: self._on_state_entered('waving'))
        
        # Define transitions between states
        # Note: Transitions are triggered programmatically via transition_to_state()
        # This allows external code to control animation state changes
        # Future enhancement: Add event-based transitions (e.g., timers, collision detection)
        
        # Start the state machine
        self.state_machine.start()
        logger.info("Animation state machine initialized")
    
    def _on_state_entered(self, state_name: str):
        """Called when entering a new animation state."""
        self.animation_state = state_name
        self.animation_changed.emit(state_name)
        logger.debug(f"Animation state changed to: {state_name}")
    
    def transition_to_state(self, state_name: str):
        """
        Transition to an animation state with blending, anticipation, and follow-through kicks.
        Big actions (jumping, celebrating) use a brief anticipation crouch first.
        All transitions blend smoothly from the previous state.
        """
        if not self.state_machine:
            self._set_state_direct(state_name)
            return

        # ── Anticipation phase for high-energy actions ────────────────────────
        if state_name in ('jumping', 'celebrating') and self.animation_state == 'idle':
            # Brief anticipation → then the real action
            self._anticipation_t     = random.uniform(0.10, 0.20)
            self._anticipation_state = '_anticipation'
            self._pending_action     = state_name
            # Kick arm overshoots backward (windup)
            self._arm_over_vel[0] += 8.0
            self._arm_over_vel[1] += 8.0
            return

        # ── Micro-hold at end of action before going idle ─────────────────────
        if state_name == 'idle' and self.animation_state in self.HOLD_STATES:
            self._hold_t = random.uniform(0.12, 0.28)
            # Schedule the idle transition after the hold
            fire_t = time.time() + self._hold_t
            self._reaction_delay_q.append((fire_t, lambda: self._set_state_direct('idle')))
            return

        # ── Follow-through kick on arm-heavy transitions ──────────────────────
        if state_name in ('waving',):
            self._arm_over_vel[1] += random.uniform(10.0, 18.0)  # right arm overshoot
        elif state_name in ('walking', 'running', 'crawling'):
            self._arm_over_vel[0] += random.uniform(4.0, 8.0)
            self._arm_over_vel[1] -= random.uniform(4.0, 8.0)
        elif state_name == 'falling_back':
            self._arm_over_vel[0] += random.uniform(-12.0, -8.0)
            self._arm_over_vel[1] += random.uniform(-12.0, -8.0)

        # ── Surprised wide-eyes for jumps/celebrations ────────────────────────
        if state_name in ('jumping', 'celebrating', 'waving', 'falling_back'):
            self._surprised_eye_t = 0.25

        self._set_state_direct(state_name)

    def initializeGL(self):
        """Initialize OpenGL settings."""
        try:
            self._do_initialize_gl()
            # Probe that fixed-function matrix mode works (CompatibilityProfile required).
            # If this raises (e.g. ANGLE / CoreProfile), we cannot render 3D at all —
            # emit gl_failed so the caller can swap in the 2D QPainter fallback instead
            # of leaving a black square where the panda should be.
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
        except Exception as e:
            logger.error(f"OpenGL initialization failed: {e}", exc_info=True)
            self.gl_initialized = False
            # Emit signal on next event-loop tick so callers can swap in 2D fallback
            QTimer.singleShot(0, lambda: self.gl_failed.emit(str(e)))

    def _do_initialize_gl(self):
        """Actual GL initialization — called inside a try/except in initializeGL()."""
        # Core calls — available in ALL GL profiles (1.1+)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.0, 0.0, 0.0, 0.0)  # fully transparent — composited over the app UI

        # CompatibilityProfile-only calls — safe to skip on CoreProfile/ANGLE
        # (QT_OPENGL=desktop should mean we NEVER reach this on ANGLE, but be
        # defensive in case the env var wasn't honoured by the driver/platform)
        self._has_gl_lighting = False

        try:
            glShadeModel(GL_SMOOTH)
        except Exception:
            pass  # CoreProfile: glShadeModel removed; shading still works via color

        try:
            glEnable(GL_MULTISAMPLE)
        except Exception:
            pass

        try:
            glEnable(GL_LINE_SMOOTH)
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        except Exception:
            pass

        try:
            # Lighting — CompatibilityProfile only (fixed-function pipeline)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glLightfv(GL_LIGHT0, GL_POSITION, self.light_position)
            glLightfv(GL_LIGHT0, GL_AMBIENT, self.ambient_light)
            glLightfv(GL_LIGHT0, GL_DIFFUSE, self.diffuse_light)
            glLightfv(GL_LIGHT0, GL_SPECULAR, self.specular_light)
            glEnable(GL_LIGHT2)
            glLightfv(GL_LIGHT2, GL_POSITION, [-3.0, 2.0, -4.0, 1.0])
            glLightfv(GL_LIGHT2, GL_AMBIENT,  [0.0,  0.0,  0.0,  1.0])
            glLightfv(GL_LIGHT2, GL_DIFFUSE,  [0.18, 0.15, 0.10, 1.0])
            glLightfv(GL_LIGHT2, GL_SPECULAR, [0.08, 0.06, 0.04, 1.0])
            glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
            glMaterialf(GL_FRONT, GL_SHININESS, 50.0)
            self._has_gl_lighting = True
        except Exception as _le:
            logger.warning(f"GL lighting unavailable ({_le}); using flat-colour rendering")

        # Initialize shadow mapping
        self._init_shadow_mapping()

        self.gl_initialized = True
        logger.info(f"OpenGL initialized successfully (lighting={'yes' if self._has_gl_lighting else 'no'})")
    
    def _init_shadow_mapping(self):
        """Initialize shadow mapping framebuffer and texture."""
        try:
            # Create shadow map texture
            self.shadow_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.shadow_texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, 
                        self.shadow_map_size, self.shadow_map_size, 
                        0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            
            # Create framebuffer for shadow rendering
            self.shadow_fbo = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, 
                                  GL_TEXTURE_2D, self.shadow_texture, 0)
            glDrawBuffer(GL_NONE)
            glReadBuffer(GL_NONE)
            
            # Check framebuffer status
            if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                logger.warning("Shadow framebuffer not complete, shadows may not work")
            
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            logger.info("Shadow mapping initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize shadow mapping: {e}")
            self.shadow_fbo = None
            self.shadow_texture = None
    
    def resizeGL(self, width, height):
        """Handle window resize."""
        if height == 0:
            height = 1
        try:
            glViewport(0, 0, width, height)
            # Setup projection matrix (fixed-function GL — requires CompatibilityProfile)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            aspect = width / height
            gluPerspective(45.0, aspect, 0.1, 100.0)
            glMatrixMode(GL_MODELVIEW)
        except Exception:
            pass  # CoreProfile: matrix mode calls unavailable; paintGL handles this gracefully

    def paintGL(self):
        """Render the 3D scene."""
        if not self.gl_initialized:
            return  # GL init failed or hasn't run yet — don't attempt GL calls
        # The animation timer (_update_animation) already fires at TARGET_FPS, so
        # no extra time-gate is needed here.  The previous gate caused every frame
        # to be skipped because _update_animation resets last_frame_time right
        # before calling update(), leaving elapsed ≈ 0 < FRAME_TIME always.
        try:
            self._paint_gl_body()
        except Exception as _e:
            logger.debug(f"paintGL error (frame skipped): {_e}")

    def _paint_gl_body(self):
        """Inner paintGL — wrapped by paintGL's try/except so a GL error skips the frame."""
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Ensure blend is off at frame start so the first opaque draws are truly opaque.
        # Individual draw sections re-enable it as needed and are required to disable it
        # before returning.
        glDisable(GL_BLEND)
        
        # Render shadows first (if supported)
        if self.shadow_fbo:
            self._render_shadows()
        
        # Setup camera
        glLoadIdentity()
        # Camera Y = +0.3: lifts the view target so the panda (ground at y=-0.7,
        # body centre at y=-0.4, head at y≈-0.1) is framed in the upper two-thirds
        # of the viewport with room for the feet at the bottom.
        glTranslatef(0.0, 0.3, -self.camera_distance)
        glRotatef(self.camera_angle_x, 1.0, 0.0, 0.0)
        glRotatef(self.camera_angle_y, 0.0, 1.0, 0.0)
        
        # Update light position relative to camera
        try:
            glLightfv(GL_LIGHT0, GL_POSITION, self.light_position)
        except Exception:
            pass  # not available if lighting not initialized
        
        # Draw ground plane (for shadow reference)
        self._draw_ground()
        
        # Draw trail particles (before panda for correct depth)
        self._draw_trail()
        
        # Apply panda position and rotation
        glPushMatrix()
        glTranslatef(self.panda_x, self.panda_y, self.panda_z)
        glRotatef(self.rotation_y, 0.0, 1.0, 0.0)  # Y rotation (turning)
        glRotatef(self.rotation_x, 1.0, 0.0, 0.0)  # X rotation (pitching)
        glRotatef(self.rotation_z, 0.0, 0.0, 1.0)  # Z rotation (rolling)
        
        # Draw panda body
        self._draw_panda()
        
        glPopMatrix()
        
        # Draw items (toys, food, clothes)
        for item in self.items_3d:
            self._draw_item_3d(item)

        # ── 2D overlay (drawn on top of GL via QPainter) ─────────────────────
        if QT_AVAILABLE:
            self._draw_2d_overlay()

    def _draw_2d_overlay(self):
        """Draw 2D text/icon overlays on top of the GL scene using QPainter.

        Avoids deprecated glRasterPos/glutBitmapCharacter and works on any
        OpenGL ES / core-profile context.  Called at the END of paintGL so
        the GL scene is already composed.
        """
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

            if self.animation_state == 'sleeping':
                # Floating Z Z Z above panda head
                t = self.animation_frame
                if self._OVERLAY_FONT_ZZZ:
                    painter.setFont(self._OVERLAY_FONT_ZZZ)
                cx = self.width() // 2
                cy = self.height() // 3  # upper third — above panda head
                # Three 'Z' letters staggered upward and to the right
                for i, letter in enumerate(['z', 'Z', 'Z']):
                    offset_x = i * 14
                    offset_y = -i * 18
                    alpha = min(255, int(180 * (0.4 + 0.3 * i)))   # clamp [0,255]
                    # Animate gentle float using animation_frame
                    float_y = int(8 * math.sin((t * 0.04) + i * 1.2))
                    painter.setPen(QColor(80, 80, 220, alpha))
                    painter.drawText(cx + offset_x, cy + offset_y + float_y, letter)

            elif self.animation_state in ('waving', 'celebrating') and self._micro_emotion.get('happy', 0) > 0.5:
                # Happy hearts/sparkles
                if self._OVERLAY_FONT_EMOJI:
                    painter.setFont(self._OVERLAY_FONT_EMOJI)
                cx, cy = self.width() // 2, self.height() // 4
                t = self.animation_frame
                for i, emoji in enumerate(['♥', '✨', '♥']):
                    alpha = min(255, int(200 * abs(math.sin(t * 0.05 + i * 1.0))))
                    ox = int(30 * math.cos(t * 0.06 + i * 2.1))
                    oy = int(-i * 20 - 10)
                    painter.setPen(QColor(220, 60, 120, alpha))
                    painter.drawText(cx + ox, cy + oy, emoji)

            elif self.animation_state == 'wall_hit':
                # Angry sparks — exclamation marks orbit head
                if self._OVERLAY_FONT_EMOJI:
                    painter.setFont(self._OVERLAY_FONT_EMOJI)
                cx, cy = self.width() // 2, self.height() // 3
                t = self.animation_frame
                for i, glyph in enumerate(['!', '💢', '!']):
                    a = t * 0.12 + i * 2.09   # orbit angle (fast angry spin)
                    ox = int(28 * math.cos(a))
                    oy = int(-28 * abs(math.sin(a)) - 8)
                    alpha = min(255, int(220 * abs(math.sin(t * 0.15 + i))))
                    painter.setPen(QColor(220, 40, 20, alpha))
                    painter.drawText(cx + ox, cy + oy, glyph)

            elif self.animation_state == 'working':
                # Small gear/progress dots above head while working
                if self._OVERLAY_FONT_EMOJI:
                    painter.setFont(self._OVERLAY_FONT_EMOJI)
                cx, cy = self.width() // 2, self.height() // 3
                t = self.animation_frame
                # Spinning gear
                a = t * 0.08
                ox = int(18 * math.cos(a))
                oy = int(-18 * math.sin(a)) - 15
                alpha = min(255, int(160 + 60 * math.sin(t * 0.10)))
                painter.setPen(QColor(80, 160, 220, alpha))
                painter.drawText(cx + ox, cy + oy, '⚙')

            elif self._idle_sub_state == 'daydream':
                # Thought bubble above head while daydreaming
                if self._OVERLAY_FONT_EMOJI:
                    painter.setFont(self._OVERLAY_FONT_EMOJI)
                cx, cy = self.width() // 2, self.height() // 4
                t = self.animation_frame
                for i, glyph in enumerate(['·', '°', '💭']):
                    alpha = min(255, int(180 * abs(math.sin(t * 0.03 + i * 0.8))))
                    painter.setPen(QColor(160, 180, 220, alpha))
                    painter.drawText(cx + i * 12 - 12, cy - i * 10, glyph)

            elif self.animation_state == 'dance':
                # Music notes floating up while dancing
                if self._OVERLAY_FONT_EMOJI:
                    painter.setFont(self._OVERLAY_FONT_EMOJI)
                cx, cy = self.width() // 2, self.height() // 3
                t = self.animation_frame
                for i, glyph in enumerate(['♪', '♫', '🎵']):
                    alpha = min(255, int(190 * abs(math.sin(t * 0.07 + i * 1.5))))
                    ox = int(35 * math.sin(t * 0.10 + i * 2.1))
                    oy = int(-20 - i * 14 - 4 * math.sin(t * 0.12 + i))
                    painter.setPen(QColor(220, 100, 180, alpha))
                    painter.drawText(cx + ox, cy + oy, glyph)

            elif self.animation_state == 'spin':
                # Sparkle arc around spinning body
                if self._OVERLAY_FONT_EMOJI:
                    painter.setFont(self._OVERLAY_FONT_EMOJI)
                cx, cy = self.width() // 2, self.height() // 2
                t = self.animation_frame
                for i, glyph in enumerate(['✨', '⭐', '✨']):
                    a = t * 0.14 + i * 2.09
                    ox = int(40 * math.cos(a))
                    oy = int(20 * math.sin(a)) - 15
                    alpha = min(255, int(200 * abs(math.sin(t * 0.12 + i))))
                    painter.setPen(QColor(255, 220, 60, alpha))
                    painter.drawText(cx + ox, cy + oy, glyph)

            elif self.animation_state == 'backflip':
                # Motion blur streaks
                if self._OVERLAY_FONT_EMOJI:
                    painter.setFont(self._OVERLAY_FONT_EMOJI)
                cx, cy = self.width() // 2, self.height() // 2
                t = self.animation_frame
                alpha = min(255, int(200 * abs(math.sin(t * 0.20))))
                painter.setPen(QColor(100, 200, 255, alpha))
                painter.drawText(cx - 25, cy - 30, '💨')
                painter.drawText(cx + 15, cy + 10, '💨')

            painter.end()
        except Exception:
            pass  # Overlay is decorative — never crash the render loop
    
    def _render_shadows(self):
        """Render shadow map from light's perspective."""
        if not self.shadow_fbo:
            return
        
        # Save current viewport
        viewport = glGetIntegerv(GL_VIEWPORT)
        
        # Bind shadow framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, self.shadow_fbo)
        glViewport(0, 0, self.shadow_map_size, self.shadow_map_size)
        glClear(GL_DEPTH_BUFFER_BIT)
        
        # Setup light's view matrix
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-3, 3, -3, 3, 0.1, 10.0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        gluLookAt(
            self.light_position[0], self.light_position[1], self.light_position[2],
            0.0, 0.0, 0.0,
            0.0, 1.0, 0.0
        )
        
        # Disable lighting for shadow pass
        try:
            glDisable(GL_LIGHTING)
        except Exception:
            pass  # not available if lighting not initialized
        
        # Render scene geometry (depth only)
        glPushMatrix()
        glTranslatef(self.panda_x, self.panda_y, self.panda_z)
        glRotatef(self.rotation_y, 0.0, 1.0, 0.0)
        self._draw_panda_geometry_only()
        glPopMatrix()
        
        # Restore state
        try:
            glEnable(GL_LIGHTING)
        except Exception:
            pass  # not available if lighting not initialized
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        # Restore framebuffer and viewport
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(*viewport)
    
    def _get_color(self, key: str) -> list:
        """
        Return the current colour for *key* from custom_colors.

        Centralises default-value handling so callers don't each need their own
        hardcoded fallback — the canonical defaults live in __init__ and here.
        Falls back to the 'body' colour for unknown keys.
        """
        return self.custom_colors.get(key,
               self.custom_colors.get('body', [0.97, 0.97, 0.99]))

    def _draw_ground(self):
        """Draw a tiled ground plane — skipped in overlay mode where the app UI is the floor."""
        if self._overlay_mode:
            return  # no floor texture when the panda floats over the application window
        try:
            glDisable(GL_LIGHTING)
        except Exception:
            pass  # not available if lighting not initialized
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        size = 5.0
        y    = -1.0
        step = 1.0
        x0   = -size

        # Draw alternating light/dark tiles
        i = 0
        x = x0
        while x < size:
            z = x0
            while z < size:
                if (i % 2) == 0:
                    glColor4f(0.88, 0.82, 0.74, 0.70)   # warm light oak
                else:
                    glColor4f(0.76, 0.68, 0.58, 0.70)   # warm dark oak
                glBegin(GL_QUADS)
                glVertex3f(x,        y, z)
                glVertex3f(x + step, y, z)
                glVertex3f(x + step, y, z + step)
                glVertex3f(x,        y, z + step)
                glEnd()
                z += step
                i += 1
            x += step
            i += 1   # offset row so columns alternate too

        # Thin grid lines on top
        glColor4f(0.55, 0.48, 0.40, 0.35)
        glLineWidth(0.8)
        glBegin(GL_LINES)
        pos = x0
        while pos <= size:
            glVertex3f(pos, y + 0.001, x0)
            glVertex3f(pos, y + 0.001, size)
            glVertex3f(x0,  y + 0.001, pos)
            glVertex3f(size, y + 0.001, pos)
            pos += step
        glEnd()
        glLineWidth(1.0)

        glDisable(GL_BLEND)
        try:
            glEnable(GL_LIGHTING)
        except Exception:
            pass  # not available if lighting not initialized
    
    def _draw_panda(self):
        """Draw detailed 3D panda character with all body parts."""
        bob = self._get_body_bob()
        limb = self._get_limb_positions()
        t  = self.animation_frame           # raw frame counter used for trig

        # Fetch fur colours once — avoids repeated dict lookups per frame
        body_col   = self.custom_colors['body']
        belly_col  = self.custom_colors['belly']
        accent_col = self.custom_colors['accent']

        # ── Torso ────────────────────────────────────────────────────────────
        # Gather idle sub-pose offsets (grooming/stretching/yawning/flopping etc.)
        # MUST be fetched BEFORE sy calculation that reads it.
        _sub = self._get_idle_sub_pose()

        # Apply squash/stretch to the torso (sub-pose can add stretch too)
        sy = self._squash_y * _sub.get('body_y_scale', 1.0)

        glPushMatrix()
        # _paint_gl_body already applied panda_x/panda_z and rotation_y via
        # glTranslatef/glRotatef; only add the vertical bob offset here to avoid
        # doubling the XZ position or rotation.
        # Use 0.30 (was 0.28) so the body centre sits a little higher, giving
        # the shorter BODY_HEIGHT=0.50 enough clearance above the legs.
        glTranslatef(0.0, 0.30 + bob, 0.0)
        # Wobble: random lateral lean added to whole body (pandas are uncoordinated)
        if abs(self._wobble_x) > 0.05:
            glRotatef(self._wobble_x, 0.0, 0.0, 1.0)
        # Flopping sub-behavior: roll torso sideways
        if _sub.get('body_x', 0.0):
            glRotatef(_sub['body_x'], 1.0, 0.0, 0.0)
        # Rolling state: continuous Z-rotation (panda rolling on the ground)
        if self.animation_state == 'rolling':
            roll_angle = (self.animation_frame * 4.0) % 360.0
            glRotatef(roll_angle, 0.0, 0.0, 1.0)
        # Backflip: continuous X-rotation (somersault backward)
        elif self.animation_state == 'backflip':
            flip_angle = (self.animation_frame * 6.0) % 360.0
            glRotatef(flip_angle, 1.0, 0.0, 0.0)
        # Spin: continuous Y-rotation (pirouette)
        elif self.animation_state == 'spin':
            spin_angle = (self.animation_frame * 8.0) % 360.0
            glRotatef(spin_angle, 0.0, 1.0, 0.0)
        # Quadruped body pitch (crawling/climbing/falling_back)
        if abs(self._body_pitch_cur) > 0.5:
            glRotatef(self._body_pitch_cur, 1.0, 0.0, 0.0)

        # Disable blending for opaque solid body parts so they are never transparent
        glDisable(GL_BLEND)

        # Belly — creamy white underside; belly jiggle on Y (height oscillation)
        glPushMatrix()
        glScalef(self.BODY_WIDTH * 0.65,
                 self.BODY_HEIGHT * 0.55 * sy * self._belly_y,
                 self.BODY_WIDTH * 0.50)
        glColor4f(*belly_col, 1.0)
        self._draw_sphere(1.0, 32, 32)
        glPopMatrix()

        # Main body — colour from custom_colors['body'] (fur style)
        # Apply subtle specular sheen to simulate fur gloss
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.25, 0.25, 0.25, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 14.0)
        glPushMatrix()
        glScalef(self.BODY_WIDTH, self.BODY_HEIGHT * sy, self.BODY_WIDTH * 0.92)
        glColor4f(*body_col, 1.0)
        self._draw_sphere(1.0, 32, 32)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 50.0)

        # Fur layer — skip in overlay mode: semi-transparent shells over a
        # transparent-background GL context make the panda look ghostly/translucent
        # because the shell alpha blends against the transparent window rather than
        # the solid body beneath it at the silhouette edges.
        if not self._overlay_mode:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            _fur_col = self._get_color('body')
            # Shell 1 — innermost (near body surface, most opaque)
            glPushMatrix()
            glScalef(self.BODY_WIDTH * 1.025,
                     self.BODY_HEIGHT * 1.018 * sy * self._belly_y,
                     self.BODY_WIDTH * 0.945)
            glColor4f(*_fur_col, 0.22)
            self._draw_sphere(1.0, 16, 16)
            glPopMatrix()
            # Shell 2 — middle layer
            glPushMatrix()
            glScalef(self.BODY_WIDTH * 1.045,
                     self.BODY_HEIGHT * 1.030 * sy * self._belly_y,
                     self.BODY_WIDTH * 0.960)
            glColor4f(*_fur_col, 0.14)
            self._draw_sphere(1.0, 14, 14)
            glPopMatrix()
            # Shell 3 — outermost (fluffy tips, very transparent)
            glPushMatrix()
            glScalef(self.BODY_WIDTH * 1.065,
                     self.BODY_HEIGHT * 1.042 * sy * self._belly_y,
                     self.BODY_WIDTH * 0.978)
            glColor4f(*_fur_col, 0.07)
            self._draw_sphere(1.0, 12, 12)
            glPopMatrix()
            glDisable(GL_BLEND)

        # Black saddle patch across lower torso — uses accent colour (fur style)
        glPushMatrix()
        glTranslatef(0.0, -0.18, 0.0)
        glScalef(self.BODY_WIDTH * 0.95, self.BODY_HEIGHT * 0.35 * sy, self.BODY_WIDTH * 0.70)
        glColor3f(*accent_col)
        self._draw_sphere(1.0, 20, 20)
        glPopMatrix()

        # Spine ridge — darker streak along the back
        glPushMatrix()
        glTranslatef(0.0, 0.05, -self.BODY_WIDTH * 0.65)
        glScalef(0.20, 0.55 * sy, 0.22)
        glColor3f(*[max(0.0, c - 0.06) for c in accent_col])
        self._draw_sphere(1.0, 10, 10)
        glPopMatrix()

        # Shoulder muscle masses (black) — give quadruped shoulder hump
        # Y derived from ARM_Y (+ 0.02 for slight upward centre) so shoulder
        # blobs visually connect to the arm pivot point.
        for sx in (-self.BODY_WIDTH * 0.70, self.BODY_WIDTH * 0.70):
            glPushMatrix()
            glTranslatef(sx, self.ARM_Y + 0.02, -self.BODY_WIDTH * 0.15)
            glScalef(0.30, 0.28 * sy, 0.24)
            glColor3f(*accent_col)
            self._draw_sphere(1.0, 12, 12)
            glPopMatrix()

        # ── Neck ─────────────────────────────────────────────────────────────
        # Short cylinder-like neck connecting torso to head
        glPushMatrix()
        glTranslatef(0.0, self.BODY_HEIGHT * 0.48 * sy, 0.0)
        glScalef(0.30, 0.32 * sy, 0.28)
        glColor3f(*body_col)
        self._draw_sphere(1.0, 14, 14)
        glPopMatrix()

        # ── Chest / throat white patch ────────────────────────────────────────
        # Real pandas have a bright white chest band between the black shoulders
        glPushMatrix()
        glTranslatef(0.0, self.BODY_HEIGHT * 0.28 * sy, self.BODY_WIDTH * 0.55)
        glScalef(0.45, 0.38 * sy, 0.25)
        bright_white = [min(1.0, c + 0.06) for c in belly_col]
        glColor3f(*bright_white)
        self._draw_sphere(1.0, 14, 14)
        glPopMatrix()

        # ── Belly ventral stripe ──────────────────────────────────────────────
        # Cream-coloured midline stripe from chest to groin
        glPushMatrix()
        glTranslatef(0.0, 0.0, self.BODY_WIDTH * 0.46)
        glScalef(0.18, 0.82 * sy, 0.15)
        glColor3f(*belly_col)
        self._draw_sphere(1.0, 10, 10)
        glPopMatrix()

        # ── Hip patches (black) ──────────────────────────────────────────────
        # Real pandas have prominent black oval patches on each hip / upper thigh.
        # Y = -BODY_HEIGHT * 0.48 = -0.24 matches the leg pivot (leg_y = -0.24)
        # so the black patch visually joins the body to the upper leg.
        for hx in (-self.BODY_WIDTH * 0.78, self.BODY_WIDTH * 0.78):
            glPushMatrix()
            glTranslatef(hx, -self.BODY_HEIGHT * 0.48 * sy, 0.0)
            glScalef(0.36, 0.42 * sy, 0.30)
            glColor3f(*accent_col)
            self._draw_sphere(1.0, 12, 12)
            glPopMatrix()

        # ── Legs ─────────────────────────────────────────────────────────────
        self._draw_panda_legs(limb, bob, t)

        # ── Arms ─────────────────────────────────────────────────────────────
        self._draw_panda_arms(limb, bob, t, _sub)

        # ── Tail (spring-physics wag; droops when sad/sleeping, wags when happy) ─
        glPushMatrix()
        glTranslatef(0.0, -0.05, -self.BODY_WIDTH * 0.78)
        glRotatef(self._tail_droop, 1.0, 0.0, 0.0)   # droop / raise on X
        glRotatef(self._tail_angle, 0.0, 0.0, 1.0)   # side wag on Z (spring)
        glScalef(1.0, 0.80, 1.0)
        glColor3f(*[min(1.0, c + 0.04) for c in body_col])
        self._draw_sphere(0.090, 12, 12)
        glPopMatrix()

        # ── Neck scruff ───────────────────────────────────────────────────────
        # White fur tuft between the shoulder blades and the base of the skull
        glPushMatrix()
        glTranslatef(0.0, self.BODY_HEIGHT * 0.38 * sy, self.BODY_WIDTH * 0.35)
        glScalef(0.28, 0.22 * sy, 0.22)
        glColor3f(*[min(1.0, c + 0.06) for c in body_col])
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()

        # ── Depth overlap shadows (adds realism in non-overlay mode) ─────────
        # In overlay mode these semi-transparent dark blobs blend against the
        # transparent window background and produce visible dark halos.
        if not self._overlay_mode:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            # Shadow pocket between chin and chest
            glPushMatrix()
            glTranslatef(0.0, self.BODY_HEIGHT * 0.45 * sy, self.BODY_WIDTH * 0.46)
            glScalef(0.35, 0.14 * sy, 0.12)
            glColor4f(0.0, 0.0, 0.0, 0.28)
            self._draw_sphere(1.0, 10, 10)
            glPopMatrix()
            # Belly-over-legs shadow
            glPushMatrix()
            glTranslatef(0.0, -self.BODY_HEIGHT * 0.50 * sy, self.BODY_WIDTH * 0.22)
            glScalef(0.55, 0.10 * sy, 0.35)
            glColor4f(0.0, 0.0, 0.0, 0.22)
            self._draw_sphere(1.0, 10, 10)
            glPopMatrix()
            # Arm contact shadows (both sides)
            for asx in (-self.BODY_WIDTH * 0.80, self.BODY_WIDTH * 0.80):
                glPushMatrix()
                glTranslatef(asx, 0.10, 0.0)
                glScalef(0.18, 0.28 * sy, 0.16)
                glColor4f(0.0, 0.0, 0.0, 0.20)
                self._draw_sphere(1.0, 8, 8)
                glPopMatrix()
            glDisable(GL_BLEND)

        # ── Head (inside torso matrix so it follows body pitch, roll, and spin) ─
        # Keeping the head in the SAME GL matrix as the body means it
        # automatically inherits every rotation applied to the torso (walking
        # pitch, rolling Z-spin, backflip X-rotation, wobble, etc.), which fixes
        # the previously visible disconnect between the pitched body and the
        # floating head.
        # Head Y in torso-local space = 0.88 (old world) − 0.30 (body translate) = 0.58.
        # Body bob is already incorporated in the parent glTranslatef(0.30+bob, ...),
        # so we do NOT add bob here again (avoids 2× head-bob relative to body).
        tilt = (4.0 * math.sin(t * 0.04) +
                self._head_lag +
                self._asym.get('head_tilt_rest', 0.0) +
                self._eye_head_yaw * 0.5 +
                _sub.get('head_z', 0.0))
        glPushMatrix()
        glTranslatef(0.0, 0.58, 0.0)   # 0.58 above body centre (torso-local)
        glRotatef(self._eye_head_yaw * 0.4, 0.0, 1.0, 0.0)
        glRotatef(tilt, 0.0, 0.0, 1.0)
        glRotatef(self._eye_head_pitch * 0.5 + _sub.get('head_x', 0.0), 1.0, 0.0, 0.0)

        # "Whoa face" — slight backwards lean
        if self._whoa_t > 0.0:
            lean = min(self._whoa_t / 0.5, 1.0) * -8.0
            glRotatef(lean, 1.0, 0.0, 0.0)

        # Main skull — subtle fur sheen, colour from fur style
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.22, 0.22, 0.22, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 12.0)
        glColor3f(*body_col)
        self._draw_sphere(self.HEAD_RADIUS, 36, 36)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 50.0)
        # Head fur shells — skip in overlay mode (same reason as body shells:
        # alpha blends against transparent window background, not the head sphere)
        if not self._overlay_mode:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(*self._get_color('body'), 0.18)
            self._draw_sphere(self.HEAD_RADIUS * 1.028, 14, 14)
            glColor4f(*self._get_color('body'), 0.09)
            self._draw_sphere(self.HEAD_RADIUS * 1.052, 12, 12)
            glDisable(GL_BLEND)

        # ── Cranial dome / sagittal-crest ridge ───────────────────────────────
        # Real pandas have a broad rounded skull with a subtle midline fur ridge
        glPushMatrix()
        glTranslatef(0.0, self.HEAD_RADIUS * 0.65, -self.HEAD_RADIUS * 0.05)
        glScalef(0.52, 0.38, 0.44)
        glColor3f(*body_col)
        self._draw_sphere(self.HEAD_RADIUS, 14, 14)
        glPopMatrix()
        # Central fur ridge along top of skull
        glPushMatrix()
        glTranslatef(0.0, self.HEAD_RADIUS * 0.82, 0.0)
        glScalef(0.18, 0.30, 0.48)
        glColor3f(*[min(1.0, c + 0.04) for c in body_col])
        self._draw_sphere(self.HEAD_RADIUS * 0.55, 10, 10)
        glPopMatrix()

        # ── Jaw / chin mass ──────────────────────────────────────────────────
        # Real pandas have a heavy rounded lower jaw
        glPushMatrix()
        glTranslatef(0.0, -self.HEAD_RADIUS * 0.55, self.HEAD_RADIUS * 0.35)
        glScalef(0.70, 0.42, 0.58)
        glColor3f(*body_col)
        self._draw_sphere(self.HEAD_RADIUS * 0.65, 14, 14)
        glPopMatrix()

        # ── Cheek fur puffs — slightly larger, same body colour ──────────────
        for cx in (-self.HEAD_RADIUS * 0.68, self.HEAD_RADIUS * 0.68):
            glPushMatrix()
            glTranslatef(cx, -self.HEAD_RADIUS * 0.22, self.HEAD_RADIUS * 0.52)
            glScalef(0.80, 0.68, 0.55)
            glColor3f(*body_col)
            self._draw_sphere(self.HEAD_RADIUS * 0.45, 12, 12)
            glPopMatrix()

        # Fur fuzz over skull — skip in overlay mode (same transparency issue)
        if not self._overlay_mode:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1.0, 1.0, 1.0, 0.15)
            self._draw_sphere(self.HEAD_RADIUS * 1.04, 16, 16)
            glDisable(GL_BLEND)

        # ── Tear-duct streaks ────────────────────────────────────────────────
        # Most iconic real panda feature: dark teardrop smear from inner
        # eye corner running diagonally down toward the muzzle corners.
        for side in (-1, 1):
            for seg, (tx, ty, tz, sx, sy_s, sz) in enumerate([
                # seg 0: eye-corner origin
                ( side * 0.085,  0.035,  self.HEAD_RADIUS * 0.82,  0.055, 0.048, 0.038),
                # seg 1: mid streak
                ( side * 0.092,  -0.018, self.HEAD_RADIUS * 0.85,  0.040, 0.052, 0.030),
                # seg 2: lower end — fades into muzzle side
                ( side * 0.082,  -0.062, self.HEAD_RADIUS * 0.86,  0.030, 0.040, 0.025),
            ]):
                glPushMatrix()
                glTranslatef(tx, ty, tz)
                glScalef(sx, sy_s, sz)
                # Slightly softer at the tip (seg 2)
                dark = [max(0.0, c - 0.01 * seg) for c in accent_col]
                glColor3f(*dark)
                self._draw_sphere(1.0, 10, 10)
                glPopMatrix()

        # ── Neck fluff overlap — fur collar from skull base down to torso ────
        # Drawn in head matrix so it follows head tilt; wraps over the neck join.
        # Skip in overlay mode: semi-transparent blobs create visible halos.
        if not self._overlay_mode:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            for ny, nz, na in [
                (-self.HEAD_RADIUS * 0.65, -self.HEAD_RADIUS * 0.05, 0.55),
                (-self.HEAD_RADIUS * 0.78,  self.HEAD_RADIUS * 0.05, 0.38),
                (-self.HEAD_RADIUS * 0.60, -self.HEAD_RADIUS * 0.18, 0.30),
            ]:
                glPushMatrix()
                glTranslatef(0.0, ny, nz)
                glScalef(0.32, 0.20, 0.25)
                body_c = self._get_color('body')
                glColor4f(body_c[0], body_c[1], body_c[2], na)
                self._draw_sphere(1.0, 10, 10)
                glPopMatrix()
            glDisable(GL_BLEND)

        # ── Ears ─────────────────────────────────────────────────────────────
        self._draw_panda_ears(bob, t)

        # ── Eye patches ───────────────────────────────────────────────────────
        self._draw_panda_eyes(t)

        # ── Snout ─────────────────────────────────────────────────────────────
        self._draw_panda_snout()

        # ── Hair style (head-top accessory) ───────────────────────────────────
        if self._hair_style not in ('none', '', None):
            self._draw_panda_head_hair()

        # ── Hat (drawn here so it follows head bob/tilt/rotation) ─────────────
        if self.clothing['hat']:
            self._draw_hat(self.clothing['hat'])

        glPopMatrix()   # end head sub-matrix

        # ── Clothing & weapons (inside torso matrix so they follow body pitch) ─
        self._draw_clothing()
        self._draw_weapon()
        self._draw_held_items()

        glPopMatrix()   # end torso matrix

    def _draw_panda_geometry_only(self):
        """Draw simplified panda geometry for shadow pass (no colour changes)."""
        # Both body and head inside the single torso matrix so the shadow geometry
        # correctly follows any body pitch/roll applied during animation.
        glPushMatrix()
        glTranslatef(0.0, 0.30, 0.0)
        glScalef(self.BODY_WIDTH, self.BODY_HEIGHT, self.BODY_WIDTH * 0.92)
        self._draw_sphere(1.0, 10, 10)
        glPopMatrix()
        # Head at torso-local Y = 0.58 (same as in _draw_panda)
        glPushMatrix()
        glTranslatef(0.0, 0.30 + 0.58, 0.0)  # body translate + head local = 0.88
        self._draw_sphere(self.HEAD_RADIUS, 10, 10)
        glPopMatrix()

    # ─── Ear drawing ────────────────────────────────────────────────────────
    def _draw_panda_ears(self, bob_offset, t=0):
        """Draw rounded ears with black outer ring, pink inner ear, antihelical ridge and spring physics."""
        accent_col = self._get_color('accent')
        ear_positions = [(-0.265, 0.295, 0.06), (0.265, 0.295, 0.06)]
        for i, (ex, ey, ez) in enumerate(ear_positions):
            side = 1 if ex > 0 else -1
            ear_rot = self._ear_pos[i]

            # ── Ear base shadow (depth overlap where ear meets skull) ─────────
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glPushMatrix()
            glTranslatef(ex * 0.80, ey - 0.015, ez - 0.008)
            glScalef(0.55, 0.35, 0.28)
            glColor4f(0.0, 0.0, 0.0, 0.26)
            self._draw_sphere(self.EAR_SIZE, 10, 10)
            glPopMatrix()
            glDisable(GL_BLEND)

            glPushMatrix()
            glTranslatef(ex, ey, ez)
            glRotatef(ear_rot, 0.0, 0.0, 1.0)   # spring-driven tilt
            glScalef(1.0, 0.88, 0.55)
            glColor3f(*accent_col)
            self._draw_sphere(self.EAR_SIZE, 16, 16)
            # Inner pink concha
            glPushMatrix()
            glTranslatef(0.0, -0.005, 0.015)
            glScalef(0.58, 0.52, 0.40)
            glColor3f(0.88, 0.60, 0.68)   # warm pink
            self._draw_sphere(self.EAR_SIZE, 12, 12)
            glPopMatrix()
            # Ear canal depth — tiny dark oval in centre of concha
            glPushMatrix()
            glTranslatef(0.0, -0.008, 0.022)
            glScalef(0.28, 0.22, 0.22)
            glColor3f(0.12, 0.08, 0.10)
            self._draw_sphere(self.EAR_SIZE * 0.45, 8, 8)
            glPopMatrix()
            # Antihelical ridge — darker rim arc along outer edge
            glPushMatrix()
            glTranslatef(side * 0.018, 0.035, 0.008)
            glScalef(0.28, 0.72, 0.25)
            glColor3f(*[max(0.0, c - 0.04) for c in accent_col])
            self._draw_sphere(self.EAR_SIZE * 0.72, 10, 10)
            glPopMatrix()
            # Tiny pale tuft at ear tip
            glPushMatrix()
            glTranslatef(0.0, self.EAR_SIZE * 0.88, 0.0)
            glScalef(0.40, 0.28, 0.35)
            glColor3f(*self._get_color('body'))
            self._draw_sphere(self.EAR_SIZE * 0.45, 8, 8)
            glPopMatrix()
            glPopMatrix()

    # ─── Eye drawing ────────────────────────────────────────────────────────
    def _draw_panda_eyes(self, t=0):
        """Draw detailed eyes with saccades, eye-lead, asymmetric squint and eyelid states."""
        blink = self._get_blink_scale(t)        # 1.0 = open, ≈0 = closed

        # Surprised: widen eyes; whoa face: also widens
        surprised_boost = min(1.0, self._surprised_eye_t / 0.3) * 0.18
        whoa_boost      = min(1.0, self._whoa_t / 0.5) * 0.12
        wide_factor     = 1.0 + surprised_boost + whoa_boost + self._eyelid_extra

        eye_y  = 0.055
        # eye_z: HEAD_RADIUS * 0.86 places the eye patches on the head surface so they
        # protrude as distinct dark bumps (old 0.74 put them deep inside the head, making
        # them look flat/painted-on rather than 3-dimensional).
        eye_z  = self.HEAD_RADIUS * 0.86

        # Eye direction: use eye_yaw + saccade, converted to small translation offset
        eye_dx = math.sin(math.radians(self._eye_yaw))   * 0.012
        eye_dy = math.sin(math.radians(self._eye_pitch)) * 0.010

        for side in (-1, 1):
            eye_x = side * 0.158

            # Asymmetric squint during bored/thinking (one side only)
            thinking = self._emotion_weights.get('bored', 0.0)
            squint   = 1.0
            if thinking > 0.2 and side == self._asym.get('eye_squint_side', 1):
                squint = 1.0 - thinking * 0.22

            # Micro-emotion: curious widens; playful adds asymmetric tilt; happy slightly narrows + lifts (smile shape)
            curious_w  = self._micro_emotion.get('curious', 0.0)
            playful_w  = self._micro_emotion.get('playful', 0.0)
            happy_w    = self._micro_emotion.get('happy',   0.0)
            # Happy eye: cheek lifts compress the bottom of the eye (squint from below)
            happy_squint = 1.0 - happy_w * 0.12
            blink_s = blink * (wide_factor + curious_w * 0.08) * squint * happy_squint

            # ── Realistic eye mask: multi-layer ellipsoid + cheek extension ───
            # Per-instance asymmetry: one side is slightly bigger
            mask_bias = self._asym.get('mask_lr_bias', 0.0)  # -0.08 to +0.08
            mask_sx = 1.25 + side * mask_bias * 0.4
            mask_sy = 0.90 + side * mask_bias * 0.2
            # Playful adds slight tilt asymmetry
            mask_tilt = side * -12.0 + playful_w * side * 4.0

            # Outer feathered ring (slightly larger, slightly transparent)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glPushMatrix()
            glTranslatef(eye_x, eye_y, eye_z - 0.005)
            glScalef(1.0, blink_s, 1.0)
            glRotatef(mask_tilt, 0.0, 0.0, 1.0)
            glScalef(mask_sx * 1.18, mask_sy * 1.12, 0.55)
            glColor4f(*self._get_color('accent'), 0.55)
            self._draw_sphere(0.118, 14, 14)
            glPopMatrix()
            glDisable(GL_BLEND)

            # Inner solid patch
            glPushMatrix()
            glTranslatef(eye_x, eye_y, eye_z)
            glScalef(1.0, blink_s, 1.0)
            glRotatef(mask_tilt, 0.0, 0.0, 1.0)
            glScalef(mask_sx, mask_sy, 0.60)
            glColor3f(*self._get_color('accent'))
            self._draw_sphere(0.118, 16, 16)
            glPopMatrix()

            # Cheek-wrap extension: extra downward oval that wraps toward muzzle
            glPushMatrix()
            glTranslatef(eye_x + side * 0.010, eye_y - 0.040, eye_z - 0.010)
            glScalef(0.60, 0.55, 0.40)
            glColor3f(*self._get_color('accent'))
            self._draw_sphere(0.095, 12, 12)
            glPopMatrix()

            # Tear-duct streak: dark smear from inner-eye corner diagonally down
            # Most iconic giant-panda facial marking
            for seg, (sdx, sdy, sdz, ssx, ssy) in enumerate([
                (side * -0.045,  0.005, 0.008, 0.18, 0.30),
                (side * -0.068, -0.022, 0.002, 0.14, 0.25),
                (side * -0.085, -0.042, -0.004, 0.11, 0.20),
            ]):
                glPushMatrix()
                glTranslatef(eye_x + sdx, eye_y + sdy, eye_z + sdz)
                glScalef(ssx, ssy, 0.18)
                glColor3f(*[max(0.0, c - 0.02) for c in self._get_color('accent')])
                self._draw_sphere(0.065, 8, 8)
                glPopMatrix()

            # ── White sclera ──────────────────────────────────────────────
            glPushMatrix()
            glTranslatef(eye_x, eye_y, eye_z + 0.052)
            glScalef(1.0, blink_s, 1.0)
            glColor3f(1.0, 1.0, 1.0)
            self._draw_sphere(0.060, 16, 16)
            glPopMatrix()

            # ── Iris (brown) — shifted by eye direction ────────────────────
            glPushMatrix()
            glTranslatef(eye_x + eye_dx * side, eye_y + eye_dy, eye_z + 0.092)
            glScalef(1.0, blink_s, 1.0)
            glColor3f(0.42, 0.28, 0.12)
            self._draw_sphere(0.036, 14, 14)
            glPopMatrix()

            # ── Pupil ─────────────────────────────────────────────────────
            glPushMatrix()
            glTranslatef(eye_x + eye_dx * side, eye_y + eye_dy, eye_z + 0.118)
            glScalef(1.0, blink_s, 1.0)
            glColor3f(0.04, 0.04, 0.04)
            self._draw_sphere(0.021, 12, 12)
            glPopMatrix()

            # ── Specular highlight ─────────────────────────────────────────
            glPushMatrix()
            glTranslatef(eye_x + side * 0.007 + eye_dx * side,
                         eye_y + 0.012 + eye_dy,
                         eye_z + 0.128)
            glScalef(1.0, blink_s, 1.0)
            try:
                glDisable(GL_LIGHTING)
            except Exception:
                pass  # not available if lighting not initialized
            glColor3f(1.0, 1.0, 1.0)
            self._draw_sphere(0.009, 8, 8)
            try:
                glEnable(GL_LIGHTING)
            except Exception:
                pass  # not available if lighting not initialized
            glPopMatrix()

    def _get_blink_scale(self, t):
        """
        Return vertical eye scale (1.0 = fully open, ~0.05 = closed).
        Uses time-based blink phase set by _update_subsystems().
        phase 0–1: closing (ease-in),  phase 1–2: opening (ease-out).
        Fatigue droops the eye (keeps scale slightly below 1.0 when open).
        Sleeping state forces eyes fully shut.
        """
        # Sleeping — eyes always shut (slowly droop closed then stay)
        if self.animation_state == 'sleeping':
            return 0.05
        phase = self._blink_phase
        if phase > 0.0:
            if phase < 1.0:
                return max(0.05, 1.0 - self._ease_in_cubic(phase))
            else:
                return max(0.05, self._ease_out_cubic(phase - 1.0))
        # Open — droop increases with fatigue (bottom eyelid rises)
        droop = self._fatigue * 0.30
        return max(0.35, 1.0 - droop)

    # ─── Snout drawing ──────────────────────────────────────────────────────
    def _draw_panda_snout(self):
        """Draw muzzle, nose tip, philtrum, teeth. Jaw drops by _jaw_open (0=closed→1=open)."""
        jaw_drop = self._jaw_open * 0.055   # max 5.5 units of downward jaw movement

        # Muzzle — off-white ellipsoid.
        # Center moved to HEAD_RADIUS * 0.90 so it protrudes visibly from the head sphere
        # (old: 0.84, muzzle barely broke the surface; real pandas have a distinct snout).
        # Radius increased from 0.138 to 0.155 and Z-scale from 0.55 to 0.75 for bulk.
        # Y kept at -0.065 (slightly below eye line, same as before).
        glPushMatrix()
        glTranslatef(0.0, -0.065, self.HEAD_RADIUS * 0.90)
        glScalef(1.10, 0.72, 0.75)
        glColor3f(0.96, 0.95, 0.91)
        self._draw_sphere(0.155, 18, 18)
        glPopMatrix()

        # Nose bridge ridge (dark grey)
        glPushMatrix()
        glTranslatef(0.0, 0.010, self.HEAD_RADIUS * 0.88)
        glScalef(0.75, 0.45, 0.35)
        glColor3f(0.18, 0.15, 0.15)
        self._draw_sphere(0.052, 12, 12)
        glPopMatrix()

        # Nose tip — shiny black oval
        glPushMatrix()
        glTranslatef(0.0, -0.020, self.HEAD_RADIUS * 0.92 + 0.002)
        glScalef(1.20, 0.75, 0.60)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.9, 0.9, 0.9, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 80.0)
        glColor3f(0.06, 0.06, 0.06)
        self._draw_sphere(0.048, 14, 14)
        # restore default specular
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 50.0)
        # Wet nose specular catch-light
        try:
            glDisable(GL_LIGHTING)
        except Exception:
            pass  # not available if lighting not initialized
        glPushMatrix()
        glTranslatef(0.012, 0.008, 0.026)
        glColor3f(1.0, 1.0, 1.0)
        self._draw_sphere(0.008, 6, 6)
        glPopMatrix()
        try:
            glEnable(GL_LIGHTING)
        except Exception:
            pass  # not available if lighting not initialized
        glPopMatrix()

        # Philtrum groove — dark line below nose
        glPushMatrix()
        glTranslatef(0.0, -0.068, self.HEAD_RADIUS * 0.94)
        glScalef(0.25, 1.10, 0.30)
        glColor3f(0.55, 0.45, 0.42)
        self._draw_sphere(0.022, 8, 8)
        glPopMatrix()

        # Lower jaw — drops when biting; subtle lower-muzzle mass
        jaw_y = -0.100 - jaw_drop
        glPushMatrix()
        glTranslatef(0.0, jaw_y, self.HEAD_RADIUS * 0.88)
        glScalef(0.95, 0.45 + jaw_drop * 2.0, 0.50)
        glColor3f(0.93, 0.91, 0.88)
        self._draw_sphere(0.110, 14, 14)
        glPopMatrix()

        # Mouth line — thin dark crescent (three corner spheres + centre dip)
        # When jaw drops, corners separate vertically
        for mx, my in [(-0.048, jaw_y + 0.006), (0.0, jaw_y + 0.000), (0.048, jaw_y + 0.006)]:
            glPushMatrix()
            glTranslatef(mx, my, self.HEAD_RADIUS * 0.91)
            glColor3f(0.30, 0.22, 0.20)
            self._draw_sphere(0.013, 8, 8)
            glPopMatrix()

        # Teeth (two white incisors — visible & scaled by jaw_open)
        if self._jaw_open > 0.05:
            teeth_scale = 0.6 + self._jaw_open * 0.8   # grow into view as jaw opens
            for tx in (-0.018, 0.018):
                glPushMatrix()
                glTranslatef(tx, jaw_y + 0.012, self.HEAD_RADIUS * 0.91)
                glScalef(0.55 * teeth_scale, 1.20, 0.50 * teeth_scale)
                glColor3f(0.97, 0.97, 0.94)
                self._draw_sphere(0.016, 8, 8)
                glPopMatrix()
            # Lower teeth row (smaller)
            for tx in (-0.024, -0.008, 0.008, 0.024):
                glPushMatrix()
                glTranslatef(tx, jaw_y - 0.008, self.HEAD_RADIUS * 0.90)
                glScalef(0.45 * teeth_scale, 0.90, 0.40 * teeth_scale)
                glColor3f(0.96, 0.96, 0.93)
                self._draw_sphere(0.012, 8, 8)
                glPopMatrix()
            # Tongue — pink, visible when mouth open
            if self._jaw_open > 0.12:
                tongue_scale = min(1.0, (self._jaw_open - 0.12) / 0.6)
                glPushMatrix()
                glTranslatef(0.0, jaw_y - 0.004, self.HEAD_RADIUS * 0.875)
                glScalef(0.90 * tongue_scale, 0.28, 0.55 * tongue_scale)
                glColor3f(0.92, 0.45, 0.52)
                self._draw_sphere(0.055, 12, 12)
                # Tongue tip (slightly lighter, rounded)
                glTranslatef(0.0, -0.005, 0.042)
                glScalef(0.80, 1.10, 0.70)
                glColor3f(0.95, 0.50, 0.58)
                self._draw_sphere(0.032, 10, 10)
                glPopMatrix()
        else:
            # Static top incisor hints (mouth closed)
            for tx in (-0.018, 0.018):
                glPushMatrix()
                glTranslatef(tx, -0.098, self.HEAD_RADIUS * 0.91)
                glScalef(0.55, 1.20, 0.50)
                glColor3f(0.97, 0.97, 0.94)
                self._draw_sphere(0.016, 8, 8)
                glPopMatrix()

        # Whisker pad bumps — two raised oval areas on muzzle sides
        for wx, wy in [(-0.072, -0.058), (0.072, -0.058)]:
            glPushMatrix()
            glTranslatef(wx, wy, self.HEAD_RADIUS * 0.87)
            glScalef(0.60, 0.45, 0.35)
            glColor3f(0.94, 0.92, 0.88)
            self._draw_sphere(0.040, 10, 10)
            glPopMatrix()

        # Nostril flare marks — tiny dark ovals flanking nose tip
        for nx in (-0.022, 0.022):
            glPushMatrix()
            glTranslatef(nx, -0.012, self.HEAD_RADIUS * 0.94)
            glScalef(0.40, 0.35, 0.30)
            glColor3f(0.12, 0.10, 0.10)
            self._draw_sphere(0.018, 8, 8)
            glPopMatrix()

        # Whiskers — 4 fine lines per side radiating from whisker pads
        # GL_LINES: each pair of vertices = one whisker
        glLineWidth(1.2)
        glColor3f(0.82, 0.80, 0.78)
        glBegin(GL_LINES)
        _wz = self.HEAD_RADIUS * 0.87
        for side in (-1.0, 1.0):
            # Four whiskers fanning out from pad centre
            _px = side * 0.072   # pad X centre
            _py = -0.058          # pad Y centre
            for angle_deg, length in [(-12.0, 0.10), (-3.0, 0.13), (7.0, 0.13), (17.0, 0.11), (26.0, 0.08)]:
                a = math.radians(angle_deg)
                dx = math.cos(a) * length * side
                dy = math.sin(a) * length
                glVertex3f(_px, _py, _wz)
                glVertex3f(_px + dx, _py + dy, _wz - 0.01)
        glEnd()
        glLineWidth(1.0)

    def _draw_panda_head_hair(self):
        """
        Draw the currently-equipped hair style on top of the panda's head.
        Coordinates are relative to the head's local matrix (already active when called).
        """
        style = self._hair_style
        body_col   = self._get_color('body')
        accent_col = self._get_color('accent')
        # Most styles use a slightly darker tinted version of the body colour
        hair_col = [max(0.0, c - 0.10) for c in body_col]

        if style == 'hair_wild_mane':
            # Ring of fluffy tufts around crown
            for i in range(8):
                a = i * math.pi / 4.0
                glPushMatrix()
                glTranslatef(math.cos(a) * 0.14, self.HEAD_RADIUS * 0.82, math.sin(a) * 0.10)
                glColor3f(*hair_col)
                self._draw_sphere(0.055, 8, 8)
                glPopMatrix()

        elif style == 'hair_mohawk':
            # Ridge of spikes along the skull centre line
            for i, (y, r) in enumerate([(0.80, 0.035), (0.88, 0.030), (0.92, 0.025),
                                         (0.86, 0.030), (0.80, 0.032)]):
                glPushMatrix()
                glTranslatef(0.0, self.HEAD_RADIUS * y, -0.05 + i * 0.025)
                glScalef(0.5, 1.6, 0.5)
                glColor3f(*accent_col)
                self._draw_sphere(r, 8, 8)
                glPopMatrix()

        elif style == 'hair_top_knot':
            # Bun sphere sitting on top
            glPushMatrix()
            glTranslatef(0.0, self.HEAD_RADIUS * 1.05, 0.0)
            glColor3f(*hair_col)
            self._draw_sphere(0.08, 12, 12)
            glPopMatrix()
            # Knot band ring
            for i in range(6):
                a = i * math.pi / 3.0
                glPushMatrix()
                glTranslatef(math.cos(a) * 0.06, self.HEAD_RADIUS * 1.04, math.sin(a) * 0.06)
                glColor3f(*accent_col)
                self._draw_sphere(0.018, 6, 6)
                glPopMatrix()

        elif style == 'hair_spiked':
            # 5 short spiky cones
            for i, (a, y) in enumerate([(0, 0.95), (0.4, 0.90), (-0.4, 0.90),
                                          (0.8, 0.85), (-0.8, 0.85)]):
                glPushMatrix()
                glTranslatef(math.sin(a) * 0.10, self.HEAD_RADIUS * y, 0.0)
                glScalef(0.4, 2.0, 0.4)
                glColor3f(*accent_col)
                self._draw_sphere(0.028, 6, 6)
                glPopMatrix()

        elif style == 'hair_bowl_cut':
            # Flat-bottomed dome cap
            glPushMatrix()
            glTranslatef(0.0, self.HEAD_RADIUS * 0.55, 0.0)
            glScalef(1.08, 0.60, 1.00)
            glColor3f(*hair_col)
            self._draw_sphere(self.HEAD_RADIUS * 0.98, 16, 16)
            glPopMatrix()

        elif style == 'hair_braid':
            # Series of pearls along one side representing a braid
            for i in range(5):
                glPushMatrix()
                glTranslatef(-self.HEAD_RADIUS * 0.85,
                             self.HEAD_RADIUS * (0.65 - i * 0.18),
                             0.0)
                glColor3f(*hair_col)
                self._draw_sphere(0.030 if i < 4 else 0.020, 8, 8)
                glPopMatrix()

        elif style == 'hair_afro':
            # Large poofy sphere cluster
            glPushMatrix()
            glTranslatef(0.0, self.HEAD_RADIUS * 0.75, 0.0)
            glColor3f(*hair_col)
            self._draw_sphere(0.22, 16, 16)
            glPopMatrix()
            # Smaller surrounding puffs
            for i in range(6):
                a = i * math.pi / 3.0
                glPushMatrix()
                glTranslatef(math.cos(a) * 0.18, self.HEAD_RADIUS * 0.60, math.sin(a) * 0.12)
                glColor3f(*hair_col)
                self._draw_sphere(0.10, 10, 10)
                glPopMatrix()

        elif style == 'hair_dreadlocks':
            # Several elongated oval strands hanging down
            for i in range(5):
                a = (i - 2) * 0.22
                glPushMatrix()
                glTranslatef(math.sin(a) * 0.14, self.HEAD_RADIUS * 0.40, 0.0)
                glScalef(0.35, 2.5, 0.35)
                glColor3f(*hair_col)
                self._draw_sphere(0.040, 8, 8)
                glPopMatrix()

    # ─── Arm drawing ────────────────────────────────────────────────────────
    def _draw_panda_arms(self, limb, bob, t=0, sub_pose: dict | None = None):
        """Draw arms with follow-through overshoot, uneven breathing, paw/claws."""
        if sub_pose is None:
            sub_pose = {}
        # NOTE: this method is called INSIDE the torso glPushMatrix which already
        # translates by (0, 0.30 + bob, 0).  Do NOT add bob here again or the arms
        # will appear to move at 2× the body bob rate.
        # arm_y from class constant ARM_Y: shoulder height inside the body
        # (body extends ±0.25 from torso centre; ARM_Y=0.18 sits at shoulder level).
        arm_y   = self.ARM_Y
        arm_x   = self.BODY_WIDTH + 0.06
        ac = self._get_color('accent')   # fur-style accent colour for arm patches

        swing_idle = 5.0 * math.sin(t * 0.030)  # tiny idle sway

        # Asymmetric breathing offset (uneven arm sway amplitude)
        breath_offset = [self._asym.get('breath_l_offset', 0.0),
                         self._asym.get('breath_r_offset', 0.0)]

        # Sub-pose overrides (grooming, stretching, scratching, yawning)
        sub_l = sub_pose.get('arm_l', 0.0)
        sub_r = sub_pose.get('arm_r', 0.0)

        for idx, (side, key) in enumerate(((-1, 'left_arm_angle'), (1, 'right_arm_angle'))):
            sub_extra = sub_l if idx == 0 else sub_r
            angle = (limb.get(key, 0)
                     + swing_idle * side
                     + self._arm_over[idx]           # follow-through overshoot
                     + breath_offset[idx] * 180.0    # tiny uneven breathing
                     + sub_extra)                    # idle sub-behavior offset

            glPushMatrix()
            glTranslatef(side * arm_x, arm_y + 0.06, 0.0)
            glRotatef(-side * 8, 0.0, 0.0, 1.0)   # arms hang slightly outward
            glRotatef(angle, 1.0, 0.0, 0.0)

            # Upper arm — thick ovoid in accent colour
            glPushMatrix()
            glScalef(0.115, 0.200, 0.115)
            glTranslatef(0.0, -0.50, 0.0)
            glColor3f(*ac)
            self._draw_sphere(1.0, 22, 22)
            glPopMatrix()

            # Elbow joint
            glPushMatrix()
            glTranslatef(0.0, -self.ARM_LENGTH * 0.45, 0.0)
            glColor3f(*[min(1.0, c + 0.02) for c in ac])
            self._draw_sphere(0.075, 12, 12)
            glPopMatrix()

            # Forearm — slightly thinner
            glPushMatrix()
            glTranslatef(0.0, -self.ARM_LENGTH * 0.45, 0.0)
            glScalef(0.095, 0.185, 0.095)
            glTranslatef(0.0, -0.50, 0.0)
            glColor3f(*ac)
            self._draw_sphere(1.0, 14, 14)
            glPopMatrix()

            # Paw (rounded teardrop)
            glPushMatrix()
            glTranslatef(0.0, -self.ARM_LENGTH * 0.88, 0.0)
            glScalef(1.20, 0.65, 1.15)
            glColor3f(*ac)
            self._draw_sphere(0.082, 18, 18)
            # Paw pad (pink ellipse on palm face)
            glPushMatrix()
            glTranslatef(0.0, 0.0, 0.07)
            glScalef(0.70, 0.58, 0.30)
            glColor3f(0.78, 0.48, 0.55)
            self._draw_sphere(0.082, 10, 10)
            glPopMatrix()
            # Pseudo-thumb (enlarged radial sesamoid) — inner edge of paw
            # This is the iconic panda "extra thumb" used for gripping bamboo
            glPushMatrix()
            glTranslatef(-side * 0.072, 0.012, 0.035)
            glScalef(0.50, 0.38, 0.42)
            glColor3f(*ac)
            self._draw_sphere(0.058, 10, 10)
            glPopMatrix()
            # Individual toe pads — 4 small pink ovals above main pad
            for ti in range(4):
                tx = (ti - 1.5) * 0.030
                glPushMatrix()
                glTranslatef(tx, 0.055, 0.065)
                glScalef(0.42, 0.35, 0.28)
                glColor3f(0.72, 0.42, 0.50)
                self._draw_sphere(0.028, 8, 8)
                glPopMatrix()
            glPopMatrix()

            # Wrist black band — ring of accent colour just above the paw
            glPushMatrix()
            glTranslatef(0.0, -self.ARM_LENGTH * 0.78, 0.0)
            glScalef(0.130, 0.058, 0.130)
            glColor3f(*ac)
            self._draw_sphere(1.0, 12, 12)
            glPopMatrix()

            # Claws — 4 small dark cones arranged in arc
            glPushMatrix()
            glTranslatef(0.0, -self.ARM_LENGTH * 0.88 - 0.07, 0.0)
            for ci in range(4):
                cx = (ci - 1.5) * 0.028
                glPushMatrix()
                glTranslatef(cx, -0.012, 0.06)
                glRotatef(-25, 1.0, 0.0, 0.0)
                glColor3f(0.20, 0.18, 0.16)
                self._draw_claw(0.032, 0.012)
                glPopMatrix()
            glPopMatrix()

            glPopMatrix()  # end arm

    # ─── Leg drawing ────────────────────────────────────────────────────────
    def _draw_panda_legs(self, limb, bob, t=0):
        """Draw stocky legs with thigh, shin, foot and claws."""
        # NOTE: called INSIDE the torso glPushMatrix; bob is already applied there.
        # Do NOT add bob here or legs will double-bob relative to the body.
        # leg_y = -0.24: pivot is well below the body centre so legs protrude
        # visibly beneath the belly (old value -0.04 hid them inside the body).
        leg_y = -0.24
        # 0.78 × BODY_WIDTH = 0.437 — wider than old 0.80 × 0.50 = 0.40
        # despite the smaller multiplier, because BODY_WIDTH increased to 0.56.
        leg_x = self.BODY_WIDTH * 0.78   # aligns with hip-patch positions
        ac = self._get_color('accent')   # fur-style accent colour for leg patches

        for side, key in ((-1, 'left_leg_angle'), (1, 'right_leg_angle')):
            angle = limb.get(key, 0)

            glPushMatrix()
            glTranslatef(side * leg_x, leg_y, 0.0)
            glRotatef(angle, 1.0, 0.0, 0.0)

            # Thigh — wide ovoid in accent colour
            glPushMatrix()
            glScalef(0.155, 0.195, 0.155)
            glTranslatef(0.0, -0.50, 0.0)
            glColor3f(*ac)
            self._draw_sphere(1.0, 22, 22)
            glPopMatrix()

            # Knee joint
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.42, 0.0)
            glColor3f(*[min(1.0, c + 0.02) for c in ac])
            self._draw_sphere(0.082, 12, 12)
            glPopMatrix()

            # Shin
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.42, 0.0)
            glScalef(0.130, 0.160, 0.130)
            glTranslatef(0.0, -0.50, 0.0)
            glColor3f(*ac)
            self._draw_sphere(1.0, 14, 14)
            glPopMatrix()

            # Foot — flattened ovoid, slightly forward
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.85, 0.045)
            glScalef(1.25, 0.55, 1.55)
            glColor3f(*ac)
            self._draw_sphere(0.092, 16, 16)
            # Foot pad (central pink pad)
            glPushMatrix()
            glTranslatef(0.0, -0.06, 0.04)
            glScalef(0.65, 0.30, 0.75)
            glColor3f(0.78, 0.48, 0.55)
            self._draw_sphere(0.092, 10, 10)
            glPopMatrix()
            # Individual toe pads — 5 small pink spheres in an arc
            for ti in range(5):
                ta = (ti - 2) * 0.30   # angular spread
                glPushMatrix()
                glTranslatef(math.sin(ta) * 0.065, -0.052, 0.08 + math.cos(ta) * 0.010)
                glScalef(0.55, 0.30, 0.55)
                glColor3f(0.74, 0.45, 0.52)
                self._draw_sphere(0.028, 8, 8)
                glPopMatrix()
            # Hind toe pads
            for ti in range(4):
                tx = (ti - 1.5) * 0.032
                glPushMatrix()
                glTranslatef(tx, -0.005, 0.055)
                glScalef(0.42, 0.32, 0.28)
                glColor3f(0.72, 0.42, 0.50)
                self._draw_sphere(0.025, 8, 8)
                glPopMatrix()
            glPopMatrix()

            # Ankle black band — ring just above the foot
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.74, 0.015)
            glScalef(0.155, 0.055, 0.155)
            glColor3f(*ac)
            self._draw_sphere(1.0, 12, 12)
            glPopMatrix()

            # Toe claws — 5 per foot
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.85 - 0.055, 0.09)
            for ci in range(5):
                cx = (ci - 2.0) * 0.028
                glPushMatrix()
                glTranslatef(cx, -0.006, 0.0)
                glRotatef(-30, 1.0, 0.0, 0.0)
                glColor3f(0.22, 0.19, 0.16)
                self._draw_claw(0.028, 0.010)
                glPopMatrix()
            glPopMatrix()

            glPopMatrix()  # end leg
    
    def _draw_sphere(self, radius, slices, stacks):
        """Draw a smooth sphere using GLU quadrics."""
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluQuadricTexture(quad, GL_TRUE)
        gluSphere(quad, radius, slices, stacks)
        gluDeleteQuadric(quad)

    def _draw_claw(self, length: float, base_radius: float):
        """Draw a single curved claw using a tapered cylinder + sphere tip."""
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluCylinder(quad, base_radius, base_radius * 0.08, length, 8, 2)
        gluDeleteQuadric(quad)
        # Tip sphere
        glPushMatrix()
        glTranslatef(0.0, 0.0, length)
        self._draw_sphere(base_radius * 0.08, 6, 6)
        glPopMatrix()
    
    def _draw_item_3d(self, item):
        """Draw a 3D item (toy, food, or clothing)."""
        glPushMatrix()
        glTranslatef(item['x'], item['y'], item['z'])
        glRotatef(item.get('rotation', 0), 0.0, 1.0, 0.0)
        
        # Draw based on item type
        item_type = item.get('type', 'toy')
        if item_type == 'food':
            self._draw_food_item(item)
        elif item_type == 'toy':
            self._draw_toy_item(item)
        elif item_type == 'clothing':
            self._draw_clothing_item(item)
        
        glPopMatrix()

    @staticmethod
    def _matches_subtype(subtype: str, keywords: tuple) -> bool:
        """Return True if any keyword appears in subtype string.  Used by food/toy renderers."""
        return any(k in subtype for k in keywords)

    def _draw_food_item(self, item):
        """Draw food item in 3D — shaped by item subtype."""
        color   = item.get('color', [0.8, 0.2, 0.2])
        subtype = str(item.get('id', item.get('name', ''))).lower()
        quad    = gluNewQuadric()
        glColor3f(*color)
        try:
            if self._matches_subtype(subtype, ('bamboo', 'stick', 'shoot')):
                # Bamboo shoot: tall segmented green cylinder
                glColor3f(0.35, 0.70, 0.20)
                for seg in range(4):
                    glPushMatrix()
                    glTranslatef(0.0, seg * 0.06 - 0.05, 0.0)
                    gluCylinder(quad, 0.025, 0.020, 0.065, 8, 1)
                    glColor3f(0.25, 0.55, 0.15)
                    gluDisk(quad, 0.0, 0.030, 8, 1)
                    glColor3f(0.35, 0.70, 0.20)
                    glPopMatrix()
            elif self._matches_subtype(subtype, ('apple', 'fruit')):
                # Apple: red sphere with green leaf on top
                glColor3f(0.85, 0.12, 0.10)
                self._draw_sphere(0.09, 14, 14)
                glPushMatrix()
                glTranslatef(0.0, 0.10, 0.0)
                glColor3f(0.18, 0.60, 0.12)
                glScalef(0.8, 0.3, 0.4)
                self._draw_sphere(0.04, 8, 8)
                glPopMatrix()
            elif self._matches_subtype(subtype, ('fish', 'salmon')):
                # Fish: tapered body + tail
                glColor3f(*color)
                glPushMatrix()
                glScalef(1.4, 0.55, 0.6)
                self._draw_sphere(0.08, 12, 12)
                glPopMatrix()
                glPushMatrix()
                glTranslatef(0.12, 0.0, 0.0)
                glBegin(GL_TRIANGLES)
                glVertex3f(0.0, 0.0, 0.0)
                glVertex3f(0.07, 0.05, 0.0)
                glVertex3f(0.07, -0.05, 0.0)
                glEnd()
                glPopMatrix()
            elif self._matches_subtype(subtype, ('cookie', 'biscuit')):
                # Cookie: flattened disc with chocolate dots
                glColor3f(0.80, 0.60, 0.35)
                glPushMatrix()
                glScalef(1.0, 0.3, 1.0)
                self._draw_sphere(0.09, 12, 12)
                glPopMatrix()
                glColor3f(0.45, 0.25, 0.10)
                for cx, cz in ((0.04, 0.03), (-0.04, 0.03), (0.0, -0.04)):
                    glPushMatrix()
                    glTranslatef(cx, 0.03, cz)
                    self._draw_sphere(0.015, 6, 6)
                    glPopMatrix()
            else:
                glColor3f(*color)
                self._draw_sphere(0.09, 14, 14)
        finally:
            gluDeleteQuadric(quad)

    def _draw_toy_item(self, item):
        """Draw toy item in 3D — shaped by item subtype."""
        color   = item.get('color', [0.2, 0.4, 0.85])
        subtype = str(item.get('id', item.get('name', ''))).lower()
        quad    = gluNewQuadric()
        try:
            if self._matches_subtype(subtype, ('ball', 'orb', 'sphere')):
                # Ball: coloured sphere with contrasting stripe
                glColor3f(*color)
                self._draw_sphere(0.10, 16, 16)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                alt = [1.0 - c for c in color]
                glColor4f(*alt, 0.7)
                glPushMatrix()
                glScalef(1.0, 0.22, 1.0)
                self._draw_sphere(0.105, 14, 14)
                glPopMatrix()
                glDisable(GL_BLEND)
            elif self._matches_subtype(subtype, ('wand', 'magic')):
                # Toy wand: thin shaft + glowing orb tip
                glColor3f(0.55, 0.35, 0.15)
                gluCylinder(quad, 0.012, 0.010, 0.22, 8, 1)
                glPushMatrix()
                glTranslatef(0.0, 0.0, 0.22)
                glColor3f(1.0, 0.85, 0.20)
                self._draw_sphere(0.025, 10, 10)
                glPopMatrix()
            elif self._matches_subtype(subtype, ('flower', 'daisy', 'rose')):
                # Flower: green stem + five petals + yellow centre
                glColor3f(0.25, 0.65, 0.20)
                gluCylinder(quad, 0.008, 0.007, 0.14, 6, 1)
                glPushMatrix()
                glTranslatef(0.0, 0.0, 0.14)
                for i in range(5):
                    a = math.radians(i * 72)
                    glPushMatrix()
                    glTranslatef(math.cos(a) * 0.04, math.sin(a) * 0.04, 0.0)
                    glColor3f(*color)
                    self._draw_sphere(0.025, 8, 8)
                    glPopMatrix()
                glColor3f(1.0, 0.90, 0.15)
                self._draw_sphere(0.020, 8, 8)
                glPopMatrix()
            elif self._matches_subtype(subtype, ('teddy', 'bear', 'plush', 'stuffed')):
                # Plush teddy: body + head + ears
                glColor3f(0.72, 0.50, 0.30)
                self._draw_sphere(0.08, 12, 12)
                glPushMatrix()
                glTranslatef(0.0, 0.10, 0.0)
                self._draw_sphere(0.06, 12, 12)
                for side in (-1.0, 1.0):
                    glPushMatrix()
                    glTranslatef(side * 0.05, 0.05, 0.0)
                    self._draw_sphere(0.022, 8, 8)
                    glPopMatrix()
                glPopMatrix()
            else:
                glColor3f(*color)
                self._draw_cube(0.08)
        finally:
            gluDeleteQuadric(quad)
    
    def _draw_clothing_item(self, item):
        """Draw clothing item dropped in the world (not yet equipped)."""
        # Draw as a folded-cloth diamond shape using two crossed quads
        color = item.get('color', [0.5, 0.3, 0.8])
        glColor3f(*color)
        s = 0.12
        glBegin(GL_QUADS)
        # Horizontal quad
        glVertex3f(-s, 0.0, -s * 0.4)
        glVertex3f(s, 0.0, -s * 0.4)
        glVertex3f(s, 0.0, s * 0.4)
        glVertex3f(-s, 0.0, s * 0.4)
        # Vertical quad (crossed)
        glVertex3f(0.0, -s, -s * 0.4)
        glVertex3f(0.0, -s, s * 0.4)
        glVertex3f(0.0, s, s * 0.4)
        glVertex3f(0.0, s, -s * 0.4)
        glEnd()
    
    def _draw_cube(self, size):
        """Draw a cube."""
        glBegin(GL_QUADS)
        # Front face
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(-size, -size, size)
        glVertex3f(size, -size, size)
        glVertex3f(size, size, size)
        glVertex3f(-size, size, size)
        # Back face
        glNormal3f(0.0, 0.0, -1.0)
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, size, -size)
        glVertex3f(size, size, -size)
        glVertex3f(size, -size, -size)
        # Top face
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-size, size, -size)
        glVertex3f(-size, size, size)
        glVertex3f(size, size, size)
        glVertex3f(size, size, -size)
        # Bottom face
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-size, -size, -size)
        glVertex3f(size, -size, -size)
        glVertex3f(size, -size, size)
        glVertex3f(-size, -size, size)
        # Right face
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(size, -size, -size)
        glVertex3f(size, size, -size)
        glVertex3f(size, size, size)
        glVertex3f(size, -size, size)
        # Left face
        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, -size, size)
        glVertex3f(-size, size, size)
        glVertex3f(-size, size, -size)
        glEnd()
    
    # ─── Easing functions ────────────────────────────────────────────────────
    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Decelerate: fast start → slow stop."""
        t = max(0.0, min(1.0, t))
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _ease_in_cubic(t: float) -> float:
        """Accelerate: slow start → fast stop."""
        t = max(0.0, min(1.0, t))
        return t ** 3

    @staticmethod
    def _ease_in_out_cubic(t: float) -> float:
        """Smooth S-curve."""
        t = max(0.0, min(1.0, t))
        return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2

    # ─── Per-frame sub-system updates ────────────────────────────────────────
    def _update_subsystems(self, now: float, dt: float):
        """
        Update all secondary animation subsystems once per timer tick.

        Separated from _update_animation for readability; called at the
        top of _update_animation before requesting a repaint.
        """
        # ── Fatigue accumulation / recovery ──────────────────────────────────
        if self.animation_state == 'sleeping':
            self._fatigue = max(0.0, self._fatigue - self._fatigue_recovery * dt)
        else:
            self._fatigue = min(1.0, self._fatigue + self._fatigue_rate * dt)

        # Auto-sleep when exhausted
        if self._fatigue >= 0.98 and self.animation_state not in ('sleeping',):
            self._set_state_direct('sleeping')
            self._emotion = 'tired'
            self._emotion_weights = {k: 0.0 for k in self._emotion_weights}
            self._emotion_weights['tired'] = 1.0

        # ── Boredom tracking ──────────────────────────────────────────────────
        self._boredom_t += dt
        if self._boredom_t > self._boredom_threshold and self._emotion == 'neutral':
            self._emotion = 'bored'
            self._emotion_weights['neutral'] = 0.0
            self._emotion_weights['bored'] = 1.0

        # ── Time-based blink system ───────────────────────────────────────────
        if now >= self._next_blink_t:
            self._blink_phase = 0.001   # start a blink
            # Decide on double-blink
            self._double_blink = random.random() < self._micro['blink_double_prob']
            jitter = random.uniform(-0.6, 0.6)
            self._next_blink_t = (now + self._micro['blink_base']
                                  + (3.0 if self._double_blink else 0.0) + jitter)
            # Tired panda blinks more slowly
            self._blink_speed = max(5.0, 8.0 - 3.0 * self._fatigue)

        if self._blink_phase > 0.0:
            self._blink_phase += self._blink_speed * dt
            if self._blink_phase >= 2.0:
                if self._double_blink:
                    self._blink_phase = 0.0
                    self._double_blink = False
                    # Schedule the second blink in ~0.15 s
                    self._next_blink_t = now + 0.15
                else:
                    self._blink_phase = 0.0   # blink complete

        # ── Ear spring physics ────────────────────────────────────────────────
        stiffness = self._micro['ear_stiffness']
        damping   = self._micro['ear_damping']

        # Target: slight flick on large body-bob direction changes; else rest
        body_jerk = abs(self._get_body_bob()) * 120.0   # proportional nudge
        for i in range(2):
            # Spring toward 0
            spring_force = -stiffness * self._ear_pos[i]
            damp_force   = -damping * self._ear_vel[i]
            # Body movement nudges ears opposite to motion (follow-through)
            self._ear_vel[i] += (spring_force + damp_force + body_jerk * 0.06 * (1 - 2 * i)) * dt
            self._ear_pos[i] += self._ear_vel[i] * dt

        # Asymmetric ear twitch: biased ear has higher probability
        twitch_mult = self._asym.get('ear_twitch_mult', [1.0, 1.0])
        for i in range(2):
            base_prob = 0.0015 * twitch_mult[i]
            if random.random() < base_prob:
                self._ear_vel[i] += random.uniform(-8.0, 8.0)

        # ── Tail spring physics ────────────────────────────────────────────────
        state = self.animation_state
        # Happy/excited states drive tail wag; idle = gentle sway; others = droop
        wag_amp = _TAIL_WAG_AMP.get(state, 4.0)
        if wag_amp > 0:
            # Oscillating drive — frequency scales with animation energy
            freq = 0.22 if state in ('celebrating', 'waving') else 0.12
            tail_target = wag_amp * math.sin(self.animation_frame * freq)
        else:
            tail_target = 0.0
        _tail_spring = 18.0 * (tail_target - self._tail_angle)
        _tail_damp   = -6.0 * self._tail_vel
        self._tail_vel   += (_tail_spring + _tail_damp) * dt
        self._tail_angle += self._tail_vel * dt

        # Tail droop: down when tired/sleeping, up when happy
        droop_target = 20.0 if state == 'sleeping' else (-5.0 if wag_amp >= 20 else 8.0)
        self._tail_droop += (droop_target - self._tail_droop) * 2.5 * dt

        # ── Cursor look interpolation (eased) ─────────────────────────────────
        if self._cursor_wpos is not None:
            cx = self._cursor_wpos.x() - self.width()  / 2.0
            cy = self._cursor_wpos.y() - self.height() / 2.0
            proximity = 1.0 - min(1.0, math.hypot(cx, cy) / max(self.width(), 1))
            self._look_yaw_tgt   = max(-12.0, min(12.0, cx / max(self.width(),  1) * 18.0)) * proximity
            self._look_pitch_tgt = max(-8.0,  min( 8.0, -cy / max(self.height(), 1) * 12.0)) * proximity

        ease = min(1.0, dt * 6.0)
        self._look_yaw   += (self._look_yaw_tgt   - self._look_yaw)   * ease
        self._look_pitch += (self._look_pitch_tgt - self._look_pitch) * ease

        # ── State blend alpha ─────────────────────────────────────────────────
        if self._blend_alpha < 1.0:
            elapsed_blend = now - self._blend_start_t
            raw = elapsed_blend / max(self._blend_duration, 1e-6)
            self._blend_alpha = self._ease_in_out_cubic(raw)

        # ── Squash-and-stretch spring ─────────────────────────────────────────
        was_airborne_now = self.panda_y > -0.68
        if self._was_airborne and not was_airborne_now:
            # Landing impact: squash down
            impact = min(abs(self.velocity_y) * 0.15, 0.30)
            self._squash_y    = max(0.72, 1.0 - impact)
            self._squash_vel  = 0.0
        self._was_airborne = was_airborne_now

        # Spring squash back to 1.0 (stiffness=24, damping=0.55)
        spring = 24.0 * (1.0 - self._squash_y)
        damp   = -0.55 * self._squash_vel
        self._squash_vel += (spring + damp) * dt
        self._squash_y   += self._squash_vel * dt
        self._squash_y    = max(0.60, min(1.30, self._squash_y))

        # ── Anticipation countdown ────────────────────────────────────────────
        if self._anticipation_t > 0.0:
            self._anticipation_t -= dt
            if self._anticipation_t <= 0.0:
                action = self._pending_action
                self._pending_action   = None
                self._anticipation_t   = 0.0
                if action:
                    self._set_state_direct(action)

        # ── Follow-through springs ────────────────────────────────────────────
        self._update_follow_through(dt)

        # ── Saccades + eye-lead ───────────────────────────────────────────────
        self._update_saccades(now, dt)

        # ── Micro-holds / reaction-delay queue ───────────────────────────────
        fired = [item for item in self._reaction_delay_q if now >= item[0]]
        for item in fired:
            self._reaction_delay_q.remove(item)
            try:
                item[1]()
            except Exception:
                pass

        # ── Idle loop pause ───────────────────────────────────────────────────
        if self.animation_state == 'idle':
            self._idle_pause_countdown -= dt
            if self._idle_pause_countdown <= 0.0:
                self._hold_t = random.uniform(0.12, 0.32)
                self._idle_pause_countdown = random.uniform(9.0, 20.0)

        # ── Decay reaction states ─────────────────────────────────────────────
        self._whoa_t    = max(0.0, self._whoa_t    - dt)
        self._flinch_t  = max(0.0, self._flinch_t  - dt)
        self._surprised_eye_t = max(0.0, self._surprised_eye_t - dt)
        self._ui_interact_t   = max(0.0, self._ui_interact_t   - dt)

        # ── Jaw / bite animation ──────────────────────────────────────────────
        # Phase: 0.0→0.5 = opening (ease-in), 0.5→1.0 = closing (ease-out)
        # _ui_interact_type == 'bite' drives _jaw_open via interact timer progress
        if self._ui_interact_type == 'bite' and self._ui_interact_t > 0.0:
            phase = 1.0 - (self._ui_interact_t / max(self._bite_duration, 0.01))
            if phase < 0.5:
                self._jaw_open = self._ease_in_cubic(phase * 2.0)
            else:
                self._jaw_open = 1.0 - self._ease_out_cubic((phase - 0.5) * 2.0)
            # Chomp sound at peak
            if 0.48 < phase < 0.53 and not getattr(self, '_bite_chomp_played', False):
                self._play_sound('chomp')
                self._bite_chomp_played = True
        else:
            # Decay jaw closed smoothly
            self._jaw_open = max(0.0, self._jaw_open - dt * 6.0)
            if self._ui_interact_t <= 0.0:
                self._bite_chomp_played = False

        # Flinch → trigger quick blink
        if self._flinch_t > 0.1 and self._blink_phase == 0.0:
            self._blink_phase = 0.001

        # ── Wobble / stumble ─────────────────────────────────────────────────
        self._update_wobble(dt)

        # ── Idle sub-behaviors (grooming, stretching, etc.) ──────────────────
        self._update_idle_sub_behavior(dt)

        # ── Micro-emotion decay ───────────────────────────────────────────────
        # iterate over a snapshot so set_micro_emotion() won't cause RuntimeError
        for k in tuple(self._micro_emotion):
            self._micro_emotion[k] = max(0.0, self._micro_emotion[k] - dt * 0.08)

    # ─── Follow-through springs ───────────────────────────────────────────────
    def _update_follow_through(self, dt: float):
        """
        Update all follow-through springs:
        head lag, belly jiggle, per-arm overshoot, eyelid settle.
        """
        # ── Head lag (spring: head lags body horizontal acceleration) ─────────
        body_vx = self.velocity_x
        body_ax = (body_vx - self._body_vel_prev_x) / max(dt, 1e-4)
        self._body_vel_prev_x = body_vx
        # Target: pull head opposite to acceleration (fish-tail effect)
        head_lag_tgt = -body_ax * 0.08
        spring = 18.0 * (head_lag_tgt - self._head_lag)
        damp   = -0.60 * self._head_lag_vel
        self._head_lag_vel += (spring + damp) * dt
        self._head_lag     += self._head_lag_vel * dt
        self._head_lag      = max(-8.0, min(8.0, self._head_lag))

        # ── Belly / fur jiggle spring ─────────────────────────────────────────
        # Spring back to 1.0; excited by body-bob changes
        bob_now = self._get_body_bob()
        belly_spring  = 14.0 * (1.0 - self._belly_y)
        belly_damp    = -0.50 * self._belly_vel
        # Add small periodic nudge from breathing
        belly_drive   = bob_now * 2.5
        self._belly_vel += (belly_spring + belly_damp + belly_drive) * dt
        self._belly_y   += self._belly_vel * dt
        self._belly_y    = max(0.88, min(1.12, self._belly_y))

        # ── Per-arm overshoot springs ─────────────────────────────────────────
        for i in range(2):
            spring_f = -20.0 * self._arm_over[i]
            damp_f   = -0.58 * self._arm_over_vel[i]
            self._arm_over_vel[i] += (spring_f + damp_f) * dt
            self._arm_over[i]     += self._arm_over_vel[i] * dt
            self._arm_over[i]      = max(-15.0, min(15.0, self._arm_over[i]))

        # ── Eyelid settle spring (tiny overshoot when blink re-opens) ─────────
        # When blink_phase crosses 2.0 (fully open), kick eyelid_vel upward
        # so eyelid briefly opens wider than normal, then settles back
        if self._blink_phase == 0.0 and abs(self._eyelid_extra) < 1e-3:
            pass   # at rest
        eyelid_spring = -22.0 * self._eyelid_extra
        eyelid_damp   = -0.65 * self._eyelid_vel
        self._eyelid_vel   += (eyelid_spring + eyelid_damp) * dt
        self._eyelid_extra += self._eyelid_vel * dt
        self._eyelid_extra  = max(-0.08, min(0.12, self._eyelid_extra))

        # ── Body pitch spring (quadruped stances) ─────────────────────────────
        pitch_tgt = _BODY_PITCH_TARGETS.get(self.animation_state, 0.0)
        pitch_spring = 16.0 * (pitch_tgt - self._body_pitch_cur)
        pitch_damp   = -5.0 * self._body_pitch_vel
        self._body_pitch_vel += (pitch_spring + pitch_damp) * dt
        self._body_pitch_cur += self._body_pitch_vel * dt
        self._body_pitch_cur  = max(-90.0, min(90.0, self._body_pitch_cur))

    # ─── Saccade + eye-lead system ────────────────────────────────────────────
    def _update_saccades(self, now: float, dt: float):
        """
        Drive eye saccades (quick micro-darts) and eye-lead / head-follow.
        Eyes move first at high speed; head follows at ~1/4 the speed.
        """
        # ── Schedule next saccade ─────────────────────────────────────────────
        if now >= self._next_saccade_t and self._saccade_hold_t <= 0.0:
            # Pick a random target offset relative to current look direction
            max_sac = 5.0 + self._emotion_weights.get('excited', 0.0) * 4.0
            self._saccade_tgt_yaw   = random.uniform(-max_sac, max_sac)
            self._saccade_tgt_pitch = random.uniform(-max_sac * 0.6, max_sac * 0.6)
            self._saccade_hold_t    = random.uniform(0.15, 0.70)
            interval = self._micro['blink_base'] * random.uniform(0.5, 0.9)
            self._next_saccade_t = now + interval

        # ── Move saccade toward target (fast dart) ────────────────────────────
        if self._saccade_hold_t > 0.0:
            self._saccade_hold_t -= dt
            spd = self._saccade_speed * dt
            dy = self._saccade_tgt_yaw   - self._saccade_yaw
            dp = self._saccade_tgt_pitch - self._saccade_pitch
            self._saccade_yaw   += max(-spd, min(spd, dy))
            self._saccade_pitch += max(-spd, min(spd, dp))
        else:
            # Return to cursor direction
            self._saccade_yaw   *= max(0.0, 1.0 - dt * 5.0)
            self._saccade_pitch *= max(0.0, 1.0 - dt * 5.0)

        # ── Eye-lead: eyes = cursor_look + saccade ────────────────────────────
        target_eye_yaw   = self._look_yaw_tgt   + self._saccade_yaw
        target_eye_pitch = self._look_pitch_tgt + self._saccade_pitch
        eye_speed = min(1.0, dt * 16.0)   # fast
        self._eye_yaw   += (target_eye_yaw   - self._eye_yaw)   * eye_speed
        self._eye_pitch += (target_eye_pitch - self._eye_pitch) * eye_speed

        # ── Head follows eyes with lag ────────────────────────────────────────
        head_speed = min(1.0, dt * 4.0)   # much slower
        self._eye_head_yaw   += (self._eye_yaw   - self._eye_head_yaw)   * head_speed
        self._eye_head_pitch += (self._eye_pitch - self._eye_head_pitch) * head_speed

    # ─── Wobble / stumble system ──────────────────────────────────────────────
    def _update_wobble(self, dt: float):
        """
        Pandas are famously uncoordinated. Simulate subtle lateral sway with
        occasional slow overcorrection and random stumbles.
        Only active when panda is upright (idle, working, waving, celebrating).
        """
        upright = self.animation_state in (
            'idle', 'working', 'waving', 'celebrating', 'sitting_back'
        )
        if not upright:
            # Damp wobble quickly when not upright
            self._wobble_x   *= max(0.0, 1.0 - dt * 8.0)
            self._wobble_vel *= max(0.0, 1.0 - dt * 8.0)
            return

        # Spring back to centre with very soft stiffness (slow overcorrect)
        spring = -3.5 * self._wobble_x
        damp   = -0.45 * self._wobble_vel
        # Tiny random breathing-rhythm perturbation
        noise = random.gauss(0, 0.04) if random.random() < 0.15 else 0.0
        self._wobble_vel += (spring + damp + noise) * dt
        self._wobble_x   += self._wobble_vel * dt
        self._wobble_x    = max(-6.0, min(6.0, self._wobble_x))

        # Stumble countdown
        self._stumble_timer -= dt
        if self._stumble_timer <= 0.0 and not self._stumble_active:
            # Kick a random stumble
            self._wobble_vel += random.choice([-1, 1]) * random.uniform(12.0, 22.0)
            self._stumble_active = True
            self._stumble_timer  = random.uniform(20.0, 60.0)
            QTimer.singleShot(int(random.uniform(0.4, 0.9) * 1000),
                              lambda: setattr(self, '_stumble_active', False))

    # ─── Idle sub-behaviors ───────────────────────────────────────────────────
    def _update_idle_sub_behavior(self, dt: float):
        """
        Panda does things without being asked.
        Sub-states layered on top of the main idle state (don't switch main state).
        """
        if self.animation_state not in ('idle', 'working'):
            self._idle_sub_t = 0.0
            self._idle_sub_state = ''
            self._idle_sub_next = random.uniform(8.0, 20.0)
            return

        # Tick down to next sub-behavior
        self._idle_sub_next -= dt
        if self._idle_sub_next <= 0.0 and not self._idle_sub_state:
            choices = [
                ('grooming',   0.20),
                ('stretching', 0.15),
                ('scratching', 0.18),
                ('daydream',   0.15),
                ('sniffing',   0.12),
                ('yawning',    0.10),
                ('flopping',   0.10),
            ]
            total = sum(w for _, w in choices)
            r = random.uniform(0, total)
            c = 0.0
            for name, w in choices:
                c += w
                if r <= c:
                    self._idle_sub_state = name
                    self._idle_sub_t = 0.0
                    self._play_sound(self._IDLE_SUB_SOUNDS.get(name, 'purr'))
                    break
            self._idle_sub_next = random.uniform(8.0, 20.0)

        if self._idle_sub_state:
            self._idle_sub_t += dt
            dur = {
                'grooming':   3.5, 'stretching': 2.5, 'scratching': 2.0,
                'daydream':   5.0, 'sniffing':   1.8, 'yawning':    2.0,
                'flopping':   4.0,
            }.get(self._idle_sub_state, 3.0)
            if self._idle_sub_t >= dur:
                # Reset jaw when yawning finishes
                if self._idle_sub_state == 'yawning':
                    self._jaw_open = 0.0
                self._idle_sub_state = ''
                self._idle_sub_t = 0.0

    def _get_idle_sub_pose(self) -> dict:
        """
        Return additional joint offsets for the current idle sub-behavior.
        Keys: 'head_z', 'head_x', 'arm_l', 'arm_r', 'body_y_scale', 'body_x'.
        All values are in degrees (for rotations) or scale factors.
        """
        s = self._idle_sub_state
        t = self._idle_sub_t
        if not s:
            return {}

        if s == 'grooming':
            # Panda licks its paw then rubs over the ear / top of head.
            # Full 3.5 s cycle: lift → rub (rapid oscillation) → lower.
            phase = t / 3.5
            swing  = math.sin(math.pi * phase)        # 0→1→0 envelope
            rub_osc = math.sin(t * 14.0) * 10.0 * (1.0 - abs(2.0 * phase - 1.0))
            arm_r  = -85.0 * swing + rub_osc          # right paw to head level
            # Head turns toward the grooming paw and tilts slightly
            head_z = -20.0 * swing                    # tilt toward right
            head_x = -8.0 * swing                     # slight look-down
            # Brief squint on grooming side (right eye)
            self._micro_emotion['content'] = min(1.0, self._micro_emotion.get('content', 0.0) + _GROOMING_CONTENT_INCREMENT)
            return {'arm_r': arm_r, 'head_z': head_z, 'head_x': head_x}

        elif s == 'stretching':
            # Both arms extend forward, body elongates
            phase = min(1.0, t / 1.2)
            both = -120.0 * self._ease_in_out_cubic(phase) if phase < 1.0 \
                   else -120.0 * self._ease_out_cubic(2.0 - t / 1.25)
            return {'arm_l': both, 'arm_r': both, 'body_y_scale': 1.0 + 0.08 * math.sin(math.pi * min(1.0, t / 2.5))}

        elif s == 'scratching':
            # Left paw to side of head, rapid oscillation
            osc = math.sin(t * 18.0) * 20.0
            arm_l = -70.0 + osc
            head_z = 12.0 + math.sin(t * 8.0) * 5.0
            return {'arm_l': arm_l, 'head_z': head_z}

        elif s == 'daydream':
            # Head tilts up-left, slow sway, eyes soften (handled in _draw_panda_eyes via micro_emotion)
            self._micro_emotion['curious'] = min(1.0, self._micro_emotion['curious'] + 0.02)
            head_z = -18.0 * math.sin(t * 0.4)
            head_x = 10.0 + math.sin(t * 0.3) * 5.0
            return {'head_z': head_z, 'head_x': head_x}

        elif s == 'sniffing':
            # Head bobs up/down rapidly + small side twitch (nose-twitch effect)
            head_x  = math.sin(t * 12.0) * 8.0
            head_z  = math.sin(t * 7.3)  * 4.0   # slight side sway
            return {'head_x': head_x, 'head_z': head_z}

        elif s == 'yawning':
            # Arms stretch out, jaw opens wide, then closes
            phase = min(1.0, t / 2.0)  # 2s total cycle
            jaw_phase = math.sin(math.pi * phase)          # 0→1→0 over cycle
            self._jaw_open = jaw_phase * 0.92              # actually open jaw
            arm_both = -95.0 * jaw_phase
            scale = 1.0 + 0.05 * jaw_phase
            return {'arm_l': arm_both, 'arm_r': arm_both, 'body_y_scale': scale}

        elif s == 'flopping':
            # Fall sideways, roll, recover
            phase = t / 4.0
            if phase < 0.3:
                body_x = 45.0 * self._ease_in_cubic(phase / 0.3)
            elif phase < 0.7:
                body_x = 45.0 + math.sin((phase - 0.3) * math.pi * 3) * 15.0
            else:
                body_x = 45.0 * (1.0 - self._ease_out_cubic((phase - 0.7) / 0.3))
            return {'body_x': body_x}

        return {}

    # ─── Public UI interaction methods ────────────────────────────────────────
    def notify_file_dragged(self, file_path: str):
        """Called when user drags a file near the panda — triggers sniff."""
        self._last_drag_file = file_path
        self._idle_sub_state = 'sniffing'
        self._idle_sub_t = 0.0
        self._micro_emotion['curious'] = 0.8

    def notify_button_nearby(self):
        """Called when cursor is near a UI button — panda peeks/pokes."""
        if self._ui_interact_t <= 0.0:
            self._ui_interact_type = 'poke'
            self._ui_interact_t = 1.2
            self._arm_over_vel[0] += random.choice([-1, 1]) * 18.0

    def start_bite_tab(self):
        """
        Trigger the bite-tab animation: panda leans forward, jaw drops open,
        chomps sound plays at peak, jaw closes. Call this when the panda
        is positioned near a tab widget.
        """
        self._ui_interact_type  = 'bite'
        self._ui_interact_t     = self._bite_duration
        self._bite_chomp_played = False
        # Head leans forward via body pitch spring kick
        self._body_pitch_vel += 20.0
        # Surprised wide-eyes (chomping is exciting)
        self._surprised_eye_t = 0.35
        # Micro-emotion: playful + excited
        self._micro_emotion['playful']  = 0.9
        self._micro_emotion['curious']  = 0.6

    def start_hug_window(self):
        """Panda climbs/hugs the window edge — triggers climbing_wall state."""
        self.transition_to_state('climbing_wall')
        self._micro_emotion['playful'] = 0.8
        # Schedule return to idle after 3–5 seconds
        fire_t = time.time() + random.uniform(3.0, 5.0)
        self._reaction_delay_q.append((fire_t, lambda: self.transition_to_state('falling_back')))

    def start_sit_on_panel(self):
        """Panda sits down on a panel — triggers sitting_back state."""
        self.transition_to_state('sitting_back')
        self._micro_emotion['content'] = 0.9

    def set_micro_emotion(self, emotion_name: str, weight: float = 0.8):
        """Blend in a micro-emotion (curious, playful, annoyed, content, nervous, happy, …).

        Unknown emotion names are registered on first use so callers never silently fail.
        """
        clamped = max(0.0, min(1.0, weight))
        # Allow any emotion name — registers at 0.0 if unseen before
        if emotion_name not in self._micro_emotion:
            self._micro_emotion[emotion_name] = 0.0
        self._micro_emotion[emotion_name] = clamped

    def apply_squash_effect(self, scale: float = 0.85):
        """Temporarily squash/stretch the panda body (1.0 = normal, <1 = squash).

        Called by PandaInteractionBehavior after click animations.  The value
        is blended into the existing squash spring rather than overwriting it
        so normal physics resume immediately.
        """
        self._squash_y = max(0.6, min(1.2, scale))


    # 2D overlay fonts — created once as class constants to avoid per-frame allocations.
    # QFont() returns a default placeholder when PyQt6 is absent; QPainter.setFont()
    # is only called inside the try block in _draw_2d_overlay, so it's safe.
    try:
        _OVERLAY_FONT_ZZZ   = QFont('Arial', 16, QFont.Weight.Bold)
        _OVERLAY_FONT_EMOJI = QFont('Arial', 14)
    except Exception:
        _OVERLAY_FONT_ZZZ   = None   # type: ignore[assignment]
        _OVERLAY_FONT_EMOJI = None   # type: ignore[assignment]

    # Map logical sound names → actual WAV filenames in resources/sounds/.
    # This allows call-sites to use short, descriptive names without caring
    # about the exact filename on disk.
    _SOUND_ALIASES: dict = {
        'boop':           'panda_boop',
        'thump':          'panda_thud',
        'landing':        'panda_thud',
        'click':          'click',
        'yawn':           'panda_sleepy_yawn',
        'big_yawn':       'panda_big_yawn',
        'tired_yawn':     'panda_tired_yawn',
        'wake_yawn':      'panda_wake_yawn',
        'giggle':         'panda_giggle',
        'chomp':          'panda_chomp',
        'plop':           'panda_plop',
        'poke':           'panda_poke',
        'purr':           'panda_purr',
        'snore':          'panda_snore',
        'stretch':        'panda_stretch',
        'scratch':        'panda_scratch',
        'sniff':          'panda_sniff',
        'flop':           'panda_flop',
        'wag':            'panda_wag',
        'greet':          'panda_chirp',
        'excited':        'panda_excited',
        'munch':          'panda_munch',
        'nom':            'panda_nom',
        'crunch':         'panda_crunch',
        'slurp':          'panda_slurp',
        'squeak':         'panda_squeak',
        'sigh':           'panda_sigh',
        'content':        'panda_content',
        'hop':            'panda_hop',
        'leap':           'panda_leap',
        'bounce':         'panda_bounce',
        'achievement':    'achievement',
        'error':          'error',
        'notification':   'notification',
        'start':          'start',
        'complete':       'complete',
        'milestone':      'milestone',
        'warning':        'warning',
    }

    # Sound played when each idle sub-behavior starts
    _IDLE_SUB_SOUNDS: dict = {
        'grooming':   'purr',
        'stretching': 'stretch',
        'scratching': 'scratch',
        'daydream':   'sigh',
        'sniffing':   'sniff',
        'yawning':    'yawn',
        'flopping':   'flop',
    }

    def _play_sound(self, name: str):
        """
        Play a named sound effect.

        Looks up the logical name in _SOUND_ALIASES to get the actual WAV filename,
        then searches (in order):
          1. resources/sounds/<file>.wav via config.get_resource_path() — works in dev
             mode AND in the frozen EXE (PyInstaller bundles resources/sounds/).
          2. app_data/sounds/<file>.wav — user-installed custom sounds.
        Falls back to QApplication.beep() for 'boop'.  Fails silently on any error.
        """
        if not self._audio_available:
            if name == 'boop':
                try:
                    QApplication.beep()
                except Exception:
                    pass
            return
        try:
            if name not in self._audio_sfx:
                from PyQt6.QtMultimedia import QSoundEffect
                from PyQt6.QtCore import QUrl
                # Resolve alias → actual filename (fall back to name itself)
                file_stem = self._SOUND_ALIASES.get(name, name)
                wav_name = f'{file_stem}.wav'
                wav_path = None
                # 1. Bundled resources (dev tree AND frozen EXE via _MEIPASS)
                try:
                    from config import get_resource_path
                except (ImportError, OSError, RuntimeError):
                    try:
                        from src.config import get_resource_path
                    except (ImportError, OSError, RuntimeError):
                        get_resource_path = None
                if get_resource_path is not None:
                    candidate = get_resource_path('sounds', wav_name)
                    if candidate.exists():
                        wav_path = str(candidate)
                # 2. app_data/sounds/ next to EXE (user-installed custom sounds)
                if wav_path is None:
                    import os
                    for base in (
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app_data', 'sounds'),
                        os.path.join(os.getcwd(), 'app_data', 'sounds'),
                    ):
                        candidate_path = os.path.normpath(os.path.join(base, wav_name))
                        if os.path.isfile(candidate_path):
                            wav_path = candidate_path
                            break
                if wav_path is not None:
                    sfx = QSoundEffect(self)
                    from PyQt6.QtCore import QUrl
                    sfx.setSource(QUrl.fromLocalFile(wav_path))
                    sfx.setVolume(0.55)
                    self._audio_sfx[name] = sfx
                else:
                    self._audio_sfx[name] = None   # not found — mark as absent
            sfx = self._audio_sfx.get(name)
            if sfx is not None:
                sfx.play()
            elif name == 'boop':
                QApplication.beep()
        except Exception:
            pass

    def _set_state_direct(self, state: str):
        """Set animation state with blend transition (bypasses anticipation, used internally)."""
        prev = self.animation_state
        self._prev_state    = prev
        self._blend_alpha   = 0.0
        self._blend_start_t = time.time()
        self.animation_state = state
        self.animation_changed.emit(state)
        # Play entry sound for special states
        if state == 'sleeping' and prev != 'sleeping':
            self._play_sound('snore')
        elif state == 'rolling' and prev != 'rolling':
            self._play_sound('bounce')
        elif state in ('celebrating', 'waving') and prev not in ('celebrating', 'waving'):
            self._play_sound('wag')
            # Kick the tail spring for big wag on happy state entry
            self._tail_vel += 45.0
        elif state == 'wall_hit' and prev != 'wall_hit':
            self._play_sound('thump')
            self._surprised_eye_t = 0.4   # wide surprised eyes on impact
        elif state == 'sitting_back' and prev not in ('sitting_back', 'sleeping'):
            self._play_sound('plop')
        elif state == 'falling_back' and prev != 'falling_back':
            self._play_sound('landing')
        elif state in ('dance', 'spin', 'backflip', 'juggle') and prev not in (
                'dance', 'spin', 'backflip', 'juggle'):
            self._play_sound('wag')
            self._surprised_eye_t = 0.2

    # ─── Smooth animation helpers ────────────────────────────────────────────
    def _get_body_bob(self):
        """Return vertical body-bob offset using smooth sinusoidal curves with personality."""
        t     = self.animation_frame
        state = self.animation_state if self._anticipation_t <= 0.0 else self._anticipation_state
        spd   = self._micro['sway_speed']
        amp   = self._micro['breath_amp']
        tired = self._fatigue
        excited = self._emotion_weights.get('excited', 0.0)

        if state == 'idle' or state == 'neutral':
            # Layered breathing + emotional variation
            base = (0.016 * math.sin(t * 0.040 * spd) +
                    0.004 * math.sin(t * 0.110 * spd)) * amp
            # Tired: slower, shallower; Excited: bigger, bouncier
            base *= (1.0 - tired * 0.50) * (1.0 + excited * 0.40)
            return base

        if state in ('walking', 'walking_left', 'walking_right'):
            return 0.038 * abs(math.sin(t * 0.160)) - 0.010

        if state == 'running':
            return 0.055 * abs(math.sin(t * 0.280)) - 0.012

        if state == 'jumping':
            phase = (t % 70) / 70.0
            return 0.35 * math.sin(phase * math.pi)

        if state in ('celebrating', 'excited'):
            return 0.06 * abs(math.sin(t * 0.22)) * (1.0 + excited * 0.30)

        if state == 'waving':
            return 0.010 * math.sin(t * 0.060)

        if state == 'sleeping':
            # Slow, deep breathing when sleeping
            return 0.022 * math.sin(t * 0.020)

        if state == '_anticipation':
            # Slight crouch-back before a big action
            return -0.04 * math.sin(t * 0.12)

        return 0.0

    def _get_limb_positions(self):
        """
        Return per-limb rotation angles (degrees) using smooth sinusoidal curves.
        Blends between previous state and current state for smooth transitions.
        """
        frame = self.animation_frame

        def _positions_for_state(state: str) -> dict:
            pos = {
                'left_arm_angle':  0.0,
                'right_arm_angle': 0.0,
                'left_leg_angle':  0.0,
                'right_leg_angle': 0.0,
            }
            # Working animation overrides
            if self.is_working:
                pos.update(self._get_working_limb_offsets())
                return pos

            if state in ('walking', 'walking_left', 'walking_right'):
                # Quadruped diagonal gait: front-left/rear-right move together.
                # Base angle 25° pitches limbs forward/back from the body; swing
                # amplitude 32° provides natural reach; harmonic 5° adds realism.
                # Reduced base from 35° to 25° so legs hang more naturally with
                # the gentler -20° body pitch.
                base  = frame * 0.160
                swing = 32.0 * math.sin(base) + 5.0 * math.sin(base * 3) / 3.0
                pos['left_arm_angle']  =  25.0 + swing    # front legs pitched forward
                pos['right_arm_angle'] =  25.0 - swing
                pos['left_leg_angle']  = -25.0 - swing    # rear legs pitched backward
                pos['right_leg_angle'] = -25.0 + swing

            elif state == 'running':
                base  = frame * 0.280
                swing = 55.0 * math.sin(base) + 9.0 * math.sin(base * 3) / 3.0
                pos['left_arm_angle']  =  swing
                pos['right_arm_angle'] = -swing
                pos['left_leg_angle']  = -swing
                pos['right_leg_angle'] =  swing

            elif state == 'jumping':
                phase  = (frame % 70) / 70.0
                extend = 40.0 * math.sin(phase * math.pi)
                pos['left_arm_angle']  = -extend * 0.9
                pos['right_arm_angle'] = -extend * 0.9
                pos['left_leg_angle']  =  extend * 0.6
                pos['right_leg_angle'] =  extend * 0.6

            elif state == 'waving':
                wave = -95.0 + 28.0 * math.sin(frame * 0.28)
                pos['right_arm_angle'] = wave
                pos['left_arm_angle']  = 5.0 * math.sin(frame * 0.060)

            elif state in ('celebrating', 'excited'):
                pos['left_arm_angle']  = -115.0 + 22.0 * math.sin(frame * 0.22)
                pos['right_arm_angle'] = -115.0 + 22.0 * math.sin(frame * 0.22 + 0.4)
                pos['left_leg_angle']  =  18.0 * math.sin(frame * 0.22)
                pos['right_leg_angle'] = -18.0 * math.sin(frame * 0.22)

            elif state == 'sleeping':
                # Arms droop down, slight lean forward
                droop = 20.0 + self._fatigue * 15.0
                pos['left_arm_angle']  =  droop
                pos['right_arm_angle'] =  droop

            elif state == 'crawling':
                # All-fours: diagonal pair gait (left-front / right-back together)
                base  = frame * 0.130
                swing = 28.0 * math.sin(base) + 4.0 * math.sin(base * 3) / 3.0
                # Arms swing opposite to legs (front-left with rear-right)
                pos['left_arm_angle']  =  45.0 + swing        # shoulder pitched forward
                pos['right_arm_angle'] =  45.0 - swing
                pos['left_leg_angle']  = -45.0 - swing        # hip pitched forward
                pos['right_leg_angle'] = -45.0 + swing

            elif state == 'climbing_wall':
                # Vertical body: arms reach up alternately, legs push against wall
                base  = frame * 0.100
                reach = 30.0 * math.sin(base)
                pos['left_arm_angle']  = -120.0 + reach
                pos['right_arm_angle'] = -120.0 - reach
                pos['left_leg_angle']  =  -60.0 - reach
                pos['right_leg_angle'] =  -60.0 + reach

            elif state == 'falling_back':
                # On back: legs kick up, arms flail outward
                phase = (frame % 50) / 50.0
                flail = 25.0 * math.sin(phase * math.pi * 2)
                kick  = 60.0 + 15.0 * math.sin(phase * math.pi)
                pos['left_arm_angle']  = -90.0 + flail
                pos['right_arm_angle'] = -90.0 - flail
                pos['left_leg_angle']  =  kick
                pos['right_leg_angle'] =  kick

            elif state == '_anticipation':
                # Pull arms back and crouch before jump/celebrate
                pos['left_arm_angle']  = 25.0
                pos['right_arm_angle'] = 25.0
                pos['left_leg_angle']  = 12.0
                pos['right_leg_angle'] = 12.0

            elif state == 'sitting_back':
                # Relaxed sitting: legs splayed forward, arms resting on belly
                pos['left_arm_angle']  = -20.0
                pos['right_arm_angle'] = -20.0
                pos['left_leg_angle']  =  45.0
                pos['right_leg_angle'] =  45.0

            elif state == 'rolling':
                # Rolling on back: all limbs flailing loosely
                swing = 40.0 * math.sin(frame * 0.18)
                pos['left_arm_angle']  =  swing + 15.0
                pos['right_arm_angle'] = -swing + 15.0
                pos['left_leg_angle']  = -swing + 20.0
                pos['right_leg_angle'] =  swing + 20.0

            elif state == 'hanging_ceiling':
                # Inverted grip: all limbs reaching upward (which is now downward)
                base = frame * 0.08
                sway = 12.0 * math.sin(base)
                pos['left_arm_angle']  = -140.0 + sway
                pos['right_arm_angle'] = -140.0 - sway
                pos['left_leg_angle']  = -130.0 + sway * 0.7
                pos['right_leg_angle'] = -130.0 - sway * 0.7

            elif state == 'hanging_window_edge':
                # Arms reaching up to grip edge, body dangling
                base = frame * 0.07
                grip_sway = 8.0 * math.sin(base)
                pos['left_arm_angle']  = -160.0 + grip_sway
                pos['right_arm_angle'] = -160.0 - grip_sway
                pos['left_leg_angle']  =  25.0 + 15.0 * math.sin(base * 0.6)
                pos['right_leg_angle'] =  25.0 - 15.0 * math.sin(base * 0.6 + 0.4)

            elif state == 'wall_hit':
                # Frustrated/angry slam: arms raised at sides, legs braced
                phase = math.sin(frame * 0.25)   # fast angry tremor
                pos['left_arm_angle']  = -70.0 + phase * 8.0
                pos['right_arm_angle'] = -70.0 - phase * 8.0
                pos['left_leg_angle']  =  15.0
                pos['right_leg_angle'] =  15.0

            elif state == 'dance':
                # Full-body dance: alternating arm pumps + leg kicks in 4-beat rhythm
                beat = math.sin(frame * 0.18)           # ~0.9 Hz at 30fps
                beat2 = math.sin(frame * 0.18 + math.pi)
                pos['left_arm_angle']  = -110.0 + beat  * 40.0   # pump up/down
                pos['right_arm_angle'] = -110.0 + beat2 * 40.0   # opposite phase
                pos['left_leg_angle']  =  30.0  * abs(math.sin(frame * 0.18))
                pos['right_leg_angle'] = -30.0  * abs(math.sin(frame * 0.18 + math.pi * 0.5))

            elif state == 'backflip':
                # Tuck arms in, both legs swing over (continuous rotation via body pitch)
                t_norm = (frame % 40) / 40.0   # 40-frame cycle
                pos['left_arm_angle']  = -30.0 + math.sin(t_norm * math.pi * 2) * 20.0
                pos['right_arm_angle'] = -30.0 - math.sin(t_norm * math.pi * 2) * 20.0
                pos['left_leg_angle']  = -60.0 + math.sin(t_norm * math.pi * 2) * 60.0
                pos['right_leg_angle'] = -60.0 + math.sin(t_norm * math.pi * 2) * 60.0

            elif state == 'spin':
                # Arms wide, legs stable — continuous spin via body_yaw (applied in draw)
                pos['left_arm_angle']  = -90.0
                pos['right_arm_angle'] = -90.0
                pos['left_leg_angle']  = 10.0
                pos['right_leg_angle'] = 10.0

            elif state == 'juggle':
                # Alternating arm arcs as if tossing items
                arc = math.sin(frame * 0.22)
                pos['left_arm_angle']  = -80.0 + arc  * 55.0
                pos['right_arm_angle'] = -80.0 - arc  * 55.0
                pos['left_leg_angle']  =  5.0
                pos['right_leg_angle'] =  5.0

            else:  # idle / neutral / default
                sway = 3.5 * math.sin(frame * 0.040 * self._micro['sway_speed'])
                pos['left_arm_angle']  =  sway
                pos['right_arm_angle'] = -sway

            return pos

        cur  = _positions_for_state(self.animation_state)
        if self._blend_alpha >= 1.0:
            return cur

        prev = _positions_for_state(self._prev_state)
        alpha = self._ease_in_out_cubic(self._blend_alpha)
        blended = {}
        for k in cur:
            blended[k] = prev[k] * (1.0 - alpha) + cur[k] * alpha
        return blended
    
    def _update_animation(self):
        """Update animation frame and physics."""
        self.animation_frame += 1
        if self.animation_frame > 10000:
            self.animation_frame = 0
        
        # Calculate delta time
        now = time.time()
        dt = min(now - self.last_frame_time, 0.10)   # cap at 100 ms to avoid spiral
        self.last_frame_time = now

        # Update all secondary animation subsystems
        self._update_subsystems(now, dt)

        # Update physics
        self._update_physics(dt)
        
        # Update trail particles
        self._update_trail()
        
        # Update autonomous behavior (walking around)
        self._update_autonomous_behavior(dt)
        
        # Update working animation
        self._update_working_animation(dt)

        # Update click mask so only the panda region captures mouse events;
        # everything outside the mask passes through to the UI widgets below.
        if self._overlay_mode:
            self._update_click_mask()
        
        # Request redraw
        self.update()
    
    def _update_physics(self, dt: float = None):
        """Update physics simulation. Uses actual dt for synchronized motion."""
        if dt is None:
            dt = self.FRAME_TIME   # fallback for direct calls

        # Apply gravity if not on ground
        if self.panda_y > -1.0:
            self.velocity_y -= self.GRAVITY * dt

        # Track pre-collision velocity for landing detection
        vy_before = self.velocity_y

        # Apply velocities
        self.panda_x += self.velocity_x * dt
        self.panda_y += self.velocity_y * dt
        self.panda_z += self.velocity_z * dt
        self.rotation_y += self.angular_velocity * dt

        # Ground collision — detect landing impact
        if self.panda_y < -0.7:
            self.panda_y = -0.7
            if vy_before < -0.8:
                # Landing impact: squash + belly jiggle + flinch blink + thump sound
                impact = min(abs(vy_before) * 0.12, 0.28)
                self._squash_y   = max(0.72, 1.0 - impact)
                self._squash_vel = 0.0
                self._belly_vel += abs(vy_before) * 0.18   # kick belly jiggle upward
                self._flinch_t   = 0.15
                self._play_sound('thump')
            self.velocity_y *= -self.BOUNCE_DAMPING
            if abs(self.velocity_y) < 0.01:
                self.velocity_y = 0

        # Detect fast drag → "whoa face"
        if self.is_dragging:
            drag_vx = self.velocity_x
            if abs(drag_vx - self._drag_vx_prev) > 0.4:
                self._whoa_t            = 0.5
                self._surprised_eye_t   = 0.3
            self._drag_vx_prev = drag_vx

        # Wall (world-boundary) collision — flinch + blink on hit
        if self.panda_x > self.WORLD_HALF_X:
            self.panda_x = self.WORLD_HALF_X
            if self.velocity_x > 0.05:
                self.velocity_x *= -self.BOUNCE_DAMPING
                self._flinch_t        = 0.25
                self._surprised_eye_t = 0.25
                self._play_sound('thump')
        elif self.panda_x < -self.WORLD_HALF_X:
            self.panda_x = -self.WORLD_HALF_X
            if self.velocity_x < -0.05:
                self.velocity_x *= -self.BOUNCE_DAMPING
                self._flinch_t        = 0.25
                self._surprised_eye_t = 0.25
                self._play_sound('thump')
        if self.panda_z > self.WORLD_HALF_Z:
            self.panda_z = self.WORLD_HALF_Z
            if self.velocity_z > 0.05:
                self.velocity_z *= -self.BOUNCE_DAMPING
                self._flinch_t        = 0.20
                self._surprised_eye_t = 0.20
        elif self.panda_z < -self.WORLD_HALF_Z:
            self.panda_z = -self.WORLD_HALF_Z
            if self.velocity_z < -0.05:
                self.velocity_z *= -self.BOUNCE_DAMPING
                self._flinch_t        = 0.20
                self._surprised_eye_t = 0.20

        # Apply friction
        self.velocity_x *= self.FRICTION
        self.velocity_z *= self.FRICTION
        self.angular_velocity *= self.FRICTION

        # Update items physics
        for item in self.items_3d:
            if 'velocity_y' in item:
                item['y'] += item['velocity_y'] * dt
                item['velocity_y'] -= self.GRAVITY * dt
                if item['y'] < -0.9:
                    item['y'] = -0.9
                    item['velocity_y'] *= -self.BOUNCE_DAMPING

    def _get_panda_screen_center(self):
        """Return the approximate (screen_x, screen_y, screen_radius) of the rendered panda.

        Uses the OpenGL perspective formula to map panda world-position to screen
        coordinates.  The result is a rough hit-test area — not pixel-perfect.
        """
        import math as _math
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return w // 2, h // 2, max(w, h) // 2
        aspect = w / h
        # Half-tangent of 45° vertical FOV
        half_fov_tan = _math.tan(_math.radians(22.5))
        # World frustum height at z=0 (panda z is ~0)
        frustum_h = 2.0 * self.camera_distance * half_fov_tan
        frustum_w = frustum_h * aspect
        # The camera is shifted so it looks at y=0.5
        look_at_y = 0.5
        pan_world_x = self.panda_x
        pan_world_y = self.panda_y - look_at_y
        sx = int(w / 2 + pan_world_x / frustum_w * w)
        sy = int(h / 2 - pan_world_y / frustum_h * h)
        # Screen radius that encloses the full panda (head + body ~1.4 world units tall)
        panda_world_radius = max(self.HEAD_RADIUS, self.BODY_HEIGHT) * 1.8
        radius = int(panda_world_radius / frustum_h * h) + 30  # +30px margin
        return sx, sy, radius

    def _update_click_mask(self):
        """Set the widget mask to the panda's bounding ellipse.

        Using setMask() means Qt only routes mouse/keyboard events to this
        widget for pixels INSIDE the mask.  Clicks outside the ellipse are
        automatically delivered to whatever widget lies underneath — this is
        the correct Qt-native way to achieve per-pixel click-through for a
        full-window transparent overlay.  event.ignore() alone is insufficient
        because ignored child-widget events propagate to the parent, not to
        sibling widgets at the same screen position.
        """
        try:
            from PyQt6.QtGui import QRegion
            sx, sy, radius = self._get_panda_screen_center()
            # Ellipse slightly taller than wide (panda is taller than wide)
            rx = int(radius * 0.85)
            ry = radius
            region = QRegion(sx - rx, sy - ry, rx * 2, ry * 2, QRegion.RegionType.Ellipse)
            self.setMask(region)
        except (ImportError, AttributeError, ValueError):
            pass  # non-critical; worst case is full-window hit area

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press — play boop, reset boredom, surprised face.

        When used as a full-window transparent overlay, pass events through to
        the UI layer below if the click is outside the panda's hit area.
        """
        # --- Hit test: only consume events near the panda ---
        try:
            sx, sy, radius = self._get_panda_screen_center()
            dx = event.pos().x() - sx
            dy = event.pos().y() - sy
            if dx * dx + dy * dy > radius * radius:
                event.ignore()
                return
        except Exception:
            pass  # fall through if hit-test fails

        self.last_mouse_pos = event.pos()
        self.drag_start_pos = event.pos()
        self.is_dragging = False
        self._boredom_t = 0.0

        if event.button() == Qt.MouseButton.LeftButton:
            # Quick surprised blink + boop sound
            self._surprised_eye_t = 0.25
            self._play_sound('boop')
            # Kick an arm overshoot (right arm reacts to click)
            self._arm_over_vel[1] += random.uniform(6.0, 12.0)
            self.clicked.emit()


    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse drag and track cursor for panda awareness."""
        # Track cursor position for look-at-cursor system (always)
        self._cursor_wpos = event.pos()

        # If not currently dragging, only track cursor; pass event through to UI.
        # This prevents the overlay from consuming mouse-move events over buttons/sliders.
        if not self.is_dragging and not (event.buttons() & Qt.MouseButton.LeftButton):
            event.ignore()
            # Still update boredom reset and look-at, but don't consume the event
            self._boredom_t = 0.0
            if self._emotion == 'bored':
                self._emotion = 'neutral'
                self._emotion_weights['bored']   = 0.0
                self._emotion_weights['neutral'] = 1.0
            return

        # Reset boredom when user moves cursor near panda
        self._boredom_t = 0.0
        if self._emotion == 'bored':
            self._emotion = 'neutral'
            self._emotion_weights['bored']   = 0.0
            self._emotion_weights['neutral'] = 1.0

        if self.last_mouse_pos is None:
            return

        delta = event.pos() - self.last_mouse_pos
        
        # Check if dragging
        if self.drag_start_pos:
            total_delta = event.pos() - self.drag_start_pos
            if total_delta.manhattanLength() > 5:
                self.is_dragging = True
        
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.is_dragging:
                # Drag panda — scale factor keeps drag proportional to camera distance.
                # Divide by 600 (was 300) for a less twitchy drag feel.
                drag_scale = self.camera_distance / 600.0
                self.panda_x += delta.x() * drag_scale
                self.panda_y -= delta.y() * drag_scale
            else:
                # Rotate camera
                self.camera_angle_y += delta.x() * 0.5
                self.camera_angle_x += delta.y() * 0.5
                self.camera_angle_x = max(-89, min(89, self.camera_angle_x))
        
        self.last_mouse_pos = event.pos()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        self.last_mouse_pos = None
        self.drag_start_pos = None
        self.is_dragging = False

    def dragEnterEvent(self, event) -> None:
        """Accept food/toy drops dragged from the inventory panel."""
        try:
            if event.mimeData().hasText():
                text = event.mimeData().text()
                if text.startswith('panda_item:'):
                    event.acceptProposedAction()
                    return
        except Exception:
            pass
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Keep accepting the drag so the cursor stays as a copy icon."""
        try:
            if event.mimeData().hasText() and event.mimeData().text().startswith('panda_item:'):
                event.acceptProposedAction()
                return
        except Exception:
            pass
        event.ignore()

    def dropEvent(self, event) -> None:
        """Item dropped on panda — play eat/play animation, trigger sniff→react."""
        try:
            text = event.mimeData().text()
            if not text.startswith('panda_item:'):
                event.ignore()
                return
            parts = text.split(':', 2)
            item_id = parts[1] if len(parts) > 1 else 'item'
            category = parts[2] if len(parts) > 2 else ''
            event.acceptProposedAction()

            # Sniff the incoming item, then react with eating/playing animation
            self.notify_file_dragged(item_id)
            is_food = 'food' in category.lower()
            def _react_to_item():
                if is_food:
                    self._jaw_open = 0.8
                    self._surprised_eye_t = 0.4
                    self._micro_emotion['happy'] = min(1.0, self._micro_emotion.get('happy', 0) + 0.6)
                    self._play_sound('boop')
                    QTimer.singleShot(900, lambda: setattr(self, '_jaw_open', 0.0))
                else:
                    # Toy — playful reaction
                    self.set_animation_state('waving')
                    self._surprised_eye_t = 0.35
                    self._micro_emotion['playful'] = min(1.0, self._micro_emotion.get('playful', 0) + 0.7)
                    QTimer.singleShot(1500, lambda: self.set_animation_state('idle')
                                      if self.animation_state == 'waving' else None)
            QTimer.singleShot(500, _react_to_item)
        except Exception as _e:
            logger.debug(f"Panda dropEvent error: {_e}")
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        self.camera_distance -= delta * 0.001
        self.camera_distance = max(2.0, min(12.0, self.camera_distance))
        self.update()
    
    def set_animation_state(self, state: str):
        """Set animation state using Qt State Machine."""
        # Use the state machine for state transitions
        self.transition_to_state(state)
    
    def add_item_3d(self, item_type: str, x: float, y: float, z: float, **kwargs):
        """Add a 3D item to the scene."""
        item = {
            'type': item_type,
            'x': x,
            'y': y,
            'z': z,
            'velocity_y': 0.0,
            'rotation': 0.0,
            **kwargs
        }
        self.items_3d.append(item)
    
    def clear_items(self):
        """Remove all items from the scene."""
        self.items_3d.clear()
    
    # ========================================================================
    # Clothing System (3D)
    # ========================================================================
    
    def equip_clothing(self, slot: str, clothing_item):
        """Equip clothing item in 3D.

        Args:
            slot: 'hat', 'shirt', 'pants', 'glasses', 'accessory',
                  'held_right', 'held_left', 'gloves',
                  'armor', 'boots', 'belt', 'backpack'
            clothing_item: Clothing data dict (name, color, type)
        """
        if slot in self.clothing:
            self.clothing[slot] = clothing_item
            logger.info(f"Equipped {clothing_item} in slot {slot}")
    
    def unequip_clothing(self, slot: str):
        """Remove clothing from slot."""
        if slot in self.clothing:
            self.clothing[slot] = None
    
    def _draw_clothing(self):
        """Draw body-relative clothing (shirt, pants, glasses, accessory).
        NOTE: Hat is drawn inside the head matrix in _draw_panda() so it follows head bob/tilt.
              Held items are drawn at paw positions via _draw_held_items().
        """
        # Draw shirt (body-relative)
        if self.clothing['shirt']:
            self._draw_shirt(self.clothing['shirt'])

        # Draw pants (body-relative — drawn over leg positions)
        if self.clothing['pants']:
            self._draw_pants(self.clothing['pants'])

        # Draw glasses (body-relative — positioned at head-ish height)
        if self.clothing['glasses']:
            self._draw_glasses(self.clothing['glasses'])

        # Draw accessory
        if self.clothing['accessory']:
            self._draw_accessory(self.clothing['accessory'])

        # Draw gloves (on both paws)
        if self.clothing['gloves']:
            self._draw_gloves(self.clothing['gloves'])

        # Draw armor / cape / robe (chest-relative)
        if self.clothing['armor']:
            self._draw_armor(self.clothing['armor'])

        # Draw boots (at foot positions)
        if self.clothing['boots']:
            self._draw_boots(self.clothing['boots'])

        # Draw belt
        if self.clothing['belt']:
            self._draw_belt(self.clothing['belt'])

        # Draw backpack (rear body-relative)
        if self.clothing['backpack']:
            self._draw_backpack(self.clothing['backpack'])
    
    def _draw_hat(self, hat_data):
        """Draw hat on panda's head. MUST be called inside the head pushMatrix."""
        glPushMatrix()
        # Offset from head centre to top — slightly forward of centre
        glTranslatef(0.0, self.HEAD_RADIUS * 1.05, -self.HEAD_RADIUS * 0.05)

        hat_type = hat_data.get('type', 'classic') if isinstance(hat_data, dict) else 'classic'
        color    = hat_data.get('color', [0.8, 0.2, 0.2]) if isinstance(hat_data, dict) else [0.8, 0.2, 0.2]
        glColor3f(*color)

        quad = gluNewQuadric()
        if hat_type in ('crown', 'tiara'):
            # Crown: short cylinder base + spikes
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            gluCylinder(quad, 0.26, 0.26, 0.08, 16, 1)
            glTranslatef(0.0, 0.0, 0.08)
            for i in range(5):
                a = math.radians(i * 72)
                glPushMatrix()
                glTranslatef(math.cos(a) * 0.20, math.sin(a) * 0.20, 0.0)
                gluCylinder(quad, 0.03, 0.01, 0.12, 8, 1)
                glPopMatrix()
        elif hat_type in ('top_hat', 'tophat'):
            # Brim
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            gluDisk(quad, 0.0, 0.34, 16, 1)
            # Cylinder body
            gluCylinder(quad, 0.22, 0.22, 0.32, 16, 1)
            glTranslatef(0.0, 0.0, 0.32)
            gluDisk(quad, 0.0, 0.22, 16, 1)
        elif hat_type == 'wizard':
            # Tall pointed cone
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            gluCylinder(quad, 0.26, 0.01, 0.55, 16, 1)
        elif hat_type in ('beanie', 'cap'):
            self._draw_sphere(0.24, 12, 12)
            glTranslatef(0.0, 0.20, 0.0)
            glColor3f(*[min(1.0, c + 0.15) for c in color])
            self._draw_sphere(0.08, 8, 8)
        else:
            # Default: rounded cone hat
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            gluCylinder(quad, 0.28, 0.08, 0.30, 16, 1)
        gluDeleteQuadric(quad)
        glPopMatrix()
    
    def _draw_shirt(self, shirt_data):
        """
        Draw shirt on panda's body + sleeve extensions over arms.
        Called from inside the torso world-space matrix so positions are body-relative.
        """
        color   = shirt_data.get('color', [0.2, 0.2, 0.8]) if isinstance(shirt_data, dict) else [0.2, 0.2, 0.8]
        style   = shirt_data.get('type', 'tshirt') if isinstance(shirt_data, dict) else 'tshirt'
        glColor3f(*color)

        # Main torso section — slightly proud of body sphere
        glPushMatrix()
        glScalef(self.BODY_WIDTH * 1.08, self.BODY_HEIGHT * 0.82, self.BODY_WIDTH * 0.88)
        self._draw_sphere(1.0, 20, 20)
        glPopMatrix()

        # Collar / neckline ring
        glPushMatrix()
        glTranslatef(0.0, self.BODY_HEIGHT * 0.78, 0.0)
        quad = gluNewQuadric()
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        darker = [max(0.0, c - 0.12) for c in color]
        glColor3f(*darker)
        gluCylinder(quad, 0.14, 0.16, 0.04, 14, 1)
        gluDeleteQuadric(quad)
        glPopMatrix()

        # Sleeve bands — at shoulder positions (body-relative ≈ ±arm_x offset)
        arm_x = self.BODY_WIDTH * 0.88
        arm_y = self.BODY_HEIGHT * 0.62
        sleeve_len = 0.10 if style in ('tshirt', 'polo') else 0.20  # short vs long sleeve
        for side in (-1.0, 1.0):
            glPushMatrix()
            glTranslatef(side * arm_x, arm_y, 0.0)
            glRotatef(side * -60.0, 0.0, 0.0, 1.0)   # angled downward along arm
            quad2 = gluNewQuadric()
            glRotatef(-90.0, 0.0, 1.0, 0.0)
            gluCylinder(quad2, 0.108, 0.095, sleeve_len, 12, 1)
            # Cuff/hem ring
            glTranslatef(0.0, 0.0, sleeve_len)
            glColor3f(*darker)
            gluDisk(quad2, 0.070, 0.096, 12, 1)
            gluDeleteQuadric(quad2)
            glColor3f(*color)
            glPopMatrix()

        # Shirt hem at bottom
        glPushMatrix()
        glTranslatef(0.0, -self.BODY_HEIGHT * 0.38, 0.0)
        quad3 = gluNewQuadric()
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        glColor3f(*darker)
        gluCylinder(quad3, self.BODY_WIDTH * 0.95, self.BODY_WIDTH * 0.90, 0.03, 16, 1)
        gluDeleteQuadric(quad3)
        glPopMatrix()

    def _draw_pants(self, pants_data):
        """
        Draw pants / trousers following the actual leg positions from _get_limb_positions().
        Called inside the torso world-space matrix.
        """
        color  = pants_data.get('color', [0.2, 0.2, 0.4]) if isinstance(pants_data, dict) else [0.2, 0.2, 0.4]
        style  = pants_data.get('type', 'jeans') if isinstance(pants_data, dict) else 'jeans'
        limb   = self._get_limb_positions()
        glColor3f(*color)

        leg_x     = self.LEG_SPACING * 0.5
        # leg_top_y matches the leg pivot used by _draw_panda_legs: leg_y = -0.24.
        # Expressed as a fraction of BODY_HEIGHT for consistency with the rest of
        # the body-relative coordinate expressions: -0.48 × 0.50 = -0.24.
        leg_top_y = -self.BODY_HEIGHT * 0.48
        quad = gluNewQuadric()

        for side in (-1.0, 1.0):
            swing = limb.get('left_leg_angle' if side < 0 else 'right_leg_angle', 0.0)
            glPushMatrix()
            glTranslatef(side * leg_x, leg_top_y, 0.0)
            glRotatef(swing, 1.0, 0.0, 0.0)    # follows leg swing

            # Upper leg (thigh tube)
            glPushMatrix()
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            gluCylinder(quad, 0.115, 0.098, self.LEG_LENGTH * 0.52, 12, 1)
            glPopMatrix()

            # Knee-area curve
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.50, 0.0)
            glScalef(1.0, 0.6, 1.0)
            glColor3f(*[max(0.0, c - 0.05) for c in color])
            self._draw_sphere(0.10, 10, 10)
            glColor3f(*color)
            glPopMatrix()

            # Lower leg (shin tube)
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.50, 0.0)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            gluCylinder(quad, 0.095, 0.082, self.LEG_LENGTH * 0.45, 12, 1)
            glPopMatrix()

            # Cuff hem at ankle
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.90, 0.0)
            darker = [max(0.0, c - 0.10) for c in color]
            glColor3f(*darker)
            glRotatef(-90.0, 1.0, 0.0, 0.0)
            gluCylinder(quad, 0.086, 0.090, 0.035, 12, 1)
            glColor3f(*color)
            glPopMatrix()

            glPopMatrix()   # end leg

        # Waistband
        glPushMatrix()
        glTranslatef(0.0, leg_top_y + 0.025, 0.0)
        darker = [max(0.0, c - 0.08) for c in color]
        glColor3f(*darker)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        gluCylinder(quad, self.LEG_SPACING * 0.70, self.LEG_SPACING * 0.72, 0.05, 16, 1)
        glPopMatrix()

        gluDeleteQuadric(quad)
    
    def _draw_glasses(self, glasses_data):
        """Draw glasses on panda's face (torso-local space — head centre at Y=0.58)."""
        glPushMatrix()
        # Eye level in torso-local: head_y_local + eye_y_on_head + slight forward
        # = 0.58 + 0.055 ≈ 0.64; Z = HEAD_RADIUS * 0.80
        glTranslatef(0.0, 0.65, self.HEAD_RADIUS * 0.8)

        color = glasses_data.get('color', [0.0, 0.0, 0.0])
        glColor3f(*color)
        quad = gluNewQuadric()

        # Left lens ring — drawn as two concentric disks (frame)
        for side, dx in ((-1, -0.12), (1, 0.12)):
            glPushMatrix()
            glTranslatef(dx, 0.0, 0.0)
            glRotatef(90.0, 0.0, 1.0, 0.0)
            # Outer ring
            gluDisk(quad, 0.060, 0.080, 16, 1)
            # Inner tinted lens
            glColor4f(*color[:3], 0.25)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            gluDisk(quad, 0.0, 0.060, 16, 1)
            glDisable(GL_BLEND)
            glColor3f(*color)
            glPopMatrix()

        # Bridge piece — thin cylinder between lenses
        glPushMatrix()
        glTranslatef(-0.04, 0.0, 0.0)
        glRotatef(90.0, 0.0, 1.0, 0.0)
        gluCylinder(quad, 0.008, 0.008, 0.08, 6, 1)
        glPopMatrix()

        # Temple arms (side pieces)
        for side_x in (-0.12 - 0.08, 0.12 + 0.08):
            glPushMatrix()
            glTranslatef(side_x, 0.0, 0.0)
            glRotatef(90.0 * (1 if side_x < 0 else -1), 0.0, 1.0, 0.0)
            gluCylinder(quad, 0.006, 0.004, 0.18, 6, 1)
            glPopMatrix()

        gluDeleteQuadric(quad)
        glPopMatrix()
    
    def _draw_accessory(self, accessory_data):
        """Draw equipped accessory item on the panda."""
        accessory_type = accessory_data.get('type', 'bow')
        color = accessory_data.get('color', [1.0, 0.5, 0.0])
        glColor3f(*color)

        if accessory_type == 'bow':
            # Bow on top of head: two small spheres side-by-side.
            # Head top in torso-local = 0.58 + HEAD_RADIUS ≈ 1.00; bow just above = 1.05.
            glPushMatrix()
            glTranslatef(0.0, 1.05, 0.0)
            glPushMatrix()
            glTranslatef(-0.08, 0.0, 0.0)
            self._draw_sphere(0.07, 8, 8)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0.08, 0.0, 0.0)
            self._draw_sphere(0.07, 8, 8)
            glPopMatrix()
            glPopMatrix()

        elif accessory_type == 'scarf':
            # Scarf around neck: flat torus-like ring.
            # Neck centre torso-local ≈ BODY_HEIGHT * 0.48 = 0.24; top of neck ≈ 0.32
            glPushMatrix()
            glTranslatef(0.0, 0.32, 0.0)
            glScalef(1.0, 0.3, 1.0)
            self._draw_sphere(0.25, 16, 8)
            glPopMatrix()

        elif accessory_type == 'necklace':
            # Necklace: small spheres in an arc at front of neck.
            # Chest-neck area torso-local ≈ 0.28
            glPushMatrix()
            glTranslatef(0.0, 0.28, 0.22)
            for i in range(7):
                angle = (i - 3) * 15.0
                rad = math.radians(angle)
                glPushMatrix()
                glTranslatef(math.sin(rad) * 0.18, 0.0, 0.0)
                self._draw_sphere(0.025, 6, 6)
                glPopMatrix()
            glPopMatrix()

        elif accessory_type == 'earrings':
            # Earrings: small dangling spheres on each side of head.
            # Ear Y torso-local ≈ head_local + ear_local_y = 0.58 + 0.295 = 0.875;
            # earrings dangle ~0.35 below ears → 0.875 - 0.35 = 0.525 ≈ 0.55
            glPushMatrix()
            glTranslatef(-0.35, 0.55, 0.0)
            self._draw_sphere(0.05, 8, 8)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0.35, 0.55, 0.0)
            self._draw_sphere(0.05, 8, 8)
            glPopMatrix()

        else:
            # Generic accessory: small cube on chest (torso-local ≈ 0.20)
            glPushMatrix()
            glTranslatef(0.0, 0.20, 0.25)
            self._draw_cube(0.06)
            glPopMatrix()

    # ────────────────────────────────────────────────────────────────────────
    # New clothing slot renderers
    # ────────────────────────────────────────────────────────────────────────

    def _draw_gloves(self, glove_data: dict) -> None:
        """Draw gloves on both paws, following arm positions (torso-local space)."""
        color = glove_data.get('color', [0.9, 0.1, 0.1]) if isinstance(glove_data, dict) else [0.9, 0.1, 0.1]
        glove_type = (glove_data.get('type', 'glove') if isinstance(glove_data, dict) else 'glove').lower()
        glColor3f(*color)
        quad = gluNewQuadric()
        limb = self._get_limb_positions()
        for side_sign, arm_key in ((-1.0, 'left_arm_angle'), (1.0, 'right_arm_angle')):
            angle = limb.get(arm_key, 0.0)
            # Paw position in torso-local space (mirrors _draw_panda_arms geometry).
            # arm_pivot_x already incorporates side_sign so the pivot is at
            # (±(BODY_WIDTH+0.06), 0.36, 0) — same values as _draw_panda_arms.
            # The paw swings away from the pivot along the arm angle; the X
            # component of that swing also flips per side (sin * side_sign).
            arm_pivot_x = side_sign * (self.BODY_WIDTH + 0.06)
            arm_pivot_y = 0.36
            paw_len = self.ARM_LENGTH * 0.88
            rad = math.radians(angle)
            paw_x = arm_pivot_x + paw_len * math.sin(rad) * side_sign
            paw_y = arm_pivot_y - paw_len * math.cos(rad)
            glPushMatrix()
            glTranslatef(paw_x, paw_y, 0.05)
            glRotatef(angle * side_sign, 0.0, 0.0, 1.0)
            # Glove body
            if glove_type in ('gauntlet', 'metal', 'steel'):
                glColor3f(min(1.0, color[0] * 0.85), min(1.0, color[1] * 0.85), min(1.0, color[2] * 0.85))
                gluCylinder(quad, 0.058, 0.045, 0.09, 10, 1)
                glTranslatef(0.0, 0.0, 0.09)
                glColor3f(*color)
                gluDisk(quad, 0.0, 0.058, 10, 1)
            else:
                # Soft glove — rounded paw cover
                glColor3f(*color)
                glScalef(1.1, 0.7, 1.1)
                self._draw_sphere(0.062, 10, 10)
                # Three knuckle bumps
                for ki in range(3):
                    kx = (ki - 1) * 0.026
                    glPushMatrix()
                    glTranslatef(kx, 0.04, 0.0)
                    glColor3f(min(1.0, color[0] + 0.08), min(1.0, color[1] + 0.08), min(1.0, color[2] + 0.08))
                    self._draw_sphere(0.018, 6, 6)
                    glPopMatrix()
            glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_armor(self, armor_data: dict) -> None:
        """Draw chest armor, robe, or cape on panda torso."""
        color = armor_data.get('color', [0.5, 0.5, 0.6]) if isinstance(armor_data, dict) else [0.5, 0.5, 0.6]
        armor_type = (armor_data.get('type', 'chestplate') if isinstance(armor_data, dict) else 'chestplate').lower()
        quad = gluNewQuadric()
        glColor3f(*color)
        if armor_type in ('cape', 'cloak', 'robe'):
            # Long flowing cape hanging down back.
            # Y = 0.35 = 0.65 panda-local − 0.30 body-translate = mid-back torso level.
            glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(*color, 0.88)
            glPushMatrix()
            glTranslatef(0.0, 0.35, -self.BODY_WIDTH * 0.52)
            glScalef(0.60, 0.90, 0.08)
            self._draw_sphere(1.0, 12, 8)
            glPopMatrix()
            # Hood (robe only)
            if armor_type == 'robe':
                # Y = 0.90 ≈ head top in torso-local (head centre 0.58 + HEAD_RADIUS 0.42*0.75)
                glPushMatrix()
                glTranslatef(0.0, 0.90, -self.BODY_WIDTH * 0.18)
                glScalef(0.40, 0.30, 0.35)
                self._draw_sphere(1.0, 10, 8)
                glPopMatrix()
            glDisable(GL_BLEND)
        else:
            # Chest plate: front torso coverage.
            # Y = 0.20 = 0.50 panda-local − 0.30 = upper quarter of body sphere.
            glPushMatrix()
            glTranslatef(0.0, 0.20, self.BODY_WIDTH * 0.46)
            glScalef(0.68, 0.55, 0.15)
            self._draw_sphere(1.0, 14, 10)
            glPopMatrix()
            # Shoulder pauldrons.
            # Y = 0.42 = 0.72 panda-local − 0.30 ≈ arm-pivot level.
            c2 = [min(1.0, c + 0.12) for c in color]
            glColor3f(*c2)
            for sx in (-1.0, 1.0):
                glPushMatrix()
                glTranslatef(sx * self.BODY_WIDTH * 0.58, 0.42, 0.0)
                glScalef(0.25, 0.22, 0.22)
                self._draw_sphere(1.0, 10, 8)
                glPopMatrix()
            # Central chest gem / badge.
            # Y = 0.25 = 0.55 panda-local − 0.30.
            glColor3f(1.0, 0.82, 0.1)
            glPushMatrix()
            glTranslatef(0.0, 0.25, self.BODY_WIDTH * 0.54)
            self._draw_sphere(0.040, 8, 8)
            glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_boots(self, boots_data: dict) -> None:
        """Draw boots on both feet, following leg positions (torso-local space)."""
        color = boots_data.get('color', [0.35, 0.22, 0.10]) if isinstance(boots_data, dict) else [0.35, 0.22, 0.10]
        boots_type = (boots_data.get('type', 'boot') if isinstance(boots_data, dict) else 'boot').lower()
        glColor3f(*color)
        quad = gluNewQuadric()
        limb = self._get_limb_positions()
        # Use the exact same geometry as _draw_panda_legs:
        #   leg pivot at (side * BODY_WIDTH * 0.78, -0.24, 0) in torso-local space.
        #   foot centre at (0, -LEG_LENGTH * 0.85, 0.045) in leg-local (after rotation).
        leg_pivot_x = self.BODY_WIDTH * 0.78   # matches leg_x in _draw_panda_legs
        leg_pivot_y = -0.24                     # matches leg_y in _draw_panda_legs
        for side_sign, leg_key in ((-1.0, 'left_leg_angle'), (1.0, 'right_leg_angle')):
            leg_ang = limb.get(leg_key, 0.0)
            rad = math.radians(leg_ang)
            # Apply the same rotation as _draw_panda_legs to find foot-tip in torso-local.
            # Unrotated foot offset: (0, -LEG_LENGTH*0.85, 0.045).
            # After glRotatef(angle, 1, 0, 0): y' = y*cos - z*sin, z' = y*sin + z*cos.
            fy_local = -self.LEG_LENGTH * 0.85 * math.cos(rad) - 0.045 * math.sin(rad)
            foot_x = side_sign * leg_pivot_x
            foot_y = leg_pivot_y + fy_local
            glPushMatrix()
            glTranslatef(foot_x, foot_y, 0.0)
            # Tilt boot to match foot orientation
            glRotatef(leg_ang, 1.0, 0.0, 0.0)
            if boots_type in ('moon', 'ski', 'platform', 'lava'):
                # Chunky sole
                glPushMatrix()
                glTranslatef(0.0, -0.02, 0.0)
                glScalef(1.0, 0.3, 1.0)
                glColor3f(min(1.0, color[0] * 0.7), min(1.0, color[1] * 0.7), min(1.0, color[2] * 0.7))
                gluCylinder(quad, 0.07, 0.07, 0.04, 10, 1)
                glPopMatrix()
            glColor3f(*color)
            # Boot shaft
            gluCylinder(quad, 0.060, 0.055, 0.12, 10, 1)
            glTranslatef(0.0, 0.0, 0.12)
            gluDisk(quad, 0.0, 0.060, 10, 1)
            glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_belt(self, belt_data: dict) -> None:
        """Draw belt / waistband around panda torso (torso-local space)."""
        color = belt_data.get('color', [0.45, 0.25, 0.08]) if isinstance(belt_data, dict) else [0.45, 0.25, 0.08]
        quad = gluNewQuadric()
        glColor3f(*color)
        # Belt strap: ring around torso at waist height.
        # Y = -0.18 = 0.12 panda-local − 0.30 body-translate = just below body centre.
        glPushMatrix()
        glTranslatef(0.0, -0.18, 0.0)
        glRotatef(90.0, 1.0, 0.0, 0.0)
        gluCylinder(quad, self.BODY_WIDTH * 0.58, self.BODY_WIDTH * 0.58, 0.05, 20, 1)
        glPopMatrix()
        # Buckle
        glColor3f(0.85, 0.78, 0.20)  # gold
        glPushMatrix()
        glTranslatef(0.0, -0.18, self.BODY_WIDTH * 0.60)
        glScalef(0.09, 0.055, 0.02)
        self._draw_sphere(1.0, 8, 6)
        glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_backpack(self, pack_data: dict) -> None:
        """Draw backpack on panda's back (torso-local space)."""
        color = pack_data.get('color', [0.2, 0.5, 0.8]) if isinstance(pack_data, dict) else [0.2, 0.5, 0.8]
        quad = gluNewQuadric()
        glColor3f(*color)
        # Main bag body.
        # Y = 0.15 = 0.45 panda-local − 0.30 = mid-back area of torso sphere.
        glPushMatrix()
        glTranslatef(0.0, 0.15, -self.BODY_WIDTH * 0.52)
        glScalef(0.42, 0.48, 0.22)
        self._draw_sphere(1.0, 12, 10)
        glPopMatrix()
        # Front pocket.
        # Y = 0.05 = 0.35 panda-local − 0.30.
        c2 = [min(1.0, c + 0.10) for c in color]
        glColor3f(*c2)
        glPushMatrix()
        glTranslatef(0.0, 0.05, -self.BODY_WIDTH * 0.62)
        glScalef(0.26, 0.22, 0.08)
        self._draw_sphere(1.0, 10, 8)
        glPopMatrix()
        # Shoulder straps.
        # Y = 0.42 = 0.72 panda-local − 0.30 ≈ arm-pivot level (shoulder area).
        glColor3f(*[max(0, c - 0.12) for c in color])
        for sx in (-0.18, 0.18):
            glPushMatrix()
            glTranslatef(sx, 0.42, -self.BODY_WIDTH * 0.35)
            glRotatef(15.0 * (-1 if sx < 0 else 1), 0.0, 0.0, 1.0)
            gluCylinder(quad, 0.025, 0.020, 0.45, 8, 1)
            glPopMatrix()
        gluDeleteQuadric(quad)

    # ========================================================================
    # Weapon System (3D)
    # ========================================================================
    
    def equip_weapon(self, weapon_data):
        """
        Equip weapon in 3D.
        
        Args:
            weapon_data: Weapon data (name, type, color, size)
        """
        self.equipped_weapon = weapon_data
        logger.info(f"Equipped weapon: {weapon_data.get('name', 'Unknown')}")
    
    def unequip_weapon(self):
        """Remove equipped weapon."""
        self.equipped_weapon = None
    
    def _draw_weapon(self):
        """Draw equipped weapon in panda's hand."""
        if not self.equipped_weapon:
            return
        
        glPushMatrix()
        
        # Position in right arm — torso-local space (body centre = origin)
        # arm pivot: (BODY_WIDTH + 0.1, arm_y + 0.06, 0) = (0.66, 0.36, 0)
        arm_x = self.BODY_WIDTH + 0.1
        arm_y = 0.36
        
        glTranslatef(arm_x, arm_y, 0.0)
        glRotatef(self.weapon_rotation, 0.0, 0.0, 1.0)
        
        # Get weapon properties
        weapon_type = self.equipped_weapon.get('type', 'sword')
        color = self.equipped_weapon.get('color', [0.7, 0.7, 0.7])
        size = self.equipped_weapon.get('size', 0.5)
        
        glColor3f(*color)
        
        # Draw different weapon types
        _wt = str(weapon_type).lower()
        _wid = str(self.equipped_weapon.get('id', '')).lower()
        if any(k in _wt or k in _wid for k in ('sword', 'blade', 'katana', 'dagger')):
            self._draw_sword(size)
        elif any(k in _wt or k in _wid for k in ('axe', 'hatchet', 'battleaxe', 'halberd')):
            self._draw_axe(size)
        elif any(k in _wt or k in _wid for k in ('staff', 'cane', 'scepter')):
            self._draw_staff(size)
        elif any(k in _wt or k in _wid for k in ('wand', 'magic', 'enchanted')):
            self._draw_held_wand(size, color)
        elif any(k in _wt or k in _wid for k in ('spear', 'lance', 'polearm')):
            self._draw_held_spear(size, color)
        elif any(k in _wt or k in _wid for k in ('bow', 'longbow', 'crossbow', 'blowgun', 'archer')):
            self._draw_held_bow(size, color)
        elif any(k in _wt or k in _wid for k in ('gun', 'pistol', 'rifle', 'cannon', 'blaster')):
            self._draw_held_gun(size, color)
        elif any(k in _wt or k in _wid for k in ('shield', 'buckler', 'tower')):
            self._draw_held_shield(size, color)
        elif any(k in _wt or k in _wid for k in ('hammer', 'mallet', 'maul', 'mace', 'club')):
            self._draw_held_hammer(size, color)
        else:
            self._draw_sword(size)  # Default
        
        glPopMatrix()
    
    def _draw_sword(self, size: float):
        """Draw sword weapon."""
        # Blade
        glPushMatrix()
        glScalef(0.05, size, 0.02)
        self._draw_cube(1.0)
        glPopMatrix()
        
        # Handle
        glPushMatrix()
        glTranslatef(0.0, -size * 0.2, 0.0)
        glScalef(0.08, 0.15, 0.08)
        self._draw_cube(1.0)
        glPopMatrix()
        
        # Guard
        glPushMatrix()
        glTranslatef(0.0, -size * 0.1, 0.0)
        glScalef(0.2, 0.02, 0.05)
        self._draw_cube(1.0)
        glPopMatrix()
    
    def _draw_axe(self, size: float):
        """Draw axe weapon."""
        # Handle
        glPushMatrix()
        glScalef(0.05, size, 0.05)
        self._draw_cube(1.0)
        glPopMatrix()
        
        # Axe head
        glPushMatrix()
        glTranslatef(0.0, size * 0.4, 0.0)
        glScalef(0.15, 0.1, 0.05)
        self._draw_cube(1.0)
        glPopMatrix()
    
    def _draw_staff(self, size: float):
        """Draw staff weapon."""
        # Staff pole
        glPushMatrix()
        glScalef(0.04, size, 0.04)
        self._draw_cube(1.0)
        glPopMatrix()
        
        # Orb on top
        glPushMatrix()
        glTranslatef(0.0, size * 0.5, 0.0)
        glColor3f(0.2, 0.5, 1.0)  # Blue orb
        self._draw_sphere(0.08, 12, 12)
        glPopMatrix()

    def _draw_held_items(self) -> None:
        """Draw items held in paw(s) — positioned in torso-local space."""
        if not self.clothing['held_right'] and not self.clothing['held_left']:
            return

        limb   = self._get_limb_positions()
        # Arm shoulder in torso-local space:
        #   arm_y + 0.06 = 0.30 + 0.06 = 0.36 (same pivot used by _draw_panda_arms)
        # Body bob is already incorporated in the parent torso glTranslatef,
        # so we do NOT add it here again.
        arm_x  = self.BODY_WIDTH + 0.06
        arm_y  = 0.36

        for side, key in ((-1, 'held_left'), (1, 'held_right')):
            item = self.clothing[key]
            if not item:
                continue
            angle = limb.get('left_arm_angle' if side == -1 else 'right_arm_angle', 0.0)
            # Translate to shoulder then rotate by limb angle then move to paw tip
            glPushMatrix()
            glTranslatef(side * arm_x, arm_y, 0.0)
            glRotatef(angle, 1.0, 0.0, 0.0)
            # Paw tip offset
            glTranslatef(0.0, -(self.ARM_LENGTH * 0.88 + 0.10), 0.0)
            # Grip tilt — weapon points mostly upward/forward
            glRotatef(-85.0, 1.0, 0.0, 0.0)
            self._draw_held_item(item)
            glPopMatrix()

    def _draw_held_item(self, item: dict) -> None:
        """Dispatch to specific item renderer based on type."""
        if isinstance(item, str):
            item = {'id': item, 'type': item}
        item_type = str(item.get('type', item.get('id', 'bamboo'))).lower()
        color = item.get('color', [0.7, 0.6, 0.3])
        size  = float(item.get('size', 0.5))
        glColor3f(*color)

        if any(k in item_type for k in ('sword', 'blade', 'katana', 'dagger')):
            self._draw_held_sword(size, color)
        elif any(k in item_type for k in ('bow', 'longbow', 'crossbow', 'archer', 'blowgun')):
            self._draw_held_bow(size, color)
        elif any(k in item_type for k in ('bamboo', 'stick', 'cane')):
            self._draw_held_bamboo(size, color)
        elif any(k in item_type for k in ('staff', 'scepter')):
            self._draw_held_bamboo(size, color)  # rod shape same as bamboo
        elif any(k in item_type for k in ('wand', 'magic', 'enchanted')):
            self._draw_held_wand(size, color)
        elif any(k in item_type for k in ('spear', 'lance', 'polearm', 'halberd')):
            self._draw_held_spear(size, color)
        elif any(k in item_type for k in ('gun', 'pistol', 'rifle', 'cannon', 'blaster')):
            self._draw_held_gun(size, color)
        elif any(k in item_type for k in ('shield', 'buckler')):
            self._draw_held_shield(size, color)
        elif any(k in item_type for k in ('hammer', 'mace', 'maul')):
            self._draw_held_hammer(size, color)
        elif any(k in item_type for k in ('axe', 'hatchet', 'battleaxe')):
            self._draw_axe(size)  # consistent with _draw_weapon axe path
        elif any(k in item_type for k in ('ball', 'toy', 'sphere')):
            self._draw_held_toy_ball(size, color)
        elif any(k in item_type for k in ('flower', 'rose', 'daisy')):
            self._draw_held_flower(size, color)
        elif any(k in item_type for k in ('food', 'fish', 'dumpling', 'apple', 'cookie')):
            self._draw_held_food(item_type, size, color)
        else:
            # Generic: simple rod
            quad = gluNewQuadric()
            gluCylinder(quad, 0.020, 0.015, size, 8, 1)
            gluDeleteQuadric(quad)

    def _draw_held_sword(self, size: float, color: list) -> None:
        """Sword held in paw — blade up, cross-guard at grip."""
        quad = gluNewQuadric()
        # Blade
        glPushMatrix()
        glColor3f(min(1.0, color[0]+0.2), min(1.0, color[1]+0.2), min(1.0, color[2]+0.2))
        glScalef(0.035, 1.0, 0.018)
        gluCylinder(quad, size * 0.5, size * 0.05, size, 12, 1)
        glPopMatrix()
        # Blade edge glint
        glPushMatrix()
        glTranslatef(0.018, 0.0, 0.0)
        glColor4f(1.0, 1.0, 1.0, 0.55)
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glScalef(0.004, size * 0.85, 0.004)
        self._draw_sphere(1.0, 6, 6)
        glDisable(GL_BLEND)
        glPopMatrix()
        # Cross-guard
        glPushMatrix()
        glColor3f(*color)
        glTranslatef(0.0, -size * 0.08, 0.0)
        glScalef(0.18, 0.022, 0.05)
        self._draw_sphere(1.0, 8, 8)
        glPopMatrix()
        # Handle / grip with wrapping
        glPushMatrix()
        glTranslatef(0.0, -size * 0.22, 0.0)
        c2 = [max(0, c - 0.2) for c in color]
        glColor3f(*c2)
        gluCylinder(quad, 0.030, 0.025, size * 0.18, 8, 1)
        glPopMatrix()
        # Pommel
        glPushMatrix()
        glTranslatef(0.0, -size * 0.40, 0.0)
        glColor3f(*color)
        self._draw_sphere(0.032, 8, 8)
        glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_held_bow(self, size: float, color: list) -> None:
        """Bow held in paw — arc of wood with string."""
        quad = gluNewQuadric()
        # Bow limbs: arc of small cylinders
        num_seg = 12
        arc_r = size * 0.38
        for i in range(num_seg + 1):
            a0 = math.radians(-110 + i * (220 / num_seg))
            a1 = math.radians(-110 + (i+1) * (220 / num_seg))
            if i >= num_seg:
                break
            x0, y0 = arc_r * math.sin(a0), arc_r * math.cos(a0)
            x1, y1 = arc_r * math.sin(a1), arc_r * math.cos(a1)
            dx, dy = x1 - x0, y1 - y0
            length = math.hypot(dx, dy)
            angle  = math.degrees(math.atan2(dy, dx))
            glPushMatrix()
            glTranslatef(x0, y0, 0.0)
            glRotatef(angle - 90, 0.0, 0.0, 1.0)
            glColor3f(*color)
            gluCylinder(quad, 0.018, 0.018, length, 6, 1)
            glPopMatrix()
        # String (thin pale line)
        tip0y =  arc_r * math.cos(math.radians(-110))
        tip1y =  arc_r * math.cos(math.radians( 110))
        glBegin(GL_LINES)
        glColor3f(0.9, 0.88, 0.78)
        glVertex3f(0.0, tip0y, 0.0)
        glVertex3f(0.0, tip1y, 0.0)
        glEnd()
        gluDeleteQuadric(quad)

    def _draw_held_bamboo(self, size: float, color: list) -> None:
        """Bamboo stalk with nodes."""
        quad = gluNewQuadric()
        seg_h = size / 5.0
        for i in range(5):
            y = i * seg_h
            glPushMatrix()
            glTranslatef(0.0, y, 0.0)
            glColor3f(*color)
            gluCylinder(quad, 0.026, 0.022, seg_h, 8, 1)
            # Node ring
            glTranslatef(0.0, seg_h, 0.0)
            glColor3f(min(1.0, color[0]+0.06), min(1.0, color[1]+0.04), min(1.0, color[2]+0.0))
            gluDisk(quad, 0.0, 0.030, 8, 1)
            glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_held_toy_ball(self, size: float, color: list) -> None:
        """Colourful toy ball."""
        glColor3f(*color)
        self._draw_sphere(size * 0.18, 14, 14)
        # Stripe
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 1.0, 1.0, 0.45)
        glPushMatrix()
        glScalef(1.0, 0.18, 1.0)
        self._draw_sphere(size * 0.19, 10, 10)
        glPopMatrix()
        glDisable(GL_BLEND)

    def _draw_held_flower(self, size: float, color: list) -> None:
        """Simple flower — stem + petals."""
        quad = gluNewQuadric()
        # Stem
        glColor3f(0.3, 0.65, 0.2)
        gluCylinder(quad, 0.012, 0.010, size * 0.5, 6, 1)
        # Petals
        glTranslatef(0.0, size * 0.5, 0.0)
        for i in range(6):
            a = math.radians(i * 60)
            glPushMatrix()
            glTranslatef(math.cos(a) * 0.05, math.sin(a) * 0.05, 0.0)
            glColor3f(*color)
            self._draw_sphere(0.040, 8, 8)
            glPopMatrix()
        # Centre
        glColor3f(1.0, 0.95, 0.2)
        self._draw_sphere(0.028, 8, 8)
        gluDeleteQuadric(quad)

    def _draw_held_food(self, item_type: str, size: float, color: list) -> None:
        """Generic food item."""
        if 'fish' in item_type:
            # Simple fish silhouette
            glColor3f(*color)
            glPushMatrix()
            glScalef(0.06, 0.13, 0.04)
            self._draw_sphere(1.0, 10, 10)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0.0, -0.10, 0.0)
            glScalef(0.10, 0.06, 0.02)
            self._draw_sphere(1.0, 8, 8)
            glPopMatrix()
        elif 'apple' in item_type or 'fruit' in item_type:
            glColor3f(*color)
            self._draw_sphere(0.07, 12, 12)
            glColor3f(0.3, 0.6, 0.1)
            glPushMatrix()
            glTranslatef(0.0, 0.06, 0.0)
            glScalef(0.01, 0.055, 0.01)
            quad = gluNewQuadric()
            gluCylinder(quad, 1.0, 0.5, 1.0, 6, 1)
            gluDeleteQuadric(quad)
            glPopMatrix()
        else:
            # Default round food blob
            glColor3f(*color)
            self._draw_sphere(0.065, 10, 10)

    # ────────────────────────────────────────────────────────────────────────
    # Additional held-weapon renderers (wand, spear, gun, shield, hammer)
    # ────────────────────────────────────────────────────────────────────────

    def _draw_held_wand(self, size: float, color: list) -> None:
        """Magic wand with glowing orb tip."""
        quad = gluNewQuadric()
        # Wand shaft
        glColor3f(*color)
        gluCylinder(quad, 0.018, 0.014, size * 0.75, 8, 1)
        # Orb tip
        glTranslatef(0.0, 0.0, size * 0.75)
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glColor4f(0.6, 0.2, 1.0, 0.90)
        self._draw_sphere(0.040, 10, 10)
        glColor4f(0.9, 0.7, 1.0, 0.55)
        self._draw_sphere(0.055, 10, 10)
        glDisable(GL_BLEND)
        # Star sparkles
        glColor3f(1.0, 0.95, 0.3)
        for i in range(4):
            a = math.radians(i * 90 + self.animation_frame * 3.0)
            glPushMatrix()
            glTranslatef(math.cos(a) * 0.045, math.sin(a) * 0.045, 0.0)
            self._draw_sphere(0.010, 5, 5)
            glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_held_spear(self, size: float, color: list) -> None:
        """Spear: long shaft with metal tip."""
        quad = gluNewQuadric()
        # Shaft
        glColor3f(*[max(0, c - 0.1) for c in color])
        gluCylinder(quad, 0.022, 0.018, size * 0.85, 10, 1)
        # Metal tip
        glTranslatef(0.0, 0.0, size * 0.85)
        glColor3f(0.78, 0.78, 0.82)
        gluCylinder(quad, 0.028, 0.004, size * 0.20, 10, 1)
        # Butt cap
        glTranslatef(0.0, 0.0, -(size * 0.85 + 0.005))
        glColor3f(*color)
        self._draw_sphere(0.025, 8, 8)
        gluDeleteQuadric(quad)

    def _draw_held_gun(self, size: float, color: list) -> None:
        """Stylized gun/pistol."""
        quad = gluNewQuadric()
        # Barrel
        glColor3f(*color)
        gluCylinder(quad, 0.025, 0.022, size * 0.55, 10, 1)
        # Body / frame
        glPushMatrix()
        glTranslatef(0.0, -size * 0.08, size * 0.05)
        glColor3f(*[max(0, c - 0.08) for c in color])
        glScalef(0.06, 0.14, 0.16)
        self._draw_sphere(1.0, 8, 8)
        glPopMatrix()
        # Handle grip
        glPushMatrix()
        glTranslatef(0.0, -size * 0.28, size * 0.08)
        glRotatef(25.0, 1.0, 0.0, 0.0)
        glColor3f(0.22, 0.16, 0.12)
        gluCylinder(quad, 0.030, 0.025, size * 0.22, 8, 1)
        glPopMatrix()
        # Muzzle accent ring
        glTranslatef(0.0, 0.0, size * 0.55)
        glColor3f(0.55, 0.55, 0.55)
        gluDisk(quad, 0.018, 0.030, 10, 1)
        gluDeleteQuadric(quad)

    def _draw_held_shield(self, size: float, color: list) -> None:
        """Kite shield held on left arm."""
        quad = gluNewQuadric()
        # Shield face
        glColor3f(*color)
        glScalef(0.45, 0.55, 0.05)
        self._draw_sphere(size, 14, 12)
        glScalef(1 / 0.45, 1 / 0.55, 1 / 0.05)  # undo scale
        # Rim
        glColor3f(*[max(0, c - 0.15) for c in color])
        glPushMatrix()
        glScalef(0.46, 0.56, 0.04)
        self._draw_sphere(size + 0.01, 14, 12)
        glPopMatrix()
        # Central boss / emblem
        glColor3f(0.85, 0.75, 0.20)
        glPushMatrix()
        glTranslatef(0.0, 0.0, size * 0.055)
        self._draw_sphere(0.058, 10, 10)
        glPopMatrix()
        gluDeleteQuadric(quad)

    def _draw_held_hammer(self, size: float, color: list) -> None:
        """Hammer / mace / maul."""
        quad = gluNewQuadric()
        # Shaft
        glColor3f(*[max(0, c - 0.12) for c in color])
        gluCylinder(quad, 0.025, 0.022, size * 0.70, 10, 1)
        # Head (cylinder on side)
        glTranslatef(0.0, 0.0, size * 0.70)
        glColor3f(*color)
        glRotatef(90.0, 1.0, 0.0, 0.0)
        gluCylinder(quad, size * 0.12, size * 0.12, size * 0.28, 12, 1)
        # Cap ends
        glColor3f(min(1.0, color[0] + 0.12), min(1.0, color[1] + 0.12), min(1.0, color[2] + 0.12))
        gluDisk(quad, 0.0, size * 0.12, 12, 1)
        glTranslatef(0.0, 0.0, size * 0.28)
        gluDisk(quad, 0.0, size * 0.12, 12, 1)
        gluDeleteQuadric(quad)

    # ========================================================================
    # Autonomous Behavior
    # ========================================================================
    
    def set_autonomous_mode(self, enabled: bool):
        """Enable or disable autonomous wandering."""
        self.autonomous_mode = enabled
    
    def walk_to_position(self, x: float, y: float, z: float,
                         callback: Optional[Callable] = None) -> None:
        """Make panda walk to *x, y, z*.  Calls *callback* (no args) when arrived."""
        self.target_position = (x, y, z)
        self._walk_arrived_cb = callback
        self.transition_to_state('walking')
    
    def _update_autonomous_behavior(self, delta_time: float):
        """Update autonomous walking and activities."""
        if not self.autonomous_mode:
            return
        
        # If has target, walk towards it
        if self.target_position:
            self._move_towards_target(delta_time)
        else:
            # Idle behavior
            self.idle_timer += delta_time
            
            if self.idle_timer >= self.next_activity_time:
                self._choose_random_activity()
                self.idle_timer = 0.0
                self.next_activity_time = random.uniform(3.0, 8.0)
    
    def _move_towards_target(self, delta_time: float):
        """Move panda towards target position."""
        if not self.target_position:
            return
        
        tx, ty, tz = self.target_position
        
        # Calculate direction
        dx = tx - self.panda_x
        dy = ty - self.panda_y
        dz = tz - self.panda_z
        
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if distance < 0.12:
            # Reached target — fire optional callback, then return to idle
            self.target_position = None
            self.transition_to_state('idle')
            cb = getattr(self, '_walk_arrived_cb', None)
            self._walk_arrived_cb = None  # clear before calling so re-entrancy is safe
            if callable(cb):
                try:
                    cb()
                except Exception as _e:  # noqa: BLE001
                    logger.debug('walk_arrived_cb: %s', _e)
            return
        
        # Normalize direction
        dx /= distance
        dy /= distance
        dz /= distance
        
        # Move towards target
        move_amount = self.walking_speed * delta_time
        self.panda_x += dx * move_amount
        self.panda_y += dy * move_amount
        self.panda_z += dz * move_amount
        
        # Face direction of movement
        angle = math.atan2(dx, dz)
        self.rotation_y = math.degrees(angle)
    
    def _choose_random_activity(self):
        """Choose a random activity for panda using the class-level weights table."""
        # Weights sum to 1.0 — use random.random() which returns [0.0, 1.0)
        r = random.random()

        cumulative = 0.0
        for activity, weight in self._ACTIVITY_WEIGHTS:
            cumulative += weight
            if r <= cumulative:
                if activity == 'walk_around':
                    # Pick random position to walk to
                    x = random.uniform(-1.5, 1.5)
                    z = random.uniform(-1.5, 1.5)
                    self.walk_to_position(x, -0.7, z)
                elif activity == 'work':
                    self.start_working()
                elif activity == 'celebrate':
                    self.set_animation_state('celebrating')
                elif activity == 'crawl_around':
                    # Crawl then return to idle — guard so a later state change wins
                    self.set_animation_state('crawling')
                    dur = random.uniform(1.5, 3.5)
                    QTimer.singleShot(int(dur * 1000),
                                      lambda: self.set_animation_state('idle')
                                      if self.animation_state == 'crawling' else None)
                elif activity == 'climb_wall':
                    # Climb → fall back → idle  (each step checks current state)
                    self.set_animation_state('climbing_wall')
                    fall_ms = int(random.uniform(1.0, 2.5) * 1000)
                    idle_ms = fall_ms + int(random.uniform(0.8, 1.8) * 1000)
                    QTimer.singleShot(fall_ms,
                                      lambda: self.set_animation_state('falling_back')
                                      if self.animation_state == 'climbing_wall' else None)
                    QTimer.singleShot(idle_ms,
                                      lambda: self.set_animation_state('idle')
                                      if self.animation_state == 'falling_back' else None)
                elif activity == 'sit_back':
                    self.set_animation_state('sitting_back')
                    dur = random.uniform(3.0, 7.0)
                    QTimer.singleShot(int(dur * 1000),
                                      lambda: self.set_animation_state('idle')
                                      if self.animation_state == 'sitting_back' else None)
                elif activity == 'hang_ceiling':
                    self.set_animation_state('hanging_ceiling')
                    dur = random.uniform(2.5, 5.0)
                    QTimer.singleShot(int(dur * 1000),
                                      lambda: self.set_animation_state('falling_back')
                                      if self.animation_state == 'hanging_ceiling' else None)
                    QTimer.singleShot(int(dur * 1000) + 1800,
                                      lambda: self.set_animation_state('idle')
                                      if self.animation_state == 'falling_back' else None)
                elif activity == 'rolling':
                    # Roll on back then recover — belly jiggle kick on start
                    self.set_animation_state('rolling')
                    self._belly_y = -0.06
                    dur = random.uniform(2.0, 4.0)
                    QTimer.singleShot(int(dur * 1000),
                                      lambda: self.set_animation_state('idle')
                                      if self.animation_state == 'rolling' else None)
                elif activity == 'sleeping':
                    self.set_animation_state('sleeping')
                    dur = random.uniform(5.0, 12.0)
                    QTimer.singleShot(int(dur * 1000),
                                      lambda: self.set_animation_state('idle')
                                      if self.animation_state == 'sleeping' else None)
                elif activity in ('dance', 'spin', 'backflip'):
                    self.set_animation_state(activity)
                    dur = random.uniform(2.5, 5.0) if activity == 'dance' else random.uniform(1.5, 3.0)
                    QTimer.singleShot(int(dur * 1000),
                                      lambda a=activity: self.set_animation_state('idle')
                                      if self.animation_state == a else None)
                break
    
    # ========================================================================
    # Working Behavior
    # ========================================================================
    
    def start_working(self):
        """Start working animation."""
        self.is_working = True
        self.work_progress = 0.0
        self.set_animation_state('working')
        logger.info("Panda started working")
    
    def stop_working(self):
        """Stop working animation."""
        self.is_working = False
        self.set_animation_state('idle')
        logger.info("Panda stopped working")

    def open_furniture(self, furniture_id: str) -> None:
        """Play a short reach-forward animation as if opening a piece of furniture.

        The panda faces the furniture (already walked there), reaches both arms
        forward (arm overshoot kick), holds briefly, then returns to idle.
        The ``furniture_id`` drives which side is emphasised:
          - wardrobe / fridge / toy_box → both arms reach (opening double doors / lid)
          - weapons_rack / armor_rack   → single reach-up pose
          - trophy_stand               → gentle celebratory raise
        """
        try:
            if furniture_id == 'trophy_stand':
                self.set_animation_state('celebrating')
                QTimer.singleShot(1800, lambda: self.set_animation_state('idle')
                                  if self.animation_state == 'celebrating' else None)
            elif furniture_id in ('weapons_rack', 'armor_rack'):
                # Reach up to wall rack
                self._arm_over[0] += 25.0   # both arms
                self._arm_over[1] += 25.0
                self.set_animation_state('waving')
                QTimer.singleShot(900, lambda: self.set_animation_state('idle')
                                  if self.animation_state == 'waving' else None)
            else:
                # Both arms forward (push/pull motion)
                self._arm_over[0] += 20.0
                self._arm_over[1] += 20.0
                self.set_animation_state('working')
                QTimer.singleShot(700, lambda: self.set_animation_state('idle'))
        except Exception as _e:
            logger.debug(f"open_furniture({furniture_id}): {_e}")
    
    def _update_working_animation(self, delta_time: float):
        """Update working animation state."""
        if not self.is_working:
            return
        
        # Update work progress
        self.work_progress += delta_time * 0.1
        if self.work_progress >= 1.0:
            self.work_progress = 0.0
        
        # Update animation phase for typing/sorting gestures
        self.work_animation_phase += delta_time * 5.0
        
        # Arms move as if typing or sorting
        # This is reflected in limb positions
    
    def _get_working_limb_offsets(self):
        """Get limb positions for working animation."""
        if not self.is_working:
            return {}
        
        # Simulate typing motions
        phase = self.work_animation_phase
        left_offset = 10 * math.sin(phase)
        right_offset = 10 * math.sin(phase + math.pi)
        
        return {
            'left_arm_angle': -30 + left_offset,
            'right_arm_angle': -30 + right_offset,
            'left_leg_angle': 0,
            'right_leg_angle': 0
        }
    
    def clear_items(self):
        """Remove all items from the scene."""
        self.items_3d.clear()
    
    # ========================================================================
    # Enhanced Helper Methods (Replacement for deprecated bridge functionality)
    # ========================================================================
    
    def play_animation_sequence(self, states: List[str], durations: List[float]):
        """
        Play a sequence of animations with specified durations.
        
        Args:
            states: List of animation state names
            durations: List of durations (in seconds) for each state
            
        Example:
            widget.play_animation_sequence(['jumping', 'celebrating', 'idle'], [1.0, 2.0, 0])
        """
        if not QT_AVAILABLE:
            return
        
        def play_next_animation(index):
            if index >= len(states):
                return
            
            self.set_animation_state(states[index])
            
            if index < len(durations) and durations[index] > 0:
                QTimer.singleShot(int(durations[index] * 1000), 
                                lambda: play_next_animation(index + 1))
        
        play_next_animation(0)
    
    def add_item_from_emoji(self, emoji: str, name: str = None, 
                           position: tuple = None, physics: dict = None):
        """
        Add an item to the scene based on emoji representation.
        Converts 2D position to 3D coordinates automatically.
        
        Args:
            emoji: Emoji representing the item (🎾, 🍕, etc.)
            name: Optional name for the item
            position: Optional (x, y) 2D position, converted to 3D
            physics: Optional physics properties override
            
        Example:
            widget.add_item_from_emoji('🎾', 'Tennis Ball', position=(100, 200))
        """
        # Emoji to color mapping for visual representation
        emoji_colors = {
            '🍕': [1.0, 0.5, 0.0],  # Pizza - orange
            '🎾': [0.8, 1.0, 0.0],  # Tennis ball - yellow-green
            '🏀': [1.0, 0.5, 0.0],  # Basketball - orange
            '⚽': [1.0, 1.0, 1.0],  # Soccer ball - white
            '🍎': [1.0, 0.0, 0.0],  # Apple - red
            '🍌': [1.0, 1.0, 0.0],  # Banana - yellow
            '🍇': [0.5, 0.0, 0.5],  # Grapes - purple
            '🥕': [1.0, 0.5, 0.0],  # Carrot - orange
            '🍔': [0.8, 0.5, 0.2],  # Burger - brown
            '🍰': [1.0, 0.8, 0.9],  # Cake - pink
        }
        
        # Emoji to item type mapping
        food_emojis = {'🍕', '🍎', '🍌', '🍇', '🥕', '🍔', '🍰'}
        toy_emojis = {'🎾', '🏀', '⚽'}
        
        item_type = 'food' if emoji in food_emojis else 'toy'
        color = emoji_colors.get(emoji, [0.7, 0.7, 0.7])
        
        # Convert 2D position to 3D if provided
        if position:
            x = (position[0] - 200) / 200.0
            y = 0.5  # Start slightly above ground
            z = -(position[1] - 250) / 250.0
        else:
            x, y, z = 0.0, 0.5, 0.0
        
        # Add item with physics
        item_data = {
            'color': color,
            'name': name or emoji,
            'emoji': emoji
        }
        
        if physics:
            item_data.update(physics)
        
        self.add_item_3d(item_type, x, y, z, **item_data)
    
    def walk_to_item(self, item_index: int, callback: Optional[Callable] = None):
        """
        Make panda walk to a specific item in the scene.
        
        Args:
            item_index: Index of item in items_3d list
            callback: Optional callback function when panda reaches item
            
        Example:
            widget.walk_to_item(0, lambda: logger.debug("Reached item!"))
        """
        if not QT_AVAILABLE or item_index >= len(self.items_3d):
            return
        
        item = self.items_3d[item_index]
        target_x = item['x']
        target_y = item['y']
        target_z = item['z']
        
        # Walk to position
        self.walk_to_position(target_x, target_y, target_z)
        
        # Set up callback when reached
        if callback:
            def check_reached():
                if self.target_position is None:
                    # Reached target
                    callback()
                else:
                    # Check again in 100ms
                    QTimer.singleShot(100, check_reached)
            
            QTimer.singleShot(100, check_reached)
    
    def interact_with_item(self, item_index: int, interaction_type: str = 'auto'):
        """
        Make panda interact with an item (pick up, eat, play, etc.).
        
        Args:
            item_index: Index of item in items_3d list
            interaction_type: Type of interaction ('pick_up', 'eat', 'kick', 'auto')
                            'auto' determines interaction based on item type
        """
        if item_index >= len(self.items_3d):
            return
        
        item = self.items_3d[item_index]
        item_type = item.get('type', 'toy')
        
        # Auto-determine interaction
        if interaction_type == 'auto':
            if item_type == 'food':
                interaction_type = 'eat'
            else:
                interaction_type = 'kick'
        
        # Play appropriate animation
        animation_map = {
            'eat': 'fed',
            'kick': 'jumping',
            'pick_up': 'working',
            'play': 'celebrating'
        }
        
        animation = animation_map.get(interaction_type, 'idle')
        self.set_animation_state(animation)
        
        # Remove item after interaction if it's consumable
        if item_type == 'food':
            QTimer.singleShot(1000, lambda: self._remove_item(item_index))
    
    def _remove_item(self, item_index: int):
        """Internal method to remove an item from scene."""
        if item_index < len(self.items_3d):
            self.items_3d.pop(item_index)
            self.update()
    
    def react_to_collision(self, collision_point: tuple, intensity: float = 1.0):
        """
        Make panda react to collision (being hit by object, hitting wall, etc.).
        
        Args:
            collision_point: (x, y, z) point of collision relative to panda
            intensity: Intensity of collision (0.0 to 1.0+)
        """
        # Determine which part was hit based on collision point
        _, cy, _ = collision_point
        
        # Normalize to body height (0 = feet, 1 = head)
        body_height = 1.5  # Approximate panda height
        hit_ratio = cy / body_height
        
        # Choose reaction animation based on hit location and intensity
        if intensity > 0.8:
            # Strong hit
            self.set_animation_state('wall_hit')
        elif hit_ratio > 0.7:
            # Head hit
            self.set_animation_state('clicked')
            self.play_animation_sequence(['clicked', 'idle'], [0.5, 0])
        elif hit_ratio < 0.3:
            # Feet hit - jump
            self.set_animation_state('jumping')
        else:
            # Body hit
            self.play_animation_sequence(['wall_hit', 'idle'], [0.3, 0])
    
    def take_damage(self, amount: float, damage_type: str = 'physical',
                   source_position: tuple = None) -> dict:
        """
        Apply damage to panda (for combat/game systems).
        
        Args:
            amount: Damage amount
            damage_type: Type of damage ('physical', 'fire', 'ice', etc.)
            source_position: Position of damage source for knockback
            
        Returns:
            Dictionary with damage results
        """
        # Play damage animation
        self.set_animation_state('wall_hit')
        
        # Calculate knockback if source position provided
        if source_position and QT_AVAILABLE:
            sx, sy, sz = source_position
            
            # Direction away from source
            dx = self.panda_x - sx
            dz = self.panda_z - sz
            length = math.sqrt(dx*dx + dz*dz)
            
            if length > 0:
                # Apply knockback
                knockback_strength = min(amount * 0.1, 0.5)
                self.panda_x += (dx / length) * knockback_strength
                self.panda_z += (dz / length) * knockback_strength
        
        # Return damage info (actual health tracking should be in game system)
        return {
            'damage_taken': amount,
            'damage_type': damage_type,
            'animation': 'wall_hit',
            'position': (self.panda_x, self.panda_y, self.panda_z)
        }
    
    def heal(self, amount: float):
        """
        Heal panda (for game systems).
        
        Args:
            amount: Healing amount
        """
        # Play celebration animation for healing
        self.play_animation_sequence(['fed', 'celebrating', 'idle'], [1.0, 1.0, 0])
        
        return {
            'healed': amount,
            'animation': 'celebrating'
        }
    
    def set_mood(self, mood: str):
        """
        Set panda's visual mood/expression.

        Args:
            mood: Mood name string (or Enum — .value is extracted automatically).
                  Accepts values from both PandaCharacter and PandaMoodSystem enums.
        """
        # Accept Enum objects gracefully (panda_character passes PandaMood.WORKING etc.)
        if hasattr(mood, 'value'):
            mood = mood.value

        animation = _MOOD_TO_ANIMATION.get(mood, 'idle')
        self.set_animation_state(animation)
        # Also update the emotion layer so secondary motion reacts
        if hasattr(self, '_emotion_weights'):
            for key in self._emotion_weights:
                self._emotion_weights[key] = 0.0
            emo = _MOOD_TO_EMOTION.get(mood)
            if emo and emo in self._emotion_weights:
                self._emotion_weights[emo] = 1.0

        self.mood_changed.emit(mood)
    
    def set_color(self, color_type: str, rgb: tuple):
        """
        Set custom color for panda parts.
        
        Args:
            color_type: Type of color ('body', 'eyes', 'accent', 'glow')
            rgb: RGB tuple (0-255 range) or (0.0-1.0 range)
        """
        # Normalize RGB to 0.0-1.0 range if needed
        if all(isinstance(v, int) or v > 1.0 for v in rgb):
            # Convert from 0-255 to 0.0-1.0
            normalized_rgb = [c / 255.0 for c in rgb[:3]]
        else:
            # Already normalized
            normalized_rgb = list(rgb[:3])
        
        # Apply the color
        if color_type in self.custom_colors:
            self.custom_colors[color_type] = normalized_rgb
            logger.debug(f"Panda color {color_type} set to {normalized_rgb}")
            self.update()  # Trigger redraw
        else:
            logger.warning(f"Unknown color type: {color_type}")

    # Fur-style → (body_rgb, accent_rgb, belly_rgb) in 0-1 float range
    _FUR_STYLE_COLORS: dict = {
        # ── Core presets ────────────────────────────────────────────────────
        'classic':         ((0.97, 0.97, 0.99), (0.08, 0.08, 0.08), (1.00, 0.98, 0.93)),
        'black_white':     ((0.97, 0.97, 0.99), (0.08, 0.08, 0.08), (1.00, 0.98, 0.93)),
        'albino':          ((1.00, 1.00, 1.00), (0.85, 0.82, 0.80), (1.00, 0.99, 0.97)),
        'snow_panda':      ((0.92, 0.95, 1.00), (0.65, 0.72, 0.88), (0.95, 0.97, 1.00)),
        'red_panda_fur':   ((0.80, 0.42, 0.18), (0.15, 0.10, 0.06), (0.90, 0.72, 0.50)),
        'red_panda':       ((0.80, 0.42, 0.18), (0.15, 0.10, 0.06), (0.90, 0.72, 0.50)),
        'fluffy':          ((0.98, 0.98, 1.00), (0.06, 0.06, 0.06), (1.00, 0.97, 0.90)),
        'young':           ((0.99, 0.99, 1.00), (0.25, 0.25, 0.30), (1.00, 0.98, 0.92)),
        'elder':           ((0.88, 0.88, 0.86), (0.20, 0.20, 0.22), (0.92, 0.90, 0.85)),
        'golden':          ((0.95, 0.82, 0.40), (0.50, 0.32, 0.08), (1.00, 0.92, 0.65)),
        'golden_fur':      ((0.95, 0.82, 0.40), (0.50, 0.32, 0.08), (1.00, 0.92, 0.65)),
        # ── Fur texture styles ────────────────────────────────────────────
        'sleek':           ((0.97, 0.97, 0.99), (0.05, 0.05, 0.07), (1.00, 0.99, 0.95)),
        'shaggy':          ((0.94, 0.92, 0.90), (0.12, 0.10, 0.10), (0.98, 0.95, 0.88)),
        'curly':           ((0.98, 0.96, 0.94), (0.10, 0.08, 0.08), (1.00, 0.96, 0.88)),
        'wavy':            ((0.96, 0.96, 0.98), (0.09, 0.09, 0.11), (1.00, 0.97, 0.90)),
        'wispy':           ((0.99, 0.99, 1.00), (0.14, 0.14, 0.16), (1.00, 0.98, 0.93)),
        'spiky':           ((0.95, 0.95, 0.97), (0.05, 0.05, 0.06), (0.99, 0.97, 0.91)),
        'braided':         ((0.93, 0.91, 0.89), (0.11, 0.09, 0.09), (0.97, 0.94, 0.86)),
        'woolly':          ((0.95, 0.93, 0.91), (0.14, 0.12, 0.12), (0.99, 0.95, 0.87)),
        'velvet':          ((0.96, 0.94, 0.96), (0.06, 0.04, 0.08), (1.00, 0.96, 0.98)),
        'plush':           ((0.98, 0.97, 0.97), (0.10, 0.08, 0.09), (1.00, 0.97, 0.94)),
        'tufted':          ((0.95, 0.95, 0.98), (0.10, 0.10, 0.12), (0.99, 0.97, 0.91)),
        'feathered':       ((0.97, 0.97, 0.99), (0.06, 0.06, 0.08), (1.00, 0.98, 0.94)),
        'silky':           ((0.99, 0.98, 1.00), (0.07, 0.06, 0.10), (1.00, 0.99, 0.96)),
        'windswept':       ((0.96, 0.96, 0.98), (0.08, 0.08, 0.10), (1.00, 0.97, 0.91)),
        'mohawk':          ((0.96, 0.96, 0.98), (0.06, 0.06, 0.08), (1.00, 0.97, 0.91)),
        'frosted':         ((0.93, 0.95, 0.99), (0.58, 0.64, 0.82), (0.96, 0.98, 1.00)),
        'metallic':        ((0.82, 0.84, 0.88), (0.30, 0.32, 0.38), (0.88, 0.90, 0.94)),
        'spotted':         ((0.97, 0.95, 0.93), (0.15, 0.12, 0.10), (1.00, 0.96, 0.90)),
        'striped':         ((0.97, 0.97, 0.99), (0.08, 0.08, 0.10), (1.00, 0.97, 0.92)),
        # ── Colour variants (FUR_COLOR category uses same dict) ───────────
        'brown':           ((0.62, 0.42, 0.26), (0.22, 0.12, 0.06), (0.80, 0.60, 0.40)),
        'cinnamon':        ((0.76, 0.52, 0.28), (0.30, 0.16, 0.06), (0.88, 0.70, 0.48)),
        'silver':          ((0.82, 0.84, 0.88), (0.32, 0.34, 0.40), (0.90, 0.90, 0.92)),
        'midnight':        ((0.18, 0.18, 0.22), (0.04, 0.04, 0.06), (0.28, 0.28, 0.34)),
        'phantom':         ((0.22, 0.20, 0.26), (0.06, 0.04, 0.08), (0.32, 0.30, 0.36)),
        'shadow':          ((0.20, 0.20, 0.24), (0.05, 0.05, 0.07), (0.30, 0.28, 0.32)),
        'arctic_white':    ((1.00, 1.00, 1.00), (0.78, 0.80, 0.88), (1.00, 1.00, 1.00)),
        'starlight':       ((0.92, 0.92, 1.00), (0.55, 0.55, 0.85), (0.96, 0.96, 1.00)),
        'ice_crystal':     ((0.88, 0.94, 1.00), (0.50, 0.65, 0.90), (0.92, 0.96, 1.00)),
        'cotton_candy':    ((1.00, 0.80, 0.88), (0.80, 0.45, 0.62), (1.00, 0.88, 0.94)),
        'cherry_blossom':  ((1.00, 0.82, 0.88), (0.85, 0.40, 0.58), (1.00, 0.90, 0.94)),
        'sakura':          ((1.00, 0.84, 0.90), (0.82, 0.42, 0.60), (1.00, 0.92, 0.95)),
        'rose_gold':       ((0.95, 0.76, 0.70), (0.60, 0.36, 0.30), (1.00, 0.86, 0.80)),
        'lavender':        ((0.82, 0.72, 0.92), (0.42, 0.28, 0.65), (0.90, 0.82, 0.96)),
        'sunset_orange':   ((0.96, 0.64, 0.30), (0.55, 0.22, 0.06), (1.00, 0.80, 0.55)),
        'ember':           ((0.90, 0.50, 0.22), (0.48, 0.18, 0.05), (0.98, 0.70, 0.44)),
        'copper':          ((0.78, 0.52, 0.30), (0.40, 0.22, 0.08), (0.88, 0.68, 0.48)),
        'emerald':         ((0.20, 0.70, 0.40), (0.05, 0.30, 0.14), (0.40, 0.82, 0.58)),
        'mossy':           ((0.48, 0.62, 0.30), (0.18, 0.28, 0.10), (0.60, 0.72, 0.44)),
        'ocean_blue':      ((0.28, 0.58, 0.88), (0.10, 0.28, 0.58), (0.48, 0.72, 0.96)),
        'glacial':         ((0.70, 0.86, 0.96), (0.30, 0.58, 0.80), (0.82, 0.92, 1.00)),
        'neon_green':      ((0.40, 0.98, 0.40), (0.10, 0.55, 0.10), (0.70, 1.00, 0.70)),
        'electric':        ((0.60, 0.80, 1.00), (0.20, 0.40, 0.90), (0.80, 0.90, 1.00)),
        'thunder':         ((0.50, 0.52, 0.68), (0.20, 0.22, 0.45), (0.65, 0.65, 0.80)),
        # ── Fantasy / special ─────────────────────────────────────────────
        'rainbow':         ((1.00, 0.50, 0.50), (0.50, 0.00, 0.50), (1.00, 0.80, 0.50)),
        'galaxy':          ((0.18, 0.10, 0.30), (0.55, 0.20, 0.75), (0.30, 0.18, 0.48)),
        'cosmic':          ((0.12, 0.08, 0.25), (0.48, 0.15, 0.68), (0.22, 0.14, 0.38)),
        'starweave':       ((0.14, 0.10, 0.28), (0.60, 0.25, 0.80), (0.26, 0.18, 0.44)),
        'holographic':     ((0.90, 0.85, 1.00), (0.55, 0.45, 0.90), (0.96, 0.92, 1.00)),
        'aurora':          ((0.30, 0.85, 0.75), (0.10, 0.50, 0.85), (0.55, 0.92, 0.80)),
        'phoenix':         ((0.95, 0.45, 0.10), (0.55, 0.10, 0.02), (1.00, 0.70, 0.35)),
        'bamboo_spirit':   ((0.60, 0.80, 0.40), (0.20, 0.48, 0.15), (0.78, 0.90, 0.60)),
        'crystalline':     ((0.88, 0.96, 1.00), (0.45, 0.70, 0.92), (0.94, 0.98, 1.00)),
        'pixelated':       ((0.85, 0.85, 0.88), (0.15, 0.15, 0.18), (0.95, 0.92, 0.88)),
        'diamond':         ((0.92, 0.96, 1.00), (0.60, 0.72, 0.90), (0.96, 0.98, 1.00)),
        'volcanic':        ((0.25, 0.08, 0.04), (0.80, 0.30, 0.05), (0.40, 0.15, 0.08)),
    }

    def set_fur_style(self, style_id: str) -> None:
        """
        Apply a fur-style preset to the panda's body colors.

        Args:
            style_id: One of the keys in _FUR_STYLE_COLORS (e.g. 'albino', 'snow_panda').
                      Unknown ids are silently treated as 'classic'.
        """
        if hasattr(style_id, 'value'):
            style_id = style_id.value
        self._fur_style = str(style_id)
        body_rgb, accent_rgb, belly_rgb = self._FUR_STYLE_COLORS.get(
            self._fur_style, self._FUR_STYLE_COLORS['classic']
        )
        self.custom_colors['body']   = list(body_rgb)
        self.custom_colors['accent'] = list(accent_rgb)
        # belly colour stored separately so _draw_panda can use it
        self.custom_colors['belly']  = list(belly_rgb)
        logger.debug(f"Panda fur style set to '{self._fur_style}'")
        self.update()

    # Hair style id → description string (used for debug logging).
    # Actual rendering is via head-top accessory spheres drawn in _draw_panda_head_hair().
    _HAIR_STYLE_NAMES: dict = {
        'hair_wild_mane':   'Wild Mane',
        'hair_mohawk':      'Punk Mohawk',
        'hair_top_knot':    'Top Knot',
        'hair_spiked':      'Spiked Tips',
        'hair_bowl_cut':    'Bowl Cut',
        'hair_braid':       'Side Braid',
        'hair_afro':        'Fur Afro',
        'hair_dreadlocks':  'Dreads',
    }

    def set_hair_style(self, style_id: str) -> None:
        """
        Apply a hair-style to the panda's head.

        The hair style is stored and rendered in _draw_panda_head_hair() which is
        called from _draw_panda() after the ear/eye/snout pass.

        Args:
            style_id: One of the keys in _HAIR_STYLE_NAMES.
                      Pass 'none' or '' to remove hair style.
        """
        if hasattr(style_id, 'value'):
            style_id = style_id.value
        self._hair_style = str(style_id)
        name = self._HAIR_STYLE_NAMES.get(self._hair_style, self._hair_style)
        logger.debug(f"Panda hair style set to '{name}'")
        self.update()
    
    def set_trail(self, trail_type: str, trail_data: dict):
        """
        Set motion trail/effect for panda.
        
        Args:
            trail_type: Type of trail ('sparkle', 'rainbow', 'fire', 'ice', 'none').
                        Also accepts UI display names ('Dots', 'Line', 'Glow', 'Particles', 'None').
            trail_data: Configuration dict for trail (color, intensity, duration, etc.)
        """
        # Normalize UI display names → internal trail type strings
        _type_map = {
            'none': 'none', 'None': 'none', '': 'none',
            'dots': 'sparkle', 'Dots': 'sparkle',
            'line': 'rainbow', 'Line': 'rainbow',
            'glow': 'fire',    'Glow': 'fire',
            'particles': 'ice', 'Particles': 'ice',
        }
        trail_type = _type_map.get(trail_type, trail_type.lower() if trail_type else 'none')

        self.trail_type = trail_type
        self.trail_data = trail_data
        self.trail_enabled = trail_type != 'none'
        
        # Clear existing trail particles when changing type
        self.trail_particles = []
        
        logger.debug(f"Panda trail set to {trail_type} with data {trail_data}")
        self.update()
    
    def _update_trail(self):
        """Update trail particle system."""
        if not self.trail_enabled or self.trail_type == 'none':
            return
        
        # Add new particle at current position whenever the panda is moving
        if abs(self.velocity_x) > 0.002 or abs(self.velocity_z) > 0.002:
            particle = {
                'pos': [self.panda_x, self.panda_y + 0.3, self.panda_z],
                'life': 1.0,  # Life from 1.0 to 0.0
                'color': self._get_trail_color()
            }
            self.trail_particles.append(particle)
        
        # Update existing particles
        for particle in self.trail_particles[:]:
            particle['life'] -= 0.02  # Decay rate
            if particle['life'] <= 0:
                self.trail_particles.remove(particle)
        
        # Limit particle count
        if len(self.trail_particles) > self.max_trail_particles:
            self.trail_particles = self.trail_particles[-self.max_trail_particles:]
    
    def _get_trail_color(self):
        """Get color for trail particle based on trail type."""
        if self.trail_type == 'sparkle':
            return [1.0, 1.0, 0.0]  # Yellow
        elif self.trail_type == 'rainbow':
            # Cycle through rainbow colors
            hue = (time.time() * 2.0) % 1.0
            return self._hsv_to_rgb(hue, 1.0, 1.0)
        elif self.trail_type == 'fire':
            return [1.0, 0.3, 0.0]  # Orange/red
        elif self.trail_type == 'ice':
            return [0.3, 0.6, 1.0]  # Light blue
        else:
            return self.trail_data.get('color', [1.0, 1.0, 1.0])
    
    @staticmethod
    def _hsv_to_rgb(h, s, v):
        """Convert HSV color to RGB."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return [r, g, b]
    
    def _draw_trail(self):
        """Draw trail particles."""
        if not self.trail_enabled or not self.trail_particles:
            return
        
        try:
            glDisable(GL_LIGHTING)
        except Exception:
            pass  # not available if lighting not initialized
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPointSize(5.0)
        
        glBegin(GL_POINTS)
        for particle in self.trail_particles:
            color = particle['color']
            alpha = particle['life']  # Fade out as life decreases
            glColor4f(color[0], color[1], color[2], alpha)
            glVertex3f(particle['pos'][0], particle['pos'][1], particle['pos'][2])
        glEnd()
        
        try:
            glEnable(GL_LIGHTING)
        except Exception:
            pass  # not available if lighting not initialized
    
    # ── Unified public interface (matches main.py call sites) ──────────────────

    def set_animation(self, animation: str) -> None:
        """Alias for set_animation_state — used by main.py callback."""
        self.set_animation_state(animation)

    def preview_item(self, item_id: str) -> None:
        """
        Temporarily show an inventory item near the panda (hover/inspect).

        Adds a floating 3D item above the panda's position so the user can
        see what it looks like before equipping it.  The item is removed the
        next time preview_item is called or when equip_item is called.

        Args:
            item_id: Inventory item identifier string.
        """
        # Clear any previous preview item using the tracked reference (O(1))
        if self._preview_item_ref is not None and self._preview_item_ref in self.items_3d:
            self.items_3d.remove(self._preview_item_ref)
        self._preview_item_ref = None

        if not item_id:
            self.update()
            return

        # Map common item categories to 3D item types
        _id = str(item_id).lower()
        if any(k in _id for k in ('sword', 'axe', 'staff', 'weapon')):
            item_type = 'weapon'
        elif any(k in _id for k in ('hat', 'crown', 'helmet')):
            item_type = 'hat'
        elif any(k in _id for k in ('food', 'bamboo', 'apple', 'cake')):
            item_type = 'food'
        elif any(k in _id for k in ('toy', 'ball', 'plush')):
            item_type = 'toy'
        else:
            item_type = 'toy'   # generic fallback — renders as floating cube

        preview_item = {
            '_preview': True,
            'type': item_type,
            'id': item_id,
            'x': self.panda_x + 0.6,
            'y': self.panda_y + 1.2,
            'z': self.panda_z,
        }
        self._preview_item_ref = preview_item
        self.items_3d.append(preview_item)
        logger.debug("Previewing item: %s as %s", item_id, item_type)
        self.update()

    def equip_item(self, item_data) -> None:
        """
        Equip a clothing/accessory item onto the panda.

        Delegates to equip_clothing() using the item's slot information.
        Also clears any active preview for the same item.

        Args:
            item_data: dict with at least 'id' key, optionally 'slot' and 'type'.
                       May also be a plain string item identifier, or a
                       CustomizationItem dataclass instance.
        """
        if isinstance(item_data, str):
            item_data = {'id': item_data}
        elif not isinstance(item_data, dict):
            # CustomizationItem or similar dataclass — convert to dict
            _raw = item_data
            item_data = {
                'id':   getattr(_raw, 'id', ''),
                'type': getattr(_raw, 'clothing_type', '') or getattr(_raw, 'id', ''),
                'slot': '',
            }
            # Map category → slot if possible
            try:
                _cat_val = getattr(getattr(_raw, 'category', None), 'value', '')
                _CAT_SLOT = {
                    'hat': 'hat', 'shoes': 'boots', 'accessory': 'accessory',
                    'gloves': 'gloves', 'armor': 'armor', 'boots': 'boots',
                    'belt': 'belt', 'backpack': 'backpack', 'clothing': 'shirt',
                    'weapon': 'held_right', 'food': 'held_left', 'toy': 'held_right',
                }
                item_data['slot'] = _CAT_SLOT.get(_cat_val, '')
            except Exception:
                pass

        item_id = item_data.get('id', '')
        slot = item_data.get('slot', '')
        item_type = str(item_data.get('type', item_id)).lower()

        # Clear preview if it's the same item (O(1) via tracked ref)
        if (self._preview_item_ref is not None
                and self._preview_item_ref.get('id') == item_id
                and self._preview_item_ref in self.items_3d):
            self.items_3d.remove(self._preview_item_ref)
            self._preview_item_ref = None

        # Determine clothing slot from type/id heuristics
        if not slot:
            if any(k in item_type for k in ('hat', 'crown', 'helmet', 'bow')):
                slot = 'hat'
            elif any(k in item_type for k in ('shirt', 'jacket', 'top', 'hoodie', 'tshirt', 't-shirt')):
                slot = 'shirt'
            elif any(k in item_type for k in ('pants', 'skirt', 'bottom', 'trouser')):
                slot = 'pants'
            elif any(k in item_type for k in ('glasses', 'goggles', 'sunglasses')):
                slot = 'glasses'
            elif any(k in item_type for k in ('armor', 'chestplate', 'breastplate', 'cape', 'cloak', 'robe')):
                slot = 'armor'
            elif any(k in item_type for k in ('boot', 'shoe', 'sandal', 'slipper')):
                slot = 'boots'
            elif any(k in item_type for k in ('belt', 'waistband', 'sash')):
                slot = 'belt'
            elif any(k in item_type for k in ('backpack', 'bag', 'satchel', 'knapsack')):
                slot = 'backpack'
            elif any(k in item_type for k in ('sword', 'axe', 'staff', 'weapon', 'gun', 'blade',
                                               'katana', 'wand', 'spear', 'hammer', 'mace',
                                               'dagger', 'lance', 'halberd', 'pistol', 'rifle',
                                               'cannon', 'blaster', 'bow', 'longbow', 'crossbow',
                                               'archer', 'blowgun', 'bamboo', 'held_right')):
                slot = 'held_right'
            elif any(k in item_type for k in ('held_left', 'shield', 'buckler')):
                slot = 'held_left'
            elif any(k in item_type for k in ('gloves', 'gauntlet', 'mitten')):
                slot = 'gloves'
            elif any(k in item_type for k in ('food', 'fish', 'apple', 'cookie', 'toy', 'ball', 'flower')):
                slot = 'held_right'
            else:
                slot = 'accessory'

        self.equip_clothing(slot, item_data)
        logger.debug("Equipped item %r into slot %r", item_id, slot)
        self.update()

    def update_appearance(self) -> None:
        """Trigger a full redraw of the panda widget.  Called by CustomizationPanelQt."""
        self.update()

    # ── Info ───────────────────────────────────────────────────────────────────

    def get_info(self) -> dict:
        """
        Get current panda widget information.
        
        Returns:
            Dictionary with widget state information
        """
        return {
            'animation_state': self.animation_state,
            'position': (self.panda_x, self.panda_y, self.panda_z),
            'camera_distance': self.camera_distance,
            'camera_angle': (self.camera_angle_x, self.camera_angle_y),
            'item_count': len(self.items_3d),
            'autonomous_mode': self.autonomous_mode,
            'has_weapon': self.equipped_weapon is not None,
            'clothing_slots': list(self.clothing.keys())
        }

    def get_idle_sub_state(self) -> str:
        """Return the active idle sub-state (e.g. 'grooming', 'daydream'), or '' if none."""
        return getattr(self, '_idle_sub_state', '')


# Export PandaOpenGLWidget as the primary widget interface
# Direct usage is now preferred over the deprecated bridge wrapper
PandaWidget = PandaOpenGLWidget if QT_AVAILABLE else None
