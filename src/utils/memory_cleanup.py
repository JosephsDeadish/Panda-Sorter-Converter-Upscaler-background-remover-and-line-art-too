"""
Memory Management Utilities
Ensures proper cleanup of PIL images, caches, and prevents memory leaks
"""

from __future__ import annotations


import gc
import logging
import weakref
from typing import Any, Optional, Callable, Dict, List
from threading import Lock
try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, OSError):
    HAS_PIL = False


logger = logging.getLogger(__name__)


class ImageManager:
    """
    Manages PIL Image objects to ensure proper cleanup.
    Tracks image references and provides explicit cleanup.
    """
    
    def __init__(self):
        self._images: Dict[int, Image.Image] = {}
        self._lock = Lock()
    
    def register(self, image: Image.Image) -> int:
        """
        Register an image for tracking.
        
        Args:
            image: PIL Image to track
        
        Returns:
            Image ID for later reference
        """
        with self._lock:
            img_id = id(image)
            self._images[img_id] = image
            return img_id
    
    def get(self, img_id: int) -> Optional[Image.Image]:
        """Get tracked image by ID."""
        with self._lock:
            return self._images.get(img_id)
    
    def close(self, img_id: int):
        """
        Close and remove tracked image.
        
        Args:
            img_id: Image ID from register()
        """
        with self._lock:
            img = self._images.pop(img_id, None)
            if img:
                try:
                    img.close()
                    logger.debug(f"Closed image {img_id}")
                except Exception as e:
                    logger.error(f"Error closing image {img_id}: {e}")
    
    def close_all(self):
        """Close all tracked images."""
        with self._lock:
            closed_count = 0
            for img_id, img in list(self._images.items()):
                try:
                    img.close()
                    closed_count += 1
                except Exception as e:
                    logger.error(f"Error closing image {img_id}: {e}")
            
            self._images.clear()
            logger.info(f"Closed {closed_count} images")
    
    def cleanup_unused(self):
        """Remove references to images that have been deleted elsewhere."""
        with self._lock:
            # Check which images still exist
            valid_ids = []
            for img_id in list(self._images.keys()):
                try:
                    # Try to access the image
                    img = self._images[img_id]
                    if img.fp is None or (hasattr(img, 'closed') and img.closed):
                        # Image has been closed
                        del self._images[img_id]
                    else:
                        valid_ids.append(img_id)
                except Exception:
                    # Image is invalid
                    del self._images[img_id]
            
            logger.debug(f"Cleaned up unused images, {len(valid_ids)} remaining")
    
    def get_count(self) -> int:
        """Get number of tracked images."""
        with self._lock:
            return len(self._images)


class WeakCache:
    """
    Cache that uses weak references to allow garbage collection.
    Items are automatically removed when no strong references exist.
    """
    
    def __init__(self, name: str = "Cache"):
        self.name = name
        self._cache: Dict[Any, Any] = {}
        self._lock = Lock()
    
    def set(self, key: Any, value: Any):
        """Set cache value with weak reference."""
        with self._lock:
            try:
                # Use weakref for objects that support it
                self._cache[key] = weakref.ref(value)
            except TypeError:
                # For objects that don't support weakref, store directly
                # (will be cleared manually)
                self._cache[key] = value
    
    def get(self, key: Any) -> Optional[Any]:
        """Get cache value."""
        with self._lock:
            cached = self._cache.get(key)
            if cached is None:
                return None
            
            # Handle weakref
            if isinstance(cached, weakref.ref):
                value = cached()
                if value is None:
                    # Object was garbage collected
                    del self._cache[key]
                    return None
                return value
            
            # Direct reference
            return cached
    
    def remove(self, key: Any):
        """Remove key from cache."""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            logger.info(f"{self.name} cache cleared")
    
    def cleanup(self):
        """Remove dead weak references."""
        with self._lock:
            dead_keys = []
            for key, value in self._cache.items():
                if isinstance(value, weakref.ref) and value() is None:
                    dead_keys.append(key)
            
            for key in dead_keys:
                del self._cache[key]
            
            if dead_keys:
                logger.debug(f"{self.name} removed {len(dead_keys)} dead references")
    
    def size(self) -> int:
        """Get cache size."""
        with self._lock:
            return len(self._cache)


