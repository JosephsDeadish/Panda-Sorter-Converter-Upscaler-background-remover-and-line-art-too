"""
⚠️ DEPRECATED AND UNUSED ⚠️

This file is NOT IMPORTED anywhere in the codebase and is kept only for
potential backward compatibility.

Use the Qt version instead: src/ui/qt_travel_animation.py

This file will be removed in a future version.

Simple travel animation using Labels instead of canvas drawing.
"""

import warnings
warnings.warn(
    "travel_animation_simple.py is deprecated and unused. "
    "Use qt_travel_animation.py (Qt-based) instead.",
    DeprecationWarning,
    stacklevel=2
)

import tkinter as tk
import customtkinter as ctk
from typing import List, Callable

class TravelAnimationWidget:
    """Simple travel animation display using widgets"""
    
    def __init__(self, parent_frame, scenes: List, on_complete: Callable):
        """
        Initialize travel animation.
        
        Args:
            parent_frame: Parent frame to place animation in
            scenes: List of scene objects with description, sky_color, etc.
            on_complete: Callback when animation completes
        """
        self.parent = parent_frame
        self.scenes = scenes
        self.on_complete = on_complete
        self.current_index = 0
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(parent_frame)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scene display frame
        self.scene_frame = tk.Frame(self.main_frame, width=500, height=300)
        self.scene_frame.pack(pady=10)
        self.scene_frame.pack_propagate(False)
        
        # Description label
        self.desc_label = ctk.CTkLabel(self.main_frame, text="", font=("Arial Bold", 16))
        self.desc_label.pack(pady=10)
        
        # Start animation
        self.show_scene(0)
    
    def show_scene(self, index):
        """Show a specific scene"""
        if index >= len(self.scenes):
            # Animation complete
            self.on_complete()
            return
        
        scene = self.scenes[index]
        
        # Clear scene frame
        for widget in self.scene_frame.winfo_children():
            widget.destroy()
        
        # Set background color
        self.scene_frame.configure(bg=scene.sky_color)
        
        # Create ground
        ground = tk.Frame(self.scene_frame, bg=scene.ground_color, height=100)
        ground.pack(side="bottom", fill="x")
        
        # Create road on ground
        road = tk.Frame(ground, bg=scene.road_color, height=50)
        road.pack(side="bottom", fill="x", pady=(0, 30))
        
        # Add road markings (simple labels)
        markings_frame = tk.Frame(road, bg=scene.road_color)
        markings_frame.pack(expand=True)
        for i in range(8):
            tk.Label(markings_frame, text="━", fg="#FFFFFF", bg=scene.road_color,
                    font=("Arial", 16)).pack(side="left", padx=10)
        
        # Create sky area
        sky = tk.Frame(self.scene_frame, bg=scene.sky_color)
        sky.pack(side="top", fill="both", expand=True)
        
        # Add details (trees, etc.)
        if hasattr(scene, 'detail_emoji') and scene.detail_emoji:
            detail_frame = tk.Frame(sky, bg=scene.sky_color)
            detail_frame.pack(side="bottom", fill="x", pady=5)
            for i in range(4):
                tk.Label(detail_frame, text=scene.detail_emoji, bg=scene.sky_color,
                        font=("Arial", 20)).pack(side="left", padx=30)
        
        # Add car and panda based on scene type
        scene_content = tk.Frame(sky, bg=scene.sky_color)
        scene_content.pack(expand=True)
        
        if hasattr(scene, 'scene_type'):
            if scene.scene_type.value == "walk_to_car":
                tk.Label(scene_content, text="🐼", bg=scene.sky_color,
                        font=("Arial", 40)).pack(side="left", padx=20)
                tk.Label(scene_content, text="➡️", bg=scene.sky_color,
                        font=("Arial", 30)).pack(side="left", padx=10)
                tk.Label(scene_content, text="🚗", bg=scene.sky_color,
                        font=("Arial", 40)).pack(side="left", padx=20)
            elif scene.scene_type.value == "get_in_car":
                tk.Label(scene_content, text="🚗🐼", bg=scene.sky_color,
                        font=("Arial", 40)).pack()
            elif scene.scene_type.value == "arrive":
                tk.Label(scene_content, text=f"🚗\n{scene.detail_emoji}", bg=scene.sky_color,
                        font=("Arial", 40)).pack()
            else:
                # Driving
                tk.Label(scene_content, text="🚗💨", bg=scene.sky_color,
                        font=("Arial", 40)).pack()
        else:
            # Default: just show car
            tk.Label(scene_content, text="🚗", bg=scene.sky_color,
                    font=("Arial", 40)).pack()
        
        # Update description
        self.desc_label.configure(text=scene.description)
        
        # Schedule next scene
        duration = scene.duration_ms if hasattr(scene, 'duration_ms') else 1000
        self.parent.after(duration, lambda: self.show_scene(index + 1))
