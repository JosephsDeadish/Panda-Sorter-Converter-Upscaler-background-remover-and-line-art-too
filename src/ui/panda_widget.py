"""
Panda Widget - Animated panda character for the UI
Displays an interactive panda that users can click, hover, and pet
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
import tkinter as tk
from typing import Optional, Callable
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

logger = logging.getLogger(__name__)


class PandaWidget(ctk.CTkFrame if ctk else tk.Frame):
    """Interactive animated panda widget - always present."""
    
    def __init__(self, parent, panda_character=None, panda_level_system=None, **kwargs):
        """
        Initialize panda widget.
        
        Args:
            parent: Parent widget
            panda_character: PandaCharacter instance for handling interactions
            panda_level_system: PandaLevelSystem instance for XP tracking
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.panda = panda_character
        self.panda_level_system = panda_level_system
        self.current_animation = 'idle'
        self.animation_frame = 0
        self.animation_timer = None
        
        # Configure frame
        if ctk:
            self.configure(fg_color="transparent", corner_radius=10)
        
        # Create panda display area
        self.panda_label = ctk.CTkLabel(
            self,
            text="",
            font=("Courier New", 12),
            justify="left",
            anchor="center"
        ) if ctk else tk.Label(
            self,
            text="",
            font=("Courier New", 12),
            justify="left"
        )
        self.panda_label.pack(pady=10, padx=10)
        
        # Create info display
        self.info_label = ctk.CTkLabel(
            self,
            text="Click me! 🐼",
            font=("Arial", 10),
            text_color="gray"
        ) if ctk else tk.Label(
            self,
            text="Click me! 🐼",
            font=("Arial", 10),
            fg="gray"
        )
        self.info_label.pack(pady=5)
        
        # Bind events
        self.panda_label.bind("<Button-1>", self._on_click)
        self.panda_label.bind("<Button-3>", self._on_right_click)
        self.panda_label.bind("<Enter>", self._on_hover)
        self.panda_label.bind("<Leave>", self._on_leave)
        
        # Start idle animation
        self.start_animation('idle')
    
    def _on_click(self, event=None):
        """Handle left click on panda."""
        if self.panda:
            response = self.panda.on_click()
            self.info_label.configure(text=response)
            # Play celebration animation briefly
            self.play_animation_once('celebrating')
            
            # Award XP for clicking
            if self.panda_level_system:
                xp = self.panda_level_system.get_xp_reward('click')
                leveled_up, new_level = self.panda_level_system.add_xp(xp, 'Click interaction')
                if leveled_up:
                    self.info_label.configure(text=f"🎉 Panda Level {new_level}!")
    
    def _on_right_click(self, event=None):
        """Handle right click on panda."""
        if self.panda:
            menu_items = self.panda.get_context_menu()
            # Create context menu
            menu = tk.Menu(self, tearoff=0)
            for key, label in menu_items.items():
                menu.add_command(
                    label=label,
                    command=lambda k=key: self._handle_menu_action(k)
                )
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
    
    def _on_hover(self, event=None):
        """Handle hover over panda."""
        if self.panda:
            thought = self.panda.on_hover()
            self.info_label.configure(text=thought)
    
    def _on_leave(self, event=None):
        """Handle mouse leaving panda."""
        self.info_label.configure(text="🐼")
    
    def _handle_menu_action(self, action: str):
        """Handle menu item selection."""
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
            self.play_animation_once('working')
            
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
    
    def start_animation(self, animation_name: str):
        """Start looping animation."""
        self.current_animation = animation_name
        self.animation_frame = 0
        self._animate_loop()
    
    def play_animation_once(self, animation_name: str):
        """Play animation once then return to idle."""
        self.current_animation = animation_name
        self.animation_frame = 0
        self._animate_once()
    
    def _animate_loop(self):
        """Animate loop for continuous animation."""
        if self.panda:
            frame = self.panda.get_animation_frame(self.current_animation)
            self.panda_label.configure(text=frame)
        
        # Continue animation
        self.animation_timer = self.after(500, self._animate_loop)
    
    def _animate_once(self):
        """Animate once then return to idle."""
        if self.panda:
            frame = self.panda.get_animation_frame(self.current_animation)
            self.panda_label.configure(text=frame)
        
        # Return to idle after 1 second
        self.after(1000, lambda: self.start_animation('idle'))
    
    def set_mood(self, mood):
        """Update panda mood and animation."""
        if self.panda:
            self.panda.set_mood(mood)
            # Change animation based on mood
            mood_animations = {
                'happy': 'idle',
                'working': 'working',
                'celebrating': 'celebrating',
                'rage': 'rage',
                'sarcastic': 'sarcastic',
                'drunk': 'drunk',
            }
            anim = mood_animations.get(mood.value if hasattr(mood, 'value') else mood, 'idle')
            self.start_animation(anim)
    
    def update_info(self, text: str):
        """Update info text below panda."""
        self.info_label.configure(text=text)
    
    def destroy(self):
        """Clean up widget."""
        if self.animation_timer:
            self.after_cancel(self.animation_timer)
        super().destroy()
