"""
Panda Widget - Animated panda character for the UI
Displays an interactive panda that users can click, hover, pet, and drag around
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
    """Interactive animated panda widget - always present and draggable."""
    
    def __init__(self, parent, panda_character=None, panda_level_system=None, **kwargs):
        """
        Initialize panda widget with drag functionality.
        
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
        
        # Dragging state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        
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
        
        # Bind events for interaction
        self.panda_label.bind("<Button-3>", self._on_right_click)
        self.panda_label.bind("<Enter>", self._on_hover)
        self.panda_label.bind("<Leave>", self._on_leave)
        
        # Bind events for dragging
        self.panda_label.bind("<Button-1>", self._on_drag_start)
        self.panda_label.bind("<B1-Motion>", self._on_drag_motion)
        self.panda_label.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # Also bind to the frame itself for dragging
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # Start idle animation
        self.start_animation('idle')
    
    def _on_drag_start(self, event):
        """Handle start of drag operation."""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True
        if self.panda:
            self.info_label.configure(text="🐼 Wheee!")
    
    def _on_drag_motion(self, event):
        """Handle drag motion - move the panda container."""
        if not self.is_dragging:
            return
        
        # Get the parent container (panda_container)
        parent = self.master
        if parent and hasattr(parent, 'place'):
            # Calculate new position
            x = parent.winfo_x() + (event.x - self.drag_start_x)
            y = parent.winfo_y() + (event.y - self.drag_start_y)
            
            # Constrain to window bounds
            root = self.winfo_toplevel()
            max_x = root.winfo_width() - parent.winfo_width()
            max_y = root.winfo_height() - parent.winfo_height()
            
            x = max(0, min(x, max_x))
            y = max(0, min(y, max_y))
            
            # Update position
            parent.place(x=x, y=y)
    
    def _on_drag_end(self, event):
        """Handle end of drag operation."""
        if not self.is_dragging:
            return
        
        self.is_dragging = False
        
        # Check if it was just a click (minimal movement)
        distance = ((event.x - self.drag_start_x) ** 2 + (event.y - self.drag_start_y) ** 2) ** 0.5
        if distance < 5:  # Less than 5 pixels = click, not drag
            self._on_click(event)
        else:
            # Save new position in config
            parent = self.master
            if parent:
                root = self.winfo_toplevel()
                # Calculate relative position (0.0 to 1.0)
                rel_x = parent.winfo_x() / max(1, root.winfo_width())
                rel_y = parent.winfo_y() / max(1, root.winfo_height())
                
                # Save to config (if config is available)
                try:
                    from src.config import config
                    config.set('panda', 'position_x', value=rel_x)
                    config.set('panda', 'position_y', value=rel_y)
                    config.save()
                    logger.info(f"Saved panda position: ({rel_x:.2f}, {rel_y:.2f})")
                except Exception as e:
                    logger.warning(f"Failed to save panda position: {e}")
            
            if self.panda:
                self.info_label.configure(text="🐼 Home sweet home!")
                # Award XP for moving the panda
                if self.panda_level_system:
                    # Use half the click reward for moving, or default to 5 XP
                    try:
                        xp = self.panda_level_system.get_xp_reward('click') // 2
                    except (KeyError, AttributeError, TypeError):
                        xp = 5  # Default XP for moving panda
                    self.panda_level_system.add_xp(xp, 'Moved panda')
    
    def _on_click(self, event=None):
        """Handle left click on panda."""
        try:
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
        except Exception as e:
            logger.error(f"Error handling panda click: {e}")
            self.info_label.configure(text="🐼 *confused panda noises*")
    
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
        except Exception as e:
            logger.error(f"Error handling menu action '{action}': {e}")
    
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
        try:
            if self.panda:
                frame = self.panda.get_animation_frame(self.current_animation)
                self.panda_label.configure(text=frame)
            
            # Continue animation
            self.animation_timer = self.after(500, self._animate_loop)
        except Exception as e:
            logger.error(f"Error in animation loop: {e}")
    
    def _animate_once(self):
        """Animate once then return to idle."""
        try:
            if self.panda:
                frame = self.panda.get_animation_frame(self.current_animation)
                self.panda_label.configure(text=frame)
            
            # Return to idle after 1 second
            self.after(1000, lambda: self.start_animation('idle'))
        except Exception as e:
            logger.error(f"Error in single animation: {e}")
    
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

