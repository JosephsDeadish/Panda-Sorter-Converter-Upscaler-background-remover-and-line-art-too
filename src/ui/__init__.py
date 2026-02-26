"""
UI Module
Custom UI components and customization systems
"""

import logging
_log = logging.getLogger(__name__)

# Each widget is imported independently so one failure doesn't disable all exports.
ColorWheelWidget = None
CustomizationPanelQt = None
ProcessingQueueQt = None

try:
    from .settings_panel_qt import ColorWheelWidget  # type: ignore[assignment]
except Exception as _e:
    _log.debug(f"ColorWheelWidget not available: {_e}")

try:
    from .customization_panel_qt import CustomizationPanelQt  # type: ignore[assignment]
except Exception as _e:
    _log.debug(f"CustomizationPanelQt not available: {_e}")

try:
    from .archive_queue_widgets_qt import ProcessingQueueQt  # type: ignore[assignment]
except Exception as _e:
    _log.debug(f"ProcessingQueueQt not available: {_e}")

__all__ = [name for name in ['ColorWheelWidget', 'CustomizationPanelQt', 'ProcessingQueueQt']
           if globals().get(name) is not None]
