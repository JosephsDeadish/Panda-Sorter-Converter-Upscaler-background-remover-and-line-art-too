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
    from PyQt6.QtWidgets import QOpenGLWidget, QWidget
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
        'idle': 0.4,
        'walking': 0.3,
        'interacting': 0.2,
        'investigating': 0.1
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
        
        # Make transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
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
        # Enable transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        
        # Enable smooth shading
        glShadeModel(GL_SMOOTH)
        
        # Clear color (transparent)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        
        # Lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        # Light position
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    
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
        """Render the 3D panda."""
        glPushMatrix()
        
        # Position panda
        glTranslatef(self.panda_x, self.panda_y, self.panda_z)
        glRotatef(self.panda_rotation, 0.0, 1.0, 0.0)
        glScalef(self.panda_scale, self.panda_scale * self.squash_factor, self.panda_scale)
        
        # Panda body (white torso)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        self._draw_sphere(0.0, 0.0, 0.0, 0.3)
        
        # Panda head (white)
        self._draw_sphere(0.0, 0.4, 0.0, 0.25)
        
        # Black ears
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.0, 0.0, 0.0, 1.0])
        self._draw_sphere(-0.15, 0.55, 0.0, 0.1)
        self._draw_sphere(0.15, 0.55, 0.0, 0.1)
        
        # Black eye patches
        self._draw_sphere(-0.1, 0.45, 0.2, 0.08)
        self._draw_sphere(0.1, 0.45, 0.2, 0.08)
        
        # White eyes
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        self._draw_sphere(-0.1, 0.45, 0.22, 0.04)
        self._draw_sphere(0.1, 0.45, 0.22, 0.04)
        
        # Black pupils
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.0, 0.0, 0.0, 1.0])
        self._draw_sphere(-0.1, 0.45, 0.24, 0.02)
        self._draw_sphere(0.1, 0.45, 0.24, 0.02)
        
        # Black nose
        self._draw_sphere(0.0, 0.4, 0.23, 0.03)
        
        # Legs (black)
        self._draw_sphere(-0.15, -0.2, 0.1, 0.12)
        self._draw_sphere(0.15, -0.2, 0.1, 0.12)
        
        # Arms (black)
        arm_angle = math.sin(self.animation_phase) * 20 if self.animation_state == 'walking' else 0
        
        glPushMatrix()
        glRotatef(arm_angle, 1.0, 0.0, 0.0)
        self._draw_sphere(-0.25, 0.05, 0.0, 0.1)
        glPopMatrix()
        
        glPushMatrix()
        glRotatef(-arm_angle, 1.0, 0.0, 0.0)
        self._draw_sphere(0.25, 0.05, 0.0, 0.1)
        glPopMatrix()
        
        glPopMatrix()
    
    def _draw_sphere(self, x, y, z, radius):
        """Draw a sphere at position with radius."""
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Use GLU quadric for smooth sphere
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        gluSphere(quadric, radius, 20, 20)
        gluDeleteQuadric(quadric)
        
        glPopMatrix()
    
    def _update_body_part_positions(self):
        """Update body part positions in screen coordinates for interaction detection."""
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
        model_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        
        screen_pos = gluProject(x, y, z, model_matrix, proj_matrix, viewport)
        return QPoint(int(screen_pos[0]), int(viewport[3] - screen_pos[1]))
    
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
