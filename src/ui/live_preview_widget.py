"""
Live Preview Widget for Image Processing Tools
Provides real-time preview functionality with before/after comparison
Author: Dead On The Inside / JosephsDeadish
"""

import customtkinter as ctk
from tkinter import Canvas
from PIL import Image, ImageTk
import logging
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class LivePreviewWidget(ctk.CTkFrame):
    """
    Live preview widget with before/after comparison for image processing.
    Updates in real-time as parameters change.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.original_image: Optional[Image.Image] = None
        self.processed_image: Optional[Image.Image] = None
        self.preview_size = (400, 300)
        self.comparison_mode = "side_by_side"  # side_by_side, slider, toggle
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the preview widgets."""
        # Title
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            title_frame,
            text="👁️ Live Preview",
            font=("Arial Bold", 14)
        ).pack(side="left", padx=10)
        
        # Comparison mode selector
        self.mode_var = ctk.StringVar(value="Side by Side")
        mode_menu = ctk.CTkOptionMenu(
            title_frame,
            variable=self.mode_var,
            values=["Side by Side", "Toggle", "Slider"],
            command=self._on_mode_change,
            width=120
        )
        mode_menu.pack(side="right", padx=10)
        
        # Preview canvas frame
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Before/After labels
        label_frame = ctk.CTkFrame(canvas_frame)
        label_frame.pack(fill="x", padx=10, pady=5)
        
        self.before_label = ctk.CTkLabel(
            label_frame,
            text="Before",
            font=("Arial Bold", 12),
            text_color="#64748B"
        )
        self.before_label.pack(side="left", expand=True)
        
        self.after_label = ctk.CTkLabel(
            label_frame,
            text="After",
            font=("Arial Bold", 12),
            text_color="#10B981"
        )
        self.after_label.pack(side="right", expand=True)
        
        # Canvas for image display
        self.canvas = Canvas(
            canvas_frame,
            bg="#1E293B",
            highlightthickness=0,
            width=800,
            height=300
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Toggle button (for toggle mode)
        self.toggle_btn = ctk.CTkButton(
            self,
            text="Show After",
            command=self._toggle_view,
            width=150
        )
        self.showing_after = False
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Load an image to see preview",
            font=("Arial", 10),
            text_color="gray"
        )
        self.status_label.pack(pady=5)
    
    def load_image(self, image_path: str):
        """Load an image for preview."""
        try:
            self.original_image = Image.open(image_path)
            self.processed_image = self.original_image.copy()
            self._update_preview()
            self.status_label.configure(
                text=f"Loaded: {Path(image_path).name}",
                text_color="white"
            )
            logger.info(f"Loaded image for preview: {image_path}")
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            self.status_label.configure(
                text=f"Error loading image: {e}",
                text_color="red"
            )
    
    def update_processed(self, processed_image: Image.Image):
        """Update the processed image and refresh preview."""
        self.processed_image = processed_image
        self._update_preview()
    
    def set_processing_function(self, func: Callable):
        """Set a function that processes the original image."""
        self.processing_function = func
        if self.original_image:
            self.apply_processing()
    
    def apply_processing(self):
        """Apply the processing function to the original image."""
        if hasattr(self, 'processing_function') and self.original_image:
            try:
                self.processed_image = self.processing_function(self.original_image)
                self._update_preview()
            except Exception as e:
                logger.error(f"Processing failed: {e}")
                self.status_label.configure(
                    text=f"Processing error: {e}",
                    text_color="red"
                )
    
    def _update_preview(self):
        """Update the preview display."""
        if not self.original_image or not self.processed_image:
            return
        
        self.canvas.delete("all")
        
        if self.comparison_mode == "side_by_side":
            self._show_side_by_side()
        elif self.comparison_mode == "toggle":
            self._show_toggle()
        elif self.comparison_mode == "slider":
            self._show_slider()
    
    def _show_side_by_side(self):
        """Show before and after side by side."""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 300
        
        # Calculate sizes
        preview_width = (canvas_width - 30) // 2
        preview_height = canvas_height - 20
        
        # Resize images
        before_img = self._resize_image(self.original_image, preview_width, preview_height)
        after_img = self._resize_image(self.processed_image, preview_width, preview_height)
        
        # Convert to PhotoImage
        self.before_photo = ImageTk.PhotoImage(before_img)
        self.after_photo = ImageTk.PhotoImage(after_img)
        
        # Display images
        self.canvas.create_image(
            preview_width // 2 + 10,
            preview_height // 2 + 10,
            image=self.before_photo,
            anchor="center"
        )
        
        self.canvas.create_image(
            preview_width + preview_width // 2 + 20,
            preview_height // 2 + 10,
            image=self.after_photo,
            anchor="center"
        )
        
        # Draw separator line
        self.canvas.create_line(
            preview_width + 15,
            10,
            preview_width + 15,
            canvas_height - 10,
            fill="#475569",
            width=2
        )
    
    def _show_toggle(self):
        """Show either before or after (toggle mode)."""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 300
        
        img = self.processed_image if self.showing_after else self.original_image
        preview_img = self._resize_image(img, canvas_width - 20, canvas_height - 20)
        
        self.preview_photo = ImageTk.PhotoImage(preview_img)
        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.preview_photo,
            anchor="center"
        )
        
        # Show toggle button
        if not self.toggle_btn.winfo_ismapped():
            self.toggle_btn.pack(before=self.status_label, pady=5)
    
    def _show_slider(self):
        """Show before/after with vertical slider."""
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 300
        
        # For now, show side by side as slider requires more complex implementation
        self._show_side_by_side()
    
    def _resize_image(self, image: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """Resize image to fit within max dimensions while maintaining aspect ratio."""
        img_width, img_height = image.size
        
        # Calculate scaling
        scale = min(max_width / img_width, max_height / img_height)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _on_mode_change(self, mode: str):
        """Handle comparison mode change."""
        mode_map = {
            "Side by Side": "side_by_side",
            "Toggle": "toggle",
            "Slider": "slider"
        }
        self.comparison_mode = mode_map.get(mode, "side_by_side")
        
        # Hide toggle button if not in toggle mode
        if self.comparison_mode != "toggle" and self.toggle_btn.winfo_ismapped():
            self.toggle_btn.pack_forget()
        
        self._update_preview()
    
    def _toggle_view(self):
        """Toggle between before and after in toggle mode."""
        self.showing_after = not self.showing_after
        self.toggle_btn.configure(
            text="Show Before" if self.showing_after else "Show After"
        )
        self._update_preview()
    
    def clear(self):
        """Clear the preview."""
        self.original_image = None
        self.processed_image = None
        self.canvas.delete("all")
        self.status_label.configure(
            text="Load an image to see preview",
            text_color="gray"
        )
