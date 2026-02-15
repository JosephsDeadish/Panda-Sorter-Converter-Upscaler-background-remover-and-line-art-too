"""
Qt Panel Loader - Dynamically loads Qt or Tkinter versions of panels
Author: Dead On The Inside / JosephsDeadish
"""

import logging

logger = logging.getLogger(__name__)

# Try to import PyQt6
try:
    from PyQt6.QtWidgets import QWidget
    PYQT6_AVAILABLE = True
    logger.info("PyQt6 available - will use Qt panels where implemented")
except ImportError:
    PYQT6_AVAILABLE = False
    logger.info("PyQt6 not available - using Tkinter panels")


def get_widgets_panel(parent, widget_collection, panda_callback=None):
    """
    Get widgets panel - Qt version if available, Tkinter otherwise.
    
    Args:
        parent: Parent widget
        widget_collection: WidgetCollection instance
        panda_callback: Callback for panda updates
        
    Returns:
        WidgetsPanel instance (Qt or Tkinter)
    """
    if PYQT6_AVAILABLE:
        try:
            from src.ui.widgets_panel_qt import WidgetsPanelQt
            logger.info("Using Qt widgets panel")
            return WidgetsPanelQt(widget_collection, panda_callback, parent)
        except Exception as e:
            logger.warning(f"Failed to load Qt widgets panel: {e}, falling back to Tkinter")
    
    from src.ui.widgets_panel import WidgetsPanel
    logger.info("Using Tkinter widgets panel")
    return WidgetsPanel(parent, widget_collection, panda_callback)


def get_closet_panel(parent, panda_closet, panda_character=None, panda_preview=None):
    """
    Get closet panel - Qt version if available, Tkinter otherwise.
    
    Args:
        parent: Parent widget
        panda_closet: PandaCloset instance
        panda_character: PandaCharacter instance
        panda_preview: Preview callback
        
    Returns:
        ClosetPanel instance (Qt or Tkinter)
    """
    if PYQT6_AVAILABLE:
        try:
            from src.ui.closet_display_qt import ClosetDisplayQt
            logger.info("Using Qt closet panel")
            return ClosetDisplayQt(parent)
        except Exception as e:
            logger.warning(f"Failed to load Qt closet panel: {e}, falling back to Tkinter")
    
    from src.ui.closet_panel import ClosetPanel
    logger.info("Using Tkinter closet panel")
    return ClosetPanel(parent, panda_closet, panda_character, panda_preview)


def get_hotkey_settings_panel(parent, hotkey_manager):
    """
    Get hotkey settings panel - Qt version if available, Tkinter otherwise.
    
    Args:
        parent: Parent widget
        hotkey_manager: HotkeyManager instance
        
    Returns:
        HotkeySettingsPanel instance (Qt or Tkinter)
    """
    if PYQT6_AVAILABLE:
        try:
            from src.ui.hotkey_display_qt import HotkeyDisplayQt
            logger.info("Using Qt hotkey settings panel")
            return HotkeyDisplayQt(parent)
        except Exception as e:
            logger.warning(f"Failed to load Qt hotkey panel: {e}, falling back to Tkinter")
    
    from src.ui.hotkey_settings_panel import HotkeySettingsPanel
    logger.info("Using Tkinter hotkey settings panel")
    return HotkeySettingsPanel(parent, hotkey_manager)


def get_customization_panel(parent, panda_closet, panda_character=None):
    """
    Get customization panel - Qt version if available, Tkinter otherwise.
    
    Args:
        parent: Parent widget
        panda_closet: PandaCloset instance
        panda_character: PandaCharacter instance
        
    Returns:
        CustomizationPanel instance (Qt or Tkinter)
    """
    if PYQT6_AVAILABLE:
        try:
            from src.ui.customization_panel_qt import CustomizationPanelQt
            logger.info("Using Qt customization panel")
            return CustomizationPanelQt(panda_character, panda_closet, parent)
        except Exception as e:
            logger.warning(f"Failed to load Qt customization panel: {e}, falling back to Tkinter")
    
    from src.ui.customization_panel import CustomizationPanel
    logger.info("Using Tkinter customization panel")
    return CustomizationPanel(parent, panda_closet, panda_character)


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
