"""
Line Art Converter UI Panel
Provides UI for converting images to line art and stencils
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional
import logging
from PIL import Image, ImageTk
import threading

from src.tools.lineart_converter import (
    LineArtConverter, LineArtSettings,
    ConversionMode, BackgroundMode, MorphologyOperation
)

# SVG icon support
try:
    from src.utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    SVG_ICONS_AVAILABLE = False
    logger.warning("SVG icon helper not available, using emoji fallback")

# Tooltip support
try:
    from src.features.tutorial_system import WidgetTooltip
    TOOLTIPS_AVAILABLE = True
except ImportError:
    WidgetTooltip = None
    TOOLTIPS_AVAILABLE = False

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}

# ── 10 most-common line-art presets (most popular first) ──────────────
LINEART_PRESETS = {
    "⭐ Clean Ink Lines": {
        "desc": "Crisp black ink lines — the go-to for most art & game textures",
        "mode": "pure_black", "threshold": 128, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 1.5, "sharpen": True,
        "sharpen_amount": 1.2, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
    },
    "✏️ Pencil Sketch": {
        "desc": "Soft graphite pencil look with tonal gradation",
        "mode": "sketch", "threshold": 128, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": False,
        "midtone_threshold": 200, "contrast": 1.2, "sharpen": False,
        "sharpen_amount": 1.0, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": False, "denoise_size": 2,
    },
    "🖊️ Bold Outlines": {
        "desc": "Thick, punchy outlines — great for stickers or cartoon style",
        "mode": "pure_black", "threshold": 140, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 180, "contrast": 2.0, "sharpen": True,
        "sharpen_amount": 1.5, "morphology": "dilate", "morph_iter": 2,
        "kernel": 3, "denoise": True, "denoise_size": 3,
    },
    "🔍 Fine Detail Lines": {
        "desc": "Thin, delicate lines preserving intricate detail",
        "mode": "adaptive", "threshold": 128, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 220, "contrast": 1.8, "sharpen": True,
        "sharpen_amount": 2.0, "morphology": "erode", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 1,
    },
    "💥 Comic Book Inks": {
        "desc": "High-contrast inks like professional comic book art",
        "mode": "pure_black", "threshold": 120, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 190, "contrast": 2.5, "sharpen": True,
        "sharpen_amount": 1.8, "morphology": "close", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 3,
    },
    "📖 Manga Lines": {
        "desc": "Clean adaptive lines suited for manga / anime styles",
        "mode": "adaptive", "threshold": 128, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 210, "contrast": 1.6, "sharpen": True,
        "sharpen_amount": 1.4, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
    },
    "🖍️ Coloring Book": {
        "desc": "Thick clean outlines with no inner detail — ready to color in",
        "mode": "edge_detect", "threshold": 128, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 1.4, "sharpen": False,
        "sharpen_amount": 1.0, "morphology": "dilate", "morph_iter": 3,
        "kernel": 5, "denoise": True, "denoise_size": 4,
    },
    "📐 Blueprint / Technical": {
        "desc": "Precise edge-detected lines for technical / architectural art",
        "mode": "edge_detect", "threshold": 128, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 1.0, "sharpen": True,
        "sharpen_amount": 1.5, "morphology": "none", "morph_iter": 1,
        "kernel": 3, "denoise": True, "denoise_size": 2,
    },
    "✂️ Stencil / Vinyl Cut": {
        "desc": "High-contrast 1-bit shapes — perfect for stencils & vinyl cutters",
        "mode": "stencil_1bit", "threshold": 128, "auto_threshold": True,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 200, "contrast": 2.0, "sharpen": False,
        "sharpen_amount": 1.0, "morphology": "close", "morph_iter": 2,
        "kernel": 5, "denoise": True, "denoise_size": 5,
    },
    "🪵 Woodcut / Linocut": {
        "desc": "Bold simplified shapes evoking hand-carved block prints",
        "mode": "threshold", "threshold": 100, "auto_threshold": False,
        "background": "white", "invert": False, "remove_midtones": True,
        "midtone_threshold": 180, "contrast": 2.8, "sharpen": False,
        "sharpen_amount": 1.0, "morphology": "close", "morph_iter": 2,
        "kernel": 7, "denoise": True, "denoise_size": 6,
    },
    "🖋️ Tattoo Stencil": {
        "desc": "High-contrast smooth outlines optimised for tattoo transfer stencils",
        "mode": "pure_black", "threshold": 135, "auto_threshold": False,
        "background": "transparent", "invert": False, "remove_midtones": True,
        "midtone_threshold": 195, "contrast": 2.2, "sharpen": True,
        "sharpen_amount": 1.6, "morphology": "close", "morph_iter": 2,
        "kernel": 3, "denoise": True, "denoise_size": 3,
    },
}

# Custom user presets are appended at runtime
_USER_CUSTOM_PRESETS: dict = {}

PRESET_NAMES = list(LINEART_PRESETS.keys())


class LineArtConverterPanel(ctk.CTkFrame):
    """UI panel for line art conversion."""
    
    def __init__(self, master, tooltip_manager=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.tooltip_manager = tooltip_manager
        self.converter = LineArtConverter()
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.processing_thread = None
        self.preview_image = None
        
        self._tooltips = []
        self._create_widgets()
        self._add_tooltips()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="✏️ Line Art / Stencil Converter",
            font=("Arial Bold", 18)
        )
        title_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            self,
            text="Convert images to pure black linework and 1-bit stencils",
            font=("Arial", 12),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Settings (scrollable)
        left_frame = ctk.CTkScrollableFrame(main_container, width=400)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # File selection
        self._create_file_selection(left_frame)
        
        # Conversion settings
        self._create_conversion_settings(left_frame)
        
        # Line modification settings
        self._create_line_modification_settings(left_frame)
        
        # Cleanup settings
        self._create_cleanup_settings(left_frame)
        
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

        self.export_preview_btn = ctk.CTkButton(
            preview_controls,
            text="📤 Export Preview",
            command=self._export_preview,
            fg_color="#2B7A0B", hover_color="#368B14"
        )
        self.export_preview_btn.pack(side="left", padx=5)
    
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
    
    def _create_conversion_settings(self, parent):
        """Create conversion settings."""
        conv_frame = ctk.CTkFrame(parent)
        conv_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(conv_frame, text="🎨 Conversion Settings", font=("Arial Bold", 14)).pack(pady=5)
        
        # ── Preset selector ──────────────────────────────────────
        preset_frame = ctk.CTkFrame(conv_frame)
        preset_frame.pack(fill="x", pady=(5, 2), padx=10)
        
        ctk.CTkLabel(preset_frame, text="Preset:", font=("Arial Bold", 12)).pack(side="left", padx=5)
        
        _default_preset = PRESET_NAMES[0] if PRESET_NAMES else ""
        self.preset_var = ctk.StringVar(value=_default_preset)
        self.preset_menu = ctk.CTkOptionMenu(
            preset_frame,
            variable=self.preset_var,
            values=PRESET_NAMES or ["(none)"],
            command=self._apply_preset,
            width=220
        )
        self.preset_menu.pack(side="left", padx=5)

        self.save_preset_btn = ctk.CTkButton(
            preset_frame, text="💾 Save as Preset",
            command=self._save_custom_preset, width=130
        )
        self.save_preset_btn.pack(side="left", padx=5)

        self.preset_desc_label = ctk.CTkLabel(
            conv_frame,
            text=LINEART_PRESETS.get(_default_preset, {}).get("desc", ""),
            font=("Arial", 11), text_color="gray", wraplength=360
        )
        self.preset_desc_label.pack(pady=(0, 8), padx=10, anchor="w")
        
        # ── Conversion mode ──────────────────────────────────────
        mode_frame = ctk.CTkFrame(conv_frame)
        mode_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(mode_frame, text="Mode:").pack(side="left", padx=5)
        
        self.mode_var = ctk.StringVar(value="pure_black")
        self.mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            variable=self.mode_var,
            values=["pure_black", "threshold", "stencil_1bit", "edge_detect", "adaptive", "sketch"],
            width=140
        )
        self.mode_menu.pack(side="left", padx=5)
        
        # Threshold
        threshold_frame = ctk.CTkFrame(conv_frame)
        threshold_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(threshold_frame, text="Threshold:").pack(side="left", padx=5)
        
        self.threshold_var = ctk.IntVar(value=128)
        self.threshold_slider = ctk.CTkSlider(
            threshold_frame,
            from_=0,
            to=255,
            variable=self.threshold_var,
            number_of_steps=255
        )
        self.threshold_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.threshold_label = ctk.CTkLabel(threshold_frame, text="128")
        self.threshold_label.pack(side="left", padx=5)
        self.threshold_slider.configure(command=lambda v: self.threshold_label.configure(text=f"{int(v)}"))
        
        # Auto threshold
        self.auto_threshold_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            conv_frame,
            text="Auto Threshold (Otsu's method)",
            variable=self.auto_threshold_var
        ).pack(pady=5, padx=10, anchor="w")
        
        # Background mode
        bg_frame = ctk.CTkFrame(conv_frame)
        bg_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(bg_frame, text="Background:").pack(side="left", padx=5)
        
        self.background_var = ctk.StringVar(value="transparent")
        ctk.CTkOptionMenu(
            bg_frame,
            variable=self.background_var,
            values=["transparent", "white", "black"],
            width=120
        ).pack(side="left", padx=5)
        
        # Invert
        self.invert_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            conv_frame,
            text="Invert Colors",
            variable=self.invert_var
        ).pack(pady=5, padx=10, anchor="w")
        
        # Remove midtones
        self.remove_midtones_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            conv_frame,
            text="Remove Midtones (pure black/white only)",
            variable=self.remove_midtones_var
        ).pack(pady=5, padx=10, anchor="w")
        
        # Midtone threshold
        midtone_frame = ctk.CTkFrame(conv_frame)
        midtone_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(midtone_frame, text="Midtone Threshold:").pack(side="left", padx=5)
        
        self.midtone_threshold_var = ctk.IntVar(value=200)
        midtone_slider = ctk.CTkSlider(
            midtone_frame,
            from_=128,
            to=255,
            variable=self.midtone_threshold_var,
            number_of_steps=127
        )
        midtone_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.midtone_label = ctk.CTkLabel(midtone_frame, text="200")
        self.midtone_label.pack(side="left", padx=5)
        midtone_slider.configure(command=lambda v: self.midtone_label.configure(text=f"{int(v)}"))
    
    def _create_line_modification_settings(self, parent):
        """Create line modification settings."""
        line_frame = ctk.CTkFrame(parent)
        line_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(line_frame, text="🔧 Line Modification", font=("Arial Bold", 14)).pack(pady=5)
        
        # Contrast boost
        contrast_frame = ctk.CTkFrame(line_frame)
        contrast_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(contrast_frame, text="Contrast Boost:").pack(side="left", padx=5)
        
        self.contrast_var = ctk.DoubleVar(value=1.0)
        self.contrast_slider = ctk.CTkSlider(
            contrast_frame,
            from_=0.5,
            to=3.0,
            variable=self.contrast_var,
            number_of_steps=25
        )
        self.contrast_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.contrast_label = ctk.CTkLabel(contrast_frame, text="1.0")
        self.contrast_label.pack(side="left", padx=5)
        self.contrast_slider.configure(command=lambda v: self.contrast_label.configure(text=f"{v:.1f}"))
        
        # Sharpen
        self.sharpen_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            line_frame,
            text="Sharpen Before Conversion",
            variable=self.sharpen_var
        ).pack(pady=5, padx=10, anchor="w")
        
        # Sharpen amount
        sharpen_frame = ctk.CTkFrame(line_frame)
        sharpen_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(sharpen_frame, text="Sharpen Amount:").pack(side="left", padx=5)
        
        self.sharpen_amount_var = ctk.DoubleVar(value=1.0)
        sharpen_slider = ctk.CTkSlider(
            sharpen_frame,
            from_=0.5,
            to=3.0,
            variable=self.sharpen_amount_var,
            number_of_steps=25
        )
        sharpen_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.sharpen_label = ctk.CTkLabel(sharpen_frame, text="1.0")
        self.sharpen_label.pack(side="left", padx=5)
        sharpen_slider.configure(command=lambda v: self.sharpen_label.configure(text=f"{v:.1f}"))
        
        # Morphology operation
        morph_frame = ctk.CTkFrame(line_frame)
        morph_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(morph_frame, text="Morphology:").pack(side="left", padx=5)
        
        self.morphology_var = ctk.StringVar(value="none")
        self.morphology_menu = ctk.CTkOptionMenu(
            morph_frame,
            variable=self.morphology_var,
            values=["none", "dilate", "erode", "close", "open"],
            width=100
        )
        self.morphology_menu.pack(side="left", padx=5)
        
        # Morphology iterations
        iter_frame = ctk.CTkFrame(line_frame)
        iter_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(iter_frame, text="Iterations:").pack(side="left", padx=5)
        
        self.morphology_iterations_var = ctk.IntVar(value=1)
        ctk.CTkSlider(
            iter_frame,
            from_=1,
            to=10,
            variable=self.morphology_iterations_var,
            number_of_steps=9
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        self.iter_label = ctk.CTkLabel(iter_frame, text="1")
        self.iter_label.pack(side="left", padx=5)
        
        # Kernel size
        kernel_frame = ctk.CTkFrame(line_frame)
        kernel_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(kernel_frame, text="Kernel Size:").pack(side="left", padx=5)
        
        self.kernel_size_var = ctk.IntVar(value=3)
        ctk.CTkOptionMenu(
            kernel_frame,
            variable=self.kernel_size_var,
            values=["3", "5", "7", "9"],
            width=80
        ).pack(side="left", padx=5)
    
    def _create_cleanup_settings(self, parent):
        """Create cleanup settings."""
        cleanup_frame = ctk.CTkFrame(parent)
        cleanup_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(cleanup_frame, text="🧹 Cleanup", font=("Arial Bold", 14)).pack(pady=5)
        
        # Denoise
        self.denoise_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            cleanup_frame,
            text="Remove Noise / Speckles",
            variable=self.denoise_var
        ).pack(pady=5, padx=10, anchor="w")
        
        # Denoise size
        denoise_frame = ctk.CTkFrame(cleanup_frame)
        denoise_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(denoise_frame, text="Min Feature Size:").pack(side="left", padx=5)
        
        self.denoise_size_var = ctk.IntVar(value=2)
        ctk.CTkSlider(
            denoise_frame,
            from_=1,
            to=10,
            variable=self.denoise_size_var,
            number_of_steps=9
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        self.denoise_label = ctk.CTkLabel(denoise_frame, text="2")
        self.denoise_label.pack(side="left", padx=5)
    
    def _create_action_buttons(self, parent):
        """Create action buttons."""
        action_frame = ctk.CTkFrame(parent)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.convert_button = ctk.CTkButton(
            action_frame,
            text="▶ Convert to Line Art",
            command=self._convert_batch,
            height=40,
            font=("Arial Bold", 14),
            fg_color="green"
        )
        self.convert_button.pack(fill="x", pady=5)
        
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
    
    def _apply_preset(self, preset_name: str):
        """Apply a preset's settings to all UI controls."""
        if preset_name not in LINEART_PRESETS:
            return
        p = LINEART_PRESETS[preset_name]
        self.preset_desc_label.configure(text=p["desc"])
        self.mode_var.set(p["mode"])
        self.threshold_var.set(p["threshold"])
        self.threshold_label.configure(text=str(p["threshold"]))
        self.auto_threshold_var.set(p["auto_threshold"])
        self.background_var.set(p["background"])
        self.invert_var.set(p["invert"])
        self.remove_midtones_var.set(p["remove_midtones"])
        self.midtone_threshold_var.set(p["midtone_threshold"])
        self.midtone_label.configure(text=str(p["midtone_threshold"]))
        self.contrast_var.set(p["contrast"])
        self.contrast_label.configure(text=f"{p['contrast']:.1f}")
        self.sharpen_var.set(p["sharpen"])
        self.sharpen_amount_var.set(p["sharpen_amount"])
        self.sharpen_label.configure(text=f"{p['sharpen_amount']:.1f}")
        self.morphology_var.set(p["morphology"])
        self.morphology_iterations_var.set(p["morph_iter"])
        self.iter_label.configure(text=str(p["morph_iter"]))
        self.kernel_size_var.set(p["kernel"])
        self.denoise_var.set(p["denoise"])
        self.denoise_size_var.set(p["denoise_size"])
        self.denoise_label.configure(text=str(p["denoise_size"]))

    def _save_custom_preset(self):
        """Save current settings as a named custom preset."""
        dialog = ctk.CTkInputDialog(
            text="Enter a name for your custom preset:",
            title="Save Custom Preset"
        )
        name = dialog.get_input()
        if not name or not name.strip():
            return
        name = f"⭐ {name.strip()}"
        preset = {
            "desc": f"Custom preset: {name}",
            "mode": self.mode_var.get(),
            "threshold": self.threshold_var.get(),
            "auto_threshold": self.auto_threshold_var.get(),
            "background": self.background_var.get(),
            "invert": self.invert_var.get(),
            "remove_midtones": self.remove_midtones_var.get(),
            "midtone_threshold": self.midtone_threshold_var.get(),
            "contrast": self.contrast_var.get(),
            "sharpen": self.sharpen_var.get(),
            "sharpen_amount": self.sharpen_amount_var.get(),
            "morphology": self.morphology_var.get(),
            "morph_iter": self.morphology_iterations_var.get(),
            "kernel": int(self.kernel_size_var.get()),
            "denoise": self.denoise_var.get(),
            "denoise_size": self.denoise_size_var.get(),
        }
        _USER_CUSTOM_PRESETS[name] = preset
        LINEART_PRESETS[name] = preset
        PRESET_NAMES.append(name)
        self.preset_menu.configure(values=PRESET_NAMES)
        self.preset_var.set(name)
        self.preset_desc_label.configure(text=preset["desc"])
        messagebox.showinfo("Saved", f"Preset '{name}' saved!")

    def _export_preview(self):
        """Export the currently previewed line art result to a file."""
        if not hasattr(self, '_last_preview_result') or self._last_preview_result is None:
            messagebox.showwarning("No Preview", "Update the preview first before exporting.")
            return
        filepath = filedialog.asksaveasfilename(
            title="Export Line Art Preview",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"),
                       ("BMP files", "*.bmp"), ("All files", "*.*")])
        if not filepath:
            return
        try:
            self._last_preview_result.save(filepath)
            messagebox.showinfo("Exported",
                                f"Line art exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")

    def _get_settings(self) -> LineArtSettings:
        """Get current settings from UI."""
        return LineArtSettings(
            mode=ConversionMode(self.mode_var.get()),
            threshold=self.threshold_var.get(),
            invert=self.invert_var.get(),
            background_mode=BackgroundMode(self.background_var.get()),
            remove_midtones=self.remove_midtones_var.get(),
            midtone_threshold=self.midtone_threshold_var.get(),
            morphology_operation=MorphologyOperation(self.morphology_var.get()),
            morphology_iterations=self.morphology_iterations_var.get(),
            morphology_kernel_size=int(self.kernel_size_var.get()),
            denoise=self.denoise_var.get(),
            denoise_size=self.denoise_size_var.get(),
            sharpen=self.sharpen_var.get(),
            sharpen_amount=self.sharpen_amount_var.get(),
            contrast_boost=self.contrast_var.get(),
            auto_threshold=self.auto_threshold_var.get()
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
            processed = self.converter.preview_settings(self.preview_image, settings)

            # Store full-resolution result for export
            self._last_preview_result = processed.copy()

            # Resize for display
            display_size = (400, 400)
            processed.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(processed)
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo
            
        except Exception as e:
            logger.error(f"Error updating preview: {e}")
            messagebox.showerror("Error", f"Failed to update preview: {e}")
    
    def _convert_batch(self):
        """Convert batch of images."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to convert")
            return
        
        if not self.output_directory:
            messagebox.showwarning("No Output", "Please select output directory")
            return
        
        # Disable button during processing
        self.convert_button.configure(state="disabled")
        self.progress_bar.set(0)
        
        # Run in thread
        self.processing_thread = threading.Thread(target=self._run_conversion, daemon=True)
        self.processing_thread.start()
    
    def _run_conversion(self):
        """Run conversion in background thread."""
        try:
            settings = self._get_settings()
            
            def progress_callback(current, total, filename):
                progress = current / total
                self.after(0, lambda: self.progress_bar.set(progress))
                self.after(0, lambda: self.progress_label.configure(
                    text=f"Converting {current}/{total}: {filename}"
                ))
            
            # Convert batch
            results = self.converter.convert_batch(
                self.selected_files,
                self.output_directory,
                settings,
                progress_callback
            )
            
            # Count results
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            # Show results
            message = f"Conversion complete!\n\nSuccessful: {successful}\nFailed: {failed}"
            self.after(0, lambda: messagebox.showinfo("Complete", message))
            self.after(0, lambda: self.progress_label.configure(text="✓ Conversion complete"))
            
        except Exception as e:
            logger.error(f"Error converting batch: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Conversion failed: {e}"))
        
        finally:
            self.after(0, lambda: self.convert_button.configure(state="normal"))

    def _add_tooltips(self):
        """Add mode-aware tooltips to widgets."""
        if not TOOLTIPS_AVAILABLE:
            return
        try:
            tm = self.tooltip_manager

            def _tt(widget_id, fallback):
                if tm:
                    text = tm.get_tooltip(widget_id)
                    if text:
                        return text
                return fallback

            if hasattr(self, 'preset_menu'):
                self._tooltips.append(WidgetTooltip(
                    self.preset_menu,
                    _tt('la_preset', "Pick a ready-made preset to instantly configure all settings for a common line art style"),
                    widget_id='la_preset', tooltip_manager=tm))
            if hasattr(self, 'convert_button'):
                self._tooltips.append(WidgetTooltip(
                    self.convert_button,
                    _tt('la_convert', "Convert images to clean line art renditions"),
                    widget_id='la_convert', tooltip_manager=tm))
            if hasattr(self, 'mode_menu'):
                self._tooltips.append(WidgetTooltip(
                    self.mode_menu,
                    _tt('la_mode', "Select the line art conversion algorithm"),
                    widget_id='la_mode', tooltip_manager=tm))
            if hasattr(self, 'threshold_slider'):
                self._tooltips.append(WidgetTooltip(
                    self.threshold_slider,
                    _tt('la_threshold', "Set the brightness threshold for black/white separation (0-255)"),
                    widget_id='la_threshold', tooltip_manager=tm))
            if hasattr(self, 'contrast_slider'):
                self._tooltips.append(WidgetTooltip(
                    self.contrast_slider,
                    _tt('la_contrast', "Boost contrast before conversion to strengthen line edges"),
                    widget_id='la_contrast', tooltip_manager=tm))
            if hasattr(self, 'morphology_menu'):
                self._tooltips.append(WidgetTooltip(
                    self.morphology_menu,
                    _tt('la_morphology', "Apply morphology operations to thicken or thin lines"),
                    widget_id='la_morphology', tooltip_manager=tm))
            if hasattr(self, 'save_preset_btn'):
                self._tooltips.append(WidgetTooltip(
                    self.save_preset_btn,
                    _tt('la_save_preset', "Save current settings as a reusable custom preset"),
                    widget_id='la_save_preset', tooltip_manager=tm))
            if hasattr(self, 'export_preview_btn'):
                self._tooltips.append(WidgetTooltip(
                    self.export_preview_btn,
                    _tt('la_export', "Export the previewed line art result to a file"),
                    widget_id='la_export', tooltip_manager=tm))
        except Exception as e:
            logger.error(f"Error adding tooltips to Line Art Converter Panel: {e}")
