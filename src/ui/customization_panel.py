"""
UI Customization System
Comprehensive theming, color picker, and cursor customization
"""

import json
import math
import colorsys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import customtkinter as ctk
from tkinter import filedialog, messagebox

from src.config import config, THEMES_DIR

logger = logging.getLogger(__name__)


# Built-in theme presets
THEME_PRESETS = {
    "dark_panda": {
        "name": "🐼 Dark Panda (Default)",
        "appearance_mode": "dark",
        "colors": {
            "primary": "#1f538d",
            "secondary": "#14375e",
            "background": "#1a1a1a",
            "foreground": "#ffffff",
            "accent": "#2fa572",
            "button": "#1f538d",
            "button_hover": "#2d6ba8",
            "text": "#ffffff",
            "text_secondary": "#b0b0b0",
            "border": "#333333"
        }
    },
    "light_mode": {
        "name": "☀️ Light Mode",
        "appearance_mode": "light",
        "colors": {
            "primary": "#2874A6",
            "secondary": "#d6e9f5",
            "background": "#f0f0f0",
            "foreground": "#000000",
            "accent": "#3498DB",
            "button": "#2874A6",
            "button_hover": "#1F618D",
            "text": "#000000",
            "text_secondary": "#555555",
            "border": "#cccccc"
        }
    },
    "cyberpunk": {
        "name": "🤖 Cyberpunk",
        "appearance_mode": "dark",
        "colors": {
            "primary": "#00cc33",
            "secondary": "#0d1a0f",
            "background": "#0a0e27",
            "foreground": "#e0e0e0",
            "accent": "#ff006e",
            "button": "#005522",
            "button_hover": "#007733",
            "text": "#00ff41",
            "text_secondary": "#66cc88",
            "border": "#1a3a1a"
        }
    },
    "neon_dreams": {
        "name": "💜 Neon Dreams",
        "appearance_mode": "dark",
        "colors": {
            "primary": "#00d4ff",
            "secondary": "#152535",
            "background": "#0d1b2a",
            "foreground": "#ffffff",
            "accent": "#ff00ff",
            "button": "#005577",
            "button_hover": "#007799",
            "text": "#ffffff",
            "text_secondary": "#a0d2eb",
            "border": "#1a3550"
        }
    },
    "classic_windows": {
        "name": "🪟 Classic Windows",
        "appearance_mode": "light",
        "colors": {
            "primary": "#0078d7",
            "secondary": "#d4d4d4",
            "background": "#c0c0c0",
            "foreground": "#000000",
            "accent": "#0078d7",
            "button": "#0078d7",
            "button_hover": "#005a9e",
            "text": "#000000",
            "text_secondary": "#333333",
            "border": "#808080"
        }
    },
    "red_panda": {
        "name": "🔴 Red Panda",
        "appearance_mode": "dark",
        "colors": {
            "primary": "#cc0000",
            "secondary": "#2a0a0a",
            "background": "#1a0000",
            "foreground": "#e0e0e0",
            "accent": "#ff3333",
            "button": "#8b0000",
            "button_hover": "#aa0000",
            "text": "#f0c0c0",
            "text_secondary": "#cc8888",
            "border": "#4a1a1a"
        }
    }
}

# Common color presets
COLOR_PRESETS = [
    "#1f538d",  # Blue
    "#2fa572",  # Green
    "#e74c3c",  # Red
    "#f39c12",  # Orange
    "#9b59b6",  # Purple
    "#1abc9c"   # Teal
]


