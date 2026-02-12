"""
Panda Widget - Animated panda character for the UI
Displays an interactive panda drawn on a canvas with body-shaped rendering
and walking/idle animations. Users can click, hover, pet, and drag the panda.
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import math
import random
import sys
import time
import tkinter as tk
from typing import Optional, Callable
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

logger = logging.getLogger(__name__)


# Canvas dimensions for the panda drawing
PANDA_CANVAS_W = 220
PANDA_CANVAS_H = 270

# Transparent color key for the Toplevel window (Windows only).
# Magenta is the classic choice – it does not appear in the panda drawing.
TRANSPARENT_COLOR = '#FF00FF'

# Speech bubble layout constants
BUBBLE_MAX_CHARS_PER_LINE = 36
BUBBLE_PAD_X = 18
BUBBLE_PAD_Y = 12
BUBBLE_CHAR_WIDTH = 10   # approximate px per character at font size 16 bold
BUBBLE_LINE_HEIGHT = 24  # px per line of text
BUBBLE_MAX_WIDTH = 400
BUBBLE_CORNER_RADIUS = 12
BUBBLE_TAIL_HEIGHT = 10


class _SpeechProxy:
    """Proxy that mimics CTkLabel.configure(text=...) but routes to speech bubble."""

    def __init__(self, widget: 'PandaWidget'):
        self._widget = widget

    def configure(self, **kwargs):
        text = kwargs.get("text")
        if text is not None:
            self._widget._show_speech_bubble(str(text))

    def cget(self, key):
        if key == "text":
            return self._widget._speech_text
        return ""


class PandaWidget(ctk.CTkFrame if ctk else tk.Frame):
    """Interactive animated panda widget - always present and draggable.
    
    Renders the panda as a body-shaped canvas drawing with distinct
    black-and-white panda features and walking/idle animations.
    
    Note: ``panda_label`` is kept as an alias for ``panda_canvas`` so that
    external code (e.g. body-part click detection) that references
    ``panda_label`` continues to work without modification.
    """
    
    # Minimum drag distance (pixels) to distinguish drag from click
    CLICK_THRESHOLD = 5
    # Minimum mouse positions needed to detect rubbing motion
    MIN_RUB_POSITIONS = 4
    # Cooldown in seconds between rub detections
    RUB_COOLDOWN_SECONDS = 2.0
    # Cooldown in seconds between wall hit reactions
    WALL_HIT_COOLDOWN_SECONDS = 1.0
    
    # Animation timing (ms) - lower values = smoother animations
    ANIMATION_INTERVAL = 33
    # Reset frame counter at this value to prevent unbounded growth
    MAX_ANIMATION_FRAME = 10000
    # Emoji decoration cycle interval (frames between emoji changes, ~660ms at 33ms/frame)
    EMOJI_CYCLE_FRAMES = 20
    
    # Drag pattern detection thresholds
    DRAG_HISTORY_SECONDS = 2.0      # How long to retain drag positions
    SHAKE_DIRECTION_CHANGES = 6     # X direction changes needed for shaking (lowered for better detection)
    MIN_SHAKE_MOVEMENT = 8          # Min px movement for a direction change (lowered for fast shakes)
    MIN_SHAKE_VELOCITY = 500        # Min avg speed (px/s) to consider shake (high = only super fast shakes)
    MIN_ROTATION_ANGLE = 0.7        # Min angle diff (radians) for spin detection (higher = less sensitive)
    SPIN_CONSISTENCY_THRESHOLD = 0.95  # Required ratio of consistent rotations (higher = stricter)
    MIN_SPIN_POSITIONS = 24         # Min drag positions to attempt spin detection (more points needed)
    MIN_SPIN_TOTAL_ANGLE = 4.71239  # Min total angle (radians, ~1.5*pi) swept for spin
    
    # Toss physics constants
    TOSS_FRICTION = 0.92            # Velocity decay per frame
    TOSS_GRAVITY = 1.5              # Downward acceleration per frame
    TOSS_BOUNCE_DAMPING = 0.6       # Velocity retained after bounce
    TOSS_MIN_VELOCITY = 1.5         # Minimum velocity to keep bouncing
    TOSS_FRAME_INTERVAL = 20        # Physics tick interval (ms)
    TOSS_FRAME_TIME = 0.016         # Approximate frame time in seconds (~60fps)
    
    # Cooldown between drag-pattern animation triggers (seconds)
    DRAG_PATTERN_COOLDOWN = 2.0
    
    # Belly jiggle physics constants
    JIGGLE_SPRING = 0.35             # Spring stiffness for belly wobble
    JIGGLE_DAMPING = 0.82            # Damping factor for belly wobble
    JIGGLE_VELOCITY_POKE = 8.0       # Jiggle impulse from belly poke/click
    JIGGLE_VELOCITY_ITEM_HIT = 10.0  # Jiggle impulse from item impact
    
    # Limb dangle physics constants (arms/legs inertia during drag)
    DANGLE_SPRING = 0.18             # Spring stiffness for limb dangle
    DANGLE_DAMPING = 0.88            # Damping factor for limb dangle
    DANGLE_ARM_FACTOR = 0.3          # Arm response to vertical drag velocity
    DANGLE_LEG_FACTOR = 0.4          # Leg response to vertical drag velocity
    DANGLE_ARM_H_FACTOR = 0.25       # Arm response to horizontal drag velocity
    DANGLE_LEG_H_FACTOR = 0.35       # Leg response to horizontal drag velocity
    # Full dangle (dangly look) only when grabbed by head region
    DANGLE_HEAD_MULTIPLIER = 1.0     # Full dangle when held by head
    DANGLE_BODY_MULTIPLIER = 0.3     # Minimal dangle when held elsewhere
    
    # Ear stretch physics constants (elastic stretch during drag)
    EAR_STRETCH_SPRING = 0.25        # Spring stiffness for ear stretch
    EAR_STRETCH_DAMPING = 0.85       # Damping factor for ear stretch
    EAR_STRETCH_FACTOR = -0.15       # Ear response to vertical drag velocity
    EAR_STRETCH_MAX = 12.0           # Maximum ear stretch (pixels)
    
    # Belly rub animation frequency (rubbing motion speed)
    BELLY_RUB_FREQUENCY = 0.8
    
    # Upside-down flip threshold (velocity when dragged by legs)
    UPSIDE_DOWN_VELOCITY_THRESHOLD = 2.0  # Velocity threshold for flip detection
    
    # Emoji decorations shown next to the panda for each animation type
    ANIMATION_EMOJIS = {
        'working': ['💼', '⚙️', '📊', '💻', '☕'],
        'celebrating': ['🎉', '🥳', '🎊', '🎈', '✨', '🎆'],
        'rage': ['💢', '🔥', '💢💢', '🔥💢', '💥', '🔥🔥'],
        'dancing': ['🎵', '🎶', '🎵', '♪', '🎶'],
        'drunk': ['🍺', '🍻', '🥴', '🍺', '🍾', '😵‍💫'],
        'petting': ['💕', '❤️', '💖', '😊'],
        'fed': ['🎋', '🍃', '🌿', '😋'],
        'clicked': ['✨', '⭐', '💫'],
        'tossed': ['😵', '💫', '🌀'],
        'wall_hit': ['💥', '😣', '⚡'],
        'playing': ['🎾', '🎮', '⚽', '🏀', '🎯'],
        'eating': ['🍱', '🎋', '🍃', '😋', '🍜'],
        'customizing': ['✨', '👔', '🎀', '💅', '🪞'],
        'spinning': ['🌀', '💫', '😵‍💫', '🌪️', '🔄'],
        'shaking': ['😵', '🫨', '💫', '😰', '🤪'],
        'rolling': ['🌀', '💫', '😵', '🔄', '⭐'],
        'stretching': ['🙆', '✨', '💪', '🌟', '😌'],
        'waving': ['👋', '🤗', '😊', '✋', '🖐️'],
        'jumping': ['🦘', '⬆️', '🎉', '💫', '🏀'],
        'yawning': ['🥱', '😪', '💤', '😴', '🌙'],
        'sneezing': ['🤧', '💨', '😤', '🌬️', '💥'],
        'belly_rub': ['🐾', '💕', '😊', '🐼', '💖'],
        'cartwheel': ['🤸', '🎪', '⭐', '💫', '🎉', '🤸‍♀️'],
        'backflip': ['🤸', '🔄', '💫', '🎯', '⭐', '🌟'],
        'lay_on_back': ['😌', '💤', '☁️', '💭', '🌙', '😴'],
        'lay_on_side': ['😴', '💤', '☁️', '😌', '🛌', '💭'],
        'carrying': ['📦', '💪', '🎁', '📚', '🧳'],
        'sitting': ['🪑', '😌', '💭', '☕', '🧘'],
        'belly_grab': ['🤗', '😊', '💕', '🐼', '🫃'],
        'belly_jiggle': ['🫃', '😂', '🤣', '😊', '✨'],
    }
    
    def __init__(self, parent, panda_character=None, panda_level_system=None,
                 widget_collection=None, panda_closet=None, **kwargs):
        """
        Initialize panda widget with drag functionality.
        
        Args:
            parent: Parent widget
            panda_character: PandaCharacter instance for handling interactions
            panda_level_system: PandaLevelSystem instance for XP tracking
            widget_collection: WidgetCollection instance for toys/food
            panda_closet: PandaCloset instance for customization
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.panda = panda_character
        self.panda_level_system = panda_level_system
        self.widget_collection = widget_collection
        self.panda_closet = panda_closet
        self.current_animation = 'idle'
        self.animation_frame = 0
        self.animation_timer = None
        self._destroyed = False
        
        # Active item being used during eating/playing animations
        self._active_item_name = None  # Name of item (e.g. "Fresh Bamboo")
        self._active_item_emoji = None  # Emoji for the item (e.g. "🎋")
        self._active_item_type = None  # 'food' or 'toy'
        self._active_item_key = None   # Widget key (e.g. 'bamboo') for per-item responses
        
        # Eating sequence state
        self._eating_phase = 0
        self._eating_frame = 0
        
        # Dragging state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        self._drag_moved = False  # Track if actual movement occurred
        # Track drag positions for pattern detection
        self._drag_positions = []  # list of (x, y, time) tuples
        self._last_drag_time = 0  # Throttle drag events (ms)
        self._last_wall_hit_time = 0  # Cooldown for wall hit reactions
        self._last_drag_pattern_time = 0  # Cooldown for drag-pattern animations
        
        # Toss physics state
        self._toss_velocity_x = 0.0
        self._toss_velocity_y = 0.0
        self._toss_timer = None
        self._is_tossing = False
        self._prev_drag_x = 0
        self._prev_drag_y = 0
        self._prev_drag_time = 0
        
        # Jiggle physics state (belly wobble on poke)
        self._belly_jiggle = 0.0       # Current jiggle amplitude
        self._belly_jiggle_vel = 0.0   # Jiggle velocity (spring-damper)
        
        # Limb dangle physics (arms/legs swing with inertia during drag)
        # Now supports individual limb tracking
        self._dangle_arm = 0.0         # Arm dangle offset (pixels, vertical) - when both arms dangle
        self._dangle_arm_vel = 0.0     # Arm dangle velocity
        self._dangle_leg = 0.0         # Leg dangle offset (pixels, vertical) - when both legs dangle
        self._dangle_leg_vel = 0.0     # Leg dangle velocity
        self._dangle_arm_h = 0.0       # Arm horizontal dangle offset
        self._dangle_arm_h_vel = 0.0   # Arm horizontal dangle velocity
        self._dangle_leg_h = 0.0       # Leg horizontal dangle offset
        self._dangle_leg_h_vel = 0.0   # Leg horizontal dangle velocity
        # Individual limb dangle tracking
        self._dangle_left_arm = 0.0
        self._dangle_left_arm_vel = 0.0
        self._dangle_right_arm = 0.0
        self._dangle_right_arm_vel = 0.0
        self._dangle_left_leg = 0.0
        self._dangle_left_leg_vel = 0.0
        self._dangle_right_leg = 0.0
        self._dangle_right_leg_vel = 0.0
        self._dangle_left_ear = 0.0
        self._dangle_left_ear_vel = 0.0
        self._dangle_right_ear = 0.0
        self._dangle_right_ear_vel = 0.0
        self._prev_drag_vy = 0.0       # Previous vertical drag velocity for dangle
        self._prev_drag_vx = 0.0       # Previous horizontal drag velocity for dangle
        self._drag_grab_head = False   # True when drag started in head region
        self._drag_grab_part = 'body'  # Body part grabbed during drag (specific limb/ear/etc)
        self._is_upside_down = False   # True when dragged upside down by legs
        
        # Ear stretch physics (elastic stretch during drag)
        self._ear_stretch = 0.0        # Current ear stretch amount
        self._ear_stretch_vel = 0.0    # Ear stretch velocity
        
        # Shake animation decay (shared between limb and body sway calculations)
        self._shake_decay = 1.0
        
        # Autonomous walking state
        self._auto_walk_timer = None
        self._is_auto_walking = False
        self._auto_walk_target_x = 0
        self._auto_walk_target_y = 0
        self._auto_walk_step_dx = 0.0
        self._auto_walk_step_dy = 0.0
        self._auto_walk_steps_remaining = 0
        
        # Configure the proxy frame – it stays in the widget tree for API
        # compatibility but is intentionally empty / zero-size.
        if ctk:
            self.configure(fg_color="transparent", corner_radius=0, bg_color="transparent")
        else:
            try:
                parent_bg = parent.cget('bg')
                self.configure(bg=parent_bg, highlightthickness=0)
            except Exception:
                self.configure(highlightthickness=0)
        
        # ----------------------------------------------------------
        # Create a separate Toplevel window for the panda rendering.
        # ----------------------------------------------------------
        self._toplevel = tk.Toplevel(self)
        self._toplevel.overrideredirect(True)
        self._toplevel.wm_attributes('-topmost', True)
        
        # Determine canvas/toplevel background color
        if sys.platform == 'win32':
            self._canvas_bg = TRANSPARENT_COLOR
            self._toplevel.configure(bg=TRANSPARENT_COLOR)
            try:
                self._toplevel.wm_attributes('-transparentcolor', TRANSPARENT_COLOR)
            except Exception:
                pass
        else:
            self._canvas_bg = self._get_parent_bg()
            self._toplevel.configure(bg=self._canvas_bg)
        
        # Size the toplevel to hold the panda canvas + speech bubble
        self._toplevel_w = PANDA_CANVAS_W + 8
        self._toplevel_h = PANDA_CANVAS_H + 100  # extra room for bubble
        self._toplevel.geometry(f"{self._toplevel_w}x{self._toplevel_h}")
        
        # Create canvas for panda body-shaped drawing inside the Toplevel
        self.panda_canvas = tk.Canvas(
            self._toplevel,
            width=PANDA_CANVAS_W,
            height=PANDA_CANVAS_H,
            bg=self._canvas_bg,
            highlightthickness=0,
            bd=0,
        )
        self.panda_canvas.pack(side="bottom", pady=4, padx=4)
        
        # Speech bubble timer
        self._speech_timer = None
        
        # Create floating speech bubble canvas inside the Toplevel
        self._bubble_canvas = tk.Canvas(
            self._toplevel,
            width=0,
            height=0,
            bg=self._canvas_bg,
            highlightthickness=0,
            bd=0,
        )
        
        # Create info_label as a hidden helper to keep external API working.
        # Speech text is rendered on _bubble_canvas instead.
        self._speech_text = "Click me! 🐼"
        self.info_label = _SpeechProxy(self)
        
        # Show initial bubble
        self._show_speech_bubble(self._speech_text)
        
        # Keep panda_label as an alias to panda_canvas for external code compatibility
        self.panda_label = self.panda_canvas
        
        # Bind events for interaction on canvas
        self.panda_canvas.bind("<Button-3>", self._on_right_click)
        self.panda_canvas.bind("<Enter>", self._on_hover)
        self.panda_canvas.bind("<Leave>", self._on_leave)
        
        # Bind events for dragging on canvas
        self.panda_canvas.bind("<Button-1>", self._on_drag_start)
        self.panda_canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.panda_canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # Bind mouse motion for pet-by-rubbing detection
        self._rub_positions = []
        self._last_rub_time = 0
        self.panda_canvas.bind("<Motion>", self._on_mouse_motion)
        
        # Also bind to the Toplevel itself for dragging
        self._toplevel.bind("<Button-1>", self._on_drag_start)
        self._toplevel.bind("<B1-Motion>", self._on_drag_motion)
        self._toplevel.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # Draw initial panda and start animation
        self._draw_panda(0)
        self.start_animation('idle')
        
        # Position the Toplevel relative to the main window once mapped
        self._follow_main_job = None
        self.after(100, self._initial_toplevel_position)
        
        # Destroy the Toplevel when the main window is destroyed
        self._main_window = self.winfo_toplevel()
        self._destroy_bind_id = self._main_window.bind("<Destroy>", self._on_main_destroy, add=True)
        
        # Deferred background refresh – once the widget tree is fully
        # rendered the parent background colour is reliably available.
        if sys.platform != 'win32':
            self.after(100, self._refresh_canvas_bg)
        
        # Set up periodic background refresh to keep canvas blended
        # (not needed on Windows – the transparent-color key is fixed)
        self._bg_refresh_job = None
        if sys.platform != 'win32':
            self._schedule_bg_refresh()
        
        # Start autonomous walking after a short delay
        self.after(10000, self._schedule_auto_walk)
    
    # ------------------------------------------------------------------
    # Canvas-based panda drawing
    # ------------------------------------------------------------------
    
    def _get_parent_bg(self) -> str:
        """Determine appropriate canvas background to blend with the parent.
        
        Uses CustomTkinter's built-in colour detection so the canvas
        blends seamlessly (no visible box) in both light and dark modes.
        """
        # Use CTk's own detection for the most accurate parent color
        try:
            if ctk and hasattr(self, '_detect_color_of_master'):
                color = self._detect_color_of_master()
                return self._apply_appearance_mode(color)
        except Exception:
            pass
        # Walk the widget tree manually as a fallback
        try:
            widget = self.master
            while widget is not None:
                try:
                    if ctk and isinstance(widget, ctk.CTkBaseClass):
                        fg = widget.cget("fg_color")
                        if fg and fg != "transparent":
                            return self._apply_appearance_mode(fg)
                    bg = widget.cget("bg")
                    if bg and bg != "SystemButtonFace":
                        return bg
                except Exception:
                    pass
                widget = getattr(widget, 'master', None)
        except Exception:
            pass
        # Fallback to theme-based colour
        try:
            if ctk:
                mode = ctk.get_appearance_mode()
                return "#2b2b2b" if mode == "Dark" else "#f0f0f0"
        except Exception:
            pass
        return "#f0f0f0"

    # Deprecated: use _get_parent_bg instead
    _get_canvas_bg = _get_parent_bg

    def _schedule_bg_refresh(self):
        """Schedule periodic background refresh to keep canvas blended."""
        if self._destroyed:
            return
        # Refresh every 500ms to keep background in sync with theme changes
        self._refresh_canvas_bg()
        self._bg_refresh_job = self.after(500, self._schedule_bg_refresh)
    
    def _refresh_canvas_bg(self):
        """Re-detect the parent background and update both canvases."""
        if self._destroyed:
            return
        # On Windows the transparent-color key is fixed; skip refresh.
        if sys.platform == 'win32':
            return
        new_bg = self._get_parent_bg()
        # Only update if color changed to avoid unnecessary redraws
        if new_bg != self._canvas_bg:
            self._canvas_bg = new_bg
            try:
                self.panda_canvas.configure(bg=self._canvas_bg)
            except Exception:
                pass
            try:
                self._bubble_canvas.configure(bg=self._canvas_bg)
            except Exception:
                pass
            try:
                self._toplevel.configure(bg=self._canvas_bg)
            except Exception:
                pass
            # Redraw panda to ensure proper rendering with new background
            self._draw_panda(self.animation_frame)

    def _set_appearance_mode(self, mode_string):
        """Called by CustomTkinter when the appearance mode changes."""
        super()._set_appearance_mode(mode_string)
        if sys.platform != 'win32':
            self._refresh_canvas_bg()
        self._draw_panda(self.animation_frame)

    # ------------------------------------------------------------------
    # Toplevel position helpers
    # ------------------------------------------------------------------

    def _get_main_window_bounds(self):
        """Return the main application window bounds as (min_x, min_y, max_x, max_y) in screen coordinates.

        ``min_x`` / ``min_y`` are the minimum allowed origin (top-left
        corner of the application content area).  ``max_x`` / ``max_y``
        are the maximum allowed origin for the panda Toplevel so that
        it stays fully inside the application.
        """
        root = self.winfo_toplevel()
        root.update_idletasks()
        rx = root.winfo_rootx()
        ry = root.winfo_rooty()
        rw = max(1, root.winfo_width())
        rh = max(1, root.winfo_height())
        tw = max(1, self._toplevel.winfo_width())
        th = max(1, self._toplevel.winfo_height())
        min_x = rx
        min_y = ry
        max_x = max(rx, rx + rw - tw)
        max_y = max(ry, ry + rh - th)
        return min_x, min_y, max_x, max_y

    def _initial_toplevel_position(self):
        """Position the Toplevel window relative to the main app window."""
        if self._destroyed:
            return
        try:
            root = self.winfo_toplevel()
            # Read saved relative position from config
            from src.config import config
            saved_x = config.get('panda', 'position_x', default=0.98)
            saved_y = config.get('panda', 'position_y', default=0.98)
            
            root.update_idletasks()
            rx = root.winfo_rootx()
            ry = root.winfo_rooty()
            rw = max(1, root.winfo_width())
            rh = max(1, root.winfo_height())
            
            # Convert relative coords to screen position (anchor "se")
            abs_x = int(rx + saved_x * rw - self._toplevel_w)
            abs_y = int(ry + saved_y * rh - self._toplevel_h)
            self._toplevel.geometry(f"+{abs_x}+{abs_y}")
        except Exception as e:
            logger.debug(f"Initial toplevel position error: {e}")
        
        # Start periodic follow
        self._start_follow_main()

    def _start_follow_main(self):
        """Periodically keep the Toplevel near the main window when not dragging."""
        if self._destroyed:
            return
        self._follow_main_job = self.after(500, self._follow_main_tick)

    def _follow_main_tick(self):
        """Re-check main window position and adjust if the window moved."""
        if self._destroyed:
            return
        # Only follow when not being dragged or tossed
        if not self.is_dragging and not self._is_tossing:
            try:
                root = self.winfo_toplevel()
                root.update_idletasks()
                rx = root.winfo_rootx()
                ry = root.winfo_rooty()
                rw = max(1, root.winfo_width())
                rh = max(1, root.winfo_height())
                
                # Get current toplevel screen position
                tx = self._toplevel.winfo_x()
                ty = self._toplevel.winfo_y()
                
                # Clamp toplevel so it stays within screen bounds but allow
                # it to be anywhere — only pull it back if main window moved.
                # We store _last_root_geom to detect main-window movement.
                cur_geom = (rx, ry, rw, rh)
                prev = getattr(self, '_last_root_geom', None)
                if prev is not None and prev != cur_geom:
                    # Main window moved; shift the toplevel by the delta.
                    drx = rx - prev[0]
                    dry = ry - prev[1]
                    self._toplevel.geometry(f"+{tx + drx}+{ty + dry}")
                self._last_root_geom = cur_geom
            except Exception:
                pass
        self._follow_main_job = self.after(500, self._follow_main_tick)

    def _on_main_destroy(self, event=None):
        """Destroy the Toplevel when the main window is destroyed."""
        if event and event.widget is self._main_window:
            self.destroy()

    def _show_speech_bubble(self, text: str):
        """Draw a floating speech bubble next to the panda on _bubble_canvas."""
        if self._destroyed:
            return

        self._speech_text = text
        if not text or text.strip() == "":
            self._bubble_canvas.pack_forget()
            return

        bc = self._bubble_canvas
        bc.delete("all")

        # Measure text to determine bubble size
        font = ("Arial Bold", 16)
        # Wrap long text
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= BUBBLE_MAX_CHARS_PER_LINE:
                current_line = (current_line + " " + word).strip()
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        if not lines:
            lines = [text[:BUBBLE_MAX_CHARS_PER_LINE]]

        display_text = "\n".join(lines)
        line_count = len(lines)
        max_line_len = max(len(l) for l in lines) if lines else 0

        # Bubble dimensions
        bubble_w = min(max_line_len * BUBBLE_CHAR_WIDTH + BUBBLE_PAD_X * 2, BUBBLE_MAX_WIDTH)
        bubble_h = line_count * BUBBLE_LINE_HEIGHT + BUBBLE_PAD_Y * 2

        canvas_w = bubble_w + 4
        canvas_h = bubble_h + BUBBLE_TAIL_HEIGHT + 4

        bc.configure(width=canvas_w, height=canvas_h, bg=self._canvas_bg)

        # Draw rounded rectangle bubble
        x1, y1 = 2, 2
        x2, y2 = bubble_w + 2, bubble_h + 2
        r = BUBBLE_CORNER_RADIUS
        # Rounded rect via polygon
        bc.create_polygon(
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
            fill="white", outline="#888888", width=1,
            smooth=True, tags="bubble"
        )

        # Draw tail (small triangle pointing down toward panda)
        tail_cx = bubble_w // 2 + 2
        bc.create_polygon(
            tail_cx - 6, y2 - 1,
            tail_cx + 6, y2 - 1,
            tail_cx, y2 + BUBBLE_TAIL_HEIGHT,
            fill="white", outline="#888888", width=1,
            tags="tail"
        )
        # Cover the tail-bubble border
        bc.create_line(tail_cx - 5, y2, tail_cx + 5, y2,
                       fill="white", width=2, tags="tail_cover")

        # Draw text
        bc.create_text(
            (x1 + x2) // 2, (y1 + y2) // 2,
            text=display_text, font=font,
            fill="#222222", width=bubble_w - BUBBLE_PAD_X,
            justify="center", tags="text"
        )

        # Place bubble above panda canvas using place for fixed positioning
        # to avoid layout re-flow that causes the widget to resize
        if not bc.winfo_ismapped():
            bc.pack(pady=(0, 0), before=self.panda_canvas)

        # Auto-hide after a delay
        if self._speech_timer:
            try:
                self.after_cancel(self._speech_timer)
            except Exception:
                pass
        self._speech_timer = self.after(5000, self._hide_speech_bubble)

    def _hide_speech_bubble(self):
        """Hide the speech bubble after timeout."""
        if self._destroyed:
            return
        self._bubble_canvas.pack_forget()
        self._speech_timer = None
    
    def _draw_panda(self, frame_idx: int):
        """Draw the panda on the canvas for the given animation frame.
        
        The panda is drawn with proper body proportions and black/white
        coloring. The frame_idx drives limb positions for walking.
        """
        c = self.panda_canvas
        c.delete("all")
        
        w = PANDA_CANVAS_W
        h = PANDA_CANVAS_H
        cx = w // 2  # center x
        
        anim = self.current_animation
        
        # --- Determine limb offsets for animations ---
        # Cycle through 60 frames for smooth animation
        phase = (frame_idx % 60) / 60.0 * 2 * math.pi
        
        if anim in ('idle', 'working', 'sarcastic', 'thinking'):
            # Lively idle: body sways, head bobs, arms swing with layered motion
            idle_sub = (frame_idx % 180) / 180.0
            leg_swing = math.sin(phase * 1.2) * 3 + math.sin(phase * 0.4) * 2
            arm_swing = math.sin(phase) * 6 + math.sin(phase * 2.5) * 3 + math.cos(phase * 0.7) * 2
            body_bob = math.sin(phase * 0.8) * 4 + abs(math.sin(phase * 1.6)) * 2 + math.sin(phase * 0.3) * 2
            # Occasional micro-bounce
            if idle_sub < 0.06:
                body_bob -= idle_sub * 40
        elif anim == 'carrying':
            # Distinct carrying animation - stable, no shake/spin
            leg_swing = math.sin(phase) * 4  # Gentle walk
            arm_swing = -8  # Arms held up carrying something
            body_bob = abs(math.sin(phase)) * 1.5  # Minimal bob
        elif anim == 'dragging':
            # Gentler dragging — legs dangle, arms flail less
            leg_swing = math.sin(phase) * 8
            arm_swing = math.sin(phase + math.pi) * 6
            body_bob = abs(math.sin(phase)) * 2
        elif anim == 'tossed':
            # Wild toss — exaggerated flailing
            leg_swing = math.sin(phase * 1.5) * 18
            arm_swing = math.sin(phase * 2 + math.pi) * 16
            body_bob = abs(math.sin(phase * 1.5)) * 6
        elif anim == 'wall_hit':
            # Impact stun — shudder and recoil
            leg_swing = math.sin(phase * 3) * 5
            arm_swing = math.sin(phase * 4) * 8
            body_bob = -abs(math.sin(phase * 3)) * 4
        elif anim == 'dancing':
            dance_cycle = (frame_idx % 72) / 72.0
            if dance_cycle < 0.25:
                # Side sway left with arm pump
                leg_swing = math.sin(phase) * 16 + math.cos(phase * 0.5) * 4
                arm_swing = math.sin(phase * 2) * 18 + math.sin(phase * 0.7) * 4
                body_bob = math.sin(phase * 2) * 6 + abs(math.sin(phase * 3)) * 3
            elif dance_cycle < 0.5:
                # Spin move with body twist
                leg_swing = math.sin(phase * 3) * 12 + math.cos(phase * 1.5) * 4
                arm_swing = -abs(math.sin(phase * 2)) * 20
                body_bob = abs(math.sin(phase * 3)) * 7 + math.sin(phase * 1.5) * 3
            elif dance_cycle < 0.75:
                # Side sway right with opposite arm
                leg_swing = -math.sin(phase) * 16 - math.cos(phase * 0.5) * 4
                arm_swing = math.sin(phase * 2 + math.pi) * 18 + math.cos(phase * 0.7) * 4
                body_bob = math.sin(phase * 2) * 6 + abs(math.sin(phase * 3)) * 3
            else:
                # Jump and arms up with twist
                leg_swing = math.sin(phase * 2) * 10
                arm_swing = -abs(math.sin(phase)) * 22
                body_bob = -abs(math.sin(phase * 2)) * 10 + math.sin(phase * 4) * 3
        elif anim == 'celebrating':
            celeb_cycle = (frame_idx % 48) / 48.0
            if celeb_cycle < 0.33:
                # Arms pumping up
                leg_swing = math.sin(phase) * 6
                arm_swing = -abs(math.sin(phase * 2)) * 20
                body_bob = abs(math.sin(phase)) * 4
            elif celeb_cycle < 0.66:
                # Happy bouncing
                leg_swing = math.sin(phase * 2) * 10
                arm_swing = math.sin(phase * 3) * 14
                body_bob = -abs(math.sin(phase * 2)) * 7
            else:
                # Spinning celebration
                leg_swing = math.sin(phase * 2) * 12
                arm_swing = math.cos(phase * 2) * 16
                body_bob = math.sin(phase * 3) * 5
        elif anim in ('sleeping', 'laying_down'):
            # Gradual settling with gentle breathing
            settle_phase = min(1.0, frame_idx / 30.0)  # settle over ~30 frames
            leg_swing = (1 - settle_phase) * math.sin(phase) * 3
            arm_swing = settle_phase * 5  # arms rest outward
            body_bob = settle_phase * 25 + math.sin(phase * 0.3) * 2  # lower body, gentle breathing
        elif anim in ('laying_back', 'laying_side'):
            leg_swing = math.sin(phase * 0.3) * 2
            arm_swing = 5
            body_bob = 30 + math.sin(phase * 0.3) * 2
        elif anim == 'sitting':
            # Squatting pose: legs bend wide, body drops low, arms rest on knees
            sit_phase = min(1.0, frame_idx / 24.0)  # settle over ~24 frames
            leg_swing = sit_phase * 14  # Legs spread/bent forward (wide squat)
            arm_swing = sit_phase * 10 + math.sin(phase * 0.5) * 2  # Arms resting outward on knees
            body_bob = sit_phase * 28 + math.sin(phase * 0.4) * 2  # Body drops low for squat
        elif anim == 'belly_grab':
            # Both hands reach to belly, grab it, and shake causing jiggle
            grab_phase = min(1.0, frame_idx / 12.0)
            grab_cycle = (frame_idx % 48) / 48.0
            if grab_cycle < 0.25:
                # Arms reaching inward to belly
                ramp = grab_cycle / 0.25
                arm_swing = -ramp * 20  # Both arms move strongly inward
                leg_swing = ramp * 3
                body_bob = ramp * 4
            elif grab_cycle < 0.75:
                # Grabbing and shaking belly — wobble effect
                shake_t = (grab_cycle - 0.25) / 0.5
                arm_swing = -20 + math.sin(shake_t * 8 * math.pi) * 4  # Arms vibrate on belly
                leg_swing = math.sin(shake_t * 6 * math.pi) * 3
                body_bob = 4 + math.sin(shake_t * 8 * math.pi) * 5  # Jiggle wobble
            else:
                # Release, settle back
                settle = (grab_cycle - 0.75) / 0.25
                arm_swing = -20 * (1 - settle) + math.sin(phase) * 2 * (1 - settle)
                leg_swing = 3 * (1 - settle)
                body_bob = 4 * (1 - settle) + math.sin(phase * 0.5) * 2
        elif anim == 'belly_jiggle':
            # Belly poke jiggle - bouncy wobble that decays
            jiggle_phase = min(1.0, frame_idx / 36.0)  # decay over ~36 frames
            decay = 1.0 - jiggle_phase
            leg_swing = math.sin(phase * 3) * 4 * decay
            arm_swing = math.sin(phase * 4) * 8 * decay
            body_bob = math.sin(phase * 5) * 6 * decay
        elif anim == 'rage':
            leg_swing = math.sin(phase * 3) * 8
            arm_swing = math.sin(phase * 3) * 10
            body_bob = math.sin(phase * 4) * 4
        elif anim == 'petting':
            pet_cycle = (frame_idx % 48) / 48.0
            leg_swing = math.sin(phase * 1.2) * 3
            arm_swing = math.sin(phase * 1.5) * 6 + math.sin(phase * 3) * 2
            body_bob = math.sin(phase) * 4 + abs(math.sin(phase * 2)) * 2.5
            # Happy wiggle burst
            if pet_cycle < 0.2:
                body_bob += math.sin(pet_cycle * 25) * 3
        elif anim == 'playing':
            play_cycle = (frame_idx % 60) / 60.0
            if play_cycle < 0.3:
                # Bouncing with excitement
                leg_swing = math.sin(phase * 2) * 12
                arm_swing = math.sin(phase * 3) * 16
                body_bob = -abs(math.sin(phase * 2)) * 6
            elif play_cycle < 0.6:
                # Playful swipe at toy
                leg_swing = math.sin(phase) * 8
                arm_swing = -abs(math.sin(phase * 2)) * 18
                body_bob = abs(math.sin(phase)) * 4
            else:
                # Happy tumble
                leg_swing = math.sin(phase * 2) * 14
                arm_swing = math.cos(phase * 2) * 12
                body_bob = math.sin(phase * 3) * 5
        elif anim == 'eating':
            eat_cycle = (frame_idx % 48) / 48.0
            if eat_cycle < 0.3:
                # Reaching for food
                leg_swing = 0
                arm_swing = -abs(math.sin(phase * 2)) * 14
                body_bob = math.sin(phase) * 2
            elif eat_cycle < 0.7:
                # Munching - faster arm motion
                leg_swing = 0
                arm_swing = -12 + math.sin(phase * 4) * 6
                body_bob = math.sin(phase * 3) * 3 + 1
            else:
                # Satisfied lean back
                settle = (eat_cycle - 0.7) / 0.3
                leg_swing = 0
                arm_swing = -12 * (1 - settle) + math.sin(phase) * 3
                body_bob = 1 + settle * 3 + math.sin(phase * 0.5) * 2
        elif anim == 'customizing':
            # Preening, gentle sway with arms up
            leg_swing = 0
            arm_swing = math.sin(phase) * 6
            body_bob = math.sin(phase) * 3
        elif anim == 'spinning':
            # Full-body spin: limbs follow a rotation cycle, body sways side to side
            spin_cycle = (frame_idx % 48) / 48.0
            spin_angle = spin_cycle * 2 * math.pi  # One full rotation per cycle
            # Arms and legs follow the rotation so the whole body appears to turn
            leg_swing = math.sin(spin_angle) * 12
            arm_swing = math.cos(spin_angle) * 14
            body_bob = abs(math.sin(spin_angle * 2)) * 4
        elif anim == 'shaking':
            # Intense rapid side-to-side shaking with head wobble
            self._shake_decay = max(0.3, 1.0 - (frame_idx % 60) / 60.0)  # Decays over time
            leg_swing = math.sin(phase * 10) * 12 * self._shake_decay
            arm_swing = math.sin(phase * 10 + math.pi/3) * 16 * self._shake_decay
            body_bob = math.sin(phase * 12) * 8 * self._shake_decay + math.cos(phase * 7) * 4 * self._shake_decay
        elif anim == 'rolling':
            leg_swing = math.sin(phase * 2) * 15
            arm_swing = math.cos(phase * 2) * 15
            body_bob = math.sin(phase) * 8
        elif anim == 'clicked':
            # Bouncy multi-phase click reaction with squash & stretch feel
            click_phase = (frame_idx % 30) / 30.0
            if click_phase < 0.1:
                # Squash down (anticipation)
                sq = click_phase / 0.1
                body_bob = sq * 12
                arm_swing = sq * 8
                leg_swing = sq * 4
            elif click_phase < 0.25:
                # Launch up with arms wide
                launch = (click_phase - 0.1) / 0.15
                body_bob = 12 - launch * 30
                arm_swing = 8 - launch * 28
                leg_swing = 4 - launch * 14
            elif click_phase < 0.4:
                # Peak of jump, arms out
                peak = (click_phase - 0.25) / 0.15
                body_bob = -18 + math.sin(peak * math.pi) * 4
                arm_swing = -20 + math.sin(peak * math.pi * 2) * 12
                leg_swing = -10 + math.sin(peak * math.pi) * 6
            elif click_phase < 0.55:
                # Fall down
                fall = (click_phase - 0.4) / 0.15
                body_bob = -18 + fall * 26
                arm_swing = -20 + fall * 26
                leg_swing = -10 + fall * 16
            elif click_phase < 0.7:
                # Landing squash bounce
                land = (click_phase - 0.55) / 0.15
                body_bob = 8 * math.sin(land * math.pi) + 2
                arm_swing = 6 * math.sin(land * math.pi * 1.5)
                leg_swing = 6 * math.sin(land * math.pi)
            else:
                # Happy settle with wiggle
                settle = (click_phase - 0.7) / 0.3
                body_bob = math.sin(settle * math.pi * 3) * 4 * (1 - settle)
                arm_swing = math.sin(phase * 2) * 6 * (1 - settle * 0.5)
                leg_swing = math.sin(phase * 1.5) * 3 * (1 - settle)
        elif anim == 'stretching':
            stretch_cycle = (frame_idx % 60) / 60.0
            if stretch_cycle < 0.2:
                # Arms starting to raise
                leg_swing = 0
                arm_swing = -stretch_cycle * 5 * 22
                body_bob = -stretch_cycle * 5 * 4
            elif stretch_cycle < 0.5:
                # Full stretch with slight sway
                leg_swing = math.sin(phase * 0.5) * 2
                arm_swing = -22 + math.sin(phase) * 4
                body_bob = -6 + math.sin(phase * 0.8) * 2
            elif stretch_cycle < 0.7:
                # Side stretch
                offset = (stretch_cycle - 0.5) / 0.2
                leg_swing = math.sin(offset * math.pi) * 8
                arm_swing = -18 + math.sin(phase) * 6
                body_bob = -4 + math.sin(phase) * 3
            else:
                # Settling back down
                settle = (stretch_cycle - 0.7) / 0.3
                leg_swing = 0
                arm_swing = -22 * (1 - settle) + math.sin(phase) * 3
                body_bob = -6 * (1 - settle)
        elif anim == 'waving':
            wave_cycle = (frame_idx % 48) / 48.0
            if wave_cycle < 0.15:
                # Arm raising
                ramp = wave_cycle / 0.15
                leg_swing = 0
                arm_swing = -ramp * 18
                body_bob = ramp * 2
            elif wave_cycle < 0.7:
                # Waving back and forth
                leg_swing = math.sin(phase * 0.5) * 2
                arm_swing = -18 + math.sin(phase * 3) * 10
                body_bob = 2 + math.sin(phase * 2) * 2
            else:
                # Arm lowering
                settle = (wave_cycle - 0.7) / 0.3
                leg_swing = 0
                arm_swing = -18 * (1 - settle) + math.sin(phase * 2) * 5 * (1 - settle)
                body_bob = 2 * (1 - settle)
        elif anim == 'jumping':
            jump_cycle = (frame_idx % 36) / 36.0
            if jump_cycle < 0.15:
                # Crouch down — both legs bend together
                crouch = jump_cycle / 0.15
                leg_swing = crouch * 10  # Legs bend down (squat)
                arm_swing = crouch * 6
                body_bob = crouch * 14  # Body drops in crouch
            elif jump_cycle < 0.35:
                # Launch upward — both feet spring up, body rises high
                launch = (jump_cycle - 0.15) / 0.2
                leg_swing = 10 - launch * 20  # Legs snap up together
                arm_swing = 6 - launch * 28  # Arms swing up
                body_bob = 14 - launch * 44  # Large upward movement
            elif jump_cycle < 0.55:
                # Airborne / peak — legs tucked, arms up, body high
                air = (jump_cycle - 0.35) / 0.2
                leg_swing = -10 + math.sin(air * math.pi) * 3  # Both legs tucked up
                arm_swing = -22 + math.sin(air * math.pi) * 4  # Arms raised
                body_bob = -30 + math.sin(air * math.pi) * 4  # Peak height
            elif jump_cycle < 0.75:
                # Falling down — legs extend for landing
                fall = (jump_cycle - 0.55) / 0.2
                leg_swing = -10 + fall * 14  # Legs come back down together
                arm_swing = -22 + fall * 26
                body_bob = -30 + fall * 38  # Fall back to ground
            else:
                # Landing bounce — slight squash
                land = (jump_cycle - 0.75) / 0.25
                leg_swing = 4 * math.sin(land * math.pi * 2) * (1 - land)
                arm_swing = 4 * math.sin(land * math.pi * 2) * (1 - land)
                body_bob = 8 * math.sin(land * math.pi) * (1 - land * 0.7)
        elif anim == 'yawning':
            yawn_cycle = (frame_idx % 48) / 48.0
            if yawn_cycle < 0.15:
                # Inhale, lean back slightly
                ramp = yawn_cycle / 0.15
                leg_swing = 0
                arm_swing = ramp * 6
                body_bob = ramp * 4
            elif yawn_cycle < 0.5:
                # Full yawn, head tilted back, arms up stretch
                leg_swing = 0
                arm_swing = 6 + math.sin(phase * 0.5) * 4
                body_bob = 4 + math.sin(phase * 0.3) * 2
            elif yawn_cycle < 0.7:
                # Closing yawn
                settle = (yawn_cycle - 0.5) / 0.2
                leg_swing = 0
                arm_swing = 6 * (1 - settle)
                body_bob = 4 * (1 - settle)
            else:
                # Post-yawn drowsy sway
                leg_swing = 0
                arm_swing = math.sin(phase * 0.8) * 3
                body_bob = math.sin(phase * 0.5) * 2 + 1
        elif anim == 'sneezing':
            sneeze_cycle = (frame_idx % 36) / 36.0
            if sneeze_cycle < 0.25:
                # Building up - nose tickle, leaning back
                build = sneeze_cycle / 0.25
                body_bob = -build * 8
                leg_swing = 0
                arm_swing = build * 5
            elif sneeze_cycle < 0.35:
                # SNEEZE! - sharp forward snap
                snap = (sneeze_cycle - 0.25) / 0.1
                body_bob = -8 + snap * 28
                leg_swing = snap * 6
                arm_swing = 5 - snap * 12
            elif sneeze_cycle < 0.5:
                # Recoil
                recoil = (sneeze_cycle - 0.35) / 0.15
                body_bob = 20 - recoil * 18
                leg_swing = 6 * (1 - recoil)
                arm_swing = -7 + recoil * 10
            else:
                # Recovery - gentle sway
                leg_swing = math.sin(phase * 0.5) * 2
                arm_swing = math.sin(phase * 0.8) * 3
                body_bob = 2 + math.sin(phase * 0.5) * 2
        elif anim == 'belly_rub':
            # Belly rub: arms move inward to belly and rub in circular motion, body rocks gently
            rub_cycle = (frame_idx % 60) / 60.0
            rub_phase = rub_cycle * 2 * math.pi
            if rub_cycle < 0.15:
                # Arms reaching toward belly
                ramp = rub_cycle / 0.15
                arm_swing = -ramp * 14  # Arms inward
                leg_swing = ramp * 3
                body_bob = ramp * 4
            elif rub_cycle < 0.75:
                # Rubbing belly - circular arm motion with gentle body sway
                rub_t = (rub_cycle - 0.15) / 0.6
                arm_swing = -14 + math.sin(rub_t * 6 * math.pi) * 6  # Circular rubbing
                leg_swing = math.sin(rub_t * 4 * math.pi) * 3 + math.sin(rub_t * 2 * math.pi) * 2
                body_bob = 4 + math.sin(rub_t * 3 * math.pi) * 3  # Gentle rocking
            else:
                # Settling back, satisfied
                settle = (rub_cycle - 0.75) / 0.25
                arm_swing = -14 * (1 - settle) + math.sin(phase) * 3 * (1 - settle)
                leg_swing = 3 * (1 - settle)
                body_bob = 4 * (1 - settle) + math.sin(phase * 0.5) * 2
        elif anim == 'cartwheel':
            # Full dramatic cartwheel with body rotation and ground contact
            cart_cycle = (frame_idx % 36) / 36.0  # Slower for more detail
            rotation = cart_cycle * 2 * math.pi
            # Multi-phase cartwheel: windup, rotate, land
            if cart_cycle < 0.15:
                # Wind-up crouch
                ramp = cart_cycle / 0.15
                leg_swing = ramp * 8
                arm_swing = -ramp * 10
                body_bob = ramp * 6
            elif cart_cycle < 0.75:
                # Full rotation phase with large circular limb motion
                rot_t = (cart_cycle - 0.15) / 0.6
                rot_angle = rot_t * 2 * math.pi
                leg_swing = math.cos(rot_angle) * 30  # Large circular motion
                arm_swing = math.sin(rot_angle) * 30  # Opposite phase
                body_bob = -abs(math.sin(rot_angle)) * 18 + math.sin(rot_angle * 2) * 5
            else:
                # Landing with bounce
                land = (cart_cycle - 0.75) / 0.25
                leg_swing = 30 * (1 - land) * math.cos(land * math.pi)
                arm_swing = math.sin(land * math.pi * 2) * 10 * (1 - land)
                body_bob = 8 * math.sin(land * math.pi) * (1 - land * 0.6)
        elif anim == 'backflip':
            # Dramatic backflip with full rotation and landing
            flip_phase = (frame_idx % 36) / 36.0  # Slower for detail
            if flip_phase < 0.2:
                # Crouch with arms back
                ramp = flip_phase / 0.2
                leg_swing = ramp * 6
                arm_swing = ramp * 8
                body_bob = ramp * 12
            elif flip_phase < 0.35:
                # Launch upward
                launch = (flip_phase - 0.2) / 0.15
                leg_swing = 6 - launch * 16
                arm_swing = 8 - launch * 30
                body_bob = 12 - launch * 35
            elif flip_phase < 0.7:
                # Full rotation in air
                flip_t = (flip_phase - 0.35) / 0.35
                flip_angle = flip_t * 2 * math.pi
                leg_swing = math.sin(flip_angle) * 35
                arm_swing = math.cos(flip_angle) * 35
                body_bob = -23 + math.sin(flip_angle) * 8
            elif flip_phase < 0.85:
                # Landing
                land = (flip_phase - 0.7) / 0.15
                leg_swing = 35 * (1 - land) * math.sin(land * math.pi * 0.5)
                arm_swing = 35 * (1 - land) * math.cos(land * math.pi * 0.5)
                body_bob = -23 + land * 28
            else:
                # Bounce settle
                settle = (flip_phase - 0.85) / 0.15
                leg_swing = math.sin(settle * math.pi * 2) * 5 * (1 - settle)
                arm_swing = math.sin(settle * math.pi * 3) * 8 * (1 - settle)
                body_bob = 5 * math.sin(settle * math.pi) * (1 - settle * 0.7)
        elif anim == 'lay_on_back':
            # Lying on back: body low, arms spread wide, legs splayed up
            leg_swing = -8 + math.sin(phase * 0.4) * 2  # Legs up and slightly wiggling
            arm_swing = 18 + math.sin(phase * 0.3) * 2  # Arms spread wide outward
            body_bob = 50  # Very low position (on ground)
        elif anim == 'lay_on_side':
            # Lying on side: body tilted, legs together, arm tucked
            leg_swing = 6 + math.sin(phase * 0.3) * 2  # Legs slightly forward together
            arm_swing = -8  # Arm resting forward (pillow-style)
            body_bob = 45  # Low position (on ground)
        else:
            # Default walking for fed, etc.
            leg_swing = math.sin(phase) * 8
            arm_swing = math.sin(phase + math.pi) * 6
            body_bob = abs(math.sin(phase)) * 2
        
        # --- Subtle breathing (body scale oscillation) ---
        breath_scale = 1.0
        if anim == 'spinning':
            # Horizontal squeeze/stretch to simulate the body turning
            spin_cycle = (frame_idx % 48) / 48.0
            spin_angle = spin_cycle * 2 * math.pi
            breath_scale = 0.55 + 0.45 * abs(math.cos(spin_angle))  # Narrow when sideways, full when facing
        elif anim in ('idle', 'working', 'sarcastic', 'thinking'):
            breath_scale = 1.0 + math.sin(phase * 0.5) * 0.015
        elif anim == 'lay_on_side':
            # Squeeze body horizontally to simulate being viewed from a tilted angle
            breath_scale = 0.7 + math.sin(phase * 0.3) * 0.02
        elif anim in ('sleeping', 'laying_down', 'laying_back', 'laying_side', 'sitting'):
            breath_scale = 1.0 + math.sin(phase * 0.3) * 0.025
        
        # --- Jiggle physics (spring-damper for belly wobble) ---
        self._belly_jiggle_vel = (self._belly_jiggle_vel - self._belly_jiggle * self.JIGGLE_SPRING) * self.JIGGLE_DAMPING
        self._belly_jiggle += self._belly_jiggle_vel
        if abs(self._belly_jiggle) < 0.3 and abs(self._belly_jiggle_vel) < 0.3:
            self._belly_jiggle = 0.0
            self._belly_jiggle_vel = 0.0
        
        # --- Individual limb dangle physics (only non-grabbed limbs dangle) ---
        if anim == 'dragging' and self.is_dragging:
            # Determine which limbs should dangle based on what's being grabbed
            grabbed_part = self._drag_grab_part
            
            # Left arm dangles unless it's being grabbed
            if grabbed_part != 'left_arm':
                self._dangle_left_arm_vel += self._prev_drag_vy * self.DANGLE_ARM_FACTOR
                self._dangle_left_arm_vel += -self._prev_drag_vx * self.DANGLE_ARM_H_FACTOR * 0.5
            else:
                # Grabbed arm doesn't dangle - reset it
                self._dangle_left_arm = 0.0
                self._dangle_left_arm_vel = 0.0
            
            # Right arm dangles unless it's being grabbed
            if grabbed_part != 'right_arm':
                self._dangle_right_arm_vel += self._prev_drag_vy * self.DANGLE_ARM_FACTOR
                self._dangle_right_arm_vel += -self._prev_drag_vx * self.DANGLE_ARM_H_FACTOR * 0.5
            else:
                self._dangle_right_arm = 0.0
                self._dangle_right_arm_vel = 0.0
            
            # Left leg dangles unless it's being grabbed
            if grabbed_part != 'left_leg':
                self._dangle_left_leg_vel += self._prev_drag_vy * self.DANGLE_LEG_FACTOR
                self._dangle_left_leg_vel += -self._prev_drag_vx * self.DANGLE_LEG_H_FACTOR * 0.5
            else:
                self._dangle_left_leg = 0.0
                self._dangle_left_leg_vel = 0.0
            
            # Right leg dangles unless it's being grabbed
            if grabbed_part != 'right_leg':
                self._dangle_right_leg_vel += self._prev_drag_vy * self.DANGLE_LEG_FACTOR
                self._dangle_right_leg_vel += -self._prev_drag_vx * self.DANGLE_LEG_H_FACTOR * 0.5
            else:
                self._dangle_right_leg = 0.0
                self._dangle_right_leg_vel = 0.0
            
            # Left ear stretches unless it's being grabbed
            if grabbed_part != 'left_ear':
                self._dangle_left_ear_vel += self._prev_drag_vy * 0.2
            else:
                self._dangle_left_ear = 0.0
                self._dangle_left_ear_vel = 0.0
            
            # Right ear stretches unless it's being grabbed
            if grabbed_part != 'right_ear':
                self._dangle_right_ear_vel += self._prev_drag_vy * 0.2
            else:
                self._dangle_right_ear = 0.0
                self._dangle_right_ear_vel = 0.0
        
        # Apply spring-damper physics to all individual limbs
        self._dangle_left_arm_vel = (self._dangle_left_arm_vel - self._dangle_left_arm * self.DANGLE_SPRING) * self.DANGLE_DAMPING
        self._dangle_left_arm += self._dangle_left_arm_vel
        self._dangle_right_arm_vel = (self._dangle_right_arm_vel - self._dangle_right_arm * self.DANGLE_SPRING) * self.DANGLE_DAMPING
        self._dangle_right_arm += self._dangle_right_arm_vel
        self._dangle_left_leg_vel = (self._dangle_left_leg_vel - self._dangle_left_leg * self.DANGLE_SPRING) * self.DANGLE_DAMPING
        self._dangle_left_leg += self._dangle_left_leg_vel
        self._dangle_right_leg_vel = (self._dangle_right_leg_vel - self._dangle_right_leg * self.DANGLE_SPRING) * self.DANGLE_DAMPING
        self._dangle_right_leg += self._dangle_right_leg_vel
        self._dangle_left_ear_vel = (self._dangle_left_ear_vel - self._dangle_left_ear * self.EAR_STRETCH_SPRING) * self.EAR_STRETCH_DAMPING
        self._dangle_left_ear += self._dangle_left_ear_vel
        self._dangle_right_ear_vel = (self._dangle_right_ear_vel - self._dangle_right_ear * self.EAR_STRETCH_SPRING) * self.EAR_STRETCH_DAMPING
        self._dangle_right_ear += self._dangle_right_ear_vel
        
        # Clamp small values to zero
        if abs(self._dangle_left_arm) < 0.2 and abs(self._dangle_left_arm_vel) < 0.2:
            self._dangle_left_arm = 0.0
            self._dangle_left_arm_vel = 0.0
        if abs(self._dangle_right_arm) < 0.2 and abs(self._dangle_right_arm_vel) < 0.2:
            self._dangle_right_arm = 0.0
            self._dangle_right_arm_vel = 0.0
        if abs(self._dangle_left_leg) < 0.2 and abs(self._dangle_left_leg_vel) < 0.2:
            self._dangle_left_leg = 0.0
            self._dangle_left_leg_vel = 0.0
        if abs(self._dangle_right_leg) < 0.2 and abs(self._dangle_right_leg_vel) < 0.2:
            self._dangle_right_leg = 0.0
            self._dangle_right_leg_vel = 0.0
        if abs(self._dangle_left_ear) < 0.2 and abs(self._dangle_left_ear_vel) < 0.2:
            self._dangle_left_ear = 0.0
            self._dangle_left_ear_vel = 0.0
        if abs(self._dangle_right_ear) < 0.2 and abs(self._dangle_right_ear_vel) < 0.2:
            self._dangle_right_ear = 0.0
            self._dangle_right_ear_vel = 0.0
        
        # Keep old dangle variables for backward compatibility (set to average)
        self._dangle_arm = (self._dangle_left_arm + self._dangle_right_arm) / 2
        self._dangle_leg = (self._dangle_left_leg + self._dangle_right_leg) / 2
        self._dangle_arm_h = 0  # Horizontal incorporated into individual limbs
        self._dangle_leg_h = 0
        
        # --- Ear stretch physics (elastic spring-back) ---
        if anim == 'dragging' and self.is_dragging:
            # Ears stretch downward when dragged upward (opposing motion)
            self._ear_stretch_vel += self._prev_drag_vy * self.EAR_STRETCH_FACTOR
        self._ear_stretch_vel = (self._ear_stretch_vel - self._ear_stretch * self.EAR_STRETCH_SPRING) * self.EAR_STRETCH_DAMPING
        self._ear_stretch += self._ear_stretch_vel
        self._ear_stretch = max(-self.EAR_STRETCH_MAX, min(self.EAR_STRETCH_MAX, self._ear_stretch))
        if abs(self._ear_stretch) < 0.2 and abs(self._ear_stretch_vel) < 0.2:
            self._ear_stretch = 0.0
            self._ear_stretch_vel = 0.0
        
        by = body_bob  # vertical body offset
        
        # --- Body sway (horizontal offset for turning/direction changes) ---
        body_sway = 0
        if anim == 'dancing':
            body_sway = math.sin(phase * 1.5) * 6
        elif anim == 'cartwheel':
            cart_cycle = (frame_idx % 36) / 36.0
            if 0.15 < cart_cycle < 0.75:
                rot_t = (cart_cycle - 0.15) / 0.6
                body_sway = math.sin(rot_t * 2 * math.pi) * 15
        elif anim == 'spinning':
            # Large sway to simulate the body rotating around its center
            spin_cycle = (frame_idx % 48) / 48.0
            spin_angle = spin_cycle * 2 * math.pi
            body_sway = math.sin(spin_angle) * 18
        elif anim == 'belly_rub':
            rub_cycle = (frame_idx % 60) / 60.0
            if 0.15 < rub_cycle < 0.75:
                body_sway = math.sin((rub_cycle - 0.15) / 0.6 * 4 * math.pi) * 4
        elif anim in ('idle', 'working', 'sarcastic', 'thinking'):
            body_sway = math.sin(phase * 0.3) * 2
        elif anim == 'lay_on_side':
            # Large sway to tilt the body to one side (simulating 90-degree rotation)
            body_sway = 22
        elif anim == 'celebrating':
            body_sway = math.sin(phase * 2) * 5
        elif anim == 'backflip':
            body_sway = math.sin(phase * 2) * 4
        elif anim == 'shaking':
            body_sway = math.sin(phase * 12) * 8 * self._shake_decay
        
        # --- Determine eye style based on animation ---
        eye_style = 'normal'
        if anim == 'sleeping' or anim in ('laying_down', 'laying_back', 'laying_side'):
            # Gradual eye closing for sleep transitions
            cycle = frame_idx % 16
            if cycle < 4:
                eye_style = 'half'
            else:
                eye_style = 'closed'
        elif anim == 'sitting':
            eye_style = 'half'
        elif anim == 'belly_grab':
            eye_style = 'happy'
        elif anim == 'celebrating':
            cycle = frame_idx % 24
            if cycle < 8:
                eye_style = 'happy'
            elif cycle < 14:
                eye_style = 'sparkle'
            elif cycle < 18:
                eye_style = 'surprised'
            else:
                eye_style = 'happy'
        elif anim == 'rage':
            eye_style = 'angry'
        elif anim == 'sarcastic':
            eye_style = 'half'
        elif anim == 'drunk':
            eye_style = 'dizzy'
        elif anim == 'petting':
            # Squint progression: normal → happy → squint → happy
            cycle = frame_idx % 12
            if cycle < 3:
                eye_style = 'happy'
            elif cycle < 6:
                eye_style = 'squint'
            else:
                eye_style = 'happy'
        elif anim == 'clicked':
            # Multi-phase eye transitions: surprised → wide → wink → happy
            cycle = frame_idx % 24
            if cycle < 5:
                eye_style = 'surprised'
            elif cycle < 10:
                eye_style = 'normal'
            elif cycle < 14:
                eye_style = 'wink'
            elif cycle < 18:
                eye_style = 'happy'
            else:
                eye_style = 'happy'
        elif anim == 'dancing':
            cycle = frame_idx % 20
            if cycle < 5:
                eye_style = 'happy'
            elif cycle < 10:
                eye_style = 'sparkle'
            elif cycle < 15:
                eye_style = 'normal'
            else:
                eye_style = 'happy'
        elif anim == 'eating':
            cycle = frame_idx % 16
            if cycle < 6:
                eye_style = 'happy'
            elif cycle < 10:
                eye_style = 'closed'
            else:
                eye_style = 'happy'
        elif anim == 'playing':
            cycle = frame_idx % 20
            if cycle < 8:
                eye_style = 'happy'
            elif cycle < 12:
                eye_style = 'sparkle'
            elif cycle < 16:
                eye_style = 'surprised'
            else:
                eye_style = 'happy'
        elif anim == 'customizing':
            cycle = frame_idx % 16
            if cycle < 6:
                eye_style = 'happy'
            elif cycle < 10:
                eye_style = 'sparkle'
            else:
                eye_style = 'normal'
        elif anim == 'spinning':
            eye_style = 'spinning'
        elif anim == 'shaking':
            eye_style = 'dizzy'
        elif anim == 'rolling':
            eye_style = 'rolling'
        elif anim == 'stretching':
            stretch_cycle = (frame_idx % 60) / 60.0
            if stretch_cycle < 0.2:
                eye_style = 'normal'
            elif stretch_cycle < 0.5:
                eye_style = 'closed'
            elif stretch_cycle < 0.7:
                eye_style = 'half'
            else:
                eye_style = 'happy'
        elif anim == 'waving':
            cycle = frame_idx % 16
            if cycle < 4:
                eye_style = 'happy'
            elif cycle < 8:
                eye_style = 'wink'
            elif cycle < 12:
                eye_style = 'happy'
            else:
                eye_style = 'normal'
        elif anim == 'jumping':
            jump_cycle = (frame_idx % 36) / 36.0
            if jump_cycle < 0.15:
                eye_style = 'normal'
            elif jump_cycle < 0.55:
                eye_style = 'happy'
            elif jump_cycle < 0.75:
                eye_style = 'surprised'
            else:
                eye_style = 'happy'
        elif anim == 'yawning':
            yawn_cycle = (frame_idx % 48) / 48.0
            if yawn_cycle < 0.15:
                eye_style = 'normal'
            elif yawn_cycle < 0.5:
                eye_style = 'closed'
            elif yawn_cycle < 0.7:
                eye_style = 'half'
            else:
                eye_style = 'closed'
        elif anim == 'sneezing':
            sneeze_cycle = (frame_idx % 36) / 36.0
            if sneeze_cycle < 0.25:
                eye_style = 'closed'
            elif sneeze_cycle < 0.35:
                eye_style = 'surprised'
            elif sneeze_cycle < 0.5:
                eye_style = 'closed'
            else:
                eye_style = 'half'
        elif anim == 'belly_rub':
            cycle = frame_idx % 16
            if cycle < 6:
                eye_style = 'happy'
            elif cycle < 10:
                eye_style = 'sparkle'
            else:
                eye_style = 'happy'
        elif anim == 'fed':
            cycle = frame_idx % 20
            if cycle < 6:
                eye_style = 'happy'
            elif cycle < 10:
                eye_style = 'sparkle'
            elif cycle < 14:
                eye_style = 'heart'
            else:
                eye_style = 'happy'
        elif anim == 'cartwheel':
            eye_style = 'spinning'
        elif anim == 'backflip':
            eye_style = 'surprised'
        elif anim == 'lay_on_back':
            eye_style = 'closed'
        elif anim == 'lay_on_side':
            eye_style = 'half'
        elif anim == 'carrying':
            eye_style = 'normal'
        elif anim == 'belly_jiggle':
            eye_style = 'happy'
        
        # --- Determine mouth style ---
        mouth_style = 'normal'
        if anim == 'celebrating':
            cycle = frame_idx % 24
            if cycle < 12:
                mouth_style = 'smile'
            elif cycle < 18:
                mouth_style = 'grin'
            else:
                mouth_style = 'smile'
        elif anim == 'dancing':
            cycle = frame_idx % 20
            if cycle < 8:
                mouth_style = 'smile'
            elif cycle < 14:
                mouth_style = 'grin'
            else:
                mouth_style = 'tongue'
        elif anim == 'rage':
            mouth_style = 'angry'
        elif anim == 'sleeping' or anim in ('laying_down', 'laying_back', 'laying_side'):
            mouth_style = 'sleep'
        elif anim == 'petting':
            mouth_style = 'smile'
        elif anim == 'fed':
            cycle = frame_idx % 20
            if cycle < 8:
                mouth_style = 'smile'
            elif cycle < 14:
                mouth_style = 'eating'
            else:
                mouth_style = 'smile'
        elif anim in ('playing', 'customizing'):
            mouth_style = 'smile'
        elif anim == 'eating':
            cycle = frame_idx % 12
            if cycle < 4:
                mouth_style = 'eating'
            elif cycle < 8:
                mouth_style = 'smile'
            else:
                mouth_style = 'eating'
        elif anim == 'drunk':
            mouth_style = 'wavy'
        elif anim == 'stretching':
            stretch_cycle = (frame_idx % 60) / 60.0
            if stretch_cycle < 0.5:
                mouth_style = 'open_wide'
            elif stretch_cycle < 0.7:
                mouth_style = 'normal'
            else:
                mouth_style = 'smile'
        elif anim == 'waving':
            mouth_style = 'smile'
        elif anim == 'jumping':
            jump_cycle = (frame_idx % 36) / 36.0
            if jump_cycle < 0.35:
                mouth_style = 'normal'
            elif jump_cycle < 0.55:
                mouth_style = 'grin'
            elif jump_cycle < 0.75:
                mouth_style = 'open_wide'
            else:
                mouth_style = 'smile'
        elif anim == 'yawning':
            yawn_cycle = (frame_idx % 48) / 48.0
            if yawn_cycle < 0.15:
                mouth_style = 'normal'
            elif yawn_cycle < 0.35:
                mouth_style = 'open_wide'
            elif yawn_cycle < 0.5:
                mouth_style = 'open_wide'
            elif yawn_cycle < 0.7:
                mouth_style = 'normal'
            else:
                mouth_style = 'sleep'
        elif anim == 'sneezing':
            sneeze_cycle = (frame_idx % 36) / 36.0
            if sneeze_cycle < 0.25:
                mouth_style = 'normal'
            elif sneeze_cycle < 0.35:
                mouth_style = 'open_wide'
            elif sneeze_cycle < 0.5:
                mouth_style = 'grin'
            else:
                mouth_style = 'normal'
        elif anim == 'belly_rub':
            mouth_style = 'smile'
        elif anim == 'cartwheel':
            mouth_style = 'grin'
        elif anim == 'backflip':
            mouth_style = 'grin'
        elif anim == 'lay_on_back':
            mouth_style = 'smile'
        elif anim == 'lay_on_side':
            mouth_style = 'sleep'
        elif anim == 'carrying':
            mouth_style = 'normal'
        elif anim == 'belly_jiggle':
            mouth_style = 'grin'
        
        # --- Colors ---
        white = "#FFFFFF"
        black = "#1a1a1a"
        pink = "#FFB6C1"
        nose_color = "#333333"
        
        # Scale factor for larger canvas (base was 160x200)
        sx = w / 160.0
        sy = h / 200.0
        
        # --- Ear wiggle for idle/petting ---
        ear_wiggle = 0
        if anim == 'petting':
            ear_wiggle = math.sin(phase * 3) * 4 * sx + math.sin(phase * 1.3) * 2 * sx
        elif anim in ('idle', 'celebrating', 'playing'):
            ear_wiggle = math.sin(phase * 2) * 3 * sx
        elif anim in ('sleeping', 'laying_down', 'laying_back', 'laying_side', 'lay_on_back', 'lay_on_side'):
            # Occasional ear twitch while sleeping/laying
            if frame_idx % 20 < 3:
                ear_wiggle = math.sin(phase * 6) * 2 * sx
        elif anim in ('waving', 'belly_rub', 'jumping', 'cartwheel', 'backflip'):
            ear_wiggle = math.sin(phase * 2) * 3 * sx
        elif anim == 'sneezing':
            ear_wiggle = math.sin(phase * 5) * 4 * sx
        elif anim == 'carrying':
            ear_wiggle = math.sin(phase * 1.5) * 2 * sx  # Gentle movement while carrying
        
        # --- Draw legs (behind body) ---
        # Apply body sway to center position for turning/direction effect
        cx_draw = cx + int(body_sway)
        leg_top = int(145 * sy + by)
        leg_len = int(30 * sy)
        
        # Apply individual limb dangle physics during drag
        # Left leg
        left_leg_dangle = int(self._dangle_left_leg) if anim == 'dragging' else 0
        left_leg_x = cx_draw - int(25 * sx)
        left_leg_swing = leg_swing + left_leg_dangle
        c.create_oval(
            left_leg_x - int(12 * sx), leg_top + left_leg_swing,
            left_leg_x + int(12 * sx), leg_top + leg_len + left_leg_swing,
            fill=black, outline=black, tags="leg"
        )
        # Left foot (white pad)
        c.create_oval(
            left_leg_x - int(10 * sx), leg_top + leg_len - int(8 * sy) + left_leg_swing,
            left_leg_x + int(10 * sx), leg_top + leg_len + int(4 * sy) + left_leg_swing,
            fill=white, outline=black, width=1, tags="foot"
        )
        
        # Right leg
        right_leg_dangle = int(self._dangle_right_leg) if anim == 'dragging' else 0
        right_leg_x = cx_draw + int(25 * sx)
        right_leg_swing = -leg_swing + right_leg_dangle
        c.create_oval(
            right_leg_x - int(12 * sx), leg_top + right_leg_swing,
            right_leg_x + int(12 * sx), leg_top + leg_len + right_leg_swing,
            fill=black, outline=black, tags="leg"
        )
        # Right foot (white pad)
        c.create_oval(
            right_leg_x - int(10 * sx), leg_top + leg_len - int(8 * sy) + right_leg_swing,
            right_leg_x + int(10 * sx), leg_top + leg_len + int(4 * sy) + right_leg_swing,
            fill=white, outline=black, width=1, tags="foot"
        )
        
        # --- Draw body (white belly, rounded) ---
        body_top = int(75 * sy + by)
        body_bot = int(160 * sy + by)
        body_rx = int(42 * sx * breath_scale)
        # Apply belly jiggle - wobble the body horizontally
        belly_jiggle_px = int(self._belly_jiggle)
        jiggle_scale = 1.0 + abs(self._belly_jiggle) * 0.008  # slight width pulse
        body_rx_jiggle = int(body_rx * jiggle_scale)
        c.create_oval(
            cx_draw - body_rx_jiggle + belly_jiggle_px, body_top,
            cx_draw + body_rx_jiggle + belly_jiggle_px, body_bot,
            fill=white, outline=black, width=2, tags="body"
        )
        # Inner belly patch (lighter) — sized to fit fully inside body with no visible gap
        belly_rx = int(26 * sx * breath_scale * jiggle_scale)
        c.create_oval(
            cx_draw - belly_rx + belly_jiggle_px, body_top + int(18 * sy),
            cx_draw + belly_rx + belly_jiggle_px, body_bot - int(14 * sy),
            fill="#FAFAFA", outline="", tags="belly"
        )
        
        # --- Draw arms (black, attached to body sides) ---
        arm_top = int(95 * sy + by)
        arm_len = int(35 * sy)
        
        # Apply individual limb dangle physics during drag
        # Left arm
        left_arm_dangle = int(self._dangle_left_arm) if anim == 'dragging' else 0
        la_swing = arm_swing + left_arm_dangle
        c.create_oval(
            cx_draw - int(55 * sx), arm_top + la_swing,
            cx_draw - int(30 * sx), arm_top + arm_len + la_swing,
            fill=black, outline=black, tags="arm"
        )
        
        # Right arm
        right_arm_dangle = int(self._dangle_right_arm) if anim == 'dragging' else 0
        ra_swing = -arm_swing + right_arm_dangle
        c.create_oval(
            cx_draw + int(30 * sx), arm_top + ra_swing,
            cx_draw + int(55 * sx), arm_top + arm_len + ra_swing,
            fill=black, outline=black, tags="arm"
        )
        
        # --- Draw head ---
        head_cy = int(52 * sy + by)
        head_rx = int(36 * sx)
        head_ry = int(32 * sy)
        c.create_oval(
            cx_draw - head_rx, head_cy - head_ry,
            cx_draw + head_rx, head_cy + head_ry,
            fill=white, outline=black, width=2, tags="head"
        )
        
        # --- Draw ears (black circles on top of head) with wiggle and individual stretch ---
        ear_y = head_cy - head_ry + int(5 * sy)
        ear_w = int(22 * sx)
        ear_h = int(24 * sy)
        
        # Individual ear stretch/dangle during drag
        left_ear_stretch_px = int(self._dangle_left_ear * sy) if anim == 'dragging' else int(self._ear_stretch * sy)
        right_ear_stretch_px = int(self._dangle_right_ear * sy) if anim == 'dragging' else int(self._ear_stretch * sy)
        
        # Left ear
        c.create_oval(cx_draw - head_rx - int(2 * sx) + ear_wiggle, ear_y - int(16 * sy) - left_ear_stretch_px,
                       cx_draw - head_rx + ear_w + ear_wiggle, ear_y + int(8 * sy),
                       fill=black, outline=black, tags="ear")
        # Inner ear pink
        c.create_oval(cx_draw - head_rx + int(4 * sx) + ear_wiggle, ear_y - int(10 * sy) - left_ear_stretch_px,
                       cx_draw - head_rx + int(16 * sx) + ear_wiggle, ear_y + int(2 * sy),
                       fill=pink, outline="", tags="ear_inner")
        # Right ear
        c.create_oval(cx_draw + head_rx - ear_w - ear_wiggle, ear_y - int(16 * sy) - right_ear_stretch_px,
                       cx_draw + head_rx + int(2 * sx) - ear_wiggle, ear_y + int(8 * sy),
                       fill=black, outline=black, tags="ear")
        # Inner ear pink
        c.create_oval(cx_draw + head_rx - int(16 * sx) - ear_wiggle, ear_y - int(10 * sy) - right_ear_stretch_px,
                       cx_draw + head_rx - int(4 * sx) - ear_wiggle, ear_y + int(2 * sy),
                       fill=pink, outline="", tags="ear_inner")
        
        # --- Draw eye patches (black ovals around eyes) ---
        eye_y = head_cy - int(4 * sy)
        patch_rx = int(14 * sx)
        patch_ry = int(11 * sy)
        eye_offset = int(24 * sx)
        # Left eye patch
        c.create_oval(cx_draw - eye_offset - patch_rx, eye_y - patch_ry,
                       cx_draw - eye_offset + patch_rx, eye_y + patch_ry,
                       fill=black, outline="", tags="eye_patch")
        # Right eye patch
        c.create_oval(cx_draw + eye_offset - patch_rx, eye_y - patch_ry,
                       cx_draw + eye_offset + patch_rx, eye_y + patch_ry,
                       fill=black, outline="", tags="eye_patch")
        
        # --- Draw equipped items on panda body (before face details) ---
        self._draw_equipped_items(c, cx_draw, by, sx, sy)
        
        # --- Draw eyes ---
        self._draw_eyes(c, cx_draw, eye_y, eye_style, sx, sy)
        
        # --- Draw nose ---
        nose_y = head_cy + int(8 * sy)
        c.create_oval(cx_draw - int(5 * sx), nose_y - int(3 * sy), cx_draw + int(5 * sx), nose_y + int(4 * sy),
                       fill=nose_color, outline="", tags="nose")
        
        # --- Draw mouth ---
        self._draw_mouth(c, cx_draw, nose_y + int(6 * sy), mouth_style, sx, sy)
        
        # --- Draw animation-specific extras ---
        self._draw_animation_extras(c, cx_draw, by, anim, frame_idx, sx, sy)
        
        # --- Draw panda name tag below feet ---
        if self.panda and self.panda.name:
            name_y = int(h - 12 * sy)  # position just above canvas bottom edge
            # width constrains text wrapping to fit within the canvas
            c.create_text(cx_draw, name_y, text=self.panda.name,
                          font=("Arial Bold", int(10 * sx)),
                          fill="#666666", width=int(w * 0.9), tags="name_tag")
    
    def _draw_eyes(self, c: tk.Canvas, cx: int, ey: int, style: str, sx: float = 1.0, sy: float = 1.0):
        """Draw panda eyes based on the current animation style."""
        left_ex = cx - int(24 * sx)
        right_ex = cx + int(24 * sx)
        es = int(6 * sx)  # eye size
        ps = int(3 * sx)  # pupil size
        
        if style == 'closed':
            c.create_line(left_ex - es, ey, left_ex + es, ey,
                          fill="white", width=2, tags="eye")
            c.create_line(right_ex - es, ey, right_ex + es, ey,
                          fill="white", width=2, tags="eye")
        elif style == 'happy':
            c.create_arc(left_ex - es, ey - es, left_ex + es, ey + int(4 * sy),
                         start=0, extent=180, style="arc",
                         outline="white", width=3, tags="eye")
            c.create_arc(right_ex - es, ey - es, right_ex + es, ey + int(4 * sy),
                         start=0, extent=180, style="arc",
                         outline="white", width=3, tags="eye")
            # Small shine marks
            sh = int(2 * sx)
            c.create_oval(left_ex - es + sh, ey - es + sh,
                          left_ex - es + sh * 2, ey - es + sh * 2,
                          fill="white", outline="", tags="shine")
            c.create_oval(right_ex - es + sh, ey - es + sh,
                          right_ex - es + sh * 2, ey - es + sh * 2,
                          fill="white", outline="", tags="shine")
        elif style == 'angry':
            c.create_oval(left_ex - ps, ey - ps, left_ex + ps, ey + ps,
                          fill="red", outline="", tags="eye")
            c.create_oval(right_ex - ps, ey - ps, right_ex + ps, ey + ps,
                          fill="red", outline="", tags="eye")
            c.create_line(left_ex - int(7 * sx), ey - int(10 * sy), left_ex + int(5 * sx), ey - es,
                          fill="white", width=2, tags="brow")
            c.create_line(right_ex + int(7 * sx), ey - int(10 * sy), right_ex - int(5 * sx), ey - es,
                          fill="white", width=2, tags="brow")
        elif style == 'half':
            c.create_oval(left_ex - int(4 * sx), ey - 1, left_ex + int(4 * sx), ey + int(4 * sy),
                          fill="white", outline="", tags="eye")
            c.create_oval(left_ex - int(2 * sx), ey, left_ex + int(2 * sx), ey + ps,
                          fill="#222222", outline="", tags="pupil")
            c.create_oval(right_ex - int(4 * sx), ey - 1, right_ex + int(4 * sx), ey + int(4 * sy),
                          fill="white", outline="", tags="eye")
            c.create_oval(right_ex - int(2 * sx), ey, right_ex + int(2 * sx), ey + ps,
                          fill="#222222", outline="", tags="pupil")
        elif style == 'dizzy':
            c.create_line(left_ex - int(4 * sx), ey - int(4 * sy), left_ex + int(4 * sx), ey + int(4 * sy),
                          fill="white", width=2, tags="eye")
            c.create_line(left_ex - int(4 * sx), ey + int(4 * sy), left_ex + int(4 * sx), ey - int(4 * sy),
                          fill="white", width=2, tags="eye")
            c.create_line(right_ex - int(4 * sx), ey - int(4 * sy), right_ex + int(4 * sx), ey + int(4 * sy),
                          fill="white", width=2, tags="eye")
            c.create_line(right_ex - int(4 * sx), ey + int(4 * sy), right_ex + int(4 * sx), ey - int(4 * sy),
                          fill="white", width=2, tags="eye")
        elif style == 'wink':
            # Left eye normal, right eye winking (line)
            c.create_oval(left_ex - es, ey - es, left_ex + es, ey + es,
                          fill="white", outline="", tags="eye")
            c.create_oval(left_ex - ps, ey - ps, left_ex + ps, ey + ps,
                          fill="#222222", outline="", tags="pupil")
            c.create_line(right_ex - es, ey, right_ex + es, ey,
                          fill="white", width=2, tags="eye")
        elif style == 'surprised':
            # Wide open eyes (larger)
            big_es = int(9 * sx)
            c.create_oval(left_ex - big_es, ey - big_es, left_ex + big_es, ey + big_es,
                          fill="white", outline="", tags="eye")
            c.create_oval(left_ex - ps, ey - ps, left_ex + ps, ey + ps,
                          fill="#222222", outline="", tags="pupil")
            # Highlight dot
            hl = int(2 * sx)
            c.create_oval(left_ex + ps, ey - big_es + hl,
                          left_ex + ps + hl * 2, ey - big_es + hl * 3,
                          fill="white", outline="", tags="shine")
            c.create_oval(right_ex - big_es, ey - big_es, right_ex + big_es, ey + big_es,
                          fill="white", outline="", tags="eye")
            c.create_oval(right_ex - ps, ey - ps, right_ex + ps, ey + ps,
                          fill="#222222", outline="", tags="pupil")
            c.create_oval(right_ex + ps, ey - big_es + hl,
                          right_ex + ps + hl * 2, ey - big_es + hl * 3,
                          fill="white", outline="", tags="shine")
        elif style == 'spinning':
            # Swirly spiral eyes
            for ex_pos in [left_ex, right_ex]:
                # Draw spiral-like circle
                r = int(5 * sx)
                c.create_oval(ex_pos - r, ey - r, ex_pos + r, ey + r,
                              fill="white", outline="", tags="eye")
                # Inner spiral dots
                c.create_text(ex_pos, ey, text="@", font=("Arial", int(8 * sx)),
                              fill="#222222", tags="pupil")
        elif style == 'rolling':
            # Eyes rolling around
            offset = int(4 * sx * math.sin(self.animation_frame * 0.5))
            v_offset = int(3 * sy * math.cos(self.animation_frame * 0.5))
            for ex_pos in [left_ex, right_ex]:
                c.create_oval(ex_pos - es, ey - es, ex_pos + es, ey + es,
                              fill="white", outline="", tags="eye")
                c.create_oval(ex_pos + offset - ps, ey + v_offset - ps,
                              ex_pos + offset + ps, ey + v_offset + ps,
                              fill="#222222", outline="", tags="pupil")
        elif style == 'squint':
            # Squinting eyes
            for ex_pos in [left_ex, right_ex]:
                c.create_oval(ex_pos - int(5 * sx), ey - int(2 * sy),
                              ex_pos + int(5 * sx), ey + int(2 * sy),
                              fill="white", outline="", tags="eye")
                c.create_oval(ex_pos - int(2 * sx), ey - int(1 * sy),
                              ex_pos + int(2 * sx), ey + int(1 * sy),
                              fill="#222222", outline="", tags="pupil")
        elif style == 'sparkle':
            # Sparkly star eyes with extra sparkle rays
            for ex_pos in [left_ex, right_ex]:
                c.create_text(ex_pos, ey, text="★", font=("Arial", int(10 * sx)),
                              fill="white", tags="eye")
                # Sparkle rays radiating outward
                ray_len = int(4 * sx)
                for angle_deg in range(0, 360, 45):
                    rad = math.radians(angle_deg)
                    rx = int(math.cos(rad) * ray_len)
                    ry = int(math.sin(rad) * ray_len)
                    c.create_line(ex_pos + rx, ey + ry,
                                  ex_pos + rx + int(math.cos(rad) * 2 * sx),
                                  ey + ry + int(math.sin(rad) * 2 * sy),
                                  fill="white", width=1, tags="sparkle_ray")
        elif style == 'heart':
            # Heart eyes
            for ex_pos in [left_ex, right_ex]:
                c.create_text(ex_pos, ey, text="♥", font=("Arial", int(10 * sx)),
                              fill="#FF69B4", tags="eye")
        else:
            # Normal round eyes with pupils and shine
            c.create_oval(left_ex - es, ey - es, left_ex + es, ey + es,
                          fill="white", outline="", tags="eye")
            c.create_oval(left_ex - ps, ey - ps, left_ex + ps, ey + ps,
                          fill="#222222", outline="", tags="pupil")
            c.create_oval(left_ex - int(5 * sx), ey - int(5 * sy), left_ex - int(2 * sx), ey - int(2 * sy),
                          fill="white", outline="", tags="shine")
            c.create_oval(right_ex - es, ey - es, right_ex + es, ey + es,
                          fill="white", outline="", tags="eye")
            c.create_oval(right_ex - ps, ey - ps, right_ex + ps, ey + ps,
                          fill="#222222", outline="", tags="pupil")
            c.create_oval(right_ex - int(5 * sx), ey - int(5 * sy), right_ex - int(2 * sx), ey - int(2 * sy),
                          fill="white", outline="", tags="shine")
    
    def _draw_mouth(self, c: tk.Canvas, cx: int, my: int, style: str, sx: float = 1.0, sy: float = 1.0):
        """Draw panda mouth based on the current animation style."""
        ms = int(8 * sx)  # mouth size
        if style == 'smile':
            # Wider smile when mood is very happy
            mood_bonus = 0
            try:
                if self.panda and hasattr(self.panda, 'current_mood') and self.panda.current_mood:
                    mood_val = self.panda.current_mood.value
                    if mood_val in ('ecstatic', 'overjoyed', 'very_happy'):
                        mood_bonus = int(3 * sx)
            except Exception:
                pass
            sm = ms + mood_bonus
            c.create_arc(cx - sm, my - int(6 * sy), cx + sm, my + int(6 * sy),
                         start=200, extent=140, style="arc",
                         outline="#333333", width=2, tags="mouth")
        elif style == 'angry':
            c.create_arc(cx - ms, my, cx + ms, my + int(10 * sy),
                         start=20, extent=140, style="arc",
                         outline="#333333", width=2, tags="mouth")
        elif style == 'sleep':
            # ZZZ that drifts upward based on animation frame
            zzz_drift = (self.animation_frame % 12) * sy * 0.8
            c.create_text(cx + int(30 * sx), my - int(20 * sy) - zzz_drift * 0.3, text="z",
                          font=("Arial", int(10 * sx)), fill="gray", tags="zzz")
            c.create_text(cx + int(38 * sx), my - int(30 * sy) - zzz_drift * 0.6, text="Z",
                          font=("Arial", int(12 * sx)), fill="gray", tags="zzz")
            c.create_text(cx + int(46 * sx), my - int(42 * sy) - zzz_drift, text="Z",
                          font=("Arial", int(15 * sx)), fill="gray", tags="zzz")
            c.create_line(cx - int(4 * sx), my + 2, cx + int(4 * sx), my + 2,
                          fill="#333333", width=1, tags="mouth")
        elif style == 'blep':
            # Smile with tongue peeking out
            c.create_arc(cx - ms, my - int(6 * sy), cx + ms, my + int(6 * sy),
                         start=200, extent=140, style="arc",
                         outline="#333333", width=2, tags="mouth")
            c.create_oval(cx - int(3 * sx), my + int(3 * sy),
                          cx + int(3 * sx), my + int(8 * sy),
                          fill="#FF69B4", outline="#E0559D", tags="tongue")
        elif style == 'wavy':
            points = []
            for i in range(9):
                px = cx - ms + i * int(2 * sx)
                py = my + math.sin(i * 1.2) * int(3 * sy)
                points.extend([px, py])
            if len(points) >= 4:
                c.create_line(*points, fill="#333333", width=2,
                              smooth=True, tags="mouth")
        elif style == 'eating':
            c.create_oval(cx - int(5 * sx), my - int(2 * sy), cx + int(5 * sx), my + int(5 * sy),
                          fill="#333333", outline="#333333", tags="mouth")
        elif style == 'open_wide':
            c.create_oval(cx - int(6 * sx), my - int(4 * sy), cx + int(6 * sx), my + int(7 * sy),
                          fill="#333333", outline="#333333", tags="mouth")
        elif style == 'tongue':
            c.create_arc(cx - ms, my - int(6 * sy), cx + ms, my + int(6 * sy),
                         start=200, extent=140, style="arc",
                         outline="#333333", width=2, tags="mouth")
            c.create_oval(cx - int(3 * sx), my + int(2 * sy), cx + int(3 * sx), my + int(7 * sy),
                          fill="#FF69B4", outline="#FF69B4", tags="tongue")
        elif style == 'grin':
            c.create_arc(cx - int(10 * sx), my - int(8 * sy), cx + int(10 * sx), my + int(8 * sy),
                         start=200, extent=140, style="arc",
                         outline="#333333", width=2, tags="mouth")
        else:
            c.create_arc(cx - int(5 * sx), my - int(3 * sy), cx + int(5 * sx), my + int(4 * sy),
                         start=210, extent=120, style="arc",
                         outline="#333333", width=1.5, tags="mouth")

    # Emoji-to-color mapping for equipped item shapes
    _EMOJI_COLORS = {
        '🎩': '#1a1a1a', '👑': '#FFD700', '🧢': '#4169E1', '🎓': '#1a1a1a',
        '🪖': '#556B2F', '⛑️': '#FF4500', '👒': '#F5DEB3', '🎀': '#FF69B4',
        '👗': '#FF69B4', '👕': '#4169E1', '👔': '#8B0000', '🧥': '#8B4513',
        '🥼': '#FFFFFF', '🦺': '#FF8C00', '👚': '#FFB6C1', '🧣': '#FF0000',
        '📿': '#FFD700', '🕶️': '#1a1a1a', '💎': '#00CED1', '🎗️': '#FFFF00',
        '🧤': '#8B4513', '👞': '#8B4513', '👟': '#FFFFFF', '👠': '#FF0000',
        '🥾': '#556B2F', '👢': '#8B4513', '🩴': '#FFD700',
        # Additional emojis for new closet items
        '🎍': '#2E8B57', '🏋️': '#FF6347', '🌺': '#FF69B4', '🏴‍☠️': '#1a1a1a',
        '⚔️': '#808080', '😇': '#FFD700', '🕵️': '#8B4513', '🥷': '#333333',
        '🪐': '#C0C0C0', '⛩️': '#B22222', '🌀': '#4682B4', '🎨': '#FF4500',
        '🌮': '#DAA520', '🚒': '#FF0000', '🎓': '#1a1a1a', '👸': '#FFD700',
        '🌾': '#D2B48C', '❄️': '#ADD8E6', '🏃': '#FF6347', '🐾': '#8B4513',
        '⛸️': '#C0C0C0', '🛼': '#FF69B4', '🏔️': '#8B4513', '✨': '#FFD700',
        '🤠': '#8B4513', '🩰': '#FFB6C1', '🌙': '#4169E1', '📐': '#8B0000',
        '⛷️': '#4169E1', '🛡️': '#808080', '💡': '#00FF00', '🐰': '#FFB6C1',
        '🔥': '#FF4500', '🎋': '#2E8B57', '🐼': '#1a1a1a', '🤝': '#FFD700',
        '🎖️': '#FFD700', '🍀': '#2E8B57', '⭐': '#FFD700', '🔔': '#FFD700',
        '💍': '#C0C0C0', '🪶': '#FF69B4', '🕰️': '#8B4513', '🪄': '#9370DB',
        '🦪': '#FAEBD7', '🏴': '#1a1a1a', '🧭': '#DAA520', '📸': '#333333',
        '🔭': '#8B4513', '🧶': '#FF6347', '👖': '#4169E1', '🏛️': '#FFFFFF',
        '🚀': '#C0C0C0', '🏅': '#FFD700', '🤵': '#1a1a1a', '🩳': '#87CEEB',
        '🏀': '#FF8C00', '🦸‍♂️': '#FF0000', '🦸': '#FF0000', '🧐': '#FFD700',
        '🌸': '#FFB6C1', '🎧': '#333333', '🎒': '#FF6347', '👼': '#FFFFFF',
        # New fur style emojis
        '🌬️': '#B0C4DE', '🐆': '#DEB887', '🦓': '#808080', '💠': '#00CED1',
        '🔩': '#808080', '🌱': '#228B22', '🧸': '#DEB887', '⛈️': '#4682B4',
        '🌟': '#FFD700', '🌌': '#191970', '⌚': '#C0C0C0', '🤘': '#8B0000',
    }

    @staticmethod
    def _color_for_emoji(emoji: str, fallback: str = '#888888') -> str:
        """Return a color corresponding to the given emoji icon."""
        return PandaWidget._EMOJI_COLORS.get(emoji, fallback)

    def _compute_limb_offsets(self, anim: str, frame_idx: int) -> tuple:
        """Compute limb swing offsets for a given animation state.
        
        Returns (leg_swing, arm_swing) tuple used for clothing/accessory
        positioning and body part rendering.
        """
        phase = (frame_idx % 60) / 60.0 * 2 * math.pi
        
        if anim in ('idle', 'working', 'sarcastic', 'thinking'):
            leg_swing = math.sin(phase * 1.2) * 2 + math.sin(phase * 0.4) * 1
            arm_swing = math.sin(phase) * 5 + math.sin(phase * 2.5) * 2
        elif anim in ('dragging', 'tossed', 'wall_hit'):
            leg_swing = math.sin(phase) * 15
            arm_swing = math.sin(phase + math.pi) * 12
        elif anim == 'dancing':
            dc = (frame_idx % 60) / 60.0
            if dc < 0.25:
                leg_swing = math.sin(phase) * 14
                arm_swing = math.sin(phase * 2) * 16
            elif dc < 0.5:
                leg_swing = math.sin(phase * 3) * 10
                arm_swing = -abs(math.sin(phase * 2)) * 18
            elif dc < 0.75:
                leg_swing = -math.sin(phase) * 14
                arm_swing = math.sin(phase * 2 + math.pi) * 16
            else:
                leg_swing = math.sin(phase * 2) * 8
                arm_swing = -abs(math.sin(phase)) * 20
        elif anim == 'celebrating':
            cc = (frame_idx % 48) / 48.0
            if cc < 0.33:
                leg_swing = math.sin(phase) * 6
                arm_swing = -abs(math.sin(phase * 2)) * 20
            elif cc < 0.66:
                leg_swing = math.sin(phase * 2) * 10
                arm_swing = math.sin(phase * 3) * 14
            else:
                leg_swing = math.sin(phase * 2) * 12
                arm_swing = math.cos(phase * 2) * 16
        elif anim == 'playing':
            pc = (frame_idx % 60) / 60.0
            if pc < 0.3:
                leg_swing = math.sin(phase * 2) * 12
                arm_swing = math.sin(phase * 3) * 16
            elif pc < 0.6:
                leg_swing = math.sin(phase) * 8
                arm_swing = -abs(math.sin(phase * 2)) * 18
            else:
                leg_swing = math.sin(phase * 2) * 14
                arm_swing = math.cos(phase * 2) * 12
        elif anim in ('jumping', 'backflip', 'cartwheel'):
            leg_swing = math.sin(phase * 2) * 10
            arm_swing = math.sin(phase * 2) * 16
        elif anim == 'spinning':
            leg_swing = math.sin(phase * 4) * 18
            arm_swing = math.sin(phase * 4 + math.pi / 2) * 20
        elif anim == 'shaking':
            leg_swing = math.sin(phase * 8) * 10
            arm_swing = math.sin(phase * 8) * 12
        elif anim == 'rolling':
            leg_swing = math.sin(phase * 2) * 15
            arm_swing = math.cos(phase * 2) * 15
        elif anim == 'rage':
            leg_swing = math.sin(phase * 3) * 8
            arm_swing = math.sin(phase * 3) * 10
        elif anim == 'eating':
            ec = (frame_idx % 48) / 48.0
            leg_swing = 0
            if ec < 0.3:
                arm_swing = -abs(math.sin(phase * 2)) * 14
            elif ec < 0.7:
                arm_swing = -12 + math.sin(phase * 4) * 6
            else:
                settle = (ec - 0.7) / 0.3
                arm_swing = -12 * (1 - settle) + math.sin(phase) * 3
        elif anim in ('waving', 'stretching'):
            leg_swing = math.sin(phase * 0.5) * 2
            arm_swing = math.sin(phase * 3) * 10
        elif anim == 'carrying':
            leg_swing = math.sin(phase) * 4
            arm_swing = -8
        else:
            leg_swing = math.sin(phase + math.pi) * 2
            arm_swing = math.sin(phase + math.pi) * 6
        
        return leg_swing, arm_swing

    def _draw_equipped_items(self, c: tk.Canvas, cx: int, by: float, sx: float, sy: float):
        """Draw equipped closet items as fitted shapes on the panda body.

        Items are drawn with enough detail so they look like the panda is
        actually wearing them, using layered shapes, highlights and shadows.
        Clothing is rendered based on its ``clothing_type`` (shirt, pants,
        jacket, dress, full_body) so different garments attach to the
        correct body parts and follow limb animations.
        """
        if not self.panda_closet:
            return
        try:
            appearance = self.panda_closet.get_current_appearance()

            # Compute limb offsets so equipped items track body movement
            _leg_swing, _arm_swing = self._compute_limb_offsets(
                self.current_animation, self.animation_frame)

            # Add dangle offsets during drag so clothes stay glued to limbs
            _left_leg_dangle = 0
            _right_leg_dangle = 0
            _left_arm_dangle = 0
            _right_arm_dangle = 0
            if self.current_animation == 'dragging' and self.is_dragging:
                _left_leg_dangle = int(self._dangle_left_leg)
                _right_leg_dangle = int(self._dangle_right_leg)
                _left_arm_dangle = int(self._dangle_left_arm)
                _right_arm_dangle = int(self._dangle_right_arm)

            # --- Draw clothing based on clothing_type ---
            if appearance.clothing:
                clothing_item = self.panda_closet.get_item(appearance.clothing)
                if clothing_item:
                    color = self._color_for_emoji(clothing_item.emoji, '#4169E1')
                    shadow = self._shade_color(color, -30)
                    highlight = self._shade_color(color, 40)
                    ctype = clothing_item.clothing_type or 'shirt'

                    bt = int(82 * sy + by)   # body top (below neck)
                    bb = int(152 * sy + by)  # body bottom
                    mid = (bt + bb) // 2

                    # --- Pants: drawn on legs, synced with leg swing ---
                    if ctype == 'pants':
                        waist_y = mid
                        leg_bottom = int(170 * sy + by)
                        left_swing = int(_leg_swing) + _left_leg_dangle
                        right_swing = int(-_leg_swing) + _right_leg_dangle
                        # Waistband
                        c.create_rectangle(
                            cx - int(34 * sx), waist_y - int(4 * sy),
                            cx + int(34 * sx), waist_y + int(4 * sy),
                            fill=color, outline=shadow, width=1,
                            tags="equipped_clothing")
                        # Left leg
                        c.create_polygon(
                            cx - int(30 * sx), waist_y,
                            cx - int(8 * sx), waist_y,
                            cx - int(12 * sx), leg_bottom + left_swing,
                            cx - int(28 * sx), leg_bottom + left_swing,
                            fill=color, outline=shadow, width=1,
                            tags="equipped_clothing")
                        # Right leg
                        c.create_polygon(
                            cx + int(8 * sx), waist_y,
                            cx + int(30 * sx), waist_y,
                            cx + int(28 * sx), leg_bottom + right_swing,
                            cx + int(12 * sx), leg_bottom + right_swing,
                            fill=color, outline=shadow, width=1,
                            tags="equipped_clothing")
                        # Highlight seams
                        c.create_line(
                            cx, waist_y, cx, leg_bottom,
                            fill=highlight, width=1, tags="equipped_clothing")

                    # --- Jacket: torso + extended sleeves synced with arms ---
                    elif ctype == 'jacket':
                        # Main jacket body (torso)
                        c.create_polygon(
                            cx - int(40 * sx), bt,
                            cx - int(44 * sx), bt + int(14 * sy),
                            cx - int(42 * sx), mid,
                            cx - int(38 * sx), bb,
                            cx + int(38 * sx), bb,
                            cx + int(42 * sx), mid,
                            cx + int(44 * sx), bt + int(14 * sy),
                            cx + int(40 * sx), bt,
                            fill=color, outline=shadow, width=1,
                            smooth=True, tags="equipped_clothing")
                        # Collar
                        c.create_arc(
                            cx - int(18 * sx), bt - int(6 * sy),
                            cx + int(18 * sx), bt + int(10 * sy),
                            start=200, extent=140, style="arc",
                            outline=shadow, width=2, tags="equipped_clothing")
                        # Centre zipper/buttons
                        c.create_line(
                            cx, bt + int(6 * sy), cx, bb - int(4 * sy),
                            fill=shadow, width=2, tags="equipped_clothing")
                        # Long sleeves following arm swing + dangle
                        arm_top = bt + int(4 * sy)
                        arm_len = int(40 * sy)
                        for side, swing, dangle in [(-1, _arm_swing, _left_arm_dangle), (1, -_arm_swing, _right_arm_dangle)]:
                            arm_cx = cx + side * int(44 * sx)
                            arm_end_y = arm_top + arm_len + int(swing) + dangle
                            c.create_polygon(
                                arm_cx - int(10 * sx), arm_top,
                                arm_cx + int(10 * sx), arm_top,
                                arm_cx + int(8 * sx), arm_end_y,
                                arm_cx - int(8 * sx), arm_end_y,
                                fill=color, outline=shadow, width=1,
                                tags="equipped_clothing")
                            # Cuff highlight
                            c.create_line(
                                arm_cx - int(7 * sx), arm_end_y - int(2 * sy),
                                arm_cx + int(7 * sx), arm_end_y - int(2 * sy),
                                fill=highlight, width=1, tags="equipped_clothing")

                    # --- Dress: flows from neck to below body ---
                    elif ctype == 'dress':
                        dress_bottom = bb + int(12 * sy)
                        c.create_polygon(
                            cx - int(28 * sx), bt,
                            cx - int(38 * sx), mid,
                            cx - int(44 * sx), dress_bottom,
                            cx + int(44 * sx), dress_bottom,
                            cx + int(38 * sx), mid,
                            cx + int(28 * sx), bt,
                            fill=color, outline=shadow, width=1,
                            smooth=True, tags="equipped_clothing")
                        # Neckline
                        c.create_arc(
                            cx - int(14 * sx), bt - int(4 * sy),
                            cx + int(14 * sx), bt + int(8 * sy),
                            start=200, extent=140, style="arc",
                            outline=shadow, width=2, tags="equipped_clothing")
                        # Waist ribbon
                        c.create_rectangle(
                            cx - int(30 * sx), mid - int(3 * sy),
                            cx + int(30 * sx), mid + int(3 * sy),
                            fill=highlight, outline='', tags="equipped_clothing")

                    # --- Full body: covers torso + legs + sleeves ---
                    elif ctype == 'full_body':
                        leg_bottom = int(170 * sy + by)
                        left_swing = int(_leg_swing) + _left_leg_dangle
                        right_swing = int(-_leg_swing) + _right_leg_dangle
                        # Torso section
                        c.create_polygon(
                            cx - int(38 * sx), bt,
                            cx - int(42 * sx), bt + int(12 * sy),
                            cx - int(40 * sx), mid,
                            cx - int(36 * sx), bb,
                            cx + int(36 * sx), bb,
                            cx + int(40 * sx), mid,
                            cx + int(42 * sx), bt + int(12 * sy),
                            cx + int(38 * sx), bt,
                            fill=color, outline=shadow, width=1,
                            smooth=True, tags="equipped_clothing")
                        # Collar
                        c.create_arc(
                            cx - int(16 * sx), bt - int(6 * sy),
                            cx + int(16 * sx), bt + int(10 * sy),
                            start=200, extent=140, style="arc",
                            outline=shadow, width=2, tags="equipped_clothing")
                        # Pant legs synced with leg swing
                        for leg_side, leg_sw in [(-1, left_swing), (1, right_swing)]:
                            lx = cx + leg_side * int(19 * sx)
                            c.create_polygon(
                                lx - int(14 * sx), bb,
                                lx + int(14 * sx), bb,
                                lx + int(12 * sx), leg_bottom + leg_sw,
                                lx - int(12 * sx), leg_bottom + leg_sw,
                                fill=color, outline=shadow, width=1,
                                tags="equipped_clothing")
                        # Sleeves synced with arm swing + dangle
                        arm_top = bt + int(4 * sy)
                        arm_len = int(35 * sy)
                        for side, swing, dangle in [(-1, _arm_swing, _left_arm_dangle), (1, -_arm_swing, _right_arm_dangle)]:
                            arm_cx = cx + side * int(42 * sx)
                            arm_end_y = arm_top + arm_len + int(swing) + dangle
                            c.create_oval(
                                arm_cx - int(10 * sx), arm_top,
                                arm_cx + int(10 * sx), arm_end_y,
                                fill=color, outline=shadow, width=1,
                                tags="equipped_clothing")
                        # Centre highlight
                        c.create_line(
                            cx, bt + int(8 * sy), cx, bb - int(4 * sy),
                            fill=highlight, width=1, tags="equipped_clothing")

                    # --- Default (shirt): torso-only garment ---
                    else:
                        # Main shirt body - follows torso curve
                        c.create_polygon(
                            cx - int(38 * sx), bt,
                            cx - int(42 * sx), bt + int(12 * sy),
                            cx - int(40 * sx), mid,
                            cx - int(36 * sx), bb,
                            cx + int(36 * sx), bb,
                            cx + int(40 * sx), mid,
                            cx + int(42 * sx), bt + int(12 * sy),
                            cx + int(38 * sx), bt,
                            fill=color, outline=shadow, width=1,
                            smooth=True, tags="equipped_clothing")
                        # Collar / neckline
                        c.create_arc(
                            cx - int(16 * sx), bt - int(6 * sy),
                            cx + int(16 * sx), bt + int(10 * sy),
                            start=200, extent=140, style="arc",
                            outline=shadow, width=2, tags="equipped_clothing")
                        # Centre highlight stripe
                        c.create_line(
                            cx, bt + int(8 * sy), cx, bb - int(4 * sy),
                            fill=highlight, width=1, tags="equipped_clothing")
                        # Sleeve caps synced with arm swing + dangle
                        for side, swing, dangle in [(-1, _arm_swing, _left_arm_dangle), (1, -_arm_swing, _right_arm_dangle)]:
                            sleeve_cx = cx + side * int(40 * sx)
                            sleeve_offset = int(swing * 0.4) + int(dangle * 0.4)
                            c.create_oval(
                                sleeve_cx - int(10 * sx), bt + int(2 * sy) + sleeve_offset,
                                sleeve_cx + int(10 * sx), bt + int(18 * sy) + sleeve_offset,
                                fill=color, outline=shadow, width=1,
                                tags="equipped_clothing")

            # --- Draw hat on top of head ---
            if appearance.hat:
                hat_item = self.panda_closet.get_item(appearance.hat)
                if hat_item:
                    color = self._color_for_emoji(hat_item.emoji, '#1a1a1a')
                    shadow = self._shade_color(color, -30)
                    highlight = self._shade_color(color, 50)

                    hat_y = int(20 * sy + by)

                    # Hat brim - wider, slightly rounded
                    c.create_oval(
                        cx - int(34 * sx), hat_y - int(2 * sy),
                        cx + int(34 * sx), hat_y + int(8 * sy),
                        fill=color, outline=shadow, width=1, tags="equipped_hat")

                    # Hat crown - rounded top
                    c.create_oval(
                        cx - int(22 * sx), hat_y - int(22 * sy),
                        cx + int(22 * sx), hat_y + int(4 * sy),
                        fill=color, outline=shadow, width=1, tags="equipped_hat")

                    # Hat band / ribbon detail
                    c.create_rectangle(
                        cx - int(22 * sx), hat_y - int(4 * sy),
                        cx + int(22 * sx), hat_y + int(1 * sy),
                        fill=shadow, outline='', tags="equipped_hat")

                    # Highlight on crown
                    c.create_arc(
                        cx - int(14 * sx), hat_y - int(20 * sy),
                        cx + int(6 * sx), hat_y - int(8 * sy),
                        start=20, extent=140, style="arc",
                        outline=highlight, width=1, tags="equipped_hat")

            # --- Draw accessories with type-specific positioning ---
            if appearance.accessories:
                # Include dangle physics for drag sync. Dangle represents whole-body
                # motion, applied equally to both arms; swing provides left/right symmetry.
                arm_dangle = int(self._dangle_arm)
                arm_dangle_h = int(self._dangle_arm_h)
                la_swing = _arm_swing + arm_dangle
                ra_swing = -_arm_swing + arm_dangle

                # Classify accessories by type for proper placement
                _WRIST_IDS = {
                    'bamboo_bracelet', 'friendship_band', 'watch',
                    'diamond_ring',
                }
                _NECK_IDS = {
                    'bowtie', 'bow_tie', 'necklace', 'pearl_necklace',
                    'scarf', 'bandana',
                }

                for i, acc_id in enumerate(appearance.accessories[:3]):
                    acc_item = self.panda_closet.get_item(acc_id)
                    if not acc_item:
                        continue
                    color = self._color_for_emoji(acc_item.emoji, '#FF69B4')
                    shadow = self._shade_color(color, -25)
                    highlight = self._shade_color(color, 60)

                    if acc_id in _WRIST_IDS:
                        # --- Draw on wrist (end of arm) ---
                        arm_top = int(95 * sy + by)
                        arm_len = int(35 * sy)
                        wrist_y = arm_top + arm_len
                        if i % 2 == 0:
                            wrist_x = cx - int(42 * sx) + arm_dangle_h
                            wrist_y_adj = wrist_y + int(la_swing)
                        else:
                            wrist_x = cx + int(42 * sx) + arm_dangle_h
                            wrist_y_adj = wrist_y + int(ra_swing)
                        # Bracelet band
                        band_h = int(5 * sy)
                        c.create_oval(
                            wrist_x - int(10 * sx), wrist_y_adj - band_h,
                            wrist_x + int(10 * sx), wrist_y_adj + band_h,
                            fill=color, outline=shadow, width=1,
                            tags="equipped_acc")
                        # Gem/detail on bracelet
                        c.create_oval(
                            wrist_x - int(3 * sx), wrist_y_adj - int(2 * sy),
                            wrist_x + int(3 * sx), wrist_y_adj + int(2 * sy),
                            fill=highlight, outline='',
                            tags="equipped_acc")

                    elif acc_id in _NECK_IDS:
                        # --- Draw on neck area ---
                        neck_y = int(78 * sy + by)
                        if acc_id in ('bowtie', 'bow_tie'):
                            # Bow tie shape: two triangles meeting at center
                            bow_w = int(14 * sx)
                            bow_h = int(8 * sy)
                            # Left wing
                            c.create_polygon(
                                cx, neck_y,
                                cx - bow_w, neck_y - bow_h,
                                cx - bow_w, neck_y + bow_h,
                                fill=color, outline=shadow, width=1,
                                tags="equipped_acc")
                            # Right wing
                            c.create_polygon(
                                cx, neck_y,
                                cx + bow_w, neck_y - bow_h,
                                cx + bow_w, neck_y + bow_h,
                                fill=color, outline=shadow, width=1,
                                tags="equipped_acc")
                            # Center knot
                            c.create_oval(
                                cx - int(3 * sx), neck_y - int(3 * sy),
                                cx + int(3 * sx), neck_y + int(3 * sy),
                                fill=shadow, outline='',
                                tags="equipped_acc")
                        elif acc_id in ('necklace', 'pearl_necklace'):
                            # Necklace arc around neck
                            c.create_arc(
                                cx - int(24 * sx), neck_y - int(10 * sy),
                                cx + int(24 * sx), neck_y + int(16 * sy),
                                start=200, extent=140, style="arc",
                                outline=color, width=2, tags="equipped_acc")
                            # Pendant
                            c.create_oval(
                                cx - int(4 * sx), neck_y + int(10 * sy),
                                cx + int(4 * sx), neck_y + int(16 * sy),
                                fill=color, outline=shadow, width=1,
                                tags="equipped_acc")
                        else:
                            # Scarf / bandana - draped around neck
                            c.create_arc(
                                cx - int(28 * sx), neck_y - int(6 * sy),
                                cx + int(28 * sx), neck_y + int(12 * sy),
                                start=200, extent=140, style="arc",
                                outline=color, width=3, tags="equipped_acc")
                    else:
                        # --- Default: pendant near chest ---
                        neck_y = int(90 * sy + by)
                        ox = int((-12 + i * 24) * sx)
                        pts = [
                            cx + ox, neck_y - int(7 * sy),
                            cx + ox - int(10 * sx), neck_y,
                            cx + ox, neck_y + int(7 * sy),
                            cx + ox + int(10 * sx), neck_y,
                        ]
                        c.create_polygon(
                            *pts, fill=color, outline=shadow, width=1,
                            tags="equipped_acc")
                        c.create_oval(
                            cx + ox - int(3 * sx), neck_y - int(3 * sy),
                            cx + ox + int(3 * sx), neck_y + int(3 * sy),
                            fill=highlight, outline='',
                            tags="equipped_acc")

            # --- Draw shoes at feet (synced with leg movement) ---
            if appearance.shoes:
                shoes_item = self.panda_closet.get_item(appearance.shoes)
                if shoes_item:
                    color = self._color_for_emoji(shoes_item.emoji, '#8B4513')
                    shadow = self._shade_color(color, -30)
                    highlight = self._shade_color(color, 40)
                    foot_base = int(170 * sy + by)
                    # Include dangle physics for drag sync. Dangle represents whole-body
                    # motion applied equally to both legs; swing provides left/right symmetry.
                    leg_dangle = int(self._dangle_leg)
                    leg_dangle_h = int(self._dangle_leg_h)
                    left_shoe_swing = int(_leg_swing) + leg_dangle
                    right_shoe_swing = int(-_leg_swing) + leg_dangle

                    for shoe_cx, shoe_swing in [(cx - int(25 * sx), left_shoe_swing),
                                                 (cx + int(25 * sx), right_shoe_swing)]:
                        shoe_y = foot_base + shoe_swing
                        shoe_x = shoe_cx + leg_dangle_h
                        # Shoe body
                        c.create_oval(
                            shoe_x - int(15 * sx), shoe_y,
                            shoe_x + int(15 * sx), shoe_y + int(12 * sy),
                            fill=color, outline=shadow, width=1,
                            tags="equipped_shoes")
                        # Sole
                        c.create_rectangle(
                            shoe_x - int(14 * sx), shoe_y + int(8 * sy),
                            shoe_x + int(14 * sx), shoe_y + int(12 * sy),
                            fill=shadow, outline='', tags="equipped_shoes")
                        # Lace / highlight
                        c.create_line(
                            shoe_x - int(4 * sx), shoe_y + int(3 * sy),
                            shoe_x + int(4 * sx), shoe_y + int(3 * sy),
                            fill=highlight, width=1, tags="equipped_shoes")
        except Exception as e:
            logger.debug(f"Error drawing equipped items: {e}")

    @staticmethod
    def _shade_color(hex_color: str, amount: int) -> str:
        """Lighten (positive) or darken (negative) a hex color by *amount*."""
        try:
            hex_color = hex_color.lstrip('#')
            r = max(0, min(255, int(hex_color[0:2], 16) + amount))
            g = max(0, min(255, int(hex_color[2:4], 16) + amount))
            b = max(0, min(255, int(hex_color[4:6], 16) + amount))
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            return hex_color
    
    def _draw_animation_extras(self, c: tk.Canvas, cx: int, by: float,
                                anim: str, frame_idx: int, sx: float = 1.0, sy: float = 1.0):
        """Draw extra decorations based on animation type."""
        emoji_list = self.ANIMATION_EMOJIS.get(anim)
        if emoji_list:
            # Cycle emojis slowly to avoid frantic flicker
            emoji = emoji_list[(frame_idx // self.EMOJI_CYCLE_FRAMES) % len(emoji_list)]
            c.create_text(cx + int(55 * sx), int(18 * sy + by), text=emoji,
                          font=("Arial", int(20 * sx)), tags="extra")
        
        # Blush cheeks when petting, celebrating, playing, eating, etc.
        if anim in ('petting', 'celebrating', 'fed', 'playing', 'eating', 'customizing', 'belly_rub', 'belly_grab', 'belly_jiggle'):
            cheek_y = int(56 * sy + by)
            br = int(5 * sx)
            c.create_oval(cx - int(38 * sx), cheek_y - br, cx - int(28 * sx), cheek_y + br,
                          fill="#FFB6C1", outline="", tags="blush")
            c.create_oval(cx + int(28 * sx), cheek_y - br, cx + int(38 * sx), cheek_y + br,
                          fill="#FFB6C1", outline="", tags="blush")
        
        # Draw active item during eating/playing animations
        if self._active_item_emoji:
            if anim == 'eating':
                # Multi-phase eating: pickup → inspect → chew → satisfied
                # Use the eating sequence phase if available, else fall back
                phase = getattr(self, '_eating_phase', 0)
                mouth_y = int(68 * sy + by)

                if phase == 0:
                    # Phase 0: Picking up — food on the ground, panda reaching
                    reach_t = (frame_idx % 25) / 25.0
                    item_x = cx - int(30 * sx) + int(reach_t * 15 * sx)
                    item_y = int(140 * sy + by) - int(reach_t * 50 * sy)
                    item_size = int(18 * sx)
                elif phase == 1:
                    # Phase 1: Inspecting — food held up, slight tilt/sniff
                    sniff_bob = math.sin(frame_idx * 0.8) * int(4 * sy)
                    item_x = cx - int(10 * sx) + int(math.sin(frame_idx * 0.5) * 3 * sx)
                    item_y = int(75 * sy + by) + sniff_bob
                    item_size = int(16 * sx)
                elif phase == 2:
                    # Phase 2: Chewing — food at mouth, shrinking as eaten
                    eat_progress = getattr(self, '_eating_frame', 0) / max(1, self.EATING_CHEW_FRAMES)
                    bob = math.sin(frame_idx * 1.5) * int(3 * sy)
                    item_x = cx - int(12 * sx)
                    item_y = mouth_y + bob
                    # Food shrinks as it's eaten
                    item_size = int(16 * sx * (1.0 - eat_progress * 0.8))
                    # Add crumb particles during chewing
                    if frame_idx % 6 < 3:
                        crumb_x = item_x + random.randint(-int(10 * sx), int(10 * sx))
                        crumb_y = item_y + random.randint(0, int(8 * sy))
                        c.create_text(crumb_x, crumb_y, text="·",
                                      font=("Arial", max(4, int(6 * sx))),
                                      fill="#8B4513", tags="active_item")
                else:
                    # Phase 3: Satisfied — food gone, happy belly pat
                    item_x = None
                    item_y = None
                    item_size = 0

                if item_x is not None:
                    c.create_text(item_x, item_y, text=self._active_item_emoji,
                                  font=("Arial", max(8, item_size)), tags="active_item")
            elif anim == 'playing':
                # Draw toy item near panda's hands with play motion
                play_cycle = (frame_idx % 60) / 60.0
                if play_cycle < 0.3:
                    # Bouncing - toy in front, bouncing up and down
                    bounce = abs(math.sin(frame_idx * 0.5)) * int(20 * sy)
                    item_x = cx
                    item_y = int(160 * sy + by) - bounce
                    item_size = int(18 * sx)
                elif play_cycle < 0.6:
                    # Playful swipe - toy near hand
                    swing = math.sin(frame_idx * 0.8) * int(25 * sx)
                    item_x = cx + int(swing)
                    item_y = int(100 * sy + by)
                    item_size = int(16 * sx)
                else:
                    # Tossed in air then caught
                    toss_phase = (play_cycle - 0.6) / 0.4
                    arc = -math.sin(toss_phase * math.pi) * int(40 * sy)
                    item_x = cx + int(20 * sx)
                    item_y = int(80 * sy + by) + arc
                    item_size = int(16 * sx)
                c.create_text(item_x, item_y, text=self._active_item_emoji,
                              font=("Arial", max(8, item_size)), tags="active_item")
        
        # Draw belly rub hands visual for belly_rub animation
        if anim == 'belly_rub':
            rub_cycle = (frame_idx % 60) / 60.0
            if 0.15 < rub_cycle < 0.75:
                # Draw small circular motion lines on belly area
                rub_t = (rub_cycle - 0.15) / 0.6
                rub_angle = rub_t * 6 * math.pi
                rub_x = cx + int(math.cos(rub_angle) * 8 * sx)
                rub_y = int(120 * sy + by) + int(math.sin(rub_angle) * 6 * sy)
                c.create_text(rub_x, rub_y, text="💕",
                              font=("Arial", max(8, int(10 * sx))), tags="rub_effect")
    
    def set_active_item(self, item_name: str = None, item_emoji: str = None,
                       item_type: str = None, item_key: str = None):
        """Set the item currently being used by the panda during eating/playing.
        
        Args:
            item_name: Display name of the item
            item_emoji: Emoji character for the item
            item_type: 'food' or 'toy'
            item_key: Widget key (e.g. 'bamboo') for per-item eating responses
        """
        self._active_item_name = item_name
        self._active_item_emoji = item_emoji
        self._active_item_type = item_type
        self._active_item_key = item_key
    
    def walk_to_item(self, target_x: int, target_y: int, item_name: str = None,
                     item_emoji: str = None, item_type: str = 'toy',
                     on_arrive=None, item_key: str = None):
        """Animate the panda walking to an item's location on screen.
        
        The panda toplevel smoothly moves towards the target coordinates,
        then triggers the appropriate interaction animation.
        For food items, the panda walks up, picks up the food, and plays
        a detailed multi-phase eating animation before the item disappears.
        
        Args:
            target_x: Screen X coordinate of the item
            target_y: Screen Y coordinate of the item
            item_name: Name of the item to interact with
            item_emoji: Emoji for the item
            item_type: 'food' or 'toy'
            on_arrive: Optional callback when panda arrives (for food, fires after eating)
            item_key: Widget key (e.g. 'bamboo') for per-item eating responses
        """
        if self._destroyed:
            return
        
        # Set the active item so it renders during the interaction
        self.set_active_item(item_name, item_emoji, item_type, item_key)
        
        # Start walking animation
        self._set_animation_no_cancel('carrying' if item_type == 'food' else 'playing')
        
        # Get current panda position
        try:
            px = self._toplevel.winfo_x()
            py = self._toplevel.winfo_y()
        except Exception:
            return
        
        # Calculate distance and direction
        dx = target_x - px - self._toplevel_w // 2
        dy = target_y - py - self._toplevel_h // 2
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        
        # Walk speed: ~4px per frame at 50ms intervals
        speed = 4
        steps = max(1, int(dist / speed))
        step_x = dx / steps
        step_y = dy / steps
        
        self._walk_step_count = 0
        self._walk_total_steps = steps
        self._walk_step_dx = step_x
        self._walk_step_dy = step_y
        self._walk_on_arrive = on_arrive
        self._walk_item_type = item_type
        
        # Show speech
        if self.panda and item_name:
            response = self.panda.on_item_interact(item_name, item_type)
            self.info_label.configure(text=response)
        
        self._walk_tick()
    
    def _walk_tick(self):
        """Single step of the walk-to-item animation."""
        if self._destroyed:
            return
        
        self._walk_step_count += 1
        if self._walk_step_count > self._walk_total_steps:
            # Arrived at the item
            if self._walk_item_type == 'food':
                # Food: multi-phase sequence — pickup comment, then detailed eat
                if self.panda and self._active_item_name:
                    pickup_msg = self.panda.on_food_pickup(self._active_item_name) if hasattr(self.panda, 'on_food_pickup') else f"🐼 *picks up {self._active_item_name}*"
                    self.info_label.configure(text=pickup_msg)
                # Play the extended eating animation (longer duration for food)
                self._play_eating_sequence()
                # Callback fires only after the full eating animation finishes
                # (handled inside _eating_sequence_tick)
            else:
                # Toys: play animation normally
                self.play_animation_once('playing')
                if self._walk_on_arrive:
                    try:
                        self._walk_on_arrive()
                    except Exception:
                        pass
            return
        
        try:
            px = self._toplevel.winfo_x()
            py = self._toplevel.winfo_y()
            new_x = int(px + self._walk_step_dx)
            new_y = int(py + self._walk_step_dy)
            self._toplevel.geometry(f"+{new_x}+{new_y}")
        except Exception:
            return
        
        self.after(50, self._walk_tick)

    # Duration in frames for each phase of the eating sequence
    EATING_PICKUP_FRAMES = 25   # ~825ms - picking up the food
    EATING_INSPECT_FRAMES = 20  # ~660ms - inspecting / sniffing
    EATING_CHEW_FRAMES = 40     # ~1320ms - chewing / munching
    EATING_SATISFIED_FRAMES = 20  # ~660ms - happy satisfaction

    def _play_eating_sequence(self):
        """Start the multi-phase eating sequence: pickup → inspect → chew → satisfied."""
        if self._destroyed:
            return
        self._eating_phase = 0  # 0=pickup, 1=inspect, 2=chew, 3=satisfied
        self._eating_frame = 0
        self._cancel_animation_timer()
        self.current_animation = 'eating'
        self.animation_frame = 0
        self._eating_sequence_tick()

    def _eating_sequence_tick(self):
        """Tick for the multi-phase eating animation."""
        if self._destroyed:
            return

        phase_frames = [
            self.EATING_PICKUP_FRAMES,
            self.EATING_INSPECT_FRAMES,
            self.EATING_CHEW_FRAMES,
            self.EATING_SATISFIED_FRAMES,
        ]

        try:
            self._draw_panda(self.animation_frame)
            self.animation_frame += 1
            self._eating_frame += 1

            # Show eating comment at the start of the chew phase (phase 2)
            if self._eating_phase == 2 and self._eating_frame == 1:
                if self.panda and self._active_item_name and hasattr(self.panda, 'on_eating'):
                    item_key = getattr(self, '_active_item_key', '') or ''
                    msg = self.panda.on_eating(self._active_item_name, item_key)
                    self.info_label.configure(text=msg)

            # Check if current phase is complete
            if self._eating_frame >= phase_frames[self._eating_phase]:
                self._eating_phase += 1
                self._eating_frame = 0

                if self._eating_phase >= len(phase_frames):
                    # All phases done — clear item and fire callback
                    self._active_item_name = None
                    self._active_item_emoji = None
                    self._active_item_type = None
                    self._active_item_key = None
                    if self._walk_on_arrive:
                        try:
                            self._walk_on_arrive()
                        except Exception:
                            pass
                    self.animation_timer = self.after(200, lambda: self.start_animation('idle'))
                    return

            self.animation_timer = self.after(self.ANIMATION_INTERVAL, self._eating_sequence_tick)
        except Exception as e:
            logger.error(f"Error in eating sequence: {e}")
            # Fallback: clear item and go idle
            self._active_item_name = None
            self._active_item_emoji = None
            self._active_item_type = None
            self._active_item_key = None
            if not self._destroyed:
                try:
                    self.animation_timer = self.after(500, lambda: self.start_animation('idle'))
                except Exception:
                    pass
    
    # Auto-walk comments the panda makes while exploring
    AUTO_WALK_COMMENTS = [
        "🐼 *waddling around* Just exploring!",
        "🐼 Hmm, what's over here?",
        "🐼 *looks around curiously* Nice place!",
        "🐼 I wonder what this button does... 🤔",
        "🐼 *walks casually* Don't mind me~",
        "🐼 Just stretching my legs! 🦵",
        "🐼 *humming* 🎵 la la la~",
        "🐼 Ooh, let me check this out!",
        "🐼 *sniffing around* I smell bamboo... 🎋",
        "🐼 Taking a little stroll! 🚶",
        "🐼 This app is pretty cool, honestly.",
        "🐼 *peeks at the UI* Interesting...",
        "🐼 I like this corner! Cozy~ 🏠",
        "🐼 *tiptoes* Shhh, being sneaky 🥷",
        "🐼 Where should I go next? 🤔",
        "🐼 *climbs up* Whew, good view from here! 🏔️",
        "🐼 *slides down* Wheee! 🛝",
        "🐼 So many textures to sort! 📂",
        "🐼 *pokes around* What's in this tab?",
        "🐼 I'm a busy panda! 💼",
    ]

    def _schedule_auto_walk(self):
        """Schedule the next autonomous walk after a random delay."""
        if self._destroyed:
            return
        # Random delay between 15-45 seconds before next auto-walk
        delay_ms = random.randint(15000, 45000)
        self._auto_walk_timer = self.after(delay_ms, self._start_auto_walk)
    
    def _start_auto_walk(self):
        """Begin an autonomous walk to a random location within the application."""
        if self._destroyed:
            return
        # Don't auto-walk while user is interacting
        if self.is_dragging or self._is_tossing or self._is_auto_walking:
            self._schedule_auto_walk()
            return
        
        # Don't interrupt existing walk-to-item animations
        if hasattr(self, '_walk_step_count') and hasattr(self, '_walk_total_steps'):
            if self._walk_step_count < self._walk_total_steps:
                self._schedule_auto_walk()
                return
        
        try:
            min_x, min_y, max_x, max_y = self._get_main_window_bounds()
            
            # Pick a random target within the application window
            target_x = random.randint(min_x, max(min_x, max_x))
            target_y = random.randint(min_y, max(min_y, max_y))
            
            # Get current position
            px = self._toplevel.winfo_x()
            py = self._toplevel.winfo_y()
            
            dx = target_x - px
            dy = target_y - py
            dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
            
            # Walk speed: ~3px per frame at 50ms intervals
            speed = 3
            steps = max(1, int(dist / speed))
            
            self._auto_walk_target_x = target_x
            self._auto_walk_target_y = target_y
            self._auto_walk_step_dx = dx / steps
            self._auto_walk_step_dy = dy / steps
            self._auto_walk_steps_remaining = steps
            self._is_auto_walking = True
            
            # Show a comment
            comment = random.choice(self.AUTO_WALK_COMMENTS)
            self.info_label.configure(text=comment)
            
            # Use a walking-style animation (varies for visual interest)
            walk_anims = ['waving', 'dancing', 'stretching', 'belly_rub']
            self._set_animation_no_cancel(random.choice(walk_anims))
            
            # Start walking
            self._auto_walk_tick()
        except Exception as e:
            logger.debug(f"Auto-walk start error: {e}")
            self._is_auto_walking = False
            self._schedule_auto_walk()
    
    def _auto_walk_tick(self):
        """Single step of autonomous walking animation."""
        if self._destroyed:
            return
        
        # Stop if user started dragging
        if self.is_dragging or self._is_tossing:
            self._is_auto_walking = False
            self._schedule_auto_walk()
            return
        
        self._auto_walk_steps_remaining -= 1
        if self._auto_walk_steps_remaining <= 0:
            # Arrived at destination
            self._is_auto_walking = False
            self._save_panda_position()
            self.start_animation('idle')
            self._schedule_auto_walk()
            return
        
        try:
            px = self._toplevel.winfo_x()
            py = self._toplevel.winfo_y()
            new_x = int(px + self._auto_walk_step_dx)
            new_y = int(py + self._auto_walk_step_dy)
            
            # Clamp to application window bounds
            min_x, min_y, max_x, max_y = self._get_main_window_bounds()
            new_x = max(min_x, min(new_x, max_x))
            new_y = max(min_y, min(new_y, max_y))
            
            self._toplevel.geometry(f"+{new_x}+{new_y}")
        except Exception:
            self._is_auto_walking = False
            self._schedule_auto_walk()
            return
        
        self.after(50, self._auto_walk_tick)

    def react_to_item_hit(self, item_name: str, item_emoji: str, hit_y_ratio: float):
        """React to an item being thrown at the panda.
        
        Triggers a wobble/bump animation depending on where the item hits.
        Sometimes the panda catches the item instead of getting bonked.
        
        Args:
            item_name: Name of the item that hit
            item_emoji: Emoji for the item
            hit_y_ratio: Where on the panda the item hit (0=top of head, 1=feet)
        """
        if self._destroyed or not self.panda:
            return
        
        # 25% chance panda catches the item (only for body/belly hits)
        if 0.25 <= hit_y_ratio < 0.65 and random.random() < 0.25:
            response = f"🐼 *catches {item_name}!* Nice throw! 🎯"
            self.info_label.configure(text=response)
            self.set_active_item(item_name, item_emoji, 'toy')
            self.play_animation_once('celebrating')
            return
        
        # Determine body part from hit position
        if hit_y_ratio < 0.25:
            body_part = 'head'
        elif hit_y_ratio < 0.65:
            body_part = 'belly'
        else:
            body_part = 'legs'
        
        # Get panda reaction
        response = self.panda.on_item_thrown_at(item_name, body_part)
        self.info_label.configure(text=response)
        
        # Play appropriate reaction animation
        if body_part == 'head':
            self.play_animation_once('shaking')
        elif body_part == 'belly':
            # Trigger belly jiggle physics on item impact
            self._belly_jiggle_vel += random.choice([-1, 1]) * self.JIGGLE_VELOCITY_ITEM_HIT
            self.play_animation_once('belly_jiggle')
        else:
            self.play_animation_once('jumping')
    
    def _on_drag_start(self, event):
        """Handle start of drag operation."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True
        self._drag_moved = False
        # Stop any auto-walk in progress
        self._is_auto_walking = False
        # Detect which body part is being grabbed
        label_height = max(1, self.panda_label.winfo_height())
        label_width = max(1, self.panda_label.winfo_width())
        rel_y = event.y / label_height
        rel_x = event.x / label_width
        self._drag_grab_head = rel_y < 0.32  # HEAD_BOUNDARY
        # Determine the specific body part grabbed for spin/shake detection
        if self.panda and hasattr(self.panda, 'get_body_part_at_position'):
            self._drag_grab_part = self.panda.get_body_part_at_position(rel_y, rel_x)
        else:
            # Fallback if panda character not available
            self._drag_grab_part = 'head' if self._drag_grab_head else 'body'
        
        # Check if grabbed by leg (will cause upside-down if dragged upward)
        self._is_upside_down = False  # Will be set during drag motion if pulled up
        
        # Stop any active toss physics
        if self._toss_timer:
            try:
                self.after_cancel(self._toss_timer)
            except Exception:
                pass
            self._toss_timer = None
            self._is_tossing = False
        # Init velocity tracking
        self._prev_drag_x = event.x_root
        self._prev_drag_y = event.y_root
        self._prev_drag_time = time.monotonic()
    
    def _on_drag_motion(self, event):
        """Handle drag motion - move the panda container with throttling."""
        if not self.is_dragging:
            return
        
        # Throttle drag events to ~60fps (16ms) to prevent frame spikes
        now = time.monotonic()
        if now - self._last_drag_time < 0.016:
            return
        self._last_drag_time = now
        
        # Track position for drag pattern detection
        self._drag_positions.append((event.x_root, event.y_root, now))
        # Keep only recent positions
        self._drag_positions = [(x, y, t) for x, y, t in self._drag_positions if now - t < self.DRAG_HISTORY_SECONDS]
        
        # Track velocity for toss
        dt = now - self._prev_drag_time if self._prev_drag_time else self.TOSS_FRAME_TIME
        if dt > 0:
            self._toss_velocity_x = (event.x_root - self._prev_drag_x) / max(dt, 0.001) * self.TOSS_FRAME_TIME
            self._toss_velocity_y = (event.y_root - self._prev_drag_y) / max(dt, 0.001) * self.TOSS_FRAME_TIME
            # Track velocities for limb dangle and ear stretch physics
            self._prev_drag_vy = self._toss_velocity_y
            self._prev_drag_vx = self._toss_velocity_x
        self._prev_drag_x = event.x_root
        self._prev_drag_y = event.y_root
        self._prev_drag_time = now
        
        # Detect drag patterns
        self._detect_drag_patterns()
        
        # Check if dragged by leg and moving upward (upside-down flip)
        if self._drag_grab_part in ('left_leg', 'right_leg'):
            # If dragged upward (negative velocity), flip upside down
            if self._toss_velocity_y < -self.UPSIDE_DOWN_VELOCITY_THRESHOLD:
                self._is_upside_down = True
            elif self._toss_velocity_y > self.UPSIDE_DOWN_VELOCITY_THRESHOLD:
                self._is_upside_down = False
        else:
            self._is_upside_down = False
        
        # Check if we've moved enough to count as a real drag
        distance = ((event.x - self.drag_start_x) ** 2 + (event.y - self.drag_start_y) ** 2) ** 0.5
        if distance < self.CLICK_THRESHOLD:
            return
        
        if not self._drag_moved:
            # First real movement — switch to dragging animation
            self._drag_moved = True
            self._set_animation_no_cancel('dragging')
            if self.panda:
                # Pass grabbed_part for specific responses
                response = self.panda.on_drag(grabbed_part=self._drag_grab_part) if hasattr(self.panda, 'on_drag') else "🐼 Wheee!"
                self.info_label.configure(text=response)
        
        # Move the Toplevel window using screen coordinates
        try:
            tx = self._toplevel.winfo_x()
            ty = self._toplevel.winfo_y()
            new_x = tx + (event.x - self.drag_start_x)
            new_y = ty + (event.y - self.drag_start_y)
            
            # Application window bounds for wall detection
            min_x, min_y, max_x, max_y = self._get_main_window_bounds()
            
            hit_wall = False
            if new_x < min_x or new_x > max_x:
                hit_wall = True
            if new_y < min_y or new_y > max_y:
                hit_wall = True
            
            new_x = max(min_x, min(new_x, max_x))
            new_y = max(min_y, min(new_y, max_y))
            
            self._toplevel.geometry(f"+{new_x}+{new_y}")
            
            if hit_wall and now - self._last_wall_hit_time > self.WALL_HIT_COOLDOWN_SECONDS:
                self._last_wall_hit_time = now
                self._set_animation_no_cancel('wall_hit')
                if self.panda:
                    response = self.panda.on_wall_hit() if hasattr(self.panda, 'on_wall_hit') else "🐼 Ouch!"
                    self.info_label.configure(text=response)
        except Exception as e:
            logger.debug(f"Drag motion error: {e}")
    
    def _detect_drag_patterns(self):
        """Detect circular or shaking drag patterns.
        
        Uses velocity and motion shape to distinguish between:
        - Shaking: rapid side-to-side with high velocity
        - Spinning: consistent circular rotation around a center
        These are mutually exclusive; shake requires primarily linear
        back-and-forth motion while spin requires a circular path.
        
        Spin and shake detection is DISABLED when grabbed by head, arms, legs, or ears.
        It only occurs when grabbed by belly/body/butt.
        """
        if len(self._drag_positions) < 8:
            return
        
        # Disable spin/shake when grabbed by head, arms, legs, or ears
        # Only allow when grabbed by body/butt (belly region)
        disabled_parts = ('head', 'left_arm', 'right_arm', 'left_leg', 'right_leg', 
                         'left_ear', 'right_ear', 'nose', 'left_eye', 'right_eye')
        if self._drag_grab_part in disabled_parts:
            return
        
        # Only detect spin/shake when grabbed by belly (body/butt areas)
        if self._drag_grab_part not in ('body', 'butt'):
            return
        
        # Enforce cooldown between drag-pattern animation triggers
        now = time.monotonic()
        if now - self._last_drag_pattern_time < self.DRAG_PATTERN_COOLDOWN:
            return
        
        positions = self._drag_positions
        
        # Calculate average speed to distinguish fast shake from slow movement
        total_dist = 0.0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            total_dist += (dx * dx + dy * dy) ** 0.5
        time_span = positions[-1][2] - positions[0][2] if len(positions) > 1 else 1.0
        avg_speed = total_dist / max(time_span, 0.01)
        
        # Detect fast side-to-side shaking (rapid X direction changes at high speed)
        # Require high average speed to avoid false triggers from slow movement
        if avg_speed > self.MIN_SHAKE_VELOCITY:
            x_direction_changes = 0
            for i in range(2, len(positions)):
                dx_prev = positions[i-1][0] - positions[i-2][0]
                dx_curr = positions[i][0] - positions[i-1][0]
                if dx_prev * dx_curr < 0 and abs(dx_curr) > self.MIN_SHAKE_MOVEMENT:
                    x_direction_changes += 1
            
            if x_direction_changes >= self.SHAKE_DIRECTION_CHANGES:
                self._last_drag_pattern_time = now
                self._set_animation_no_cancel('shaking')
                if self.panda:
                    response = self.panda.on_shake() if hasattr(self.panda, 'on_shake') else "🐼 S-s-stop shaking me!"
                    self.info_label.configure(text=response)
                self._drag_positions = []
                return
        
        # Detect circular dragging (consistent angle rotation)
        # Requires enough points to form a real arc, and the path must
        # span a meaningful angle range to distinguish from linear drag
        if len(positions) >= self.MIN_SPIN_POSITIONS:
            angles = []
            cx = sum(p[0] for p in positions) / len(positions)
            cy = sum(p[1] for p in positions) / len(positions)
            for p in positions:
                angle = math.atan2(p[1] - cy, p[0] - cx)
                angles.append(angle)
            
            # Check for consistent rotation direction
            positive_diffs = 0
            negative_diffs = 0
            total_angle = 0.0
            for i in range(1, len(angles)):
                diff = angles[i] - angles[i-1]
                # Normalize to [-pi, pi]
                while diff > math.pi:
                    diff -= 2 * math.pi
                while diff < -math.pi:
                    diff += 2 * math.pi
                total_angle += abs(diff)
                if diff > self.MIN_ROTATION_ANGLE:
                    positive_diffs += 1
                elif diff < -self.MIN_ROTATION_ANGLE:
                    negative_diffs += 1
            
            total = positive_diffs + negative_diffs
            # Require sufficient total rotation and high directional consistency
            if total > 0 and total_angle > self.MIN_SPIN_TOTAL_ANGLE and (positive_diffs / total > self.SPIN_CONSISTENCY_THRESHOLD or negative_diffs / total > self.SPIN_CONSISTENCY_THRESHOLD):
                self._last_drag_pattern_time = now
                self._set_animation_no_cancel('spinning')
                if self.panda:
                    response = self.panda.on_spin() if hasattr(self.panda, 'on_spin') else "🐼 I'm getting dizzy! 🌀"
                    self.info_label.configure(text=response)
                self._drag_positions = []
                return

    def _on_drag_end(self, event):
        """Handle end of drag operation."""
        if not self.is_dragging:
            return
        
        self.is_dragging = False
        
        if not self._drag_moved:
            # It was just a click (minimal movement)
            self._on_click(event)
        else:
            # Start toss physics if there's enough velocity (actually thrown)
            speed = (self._toss_velocity_x ** 2 + self._toss_velocity_y ** 2) ** 0.5
            if speed > self.TOSS_MIN_VELOCITY:
                if self.panda:
                    response = self.panda.on_toss() if hasattr(self.panda, 'on_toss') else "🐼 WHEEEEE! 🚀"
                    self.info_label.configure(text=response)
                self._start_toss_physics()
            else:
                # Gentle release — just put down, not a toss
                if self.panda:
                    response = self.panda.on_drag() if hasattr(self.panda, 'on_drag') else "🐼 Home sweet home!"
                    self.info_label.configure(text=response)
                self._save_panda_position()
                self.start_animation('idle')
            
            # Award XP for moving the panda
            if self.panda and self.panda_level_system:
                try:
                    xp = self.panda_level_system.get_xp_reward('click') // 2
                except (KeyError, AttributeError, TypeError):
                    xp = 5
                self.panda_level_system.add_xp(xp, 'Moved panda')
    
    def _start_toss_physics(self):
        """Start toss physics simulation - panda bounces off walls and floor."""
        self._is_tossing = True
        self._set_animation_no_cancel('tossed')
        self._toss_bounce_count = 0
        self._toss_physics_tick()
    
    def _toss_physics_tick(self):
        """Run one frame of toss physics."""
        if self._destroyed or not self._is_tossing:
            return
        
        try:
            # Application window bounds
            min_x, min_y, max_x, max_y = self._get_main_window_bounds()
            
            # Current screen position
            x = float(self._toplevel.winfo_x())
            y = float(self._toplevel.winfo_y())
            
            # Apply gravity
            self._toss_velocity_y += self.TOSS_GRAVITY
            
            # Apply friction
            self._toss_velocity_x *= self.TOSS_FRICTION
            self._toss_velocity_y *= self.TOSS_FRICTION
            
            # Move
            x += self._toss_velocity_x
            y += self._toss_velocity_y
            
            # Bounce off application window edges
            bounced = False
            if x <= min_x:
                x = min_x
                self._toss_velocity_x = abs(self._toss_velocity_x) * self.TOSS_BOUNCE_DAMPING
                bounced = True
            elif x >= max_x:
                x = max_x
                self._toss_velocity_x = -abs(self._toss_velocity_x) * self.TOSS_BOUNCE_DAMPING
                bounced = True
            
            if y <= min_y:
                y = min_y
                self._toss_velocity_y = abs(self._toss_velocity_y) * self.TOSS_BOUNCE_DAMPING
                bounced = True
            elif y >= max_y:
                y = max_y
                self._toss_velocity_y = -abs(self._toss_velocity_y) * self.TOSS_BOUNCE_DAMPING
                bounced = True
            
            if bounced:
                self._toss_bounce_count += 1
                # Cycle through bounce animations
                bounce_anims = ['tossed', 'wall_hit', 'rolling', 'spinning']
                anim = bounce_anims[self._toss_bounce_count % len(bounce_anims)]
                self._set_animation_no_cancel(anim)
            
            # Place at new position
            self._toplevel.geometry(f"+{int(x)}+{int(y)}")
            
            # Check if velocity is low enough to stop
            speed = (self._toss_velocity_x ** 2 + self._toss_velocity_y ** 2) ** 0.5
            if speed < self.TOSS_MIN_VELOCITY:
                self._stop_toss_physics()
                return
            
            # Schedule next tick
            self._toss_timer = self.after(self.TOSS_FRAME_INTERVAL, self._toss_physics_tick)
        except Exception as e:
            logger.debug(f"Toss physics error: {e}")
            self._stop_toss_physics()
    
    def _stop_toss_physics(self):
        """Stop toss physics and save final position."""
        self._is_tossing = False
        if self._toss_timer:
            try:
                self.after_cancel(self._toss_timer)
            except Exception:
                pass
            self._toss_timer = None
        self._toss_velocity_x = 0.0
        self._toss_velocity_y = 0.0
        self._save_panda_position()
        self.start_animation('idle')
    
    def _save_panda_position(self):
        """Save the current panda position to config (relative to main window)."""
        try:
            root = self.winfo_toplevel()
            root.update_idletasks()
            rx = root.winfo_rootx()
            ry = root.winfo_rooty()
            rw = max(1, root.winfo_width())
            rh = max(1, root.winfo_height())
            
            tx = self._toplevel.winfo_x()
            ty = self._toplevel.winfo_y()
            tw = max(1, self._toplevel.winfo_width())
            th = max(1, self._toplevel.winfo_height())
            
            # Store as relative coords (anchor "se" convention)
            rel_x = (tx + tw - rx) / rw
            rel_y = (ty + th - ry) / rh
            rel_x = max(0.05, min(1.0, rel_x))
            rel_y = max(0.05, min(1.0, rel_y))
            
            from src.config import config
            config.set('panda', 'position_x', value=rel_x)
            config.set('panda', 'position_y', value=rel_y)
            config.save()
            logger.info(f"Saved panda position: ({rel_x:.2f}, {rel_y:.2f})")
        except Exception as e:
            logger.warning(f"Failed to save panda position: {e}")
    
    def _on_click(self, event=None):
        """Handle left click on panda with body part detection."""
        try:
            if self.panda:
                # Detect which body part was clicked
                body_part = None
                if event and hasattr(self.panda, 'get_body_part_at_position'):
                    label_height = max(1, self.panda_label.winfo_height())
                    label_width = max(1, self.panda_label.winfo_width())
                    rel_y = event.y / label_height
                    rel_x = event.x / label_width
                    body_part = self.panda.get_body_part_at_position(rel_y, rel_x)
                
                # Belly poke triggers jiggle effect
                if body_part in ('body', 'butt') and hasattr(self.panda, 'on_belly_poke'):
                    response = self.panda.on_belly_poke()
                    self.info_label.configure(text=response)
                    # Trigger belly jiggle physics
                    self._belly_jiggle_vel += random.choice([-1, 1]) * self.JIGGLE_VELOCITY_POKE
                    self.play_animation_once('belly_jiggle')
                elif body_part and hasattr(self.panda, 'on_body_part_click'):
                    response = self.panda.on_body_part_click(body_part)
                    self.info_label.configure(text=response)
                    # Multiple random response animations for variety
                    # belly_rub is excluded — it should only play from inventory use
                    click_animations = ['clicked', 'waving', 'jumping', 'celebrating', 
                                       'stretching', 'dancing']
                    chosen_anim = random.choice(click_animations)
                    self.play_animation_once(chosen_anim)
                else:
                    response = self.panda.on_click()
                    self.info_label.configure(text=response)
                    click_animations = ['clicked', 'waving', 'jumping', 'celebrating', 
                                       'stretching', 'dancing']
                    chosen_anim = random.choice(click_animations)
                    self.play_animation_once(chosen_anim)
                
                # Award XP for clicking
                if self.panda_level_system:
                    xp = self.panda_level_system.get_xp_reward('click')
                    leveled_up, new_level = self.panda_level_system.add_xp(xp, 'Click interaction')
                    if leveled_up:
                        self.info_label.configure(text=f"🎉 Panda Level {new_level}!")
        except Exception as e:
            logger.error(f"Error handling panda click: {e}")
            self.info_label.configure(text="🐼 *confused panda noises*")
    
    def _on_mouse_motion(self, event=None):
        """Track mouse motion for pet-by-rubbing detection."""
        if self._destroyed or not self.panda or self.is_dragging:
            return
        
        now = time.monotonic()
        
        # Track positions for rubbing detection
        if event:
            self._rub_positions.append((event.x, event.y, now))
        
        # Keep only recent positions (last 1 second)
        self._rub_positions = [(x, y, t) for x, y, t in self._rub_positions if now - t < 1.0]
        
        # Detect rubbing: rapid back-and-forth motion
        if len(self._rub_positions) >= self.MIN_RUB_POSITIONS and now - self._last_rub_time > self.RUB_COOLDOWN_SECONDS:
            # Check for direction changes in x movement
            direction_changes = 0
            for i in range(2, len(self._rub_positions)):
                dx_prev = self._rub_positions[i-1][0] - self._rub_positions[i-2][0]
                dx_curr = self._rub_positions[i][0] - self._rub_positions[i-1][0]
                if dx_prev * dx_curr < 0:  # Direction changed
                    direction_changes += 1
            
            if direction_changes >= 2:
                # Rubbing detected! Trigger petting response
                self._last_rub_time = now
                label_height = max(1, self.panda_label.winfo_height())
                label_width = max(1, self.panda_label.winfo_width())
                rel_y = event.y / label_height if event else 0.5
                rel_x = event.x / label_width if event else 0.5
                
                if hasattr(self.panda, 'on_rub'):
                    body_part = self.panda.get_body_part_at_position(rel_y, rel_x)
                    response = self.panda.on_rub(body_part)
                else:
                    response = self.panda.on_pet()
                
                self.info_label.configure(text=response)
                self.play_animation_once('petting')
                self._rub_positions = []
                
                # Award XP for petting
                if self.panda_level_system:
                    try:
                        xp = self.panda_level_system.get_xp_reward('pet')
                        self.panda_level_system.add_xp(xp, 'Rubbing interaction')
                    except Exception:
                        pass
    
    def _on_right_click(self, event=None):
        """Handle right click on panda."""
        try:
            if self.panda:
                menu_items = self.panda.get_context_menu()
                # Create context menu with larger font for readability
                menu = tk.Menu(self, tearoff=0, font=("Arial", 15))
                for key, label in menu_items.items():
                    menu.add_command(
                        label=label,
                        command=lambda k=key: self._handle_menu_action(k)
                    )

                # Add panda stats submenu (name, gender, mood)
                menu.add_separator()
                stats_menu = tk.Menu(menu, tearoff=0, font=("Arial", 15))
                stats_menu.add_command(
                    label=f"📛 Rename Panda",
                    command=self._show_rename_dialog
                )
                stats_menu.add_command(
                    label=f"⚧ Change Gender",
                    command=self._show_gender_dialog
                )
                mood_indicator = self.panda.get_mood_indicator() if self.panda else "🐼"
                mood_name = self.panda.current_mood.value if self.panda else "happy"
                stats_menu.add_command(
                    label=f"{mood_indicator} Mood: {mood_name}",
                    state="disabled"
                )
                menu.add_cascade(label="📊 Panda Stats", menu=stats_menu)

                # Add toy/food sub-menus if widget collection available
                if self.widget_collection:
                    # Toys sub-menu
                    toys = self.widget_collection.get_toys(unlocked_only=True)
                    if toys:
                        menu.add_separator()
                        toy_menu = tk.Menu(menu, tearoff=0, font=("Arial", 15))
                        for toy in toys:
                            toy_menu.add_command(
                                label=f"{toy.emoji} {toy.name}",
                                command=lambda t=toy: self._give_widget_to_panda(t)
                            )
                        menu.add_cascade(label="🎾 Give Toy", menu=toy_menu)

                    # Food sub-menu
                    food = self.widget_collection.get_food(unlocked_only=True)
                    if food:
                        food_menu = tk.Menu(menu, tearoff=0, font=("Arial", 15))
                        for f in food:
                            food_menu.add_command(
                                label=f"{f.emoji} {f.name}",
                                command=lambda fd=f: self._give_widget_to_panda(fd)
                            )
                        menu.add_cascade(label="🍱 Give Food", menu=food_menu)

                # Add separator and "Reset Position" option
                menu.add_separator()
                menu.add_command(label="🏠 Reset to Corner", command=self._reset_position)
                
                try:
                    menu.tk_popup(event.x_root, event.y_root)
                finally:
                    menu.grab_release()
        except Exception as e:
            logger.error(f"Error handling panda right-click: {e}")
    
    def _reset_position(self):
        """Reset panda to default corner position."""
        try:
            root = self.winfo_toplevel()
            root.update_idletasks()
            rx = root.winfo_rootx()
            ry = root.winfo_rooty()
            rw = max(1, root.winfo_width())
            rh = max(1, root.winfo_height())
            
            abs_x = int(rx + 0.98 * rw - self._toplevel_w)
            abs_y = int(ry + 0.98 * rh - self._toplevel_h)
            self._toplevel.geometry(f"+{abs_x}+{abs_y}")
            
            # Save to config
            from src.config import config
            config.set('panda', 'position_x', value=0.98)
            config.set('panda', 'position_y', value=0.98)
            config.save()
        except Exception as e:
            logger.warning(f"Failed to save panda position: {e}")
        
        if self.panda:
            self.info_label.configure(text="🐼 Back to my corner!")

    def _show_rename_dialog(self):
        """Show dialog to rename the panda."""
        if not self.panda:
            return
        try:
            from tkinter import simpledialog
            new_name = simpledialog.askstring(
                "Rename Panda",
                f"Current name: {self.panda.name}\n\nEnter new name:",
                initialvalue=self.panda.name
            )
            if new_name and new_name.strip():
                new_name = new_name.strip()
                self.panda.set_name(new_name)
                # Save to config
                try:
                    from src.config import config
                    config.set('panda', 'name', value=new_name)
                    config.save()
                except Exception as e:
                    logger.warning(f"Failed to save panda name: {e}")
                self.info_label.configure(text=f"🐼 Call me {new_name}!")
                logger.info(f"Panda renamed to: {new_name}")
        except Exception as e:
            logger.error(f"Error renaming panda: {e}")

    def _show_gender_dialog(self):
        """Show dialog to change panda gender."""
        if not self.panda:
            return
        try:
            from src.features.panda_character import PandaGender
            # Create a small dialog window
            dialog = tk.Toplevel(self)
            dialog.title("Panda Gender")
            dialog.geometry("300x180")
            dialog.resizable(False, False)
            dialog.transient(self.winfo_toplevel())
            dialog.grab_set()

            tk.Label(dialog, text="Select Gender:", font=("Arial", 14, "bold")).pack(pady=10)

            gender_var = tk.StringVar(value=self.panda.gender.value)

            for gender, label in [
                (PandaGender.MALE, "♂ Male"),
                (PandaGender.FEMALE, "♀ Female"),
                (PandaGender.NON_BINARY, "⚧ Non-Binary")
            ]:
                tk.Radiobutton(
                    dialog, text=label, variable=gender_var,
                    value=gender.value, font=("Arial", 12)
                ).pack(anchor="w", padx=30)

            def apply_gender():
                selected = PandaGender(gender_var.get())
                self.panda.set_gender(selected)
                try:
                    from src.config import config
                    config.set('panda', 'gender', value=selected.value)
                    config.save()
                except Exception as e:
                    logger.warning(f"Failed to save panda gender: {e}")
                pronoun = self.panda.get_pronoun_subject()
                self.info_label.configure(text=f"🐼 Pronouns set to {pronoun}/{self.panda.get_pronoun_object()}!")
                logger.info(f"Panda gender set to: {selected.value}")
                dialog.destroy()

            tk.Button(dialog, text="Apply", font=("Arial", 12), command=apply_gender).pack(pady=10)
        except Exception as e:
            logger.error(f"Error changing panda gender: {e}")

    def _give_widget_to_panda(self, widget):
        """Give a toy or food widget to the panda.
        
        For food items, the panda plays the full eating sequence (pickup →
        inspect → chew → satisfied) and the food is only consumed after the
        animation completes.  For toys, an immediate play animation is shown.
        """
        try:
            from src.features.panda_widgets import FoodWidget
            if isinstance(widget, FoodWidget):
                # Food: consume only after full eating animation completes
                if widget.consumable and widget.quantity <= 0:
                    self.info_label.configure(
                        text=f"🐼 No {widget.name} left! Buy more from the shop.")
                    return

                # Resolve widget key for per-item eating responses
                wkey = ''
                if self.widget_collection:
                    for k, w in self.widget_collection.widgets.items():
                        if w is widget:
                            wkey = k
                            break

                def _on_eat_complete():
                    """Called after the full eating animation finishes."""
                    widget.use()  # Actually consume the food item now
                    if self.panda_level_system:
                        try:
                            xp = self.panda_level_system.get_xp_reward('click')
                            self.panda_level_system.add_xp(xp, f'Ate {widget.name}')
                        except Exception:
                            pass

                # Set active item and play multi-phase eating sequence in-place
                self.set_active_item(widget.name, widget.emoji, 'food', wkey)
                if self.panda:
                    msg = self.panda.on_food_pickup(widget.name) if hasattr(self.panda, 'on_food_pickup') else f"🐼 *picks up {widget.name}*"
                    self.info_label.configure(text=msg)
                self._walk_on_arrive = _on_eat_complete
                self._play_eating_sequence()
            else:
                # Toys: use immediately and play animation
                result = widget.use()
                message = result.get('message', f"Panda enjoys the {widget.name}!")
                self.info_label.configure(text=message)
                self.play_animation_once(result.get('animation', 'playing'))

                if self.panda_level_system:
                    try:
                        xp = self.panda_level_system.get_xp_reward('click')
                        self.panda_level_system.add_xp(xp, f'Used {widget.name}')
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Error giving widget to panda: {e}")
            self.info_label.configure(text="🐼 *confused*")
    
    def _on_hover(self, event=None):
        """Handle hover over panda."""
        if not self.is_dragging and self.panda:
            thought = self.panda.on_hover()
            self.info_label.configure(text=thought)
    
    def _on_leave(self, event=None):
        """Handle mouse leaving panda."""
        if not self.is_dragging:
            self.info_label.configure(text="🐼")
    
    def _handle_menu_action(self, action: str):
        """Handle menu item selection."""
        try:
            if action == 'pet_panda' and self.panda:
                reaction = self.panda.on_pet()
                self.info_label.configure(text=reaction)
                self.play_animation_once('celebrating')
                
                # Award XP for petting
                if self.panda_level_system:
                    xp = self.panda_level_system.get_xp_reward('pet')
                    leveled_up, new_level = self.panda_level_system.add_xp(xp, 'Pet interaction')
                    if leveled_up:
                        self.info_label.configure(text=f"🎉 Panda Level {new_level}!")
                        
            elif action == 'feed_bamboo' and self.panda:
                response = self.panda.on_feed()
                self.info_label.configure(text=response)
                self.play_animation_once('fed')
                
                # Award XP for feeding
                if self.panda_level_system:
                    xp = self.panda_level_system.get_xp_reward('feed')
                    leveled_up, new_level = self.panda_level_system.add_xp(xp, 'Feed interaction')
                    if leveled_up:
                        self.info_label.configure(text=f"🎉 Panda Level {new_level}!")
                        
            elif action == 'check_mood' and self.panda:
                mood = self.panda.get_mood_indicator()
                mood_name = self.panda.current_mood.value
                self.info_label.configure(text=f"{mood} Mood: {mood_name}")
        except Exception as e:
            logger.error(f"Error handling menu action '{action}': {e}")
    
    # Animations allowed while the panda is being dragged.
    # Only dangling/drag-related animations should play; everything else is
    # blocked so the panda doesn't randomly wave/dance while held by the head.
    DRAG_ALLOWED_ANIMATIONS = frozenset({
        'dragging', 'wall_hit', 'shaking', 'spinning',
    })

    def start_animation(self, animation_name: str):
        """Start looping animation."""
        if self._destroyed:
            return
        # Block non-drag animations while panda is being dragged
        if self.is_dragging and animation_name not in self.DRAG_ALLOWED_ANIMATIONS:
            return
        # Check if panda is disabled
        try:
            from src.config import config
            if config.get('ui', 'disable_panda_animations', default=False):
                # Hide panda entirely when disabled
                self._cancel_animation_timer()
                self.current_animation = animation_name
                try:
                    self._toplevel.withdraw()
                except Exception:
                    pass
                return
        except Exception:
            pass
        # Ensure toplevel is visible (in case it was hidden by disable)
        try:
            if self._toplevel.state() == 'withdrawn':
                self._toplevel.deiconify()
        except Exception:
            pass
        # Cancel any existing animation timer to avoid race conditions
        self._cancel_animation_timer()
        self.current_animation = animation_name
        self.animation_frame = 0
        self._animate_loop()
    
    def _set_animation_no_cancel(self, animation_name: str):
        """Set current animation frame without cancelling the timer.
        
        Used during drag to update the displayed frame immediately
        without disrupting the animation loop timing.
        """
        if self._destroyed:
            return
        self.current_animation = animation_name
        try:
            self._draw_panda(self.animation_frame)
        except Exception as e:
            logger.debug(f"Error setting animation frame: {e}")
    
    def play_animation_once(self, animation_name: str):
        """Play animation once then return to idle."""
        if self._destroyed:
            return
        # Block non-drag animations while panda is being dragged
        if self.is_dragging and animation_name not in self.DRAG_ALLOWED_ANIMATIONS:
            return
        # Respect disable setting
        try:
            from src.config import config
            if config.get('ui', 'disable_panda_animations', default=False):
                return
        except Exception:
            pass
        # Cancel any existing animation timer to avoid race conditions
        self._cancel_animation_timer()
        self.current_animation = animation_name
        self.animation_frame = 0
        self._animate_once()
    
    def _cancel_animation_timer(self):
        """Safely cancel any pending animation timer."""
        if self.animation_timer:
            try:
                self.after_cancel(self.animation_timer)
            except Exception:
                pass
            self.animation_timer = None
    
    def _get_equipped_items_text(self) -> str:
        """Get equipped items text for display below the panda."""
        if not self.panda_closet:
            return ""
        
        try:
            appearance = self.panda_closet.get_current_appearance()
            equipped_items = []
            
            if appearance.hat:
                hat_item = self.panda_closet.get_item(appearance.hat)
                if hat_item:
                    equipped_items.append(hat_item.emoji)
            
            if appearance.clothing:
                clothing_item = self.panda_closet.get_item(appearance.clothing)
                if clothing_item:
                    equipped_items.append(clothing_item.emoji)
            
            if appearance.shoes:
                shoes_item = self.panda_closet.get_item(appearance.shoes)
                if shoes_item:
                    equipped_items.append(shoes_item.emoji)
            
            if appearance.accessories:
                for acc_id in appearance.accessories[:3]:
                    acc_item = self.panda_closet.get_item(acc_id)
                    if acc_item:
                        equipped_items.append(acc_item.emoji)
            
            if equipped_items:
                return ' '.join(equipped_items)
            return ""
        except Exception as e:
            logger.debug(f"Error getting equipped items: {e}")
            return ""
    
    def _animate_loop(self):
        """Animate loop for continuous canvas-based animation."""
        if self._destroyed:
            return
        try:
            self._draw_panda(self.animation_frame)
            self.animation_frame += 1
            # Reset frame counter to prevent unbounded growth
            if self.animation_frame > self.MAX_ANIMATION_FRAME:
                self.animation_frame = 0
            
            # Continue animation
            self.animation_timer = self.after(self.ANIMATION_INTERVAL, self._animate_loop)
        except Exception as e:
            logger.error(f"Error in animation loop: {e}")
            if not self._destroyed:
                try:
                    self.animation_timer = self.after(self.ANIMATION_INTERVAL * 2, self._animate_loop)
                except Exception:
                    pass
    
    def _animate_once(self):
        """Animate continuously then return to idle after duration."""
        if self._destroyed:
            return
        try:
            self._draw_panda(self.animation_frame)
            self.animation_frame += 1

            # Keep animating for ~3 seconds (about 20 frames at 150ms)
            if self.animation_frame < 20:
                self.animation_timer = self.after(self.ANIMATION_INTERVAL, self._animate_once)
            else:
                # Clear active item when returning to idle
                self._active_item_name = None
                self._active_item_emoji = None
                self._active_item_type = None
                self._active_item_key = None
                # Return to idle
                self.animation_timer = self.after(200, lambda: self.start_animation('idle'))
        except Exception as e:
            logger.error(f"Error in single animation: {e}")
            if not self._destroyed:
                try:
                    self.animation_timer = self.after(1000, lambda: self.start_animation('idle'))
                except Exception:
                    pass
    
    def set_mood(self, mood):
        """Update panda mood and animation."""
        if self._destroyed:
            return
        if self.panda:
            self.panda.set_mood(mood)
            # Don't interrupt drag animations
            if self.is_dragging:
                return
            # Change animation based on mood — cover all mood types
            mood_animations = {
                'happy': 'idle',
                'excited': 'celebrating',
                'working': 'working',
                'tired': 'idle',
                'celebrating': 'celebrating',
                'sleeping': 'laying_down',
                'sarcastic': 'sarcastic',
                'rage': 'rage',
                'drunk': 'drunk',
                'existential': 'idle',
                'motivating': 'dancing',
                'tech_support': 'working',
                'sleepy': 'laying_side',
            }
            anim = mood_animations.get(mood.value if hasattr(mood, 'value') else mood, 'idle')
            self.start_animation(anim)
    
    def update_info(self, text: str):
        """Update info text below panda."""
        if not self._destroyed:
            self.info_label.configure(text=text)
    
    def destroy(self):
        """Clean up widget and Toplevel."""
        self._destroyed = True
        self._is_tossing = False
        self._cancel_animation_timer()
        if self._toss_timer:
            try:
                self.after_cancel(self._toss_timer)
            except Exception:
                pass
            self._toss_timer = None
        if self._speech_timer:
            try:
                self.after_cancel(self._speech_timer)
            except Exception:
                pass
            self._speech_timer = None
        if self._bg_refresh_job:
            try:
                self.after_cancel(self._bg_refresh_job)
            except Exception:
                pass
            self._bg_refresh_job = None
        if self._follow_main_job:
            try:
                self.after_cancel(self._follow_main_job)
            except Exception:
                pass
            self._follow_main_job = None
        # Unbind from main window to avoid stale references
        try:
            if self._destroy_bind_id and self._main_window:
                self._main_window.unbind("<Destroy>", self._destroy_bind_id)
        except Exception:
            pass
        # Destroy the separate Toplevel window
        try:
            self._toplevel.destroy()
        except Exception:
            pass
        super().destroy()

