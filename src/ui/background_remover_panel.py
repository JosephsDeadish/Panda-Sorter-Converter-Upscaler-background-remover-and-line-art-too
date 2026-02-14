"""
Background Remover UI Panel
Provides UI for AI-based background removal with edge refinement controls,
live preview, alpha presets, archive support, and processing queue
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional, Callable
import logging
from PIL import Image, ImageTk
import zipfile
import threading

from src.tools.background_remover import BackgroundRemover, check_dependencies, AlphaPresets
from src.tools.object_remover import ObjectRemover
from src.ui.live_preview_widget import LivePreviewWidget
from src.ui.archive_queue_widgets import ArchiveSettingsWidget, ProcessingQueue, OutputMode
from src.utils.archive_handler import ArchiveHandler

# Try to import SVG icon helper
try:
    from src.utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    load_icon = None
    SVG_ICONS_AVAILABLE = False
    logger.warning("SVG icons not available for Background Remover Panel")

try:
    from src.features.tutorial_system import WidgetTooltip
    TOOLTIPS_AVAILABLE = True
except ImportError:
    WidgetTooltip = None
    TOOLTIPS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Supported image file extensions
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}


class BackgroundRemoverPanel(ctk.CTkFrame):
    """
    UI panel for background removal operations with one-click processing,
    batch support, and edge refinement controls.
    """
    
    def __init__(self, master, unlockables_system=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Initialize background remover and object remover
        self.remover = BackgroundRemover()
        self.object_remover = ObjectRemover()
        self.archive_handler = ArchiveHandler()
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.processing_thread = None
        self.current_preset = None
        
        # Store unlockables system for tooltips
        self.unlockables_system = unlockables_system
        self._tooltips = []
        
        # Mode tracking
        self.current_mode = "background"  # "background" or "object"
        
        # Object remover state
        self.painting_enabled = False
        self.eraser_mode = False
        self.brush_size = 20
        self.brush_opacity = 80  # 0-100%
        self.selection_tool = "brush"  # "brush", "rectangle", "lasso", "wand"
        self.highlight_color = (255, 0, 0)  # Red
        self.canvas_image = None
        self.canvas_photo = None
        self.last_paint_x = None
        self.last_paint_y = None
        self.paint_strokes = []  # For undo functionality
        self.paint_redo_stack = []  # For redo functionality
        self.current_stroke = []
        
        # Selection tool state
        self.rect_start = None
        self.lasso_points = []
        self.wand_tolerance = 30
        
        self._create_widgets()
        self._check_availability()
        
        # Load first file for preview if any
        if self.selected_files:
            self.preview.load_image(self.selected_files[0])
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="🎭 AI Background & Object Remover",
            font=("Arial Bold", 18)
        )
        title_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            self,
            text="One-click subject isolation with transparent PNG export",
            font=("Arial", 12),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Mode Toggle Frame
        mode_frame = ctk.CTkFrame(self)
        mode_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(mode_frame, text="Mode:", font=("Arial Bold", 12)).pack(side="left", padx=10, pady=5)
        
        self.mode_var = ctk.StringVar(value="background")
        self.bg_remover_radio = ctk.CTkRadioButton(
            mode_frame,
            text="🎭 Background Remover",
            variable=self.mode_var,
            value="background",
            command=self._on_mode_change
        )
        self.bg_remover_radio.pack(side="left", padx=5)
        
        self.obj_remover_radio = ctk.CTkRadioButton(
            mode_frame,
            text="🎯 Object Remover",
            variable=self.mode_var,
            value="object",
            command=self._on_mode_change
        )
        self.obj_remover_radio.pack(side="left", padx=5)
        
        # Status frame
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Checking dependencies...",
            font=("Arial", 11)
        )
        self.status_label.pack(pady=5)
        
        # File selection frame
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(file_frame, text="📁 Input Files:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        btn_frame = ctk.CTkFrame(file_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.select_files_btn = ctk.CTkButton(
            btn_frame,
            text="Select Images",
            command=self._select_files,
            width=120
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("file_open_animated", (20, 20))
            if icon:
                self.select_files_btn.configure(image=icon, compound="left")
        self.select_files_btn.pack(side="left", padx=5)
        
        self.select_folder_btn = ctk.CTkButton(
            btn_frame,
            text="Select Folder",
            command=self._select_folder,
            width=120
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("folder_open_animated", (20, 20))
            if icon:
                self.select_folder_btn.configure(image=icon, compound="left")
        self.select_folder_btn.pack(side="left", padx=5)
        
        self.select_archive_btn = ctk.CTkButton(
            btn_frame,
            text="Select Archive",
            command=self._select_archive,
            width=120
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("package_animated", (20, 20))
            if icon:
                self.select_archive_btn.configure(image=icon, compound="left")
        self.select_archive_btn.pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear Selection",
            command=self._clear_selection,
            width=120,
            fg_color="gray40"
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("trash_empty_animated", (18, 18))
            if icon:
                self.clear_btn.configure(image=icon, compound="left")
        self.clear_btn.pack(side="left", padx=5)
        
        # File list
        self.file_list_label = ctk.CTkLabel(
            file_frame,
            text="No files selected",
            font=("Arial", 10),
            text_color="gray"
        )
        self.file_list_label.pack(anchor="w", padx=10, pady=5)
        
        # Output directory frame
        output_frame = ctk.CTkFrame(self)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(output_frame, text="📂 Output Directory:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        output_btn_frame = ctk.CTkFrame(output_frame)
        output_btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.select_output_btn = ctk.CTkButton(
            output_btn_frame,
            text="Select Output Folder",
            command=self._select_output_directory,
            width=200
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("folder_open_animated", (20, 20))
            if icon:
                self.select_output_btn.configure(image=icon, compound="left")
        self.select_output_btn.pack(side="left", padx=5)
        
        self.output_label = ctk.CTkLabel(
            output_btn_frame,
            text="(Same as input)",
            font=("Arial", 10),
            text_color="gray"
        )
        self.output_label.pack(side="left", padx=10)
        
        # Object Remover Controls (hidden by default)
        self.object_controls_frame = ctk.CTkFrame(self)
        
        ctk.CTkLabel(self.object_controls_frame, text="🎨 Object Remover Tools:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Brush controls
        brush_frame = ctk.CTkFrame(self.object_controls_frame)
        brush_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(brush_frame, text="Brush Size:", width=100).pack(side="left", padx=5)
        
        self.brush_slider = ctk.CTkSlider(
            brush_frame,
            from_=5,
            to=50,
            number_of_steps=45,
            command=self._on_brush_size_change
        )
        self.brush_slider.set(20)
        self.brush_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.brush_size_label = ctk.CTkLabel(brush_frame, text="20px", width=50)
        self.brush_size_label.pack(side="left", padx=5)
        
        # Brush opacity control
        opacity_frame = ctk.CTkFrame(self.object_controls_frame)
        opacity_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(opacity_frame, text="Brush Opacity:", width=100).pack(side="left", padx=5)
        
        self.opacity_slider = ctk.CTkSlider(
            opacity_frame,
            from_=10,
            to=100,
            number_of_steps=90,
            command=self._on_opacity_change
        )
        self.opacity_slider.set(80)
        self.opacity_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.opacity_label = ctk.CTkLabel(opacity_frame, text="80%", width=50)
        self.opacity_label.pack(side="left", padx=5)
        
        # Color picker
        color_frame = ctk.CTkFrame(self.object_controls_frame)
        color_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(color_frame, text="Highlight Color:", width=100).pack(side="left", padx=5)
        
        self.color_red_btn = ctk.CTkButton(color_frame, text="🔴 Red", command=lambda: self._set_color((255, 0, 0)), width=80)
        self.color_red_btn.pack(side="left", padx=2)
        
        self.color_green_btn = ctk.CTkButton(color_frame, text="🟢 Green", command=lambda: self._set_color((0, 255, 0)), width=80)
        self.color_green_btn.pack(side="left", padx=2)
        
        self.color_blue_btn = ctk.CTkButton(color_frame, text="🔵 Blue", command=lambda: self._set_color((0, 0, 255)), width=80)
        self.color_blue_btn.pack(side="left", padx=2)
        
        self.color_yellow_btn = ctk.CTkButton(color_frame, text="🟡 Yellow", command=lambda: self._set_color((255, 255, 0)), width=80)
        self.color_yellow_btn.pack(side="left", padx=2)
        
        # Selection tools
        selection_frame = ctk.CTkFrame(self.object_controls_frame)
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(selection_frame, text="Selection Tool:", width=100).pack(side="left", padx=5)
        
        self.brush_tool_btn = ctk.CTkButton(
            selection_frame,
            text="🖌️ Brush",
            command=lambda: self._set_selection_tool("brush"),
            width=100,
            fg_color="#1f538d"
        )
        self.brush_tool_btn.pack(side="left", padx=2)
        
        self.rect_tool_btn = ctk.CTkButton(
            selection_frame,
            text="⬜ Rectangle",
            command=lambda: self._set_selection_tool("rectangle"),
            width=100
        )
        self.rect_tool_btn.pack(side="left", padx=2)
        
        self.lasso_tool_btn = ctk.CTkButton(
            selection_frame,
            text="✂️ Lasso",
            command=lambda: self._set_selection_tool("lasso"),
            width=100
        )
        self.lasso_tool_btn.pack(side="left", padx=2)
        
        self.wand_tool_btn = ctk.CTkButton(
            selection_frame,
            text="🪄 Magic Wand",
            command=lambda: self._set_selection_tool("wand"),
            width=120
        )
        self.wand_tool_btn.pack(side="left", padx=2)
        
        # Tool buttons
        tool_frame = ctk.CTkFrame(self.object_controls_frame)
        tool_frame.pack(fill="x", padx=10, pady=5)
        
        self.paint_toggle_btn = ctk.CTkButton(
            tool_frame,
            text="🖌️ Start Painting",
            command=self._toggle_painting,
            width=120
        )
        self.paint_toggle_btn.pack(side="left", padx=5)
        
        self.eraser_btn = ctk.CTkButton(
            tool_frame,
            text="🧹 Eraser",
            command=self._toggle_eraser,
            width=100
        )
        self.eraser_btn.pack(side="left", padx=5)
        
        self.undo_paint_btn = ctk.CTkButton(
            tool_frame,
            text="↶ Undo",
            command=self._undo_paint_stroke,
            width=80
        )
        self.undo_paint_btn.pack(side="left", padx=5)
        
        self.redo_paint_btn = ctk.CTkButton(
            tool_frame,
            text="↷ Redo",
            command=self._redo_paint_stroke,
            width=80
        )
        self.redo_paint_btn.pack(side="left", padx=5)
        
        self.clear_mask_btn = ctk.CTkButton(
            tool_frame,
            text="🗑️ Clear All",
            command=self._clear_mask,
            width=100,
            fg_color="gray40"
        )
        self.clear_mask_btn.pack(side="left", padx=5)
        
        # Remove object button
        remove_btn_frame = ctk.CTkFrame(self.object_controls_frame)
        remove_btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.remove_object_btn = ctk.CTkButton(
            remove_btn_frame,
            text="🎯 Remove Highlighted Object",
            command=self._remove_object,
            height=35,
            font=("Arial Bold", 12),
            fg_color="#DC2626",
            hover_color="#991B1B"
        )
        self.remove_object_btn.pack(fill="x", padx=5, pady=5)
        
        self.undo_removal_btn = ctk.CTkButton(
            remove_btn_frame,
            text="↶ Undo Removal",
            command=self._undo_removal,
            width=150
        )
        self.undo_removal_btn.pack(side="left", padx=5)
        
        self.redo_removal_btn = ctk.CTkButton(
            remove_btn_frame,
            text="↷ Redo Removal",
            command=self._redo_removal,
            width=150
        )
        self.redo_removal_btn.pack(side="left", padx=5)
        
        # Settings frame (for background remover mode)
        self.bg_settings_frame = ctk.CTkFrame(self)
        self.bg_settings_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.bg_settings_frame, text="⚙️ Settings:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Alpha Preset Selection
        preset_frame = ctk.CTkFrame(self.bg_settings_frame)
        preset_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(preset_frame, text="🎯 Alpha Preset:", width=120).pack(side="left", padx=5)
        
        preset_names = [p.name for p in AlphaPresets.get_all_presets()]
        self.preset_var = ctk.StringVar(value="Gaming Assets")
        self.preset_menu = ctk.CTkOptionMenu(
            preset_frame,
            variable=self.preset_var,
            values=preset_names,
            command=self._on_preset_change
        )
        self.preset_menu.pack(side="left", fill="x", expand=True, padx=5)
        
        # Info button for preset
        self.preset_info_btn = ctk.CTkButton(
            preset_frame,
            text="ℹ️",
            width=30,
            command=self._show_preset_info,
            fg_color="transparent",
            hover_color="gray30"
        )
        self.preset_info_btn.pack(side="left", padx=2)
        
        # Preset description
        self.preset_desc_label = ctk.CTkLabel(
            self.bg_settings_frame,
            text="",
            font=("Arial", 9),
            text_color="gray",
            wraplength=600,
            anchor="w"
        )
        self.preset_desc_label.pack(fill="x", padx=10, pady=(0, 5))
        
        # Initialize with default preset
        self._on_preset_change("Gaming Assets")
        
        # Edge refinement slider
        edge_frame = ctk.CTkFrame(self.bg_settings_frame)
        edge_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(edge_frame, text="Edge Refinement:", width=120).pack(side="left", padx=5)
        
        self.edge_slider = ctk.CTkSlider(
            edge_frame,
            from_=0.0,
            to=1.0,
            number_of_steps=20,
            command=self._on_edge_refinement_change
        )
        self.edge_slider.set(0.5)
        self.edge_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.edge_value_label = ctk.CTkLabel(edge_frame, text="50%", width=50)
        self.edge_value_label.pack(side="left", padx=5)
        
        # Model selection
        model_frame = ctk.CTkFrame(self.bg_settings_frame)
        model_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(model_frame, text="🤖 AI Model:", width=120).pack(side="left", padx=5)
        
        self.model_var = ctk.StringVar(value="u2net")
        self.model_menu = ctk.CTkOptionMenu(
            model_frame,
            variable=self.model_var,
            values=self.remover.get_supported_models(),
            command=self._on_model_change
        )
        self.model_menu.pack(side="left", fill="x", expand=True, padx=5)
        
        # Alpha matting checkbox
        self.alpha_matting_var = ctk.BooleanVar(value=False)
        self.alpha_matting_check = ctk.CTkCheckBox(
            self.bg_settings_frame,
            text="✨ Enable Alpha Matting (Better edges, slower)",
            variable=self.alpha_matting_var,
            command=self._update_preview
        )
        self.alpha_matting_check.pack(anchor="w", padx=10, pady=5)
        
        # Archive settings
        self.archive_settings = ArchiveSettingsWidget(self)
        self.archive_settings.pack(fill="x", padx=10, pady=5)
        
        # Live Preview
        self.preview = LivePreviewWidget(self)
        self.preview.pack(fill="both", expand=True, padx=10, pady=5)
        self.preview.set_processing_function(self._process_preview_image)
        
        # Processing Queue
        self.queue = ProcessingQueue(self)
        self.queue.pack(fill="both", expand=True, padx=10, pady=5)
        self.queue.set_process_callback(self._process_single_file)
        
        # Progress frame (for non-queue processing)
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=("Arial", 10)
        )
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        # Action buttons
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        # Add to Queue button
        self.add_to_queue_btn = ctk.CTkButton(
            action_frame,
            text="➕ Add to Queue",
            command=self._add_to_queue,
            height=35,
            font=("Arial Bold", 12),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.add_to_queue_btn.pack(fill="x", padx=10, pady=2)
        
        self.process_btn = ctk.CTkButton(
            action_frame,
            text="🚀 Process Now",
            command=self._process_images,
            height=40,
            font=("Arial Bold", 14),
            fg_color="#2B7A0B",
            hover_color="#1F5808"
        )
        self.process_btn.pack(fill="x", padx=10, pady=5)
        
        self.cancel_btn = ctk.CTkButton(
            action_frame,
            text="Cancel",
            command=self._cancel_processing,
            height=30,
            fg_color="gray40",
            state="disabled"
        )
        self.cancel_btn.pack(fill="x", padx=10, pady=2)
        
        # Setup tooltips after all widgets are created
        self._setup_tooltips()
    
    def _setup_tooltips(self):
        """Setup tooltips for all controls using unlockables system."""
        if not TOOLTIPS_AVAILABLE or not self.unlockables_system:
            return
        
        # Get tooltip collection based on current mode
        bg_tooltips = []
        obj_tooltips = []
        
        # Try to get tooltips from unlockables system
        try:
            bg_collection = self.unlockables_system.tooltip_collections.get('background_remover')
            if bg_collection and bg_collection.unlocked:
                bg_tooltips = bg_collection.tooltips
            
            obj_collection = self.unlockables_system.tooltip_collections.get('object_remover')
            if obj_collection and obj_collection.unlocked:
                obj_tooltips = obj_collection.tooltips
        except AttributeError:
            logger.debug("Tooltip collections not available")
            return
        
        # Optimize: Pre-lowercase all tooltips once for faster matching
        bg_tooltips_lower = [(tip, tip.lower()) for tip in bg_tooltips]
        obj_tooltips_lower = [(tip, tip.lower()) for tip in obj_tooltips]
        
        # Helper to get tooltip by keyword (optimized with pre-lowercased list)
        def get_tooltip(tooltips_with_lower, keyword):
            keyword_lower = keyword.lower()
            for tooltip, tooltip_lower in tooltips_with_lower:
                if keyword_lower in tooltip_lower:
                    return tooltip
            return None
        
        # Background Remover tooltips
        if bg_tooltips_lower:
            # Mode toggle
            if hasattr(self, 'bg_remover_radio'):
                tooltip = get_tooltip(bg_tooltips_lower, "Mode toggle") or "Remove background to create transparent PNGs"
                self._tooltips.append(WidgetTooltip(self.bg_remover_radio, tooltip))
            
            # Preset dropdown
            if hasattr(self, 'preset_menu'):
                tooltip = get_tooltip(bg_tooltips_lower, "Preset selector") or "Choose a preset optimized for your image type"
                self._tooltips.append(WidgetTooltip(self.preset_menu, tooltip))
            
            # Edge slider
            if hasattr(self, 'edge_slider'):
                tooltip = get_tooltip(bg_tooltips_lower, "Edge refinement") or "Adjust edge feathering and refinement"
                self._tooltips.append(WidgetTooltip(self.edge_slider, tooltip))
            
            # Model dropdown
            if hasattr(self, 'model_menu'):
                tooltip = get_tooltip(bg_tooltips_lower, "AI model") or "Select the AI model for background removal"
                self._tooltips.append(WidgetTooltip(self.model_menu, tooltip))
            
            # Alpha matting checkbox
            if hasattr(self, 'alpha_matting_check'):
                tooltip = get_tooltip(bg_tooltips_lower, "Alpha matting") or "Enable for semi-transparent objects"
                self._tooltips.append(WidgetTooltip(self.alpha_matting_check, tooltip))
            
            # Archive button
            if hasattr(self, 'select_archive_btn'):
                tooltip = get_tooltip(bg_tooltips_lower, "Archive") or "Process ZIP/RAR archives without extracting"
                self._tooltips.append(WidgetTooltip(self.select_archive_btn, tooltip))
        
        # Object Remover tooltips
        if obj_tooltips_lower:
            # Mode toggle
            if hasattr(self, 'obj_remover_radio'):
                tooltip = get_tooltip(obj_tooltips_lower, "Mode toggle") or "Paint objects to remove them from images"
                self._tooltips.append(WidgetTooltip(self.obj_remover_radio, tooltip))
            
            # Brush size slider
            if hasattr(self, 'brush_slider'):
                tooltip = get_tooltip(obj_tooltips_lower, "Brush size") or "Adjust brush size for painting"
                self._tooltips.append(WidgetTooltip(self.brush_slider, tooltip))
            
            # Paint toggle button
            if hasattr(self, 'paint_toggle_btn'):
                tooltip = get_tooltip(obj_tooltips_lower, "brush") or "Toggle painting mode"
                self._tooltips.append(WidgetTooltip(self.paint_toggle_btn, tooltip))
            
            # Eraser button
            if hasattr(self, 'eraser_btn'):
                tooltip = get_tooltip(obj_tooltips_lower, "Eraser") or "Switch to eraser mode"
                self._tooltips.append(WidgetTooltip(self.eraser_btn, tooltip))
            
            # Opacity slider
            if hasattr(self, 'opacity_slider'):
                tooltip = get_tooltip(obj_tooltips_lower, "opacity") or "Adjust brush opacity for gradual masking"
                self._tooltips.append(WidgetTooltip(self.opacity_slider, tooltip))
            
            # Selection tools
            if hasattr(self, 'brush_tool_btn'):
                tooltip = get_tooltip(obj_tooltips_lower, "brush") or "Freehand brush tool for painting selection"
                self._tooltips.append(WidgetTooltip(self.brush_tool_btn, tooltip))
            
            if hasattr(self, 'rect_tool_btn'):
                tooltip = get_tooltip(obj_tooltips_lower, "Rectangle") or "Rectangle selection tool for quick area masking"
                self._tooltips.append(WidgetTooltip(self.rect_tool_btn, tooltip))
            
            if hasattr(self, 'lasso_tool_btn'):
                tooltip = get_tooltip(obj_tooltips_lower, "Lasso") or "Lasso tool for freehand polygon selection"
                self._tooltips.append(WidgetTooltip(self.lasso_tool_btn, tooltip))
            
            if hasattr(self, 'wand_tool_btn'):
                tooltip = get_tooltip(obj_tooltips_lower, "wand") or "Magic wand for color-based selection"
                self._tooltips.append(WidgetTooltip(self.wand_tool_btn, tooltip))
            
            # Undo/Redo buttons
            if hasattr(self, 'undo_paint_btn'):
                tooltip = get_tooltip(obj_tooltips_lower, "Undo") or "Undo last brush stroke"
                self._tooltips.append(WidgetTooltip(self.undo_paint_btn, tooltip))
            
            if hasattr(self, 'redo_paint_btn'):
                tooltip = get_tooltip(obj_tooltips_lower, "Redo") or "Redo previously undone stroke"
                self._tooltips.append(WidgetTooltip(self.redo_paint_btn, tooltip))
            
            # Remove object button
            if hasattr(self, 'remove_object_btn'):
                tooltip = get_tooltip(obj_tooltips_lower, "Remove button") or "Process the masked area to remove object"
                self._tooltips.append(WidgetTooltip(self.remove_object_btn, tooltip))
    
    def _check_availability(self):
        """Check if background removal is available."""
        deps = check_dependencies()
        
        if deps['rembg']:
            self.status_label.configure(
                text="✓ AI Background & Object Removal Available",
                text_color="green"
            )
        else:
            self.status_label.configure(
                text="✗ Background removal not available. Install with: pip install rembg",
                text_color="red"
            )
            self.process_btn.configure(state="disabled")
            self.select_files_btn.configure(state="disabled")
            self.select_folder_btn.configure(state="disabled")
            self.select_archive_btn.configure(state="disabled")
        
        if not deps['opencv']:
            logger.warning("OpenCV not available - advanced edge refinement disabled")
    
    def _on_mode_change(self):
        """Handle mode toggle between background and object remover."""
        mode = self.mode_var.get()
        self.current_mode = mode
        
        if mode == "background":
            # Show background remover settings
            self.bg_settings_frame.pack(fill="x", padx=10, pady=5)
            self.object_controls_frame.pack_forget()
            # Update preview function
            self.preview.set_processing_function(self._process_preview_image)
        else:
            # Show object remover controls
            self.bg_settings_frame.pack_forget()
            self.object_controls_frame.pack(fill="x", padx=10, pady=5)
            # Update preview to show mask overlay
            if self.selected_files:
                self._load_image_for_object_removal(self.selected_files[0])
    
    def _select_archive(self):
        """Open file dialog to select an archive."""
        archive = filedialog.askopenfilename(
            title="Select Archive",
            filetypes=[
                ("Archive files", "*.zip *.7z *.rar *.tar.gz *.tar *.tgz"),
                ("All files", "*.*")
            ]
        )
        
        if archive:
            archive_path = Path(archive)
            
            # Check if it's a valid archive
            if not self.archive_handler.is_archive(archive_path):
                messagebox.showerror("Invalid Archive", "The selected file is not a supported archive format.")
                return
            
            # Extract archive to temp directory
            self.progress_label.configure(text="Extracting archive...")
            self.progress_bar.set(0.5)
            
            def extract_archive():
                try:
                    extract_dir = self.archive_handler.extract_archive(
                        archive_path,
                        progress_callback=self._on_archive_progress
                    )
                    
                    if extract_dir:
                        # Find all images in extracted directory
                        self.selected_files = [
                            str(f) for f in extract_dir.rglob('*')
                            if f.suffix.lower() in IMAGE_EXTENSIONS
                        ]
                        
                        self._update_file_list()
                        self.progress_label.configure(
                            text=f"Extracted {len(self.selected_files)} images from archive",
                            text_color="green"
                        )
                        self.progress_bar.set(1.0)
                        
                        # Load first file for preview
                        if self.selected_files:
                            self.preview.load_image(self.selected_files[0])
                    else:
                        self.progress_label.configure(
                            text="Failed to extract archive",
                            text_color="red"
                        )
                        self.progress_bar.set(0)
                        
                except Exception as e:
                    logger.error(f"Error extracting archive: {e}")
                    messagebox.showerror("Extraction Error", f"Failed to extract archive: {e}")
                    self.progress_bar.set(0)
            
            thread = threading.Thread(target=extract_archive, daemon=True)
            thread.start()
    
    def _on_archive_progress(self, current: int, total: int, filename: str):
        """Handle archive extraction progress."""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Extracting {current}/{total}: {filename}")
    
    def _select_files(self):
        """Open file dialog to select images."""
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if files:
            self.selected_files = list(files)
            self._update_file_list()
            # Load first file for preview
            if self.selected_files:
                self.preview.load_image(self.selected_files[0])
    
    def _select_folder(self):
        """Open folder dialog to select all images in a folder."""
        folder = filedialog.askdirectory(title="Select Folder with Images")
        
        if folder:
            folder_path = Path(folder)
            self.selected_files = [
                str(f) for f in folder_path.iterdir()
                if f.suffix.lower() in IMAGE_EXTENSIONS
            ]
            self._update_file_list()
            # Load first file for preview
            if self.selected_files:
                self.preview.load_image(self.selected_files[0])
    
    def _clear_selection(self):
        """Clear selected files."""
        self.selected_files = []
        self._update_file_list()
        self.preview.clear()
    
    def _update_file_list(self):
        """Update the file list label."""
        count = len(self.selected_files)
        if count == 0:
            self.file_list_label.configure(text="No files selected", text_color="gray")
        elif count == 1:
            filename = Path(self.selected_files[0]).name
            self.file_list_label.configure(
                text=f"1 file selected: {filename}",
                text_color="white"
            )
        else:
            self.file_list_label.configure(
                text=f"{count} files selected",
                text_color="white"
            )
    
    def _on_preset_change(self, preset_name):
        """Handle preset selection change."""
        preset = AlphaPresets.get_preset_by_name(preset_name)
        if preset:
            self.current_preset = preset
            self.remover.apply_preset(preset)
            self.preset_desc_label.configure(text=f"📝 {preset.description}")
            
            # Update UI controls to match preset
            self.edge_slider.set(preset.edge_refinement)
            self.edge_value_label.configure(text=f"{int(preset.edge_refinement * 100)}%")
            
            # Update preview
            self._update_preview()
    
    def _show_preset_info(self):
        """Show detailed info about current preset."""
        if not self.current_preset:
            return
        
        preset = self.current_preset
        messagebox.showinfo(
            f"Preset: {preset.name}",
            f"{preset.description}\n\n"
            f"Why Use This:\n{preset.why_use}\n\n"
            f"Technical Settings:\n"
            f"• Foreground Threshold: {preset.foreground_threshold}\n"
            f"• Background Threshold: {preset.background_threshold}\n"
            f"• Erode Size: {preset.erode_size}\n"
            f"• Edge Refinement: {preset.edge_refinement * 100:.0f}%"
        )
    
    def _update_preview(self):
        """Update the live preview."""
        if hasattr(self, 'preview'):
            self.preview.apply_processing()
    
    def _process_preview_image(self, image: Image.Image) -> Image.Image:
        """Process image for preview."""
        if not self.remover.is_available():
            return image
        
        try:
            # Use current settings
            kwargs = {
                'alpha_matting': self.alpha_matting_var.get()
            }
            
            if self.current_preset:
                kwargs['alpha_matting_foreground_threshold'] = self.current_preset.foreground_threshold
                kwargs['alpha_matting_background_threshold'] = self.current_preset.background_threshold
                kwargs['alpha_matting_erode_size'] = self.current_preset.erode_size
            
            result = self.remover.remove_background(image, **kwargs)
            return result if result else image
        except Exception as e:
            logger.error(f"Preview processing failed: {e}")
            return image
    
    def _add_to_queue(self):
        """Add selected files to processing queue."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select images to add to queue")
            return
        
        # Determine output paths
        archive_settings = self.archive_settings.get_settings()
        output_dir = self.output_directory
        
        for input_path in self.selected_files:
            if output_dir:
                output_path = str(Path(output_dir) / f"{Path(input_path).stem}_nobg.png")
            else:
                output_path = str(Path(input_path).parent / f"{Path(input_path).stem}_nobg.png")
            
            self.queue.add_item(input_path, output_path)
        
        self.progress_label.configure(
            text=f"Added {len(self.selected_files)} items to queue",
            text_color="green"
        )
    
    def _process_single_file(self, input_path: str, output_path: str):
        """Process a single file (called by queue)."""
        kwargs = {
            'alpha_matting': self.alpha_matting_var.get()
        }
        
        if self.current_preset:
            kwargs['alpha_matting_foreground_threshold'] = self.current_preset.foreground_threshold
            kwargs['alpha_matting_background_threshold'] = self.current_preset.background_threshold
            kwargs['alpha_matting_erode_size'] = self.current_preset.erode_size
        
        result = self.remover.remove_background_from_file(input_path, output_path, **kwargs)
        
        if not result.success:
            raise Exception(result.error_message)
    
    def _select_output_directory(self):
        """Select output directory."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        
        if folder:
            self.output_directory = folder
            self.output_label.configure(
                text=f".../{Path(folder).name}",
                text_color="white"
            )
    
    def _on_edge_refinement_change(self, value):
        """Handle edge refinement slider change."""
        value = float(value)
        self.remover.set_edge_refinement(value)
        self.edge_value_label.configure(text=f"{int(value * 100)}%")
        # Update preview
        self._update_preview()
    
    def _on_model_change(self, model_name):
        """Handle model selection change."""
        success = self.remover.change_model(model_name)
        if not success:
            messagebox.showerror("Error", f"Failed to load model: {model_name}")
        else:
            # Update preview with new model
            self._update_preview()
    
    def _process_images(self):
        """Start background removal processing."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select images to process")
            return
        
        archive_settings = self.archive_settings.get_settings()
        
        # If archive mode, process and create archive
        if archive_settings['mode'] in [OutputMode.ZIP_ARCHIVE, OutputMode.SEVEN_ZIP_ARCHIVE]:
            self._process_to_archive(archive_settings)
        else:
            self._process_to_files()
    
    def _process_to_files(self):
        """Process images to individual files."""
        # Disable buttons
        self.process_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.select_files_btn.configure(state="disabled")
        self.select_folder_btn.configure(state="disabled")
        
        kwargs = {
            'alpha_matting': self.alpha_matting_var.get()
        }
        
        if self.current_preset:
            kwargs['alpha_matting_foreground_threshold'] = self.current_preset.foreground_threshold
            kwargs['alpha_matting_background_threshold'] = self.current_preset.background_threshold
            kwargs['alpha_matting_erode_size'] = self.current_preset.erode_size
        
        # Start async processing
        self.processing_thread = self.remover.batch_process_async(
            input_paths=self.selected_files,
            output_dir=self.output_directory,
            progress_callback=self._on_progress,
            completion_callback=self._on_completion,
            **kwargs
        )
    
    def _process_to_archive(self, archive_settings):
        """Process images and save to archive."""
        import tempfile
        
        self.process_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        
        def process_and_archive():
            try:
                # Create temp directory for processed files
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Process files
                    kwargs = {
                        'alpha_matting': self.alpha_matting_var.get()
                    }
                    
                    if self.current_preset:
                        kwargs['alpha_matting_foreground_threshold'] = self.current_preset.foreground_threshold
                        kwargs['alpha_matting_background_threshold'] = self.current_preset.background_threshold
                        kwargs['alpha_matting_erode_size'] = self.current_preset.erode_size
                    
                    results = self.remover.batch_process(
                        input_paths=self.selected_files,
                        output_dir=str(temp_path),
                        progress_callback=self._on_progress,
                        **kwargs
                    )
                    
                    # Create archive
                    archive_name = archive_settings['archive_name']
                    output_dir = self.output_directory or Path(self.selected_files[0]).parent
                    
                    if archive_settings['mode'] == OutputMode.ZIP_ARCHIVE:
                        archive_path = Path(output_dir) / f"{archive_name}.zip"
                        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED,
                                           compresslevel=archive_settings['compression_level']) as zf:
                            for result in results:
                                if result.success:
                                    zf.write(result.output_path, Path(result.output_path).name)
                    
                    # Call completion callback
                    self._on_completion(results)
                    
                    self.progress_label.configure(
                        text=f"Archive created: {archive_path.name}",
                        text_color="green"
                    )
            
            except Exception as e:
                logger.error(f"Archive processing failed: {e}")
                messagebox.showerror("Error", f"Archive processing failed: {e}")
            finally:
                self.process_btn.configure(state="normal")
                self.cancel_btn.configure(state="disabled")
        
        thread = threading.Thread(target=process_and_archive, daemon=True)
        thread.start()
    
    def _safe_ui_update(self, func, *args, **kwargs):
        """Thread-safe UI update using after() method."""
        try:
            self.after(0, func, *args, **kwargs)
        except Exception as e:
            logger.error(f"UI update failed: {e}")
    
    def _on_progress(self, current: int, total: int, filename: str):
        """Handle progress updates."""
        progress = current / total
        self.progress_bar.set(progress)
        self.progress_label.configure(
            text=f"Processing {current}/{total}: {filename}"
        )
    
    def _on_completion(self, results):
        """Handle processing completion."""
        # Re-enable buttons
        self.process_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.select_files_btn.configure(state="normal")
        self.select_folder_btn.configure(state="normal")
        
        # Show results
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_time = sum(r.processing_time for r in results)
        
        self.progress_label.configure(
            text=f"Complete! {successful} successful, {failed} failed ({total_time:.1f}s total)"
        )
        
        messagebox.showinfo(
            "Processing Complete",
            f"Background removal complete!\n\n"
            f"Successful: {successful}\n"
            f"Failed: {failed}\n"
            f"Total time: {total_time:.1f} seconds"
        )
    
    def _cancel_processing(self):
        """Cancel ongoing processing."""
        self.remover.cancel_processing()
        self.progress_label.configure(text="Cancelling...")
        self.cancel_btn.configure(state="disabled")
    
    # ========== Object Remover Methods ==========
    
    def _load_image_for_object_removal(self, image_path: str):
        """Load image for object removal mode."""
        if self.object_remover.load_image(image_path):
            # Show preview with mask overlay
            self._update_object_preview()
    
    def _update_object_preview(self):
        """Update preview with mask overlay for object remover."""
        if self.current_mode != "object":
            return
        
        overlay = self.object_remover.get_mask_overlay(
            color=self.highlight_color,
            alpha=128
        )
        
        if overlay:
            self.preview.update_processed(overlay)
    
    def _on_brush_size_change(self, value):
        """Handle brush size slider change."""
        self.brush_size = int(value)
        self.brush_size_label.configure(text=f"{self.brush_size}px")
    
    def _on_opacity_change(self, value):
        """Handle brush opacity slider change."""
        self.brush_opacity = int(value)
        self.opacity_label.configure(text=f"{self.brush_opacity}%")
    
    def _set_selection_tool(self, tool: str):
        """Set the current selection tool."""
        self.selection_tool = tool
        
        # Reset button colors
        default_color = None  # Default CTk color
        active_color = "#1f538d"
        
        self.brush_tool_btn.configure(fg_color=active_color if tool == "brush" else default_color)
        self.rect_tool_btn.configure(fg_color=active_color if tool == "rectangle" else default_color)
        self.lasso_tool_btn.configure(fg_color=active_color if tool == "lasso" else default_color)
        self.wand_tool_btn.configure(fg_color=active_color if tool == "wand" else default_color)
        
        # Reset tool-specific state
        self.rect_start = None
        self.lasso_points = []
        
        self.progress_label.configure(
            text=f"Selection tool: {tool.capitalize()}",
            text_color="gray"
        )
    
    def _set_color(self, color):
        """Set the highlight color."""
        self.highlight_color = color
        self._update_object_preview()
    
    def _is_canvas_available(self) -> bool:
        """Check if preview canvas is available for painting."""
        return hasattr(self.preview, 'canvas') and self.preview.canvas is not None
    
    def _toggle_painting(self):
        """Toggle painting mode on/off."""
        self.painting_enabled = not self.painting_enabled
        
        if self.painting_enabled:
            self.paint_toggle_btn.configure(text="🖌️ Stop Painting", fg_color="#DC2626")
            # Bind canvas events for painting
            if self._is_canvas_available():
                self.preview.canvas.bind("<B1-Motion>", self._on_paint_drag)
                self.preview.canvas.bind("<Button-1>", self._on_paint_click)
                self.preview.canvas.bind("<ButtonRelease-1>", self._on_paint_release)
        else:
            self.paint_toggle_btn.configure(text="🖌️ Start Painting", fg_color="#3B82F6")
            # Unbind canvas events
            if self._is_canvas_available():
                self.preview.canvas.unbind("<B1-Motion>")
                self.preview.canvas.unbind("<Button-1>")
                self.preview.canvas.unbind("<ButtonRelease-1>")
    
    def _toggle_eraser(self):
        """Toggle eraser mode."""
        self.eraser_mode = not self.eraser_mode
        
        if self.eraser_mode:
            self.eraser_btn.configure(text="🖌️ Paint", fg_color="#DC2626")
        else:
            self.eraser_btn.configure(text="🧹 Eraser", fg_color="#3B82F6")
    
    def _on_paint_click(self, event):
        """Handle paint click - tool-specific behavior."""
        if not self.painting_enabled or self.current_mode != "object":
            return
        
        if self.selection_tool == "brush":
            # Brush tool - start painting
            self.last_paint_x = event.x
            self.last_paint_y = event.y
            self.current_stroke = [(event.x, event.y)]
            
            # Paint at click position
            self.object_remover.paint_mask(event.x, event.y, self.brush_size, self.eraser_mode, self.brush_opacity)
            self._update_object_preview()
            
        elif self.selection_tool == "rectangle":
            # Rectangle tool - start selection
            self.rect_start = (event.x, event.y)
            
        elif self.selection_tool == "lasso":
            # Lasso tool - start freehand selection
            self.lasso_points = [(event.x, event.y)]
            
        elif self.selection_tool == "wand":
            # Magic wand - instant selection
            self.object_remover.magic_wand_select(
                event.x, event.y, 
                self.wand_tolerance, 
                self.eraser_mode, 
                self.brush_opacity
            )
            self._save_paint_state()
            self._update_object_preview()
    
    def _on_paint_drag(self, event):
        """Handle paint drag - tool-specific behavior."""
        if not self.painting_enabled or self.current_mode != "object":
            return
        
        if self.selection_tool == "brush":
            # Brush tool - continue painting
            if self.last_paint_x is not None and self.last_paint_y is not None:
                # Paint stroke from last position to current
                points = [(self.last_paint_x, self.last_paint_y), (event.x, event.y)]
                self.object_remover.paint_mask_stroke(points, self.brush_size, self.eraser_mode, self.brush_opacity)
                self.current_stroke.append((event.x, event.y))
            
            self.last_paint_x = event.x
            self.last_paint_y = event.y
            self._update_object_preview()
            
        elif self.selection_tool == "rectangle":
            # Rectangle tool - show preview (would need canvas overlay)
            pass  # Visual feedback could be added
            
        elif self.selection_tool == "lasso":
            # Lasso tool - add points to polygon
            self.lasso_points.append((event.x, event.y))
            # Could draw preview line
    
    def _on_paint_release(self, event):
        """Handle paint release - tool-specific behavior."""
        if not self.painting_enabled or self.current_mode != "object":
            return
        
        if self.selection_tool == "brush":
            # Brush tool - save stroke for undo
            if hasattr(self, 'current_stroke') and self.current_stroke:
                self._save_paint_state()
            
            self.last_paint_x = None
            self.last_paint_y = None
            self.current_stroke = []
            
        elif self.selection_tool == "rectangle":
            # Rectangle tool - complete selection
            if self.rect_start:
                x1, y1 = self.rect_start
                x2, y2 = event.x, event.y
                self.object_remover.paint_rectangle(x1, y1, x2, y2, self.eraser_mode, self.brush_opacity)
                self._save_paint_state()
                self._update_object_preview()
                self.rect_start = None
                
        elif self.selection_tool == "lasso":
            # Lasso tool - complete polygon
            if len(self.lasso_points) >= 3:
                self.object_remover.paint_polygon(self.lasso_points, self.eraser_mode, self.brush_opacity)
                self._save_paint_state()
                self._update_object_preview()
            self.lasso_points = []
    
    def _save_paint_state(self):
        """Save current paint state for undo."""
        self.paint_strokes.append({
            'mask': self.object_remover.mask.copy() if self.object_remover.mask else None
        })
        # Clear redo stack when new painting happens
        self.paint_redo_stack.clear()
    
    def _undo_paint_stroke(self):
        """Undo last paint stroke."""
        if self.paint_strokes:
            # Remove last stroke and add to redo stack
            stroke = self.paint_strokes.pop()
            self.paint_redo_stack.append(stroke)
            
            # Restore previous mask state if available
            if len(self.paint_strokes) > 0:
                prev_stroke = self.paint_strokes[-1]
                prev_mask = prev_stroke.get('mask')
                if prev_mask and hasattr(prev_mask, 'copy'):
                    try:
                        self.object_remover.mask = prev_mask.copy()
                    except (AttributeError, TypeError):
                        logger.warning("Failed to copy mask, clearing instead")
                        self.object_remover.clear_mask()
            else:
                # Clear mask if no strokes left
                self.object_remover.clear_mask()
            
            self._update_object_preview()
    
    def _redo_paint_stroke(self):
        """Redo paint stroke."""
        if self.paint_redo_stack:
            # Pop from redo stack and push to undo stack
            stroke = self.paint_redo_stack.pop()
            self.paint_strokes.append(stroke)
            
            # Restore the mask state from the stroke
            if 'mask' in stroke and stroke['mask'] is not None:
                self.object_remover.mask = stroke['mask'].copy()
                self._update_object_preview()
                self.progress_label.configure(text="Redo applied", text_color="gray")
        else:
            self.progress_label.configure(
                text="Nothing to redo",
                text_color="gray"
            )
    
    
    def _clear_mask(self):
        """Clear all mask painting."""
        self.object_remover.clear_mask()
        self.paint_strokes.clear()
        self._update_object_preview()
    
    def _remove_object(self):
        """Remove the highlighted object."""
        if self.current_mode != "object":
            return
        
        if not self.selected_files:
            messagebox.showwarning("No Image", "Please load an image first.")
            return
        
        # Show progress
        self.progress_label.configure(text="Removing object...")
        self.progress_bar.set(0.5)
        
        def remove_object():
            try:
                success = self.object_remover.remove_object()
                
                if success:
                    # Update preview with result
                    self._update_object_preview()
                    self.progress_label.configure(
                        text="Object removed successfully!",
                        text_color="green"
                    )
                    self.progress_bar.set(1.0)
                else:
                    self.progress_label.configure(
                        text="Failed to remove object",
                        text_color="red"
                    )
                    self.progress_bar.set(0)
            except Exception as e:
                logger.error(f"Error removing object: {e}")
                messagebox.showerror("Error", f"Failed to remove object: {e}")
                self.progress_bar.set(0)
        
        thread = threading.Thread(target=remove_object, daemon=True)
        thread.start()
    
    def _undo_removal(self):
        """Undo last object removal."""
        if self.object_remover.undo():
            self._update_object_preview()
            self.progress_label.configure(text="Undone last removal", text_color="white")
        else:
            messagebox.showinfo("Cannot Undo", "No more actions to undo.")
    
    def _redo_removal(self):
        """Redo object removal."""
        if self.object_remover.redo():
            self._update_object_preview()
            self.progress_label.configure(text="Redone removal", text_color="white")
        else:
            messagebox.showinfo("Cannot Redo", "No more actions to redo.")


def open_background_remover_dialog(parent=None):
    """Open background remover as a standalone dialog."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("AI Background Remover")
    dialog.geometry("700x800")
    
    if parent:
        dialog.transient(parent)
    
    panel = BackgroundRemoverPanel(dialog)
    panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    return dialog


if __name__ == "__main__":
    # Test the panel
    app = ctk.CTk()
    app.title("Background Remover Test")
    app.geometry("700x800")
    
    panel = BackgroundRemoverPanel(app)
    panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    app.mainloop()