class ColorWheelWidget(ctk.CTkFrame):
    """Interactive RGB color picker with HSV support"""
    
    def __init__(self, master, initial_color="#1f538d", on_color_change=None):
        super().__init__(master)
        self.on_color_change = on_color_change
        self.recent_colors = []
        self.max_recent = 10
        
        self.current_color = initial_color
        self.rgb = self._hex_to_rgb(initial_color)
        
        self._create_widgets()
        self._update_all_from_rgb()
    
    def _create_widgets(self):
        """Create color picker widgets"""
        # Wrap everything in scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        title = ctk.CTkLabel(scroll_frame, text="🎨 Color Picker", font=("Arial Bold", 14))
        title.pack(pady=10)
        
        # Add explanatory label
        info_label = ctk.CTkLabel(
            scroll_frame, 
            text="This color sets the accent/highlight color for the UI theme",
            font=("Arial", 11),
            text_color="gray"
        )
        info_label.pack(pady=(0, 10))
        
        # Color target selector
        target_frame = ctk.CTkFrame(scroll_frame)
        target_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(target_frame, text="🎯 Apply color to:", font=("Arial Bold", 11)).pack(anchor="w", padx=5, pady=2)
        self.color_target_var = ctk.StringVar(value="accent")
        target_options = [
            "🎨 accent", "🔵 primary", "🟣 secondary", "🖼️ background",
            "🔘 button", "✨ button_hover", "📝 text", "💬 text_secondary", "📏 border"
        ]
        self._target_display_to_key = {v: v.split(" ", 1)[1] if " " in v else v for v in target_options}
        target_menu = ctk.CTkOptionMenu(target_frame, variable=self.color_target_var,
                                        values=target_options, width=200,
                                        command=self._on_target_change)
        target_menu.pack(padx=5, pady=5)
        
        # Label showing which element is being modified
        self._target_info = ctk.CTkLabel(
            target_frame,
            text="Currently editing: accent color (UI highlights & buttons)",
            font=("Arial", 10), text_color="gray"
        )
        self._target_info.pack(anchor="w", padx=5, pady=(0, 5))
        
        hex_frame = ctk.CTkFrame(scroll_frame)
        hex_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(hex_frame, text="Hex:").pack(side="left", padx=5)
        self.hex_var = ctk.StringVar(value=self.current_color)
        self.hex_entry = ctk.CTkEntry(hex_frame, textvariable=self.hex_var, width=100)
        self.hex_entry.pack(side="left", padx=5)
        self.hex_entry.bind("<Return>", lambda e: self._on_hex_change())
        
        ctk.CTkButton(hex_frame, text="Apply", width=60, 
                     command=self._on_hex_change).pack(side="left", padx=5)
        
        self.preview = ctk.CTkLabel(scroll_frame, text="", width=200, height=50, fg_color=self.current_color)
        self.preview.pack(pady=10, padx=10)
        
        # --- Color picker (replaced canvas color wheel) ---
        wheel_label = ctk.CTkLabel(scroll_frame, text="🎨 Color Preview:", font=("Arial Bold", 11))
        wheel_label.pack(anchor="w", padx=15, pady=(5, 2))
        
        # Color preview frame (replaces canvas color wheel)
        self._color_preview_frame = ctk.CTkFrame(scroll_frame, width=200, height=60, fg_color=self.current_color)
        self._color_preview_frame.pack(pady=5)
        self._color_preview_frame.pack_propagate(False)
        
        # Click to open system color picker
        preview_label = ctk.CTkLabel(self._color_preview_frame, text="Click to pick color", 
                                     text_color="white", font=("Arial", 10))
        preview_label.place(relx=0.5, rely=0.5, anchor="center")
        self._color_preview_frame.bind("<Button-1>", self._open_color_picker)
        preview_label.bind("<Button-1>", self._open_color_picker)
        
        # RGB sliders
        rgb_label = ctk.CTkLabel(scroll_frame, text="RGB Sliders:", font=("Arial Bold", 11))
        rgb_label.pack(anchor="w", padx=15, pady=(5, 2))
        
        sliders_frame = ctk.CTkFrame(scroll_frame)
        sliders_frame.pack(fill="x", padx=10, pady=5)
        
        r_frame = ctk.CTkFrame(sliders_frame)
        r_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(r_frame, text="R:", width=30).pack(side="left", padx=5)
        self.r_slider = ctk.CTkSlider(r_frame, from_=0, to=255, number_of_steps=255,
                                      command=lambda v: self._on_rgb_change())
        self.r_slider.set(self.rgb[0])
        self.r_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.r_label = ctk.CTkLabel(r_frame, text=str(int(self.rgb[0])), width=40)
        self.r_label.pack(side="left", padx=5)
        
        g_frame = ctk.CTkFrame(sliders_frame)
        g_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(g_frame, text="G:", width=30).pack(side="left", padx=5)
        self.g_slider = ctk.CTkSlider(g_frame, from_=0, to=255, number_of_steps=255,
                                      command=lambda v: self._on_rgb_change())
        self.g_slider.set(self.rgb[1])
        self.g_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.g_label = ctk.CTkLabel(g_frame, text=str(int(self.rgb[1])), width=40)
        self.g_label.pack(side="left", padx=5)
        
        b_frame = ctk.CTkFrame(sliders_frame)
        b_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(b_frame, text="B:", width=30).pack(side="left", padx=5)
        self.b_slider = ctk.CTkSlider(b_frame, from_=0, to=255, number_of_steps=255,
                                      command=lambda v: self._on_rgb_change())
        self.b_slider.set(self.rgb[2])
        self.b_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.b_label = ctk.CTkLabel(b_frame, text=str(int(self.rgb[2])), width=40)
        self.b_label.pack(side="left", padx=5)
        
        # HSV sliders
        hsv_label = ctk.CTkLabel(scroll_frame, text="HSV Sliders:", font=("Arial Bold", 11))
        hsv_label.pack(anchor="w", padx=15, pady=(10, 2))
        
        hsv_frame = ctk.CTkFrame(scroll_frame)
        hsv_frame.pack(fill="x", padx=10, pady=5)
        
        h_frame = ctk.CTkFrame(hsv_frame)
        h_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(h_frame, text="H:", width=30).pack(side="left", padx=5)
        self.h_slider = ctk.CTkSlider(h_frame, from_=0, to=360, number_of_steps=360,
                                      command=lambda v: self._on_hsv_change())
        self.h_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.h_label = ctk.CTkLabel(h_frame, text="0°", width=40)
        self.h_label.pack(side="left", padx=5)
        
        s_frame = ctk.CTkFrame(hsv_frame)
        s_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(s_frame, text="S:", width=30).pack(side="left", padx=5)
        self.s_slider = ctk.CTkSlider(s_frame, from_=0, to=100, number_of_steps=100,
                                      command=lambda v: self._on_hsv_change())
        self.s_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.s_label = ctk.CTkLabel(s_frame, text="0%", width=40)
        self.s_label.pack(side="left", padx=5)
        
        v_frame = ctk.CTkFrame(hsv_frame)
        v_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(v_frame, text="V:", width=30).pack(side="left", padx=5)
        self.v_slider = ctk.CTkSlider(v_frame, from_=0, to=100, number_of_steps=100,
                                      command=lambda v: self._on_hsv_change())
        self.v_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.v_label = ctk.CTkLabel(v_frame, text="0%", width=40)
        self.v_label.pack(side="left", padx=5)
        
        presets_frame = ctk.CTkFrame(scroll_frame)
        presets_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(presets_frame, text="Presets:", font=("Arial Bold", 11)).pack(anchor="w", padx=5)
        
        preset_buttons = ctk.CTkFrame(presets_frame)
        preset_buttons.pack(fill="x", padx=5, pady=5)
        
        for i, color in enumerate(COLOR_PRESETS):
            btn = ctk.CTkButton(preset_buttons, text="", width=40, height=30,
                               fg_color=color, hover_color=color,
                               command=lambda c=color: self.set_color(c))
            btn.grid(row=0, column=i, padx=2, pady=2)
        
        self.recent_frame = ctk.CTkFrame(scroll_frame)
        self.recent_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.recent_frame, text="Recent:", font=("Arial Bold", 11)).pack(anchor="w", padx=5)
        self.recent_container = ctk.CTkFrame(self.recent_frame)
        self.recent_container.pack(fill="x", padx=5, pady=5)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_rgb_change(self):
        r = int(self.r_slider.get())
        g = int(self.g_slider.get())
        b = int(self.b_slider.get())
        
        self.rgb = (r, g, b)
        self.current_color = self._rgb_to_hex(r, g, b)
        
        self.r_label.configure(text=str(r))
        self.g_label.configure(text=str(g))
        self.b_label.configure(text=str(b))
        self.hex_var.set(self.current_color)
        self.preview.configure(fg_color=self.current_color)
        
        self._add_to_recent(self.current_color)
        
        if self.on_color_change:
            self.on_color_change(self.current_color, self.get_color_target())
    
    def _on_hsv_change(self):
        """Handle HSV slider changes"""
        h = int(self.h_slider.get()) / 360.0
        s = int(self.s_slider.get()) / 100.0
        v = int(self.v_slider.get()) / 100.0
        
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        
        self.rgb = (r, g, b)
        self.current_color = self._rgb_to_hex(r, g, b)
        
        self.r_slider.set(r)
        self.g_slider.set(g)
        self.b_slider.set(b)
        self.r_label.configure(text=str(r))
        self.g_label.configure(text=str(g))
        self.b_label.configure(text=str(b))
        self.h_label.configure(text=f"{int(self.h_slider.get())}°")
        self.s_label.configure(text=f"{int(self.s_slider.get())}%")
        self.v_label.configure(text=f"{int(self.v_slider.get())}%")
        self.hex_var.set(self.current_color)
        self.preview.configure(fg_color=self.current_color)
        
        self._add_to_recent(self.current_color)
        
        if self.on_color_change:
            self.on_color_change(self.current_color, self.get_color_target())
    def _on_hex_change(self):
        hex_value = self.hex_var.get().strip()
        if not hex_value.startswith('#'):
            hex_value = '#' + hex_value
        
        try:
            rgb = self._hex_to_rgb(hex_value)
            self.set_color(hex_value)
        except ValueError:
            messagebox.showerror("Invalid Color", "Please enter a valid hex color (e.g., #1f538d)")
    
    def _update_all_from_rgb(self):
        r, g, b = self.rgb
        self.r_slider.set(r)
        self.g_slider.set(g)
        self.b_slider.set(b)
        self.r_label.configure(text=str(r))
        self.g_label.configure(text=str(g))
        self.b_label.configure(text=str(b))
        self.hex_var.set(self.current_color)
        self.preview.configure(fg_color=self.current_color)
        
        # Update color preview frame (replaces color wheel)
        if hasattr(self, '_color_preview_frame'):
            self._color_preview_frame.configure(fg_color=self.current_color)
        
        # Sync HSV sliders
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self.h_slider.set(int(h * 360))
        self.s_slider.set(int(s * 100))
        self.v_slider.set(int(v * 100))
        self.h_label.configure(text=f"{int(h * 360)}°")
        self.s_label.configure(text=f"{int(s * 100)}%")
        self.v_label.configure(text=f"{int(v * 100)}%")
    
    def _add_to_recent(self, color: str):
        if color in self.recent_colors:
            self.recent_colors.remove(color)
        self.recent_colors.insert(0, color)
        self.recent_colors = self.recent_colors[:self.max_recent]
        self._update_recent_display()
    
    def _update_recent_display(self):
        for widget in self.recent_container.winfo_children():
            widget.destroy()
        
        for i, color in enumerate(self.recent_colors):
            btn = ctk.CTkButton(self.recent_container, text="", width=30, height=25,
                               fg_color=color, hover_color=color,
                               command=lambda c=color: self.set_color(c))
            btn.grid(row=0, column=i, padx=2, pady=2)
    
    def _open_color_picker(self, event=None):
        """Open system color picker dialog."""
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=self.current_color, title="Choose Color")
        if color and color[1]:  # color[1] is the hex string
            self.set_color(color[1])
    
    def set_color(self, hex_color: str):
        self.current_color = hex_color
        self.rgb = self._hex_to_rgb(hex_color)
        self._update_all_from_rgb()
        self._add_to_recent(hex_color)
        
        # Update color preview frame
        if hasattr(self, '_color_preview_frame'):
            self._color_preview_frame.configure(fg_color=hex_color)
        
        if self.on_color_change:
            self.on_color_change(hex_color, self.get_color_target())
    
    def get_color(self) -> str:
        return self.current_color
    
    def get_color_target(self) -> str:
        """Return the raw target key (accent, primary, etc.)"""
        display = self.color_target_var.get()
        return self._target_display_to_key.get(display, display)
    
    _TARGET_DESCRIPTIONS = {
        "accent": "accent color (UI highlights & buttons)",
        "primary": "primary color (main UI panels)",
        "secondary": "secondary color (side panels & accents)",
        "background": "background color (main window)",
        "button": "button color (clickable controls)",
        "button_hover": "button hover color (mouse-over effect)",
        "text": "text color (primary labels & headings)",
        "text_secondary": "secondary text color (descriptions & hints)",
        "border": "border color (edges & separators)",
    }
    
    def _on_target_change(self, value):
        """Update info label when the color target dropdown changes."""
        target = self.get_color_target()
        desc = self._TARGET_DESCRIPTIONS.get(target, target)
        if hasattr(self, '_target_info'):
            self._target_info.configure(text=f"Currently editing: {desc}")


