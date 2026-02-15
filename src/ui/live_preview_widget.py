"""
Live Preview Widget for Image Processing Tools
Provides real-time preview functionality with before/after comparison.
Slider mode: upscayl-style draggable vertical divider with zoom/pan.

DEPRECATED: This widget uses tk.Canvas for image display.
For PyQt6 applications, use: src/ui/live_preview_qt.py

The Canvas-based image rendering is being replaced with PyQt6 QGraphicsView
for better performance and hardware acceleration.

This file remains for Tkinter/customtkinter fallback compatibility.

Author: Dead On The Inside / JosephsDeadish
"""

import customtkinter as ctk
from tkinter import Canvas
from PIL import Image, ImageTk, ImageDraw
import logging
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class LivePreviewWidget(ctk.CTkFrame):
    """
    Live preview widget with before/after comparison for image processing.
    Default mode is Slider — a draggable vertical line that reveals
    before (left) and after (right), inspired by upscayl.
    Supports zoom (mouse-wheel) and pan (right-click drag).
    """

    SLIDER_LINE_COLOR = "#FFFFFF"
    SLIDER_LINE_WIDTH = 3
    SLIDER_HANDLE_RADIUS = 10
    SLIDER_HANDLE_COLOR = "#10B981"
    SLIDER_LABEL_BG = "#000000"
    SLIDER_LABEL_FG = "#FFFFFF"

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.original_image: Optional[Image.Image] = None
        self.processed_image: Optional[Image.Image] = None
        self.preview_size = (400, 300)
        self.comparison_mode = "slider"  # slider is default (upscayl-style)

        # Zoom / pan state
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._pan_start = None

        # Slider divider position as fraction 0..1 (starts at center)
        self._slider_pos = 0.5
        self._dragging_slider = False
        
        # Cached canvas dimensions to avoid repeated winfo calls
        self._canvas_width = 800
        self._canvas_height = 300
        self._resize_pending = False
        
        # Store photo references for cleanup
        self._photo_refs = []

        self._create_widgets()
        
        # Bind canvas configure event with throttling
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _create_widgets(self):
        """Create the preview widgets."""
        # Title bar
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            title_frame,
            text="\U0001f441\ufe0f Live Preview",
            font=("Arial Bold", 14)
        ).pack(side="left", padx=10)

        # Zoom controls
        zoom_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        zoom_frame.pack(side="right", padx=5)
        ctk.CTkButton(zoom_frame, text="\u2796", width=28,
                       command=self._zoom_out).pack(side="left", padx=1)
        self._zoom_label = ctk.CTkLabel(zoom_frame, text="100%",
                                         font=("Arial", 10), width=45)
        self._zoom_label.pack(side="left", padx=2)
        ctk.CTkButton(zoom_frame, text="\u2795", width=28,
                       command=self._zoom_in).pack(side="left", padx=1)
        ctk.CTkButton(zoom_frame, text="Fit", width=32,
                       command=self._zoom_fit).pack(side="left", padx=4)

        # Comparison mode selector
        self.mode_var = ctk.StringVar(value="Slider")
        mode_menu = ctk.CTkOptionMenu(
            title_frame,
            variable=self.mode_var,
            values=["Slider", "Side by Side", "Toggle"],
            command=self._on_mode_change,
            width=120
        )
        mode_menu.pack(side="right", padx=10)

        # Canvas frame
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Before/After labels (hidden in slider mode — drawn on canvas instead)
        self._label_frame = ctk.CTkFrame(canvas_frame)

        self.before_label = ctk.CTkLabel(
            self._label_frame, text="Before",
            font=("Arial Bold", 12), text_color="#64748B")
        self.before_label.pack(side="left", expand=True)

        self.after_label = ctk.CTkLabel(
            self._label_frame, text="After",
            font=("Arial Bold", 12), text_color="#10B981")
        self.after_label.pack(side="right", expand=True)

        # Canvas
        self.canvas = Canvas(
            canvas_frame, bg="#1E293B", highlightthickness=0,
            width=800, height=300)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=5)

        # Bind mouse events for slider / zoom / pan
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_end)
        self.canvas.bind("<MouseWheel>", self._on_scroll)        # Windows/macOS
        self.canvas.bind("<Button-4>", self._on_scroll_up)       # Linux
        self.canvas.bind("<Button-5>", self._on_scroll_down)     # Linux

        # Toggle button (toggle mode only)
        self.toggle_btn = ctk.CTkButton(
            self, text="Show After", command=self._toggle_view, width=150)
        self.showing_after = False

        # Status
        self.status_label = ctk.CTkLabel(
            self, text="Load an image to see preview",
            font=("Arial", 10), text_color="gray")
        self.status_label.pack(pady=5)

        # Show/hide label frame based on mode
        self._sync_label_frame()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_image(self, image_path: str):
        """Load an image for preview."""
        try:
            self.original_image = Image.open(image_path)
            self.processed_image = self.original_image.copy()
            self._zoom_fit()
            self._update_preview()
            self.status_label.configure(
                text=f"Loaded: {Path(image_path).name}", text_color="white")
            logger.info(f"Loaded image for preview: {image_path}")
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            self.status_label.configure(
                text=f"Error loading image: {e}", text_color="red")

    def load_images(self, before: Image.Image, after: Image.Image):
        """Load before/after PIL images directly (no file needed)."""
        self.original_image = before
        self.processed_image = after
        self._update_preview()

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
                self.processed_image = self.processing_function(
                    self.original_image)
                self._update_preview()
            except Exception as e:
                logger.error(f"Processing failed: {e}")
                self.status_label.configure(
                    text=f"Processing error: {e}", text_color="red")

    def clear(self):
        """Clear the preview."""
        self.original_image = None
        self.processed_image = None
        self._cleanup_photo_refs()
        self.canvas.delete("all")
        self.status_label.configure(
            text="Load an image to see preview", text_color="gray")
        # Force garbage collection after clearing
        import gc
        gc.collect()

    # ------------------------------------------------------------------
    # Internal — preview rendering
    # ------------------------------------------------------------------
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize events with throttling to prevent screen tearing."""
        # Update cached dimensions
        self._canvas_width = event.width
        self._canvas_height = event.height
        
        # Throttle resize updates to prevent excessive redraws
        if self._resize_pending:
            return
        
        self._resize_pending = True
        # Delay the update by 150ms to batch multiple resize events
        self.after(150, self._do_resize_update)
    
    def _do_resize_update(self):
        """Perform the actual resize update after throttling."""
        self._resize_pending = False
        if self.original_image and self.processed_image:
            self._update_preview()

    def _update_preview(self):
        if not self.original_image or not self.processed_image:
            return
        
        # Clean up old photo references to prevent memory leaks
        self._cleanup_photo_refs()
        
        self.canvas.delete("all")
        if self.comparison_mode == "side_by_side":
            self._show_side_by_side()
        elif self.comparison_mode == "toggle":
            self._show_toggle()
        elif self.comparison_mode == "slider":
            self._show_slider()
    
    def _cleanup_photo_refs(self):
        """Clean up old ImageTk.PhotoImage references to free memory."""
        # Clear the list of photo references
        # Note: This only removes our references; Python's GC will handle the actual cleanup
        self._photo_refs.clear()
        
        # Also clear individual photo attributes for backward compatibility
        # These are redundant if everything is tracked in _photo_refs, but kept for safety
        for attr_name in ['_slider_photo', 'before_photo', 'after_photo', 'preview_photo']:
            if hasattr(self, attr_name):
                try:
                    delattr(self, attr_name)
                except Exception:
                    pass

    # ---------- Slider mode (upscayl-style) ----------

    def _show_slider(self):
        """Render upscayl-style before/after with draggable vertical divider."""
        # Use cached dimensions instead of winfo calls to avoid resize issues
        cw = self._canvas_width
        ch = self._canvas_height

        # Resize both images to same display size (respecting zoom + pan)
        display_w = max(1, int(cw * self._zoom))
        display_h = max(1, int(ch * self._zoom))

        before_img = self._resize_image(
            self.original_image, display_w, display_h)
        after_img = self._resize_image(
            self.processed_image, display_w, display_h)

        # Make both the same size (use the smaller dimensions)
        bw, bh = before_img.size
        aw, ah = after_img.size
        w = min(bw, aw)
        h = min(bh, ah)
        before_img = before_img.crop((0, 0, w, h))
        after_img = after_img.crop((0, 0, w, h))

        # Compute the divider pixel position within the image
        divider_x = max(0, min(w, int(self._slider_pos * w)))

        # Composite: left of divider = before, right = after
        # Handle RGBA images by compositing onto white background first
        composite = Image.new("RGB", (w, h), (255, 255, 255))
        
        # Convert before image to RGB with white background if it has alpha
        if before_img.mode == 'RGBA':
            bg = Image.new('RGB', before_img.size, (255, 255, 255))
            bg.paste(before_img, mask=before_img.split()[3])  # Use alpha as mask
            before_rgb = bg
        else:
            before_rgb = before_img.convert("RGB")
        
        # Convert after image to RGB with white background if it has alpha
        if after_img.mode == 'RGBA':
            bg = Image.new('RGB', after_img.size, (255, 255, 255))
            bg.paste(after_img, mask=after_img.split()[3])  # Use alpha as mask
            after_rgb = bg
        else:
            after_rgb = after_img.convert("RGB")
        
        composite.paste(before_rgb, (0, 0))
        right_crop = after_rgb.crop((divider_x, 0, w, h))
        composite.paste(right_crop, (divider_x, 0))

        # Draw divider line + handle directly onto the composite
        draw = ImageDraw.Draw(composite)
        draw.line([(divider_x, 0), (divider_x, h)],
                  fill=self.SLIDER_LINE_COLOR, width=self.SLIDER_LINE_WIDTH)
        # Handle circle at vertical center
        cy = h // 2
        r = self.SLIDER_HANDLE_RADIUS
        draw.ellipse([divider_x - r, cy - r, divider_x + r, cy + r],
                     fill=self.SLIDER_HANDLE_COLOR, outline=self.SLIDER_LINE_COLOR)

        # Draw "Before" / "After" labels
        lbl_y = 12
        lbl_pad = 6
        for text, x_pos, anc in [("Before", lbl_pad, "la"),
                                   ("After", w - lbl_pad, "ra")]:
            draw.text((x_pos, lbl_y), text, fill=self.SLIDER_LABEL_FG,
                      anchor=anc)

        # Apply pan offset and render on canvas
        ox = (cw - w) // 2 + int(self._pan_x)
        oy = (ch - h) // 2 + int(self._pan_y)

        self._slider_photo = ImageTk.PhotoImage(composite)
        self._photo_refs.append(self._slider_photo)  # Track for cleanup
        self.canvas.create_image(ox, oy, image=self._slider_photo, anchor="nw")

        # Store geometry for hit-testing
        self._slider_img_rect = (ox, oy, ox + w, oy + h)

    # ---------- Side-by-side mode ----------

    def _show_side_by_side(self):
        # Use cached dimensions
        cw = self._canvas_width
        ch = self._canvas_height

        pw = (cw - 30) // 2
        ph = ch - 20

        before_img = self._resize_image(self.original_image, pw, ph)
        after_img = self._resize_image(self.processed_image, pw, ph)
        
        # Handle RGBA by compositing onto white background
        if before_img.mode == 'RGBA':
            bg = Image.new('RGB', before_img.size, (255, 255, 255))
            bg.paste(before_img, mask=before_img.split()[3])
            before_img = bg
        
        if after_img.mode == 'RGBA':
            bg = Image.new('RGB', after_img.size, (255, 255, 255))
            bg.paste(after_img, mask=after_img.split()[3])
            after_img = bg

        self.before_photo = ImageTk.PhotoImage(before_img)
        self.after_photo = ImageTk.PhotoImage(after_img)
        self._photo_refs.extend([self.before_photo, self.after_photo])  # Track for cleanup

        self.canvas.create_image(
            pw // 2 + 10, ph // 2 + 10,
            image=self.before_photo, anchor="center")
        self.canvas.create_image(
            pw + pw // 2 + 20, ph // 2 + 10,
            image=self.after_photo, anchor="center")
        self.canvas.create_line(
            pw + 15, 10, pw + 15, ch - 10, fill="#475569", width=2)

    # ---------- Toggle mode ----------

    def _show_toggle(self):
        # Use cached dimensions
        cw = self._canvas_width
        ch = self._canvas_height

        img = self.processed_image if self.showing_after else self.original_image
        preview_img = self._resize_image(img, cw - 20, ch - 20)
        
        # Handle RGBA by compositing onto white background
        if preview_img.mode == 'RGBA':
            bg = Image.new('RGB', preview_img.size, (255, 255, 255))
            bg.paste(preview_img, mask=preview_img.split()[3])
            preview_img = bg

        self.preview_photo = ImageTk.PhotoImage(preview_img)
        self._photo_refs.append(self.preview_photo)  # Track for cleanup
        self.canvas.create_image(
            cw // 2, ch // 2, image=self.preview_photo, anchor="center")

        if not self.toggle_btn.winfo_ismapped():
            self.toggle_btn.pack(before=self.status_label, pady=5)

    # ------------------------------------------------------------------
    # Zoom helpers
    # ------------------------------------------------------------------

    def _zoom_in(self):
        self._zoom = min(8.0, self._zoom + 0.25)
        self._zoom_label.configure(text=f"{int(self._zoom * 100)}%")
        self._update_preview()

    def _zoom_out(self):
        self._zoom = max(0.25, self._zoom - 0.25)
        self._zoom_label.configure(text=f"{int(self._zoom * 100)}%")
        self._update_preview()

    def _zoom_fit(self):
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._zoom_label.configure(text="100%")
        self._update_preview()

    # ------------------------------------------------------------------
    # Mouse event handlers
    # ------------------------------------------------------------------

    def _on_press(self, event):
        """Left-click: start dragging the slider divider."""
        if self.comparison_mode != "slider":
            return
        self._dragging_slider = True
        self._move_slider(event.x)

    def _on_drag(self, event):
        if self._dragging_slider:
            self._move_slider(event.x)

    def _on_release(self, event):
        self._dragging_slider = False

    def _move_slider(self, canvas_x):
        """Move the slider divider to the given canvas x coordinate."""
        rect = getattr(self, '_slider_img_rect', None)
        if not rect:
            return
        ix0, _, ix1, _ = rect
        img_w = ix1 - ix0
        if img_w <= 0:
            return
        local_x = canvas_x - ix0
        self._slider_pos = max(0.0, min(1.0, local_x / img_w))
        self._update_preview()

    def _on_pan_start(self, event):
        self._pan_start = (event.x, event.y)

    def _on_pan_move(self, event):
        if self._pan_start:
            dx = event.x - self._pan_start[0]
            dy = event.y - self._pan_start[1]
            self._pan_x += dx
            self._pan_y += dy
            self._pan_start = (event.x, event.y)
            self._update_preview()

    def _on_pan_end(self, event):
        self._pan_start = None

    def _on_scroll(self, event):
        if event.delta > 0:
            self._zoom_in()
        elif event.delta < 0:
            self._zoom_out()

    def _on_scroll_up(self, _event):
        self._zoom_in()

    def _on_scroll_down(self, _event):
        self._zoom_out()

    # ------------------------------------------------------------------
    # Mode switching helpers
    # ------------------------------------------------------------------

    def _on_mode_change(self, mode: str):
        mode_map = {
            "Side by Side": "side_by_side",
            "Toggle": "toggle",
            "Slider": "slider"
        }
        self.comparison_mode = mode_map.get(mode, "slider")
        if self.comparison_mode != "toggle" and self.toggle_btn.winfo_ismapped():
            self.toggle_btn.pack_forget()
        self._sync_label_frame()
        self._update_preview()

    def _sync_label_frame(self):
        """Show label row for side-by-side, hide for slider/toggle."""
        if self.comparison_mode == "side_by_side":
            if not self._label_frame.winfo_ismapped():
                self._label_frame.pack(fill="x", padx=10, pady=5,
                                       before=self.canvas.master)
        else:
            if self._label_frame.winfo_ismapped():
                self._label_frame.pack_forget()

    def _toggle_view(self):
        self.showing_after = not self.showing_after
        self.toggle_btn.configure(
            text="Show Before" if self.showing_after else "Show After")
        self._update_preview()

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _resize_image(self, image: Image.Image,
                      max_width: int, max_height: int) -> Image.Image:
        """Resize image to fit within max dimensions, keeping aspect ratio."""
        iw, ih = image.size
        scale = min(max_width / max(iw, 1), max_height / max(ih, 1))
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        return image.resize((nw, nh), Image.Resampling.LANCZOS)
