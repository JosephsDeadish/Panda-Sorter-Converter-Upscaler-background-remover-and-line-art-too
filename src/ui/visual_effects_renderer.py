"""
Visual Effects Renderer - Renders damage effects, wounds, and projectiles
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import math
import tkinter as tk
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class VisualEffectsRenderer:
    """Renders visual effects like wounds, projectiles, and damage overlays."""
    
    def __init__(self):
        """Initialize visual effects renderer."""
        self.show_debug = False
    
    def render_wounds(self, canvas: tk.Canvas, wounds: List, 
                     offset_x: int = 0, offset_y: int = 0,
                     scale: float = 1.0):
        """
        Render visual wounds on a canvas.
        
        Args:
            canvas: tkinter Canvas to draw on
            wounds: List of VisualWound objects from DamageTracker
            offset_x: X offset for positioning
            offset_y: Y offset for positioning
            scale: Scale factor for wound sizes
        """
        for wound in wounds:
            # Calculate position
            wx = offset_x + wound.position[0]
            wy = offset_y + wound.position[1]
            
            # Scale size based on severity
            size = int(wound.size * scale)
            
            # Render based on wound type
            if wound.wound_type == "gash":
                self._draw_gash(canvas, wx, wy, size, wound.color, wound.severity)
            elif wound.wound_type == "bruise":
                self._draw_bruise(canvas, wx, wy, size, wound.color, wound.severity)
            elif wound.wound_type == "hole":
                self._draw_hole(canvas, wx, wy, size, wound.color)
            elif wound.wound_type == "burn":
                self._draw_burn(canvas, wx, wy, size, wound.color, wound.severity)
            elif wound.wound_type == "frostbite":
                self._draw_frostbite(canvas, wx, wy, size, wound.color)
            else:
                # Generic wound
                self._draw_generic_wound(canvas, wx, wy, size, wound.color)
    
    def render_stuck_projectiles(self, canvas: tk.Canvas, projectiles: List,
                                 offset_x: int = 0, offset_y: int = 0,
                                 scale: float = 1.0):
        """
        Render projectiles stuck in body.
        
        Args:
            canvas: tkinter Canvas to draw on
            projectiles: List of ProjectileStuck objects
            offset_x: X offset for positioning
            offset_y: Y offset for positioning
            scale: Scale factor
        """
        for proj in projectiles:
            px = offset_x + int(proj.position[0] * scale)
            py = offset_y + int(proj.position[1] * scale)
            
            if proj.projectile_type == "arrow":
                self._draw_arrow_stuck(canvas, px, py, scale)
            elif proj.projectile_type == "bolt":
                self._draw_bolt_stuck(canvas, px, py, scale)
            elif proj.projectile_type == "spear":
                self._draw_spear_stuck(canvas, px, py, scale)
    
    def render_projectile(self, canvas: tk.Canvas, projectile,
                         offset_x: int = 0, offset_y: int = 0):
        """
        Render a flying projectile.
        
        Args:
            canvas: tkinter Canvas to draw on
            projectile: Projectile object from projectile_system
            offset_x: X offset for positioning
            offset_y: Y offset for positioning
        """
        if not projectile.active or projectile.stuck:
            return
        
        px = int(projectile.x + offset_x)
        py = int(projectile.y + offset_y)
        
        # Draw trail if available
        if projectile.trail_positions:
            self._draw_projectile_trail(canvas, projectile.trail_positions, 
                                       offset_x, offset_y)
        
        # Rotate based on angle
        angle_deg = math.degrees(projectile.angle)
        
        # Draw projectile icon with rotation effect
        canvas.create_text(
            px, py,
            text=projectile.icon,
            font=("Arial", 16),
            angle=angle_deg,
            tags="projectile"
        )
    
    def render_bleeding_effect(self, canvas: tk.Canvas, x: int, y: int,
                               bleeding_rate: float, frame: int):
        """
        Render bleeding drip animation.
        
        Args:
            canvas: tkinter Canvas
            x: Center X position
            y: Center Y position
            bleeding_rate: Rate of bleeding (affects drip count)
            frame: Current animation frame
        """
        if bleeding_rate <= 0:
            return
        
        # Number of drips based on bleeding rate
        drip_count = min(5, int(bleeding_rate))
        
        for i in range(drip_count):
            # Offset each drip
            drip_x = x + (i - drip_count // 2) * 10
            
            # Animated drip falling
            drip_y = y + 20 + (frame % 30) * 2
            
            # Draw blood drop
            canvas.create_oval(
                drip_x - 2, drip_y - 3,
                drip_x + 2, drip_y + 3,
                fill="#8B0000",
                outline="",
                tags="bleeding"
            )
    
    def render_damage_indicator(self, canvas: tk.Canvas, x: int, y: int,
                                damage_text: str, color: str = "#FF0000"):
        """
        Render floating damage number.
        
        Args:
            canvas: tkinter Canvas
            x: X position
            y: Y position
            damage_text: Text to display (e.g., "-25")
            color: Text color
        """
        canvas.create_text(
            x, y,
            text=damage_text,
            font=("Arial", 20, "bold"),
            fill=color,
            tags="damage_indicator"
        )
    
    def _draw_gash(self, canvas: tk.Canvas, x: int, y: int, 
                   size: int, color: str, severity: int):
        """Draw a gash wound."""
        # Gash is a jagged line
        length = size * 2
        
        # More jagged for higher severity
        points = []
        segments = 3 + severity // 3
        for i in range(segments + 1):
            px = x - length // 2 + (length * i // segments)
            py = y + ((-1) ** i) * (size // 4)
            points.extend([px, py])
        
        canvas.create_line(
            points,
            fill=color,
            width=max(1, severity // 3),
            tags="wound"
        )
    
    def _draw_bruise(self, canvas: tk.Canvas, x: int, y: int,
                     size: int, color: str, severity: int):
        """Draw a bruise wound."""
        # Bruise is irregular oval with darker center
        canvas.create_oval(
            x - size, y - size * 0.7,
            x + size, y + size * 0.7,
            fill=color,
            outline="",
            tags="wound"
        )
        
        # Darker center for severe bruises
        if severity > 6:
            center_size = size * 0.5
            canvas.create_oval(
                x - center_size, y - center_size * 0.7,
                x + center_size, y + center_size * 0.7,
                fill="#2F0052",  # Darker purple
                outline="",
                tags="wound"
            )
    
    def _draw_hole(self, canvas: tk.Canvas, x: int, y: int,
                   size: int, color: str):
        """Draw a bullet hole."""
        # Small circle with dark center
        canvas.create_oval(
            x - size, y - size,
            x + size, y + size,
            fill=color,
            outline="#8B0000",
            width=1,
            tags="wound"
        )
    
    def _draw_burn(self, canvas: tk.Canvas, x: int, y: int,
                   size: int, color: str, severity: int):
        """Draw a burn wound."""
        # Irregular shape with charred edges
        canvas.create_oval(
            x - size, y - size,
            x + size, y + size,
            fill=color,
            outline="#8B0000",
            width=max(1, severity // 4),
            tags="wound"
        )
        
        # Add darker spots for severe burns
        if severity > 6:
            for i in range(3):
                spot_x = x + (i - 1) * size // 2
                spot_y = y + ((-1) ** i) * size // 3
                spot_size = size // 3
                canvas.create_oval(
                    spot_x - spot_size, spot_y - spot_size,
                    spot_x + spot_size, spot_y + spot_size,
                    fill="#2F1800",
                    outline="",
                    tags="wound"
                )
    
    def _draw_frostbite(self, canvas: tk.Canvas, x: int, y: int,
                        size: int, color: str):
        """Draw frostbite effect."""
        # Light blue/white discoloration
        canvas.create_oval(
            x - size, y - size,
            x + size, y + size,
            fill=color,
            outline="#B0E0E6",
            width=2,
            tags="wound"
        )
    
    def _draw_generic_wound(self, canvas: tk.Canvas, x: int, y: int,
                           size: int, color: str):
        """Draw generic wound."""
        canvas.create_oval(
            x - size, y - size,
            x + size, y + size,
            fill=color,
            outline="",
            tags="wound"
        )
    
    def _draw_arrow_stuck(self, canvas: tk.Canvas, x: int, y: int, scale: float):
        """Draw arrow stuck in body."""
        shaft_length = int(15 * scale)
        
        # Arrow shaft
        canvas.create_line(
            x, y,
            x + shaft_length, y - shaft_length // 2,
            fill="#8B4513",
            width=int(2 * scale),
            tags="stuck_projectile"
        )
        
        # Arrowhead
        canvas.create_polygon(
            x + shaft_length - 5, y - shaft_length // 2 - 3,
            x + shaft_length, y - shaft_length // 2,
            x + shaft_length - 5, y - shaft_length // 2 + 3,
            fill="#696969",
            outline="",
            tags="stuck_projectile"
        )
    
    def _draw_bolt_stuck(self, canvas: tk.Canvas, x: int, y: int, scale: float):
        """Draw crossbow bolt stuck in body."""
        shaft_length = int(12 * scale)
        
        # Bolt shaft (shorter than arrow)
        canvas.create_line(
            x, y,
            x + shaft_length, y,
            fill="#654321",
            width=int(3 * scale),
            tags="stuck_projectile"
        )
        
        # Bolt head
        canvas.create_polygon(
            x + shaft_length - 4, y - 2,
            x + shaft_length, y,
            x + shaft_length - 4, y + 2,
            fill="#2F4F4F",
            outline="",
            tags="stuck_projectile"
        )
    
    def _draw_spear_stuck(self, canvas: tk.Canvas, x: int, y: int, scale: float):
        """Draw spear stuck in body."""
        shaft_length = int(20 * scale)
        
        # Spear shaft
        canvas.create_line(
            x, y,
            x + shaft_length, y + shaft_length // 4,
            fill="#A0522D",
            width=int(3 * scale),
            tags="stuck_projectile"
        )
        
        # Spear head
        canvas.create_polygon(
            x + shaft_length - 6, y + shaft_length // 4 - 4,
            x + shaft_length, y + shaft_length // 4,
            x + shaft_length - 6, y + shaft_length // 4 + 4,
            fill="#708090",
            outline="",
            tags="stuck_projectile"
        )
    
    def _draw_projectile_trail(self, canvas: tk.Canvas, trail_positions: List,
                               offset_x: int, offset_y: int):
        """Draw projectile trail effect."""
        if len(trail_positions) < 2:
            return
        
        # Draw fading trail
        for i, (tx, ty) in enumerate(trail_positions):
            px = int(tx + offset_x)
            py = int(ty + offset_y)
            
            # Fade based on position in trail
            opacity = int(255 * (i / len(trail_positions)))
            
            # Small dot for trail
            canvas.create_oval(
                px - 2, py - 2,
                px + 2, py + 2,
                fill=f"#{opacity:02x}{opacity:02x}{opacity:02x}",
                outline="",
                tags="projectile_trail"
            )
    
    def clear_effects(self, canvas: tk.Canvas):
        """Clear all visual effects from canvas."""
        canvas.delete("wound")
        canvas.delete("stuck_projectile")
        canvas.delete("projectile")
        canvas.delete("projectile_trail")
        canvas.delete("bleeding")
        canvas.delete("damage_indicator")
