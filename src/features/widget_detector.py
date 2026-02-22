"""
Widget Detector System

Hit-testing and widget detection system for interactive panda overlay.
Detects Qt widgets at specific positions and builds collision maps.

Features:
    - Real-time widget detection at any position
    - Collision map generation for path finding
    - Widget geometry tracking
    - Widget type identification
    - Center point calculation
"""

import logging

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QPushButton, QSlider, 
        QTabBar, QComboBox, QCheckBox, QRadioButton,
        QLabel, QLineEdit
    )
    from PyQt6.QtCore import QPoint, QRect
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False


class WidgetDetector:
    """
    Detects Qt widgets at specific positions for panda interaction.
    
    This class provides:
    - Hit-testing to find widgets at positions
    - Collision map for path finding
    - Widget geometry queries
    - Interactive widget filtering
    """
    
    def __init__(self, main_window):
        """
        Initialize widget detector.
        
        Args:
            main_window: The main QMainWindow or QWidget to detect widgets in
        """
        if not PYQT_AVAILABLE:
            logger.warning("WidgetDetector: PyQt6 not available; detection disabled")
            self.main_window = main_window
            self.collision_map = {}
            self.cached_widgets = []
            self.cache_valid = False
            return
        
        self.main_window = main_window
        self.collision_map = {}
        self.cached_widgets = []
        self.cache_valid = False
        
        # Widget types we consider "interactive"
        self.interactive_types = (
            QPushButton,
            QSlider,
            QTabBar,
            QComboBox,
            QCheckBox,
            QRadioButton,
            QLineEdit,
        )
    
    def get_widget_at_position(self, x, y):
        """
        Get the widget at a specific screen position.
        
        Args:
            x: X coordinate in overlay space
            y: Y coordinate in overlay space
            
        Returns:
            QWidget or None if no widget found
        """
        # Convert to global coordinates
        global_pos = self.main_window.mapToGlobal(QPoint(int(x), int(y)))
        
        # Use Qt's built-in hit-testing
        widget = QApplication.widgetAt(global_pos)
        
        # Check if it's an interactive widget
        if widget and isinstance(widget, self.interactive_types):
            return widget
        
        # If not directly interactive, check parent
        if widget:
            parent = widget.parent()
            if parent and isinstance(parent, self.interactive_types):
                return parent
        
        return None
    
    def get_all_widgets(self, parent=None):
        """
        Get all interactive widgets in the window.
        
        Args:
            parent: Parent widget to search in (defaults to main_window)
            
        Returns:
            List of interactive widgets
        """
        if parent is None:
            parent = self.main_window
        
        widgets = []
        
        def find_widgets_recursive(widget):
            # Check if this widget is interactive
            if isinstance(widget, self.interactive_types):
                if widget.isVisible() and widget.isEnabled():
                    widgets.append(widget)
            
            # Recurse into children
            for child in widget.children():
                if isinstance(child, QWidget):
                    find_widgets_recursive(child)
        
        find_widgets_recursive(parent)
        
        self.cached_widgets = widgets
        self.cache_valid = True
        
        return widgets
    
    def build_collision_map(self, resolution=20):
        """
        Build a collision map of the window for path finding.
        
        Args:
            resolution: Grid cell size in pixels
            
        Returns:
            Dict mapping (grid_x, grid_y) to widget or None
        """
        self.collision_map = {}
        
        # Get all widgets
        if not self.cache_valid:
            self.get_all_widgets()
        
        window_rect = self.main_window.rect()
        
        # Build grid
        for x in range(0, window_rect.width(), resolution):
            for y in range(0, window_rect.height(), resolution):
                widget = self.get_widget_at_position(x, y)
                
                grid_x = x // resolution
                grid_y = y // resolution
                
                if widget:
                    self.collision_map[(grid_x, grid_y)] = widget
        
        return self.collision_map
    
    def is_position_blocked(self, x, y, resolution=20):
        """
        Check if a position is blocked by a widget.
        
        Args:
            x: X coordinate
            y: Y coordinate
            resolution: Grid resolution (should match build_collision_map)
            
        Returns:
            True if position is blocked, False otherwise
        """
        grid_x = int(x) // resolution
        grid_y = int(y) // resolution
        
        return (grid_x, grid_y) in self.collision_map
    
    def get_widget_center(self, widget):
        """
        Get the center point of a widget in window coordinates.
        
        Args:
            widget: The QWidget to get center of
            
        Returns:
            QPoint with center coordinates, or None if widget invalid
        """
        if not widget:
            return None
        
        # Get widget geometry
        rect = widget.geometry()
        
        # Get global position
        global_center = widget.mapToGlobal(rect.center())
        
        # Convert to main window coordinates
        local_center = self.main_window.mapFromGlobal(global_center)
        
        return local_center
    
    def get_widget_rect(self, widget):
        """
        Get the rectangle of a widget in window coordinates.
        
        Args:
            widget: The QWidget to get rect of
            
        Returns:
            QRect in window coordinates, or None if widget invalid
        """
        if not widget:
            return None
        
        # Get widget geometry
        local_rect = widget.geometry()
        
        # Get global rect
        global_pos = widget.mapToGlobal(QPoint(0, 0))
        
        # Convert to main window coordinates
        local_pos = self.main_window.mapFromGlobal(global_pos)
        
        return QRect(local_pos, local_rect.size())
    
    def get_widget_bounds(self, widget):
        """
        Get the bounding box of a widget.
        
        Args:
            widget: The QWidget to get bounds of
            
        Returns:
            Tuple of (left, top, right, bottom) or None
        """
        rect = self.get_widget_rect(widget)
        
        if not rect:
            return None
        
        return (
            rect.left(),
            rect.top(),
            rect.right(),
            rect.bottom()
        )
    
    def get_widgets_in_area(self, x, y, width, height):
        """
        Get all widgets in a rectangular area.
        
        Args:
            x: Left coordinate
            y: Top coordinate
            width: Width of area
            height: Height of area
            
        Returns:
            List of widgets in the area
        """
        area_rect = QRect(int(x), int(y), int(width), int(height))
        
        if not self.cache_valid:
            self.get_all_widgets()
        
        widgets_in_area = []
        
        for widget in self.cached_widgets:
            widget_rect = self.get_widget_rect(widget)
            if widget_rect and widget_rect.intersects(area_rect):
                widgets_in_area.append(widget)
        
        return widgets_in_area
    
    def get_nearest_widget(self, x, y, max_distance=200):
        """
        Get the nearest widget to a position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            max_distance: Maximum distance to search
            
        Returns:
            Tuple of (widget, distance) or (None, None) if none found
        """
        if not self.cache_valid:
            self.get_all_widgets()
        
        pos = QPoint(int(x), int(y))
        
        nearest_widget = None
        nearest_distance = float('inf')
        
        for widget in self.cached_widgets:
            center = self.get_widget_center(widget)
            if not center:
                continue
            
            # Calculate distance
            dx = center.x() - pos.x()
            dy = center.y() - pos.y()
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < nearest_distance and distance <= max_distance:
                nearest_distance = distance
                nearest_widget = widget
        
        if nearest_widget:
            return nearest_widget, nearest_distance
        
        return None, None
    
    def get_widget_type_name(self, widget):
        """
        Get a human-readable type name for a widget.
        
        Args:
            widget: The QWidget to get type of
            
        Returns:
            String type name
        """
        if isinstance(widget, QPushButton):
            return "button"
        elif isinstance(widget, QSlider):
            return "slider"
        elif isinstance(widget, QTabBar):
            return "tab"
        elif isinstance(widget, QComboBox):
            return "combobox"
        elif isinstance(widget, QCheckBox):
            return "checkbox"
        elif isinstance(widget, QRadioButton):
            return "radio"
        elif isinstance(widget, QLineEdit):
            return "textbox"
        else:
            return "widget"
    
    def invalidate_cache(self):
        """Invalidate the widget cache, forcing refresh on next query."""
        self.cache_valid = False
        self.cached_widgets = []
    
    def get_widget_info(self, widget):
        """
        Get comprehensive information about a widget.
        
        Args:
            widget: The QWidget to get info about
            
        Returns:
            Dict with widget information
        """
        if not widget:
            return None
        
        center = self.get_widget_center(widget)
        rect = self.get_widget_rect(widget)
        
        return {
            'widget': widget,
            'type': self.get_widget_type_name(widget),
            'class_name': widget.__class__.__name__,
            'center': (center.x(), center.y()) if center else None,
            'rect': (rect.x(), rect.y(), rect.width(), rect.height()) if rect else None,
            'text': widget.text() if hasattr(widget, 'text') else None,
            'enabled': widget.isEnabled(),
            'visible': widget.isVisible(),
        }


# Convenience function
def create_widget_detector(main_window):
    """
    Create a widget detector for a main window.
    
    Args:
        main_window: The QMainWindow or QWidget to detect widgets in
        
    Returns:
        WidgetDetector instance or None if PyQt not available
    """
    if not PYQT_AVAILABLE:
        logger.warning("PyQt6 not available, cannot create widget detector")
        return None
    
    return WidgetDetector(main_window)
