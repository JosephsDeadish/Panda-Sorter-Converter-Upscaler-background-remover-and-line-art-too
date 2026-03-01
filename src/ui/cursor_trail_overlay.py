"""
Cursor Trail Overlay
====================
Transparent frameless QWidget that overlays the main window and paints a
fading dot-trail wherever the mouse cursor moves.

Usage (from main window)::

    from ui.cursor_trail_overlay import CursorTrailOverlay
    self._cursor_trail = CursorTrailOverlay(self)
    self._cursor_trail.set_color_scheme('rainbow')
    self._cursor_trail.show()
    # To remove:
    self._cursor_trail.hide()
    self._cursor_trail.deleteLater()
    self._cursor_trail = None
"""
from __future__ import annotations

import math
from collections import deque

try:
    from PyQt6.QtWidgets import QWidget, QApplication
    from PyQt6.QtCore import Qt, QTimer, QPoint, QEvent, QObject
    from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
    _PYQT_OK = True
except (ImportError, OSError, RuntimeError):
    _PYQT_OK = False
    QWidget = object  # type: ignore[assignment,misc]
    QObject = object  # type: ignore[assignment,misc]


# ─── colour schemes ────────────────────────────────────────────────────────────
_SCHEMES: dict[str, list[tuple[int, int, int]]] = {
    'rainbow':   [(255, 0, 0), (255, 128, 0), (255, 255, 0),
                  (0, 200, 0), (0, 128, 255), (128, 0, 255)],
    'sparkle':   [(255, 220, 50), (255, 255, 150), (200, 200, 255),
                  (255, 200, 255), (180, 255, 180)],
    'fire':      [(255, 50, 0), (255, 120, 0), (255, 200, 0),
                  (255, 80, 30), (200, 20, 0)],
    'ice':       [(180, 230, 255), (100, 200, 255), (60, 160, 255),
                  (200, 240, 255), (130, 200, 230)],
    'purple':    [(180, 0, 255), (140, 50, 200), (200, 100, 255),
                  (100, 0, 200), (220, 150, 255)],
    'white':     [(255, 255, 255)],
    'red':       [(220, 30, 30)],
    'blue':      [(30, 100, 255)],
    'green':     [(30, 200, 80)],
    'gold':      [(255, 200, 0), (255, 165, 0), (200, 130, 0)],
    # Additional schemes to match settings combo options
    'nature':    [(60, 180, 60), (100, 220, 80), (40, 140, 40),
                  (160, 220, 100), (80, 200, 120)],
    'galaxy':    [(80, 0, 160), (0, 60, 180), (160, 0, 200),
                  (30, 0, 100), (200, 100, 255), (0, 200, 255)],
    'silver':    [(200, 200, 210), (160, 170, 185), (220, 220, 230),
                  (180, 185, 195), (240, 240, 245)],
    'neon':      [(0, 255, 100), (0, 200, 255), (255, 0, 200),
                  (200, 255, 0), (255, 100, 0)],
}
# Aliases so key lookups are forgiving
_SCHEME_ALIASES = {
    'sparkles': 'sparkle',   # "Sparkles" combo entry maps to 'sparkle' scheme
    'neon_green': 'neon',
    'forest': 'nature',
}

_MAX_DOTS = 30        # trail length (number of positions kept)
_DOT_BASE_SIZE = 8    # px diameter of freshest dot
_TICK_MS = 16         # ~60 fps repaint timer


class CursorTrailOverlay(QWidget):  # type: ignore[misc]
    """Transparent overlay that draws a fading cursor trail.

    Parent *must* be the main window.  The overlay resizes itself whenever
    the parent resizes so it always covers the full window area.
    """

    def __init__(self, parent: QWidget):
        if not _PYQT_OK:
            raise ImportError("PyQt6 is required for CursorTrailOverlay")
        super().__init__(parent)

        # Make completely transparent to mouse events (clicks pass through)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowTransparentForInput)

        self._dots: deque[tuple[int, int]] = deque(maxlen=_MAX_DOTS)
        self._color_idx = 0
        self._scheme: list[tuple[int, int, int]] = _SCHEMES['rainbow']
        self._intensity: int = 5  # 1–10; default mid

        # Install event filter on QApplication so ALL child-widget mouse events
        # are captured (installing only on parent misses events on child widgets).
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        elif parent is not None:
            parent.installEventFilter(self)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(_TICK_MS)

        self._cover_parent()

    # ── public API ────────────────────────────────────────────────────────────

    def set_color_scheme(self, name: str) -> None:
        """Set trail colour scheme by name (see _SCHEMES)."""
        key = name.lower().replace(' ', '_')
        # Resolve alias first, then look up scheme
        key = _SCHEME_ALIASES.get(key, key)
        self._scheme = _SCHEMES.get(key, _SCHEMES['rainbow'])
        self._color_idx = 0

    def set_intensity(self, level: int) -> None:
        """Set trail intensity (1–10).

        Higher intensity means more dots kept and a slightly larger dot size.
        """
        level = max(1, min(10, int(level)))
        self._dots = deque(self._dots, maxlen=max(5, level * 4))  # 4–40 dots
        self._intensity = level

    # ── event filter on parent ────────────────────────────────────────────────

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # type: ignore[override]
        """Intercept mouse-move events anywhere in the app to record trail positions.

        Since we install the filter on QApplication, pos() is relative to the
        source widget.  Convert to parent-window-local coords via globalPos().
        """
        try:
            if event.type() == QEvent.Type.MouseMove:
                # globalPosition() → QPointF in Qt6; map to our parent widget's local frame
                p = self.parent()
                if p is not None:
                    global_pos = event.globalPosition().toPoint()  # type: ignore[attr-defined]
                    # toPoint() converts QPointF → QPoint (integer pixel coords for trail dots)
                    local_pos = p.mapFromGlobal(global_pos)
                    self._dots.append((local_pos.x(), local_pos.y()))
        except Exception:
            pass
        return False  # never consume the event

    # ── Qt overrides ──────────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        self._cover_parent()
        super().resizeEvent(event)

    def showEvent(self, event) -> None:
        self._cover_parent()
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        self._dots.clear()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        # Remove the app-level event filter on cleanup
        try:
            app = QApplication.instance()
            if app is not None:
                app.removeEventFilter(self)
        except Exception:
            pass
        super().closeEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if not self._dots:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(Qt.PenStyle.NoPen))

        n = len(self._dots)
        dots = list(self._dots)
        scheme = self._scheme
        s_len = len(scheme)

        for i, (x, y) in enumerate(dots):
            # Oldest dot = index 0, newest = index n-1
            progress = (i + 1) / n          # 0..1 (newest = 1.0)
            alpha = int(progress * 220)
            # Scale dot size by both trail progress and intensity (1=small, 10=large)
            dot_base = _DOT_BASE_SIZE * (0.5 + self._intensity * 0.1)
            size = max(2, int(dot_base * progress))
            # Cycle through colour palette based on position in trail
            r, g, b = scheme[(i + self._color_idx) % s_len]
            color = QColor(r, g, b, alpha)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x - size // 2, y - size // 2, size, size)

        self._color_idx = (self._color_idx + 1) % max(1, s_len)
        painter.end()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _cover_parent(self) -> None:
        """Resize/reposition to cover the entire parent widget."""
        p = self.parent()
        if p is not None:
            try:
                self.setGeometry(0, 0, p.width(), p.height())
                self.raise_()
            except Exception:
                pass
