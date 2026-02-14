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
from PIL import Image
import zipfile
import threading

from src.tools.background_remover import BackgroundRemover, check_dependencies, AlphaPresets
from src.ui.live_preview_widget import LivePreviewWidget
from src.ui.archive_queue_widgets import ArchiveSettingsWidget, ProcessingQueue, OutputMode

logger = logging.getLogger(__name__)


class BackgroundRemoverPanel(ctk.CTkFrame):
    """
    UI panel for background removal operations with one-click processing,
    batch support, and edge refinement controls.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Initialize background remover
        self.remover = BackgroundRemover()
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.processing_thread = None
        self.current_preset = None
        
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
            text="🎭 AI Background Remover",
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
            width=150
        )
        self.select_files_btn.pack(side="left", padx=5)
        
        self.select_folder_btn = ctk.CTkButton(
            btn_frame,
            text="Select Folder",
            command=self._select_folder,
            width=150
        )
        self.select_folder_btn.pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear Selection",
            command=self._clear_selection,
            width=150,
            fg_color="gray40"
        )
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
        self.select_output_btn.pack(side="left", padx=5)
        
        self.output_label = ctk.CTkLabel(
            output_btn_frame,
            text="(Same as input)",
            font=("Arial", 10),
            text_color="gray"
        )
        self.output_label.pack(side="left", padx=10)
        
        # Settings frame
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(settings_frame, text="⚙️ Settings:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Alpha Preset Selection
        preset_frame = ctk.CTkFrame(settings_frame)
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
            settings_frame,
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
        edge_frame = ctk.CTkFrame(settings_frame)
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
        model_frame = ctk.CTkFrame(settings_frame)
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
            settings_frame,
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
    
    def _check_availability(self):
        """Check if background removal is available."""
        deps = check_dependencies()
        
        if deps['rembg']:
            self.status_label.configure(
                text="✓ AI Background Removal Available",
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
        
        if not deps['opencv']:
            logger.warning("OpenCV not available - advanced edge refinement disabled")
    
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
            image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
            self.selected_files = [
                str(f) for f in folder_path.iterdir()
                if f.suffix.lower() in image_extensions
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
