"""
Qt Panel Loader - Loads Qt panels for UI
Qt/PyQt6 is the only supported UI framework.
Author: Dead On The Inside / JosephsDeadish
"""

import logging

logger = logging.getLogger(__name__)

# Try to import PyQt6 (required)
try:
    from PyQt6.QtWidgets import QWidget
    PYQT6_AVAILABLE = True
    logger.info("✅ PyQt6 available - using Qt panels")
except ImportError:
    PYQT6_AVAILABLE = False
    logger.error("❌ PyQt6 required but not available")
    logger.error("   Install with: pip install PyQt6")


def get_widgets_panel(parent, widget_collection, panda_callback=None):
    """
    Get Qt widgets panel.
    
    Args:
        parent: Parent widget
        widget_collection: WidgetCollection instance
        panda_callback: Callback for panda updates
        
    Returns:
        WidgetsPanelQt instance
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 required for widgets panel. Install with: pip install PyQt6")
    
    from ui.widgets_panel_qt import WidgetsPanelQt
    logger.info("Using Qt widgets panel")
    return WidgetsPanelQt(widget_collection, panda_callback, parent)


def get_closet_panel(parent, panda_closet, panda_character=None, panda_preview=None):
    """
    Get Qt closet panel.
    
    Args:
        parent: Parent widget
        panda_closet: PandaCloset instance
        panda_character: PandaCharacter instance
        panda_preview: Preview callback
        
    Returns:
        ClosetDisplayQt instance
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 required for closet panel. Install with: pip install PyQt6")
    
    from ui.closet_display_qt import ClosetDisplayQt
    logger.info("Using Qt closet panel")
    return ClosetDisplayQt(parent)


def get_hotkey_settings_panel(parent, hotkey_manager):
    """
    Get Qt hotkey settings panel.
    
    Args:
        parent: Parent widget
        hotkey_manager: HotkeyManager instance
        
    Returns:
        HotkeyDisplayQt instance
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 required for hotkey panel. Install with: pip install PyQt6")
    
    from ui.hotkey_display_qt import HotkeyDisplayQt
    logger.info("Using Qt hotkey settings panel")
    return HotkeyDisplayQt(parent)


def get_customization_panel(parent, panda_closet, panda_character=None):
    """
    Get Qt customization panel.
    
    Args:
        parent: Parent widget
        panda_closet: PandaCloset instance
        panda_character: PandaCharacter instance
        
    Returns:
        CustomizationPanelQt instance
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 required for customization panel. Install with: pip install PyQt6")
    
    from ui.customization_panel_qt import CustomizationPanelQt
    logger.info("Using Qt customization panel")
    return CustomizationPanelQt(panda_character, panda_closet, parent)


def get_background_remover_panel(parent):
    """
    Get Qt background remover panel.
    
    Args:
        parent: Parent widget
        
    Returns:
        BackgroundRemoverPanelQt instance
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 required for background remover panel. Install with: pip install PyQt6")
    
    from ui.background_remover_panel_qt import BackgroundRemoverPanelQt
    logger.info("Using Qt background remover panel")
    return BackgroundRemoverPanelQt(parent)


def get_batch_rename_panel(parent, unlockables_system=None, tooltip_manager=None):
    """
    Get Qt batch rename panel.
    
    Args:
        parent: Parent widget
        unlockables_system: Unlockables system instance (optional)
        tooltip_manager: Tooltip manager instance (optional)
        
    Returns:
        BatchRenamePanelQt instance
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 required for batch rename panel. Install with: pip install PyQt6")
    
    from ui.batch_rename_panel_qt import BatchRenamePanelQt
    logger.info("Using Qt batch rename panel")
    return BatchRenamePanelQt(parent, tooltip_manager)


def get_lineart_converter_panel(parent, unlockables_system=None, tooltip_manager=None):
    """
    Get Qt line art converter panel.
    
    Args:
        parent: Parent widget
        unlockables_system: Unlockables system instance (optional)
        tooltip_manager: Tooltip manager instance (optional)
        
    Returns:
        LineArtConverterPanelQt instance
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 required for lineart converter panel. Install with: pip install PyQt6")
    
    from ui.lineart_converter_panel_qt import LineArtConverterPanelQt
    logger.info("Using Qt line art converter panel")
    return LineArtConverterPanelQt(parent, tooltip_manager)


def get_image_repair_panel(parent, unlockables_system=None, tooltip_manager=None):
    """
    Get Qt image repair panel.
    
    Args:
        parent: Parent widget
        unlockables_system: Unlockables system instance (optional)
        tooltip_manager: Tooltip manager instance (optional)
        
    Returns:
        ImageRepairPanelQt instance
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 required for image repair panel. Install with: pip install PyQt6")
    
    from ui.image_repair_panel_qt import ImageRepairPanelQt
    logger.info("Using Qt image repair panel")
    return ImageRepairPanelQt(parent, tooltip_manager)


def get_minigame_panel(parent, minigame_manager=None):
    """
    Get Qt minigame panel.
    
    Args:
        parent: Parent widget
        minigame_manager: Minigame manager instance (optional)
        
    Returns:
        MiniGamePanelQt instance
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 required for minigame panel. Install with: pip install PyQt6")
    
    from ui.minigame_panel_qt import MiniGamePanelQt
    logger.info("Using Qt minigame panel")
    return MiniGamePanelQt(parent, minigame_manager)
