"""
Memory Manager - Monitor and control memory usage
Author: Dead On The Inside / JosephsDeadish
"""

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None  # type: ignore[assignment]
    HAS_PSUTIL = False
import gc
import threading
import time
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Memory monitoring and management system
    Tracks memory usage and triggers cleanup when needed
    """
    
    def __init__(self, max_memory_mb: int = 2048, cleanup_threshold: float = 0.85):
        """
        Initialize memory manager
        
        Args:
            max_memory_mb: Maximum allowed memory in megabytes
            cleanup_threshold: Trigger cleanup at this percentage of max (0.0-1.0)
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cleanup_threshold = cleanup_threshold
        self.process = psutil.Process() if HAS_PSUTIL else None
        self.monitoring = False
        self.monitor_thread = None
        self.cleanup_callbacks = []
        
    def get_current_usage(self) -> dict:
        """
        Get current memory usage statistics
        
        Returns:
            Dictionary with memory stats
        """
        if not HAS_PSUTIL or self.process is None:
            return {
                'rss_mb': 0, 'vms_mb': 0, 'percent': 0,
                'system_available_mb': 0, 'system_percent': 0,
                'max_allowed_mb': self.max_memory_bytes / (1024 * 1024),
                'usage_of_max': 0
            }
        mem_info = self.process.memory_info()
        system_mem = psutil.virtual_memory()
        
        return {
            'rss_mb': mem_info.rss / (1024 * 1024),  # Resident Set Size
            'vms_mb': mem_info.vms / (1024 * 1024),  # Virtual Memory Size
            'percent': self.process.memory_percent(),
            'system_available_mb': system_mem.available / (1024 * 1024),
            'system_percent': system_mem.percent,
            'max_allowed_mb': self.max_memory_bytes / (1024 * 1024),
            'usage_of_max': (mem_info.rss / self.max_memory_bytes) * 100
        }
    
    def is_memory_critical(self) -> bool:
        """
        Check if memory usage is critical
        
        Returns:
            True if memory usage exceeds threshold
        """
        if not HAS_PSUTIL or self.process is None:
            return False
        mem_info = self.process.memory_info()
        usage_ratio = mem_info.rss / self.max_memory_bytes
        return usage_ratio >= self.cleanup_threshold
    
    def force_cleanup(self):
        """Force garbage collection and memory cleanup"""
        logger.info("Forcing memory cleanup...")
        
        # Run registered cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Cleanup callback error: {e}")
        
        # Force garbage collection
        gc.collect()
        
        # Log results
        after_stats = self.get_current_usage()
        logger.info(f"Memory after cleanup: {after_stats['rss_mb']:.1f} MB")
    
    def register_cleanup_callback(self, callback: Callable):
        """
        Register a callback to be called during cleanup
        
        Args:
            callback: Function to call during cleanup
        """
        self.cleanup_callbacks.append(callback)
    
    def start_monitoring(self, interval_seconds: float = 5.0):
        """
        Start background memory monitoring
        
        Args:
            interval_seconds: Check interval in seconds
        """
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop background memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Memory monitoring stopped")
    
    def _monitoring_loop(self, interval: float):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                if self.is_memory_critical():
                    logger.warning("Memory usage critical, triggering cleanup")
                    self.force_cleanup()
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
            
            time.sleep(interval)
    
    def get_recommendations(self) -> list:
        """
        Get memory optimization recommendations
        
        Returns:
            List of recommendation strings
        """
        stats = self.get_current_usage()
        recommendations = []
        
        if stats['usage_of_max'] > 90:
            recommendations.append("Memory usage very high - consider reducing cache size")
        elif stats['usage_of_max'] > 75:
            recommendations.append("Memory usage high - enable memory saver mode")
        
        if stats['system_percent'] > 90:
            recommendations.append("System memory critical - close other applications")
        
        if not recommendations:
            recommendations.append("Memory usage normal")
        
        return recommendations

    def get_memory_info(self) -> dict:
        """Alias for get_current_usage()."""
        return self.get_current_usage()

