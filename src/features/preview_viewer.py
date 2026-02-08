"""
Preview Viewer - Image preview with zoom, pan, and properties
Provides a non-blocking, moveable preview window for texture files
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import Optional, List, Callable
from PIL import Image, ImageTk
import os

logger = logging.getLogger(__name__)

# Try to import GUI libraries
try:
    import customtkinter as ctk
    from tkinter import Canvas
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


class PreviewViewer:
    """
    Moveable preview window with zoom, pan, and navigation controls
    """
    
    def __init__(self, master_window):
        self.master = master_window
        self.preview_window = None
        self.current_file = None
        self.file_list = []
        self.current_index = 0
        
        # Image display state
        self.original_image = None
        self.display_image = None
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # Canvas for image display
        self.canvas = None
        self.image_on_canvas = None
        
        # Panning state
        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        
    def open_preview(self, file_path: str, file_list: Optional[List[str]] = None):
        """
        Open preview window for a texture file
        
        Args:
            file_path: Path to the texture file to preview
            file_list: Optional list of files for navigation
        """
        if not GUI_AVAILABLE:
            logger.warning("GUI not available, cannot open preview")
            return
        
        self.current_file = Path(file_path)
        
        # Set up file list for navigation
        if file_list:
            self.file_list = [Path(f) for f in file_list]
            try:
                self.current_index = self.file_list.index(self.current_file)
            except ValueError:
                self.file_list = [self.current_file]
                self.current_index = 0
        else:
            # Get all texture files in the same directory
            self.file_list = self._get_sibling_textures(self.current_file)
            try:
                self.current_index = self.file_list.index(self.current_file)
            except ValueError:
                self.current_index = 0
        
        # Create or update window
        if self.preview_window is None or not self.preview_window.winfo_exists():
            self._create_preview_window()
        
        # Load and display the image
        self._load_image(self.current_file)
        
        # Update window title and properties
        self._update_window_title()
        
        # Bring window to front
        self.preview_window.lift()
        self.preview_window.focus_force()
    
    def _create_preview_window(self):
        """Create the preview window UI"""
        self.preview_window = ctk.CTkToplevel(self.master)
        self.preview_window.title("Preview Viewer")
        self.preview_window.geometry("900x700")
        
        # Make it non-modal and moveable
        self.preview_window.transient(self.master)
        # Don't make it modal - allow interaction with main window
        
        # Main container
        main_frame = ctk.CTkFrame(self.preview_window)
        main_frame.pack(fill="both", expand=True)
        
        # === TOOLBAR ===
        toolbar = ctk.CTkFrame(main_frame, height=50)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # Navigation buttons
        nav_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        nav_frame.pack(side="left", padx=5)
        
        ctk.CTkButton(
            nav_frame,
            text="◀ Previous",
            width=100,
            command=self._show_previous
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            nav_frame,
            text="Next ▶",
            width=100,
            command=self._show_next
        ).pack(side="left", padx=2)
        
        # Zoom controls
        zoom_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        zoom_frame.pack(side="left", padx=20)
        
        ctk.CTkButton(
            zoom_frame,
            text="🔍−",
            width=50,
            command=self._zoom_out
        ).pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(zoom_frame, text="100%", width=60)
        self.zoom_label.pack(side="left", padx=5)
        
        ctk.CTkButton(
            zoom_frame,
            text="🔍+",
            width=50,
            command=self._zoom_in
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            zoom_frame,
            text="Reset",
            width=70,
            command=self._reset_view
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            zoom_frame,
            text="Fit",
            width=60,
            command=self._fit_to_window
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            zoom_frame,
            text="1:1",
            width=50,
            command=self._actual_size
        ).pack(side="left", padx=2)
        
        # Export button
        ctk.CTkButton(
            toolbar,
            text="💾 Export",
            width=100,
            command=self._export_image
        ).pack(side="right", padx=5)
        
        # Properties toggle
        ctk.CTkButton(
            toolbar,
            text="ℹ️ Properties",
            width=100,
            command=self._toggle_properties
        ).pack(side="right", padx=5)
        
        # === MAIN CONTENT AREA ===
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Canvas for image display (with scrollbars)
        self.canvas = Canvas(
            content_frame,
            bg='#2b2b2b',
            highlightthickness=0
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Properties panel (initially hidden)
        self.properties_panel = ctk.CTkFrame(content_frame, width=250)
        self.properties_visible = False
        
        self._setup_properties_panel()
        
        # === STATUS BAR ===
        self.status_bar = ctk.CTkFrame(main_frame, height=30)
        self.status_bar.pack(fill="x", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10)
        
        # Bind mouse events for panning
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._do_pan)
        self.canvas.bind("<ButtonRelease-1>", self._end_pan)
        
        # Bind mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self._mouse_wheel_zoom)
        
        # Bind keyboard shortcuts
        self.preview_window.bind("<Left>", lambda e: self._show_previous())
        self.preview_window.bind("<Right>", lambda e: self._show_next())
        self.preview_window.bind("<Escape>", lambda e: self.preview_window.destroy())
    
    def _setup_properties_panel(self):
        """Setup the properties panel"""
        # Title
        title = ctk.CTkLabel(
            self.properties_panel,
            text="Properties",
            font=("Arial Bold", 14)
        )
        title.pack(pady=10)
        
        # Scrollable frame for properties
        self.properties_scroll = ctk.CTkScrollableFrame(self.properties_panel)
        self.properties_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Properties labels (will be populated when image loads)
        self.prop_labels = {}
    
    def _toggle_properties(self):
        """Toggle visibility of properties panel"""
        if self.properties_visible:
            self.properties_panel.pack_forget()
            self.properties_visible = False
        else:
            self.properties_panel.pack(side="right", fill="y", padx=(5, 0))
            self.properties_visible = True
            self._update_properties()
    
    def _update_properties(self):
        """Update properties panel with current image info"""
        # Clear existing labels
        for widget in self.properties_scroll.winfo_children():
            widget.destroy()
        
        if not self.current_file or not self.current_file.exists():
            return
        
        # File properties
        file_stats = self.current_file.stat()
        file_size = file_stats.st_size
        file_size_str = self._format_file_size(file_size)
        
        properties = {
            "File Name": self.current_file.name,
            "File Path": str(self.current_file.parent),
            "File Size": file_size_str,
            "Format": self.current_file.suffix.upper().replace('.', ''),
        }
        
        # Image properties
        if self.original_image:
            properties.update({
                "Dimensions": f"{self.original_image.width} × {self.original_image.height}",
                "Mode": self.original_image.mode,
                "Aspect Ratio": f"{self.original_image.width / self.original_image.height:.2f}",
            })
            
            # Additional image info if available
            if hasattr(self.original_image, 'info'):
                info = self.original_image.info
                if 'dpi' in info:
                    properties["DPI"] = str(info['dpi'])
        
        # Display properties
        for key, value in properties.items():
            prop_frame = ctk.CTkFrame(self.properties_scroll, fg_color="transparent")
            prop_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                prop_frame,
                text=f"{key}:",
                font=("Arial Bold", 11),
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                prop_frame,
                text=str(value),
                font=("Arial", 10),
                anchor="w",
                wraplength=220
            ).pack(anchor="w", padx=10)
    
    def _load_image(self, file_path: Path):
        """Load an image file"""
        try:
            self.original_image = Image.open(file_path)
            self.zoom_level = 1.0
            self.pan_x = 0
            self.pan_y = 0
            
            self._update_display()
            self._update_status(f"Loaded: {file_path.name}")
            
            if self.properties_visible:
                self._update_properties()
                
        except Exception as e:
            logger.error(f"Failed to load image {file_path}: {e}")
            self._update_status(f"Error loading image: {e}")
    
    def _update_display(self):
        """Update the canvas with the current image at current zoom/pan"""
        if not self.original_image:
            return
        
        # Calculate display size
        width = int(self.original_image.width * self.zoom_level)
        height = int(self.original_image.height * self.zoom_level)
        
        # Resize image
        if self.zoom_level == 1.0:
            self.display_image = self.original_image
        else:
            # Use LANCZOS for both scaling directions for best quality
            # Game textures benefit from LANCZOS which preserves sharp edges
            self.display_image = self.original_image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(self.display_image)
        
        # Update canvas
        self.canvas.delete("all")
        
        # Calculate position (center image + pan offset)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        x = (canvas_width - width) // 2 + self.pan_x
        y = (canvas_height - height) // 2 + self.pan_y
        
        self.image_on_canvas = self.canvas.create_image(x, y, anchor="nw", image=photo)
        
        # Keep a reference to prevent garbage collection
        self.canvas.image = photo
        
        # Update zoom label
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
    
    def _zoom_in(self):
        """Zoom in"""
        self.zoom_level *= 1.2
        if self.zoom_level > 10.0:
            self.zoom_level = 10.0
        self._update_display()
    
    def _zoom_out(self):
        """Zoom out"""
        self.zoom_level /= 1.2
        if self.zoom_level < 0.1:
            self.zoom_level = 0.1
        self._update_display()
    
    def _reset_view(self):
        """Reset zoom and pan to defaults"""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._update_display()
    
    def _fit_to_window(self):
        """Fit image to window size"""
        if not self.original_image:
            return
        
        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Calculate zoom level to fit
        zoom_w = canvas_width / self.original_image.width
        zoom_h = canvas_height / self.original_image.height
        
        # Use the smaller zoom to fit entirely
        self.zoom_level = min(zoom_w, zoom_h) * 0.95  # 95% to leave some padding
        self.pan_x = 0
        self.pan_y = 0
        self._update_display()
    
    def _actual_size(self):
        """Show image at actual size (1:1)"""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._update_display()
    
    def _export_image(self):
        """Export current texture to a different format"""
        if not self.current_file or not self.original_image:
            return
        
        try:
            from tkinter import filedialog
            
            # Suggest filename
            default_name = self.current_file.stem + "_exported"
            
            # Ask for save location
            file_types = [
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("BMP files", "*.bmp"),
                ("TIFF files", "*.tif"),
                ("All files", "*.*")
            ]
            
            save_path = filedialog.asksaveasfilename(
                title="Export Texture",
                defaultextension=".png",
                initialfile=default_name,
                filetypes=file_types
            )
            
            if save_path:
                # Save the original image (not the displayed/zoomed one)
                self.original_image.save(save_path)
                self._update_status(f"Exported to: {Path(save_path).name}")
                logger.info(f"Exported texture to {save_path}")
                
        except Exception as e:
            logger.error(f"Failed to export image: {e}")
            self._update_status(f"Export failed: {e}")
    
    def _mouse_wheel_zoom(self, event):
        """Zoom with mouse wheel"""
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
    
    def _start_pan(self, event):
        """Start panning"""
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.config(cursor="fleur")
    
    def _do_pan(self, event):
        """Pan the image"""
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            
            self.pan_x += dx
            self.pan_y += dy
            
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            
            self._update_display()
    
    def _end_pan(self, event):
        """End panning"""
        self.is_panning = False
        self.canvas.config(cursor="")
    
    def _show_previous(self):
        """Show previous image in the list"""
        if not self.file_list:
            return
        
        self.current_index = (self.current_index - 1) % len(self.file_list)
        self.current_file = self.file_list[self.current_index]
        self._load_image(self.current_file)
        self._update_window_title()
    
    def _show_next(self):
        """Show next image in the list"""
        if not self.file_list:
            return
        
        self.current_index = (self.current_index + 1) % len(self.file_list)
        self.current_file = self.file_list[self.current_index]
        self._load_image(self.current_file)
        self._update_window_title()
    
    def _update_window_title(self):
        """Update window title with current file info"""
        if self.current_file:
            title = f"Preview: {self.current_file.name} ({self.current_index + 1}/{len(self.file_list)})"
            self.preview_window.title(title)
    
    def _update_status(self, message: str):
        """Update status bar message"""
        if self.status_label:
            self.status_label.configure(text=message)
    
    def _get_sibling_textures(self, file_path: Path) -> List[Path]:
        """Get all texture files in the same directory"""
        if not file_path.exists():
            return [file_path]
        
        parent_dir = file_path.parent
        texture_extensions = {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga'}
        
        textures = []
        try:
            for item in parent_dir.iterdir():
                if item.is_file() and item.suffix.lower() in texture_extensions:
                    textures.append(item)
        except Exception as e:
            logger.warning(f"Failed to list sibling textures: {e}")
            return [file_path]
        
        # Sort by name
        textures.sort(key=lambda x: x.name.lower())
        
        return textures if textures else [file_path]
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def close(self):
        """Close the preview window"""
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.destroy()