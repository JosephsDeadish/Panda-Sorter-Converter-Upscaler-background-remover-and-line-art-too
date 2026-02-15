"""
Batch Progress Dialog
Enhanced dialog for showing batch upscaling progress with detailed tracking
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import time
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Constants
BYTES_PER_MB = 1024 * 1024

try:
    import customtkinter as ctk
    import tkinter as tk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    logger.warning("CustomTkinter not available")


class BatchProgressDialog:
    """
    Enhanced progress dialog for batch operations.
    
    Features:
    - Multi-folder queue tracking
    - Current folder/subfolder/file display
    - Time and storage estimates
    - Pause/resume/cancel controls
    - Real-time statistics
    """
    
    def __init__(self, parent, title: str = "Batch Upscaling Progress"):
        """
        Initialize batch progress dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
        """
        self.parent = parent
        self.dialog = None
        self.title = title
        
        # State tracking
        self.is_paused = False
        self.is_cancelled = False
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0.0
        
        # Progress tracking
        self.current_folder = ""
        self.current_subfolder = ""
        self.current_file = ""
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.skipped_files = 0
        self.total_size_bytes = 0
        self.processed_size_bytes = 0
        
        # Folder queue
        self.folder_queue = []
        self.current_folder_index = 0
        
        # Callbacks
        self.on_pause_callback: Optional[Callable] = None
        self.on_resume_callback: Optional[Callable] = None
        self.on_cancel_callback: Optional[Callable] = None
        
        # UI elements
        self.progress_bar = None
        self.current_folder_label = None
        self.current_subfolder_label = None
        self.current_file_label = None
        self.stats_label = None
        self.time_label = None
        self.storage_label = None
        self.queue_label = None
        self.pause_button = None
        self.cancel_button = None
    
    def show(self):
        """Display the progress dialog."""
        if not GUI_AVAILABLE:
            logger.warning("GUI not available, cannot show dialog")
            return
        
        # Create dialog window
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("900x600")
        self.dialog.resizable(True, True)
        
        # Make it modal-like (but allow interaction with cancel/pause)
        self.dialog.grab_set()
        self.dialog.focus_set()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (900 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (600 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Title
        title_label = ctk.CTkLabel(
            self.dialog,
            text="🔍 Batch Upscaling in Progress 🔍",
            font=("Arial Bold", 20)
        )
        title_label.pack(pady=15)
        
        # Main content frame
        content_frame = ctk.CTkFrame(self.dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Queue information
        queue_frame = ctk.CTkFrame(content_frame)
        queue_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(
            queue_frame,
            text="📁 Folder Queue:",
            font=("Arial Bold", 13)
        ).pack(anchor="w", padx=10, pady=5)
        self.queue_label = ctk.CTkLabel(
            queue_frame,
            text="Processing folder 1 of 1",
            font=("Arial", 12),
            anchor="w"
        )
        self.queue_label.pack(anchor="w", padx=20, pady=2)
        
        # Current operation section
        current_frame = ctk.CTkFrame(content_frame)
        current_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(
            current_frame,
            text="📂 Current Location:",
            font=("Arial Bold", 13)
        ).pack(anchor="w", padx=10, pady=5)
        
        # Current folder
        self.current_folder_label = ctk.CTkLabel(
            current_frame,
            text="Folder: ...",
            font=("Arial", 11),
            anchor="w",
            wraplength=800
        )
        self.current_folder_label.pack(anchor="w", padx=20, pady=2, fill="x")
        
        # Current subfolder
        self.current_subfolder_label = ctk.CTkLabel(
            current_frame,
            text="Subfolder: None",
            font=("Arial", 11),
            anchor="w",
            wraplength=800
        )
        self.current_subfolder_label.pack(anchor="w", padx=20, pady=2, fill="x")
        
        # Current file
        self.current_file_label = ctk.CTkLabel(
            current_frame,
            text="File: ...",
            font=("Arial", 11),
            anchor="w",
            wraplength=800
        )
        self.current_file_label.pack(anchor="w", padx=20, pady=2, fill="x")
        
        # Progress bar
        progress_frame = ctk.CTkFrame(content_frame)
        progress_frame.pack(fill="x", padx=15, pady=10)
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        
        # Statistics section
        stats_frame = ctk.CTkFrame(content_frame)
        stats_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(
            stats_frame,
            text="📊 Statistics:",
            font=("Arial Bold", 13)
        ).pack(anchor="w", padx=10, pady=5)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="Processed: 0 / 0 | Failed: 0 | Skipped: 0",
            font=("Arial", 11),
            anchor="w"
        )
        self.stats_label.pack(anchor="w", padx=20, pady=2)
        
        self.time_label = ctk.CTkLabel(
            stats_frame,
            text="Elapsed: 0s | Estimated remaining: Calculating...",
            font=("Arial", 11),
            anchor="w"
        )
        self.time_label.pack(anchor="w", padx=20, pady=2)
        
        self.storage_label = ctk.CTkLabel(
            stats_frame,
            text="Processed: 0 MB | Estimated output: Calculating...",
            font=("Arial", 11),
            anchor="w"
        )
        self.storage_label.pack(anchor="w", padx=20, pady=2)
        
        # Control buttons
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.pause_button = ctk.CTkButton(
            button_frame,
            text="⏸ Pause",
            command=self._on_pause_clicked,
            width=150,
            height=40,
            font=("Arial Bold", 13),
            fg_color="#FFA500",
            hover_color="#FF8C00"
        )
        self.pause_button.pack(side="left", padx=10, pady=10)
        
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self._on_cancel_clicked,
            width=150,
            height=40,
            font=("Arial Bold", 13),
            fg_color="#B22222",
            hover_color="#8B0000"
        )
        self.cancel_button.pack(side="left", padx=10, pady=10)
        
        # Start time
        self.start_time = time.time()
    
    def set_folder_queue(self, folders: list):
        """
        Set the list of folders to process.
        
        Args:
            folders: List of folder paths
        """
        self.folder_queue = folders
        self.current_folder_index = 0
        self._update_queue_display()
    
    def set_total_files(self, count: int):
        """
        Set total number of files to process.
        
        Args:
            count: Total file count
        """
        self.total_files = count
        self._update_stats_display()
    
    def set_current_folder(self, folder: str, index: Optional[int] = None):
        """
        Update current folder being processed.
        
        Args:
            folder: Folder path
            index: Index in folder queue (optional)
        """
        self.current_folder = folder
        if index is not None:
            self.current_folder_index = index
        
        if self.current_folder_label:
            self.current_folder_label.configure(
                text=f"Folder: {self._truncate_path(folder, 100)}"
            )
        
        self._update_queue_display()
    
    def set_current_subfolder(self, subfolder: Optional[str]):
        """
        Update current subfolder being processed.
        
        Args:
            subfolder: Subfolder path or None
        """
        self.current_subfolder = subfolder or ""
        
        if self.current_subfolder_label:
            if subfolder:
                self.current_subfolder_label.configure(
                    text=f"Subfolder: {self._truncate_path(subfolder, 100)}"
                )
            else:
                self.current_subfolder_label.configure(text="Subfolder: None")
    
    def set_current_file(self, filename: str):
        """
        Update current file being processed.
        
        Args:
            filename: File name
        """
        self.current_file = filename
        
        if self.current_file_label:
            self.current_file_label.configure(
                text=f"File: {self._truncate_path(filename, 100)}"
            )
    
    def update_progress(self, processed: int, failed: int = 0, skipped: int = 0):
        """
        Update progress statistics.
        
        Args:
            processed: Number of successfully processed files
            failed: Number of failed files
            skipped: Number of skipped files
        """
        self.processed_files = processed
        self.failed_files = failed
        self.skipped_files = skipped
        
        # Update progress bar
        if self.total_files > 0 and self.progress_bar:
            progress = (processed + failed + skipped) / self.total_files
            self.progress_bar.set(progress)
        
        self._update_stats_display()
        self._update_time_display()
    
    def update_storage(self, processed_bytes: int, total_bytes: Optional[int] = None):
        """
        Update storage statistics.
        
        Args:
            processed_bytes: Bytes processed so far
            total_bytes: Total bytes (if known)
        """
        self.processed_size_bytes = processed_bytes
        if total_bytes is not None:
            self.total_size_bytes = total_bytes
        
        self._update_storage_display()
    
    def close(self):
        """Close the dialog."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None
    
    def _on_pause_clicked(self):
        """Handle pause button click."""
        if self.is_paused:
            # Resume
            self.is_paused = False
            if self.pause_time:
                self.total_pause_duration += time.time() - self.pause_time
                self.pause_time = None
            
            if self.pause_button:
                self.pause_button.configure(text="⏸ Pause")
            
            if self.on_resume_callback:
                self.on_resume_callback()
        else:
            # Pause
            self.is_paused = True
            self.pause_time = time.time()
            
            if self.pause_button:
                self.pause_button.configure(text="▶ Resume")
            
            if self.on_pause_callback:
                self.on_pause_callback()
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.is_cancelled = True
        
        if self.cancel_button:
            self.cancel_button.configure(state="disabled", text="Cancelling...")
        
        if self.on_cancel_callback:
            self.on_cancel_callback()
    
    def _update_queue_display(self):
        """Update folder queue display."""
        if self.queue_label and self.folder_queue:
            total = len(self.folder_queue)
            current = self.current_folder_index + 1
            self.queue_label.configure(
                text=f"Processing folder {current} of {total}"
            )
    
    def _update_stats_display(self):
        """Update statistics display."""
        if self.stats_label:
            self.stats_label.configure(
                text=f"Processed: {self.processed_files} / {self.total_files} | "
                     f"Failed: {self.failed_files} | Skipped: {self.skipped_files}"
            )
    
    def _update_time_display(self):
        """Update time estimates display."""
        if not self.time_label or not self.start_time:
            return
        
        # Calculate elapsed time
        elapsed = time.time() - self.start_time - self.total_pause_duration
        elapsed_str = self._format_duration(elapsed)
        
        # Estimate remaining time
        if self.processed_files > 0 and self.total_files > 0:
            avg_time_per_file = elapsed / self.processed_files
            remaining_files = self.total_files - (self.processed_files + self.failed_files + self.skipped_files)
            estimated_remaining = avg_time_per_file * remaining_files
            remaining_str = self._format_duration(estimated_remaining)
        else:
            remaining_str = "Calculating..."
        
        self.time_label.configure(
            text=f"Elapsed: {elapsed_str} | Estimated remaining: {remaining_str}"
        )
    
    def _update_storage_display(self):
        """Update storage statistics display."""
        if not self.storage_label:
            return
        
        processed_mb = self.processed_size_bytes / BYTES_PER_MB
        
        # Estimate output size based on scale factor (rough estimate)
        # This will be refined when we know the actual scale factor
        if self.processed_files > 0 and self.total_files > 0:
            avg_size_per_file = self.processed_size_bytes / self.processed_files
            estimated_total = avg_size_per_file * self.total_files
            estimated_mb = estimated_total / BYTES_PER_MB
            estimated_str = f"{estimated_mb:.1f} MB"
        else:
            estimated_str = "Calculating..."
        
        self.storage_label.configure(
            text=f"Processed: {processed_mb:.1f} MB | Estimated output: {estimated_str}"
        )
    
    def _truncate_path(self, path: str, max_length: int) -> str:
        """
        Truncate path for display.
        
        Args:
            path: Path to truncate
            max_length: Maximum length
            
        Returns:
            Truncated path
        """
        if len(path) <= max_length:
            return path
        
        # Try to keep the filename and some parent dirs
        parts = Path(path).parts
        if len(parts) > 1:
            filename = parts[-1]
            if len(filename) < max_length - 10:
                # Keep filename and truncate parents
                remaining = max_length - len(filename) - 5
                parent = str(Path(*parts[:-1]))
                if len(parent) > remaining and remaining > 3:
                    # Safe truncation: ensure remaining > 3 to avoid negative index
                    return f"...{parent[-(remaining-3):]}/{filename}"
                elif len(parent) > remaining:
                    # If remaining <= 3, just show filename
                    return f".../{filename}"
                return f"{parent}/{filename}"
        
        # Just truncate from end
        if max_length > 3:
            return f"...{path[-(max_length-3):]}"
        return path[:max_length]
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in seconds to human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
