"""
Performance Monitor - Track and analyze performance metrics
Author: Dead On The Inside / JosephsDeadish
"""

import time
import psutil
import threading
from collections import deque
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    timestamp: float
    textures_processed: int = 0
    textures_per_second: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    thread_count: int = 0
    cache_hit_rate: float = 0.0

class PerformanceMonitor:
    """
    Monitor and track application performance
    Provides real-time metrics and historical analysis
    """
    
    def __init__(self, history_size: int = 100):
        """
        Initialize performance monitor
        
        Args:
            history_size: Number of historical data points to keep
        """
        self.history_size = history_size
        self.metrics_history: deque = deque(maxlen=history_size)
        self.process = psutil.Process()
        self.lock = threading.Lock()
        
        # Counters
        self.total_textures_processed = 0
        self.start_time = None
        self.operation_start_time = None
        
        # Performance tracking
        self.operation_times: Dict[str, List[float]] = {}
        
    def start_operation(self, operation_name: str = "default"):
        """
        Start tracking an operation
        
        Args:
            operation_name: Name of the operation
        """
        self.operation_start_time = time.time()
        if self.start_time is None:
            self.start_time = self.operation_start_time
    
    def end_operation(self, operation_name: str = "default", items_processed: int = 0):
        """
        End tracking an operation
        
        Args:
            operation_name: Name of the operation
            items_processed: Number of items processed
        """
        if self.operation_start_time is None:
            return
        
        duration = time.time() - self.operation_start_time
        
        with self.lock:
            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []
            self.operation_times[operation_name].append(duration)
            
            self.total_textures_processed += items_processed
    
    def record_metrics(self, textures_processed: int = 0, cache_hit_rate: float = 0.0):
        """
        Record current performance metrics
        
        Args:
            textures_processed: Number of textures processed in this interval
            cache_hit_rate: Current cache hit rate (0.0-1.0)
        """
        with self.lock:
            mem_info = self.process.memory_info()
            
            # Calculate textures per second
            elapsed = time.time() - self.start_time if self.start_time else 1.0
            tps = self.total_textures_processed / elapsed if elapsed > 0 else 0.0
            
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                textures_processed=self.total_textures_processed,
                textures_per_second=tps,
                memory_mb=mem_info.rss / (1024 * 1024),
                cpu_percent=self.process.cpu_percent(),
                thread_count=self.process.num_threads(),
                cache_hit_rate=cache_hit_rate
            )
            
            self.metrics_history.append(metrics)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """
        Get most recent metrics
        
        Returns:
            Most recent PerformanceMetrics or None
        """
        with self.lock:
            return self.metrics_history[-1] if self.metrics_history else None
    
    def get_average_metrics(self, last_n: int = 10) -> Dict[str, float]:
        """
        Get average metrics over last N samples
        
        Args:
            last_n: Number of samples to average
            
        Returns:
            Dictionary of average metrics
        """
        with self.lock:
            if not self.metrics_history:
                return {}
            
            samples = list(self.metrics_history)[-last_n:]
            n = len(samples)
            
            return {
                'avg_textures_per_second': sum(m.textures_per_second for m in samples) / n,
                'avg_memory_mb': sum(m.memory_mb for m in samples) / n,
                'avg_cpu_percent': sum(m.cpu_percent for m in samples) / n,
                'avg_cache_hit_rate': sum(m.cache_hit_rate for m in samples) / n,
            }
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, float]:
        """
        Get statistics for a specific operation
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Dictionary with operation statistics
        """
        with self.lock:
            if operation_name not in self.operation_times:
                return {}
            
            times = self.operation_times[operation_name]
            if not times:
                return {}
            
            return {
                'count': len(times),
                'total_time': sum(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get complete performance summary
        
        Returns:
            Dictionary with complete performance summary
        """
        with self.lock:
            current = self.get_current_metrics()
            elapsed = time.time() - self.start_time if self.start_time else 0
            
            summary = {
                'total_textures_processed': self.total_textures_processed,
                'total_elapsed_time': elapsed,
                'current_metrics': current.__dict__ if current else {},
                'average_metrics': self.get_average_metrics(),
                'operations': {}
            }
            
            for op_name in self.operation_times:
                summary['operations'][op_name] = self.get_operation_stats(op_name)
            
            return summary
    
    def estimate_completion_time(self, total_items: int) -> Optional[float]:
        """
        Estimate time to completion based on current rate
        
        Args:
            total_items: Total number of items to process
            
        Returns:
            Estimated seconds to completion, or None if can't estimate
        """
        current = self.get_current_metrics()
        if not current or current.textures_per_second == 0:
            return None
        
        remaining = total_items - current.textures_processed
        if remaining <= 0:
            return 0.0
        
        return remaining / current.textures_per_second
    
    def reset(self):
        """Reset all metrics and counters"""
        with self.lock:
            self.metrics_history.clear()
            self.operation_times.clear()
            self.total_textures_processed = 0
            self.start_time = None
            self.operation_start_time = None
