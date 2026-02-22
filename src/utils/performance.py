"""
Performance Monitor - Track and analyze performance metrics
Author: Dead On The Inside / JosephsDeadish
"""

import time
try:
    import psutil
    HAS_PSUTIL = True
except (ImportError, OSError):
    psutil = None  # type: ignore[assignment]
    HAS_PSUTIL = False
import threading
from collections import deque
from typing import Dict, List, Optional, Any
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
        self.process = psutil.Process() if HAS_PSUTIL else None
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
            if HAS_PSUTIL and self.process is not None:
                mem_info = self.process.memory_info()
                memory_mb = mem_info.rss / (1024 * 1024)
                cpu_pct = self.process.cpu_percent()
                thread_cnt = self.process.num_threads()
            else:
                memory_mb = 0.0
                cpu_pct = 0.0
                thread_cnt = 0
            
            # Calculate textures per second
            elapsed = time.time() - self.start_time if self.start_time else 1.0
            tps = self.total_textures_processed / elapsed if elapsed > 0 else 0.0
            
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                textures_processed=self.total_textures_processed,
                textures_per_second=tps,
                memory_mb=memory_mb,
                cpu_percent=cpu_pct,
                thread_count=thread_cnt,
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


# ══════════════════════════════════════════════════════════════════════════════
# Lazy Loading and Smart Batch Processing Utilities
# ══════════════════════════════════════════════════════════════════════════════

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, TypeVar, Generic
import multiprocessing as mp

T = TypeVar('T')


class LazyLoader(Generic[T]):
    """
    Lazy loader that only initializes resource when first accessed.
    Useful for heavy objects like AI models, large datasets, etc.
    """
    
    def __init__(self, loader_func: Callable[[], T], name: str = "Resource"):
        """
        Initialize lazy loader.
        
        Args:
            loader_func: Function that creates/loads the resource
            name: Human-readable name for logging
        """
        self._loader_func = loader_func
        self._name = name
        self._resource: Optional[T] = None
        self._lock = threading.Lock()
        self._loaded = False
    
    def get(self) -> T:
        """Get the resource, loading it if necessary."""
        if not self._loaded:
            with self._lock:
                # Double-check after acquiring lock
                if not self._loaded:
                    logger.info(f"Lazy loading {self._name}...")
                    self._resource = self._loader_func()
                    self._loaded = True
                    logger.info(f"{self._name} loaded successfully")
        
        return self._resource
    
    def is_loaded(self) -> bool:
        """Check if resource is loaded."""
        return self._loaded
    
    def unload(self):
        """Unload the resource to free memory."""
        if self._loaded:
            with self._lock:
                if self._loaded:
                    logger.info(f"Unloading {self._name}...")
                    self._resource = None
                    self._loaded = False
                    
                    # Force garbage collection
                    import gc
                    gc.collect()
                    logger.info(f"{self._name} unloaded")
    
    def reload(self):
        """Reload the resource."""
        self.unload()
        return self.get()


class JobScheduler:
    """
    Smart job scheduler with CPU-aware batch processing.
    Prevents UI freezing by managing concurrent operations.
    """
    
    def __init__(self, max_workers: Optional[int] = None, name: str = "JobScheduler"):
        """
        Initialize job scheduler.
        
        Args:
            max_workers: Maximum concurrent workers (auto-detects if None)
            name: Scheduler name for logging
        """
        self.name = name
        
        # Auto-detect optimal worker count
        if max_workers is None:
            cpu_count = mp.cpu_count()
            # Use CPU count - 1 to keep one core free for UI
            # Minimum 1, maximum 8 for reasonable resource usage
            max_workers = max(1, min(cpu_count - 1, 8))
            logger.info(f"{name}: Detected {cpu_count} CPU cores, using {max_workers} workers")
        
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=name)
        self._active_jobs = 0
        self._lock = threading.Lock()
    
    def submit_job(self, func: Callable, *args, **kwargs):
        """
        Submit a single job for execution.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Future object
        """
        with self._lock:
            self._active_jobs += 1
        
        future = self.executor.submit(func, *args, **kwargs)
        future.add_done_callback(lambda f: self._job_completed())
        
        return future
    
    def submit_batch(self, func: Callable, items: List[Any], 
                     progress_callback: Optional[Callable[[int, int], None]] = None,
                     batch_size: Optional[int] = None):
        """
        Submit batch of jobs with smart scheduling.
        
        Args:
            func: Function to execute on each item
            items: List of items to process
            progress_callback: Called with (completed, total) after each job
            batch_size: Items to process in each batch (auto if None)
        
        Returns:
            List of results in order
        """
        if not items:
            return []
        
        total = len(items)
        logger.info(f"{self.name}: Processing batch of {total} items")
        
        # Auto-detect batch size if not specified
        if batch_size is None:
            # Process in batches that keep workers busy
            batch_size = max(1, total // (self.max_workers * 2))
        
        # Submit jobs
        futures = []
        for item in items:
            future = self.submit_job(func, item)
            futures.append((future, item))
        
        # Collect results with progress tracking
        completed = 0
        result_map = {}
        
        for future, item in futures:
            try:
                result = future.result()
                result_map[id(item)] = result
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, total)
                    
            except Exception as e:
                logger.error(f"{self.name}: Job failed: {e}")
                result_map[id(item)] = None
        
        # Return results in input order
        ordered_results = [result_map[id(item)] for _, item in futures]
        
        logger.info(f"{self.name}: Batch complete ({completed}/{total} successful)")
        return ordered_results
    
    def submit_batch_with_batching(self, func: Callable, items: List[Any],
                                   progress_callback: Optional[Callable[[int, int], None]] = None,
                                   items_per_batch: int = 10):
        """
        Submit batch jobs where each job processes multiple items.
        More efficient for very large datasets.
        
        Args:
            func: Function that accepts a list of items
            items: All items to process
            progress_callback: Progress callback
            items_per_batch: Items per job batch
        
        Returns:
            Flattened list of all results
        """
        if not items:
            return []
        
        # Split into batches
        batches = [items[i:i + items_per_batch] 
                  for i in range(0, len(items), items_per_batch)]
        
        logger.info(f"{self.name}: Processing {len(items)} items in {len(batches)} batches")
        
        # Process batches
        total_items = len(items)
        processed_items = 0
        all_results = []
        
        def process_batch_with_progress(batch):
            nonlocal processed_items
            results = func(batch)
            processed_items += len(batch)
            if progress_callback:
                progress_callback(processed_items, total_items)
            return results
        
        # Submit all batches
        batch_results = self.submit_batch(process_batch_with_progress, batches)
        
        # Flatten results
        for batch_result in batch_results:
            if batch_result:
                all_results.extend(batch_result)
        
        return all_results
    
    def get_active_jobs(self) -> int:
        """Get number of currently active jobs."""
        with self._lock:
            return self._active_jobs
    
    def _job_completed(self):
        """Internal callback when job completes."""
        with self._lock:
            self._active_jobs = max(0, self._active_jobs - 1)
    
    def shutdown(self, wait: bool = True):
        """Shutdown the scheduler."""
        logger.info(f"{self.name}: Shutting down...")
        self.executor.shutdown(wait=wait)
        logger.info(f"{self.name}: Shutdown complete")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


