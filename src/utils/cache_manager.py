"""
Cache Manager - LRU cache for texture metadata and thumbnails
Author: Dead On The Inside / JosephsDeadish
"""

import time
from collections import OrderedDict
from typing import Any, Optional
from pathlib import Path
import threading


class CacheManager:
    """
    Thread-safe LRU cache manager for texture data
    Implements Least Recently Used eviction policy
    """
    
    def __init__(self, max_size_mb: int = 500):
        """
        Initialize cache manager
        
        Args:
            max_size_mb: Maximum cache size in megabytes
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.current_size = 0
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]['data']
            else:
                self.misses += 1
                return None
    
    def put(self, key: str, value: Any, size_bytes: int = 0):
        """
        Put item in cache
        
        Args:
            key: Cache key
            value: Value to cache
            size_bytes: Size of the value in bytes (0 for auto-estimate)
        """
        with self.lock:
            # If key exists, remove old entry first
            if key in self.cache:
                old_size = self.cache[key]['size']
                self.current_size -= old_size
                del self.cache[key]
            
            # Estimate size if not provided
            if size_bytes == 0:
                size_bytes = self._estimate_size(value)
            
            # Evict items if necessary
            while (self.current_size + size_bytes > self.max_size_bytes 
                   and len(self.cache) > 0):
                self._evict_lru()
            
            # Add new item
            self.cache[key] = {
                'data': value,
                'size': size_bytes,
                'timestamp': time.time()
            }
            self.current_size += size_bytes
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if self.cache:
            key, value = self.cache.popitem(last=False)
            self.current_size -= value['size']
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate object size in bytes"""
        import sys
        try:
            return sys.getsizeof(obj)
        except Exception:
            return 1024  # Default 1KB if can't determine
    
    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
            self.current_size = 0
    
    def remove(self, key: str) -> bool:
        """
        Remove specific key from cache
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if removed, False if not found
        """
        with self.lock:
            if key in self.cache:
                size = self.cache[key]['size']
                self.current_size -= size
                del self.cache[key]
                return True
            return False
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                'size_mb': self.current_size / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'items': len(self.cache),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'usage_percent': (self.current_size / self.max_size_bytes) * 100
            }
