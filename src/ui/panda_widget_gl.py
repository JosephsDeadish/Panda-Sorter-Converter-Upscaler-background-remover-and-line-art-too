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
            'hat': None,      # Hat on head
            'shirt': None,    # Shirt on body
            'pants': None,    # Pants on legs
            'glasses': None,  # Glasses on face
            'accessory': None # Other accessories
        }
        
        # Weapon system
        self.equipped_weapon = None  # Current weapon
        self.weapon_rotation = 0.0  # Weapon rotation angle
        
        # Color customization system
        self.custom_colors = {
            'body': [1.0, 1.0, 1.0],     # Default white/natural
            'eyes': [0.0, 0.0, 0.0],      # Default black
            'accent': [0.5, 0.5, 0.5],    # Default gray for patches
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
        if state_name == 'idle' and self.animation_state in ('waving', 'celebrating', 'jumping'):
            self._hold_t = random.uniform(0.12, 0.28)
            # Schedule the idle transition after the hold
            fire_t = time.time() + self._hold_t
            self._reaction_delay_q.append((fire_t, lambda: self._set_state_direct('idle')))
            return

        # ── Follow-through kick on arm-heavy transitions ──────────────────────
        if state_name in ('waving',):
            self._arm_over_vel[1] += random.uniform(10.0, 18.0)  # right arm overshoot
        elif state_name in ('walking', 'running'):
            self._arm_over_vel[0] += random.uniform(4.0, 8.0)
            self._arm_over_vel[1] -= random.uniform(4.0, 8.0)

        # ── Surprised wide-eyes for jumps/celebrations ────────────────────────
        if state_name in ('jumping', 'celebrating', 'waving'):
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

        # Apply squash/stretch to the torso
        sy = self._squash_y

        # ── Torso ────────────────────────────────────────────────────────────
        glPushMatrix()
        glTranslatef(self.panda_x, 0.28 + bob, self.panda_z)
        glRotatef(self.rotation_y, 0.0, 1.0, 0.0)

        # Belly — creamy white underside; belly jiggle on Y (height oscillation)
        glPushMatrix()
        glScalef(self.BODY_WIDTH * 0.65,
                 self.BODY_HEIGHT * 0.55 * sy * self._belly_y,
                 self.BODY_WIDTH * 0.50)
        glColor3f(1.0, 0.98, 0.93)
        self._draw_sphere(1.0, 24, 24)
        glPopMatrix()

        # Main body — bright white with subtle blue-white tint
        glPushMatrix()
        glScalef(self.BODY_WIDTH, self.BODY_HEIGHT * sy, self.BODY_WIDTH * 0.78)
        glColor3f(0.97, 0.97, 0.99)
        self._draw_sphere(1.0, 24, 24)
        glPopMatrix()

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

        # Black saddle patch across lower torso
        glPushMatrix()
        glTranslatef(0.0, -0.18, 0.0)
        glScalef(self.BODY_WIDTH * 0.95, self.BODY_HEIGHT * 0.35 * sy, self.BODY_WIDTH * 0.70)
        glColor3f(0.08, 0.08, 0.08)
        self._draw_sphere(1.0, 20, 20)
        glPopMatrix()

        # ── Legs ─────────────────────────────────────────────────────────────
        self._draw_panda_legs(limb, bob, t)

        # ── Arms ─────────────────────────────────────────────────────────────
        self._draw_panda_arms(limb, bob, t)

        # ── Tail (small white puff) ───────────────────────────────────────────
        glPushMatrix()
        glTranslatef(0.0, -0.05, -self.BODY_WIDTH * 0.78)
        glColor3f(0.94, 0.94, 0.94)
        self._draw_sphere(0.07, 10, 10)
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

        # Main skull — white
        glColor3f(0.97, 0.97, 0.99)
        self._draw_sphere(self.HEAD_RADIUS, 28, 28)

        # Fur fuzz over skull
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 1.0, 1.0, 0.15)
        self._draw_sphere(self.HEAD_RADIUS * 1.04, 16, 16)
        glDisable(GL_BLEND)

        # ── Ears ─────────────────────────────────────────────────────────────
        self._draw_panda_ears(bob, t)

        # ── Eye patches ───────────────────────────────────────────────────────
        self._draw_panda_eyes(t)

        # ── Snout ─────────────────────────────────────────────────────────────
        self._draw_panda_snout()

        glPopMatrix()   # end head matrix

        # ── Clothing & weapons ────────────────────────────────────────────────
        self._draw_clothing()
        self._draw_weapon()

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
        """Draw rounded ears with black outer ring, pink inner ear, and asymmetric spring physics."""
        ear_positions = [(-0.265, 0.295, 0.06), (0.265, 0.295, 0.06)]
        for i, (ex, ey, ez) in enumerate(ear_positions):
            # Follow-through: rotate ear using spring position
            ear_rot = self._ear_pos[i]
            glPushMatrix()
            glTranslatef(ex, ey, ez)
            glRotatef(ear_rot, 0.0, 0.0, 1.0)   # spring-driven tilt
            glScalef(1.0, 0.88, 0.55)
            glColor3f(0.08, 0.08, 0.08)
            self._draw_sphere(self.EAR_SIZE, 16, 16)
            # Inner pink concha
            glPushMatrix()
            glTranslatef(0.0, -0.005, 0.015)
            glScalef(0.58, 0.52, 0.40)
            glColor3f(0.88, 0.60, 0.68)   # warm pink
            self._draw_sphere(self.EAR_SIZE, 12, 12)
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
            glColor3f(0.07, 0.07, 0.07)
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

    # ─── Arm drawing ────────────────────────────────────────────────────────
    def _draw_panda_arms(self, limb, bob, t=0):
        """Draw arms with follow-through overshoot, uneven breathing, paw/claws."""
        arm_y   = 0.30 + bob
        arm_x   = self.BODY_WIDTH + 0.06

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

            # Upper arm — thick black ovoid
            glPushMatrix()
            glScalef(0.115, 0.200, 0.115)
            glTranslatef(0.0, -0.50, 0.0)
            glColor3f(0.08, 0.08, 0.08)
            self._draw_sphere(1.0, 16, 16)
            glPopMatrix()

            # Elbow joint
            glPushMatrix()
            glTranslatef(0.0, -self.ARM_LENGTH * 0.45, 0.0)
            glColor3f(0.10, 0.10, 0.10)
            self._draw_sphere(0.075, 12, 12)
            glPopMatrix()

            # Forearm — slightly thinner
            glPushMatrix()
            glTranslatef(0.0, -self.ARM_LENGTH * 0.45, 0.0)
            glScalef(0.095, 0.185, 0.095)
            glTranslatef(0.0, -0.50, 0.0)
            glColor3f(0.09, 0.09, 0.09)
            self._draw_sphere(1.0, 14, 14)
            glPopMatrix()

            # Paw (rounded teardrop)
            glPushMatrix()
            glTranslatef(0.0, -self.ARM_LENGTH * 0.88, 0.0)
            glScalef(1.20, 0.65, 1.15)
            glColor3f(0.08, 0.08, 0.08)
            self._draw_sphere(0.082, 14, 14)
            # Paw pad (pink ellipse on palm face)
            glPushMatrix()
            glTranslatef(0.0, 0.0, 0.07)
            glScalef(0.70, 0.58, 0.30)
            glColor3f(0.78, 0.48, 0.55)
            self._draw_sphere(0.082, 10, 10)
            glPopMatrix()
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

        for side, key in ((-1, 'left_leg_angle'), (1, 'right_leg_angle')):
            angle = limb.get(key, 0)

            glPushMatrix()
            glTranslatef(side * leg_x, leg_y, 0.0)
            glRotatef(angle, 1.0, 0.0, 0.0)

            # Thigh — wide black sphere
            glPushMatrix()
            glScalef(0.155, 0.195, 0.155)
            glTranslatef(0.0, -0.50, 0.0)
            glColor3f(0.08, 0.08, 0.08)
            self._draw_sphere(1.0, 16, 16)
            glPopMatrix()

            # Knee joint
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.42, 0.0)
            glColor3f(0.10, 0.10, 0.10)
            self._draw_sphere(0.082, 12, 12)
            glPopMatrix()

            # Shin
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.42, 0.0)
            glScalef(0.130, 0.160, 0.130)
            glTranslatef(0.0, -0.50, 0.0)
            glColor3f(0.09, 0.09, 0.09)
            self._draw_sphere(1.0, 14, 14)
            glPopMatrix()

            # Foot — flattened ovoid, slightly forward
            glPushMatrix()
            glTranslatef(0.0, -self.LEG_LENGTH * 0.85, 0.045)
            glScalef(1.25, 0.55, 1.55)
            glColor3f(0.07, 0.07, 0.07)
            self._draw_sphere(0.092, 16, 16)
            # Foot pad (pink)
            glPushMatrix()
            glTranslatef(0.0, -0.06, 0.04)
            glScalef(0.65, 0.30, 0.75)
            glColor3f(0.78, 0.48, 0.55)
            self._draw_sphere(0.092, 10, 10)
            glPopMatrix()
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
    def _play_sound(self, name: str):
        """
        Play a named sound effect.
        Tries QSoundEffect from app_data/sounds/<name>.wav first.
        Falls back to QApplication.beep() for 'boop'.
        Fails silently on any error.
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
                import os
                # Look for WAV in app_data/sounds/ next to the EXE / working dir
                for base in (
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app_data', 'sounds'),
                    os.path.join(os.getcwd(), 'app_data', 'sounds'),
                ):
                    wav = os.path.normpath(os.path.join(base, f'{name}.wav'))
                    if os.path.isfile(wav):
                        sfx = QSoundEffect(self)
                        sfx.setSource(QUrl.fromLocalFile(wav))
                        sfx.setVolume(0.55)
                        self._audio_sfx[name] = sfx
                        break
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

            elif state == '_anticipation':
                # Pull arms back and crouch before jump/celebrate
                pos['left_arm_angle']  = 25.0
                pos['right_arm_angle'] = 25.0
                pos['left_leg_angle']  = 12.0
                pos['right_leg_angle'] = 12.0

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
        """Draw all equipped clothing items in 3D."""
        # Draw hat
        if self.clothing['hat']:
            self._draw_hat(self.clothing['hat'])
        
        # Draw shirt
        if self.clothing['shirt']:
            self._draw_shirt(self.clothing['shirt'])
        
        # Draw pants
        if self.clothing['pants']:
            self._draw_pants(self.clothing['pants'])
        
        # Draw glasses
        if self.clothing['glasses']:
            self._draw_glasses(self.clothing['glasses'])
        
        # Draw accessory
        if self.clothing['accessory']:
            self._draw_accessory(self.clothing['accessory'])
    
    def _draw_hat(self, hat_data):
        """Draw hat on panda's head."""
        glPushMatrix()
        # Position on top of head
        glTranslatef(0.0, 1.2, 0.0)
        
        # Get hat color
        color = hat_data.get('color', [0.8, 0.2, 0.2])
        glColor3f(*color)
        
        # Draw hat (cone shape for simple hat)
        glRotatef(-90, 1.0, 0.0, 0.0)
        quad = gluNewQuadric()
        gluCylinder(quad, 0.3, 0.1, 0.3, 16, 1)
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
                glTranslatef(_math.sin(rad) * 0.18, 0.0, 0.0)
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
            ('walk_around', 0.4),
            ('work', 0.3),
            ('idle', 0.2),
            ('celebrate', 0.1)
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
            mood: Mood name ('happy', 'sad', 'angry', 'surprised', 'tired')
        """
        # Map moods to animations
        mood_animations = {
            'happy': 'celebrating',
            'sad': 'idle',
            'angry': 'wall_hit',
            'surprised': 'clicked',
            'tired': 'working',
            'playful': 'jumping'
        }
        
        animation = mood_animations.get(mood, 'idle')
        self.set_animation_state(animation)
    
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
