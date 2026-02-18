"""
Qt implementation of the customization panel.
Pure PyQt6 UI for texture customization options.
"""

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                  QLabel, QSlider, QComboBox, QColorDialog, QGroupBox)
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    class QWidget: pass
    class pyqtSignal: pass


class CustomizationPanelQt(QWidget):
    """Qt-based customization panel for panda appearance."""
    
    # Signals
    color_changed = pyqtSignal(object) if PYQT_AVAILABLE else None
    trail_changed = pyqtSignal(str, object) if PYQT_AVAILABLE else None
    
    def __init__(self, panda_character, panda_widget, parent=None, tooltip_manager=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for CustomizationPanelQt")
        
        super().__init__(parent)
        self.panda_character = panda_character
        self.panda_widget = panda_widget
        self.current_color = QColor(255, 255, 255)
        self.tooltip_manager = tooltip_manager
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the UI layout."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎨 Panda Customization")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Color section
        color_group = QGroupBox("Colors")
        color_layout = QVBoxLayout()
        
        # Body color
        body_layout = QHBoxLayout()
        body_layout.addWidget(QLabel("Body Color:"))
        self.body_color_btn = QPushButton("Choose Color")
        self.body_color_btn.clicked.connect(lambda: self.choose_color('body'))
        body_layout.addWidget(self.body_color_btn)
        color_layout.addLayout(body_layout)
        
        # Eye color
        eye_layout = QHBoxLayout()
        eye_layout.addWidget(QLabel("Eye Color:"))
        self.eye_color_btn = QPushButton("Choose Color")
        self.eye_color_btn.clicked.connect(lambda: self.choose_color('eyes'))
        eye_layout.addWidget(self.eye_color_btn)
        color_layout.addLayout(eye_layout)
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # Trail section
        trail_group = QGroupBox("Movement Trail")
        trail_layout = QVBoxLayout()
        
        # Trail type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Trail Type:"))
        self.trail_combo = QComboBox()
        self.trail_combo.addItems(["None", "Dots", "Line", "Glow", "Particles"])
        self.trail_combo.currentTextChanged.connect(self.on_trail_changed)
        type_layout.addWidget(self.trail_combo)
        trail_layout.addLayout(type_layout)
        
        # Trail color
        trail_color_layout = QHBoxLayout()
        trail_color_layout.addWidget(QLabel("Trail Color:"))
        self.trail_color_btn = QPushButton("Choose Color")
        self.trail_color_btn.clicked.connect(lambda: self.choose_color('trail'))
        trail_color_layout.addWidget(self.trail_color_btn)
        trail_layout.addLayout(trail_color_layout)
        
        # Trail length
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Trail Length:"))
        self.trail_slider = QSlider(Qt.Orientation.Horizontal)
        self.trail_slider.setMinimum(1)
        self.trail_slider.setMaximum(20)
        self.trail_slider.setValue(10)
        self.trail_slider.valueChanged.connect(self.on_trail_changed)
        length_layout.addWidget(self.trail_slider)
        trail_layout.addLayout(length_layout)
        
        trail_group.setLayout(trail_layout)
        layout.addWidget(trail_group)
        
        # Actions
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("✓ Apply Changes")
        apply_btn.clicked.connect(self.apply_customization)
        button_layout.addWidget(apply_btn)
        
        reset_btn = QPushButton("↺ Reset to Default")
        reset_btn.clicked.connect(self.reset_customization)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
    
    def choose_color(self, color_type):
        """Open color picker dialog."""
        color = QColorDialog.getColor(self.current_color, self, f"Choose {color_type} color")
        
        if color.isValid():
            self.current_color = color
            
            # Update button color
            if color_type == 'body':
                self.body_color_btn.setStyleSheet(f"background-color: {color.name()};")
            elif color_type == 'eyes':
                self.eye_color_btn.setStyleSheet(f"background-color: {color.name()};")
            elif color_type == 'trail':
                self.trail_color_btn.setStyleSheet(f"background-color: {color.name()};")
            
            # Emit signal
            if self.color_changed:
                self.color_changed.emit({
                    'type': color_type,
                    'color': (color.red(), color.green(), color.blue())
                })
    
    def on_trail_changed(self):
        """Handle trail setting change."""
        trail_type = self.trail_combo.currentText()
        trail_length = self.trail_slider.value()
        
        if self.trail_changed:
            self.trail_changed.emit(trail_type, {
                'length': trail_length,
                'color': self.current_color
            })
    
    def apply_customization(self):
        """Apply current customization settings."""
        # Update panda appearance
        if hasattr(self.panda_widget, 'update_appearance'):
            self.panda_widget.update_appearance()
    
    def reset_customization(self):
        """Reset to default customization."""
        self.current_color = QColor(255, 255, 255)
        self.trail_combo.setCurrentIndex(0)
        self.trail_slider.setValue(10)
        
        # Reset button colors
        self.body_color_btn.setStyleSheet("")
        self.eye_color_btn.setStyleSheet("")
        self.trail_color_btn.setStyleSheet("")
    
    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager:
            tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tooltip:
                widget.setToolTip(tooltip)
