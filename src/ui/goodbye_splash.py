"""
Goodbye Splash Screen
Shows a brief farewell message when closing the application
"""

import random
import customtkinter as ctk
from pathlib import Path
from typing import Optional


# Configuration constants
INITIAL_PROGRESS = 0.3  # Initial progress value when splash appears


# Randomized panda farewell messages
GOODBYE_MESSAGES = [
    "See you later! 🐼",
    "Bamboo break time! 🎋",
    "Until next time, texture friend! 🐼",
    "Thanks for sorting with us! 🐼✨",
    "Goodbye, texture master! 🐼",
    "May your textures always be organized! 🎨",
    "Time for a panda nap! 😴🐼",
    "Stay sorted, friend! 🐼📁",
    "Catch you on the flip side! 🐼",
    "Happy texture hunting! 🐼🔍",
    "Until we sort again! 🐼💚",
    "Keep those textures tidy! 🐼✨",
]


class GoodbyeSplash:
    """Displays a brief goodbye message while saving and cleaning up"""
    
    def __init__(self, parent: Optional[ctk.CTk] = None):
        """Initialize goodbye splash
        
        Args:
            parent: Parent window (optional)
        """
        self.splash = ctk.CTkToplevel(parent)
        self.splash.title("")
        self.splash.geometry("400x200")
        
        # Remove window decorations
        self.splash.overrideredirect(True)
        
        # Center on screen
        self._center_window()
        
        # Make sure it's on top
        self.splash.lift()
        self.splash.attributes('-topmost', True)
        
        # Create content
        self._create_content()
        
    def _center_window(self):
        """Center the splash window on screen"""
        self.splash.update_idletasks()
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        window_width = 400
        window_height = 200
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.splash.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _create_content(self):
        """Create splash content with goodbye message"""
        # Main frame with border
        main_frame = ctk.CTkFrame(
            self.splash, 
            corner_radius=15,
            border_width=2,
            border_color="#2fa572"
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Random goodbye message
        message = random.choice(GOODBYE_MESSAGES)
        
        # Message label
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            font=("Arial Bold", 20),
            text_color="#2fa572"
        )
        message_label.pack(pady=(30, 10))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Saving configuration...",
            font=("Arial", 12),
            text_color="#b0b0b0"
        )
        self.status_label.pack(pady=10)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(main_frame, width=300)
        self.progress.pack(pady=20)
        self.progress.set(INITIAL_PROGRESS)
    
    def update_status(self, status: str, progress: float = None):
        """Update status message and progress
        
        Args:
            status: Status message to display
            progress: Progress value (0.0 to 1.0)
        """
        self.status_label.configure(text=status)
        if progress is not None:
            self.progress.set(progress)
        self.splash.update()
    
    def close(self):
        """Close the splash window"""
        try:
            self.splash.destroy()
        except Exception:
            pass


def show_goodbye_splash(parent: Optional[ctk.CTk] = None) -> GoodbyeSplash:
    """Show goodbye splash screen
    
    Args:
        parent: Parent window (optional)
        
    Returns:
        GoodbyeSplash instance for updating status
    """
    return GoodbyeSplash(parent)
