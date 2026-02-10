"""
Panda Widget - Animated panda character for the UI
Displays an interactive panda that users can click, hover, pet, and drag around
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
import time
import tkinter as tk
from typing import Optional, Callable
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

logger = logging.getLogger(__name__)


class PandaWidget(ctk.CTkFrame if ctk else tk.Frame):
    """Interactive animated panda widget - always present and draggable."""
    
    # Minimum drag distance (pixels) to distinguish drag from click
    CLICK_THRESHOLD = 5
    
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
        self._destroyed = False
        
        # Dragging state
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False
        self._drag_moved = False  # Track if actual movement occurred
        self._last_drag_time = 0  # Throttle drag events (ms)
        
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
                self.info_label.configure(text="🐼 Wheee!")
        
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
                    self.info_label.configure(text="🐼 Ouch!")
    
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
                self.info_label.configure(text="🐼 Home sweet home!")
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
        if self._destroyed:
            return
        # Check if animations are disabled for low-end systems
        try:
            from src.config import config
            if config.get('ui', 'disable_panda_animations', default=False):
                # Just show static frame, no animation loop
                if self.panda:
                    frame = self.panda.get_animation_frame(animation_name)
                    self.panda_label.configure(text=frame)
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
            if self.panda:
                frame = self.panda.get_animation_frame(animation_name)
                self.panda_label.configure(text=frame)
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
    
    def _animate_loop(self):
        """Animate loop for continuous animation."""
        if self._destroyed:
            return
        try:
            if self.panda:
                frame = self.panda.get_animation_frame(self.current_animation)
                self.panda_label.configure(text=frame)
            
            # Continue animation
            self.animation_timer = self.after(500, self._animate_loop)
        except Exception as e:
            logger.error(f"Error in animation loop: {e}")
            # Ensure animation loop continues even after errors
            if not self._destroyed:
                try:
                    self.animation_timer = self.after(500, self._animate_loop)
                except Exception:
                    pass
    
    def _animate_once(self):
        """Animate once then return to idle."""
        if self._destroyed:
            return
        try:
            if self.panda:
                frame = self.panda.get_animation_frame(self.current_animation)
                self.panda_label.configure(text=frame)
            
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
        if not self._destroyed:
            self.info_label.configure(text=text)
    
    def destroy(self):
        """Clean up widget."""
        self._destroyed = True
        self._cancel_animation_timer()
        super().destroy()