class CursorCustomizer(ctk.CTkFrame):
    """Cursor customization with preview"""
    
    # Trail preview canvas dimensions
    TRAIL_PREVIEW_MIN_Y = 5
    TRAIL_PREVIEW_MAX_Y = 75
    TRAIL_PREVIEW_DOT_RADIUS = 4
    TRAIL_PREVIEW_MAX_DOTS = 20
    
    # Icons for each cursor type
    CURSOR_ICONS = {
        "default": "🖱️",
        "Arrow Pointer": "➤",
        "Pointing Hand": "👆",
        "Crosshair": "🎯",
        "Text Select": "📝",
        "Hourglass": "⏳",
        "Pirate Skull": "☠️",
        "Heart": "❤️",
        "Target Cross": "✚",
        "Star": "⭐",
        "Circle": "⭕",
        "Plus Sign": "➕",
        "Pencil": "✏️",
        "Dot": "•",
        "X Cursor": "✖️",
        "Diamond": "💎",
        "Fleur": "⚜️",
        "Spraycan": "🎨",
        "Left Arrow": "⬅️",
        "Right Arrow": "➡️",
    }
    
    # Icons for each trail style
    TRAIL_ICONS = {
        "rainbow": "🌈",
        "fire": "🔥",
        "ice": "❄️",
        "nature": "🌿",
        "galaxy": "🌌",
        "gold": "✨",
    }
    
    def __init__(self, master, on_cursor_change=None, unlockables_system=None, shop_system=None):
        super().__init__(master)
        self.on_cursor_change = on_cursor_change
        self.unlockables_system = unlockables_system
        self.shop_system = shop_system
        
        # Default cursors (always available)
        self.default_cursor_types = [
            "default", "Arrow Pointer", "Pointing Hand", "Crosshair",
            "Text Select", "Hourglass"
        ]
        
        # Initialize with defaults only - will be updated with unlocked/purchased cursors
        self.cursor_types = self.default_cursor_types.copy()
        self.cursor_sizes = {
            "🔹 tiny": (8, 8),
            "🔸 small": (16, 16),
            "🔷 medium": (32, 32),
            "🔶 large": (48, 48),
            "⬛ extra-large": (64, 64),
            "🟪 huge": (96, 96),
        }
        
        self.trail_styles = [
            "rainbow", "fire", "ice", "nature", "galaxy", "gold"
        ]
        
        self.current_cursor = config.get('ui', 'cursor', default='default')
        saved_size = config.get('ui', 'cursor_size', default='medium')
        # Migrate old plain size names to emoji-prefixed keys
        _size_migration = {"tiny": "🔹 tiny", "small": "🔸 small", "medium": "🔷 medium",
                           "large": "🔶 large", "extra-large": "⬛ extra-large", "huge": "🟪 huge"}
        self.current_size = _size_migration.get(saved_size, saved_size)
        if self.current_size not in self.cursor_sizes:
            self.current_size = "🔷 medium"
        self.current_tint = "#ffffff"
        self.trail_enabled = config.get('ui', 'cursor_trail', default=False)
        self.trail_style = config.get('ui', 'cursor_trail_color', default='rainbow')
        
        # Trail preview state
        self._trail_preview_dots = []
        self._trail_preview_canvas = None
        self._trail_preview_bind_id = None
        
        # Update available cursors based on unlocks/purchases
        self._refresh_available_cursors()
        
        self._create_widgets()
    
    def _refresh_available_cursors(self):
        """Refresh the list of available cursors based on unlock/purchase status."""
        # Start with default cursors (always available)
        available_cursors = self.default_cursor_types.copy()
        
        # Add unlocked cursors from achievements/progression
        if self.unlockables_system:
            try:
                unlocked_cursors = self.unlockables_system.get_unlocked_cursors()
                for cursor in unlocked_cursors:
                    cursor_name = cursor.name
                    if cursor_name not in available_cursors:
                        available_cursors.append(cursor_name)
                logger.debug(f"Added {len(unlocked_cursors)} unlocked cursors from achievements")
            except Exception as e:
                logger.warning(f"Failed to get unlocked cursors: {e}")
        
        # Add purchased cursors from shop
        if self.shop_system:
            try:
                # Get all cursor items from shop catalog
                from src.features.shop_system import ShopCategory
                cursor_items = [
                    item for item_id, item in self.shop_system.CATALOG.items()
                    if item.category == ShopCategory.CURSORS and self.shop_system.is_purchased(item_id)
                ]
                for item in cursor_items:
                    cursor_name = item.name
                    if cursor_name not in available_cursors:
                        available_cursors.append(cursor_name)
                logger.debug(f"Added {len(cursor_items)} purchased cursors from shop")
            except Exception as e:
                logger.warning(f"Failed to get purchased cursors: {e}")
        
        self.cursor_types = available_cursors
        logger.info(f"Available cursors: {len(self.cursor_types)} total")
    
    def _create_widgets(self):
        # Use scrollable frame so cursor selector has scrollbar
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        title = ctk.CTkLabel(scroll_frame, text="🖱️ Cursor Customization", font=("Arial Bold", 14))
        title.pack(pady=10)
        
        # --- Cursor Type with icons ---
        type_frame = ctk.CTkFrame(scroll_frame)
        type_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(type_frame, text="Cursor Type:").pack(side="left", padx=5)
        # Build display values with icons
        self._cursor_display_values = [
            f"{self.CURSOR_ICONS.get(c, '🖱️')} {c}" for c in self.cursor_types
        ]
        current_display = f"{self.CURSOR_ICONS.get(self.current_cursor, '🖱️')} {self.current_cursor}"
        self.cursor_var = ctk.StringVar(value=current_display)
        self.cursor_menu = ctk.CTkOptionMenu(type_frame, variable=self.cursor_var,
                                        values=self._cursor_display_values,
                                        command=self._on_cursor_change)
        self.cursor_menu.pack(side="left", padx=5, fill="x", expand=True)
        
        size_frame = ctk.CTkFrame(scroll_frame)
        size_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(size_frame, text="Size:").pack(side="left", padx=5)
        self.size_var = ctk.StringVar(value=self.current_size)
        size_menu = ctk.CTkOptionMenu(size_frame, variable=self.size_var,
                                      values=list(self.cursor_sizes.keys()),
                                      command=self._on_size_change)
        size_menu.pack(side="left", padx=5, fill="x", expand=True)
        
        tint_frame = ctk.CTkFrame(scroll_frame)
        tint_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(tint_frame, text="Tint Color:").pack(side="left", padx=5)
        self.tint_var = ctk.StringVar(value=self.current_tint)
        tint_entry = ctk.CTkEntry(tint_frame, textvariable=self.tint_var, width=100)
        tint_entry.pack(side="left", padx=5)
        
        self.tint_preview = ctk.CTkLabel(tint_frame, text="", width=30, height=30, 
                                         fg_color=self.current_tint)
        self.tint_preview.pack(side="left", padx=5)
        
        ctk.CTkButton(tint_frame, text="Pick", width=60,
                     command=self._pick_tint_color).pack(side="left", padx=5)
        
        # --- Trail enable/disable with icon ---
        trail_frame = ctk.CTkFrame(scroll_frame)
        trail_frame.pack(fill="x", padx=10, pady=5)
        
        self.trail_var = ctk.BooleanVar(value=self.trail_enabled)
        ctk.CTkCheckBox(trail_frame, text="✨ Enable Trail Effect", 
                       variable=self.trail_var,
                       command=self._on_trail_change).pack(side="left", padx=5)
        
        # --- Trail color selection with icons ---
        trail_color_frame = ctk.CTkFrame(scroll_frame)
        trail_color_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(trail_color_frame, text="Trail Style:").pack(side="left", padx=5)
        self._trail_display_values = [
            f"{self.TRAIL_ICONS.get(s, '✨')} {s}" for s in self.trail_styles
        ]
        current_trail_display = f"{self.TRAIL_ICONS.get(self.trail_style, '✨')} {self.trail_style}"
        self.trail_style_var = ctk.StringVar(value=current_trail_display)
        self.trail_style_menu = ctk.CTkOptionMenu(
            trail_color_frame, variable=self.trail_style_var,
            values=self._trail_display_values,
            command=self._on_trail_style_change)
        self.trail_style_menu.pack(side="left", padx=5, fill="x", expand=True)
        
        # --- Preview area with interactive cursor and trail preview ---
        preview_frame = ctk.CTkFrame(scroll_frame)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(preview_frame, text="🖱️ Cursor Preview:", font=("Arial Bold", 11)).pack(anchor="w", padx=5)
        
        self.preview_area = ctk.CTkLabel(preview_frame, text="Move mouse here\nto preview cursor",
                                        width=300, height=120, fg_color="#2b2b2b")
        self.preview_area.pack(padx=5, pady=5, fill="x")
        
        ctk.CTkLabel(preview_frame, text="✨ Cursor Trail Preview:", font=("Arial Bold", 11)).pack(anchor="w", padx=5, pady=(5, 0))
        
        # Trail preview - simple label showing trail description (no canvas)
        self._trail_preview_label = ctk.CTkLabel(
            preview_frame, 
            text="Trail will follow your cursor with the selected style",
            width=300, height=150, fg_color="#2b2b2b",
            font=("Arial", 10), 
            justify="center"
        )
        self._trail_preview_label.pack(padx=5, pady=(0, 5), fill="x")
        self._trail_preview_canvas = None  # No canvas needed
    
    def _strip_icon(self, display_value):
        """Strip leading emoji icon from display value to get raw name."""
        # Icons are separated by space after emoji; take everything after first space
        parts = display_value.split(' ', 1)
        return parts[1] if len(parts) > 1 else display_value
    
    def _on_cursor_change(self, cursor_type):
        self.current_cursor = self._strip_icon(cursor_type)
        self._update_preview()
        self._apply_cursor_instant()
    
    def _on_size_change(self, size):
        self.current_size = size
        self._update_preview()
        self._apply_cursor_instant()
    
    def _on_trail_change(self):
        self.trail_enabled = self.trail_var.get()
        self._update_preview()
        self._apply_cursor_instant()
    
    def _on_trail_style_change(self, trail_style):
        self.trail_style = self._strip_icon(trail_style)
        self._update_preview()
        self._apply_cursor_instant()
    
    
    # Trail preview methods removed - no longer using canvas
    # Trail will be shown in actual cursor movement, not in preview
    
    def _pick_tint_color(self):
        picker_window = ctk.CTkToplevel(self)
        picker_window.title("Pick Tint Color")
        picker_window.geometry("400x500")
        
        def on_color_selected(color, target=None):
            self.current_tint = color
            self.tint_var.set(color)
            self.tint_preview.configure(fg_color=color)
            self._update_preview()
        
        color_picker = ColorWheelWidget(picker_window, initial_color=self.current_tint,
                                       on_color_change=on_color_selected)
        color_picker.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkButton(picker_window, text="Done", 
                     command=picker_window.destroy).pack(pady=10)
    
    def _update_preview(self):
        size_str = f"{self.cursor_sizes[self.current_size][0]}x{self.cursor_sizes[self.current_size][1]}"
        trail_icon = self.TRAIL_ICONS.get(self.trail_style, '✨')
        trail_str = f"ON {trail_icon} ({self.trail_style})" if self.trail_enabled else "OFF"
        cursor_icon = self.CURSOR_ICONS.get(self.current_cursor, '🖱️')
        
        preview_text = (
            f"{cursor_icon} Type: {self.current_cursor}\n"
            f"Size: {size_str}\n"
            f"Tint: {self.current_tint}\n"
            f"Trail: {trail_str}"
        )
        self.preview_area.configure(text=preview_text)
        
        # Apply cursor to preview area for live preview
        cursor_map = {
            'default': 'arrow', 'Arrow Pointer': 'arrow',
            'Pointing Hand': 'hand2', 'Crosshair': 'crosshair',
            'Text Select': 'xterm', 'Hourglass': 'watch',
            'Pirate Skull': 'pirate', 'Heart': 'heart',
            'Target Cross': 'tcross', 'Star': 'star',
            'Circle': 'circle', 'Plus Sign': 'plus',
            'Pencil': 'pencil', 'Dot': 'dot',
            'X Cursor': 'X_cursor', 'Diamond': 'diamond_cross',
            'Fleur': 'fleur', 'Spraycan': 'spraycan',
            'Left Arrow': 'left_ptr', 'Right Arrow': 'right_ptr',
        }
        try:
            tk_cursor = cursor_map.get(self.current_cursor, 'arrow')
            self.preview_area.configure(cursor=tk_cursor)
        except Exception:
            pass
        
        # Update trail preview label when trail is disabled
        if not self.trail_enabled and hasattr(self, '_trail_preview_label'):
            try:
                self._trail_preview_label.configure(text="Trail disabled")
            except Exception:
                pass
    
    def _apply_cursor_instant(self):
        """Apply cursor settings instantly without showing a dialog."""
        config.set('ui', 'cursor', value=self.current_cursor)
        config.set('ui', 'cursor_size', value=self.current_size)
        config.set('ui', 'cursor_tint', value=self.current_tint)
        config.set('ui', 'cursor_trail', value=self.trail_enabled)
        config.set('ui', 'cursor_trail_color', value=self.trail_style)
        
        if self.on_cursor_change:
            self.on_cursor_change({
                'type': self.current_cursor,
                'size': self.current_size,
                'tint': self.current_tint,
                'trail': self.trail_enabled,
                'trail_color': self.trail_style
            })
    
    def _apply_cursor(self):
        self._apply_cursor_instant()
    
    def get_cursor_config(self) -> Dict[str, Any]:
        return {
            'type': self.current_cursor,
            'size': self.current_size,
            'tint': self.current_tint,
            'trail': self.trail_enabled,
            'trail_color': self.trail_style
        }
    
    def update_available_cursors(self, cursor_names: List[str] = None):
        """Update the available cursor options in the dropdown.
        
        Args:
            cursor_names: Optional list of cursor type names to show. If None, refreshes from systems.
        """
        if cursor_names is not None:
            # Legacy behavior - merge with defaults
            all_cursors = list(self.default_cursor_types)
            for name in cursor_names:
                if name not in all_cursors:
                    all_cursors.append(name)
            self.cursor_types = all_cursors
        else:
            # New behavior - refresh from unlockables and shop systems
            self._refresh_available_cursors()
        
        # Build display values with icons
        self._cursor_display_values = [
            f"{self.CURSOR_ICONS.get(c, '🖱️')} {c}" for c in self.cursor_types
        ]
        
        # Update the option menu widget with new values
        try:
            self.cursor_menu.configure(values=self._cursor_display_values)
            logger.debug(f"Updated cursor menu with {len(self._cursor_display_values)} options")
        except Exception as e:
            logger.debug(f"Failed to update cursor menu options: {e}")