class MemoryManager:
    """
    Central memory management for the application.
    Provides cleanup, monitoring, and optimization.
    """
    
    def __init__(self):
        self.image_manager = ImageManager()
        self.caches: Dict[str, WeakCache] = {}
        self._lock = Lock()
    
    def register_cache(self, name: str) -> WeakCache:
        """
        Register a named cache for management.
        
        Args:
            name: Cache name
        
        Returns:
            WeakCache instance
        """
        with self._lock:
            if name not in self.caches:
                self.caches[name] = WeakCache(name)
            return self.caches[name]
    
    def get_cache(self, name: str) -> Optional[WeakCache]:
        """Get registered cache by name."""
        with self._lock:
            return self.caches.get(name)
    
    def cleanup_all(self):
        """Perform full cleanup of all managed resources."""
        logger.info("Performing full memory cleanup...")
        
        # Close all images
        self.image_manager.close_all()
        
        # Clear all caches
        with self._lock:
            for cache in self.caches.values():
                cache.clear()
        
        # Force garbage collection
        gc.collect()
        
        logger.info("Memory cleanup complete")
    
    def periodic_cleanup(self):
        """
        Periodic cleanup (call regularly, e.g., every 5 minutes).
        Less aggressive than cleanup_all().
        """
        logger.debug("Performing periodic cleanup...")
        
        # Cleanup unused images
        self.image_manager.cleanup_unused()
        
        # Cleanup dead weak references in caches
        with self._lock:
            for cache in self.caches.values():
                cache.cleanup()
        
        # Light garbage collection
        gc.collect(generation=0)  # Only collect young objects
        
        logger.debug("Periodic cleanup complete")
    
    def get_memory_stats(self) -> dict:
        """
        Get memory usage statistics.
        
        Returns:
            Dict with memory stats
        """
        stats = {
            'tracked_images': self.image_manager.get_count(),
            'caches': {}
        }
        
        with self._lock:
            for name, cache in self.caches.items():
                stats['caches'][name] = cache.size()
        
        # Try to get process memory if psutil available
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            stats['memory_mb'] = mem_info.rss / (1024 * 1024)
            stats['memory_percent'] = process.memory_percent()
        except ImportError:
            pass
        
        return stats


def close_image_safely(image: Optional[Image.Image]):
    """
    Safely close a PIL Image, handling errors.
    
    Args:
        image: PIL Image to close (can be None)
    """
    if image is not None:
        try:
            image.close()
        except Exception as e:
            logger.debug(f"Error closing image: {e}")


def process_image_with_cleanup(image_path: str, 
                               process_func: Callable[[Image.Image], Any],
                               return_image: bool = False) -> Any:
    """
    Process image with guaranteed cleanup.
    
    Args:
        image_path: Path to image
        process_func: Function that processes the image
        return_image: If True, returns the image (caller must close)
    
    Returns:
        Result from process_func
    """
    img = None
    try:
        img = Image.open(image_path)
        result = process_func(img)
        
        if return_image:
            return result, img
        else:
            return result
            
    finally:
        if img and not return_image:
            close_image_safely(img)


def batch_process_with_cleanup(image_paths: List[str],
                               process_func: Callable[[Image.Image], Any],
                               progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Any]:
    """
    Process multiple images with proper cleanup.
    
    Args:
        image_paths: List of image paths
        process_func: Function to process each image
        progress_callback: Optional progress callback
    
    Returns:
        List of results
    """
    results = []
    total = len(image_paths)
    
    for idx, path in enumerate(image_paths):
        img = None
        try:
            img = Image.open(path)
            result = process_func(img)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")
            results.append(None)
            
        finally:
            close_image_safely(img)
            
            if progress_callback:
                progress_callback(idx + 1, total)
    
    return results


# Global memory manager instance
_global_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create global memory manager."""
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager()
    return _global_memory_manager
