"""
Enemy Widget - Animated enemy character for the UI
Displays an animated enemy that autonomously moves toward the panda to attack.
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import math
import random
import sys
import time
import tkinter as tk
from typing import Optional, Tuple, Callable
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from src.features.enemy_system import Enemy

logger = logging.getLogger(__name__)


# Canvas dimensions for enemy drawing
ENEMY_CANVAS_W = 120
ENEMY_CANVAS_H = 120

# Transparent color key for the Toplevel window (Windows only)
TRANSPARENT_COLOR = '#FF00FF'


class EnemyWidget(ctk.CTkFrame if ctk else tk.Frame):
    """Animated enemy widget that moves toward the panda to attack.
    
    Each enemy is rendered in its own Toplevel window with transparent background,
    allowing it to float on top of the main application and move independently.
    """
    
    # Movement constants
    MOVEMENT_INTERVAL = 50  # ms between movement updates (20 FPS)
    MOVE_SPEED_BASE = 2.0  # Base pixels per frame
    ATTACK_RANGE = 80  # Pixels - distance to trigger attack
    COLLISION_RADIUS = 40  # Pixels - radius for collision detection
    
    # Animation constants
    ANIMATION_INTERVAL = 100  # ms between animation frames
    BOUNCE_AMPLITUDE = 5  # Pixels - how much enemy bounces while moving
    
    def __init__(self, parent, enemy: Enemy, target_widget, 
                 on_attack: Optional[Callable] = None,
                 on_death: Optional[Callable] = None,
                 **kwargs):
        """
        Initialize enemy widget.
        
        Args:
            parent: Parent widget
            enemy: Enemy instance with stats and behavior
            target_widget: Widget to move toward (typically PandaWidget)
            on_attack: Callback when enemy attacks (receives enemy)
            on_death: Callback when enemy dies (receives enemy)
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.enemy = enemy
        self.target_widget = target_widget
        self.on_attack_callback = on_attack
        self.on_death_callback = on_death
        
        # Movement state
        self.is_moving = True
        self.is_attacking = False
        self.last_attack_time = 0
        self.attack_cooldown = 2.0  # seconds
        
        # Position tracking
        self.target_x = 0
        self.target_y = 0
        
        # Animation state
        self.animation_frame = 0
        self.animation_timer = None
        self.movement_timer = None
        self._destroyed = False
        
        # Configure the proxy frame as transparent
        if ctk:
            self.configure(fg_color="transparent", corner_radius=0, bg_color="transparent")
        else:
            try:
                parent_bg = parent.cget('bg')
                self.configure(bg=parent_bg, highlightthickness=0)
            except Exception:
                self.configure(highlightthickness=0)
        
        # Create separate Toplevel window for the enemy rendering
        self._toplevel = tk.Toplevel(self)
        self._toplevel.overrideredirect(True)
        self._toplevel.wm_attributes('-topmost', True)
        
        # Set up transparency
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
        
        self._toplevel_w = ENEMY_CANVAS_W
        self._toplevel_h = ENEMY_CANVAS_H
        self._toplevel.geometry(f"{self._toplevel_w}x{self._toplevel_h}")
        
        # Create canvas for enemy drawing
        self.enemy_canvas = tk.Canvas(
            self._toplevel,
            width=ENEMY_CANVAS_W,
            height=ENEMY_CANVAS_H,
            bg=self._canvas_bg,
            highlightthickness=0,
            bd=0
        )
        self.enemy_canvas.pack()
        
        # Set initial random position off-screen or at edges
        self._spawn_at_random_edge()
        
        # Start animation and movement
        self._start_animation()
        self._start_movement()
    
    def _get_parent_bg(self):
        """Get parent background color for transparency on non-Windows."""
        try:
            parent = self.winfo_toplevel()
            return parent.cget('bg')
        except Exception:
            return '#f0f0f0'
    
    def _spawn_at_random_edge(self):
        """Spawn enemy at a random edge of the screen."""
        try:
            root = self.winfo_toplevel()
            root.update_idletasks()
            
            rx = root.winfo_rootx()
            ry = root.winfo_rooty()
            rw = max(1, root.winfo_width())
            rh = max(1, root.winfo_height())
            
            # Choose random edge: 0=top, 1=right, 2=bottom, 3=left
            edge = random.randint(0, 3)
            
            if edge == 0:  # Top
                x = rx + random.randint(0, rw)
                y = ry - self._toplevel_h
            elif edge == 1:  # Right
                x = rx + rw
                y = ry + random.randint(0, rh)
            elif edge == 2:  # Bottom
                x = rx + random.randint(0, rw)
                y = ry + rh
            else:  # Left
                x = rx - self._toplevel_w
                y = ry + random.randint(0, rh)
            
            self._toplevel.geometry(f"+{x}+{y}")
            
        except Exception as e:
            logger.error(f"Error spawning enemy: {e}")
            # Fallback position
            self._toplevel.geometry(f"+100+100")
    
    def _start_animation(self):
        """Start the animation loop."""
        if not self._destroyed:
            self._animate()
    
    def _animate(self):
        """Update animation frame."""
        if self._destroyed or not self.enemy.is_alive():
            return
        
        self._draw_enemy()
        self.animation_frame += 1
        
        # Schedule next frame
        self.animation_timer = self.after(self.ANIMATION_INTERVAL, self._animate)
    
    def _draw_enemy(self):
        """Draw the enemy on canvas."""
        c = self.enemy_canvas
        c.delete("all")
        
        w = ENEMY_CANVAS_W
        h = ENEMY_CANVAS_H
        cx = w // 2
        cy = h // 2
        
        # Simple bouncing animation
        bounce = 0
        if self.is_moving:
            bounce = int(math.sin(self.animation_frame * 0.3) * self.BOUNCE_AMPLITUDE)
        
        # Draw enemy icon (emoji) with bounce
        icon_size = 48
        c.create_text(
            cx, cy + bounce,
            text=self.enemy.icon,
            font=("Arial", icon_size),
            tags="enemy"
        )
        
        # Draw health bar
        bar_width = 80
        bar_height = 6
        bar_x = cx - bar_width // 2
        bar_y = 10
        
        # Background bar
        c.create_rectangle(
            bar_x, bar_y,
            bar_x + bar_width, bar_y + bar_height,
            fill="#CC0000", outline="#880000", tags="health_bar"
        )
        
        # Health bar foreground
        health_pct = max(0, min(1, self.enemy.stats.current_health / self.enemy.stats.max_health))
        health_width = int(bar_width * health_pct)
        if health_width > 0:
            c.create_rectangle(
                bar_x, bar_y,
                bar_x + health_width, bar_y + bar_height,
                fill="#00FF00", outline="", tags="health_bar"
            )
        
        # Draw level indicator
        c.create_text(
            cx, h - 10,
            text=f"Lv.{self.enemy.level}",
            font=("Arial", 10, "bold"),
            fill="#FFFFFF" if sys.platform == 'win32' else "#000000",
            tags="level"
        )
    
    def _start_movement(self):
        """Start the movement loop."""
        if not self._destroyed:
            self._move_toward_target()
    
    def _move_toward_target(self):
        """Move one step toward the target."""
        if self._destroyed or not self.enemy.is_alive():
            return
        
        try:
            # Get current position
            ex = self._toplevel.winfo_x() + self._toplevel_w // 2
            ey = self._toplevel.winfo_y() + self._toplevel_h // 2
            
            # Get target position (center of panda widget)
            if hasattr(self.target_widget, '_toplevel'):
                tx = self.target_widget._toplevel.winfo_x() + self.target_widget._toplevel_w // 2
                ty = self.target_widget._toplevel.winfo_y() + self.target_widget._toplevel_h // 2
            else:
                # Fallback if target doesn't have toplevel
                tx = self.target_widget.winfo_rootx() + self.target_widget.winfo_width() // 2
                ty = self.target_widget.winfo_rooty() + self.target_widget.winfo_height() // 2
            
            # Calculate distance
            dx = tx - ex
            dy = ty - ey
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Check if in attack range
            if distance <= self.ATTACK_RANGE:
                if not self.is_attacking:
                    self._trigger_attack()
                self.is_moving = False
            else:
                self.is_moving = True
                
                # Calculate movement speed based on enemy behavior
                speed = self._get_movement_speed()
                
                # Normalize direction and move
                if distance > 0:
                    move_x = (dx / distance) * speed
                    move_y = (dy / distance) * speed
                    
                    new_x = ex + move_x - self._toplevel_w // 2
                    new_y = ey + move_y - self._toplevel_h // 2
                    
                    # Check bounds (stay within main window)
                    new_x, new_y = self._clamp_to_bounds(new_x, new_y)
                    
                    # Update position
                    self._toplevel.geometry(f"+{int(new_x)}+{int(new_y)}")
            
        except Exception as e:
            logger.debug(f"Error in enemy movement: {e}")
        
        # Schedule next movement update
        self.movement_timer = self.after(self.MOVEMENT_INTERVAL, self._move_toward_target)
    
    def _get_movement_speed(self) -> float:
        """Get movement speed based on enemy type and behavior."""
        speed = self.MOVE_SPEED_BASE
        
        # Adjust speed based on enemy type
        enemy_type = self.enemy.template.enemy_type.value
        
        if enemy_type == 'slime':
            speed *= 0.7  # Slower
        elif enemy_type == 'wolf':
            speed *= 1.5  # Faster
        elif enemy_type == 'goblin':
            speed *= 1.0  # Normal
        elif enemy_type == 'skeleton':
            speed *= 0.9  # Slightly slower
        elif enemy_type == 'orc':
            speed *= 0.8  # Slower but strong
        elif enemy_type == 'dragon':
            speed *= 1.2  # Fast for a boss
        
        return speed
    
    def _clamp_to_bounds(self, x: float, y: float) -> Tuple[float, float]:
        """Clamp position to stay within main window bounds."""
        try:
            root = self.winfo_toplevel()
            rx = root.winfo_rootx()
            ry = root.winfo_rooty()
            rw = max(1, root.winfo_width())
            rh = max(1, root.winfo_height())
            
            # Clamp to window bounds
            x = max(rx - self._toplevel_w // 2, min(x, rx + rw - self._toplevel_w // 2))
            y = max(ry - self._toplevel_h // 2, min(y, ry + rh - self._toplevel_h // 2))
            
        except Exception:
            pass
        
        return x, y
    
    def _trigger_attack(self):
        """Trigger an attack on the target."""
        current_time = time.time()
        
        # Check attack cooldown
        if current_time - self.last_attack_time < self.attack_cooldown:
            return
        
        self.last_attack_time = current_time
        self.is_attacking = True
        
        # Execute attack callback
        if self.on_attack_callback:
            self.on_attack_callback(self.enemy)
        
        logger.info(f"{self.enemy.name} attacks!")
        
        # Reset attacking state after a moment
        self.after(500, self._reset_attack_state)
    
    def _reset_attack_state(self):
        """Reset attacking state after attack animation."""
        self.is_attacking = False
    
    def take_damage(self, damage: int):
        """Enemy takes damage."""
        self.enemy.stats.take_damage(damage)
        
        if not self.enemy.is_alive():
            self._on_death()
    
    def _on_death(self):
        """Handle enemy death."""
        logger.info(f"{self.enemy.name} has been defeated!")
        
        # Execute death callback
        if self.on_death_callback:
            self.on_death_callback(self.enemy)
        
        # Destroy widget after a short delay
        self.after(1000, self.destroy)
    
    def get_position(self) -> Tuple[int, int]:
        """Get current center position of enemy."""
        try:
            x = self._toplevel.winfo_x() + self._toplevel_w // 2
            y = self._toplevel.winfo_y() + self._toplevel_h // 2
            return (x, y)
        except Exception:
            return (0, 0)
    
    def destroy(self):
        """Clean up and destroy the enemy widget."""
        self._destroyed = True
        
        # Cancel timers
        if self.animation_timer:
            try:
                self.after_cancel(self.animation_timer)
            except Exception:
                pass
        
        if self.movement_timer:
            try:
                self.after_cancel(self.movement_timer)
            except Exception:
                pass
        
        # Destroy toplevel
        try:
            self._toplevel.destroy()
        except Exception:
            pass
        
        super().destroy()
