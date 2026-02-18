"""
PyQt6 Color Picker
Replaces canvas-based color wheel with Qt color dialog and custom widgets
"""

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                 QLabel, QColorDialog, QLineEdit)
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QColor, QPainter, QConicalGradient, QPen
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class ColorPickerWidget(QWidget):
    """Color picker with dialog and preview"""
    
    color_changed = pyqtSignal(QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_color = QColor(255, 255, 255)
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
        self.hex_input.setText(self.current_color.name())
        self.hex_input.textChanged.connect(self.on_hex_changed)
        hex_layout.addWidget(self.hex_input)
        layout.addLayout(hex_layout)
        
        # RGB display
        self.rgb_label = QLabel(f"RGB: {self.current_color.red()}, {self.current_color.green()}, {self.current_color.blue()}")
        layout.addWidget(self.rgb_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        pick_btn = QPushButton("Pick Color...")
        pick_btn.clicked.connect(self.show_color_dialog)
        button_layout.addWidget(pick_btn)
        
        layout.addLayout(button_layout)
        
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