class ProgressiveLoader:
    """
    Progressive loader that loads items as needed, prioritizing visible items.
    Useful for thumbnail loading, large lists, etc.
    """
    
    def __init__(self, loader_func: Callable[[Any], Any], 
                 scheduler: Optional[JobScheduler] = None):
        """
        Initialize progressive loader.
        
        Args:
            loader_func: Function to load a single item
            scheduler: Optional job scheduler (creates one if None)
        """
        self.loader_func = loader_func
        self.scheduler = scheduler or JobScheduler(name="ProgressiveLoader")
        self._own_scheduler = scheduler is None
        self._cache = {}
        self._loading = set()
        self._lock = threading.Lock()
    
    def load_items(self, items: List[Any], visible_indices: Optional[List[int]] = None,
                  callback: Optional[Callable[[Any, Any], None]] = None):
        """
        Load items progressively, prioritizing visible ones.
        
        Args:
            items: List of items to load
            visible_indices: Indices of visible items (loaded first)
            callback: Called when each item loads: callback(index, result)
        """
        if visible_indices:
            # Sort: visible first, then rest
            visible_set = set(visible_indices)
            indices = list(visible_indices) + [i for i in range(len(items)) 
                                               if i not in visible_set]
        else:
            indices = list(range(len(items)))
        
        def load_item(idx):
            item = items[idx]
            
            # Check cache
            with self._lock:
                if idx in self._cache:
                    return idx, self._cache[idx]
                
                if idx in self._loading:
                    return idx, None  # Already loading
                
                self._loading.add(idx)
            
            try:
                result = self.loader_func(item)
                
                with self._lock:
                    self._cache[idx] = result
                    self._loading.discard(idx)
                
                if callback:
                    callback(idx, result)
                
                return idx, result
                
            except Exception as e:
                logger.error(f"Error loading item {idx}: {e}")
                with self._lock:
                    self._loading.discard(idx)
                return idx, None
        
        # Submit jobs in priority order
        for idx in indices:
            self.scheduler.submit_job(load_item, idx)
    
    def get_cached(self, index: int) -> Optional[Any]:
        """Get cached item if available."""
        with self._lock:
            return self._cache.get(index)
    
    def is_loading(self, index: int) -> bool:
        """Check if item is currently loading."""
        with self._lock:
            return index in self._loading
    
    def clear_cache(self):
        """Clear the cache to free memory."""
        with self._lock:
            self._cache.clear()
            logger.info("ProgressiveLoader cache cleared")
    
    def shutdown(self):
        """Shutdown the loader."""
        if self._own_scheduler:
            self.scheduler.shutdown()


def get_optimal_worker_count() -> int:
    """
    Get optimal worker count for current system.
    
    Returns:
        Number of workers (CPU cores - 1, clamped to 1-8)
    """
    cpu_count = mp.cpu_count()
    return max(1, min(cpu_count - 1, 8))


def get_cpu_info() -> dict:
    """
    Get CPU information for performance tuning.
    
    Returns:
        Dict with cpu_count, optimal_workers, etc.
    """
    cpu_count = mp.cpu_count()
    optimal_workers = get_optimal_worker_count()
    
    return {
        'cpu_count': cpu_count,
        'optimal_workers': optimal_workers,
        'recommended_batch_size': optimal_workers * 2,
    }