class ThemeManager(ctk.CTkFrame):
    """Theme management with presets and custom themes"""
    
    def __init__(self, master, on_theme_apply=None):
        super().__init__(master)
        self.on_theme_apply = on_theme_apply
        self.current_theme = None
        self.preview_theme = None
        
        self._create_widgets()
        self._load_current_theme()
    
    def _create_widgets(self):
        title = ctk.CTkLabel(self, text="🎨 Theme Manager", font=("Arial Bold", 14))
        title.pack(pady=10)
        
        selector_frame = ctk.CTkFrame(self)
        selector_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(selector_frame, text="Select Theme:", font=("Arial Bold", 12)).pack(anchor="w", padx=5, pady=5)
        
        preset_frame = ctk.CTkScrollableFrame(selector_frame, height=200)
        preset_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        for theme_id, theme_data in THEME_PRESETS.items():
            theme_btn = ctk.CTkButton(preset_frame, text=theme_data["name"],
                                     command=lambda tid=theme_id: self._select_theme(tid),
                                     height=35)
            theme_btn.pack(fill="x", padx=5, pady=3)
        
        actions_frame = ctk.CTkFrame(self)
        actions_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(actions_frame, text="Theme Actions:", font=("Arial Bold", 12)).pack(anchor="w", padx=5, pady=5)
        
        btn_grid = ctk.CTkFrame(actions_frame)
        btn_grid.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(btn_grid, text="💾 Save as Custom", 
                     command=self._save_custom_theme,
                     width=140, height=35).grid(row=0, column=0, padx=5, pady=5)
        
        ctk.CTkButton(btn_grid, text="📂 Load Custom", 
                     command=self._load_custom_theme,
                     width=140, height=35).grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkButton(btn_grid, text="📤 Export JSON", 
                     command=self._export_theme,
                     width=140, height=35).grid(row=1, column=0, padx=5, pady=5)
        
        ctk.CTkButton(btn_grid, text="📥 Import JSON", 
                     command=self._import_theme,
                     width=140, height=35).grid(row=1, column=1, padx=5, pady=5)
        
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(preview_frame, text="Theme Preview:", font=("Arial Bold", 12)).pack(anchor="w", padx=5, pady=5)
        
        self.preview_container = ctk.CTkFrame(preview_frame, height=150)
        self.preview_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.preview_label = ctk.CTkLabel(self.preview_container, 
                                         text="Select a theme to preview",
                                         font=("Arial", 12))
        self.preview_label.pack(expand=True)
        
        apply_frame = ctk.CTkFrame(self)
        apply_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(apply_frame, text="👁️ Live Preview", 
                     command=self._live_preview,
                     width=150, height=40).pack(side="left", padx=5)
        
        ctk.CTkButton(apply_frame, text="✅ Apply Theme", 
                     command=self._apply_theme,
                     width=150, height=40).pack(side="left", padx=5)
    
    def _load_current_theme(self):
        theme_name = config.get('ui', 'theme', default='dark')
        
        for theme_id, theme_data in THEME_PRESETS.items():
            if theme_id == theme_name or theme_data["name"].lower().replace(" ", "_") == theme_name:
                self.current_theme = theme_id
                self._update_preview(theme_id)
                return
        
        self.current_theme = "dark_panda"
        self._update_preview("dark_panda")
    
    def _select_theme(self, theme_id: str):
        self.preview_theme = theme_id
        self._update_preview(theme_id)
        # Apply theme immediately when clicked
        self._apply_theme(show_message=False)
    
    def _update_preview(self, theme_id: str):
        if theme_id not in THEME_PRESETS:
            return
        
        theme = THEME_PRESETS[theme_id]
        colors = theme["colors"]
        
        for widget in self.preview_container.winfo_children():
            widget.destroy()
        
        preview_text = f"Theme: {theme['name']}\nAppearance: {theme['appearance_mode'].title()}"
        
        title = ctk.CTkLabel(self.preview_container, text=preview_text,
                            font=("Arial Bold", 12))
        title.pack(pady=10)
        
        colors_frame = ctk.CTkFrame(self.preview_container)
        colors_frame.pack(pady=10)
        
        row = 0
        col = 0
        for color_name, color_value in colors.items():
            swatch_frame = ctk.CTkFrame(colors_frame)
            swatch_frame.grid(row=row, column=col, padx=5, pady=5)
            
            ctk.CTkLabel(swatch_frame, text="", width=40, height=30,
                        fg_color=color_value).pack()
            ctk.CTkLabel(swatch_frame, text=color_name, 
                        font=("Arial", 8)).pack()
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
    
    def _live_preview(self):
        if not self.preview_theme:
            messagebox.showwarning("No Theme Selected", "Please select a theme first!")
            return
        
        theme = THEME_PRESETS[self.preview_theme]
        ctk.set_appearance_mode(theme["appearance_mode"])
        
        messagebox.showinfo("Live Preview", 
                          f"Previewing: {theme['name']}\n\n"
                          "This is a temporary preview.\n"
                          "Click 'Apply Theme' to make it permanent.")
    
    def _apply_theme(self, show_message=True):
        if not self.preview_theme:
            messagebox.showwarning("No Theme Selected", "Please select a theme first!")
            return
        
        theme = THEME_PRESETS[self.preview_theme]
        
        # Apply appearance mode
        ctk.set_appearance_mode(theme["appearance_mode"])
        
        colors = theme["colors"]
        
        # Save to config
        config.set('ui', 'theme', value=self.preview_theme)
        config.set('ui', 'appearance_mode', value=theme["appearance_mode"])
        config.set('ui', 'theme_colors', value=theme["colors"])
        
        self.current_theme = self.preview_theme
        
        # Apply theme colors to the root application window and all its children
        try:
            root = self.nametowidget(".")
        except (KeyError, ValueError):
            root = self.winfo_toplevel()
        self._apply_theme_to_existing_widgets(root, colors)
        
        if self.on_theme_apply:
            self.on_theme_apply(theme)
        
        if show_message:
            messagebox.showinfo("Success", 
                              f"Theme '{theme['name']}' applied!\n\n"
                              "Note: Some color changes may require restarting the application.")
    
    def _apply_theme_to_existing_widgets(self, widget, colors):
        """Recursively apply theme colors to all existing widgets in the hierarchy."""
        try:
            # Extract color values
            bg = colors.get("background", "#1a1a1a")
            fg = colors.get("foreground", "#ffffff")
            primary = colors.get("primary", "#1f538d")
            secondary = colors.get("secondary", "#14375e")
            accent = colors.get("accent", "#2fa572")
            button = colors.get("button", "#1f538d")
            button_hover = colors.get("button_hover", "#2d6ba8")
            text = colors.get("text", "#ffffff")
            text_secondary = colors.get("text_secondary", "#b0b0b0")
            border = colors.get("border", "#333333")
            
            # Compute contrasting text color for buttons/accent backgrounds
            button_text = self._get_contrast_text(button)
            accent_text = self._get_contrast_text(accent)
            secondary_text = self._get_contrast_text(secondary)
            
            # Apply colors based on widget type
            widget_class = widget.__class__.__name__
            
            try:
                if widget_class == 'CTk':
                    widget.configure(fg_color=bg)
                elif widget_class == 'CTkToplevel':
                    widget.configure(fg_color=bg)
                elif widget_class == 'CTkFrame':
                    # Only update if widget doesn't have explicit transparent setting
                    current_fg = widget.cget('fg_color')
                    if current_fg != 'transparent':
                        widget.configure(fg_color=secondary, border_color=border)
                elif widget_class == 'CTkButton':
                    widget.configure(fg_color=button, hover_color=button_hover, 
                                   text_color=button_text, border_color=border)
                elif widget_class == 'CTkLabel':
                    widget.configure(text_color=text)
                elif widget_class == 'CTkEntry':
                    widget.configure(fg_color=bg, text_color=text, border_color=border)
                elif widget_class == 'CTkTextbox':
                    widget.configure(fg_color=bg, text_color=text, border_color=border)
                elif widget_class == 'CTkOptionMenu':
                    widget.configure(fg_color=button, button_color=button, 
                                   button_hover_color=button_hover, text_color=button_text)
                elif widget_class == 'CTkComboBox':
                    widget.configure(fg_color=bg, button_color=button, 
                                   button_hover_color=button_hover, text_color=text, 
                                   border_color=border)
                elif widget_class == 'CTkCheckBox':
                    widget.configure(fg_color=accent, hover_color=button_hover, 
                                   text_color=text, border_color=border)
                elif widget_class == 'CTkSwitch':
                    widget.configure(progress_color=accent, button_color=button, 
                                   button_hover_color=button_hover, text_color=text)
                elif widget_class == 'CTkProgressBar':
                    widget.configure(fg_color=secondary, progress_color=accent)
                elif widget_class == 'CTkSlider':
                    widget.configure(fg_color=secondary, progress_color=accent, 
                                   button_color=button, button_hover_color=button_hover)
                elif widget_class == 'CTkScrollableFrame':
                    widget.configure(fg_color=secondary, label_fg_color=secondary)
                elif widget_class == 'CTkTabview':
                    widget.configure(fg_color=secondary, 
                                   segmented_button_selected_color=accent,
                                   segmented_button_unselected_color=secondary)
                elif widget_class == 'CTkSegmentedButton':
                    widget.configure(fg_color=secondary, selected_color=accent, 
                                   selected_hover_color=button_hover, text_color=text)
            except Exception as e:
                # Some widgets may not support all configuration options
                logger.debug(f"Could not apply theme to {widget_class}: {e}")
            
            # Recursively apply to children
            try:
                for child in widget.winfo_children():
                    self._apply_theme_to_existing_widgets(child, colors)
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"Error applying theme to widget {widget.__class__.__name__}: {e}")
    
    @staticmethod
    def _get_contrast_text(hex_color):
        """Return '#ffffff' or '#000000' depending on which contrasts better with the given color."""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) < 6:
                return "#ffffff"
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            # Relative luminance formula (ITU-R BT.709)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#000000" if luminance > 0.5 else "#ffffff"
        except (ValueError, IndexError, TypeError):
            return "#ffffff"
    
    def _save_custom_theme(self):
        if not self.preview_theme:
            messagebox.showwarning("No Theme Selected", "Please select a theme first!")
            return
        
        dialog = ctk.CTkInputDialog(text="Enter custom theme name:", title="Save Custom Theme")
        theme_name = dialog.get_input()
        
        if not theme_name:
            return
        
        theme = THEME_PRESETS[self.preview_theme].copy()
        theme["name"] = theme_name
        
        custom_theme_file = THEMES_DIR / f"{theme_name.lower().replace(' ', '_')}.json"
        
        try:
            with open(custom_theme_file, 'w') as f:
                json.dump(theme, f, indent=4)
            
            messagebox.showinfo("Success", f"Custom theme '{theme_name}' saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save theme: {e}")
    
    def _load_custom_theme(self):
        custom_themes = list(THEMES_DIR.glob("*.json"))
        
        if not custom_themes:
            messagebox.showinfo("No Custom Themes", 
                              "No custom themes found.\n\n"
                              "Create one by customizing a preset and saving it!")
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Load Custom Theme")
        dialog.geometry("400x300")
        
        ctk.CTkLabel(dialog, text="Select a custom theme:", 
                    font=("Arial Bold", 12)).pack(pady=10)
        
        listbox_frame = ctk.CTkScrollableFrame(dialog, height=200)
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        selected_file = [None]
        
        def select_theme(file_path):
            selected_file[0] = file_path
            dialog.destroy()
        
        for theme_file in custom_themes:
            theme_name = theme_file.stem.replace('_', ' ').title()
            btn = ctk.CTkButton(listbox_frame, text=theme_name,
                               command=lambda f=theme_file: select_theme(f))
            btn.pack(fill="x", padx=5, pady=3)
        
        dialog.wait_window()
        
        if selected_file[0]:
            self._load_theme_from_file(selected_file[0])
    
    def _load_theme_from_file(self, file_path: Path):
        try:
            with open(file_path, 'r') as f:
                theme_data = json.load(f)
            
            if not self._validate_theme(theme_data):
                messagebox.showerror("Invalid Theme", 
                                   "The theme file is invalid or corrupted.")
                return
            
            theme_id = file_path.stem
            THEME_PRESETS[theme_id] = theme_data
            
            self._select_theme(theme_id)
            
            messagebox.showinfo("Success", 
                              f"Custom theme '{theme_data['name']}' loaded successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load theme: {e}")
    
    def _export_theme(self):
        if not self.preview_theme:
            messagebox.showwarning("No Theme Selected", "Please select a theme first!")
            return
        
        theme = THEME_PRESETS[self.preview_theme]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{theme['name'].lower().replace(' ', '_')}.json"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w') as f:
                json.dump(theme, f, indent=4)
            
            messagebox.showinfo("Success", f"Theme exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export theme: {e}")
    
    def _import_theme(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        self._load_theme_from_file(Path(file_path))
    
    def _validate_theme(self, theme_data: Dict) -> bool:
        required_keys = ["name", "appearance_mode", "colors"]
        if not all(key in theme_data for key in required_keys):
            return False
        
        required_colors = ["primary", "secondary", "background", "foreground", 
                          "accent", "button", "button_hover", "text"]
        colors = theme_data.get("colors", {})
        if not all(color in colors for color in required_colors):
            return False
        
        return True
    
    def get_current_theme(self) -> Optional[Dict]:
        if self.current_theme:
            return THEME_PRESETS.get(self.current_theme)
        return None


class SettingsPanel(ctk.CTkFrame):
    """Settings panel for tooltip mode"""
    
    def __init__(self, master, on_settings_change=None):
        super().__init__(master)
        self.on_settings_change = on_settings_change
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Tooltip Mode Section
        tooltip_frame = ctk.CTkFrame(self)
        tooltip_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            tooltip_frame, 
            text="💬 Tooltip Mode", 
            font=("Arial Bold", 13)
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            tooltip_frame,
            text="Choose how detailed and snarky you want tooltips to be\n(This only changes tooltip text style, not the visual theme)",
            font=("Arial", 10),
            text_color="gray"
        ).pack(pady=(0, 10))
        
        # Load saved tooltip mode from config
        saved_mode = "normal"
        try:
            from src.config import config as app_config
            saved_mode = app_config.get('ui', 'tooltip_mode', default='normal')
        except Exception:
            pass
        self.tooltip_mode_var = ctk.StringVar(value=saved_mode)
        
        tooltip_options = [
            ("😊 Normal", "normal", "Standard helpful tooltips"),
            ("📖 Dumbed Down", "dumbed-down", "Detailed explanations for beginners"),
            ("🤬 Vulgar Panda", "vulgar_panda", "Fun, sarcastic tooltip text (opt-in, does not change theme)")
        ]
        
        for label, value, description in tooltip_options:
            radio_frame = ctk.CTkFrame(tooltip_frame)
            radio_frame.pack(fill="x", padx=20, pady=2)
            
            radio = ctk.CTkRadioButton(
                radio_frame,
                text=label,
                variable=self.tooltip_mode_var,
                value=value,
                command=self._on_tooltip_mode_change
            )
            radio.pack(side="left", padx=5)
            
            ctk.CTkLabel(
                radio_frame,
                text=f"- {description}",
                font=("Arial", 9),
                text_color="gray"
            ).pack(side="left", padx=5)
    
    def _on_tooltip_mode_change(self):
        mode = self.tooltip_mode_var.get()
        if self.on_settings_change:
            self.on_settings_change('tooltip_mode', mode)
    
    def get_settings(self) -> Dict[str, Any]:
        return {
            'tooltip_mode': self.tooltip_mode_var.get(),
        }
    
    def set_settings(self, settings: Dict[str, Any]):
        if 'tooltip_mode' in settings:
            self.tooltip_mode_var.set(settings['tooltip_mode'])


