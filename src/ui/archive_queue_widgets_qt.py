"""
Archive Settings Widget and Processing Queue System - PyQt6 Version
Provides archive support with ZIP/file mode selection and batch processing queue
"""

import logging
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QLineEdit, QSlider, QFrame,
    QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

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


class ArchiveSettingsWidgetQt(QWidget):
    """
    Qt widget for archive output settings with checkbox for ZIP mode.
    """
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.output_mode = OutputMode.INDIVIDUAL_FILES
        self.compression_level = 6  # 0-9
        self.archive_name = "processed_images"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the archive settings widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("📦 Output Settings")
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title_label)
        
        # Archive mode checkbox
        self.archive_checkbox = QCheckBox("💾 Create ZIP archive")
        self.archive_checkbox.stateChanged.connect(self._on_mode_change)
        layout.addWidget(self.archive_checkbox)
        
        # Format frame (hidden by default)
        self.format_frame = QWidget()
        format_layout = QVBoxLayout(self.format_frame)
        format_layout.setContentsMargins(20, 0, 0, 0)
        
        # Format selection
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["ZIP", "7-Zip"])
        self.format_combo.currentTextChanged.connect(self._on_format_change)
        format_row.addWidget(self.format_combo)
        format_row.addStretch()
        format_layout.addLayout(format_row)
        
        # Archive name
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self.name_entry = QLineEdit(self.archive_name)
        self.name_entry.textChanged.connect(self._on_name_change)
        name_row.addWidget(self.name_entry)
        format_layout.addLayout(name_row)
        
        # Compression level
        compression_row = QHBoxLayout()
        compression_row.addWidget(QLabel("Compression:"))
        self.compression_slider = QSlider(Qt.Orientation.Horizontal)
        self.compression_slider.setRange(0, 9)
        self.compression_slider.setValue(6)
        self.compression_slider.valueChanged.connect(self._on_compression_change)
        compression_row.addWidget(self.compression_slider)
        self.compression_label = QLabel("6")
        compression_row.addWidget(self.compression_label)
        format_layout.addLayout(compression_row)
        
        self.format_frame.setVisible(False)
        layout.addWidget(self.format_frame)
        
        # Info label
        self.info_label = QLabel("Individual files will be saved to output directory")
        self.info_label.setStyleSheet("color: gray;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        layout.addStretch()
    
    def _on_mode_change(self, state):
        """Handle archive mode checkbox change."""
        is_archive = self.archive_checkbox.isChecked()
        
        if is_archive:
            self.format_frame.setVisible(True)
            self.output_mode = OutputMode.ZIP_ARCHIVE
            self.info_label.setText(f"Files will be saved to {self.archive_name}.zip")
            self.info_label.setStyleSheet("color: white;")
        else:
            self.format_frame.setVisible(False)
            self.output_mode = OutputMode.INDIVIDUAL_FILES
            self.info_label.setText("Individual files will be saved to output directory")
            self.info_label.setStyleSheet("color: gray;")
        
        logger.info(f"Output mode changed to: {self.output_mode}")
        self.settings_changed.emit(self.get_settings())
    
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
        
        self.info_label.setText(f"Files will be saved to {self.archive_name}{ext}")
        self.settings_changed.emit(self.get_settings())
    
    def _on_name_change(self, text):
        """Handle archive name change."""
        self.archive_name = text or "processed_images"
        if self.archive_checkbox.isChecked():
            ext = ".zip" if self.format_combo.currentText() == "ZIP" else ".7z"
            self.info_label.setText(f"Files will be saved to {self.archive_name}{ext}")
        self.settings_changed.emit(self.get_settings())
    
    def _on_compression_change(self, value):
        """Handle compression level change."""
        self.compression_level = value
        self.compression_label.setText(str(value))
        self.settings_changed.emit(self.get_settings())
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current archive settings."""
        return {
            'mode': self.output_mode,
            'archive_name': self.name_entry.text() or self.archive_name,
            'compression_level': self.compression_level
        }
    
    def set_archive_mode(self, enabled: bool):
        """Programmatically set archive mode."""
        self.archive_checkbox.setChecked(enabled)


class ProcessingQueueQt(QWidget):
    """
    Qt processing queue widget with visualization and controls.
    Handles batch processing with pause/resume/cancel capabilities.
    """
    
    processing_started = pyqtSignal()
    processing_paused = pyqtSignal()
    processing_completed = pyqtSignal()
    item_completed = pyqtSignal(str, str)  # item_id, status
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.queue: List[QueueItem] = []
        self.current_index = -1
        self.is_processing = False
        self.is_paused = False
        self.processing_thread: Optional[threading.Thread] = None
        self.process_callback: Optional[Callable] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the queue widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header with controls
        header_frame = QWidget()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("🔄 Processing Queue")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        header_layout.addWidget(title_label)
        
        self.queue_count_label = QLabel("0 items")
        self.queue_count_label.setStyleSheet("color: gray; font-size: 11pt;")
        header_layout.addWidget(self.queue_count_label)
        
        header_layout.addStretch()
        
        # Control buttons
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setStyleSheet("background-color: #10B981; color: white; padding: 5px;")
        self.start_btn.clicked.connect(self.start_processing)
        header_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_processing)
        header_layout.addWidget(self.pause_btn)
        
        self.clear_btn = QPushButton("🗑 Clear")
        self.clear_btn.setStyleSheet("background-color: gray; color: white; padding: 5px;")
        self.clear_btn.clicked.connect(self.clear_queue)
        header_layout.addWidget(self.clear_btn)
        
        layout.addWidget(header_frame)
        
        # Queue list (scrollable)
        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setMinimumHeight(200)
        
        self.queue_container = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setSpacing(2)
        self.queue_layout.addStretch()
        
        self.queue_scroll.setWidget(self.queue_container)
        layout.addWidget(self.queue_scroll)
        
        # Progress info
        progress_frame = QWidget()
        progress_layout = QHBoxLayout(progress_frame)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_label = QLabel("Queue is empty")
        self.progress_label.setStyleSheet("color: gray; font-size: 10pt;")
        progress_layout.addWidget(self.progress_label)
        
        progress_layout.addStretch()
        
        self.eta_label = QLabel("")
        self.eta_label.setStyleSheet("color: gray; font-size: 10pt;")
        progress_layout.addWidget(self.eta_label)
        
        layout.addWidget(progress_frame)
    
    def add_item(self, item: QueueItem):
        """Add item to queue."""
        self.queue.append(item)
        self._update_ui()
        logger.info(f"Added item to queue: {item.id}")
    
    def add_items(self, items: List[QueueItem]):
        """Add multiple items to queue."""
        self.queue.extend(items)
        self._update_ui()
        logger.info(f"Added {len(items)} items to queue")
    
    def clear_queue(self):
        """Clear all items from queue."""
        if self.is_processing:
            logger.warning("Cannot clear queue while processing")
            return
        
        self.queue.clear()
        self.current_index = -1
        self._update_ui()
        logger.info("Queue cleared")
    
    def start_processing(self):
        """Start processing the queue."""
        if not self.queue or self.is_processing:
            return
        
        self.is_processing = True
        self.is_paused = False
        self.current_index = 0
        
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.clear_btn.setEnabled(False)
        
        self.processing_started.emit()
        self._update_ui()
        
        # Start processing in thread if callback is set
        if self.process_callback:
            self.processing_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.processing_thread.start()
        
        logger.info("Processing started")
    
    def pause_processing(self):
        """Pause/resume processing."""
        if not self.is_processing:
            return
        
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_btn.setText("▶ Resume")
            self.processing_paused.emit()
            logger.info("Processing paused")
        else:
            self.pause_btn.setText("⏸ Pause")
            logger.info("Processing resumed")
        
        self._update_ui()
    
    def _process_queue(self):
        """Process queue items (runs in thread)."""
        while self.current_index < len(self.queue):
            if not self.is_processing:
                break
            
            while self.is_paused:
                if not self.is_processing:
                    break
                threading.Event().wait(0.1)
            
            item = self.queue[self.current_index]
            
            if self.process_callback:
                try:
                    self.process_callback(item)
                    item.status = "completed"
                    self.item_completed.emit(item.id, "completed")
                except Exception as e:
                    item.status = "failed"
                    item.error_message = str(e)
                    self.item_completed.emit(item.id, "failed")
                    logger.error(f"Processing failed for {item.id}: {e}")
            
            self.current_index += 1
            self._update_ui()
        
        # Processing complete
        self.is_processing = False
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)
        self.processing_completed.emit()
        self._update_ui()
        logger.info("Processing completed")
    
    def set_process_callback(self, callback: Callable):
        """Set the callback function for processing items."""
        self.process_callback = callback
    
    def _update_ui(self):
        """Update UI elements."""
        # Update count
        count = len(self.queue)
        self.queue_count_label.setText(f"{count} item{'s' if count != 1 else ''}")
        
        # Update progress label
        if self.is_processing:
            completed = sum(1 for item in self.queue if item.status == "completed")
            self.progress_label.setText(
                f"Processing: {completed}/{len(self.queue)} completed"
            )
        elif count == 0:
            self.progress_label.setText("Queue is empty")
        else:
            self.progress_label.setText(f"{count} items ready to process")
        
        # Update queue list display
        # Clear existing items
        for i in reversed(range(self.queue_layout.count())):
            widget = self.queue_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Add queue items
        for i, item in enumerate(self.queue):
            item_widget = self._create_queue_item_widget(item, i)
            self.queue_layout.insertWidget(i, item_widget)
        
        self.queue_layout.addStretch()
    
    def _create_queue_item_widget(self, item: QueueItem, index: int) -> QWidget:
        """Create widget for a queue item."""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Status icon
        status_icons = {
            "pending": "⏳",
            "processing": "⚙️",
            "completed": "✓",
            "failed": "✗",
            "cancelled": "🚫"
        }
        status_label = QLabel(status_icons.get(item.status, "?"))
        layout.addWidget(status_label)
        
        # Filename
        filename = Path(item.input_path).name
        name_label = QLabel(filename)
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Status text
        status_text = QLabel(item.status.capitalize())
        if item.status == "completed":
            status_text.setStyleSheet("color: green;")
        elif item.status == "failed":
            status_text.setStyleSheet("color: red;")
        elif item.status == "processing":
            status_text.setStyleSheet("color: blue;")
        layout.addWidget(status_text)
        
        return widget
