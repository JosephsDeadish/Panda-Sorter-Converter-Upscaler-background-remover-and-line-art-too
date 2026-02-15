"""
Performance Dashboard - Pure Qt Implementation
Real-time monitoring of processing speed, memory, and queue status.
Uses PyQt6 with QTimer for updates - NO tkinter, NO customtkinter.
"""

from PyQt6.QtWidgets import (
    QWidget, QFrame, QLabel, QSlider, QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import psutil
import time
from typing import Dict, Optional
from collections import deque
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Try to import tooltip system
try:
    from src.features.tutorial_system import WidgetTooltip
    TOOLTIPS_AVAILABLE = True
except ImportError:
    WidgetTooltip = None
    TOOLTIPS_AVAILABLE = False
    logger.warning("Tooltips not available for Performance Dashboard")


class PerformanceMetrics:
    """Track performance metrics over time."""
    
    def __init__(self, history_size: int = 60):
        """
        Initialize metrics tracker.
        
        Args:
            history_size: Number of data points to keep
        """
        self.history_size = history_size
        
        # Metrics history (deques for efficient append/pop)
        self.processing_speed = deque(maxlen=history_size)  # files/second
        self.memory_usage = deque(maxlen=history_size)  # MB
        self.cpu_usage = deque(maxlen=history_size)  # percent
        self.timestamps = deque(maxlen=history_size)
        
        # Current statistics
        self.files_processed = 0
        self.bytes_processed = 0
        self.start_time = time.time()
        self.last_update = time.time()
        
        # Peak values
        self.peak_memory = 0
        self.peak_cpu = 0
        
        # Processing queue stats
        self.queue_pending = 0
        self.queue_processing = 0
        self.queue_completed = 0
        self.queue_failed = 0
    
    def update(self):
        """Update all metrics."""
        now = time.time()
        self.timestamps.append(now)
        
        # Memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        self.memory_usage.append(memory_mb)
        self.peak_memory = max(self.peak_memory, memory_mb)
        
        # CPU usage
        try:
            cpu_percent = process.cpu_percent(interval=None)
            self.cpu_usage.append(cpu_percent)
            self.peak_cpu = max(self.peak_cpu, cpu_percent)
        except:
            self.cpu_usage.append(0)
        
        # Processing speed (files per second)
        elapsed = now - self.last_update
        if elapsed > 0:
            speed = 0  # Will be updated by file processing callbacks
            self.processing_speed.append(speed)
        
        self.last_update = now
    
    def record_file_processed(self, file_size_bytes: int):
        """Record that a file was processed."""
        self.files_processed += 1
        self.bytes_processed += file_size_bytes
    
    def get_average_speed(self) -> float:
        """Get average processing speed."""
        if not self.processing_speed:
            return 0.0
        return sum(self.processing_speed) / len(self.processing_speed)
    
    def get_estimated_completion(self) -> Optional[float]:
        """
        Estimate time to completion in seconds.
        
        Returns:
            Seconds until completion or None if can't estimate
        """
        if self.queue_pending == 0:
            return 0
        
        avg_speed = self.get_average_speed()
        if avg_speed <= 0:
            return None
        
        return self.queue_pending / avg_speed
    
    def get_summary(self) -> Dict:
        """Get summary of all metrics."""
        elapsed_time = time.time() - self.start_time
        
        return {
            "files_processed": self.files_processed,
            "bytes_processed": self.bytes_processed,
            "mb_processed": self.bytes_processed / (1024 * 1024),
            "elapsed_time": elapsed_time,
            "current_memory_mb": self.memory_usage[-1] if self.memory_usage else 0,
            "peak_memory_mb": self.peak_memory,
            "current_cpu_percent": self.cpu_usage[-1] if self.cpu_usage else 0,
            "peak_cpu_percent": self.peak_cpu,
            "avg_speed_fps": self.get_average_speed(),
            "queue_pending": self.queue_pending,
            "queue_processing": self.queue_processing,
            "queue_completed": self.queue_completed,
            "queue_failed": self.queue_failed,
            "estimated_completion": self.get_estimated_completion()
        }


class PerformanceDashboard(QFrame):
    """
    Real-time performance dashboard widget using pure Qt.
    Shows processing speed, memory usage, queue status, and more.
    Uses QTimer for updates instead of tkinter .after().
    """
    
    def __init__(self, parent=None, unlockables_system=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.unlockables_system = unlockables_system
        self.tooltip_manager = tooltip_manager
        self.metrics = PerformanceMetrics()
        self.running = False
        
        # Qt timer for updates instead of tkinter .after()
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)  # 1 second
        self.update_timer.timeout.connect(self._update)
        
        # Parallel processing control
        self.max_workers = psutil.cpu_count()
        self.current_workers = 1
        
        self._tooltips = []
        self._create_widgets()
        self._add_tooltips()
    
    def _create_widgets(self):
        """Create dashboard widgets using pure Qt."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Title
        title_label = QLabel("📊 Performance Dashboard")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Content frame with grid layout
        content_frame = QFrame()
        content_layout = QGridLayout(content_frame)
        content_layout.setSpacing(5)
        
        # Left column: Processing Stats
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_title = QLabel("⚡ Processing")
        stats_title_font = QFont("Arial", 14, QFont.Weight.Bold)
        stats_title.setFont(stats_title_font)
        stats_layout.addWidget(stats_title)
        
        normal_font = QFont("Arial", 12)
        
        self.speed_label = QLabel("Speed: 0.0 files/sec")
        self.speed_label.setFont(normal_font)
        stats_layout.addWidget(self.speed_label)
        
        self.throughput_label = QLabel("Throughput: 0.0 MB/sec")
        self.throughput_label.setFont(normal_font)
        stats_layout.addWidget(self.throughput_label)
        
        self.files_processed_label = QLabel("Processed: 0 files")
        self.files_processed_label.setFont(normal_font)
        stats_layout.addWidget(self.files_processed_label)
        
        stats_layout.addStretch()
        content_layout.addWidget(stats_frame, 0, 0)
        
        # Middle column: System Resources
        resources_frame = QFrame()
        resources_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        resources_layout = QVBoxLayout(resources_frame)
        
        resources_title = QLabel("💻 System Resources")
        resources_title.setFont(stats_title_font)
        resources_layout.addWidget(resources_title)
        
        self.memory_label = QLabel("Memory: 0 MB (Peak: 0 MB)")
        self.memory_label.setFont(normal_font)
        resources_layout.addWidget(self.memory_label)
        
        self.cpu_label = QLabel("CPU: 0% (Peak: 0%)")
        self.cpu_label.setFont(normal_font)
        resources_layout.addWidget(self.cpu_label)
        
        available_memory = psutil.virtual_memory().available / (1024 * 1024 * 1024)
        self.available_label = QLabel(f"Available: {available_memory:.1f} GB")
        self.available_label.setFont(normal_font)
        resources_layout.addWidget(self.available_label)
        
        resources_layout.addStretch()
        content_layout.addWidget(resources_frame, 0, 1)
        
        # Right column: Queue Status
        queue_frame = QFrame()
        queue_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        queue_layout = QVBoxLayout(queue_frame)
        
        queue_title = QLabel("📋 Queue Status")
        queue_title.setFont(stats_title_font)
        queue_layout.addWidget(queue_title)
        
        self.queue_pending_label = QLabel("⏳ Pending: 0")
        self.queue_pending_label.setFont(normal_font)
        queue_layout.addWidget(self.queue_pending_label)
        
        self.queue_processing_label = QLabel("🔄 Processing: 0")
        self.queue_processing_label.setFont(normal_font)
        queue_layout.addWidget(self.queue_processing_label)
        
        self.queue_completed_label = QLabel("✅ Completed: 0")
        self.queue_completed_label.setFont(normal_font)
        queue_layout.addWidget(self.queue_completed_label)
        
        self.queue_failed_label = QLabel("❌ Failed: 0")
        self.queue_failed_label.setFont(normal_font)
        queue_layout.addWidget(self.queue_failed_label)
        
        eta_font = QFont("Arial", 12, QFont.Weight.Bold)
        self.eta_label = QLabel("ETA: --:--:--")
        self.eta_label.setFont(eta_font)
        queue_layout.addWidget(self.eta_label)
        
        queue_layout.addStretch()
        content_layout.addWidget(queue_frame, 0, 2)
        
        # Make columns equal width
        content_layout.setColumnStretch(0, 1)
        content_layout.setColumnStretch(1, 1)
        content_layout.setColumnStretch(2, 1)
        
        main_layout.addWidget(content_frame)
        
        # Parallel Processing Control
        parallel_frame = QFrame()
        parallel_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        parallel_layout = QHBoxLayout(parallel_frame)
        
        parallel_title = QLabel("⚙️ Parallel Processing:")
        parallel_title_font = QFont("Arial", 12, QFont.Weight.Bold)
        parallel_title.setFont(parallel_title_font)
        parallel_layout.addWidget(parallel_title)
        
        self.workers_slider = QSlider(Qt.Orientation.Horizontal)
        self.workers_slider.setMinimum(1)
        self.workers_slider.setMaximum(self.max_workers)
        self.workers_slider.setValue(self.current_workers)
        self.workers_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.workers_slider.setTickInterval(1)
        self.workers_slider.valueChanged.connect(self._on_workers_changed)
        parallel_layout.addWidget(self.workers_slider, 1)
        
        self.workers_label = QLabel(f"1 / {self.max_workers} workers")
        self.workers_label.setFont(normal_font)
        parallel_layout.addWidget(self.workers_label)
        
        main_layout.addWidget(parallel_frame)
    
    def start(self):
        """Start performance monitoring using Qt timer."""
        self.running = True
        self.metrics.start_time = time.time()
        self.update_timer.start()
    
    def stop(self):
        """Stop performance monitoring."""
        self.running = False
        self.update_timer.stop()
    
    def _update(self):
        """Update dashboard display using Qt widgets."""
        if not self.running:
            return
        
        # Update metrics
        self.metrics.update()
        summary = self.metrics.get_summary()
        
        # Update labels
        self.speed_label.setText(
            f"Speed: {summary['avg_speed_fps']:.2f} files/sec"
        )
        
        throughput_mbps = summary['mb_processed'] / max(summary['elapsed_time'], 1)
        self.throughput_label.setText(
            f"Throughput: {throughput_mbps:.2f} MB/sec"
        )
        
        self.files_processed_label.setText(
            f"Processed: {summary['files_processed']} files"
        )
        
        self.memory_label.setText(
            f"Memory: {summary['current_memory_mb']:.1f} MB (Peak: {summary['peak_memory_mb']:.1f} MB)"
        )
        
        self.cpu_label.setText(
            f"CPU: {summary['current_cpu_percent']:.1f}% (Peak: {summary['peak_cpu_percent']:.1f}%)"
        )
        
        self.queue_pending_label.setText(
            f"⏳ Pending: {summary['queue_pending']}"
        )
        
        self.queue_processing_label.setText(
            f"🔄 Processing: {summary['queue_processing']}"
        )
        
        self.queue_completed_label.setText(
            f"✅ Completed: {summary['queue_completed']}"
        )
        
        self.queue_failed_label.setText(
            f"❌ Failed: {summary['queue_failed']}"
        )
        
        # ETA
        eta_seconds = summary['estimated_completion']
        if eta_seconds is not None and eta_seconds > 0:
            eta_time = str(timedelta(seconds=int(eta_seconds)))
            self.eta_label.setText(f"ETA: {eta_time}")
        else:
            self.eta_label.setText("ETA: --:--:--")
    
    def _on_workers_changed(self, value):
        """Handle worker count slider change."""
        self.current_workers = int(value)
        self.workers_label.setText(
            f"{self.current_workers} / {self.max_workers} workers"
        )
    
    def update_queue_status(self, pending: int, processing: int, completed: int, failed: int):
        """Update queue statistics."""
        self.metrics.queue_pending = pending
        self.metrics.queue_processing = processing
        self.metrics.queue_completed = completed
        self.metrics.queue_failed = failed
    
    def record_file_processed(self, file_size_bytes: int):
        """Record that a file was processed."""
        self.metrics.record_file_processed(file_size_bytes)
    
    def get_worker_count(self) -> int:
        """Get current number of parallel workers."""
        return self.current_workers
    
    def _add_tooltips(self):
        """Add tooltips to widgets if available."""
        if not TOOLTIPS_AVAILABLE:
            return
        
        try:
            tm = self.tooltip_manager
            
            def _tt(widget_id, fallback):
                if tm:
                    text = tm.get_tooltip(widget_id)
                    if text:
                        return text
                return fallback
            
            # Processing speed tooltip
            if hasattr(self, 'speed_label'):
                self._tooltips.append(WidgetTooltip(
                    self.speed_label,
                    _tt('perf_speed', "Current processing speed in files per second"),
                    widget_id='perf_speed', tooltip_manager=tm))
            
            # Memory usage tooltip
            if hasattr(self, 'memory_label'):
                self._tooltips.append(WidgetTooltip(
                    self.memory_label,
                    _tt('perf_memory', "Current memory (RAM) used by the application"),
                    widget_id='perf_memory', tooltip_manager=tm))
            
            # CPU usage tooltip
            if hasattr(self, 'cpu_label'):
                self._tooltips.append(WidgetTooltip(
                    self.cpu_label,
                    _tt('perf_cpu', "Current CPU utilization percentage"),
                    widget_id='perf_cpu', tooltip_manager=tm))
            
            # Queue status tooltip
            if hasattr(self, 'queue_pending_label'):
                self._tooltips.append(WidgetTooltip(
                    self.queue_pending_label,
                    _tt('perf_queue', "Number of files waiting in the processing queue"),
                    widget_id='perf_queue', tooltip_manager=tm))
            
            # Workers slider tooltip
            if hasattr(self, 'workers_slider'):
                self._tooltips.append(WidgetTooltip(
                    self.workers_slider,
                    _tt('perf_workers',
                        "Number of parallel worker threads for processing\n"
                        "More workers = faster but uses more CPU/memory"),
                    widget_id='perf_workers', tooltip_manager=tm))
                    
        except Exception as e:
            logger.error(f"Error adding tooltips to Performance Dashboard: {e}")