class SoundSettingsPanel(ctk.CTkFrame):
    """Dedicated sound settings panel with full controls"""
    
    def __init__(self, master, on_settings_change=None):
        super().__init__(master)
        self.on_settings_change = on_settings_change
        
        self._create_widgets()
    
    def _create_widgets(self):
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(
            scroll_frame,
            text="🔊 Sound Settings",
            font=("Arial Bold", 14)
        ).pack(pady=(10, 5))
        
        # Sound Enable/Disable
        self.sound_enabled_var = ctk.BooleanVar(value=True)
        sound_toggle = ctk.CTkCheckBox(
            scroll_frame,
            text="Enable Sound Effects",
            variable=self.sound_enabled_var,
            command=self._on_sound_toggle
        )
        sound_toggle.pack(pady=5, padx=20, anchor="w")
        
        # Master Volume Slider
        volume_container = ctk.CTkFrame(scroll_frame)
        volume_container.pack(fill="x", padx=20, pady=10)
        
        volume_label_frame = ctk.CTkFrame(volume_container)
        volume_label_frame.pack(fill="x")
        
        ctk.CTkLabel(
            volume_label_frame,
            text="Master Volume:",
            font=("Arial", 11)
        ).pack(side="left", padx=5)
        
        self.volume_value_label = ctk.CTkLabel(
            volume_label_frame,
            text="100%",
            font=("Arial", 11)
        )
        self.volume_value_label.pack(side="right", padx=5)
        
        self.volume_slider = ctk.CTkSlider(
            volume_container,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self._on_volume_change
        )
        self.volume_slider.set(100)
        self.volume_slider.pack(fill="x", pady=5)
        
        # Effects Volume
        effects_container = ctk.CTkFrame(scroll_frame)
        effects_container.pack(fill="x", padx=20, pady=5)
        
        effects_label_frame = ctk.CTkFrame(effects_container)
        effects_label_frame.pack(fill="x")
        
        ctk.CTkLabel(effects_label_frame, text="Effects Volume:", font=("Arial", 11)).pack(side="left", padx=5)
        self.effects_value_label = ctk.CTkLabel(effects_label_frame, text="100%", font=("Arial", 11))
        self.effects_value_label.pack(side="right", padx=5)
        
        self.effects_slider = ctk.CTkSlider(effects_container, from_=0, to=100, number_of_steps=100,
                                            command=self._on_effects_volume_change)
        self.effects_slider.set(100)
        self.effects_slider.pack(fill="x", pady=5)
        
        # Notifications Volume
        notif_container = ctk.CTkFrame(scroll_frame)
        notif_container.pack(fill="x", padx=20, pady=5)
        
        notif_label_frame = ctk.CTkFrame(notif_container)
        notif_label_frame.pack(fill="x")
        
        ctk.CTkLabel(notif_label_frame, text="Notifications Volume:", font=("Arial", 11)).pack(side="left", padx=5)
        self.notif_value_label = ctk.CTkLabel(notif_label_frame, text="100%", font=("Arial", 11))
        self.notif_value_label.pack(side="right", padx=5)
        
        self.notif_slider = ctk.CTkSlider(notif_container, from_=0, to=100, number_of_steps=100,
                                          command=self._on_notif_volume_change)
        self.notif_slider.set(100)
        self.notif_slider.pack(fill="x", pady=5)
        
        # Sound Pack Selection
        pack_frame = ctk.CTkFrame(scroll_frame)
        pack_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(pack_frame, text="🎵 Sound Pack:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        self.sound_pack_var = ctk.StringVar(value="default")
        pack_options = [
            ("🔔 Default", "default", "Standard sound effects for all events"),
            ("🔕 Minimal", "minimal", "Quiet, subtle sound effects"),
            ("🤪 Vulgar", "vulgar", "Fun, aggressive sound effects"),
        ]
        
        for label, value, description in pack_options:
            radio_frame = ctk.CTkFrame(pack_frame)
            radio_frame.pack(fill="x", padx=20, pady=2)
            
            radio = ctk.CTkRadioButton(
                radio_frame, text=label, variable=self.sound_pack_var,
                value=value, command=self._on_sound_pack_change
            )
            radio.pack(side="left", padx=5)
            
            ctk.CTkLabel(radio_frame, text=f"- {description}", font=("Arial", 9),
                        text_color="gray").pack(side="left", padx=5)
        
        # Individual Sound Muting & Selection
        mute_frame = ctk.CTkFrame(scroll_frame)
        mute_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(mute_frame, text="🔇 Per-Event Sound Settings:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        ctk.CTkLabel(mute_frame, text="Toggle each sound on/off and test the WAV file for each event",
                     font=("Arial", 9), text_color="gray").pack(anchor="w", padx=20, pady=(0, 5))
        
        self.mute_vars = {}
        sound_events = [
            ("complete", "✅ Completion Sound"),
            ("error", "❌ Error Sound"),
            ("achievement", "🏆 Achievement Sound"),
            ("milestone", "📊 Milestone Sound"),
            ("warning", "⚠️ Warning Sound"),
            ("start", "▶️ Start Sound"),
            ("pause", "⏸ Pause Sound"),
            ("resume", "⏯ Resume Sound"),
            ("stop", "⏹ Stop Sound"),
            ("button_click", "🖱️ Button Click Sound"),
            ("notification", "🔔 Notification Sound"),
        ]
        
        for event_id, event_label in sound_events:
            row = ctk.CTkFrame(mute_frame)
            row.pack(fill="x", padx=20, pady=2)
            
            var = ctk.BooleanVar(value=True)  # True = enabled (not muted)
            self.mute_vars[event_id] = var
            cb = ctk.CTkCheckBox(row, text=event_label, variable=var,
                                command=lambda eid=event_id: self._on_mute_toggle(eid))
            cb.pack(side="left", padx=5)
            
            test_btn = ctk.CTkButton(row, text="🔊 Test", width=70, height=26,
                                     command=lambda eid=event_id: self._test_event_sound(eid))
            test_btn.pack(side="right", padx=5)

        # === Panda Sounds Section ===
        panda_sound_frame = ctk.CTkFrame(scroll_frame)
        panda_sound_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(panda_sound_frame, text="🐼 Panda Sounds:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        ctk.CTkLabel(panda_sound_frame, text="Select which sound plays for each panda action. Purchase more sounds in the Shop!",
                     font=("Arial", 9), text_color="gray").pack(anchor="w", padx=20, pady=(0, 5))

        self.panda_sound_vars = {}
        panda_sound_events = [
            ("panda_eat", "🍜 Eating"),
            ("panda_happy", "😊 Happy"),
            ("panda_sad", "😢 Sad"),
            ("panda_drag", "✊ Being Dragged"),
            ("panda_drop", "⬇️ Dropped"),
            ("panda_sleep", "😴 Sleeping"),
            ("panda_wake", "⏰ Waking Up"),
            ("panda_click", "👆 Clicked"),
            ("panda_pet", "🤗 Being Petted"),
            ("panda_play", "🎮 Playing"),
            ("panda_walk", "🚶 Walking"),
            ("panda_jump", "🦘 Jumping"),
            ("panda_dance", "💃 Dancing"),
            ("panda_sneeze", "🤧 Sneezing"),
            ("panda_yawn", "🥱 Yawning"),
        ]

        for event_id, event_label in panda_sound_events:
            row = ctk.CTkFrame(panda_sound_frame)
            row.pack(fill="x", padx=20, pady=2)

            # Enable/disable checkbox
            var = ctk.BooleanVar(value=True)
            self.mute_vars[event_id] = var
            cb = ctk.CTkCheckBox(row, text=event_label, variable=var, width=160,
                                command=lambda eid=event_id: self._on_mute_toggle(eid))
            cb.pack(side="left", padx=5)

            # Sound selection dropdown
            choices = self._get_panda_sound_choices(event_id)
            choice_var = ctk.StringVar(value=choices[0] if choices else "Default")
            self.panda_sound_vars[event_id] = choice_var
            dropdown = ctk.CTkOptionMenu(row, variable=choice_var, values=choices, width=150,
                                         command=lambda val, eid=event_id: self._on_panda_sound_select(eid, val))
            dropdown.pack(side="left", padx=5)

            # Test button
            test_btn = ctk.CTkButton(row, text="🔊 Test", width=70, height=26,
                                     command=lambda eid=event_id: self._test_event_sound(eid))
            test_btn.pack(side="right", padx=5)

        # === Per-Event Sound Selection for System Sounds ===
        select_frame = ctk.CTkFrame(scroll_frame)
        select_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(select_frame, text="🎵 Sound Selection (System):", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        ctk.CTkLabel(select_frame, text="Choose which sound file to use for each system event",
                     font=("Arial", 9), text_color="gray").pack(anchor="w", padx=20, pady=(0, 5))

        self.system_sound_vars = {}
        system_events_for_selection = [
            ("complete", "✅ Completion"),
            ("error", "❌ Error"),
            ("achievement", "🏆 Achievement"),
            ("milestone", "📊 Milestone"),
            ("warning", "⚠️ Warning"),
            ("start", "▶️ Start"),
            ("button_click", "🖱️ Button Click"),
            ("notification", "🔔 Notification"),
        ]

        for event_id, event_label in system_events_for_selection:
            row = ctk.CTkFrame(select_frame)
            row.pack(fill="x", padx=20, pady=2)

            ctk.CTkLabel(row, text=event_label, width=140, anchor="w").pack(side="left", padx=5)

            choices = self._get_system_sound_choices(event_id)
            choice_var = ctk.StringVar(value=choices[0] if choices else "Default")
            self.system_sound_vars[event_id] = choice_var
            dropdown = ctk.CTkOptionMenu(row, variable=choice_var, values=choices, width=180,
                                         command=lambda val, eid=event_id: self._on_system_sound_select(eid, val))
            dropdown.pack(side="left", padx=5)

            test_btn = ctk.CTkButton(row, text="🔊 Test", width=70, height=26,
                                     command=lambda eid=event_id: self._test_event_sound(eid))
            test_btn.pack(side="right", padx=5)
    
    def _test_event_sound(self, event_id):
        """Play a test sound for the given event."""
        try:
            from src.features.sound_manager import SoundManager, SoundEvent, SoundPack
            if not hasattr(self, '_test_sound_manager'):
                self._test_sound_manager = SoundManager()
            sm = self._test_sound_manager
            sm.enabled = True
            sm.muted = False
            # Apply the currently selected sound pack so the test uses it
            try:
                pack = SoundPack(self.sound_pack_var.get())
                sm.set_sound_pack(pack)
            except (ValueError, AttributeError):
                pass
            try:
                event = SoundEvent(event_id)
            except ValueError:
                logger.warning(f"Unknown sound event: {event_id}")
                return
            sm.play_sound(event, async_play=True, force=True)
        except Exception as e:
            logger.debug(f"Could not play test sound for {event_id}: {e}")
    
    def _on_sound_toggle(self):
        enabled = self.sound_enabled_var.get()
        if self.on_settings_change:
            self.on_settings_change('sound_enabled', enabled)
    
    def _on_volume_change(self, value):
        volume = int(value)
        self.volume_value_label.configure(text=f"{volume}%")
        if self.on_settings_change:
            self.on_settings_change('volume', volume / 100.0)
    
    def _on_effects_volume_change(self, value):
        volume = int(value)
        self.effects_value_label.configure(text=f"{volume}%")
        if self.on_settings_change:
            self.on_settings_change('effects_volume', volume / 100.0)
    
    def _on_notif_volume_change(self, value):
        volume = int(value)
        self.notif_value_label.configure(text=f"{volume}%")
        if self.on_settings_change:
            self.on_settings_change('notifications_volume', volume / 100.0)
    
    def _on_sound_pack_change(self):
        pack = self.sound_pack_var.get()
        if self.on_settings_change:
            self.on_settings_change('sound_pack', pack)
    
    def _on_mute_toggle(self, event_id):
        enabled = self.mute_vars[event_id].get()
        if self.on_settings_change:
            self.on_settings_change('mute_sound', {'event': event_id, 'enabled': enabled})
    
    def _get_panda_sound_choices(self, event_id):
        """Get available sound choices for a panda event."""
        return self._get_sound_choices_for_event(event_id)

    def _get_system_sound_choices(self, event_id):
        """Get available sound choices for a system event."""
        return self._get_sound_choices_for_event(event_id)

    def _get_sound_choices_for_event(self, event_id):
        """Get available sound choice labels for any event."""
        try:
            from src.features.sound_manager import SoundManager, SoundEvent
            event = SoundEvent(event_id)
            choices = SoundManager.SOUND_CHOICES.get(event, [])
            return [label for label, _filename in choices] if choices else ["Default"]
        except Exception:
            return ["Default"]

    def _on_panda_sound_select(self, event_id, selected_label):
        """Handle panda sound selection change."""
        self._on_sound_select(event_id, selected_label)

    def _on_system_sound_select(self, event_id, selected_label):
        """Handle system sound selection change."""
        self._on_sound_select(event_id, selected_label)

    def _on_sound_select(self, event_id, selected_label):
        """Handle sound selection change for any event."""
        try:
            from src.features.sound_manager import SoundManager, SoundEvent
            event = SoundEvent(event_id)
            choices = SoundManager.SOUND_CHOICES.get(event, [])
            for label, filename in choices:
                if label == selected_label:
                    if self.on_settings_change:
                        self.on_settings_change('select_sound', {'event': event_id, 'sound': filename})
                    break
        except Exception as e:
            logger.debug(f"Could not select sound: {e}")
    
    def get_settings(self) -> Dict[str, Any]:
        return {
            'sound_enabled': self.sound_enabled_var.get(),
            'volume': self.volume_slider.get() / 100.0,
            'effects_volume': self.effects_slider.get() / 100.0,
            'notifications_volume': self.notif_slider.get() / 100.0,
            'sound_pack': self.sound_pack_var.get(),
            'muted_sounds': {k: not v.get() for k, v in self.mute_vars.items()},
        }
    
    def set_settings(self, settings: Dict[str, Any]):
        if 'sound_enabled' in settings:
            self.sound_enabled_var.set(settings['sound_enabled'])
        if 'volume' in settings:
            volume = int(settings['volume'] * 100)
            self.volume_slider.set(volume)
            self.volume_value_label.configure(text=f"{volume}%")
        if 'effects_volume' in settings:
            ev = int(settings['effects_volume'] * 100)
            self.effects_slider.set(ev)
            self.effects_value_label.configure(text=f"{ev}%")
        if 'notifications_volume' in settings:
            nv = int(settings['notifications_volume'] * 100)
            self.notif_slider.set(nv)
            self.notif_value_label.configure(text=f"{nv}%")
        if 'sound_pack' in settings:
            self.sound_pack_var.set(settings['sound_pack'])
        if 'muted_sounds' in settings:
            for event_id, muted in settings['muted_sounds'].items():
                if event_id in self.mute_vars:
                    self.mute_vars[event_id].set(not muted)


class CustomizationPanel(ctk.CTkFrame):
    """Main customization panel with all features"""
    
    def __init__(self, master, on_settings_change=None, unlockables_system=None, shop_system=None):
        super().__init__(master)
        self.on_settings_change = on_settings_change
        self.unlockables_system = unlockables_system
        self.shop_system = shop_system
        
        self._create_widgets()
    
    def _create_widgets(self):
        title = ctk.CTkLabel(self, text="🎨 UI Customization", font=("Arial Bold", 16))
        title.pack(pady=15)
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_theme = self.tabview.add("🎨 Themes")
        tab_colors = self.tabview.add("🎨 Colors")
        tab_cursor = self.tabview.add("🖱️ Cursor")
        tab_sound = self.tabview.add("🔊 Sound")
        tab_settings = self.tabview.add("💬 Tooltips Settings")
        
        self.theme_manager = ThemeManager(tab_theme, on_theme_apply=self._on_theme_change)
        self.theme_manager.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.color_picker = ColorWheelWidget(tab_colors, on_color_change=self._on_color_change)
        self.color_picker.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pass unlockables and shop systems to cursor customizer
        self.cursor_customizer = CursorCustomizer(
            tab_cursor, 
            on_cursor_change=self._on_cursor_change,
            unlockables_system=self.unlockables_system,
            shop_system=self.shop_system
        )
        self.cursor_customizer.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.sound_panel = SoundSettingsPanel(tab_sound, on_settings_change=self._on_setting_change)
        self.sound_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.settings_panel = SettingsPanel(tab_settings, on_settings_change=self._on_setting_change)
        self.settings_panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _on_theme_change(self, theme_data):
        if self.on_settings_change:
            self.on_settings_change('theme', theme_data)
    
    def _on_color_change(self, color, target="accent"):
        if self.on_settings_change:
            self.on_settings_change('color', {'color': color, 'target': target})
    
    def _on_cursor_change(self, cursor_config):
        if self.on_settings_change:
            self.on_settings_change('cursor', cursor_config)
    
    def _on_setting_change(self, setting_type, value):
        if self.on_settings_change:
            self.on_settings_change(setting_type, value)
    
    def get_all_settings(self) -> Dict[str, Any]:
        return {
            'theme': self.theme_manager.get_current_theme(),
            'cursor': self.cursor_customizer.get_cursor_config(),
            'color': self.color_picker.get_color(),
            'settings': self.settings_panel.get_settings()
        }


def open_customization_dialog(parent=None, on_settings_change=None, initial_tab=None, unlockables_system=None, shop_system=None):
    """Open customization dialog window
    
    Args:
        parent: Parent window
        on_settings_change: Optional callback function(setting_type, value) to handle setting changes
        initial_tab: Optional tab name to open initially (e.g. "🔊 Sound")
        unlockables_system: UnlockablesSystem instance for cursor filtering
        shop_system: ShopSystem instance for cursor filtering
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title("🎨 UI Customization")
    dialog.geometry("600x700")
    
    # Make dialog modal and stay on top
    if parent:
        dialog.transient(parent)
        dialog.grab_set()
    
    # Handle window close button (X)
    def on_close():
        if parent:
            dialog.grab_release()
        dialog.destroy()
    
    dialog.protocol("WM_DELETE_WINDOW", on_close)
    
    panel = CustomizationPanel(
        dialog, 
        on_settings_change=on_settings_change,
        unlockables_system=unlockables_system,
        shop_system=shop_system
    )
    panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Navigate to requested tab if specified
    if initial_tab:
        try:
            panel.tabview.set(initial_tab)
        except Exception:
            pass
    
    ctk.CTkButton(dialog, text="Close", command=on_close,
                 width=100, height=35).pack(pady=10)
    
    return dialog
