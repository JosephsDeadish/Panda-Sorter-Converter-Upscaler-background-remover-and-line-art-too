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
    
    # Animation constants
    TARGET_FPS = 60
    FRAME_TIME = 1.0 / TARGET_FPS  # 16.67ms per frame
    
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
        
        # Animation timer (60 FPS)
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
        Transition to a specific animation state.
        
        Uses a simplified approach where we maintain a mapping of states
        and update the current state. In a full state machine implementation,
        you would define explicit transitions with conditions.
        """
        if not self.state_machine:
            # Fallback if state machine not available
            self.animation_state = state_name
            if hasattr(self, 'animation_changed'):
                self.animation_changed.emit(state_name)
            return
        
        state_map = {
            'idle': self.idle_state,
            'walking': self.walking_state,
            'jumping': self.jumping_state,
            'working': self.working_state,
            'celebrating': self.celebrating_state,
            'waving': self.waving_state
        }
        
        if state_name in state_map:
            target_state = state_map[state_name]
            # Manually invoke state entry since we're using programmatic control
            # rather than event-driven transitions
            self._on_state_entered(state_name)
    
    def initializeGL(self):
        """Initialize OpenGL settings."""
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
        # FPS limiting
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
        """Draw 3D panda character with all body parts."""
        # Get animation-specific offsets
        bob_offset = self._get_body_bob()
        limb_offsets = self._get_limb_positions()
        
        # Body (torso) - main oval shape
        glPushMatrix()
        glTranslatef(0.0, 0.3 + bob_offset, 0.0)
        glColor3f(1.0, 1.0, 1.0)  # White
        glPushMatrix()
        glScalef(self.BODY_WIDTH, self.BODY_HEIGHT, self.BODY_WIDTH * 0.8)
        self._draw_sphere(1.0, 20, 20)
        glPopMatrix()
        glPopMatrix()
        
        # Head
        glPushMatrix()
        glTranslatef(0.0, 0.9 + bob_offset, 0.0)
        glColor3f(1.0, 1.0, 1.0)  # White
        self._draw_sphere(self.HEAD_RADIUS, 20, 20)
        
        # Ears
        self._draw_panda_ears(bob_offset)
        
        # Eyes (black patches)
        self._draw_panda_eyes()
        
        # Nose
        glPushMatrix()
        glTranslatef(0.0, -0.05, self.HEAD_RADIUS * 0.8)
        glColor3f(0.0, 0.0, 0.0)  # Black
        self._draw_sphere(0.06, 12, 12)
        glPopMatrix()
        
        glPopMatrix()
        
        # Arms
        self._draw_panda_arms(limb_offsets, bob_offset)
        
        # Legs
        self._draw_panda_legs(limb_offsets, bob_offset)
        
        # Draw 3D clothing (hats, shirts, pants, etc.)
        self._draw_clothing()
        
        # Draw equipped weapon
        self._draw_weapon()
    
    def _draw_panda_geometry_only(self):
        """Draw panda geometry without colors (for shadow mapping)."""
        # Simplified geometry for shadow pass
        glPushMatrix()
        glTranslatef(0.0, 0.3, 0.0)
        glScalef(self.BODY_WIDTH, self.BODY_HEIGHT, self.BODY_WIDTH * 0.8)
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0.0, 0.9, 0.0)
        self._draw_sphere(self.HEAD_RADIUS, 12, 12)
        glPopMatrix()
    
    def _draw_panda_ears(self, bob_offset):
        """Draw panda ears."""
        ear_y = 0.3
        ear_x = 0.25
        
        # Left ear
        glPushMatrix()
        glTranslatef(-ear_x, ear_y, 0.0)
        glColor3f(0.0, 0.0, 0.0)  # Black
        self._draw_sphere(self.EAR_SIZE, 12, 12)
        glPopMatrix()
        
        # Right ear
        glPushMatrix()
        glTranslatef(ear_x, ear_y, 0.0)
        glColor3f(0.0, 0.0, 0.0)  # Black
        self._draw_sphere(self.EAR_SIZE, 12, 12)
        glPopMatrix()
    
    def _draw_panda_eyes(self):
        """Draw panda eyes with black patches."""
        eye_y = 0.05
        eye_x = 0.15
        eye_z = self.HEAD_RADIUS * 0.7
        
        # Left eye patch (black)
        glPushMatrix()
        glTranslatef(-eye_x, eye_y, eye_z)
        glColor3f(0.0, 0.0, 0.0)
        self._draw_sphere(0.12, 12, 12)
        glPopMatrix()
        
        # Right eye patch (black)
        glPushMatrix()
        glTranslatef(eye_x, eye_y, eye_z)
        glColor3f(0.0, 0.0, 0.0)
        self._draw_sphere(0.12, 12, 12)
        glPopMatrix()
        
        # Left eyeball (white)
        glPushMatrix()
        glTranslatef(-eye_x, eye_y, eye_z + 0.05)
        glColor3f(1.0, 1.0, 1.0)
        self._draw_sphere(0.06, 12, 12)
        glPopMatrix()
        
        # Right eyeball (white)
        glPushMatrix()
        glTranslatef(eye_x, eye_y, eye_z + 0.05)
        glColor3f(1.0, 1.0, 1.0)
        self._draw_sphere(0.06, 12, 12)
        glPopMatrix()
        
        # Pupils (black)
        pupil_offset = 0.02
        glPushMatrix()
        glTranslatef(-eye_x + pupil_offset, eye_y, eye_z + 0.1)
        glColor3f(0.0, 0.0, 0.0)
        self._draw_sphere(0.03, 8, 8)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(eye_x + pupil_offset, eye_y, eye_z + 0.1)
        glColor3f(0.0, 0.0, 0.0)
        self._draw_sphere(0.03, 8, 8)
        glPopMatrix()
    
    def _draw_panda_arms(self, limb_offsets, bob_offset):
        """Draw panda arms."""
        arm_y = 0.3 + bob_offset
        arm_x = self.BODY_WIDTH + 0.1
        
        left_arm_angle = limb_offsets.get('left_arm_angle', 0)
        right_arm_angle = limb_offsets.get('right_arm_angle', 0)
        
        # Left arm
        glPushMatrix()
        glTranslatef(-arm_x, arm_y, 0.0)
        glRotatef(left_arm_angle, 1.0, 0.0, 0.0)
        glColor3f(0.0, 0.0, 0.0)  # Black
        glPushMatrix()
        glScalef(0.12, self.ARM_LENGTH, 0.12)
        glTranslatef(0.0, -0.5, 0.0)
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()
        glPopMatrix()
        
        # Right arm
        glPushMatrix()
        glTranslatef(arm_x, arm_y, 0.0)
        glRotatef(right_arm_angle, 1.0, 0.0, 0.0)
        glColor3f(0.0, 0.0, 0.0)  # Black
        glPushMatrix()
        glScalef(0.12, self.ARM_LENGTH, 0.12)
        glTranslatef(0.0, -0.5, 0.0)
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()
        glPopMatrix()
    
    def _draw_panda_legs(self, limb_offsets, bob_offset):
        """Draw panda legs."""
        leg_y = -0.1 + bob_offset
        leg_x = 0.2
        
        left_leg_angle = limb_offsets.get('left_leg_angle', 0)
        right_leg_angle = limb_offsets.get('right_leg_angle', 0)
        
        # Left leg
        glPushMatrix()
        glTranslatef(-leg_x, leg_y, 0.0)
        glRotatef(left_leg_angle, 1.0, 0.0, 0.0)
        glColor3f(0.0, 0.0, 0.0)  # Black
        glPushMatrix()
        glScalef(0.15, self.LEG_LENGTH, 0.15)
        glTranslatef(0.0, -0.5, 0.0)
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()
        glPopMatrix()
        
        # Right leg
        glPushMatrix()
        glTranslatef(leg_x, leg_y, 0.0)
        glRotatef(right_leg_angle, 1.0, 0.0, 0.0)
        glColor3f(0.0, 0.0, 0.0)  # Black
        glPushMatrix()
        glScalef(0.15, self.LEG_LENGTH, 0.15)
        glTranslatef(0.0, -0.5, 0.0)
        self._draw_sphere(1.0, 12, 12)
        glPopMatrix()
        glPopMatrix()
    
    def _draw_sphere(self, radius, slices, stacks):
        """Draw a sphere using GLU quadrics."""
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluQuadricTexture(quad, GL_TRUE)
        gluSphere(quad, radius, slices, stacks)
        gluDeleteQuadric(quad)
    
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
    
    def _get_body_bob(self):
        """Get body bobbing offset based on animation state."""
        if self.animation_state == 'idle':
            # Gentle breathing animation
            return 0.02 * math.sin(self.animation_frame * 0.05)
        elif self.animation_state in ['walking', 'walking_left', 'walking_right']:
            # Walking bob
            return 0.05 * abs(math.sin(self.animation_frame * 0.2))
        elif self.animation_state == 'jumping':
            # Jump arc
            phase = (self.animation_frame % 60) / 60.0
            return 0.3 * math.sin(phase * math.pi)
        return 0.0
    
    def _get_limb_positions(self):
        """Get limb rotation angles based on animation state."""
        positions = {
            'left_arm_angle': 0,
            'right_arm_angle': 0,
            'left_leg_angle': 0,
            'right_leg_angle': 0
        }
        
        # Check if working (overrides other animations)
        if self.is_working:
            working_offsets = self._get_working_limb_offsets()
            positions.update(working_offsets)
            return positions
        
        if self.animation_state in ['walking', 'walking_left', 'walking_right']:
            # Walking animation - opposing arm/leg movement
            swing = 30 * math.sin(self.animation_frame * 0.2)
            positions['left_arm_angle'] = swing
            positions['right_arm_angle'] = -swing
            positions['left_leg_angle'] = -swing
            positions['right_leg_angle'] = swing
        elif self.animation_state == 'waving':
            # Waving animation
            positions['right_arm_angle'] = -90 + 20 * math.sin(self.animation_frame * 0.3)
        elif self.animation_state == 'celebrating':
            # Both arms up
            positions['left_arm_angle'] = -120
            positions['right_arm_angle'] = -120
        
        return positions
    
    def _update_animation(self):
        """Update animation frame and physics."""
        self.animation_frame += 1
        if self.animation_frame > 10000:
            self.animation_frame = 0
        
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - self.last_frame_time
        
        # Update physics
        self._update_physics()
        
        # Update trail particles
        self._update_trail()
        
        # Update autonomous behavior (walking around)
        self._update_autonomous_behavior(delta_time)
        
        # Update working animation
        self._update_working_animation(delta_time)
        
        # Request redraw
        self.update()
    
    def _update_physics(self):
        """Update physics simulation."""
        # Apply gravity if not on ground
        if self.panda_y > -1.0:
            self.velocity_y -= self.GRAVITY * 0.016  # 60 FPS delta
        
        # Apply velocities
        self.panda_x += self.velocity_x * 0.016
        self.panda_y += self.velocity_y * 0.016
        self.panda_z += self.velocity_z * 0.016
        self.rotation_y += self.angular_velocity * 0.016
        
        # Ground collision
        if self.panda_y < -0.7:
            self.panda_y = -0.7
            self.velocity_y *= -self.BOUNCE_DAMPING
            if abs(self.velocity_y) < 0.01:
                self.velocity_y = 0
        
        # Apply friction
        self.velocity_x *= self.FRICTION
        self.velocity_z *= self.FRICTION
        self.angular_velocity *= self.FRICTION
        
        # Update items physics
        for item in self.items_3d:
            if 'velocity_y' in item:
                item['y'] += item['velocity_y'] * 0.016
                item['velocity_y'] -= self.GRAVITY * 0.016
                if item['y'] < -0.9:
                    item['y'] = -0.9
                    item['velocity_y'] *= -self.BOUNCE_DAMPING
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press."""
        self.last_mouse_pos = event.pos()
        self.drag_start_pos = event.pos()
        self.is_dragging = False
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicked on panda (simple distance check)
            # In 3D, we'd need proper ray casting
            self.clicked.emit()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse drag."""
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
