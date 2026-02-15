"""
UI Performance Optimization Utilities
Provides utilities for optimizing CustomTkinter widgets performance
"""

import customtkinter as ctk
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class OptimizedScrollableFrame(ctk.CTkScrollableFrame):
    """
    Optimized version of CTkScrollableFrame that reduces rendering overhead
    and prevents screen tearing during rapid updates.
    """
    
    # Target frame rate for scrolling (60 FPS = 16.67ms per frame)
    MIN_SCROLL_INTERVAL = 1.0 / 60.0  # ~16ms minimum between scroll updates
    
    def __init__(self, master, scroll_speed: int = 20, **kwargs):
        """
        Initialize optimized scrollable frame.
        
        Args:
            master: Parent widget
            scroll_speed: Scroll speed multiplier (higher = faster scrolling)
            **kwargs: Additional arguments passed to CTkScrollableFrame
        """
        super().__init__(master, **kwargs)
        
        self._scroll_speed = scroll_speed
        self._update_pending = False
        self._last_scroll_time = 0
        
        # Override mouse wheel binding for smoother scrolling
        self._setup_smooth_scrolling()
    
    def _setup_smooth_scrolling(self):
        """Setup smooth scrolling with reduced updates."""
        try:
            # Unbind default mouse wheel events
            canvas = self._parent_canvas
            
            # Rebind with optimized handler
            canvas.bind("<MouseWheel>", self._on_mousewheel_optimized, add="+")
            canvas.bind("<Button-4>", self._on_mousewheel_optimized, add="+")  # Linux scroll up
            canvas.bind("<Button-5>", self._on_mousewheel_optimized, add="+")  # Linux scroll down
        except Exception as e:
            logger.debug(f"Could not setup smooth scrolling: {e}")
    
    def _on_mousewheel_optimized(self, event):
        """Optimized mousewheel handler with throttling."""
        import time
        
        # Throttle scroll updates to reduce rendering overhead (60 FPS max)
        current_time = time.time()
        if current_time - self._last_scroll_time < self.MIN_SCROLL_INTERVAL:
            return "break"
        
        self._last_scroll_time = current_time
        
        # Let default handler process the event
        return None


class ThrottledUpdate:
    """
    Utility class for throttling rapid UI updates to prevent performance issues.
    """
    
    def __init__(self, widget, delay_ms: int = 150):
        """
        Initialize throttled update handler.
        
        Args:
            widget: Widget to perform updates on
            delay_ms: Delay in milliseconds between updates
        """
        self.widget = widget
        self.delay_ms = delay_ms
        self._pending_id = None
        self._callback: Optional[Callable] = None
    
    def schedule(self, callback: Callable):
        """
        Schedule a callback to run after the delay period.
        Subsequent calls will cancel the previous scheduled callback.
        
        Args:
            callback: Function to call after delay
        """
        # Cancel any pending update
        if self._pending_id is not None:
            try:
                self.widget.after_cancel(self._pending_id)
            except Exception:
                pass
        
        # Schedule new update
        self._callback = callback
        self._pending_id = self.widget.after(self.delay_ms, self._execute)
    
    def _execute(self):
        """Execute the scheduled callback."""
        self._pending_id = None
        if self._callback is not None:
            try:
                self._callback()
            except Exception as e:
                logger.error(f"Error in throttled update: {e}")
            finally:
                self._callback = None
    
    def cancel(self):
        """Cancel any pending update."""
        if self._pending_id is not None:
            try:
                self.widget.after_cancel(self._pending_id)
            except Exception:
                pass
            self._pending_id = None
            self._callback = None


class DebouncedCallback:
    """
    Debounce a callback to reduce the number of calls during rapid changes.
    Similar to ThrottledUpdate but with a cleaner API.
    """
    
    def __init__(self, widget, callback: Callable, delay_ms: int = 500):
        """
        Initialize debounced callback.
        
        Args:
            widget: Widget to use for after() scheduling
            callback: Function to call after delay
            delay_ms: Delay in milliseconds
        """
        self.widget = widget
        self.callback = callback
        self.delay_ms = delay_ms
        self._after_id = None
    
    def trigger(self, *args, **kwargs):
        """
        Trigger the callback after the delay period.
        Resets the delay timer if called multiple times.
        """
        # Cancel previous timer
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
        
        # Schedule new callback
        def execute():
            self._after_id = None
            try:
                self.callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in debounced callback: {e}")
        
        self._after_id = self.widget.after(self.delay_ms, execute)
    
    def cancel(self):
        """Cancel any pending callback."""
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None


def cleanup_widget_memory(widget):
    """
    Clean up memory from a widget by removing references and forcing garbage collection.
    
    Args:
        widget: Widget to clean up
    """
    import gc
    
    # Remove image references
    if hasattr(widget, 'image'):
        try:
            del widget.image
        except Exception:
            pass
    
    if hasattr(widget, '_image'):
        try:
            del widget._image
        except Exception:
            pass
    
    # Remove photo references
    for attr in dir(widget):
        if 'photo' in attr.lower():
            try:
                delattr(widget, attr)
            except Exception:
                pass
    
    # Force garbage collection
    gc.collect()


def optimize_canvas_updates(canvas):
    """
    Optimize a canvas for better performance during frequent updates.
    
    Args:
        canvas: tkinter Canvas widget to optimize
    """
    try:
        # Disable automatic redraw
        canvas.configure(xscrollincrement=1, yscrollincrement=1)
        
        # Configure for better performance
        if hasattr(canvas, 'configure'):
            canvas.configure(
                confine=False,  # Don't confine scroll region
                takefocus=False  # Don't steal focus
            )
    except Exception as e:
        logger.debug(f"Could not optimize canvas: {e}")


def batch_widget_updates(widget, updates: Callable):
    """
    Batch widget updates to reduce rendering overhead.
    
    Args:
        widget: Widget to update
        updates: Function that performs all updates
    """
    # Suspend automatic redraws
    try:
        widget.update_idletasks()
    except Exception:
        pass
    
    # Perform updates
    try:
        updates()
    except Exception as e:
        logger.error(f"Error in batch updates: {e}")
    
    # Resume rendering
    try:
        widget.update_idletasks()
    except Exception:
        pass
