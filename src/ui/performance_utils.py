"""
Qt-based Performance Optimization Utilities
Uses Qt native timers (QTimer) instead of tkinter .after()
"""

try:
    from PyQt6.QtCore import QTimer, QObject, pyqtSignal
    from PyQt6.QtWidgets import QWidget
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class ThrottledUpdateQt(QObject):
    """
    Qt-based throttle for rapid UI updates.
    Uses QTimer instead of tkinter .after()
    """
    
    def __init__(self, delay_ms: int = 150):
        """
        Initialize throttled update handler with Qt timer.
        
        Args:
            delay_ms: Delay in milliseconds between updates
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 not available")
            
        super().__init__()
        self.delay_ms = delay_ms
        self._callback: Optional[Callable] = None
        
        # Use Qt native QTimer instead of tkinter .after()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute)
    
    def schedule(self, callback: Callable):
        """
        Schedule a callback to run after the delay period.
        Uses QTimer instead of widget.after()
        
        Args:
            callback: Function to call after delay
        """
        # Stop any pending timer (replaces after_cancel)
        self._timer.stop()
        
        # Schedule new update with Qt timer
        self._callback = callback
        self._timer.start(self.delay_ms)
    
    def _execute(self):
        """Execute the scheduled callback."""
        if self._callback is not None:
            try:
                self._callback()
            except Exception as e:
                logger.error(f"Error in throttled update: {e}")
            finally:
                self._callback = None
    
    def cancel(self):
        """Cancel any pending update."""
        self._timer.stop()
        self._callback = None


class DebouncedCallbackQt(QObject):
    """
    Qt-based debounce for callbacks.
    Uses QTimer instead of tkinter .after() for cleaner integration with Qt event loop.
    """
    
    def __init__(self, callback: Callable, delay_ms: int = 500):
        """
        Initialize debounced callback with Qt timer.
        
        Args:
            callback: Function to call after delay
            delay_ms: Delay in milliseconds
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 not available")
            
        super().__init__()
        self.callback = callback
        self.delay_ms = delay_ms
        
        # Use Qt native QTimer (replaces widget.after())
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute)
        
        # Store args/kwargs for callback
        self._args = ()
        self._kwargs = {}
    
    def trigger(self, *args, **kwargs):
        """
        Trigger the callback after the delay period.
        Resets the delay timer if called multiple times.
        Uses QTimer instead of widget.after()
        """
        # Store arguments
        self._args = args
        self._kwargs = kwargs
        
        # Restart timer (automatically cancels previous)
        self._timer.stop()
        self._timer.start(self.delay_ms)
    
    def _execute(self):
        """Execute the callback with stored arguments."""
        try:
            self.callback(*self._args, **self._kwargs)
        except Exception as e:
            logger.error(f"Error in debounced callback: {e}")
        finally:
            self._args = ()
            self._kwargs = {}
    
    def cancel(self):
        """Cancel any pending callback."""
        self._timer.stop()
        self._args = ()
        self._kwargs = {}


class PeriodicUpdateQt(QObject):
    """
    Qt-based periodic update using QTimer.
    Cleaner than recursive tkinter .after() calls.
    """
    
    updated = pyqtSignal()  # Signal emitted on each update
    
    def __init__(self, interval_ms: int = 1000, callback: Optional[Callable] = None):
        """
        Initialize periodic updater with Qt timer.
        
        Args:
            interval_ms: Interval between updates in milliseconds
            callback: Optional callback to call on each update
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 not available")
            
        super().__init__()
        self.interval_ms = interval_ms
        self._callback = callback
        
        # Use Qt native QTimer for periodic updates
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._on_timeout)
        
        # Connect callback if provided
        if callback:
            self.updated.connect(callback)
    
    def start(self):
        """Start the periodic updates."""
        self._timer.start()
    
    def stop(self):
        """Stop the periodic updates."""
        self._timer.stop()
    
    def _on_timeout(self):
        """Handle timer timeout."""
        try:
            self.updated.emit()
            if self._callback:
                self._callback()
        except Exception as e:
            logger.error(f"Error in periodic update: {e}")
    
    def set_interval(self, interval_ms: int):
        """Change the update interval."""
        self.interval_ms = interval_ms
        self._timer.setInterval(interval_ms)
    
    def is_active(self) -> bool:
        """Check if timer is active."""
        return self._timer.isActive()


def create_single_shot_timer(delay_ms: int, callback: Callable) -> QTimer:
    """
    Create a single-shot Qt timer (replaces widget.after()).
    
    Args:
        delay_ms: Delay in milliseconds
        callback: Function to call after delay
    
    Returns:
        QTimer instance (can be stopped with .stop())
    
    Example:
        # OLD: widget.after(1000, my_function)
        # NEW: timer = create_single_shot_timer(1000, my_function)
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt6 not available")
        
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(callback)
    timer.start(delay_ms)
    return timer


# Convenience function (replaces QTimer.singleShot for consistency)
def schedule_once(delay_ms: int, callback: Callable):
    """
    Schedule a callback to run once after delay.
    Simpler API, timer cannot be cancelled.
    
    Args:
        delay_ms: Delay in milliseconds
        callback: Function to call
    
    Example:
        # OLD: widget.after(1000, my_function)
        # NEW: schedule_once(1000, my_function)
    """
    if not PYQT_AVAILABLE:
        raise ImportError("PyQt6 not available")
    QTimer.singleShot(delay_ms, callback)
