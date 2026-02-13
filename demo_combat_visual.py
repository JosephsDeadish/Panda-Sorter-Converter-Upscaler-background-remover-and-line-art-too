#!/usr/bin/env python3
"""
Combat Visual Integration Demo - Shows damage effects and projectile rendering
Author: Dead On The Inside / JosephsDeadish
"""

import sys
import math
import tkinter as tk
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
except ImportError:
    print("CustomTkinter not available, using standard Tkinter")
    ctk = None

from src.features.damage_system import DamageTracker, DamageCategory, LimbType
from src.features.projectile_system import ProjectileManager, ProjectileType, ProjectilePhysics
from src.ui.visual_effects_renderer import VisualEffectsRenderer


class CombatDemo:
    """Demo showing combat visual effects."""
    
    def __init__(self):
        """Initialize demo."""
        self.root = tk.Tk() if not ctk else ctk.CTk()
        self.root.title("Combat Visual Effects Demo")
        self.root.geometry("800x600")
        
        # Systems
        self.damage_tracker = DamageTracker()
        self.projectile_manager = ProjectileManager()
        self.renderer = VisualEffectsRenderer()
        
        # State
        self.frame_count = 0
        self.last_update_time = 0
        
        self._create_ui()
        self._start_update_loop()
    
    def _create_ui(self):
        """Create UI."""
        # Main frame
        main_frame = tk.Frame(self.root) if not ctk else ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True)
        
        # Control panel
        control_frame = tk.Frame(main_frame) if not ctk else ctk.CTkFrame(main_frame)
        control_frame.pack(side="top", fill="x", padx=10, pady=10)
        
        # Title
        title_label = tk.Label(control_frame, text="⚔️ Combat Visual Effects Demo",
                               font=("Arial", 16, "bold"))
        if ctk:
            title_label = ctk.CTkLabel(control_frame, text="⚔️ Combat Visual Effects Demo",
                                      font=("Arial", 16, "bold"))
        title_label.pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(control_frame) if not ctk else ctk.CTkFrame(control_frame)
        btn_frame.pack(pady=5)
        
        # Damage buttons
        damages = [
            ("Sharp Damage", DamageCategory.SHARP, LimbType.LEFT_ARM),
            ("Blunt Damage", DamageCategory.BLUNT, LimbType.RIGHT_ARM),
            ("Fire Damage", DamageCategory.FIRE, LimbType.TORSO),
        ]
        
        for label, category, limb in damages:
            if ctk:
                btn = ctk.CTkButton(btn_frame, text=label,
                                   command=lambda c=category, l=limb: self.apply_damage(c, l))
            else:
                btn = tk.Button(btn_frame, text=label,
                               command=lambda c=category, l=limb: self.apply_damage(c, l))
            btn.pack(side="left", padx=2)
        
        # Projectile buttons
        if ctk:
            arrow_btn = ctk.CTkButton(btn_frame, text="Fire Arrow",
                                     command=lambda: self.fire_projectile(ProjectileType.ARROW))
            bullet_btn = ctk.CTkButton(btn_frame, text="Fire Bullet",
                                      command=lambda: self.fire_projectile(ProjectileType.BULLET))
        else:
            arrow_btn = tk.Button(btn_frame, text="Fire Arrow",
                                 command=lambda: self.fire_projectile(ProjectileType.ARROW))
            bullet_btn = tk.Button(btn_frame, text="Fire Bullet",
                                  command=lambda: self.fire_projectile(ProjectileType.BULLET))
        arrow_btn.pack(side="left", padx=2)
        bullet_btn.pack(side="left", padx=2)
        
        # Clear button
        if ctk:
            clear_btn = ctk.CTkButton(btn_frame, text="Clear All",
                                     command=self.clear_all)
        else:
            clear_btn = tk.Button(btn_frame, text="Clear All",
                                 command=self.clear_all)
        clear_btn.pack(side="left", padx=2)
        
        # Stats display
        self.stats_label = tk.Label(control_frame, text="", font=("Arial", 10))
        if ctk:
            self.stats_label = ctk.CTkLabel(control_frame, text="", font=("Arial", 10))
        self.stats_label.pack(pady=5)
        
        # Canvas for rendering
        self.canvas = tk.Canvas(main_frame, bg="#2B2B2B", width=760, height=400)
        self.canvas.pack(padx=20, pady=10)
        
        # Draw target dummy
        self.dummy_x = 400
        self.dummy_y = 200
        self._draw_dummy()
    
    def _draw_dummy(self):
        """Draw target dummy."""
        x, y = self.dummy_x, self.dummy_y
        
        # Head
        self.canvas.create_oval(x - 20, y - 60, x + 20, y - 20,
                               fill="#FFE4C4", outline="#8B7355", width=2,
                               tags="dummy")
        
        # Body
        self.canvas.create_rectangle(x - 30, y - 20, x + 30, y + 40,
                                     fill="#87CEEB", outline="#4682B4", width=2,
                                     tags="dummy")
        
        # Arms
        self.canvas.create_line(x - 30, y - 10, x - 60, y + 10,
                               fill="#FFE4C4", width=10, tags="dummy")
        self.canvas.create_line(x + 30, y - 10, x + 60, y + 10,
                               fill="#FFE4C4", width=10, tags="dummy")
        
        # Legs
        self.canvas.create_line(x - 15, y + 40, x - 20, y + 80,
                               fill="#4169E1", width=12, tags="dummy")
        self.canvas.create_line(x + 15, y + 40, x + 20, y + 80,
                               fill="#4169E1", width=12, tags="dummy")
    
    def apply_damage(self, category: DamageCategory, limb: LimbType):
        """Apply damage to dummy."""
        result = self.damage_tracker.apply_damage(limb, category, 25)
        print(f"Applied {category.value} damage to {limb.value}: Stage {result['stage']}")
        self._update_display()
    
    def fire_projectile(self, proj_type: ProjectileType):
        """Fire a projectile at dummy."""
        # Fire from left side toward dummy
        angle = 0  # Pointing right
        
        self.projectile_manager.spawn_projectile(
            x=50, y=200,
            angle=angle,
            projectile_type=proj_type,
            damage=30,
            on_hit=self._on_projectile_hit
        )
        print(f"Fired {proj_type.value}")
    
    def _on_projectile_hit(self, target, projectile, limb):
        """Handle projectile hit."""
        # Determine limb based on Y position
        y_offset = projectile.y - self.dummy_y
        if y_offset < -20:
            limb = LimbType.HEAD
        elif y_offset < 40:
            limb = LimbType.TORSO
        else:
            limb = LimbType.LEFT_LEG
        
        # Apply damage
        if projectile.projectile_type == ProjectileType.ARROW:
            self.damage_tracker.apply_damage(limb, DamageCategory.ARROW, 25)
            # Add stuck arrow
            rel_x = projectile.x - self.dummy_x
            rel_y = projectile.y - self.dummy_y
            self.damage_tracker.add_stuck_projectile("arrow", (rel_x, rel_y), limb)
        else:
            self.damage_tracker.apply_damage(limb, DamageCategory.BULLET, 30)
        
        print(f"Projectile hit {limb.value}!")
        self._update_display()
    
    def clear_all(self):
        """Clear all damage and projectiles."""
        self.damage_tracker.clear_all()
        self.projectile_manager.clear_all()
        self.canvas.delete("wound")
        self.canvas.delete("stuck_projectile")
        self.canvas.delete("projectile")
        self._update_display()
        print("Cleared all effects")
    
    def _update_display(self):
        """Update visual display."""
        # Clear previous effects
        self.canvas.delete("wound")
        self.canvas.delete("stuck_projectile")
        self.canvas.delete("bleeding")
        
        # Render wounds
        wounds = self.damage_tracker.get_all_wounds()
        self.renderer.render_wounds(self.canvas, wounds, self.dummy_x, self.dummy_y)
        
        # Render stuck projectiles
        stuck = self.damage_tracker.get_stuck_projectiles()
        self.renderer.render_stuck_projectiles(self.canvas, stuck, self.dummy_x, self.dummy_y)
        
        # Render bleeding effect
        if self.damage_tracker.total_bleeding_rate > 0:
            self.renderer.render_bleeding_effect(
                self.canvas, self.dummy_x, self.dummy_y + 40,
                self.damage_tracker.total_bleeding_rate,
                self.frame_count
            )
        
        # Update stats
        move_penalty = self.damage_tracker.get_movement_penalty()
        attack_penalty = self.damage_tracker.get_attack_penalty()
        
        stats_text = (
            f"Wounds: {len(wounds)} | "
            f"Stuck Projectiles: {len(stuck)} | "
            f"Bleeding: {self.damage_tracker.total_bleeding_rate:.1f}/s | "
            f"Movement Penalty: {move_penalty*100:.0f}% | "
            f"Attack Penalty: {attack_penalty*100:.0f}%"
        )
        self.stats_label.configure(text=stats_text)
    
    def _start_update_loop(self):
        """Start the update loop."""
        self._update()
    
    def _update(self):
        """Update loop."""
        import time
        
        current_time = time.time()
        delta_time = current_time - self.last_update_time if self.last_update_time > 0 else 0.016
        self.last_update_time = current_time
        
        # Update projectiles
        self.projectile_manager.update(delta_time)
        
        # Check collisions with dummy
        for proj in self.projectile_manager.get_active_projectiles():
            # Simple circular collision with dummy
            dx = proj.x - self.dummy_x
            dy = proj.y - self.dummy_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 50:  # Hit!
                proj.on_hit("dummy")
        
        # Clear and redraw projectiles
        self.canvas.delete("projectile")
        self.canvas.delete("projectile_trail")
        
        for proj in self.projectile_manager.get_active_projectiles():
            self.renderer.render_projectile(self.canvas, proj)
        
        # Update display
        self._update_display()
        
        self.frame_count += 1
        
        # Schedule next update
        self.root.after(33, self._update)  # ~30 FPS
    
    def run(self):
        """Run the demo."""
        print("Combat Visual Effects Demo")
        print("Click buttons to apply damage and fire projectiles")
        self.root.mainloop()


if __name__ == "__main__":
    try:
        demo = CombatDemo()
        demo.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
