"""
Qt Widget Bridge - Helper functions for integrating Qt widgets into existing codebase
Provides compatibility layer and utility functions
"""

from typing import Optional, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)

# Check Qt availability
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    logger.warning("PyQt6 not available - Qt widgets disabled")


class QtIntegrationHelper:
    """Helper class for integrating Qt widgets"""
    
    _qt_app = None
    _qt_widgets_active = []
    
    @classmethod
    def ensure_qt_app(cls):
        """Ensure Qt application exists"""
        if not QT_AVAILABLE:
            return False
        
        if QApplication.instance() is None:
            cls._qt_app = QApplication([])
        return True
    
    @classmethod
    def show_achievement_popup(cls, achievement_data: Dict, parent_geometry: tuple = None) -> bool:
        """
        Show achievement popup using Qt widget
        
        Args:
            achievement_data: Dict with 'name', 'emoji', 'description'
            parent_geometry: (x, y, width, height) for positioning
        
        Returns:
            True if shown, False if Qt not available
        """
        if not cls.ensure_qt_app():
            return False
        
        try:
            from src.ui.qt_achievement_popup import AchievementPopup
            
            popup = AchievementPopup(achievement_data)
            if parent_geometry:
                popup.show_popup(parent_geometry)
            else:
                popup.show_popup()
            
            cls._qt_widgets_active.append(popup)
            return True
            
        except Exception as e:
            logger.error(f"Failed to show Qt achievement popup: {e}")
            return False
    
    @classmethod
    def create_dungeon_viewport(cls, parent=None):
        """Create dungeon viewport widget"""
        if not cls.ensure_qt_app():
            return None
        
        try:
            from src.ui.qt_dungeon_viewport import DungeonViewportWidget
            return DungeonViewportWidget(parent)
        except Exception as e:
            logger.error(f"Failed to create dungeon viewport: {e}")
            return None
    
    @classmethod
    def create_enemy_widget(cls, enemy_data: Dict = None, parent=None):
        """Create enemy display widget"""
        if not cls.ensure_qt_app():
            return None
        
        try:
            from src.ui.qt_enemy_widget import EnemyDisplayWidget
            widget = EnemyDisplayWidget(parent)
            if enemy_data:
                widget.set_enemy(enemy_data)
            return widget
        except Exception as e:
            logger.error(f"Failed to create enemy widget: {e}")
            return None
    
    @classmethod
    def create_travel_animation(cls, scenes: List = None, parent=None):
        """Create travel animation widget"""
        if not cls.ensure_qt_app():
            return None
        
        try:
            from src.ui.qt_travel_animation import TravelAnimationWidget
            return TravelAnimationWidget(scenes, parent)
        except Exception as e:
            logger.error(f"Failed to create travel animation: {e}")
            return None
    
    @classmethod
    def create_visual_effects(cls, use_3d: bool = False, parent=None):
        """Create visual effects widget"""
        if not cls.ensure_qt_app():
            return None
        
        try:
            from src.ui.qt_visual_effects import create_visual_effects_widget
            return create_visual_effects_widget(use_3d, parent)
        except Exception as e:
            logger.error(f"Failed to create visual effects widget: {e}")
            return None
    
    @classmethod
    def create_color_preview(cls, parent=None):
        """Create color preview widget"""
        if not cls.ensure_qt_app():
            return None
        
        try:
            from src.ui.qt_preview_widgets import create_color_preview
            return create_color_preview()
        except Exception as e:
            logger.error(f"Failed to create color preview: {e}")
            return None
    
    @classmethod
    def create_item_preview(cls, parent=None):
        """Create item preview widget"""
        if not cls.ensure_qt_app():
            return None
        
        try:
            from src.ui.qt_preview_widgets import create_item_preview
            return create_item_preview()
        except Exception as e:
            logger.error(f"Failed to create item preview: {e}")
            return None
    
    @classmethod
    def create_item_list(cls, parent=None):
        """Create item list widget"""
        if not cls.ensure_qt_app():
            return None
        
        try:
            from src.ui.qt_preview_widgets import create_item_list
            return create_item_list()
        except Exception as e:
            logger.error(f"Failed to create item list: {e}")
            return None
    
    @classmethod
    def create_item_grid(cls, columns: int = 3, parent=None):
        """Create item grid widget"""
        if not cls.ensure_qt_app():
            return None
        
        try:
            from src.ui.qt_preview_widgets import create_item_grid
            return create_item_grid(columns)
        except Exception as e:
            logger.error(f"Failed to create item grid: {e}")
            return None
    
    @classmethod
    def create_image_preview(cls, parent=None):
        """Create image preview widget"""
        if not cls.ensure_qt_app():
            return None
        
        try:
            from src.ui.qt_preview_widgets import create_image_preview
            return create_image_preview()
        except Exception as e:
            logger.error(f"Failed to create image preview: {e}")
            return None
    
    @classmethod
    def cleanup(cls):
        """Cleanup Qt resources"""
        cls._qt_widgets_active.clear()
        if cls._qt_app:
            try:
                cls._qt_app.quit()
            except:
                pass


# Convenience functions
def qt_available() -> bool:
    """Check if Qt is available"""
    return QT_AVAILABLE


def show_achievement_qt(achievement_data: Dict, parent_geometry: tuple = None) -> bool:
    """Show achievement popup - convenience function"""
    return QtIntegrationHelper.show_achievement_popup(achievement_data, parent_geometry)


def create_dungeon_viewport_qt(parent=None):
    """Create dungeon viewport - convenience function"""
    return QtIntegrationHelper.create_dungeon_viewport(parent)


def create_enemy_widget_qt(enemy_data: Dict = None, parent=None):
    """Create enemy widget - convenience function"""
    return QtIntegrationHelper.create_enemy_widget(enemy_data, parent)


def create_travel_animation_qt(scenes: List = None, parent=None):
    """Create travel animation - convenience function"""
    return QtIntegrationHelper.create_travel_animation(scenes, parent)


def create_visual_effects_qt(use_3d: bool = False, parent=None):
    """Create visual effects widget - convenience function"""
    return QtIntegrationHelper.create_visual_effects(use_3d, parent)


def create_preview_widgets_qt(widget_type: str, **kwargs):
    """
    Create preview widget by type - convenience function
    
    Args:
        widget_type: 'color', 'item', 'list', 'grid', 'image'
        **kwargs: Additional arguments for widget creation
    
    Returns:
        Qt widget or None
    """
    if widget_type == 'color':
        return QtIntegrationHelper.create_color_preview()
    elif widget_type == 'item':
        return QtIntegrationHelper.create_item_preview()
    elif widget_type == 'list':
        return QtIntegrationHelper.create_item_list()
    elif widget_type == 'grid':
        columns = kwargs.get('columns', 3)
        return QtIntegrationHelper.create_item_grid(columns)
    elif widget_type == 'image':
        return QtIntegrationHelper.create_image_preview()
    else:
        logger.warning(f"Unknown widget type: {widget_type}")
        return None
