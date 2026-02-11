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
PANDA_CANVAS_W = 160
PANDA_CANVAS_H = 200

# Speech bubble layout constants
BUBBLE_MAX_CHARS_PER_LINE = 25
BUBBLE_PAD_X = 12
BUBBLE_PAD_Y = 8
BUBBLE_CHAR_WIDTH = 7   # approximate px per character at font size 10
BUBBLE_LINE_HEIGHT = 16  # px per line of text
BUBBLE_MAX_WIDTH = 200
BUBBLE_CORNER_RADIUS = 10
BUBBLE_TAIL_HEIGHT = 8


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
    
    # Animation timing (ms)
    ANIMATION_INTERVAL = 150
    # Reset frame counter at this value to prevent unbounded growth
    MAX_ANIMATION_FRAME = 10000
    
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
        self._last_drag_time = 0  # Throttle drag events (ms)
        
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

    def _refresh_canvas_bg(self):
        """Re-detect the parent background and update both canvases."""
        if self._destroyed:
            return
        self._canvas_bg = self._get_parent_bg()
        try:
            self.panda_canvas.configure(bg=self._canvas_bg)
        except Exception:
            pass
        try:
            self._bubble_canvas.configure(bg=self._canvas_bg)
        except Exception:
            pass

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
        font = ("Arial", 10)
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

        # Place bubble above panda canvas (pack before canvas)
        bc.pack_forget()
        self.panda_canvas.pack_forget()
        bc.pack(pady=(0, 0))
        self.panda_canvas.pack(pady=4, padx=4)

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
        # Cycle through 8 frames for smooth walking
        phase = (frame_idx % 8) / 8.0 * 2 * math.pi
        
        if anim in ('idle', 'working', 'sarcastic', 'thinking'):
            # Gentle body bob for idle
            leg_swing = 0
            arm_swing = 0
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
            arm_swing = 0
            body_bob = math.sin(phase) * 2
        elif anim == 'playing':
            # Active bouncing and arm swinging for playing with toys
            leg_swing = math.sin(phase) * 10
            arm_swing = math.sin(phase * 2) * 14
            body_bob = abs(math.sin(phase * 2)) * 4
        elif anim == 'eating':
            # Gentle bob, arms brought together toward mouth
            leg_swing = 0
            arm_swing = -abs(math.sin(phase)) * 8  # Arms forward
            body_bob = math.sin(phase) * 2
        elif anim == 'customizing':
            # Preening, gentle sway with arms up
            leg_swing = 0
            arm_swing = math.sin(phase) * 6
            body_bob = math.sin(phase) * 3
        else:
            # Default walking for clicked, fed, etc.
            leg_swing = math.sin(phase) * 8
            arm_swing = math.sin(phase + math.pi) * 6
            body_bob = abs(math.sin(phase)) * 2
        
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
            eye_style = 'happy'
        elif anim in ('playing', 'eating', 'customizing'):
            eye_style = 'happy'
        
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
        
        # --- Draw legs (behind body) ---
        leg_top = 145 + by
        leg_len = 30
        # Left leg
        left_leg_x = cx - 25
        left_leg_swing = leg_swing
        c.create_oval(
            left_leg_x - 12, leg_top + left_leg_swing,
            left_leg_x + 12, leg_top + leg_len + left_leg_swing,
            fill=black, outline=black, tags="leg"
        )
        # Left foot (white pad)
        c.create_oval(
            left_leg_x - 10, leg_top + leg_len - 8 + left_leg_swing,
            left_leg_x + 10, leg_top + leg_len + 4 + left_leg_swing,
            fill=white, outline=black, width=1, tags="foot"
        )
        # Right leg
        right_leg_x = cx + 25
        right_leg_swing = -leg_swing
        c.create_oval(
            right_leg_x - 12, leg_top + right_leg_swing,
            right_leg_x + 12, leg_top + leg_len + right_leg_swing,
            fill=black, outline=black, tags="leg"
        )
        # Right foot (white pad)
        c.create_oval(
            right_leg_x - 10, leg_top + leg_len - 8 + right_leg_swing,
            right_leg_x + 10, leg_top + leg_len + 4 + right_leg_swing,
            fill=white, outline=black, width=1, tags="foot"
        )
        
        # --- Draw body (white belly, rounded) ---
        body_top = 75 + by
        body_bot = 160 + by
        c.create_oval(
            cx - 42, body_top, cx + 42, body_bot,
            fill=white, outline=black, width=2, tags="body"
        )
        # Inner belly patch (lighter)
        c.create_oval(
            cx - 28, body_top + 15, cx + 28, body_bot - 10,
            fill="#FAFAFA", outline="", tags="belly"
        )
        
        # --- Draw arms (black, attached to body sides) ---
        arm_top = 95 + by
        arm_len = 35
        # Left arm
        la_swing = arm_swing
        c.create_oval(
            cx - 55, arm_top + la_swing,
            cx - 30, arm_top + arm_len + la_swing,
            fill=black, outline=black, tags="arm"
        )
        # Right arm
        ra_swing = -arm_swing
        c.create_oval(
            cx + 30, arm_top + ra_swing,
            cx + 55, arm_top + arm_len + ra_swing,
            fill=black, outline=black, tags="arm"
        )
        
        # --- Draw head ---
        head_cy = 52 + by
        head_rx = 36
        head_ry = 32
        c.create_oval(
            cx - head_rx, head_cy - head_ry,
            cx + head_rx, head_cy + head_ry,
            fill=white, outline=black, width=2, tags="head"
        )
        
        # --- Draw ears (black circles on top of head) ---
        ear_y = head_cy - head_ry + 5
        # Left ear
        c.create_oval(cx - head_rx - 2, ear_y - 16,
                       cx - head_rx + 22, ear_y + 8,
                       fill=black, outline=black, tags="ear")
        # Inner ear pink
        c.create_oval(cx - head_rx + 4, ear_y - 10,
                       cx - head_rx + 16, ear_y + 2,
                       fill=pink, outline="", tags="ear_inner")
        # Right ear
        c.create_oval(cx + head_rx - 22, ear_y - 16,
                       cx + head_rx + 2, ear_y + 8,
                       fill=black, outline=black, tags="ear")
        # Inner ear pink
        c.create_oval(cx + head_rx - 16, ear_y - 10,
                       cx + head_rx - 4, ear_y + 2,
                       fill=pink, outline="", tags="ear_inner")
        
        # --- Draw eye patches (black ovals around eyes) ---
        eye_y = head_cy - 4
        patch_rx = 14
        patch_ry = 11
        # Left eye patch
        c.create_oval(cx - 24 - patch_rx, eye_y - patch_ry,
                       cx - 24 + patch_rx, eye_y + patch_ry,
                       fill=black, outline="", tags="eye_patch")
        # Right eye patch
        c.create_oval(cx + 24 - patch_rx, eye_y - patch_ry,
                       cx + 24 + patch_rx, eye_y + patch_ry,
                       fill=black, outline="", tags="eye_patch")
        
        # --- Draw eyes ---
        self._draw_eyes(c, cx, eye_y, eye_style)
        
        # --- Draw nose ---
        nose_y = head_cy + 8
        c.create_oval(cx - 5, nose_y - 3, cx + 5, nose_y + 4,
                       fill=nose_color, outline="", tags="nose")
        
        # --- Draw mouth ---
        self._draw_mouth(c, cx, nose_y + 6, mouth_style)
        
        # --- Draw animation-specific extras ---
        self._draw_animation_extras(c, cx, by, anim, frame_idx)
    
    def _draw_eyes(self, c: tk.Canvas, cx: int, ey: int, style: str):
        """Draw panda eyes based on the current animation style."""
        left_ex = cx - 24
        right_ex = cx + 24
        
        if style == 'closed':
            # Sleeping - curved lines
            c.create_line(left_ex - 6, ey, left_ex + 6, ey,
                          fill="white", width=2, tags="eye")
            c.create_line(right_ex - 6, ey, right_ex + 6, ey,
                          fill="white", width=2, tags="eye")
        elif style == 'happy':
            # Happy - upward arcs (^  ^)
            c.create_arc(left_ex - 6, ey - 6, left_ex + 6, ey + 4,
                         start=0, extent=180, style="arc",
                         outline="white", width=2, tags="eye")
            c.create_arc(right_ex - 6, ey - 6, right_ex + 6, ey + 4,
                         start=0, extent=180, style="arc",
                         outline="white", width=2, tags="eye")
        elif style == 'angry':
            # Angry - small dots with angled brows
            c.create_oval(left_ex - 3, ey - 3, left_ex + 3, ey + 3,
                          fill="red", outline="", tags="eye")
            c.create_oval(right_ex - 3, ey - 3, right_ex + 3, ey + 3,
                          fill="red", outline="", tags="eye")
            # Angry brows
            c.create_line(left_ex - 7, ey - 10, left_ex + 5, ey - 6,
                          fill="white", width=2, tags="brow")
            c.create_line(right_ex + 7, ey - 10, right_ex - 5, ey - 6,
                          fill="white", width=2, tags="brow")
        elif style == 'half':
            # Sarcastic half-lidded
            c.create_oval(left_ex - 4, ey - 1, left_ex + 4, ey + 4,
                          fill="white", outline="", tags="eye")
            c.create_oval(left_ex - 2, ey + 0, left_ex + 2, ey + 3,
                          fill="#222222", outline="", tags="pupil")
            c.create_oval(right_ex - 4, ey - 1, right_ex + 4, ey + 4,
                          fill="white", outline="", tags="eye")
            c.create_oval(right_ex - 2, ey + 0, right_ex + 2, ey + 3,
                          fill="#222222", outline="", tags="pupil")
        elif style == 'dizzy':
            # Drunk - spiral/x eyes
            c.create_line(left_ex - 4, ey - 4, left_ex + 4, ey + 4,
                          fill="white", width=2, tags="eye")
            c.create_line(left_ex - 4, ey + 4, left_ex + 4, ey - 4,
                          fill="white", width=2, tags="eye")
            c.create_line(right_ex - 4, ey - 4, right_ex + 4, ey + 4,
                          fill="white", width=2, tags="eye")
            c.create_line(right_ex - 4, ey + 4, right_ex + 4, ey - 4,
                          fill="white", width=2, tags="eye")
        else:
            # Normal round eyes with pupils and shine
            # Left eye white
            c.create_oval(left_ex - 6, ey - 6, left_ex + 6, ey + 6,
                          fill="white", outline="", tags="eye")
            # Left pupil
            c.create_oval(left_ex - 3, ey - 3, left_ex + 3, ey + 3,
                          fill="#222222", outline="", tags="pupil")
            # Left shine
            c.create_oval(left_ex - 5, ey - 5, left_ex - 2, ey - 2,
                          fill="white", outline="", tags="shine")
            # Right eye white
            c.create_oval(right_ex - 6, ey - 6, right_ex + 6, ey + 6,
                          fill="white", outline="", tags="eye")
            # Right pupil
            c.create_oval(right_ex - 3, ey - 3, right_ex + 3, ey + 3,
                          fill="#222222", outline="", tags="pupil")
            # Right shine
            c.create_oval(right_ex - 5, ey - 5, right_ex - 2, ey - 2,
                          fill="white", outline="", tags="shine")
    
    def _draw_mouth(self, c: tk.Canvas, cx: int, my: int, style: str):
        """Draw panda mouth based on the current animation style."""
        if style == 'smile':
            c.create_arc(cx - 8, my - 6, cx + 8, my + 6,
                         start=200, extent=140, style="arc",
                         outline="#333333", width=2, tags="mouth")
        elif style == 'angry':
            # Frown
            c.create_arc(cx - 8, my, cx + 8, my + 10,
                         start=20, extent=140, style="arc",
                         outline="#333333", width=2, tags="mouth")
        elif style == 'sleep':
            # Small 'z' drawn as text
            c.create_text(cx + 30, my - 20, text="z",
                          font=("Arial", 8), fill="gray", tags="zzz")
            c.create_text(cx + 38, my - 30, text="Z",
                          font=("Arial", 10), fill="gray", tags="zzz")
            c.create_text(cx + 46, my - 42, text="Z",
                          font=("Arial", 13), fill="gray", tags="zzz")
            # Small line mouth
            c.create_line(cx - 4, my + 2, cx + 4, my + 2,
                          fill="#333333", width=1, tags="mouth")
        elif style == 'wavy':
            # Wavy drunk mouth
            points = []
            for i in range(9):
                px = cx - 8 + i * 2
                py = my + math.sin(i * 1.2) * 3
                points.extend([px, py])
            if len(points) >= 4:
                c.create_line(*points, fill="#333333", width=2,
                              smooth=True, tags="mouth")
        elif style == 'eating':
            # Open mouth / chewing animation
            c.create_oval(cx - 5, my - 2, cx + 5, my + 5,
                          fill="#333333", outline="#333333", tags="mouth")
        else:
            # Neutral small curve
            c.create_arc(cx - 5, my - 3, cx + 5, my + 4,
                         start=210, extent=120, style="arc",
                         outline="#333333", width=1.5, tags="mouth")
    
    def _draw_animation_extras(self, c: tk.Canvas, cx: int, by: float,
                                anim: str, frame_idx: int):
        """Draw extra decorations based on animation type."""
        emoji_list = self.ANIMATION_EMOJIS.get(anim)
        if emoji_list:
            emoji = emoji_list[frame_idx % len(emoji_list)]
            c.create_text(cx + 45, 18 + by, text=emoji,
                          font=("Arial", 16), tags="extra")
        
        # Blush cheeks when petting, celebrating, playing, eating, etc.
        if anim in ('petting', 'celebrating', 'fed', 'playing', 'eating', 'customizing'):
            cheek_y = 56 + by
            c.create_oval(cx - 38, cheek_y - 4, cx - 28, cheek_y + 4,
                          fill="#FFB6C1", outline="", tags="blush")
            c.create_oval(cx + 28, cheek_y - 4, cx + 38, cheek_y + 4,
                          fill="#FFB6C1", outline="", tags="blush")
    
    def _on_drag_start(self, event):
        """Handle start of drag operation."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True
        self._drag_moved = False
    
    def _on_drag_motion(self, event):
        """Handle drag motion - move the panda container with throttling."""
        if not self.is_dragging:
            return
        
        # Throttle drag events to ~60fps (16ms) to prevent frame spikes
        now = time.monotonic()
        if now - self._last_drag_time < 0.016:
            return
        self._last_drag_time = now
        
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
            
            if hit_wall:
                self._set_animation_no_cancel('wall_hit')
                if self.panda:
                    response = self.panda.on_wall_hit() if hasattr(self.panda, 'on_wall_hit') else "🐼 Ouch!"
                    self.info_label.configure(text=response)
    
    def _on_drag_end(self, event):
        """Handle end of drag operation."""
        if not self.is_dragging:
            return
        
        self.is_dragging = False
        
        if not self._drag_moved:
            # It was just a click (minimal movement)
            self._on_click(event)
        else:
            # Save new position in config
            parent = self.master
            if parent:
                root = self.winfo_toplevel()
                root_w = max(1, root.winfo_width())
                root_h = max(1, root.winfo_height())
                parent_w = max(1, parent.winfo_width())
                parent_h = max(1, parent.winfo_height())
                
                # Calculate relative position consistently with anchor="se"
                rel_x = (parent.winfo_x() + parent_w) / root_w
                rel_y = (parent.winfo_y() + parent_h) / root_h
                rel_x = max(0.05, min(1.0, rel_x))
                rel_y = max(0.05, min(1.0, rel_y))
                
                try:
                    from src.config import config
                    config.set('panda', 'position_x', value=rel_x)
                    config.set('panda', 'position_y', value=rel_y)
                    config.save()
                    logger.info(f"Saved panda position: ({rel_x:.2f}, {rel_y:.2f})")
                except Exception as e:
                    logger.warning(f"Failed to save panda position: {e}")
            
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
            
            # Play tossed animation briefly then return to idle
            self.play_animation_once('tossed')
    
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
                # Create context menu
                menu = tk.Menu(self, tearoff=0)
                for key, label in menu_items.items():
                    menu.add_command(
                        label=label,
                        command=lambda k=key: self._handle_menu_action(k)
                    )

                # Add toy/food sub-menus if widget collection available
                if self.widget_collection:
                    # Toys sub-menu
                    toys = self.widget_collection.get_toys(unlocked_only=True)
                    if toys:
                        menu.add_separator()
                        toy_menu = tk.Menu(menu, tearoff=0)
                        for toy in toys:
                            toy_menu.add_command(
                                label=f"{toy.emoji} {toy.name}",
                                command=lambda t=toy: self._give_widget_to_panda(t)
                            )
                        menu.add_cascade(label="🎾 Give Toy", menu=toy_menu)

                    # Food sub-menu
                    food = self.widget_collection.get_food(unlocked_only=True)
                    if food:
                        food_menu = tk.Menu(menu, tearoff=0)
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
            
            # Draw equipped items text on canvas
            equipped = self._get_equipped_items_text()
            if equipped:
                self.panda_canvas.create_text(
                    PANDA_CANVAS_W // 2, PANDA_CANVAS_H - 6,
                    text=equipped, font=("Arial", 9),
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
        self._cancel_animation_timer()
        if self._speech_timer:
            try:
                self.after_cancel(self._speech_timer)
            except Exception:
                pass
            self._speech_timer = None
        super().destroy()

