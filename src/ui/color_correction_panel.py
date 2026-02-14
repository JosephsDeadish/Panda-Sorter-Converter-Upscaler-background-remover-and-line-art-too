"""
Color Correction Panel UI

Provides UI for color correction and enhancement features.
"""

import logging
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
from typing import Optional, List
from PIL import Image

logger = logging.getLogger(__name__)

try:
    from src.tools.color_corrector import ColorCorrector
    from src.ui.live_preview_widget import LivePreviewWidget
    COLOR_CORRECTOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Color corrector not available: {e}")
    COLOR_CORRECTOR_AVAILABLE = False

# Try to import SVG icon helper
try:
    from src.utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    load_icon = None
    SVG_ICONS_AVAILABLE = False
    logger.warning("SVG icons not available for Color Correction Panel")

# Try to import tooltip system
try:
    from src.features.tutorial_system import WidgetTooltip
    TOOLTIPS_AVAILABLE = True
except ImportError:
    WidgetTooltip = None
    TOOLTIPS_AVAILABLE = False
    logger.warning("Tooltips not available for Color Correction Panel")


class ColorCorrectionPanel(ctk.CTkFrame):
    """Panel for color correction and enhancement."""
    
    def __init__(self, parent, unlockables_system=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        if not COLOR_CORRECTOR_AVAILABLE:
            self._show_unavailable()
            return
        
        self.unlockables_system = unlockables_system
        self.corrector = ColorCorrector()
        self.input_files = []
        self.output_dir = ""
        self.current_lut = None
        self.processing = False
        
        self._tooltips = []
        
        self._create_ui()
        self._add_tooltips()
    
    def _show_unavailable(self):
        """Show message when color corrector is not available."""
        label = ctk.CTkLabel(
            self,
            text="⚠️ Color Correction Tool Unavailable\n\nRequired dependencies not installed.",
            font=("Arial", 14)
        )
        label.pack(expand=True)
    
    def _create_ui(self):
        """Create the user interface."""
        # Main container with scrolling
        main_container = ctk.CTkScrollableFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title = ctk.CTkLabel(
            main_container,
            text="🎨 Color Correction & Enhancement",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=(0, 20))
        
        # File selection section
        self._create_file_section(main_container)
        
        # Adjustment controls section
        self._create_controls_section(main_container)
        
        # Live preview section
        self._create_preview_section(main_container)
        
        # Actions section
        self._create_actions_section(main_container)
    
    def _create_file_section(self, parent):
        """Create file selection section."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        # Title
        label = ctk.CTkLabel(frame, text="📁 Input Files", font=("Arial", 14, "bold"))
        label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Buttons
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.select_files_btn = ctk.CTkButton(
            btn_frame,
            text="📄 Select Images",
            command=self._select_files,
            width=140
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("file_open_animated", (20, 20))
            if icon:
                self.select_files_btn.configure(image=icon, compound="left")
        self.select_files_btn.pack(side="left", padx=5)
        
        self.select_folder_btn = ctk.CTkButton(
            btn_frame,
            text="📁 Select Folder",
            command=self._select_folder,
            width=140
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("folder_open_animated", (20, 20))
            if icon:
                self.select_folder_btn.configure(image=icon, compound="left")
        self.select_folder_btn.pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ Clear",
            command=self._clear_files,
            width=100
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("trash_empty_animated", (20, 20))
            if icon:
                self.clear_btn.configure(image=icon, compound="left")
        self.clear_btn.pack(side="left", padx=5)
        
        # File count
        self.file_count_label = ctk.CTkLabel(
            frame,
            text="No files selected",
            font=("Arial", 11)
        )
        self.file_count_label.pack(anchor="w", padx=10, pady=(0, 5))
        
        # Output directory
        output_frame = ctk.CTkFrame(frame)
        output_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(
            output_frame,
            text="📂 Output Directory:",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(0, 5))
        
        self.select_output_btn = ctk.CTkButton(
            output_frame,
            text="Select Output Folder",
            command=self._select_output,
            width=160
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("folder_open_animated", (20, 20))
            if icon:
                self.select_output_btn.configure(image=icon, compound="left")
        self.select_output_btn.pack(side="left", padx=5)
        
        self.output_label = ctk.CTkLabel(
            output_frame,
            text="Not selected",
            font=("Arial", 10)
        )
        self.output_label.pack(side="left", padx=5)
    
    def _create_controls_section(self, parent):
        """Create adjustment controls section."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        # Title
        label = ctk.CTkLabel(frame, text="⚙️ Adjustments", font=("Arial", 14, "bold"))
        label.pack(anchor="w", padx=10, pady=(10, 10))
        
        # White Balance
        self._create_slider(
            frame,
            "🔆 Auto White Balance:",
            0, 1, 0,
            lambda v: self._on_adjustment_change()
        )
        self.wb_slider = frame.winfo_children()[-1]
        self.wb_label = frame.winfo_children()[-2]
        
        # Exposure
        self._create_slider(
            frame,
            "☀️ Exposure (EV):",
            -3, 3, 0,
            lambda v: self._on_adjustment_change()
        )
        self.exp_slider = frame.winfo_children()[-1]
        self.exp_label = frame.winfo_children()[-2]
        
        # Vibrance
        self._create_slider(
            frame,
            "🌈 Vibrance:",
            0, 2, 1,
            lambda v: self._on_adjustment_change()
        )
        self.vib_slider = frame.winfo_children()[-1]
        self.vib_label = frame.winfo_children()[-2]
        
        # Clarity
        self._create_slider(
            frame,
            "✨ Clarity:",
            0, 2, 0,
            lambda v: self._on_adjustment_change()
        )
        self.clar_slider = frame.winfo_children()[-1]
        self.clar_label = frame.winfo_children()[-2]
        
        # LUT selection
        lut_frame = ctk.CTkFrame(frame)
        lut_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            lut_frame,
            text="🎭 LUT (Color Grading):",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=(0, 10))
        
        self.load_lut_btn = ctk.CTkButton(
            lut_frame,
            text="📂 Load .cube LUT",
            command=self._load_lut,
            width=140
        )
        self.load_lut_btn.pack(side="left", padx=5)
        
        self.clear_lut_btn = ctk.CTkButton(
            lut_frame,
            text="❌ Clear LUT",
            command=self._clear_lut,
            width=120,
            state="disabled"
        )
        self.clear_lut_btn.pack(side="left", padx=5)
        
        self.lut_label = ctk.CTkLabel(
            lut_frame,
            text="No LUT loaded",
            font=("Arial", 10)
        )
        self.lut_label.pack(side="left", padx=5)
        
        # LUT strength (only shown when LUT loaded)
        self.lut_strength_frame = ctk.CTkFrame(frame)
        # Pack later when LUT is loaded
        
        ctk.CTkLabel(
            self.lut_strength_frame,
            text="LUT Strength:",
            font=("Arial", 10)
        ).pack(side="left", padx=(10, 5))
        
        self.lut_strength_slider = ctk.CTkSlider(
            self.lut_strength_frame,
            from_=0,
            to=1,
            number_of_steps=100,
            command=lambda v: self._on_lut_strength_change(v),
            width=200
        )
        self.lut_strength_slider.set(1.0)
        self.lut_strength_slider.pack(side="left", padx=5)
        
        self.lut_strength_value = ctk.CTkLabel(
            self.lut_strength_frame,
            text="100%",
            font=("Arial", 10),
            width=50
        )
        self.lut_strength_value.pack(side="left", padx=5)
        
        # Reset button
        reset_btn = ctk.CTkButton(
            frame,
            text="🔄 Reset All",
            command=self._reset_adjustments,
            width=120
        )
        reset_btn.pack(pady=(10, 10))
    
    def _create_slider(self, parent, label_text, from_, to, initial, command):
        """Create a labeled slider control."""
        container = ctk.CTkFrame(parent)
        container.pack(fill="x", padx=10, pady=5)
        
        # Label with current value
        label = ctk.CTkLabel(
            container,
            text=f"{label_text} {initial:.2f}",
            font=("Arial", 11)
        )
        label.pack(anchor="w", pady=(0, 2))
        
        # Slider
        slider = ctk.CTkSlider(
            container,
            from_=from_,
            to=to,
            number_of_steps=100,
            command=lambda v: self._update_slider_label(label, label_text, v, command)
        )
        slider.set(initial)
        slider.pack(fill="x", pady=(0, 5))
        
        return container
    
    def _update_slider_label(self, label, base_text, value, callback):
        """Update slider label with current value."""
        label.configure(text=f"{base_text} {value:.2f}")
        if callback:
            callback(value)
    
    def _create_preview_section(self, parent):
        """Create live preview section."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, pady=10)
        
        # Title
        label = ctk.CTkLabel(frame, text="👁️ Live Preview", font=("Arial", 14, "bold"))
        label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Preview widget
        self.preview = LivePreviewWidget(frame)
        self.preview.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Set processing function
        self.preview.set_processing_function(self._apply_current_settings)
    
    def _create_actions_section(self, parent):
        """Create action buttons section."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=10)
        
        # Progress bar
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(frame, variable=self.progress_var)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.pack_forget()  # Hide initially
        
        self.progress_label = ctk.CTkLabel(frame, text="", font=("Arial", 10))
        self.progress_label.pack(pady=(0, 5))
        self.progress_label.pack_forget()  # Hide initially
        
        # Buttons
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(pady=10)
        
        self.process_btn = ctk.CTkButton(
            btn_frame,
            text="🚀 Process Images",
            command=self._process_images,
            width=180,
            height=40,
            font=("Arial", 13, "bold")
        )
        self.process_btn.pack(side="left", padx=10)
        
        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            command=self._cancel_processing,
            width=120,
            height=40,
            state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=10)
    
    def _select_files(self):
        """Select image files."""
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )
        if files:
            self.input_files = list(files)
            self._update_file_count()
            self._load_first_image_for_preview()
    
    def _select_folder(self):
        """Select folder containing images."""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            # Find all images in folder
            folder_path = Path(folder)
            image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
            self.input_files = [
                str(f) for f in folder_path.iterdir()
                if f.suffix.lower() in image_extensions
            ]
            self._update_file_count()
            self._load_first_image_for_preview()
    
    def _clear_files(self):
        """Clear selected files."""
        self.input_files = []
        self._update_file_count()
        self.preview.clear()
    
    def _select_output(self):
        """Select output directory."""
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.output_dir = folder
            self.output_label.configure(text=folder)
    
    def _update_file_count(self):
        """Update file count label."""
        count = len(self.input_files)
        if count == 0:
            text = "No files selected"
        elif count == 1:
            text = "1 file selected"
        else:
            text = f"{count} files selected"
        self.file_count_label.configure(text=text)
    
    def _load_first_image_for_preview(self):
        """Load first selected image for preview."""
        if self.input_files:
            self.preview.load_image(self.input_files[0])
    
    def _on_adjustment_change(self):
        """Handle adjustment slider changes."""
        # Update preview
        if self.input_files:
            self.preview.apply_processing()
    
    def _apply_current_settings(self, image: Image.Image) -> Image.Image:
        """Apply current correction settings to an image."""
        try:
            settings = {
                'white_balance': self.wb_slider.get(),
                'exposure': self.exp_slider.get(),
                'vibrance': self.vib_slider.get(),
                'clarity': self.clar_slider.get(),
                'lut_path': self.current_lut,
                'lut_strength': self.lut_strength_slider.get() if self.current_lut else 1.0
            }
            
            return self.corrector.apply_corrections(image, **settings)
            
        except Exception as e:
            logger.error(f"Failed to apply corrections: {e}")
            return image
    
    def _load_lut(self):
        """Load a .cube LUT file."""
        file = filedialog.askopenfilename(
            title="Select LUT File",
            filetypes=[("Cube LUT", "*.cube"), ("All files", "*.*")]
        )
        if file:
            # Test load
            lut = self.corrector.load_lut(file)
            if lut is not None:
                self.current_lut = file
                self.lut_label.configure(text=Path(file).name)
                self.clear_lut_btn.configure(state="normal")
                # Show LUT strength slider
                self.lut_strength_frame.pack(fill="x", padx=10, pady=5)
                self._on_adjustment_change()  # Update preview
            else:
                messagebox.showerror("Error", "Failed to load LUT file")
    
    def _clear_lut(self):
        """Clear loaded LUT."""
        self.current_lut = None
        self.lut_label.configure(text="No LUT loaded")
        self.clear_lut_btn.configure(state="disabled")
        # Hide LUT strength slider
        self.lut_strength_frame.pack_forget()
        self._on_adjustment_change()  # Update preview
    
    def _on_lut_strength_change(self, value):
        """Handle LUT strength slider change."""
        strength = float(value)
        self.lut_strength_value.configure(text=f"{int(strength * 100)}%")
        self._on_adjustment_change()  # Update preview
    
    def _reset_adjustments(self):
        """Reset all adjustments to defaults."""
        self.wb_slider.set(0)
        self.exp_slider.set(0)
        self.vib_slider.set(1)
        self.clar_slider.set(0)
        self._on_adjustment_change()
    
    def _process_images(self):
        """Process all selected images."""
        if not self.input_files:
            messagebox.showwarning("No Files", "Please select images to process")
            return
        
        if not self.output_dir:
            messagebox.showwarning("No Output", "Please select output directory")
            return
        
        # Confirm
        count = len(self.input_files)
        if not messagebox.askyesno(
            "Confirm Processing",
            f"Process {count} image(s) with current settings?"
        ):
            return
        
        # Prepare settings
        settings = {
            'white_balance': self.wb_slider.get(),
            'exposure': self.exp_slider.get(),
            'vibrance': self.vib_slider.get(),
            'clarity': self.clar_slider.get(),
            'lut_path': self.current_lut,
            'lut_strength': 1.0
        }
        
        # Start processing in background thread
        self.processing = True
        self._set_processing_state(True)
        
        thread = threading.Thread(
            target=self._process_thread,
            args=(self.input_files, self.output_dir, settings),
            daemon=True
        )
        thread.start()
    
    def _process_thread(self, files, output_dir, settings):
        """Background thread for processing."""
        try:
            def progress_callback(current, total, filename):
                if not self.processing:
                    return
                
                progress = current / total
                self.after(0, self._update_progress, progress, current, total, filename)
            
            success, errors = self.corrector.batch_process(
                files,
                output_dir,
                settings,
                progress_callback
            )
            
            # Show results
            self.after(0, self._show_results, success, len(files), errors)
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            self.after(0, messagebox.showerror, "Error", f"Processing failed: {e}")
        
        finally:
            self.after(0, self._set_processing_state, False)
            self.processing = False
    
    def _update_progress(self, progress, current, total, filename):
        """Update progress bar and label."""
        self.progress_var.set(progress)
        self.progress_label.configure(text=f"Processing {current}/{total}: {filename}")
    
    def _show_results(self, success, total, errors):
        """Show processing results."""
        if errors:
            error_text = "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_text += f"\n... and {len(errors) - 5} more errors"
            
            messagebox.showwarning(
                "Processing Complete with Errors",
                f"Successfully processed {success}/{total} images.\n\n"
                f"Errors:\n{error_text}"
            )
        else:
            messagebox.showinfo(
                "Processing Complete",
                f"Successfully processed {success}/{total} images!"
            )
    
    def _cancel_processing(self):
        """Cancel processing."""
        self.processing = False
        self.progress_label.configure(text="Cancelling...")
    
    def _set_processing_state(self, processing: bool):
        """Set UI state during processing."""
        state = "disabled" if processing else "normal"
        
        self.select_files_btn.configure(state=state)
        self.select_folder_btn.configure(state=state)
        self.clear_btn.configure(state=state)
        self.select_output_btn.configure(state=state)
        self.process_btn.configure(state=state)
        self.load_lut_btn.configure(state=state)
        
        self.cancel_btn.configure(state="normal" if processing else "disabled")
        
        if processing:
            self.progress_bar.pack(fill="x", padx=10, pady=10)
            self.progress_label.pack(pady=(0, 5))
        else:
            self.progress_bar.pack_forget()
            self.progress_label.pack_forget()
            self.progress_var.set(0)
    
    def _add_tooltips(self):
        """Add tooltips to widgets if available."""
        if not TOOLTIPS_AVAILABLE or not self.unlockables_system:
            return
        
        try:
            tooltips = self.unlockables_system.get_all_tooltips()
            tooltips_lower = [t.lower() for t in tooltips]
            
            def get_tooltip(keyword):
                """Find tooltip containing keyword."""
                for tooltip in tooltips_lower:
                    if keyword.lower() in tooltip:
                        return tooltips[tooltips_lower.index(tooltip)]
                return None
            
            # White balance tooltip
            if hasattr(self, 'white_balance_slider'):
                tooltip = get_tooltip("white balance") or get_tooltip("color temperature")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.white_balance_slider, tooltip))
            
            # Exposure tooltip
            if hasattr(self, 'exposure_slider'):
                tooltip = get_tooltip("exposure") or get_tooltip("brightness")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.exposure_slider, tooltip))
            
            # Vibrance tooltip
            if hasattr(self, 'vibrance_slider'):
                tooltip = get_tooltip("vibrance") or get_tooltip("saturation")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.vibrance_slider, tooltip))
            
            # Clarity tooltip
            if hasattr(self, 'clarity_slider'):
                tooltip = get_tooltip("clarity") or get_tooltip("sharpness")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.clarity_slider, tooltip))
            
            # LUT button tooltip
            if hasattr(self, 'load_lut_btn'):
                tooltip = get_tooltip("lut") or get_tooltip("color grading")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.load_lut_btn, tooltip))
                    
        except Exception as e:
            logger.error(f"Error adding tooltips to Color Correction Panel: {e}")


def open_color_correction_dialog(parent):
    """Open color correction dialog."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Color Correction & Enhancement")
    dialog.geometry("1000x800")
    
    panel = ColorCorrectionPanel(dialog)
    panel.pack(fill="both", expand=True)
    
    return dialog
