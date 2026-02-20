"""
UI Module
Custom UI components and customization systems
"""

import logging
_log = logging.getLogger(__name__)

# ColorWheelWidget lives in settings_panel_qt (pure-Python, no PyQt6 at class definition)
try:
    from .settings_panel_qt import ColorWheelWidget
    from .customization_panel_qt import CustomizationPanelQt
    from .archive_queue_widgets_qt import ProcessingQueueQt
    __all__ = ['ColorWheelWidget', 'CustomizationPanelQt', 'ProcessingQueueQt']
except ImportError as _e:
    _log.debug(f"Qt UI widgets not available (PyQt6 not installed?): {_e}")
    __all__ = []
