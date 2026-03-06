"""
panda_widget_2d.py - Stub replacement for the 2D QPainter floating overlay panda widget.

This stub replaces the original 1013-line 2D QPainter animated companion panda overlay.
The floating overlay has been removed per issue #207. All public API symbols are
preserved so that existing imports and call sites continue to work without errors.
"""

try:
    from PyQt6.QtWidgets import QWidget
    from PyQt6.QtCore import pyqtSignal
    _QT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    _QT_AVAILABLE = False

    class _StubSignal:
        """Minimal signal stub used when PyQt6 is unavailable."""
        def __init__(self, *args, **kwargs):
            pass
        def connect(self, *args, **kwargs):
            pass
        def disconnect(self, *args, **kwargs):
            pass
        def emit(self, *args, **kwargs):
            pass

    def pyqtSignal(*args, **kwargs):  # noqa: N802 – name must match PyQt6 API
        return _StubSignal()

    class QWidget:  # type: ignore[no-redef]
        """Minimal QWidget stub used when PyQt6 is unavailable."""
        def __init__(self, parent=None):
            pass
        def hide(self):
            pass


# Always use QWidget (real or stub) so hide() is always available.
_Base = QWidget


class PandaWidget2D(_Base):
    """
    Stub for the 2D QPainter panda companion overlay widget (issue #207).

    The original implementation painted an animated panda directly onto the
    application window using QPainter.  This stub preserves the public interface
    so that all import sites and call sites remain valid while the overlay is
    disabled.
    """

    panda = None

    if _QT_AVAILABLE:
        clicked = pyqtSignal()
        mood_changed = pyqtSignal(str)
        animation_changed = pyqtSignal(str)
        food_eaten = pyqtSignal(str)
    else:
        clicked = pyqtSignal()
        mood_changed = pyqtSignal(str)
        animation_changed = pyqtSignal(str)
        food_eaten = pyqtSignal(str)

    def __init__(self, panda_character=None, parent=None):
        super().__init__(parent)
        self.hide()
        self.panda = panda_character
        self.animation_state = 'idle'

    # ------------------------------------------------------------------
    # No-op public API methods
    # ------------------------------------------------------------------

    def set_mood(self, *args, **kwargs):
        pass

    def set_animation(self, *args, **kwargs):
        pass

    def set_animation_state(self, *args, **kwargs):
        pass

    def set_autonomous_mode(self, *args, **kwargs):
        pass

    def equip_clothing(self, *args, **kwargs):
        pass

    def equip_item(self, *args, **kwargs):
        pass

    def update_appearance(self, *args, **kwargs):
        pass

    def get_info(self, *args, **kwargs):
        return {}

    def add_item_from_emoji(self, *args, **kwargs):
        pass

    def add_item_3d(self, *args, **kwargs):
        pass

    def clear_items(self, *args, **kwargs):
        pass

    def set_theme(self, *args, **kwargs):
        pass

    def set_color(self, *args, **kwargs):
        pass

    def set_trail(self, *args, **kwargs):
        pass

    def set_fur_style(self, *args, **kwargs):
        pass

    def set_hair_style(self, *args, **kwargs):
        pass

    def preview_item(self, *args, **kwargs):
        pass

    def walk_to_position(self, *args, **kwargs):
        pass

    def notify_button_nearby(self, *args, **kwargs):
        pass

    def notify_file_dragged(self, *args, **kwargs):
        pass

    def get_idle_sub_state(self, *args, **kwargs):
        return ''
