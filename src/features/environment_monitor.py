"""
Environmental Awareness System for Interactive Panda

Monitors the application environment and triggers panda reactions to:
- User scrolling
- File previews appearing
- Dialogs showing/hiding
- Window state changes
- Other UI events

Features:
    - Event monitoring and detection
    - Panda reaction triggers
    - Hide/show behavior based on context
    - Immersive environmental responses
"""

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QEvent
    from PyQt6.QtWidgets import QDialog, QScrollBar, QApplication
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QObject = object

import time


class EnvironmentalEvent:
    """Types of environmental events the panda can react to."""
    SCROLL_START = "scroll_start"
    SCROLL_END = "scroll_end"
    DIALOG_OPENED = "dialog_opened"
    DIALOG_CLOSED = "dialog_closed"
    FILE_PREVIEW_OPENED = "file_preview_opened"
    FILE_PREVIEW_CLOSED = "file_preview_closed"
    WINDOW_MINIMIZED = "window_minimized"
    WINDOW_RESTORED = "window_restored"
    WINDOW_RESIZED = "window_resized"
    APP_FOCUS_GAINED = "app_focus_gained"
    APP_FOCUS_LOST = "app_focus_lost"


class EnvironmentMonitor(QObject if PYQT_AVAILABLE else object):
    """
    Monitors the application environment for events that should trigger panda reactions.
    
    This system:
    - Detects user scrolling
    - Monitors dialog visibility
    - Tracks file preview popups
    - Watches window state changes
    - Triggers appropriate panda responses
    """
    
    # Signals for environmental events
    environment_changed = pyqtSignal(str, dict) if PYQT_AVAILABLE else None
    panda_should_hide = pyqtSignal(bool) if PYQT_AVAILABLE else None
    panda_should_react = pyqtSignal(str, object) if PYQT_AVAILABLE else None
    
    def __init__(self, main_window, panda_overlay):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 required for EnvironmentMonitor")
        
        super().__init__()
        
        self.main_window = main_window
        self.panda_overlay = panda_overlay
        
        # State tracking
        self.is_scrolling = False
        self.scroll_end_timer = QTimer()
        self.scroll_end_timer.timeout.connect(self._on_scroll_end)
        self.scroll_end_timer.setSingleShot(True)
        
        self.active_dialogs = []
        self.active_previews = []
        
        self.last_scroll_time = 0
        self.last_resize_time = 0
        
        # Monitoring flags
        self.monitor_scrolling = True
        self.monitor_dialogs = True
        self.monitor_previews = True
        self.monitor_window_state = True
        
        # Panda reaction configurations
        self.hide_on_dialog = True
        self.hide_on_preview = False
        self.react_to_scroll = True
        
        # Install event filters
        self._install_event_filters()
    
    def _install_event_filters(self):
        """Install event filters on main window and application."""
        # Main window filter for window events
        if self.main_window:
            self.main_window.installEventFilter(self)
        
        # Application filter for dialog events
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Filter and handle events."""
        event_type = event.type()
        
        # Scroll events
        if self.monitor_scrolling and isinstance(obj, QScrollBar):
            if event_type == QEvent.Type.Wheel:
                self._on_scroll_event()
        
        # Dialog events
        if self.monitor_dialogs and isinstance(obj, QDialog):
            if event_type == QEvent.Type.Show:
                self._on_dialog_opened(obj)
            elif event_type == QEvent.Type.Hide:
                self._on_dialog_closed(obj)
        
        # Window state events
        if self.monitor_window_state and obj == self.main_window:
            if event_type == QEvent.Type.WindowStateChange:
                self._on_window_state_changed(event)
            elif event_type == QEvent.Type.Resize:
                self._on_window_resized(event)
            elif event_type == QEvent.Type.FocusIn:
                self._on_focus_gained()
            elif event_type == QEvent.Type.FocusOut:
                self._on_focus_lost()
        
        # Pass event to default handler
        return super().eventFilter(obj, event)
    
    def _on_scroll_event(self):
        """Handle scroll event."""
        current_time = time.time()
        
        # Check if this is a new scroll session
        if not self.is_scrolling or (current_time - self.last_scroll_time) > 0.5:
            self.is_scrolling = True
            self._emit_event(EnvironmentalEvent.SCROLL_START, {
                'timestamp': current_time
            })
            
            if self.react_to_scroll:
                # Panda reaction: Look at scroll direction, move eyes
                self.panda_should_react.emit('scroll_start', None)
        
        self.last_scroll_time = current_time
        
        # Reset scroll end timer
        self.scroll_end_timer.stop()
        self.scroll_end_timer.start(300)  # 300ms after last scroll
    
    def _on_scroll_end(self):
        """Handle scroll end (no scroll for 300ms)."""
        self.is_scrolling = False
        self._emit_event(EnvironmentalEvent.SCROLL_END, {
            'timestamp': time.time()
        })
        
        if self.react_to_scroll:
            # Panda reaction: Return to idle, maybe curious look
            self.panda_should_react.emit('scroll_end', None)
    
    def _on_dialog_opened(self, dialog):
        """Handle dialog opened."""
        if dialog not in self.active_dialogs:
            self.active_dialogs.append(dialog)
        
        self._emit_event(EnvironmentalEvent.DIALOG_OPENED, {
            'dialog': dialog,
            'dialog_type': dialog.__class__.__name__
        })
        
        if self.hide_on_dialog:
            # Hide panda when dialog appears
            self.panda_should_hide.emit(True)
            print(f"Panda hiding due to dialog: {dialog.__class__.__name__}")
    
    def _on_dialog_closed(self, dialog):
        """Handle dialog closed."""
        if dialog in self.active_dialogs:
            self.active_dialogs.remove(dialog)
        
        self._emit_event(EnvironmentalEvent.DIALOG_CLOSED, {
            'dialog': dialog,
            'dialog_type': dialog.__class__.__name__
        })
        
        # Show panda again if no dialogs remain
        if len(self.active_dialogs) == 0 and self.hide_on_dialog:
            self.panda_should_hide.emit(False)
            print("Panda reappearing, all dialogs closed")
    
    def register_file_preview(self, preview_widget):
        """
        Register a file preview widget for monitoring.
        
        Args:
            preview_widget: Widget showing file preview
        """
        if preview_widget not in self.active_previews:
            self.active_previews.append(preview_widget)
            preview_widget.installEventFilter(self)
        
        self._emit_event(EnvironmentalEvent.FILE_PREVIEW_OPENED, {
            'preview': preview_widget
        })
        
        if self.hide_on_preview:
            self.panda_should_hide.emit(True)
        else:
            # Panda reacts curiously to preview
            self.panda_should_react.emit('preview_opened', preview_widget)
    
    def unregister_file_preview(self, preview_widget):
        """
        Unregister a file preview widget.
        
        Args:
            preview_widget: Widget to unregister
        """
        if preview_widget in self.active_previews:
            self.active_previews.remove(preview_widget)
            preview_widget.removeEventFilter(self)
        
        self._emit_event(EnvironmentalEvent.FILE_PREVIEW_CLOSED, {
            'preview': preview_widget
        })
        
        if len(self.active_previews) == 0 and self.hide_on_preview:
            self.panda_should_hide.emit(False)
    
    def _on_window_state_changed(self, event):
        """Handle window state change."""
        # Check if minimized
        if self.main_window.isMinimized():
            self._emit_event(EnvironmentalEvent.WINDOW_MINIMIZED, {})
            self.panda_should_hide.emit(True)
        else:
            self._emit_event(EnvironmentalEvent.WINDOW_RESTORED, {})
            self.panda_should_hide.emit(False)
    
    def _on_window_resized(self, event):
        """Handle window resize."""
        current_time = time.time()
        
        # Throttle resize events
        if current_time - self.last_resize_time > 0.1:
            self._emit_event(EnvironmentalEvent.WINDOW_RESIZED, {
                'size': event.size(),
                'old_size': event.oldSize()
            })
            
            # Panda reaction: Look surprised, adjust position
            self.panda_should_react.emit('window_resized', event.size())
            
            self.last_resize_time = current_time
    
    def _on_focus_gained(self):
        """Handle application focus gained."""
        self._emit_event(EnvironmentalEvent.APP_FOCUS_GAINED, {})
        
        # Panda reaction: Perk up, happy to see user back
        self.panda_should_react.emit('focus_gained', None)
    
    def _on_focus_lost(self):
        """Handle application focus lost."""
        self._emit_event(EnvironmentalEvent.APP_FOCUS_LOST, {})
        
        # Panda reaction: Get sleepy, slow down
        self.panda_should_react.emit('focus_lost', None)
    
    def _emit_event(self, event_type, data):
        """Emit environmental event signal."""
        if self.environment_changed:
            self.environment_changed.emit(event_type, data)
            print(f"Environmental event: {event_type}")
    
    def set_hide_on_dialog(self, hide):
        """Set whether panda should hide when dialogs appear."""
        self.hide_on_dialog = hide
    
    def set_hide_on_preview(self, hide):
        """Set whether panda should hide when previews appear."""
        self.hide_on_preview = hide
    
    def set_react_to_scroll(self, react):
        """Set whether panda should react to scrolling."""
        self.react_to_scroll = react
    
    def get_state(self):
        """
        Get current environmental state.
        
        Returns:
            Dict with current state information
        """
        return {
            'is_scrolling': self.is_scrolling,
            'active_dialogs': len(self.active_dialogs),
            'active_previews': len(self.active_previews),
            'window_has_focus': self.main_window.isActiveWindow() if self.main_window else False,
            'window_minimized': self.main_window.isMinimized() if self.main_window else False,
        }


# Convenience function
def create_environment_monitor(main_window, panda_overlay):
    """
    Create an environment monitor.
    
    Args:
        main_window: Main QMainWindow
        panda_overlay: TransparentPandaOverlay instance
        
    Returns:
        EnvironmentMonitor instance or None
    """
    if not PYQT_AVAILABLE:
        print("Warning: PyQt6 not available, cannot create environment monitor")
        return None
    
    return EnvironmentMonitor(main_window, panda_overlay)
