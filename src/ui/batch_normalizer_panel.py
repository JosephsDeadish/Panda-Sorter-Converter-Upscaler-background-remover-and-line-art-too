"""
Batch Normalizer UI Panel
Provides UI for batch format normalization with live preview
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional
import logging
from PIL import Image, ImageTk
import threading

from src.tools.batch_normalizer import (
    BatchFormatNormalizer, NormalizationSettings,
    PaddingMode, ResizeMode, OutputFormat, NamingPattern
)

# SVG icon support
try:
    from src.utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    SVG_ICONS_AVAILABLE = False
    logger.warning("SVG icon helper not available, using emoji fallback")

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}


class BatchNormalizerPanel(ctk.CTkFrame):
    """UI panel for batch format normalization."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.normalizer = BatchFormatNormalizer()
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.processing_thread = None
        self.preview_image = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📏 Batch Format Normalizer",
            font=("Arial Bold", 18)
        )
        title_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            self,
            text="Resize, pad, and normalize images to consistent format",
            font=("Arial", 12),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Main container with scrollable frame
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Settings (scrollable)
        left_frame = ctk.CTkScrollableFrame(main_container, width=400)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # File selection
        self._create_file_selection(left_frame)
        
        # Size settings
        self._create_size_settings(left_frame)
        
        # Format settings
        self._create_format_settings(left_frame)
        
        # Naming settings
        self._create_naming_settings(left_frame)
        
        # Action buttons
        self._create_action_buttons(left_frame)
        
        # Right side - Preview
        right_frame = ctk.CTkFrame(main_container)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(right_frame, text="👁️ Preview", font=("Arial Bold", 14)).pack(pady=10)
        
        # Preview canvas
        self.preview_label = ctk.CTkLabel(right_frame, text="No preview")
        self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Preview controls
        preview_controls = ctk.CTkFrame(right_frame)
        preview_controls.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            preview_controls,
            text="Update Preview",
            command=self._update_preview
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            preview_controls,
            text="Select Preview Image",
            command=self._select_preview_image
        ).pack(side="left", padx=5)
    
    def _create_file_selection(self, parent):
        """Create file selection section."""
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(file_frame, text="📁 Input Files", font=("Arial Bold", 14)).pack(pady=5)
        
        btn_frame = ctk.CTkFrame(file_frame)
        btn_frame.pack(fill="x", pady=5)
        
        # Select Files button with icon
        select_files_btn = ctk.CTkButton(
            btn_frame,
            text="Select Files",
            command=self._select_files,
            width=100
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("file_open_animated", (20, 20))
            if icon:
                select_files_btn.configure(image=icon, compound="left")
        select_files_btn.pack(side="left", padx=5)
        
        # Select Folder button with icon
        select_folder_btn = ctk.CTkButton(
            btn_frame,
            text="Select Folder",
            command=self._select_folder,
            width=100
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("folder_open_animated", (20, 20))
            if icon:
                select_folder_btn.configure(image=icon, compound="left")
        select_folder_btn.pack(side="left", padx=5)
        
        self.file_count_label = ctk.CTkLabel(file_frame, text="No files selected")
        self.file_count_label.pack(pady=5)
        
        # Output directory
        ctk.CTkLabel(file_frame, text="📂 Output Directory", font=("Arial Bold", 12)).pack(pady=(10, 5))
        
        output_btn_frame = ctk.CTkFrame(file_frame)
        output_btn_frame.pack(fill="x", pady=5)
        
        self.output_dir_label = ctk.CTkLabel(output_btn_frame, text="Not selected", 
                                             font=("Arial", 10), anchor="w")
        self.output_dir_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # Browse button with icon
        browse_btn = ctk.CTkButton(
            output_btn_frame,
            text="Browse",
            command=self._select_output_directory,
            width=80
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("folder_open_animated", (20, 20))
            if icon:
                browse_btn.configure(image=icon, compound="left")
        browse_btn.pack(side="right", padx=5)
    
    def _create_size_settings(self, parent):
        """Create size and resize settings."""
        size_frame = ctk.CTkFrame(parent)
        size_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(size_frame, text="📐 Size Settings", font=("Arial Bold", 14)).pack(pady=5)
        
        # Target dimensions
        dim_frame = ctk.CTkFrame(size_frame)
        dim_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(dim_frame, text="Target Size:").pack(side="left", padx=5)
        
        self.width_var = ctk.StringVar(value="1024")
        ctk.CTkEntry(dim_frame, textvariable=self.width_var, width=80).pack(side="left", padx=5)
        
        ctk.CTkLabel(dim_frame, text="x").pack(side="left")
        
        self.height_var = ctk.StringVar(value="1024")
        ctk.CTkEntry(dim_frame, textvariable=self.height_var, width=80).pack(side="left", padx=5)
        
        # Make square
        self.make_square_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            size_frame,
            text="Make Square (pad to square)",
            variable=self.make_square_var
        ).pack(pady=5, padx=10, anchor="w")
        
        # Resize mode
        resize_frame = ctk.CTkFrame(size_frame)
        resize_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(resize_frame, text="Resize Mode:").pack(side="left", padx=5)
        
        self.resize_mode_var = ctk.StringVar(value="fit")
        ctk.CTkOptionMenu(
            resize_frame,
            variable=self.resize_mode_var,
            values=["fit", "fill", "stretch", "none"],
            width=120
        ).pack(side="left", padx=5)
        
        # Padding mode
        padding_frame = ctk.CTkFrame(size_frame)
        padding_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(padding_frame, text="Padding:").pack(side="left", padx=5)
        
        self.padding_mode_var = ctk.StringVar(value="transparent")
        ctk.CTkOptionMenu(
            padding_frame,
            variable=self.padding_mode_var,
            values=["transparent", "black", "white", "blur", "edge_extend"],
            width=120
        ).pack(side="left", padx=5)
        
        # Center subject
        self.center_subject_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            size_frame,
            text="Center Subject Automatically",
            variable=self.center_subject_var
        ).pack(pady=5, padx=10, anchor="w")
    
    def _create_format_settings(self, parent):
        """Create format settings."""
        format_frame = ctk.CTkFrame(parent)
        format_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(format_frame, text="🎨 Format Settings", font=("Arial Bold", 14)).pack(pady=5)
        
        # Output format
        out_format_frame = ctk.CTkFrame(format_frame)
        out_format_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(out_format_frame, text="Output Format:").pack(side="left", padx=5)
        
        self.output_format_var = ctk.StringVar(value="PNG")
        ctk.CTkOptionMenu(
            out_format_frame,
            variable=self.output_format_var,
            values=["PNG", "JPEG", "WEBP", "TIFF"],
            width=100
        ).pack(side="left", padx=5)
        
        # Quality settings (for JPEG/WebP)
        quality_frame = ctk.CTkFrame(format_frame)
        quality_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(quality_frame, text="Quality (JPEG/WebP):").pack(side="left", padx=5)
        
        self.quality_var = ctk.IntVar(value=95)
        quality_slider = ctk.CTkSlider(
            quality_frame,
            from_=50,
            to=100,
            variable=self.quality_var,
            number_of_steps=50
        )
        quality_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.quality_label = ctk.CTkLabel(quality_frame, text="95")
        self.quality_label.pack(side="left", padx=5)
        quality_slider.configure(command=lambda v: self.quality_label.configure(text=f"{int(v)}"))
        
        # Alpha settings
        self.preserve_alpha_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            format_frame,
            text="Preserve Alpha Channel",
            variable=self.preserve_alpha_var
        ).pack(pady=5, padx=10, anchor="w")
        
        self.force_rgb_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            format_frame,
            text="Force RGB (remove alpha)",
            variable=self.force_rgb_var
        ).pack(pady=5, padx=10, anchor="w")
    
    def _create_naming_settings(self, parent):
        """Create naming settings."""
        naming_frame = ctk.CTkFrame(parent)
        naming_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(naming_frame, text="📝 Naming Pattern", font=("Arial Bold", 14)).pack(pady=5)
        
        # Pattern selection
        pattern_frame = ctk.CTkFrame(naming_frame)
        pattern_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(pattern_frame, text="Pattern:").pack(side="left", padx=5)
        
        self.naming_pattern_var = ctk.StringVar(value="original")
        ctk.CTkOptionMenu(
            pattern_frame,
            variable=self.naming_pattern_var,
            values=["original", "sequential", "timestamp", "descriptive"],
            width=120
        ).pack(side="left", padx=5)
        
        # Prefix
        prefix_frame = ctk.CTkFrame(naming_frame)
        prefix_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(prefix_frame, text="Prefix:").pack(side="left", padx=5)
        
        self.prefix_var = ctk.StringVar(value="image")
        ctk.CTkEntry(prefix_frame, textvariable=self.prefix_var, width=150).pack(side="left", padx=5)
    
    def _create_action_buttons(self, parent):
        """Create action buttons."""
        action_frame = ctk.CTkFrame(parent)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.normalize_button = ctk.CTkButton(
            action_frame,
            text="▶ Normalize Batch",
            command=self._normalize_batch,
            height=40,
            font=("Arial Bold", 14),
            fg_color="green"
        )
        self.normalize_button.pack(fill="x", pady=5)
        
        # Progress
        self.progress_label = ctk.CTkLabel(action_frame, text="")
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(action_frame)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
    
    def _select_files(self):
        """Select individual files."""
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(title="Select Images", filetypes=filetypes)
        if files:
            self.selected_files = list(files)
            self._update_file_count()
    
    def _select_folder(self):
        """Select folder and find all images."""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            folder_path = Path(folder)
            self.selected_files = []
            
            for ext in IMAGE_EXTENSIONS:
                self.selected_files.extend([str(f) for f in folder_path.rglob(f"*{ext}")])
            
            self._update_file_count()
    
    def _select_output_directory(self):
        """Select output directory."""
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.output_directory = folder
            # Truncate long paths
            display_path = str(Path(folder).name)
            if len(display_path) > 30:
                display_path = display_path[:27] + "..."
            self.output_dir_label.configure(text=display_path)
    
    def _update_file_count(self):
        """Update file count label."""
        count = len(self.selected_files)
        if count == 0:
            self.file_count_label.configure(text="No files selected")
        elif count == 1:
            self.file_count_label.configure(text="1 file selected")
        else:
            self.file_count_label.configure(text=f"{count} files selected")
    
    def _select_preview_image(self):
        """Select image for preview."""
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
            ("All files", "*.*")
        ]
        
        file = filedialog.askopenfilename(title="Select Preview Image", filetypes=filetypes)
        if file:
            self.preview_image = file
            self._update_preview()
    
    def _get_settings(self) -> NormalizationSettings:
        """Get current settings from UI."""
        return NormalizationSettings(
            target_width=int(self.width_var.get()),
            target_height=int(self.height_var.get()),
            make_square=self.make_square_var.get(),
            resize_mode=ResizeMode(self.resize_mode_var.get()),
            padding_mode=PaddingMode(self.padding_mode_var.get()),
            center_subject=self.center_subject_var.get(),
            output_format=OutputFormat(self.output_format_var.get()),
            jpeg_quality=self.quality_var.get(),
            webp_quality=self.quality_var.get(),
            naming_pattern=NamingPattern(self.naming_pattern_var.get()),
            naming_prefix=self.prefix_var.get(),
            preserve_alpha=self.preserve_alpha_var.get(),
            force_rgb=self.force_rgb_var.get()
        )
    
    def _update_preview(self):
        """Update preview with current settings."""
        if not self.preview_image and self.selected_files:
            self.preview_image = self.selected_files[0]
        
        if not self.preview_image:
            messagebox.showwarning("No Image", "Please select an image for preview")
            return
        
        try:
            settings = self._get_settings()
            processed = self.normalizer.preview_settings(self.preview_image, settings)
            
            # Resize for display
            display_size = (400, 400)
            processed.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(processed)
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo  # Keep reference
            
        except Exception as e:
            logger.error(f"Error updating preview: {e}")
            messagebox.showerror("Error", f"Failed to update preview: {e}")
    
    def _normalize_batch(self):
        """Normalize batch of images."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to normalize")
            return
        
        if not self.output_directory:
            messagebox.showwarning("No Output", "Please select output directory")
            return
        
        # Disable button during processing
        self.normalize_button.configure(state="disabled")
        self.progress_bar.set(0)
        
        # Run in thread
        self.processing_thread = threading.Thread(target=self._run_normalization, daemon=True)
        self.processing_thread.start()
    
    def _run_normalization(self):
        """Run normalization in background thread."""
        try:
            settings = self._get_settings()
            
            def progress_callback(current, total, filename):
                progress = current / total
                self.after(0, lambda: self.progress_bar.set(progress))
                self.after(0, lambda: self.progress_label.configure(
                    text=f"Processing {current}/{total}: {filename}"
                ))
            
            # Normalize batch
            results = self.normalizer.normalize_batch(
                self.selected_files,
                self.output_directory,
                settings,
                progress_callback
            )
            
            # Count results
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            # Show results
            message = f"Normalization complete!\n\nSuccessful: {successful}\nFailed: {failed}"
            self.after(0, lambda: messagebox.showinfo("Complete", message))
            self.after(0, lambda: self.progress_label.configure(text="✓ Normalization complete"))
            
        except Exception as e:
            logger.error(f"Error normalizing batch: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Normalization failed: {e}"))
        
        finally:
            self.after(0, lambda: self.normalize_button.configure(state="normal"))
