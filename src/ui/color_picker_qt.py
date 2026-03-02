"""
PyQt6 Color Picker
Replaces canvas-based color wheel with Qt color dialog and custom widgets
"""


from __future__ import annotations
import logging
try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                 QLabel, QColorDialog, QLineEdit)
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QColor, QPainter, QConicalGradient, QPen
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    class QObject:  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class QWidget(QObject):  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class QColor:  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        def __init__(self, *args): pass
    class _SignalStub:  # noqa: E301
        """Stub signal — active only when PyQt6 is absent."""
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SignalStub()  # noqa: E301


logger = logging.getLogger(__name__)


class ColorPickerWidget(QWidget):
    """Color picker with dialog and preview"""
    
    color_changed = pyqtSignal(QColor)

    _MAX_RECENT = 8   # number of recent colours to display
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_color = QColor(255, 255, 255)
        self._recent_colors: list = []   # list of QColor, most-recent first
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Color preview
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("Current Color:"))
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(100, 50)
        self.color_preview.setStyleSheet(f"background-color: {self.current_color.name()}; border: 2px solid black;")
        preview_layout.addWidget(self.color_preview)
        
        layout.addLayout(preview_layout)
        
        # Hex input
        hex_layout = QHBoxLayout()
        hex_layout.addWidget(QLabel("Hex:"))
        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("#rrggbb")
        self.hex_input.setText(self.current_color.name())
        self.hex_input.textChanged.connect(self.on_hex_changed)
        hex_layout.addWidget(self.hex_input)
        layout.addLayout(hex_layout)
        
        # RGB display
        self.rgb_label = QLabel(f"RGB: {self.current_color.red()}, {self.current_color.green()}, {self.current_color.blue()}")
        layout.addWidget(self.rgb_label)

        # Recent colours row
        recent_row_label = QLabel("Recent:")
        layout.addWidget(recent_row_label)
        self._recent_row = QHBoxLayout()
        self._recent_swatches: list = []
        for _ in range(self._MAX_RECENT):
            swatch = QPushButton()
            swatch.setFixedSize(22, 22)
            swatch.setStyleSheet("background-color: transparent; border: 1px solid #555; border-radius: 3px;")
            swatch.setFlat(True)
            self._recent_row.addWidget(swatch)
            self._recent_swatches.append(swatch)
        self._recent_row.addStretch()
        layout.addLayout(self._recent_row)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        pick_btn = QPushButton("Pick Color...")
        pick_btn.setToolTip("Open a colour picker dialog")
        pick_btn.clicked.connect(self.show_color_dialog)
        button_layout.addWidget(pick_btn)
        
        layout.addLayout(button_layout)

    def _update_recent_swatches(self) -> None:
        """Refresh the recent-colour swatches row."""
        for i, swatch in enumerate(self._recent_swatches):
            if i < len(self._recent_colors):
                c = self._recent_colors[i]
                swatch.setStyleSheet(
                    f"QPushButton {{ background-color: {c.name()}; border: 1px solid #555; border-radius: 3px; }}"
                )
                swatch.setToolTip(c.name())
                # Disconnect any previous connection then reconnect
                try:
                    swatch.clicked.disconnect()
                except Exception:
                    pass
                swatch.clicked.connect((lambda col: (lambda: self.set_color(col)))(c))
            else:
                swatch.setStyleSheet(
                    "QPushButton { background-color: transparent; border: 1px solid #555; border-radius: 3px; }"
                )
                swatch.setToolTip("")
                try:
                    swatch.clicked.disconnect()
                except Exception:
                    pass
        
    def show_color_dialog(self):
        """Show Qt color dialog"""
        color = QColorDialog.getColor(self.current_color, self, "Select Color")
        if color.isValid():
            self.set_color(color)
            
    def set_color(self, color):
        """Set current color"""
        if not isinstance(color, QColor):
            color = QColor(color)
            
        self.current_color = color
        self.color_preview.setStyleSheet(f"background-color: {color.name()}; border: 2px solid black;")
        self.hex_input.setText(color.name())
        self.rgb_label.setText(f"RGB: {color.red()}, {color.green()}, {color.blue()}")
        # Push to recent colours (deduplicate by name, most-recent first)
        if hasattr(self, '_recent_colors'):
            self._recent_colors = [c for c in self._recent_colors if c.name() != color.name()]
            self._recent_colors.insert(0, QColor(color.name()))
            self._recent_colors = self._recent_colors[:self._MAX_RECENT]
            self._update_recent_swatches()
        self.color_changed.emit(color)
        
    def get_color(self):
        """Get current color"""
        return self.current_color
        
    def on_hex_changed(self, text):
        """Handle hex input change"""
        if text.startswith('#') and len(text) == 7:
            try:
                color = QColor(text)
                if color.isValid():
                    self.current_color = color
                    self.color_preview.setStyleSheet(f"background-color: {text}; border: 2px solid black;")
                    self.rgb_label.setText(f"RGB: {color.red()}, {color.green()}, {color.blue()}")
                    self.color_changed.emit(color)
            except Exception as e:
                # Silently ignore invalid color formats
                logger.debug(f"Color parsing error: {e}")
                pass


def create_color_picker(parent=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return ColorPickerWidget(parent)
