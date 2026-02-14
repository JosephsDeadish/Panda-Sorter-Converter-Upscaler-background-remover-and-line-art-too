"""
Image Repair Panel
UI for repairing corrupted PNG and JPEG files.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import logging
from typing import List, Optional

try:
    from src.tools.image_repairer import ImageRepairer, CorruptionType, RepairResult
except ImportError:
    ImageRepairer = None

logger = logging.getLogger(__name__)

# Try to import SVG icon helper
try:
    from src.utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    load_icon = None
    SVG_ICONS_AVAILABLE = False
    logger.warning("SVG icons not available for Image Repair Panel")

# Try to import tooltip system
try:
    from src.features.tutorial_system import WidgetTooltip
    TOOLTIPS_AVAILABLE = True
except ImportError:
    WidgetTooltip = None
    TOOLTIPS_AVAILABLE = False
    logger.warning("Tooltips not available for Image Repair Panel")


class ImageRepairPanel(ctk.CTkFrame):
    """Panel for repairing corrupted images."""
    
    def __init__(self, parent, unlockables_system=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        if ImageRepairer is None:
            self._show_import_error()
            return
        
        self.unlockables_system = unlockables_system
        self.repairer = ImageRepairer()
        self.selected_files: List[str] = []
        self.is_processing = False
        
        self._tooltips = []
        self._create_widgets()
        self._add_tooltips()
    
    def _show_import_error(self):
        """Show error if ImageRepairer cannot be imported."""
        error_label = ctk.CTkLabel(
            self,
            text="❌ Image Repair Tool could not be loaded.\nPlease check installation.",
            font=("Arial", 14),
            text_color="red"
        )
        error_label.pack(expand=True)
    
    def _create_widgets(self):
        """Create UI widgets."""
        # Title
        title = ctk.CTkLabel(
            self,
            text="🔧 Image Repair Tool",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=10)
        
        # Description
        desc = ctk.CTkLabel(
            self,
            text="Repair corrupted PNG and JPEG image files",
            font=("Arial", 12)
        )
        desc.pack(pady=(0, 10))
        
        # File selection frame
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            file_frame,
            text="📁 Input Files:",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        btn_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.select_files_btn = ctk.CTkButton(
            btn_frame,
            text="Select Files",
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
        
        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear",
            command=self._clear_files,
            width=80
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("trash_empty_animated", (18, 18))
            if icon:
                self.clear_btn.configure(image=icon, compound="left")
        self.clear_btn.pack(side="left", padx=5)
        
        self.file_count_label = ctk.CTkLabel(
            file_frame,
            text="No files selected",
            font=("Arial", 11)
        )
        self.file_count_label.pack(anchor="w", padx=10, pady=5)
        
        # Output directory frame
        output_frame = ctk.CTkFrame(self)
        output_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            output_frame,
            text="📂 Output Directory:",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        output_select_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_select_frame.pack(fill="x", padx=10, pady=5)
        
        self.output_dir_btn = ctk.CTkButton(
            output_select_frame,
            text="Select Output Folder",
            command=self._select_output_dir,
            width=150
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("folder_open_animated", (20, 20))
            if icon:
                self.output_dir_btn.configure(image=icon, compound="left")
        self.output_dir_btn.pack(side="left", padx=5)
        
        self.output_dir_label = ctk.CTkLabel(
            output_frame,
            text="No output directory selected",
            font=("Arial", 11)
        )
        self.output_dir_label.pack(anchor="w", padx=10, pady=5)
        
        self.output_dir = None
        
        # Diagnostic display
        diag_frame = ctk.CTkFrame(self)
        diag_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            diag_frame,
            text="📋 Diagnostic Information:",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.diagnostic_text = ctk.CTkTextbox(
            diag_frame,
            height=200,
            font=("Courier", 10)
        )
        self.diagnostic_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 11)
        )
        self.progress_label.pack(pady=(0, 10))
        
        # Action buttons
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=10)
        
        self.diagnose_btn = ctk.CTkButton(
            action_frame,
            text="🔍 Diagnose",
            command=self._diagnose_files,
            width=140
        )
        self.diagnose_btn.pack(side="left", padx=5)
        
        self.repair_btn = ctk.CTkButton(
            action_frame,
            text="🔧 Repair Files",
            command=self._repair_files,
            width=140,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.repair_btn.pack(side="left", padx=5)
        
        self.cancel_btn = ctk.CTkButton(
            action_frame,
            text="Cancel",
            command=self._cancel_operation,
            width=100,
            state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=5)
    
    def _select_files(self):
        """Select image files."""
        filetypes = (
            ("Image files", "*.png *.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*")
        )
        
        files = filedialog.askopenfilenames(
            title="Select Image Files",
            filetypes=filetypes
        )
        
        if files:
            self.selected_files.extend(files)
            self._update_file_count()
    
    def _select_folder(self):
        """Select folder containing images."""
        folder = filedialog.askdirectory(title="Select Folder")
        
        if folder:
            # Find all image files in folder
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        filepath = os.path.join(root, file)
                        self.selected_files.append(filepath)
            
            self._update_file_count()
    
    def _clear_files(self):
        """Clear selected files."""
        self.selected_files.clear()
        self._update_file_count()
        self.diagnostic_text.delete("1.0", "end")
    
    def _update_file_count(self):
        """Update file count label."""
        count = len(self.selected_files)
        if count == 0:
            self.file_count_label.configure(text="No files selected")
        elif count == 1:
            self.file_count_label.configure(text="1 file selected")
        else:
            self.file_count_label.configure(text=f"{count} files selected")
    
    def _select_output_dir(self):
        """Select output directory."""
        folder = filedialog.askdirectory(title="Select Output Directory")
        
        if folder:
            self.output_dir = folder
            self.output_dir_label.configure(text=folder)
    
    def _diagnose_files(self):
        """Diagnose selected files."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to diagnose.")
            return
        
        self.diagnostic_text.delete("1.0", "end")
        self.diagnostic_text.insert("end", "Running diagnostics...\n\n")
        
        def run_diagnostics():
            for i, filepath in enumerate(self.selected_files):
                filename = os.path.basename(filepath)
                self._safe_ui_update(
                    lambda f=filename: self.diagnostic_text.insert("end", f"Diagnosing: {f}\n")
                )
                
                try:
                    report = self.repairer.diagnose_file(filepath)
                    
                    # Format diagnostic output
                    output = f"File: {filename}\n"
                    output += f"  Type: {report.file_type}\n"
                    output += f"  Size: {report.file_size:,} bytes\n"
                    output += f"  Corrupted: {'Yes' if report.is_corrupted else 'No'}\n"
                    
                    if report.is_corrupted:
                        output += f"  Corruption Type: {report.corruption_type.value}\n"
                        output += f"  Repairable: {'Yes' if report.repairable else 'No'}\n"
                        output += f"  Recovery: {report.recovery_percentage:.1f}%\n"
                        
                        if report.notes:
                            output += "  Notes:\n"
                            for note in report.notes:
                                output += f"    - {note}\n"
                    
                    output += "\n"
                    
                    self._safe_ui_update(
                        lambda o=output: self.diagnostic_text.insert("end", o)
                    )
                    
                except Exception as e:
                    error_msg = f"Error diagnosing {filename}: {str(e)}\n\n"
                    self._safe_ui_update(
                        lambda m=error_msg: self.diagnostic_text.insert("end", m)
                    )
            
            self._safe_ui_update(
                lambda: self.diagnostic_text.insert("end", "Diagnostics complete!\n")
            )
        
        thread = threading.Thread(target=run_diagnostics, daemon=True)
        thread.start()
    
    def _repair_files(self):
        """Repair selected files."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to repair.")
            return
        
        if not self.output_dir:
            messagebox.showwarning("No Output", "Please select an output directory.")
            return
        
        if not messagebox.askyesno(
            "Confirm Repair",
            f"Repair {len(self.selected_files)} file(s)?\n\nRepaired files will be saved to:\n{self.output_dir}"
        ):
            return
        
        self.is_processing = True
        self._set_processing_state(True)
        self.diagnostic_text.delete("1.0", "end")
        self.diagnostic_text.insert("end", "Starting repair process...\n\n")
        
        def run_repair():
            try:
                def progress_callback(current, total, filename):
                    progress = current / total
                    self._safe_ui_update(lambda: self.progress_bar.set(progress))
                    self._safe_ui_update(
                        lambda c=current, t=total, f=filename:
                        self.progress_label.configure(text=f"Processing {c}/{t}: {f}")
                    )
                    self._safe_ui_update(
                        lambda f=filename:
                        self.diagnostic_text.insert("end", f"Repairing: {f}\n")
                    )
                
                successes, failures = self.repairer.batch_repair(
                    self.selected_files,
                    self.output_dir,
                    progress_callback
                )
                
                # Show results
                result_text = f"\nRepair complete!\n"
                result_text += f"Successfully repaired: {len(successes)} file(s)\n"
                result_text += f"Failed: {len(failures)} file(s)\n\n"
                
                if failures:
                    result_text += "Failed files:\n"
                    for filepath, reason in failures:
                        filename = os.path.basename(filepath)
                        result_text += f"  - {filename}: {reason}\n"
                
                self._safe_ui_update(
                    lambda t=result_text: self.diagnostic_text.insert("end", t)
                )
                
                self._safe_ui_update(
                    lambda: messagebox.showinfo(
                        "Repair Complete",
                        f"Repaired {len(successes)}/{len(self.selected_files)} file(s)\n\n"
                        f"Output directory:\n{self.output_dir}"
                    )
                )
                
            except Exception as e:
                error_msg = f"\nError during repair: {str(e)}\n"
                self._safe_ui_update(
                    lambda m=error_msg: self.diagnostic_text.insert("end", m)
                )
                self._safe_ui_update(
                    lambda: messagebox.showerror("Error", f"Repair failed: {str(e)}")
                )
            
            finally:
                self.is_processing = False
                self._safe_ui_update(lambda: self._set_processing_state(False))
                self._safe_ui_update(lambda: self.progress_bar.set(0))
                self._safe_ui_update(lambda: self.progress_label.configure(text=""))
        
        thread = threading.Thread(target=run_repair, daemon=True)
        thread.start()
    
    def _cancel_operation(self):
        """Cancel current operation."""
        if self.is_processing:
            self.is_processing = False
            messagebox.showinfo("Cancelled", "Operation cancelled.")
    
    def _set_processing_state(self, processing: bool):
        """Enable/disable controls during processing."""
        state = "disabled" if processing else "normal"
        
        self.select_files_btn.configure(state=state)
        self.select_folder_btn.configure(state=state)
        self.clear_btn.configure(state=state)
        self.output_dir_btn.configure(state=state)
        self.diagnose_btn.configure(state=state)
        self.repair_btn.configure(state=state)
        
        cancel_state = "normal" if processing else "disabled"
        self.cancel_btn.configure(state=cancel_state)
    
    def _safe_ui_update(self, func):
        """Thread-safe UI update."""
        try:
            self.after(0, func)
        except Exception as e:
            logger.error(f"UI update failed: {e}")
    
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
            
            # Diagnostic button tooltip
            if hasattr(self, 'diagnose_btn'):
                tooltip = get_tooltip("diagnose") or get_tooltip("analyze") or get_tooltip("check")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.diagnose_btn, tooltip))
            
            # Repair button tooltip
            if hasattr(self, 'repair_btn'):
                tooltip = get_tooltip("repair") or get_tooltip("fix")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.repair_btn, tooltip))
            
            # Results textbox tooltip
            if hasattr(self, 'result_text'):
                tooltip = get_tooltip("result") or get_tooltip("report")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.result_text, tooltip))
                    
        except Exception as e:
            logger.error(f"Error adding tooltips to Image Repair Panel: {e}")


def open_image_repair_dialog(parent):
    """Open image repair dialog window."""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Image Repair Tool")
    dialog.geometry("800x700")
    
    panel = ImageRepairPanel(dialog)
    panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    return dialog
