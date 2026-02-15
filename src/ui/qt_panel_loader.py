"""
Qt Panel Loader - Loads Qt panels for UI
Qt/PyQt6 is now required - Tkinter fallbacks have been removed.
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
    
    from src.ui.widgets_panel_qt import WidgetsPanelQt
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
    
    from src.ui.closet_display_qt import ClosetDisplayQt
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
    
    from src.ui.hotkey_display_qt import HotkeyDisplayQt
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
    
    from src.ui.customization_panel_qt import CustomizationPanelQt
    logger.info("Using Qt customization panel")
    return CustomizationPanelQt(panda_character, panda_closet, parent)


def get_background_remover_panel(parent):
    """
    Get background remover panel - Qt version if available, Tkinter otherwise.
    
    Args:
        parent: Parent widget
        
    Returns:
        BackgroundRemoverPanel instance (Qt or Tkinter)
    """
    if PYQT6_AVAILABLE:
        try:
            from src.ui.background_remover_panel_qt import BackgroundRemoverPanelQt
            logger.info("Using Qt background remover panel")
            return BackgroundRemoverPanelQt(parent)
        except Exception as e:
            logger.warning(f"Failed to load Qt background remover panel: {e}, falling back to Tkinter")
    
    from src.ui.background_remover_panel import BackgroundRemoverPanel
    logger.info("Using Tkinter background remover panel")
    return BackgroundRemoverPanel(parent)


def get_batch_rename_panel(parent, unlockables_system=None, tooltip_manager=None):
    """
    Get batch rename panel - Qt version if available, Tkinter otherwise.
    
    Args:
        parent: Parent widget
        unlockables_system: Unlockables system instance
        tooltip_manager: Tooltip manager instance
        
    Returns:
        BatchRenamePanel instance (Qt or Tkinter)
    """
    if PYQT6_AVAILABLE:
        try:
            from src.ui.batch_rename_panel_qt import BatchRenamePanelQt
            logger.info("Using Qt batch rename panel")
            return BatchRenamePanelQt(parent, tooltip_manager)
        except Exception as e:
            logger.warning(f"Failed to load Qt batch rename panel: {e}, falling back to Tkinter")
    
    from src.ui.batch_rename_panel import BatchRenamePanel
    logger.info("Using Tkinter batch rename panel")
    return BatchRenamePanel(parent, unlockables_system, tooltip_manager)


def get_lineart_converter_panel(parent, unlockables_system=None, tooltip_manager=None):
    """
    Get line art converter panel - Qt version if available, Tkinter otherwise.
    
    Args:
        parent: Parent widget
        unlockables_system: Unlockables system instance
        tooltip_manager: Tooltip manager instance
        
    Returns:
        LineArtConverterPanel instance (Qt or Tkinter)
    """
    if PYQT6_AVAILABLE:
        try:
            from src.ui.lineart_converter_panel_qt import LineArtConverterPanelQt
            logger.info("Using Qt line art converter panel")
            return LineArtConverterPanelQt(parent, tooltip_manager)
        except Exception as e:
            logger.warning(f"Failed to load Qt line art converter panel: {e}, falling back to Tkinter")
    
    from src.ui.lineart_converter_panel import LineArtConverterPanel
    logger.info("Using Tkinter line art converter panel")
    return LineArtConverterPanel(parent, unlockables_system, tooltip_manager)


def get_image_repair_panel(parent, unlockables_system=None, tooltip_manager=None):
    """
    Get image repair panel - Qt version if available, Tkinter otherwise.
    
    Args:
        parent: Parent widget
        unlockables_system: Unlockables system instance
        tooltip_manager: Tooltip manager instance
        
    Returns:
        ImageRepairPanel instance (Qt or Tkinter)
    """
    if PYQT6_AVAILABLE:
        try:
            from src.ui.image_repair_panel_qt import ImageRepairPanelQt
            logger.info("Using Qt image repair panel")
            return ImageRepairPanelQt(parent, tooltip_manager)
        except Exception as e:
            logger.warning(f"Failed to load Qt image repair panel: {e}, falling back to Tkinter")
    
    from src.ui.image_repair_panel import ImageRepairPanel
    logger.info("Using Tkinter image repair panel")
    return ImageRepairPanel(parent, unlockables_system, tooltip_manager)


def get_minigame_panel(parent, minigame_manager=None):
    """
    Get minigame panel - Qt version if available, Tkinter otherwise.
    
    Args:
        parent: Parent widget
        minigame_manager: MiniGameManager instance
        
    Returns:
        MiniGamePanel instance (Qt or Tkinter)
    """
    if PYQT6_AVAILABLE:
        try:
            from src.ui.minigame_panel_qt import MiniGamePanelQt
            logger.info("Using Qt minigame panel")
            return MiniGamePanelQt(parent, minigame_manager)
        except Exception as e:
            logger.warning(f"Failed to load Qt minigame panel: {e}, falling back to Tkinter")
    
    from src.ui.minigame_panel import MiniGamePanel
    logger.info("Using Tkinter minigame panel")
    return MiniGamePanel(parent, minigame_manager)
