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
    from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                  QProgressBar, QPushButton, QFrame, QWidget)
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont
    GUI_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    GUI_AVAILABLE = False
    logger.warning("PyQt6 not available")


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
        self.dialog = QDialog(self.parent)
        self.dialog.setWindowTitle(self.title)
        self.dialog.resize(900, 600)
        
        # Make it modal
        self.dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Main layout
        main_layout = QVBoxLayout(self.dialog)
        
        # Title
        title_label = QLabel("🔍 Batch Upscaling in Progress 🔍")
        title_font = QFont("Arial", 20, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        main_layout.addSpacing(15)
        
        # Main content frame
        content_frame = QFrame()
        content_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        content_layout = QVBoxLayout(content_frame)
        
        # Queue information
        queue_frame = QFrame()
        queue_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        queue_layout = QVBoxLayout(queue_frame)
        
        queue_title = QLabel("📁 Folder Queue:")
        queue_title_font = QFont("Arial", 13, QFont.Weight.Bold)
        queue_title.setFont(queue_title_font)
        queue_layout.addWidget(queue_title)
        
        self.queue_label = QLabel("Processing folder 1 of 1")
        queue_label_font = QFont("Arial", 12)
        self.queue_label.setFont(queue_label_font)
        self.queue_label.setContentsMargins(20, 2, 10, 2)
        queue_layout.addWidget(self.queue_label)
        
        content_layout.addWidget(queue_frame)
        
        # Current operation section
        current_frame = QFrame()
        current_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        current_layout = QVBoxLayout(current_frame)
        
        current_title = QLabel("📂 Current Location:")
        current_title.setFont(queue_title_font)
        current_layout.addWidget(current_title)
        
        # Current folder
        self.current_folder_label = QLabel("Folder: ...")
        label_font = QFont("Arial", 11)
        self.current_folder_label.setFont(label_font)
        self.current_folder_label.setWordWrap(True)
        self.current_folder_label.setContentsMargins(20, 2, 10, 2)
        current_layout.addWidget(self.current_folder_label)
        
        # Current subfolder
        self.current_subfolder_label = QLabel("Subfolder: None")
        self.current_subfolder_label.setFont(label_font)
        self.current_subfolder_label.setWordWrap(True)
        self.current_subfolder_label.setContentsMargins(20, 2, 10, 2)
        current_layout.addWidget(self.current_subfolder_label)
        
        # Current file
        self.current_file_label = QLabel("File: ...")
        self.current_file_label.setFont(label_font)
        self.current_file_label.setWordWrap(True)
        self.current_file_label.setContentsMargins(20, 2, 10, 2)
        current_layout.addWidget(self.current_file_label)
        
        content_layout.addWidget(current_frame)
        
        # Progress bar
        progress_frame = QFrame()
        progress_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        progress_layout = QVBoxLayout(progress_frame)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        content_layout.addWidget(progress_frame)
        
        # Statistics section
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_title = QLabel("📊 Statistics:")
        stats_title.setFont(queue_title_font)
        stats_layout.addWidget(stats_title)
        
        self.stats_label = QLabel("Processed: 0 / 0 | Failed: 0 | Skipped: 0")
        self.stats_label.setFont(label_font)
        self.stats_label.setContentsMargins(20, 2, 10, 2)
        stats_layout.addWidget(self.stats_label)
        
        self.time_label = QLabel("Elapsed: 0s | Estimated remaining: Calculating...")
        self.time_label.setFont(label_font)
        self.time_label.setContentsMargins(20, 2, 10, 2)
        stats_layout.addWidget(self.time_label)
        
        self.storage_label = QLabel("Processed: 0 MB | Estimated output: Calculating...")
        self.storage_label.setFont(label_font)
        self.storage_label.setContentsMargins(20, 2, 10, 2)
        stats_layout.addWidget(self.storage_label)
        
        content_layout.addWidget(stats_frame)
        
        main_layout.addWidget(content_frame, 1)
        
        # Control buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.addStretch()
        
        button_font = QFont("Arial", 13, QFont.Weight.Bold)
        
        self.pause_button = QPushButton("⏸ Pause")
        self.pause_button.setFont(button_font)
        self.pause_button.setMinimumSize(150, 40)
        self.pause_button.setStyleSheet("""
            QPushButton {
                background-color: #FFA500;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #FF8C00;
            }
        """)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        button_layout.addWidget(self.pause_button)
        
        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.setFont(button_font)
        self.cancel_button.setMinimumSize(150, 40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #B22222;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8B0000;
            }
        """)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        main_layout.addWidget(button_frame)
        
        # Start time
        self.start_time = time.time()
        
        # Show dialog
        self.dialog.show()
    
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
            self.current_folder_label.setText(
                f"Folder: {self._truncate_path(folder, 100)}"
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
                self.current_subfolder_label.setText(
                    f"Subfolder: {self._truncate_path(subfolder, 100)}"
                )
            else:
                self.current_subfolder_label.setText("Subfolder: None")
    
    def set_current_file(self, filename: str):
        """
        Update current file being processed.
        
        Args:
            filename: File name
        """
        self.current_file = filename
        
        if self.current_file_label:
            self.current_file_label.setText(
                f"File: {self._truncate_path(filename, 100)}"
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
            self.progress_bar.setValue(int(progress * 100))
        
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
            self.dialog.close()
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
                self.pause_button.setText("⏸ Pause")
            
            if self.on_resume_callback:
                self.on_resume_callback()
        else:
            # Pause
            self.is_paused = True
            self.pause_time = time.time()
            
            if self.pause_button:
                self.pause_button.setText("▶ Resume")
            
            if self.on_pause_callback:
                self.on_pause_callback()
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.is_cancelled = True
        
        if self.cancel_button:
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Cancelling...")
        
        if self.on_cancel_callback:
            self.on_cancel_callback()
    
    def _update_queue_display(self):
        """Update folder queue display."""
        if self.queue_label and self.folder_queue:
            total = len(self.folder_queue)
            current = self.current_folder_index + 1
            self.queue_label.setText(
                f"Processing folder {current} of {total}"
            )
    
    def _update_stats_display(self):
        """Update statistics display."""
        if self.stats_label:
            self.stats_label.setText(
                f"Processed: {self.processed_files} / {self.total_files} | "
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
        
        self.time_label.setText(
            f"Elapsed: {elapsed_str} | Estimated remaining: {remaining_str}"
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
        
        self.storage_label.setText(
            f"Processed: {processed_mb:.1f} MB | Estimated output: {estimated_str}"
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
