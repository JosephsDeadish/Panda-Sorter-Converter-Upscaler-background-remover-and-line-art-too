"""
Batch Rename Panel UI
---------------------
User interface for batch renaming files with various patterns.
"""

import os
import logging
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List, Optional
import threading

from src.tools.batch_renamer import BatchRenamer, RenamePattern

logger = logging.getLogger(__name__)

# Try to import SVG icon helper
try:
    from src.utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    load_icon = None
    SVG_ICONS_AVAILABLE = False
    logger.warning("SVG icons not available for Batch Rename Panel")

# Try to import tooltip system
try:
    from src.features.tutorial_system import WidgetTooltip
    TOOLTIPS_AVAILABLE = True
except ImportError:
    WidgetTooltip = None
    TOOLTIPS_AVAILABLE = False
    logger.warning("Tooltips not available for Batch Rename Panel")


class BatchRenamePanel(ctk.CTkFrame):
    """UI panel for batch file renaming"""
    
    def __init__(self, parent, unlockables_system=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.unlockables_system = unlockables_system
        self.renamer = BatchRenamer()
        self.selected_files = []
        self.preview_data = []
        
        self._tooltips = []
        self._build_ui()
        self._add_tooltips()
    
    def _build_ui(self):
        """Build the user interface"""
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📝 Batch Rename Tool",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Description
        desc_label = ctk.CTkLabel(
            self,
            text="Rename multiple files using patterns, dates, resolution, or custom templates",
            font=("Arial", 11)
        )
        desc_label.pack(pady=(0, 15))
        
        # File selection section
        files_frame = ctk.CTkFrame(self)
        files_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            files_frame,
            text="📁 Select Files:",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        btn_frame = ctk.CTkFrame(files_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        select_files_btn = ctk.CTkButton(
            btn_frame,
            text="➕ Select Images",
            command=self._select_files,
            width=150
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("file_open_animated", (20, 20))
            if icon:
                select_files_btn.configure(image=icon, compound="left")
        select_files_btn.pack(side="left", padx=5)
        
        select_folder_btn = ctk.CTkButton(
            btn_frame,
            text="📂 Select Folder",
            command=self._select_folder,
            width=150
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("folder_open_animated", (20, 20))
            if icon:
                select_folder_btn.configure(image=icon, compound="left")
        select_folder_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ Clear",
            command=self._clear_files,
            width=100
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("trash_empty_animated", (20, 20))
            if icon:
                clear_btn.configure(image=icon, compound="left")
        clear_btn.pack(side="left", padx=5)
        
        self.file_count_label = ctk.CTkLabel(
            files_frame,
            text="No files selected",
            font=("Arial", 10)
        )
        self.file_count_label.pack(anchor="w", padx=10, pady=5)
        
        # Pattern selection section
        pattern_frame = ctk.CTkFrame(self)
        pattern_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            pattern_frame,
            text="🎯 Rename Pattern:",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.pattern_var = ctk.StringVariable(value=RenamePattern.SEQUENTIAL)
        
        patterns = [
            ("📅 Date Created", RenamePattern.DATE_CREATED),
            ("📅 Date Modified", RenamePattern.DATE_MODIFIED),
            ("📷 EXIF Date", RenamePattern.DATE_EXIF),
            ("📐 Resolution (WxH)", RenamePattern.RESOLUTION),
            ("🔢 Sequential (1, 2, 3...)", RenamePattern.SEQUENTIAL),
            ("✏️ Custom Template", RenamePattern.CUSTOM),
            ("🔒 Privacy (Random)", RenamePattern.PRIVACY)
        ]
        
        for text, value in patterns:
            ctk.CTkRadioButton(
                pattern_frame,
                text=text,
                variable=self.pattern_var,
                value=value,
                command=self._on_pattern_change
            ).pack(anchor="w", padx=30, pady=2)
        
        # Custom template section (initially hidden)
        self.template_frame = ctk.CTkFrame(self)
        self.template_frame.pack(fill="x", padx=10, pady=5)
        self.template_frame.pack_forget()  # Hide initially
        
        ctk.CTkLabel(
            self.template_frame,
            text="Template (use {name}, {index}, {date}, {res}, etc.):",
            font=("Arial", 10)
        ).pack(anchor="w", padx=10, pady=(5, 0))
        
        self.template_entry = ctk.CTkEntry(
            self.template_frame,
            placeholder_text="{name}_{date}_{index}"
        )
        self.template_entry.pack(fill="x", padx=10, pady=5)
        
        # Starting index
        index_frame = ctk.CTkFrame(self, fg_color="transparent")
        index_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            index_frame,
            text="Starting Index:",
            font=("Arial", 11)
        ).pack(side="left", padx=10)
        
        self.start_index_var = ctk.StringVariable(value="1")
        self.start_index_entry = ctk.CTkEntry(
            index_frame,
            textvariable=self.start_index_var,
            width=100
        )
        self.start_index_entry.pack(side="left", padx=5)
        
        # Metadata injection section
        metadata_frame = ctk.CTkFrame(self)
        metadata_frame.pack(fill="x", padx=10, pady=5)
        
        self.add_metadata_var = ctk.BooleanVar(value=False)
        metadata_check = ctk.CTkCheckBox(
            metadata_frame,
            text="📋 Add Metadata (Copyright, Author, Description)",
            variable=self.add_metadata_var,
            command=self._toggle_metadata
        )
        metadata_check.pack(anchor="w", padx=10, pady=5)
        
        self.metadata_inputs_frame = ctk.CTkFrame(metadata_frame)
        self.metadata_inputs_frame.pack(fill="x", padx=10, pady=5)
        self.metadata_inputs_frame.pack_forget()  # Hide initially
        
        ctk.CTkLabel(
            self.metadata_inputs_frame,
            text="Copyright:",
            font=("Arial", 10)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.copyright_entry = ctk.CTkEntry(
            self.metadata_inputs_frame,
            placeholder_text="© 2026 Your Name"
        )
        self.copyright_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ctk.CTkLabel(
            self.metadata_inputs_frame,
            text="Author:",
            font=("Arial", 10)
        ).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        self.author_entry = ctk.CTkEntry(
            self.metadata_inputs_frame,
            placeholder_text="Your Name"
        )
        self.author_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        ctk.CTkLabel(
            self.metadata_inputs_frame,
            text="Description:",
            font=("Arial", 10)
        ).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        self.description_entry = ctk.CTkEntry(
            self.metadata_inputs_frame,
            placeholder_text="Image description"
        )
        self.description_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        self.metadata_inputs_frame.columnconfigure(1, weight=1)
        
        # Preview section
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        preview_header = ctk.CTkFrame(preview_frame, fg_color="transparent")
        preview_header.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            preview_header,
            text="👁️ Preview:",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10)
        
        preview_btn = ctk.CTkButton(
            preview_header,
            text="🔄 Generate Preview",
            command=self._generate_preview,
            width=150
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("syncing_animated", (20, 20))
            if icon:
                preview_btn.configure(image=icon, compound="left")
        preview_btn.pack(side="left", padx=5)
        
        # Preview textbox (scrollable)
        self.preview_text = ctk.CTkTextbox(
            preview_frame,
            height=200,
            font=("Courier", 10)
        )
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Action buttons
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=10)
        
        rename_btn = ctk.CTkButton(
            action_frame,
            text="✅ Rename Files",
            command=self._rename_files,
            fg_color="green",
            hover_color="darkgreen",
            width=150,
            height=40
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("file_rename_animated", (24, 24))
            if icon:
                rename_btn.configure(image=icon, compound="left")
        rename_btn.pack(side="left", padx=5)
        
        undo_btn = ctk.CTkButton(
            action_frame,
            text="↩️ Undo Last Rename",
            command=self._undo_rename,
            width=150,
            height=40
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("arrow_left_animated", (20, 20))
            if icon:
                undo_btn.configure(image=icon, compound="left")
        undo_btn.pack(side="left", padx=5)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(fill="x", padx=10, pady=5)
        self.progress.set(0)
        self.progress.pack_forget()  # Hide initially
        
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=5)
    
    def _on_pattern_change(self):
        """Handle pattern selection change"""
        pattern = self.pattern_var.get()
        
        # Show/hide template frame for custom pattern
        if pattern == RenamePattern.CUSTOM:
            self.template_frame.pack(fill="x", padx=10, pady=5, after=self.pattern_var.master)
        else:
            self.template_frame.pack_forget()
    
    def _toggle_metadata(self):
        """Toggle metadata inputs visibility"""
        if self.add_metadata_var.get():
            self.metadata_inputs_frame.pack(fill="x", padx=10, pady=5)
        else:
            self.metadata_inputs_frame.pack_forget()
    
    def _select_files(self):
        """Select individual image files"""
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp"),
                ("All Files", "*.*")
            ]
        )
        
        if files:
            self.selected_files = list(files)
            self._update_file_count()
    
    def _select_folder(self):
        """Select folder and get all images"""
        folder = filedialog.askdirectory(title="Select Folder")
        
        if folder:
            # Find all image files in folder
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
            self.selected_files = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if os.path.splitext(f)[1].lower() in image_extensions
            ]
            self._update_file_count()
    
    def _clear_files(self):
        """Clear selected files"""
        self.selected_files = []
        self.preview_data = []
        self._update_file_count()
        self.preview_text.delete("1.0", "end")
    
    def _update_file_count(self):
        """Update file count label"""
        count = len(self.selected_files)
        if count == 0:
            self.file_count_label.configure(text="No files selected")
        elif count == 1:
            self.file_count_label.configure(text="1 file selected")
        else:
            self.file_count_label.configure(text=f"{count} files selected")
    
    def _generate_preview(self):
        """Generate rename preview"""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files first")
            return
        
        try:
            pattern = self.pattern_var.get()
            template = self.template_entry.get() if pattern == RenamePattern.CUSTOM else None
            start_index = int(self.start_index_var.get())
            
            # Generate preview
            self.preview_data = self.renamer.generate_preview(
                self.selected_files,
                pattern,
                template,
                start_index
            )
            
            # Display preview
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", "Original → New Name\n")
            self.preview_text.insert("end", "=" * 80 + "\n\n")
            
            for original, new_name in self.preview_data:
                original_name = os.path.basename(original)
                self.preview_text.insert("end", f"{original_name}\n  → {new_name}\n\n")
            
            self.status_label.configure(text=f"Preview generated for {len(self.preview_data)} files")
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")
    
    def _rename_files(self):
        """Perform the rename operation"""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files first")
            return
        
        # Confirm action
        if not messagebox.askyesno(
            "Confirm Rename",
            f"Rename {len(self.selected_files)} files?\n\nThis action can be undone."
        ):
            return
        
        # Start rename in background thread
        thread = threading.Thread(target=self._do_rename, daemon=True)
        thread.start()
    
    def _do_rename(self):
        """Perform rename in background thread"""
        try:
            # Show progress
            self.after(0, lambda: self.progress.pack(fill="x", padx=10, pady=5))
            self.after(0, lambda: self.progress.set(0))
            self.after(0, lambda: self.status_label.configure(text="Renaming files..."))
            
            pattern = self.pattern_var.get()
            template = self.template_entry.get() if pattern == RenamePattern.CUSTOM else None
            start_index = int(self.start_index_var.get())
            
            # Get metadata if enabled
            metadata = None
            if self.add_metadata_var.get():
                metadata = {
                    'copyright': self.copyright_entry.get(),
                    'author': self.author_entry.get(),
                    'description': self.description_entry.get()
                }
            
            # Progress callback
            def update_progress(current, total, filename):
                progress_val = current / total
                self.after(0, lambda: self.progress.set(progress_val))
                self.after(0, lambda: self.status_label.configure(
                    text=f"Renaming {current}/{total}: {os.path.basename(filename)}"
                ))
            
            # Perform rename
            successes, errors = self.renamer.batch_rename(
                self.selected_files,
                pattern,
                template,
                start_index,
                metadata,
                update_progress
            )
            
            # Update UI
            self.after(0, lambda: self.progress.pack_forget())
            
            if errors:
                error_msg = f"Renamed {len(successes)} files successfully.\n\n"
                error_msg += f"Errors ({len(errors)}):\n"
                error_msg += "\n".join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_msg += f"\n... and {len(errors) - 10} more"
                
                self.after(0, lambda: messagebox.showwarning("Partial Success", error_msg))
                self.after(0, lambda: self.status_label.configure(
                    text=f"Renamed {len(successes)} files with {len(errors)} errors"
                ))
            else:
                self.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Successfully renamed {len(successes)} files!"
                ))
                self.after(0, lambda: self.status_label.configure(
                    text=f"Successfully renamed {len(successes)} files"
                ))
            
            # Clear selection
            self.after(0, self._clear_files)
            
        except Exception as e:
            logger.error(f"Error renaming files: {e}")
            self.after(0, lambda: self.progress.pack_forget())
            self.after(0, lambda: messagebox.showerror("Error", f"Rename failed: {str(e)}"))
            self.after(0, lambda: self.status_label.configure(text="Error during rename"))
    
    def _undo_rename(self):
        """Undo the last rename operation"""
        if messagebox.askyesno("Confirm Undo", "Undo the last batch rename?"):
            success = self.renamer.undo_last_rename()
            
            if success:
                messagebox.showinfo("Success", "Last rename operation undone")
                self.status_label.configure(text="Undo successful")
            else:
                messagebox.showwarning("No History", "No rename operations to undo")
                self.status_label.configure(text="Nothing to undo")
    
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
            
            # Pattern selection tooltips
            if hasattr(self, 'date_created_radio'):
                tooltip = get_tooltip("date") or get_tooltip("rename")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.date_created_radio, tooltip))
            
            # Template input tooltip
            if hasattr(self, 'template_entry'):
                tooltip = get_tooltip("template") or get_tooltip("custom") or get_tooltip("pattern")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.template_entry, tooltip))
            
            # Metadata tooltips
            if hasattr(self, 'copyright_entry'):
                tooltip = get_tooltip("copyright") or get_tooltip("metadata")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.copyright_entry, tooltip))
            
            # Preview tooltip
            if hasattr(self, 'preview_textbox'):
                tooltip = get_tooltip("preview")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.preview_textbox, tooltip))
            
            # Undo tooltip
            if hasattr(self, 'undo_btn'):
                tooltip = get_tooltip("undo")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.undo_btn, tooltip))
                    
        except Exception as e:
            logger.error(f"Error adding tooltips to Batch Rename Panel: {e}")


def open_batch_rename_dialog(parent):
    """Open batch rename dialog"""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Batch Rename Tool")
    dialog.geometry("800x900")
    
    panel = BatchRenamePanel(dialog)
    panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    return dialog
