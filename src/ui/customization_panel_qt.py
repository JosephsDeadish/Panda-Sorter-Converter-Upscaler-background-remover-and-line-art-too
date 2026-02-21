"""
Qt implementation of the customization panel.
Pure PyQt6 UI for texture customization options.
"""
from __future__ import annotations
import logging

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                  QLabel, QSlider, QComboBox, QColorDialog, QGroupBox,
                                  QMessageBox, QScrollArea)
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    class _SignalStub:
        def connect(self, *a, **kw): pass
        def emit(self, *a, **kw): pass
    class QWidget:  # type: ignore[no-redef]
        def __init__(self, *a, **kw): pass
    def pyqtSignal(*args, **kwargs):  # type: ignore[no-redef]
        return _SignalStub()

logger = logging.getLogger(__name__)

# Attempt to import TrailPreviewWidget for the live preview strip
try:
    from ui.trail_preview_qt import TrailPreviewWidget as _TrailPreviewWidget
    _TRAIL_PREVIEW_AVAILABLE = True
except Exception:
    _TrailPreviewWidget = None  # type: ignore[assignment,misc]
    _TRAIL_PREVIEW_AVAILABLE = False

# Attempt to import ColorPickerWidget for the advanced color picker
try:
    from ui.color_picker_qt import ColorPickerWidget as _ColorPickerWidget
    _COLOR_PICKER_AVAILABLE = True
except Exception:
    _ColorPickerWidget = None  # type: ignore[assignment,misc]
    _COLOR_PICKER_AVAILABLE = False


class CustomizationPanelQt(QWidget):
    """Qt-based customization panel for panda appearance."""

    # Signals — always class-level pyqtSignal calls; stubs work the same way
    color_changed = pyqtSignal(object)
    trail_changed = pyqtSignal(str, object)
    
    def __init__(self, panda_character, panda_widget, parent=None, tooltip_manager=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for CustomizationPanelQt")

        super().__init__(parent)
        self.panda_character = panda_character
        self.panda_widget = panda_widget
        self.current_color = QColor(255, 255, 255)
        self.tooltip_manager = tooltip_manager
        self._trail_preview: _TrailPreviewWidget | None = None

        self.setup_ui()
    
    def setup_ui(self):
        """Create the UI layout."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

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

        # Advanced color picker (if available)
        if _COLOR_PICKER_AVAILABLE and _ColorPickerWidget is not None:
            self._color_picker = _ColorPickerWidget()
            self._color_picker.color_changed.connect(
                lambda c: self.choose_color('body_advanced', c)
            )
            color_layout.addWidget(self._color_picker)
        else:
            self._color_picker = None

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

        # Animated trail preview
        if _TRAIL_PREVIEW_AVAILABLE and _TrailPreviewWidget is not None:
            try:
                self._trail_preview = _TrailPreviewWidget()
                self._trail_preview.setFixedHeight(120)
                trail_layout.addWidget(QLabel("Preview:"))
                trail_layout.addWidget(self._trail_preview)
            except Exception as _e:
                logger.debug("Trail preview widget could not be created: %s", _e)
                self._trail_preview = None

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
    
    def choose_color(self, color_type, preset_color=None):
        """Open color picker dialog or accept a pre-chosen color."""
        if preset_color is not None:
            color = preset_color
        else:
            color = QColorDialog.getColor(self.current_color, self, f"Choose {color_type} color")

        if not (isinstance(color, QColor) and color.isValid()):
            return

        self.current_color = color

        # Update button color
        if color_type in ('body', 'body_advanced'):
            self.body_color_btn.setStyleSheet(f"background-color: {color.name()};")
        elif color_type == 'eyes':
            self.eye_color_btn.setStyleSheet(f"background-color: {color.name()};")
        elif color_type == 'trail':
            self.trail_color_btn.setStyleSheet(f"background-color: {color.name()};")
            if self._trail_preview is not None:
                self._trail_preview.set_trail_color(color)

        # Emit signal
        self.color_changed.emit({
            'type': color_type,
            'color': (color.red(), color.green(), color.blue())
        })
    
    def on_trail_changed(self):
        """Handle trail setting change."""
        trail_type = self.trail_combo.currentText()
        trail_length = self.trail_slider.value()

        # Update live preview
        if self._trail_preview is not None:
            if trail_type == "None":
                self._trail_preview.view.stop_animation()
            else:
                self._trail_preview.set_trail_length(trail_length)
                self._trail_preview.set_trail_color(self.current_color)
                self._trail_preview.view.start_animation()

        self.trail_changed.emit(trail_type, {
            'length': trail_length,
            'color': self.current_color
        })
    
    def apply_customization(self):
        """Apply current customization settings."""
        try:
            # Update panda appearance
            if self.panda_widget and hasattr(self.panda_widget, 'update_appearance'):
                self.panda_widget.update_appearance()
            
            # Save customization to config
            if hasattr(self, 'config') and self.config:
                if 'customization' not in self.config:
                    self.config['customization'] = {}
                
                self.config['customization'].update({
                    'body_color': self.current_color.getRgb()[:3] if hasattr(self, 'current_color') else (255, 255, 255),
                    'trail_type': self.trail_combo.currentText() if hasattr(self, 'trail_combo') else 'None',
                    'trail_length': self.trail_slider.value() if hasattr(self, 'trail_slider') else 10,
                })
            
            # Visual feedback - customization applied
            logger.info("Customization settings applied and saved")
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying customization: {e}", exc_info=True)
            
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to apply customization:\n{str(e)}"
            )
            return False
    
    def reset_customization(self):
        """Reset to default customization."""
        self.current_color = QColor(255, 255, 255)
        self.trail_combo.setCurrentIndex(0)
        self.trail_slider.setValue(10)

        # Reset button colors
        self.body_color_btn.setStyleSheet("")
        self.eye_color_btn.setStyleSheet("")
        self.trail_color_btn.setStyleSheet("")

        # Stop trail preview animation
        if self._trail_preview is not None:
            self._trail_preview.view.stop_animation()
    
    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager:
            tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tooltip:
                widget.setToolTip(tooltip)
