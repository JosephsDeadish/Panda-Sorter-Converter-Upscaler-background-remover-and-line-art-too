"""
UI Customization System
Comprehensive theming, color picker, and cursor customization
"""

import json
import math
import colorsys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import customtkinter as ctk
from tkinter import filedialog, messagebox

from src.config import config, THEMES_DIR


# Built-in theme presets
THEME_PRESETS = {
    "dark_panda": {
        "name": "Dark Panda (Default)",
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
        "name": "Light Mode",
        "appearance_mode": "light",
        "colors": {
            "primary": "#2874A6",
            "secondary": "#5499C7",
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
        "name": "Cyberpunk",
        "appearance_mode": "dark",
        "colors": {
            "primary": "#00ff41",
            "secondary": "#008f11",
            "background": "#0a0e27",
            "foreground": "#00ff41",
            "accent": "#ff006e",
            "button": "#00ff41",
            "button_hover": "#00cc33",
            "text": "#00ff41",
            "text_secondary": "#008f11",
            "border": "#00ff41"
        }
    },
    "neon_dreams": {
        "name": "Neon Dreams",
        "appearance_mode": "dark",
        "colors": {
            "primary": "#00d4ff",
            "secondary": "#0080ff",
            "background": "#0d1b2a",
            "foreground": "#ffffff",
            "accent": "#ff00ff",
            "button": "#00d4ff",
            "button_hover": "#00a3cc",
            "text": "#ffffff",
            "text_secondary": "#a0d2eb",
            "border": "#00d4ff"
        }
    },
    "classic_windows": {
        "name": "Classic Windows",
        "appearance_mode": "light",
        "colors": {
            "primary": "#0078d7",
            "secondary": "#005a9e",
            "background": "#c0c0c0",
            "foreground": "#000000",
            "accent": "#0078d7",
            "button": "#0078d7",
            "button_hover": "#005a9e",
            "text": "#000000",
            "text_secondary": "#555555",
            "border": "#808080"
        }
    },
    "vulgar_panda": {
        "name": "Vulgar Panda",
        "appearance_mode": "dark",
        "colors": {
            "primary": "#cc0000",
            "secondary": "#8b0000",
            "background": "#1a0000",
            "foreground": "#ff0000",
            "accent": "#ff3333",
            "button": "#cc0000",
            "button_hover": "#ff0000",
            "text": "#ff0000",
            "text_secondary": "#cc6666",
            "border": "#cc0000"
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
        title = ctk.CTkLabel(self, text="🎨 Color Picker", font=("Arial Bold", 14))
        title.pack(pady=10)
        
        hex_frame = ctk.CTkFrame(self)
        hex_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(hex_frame, text="Hex:").pack(side="left", padx=5)
        self.hex_var = ctk.StringVar(value=self.current_color)
        self.hex_entry = ctk.CTkEntry(hex_frame, textvariable=self.hex_var, width=100)
        self.hex_entry.pack(side="left", padx=5)
        self.hex_entry.bind("<Return>", lambda e: self._on_hex_change())
        
        ctk.CTkButton(hex_frame, text="Apply", width=60, 
                     command=self._on_hex_change).pack(side="left", padx=5)
        
        self.preview = ctk.CTkLabel(self, text="", width=200, height=50, fg_color=self.current_color)
        self.preview.pack(pady=10, padx=10)
        
        sliders_frame = ctk.CTkFrame(self)
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
        
        presets_frame = ctk.CTkFrame(self)
        presets_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(presets_frame, text="Presets:", font=("Arial Bold", 11)).pack(anchor="w", padx=5)
        
        preset_buttons = ctk.CTkFrame(presets_frame)
        preset_buttons.pack(fill="x", padx=5, pady=5)
        
        for i, color in enumerate(COLOR_PRESETS):
            btn = ctk.CTkButton(preset_buttons, text="", width=40, height=30,
                               fg_color=color, hover_color=color,
                               command=lambda c=color: self.set_color(c))
            btn.grid(row=0, column=i, padx=2, pady=2)
        
        self.recent_frame = ctk.CTkFrame(self)
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
            self.on_color_change(self.current_color)
    
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
    
    def set_color(self, hex_color: str):
        self.current_color = hex_color
        self.rgb = self._hex_to_rgb(hex_color)
        self._update_all_from_rgb()
        self._add_to_recent(hex_color)
        
        if self.on_color_change:
            self.on_color_change(hex_color)
    
    def get_color(self) -> str:
        return self.current_color


class CursorCustomizer(ctk.CTkFrame):
    """Cursor customization with preview"""
    
    def __init__(self, master, on_cursor_change=None):
        super().__init__(master)
        self.on_cursor_change = on_cursor_change
        
        self.cursor_types = ["default", "skull", "panda", "sword", "arrow", "custom"]
        self.cursor_sizes = {"small": (16, 16), "medium": (32, 32), "large": (48, 48)}
        
        self.current_cursor = config.get('ui', 'cursor', default='default')
        self.current_size = "medium"
        self.current_tint = "#ffffff"
        self.trail_enabled = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        title = ctk.CTkLabel(self, text="🖱️ Cursor Customization", font=("Arial Bold", 14))
        title.pack(pady=10)
        
        type_frame = ctk.CTkFrame(self)
        type_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(type_frame, text="Cursor Type:").pack(side="left", padx=5)
        self.cursor_var = ctk.StringVar(value=self.current_cursor)
        cursor_menu = ctk.CTkOptionMenu(type_frame, variable=self.cursor_var,
                                        values=self.cursor_types,
                                        command=self._on_cursor_change)
        cursor_menu.pack(side="left", padx=5, fill="x", expand=True)
        
        size_frame = ctk.CTkFrame(self)
        size_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(size_frame, text="Size:").pack(side="left", padx=5)
        self.size_var = ctk.StringVar(value=self.current_size)
        size_menu = ctk.CTkOptionMenu(size_frame, variable=self.size_var,
                                      values=list(self.cursor_sizes.keys()),
                                      command=self._on_size_change)
        size_menu.pack(side="left", padx=5, fill="x", expand=True)
        
        tint_frame = ctk.CTkFrame(self)
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
        
        trail_frame = ctk.CTkFrame(self)
        trail_frame.pack(fill="x", padx=10, pady=5)
        
        self.trail_var = ctk.BooleanVar(value=self.trail_enabled)
        ctk.CTkCheckBox(trail_frame, text="Enable Trail Effect", 
                       variable=self.trail_var,
                       command=self._on_trail_change).pack(side="left", padx=5)
        
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(preview_frame, text="Preview:", font=("Arial Bold", 11)).pack(anchor="w", padx=5)
        
        self.preview_area = ctk.CTkLabel(preview_frame, text="Move mouse here\nto preview cursor",
                                        width=200, height=100, fg_color="#2b2b2b")
        self.preview_area.pack(padx=5, pady=5)
        
        ctk.CTkButton(self, text="Apply Cursor", command=self._apply_cursor,
                     width=150, height=35).pack(pady=10)
    
    def _on_cursor_change(self, cursor_type):
        self.current_cursor = cursor_type
        self._update_preview()
    
    def _on_size_change(self, size):
        self.current_size = size
        self._update_preview()
    
    def _on_trail_change(self):
        self.trail_enabled = self.trail_var.get()
        self._update_preview()
    
    def _pick_tint_color(self):
        picker_window = ctk.CTkToplevel(self)
        picker_window.title("Pick Tint Color")
        picker_window.geometry("400x500")
        
        def on_color_selected(color):
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
        trail_str = "ON" if self.trail_enabled else "OFF"
        
        preview_text = f"Type: {self.current_cursor}\nSize: {size_str}\nTint: {self.current_tint}\nTrail: {trail_str}"
        self.preview_area.configure(text=preview_text)
    
    def _apply_cursor(self):
        config.set('ui', 'cursor', value=self.current_cursor)
        config.set('ui', 'cursor_size', value=self.current_size)
        config.set('ui', 'cursor_tint', value=self.current_tint)
        config.set('ui', 'cursor_trail', value=self.trail_enabled)
        
        if self.on_cursor_change:
            self.on_cursor_change({
                'type': self.current_cursor,
                'size': self.current_size,
                'tint': self.current_tint,
                'trail': self.trail_enabled
            })
        
        messagebox.showinfo("Success", "Cursor settings applied!")
    
    def get_cursor_config(self) -> Dict[str, Any]:
        return {
            'type': self.current_cursor,
            'size': self.current_size,
            'tint': self.current_tint,
            'trail': self.trail_enabled
        }


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
    
    def _apply_theme(self):
        if not self.preview_theme:
            messagebox.showwarning("No Theme Selected", "Please select a theme first!")
            return
        
        theme = THEME_PRESETS[self.preview_theme]
        ctk.set_appearance_mode(theme["appearance_mode"])
        
        config.set('ui', 'theme', value=self.preview_theme)
        config.set('ui', 'appearance_mode', value=theme["appearance_mode"])
        config.set('ui', 'theme_colors', value=theme["colors"])
        
        self.current_theme = self.preview_theme
        
        if self.on_theme_apply:
            self.on_theme_apply(theme)
        
        messagebox.showinfo("Success", f"Theme '{theme['name']}' applied successfully!")
    
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


class CustomizationPanel(ctk.CTkFrame):
    """Main customization panel with all features"""
    
    def __init__(self, master, on_settings_change=None):
        super().__init__(master)
        self.on_settings_change = on_settings_change
        
        self._create_widgets()
    
    def _create_widgets(self):
        title = ctk.CTkLabel(self, text="🎨 UI Customization", font=("Arial Bold", 16))
        title.pack(pady=15)
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_theme = self.tabview.add("🎨 Themes")
        tab_colors = self.tabview.add("🎨 Colors")
        tab_cursor = self.tabview.add("🖱️ Cursor")
        
        self.theme_manager = ThemeManager(tab_theme, on_theme_apply=self._on_theme_change)
        self.theme_manager.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.color_picker = ColorWheelWidget(tab_colors, on_color_change=self._on_color_change)
        self.color_picker.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.cursor_customizer = CursorCustomizer(tab_cursor, on_cursor_change=self._on_cursor_change)
        self.cursor_customizer.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _on_theme_change(self, theme_data):
        if self.on_settings_change:
            self.on_settings_change('theme', theme_data)
    
    def _on_color_change(self, color):
        if self.on_settings_change:
            self.on_settings_change('color', color)
    
    def _on_cursor_change(self, cursor_config):
        if self.on_settings_change:
            self.on_settings_change('cursor', cursor_config)
    
    def get_all_settings(self) -> Dict[str, Any]:
        return {
            'theme': self.theme_manager.get_current_theme(),
            'cursor': self.cursor_customizer.get_cursor_config(),
            'color': self.color_picker.get_color()
        }


def open_customization_dialog(parent=None, on_settings_change=None):
    """Open customization dialog window
    
    Args:
        parent: Parent window
        on_settings_change: Optional callback function(setting_type, value) to handle setting changes
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title("🎨 UI Customization")
    dialog.geometry("600x700")
    
    panel = CustomizationPanel(dialog, on_settings_change=on_settings_change)
    panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    ctk.CTkButton(dialog, text="Close", command=dialog.destroy,
                 width=100, height=35).pack(pady=10)
    
    return dialog
