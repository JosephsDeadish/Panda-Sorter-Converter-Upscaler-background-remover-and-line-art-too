"""
Quality Checker UI Panel
Provides UI for image quality analysis with detailed reports
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Optional
import logging
from PIL import Image, ImageTk
import threading

from src.tools.quality_checker import ImageQualityChecker, format_quality_report, QualityLevel

# SVG icon support
try:
    from src.utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    SVG_ICONS_AVAILABLE = False
    logger.warning("SVG icon helper not available, using emoji fallback")

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}


class QualityCheckerPanel(ctk.CTkFrame):
    """UI panel for image quality checking."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.checker = ImageQualityChecker()
        self.selected_files: List[str] = []
        self.current_report = None
        self.processing_thread = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="🔍 Image Quality Checker",
            font=("Arial Bold", 18)
        )
        title_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            self,
            text="Analyze resolution, compression, DPI, and quality scores",
            font=("Arial", 12),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Controls
        left_frame = ctk.CTkFrame(main_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # File selection
        file_frame = ctk.CTkFrame(left_frame)
        file_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(file_frame, text="📁 Files", font=("Arial Bold", 14)).pack(pady=5)
        
        btn_frame = ctk.CTkFrame(file_frame)
        btn_frame.pack(fill="x", pady=5)
        
        # Select Files button with icon
        select_files_btn = ctk.CTkButton(
            btn_frame,
            text="Select Files",
            command=self._select_files,
            width=120
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
            width=120
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("folder_open_animated", (20, 20))
            if icon:
                select_folder_btn.configure(image=icon, compound="left")
        select_folder_btn.pack(side="left", padx=5)
        
        # Clear button with icon
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear",
            command=self._clear_files,
            width=80,
            fg_color="gray"
        )
        if SVG_ICONS_AVAILABLE:
            icon = load_icon("trash_empty_animated", (20, 20))
            if icon:
                clear_btn.configure(image=icon, compound="left")
        clear_btn.pack(side="left", padx=5)
        
        self.file_count_label = ctk.CTkLabel(file_frame, text="No files selected")
        self.file_count_label.pack(pady=5)
        
        # Settings
        settings_frame = ctk.CTkFrame(left_frame)
        settings_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(settings_frame, text="⚙️ Settings", font=("Arial Bold", 14)).pack(pady=5)
        
        # Target DPI
        dpi_frame = ctk.CTkFrame(settings_frame)
        dpi_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(dpi_frame, text="Target DPI:").pack(side="left", padx=5)
        
        self.dpi_var = ctk.StringVar(value="72")
        dpi_options = ["72", "150", "300", "600"]
        self.dpi_menu = ctk.CTkOptionMenu(
            dpi_frame,
            variable=self.dpi_var,
            values=dpi_options,
            width=100
        )
        self.dpi_menu.pack(side="left", padx=5)
        
        ctk.CTkLabel(dpi_frame, text="(72=screen, 300=print)", 
                    font=("Arial", 10), text_color="gray").pack(side="left", padx=5)
        
        # Action buttons
        action_frame = ctk.CTkFrame(left_frame)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.check_button = ctk.CTkButton(
            action_frame,
            text="🔍 Check Quality",
            command=self._check_quality,
            height=40,
            font=("Arial Bold", 14)
        )
        self.check_button.pack(fill="x", pady=5)
        
        self.export_button = ctk.CTkButton(
            action_frame,
            text="📄 Export Report",
            command=self._export_report,
            state="disabled"
        )
        self.export_button.pack(fill="x", pady=5)
        
        # Progress
        self.progress_label = ctk.CTkLabel(left_frame, text="")
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(left_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        # Right side - Results
        right_frame = ctk.CTkFrame(main_container)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(right_frame, text="📊 Results", font=("Arial Bold", 14)).pack(pady=10)
        
        # Results text box
        self.results_text = ctk.CTkTextbox(right_frame, wrap="word")
        self.results_text.pack(fill="both", expand=True, padx=10, pady=10)
    
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
    
    def _clear_files(self):
        """Clear selected files."""
        self.selected_files = []
        self._update_file_count()
        self.results_text.delete("1.0", "end")
        self.current_report = None
        self.export_button.configure(state="disabled")
    
    def _update_file_count(self):
        """Update file count label."""
        count = len(self.selected_files)
        if count == 0:
            self.file_count_label.configure(text="No files selected")
        elif count == 1:
            self.file_count_label.configure(text="1 file selected")
        else:
            self.file_count_label.configure(text=f"{count} files selected")
    
    def _check_quality(self):
        """Check quality of selected files."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to check")
            return
        
        # Disable button during processing
        self.check_button.configure(state="disabled")
        self.results_text.delete("1.0", "end")
        self.progress_bar.set(0)
        
        # Run in thread
        self.processing_thread = threading.Thread(target=self._run_quality_check, daemon=True)
        self.processing_thread.start()
    
    def _run_quality_check(self):
        """Run quality check in background thread."""
        try:
            target_dpi = float(self.dpi_var.get())
            
            def progress_callback(current, total, filename):
                progress = current / total
                self.after(0, lambda: self.progress_bar.set(progress))
                self.after(0, lambda: self.progress_label.configure(
                    text=f"Checking {current}/{total}: {filename}"
                ))
            
            # Check quality
            reports = []
            for i, path in enumerate(self.selected_files):
                report = self.checker.check_quality(path, target_dpi)
                reports.append(report)
                progress_callback(i + 1, len(self.selected_files), Path(path).name)
            
            # Store for export
            self.current_report = reports
            
            # Generate display text
            if len(reports) == 1:
                # Single file - show detailed report
                text = format_quality_report(reports[0], detailed=True)
            else:
                # Multiple files - show summary + list
                summary = self.checker.generate_summary_report(reports)
                
                lines = []
                lines.append("=" * 60)
                lines.append("BATCH QUALITY REPORT")
                lines.append("=" * 60)
                lines.append(f"\nTotal Images: {summary['total_images']}")
                lines.append(f"Average Quality Score: {summary['average_score']:.1f}/100")
                lines.append(f"Average Resolution: {summary['average_resolution']:.0f}px")
                lines.append(f"Average Sharpness: {summary['average_sharpness']:.1f}/100")
                lines.append(f"Average Noise: {summary['average_noise']:.1f}/100")
                
                lines.append("\n📊 Quality Distribution:")
                for level, count in summary['quality_distribution'].items():
                    if count > 0:
                        percentage = (count / summary['total_images']) * 100
                        lines.append(f"  {level}: {count} ({percentage:.1f}%)")
                
                lines.append("\n⚠️ Issues Found:")
                lines.append(f"  Low Resolution: {summary['low_resolution_count']} "
                           f"({summary['low_resolution_percentage']:.1f}%)")
                lines.append(f"  Compression Artifacts: {summary['compression_artifacts_count']} "
                           f"({summary['compression_artifacts_percentage']:.1f}%)")
                
                lines.append("\n" + "=" * 60)
                lines.append("INDIVIDUAL REPORTS")
                lines.append("=" * 60)
                
                for report in reports:
                    lines.append("\n" + format_quality_report(report, detailed=False))
                
                text = "\n".join(lines)
            
            # Update UI
            self.after(0, lambda: self.results_text.insert("1.0", text))
            self.after(0, lambda: self.export_button.configure(state="normal"))
            self.after(0, lambda: self.progress_label.configure(text="✓ Quality check complete"))
            
        except Exception as e:
            logger.error(f"Error checking quality: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Quality check failed: {e}"))
        
        finally:
            self.after(0, lambda: self.check_button.configure(state="normal"))
    
    def _export_report(self):
        """Export report to text file."""
        if not self.current_report:
            return
        
        output_file = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if output_file:
            try:
                text = self.results_text.get("1.0", "end")
                Path(output_file).write_text(text, encoding='utf-8')
                messagebox.showinfo("Success", f"Report saved to:\n{output_file}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report: {e}")
