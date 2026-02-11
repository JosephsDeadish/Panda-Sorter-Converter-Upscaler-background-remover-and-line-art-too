"""
Panda Widget - Animated panda character for the UI
Displays an interactive panda drawn on a canvas with body-shaped rendering
and walking/idle animations. Users can click, hover, pet, and drag the panda.
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import math
import random
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

# Speech bubble layout constants
BUBBLE_MAX_CHARS_PER_LINE = 30
BUBBLE_PAD_X = 14
BUBBLE_PAD_Y = 10
BUBBLE_CHAR_WIDTH = 8   # approximate px per character at font size 12
BUBBLE_LINE_HEIGHT = 20  # px per line of text
BUBBLE_MAX_WIDTH = 280
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
    
    # Animation timing (ms)
    ANIMATION_INTERVAL = 150
    # Reset frame counter at this value to prevent unbounded growth
    MAX_ANIMATION_FRAME = 10000
    
    # Drag pattern detection thresholds
    DRAG_HISTORY_SECONDS = 1.5      # How long to retain drag positions
    SHAKE_DIRECTION_CHANGES = 10    # X direction changes needed for shaking
    MIN_SHAKE_MOVEMENT = 2          # Min px movement for a direction change
    MIN_ROTATION_ANGLE = 0.15       # Min angle diff (radians) for spin detection
    SPIN_CONSISTENCY_THRESHOLD = 0.85  # Required ratio of consistent rotations
    
    # Toss physics constants
    TOSS_FRICTION = 0.92            # Velocity decay per frame
    TOSS_GRAVITY = 1.5              # Downward acceleration per frame
    TOSS_BOUNCE_DAMPING = 0.6       # Velocity retained after bounce
    TOSS_MIN_VELOCITY = 1.5         # Minimum velocity to keep bouncing
    TOSS_FRAME_INTERVAL = 20        # Physics tick interval (ms)
    TOSS_FRAME_TIME = 0.016         # Approximate frame time in seconds (~60fps)
    
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
        
        # Dragging state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        self._drag_moved = False  # Track if actual movement occurred
        # Track drag positions for pattern detection
        self._drag_positions = []  # list of (x, y, time) tuples
        self._last_drag_time = 0  # Throttle drag events (ms)
        self._last_wall_hit_time = 0  # Cooldown for wall hit reactions
        
        # Toss physics state
        self._toss_velocity_x = 0.0
        self._toss_velocity_y = 0.0
        self._toss_timer = None
        self._is_tossing = False
        self._prev_drag_x = 0
        self._prev_drag_y = 0
        self._prev_drag_time = 0
        
        # Configure frame - TRANSPARENT background
        if ctk:
            self.configure(fg_color="transparent", corner_radius=0, bg_color="transparent")
        else:
            try:
                parent_bg = parent.cget('bg')
                self.configure(bg=parent_bg, highlightthickness=0)
            except Exception:
                self.configure(highlightthickness=0)
        
        # Determine canvas background color to match parent theme
        self._canvas_bg = self._get_parent_bg()
        
        # Create canvas for panda body-shaped drawing with transparent bg
        self.panda_canvas = tk.Canvas(
            self,
            width=PANDA_CANVAS_W,
            height=PANDA_CANVAS_H,
            bg=self._canvas_bg,
            highlightthickness=0,
            bd=0,
        )
        self.panda_canvas.pack(pady=4, padx=4)
        
        # Speech bubble timer
        self._speech_timer = None
        
        # Create floating speech bubble canvas (appears next to panda)
        self._bubble_canvas = tk.Canvas(
            self,
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
        
        # Also bind to the frame itself for dragging
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # Draw initial panda and start animation
        self._draw_panda(0)
        self.start_animation('idle')
        
        # Deferred background refresh – once the widget tree is fully
        # rendered the parent background colour is reliably available.
        self.after(100, self._refresh_canvas_bg)
        
        # Set up periodic background refresh to keep canvas blended
        self._bg_refresh_job = None
        self._schedule_bg_refresh()
    
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
            # Redraw panda to ensure proper rendering with new background
            self._draw_panda(self.animation_frame)

    def _set_appearance_mode(self, mode_string):
        """Called by CustomTkinter when the appearance mode changes."""
        super()._set_appearance_mode(mode_string)
        self._refresh_canvas_bg()
        self._draw_panda(self.animation_frame)

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
        font = ("Arial", 14)
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
            fill="#333333", width=bubble_w - BUBBLE_PAD_X,
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
        
        # --- Determine limb offsets for walking ---
        # Cycle through 16 frames for smoother animation
        phase = (frame_idx % 16) / 16.0 * 2 * math.pi
        
        if anim in ('idle', 'working', 'sarcastic', 'thinking'):
            # Gentle body bob for idle with subtle arm sway
            leg_swing = 0
            arm_swing = math.sin(phase) * 3  # Subtle arm movement
            body_bob = math.sin(phase) * 2
        elif anim in ('dragging', 'tossed', 'wall_hit'):
            leg_swing = math.sin(phase) * 10
            arm_swing = math.sin(phase + math.pi) * 8
            body_bob = abs(math.sin(phase)) * 3
        elif anim == 'dancing':
            leg_swing = math.sin(phase) * 14
            arm_swing = math.sin(phase * 2) * 12
            body_bob = math.sin(phase * 2) * 5
        elif anim == 'celebrating':
            leg_swing = math.sin(phase) * 6
            arm_swing = -abs(math.sin(phase)) * 18  # Arms up
            body_bob = abs(math.sin(phase)) * 4
        elif anim in ('sleeping', 'laying_down', 'laying_back', 'laying_side'):
            leg_swing = 0
            arm_swing = 0
            body_bob = math.sin(phase) * 1
        elif anim == 'rage':
            leg_swing = math.sin(phase * 3) * 8
            arm_swing = math.sin(phase * 3) * 10
            body_bob = math.sin(phase * 4) * 4
        elif anim == 'petting':
            leg_swing = 0
            arm_swing = math.sin(phase * 1.5) * 4
            body_bob = math.sin(phase) * 3 + math.sin(phase * 0.5) * 1.5
        elif anim == 'playing':
            # Active bouncing and arm swinging for playing with toys
            leg_swing = math.sin(phase) * 10
            arm_swing = math.sin(phase * 2) * 14
            body_bob = abs(math.sin(phase * 2)) * 4
        elif anim == 'eating':
            # Gentle bob, arms brought together toward mouth, alternating
            leg_swing = 0
            arm_swing = -abs(math.sin(phase * 2)) * 12  # Arms forward, faster
            body_bob = math.sin(phase) * 3
        elif anim == 'customizing':
            # Preening, gentle sway with arms up
            leg_swing = 0
            arm_swing = math.sin(phase) * 6
            body_bob = math.sin(phase) * 3
        elif anim == 'spinning':
            leg_swing = math.sin(phase * 3) * 12
            arm_swing = math.sin(phase * 3 + math.pi/2) * 14
            body_bob = math.sin(phase * 2) * 5
        elif anim == 'shaking':
            leg_swing = math.sin(phase * 5) * 6
            arm_swing = math.sin(phase * 5) * 8
            body_bob = math.sin(phase * 6) * 3
        elif anim == 'rolling':
            leg_swing = math.sin(phase * 2) * 15
            arm_swing = math.cos(phase * 2) * 15
            body_bob = math.sin(phase) * 8
        elif anim == 'clicked':
            leg_swing = math.sin(phase * 2) * 5
            arm_swing = math.sin(phase * 2 + math.pi) * 8
            body_bob = -abs(math.sin(phase * 3)) * 6  # bounce effect
        else:
            # Default walking for fed, etc.
            leg_swing = math.sin(phase) * 8
            arm_swing = math.sin(phase + math.pi) * 6
            body_bob = abs(math.sin(phase)) * 2
        
        # --- Subtle breathing (body scale oscillation) ---
        breath_scale = 1.0
        if anim in ('idle', 'working', 'sarcastic', 'thinking'):
            breath_scale = 1.0 + math.sin(phase * 0.5) * 0.015
        elif anim in ('sleeping', 'laying_down', 'laying_back', 'laying_side'):
            breath_scale = 1.0 + math.sin(phase * 0.3) * 0.025
        
        by = body_bob  # vertical body offset
        
        # --- Determine eye style based on animation ---
        eye_style = 'normal'
        if anim == 'sleeping' or anim in ('laying_down', 'laying_back', 'laying_side'):
            eye_style = 'closed'
        elif anim == 'celebrating':
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
            # Surprised then transitions to happy
            cycle = frame_idx % 8
            if cycle < 3:
                eye_style = 'surprised'
            elif cycle < 5:
                eye_style = 'wink'
            else:
                eye_style = 'happy'
        elif anim in ('playing', 'eating', 'customizing'):
            eye_style = 'happy'
        elif anim == 'spinning':
            eye_style = 'spinning'
        elif anim == 'shaking':
            eye_style = 'dizzy'
        elif anim == 'rolling':
            eye_style = 'rolling'
        
        # --- Determine mouth style ---
        mouth_style = 'normal'
        if anim == 'celebrating' or anim == 'dancing':
            mouth_style = 'smile'
        elif anim == 'rage':
            mouth_style = 'angry'
        elif anim == 'sleeping' or anim in ('laying_down', 'laying_back', 'laying_side'):
            mouth_style = 'sleep'
        elif anim == 'petting' or anim == 'fed':
            mouth_style = 'smile'
        elif anim in ('playing', 'customizing'):
            mouth_style = 'smile'
        elif anim == 'eating':
            mouth_style = 'eating'
        elif anim == 'drunk':
            mouth_style = 'wavy'
        
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
        elif anim in ('sleeping', 'laying_down', 'laying_back', 'laying_side'):
            # Occasional ear twitch while sleeping
            if frame_idx % 20 < 3:
                ear_wiggle = math.sin(phase * 6) * 2 * sx
        
        # --- Draw legs (behind body) ---
        leg_top = int(145 * sy + by)
        leg_len = int(30 * sy)
        # Left leg
        left_leg_x = cx - int(25 * sx)
        left_leg_swing = leg_swing
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
        right_leg_x = cx + int(25 * sx)
        right_leg_swing = -leg_swing
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
        c.create_oval(
            cx - body_rx, body_top, cx + body_rx, body_bot,
            fill=white, outline=black, width=2, tags="body"
        )
        # Inner belly patch (lighter)
        belly_rx = int(28 * sx * breath_scale)
        c.create_oval(
            cx - belly_rx, body_top + int(15 * sy), cx + belly_rx, body_bot - int(10 * sy),
            fill="#FAFAFA", outline="", tags="belly"
        )
        
        # --- Draw arms (black, attached to body sides) ---
        arm_top = int(95 * sy + by)
        arm_len = int(35 * sy)
        # Left arm
        la_swing = arm_swing
        c.create_oval(
            cx - int(55 * sx), arm_top + la_swing,
            cx - int(30 * sx), arm_top + arm_len + la_swing,
            fill=black, outline=black, tags="arm"
        )
        # Right arm
        ra_swing = -arm_swing
        c.create_oval(
            cx + int(30 * sx), arm_top + ra_swing,
            cx + int(55 * sx), arm_top + arm_len + ra_swing,
            fill=black, outline=black, tags="arm"
        )
        
        # --- Draw head ---
        head_cy = int(52 * sy + by)
        head_rx = int(36 * sx)
        head_ry = int(32 * sy)
        c.create_oval(
            cx - head_rx, head_cy - head_ry,
            cx + head_rx, head_cy + head_ry,
            fill=white, outline=black, width=2, tags="head"
        )
        
        # --- Draw ears (black circles on top of head) with wiggle ---
        ear_y = head_cy - head_ry + int(5 * sy)
        ear_w = int(22 * sx)
        ear_h = int(24 * sy)
        # Left ear
        c.create_oval(cx - head_rx - int(2 * sx) + ear_wiggle, ear_y - int(16 * sy),
                       cx - head_rx + ear_w + ear_wiggle, ear_y + int(8 * sy),
                       fill=black, outline=black, tags="ear")
        # Inner ear pink
        c.create_oval(cx - head_rx + int(4 * sx) + ear_wiggle, ear_y - int(10 * sy),
                       cx - head_rx + int(16 * sx) + ear_wiggle, ear_y + int(2 * sy),
                       fill=pink, outline="", tags="ear_inner")
        # Right ear
        c.create_oval(cx + head_rx - ear_w - ear_wiggle, ear_y - int(16 * sy),
                       cx + head_rx + int(2 * sx) - ear_wiggle, ear_y + int(8 * sy),
                       fill=black, outline=black, tags="ear")
        # Inner ear pink
        c.create_oval(cx + head_rx - int(16 * sx) - ear_wiggle, ear_y - int(10 * sy),
                       cx + head_rx - int(4 * sx) - ear_wiggle, ear_y + int(2 * sy),
                       fill=pink, outline="", tags="ear_inner")
        
        # --- Draw eye patches (black ovals around eyes) ---
        eye_y = head_cy - int(4 * sy)
        patch_rx = int(14 * sx)
        patch_ry = int(11 * sy)
        eye_offset = int(24 * sx)
        # Left eye patch
        c.create_oval(cx - eye_offset - patch_rx, eye_y - patch_ry,
                       cx - eye_offset + patch_rx, eye_y + patch_ry,
                       fill=black, outline="", tags="eye_patch")
        # Right eye patch
        c.create_oval(cx + eye_offset - patch_rx, eye_y - patch_ry,
                       cx + eye_offset + patch_rx, eye_y + patch_ry,
                       fill=black, outline="", tags="eye_patch")
        
        # --- Draw equipped items on panda body (before face details) ---
        self._draw_equipped_items(c, cx, by, sx, sy)
        
        # --- Draw eyes ---
        self._draw_eyes(c, cx, eye_y, eye_style, sx, sy)
        
        # --- Draw nose ---
        nose_y = head_cy + int(8 * sy)
        c.create_oval(cx - int(5 * sx), nose_y - int(3 * sy), cx + int(5 * sx), nose_y + int(4 * sy),
                       fill=nose_color, outline="", tags="nose")
        
        # --- Draw mouth ---
        self._draw_mouth(c, cx, nose_y + int(6 * sy), mouth_style, sx, sy)
        
        # --- Draw animation-specific extras ---
        self._draw_animation_extras(c, cx, by, anim, frame_idx, sx, sy)
    
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
    }

    @staticmethod
    def _color_for_emoji(emoji: str, fallback: str = '#888888') -> str:
        """Return a color corresponding to the given emoji icon."""
        return PandaWidget._EMOJI_COLORS.get(emoji, fallback)

    def _draw_equipped_items(self, c: tk.Canvas, cx: int, by: float, sx: float, sy: float):
        """Draw equipped closet items as actual shapes on the panda body."""
        if not self.panda_closet:
            return
        try:
            appearance = self.panda_closet.get_current_appearance()

            # Draw hat as colored shape on top of head
            if appearance.hat:
                hat_item = self.panda_closet.get_item(appearance.hat)
                if hat_item:
                    color = self._color_for_emoji(hat_item.emoji, '#1a1a1a')
                    hat_y = int(18 * sy + by)
                    # Hat brim
                    c.create_rectangle(
                        cx - int(30 * sx), hat_y,
                        cx + int(30 * sx), hat_y + int(6 * sy),
                        fill=color, outline='#111111', width=1, tags="equipped_hat")
                    # Hat crown
                    c.create_rectangle(
                        cx - int(18 * sx), hat_y - int(18 * sy),
                        cx + int(18 * sx), hat_y,
                        fill=color, outline='#111111', width=1, tags="equipped_hat")

            # Draw clothing as shirt polygon on body
            if appearance.clothing:
                clothing_item = self.panda_closet.get_item(appearance.clothing)
                if clothing_item:
                    color = self._color_for_emoji(clothing_item.emoji, '#4169E1')
                    bt = int(85 * sy + by)
                    bb = int(150 * sy + by)
                    c.create_polygon(
                        cx - int(38 * sx), bt,
                        cx - int(42 * sx), bt + int(15 * sy),
                        cx - int(35 * sx), bb,
                        cx + int(35 * sx), bb,
                        cx + int(42 * sx), bt + int(15 * sy),
                        cx + int(38 * sx), bt,
                        fill=color, outline='#333333', width=1, tags="equipped_clothing")

            # Draw accessories as shapes near neck
            if appearance.accessories:
                for i, acc_id in enumerate(appearance.accessories[:2]):
                    acc_item = self.panda_closet.get_item(acc_id)
                    if acc_item:
                        color = self._color_for_emoji(acc_item.emoji, '#FF69B4')
                        neck_y = int(78 * sy + by)
                        # Bow-tie / scarf shape
                        ox = int((-12 + i * 24) * sx)
                        c.create_polygon(
                            cx + ox, neck_y - int(5 * sy),
                            cx + ox - int(8 * sx), neck_y,
                            cx + ox, neck_y + int(5 * sy),
                            cx + ox + int(8 * sx), neck_y,
                            fill=color, outline='#333333', width=1, tags="equipped_acc")

            # Draw shoes as colored ovals at feet
            if appearance.shoes:
                shoes_item = self.panda_closet.get_item(appearance.shoes)
                if shoes_item:
                    color = self._color_for_emoji(shoes_item.emoji, '#8B4513')
                    shoe_y = int(172 * sy + by)
                    for shoe_cx in [cx - int(25 * sx), cx + int(25 * sx)]:
                        c.create_oval(
                            shoe_cx - int(14 * sx), shoe_y,
                            shoe_cx + int(14 * sx), shoe_y + int(10 * sy),
                            fill=color, outline='#333333', width=1, tags="equipped_shoes")
        except Exception as e:
            logger.debug(f"Error drawing equipped items: {e}")
    
    def _draw_animation_extras(self, c: tk.Canvas, cx: int, by: float,
                                anim: str, frame_idx: int, sx: float = 1.0, sy: float = 1.0):
        """Draw extra decorations based on animation type."""
        emoji_list = self.ANIMATION_EMOJIS.get(anim)
        if emoji_list:
            emoji = emoji_list[frame_idx % len(emoji_list)]
            c.create_text(cx + int(55 * sx), int(18 * sy + by), text=emoji,
                          font=("Arial", int(20 * sx)), tags="extra")
        
        # Blush cheeks when petting, celebrating, playing, eating, etc.
        if anim in ('petting', 'celebrating', 'fed', 'playing', 'eating', 'customizing'):
            cheek_y = int(56 * sy + by)
            br = int(5 * sx)
            c.create_oval(cx - int(38 * sx), cheek_y - br, cx - int(28 * sx), cheek_y + br,
                          fill="#FFB6C1", outline="", tags="blush")
            c.create_oval(cx + int(28 * sx), cheek_y - br, cx + int(38 * sx), cheek_y + br,
                          fill="#FFB6C1", outline="", tags="blush")
    
    def _on_drag_start(self, event):
        """Handle start of drag operation."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True
        self._drag_moved = False
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
        self._prev_drag_x = event.x_root
        self._prev_drag_y = event.y_root
        self._prev_drag_time = now
        
        # Detect drag patterns
        self._detect_drag_patterns()
        
        # Check if we've moved enough to count as a real drag
        distance = ((event.x - self.drag_start_x) ** 2 + (event.y - self.drag_start_y) ** 2) ** 0.5
        if distance < self.CLICK_THRESHOLD:
            return
        
        if not self._drag_moved:
            # First real movement — switch to dragging animation
            self._drag_moved = True
            self._set_animation_no_cancel('dragging')
            if self.panda:
                response = self.panda.on_drag() if hasattr(self.panda, 'on_drag') else "🐼 Wheee!"
                self.info_label.configure(text=response)
        
        # Get the parent container (panda_container)
        parent = self.master
        if parent and hasattr(parent, 'place'):
            root = self.winfo_toplevel()
            root_w = max(1, root.winfo_width())
            root_h = max(1, root.winfo_height())
            parent_w = max(1, parent.winfo_width())
            parent_h = max(1, parent.winfo_height())
            
            # Calculate new absolute position
            x = parent.winfo_x() + (event.x - self.drag_start_x)
            y = parent.winfo_y() + (event.y - self.drag_start_y)
            
            # Constrain to window bounds
            max_x = max(0, root_w - parent_w)
            max_y = max(0, root_h - parent_h)
            
            hit_wall = False
            if x <= 0 or x >= max_x:
                hit_wall = True
            if y <= 0 or y >= max_y:
                hit_wall = True
            
            x = max(0, min(x, max_x))
            y = max(0, min(y, max_y))
            
            # Convert back to relative coordinates for consistent positioning
            rel_x = (x + parent_w) / max(1, root_w)
            rel_y = (y + parent_h) / max(1, root_h)
            # Clamp relative coords
            rel_x = max(0.0, min(1.0, rel_x))
            rel_y = max(0.0, min(1.0, rel_y))
            
            # Always use relx/rely with anchor="se" to stay consistent
            parent.place(relx=rel_x, rely=rel_y, anchor="se")
            
            if hit_wall and now - self._last_wall_hit_time > self.WALL_HIT_COOLDOWN_SECONDS:
                self._last_wall_hit_time = now
                self._set_animation_no_cancel('wall_hit')
                if self.panda:
                    response = self.panda.on_wall_hit() if hasattr(self.panda, 'on_wall_hit') else "🐼 Ouch!"
                    self.info_label.configure(text=response)
    
    def _detect_drag_patterns(self):
        """Detect circular or shaking drag patterns."""
        if len(self._drag_positions) < 8:
            return
        
        positions = self._drag_positions
        
        # Detect fast side-to-side shaking (rapid X direction changes)
        x_direction_changes = 0
        for i in range(2, len(positions)):
            dx_prev = positions[i-1][0] - positions[i-2][0]
            dx_curr = positions[i][0] - positions[i-1][0]
            if dx_prev * dx_curr < 0 and abs(dx_curr) > self.MIN_SHAKE_MOVEMENT:
                x_direction_changes += 1
        
        if x_direction_changes >= self.SHAKE_DIRECTION_CHANGES:
            self._set_animation_no_cancel('shaking')
            if self.panda:
                response = self.panda.on_shake() if hasattr(self.panda, 'on_shake') else "🐼 S-s-stop shaking me!"
                self.info_label.configure(text=response)
            self._drag_positions = []
            return
        
        # Detect circular dragging (consistent angle rotation)
        if len(positions) >= 12:
            angles = []
            cx = sum(p[0] for p in positions) / len(positions)
            cy = sum(p[1] for p in positions) / len(positions)
            for p in positions:
                angle = math.atan2(p[1] - cy, p[0] - cx)
                angles.append(angle)
            
            # Check for consistent rotation direction
            positive_diffs = 0
            negative_diffs = 0
            for i in range(1, len(angles)):
                diff = angles[i] - angles[i-1]
                # Normalize to [-pi, pi]
                while diff > math.pi:
                    diff -= 2 * math.pi
                while diff < -math.pi:
                    diff += 2 * math.pi
                if diff > self.MIN_ROTATION_ANGLE:
                    positive_diffs += 1
                elif diff < -self.MIN_ROTATION_ANGLE:
                    negative_diffs += 1
            
            total = positive_diffs + negative_diffs
            if total > 0 and (positive_diffs / total > self.SPIN_CONSISTENCY_THRESHOLD or negative_diffs / total > self.SPIN_CONSISTENCY_THRESHOLD):
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
            if self.panda:
                response = self.panda.on_toss() if hasattr(self.panda, 'on_toss') else "🐼 Home sweet home!"
                self.info_label.configure(text=response)
                # Award XP for moving the panda
                if self.panda_level_system:
                    try:
                        xp = self.panda_level_system.get_xp_reward('click') // 2
                    except (KeyError, AttributeError, TypeError):
                        xp = 5
                    self.panda_level_system.add_xp(xp, 'Moved panda')
            
            # Start toss physics if there's enough velocity
            speed = (self._toss_velocity_x ** 2 + self._toss_velocity_y ** 2) ** 0.5
            if speed > self.TOSS_MIN_VELOCITY:
                self._start_toss_physics()
            else:
                # Just save position and return to idle
                self._save_panda_position()
                self.play_animation_once('tossed')
    
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
        
        parent = self.master
        if not parent or not hasattr(parent, 'place'):
            self._stop_toss_physics()
            return
        
        try:
            root = self.winfo_toplevel()
            root_w = max(1, root.winfo_width())
            root_h = max(1, root.winfo_height())
            parent_w = max(1, parent.winfo_width())
            parent_h = max(1, parent.winfo_height())
            
            # Current position
            x = float(parent.winfo_x())
            y = float(parent.winfo_y())
            
            # Apply gravity
            self._toss_velocity_y += self.TOSS_GRAVITY
            
            # Apply friction
            self._toss_velocity_x *= self.TOSS_FRICTION
            self._toss_velocity_y *= self.TOSS_FRICTION
            
            # Move
            x += self._toss_velocity_x
            y += self._toss_velocity_y
            
            # Bounce off walls
            max_x = max(0, root_w - parent_w)
            max_y = max(0, root_h - parent_h)
            
            bounced = False
            if x <= 0:
                x = 0
                self._toss_velocity_x = abs(self._toss_velocity_x) * self.TOSS_BOUNCE_DAMPING
                bounced = True
            elif x >= max_x:
                x = max_x
                self._toss_velocity_x = -abs(self._toss_velocity_x) * self.TOSS_BOUNCE_DAMPING
                bounced = True
            
            if y <= 0:
                y = 0
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
            rel_x = (x + parent_w) / max(1, root_w)
            rel_y = (y + parent_h) / max(1, root_h)
            rel_x = max(0.0, min(1.0, rel_x))
            rel_y = max(0.0, min(1.0, rel_y))
            parent.place(relx=rel_x, rely=rel_y, anchor="se")
            
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
        """Save the current panda position to config."""
        parent = self.master
        if parent:
            try:
                root = self.winfo_toplevel()
                root_w = max(1, root.winfo_width())
                root_h = max(1, root.winfo_height())
                parent_w = max(1, parent.winfo_width())
                parent_h = max(1, parent.winfo_height())
                
                rel_x = (parent.winfo_x() + parent_w) / root_w
                rel_y = (parent.winfo_y() + parent_h) / root_h
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
                    rel_y = event.y / label_height
                    body_part = self.panda.get_body_part_at_position(rel_y)
                
                if body_part and hasattr(self.panda, 'on_body_part_click'):
                    response = self.panda.on_body_part_click(body_part)
                else:
                    response = self.panda.on_click()
                
                self.info_label.configure(text=response)
                # Play clicked animation if available, else celebrating
                self.play_animation_once('clicked')
                
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
                rel_y = event.y / label_height if event else 0.5
                
                if hasattr(self.panda, 'on_rub'):
                    body_part = self.panda.get_body_part_at_position(rel_y)
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
        parent = self.master
        if parent and hasattr(parent, 'place'):
            parent.place(relx=0.98, rely=0.98, anchor="se")
            
            # Save to config
            try:
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
        """Give a toy or food widget to the panda."""
        try:
            result = widget.use()
            message = result.get('message', f"Panda enjoys the {widget.name}!")
            animation = result.get('animation', 'playing')
            self.info_label.configure(text=message)
            self.play_animation_once(animation)

            # Award XP for interaction
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
    
    def start_animation(self, animation_name: str):
        """Start looping animation."""
        if self._destroyed:
            return
        # Check if animations are disabled for low-end systems
        try:
            from src.config import config
            if config.get('ui', 'disable_panda_animations', default=False):
                # Just show static frame, no animation loop
                self.current_animation = animation_name
                self._draw_panda(0)
                return
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
                for acc_id in appearance.accessories[:2]:
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
            
            # Draw equipped items text on canvas (supplementary to body drawing)
            equipped = self._get_equipped_items_text()
            if equipped:
                self.panda_canvas.create_text(
                    PANDA_CANVAS_W // 2, PANDA_CANVAS_H - 8,
                    text=equipped, font=("Arial", 12),
                    fill="gray", tags="equipped"
                )
            
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
        """Animate once then return to idle."""
        if self._destroyed:
            return
        try:
            self._draw_panda(self.animation_frame)
            self.animation_frame += 1
            
            # Return to idle after 1 second
            self.animation_timer = self.after(1000, lambda: self.start_animation('idle'))
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
        """Clean up widget."""
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
        super().destroy()

