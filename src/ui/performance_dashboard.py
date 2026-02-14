"""
Performance Dashboard
Real-time monitoring of processing speed, memory, and queue status
"""

import customtkinter as ctk
import psutil
import time
import threading
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Try to import SVG icon helper
try:
    from src.utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    load_icon = None
    SVG_ICONS_AVAILABLE = False
    logger.warning("SVG icons not available for Performance Dashboard")

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


class PerformanceDashboard(ctk.CTkFrame):
    """
    Real-time performance dashboard widget.
    Shows processing speed, memory usage, queue status, and more.
    """
    
    def __init__(self, master, unlockables_system=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.unlockables_system = unlockables_system
        self.metrics = PerformanceMetrics()
        self.update_interval = 1000  # 1 second
        self.update_job = None
        self.running = False
        
        # Parallel processing control
        self.max_workers = psutil.cpu_count()
        self.current_workers = 1
        
        self._tooltips = []
        self._create_widgets()
        self._add_tooltips()
    
    def _create_widgets(self):
        """Create dashboard widgets."""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📊 Performance Dashboard",
            font=("Arial Bold", 16)
        )
        title_label.pack(pady=(10, 5))
        
        # Main content in grid layout
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left column: Processing Stats
        stats_frame = ctk.CTkFrame(content_frame)
        stats_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(
            stats_frame,
            text="⚡ Processing",
            font=("Arial Bold", 14)
        ).pack(anchor="w", padx=10, pady=5)
        
        self.speed_label = ctk.CTkLabel(
            stats_frame,
            text="Speed: 0.0 files/sec",
            font=("Arial", 12)
        )
        self.speed_label.pack(anchor="w", padx=10, pady=2)
        
        self.throughput_label = ctk.CTkLabel(
            stats_frame,
            text="Throughput: 0.0 MB/sec",
            font=("Arial", 12)
        )
        self.throughput_label.pack(anchor="w", padx=10, pady=2)
        
        self.files_processed_label = ctk.CTkLabel(
            stats_frame,
            text="Processed: 0 files",
            font=("Arial", 12)
        )
        self.files_processed_label.pack(anchor="w", padx=10, pady=2)
        
        # Middle column: System Resources
        resources_frame = ctk.CTkFrame(content_frame)
        resources_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(
            resources_frame,
            text="💻 System Resources",
            font=("Arial Bold", 14)
        ).pack(anchor="w", padx=10, pady=5)
        
        self.memory_label = ctk.CTkLabel(
            resources_frame,
            text="Memory: 0 MB (Peak: 0 MB)",
            font=("Arial", 12)
        )
        self.memory_label.pack(anchor="w", padx=10, pady=2)
        
        self.cpu_label = ctk.CTkLabel(
            resources_frame,
            text="CPU: 0% (Peak: 0%)",
            font=("Arial", 12)
        )
        self.cpu_label.pack(anchor="w", padx=10, pady=2)
        
        # Available memory
        available_memory = psutil.virtual_memory().available / (1024 * 1024 * 1024)
        self.available_label = ctk.CTkLabel(
            resources_frame,
            text=f"Available: {available_memory:.1f} GB",
            font=("Arial", 12)
        )
        self.available_label.pack(anchor="w", padx=10, pady=2)
        
        # Right column: Queue Status
        queue_frame = ctk.CTkFrame(content_frame)
        queue_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        ctk.CTkLabel(
            queue_frame,
            text="📋 Queue Status",
            font=("Arial Bold", 14)
        ).pack(anchor="w", padx=10, pady=5)
        
        self.queue_pending_label = ctk.CTkLabel(
            queue_frame,
            text="⏳ Pending: 0",
            font=("Arial", 12)
        )
        self.queue_pending_label.pack(anchor="w", padx=10, pady=2)
        
        self.queue_processing_label = ctk.CTkLabel(
            queue_frame,
            text="🔄 Processing: 0",
            font=("Arial", 12)
        )
        self.queue_processing_label.pack(anchor="w", padx=10, pady=2)
        
        self.queue_completed_label = ctk.CTkLabel(
            queue_frame,
            text="✅ Completed: 0",
            font=("Arial", 12)
        )
        self.queue_completed_label.pack(anchor="w", padx=10, pady=2)
        
        self.queue_failed_label = ctk.CTkLabel(
            queue_frame,
            text="❌ Failed: 0",
            font=("Arial", 12)
        )
        self.queue_failed_label.pack(anchor="w", padx=10, pady=2)
        
        # Estimated completion time
        self.eta_label = ctk.CTkLabel(
            queue_frame,
            text="ETA: --:--:--",
            font=("Arial Bold", 12)
        )
        self.eta_label.pack(anchor="w", padx=10, pady=5)
        
        # Configure grid weights
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Parallel Processing Control
        parallel_frame = ctk.CTkFrame(self)
        parallel_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            parallel_frame,
            text="⚙️ Parallel Processing:",
            font=("Arial Bold", 12)
        ).pack(side="left", padx=10)
        
        self.workers_slider = ctk.CTkSlider(
            parallel_frame,
            from_=1,
            to=self.max_workers,
            number_of_steps=self.max_workers - 1,
            command=self._on_workers_changed
        )
        self.workers_slider.set(self.current_workers)
        self.workers_slider.pack(side="left", fill="x", expand=True, padx=10)
        
        self.workers_label = ctk.CTkLabel(
            parallel_frame,
            text=f"1 / {self.max_workers} workers",
            font=("Arial", 12)
        )
        self.workers_label.pack(side="left", padx=10)
    
    def start(self):
        """Start performance monitoring."""
        self.running = True
        self.metrics.start_time = time.time()
        self._update()
    
    def stop(self):
        """Stop performance monitoring."""
        self.running = False
        if self.update_job:
            self.after_cancel(self.update_job)
            self.update_job = None
    
    def _update(self):
        """Update dashboard display."""
        if not self.running:
            return
        
        # Update metrics
        self.metrics.update()
        summary = self.metrics.get_summary()
        
        # Update labels
        self.speed_label.configure(
            text=f"Speed: {summary['avg_speed_fps']:.2f} files/sec"
        )
        
        throughput_mbps = summary['mb_processed'] / max(summary['elapsed_time'], 1)
        self.throughput_label.configure(
            text=f"Throughput: {throughput_mbps:.2f} MB/sec"
        )
        
        self.files_processed_label.configure(
            text=f"Processed: {summary['files_processed']} files"
        )
        
        self.memory_label.configure(
            text=f"Memory: {summary['current_memory_mb']:.1f} MB (Peak: {summary['peak_memory_mb']:.1f} MB)"
        )
        
        self.cpu_label.configure(
            text=f"CPU: {summary['current_cpu_percent']:.1f}% (Peak: {summary['peak_cpu_percent']:.1f}%)"
        )
        
        self.queue_pending_label.configure(
            text=f"⏳ Pending: {summary['queue_pending']}"
        )
        
        self.queue_processing_label.configure(
            text=f"🔄 Processing: {summary['queue_processing']}"
        )
        
        self.queue_completed_label.configure(
            text=f"✅ Completed: {summary['queue_completed']}"
        )
        
        self.queue_failed_label.configure(
            text=f"❌ Failed: {summary['queue_failed']}"
        )
        
        # ETA
        eta_seconds = summary['estimated_completion']
        if eta_seconds is not None and eta_seconds > 0:
            eta_time = str(timedelta(seconds=int(eta_seconds)))
            self.eta_label.configure(text=f"ETA: {eta_time}")
        else:
            self.eta_label.configure(text="ETA: --:--:--")
        
        # Schedule next update
        self.update_job = self.after(self.update_interval, self._update)
    
    def _on_workers_changed(self, value):
        """Handle worker count slider change."""
        self.current_workers = int(value)
        self.workers_label.configure(
            text=f"{self.current_workers} / {self.max_workers} workers"
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
            
            # Processing speed tooltip
            if hasattr(self, 'speed_label'):
                tooltip = get_tooltip("processing speed") or get_tooltip("speed")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.speed_label, tooltip))
            
            # Memory usage tooltip
            if hasattr(self, 'memory_label'):
                tooltip = get_tooltip("memory") 
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.memory_label, tooltip))
            
            # CPU usage tooltip
            if hasattr(self, 'cpu_label'):
                tooltip = get_tooltip("cpu")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.cpu_label, tooltip))
            
            # Queue status tooltip
            if hasattr(self, 'queue_pending_label'):
                tooltip = get_tooltip("queue")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.queue_pending_label, tooltip))
            
            # Workers slider tooltip
            if hasattr(self, 'workers_slider'):
                tooltip = get_tooltip("parallel") or get_tooltip("workers") or get_tooltip("thread")
                if tooltip:
                    self._tooltips.append(WidgetTooltip(self.workers_slider, tooltip))
                    
        except Exception as e:
            logger.error(f"Error adding tooltips to Performance Dashboard: {e}")
