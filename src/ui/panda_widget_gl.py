"""
OpenGL Panda Widget - Hardware-accelerated 3D panda companion
Qt OpenGL rendering for smooth 60fps animation, real lighting, shadows, and 3D interactions.
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import math
import random
import time
from typing import Optional, Callable, Tuple, List
from enum import Enum

try:
    from PyQt6.QtWidgets import QWidget, QApplication
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtCore import QTimer, Qt, QPoint, pyqtSignal, QState, QStateMachine
    from PyQt6.QtGui import QMouseEvent, QSurfaceFormat
    from OpenGL.GL import *
    from OpenGL.GLU import *
    import numpy as np
    QT_AVAILABLE = True
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
    'crawling':      -42.0,   # body pitched forward, nose toward ground
    'climbing_wall': -80.0,   # near-vertical, claws on wall
    'falling_back':   85.0,   # on back, legs up
    'sleeping':       12.0,   # slight slump forward
    'sitting_back': -10.0,   # slight backward lean when sitting upright
    'rolling':       30.0,   # body pitching as it rolls
    'hanging_ceiling': 175.0, # nearly inverted, gripping ceiling
    'hanging_window_edge': -55.0,  # body angled forward/down, arms reaching up
}

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
    'sarcastic':    'sarcastic',
    'rage':         'rage',
    'drunk':        'drunk',
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
    'bored':        'idle',
    # New quadruped states accessible via mood
    'climbing':     'climbing_wall',
    'falling':      'falling_back',
    'crawling':     'crawling',
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
    HEAD_RADIUS = 0.4
    BODY_WIDTH = 0.5
    BODY_HEIGHT = 0.6
    ARM_LENGTH = 0.4
    LEG_LENGTH = 0.35
    EAR_SIZE = 0.15

    # States that receive a micro-hold pause before transitioning to idle
    HOLD_STATES: frozenset = frozenset({
        'waving', 'celebrating', 'jumping',
        'crawling', 'climbing_wall', 'falling_back',
        'sitting_back', 'rolling', 'hanging_ceiling', 'hanging_window_edge',
    })
    
    # Physics constants
    GRAVITY = 9.8
    BOUNCE_DAMPING = 0.6
    FRICTION = 0.92
    
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
        
        # Set OpenGL surface format for optimal rendering
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)  # OpenGL 3.3
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setSamples(4)  # 4x MSAA for antialiasing
        fmt.setDepthBufferSize(24)
        fmt.setStencilBufferSize(8)
        self.setFormat(fmt)
        
        # Panda state
        self.panda = panda_character
        
        # Animation state
        self.animation_frame = 0
        self.animation_state = 'idle'
        self.facing = 'front'
        
        # Position and rotation (in 3D space)
        self.panda_x = 0.0
        self.panda_y = 0.0
        self.panda_z = 0.0
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0
        
        # Velocity for physics
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.velocity_z = 0.0
        self.angular_velocity = 0.0
        
        # Camera settings
        self.camera_distance = 3.0
        self.camera_angle_x = 20.0
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
            'hat': None,       # Hat on head
            'shirt': None,     # Shirt on body
            'pants': None,     # Pants on legs
            'glasses': None,   # Glasses on face
            'accessory': None, # Other accessories
            'held_right': None,  # Item held in right paw
            'held_left': None,   # Item held in left paw
            'gloves': None,      # Gloves on paws
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
        self.target_position = None  # Where panda is walking to
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

        # ── Cursor awareness ─────────────────────────────────────────────────
        self._cursor_wpos   = None      # QPoint in widget space (None = unknown)
        self._look_yaw      = 0.0       # horizontal head-look offset (degrees), eased
        self._look_pitch    = 0.0       # vertical offset
        self._look_yaw_tgt  = 0.0
        self._look_pitch_tgt = 0.0
        self.setMouseTracking(True)

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
        except Exception as e:
            logger.error(f"OpenGL initialization failed: {e}", exc_info=True)
            self.gl_initialized = False
            # Emit signal on next event-loop tick so callers can swap in 2D fallback
            QTimer.singleShot(0, lambda: self.gl_failed.emit(str(e)))

    def _do_initialize_gl(self):
        """Actual GL initialization — called inside a try/except in initializeGL()."""
        # Enable depth testing for 3D
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        
        # Enable face culling for performance
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        
        # Enable smooth shading
        glShadeModel(GL_SMOOTH)
        
        # Enable antialiasing
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Set background color (transparent or light color)
        glClearColor(0.95, 0.95, 0.98, 1.0)
        
        # Setup lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Set light properties
        glLightfv(GL_LIGHT0, GL_POSITION, self.light_position)
        glLightfv(GL_LIGHT0, GL_AMBIENT, self.ambient_light)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, self.diffuse_light)
        glLightfv(GL_LIGHT0, GL_SPECULAR, self.specular_light)
        
        # Material properties for specular highlights
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 50.0)
        
        # Initialize shadow mapping
        self._init_shadow_mapping()
        
        self.gl_initialized = True
        logger.info("OpenGL initialized successfully")
    
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
        
        glViewport(0, 0, width, height)
        
        # Setup projection matrix
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height
        gluPerspective(45.0, aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render the 3D scene."""
        if not self.gl_initialized:
            return  # GL init failed or hasn't run yet — don't attempt GL calls
        current_time = time.time()
        elapsed = current_time - self.last_frame_time
        if elapsed < self.FRAME_TIME:
            return  # Skip frame to maintain 60 FPS cap
        self.last_frame_time = current_time
        
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Render shadows first (if supported)
        if self.shadow_fbo:
            self._render_shadows()
        
        # Setup camera
        glLoadIdentity()
        glTranslatef(0.0, -0.5, -self.camera_distance)
        glRotatef(self.camera_angle_x, 1.0, 0.0, 0.0)
        glRotatef(self.camera_angle_y, 0.0, 1.0, 0.0)
        
        # Update light position relative to camera
        glLightfv(GL_LIGHT0, GL_POSITION, self.light_position)
        
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
        glDisable(GL_LIGHTING)
        
        # Render scene geometry (depth only)
        glPushMatrix()
        glTranslatef(self.panda_x, self.panda_y, self.panda_z)
        glRotatef(self.rotation_y, 0.0, 1.0, 0.0)
        self._draw_panda_geometry_only()
        glPopMatrix()
        
        # Restore state
        glEnable(GL_LIGHTING)
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
        """Draw ground plane for spatial reference."""
        glDisable(GL_LIGHTING)
        glColor4f(0.85, 0.85, 0.85, 0.5)
        
        glBegin(GL_QUADS)
        size = 5.0
        glVertex3f(-size, -1.0, -size)
        glVertex3f(size, -1.0, -size)
        glVertex3f(size, -1.0, size)
        glVertex3f(-size, -1.0, size)
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def _draw_panda(self):
        """Draw detailed 3D panda character with all body parts."""
        bob = self._get_body_bob()
        limb = self._get_limb_positions()
        t  = self.animation_frame           # raw frame counter used for trig

        # Fetch fur colours once — avoids repeated dict lookups per frame
        body_col   = self.custom_colors['body']
        belly_col  = self.custom_colors['belly']
        accent_col = self.custom_colors['accent']

        # Apply squash/stretch to the torso
        sy = self._squash_y

        # ── Torso ────────────────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(self.panda_x, 0.28 + bob, self.panda_z)
        glRotatef(self.rotation_y, 0.0, 1.0, 0.0)
        # Quadruped body pitch (crawling/climbing/falling_back)
        if abs(self._body_pitch_cur) > 0.5:
            glRotatef(self._body_pitch_cur, 1.0, 0.0, 0.0)

        # Belly — creamy white underside; belly jiggle on Y (height oscillation)
        glPushMatrix()
        glScalef(self.BODY_WIDTH * 0.65,
                 self.BODY_HEIGHT * 0.55 * sy * self._belly_y,
                 self.BODY_WIDTH * 0.50)
        glColor3f(*belly_col)
        self._draw_sphere(1.0, 24, 24)
        glPopMatrix()

        # Main body — colour from custom_colors['body'] (fur style)
        # Apply subtle specular sheen to simulate fur gloss
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.25, 0.25, 0.25, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 14.0)
        glPushMatrix()
        glScalef(self.BODY_WIDTH, self.BODY_HEIGHT * sy, self.BODY_WIDTH * 0.78)
        glColor3f(*body_col)
        self._draw_sphere(1.0, 24, 24)
        glPopMatrix()
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 50.0)

        # Fur layer — belly_y also applied to Y so fur follows belly motion
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPushMatrix()
        glScalef(self.BODY_WIDTH * 1.03,
                 self.BODY_HEIGHT * 1.02 * sy * self._belly_y,
                 self.BODY_WIDTH * 0.81)
        glColor4f(1.0, 1.0, 1.0, 0.18)
        self._draw_sphere(1.0, 16, 16)
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
        for sx in (-self.BODY_WIDTH * 0.70, self.BODY_WIDTH * 0.70):
            glPushMatrix()
            glTranslatef(sx, 0.12, -self.BODY_WIDTH * 0.15)
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
        # Real pandas have prominent black oval patches on each hip / upper thigh
        for hx in (-self.BODY_WIDTH * 0.78, self.BODY_WIDTH * 0.78):
            glPushMatrix()
            glTranslatef(hx, -self.BODY_HEIGHT * 0.22 * sy, 0.0)
            glScalef(0.36, 0.42 * sy, 0.30)
            glColor3f(*accent_col)
            self._draw_sphere(1.0, 12, 12)
            glPopMatrix()

        # ── Legs ─────────────────────────────────────────────────────────────
        self._draw_panda_legs(limb, bob, t)

        # ── Arms ─────────────────────────────────────────────────────────────
        self._draw_panda_arms(limb, bob, t)

        # ── Tail (small white puff, slightly larger than before) ─────────────
        glPushMatrix()
        glTranslatef(0.0, -0.05, -self.BODY_WIDTH * 0.78)
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

        glPopMatrix()   # end torso matrix

        # ── Head (separate matrix so it can tilt independently) ───────────────
        # Head rotation = breathing tilt + head lag (follow-through) + resting asymmetry + look
        tilt = (4.0 * math.sin(t * 0.04) +
                self._head_lag +
                self._asym.get('head_tilt_rest', 0.0) +
                self._eye_head_yaw * 0.5)
        glPushMatrix()
        glTranslatef(self.panda_x, 0.90 + bob * 1.1, self.panda_z)
        glRotatef(self.rotation_y + self._eye_head_yaw * 0.4, 0.0, 1.0, 0.0)
        glRotatef(tilt, 0.0, 0.0, 1.0)
        glRotatef(self._eye_head_pitch * 0.5, 1.0, 0.0, 0.0)

        # "Whoa face" — slight backwards lean
        if self._whoa_t > 0.0:
            lean = min(self._whoa_t / 0.5, 1.0) * -8.0
            glRotatef(lean, 1.0, 0.0, 0.0)

        # Main skull — subtle fur sheen, colour from fur style
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.22, 0.22, 0.22, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 12.0)
        glColor3f(*body_col)
        self._draw_sphere(self.HEAD_RADIUS, 28, 28)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 50.0)

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

        # Fur fuzz over skull
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

        glPopMatrix()   # end head matrix

        # ── Clothing & weapons ────────────────────────────────────────────────
        self._draw_clothing()
        self._draw_weapon()
        self._draw_held_items()

    def _draw_panda_geometry_only(self):
        """Draw simplified panda geometry for shadow pass (no colour changes)."""
        glPushMatrix()
        glTranslatef(self.panda_x, 0.28, self.panda_z)
        glScalef(self.BODY_WIDTH, self.BODY_HEIGHT, self.BODY_WIDTH * 0.78)
        self._draw_sphere(1.0, 10, 10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(self.panda_x, 0.90, self.panda_z)
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
        eye_z  = self.HEAD_RADIUS * 0.74

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

            blink_s = blink * wide_factor * squint

            # ── Black fur patch ────────────────────────────────────────────
            glPushMatrix()
            glTranslatef(eye_x, eye_y, eye_z)
            glScalef(1.0, blink_s, 1.0)
            glRotatef(side * -12.0, 0.0, 0.0, 1.0)
            glScalef(1.25, 0.90, 0.60)
            glColor3f(*self._get_color('accent'))
            self._draw_sphere(0.118, 16, 16)
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
            glDisable(GL_LIGHTING)
            glColor3f(1.0, 1.0, 1.0)
            self._draw_sphere(0.009, 8, 8)
            glEnable(GL_LIGHTING)
            glPopMatrix()

    def _get_blink_scale(self, t):
        """
        Return vertical eye scale (1.0 = fully open, ~0.05 = closed).
        Uses time-based blink phase set by _update_subsystems().
        phase 0–1: closing (ease-in),  phase 1–2: opening (ease-out).
        Fatigue droops the eye (keeps scale slightly below 1.0 when open).
        """
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
        """Draw muzzle, nose tip, philtrum and teeth."""
        # Muzzle — off-white ellipsoid
        glPushMatrix()
        glTranslatef(0.0, -0.065, self.HEAD_RADIUS * 0.84)
        glScalef(1.10, 0.72, 0.55)
        glColor3f(0.96, 0.95, 0.91)
        self._draw_sphere(0.138, 18, 18)
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
        glPopMatrix()

        # Philtrum groove — dark line below nose
        glPushMatrix()
        glTranslatef(0.0, -0.068, self.HEAD_RADIUS * 0.94)
        glScalef(0.25, 1.10, 0.30)
        glColor3f(0.55, 0.45, 0.42)
        self._draw_sphere(0.022, 8, 8)
        glPopMatrix()

        # Mouth line — thin dark crescent (two corner spheres + centre dip)
        for mx, my in [(-0.048, -0.094), (0.0, -0.100), (0.048, -0.094)]:
            glPushMatrix()
            glTranslatef(mx, my, self.HEAD_RADIUS * 0.91)
            glColor3f(0.30, 0.22, 0.20)
            self._draw_sphere(0.013, 8, 8)
            glPopMatrix()

        # Teeth (two white incisors, visible when mouth slightly open)
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
    def _draw_panda_arms(self, limb, bob, t=0):
        """Draw arms with follow-through overshoot, uneven breathing, paw/claws."""
        arm_y   = 0.30 + bob
        arm_x   = self.BODY_WIDTH + 0.06
        ac = self._get_color('accent')   # fur-style accent colour for arm patches

        swing_idle = 5.0 * math.sin(t * 0.030)  # tiny idle sway

        # Asymmetric breathing offset (uneven arm sway amplitude)
        breath_offset = [self._asym.get('breath_l_offset', 0.0),
                         self._asym.get('breath_r_offset', 0.0)]

        for idx, (side, key) in enumerate(((-1, 'left_arm_angle'), (1, 'right_arm_angle'))):
            angle = (limb.get(key, 0)
                     + swing_idle * side
                     + self._arm_over[idx]           # follow-through overshoot
                     + breath_offset[idx] * 180.0)   # tiny uneven breathing

            glPushMatrix()
            glTranslatef(side * arm_x, arm_y + 0.06, 0.0)
            glRotatef(-side * 8, 0.0, 0.0, 1.0)   # arms hang slightly outward
            glRotatef(angle, 1.0, 0.0, 0.0)

            # Upper arm — thick ovoid in accent colour
            glPushMatrix()
            glScalef(0.115, 0.200, 0.115)
            glTranslatef(0.0, -0.50, 0.0)
            glColor3f(*ac)
            self._draw_sphere(1.0, 16, 16)
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
            self._draw_sphere(0.082, 14, 14)
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
        leg_y = -0.04 + bob
        leg_x = 0.20
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
            self._draw_sphere(1.0, 16, 16)
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
    
    def _draw_food_item(self, item):
        """Draw food item in 3D."""
        # Example: Draw as colored sphere
        color = item.get('color', [0.8, 0.2, 0.2])
        glColor3f(*color)
        self._draw_sphere(0.1, 12, 12)
    
    def _draw_toy_item(self, item):
        """Draw toy item in 3D."""
        # Example: Draw as colored cube
        color = item.get('color', [0.2, 0.2, 0.8])
        glColor3f(*color)
        size = 0.15
        self._draw_cube(size)
    
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

        # Flinch → trigger quick blink
        if self._flinch_t > 0.1 and self._blink_phase == 0.0:
            self._blink_phase = 0.001

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

    # ─── Audio helper ─────────────────────────────────────────────────────────
    # Map logical sound names → actual WAV filenames in resources/sounds/.
    # This allows call-sites to use short, descriptive names without caring
    # about the exact filename on disk.
    _SOUND_ALIASES: dict = {
        'boop':       'panda_boop',
        'thump':      'panda_thud',
        'landing':    'panda_thud',
        'click':      'click',
        'yawn':       'panda_sleepy_yawn',
        'big_yawn':   'panda_big_yawn',
        'tired_yawn': 'panda_tired_yawn',
        'wake_yawn':  'panda_wake_yawn',
        'giggle':     'panda_giggle',
        'chomp':      'panda_chomp',
        'plop':       'panda_plop',
        'poke':       'panda_poke',
        'purr':       'panda_purr',
        'snore':      'panda_snore',
        'achievement':'achievement',
        'error':      'error',
        'notification':'notification',
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
        self._prev_state    = self.animation_state
        self._blend_alpha   = 0.0
        self._blend_start_t = time.time()
        self.animation_state = state
        self.animation_changed.emit(state)

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
                base  = frame * 0.160
                swing = 32.0 * math.sin(base) + 5.0 * math.sin(base * 3) / 3.0
                pos['left_arm_angle']  =  swing
                pos['right_arm_angle'] = -swing
                pos['left_leg_angle']  = -swing
                pos['right_leg_angle'] =  swing

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

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press — play boop, reset boredom, surprised face."""
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
                # Drag panda
                self.panda_x += delta.x() * 0.01
                self.panda_y -= delta.y() * 0.01
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
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        self.camera_distance -= delta * 0.001
        self.camera_distance = max(1.0, min(10.0, self.camera_distance))
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
        """
        Equip clothing item in 3D.
        
        Args:
            slot: 'hat', 'shirt', 'pants', 'glasses', 'accessory'
            clothing_item: Clothing data (name, color, type)
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
        """Draw shirt on panda's body."""
        glPushMatrix()
        # Position on body
        glTranslatef(0.0, 0.3, 0.0)
        
        # Get shirt color
        color = shirt_data.get('color', [0.2, 0.2, 0.8])
        glColor3f(*color)
        
        # Draw shirt (slightly larger than body)
        glScalef(self.BODY_WIDTH * 1.05, self.BODY_HEIGHT * 0.8, self.BODY_WIDTH * 0.85)
        self._draw_sphere(1.0, 16, 16)
        
        glPopMatrix()
    
    def _draw_pants(self, pants_data):
        """Draw pants on panda's legs."""
        # Get pants color
        color = pants_data.get('color', [0.3, 0.3, 0.3])
        glColor3f(*color)
        
        # Left leg pants
        glPushMatrix()
        glTranslatef(-0.2, -0.1, 0.0)
        glScalef(0.16, self.LEG_LENGTH, 0.16)
        glTranslatef(0.0, -0.5, 0.0)
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()
        
        # Right leg pants
        glPushMatrix()
        glTranslatef(0.2, -0.1, 0.0)
        glScalef(0.16, self.LEG_LENGTH, 0.16)
        glTranslatef(0.0, -0.5, 0.0)
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()
    
    def _draw_glasses(self, glasses_data):
        """Draw glasses on panda's face."""
        glPushMatrix()
        glTranslatef(0.0, 0.95, self.HEAD_RADIUS * 0.8)
        
        # Get glasses color
        color = glasses_data.get('color', [0.0, 0.0, 0.0])
        glColor3f(*color)
        
        # Left lens
        glPushMatrix()
        glTranslatef(-0.12, 0.0, 0.0)
        glutSolidTorus(0.02, 0.08, 8, 16) if 'glutSolidTorus' in dir() else None
        glPopMatrix()
        
        # Right lens
        glPushMatrix()
        glTranslatef(0.12, 0.0, 0.0)
        glutSolidTorus(0.02, 0.08, 8, 16) if 'glutSolidTorus' in dir() else None
        glPopMatrix()
        
        # Bridge
        glBegin(GL_LINES)
        glVertex3f(-0.04, 0.0, 0.0)
        glVertex3f(0.04, 0.0, 0.0)
        glEnd()
        
        glPopMatrix()
    
    def _draw_accessory(self, accessory_data):
        """Draw equipped accessory item on the panda."""
        accessory_type = accessory_data.get('type', 'bow')
        color = accessory_data.get('color', [1.0, 0.5, 0.0])
        glColor3f(*color)

        if accessory_type == 'bow':
            # Bow on top of head: two small spheres side-by-side
            glPushMatrix()
            glTranslatef(0.0, 1.35, 0.0)
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
            # Scarf around neck: flat torus-like ring
            glPushMatrix()
            glTranslatef(0.0, 0.62, 0.0)
            glScalef(1.0, 0.3, 1.0)
            self._draw_sphere(0.25, 16, 8)
            glPopMatrix()

        elif accessory_type == 'necklace':
            # Necklace: small spheres in a arc at front of neck
            glPushMatrix()
            glTranslatef(0.0, 0.58, 0.22)
            for i in range(7):
                angle = (i - 3) * 15.0
                rad = math.radians(angle)
                glPushMatrix()
                glTranslatef(math.sin(rad) * 0.18, 0.0, 0.0)
                self._draw_sphere(0.025, 6, 6)
                glPopMatrix()
            glPopMatrix()

        elif accessory_type == 'earrings':
            # Earrings: small dangling spheres on each side of head
            glPushMatrix()
            glTranslatef(-0.35, 0.85, 0.0)
            self._draw_sphere(0.05, 8, 8)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0.35, 0.85, 0.0)
            self._draw_sphere(0.05, 8, 8)
            glPopMatrix()

        else:
            # Generic accessory: small cube on chest
            glPushMatrix()
            glTranslatef(0.0, 0.5, 0.25)
            self._draw_cube(0.06)
            glPopMatrix()
    
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
        
        # Position in right arm
        arm_x = self.BODY_WIDTH + 0.1
        arm_y = 0.15
        
        glTranslatef(arm_x, arm_y, 0.0)
        glRotatef(self.weapon_rotation, 0.0, 0.0, 1.0)
        
        # Get weapon properties
        weapon_type = self.equipped_weapon.get('type', 'sword')
        color = self.equipped_weapon.get('color', [0.7, 0.7, 0.7])
        size = self.equipped_weapon.get('size', 0.5)
        
        glColor3f(*color)
        
        # Draw different weapon types
        if weapon_type == 'sword':
            self._draw_sword(size)
        elif weapon_type == 'axe':
            self._draw_axe(size)
        elif weapon_type == 'staff':
            self._draw_staff(size)
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
        """Draw items held in paw(s) — positioned at actual paw world space."""
        if not self.clothing['held_right'] and not self.clothing['held_left']:
            return

        limb   = self._get_limb_positions()
        bob    = self._get_body_bob()
        arm_x  = self.BODY_WIDTH * 0.82
        arm_y  = 0.34 + bob

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

        if any(k in item_type for k in ('sword', 'blade', 'katana')):
            self._draw_held_sword(size, color)
        elif any(k in item_type for k in ('bow', 'archer')):
            self._draw_held_bow(size, color)
        elif any(k in item_type for k in ('bamboo', 'stick', 'staff', 'cane')):
            self._draw_held_bamboo(size, color)
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

    # ========================================================================
    # Autonomous Behavior
    # ========================================================================
    
    def set_autonomous_mode(self, enabled: bool):
        """Enable or disable autonomous wandering."""
        self.autonomous_mode = enabled
    
    def walk_to_position(self, x: float, y: float, z: float):
        """Make panda walk to specific position."""
        self.target_position = (x, y, z)
        self.set_animation_state('walking')
    
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
        
        if distance < 0.1:
            # Reached target
            self.target_position = None
            self.set_animation_state('idle')
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
        """Choose a random activity for panda."""
        activities = [
            ('walk_around',    0.35),
            ('work',           0.25),
            ('idle',           0.15),
            ('celebrate',      0.08),
            ('crawl_around',   0.10),
            ('climb_wall',     0.07),
            ('sit_back',       0.10),
            ('hang_ceiling',   0.05),
        ]
        
        # Weighted random choice
        total = sum(w for _, w in activities)
        r = random.uniform(0, total)
        
        cumulative = 0
        for activity, weight in activities:
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
                                      lambda: (self.animation_state == 'crawling'
                                               and self.set_animation_state('idle')))
                elif activity == 'climb_wall':
                    # Climb → fall back → idle  (each step checks current state)
                    self.set_animation_state('climbing_wall')
                    fall_ms = int(random.uniform(1.0, 2.5) * 1000)
                    idle_ms = fall_ms + int(random.uniform(0.8, 1.8) * 1000)
                    QTimer.singleShot(fall_ms,
                                      lambda: (self.animation_state == 'climbing_wall'
                                               and self.set_animation_state('falling_back')))
                    QTimer.singleShot(idle_ms,
                                      lambda: (self.animation_state == 'falling_back'
                                               and self.set_animation_state('idle')))
                elif activity == 'sit_back':
                    self.set_animation_state('sitting_back')
                    dur = random.uniform(3.0, 7.0)
                    QTimer.singleShot(int(dur * 1000),
                                      lambda: (self.animation_state == 'sitting_back'
                                               and self.set_animation_state('idle')))
                elif activity == 'hang_ceiling':
                    self.set_animation_state('hanging_ceiling')
                    dur = random.uniform(2.5, 5.0)
                    QTimer.singleShot(int(dur * 1000),
                                      lambda: (self.animation_state == 'hanging_ceiling'
                                               and self.set_animation_state('falling_back')))
                    QTimer.singleShot(int(dur * 1000) + 1800,
                                      lambda: (self.animation_state == 'falling_back'
                                               and self.set_animation_state('idle')))
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
                QTimer.singleShot(1800, lambda: self.animation_state == 'celebrating'
                                  and self.set_animation_state('idle'))
            elif furniture_id in ('weapons_rack', 'armor_rack'):
                # Reach up to wall rack
                self._arm_over[0] += 25.0   # both arms
                self._arm_over[1] += 25.0
                self.set_animation_state('waving')
                QTimer.singleShot(900, lambda: self.animation_state == 'waving'
                                  and self.set_animation_state('idle'))
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
        'classic':         ((0.97, 0.97, 0.99), (0.08, 0.08, 0.08), (1.00, 0.98, 0.93)),
        'albino':          ((1.00, 1.00, 1.00), (0.85, 0.82, 0.80), (1.00, 0.99, 0.97)),
        'snow_panda':      ((0.92, 0.95, 1.00), (0.65, 0.72, 0.88), (0.95, 0.97, 1.00)),
        'red_panda_fur':   ((0.80, 0.42, 0.18), (0.15, 0.10, 0.06), (0.90, 0.72, 0.50)),
        'fluffy':          ((0.98, 0.98, 1.00), (0.06, 0.06, 0.06), (1.00, 0.97, 0.90)),
        'young':           ((0.99, 0.99, 1.00), (0.25, 0.25, 0.30), (1.00, 0.98, 0.92)),
        'elder':           ((0.88, 0.88, 0.86), (0.20, 0.20, 0.22), (0.92, 0.90, 0.85)),
        'golden':          ((0.95, 0.82, 0.40), (0.50, 0.32, 0.08), (1.00, 0.92, 0.65)),
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
            trail_type: Type of trail ('sparkle', 'rainbow', 'fire', 'ice', 'none')
            trail_data: Configuration dict for trail (color, intensity, duration, etc.)
        """
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
        
        # Add new particle at current position if panda is moving
        if abs(self.velocity_x) > 0.01 or abs(self.velocity_z) > 0.01:
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
        
        glDisable(GL_LIGHTING)
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
        
        glEnable(GL_LIGHTING)
    
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
                       May also be a plain string item identifier.
        """
        if isinstance(item_data, str):
            item_data = {'id': item_data}

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
            elif any(k in item_type for k in ('shirt', 'jacket', 'top')):
                slot = 'shirt'
            elif any(k in item_type for k in ('pants', 'skirt', 'bottom')):
                slot = 'pants'
            elif any(k in item_type for k in ('glasses', 'goggles')):
                slot = 'glasses'
            elif any(k in item_type for k in ('sword', 'bow', 'axe', 'staff', 'weapon', 'gun', 'blade', 'katana', 'bamboo', 'held_right')):
                slot = 'held_right'
            elif any(k in item_type for k in ('held_left', 'shield')):
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


# Export PandaOpenGLWidget as the primary widget interface
# Direct usage is now preferred over the deprecated bridge wrapper
PandaWidget = PandaOpenGLWidget if QT_AVAILABLE else None
