"""
Integration Example: Interactive Panda Demo

This example demonstrates how to integrate the interactive panda overlay system
into a PyQt6 application.

Features demonstrated:
- Transparent overlay creation
- Widget detection
- AI behavior system
- Programmatic widget interaction
- Visual effects
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QSlider, QLabel, QCheckBox, QComboBox, QTabWidget
    )
    from PyQt6.QtCore import Qt, QTimer
    PYQT_AVAILABLE = True
except ImportError:
    print("PyQt6 not available. Install with: pip install PyQt6")
    PYQT_AVAILABLE = False
    sys.exit(1)

from src.ui.transparent_panda_overlay import TransparentPandaOverlay
from src.features.widget_detector import WidgetDetector
from src.features.panda_interaction_behavior import PandaInteractionBehavior


class InteractivePandaDemo(QMainWindow):
    """
    Demo application showing interactive panda overlay.
    
    This creates a simple UI with various widgets and overlays an interactive
    panda that can detect and interact with them.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Panda Demo")
        self.resize(1024, 768)
        
        # Create main UI
        self._create_ui()
        
        # Create transparent overlay
        self.overlay = TransparentPandaOverlay(self)
        self.overlay.resize(self.size())
        self.overlay.show()
        self.overlay.raise_()  # Always on top
        
        # Setup widget detection
        self.detector = WidgetDetector(self)
        
        # Setup interaction AI
        self.behavior = PandaInteractionBehavior(
            self.overlay,
            self.detector
        )
        
        # Configure personality
        self.behavior.set_mischievousness(0.8)  # Very mischievous
        self.behavior.set_playfulness(0.9)      # Very playful
        
        # Update timer (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_panda)
        self.timer.start(16)  # ~60 FPS
        
        # Status label update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(100)  # 10 times per second
    
    def _create_ui(self):
        """Create the main UI with various widgets."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Interactive Panda Demo")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Watch the panda! It will autonomously interact with the widgets below.\n"
            "The panda can bite buttons, tap sliders, and more!"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(QLabel("Tab 1 Content"), "Tab 1")
        tabs.addTab(QLabel("Tab 2 Content"), "Tab 2")
        tabs.addTab(QLabel("Tab 3 Content"), "Tab 3")
        layout.addWidget(tabs)
        
        # Buttons section
        btn_layout = QHBoxLayout()
        self.button1 = QPushButton("Click Me!")
        self.button1.clicked.connect(lambda: self._on_button_click(1))
        btn_layout.addWidget(self.button1)
        
        self.button2 = QPushButton("Press Me!")
        self.button2.clicked.connect(lambda: self._on_button_click(2))
        btn_layout.addWidget(self.button2)
        
        self.button3 = QPushButton("Push Me!")
        self.button3.clicked.connect(lambda: self._on_button_click(3))
        btn_layout.addWidget(self.button3)
        
        layout.addLayout(btn_layout)
        
        # Slider section
        slider_label = QLabel("Slider Value: 50")
        self.slider_label = slider_label
        layout.addWidget(slider_label)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(50)
        slider.valueChanged.connect(self._on_slider_change)
        layout.addWidget(slider)
        
        # Checkbox
        checkbox = QCheckBox("Enable Feature")
        checkbox.stateChanged.connect(self._on_checkbox_change)
        layout.addWidget(checkbox)
        
        # Combobox
        combobox = QComboBox()
        combobox.addItems(["Option 1", "Option 2", "Option 3", "Option 4"])
        combobox.currentTextChanged.connect(self._on_combobox_change)
        layout.addWidget(combobox)
        
        # Status label
        self.status_label = QLabel("Status: Waiting for panda...")
        self.status_label.setStyleSheet(
            "padding: 10px; background-color: #f0f0f0; border-radius: 5px;"
        )
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def _update_panda(self):
        """Update panda AI behavior every frame."""
        # Update behavior AI
        self.behavior.update(0.016)
        
        # Detect widget under panda
        head_pos = self.overlay.get_head_position()
        if head_pos:
            widget = self.detector.get_widget_at_position(
                head_pos.x(),
                head_pos.y()
            )
            
            # Update overlay with widget below (for shadows)
            self.overlay.set_widget_below(widget)
    
    def _update_status(self):
        """Update status label with panda information."""
        behavior = self.behavior.current_behavior
        if behavior:
            status = f"Panda is: {behavior.value.replace('_', ' ').title()}"
            if self.behavior.target_widget:
                widget_type = self.behavior.target_widget.__class__.__name__
                status += f" on {widget_type}"
        else:
            cooldown = self.behavior.interaction_cooldown
            if cooldown > 0:
                status = f"Panda cooldown: {cooldown:.1f}s"
            else:
                status = "Panda is looking for something to interact with..."
        
        self.status_label.setText(f"Status: {status}")
    
    def _on_button_click(self, button_num):
        """Handle button clicks."""
        print(f"Button {button_num} was clicked!")
        self.status_label.setText(f"Status: Button {button_num} clicked!")
    
    def _on_slider_change(self, value):
        """Handle slider value changes."""
        self.slider_label.setText(f"Slider Value: {value}")
        print(f"Slider changed to: {value}")
    
    def _on_checkbox_change(self, state):
        """Handle checkbox state changes."""
        checked = state == Qt.CheckState.Checked.value
        print(f"Checkbox changed to: {'checked' if checked else 'unchecked'}")
    
    def _on_combobox_change(self, text):
        """Handle combobox selection changes."""
        print(f"Combobox changed to: {text}")
    
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        
        # Keep overlay full-window
        if hasattr(self, 'overlay'):
            self.overlay.resize(self.size())
        
        # Invalidate widget detector cache
        if hasattr(self, 'detector'):
            self.detector.invalidate_cache()


def main():
    """Run the demo application."""
    if not PYQT_AVAILABLE:
        print("PyQt6 is required to run this demo.")
        print("Install with: pip install PyQt6 PyOpenGL PyOpenGL-accelerate")
        return 1
    
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo window
    window = InteractivePandaDemo()
    window.show()
    
    print("=" * 60)
    print("INTERACTIVE PANDA DEMO RUNNING")
    print("=" * 60)
    print("Watch the panda interact with the widgets!")
    print("The panda will:")
    print("  - Bite buttons to click them")
    print("  - Jump on buttons")
    print("  - Tap sliders to change values")
    print("  - Bite tabs to switch them")
    print("  - Push checkboxes")
    print("  - Spin comboboxes")
    print()
    print("Close the window to exit.")
    print("=" * 60)
    
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
