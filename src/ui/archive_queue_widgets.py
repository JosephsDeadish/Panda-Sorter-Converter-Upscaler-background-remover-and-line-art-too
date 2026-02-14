"""
Archive Settings Widget and Processing Queue System
Provides archive support with ZIP/file mode selection and batch processing queue
Author: Dead On The Inside / JosephsDeadish
"""

import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from enum import Enum
import logging
from dataclasses import dataclass
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class OutputMode(Enum):
    """Output mode for processed files."""
    INDIVIDUAL_FILES = "individual"
    ZIP_ARCHIVE = "zip"
    SEVEN_ZIP_ARCHIVE = "7z"


@dataclass
class QueueItem:
    """Item in the processing queue."""
    id: str
    input_path: str
    output_path: str
    status: str  # pending, processing, completed, failed, cancelled
    progress: float  # 0.0 to 1.0
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ArchiveSettingsWidget(ctk.CTkFrame):
    """
    Widget for archive output settings with checkbox for ZIP mode.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.output_mode = OutputMode.INDIVIDUAL_FILES
        self.compression_level = 6  # 0-9
        self.archive_name = "processed_images"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the archive settings widgets."""
        # Title
        ctk.CTkLabel(
            self,
            text="📦 Output Settings",
            font=("Arial Bold", 12)
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Output mode frame
        mode_frame = ctk.CTkFrame(self)
        mode_frame.pack(fill="x", padx=10, pady=5)
        
        # Checkbox for archive mode
        self.archive_mode_var = ctk.BooleanVar(value=False)
        self.archive_checkbox = ctk.CTkCheckBox(
            mode_frame,
            text="💾 Create ZIP archive",
            variable=self.archive_mode_var,
            command=self._on_mode_change,
            font=("Arial", 11)
        )
        self.archive_checkbox.pack(anchor="w", padx=5, pady=5)
        
        # Archive format dropdown (only shown when archive mode is on)
        self.format_frame = ctk.CTkFrame(mode_frame)
        
        format_label_frame = ctk.CTkFrame(self.format_frame)
        format_label_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(
            format_label_frame,
            text="Format:",
            width=80
        ).pack(side="left", padx=5)
        
        self.format_var = ctk.StringVar(value="ZIP")
        self.format_menu = ctk.CTkOptionMenu(
            format_label_frame,
            variable=self.format_var,
            values=["ZIP", "7-Zip"],
            command=self._on_format_change,
            width=120
        )
        self.format_menu.pack(side="left", padx=5)
        
        # Archive name input
        name_frame = ctk.CTkFrame(self.format_frame)
        name_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(
            name_frame,
            text="Name:",
            width=80
        ).pack(side="left", padx=5)
        
        self.name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="archive_name"
        )
        self.name_entry.insert(0, self.archive_name)
        self.name_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Compression level slider
        compression_frame = ctk.CTkFrame(self.format_frame)
        compression_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(
            compression_frame,
            text="Compression:",
            width=80
        ).pack(side="left", padx=5)
        
        self.compression_slider = ctk.CTkSlider(
            compression_frame,
            from_=0,
            to=9,
            number_of_steps=9,
            command=self._on_compression_change
        )
        self.compression_slider.set(self.compression_level)
        self.compression_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        self.compression_label = ctk.CTkLabel(
            compression_frame,
            text=f"{self.compression_level}",
            width=30
        )
        self.compression_label.pack(side="left", padx=5)
        
        # Info label
        self.info_label = ctk.CTkLabel(
            self,
            text="Individual files will be saved to output directory",
            font=("Arial", 9),
            text_color="gray"
        )
        self.info_label.pack(padx=10, pady=5)
    
    def _on_mode_change(self):
        """Handle archive mode checkbox change."""
        is_archive = self.archive_mode_var.get()
        
        if is_archive:
            self.format_frame.pack(fill="x", padx=10, pady=5)
            self.output_mode = OutputMode.ZIP_ARCHIVE
            self.info_label.configure(
                text=f"Files will be saved to {self.archive_name}.zip",
                text_color="white"
            )
        else:
            self.format_frame.pack_forget()
            self.output_mode = OutputMode.INDIVIDUAL_FILES
            self.info_label.configure(
                text="Individual files will be saved to output directory",
                text_color="gray"
            )
        
        logger.info(f"Output mode changed to: {self.output_mode}")
    
    def _on_format_change(self, format_name: str):
        """Handle archive format change."""
        if format_name == "ZIP":
            self.output_mode = OutputMode.ZIP_ARCHIVE
            ext = ".zip"
        elif format_name == "7-Zip":
            self.output_mode = OutputMode.SEVEN_ZIP_ARCHIVE
            ext = ".7z"
        else:
            ext = ".zip"
        
        self.info_label.configure(
            text=f"Files will be saved to {self.archive_name}{ext}"
        )
    
    def _on_compression_change(self, value):
        """Handle compression level change."""
        self.compression_level = int(value)
        self.compression_label.configure(text=f"{self.compression_level}")
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current archive settings."""
        return {
            'mode': self.output_mode,
            'archive_name': self.name_entry.get() or self.archive_name,
            'compression_level': self.compression_level
        }
    
    def set_archive_mode(self, enabled: bool):
        """Programmatically set archive mode."""
        self.archive_mode_var.set(enabled)
        self._on_mode_change()


class ProcessingQueue(ctk.CTkFrame):
    """
    Processing queue widget with visualization and controls.
    Handles batch processing with pause/resume/cancel capabilities.
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.queue: List[QueueItem] = []
        self.current_index = -1
        self.is_processing = False
        self.is_paused = False
        self.processing_thread: Optional[threading.Thread] = None
        self.process_callback: Optional[Callable] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the queue widgets."""
        # Title with controls
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            header_frame,
            text="🔄 Processing Queue",
            font=("Arial Bold", 14)
        ).pack(side="left", padx=10)
        
        self.queue_count_label = ctk.CTkLabel(
            header_frame,
            text="0 items",
            font=("Arial", 11),
            text_color="gray"
        )
        self.queue_count_label.pack(side="left", padx=10)
        
        # Control buttons
        btn_frame = ctk.CTkFrame(header_frame)
        btn_frame.pack(side="right", padx=10)
        
        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ Start",
            command=self.start_processing,
            width=80,
            fg_color="#10B981",
            hover_color="#059669"
        )
        self.start_btn.pack(side="left", padx=2)
        
        self.pause_btn = ctk.CTkButton(
            btn_frame,
            text="⏸ Pause",
            command=self.pause_processing,
            width=80,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=2)
        
        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="🗑 Clear",
            command=self.clear_queue,
            width=80,
            fg_color="gray40"
        )
        self.clear_btn.pack(side="left", padx=2)
        
        # Queue list (scrollable)
        self.queue_list = ctk.CTkScrollableFrame(self, height=200)
        self.queue_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Progress info
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=5, pady=5)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Queue is empty",
            font=("Arial", 10),
            text_color="gray"
        )
        self.progress_label.pack(side="left", padx=10)
        
        self.eta_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=("Arial", 10),
            text_color="gray"
        )
        self.eta_label.pack(side="right", padx=10)
    
    def add_item(self, input_path: str, output_path: str) -> str:
        """Add an item to the queue."""
        import uuid
        item_id = str(uuid.uuid4())
        
        item = QueueItem(
            id=item_id,
            input_path=input_path,
            output_path=output_path,
            status="pending",
            progress=0.0
        )
        
        self.queue.append(item)
        self._update_queue_display()
        
        return item_id
    
    def add_items(self, paths: List[tuple]):
        """Add multiple items to the queue."""
        for input_path, output_path in paths:
            self.add_item(input_path, output_path)
    
    def remove_item(self, item_id: str):
        """Remove an item from the queue."""
        self.queue = [item for item in self.queue if item.id != item_id]
        self._update_queue_display()
    
    def clear_queue(self):
        """Clear all items from the queue."""
        if self.is_processing:
            if not messagebox.askyesno(
                "Clear Queue",
                "Processing is in progress. Cancel and clear queue?"
            ):
                return
            self.stop_processing()
        
        self.queue.clear()
        self.current_index = -1
        self._update_queue_display()
    
    def set_process_callback(self, callback: Callable):
        """Set the callback function for processing items."""
        self.process_callback = callback
    
    def start_processing(self):
        """Start processing the queue."""
        if not self.queue or self.is_processing:
            return
        
        if not self.process_callback:
            logger.error("No process callback set")
            return
        
        self.is_processing = True
        self.is_paused = False
        
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        
        self.processing_thread = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self.processing_thread.start()
    
    def pause_processing(self):
        """Pause/resume processing."""
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_btn.configure(text="▶ Resume")
            self.progress_label.configure(text="Paused")
        else:
            self.pause_btn.configure(text="⏸ Pause")
    
    def stop_processing(self):
        """Stop processing the queue."""
        self.is_processing = False
        self.is_paused = False
        
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="⏸ Pause")
    
    def _process_queue(self):
        """Process all items in the queue."""
        start_index = self.current_index + 1 if self.current_index >= 0 else 0
        
        for i in range(start_index, len(self.queue)):
            if not self.is_processing:
                break
            
            # Wait if paused
            while self.is_paused:
                if not self.is_processing:
                    break
                threading.Event().wait(0.1)
            
            if not self.is_processing:
                break
            
            self.current_index = i
            item = self.queue[i]
            
            # Update status
            item.status = "processing"
            item.started_at = datetime.now()
            self._update_item_display(item)
            
            # Process item
            try:
                if self.process_callback:
                    self.process_callback(item.input_path, item.output_path)
                
                item.status = "completed"
                item.progress = 1.0
                item.completed_at = datetime.now()
            except Exception as e:
                logger.error(f"Processing failed for {item.input_path}: {e}")
                item.status = "failed"
                item.error_message = str(e)
            
            self._update_item_display(item)
        
        self.stop_processing()
        self.progress_label.configure(
            text="Queue complete",
            text_color="#10B981"
        )
    
    def _update_queue_display(self):
        """Update the queue list display."""
        # Clear existing items
        for widget in self.queue_list.winfo_children():
            widget.destroy()
        
        # Update count
        self.queue_count_label.configure(text=f"{len(self.queue)} items")
        
        if not self.queue:
            self.progress_label.configure(
                text="Queue is empty",
                text_color="gray"
            )
            return
        
        # Add items to list
        for item in self.queue:
            self._create_item_widget(item)
        
        # Update progress
        completed = sum(1 for item in self.queue if item.status == "completed")
        total = len(self.queue)
        self.progress_label.configure(
            text=f"Processed {completed}/{total} items",
            text_color="white"
        )
    
    def _create_item_widget(self, item: QueueItem):
        """Create a widget for a queue item."""
        item_frame = ctk.CTkFrame(self.queue_list)
        item_frame.pack(fill="x", padx=5, pady=2)
        
        # Status icon
        status_icons = {
            "pending": "⏳",
            "processing": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫"
        }
        
        icon_label = ctk.CTkLabel(
            item_frame,
            text=status_icons.get(item.status, "⏳"),
            width=30,
            font=("Arial", 14)
        )
        icon_label.pack(side="left", padx=5)
        
        # File name
        file_name = Path(item.input_path).name
        name_label = ctk.CTkLabel(
            item_frame,
            text=file_name,
            anchor="w",
            font=("Arial", 10)
        )
        name_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # Remove button
        remove_btn = ctk.CTkButton(
            item_frame,
            text="✕",
            width=30,
            command=lambda: self.remove_item(item.id),
            fg_color="transparent",
            hover_color="gray30"
        )
        remove_btn.pack(side="right", padx=2)
    
    def _update_item_display(self, item: QueueItem):
        """Update the display for a specific item."""
        self._update_queue_display()
