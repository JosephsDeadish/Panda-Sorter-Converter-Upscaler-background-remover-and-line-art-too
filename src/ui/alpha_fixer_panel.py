"""
Alpha Fixer UI Panel
Provides UI for comprehensive alpha channel editing and fixing
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional
import logging
from PIL import Image, ImageTk
import numpy as np
import threading

from src.preprocessing.alpha_correction import AlphaCorrector, AlphaCorrectionPresets

# SVG icon support
try:
    from src.utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    SVG_ICONS_AVAILABLE = False
    logger.warning("SVG icon helper not available, using emoji fallback")

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}


class AlphaFixerPanel(ctk.CTkFrame):
    """UI panel for alpha channel fixing and enhancement."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.corrector = AlphaCorrector()
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.processing_thread = None
        self.preview_image = None
        self.current_image = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="⚡ Alpha Channel Fixer",
            font=("Arial Bold", 18)
        )
        title_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            self,
            text="Fix, enhance, and correct alpha channels with advanced tools",
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
        
        # Alpha correction presets
        self._create_correction_presets(left_frame)
        
        # De-fringing settings
        self._create_defringe_settings(left_frame)
        
        # Matte removal settings
        self._create_matte_removal_settings(left_frame)
        
        # Alpha edge settings
        self._create_alpha_edge_settings(left_frame)
        
        # Alpha morphology settings
        self._create_alpha_morphology_settings(left_frame)
        
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
            text="Load Preview",
            command=self._select_preview_image
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            preview_controls,
            text="Apply All Fixes",
            command=self._apply_all_preview
        ).pack(side="left", padx=5)
    
    def _create_file_selection(self, parent):
        """Create file selection section."""
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(file_frame, text="📁 Batch Processing", font=("Arial Bold", 14)).pack(pady=5)
        
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
    
    def _create_correction_presets(self, parent):
        """Create alpha correction preset settings."""
        preset_frame = ctk.CTkFrame(parent)
        preset_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(preset_frame, text="🎮 Alpha Correction Presets", font=("Arial Bold", 14)).pack(pady=5)
        
        # Preset selection
        self.preset_var = ctk.StringVar(value="none")
        preset_options = ["none"] + AlphaCorrectionPresets.list_presets()
        
        ctk.CTkOptionMenu(
            preset_frame,
            variable=self.preset_var,
            values=preset_options,
            width=200
        ).pack(pady=5, padx=10)
        
        ctk.CTkLabel(
            preset_frame,
            text="Apply platform-specific alpha corrections\n(PS2, PSP, GameCube, etc.)",
            font=("Arial", 10),
            text_color="gray",
            wraplength=350
        ).pack(pady=5, padx=10)
    
    def _create_defringe_settings(self, parent):
        """Create de-fringing settings."""
        defringe_frame = ctk.CTkFrame(parent)
        defringe_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(defringe_frame, text="🔧 De-Fringe (Remove Halos)", font=("Arial Bold", 14)).pack(pady=5)
        
        self.defringe_enabled_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            defringe_frame,
            text="Enable De-Fringing",
            variable=self.defringe_enabled_var
        ).pack(pady=5, padx=10, anchor="w")
        
        # Radius
        radius_frame = ctk.CTkFrame(defringe_frame)
        radius_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(radius_frame, text="Radius:").pack(side="left", padx=5)
        
        self.defringe_radius_var = ctk.IntVar(value=2)
        ctk.CTkSlider(
            radius_frame,
            from_=1,
            to=5,
            variable=self.defringe_radius_var,
            number_of_steps=4
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        self.defringe_radius_label = ctk.CTkLabel(radius_frame, text="2")
        self.defringe_radius_label.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            defringe_frame,
            text="Removes dark halos around transparent edges",
            font=("Arial", 10),
            text_color="gray"
        ).pack(pady=5, padx=10)
    
    def _create_matte_removal_settings(self, parent):
        """Create matte color removal settings."""
        matte_frame = ctk.CTkFrame(parent)
        matte_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(matte_frame, text="🎨 Matte Color Removal", font=("Arial Bold", 14)).pack(pady=5)
        
        self.matte_removal_enabled_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            matte_frame,
            text="Enable Matte Removal",
            variable=self.matte_removal_enabled_var
        ).pack(pady=5, padx=10, anchor="w")
        
        # Matte color selection
        color_frame = ctk.CTkFrame(matte_frame)
        color_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(color_frame, text="Matte Color:").pack(side="left", padx=5)
        
        self.matte_color_var = ctk.StringVar(value="white")
        ctk.CTkOptionMenu(
            color_frame,
            variable=self.matte_color_var,
            values=["white", "black", "gray"],
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            matte_frame,
            text="Remove background color bleed from semi-transparent pixels",
            font=("Arial", 10),
            text_color="gray",
            wraplength=350
        ).pack(pady=5, padx=10)
    
    def _create_alpha_edge_settings(self, parent):
        """Create alpha edge feathering settings."""
        edge_frame = ctk.CTkFrame(parent)
        edge_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(edge_frame, text="✨ Feather Alpha Edges", font=("Arial Bold", 14)).pack(pady=5)
        
        self.feather_enabled_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            edge_frame,
            text="Enable Feathering",
            variable=self.feather_enabled_var
        ).pack(pady=5, padx=10, anchor="w")
        
        # Radius
        radius_frame = ctk.CTkFrame(edge_frame)
        radius_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(radius_frame, text="Radius:").pack(side="left", padx=5)
        
        self.feather_radius_var = ctk.IntVar(value=2)
        ctk.CTkSlider(
            radius_frame,
            from_=1,
            to=10,
            variable=self.feather_radius_var,
            number_of_steps=9
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        self.feather_radius_label = ctk.CTkLabel(radius_frame, text="2")
        self.feather_radius_label.pack(side="left", padx=5)
        
        # Strength
        strength_frame = ctk.CTkFrame(edge_frame)
        strength_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(strength_frame, text="Strength:").pack(side="left", padx=5)
        
        self.feather_strength_var = ctk.DoubleVar(value=0.5)
        ctk.CTkSlider(
            strength_frame,
            from_=0.0,
            to=1.0,
            variable=self.feather_strength_var,
            number_of_steps=10
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        self.feather_strength_label = ctk.CTkLabel(strength_frame, text="0.5")
        self.feather_strength_label.pack(side="left", padx=5)
    
    def _create_alpha_morphology_settings(self, parent):
        """Create alpha morphology settings."""
        morph_frame = ctk.CTkFrame(parent)
        morph_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(morph_frame, text="📏 Alpha Dilation / Erosion", font=("Arial Bold", 14)).pack(pady=5)
        
        # Operation type
        op_frame = ctk.CTkFrame(morph_frame)
        op_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(op_frame, text="Operation:").pack(side="left", padx=5)
        
        self.morphology_op_var = ctk.StringVar(value="none")
        ctk.CTkOptionMenu(
            op_frame,
            variable=self.morphology_op_var,
            values=["none", "dilate", "erode"],
            width=100
        ).pack(side="left", padx=5)
        
        # Iterations
        iter_frame = ctk.CTkFrame(morph_frame)
        iter_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(iter_frame, text="Iterations:").pack(side="left", padx=5)
        
        self.morphology_iterations_var = ctk.IntVar(value=1)
        ctk.CTkSlider(
            iter_frame,
            from_=1,
            to=5,
            variable=self.morphology_iterations_var,
            number_of_steps=4
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        self.morphology_iter_label = ctk.CTkLabel(iter_frame, text="1")
        self.morphology_iter_label.pack(side="left", padx=5)
        
        # Kernel size
        kernel_frame = ctk.CTkFrame(morph_frame)
        kernel_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(kernel_frame, text="Kernel Size:").pack(side="left", padx=5)
        
        self.morphology_kernel_var = ctk.IntVar(value=3)
        ctk.CTkOptionMenu(
            kernel_frame,
            variable=self.morphology_kernel_var,
            values=["3", "5", "7"],
            width=80
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            morph_frame,
            text="Dilate: Expand transparent areas\nErode: Contract transparent areas",
            font=("Arial", 10),
            text_color="gray"
        ).pack(pady=5, padx=10)
    
    def _create_action_buttons(self, parent):
        """Create action buttons."""
        action_frame = ctk.CTkFrame(parent)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.process_button = ctk.CTkButton(
            action_frame,
            text="▶ Process Batch",
            command=self._process_batch,
            height=40,
            font=("Arial Bold", 14),
            fg_color="green"
        )
        self.process_button.pack(fill="x", pady=5)
        
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
            # Load image
            img = Image.open(file)
            self.current_image = np.array(img)
            
            # Display original
            self._display_preview(img)
    
    def _display_preview(self, img: Image.Image):
        """Display image in preview."""
        # Resize for display
        display_size = (400, 400)
        img_copy = img.copy()
        img_copy.thumbnail(display_size, Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img_copy)
        self.preview_label.configure(image=photo, text="")
        self.preview_label.image = photo
    
    def _apply_all_preview(self):
        """Apply all fixes to preview image."""
        if self.current_image is None:
            messagebox.showwarning("No Image", "Please load a preview image first")
            return
        
        try:
            result = self.current_image.copy()
            
            # Apply preset if selected
            preset_name = self.preset_var.get()
            if preset_name != "none":
                result, _ = self.corrector.correct_alpha(result, preset=preset_name)
            
            # Apply de-fringing
            if self.defringe_enabled_var.get():
                result = self.corrector.defringe_alpha(result, radius=self.defringe_radius_var.get())
            
            # Apply matte removal
            if self.matte_removal_enabled_var.get():
                matte_colors = {
                    "white": (255, 255, 255),
                    "black": (0, 0, 0),
                    "gray": (128, 128, 128)
                }
                matte = matte_colors.get(self.matte_color_var.get(), (255, 255, 255))
                result = self.corrector.remove_matte_color(result, matte_color=matte)
            
            # Apply feathering
            if self.feather_enabled_var.get():
                result = self.corrector.feather_alpha_edges(
                    result,
                    radius=self.feather_radius_var.get(),
                    strength=self.feather_strength_var.get()
                )
            
            # Apply morphology
            morph_op = self.morphology_op_var.get()
            if morph_op == "dilate":
                result = self.corrector.dilate_alpha(
                    result,
                    iterations=self.morphology_iterations_var.get(),
                    kernel_size=int(self.morphology_kernel_var.get())
                )
            elif morph_op == "erode":
                result = self.corrector.erode_alpha(
                    result,
                    iterations=self.morphology_iterations_var.get(),
                    kernel_size=int(self.morphology_kernel_var.get())
                )
            
            # Display result
            result_img = Image.fromarray(result)
            self._display_preview(result_img)
            
        except Exception as e:
            logger.error(f"Error applying fixes: {e}")
            messagebox.showerror("Error", f"Failed to apply fixes: {e}")
    
    def _process_batch(self):
        """Process batch of images."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to process")
            return
        
        if not self.output_directory:
            messagebox.showwarning("No Output", "Please select output directory")
            return
        
        # Disable button during processing
        self.process_button.configure(state="disabled")
        self.progress_bar.set(0)
        
        # Run in thread
        self.processing_thread = threading.Thread(target=self._run_batch_processing, daemon=True)
        self.processing_thread.start()
    
    def _run_batch_processing(self):
        """Run batch processing in background thread."""
        try:
            output_dir = Path(self.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            total = len(self.selected_files)
            successful = 0
            failed = 0
            
            for i, input_path in enumerate(self.selected_files):
                try:
                    # Update progress
                    progress = (i + 1) / total
                    filename = Path(input_path).name
                    self.after(0, lambda: self.progress_bar.set(progress))
                    self.after(0, lambda: self.progress_label.configure(
                        text=f"Processing {i + 1}/{total}: {filename}"
                    ))
                    
                    # Load image
                    img = Image.open(input_path)
                    arr = np.array(img)
                    
                    # Apply all enabled fixes
                    result = arr
                    
                    # Apply preset
                    preset_name = self.preset_var.get()
                    if preset_name != "none":
                        result, _ = self.corrector.correct_alpha(result, preset=preset_name)
                    
                    # Apply de-fringing
                    if self.defringe_enabled_var.get():
                        result = self.corrector.defringe_alpha(result, radius=self.defringe_radius_var.get())
                    
                    # Apply matte removal
                    if self.matte_removal_enabled_var.get():
                        matte_colors = {
                            "white": (255, 255, 255),
                            "black": (0, 0, 0),
                            "gray": (128, 128, 128)
                        }
                        matte = matte_colors.get(self.matte_color_var.get(), (255, 255, 255))
                        result = self.corrector.remove_matte_color(result, matte_color=matte)
                    
                    # Apply feathering
                    if self.feather_enabled_var.get():
                        result = self.corrector.feather_alpha_edges(
                            result,
                            radius=self.feather_radius_var.get(),
                            strength=self.feather_strength_var.get()
                        )
                    
                    # Apply morphology
                    morph_op = self.morphology_op_var.get()
                    if morph_op == "dilate":
                        result = self.corrector.dilate_alpha(
                            result,
                            iterations=self.morphology_iterations_var.get(),
                            kernel_size=int(self.morphology_kernel_var.get())
                        )
                    elif morph_op == "erode":
                        result = self.corrector.erode_alpha(
                            result,
                            iterations=self.morphology_iterations_var.get(),
                            kernel_size=int(self.morphology_kernel_var.get())
                        )
                    
                    # Save result
                    result_img = Image.fromarray(result)
                    output_path = output_dir / f"{Path(input_path).stem}_fixed.png"
                    result_img.save(output_path, format='PNG')
                    
                    successful += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {input_path}: {e}")
                    failed += 1
            
            # Show results
            message = f"Processing complete!\n\nSuccessful: {successful}\nFailed: {failed}"
            self.after(0, lambda: messagebox.showinfo("Complete", message))
            self.after(0, lambda: self.progress_label.configure(text="✓ Processing complete"))
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Batch processing failed: {e}"))
        
        finally:
            self.after(0, lambda: self.process_button.configure(state="normal"))
