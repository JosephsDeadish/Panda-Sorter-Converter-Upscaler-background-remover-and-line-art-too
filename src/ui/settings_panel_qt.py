"""
Settings Panel - Comprehensive UI for application configuration
Provides tabs for Appearance, Cursor, Font, Behavior, Performance, and Advanced settings
Author: Dead On The Inside / JosephsDeadish
"""


from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
        QPushButton, QSlider, QComboBox, QSpinBox, QCheckBox,
        QGroupBox, QScrollArea, QLineEdit, QColorDialog, QMessageBox,
        QFileDialog, QFormLayout, QProgressBar
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QColor, QPainter, QPen
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    class QWidget:  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class _SignalStub:  # noqa: E301
        """Stub signal — active only when PyQt6 is absent."""
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SignalStub()  # noqa: E301

# Attempt to import TrailPreviewWidget for the cursor trail live preview
try:
    from ui.trail_preview_qt import TrailPreviewWidget as _CursorTrailPreviewWidget
    _CURSOR_TRAIL_PREVIEW_AVAILABLE = True
except Exception:
    _CursorTrailPreviewWidget = None  # type: ignore[assignment,misc]
    _CURSOR_TRAIL_PREVIEW_AVAILABLE = False


class ColorWheelWidget(QWidget):
    """Custom color picker widget for accent color selection"""
    colorChanged = pyqtSignal(str)  # Emits hex color string
    
    def __init__(self, initial_color="#0d7377", parent=None):
        super().__init__(parent)
        self.current_color = QColor(initial_color)
        self.setMinimumSize(100, 40)
        self.setMaximumHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def paintEvent(self, event):
        """Draw the color preview"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw color rectangle
        painter.fillRect(self.rect(), self.current_color)
        
        # Draw border
        pen = QPen(QColor("#ffffff" if self.current_color.lightness() < 128 else "#000000"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        
    def mousePressEvent(self, event):
        """Open color picker on click"""
        color = QColorDialog.getColor(self.current_color, self, "Select Accent Color")
        if color.isValid():
            self.current_color = color
            self.update()
            self.colorChanged.emit(color.name())


class SettingsPanelQt(QWidget):
    """
    Comprehensive settings panel with multiple tabs for all configuration options.
    Includes:
    - Appearance (theme, colors, opacity)
    - Cursor (type, size, trail effects)
    - Font (family, size, weight, icon size)
    - Behavior (animation speed, tooltips, sound)
    - Performance (threads, memory, cache)
    - Advanced (debug, import/export)
    """
    
    settingsChanged = pyqtSignal(str, object)  # Signal for real-time updates
    
    def __init__(self, config, main_window=None, tooltip_manager=None, parent=None):
        super().__init__(parent)
        
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for SettingsPanelQt")
        
        self.config = config
        self.main_window = main_window
        self.tooltip_manager = tooltip_manager
        self._updating = False  # Prevent recursive updates
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the main UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("⚙️ Settings & Preferences")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs — Cursor and Font have their own full tabs (plus summary sub-sections in Appearance)
        self.tabs.addTab(self.create_appearance_tab(), "🎨 Appearance")
        self.tabs.addTab(self.create_cursor_tab(), "🖱️ Cursor")
        self.tabs.addTab(self.create_font_tab(), "🔤 Font")
        self.tabs.addTab(self.create_behavior_tab(), "⚡ Behavior")
        self.tabs.addTab(self.create_performance_tab(), "🚀 Performance")
        self.tabs.addTab(self.create_ai_settings_tab(), "🤖 AI Settings")
        self.tabs.addTab(self.create_ai_models_tab(), "📦 AI Models")
        self.tabs.addTab(self.create_hotkeys_tab(), "⌨️ Hotkeys")
        self.tabs.addTab(self.create_language_tab(), "🌐 Language")
        self.tabs.addTab(self.create_advanced_tab(), "🔧 Advanced")
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        self.set_tooltip(reset_btn, 'reset_button')
        button_layout.addWidget(reset_btn)
        
        export_btn = QPushButton("Export Settings")
        export_btn.clicked.connect(self.export_settings)
        self.set_tooltip(export_btn, 'export_button')
        button_layout.addWidget(export_btn)
        
        import_btn = QPushButton("Import Settings")
        import_btn.clicked.connect(self.import_settings)
        self.set_tooltip(import_btn, 'import_button')
        button_layout.addWidget(import_btn)
        
        layout.addLayout(button_layout)
    
    def create_appearance_tab(self):
        """Create appearance settings tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Theme section
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        
        theme_label = QLabel("Theme Mode:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "Dark", "Light", "Nord", "Dracula", "Solarized Dark",
            "Forest", "Ocean", "Sunset", "Cyberpunk", "Gore", "Goth",
        ])
        self.theme_combo.currentTextChanged.connect(lambda: self.on_setting_changed('ui', 'theme'))
        self.set_tooltip(self.theme_combo, 'theme_selector')
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Color section
        color_group = QGroupBox("Colors")
        color_layout = QVBoxLayout()
        
        accent_label = QLabel("Accent Color:")
        self.accent_color_widget = ColorWheelWidget()
        self.accent_color_widget.colorChanged.connect(lambda c: self.on_color_changed('accent_color', c))
        self.set_tooltip(self.accent_color_widget, 'accent_color')
        
        color_layout.addWidget(accent_label)
        color_layout.addWidget(self.accent_color_widget)
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # Window section
        window_group = QGroupBox("Window")
        window_layout = QVBoxLayout()
        
        # Opacity slider
        opacity_label = QLabel("Window Opacity: 100%")
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(50)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.valueChanged.connect(lambda v: self.on_opacity_changed(opacity_label, v))
        self.set_tooltip(self.opacity_slider, 'opacity_slider')
        
        window_layout.addWidget(opacity_label)
        window_layout.addWidget(self.opacity_slider)
        
        # Compact view
        self.compact_view_check = QCheckBox("Compact View")
        self.compact_view_check.stateChanged.connect(lambda: self.on_setting_changed('ui', 'compact_view'))
        self.set_tooltip(self.compact_view_check, 'compact_view')
        window_layout.addWidget(self.compact_view_check)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)

        # ── Font sub-section ─────────────────────────────────────────────────
        font_group = QGroupBox("Font")
        font_layout = QVBoxLayout()

        font_family_label = QLabel("Font Family:")
        self.appearance_font_combo = QComboBox()
        self.appearance_font_combo.addItems(["Segoe UI", "Arial", "Helvetica", "Calibri", "Roboto", "Consolas", "Courier New"])
        self.appearance_font_combo.currentTextChanged.connect(lambda: self.on_setting_changed('ui', 'font_family'))
        font_layout.addWidget(font_family_label)
        font_layout.addWidget(self.appearance_font_combo)

        font_size_label = QLabel("Font Size:")
        self.appearance_font_size = QSpinBox()
        self.appearance_font_size.setRange(8, 24)
        self.appearance_font_size.setValue(12)
        self.appearance_font_size.valueChanged.connect(lambda: self.on_setting_changed('ui', 'font_size'))
        font_layout.addWidget(font_size_label)
        font_layout.addWidget(self.appearance_font_size)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # ── Cursor sub-section ───────────────────────────────────────────────
        cursor_group = QGroupBox("Cursor")
        cursor_layout = QVBoxLayout()

        cursor_label = QLabel("Cursor Style:")
        self.appearance_cursor_combo = QComboBox()
        self.appearance_cursor_combo.addItems(["Default", "Pointer", "Crosshair", "Panda Paw", "Bamboo", "Star"])
        self.appearance_cursor_combo.currentTextChanged.connect(lambda: self.on_setting_changed('ui', 'cursor'))
        cursor_layout.addWidget(cursor_label)
        cursor_layout.addWidget(self.appearance_cursor_combo)

        cursor_group.setLayout(cursor_layout)
        layout.addWidget(cursor_group)

        layout.addStretch()
        scroll.setWidget(container)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        return tab
    
    def create_cursor_tab(self):
        """Create cursor settings tab with basic and unlockable cursors"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Cursor type
        type_group = QGroupBox("Cursor Style")
        type_layout = QVBoxLayout()
        
        type_label = QLabel("Cursor Type:")
        self.cursor_type_combo = QComboBox()
        
        # Basic cursors (always available)
        basic_cursors = [
            "Default",
            "Arrow",
            "Hand",
            "Cross",
            "Wait",
            "Text",
            "Forbidden",
            "Move",
            "Zoom In",
            "Zoom Out",
        ]
        
        # Unlockable cursors (check achievements/purchases)
        unlockable_cursors = [
            ("Skull ⚠️", "cursor_collector"),
            ("Panda 🐼", "panda_lover"),
            ("Sword ⚔️", "cursor_collector"),
            ("Wand 🪄", "cursor_collector"),
            ("Heart ❤️", "cursor_collector"),
            ("Star ⭐", "cursor_collector"),
            ("Diamond 💎", "cursor_master"),
            ("Crown 👑", "master"),
            ("Fire 🔥", "cursor_collector"),
            ("Ice ❄️", "nordic_explorer"),
            ("Rainbow 🌈", "cursor_collector"),
            ("Galaxy 🌌", "cursor_master"),
        ]
        
        # Retrieve unlocked cursors from config (stored after achievement unlock)
        unlocked_cursor_ids = set(filter(None, self.config.get('ui', 'unlocked_cursors', default='').split(',')))
        
        # Add basic cursors
        self.cursor_type_combo.addItems(basic_cursors)
        
        # Add separator
        self.cursor_type_combo.insertSeparator(len(basic_cursors))
        
        # Add unlockable cursors - show unlocked state from config
        for cursor_name, required_achievement in unlockable_cursors:
            cursor_key = (cursor_name.split()[0] if ' ' in cursor_name else cursor_name).lower()
            if cursor_key in unlocked_cursor_ids or required_achievement in unlocked_cursor_ids:
                self.cursor_type_combo.addItem(cursor_name)
            else:
                self.cursor_type_combo.addItem(f"🔒 {cursor_name}")
        
        self.cursor_type_combo.currentTextChanged.connect(lambda: self.on_setting_changed('ui', 'cursor'))
        self.set_tooltip(self.cursor_type_combo, 'cursor_selector')
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.cursor_type_combo)
        
        # Add unlock hint
        unlock_hint = QLabel("💡 Unlock more cursors through achievements and the shop!")
        unlock_hint.setStyleSheet("color: gray; font-style: italic; font-size: 9pt;")
        unlock_hint.setWordWrap(True)
        type_layout.addWidget(unlock_hint)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Cursor size
        size_group = QGroupBox("Cursor Size")
        size_layout = QVBoxLayout()
        
        size_label = QLabel("Size:")
        self.cursor_size_combo = QComboBox()
        self.cursor_size_combo.addItems(["Small", "Medium", "Large", "Extra Large"])
        self.cursor_size_combo.currentTextChanged.connect(lambda: self.on_setting_changed('ui', 'cursor_size'))
        self.set_tooltip(self.cursor_size_combo, 'cursor_size')
        
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.cursor_size_combo)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # Mouse cursor trail (separate from panda trail!)
        trail_group = QGroupBox("Mouse Cursor Trail")
        trail_layout = QVBoxLayout()
        
        trail_info = QLabel("Note: This is the mouse cursor trail, not the panda movement trail.\nPanda trail is in: Panda Features → Customization")
        trail_info.setStyleSheet("color: #666; font-size: 9pt; font-style: italic;")
        trail_info.setWordWrap(True)
        trail_layout.addWidget(trail_info)
        
        self.cursor_trail_check = QCheckBox("Enable Mouse Cursor Trail")
        self.cursor_trail_check.stateChanged.connect(lambda: self.on_setting_changed('ui', 'cursor_trail'))
        self.set_tooltip(self.cursor_trail_check, 'cursor_trail')
        trail_layout.addWidget(self.cursor_trail_check)
        
        trail_color_label = QLabel("Trail Effect:")
        self.cursor_trail_color_combo = QComboBox()
        self.cursor_trail_color_combo.addItems([
            "Rainbow",
            "Fire",
            "Ice",
            "Nature",
            "Galaxy",
            "Gold",
            "Silver",
            "Neon",
            "Sparkles"
        ])
        self.cursor_trail_color_combo.currentTextChanged.connect(lambda: self.on_setting_changed('ui', 'cursor_trail_color'))
        self.set_tooltip(self.cursor_trail_color_combo, 'cursor_trail_color')
        
        trail_layout.addWidget(trail_color_label)
        trail_layout.addWidget(self.cursor_trail_color_combo)
        
        # Trail intensity
        intensity_label = QLabel("Trail Intensity:")
        self.cursor_trail_intensity = QSlider(Qt.Orientation.Horizontal)
        self.cursor_trail_intensity.setMinimum(1)
        self.cursor_trail_intensity.setMaximum(10)
        self.cursor_trail_intensity.setValue(5)
        self.cursor_trail_intensity.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.cursor_trail_intensity.setTickInterval(1)
        self.cursor_trail_intensity.valueChanged.connect(lambda: self.on_setting_changed('ui', 'cursor_trail_intensity'))
        
        trail_layout.addWidget(intensity_label)
        trail_layout.addWidget(self.cursor_trail_intensity)
        self.set_tooltip(self.cursor_trail_intensity, 'cursor_trail_intensity')

        # Live cursor trail preview
        if _CURSOR_TRAIL_PREVIEW_AVAILABLE and _CursorTrailPreviewWidget is not None:
            try:
                self._cursor_trail_preview = _CursorTrailPreviewWidget()
                self._cursor_trail_preview.setFixedHeight(120)
                trail_layout.addWidget(QLabel("Preview (move mouse over to test):"))
                trail_layout.addWidget(self._cursor_trail_preview)
            except Exception as _pe:
                logger.debug("Cursor trail preview could not be created: %s", _pe)
                self._cursor_trail_preview = None
        else:
            self._cursor_trail_preview = None
        
        trail_group.setLayout(trail_layout)
        layout.addWidget(trail_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        return tab
    
    def create_font_tab(self):
        """Create font settings tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Font family
        family_group = QGroupBox("Font Family")
        family_layout = QVBoxLayout()
        
        family_label = QLabel("Font:")
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Segoe UI", "Arial", "Helvetica", "Times New Roman",
            "Courier New", "Comic Sans MS", "Verdana", "Georgia"
        ])
        self.font_family_combo.currentTextChanged.connect(lambda: self.on_setting_changed('ui', 'font_family'))
        self.set_tooltip(self.font_family_combo, 'font_family')
        
        family_layout.addWidget(family_label)
        family_layout.addWidget(self.font_family_combo)
        family_group.setLayout(family_layout)
        layout.addWidget(family_group)
        
        # Font size
        size_group = QGroupBox("Font Size")
        size_layout = QVBoxLayout()
        
        size_label = QLabel("Size (pt):")
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(20)
        self.font_size_spin.setValue(12)
        self.font_size_spin.valueChanged.connect(lambda: self.on_setting_changed('ui', 'font_size'))
        self.set_tooltip(self.font_size_spin, 'font_size')
        
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.font_size_spin)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # Font weight
        weight_group = QGroupBox("Font Weight")
        weight_layout = QVBoxLayout()
        
        weight_label = QLabel("Weight:")
        self.font_weight_combo = QComboBox()
        self.font_weight_combo.addItems(["Light", "Normal", "Bold"])
        self.font_weight_combo.currentTextChanged.connect(lambda: self.on_setting_changed('ui', 'font_weight'))
        self.set_tooltip(self.font_weight_combo, 'font_weight')
        
        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self.font_weight_combo)
        weight_group.setLayout(weight_layout)
        layout.addWidget(weight_group)
        
        # Icon size
        icon_group = QGroupBox("Icon Size")
        icon_layout = QVBoxLayout()
        
        icon_label = QLabel("Size:")
        self.icon_size_combo = QComboBox()
        self.icon_size_combo.addItems(["Small", "Medium", "Large"])
        self.icon_size_combo.currentTextChanged.connect(lambda: self.on_setting_changed('ui', 'icon_size'))
        self.set_tooltip(self.icon_size_combo, 'icon_size')
        
        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(self.icon_size_combo)
        icon_group.setLayout(icon_layout)
        layout.addWidget(icon_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        return tab
    
    def create_behavior_tab(self):
        """Create behavior settings tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Animation speed
        anim_group = QGroupBox("Animation")
        anim_layout = QVBoxLayout()
        
        anim_label = QLabel("Animation Speed: 1.0x")
        self.animation_slider = QSlider(Qt.Orientation.Horizontal)
        self.animation_slider.setMinimum(5)  # 0.5x
        self.animation_slider.setMaximum(20)  # 2.0x
        self.animation_slider.setValue(10)  # 1.0x
        self.animation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.animation_slider.setTickInterval(5)
        self.animation_slider.valueChanged.connect(lambda v: self.on_animation_speed_changed(anim_label, v))
        self.set_tooltip(self.animation_slider, 'animation_speed')
        
        anim_layout.addWidget(anim_label)
        anim_layout.addWidget(self.animation_slider)
        anim_group.setLayout(anim_layout)
        layout.addWidget(anim_group)
        
        # Tooltip settings
        tooltip_group = QGroupBox("Tooltips")
        tooltip_layout = QVBoxLayout()
        
        self.tooltip_enabled_check = QCheckBox("Enable Tooltips")
        self.tooltip_enabled_check.stateChanged.connect(lambda: self.on_setting_changed('ui', 'tooltip_enabled'))
        self.set_tooltip(self.tooltip_enabled_check, 'tooltip_enabled')
        tooltip_layout.addWidget(self.tooltip_enabled_check)
        
        mode_label = QLabel("Tooltip Style Mode:")
        self.tooltip_mode_combo = QComboBox()
        self.tooltip_mode_combo.addItems([
            "Normal - Standard Helpful Tips",
            "Beginner - Detailed Explanations",
            "Profane - Hilariously Vulgar (But Still Helpful!)"
        ])
        self.tooltip_mode_combo.currentIndexChanged.connect(lambda: self.on_tooltip_mode_changed())
        self.set_tooltip(self.tooltip_mode_combo, 'tooltip_mode')
        
        # Add description label
        mode_desc = QLabel(
            "💡 Tooltip modes change the style of helpful hints:\n"
            "• Normal: Standard concise tips\n"
            "• Beginner: Detailed step-by-step explanations\n"
            "• Profane: Extremely profane and hilarious, but still helpful!"
        )
        mode_desc.setStyleSheet("color: gray; font-size: 9pt; font-style: italic;")
        mode_desc.setWordWrap(True)
        
        tooltip_layout.addWidget(mode_label)
        tooltip_layout.addWidget(self.tooltip_mode_combo)
        tooltip_layout.addWidget(mode_desc)
        
        delay_label = QLabel("Tooltip Delay: 0.5s")
        self.tooltip_delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.tooltip_delay_slider.setMinimum(0)
        self.tooltip_delay_slider.setMaximum(20)  # 0-2.0 seconds
        self.tooltip_delay_slider.setValue(5)  # 0.5s
        self.tooltip_delay_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.tooltip_delay_slider.setTickInterval(5)
        self.tooltip_delay_slider.valueChanged.connect(lambda v: self.on_tooltip_delay_changed(delay_label, v))
        self.set_tooltip(self.tooltip_delay_slider, 'tooltip_delay')
        
        tooltip_layout.addWidget(delay_label)
        tooltip_layout.addWidget(self.tooltip_delay_slider)
        tooltip_group.setLayout(tooltip_layout)
        layout.addWidget(tooltip_group)
        
        # Sound settings
        sound_group = QGroupBox("Sound")
        sound_layout = QVBoxLayout()
        
        self.sound_enabled_check = QCheckBox("Enable Sound Effects")
        self.sound_enabled_check.stateChanged.connect(lambda: self.on_setting_changed('ui', 'sound_enabled'))
        self.set_tooltip(self.sound_enabled_check, 'sound_enabled')
        sound_layout.addWidget(self.sound_enabled_check)
        
        volume_label = QLabel("Volume: 70%")
        self.sound_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.sound_volume_slider.setMinimum(0)
        self.sound_volume_slider.setMaximum(100)
        self.sound_volume_slider.setValue(70)
        self.sound_volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sound_volume_slider.setTickInterval(10)
        self.sound_volume_slider.valueChanged.connect(lambda v: self.on_volume_changed(volume_label, v))
        self.set_tooltip(self.sound_volume_slider, 'sound_volume')
        
        sound_layout.addWidget(volume_label)
        sound_layout.addWidget(self.sound_volume_slider)
        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        return tab
    
    def create_performance_tab(self):
        """Create performance settings tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Thread count
        thread_group = QGroupBox("Threading")
        thread_layout = QVBoxLayout()
        
        thread_label = QLabel("Thread Count:")
        self.thread_spin = QSpinBox()
        self.thread_spin.setMinimum(1)
        self.thread_spin.setMaximum(16)
        self.thread_spin.setValue(4)
        self.thread_spin.valueChanged.connect(lambda: self.on_setting_changed('performance', 'max_threads'))
        self.set_tooltip(self.thread_spin, 'thread_count')
        
        thread_layout.addWidget(thread_label)
        thread_layout.addWidget(self.thread_spin)
        thread_group.setLayout(thread_layout)
        layout.addWidget(thread_group)
        
        # Memory limit
        memory_group = QGroupBox("Memory")
        memory_layout = QVBoxLayout()
        
        memory_label = QLabel("Memory Limit (MB):")
        self.memory_spin = QSpinBox()
        self.memory_spin.setMinimum(512)
        self.memory_spin.setMaximum(8192)
        self.memory_spin.setSingleStep(256)
        self.memory_spin.setValue(2048)
        self.memory_spin.valueChanged.connect(lambda: self.on_setting_changed('performance', 'memory_limit_mb'))
        self.set_tooltip(self.memory_spin, 'memory_limit')
        
        memory_layout.addWidget(memory_label)
        memory_layout.addWidget(self.memory_spin)
        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)
        
        # Cache size
        cache_group = QGroupBox("Cache")
        cache_layout = QVBoxLayout()
        
        cache_label = QLabel("Cache Size (MB):")
        self.cache_spin = QSpinBox()
        self.cache_spin.setMinimum(128)
        self.cache_spin.setMaximum(2048)
        self.cache_spin.setSingleStep(128)
        self.cache_spin.setValue(512)
        self.cache_spin.valueChanged.connect(lambda: self.on_setting_changed('performance', 'cache_size_mb'))
        self.set_tooltip(self.cache_spin, 'cache_size')
        
        cache_layout.addWidget(cache_label)
        cache_layout.addWidget(self.cache_spin)
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # Thumbnail quality
        quality_group = QGroupBox("Thumbnails")
        quality_layout = QVBoxLayout()
        
        quality_label = QLabel("Thumbnail Quality:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Low", "Medium", "High"])
        self.quality_combo.currentTextChanged.connect(lambda: self.on_setting_changed('performance', 'thumbnail_quality'))
        self.set_tooltip(self.quality_combo, 'thumbnail_quality')
        
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        return tab
    
    def create_ai_settings_tab(self):
        """Create AI training + inference settings tab (separate from model downloads)."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)

        # ── Training section ──────────────────────────────────────────────
        train_group = QGroupBox("🏋️ Training Settings")
        train_layout = QFormLayout()

        # Training mode
        self.training_mode_combo = QComboBox()
        self.training_mode_combo.addItems([
            "Standard", "Fine-Tune Existing", "Incremental (Continual)",
            "Export to ONNX", "Export to PyTorch", "Custom Dataset",
        ])
        self.training_mode_combo.currentTextChanged.connect(
            lambda: self.on_setting_changed('ai', 'training_mode'))
        train_layout.addRow("Training Mode:", self.training_mode_combo)

        # Epochs
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 1000)
        self.epochs_spin.setValue(50)
        self.epochs_spin.valueChanged.connect(
            lambda: self.on_setting_changed('ai', 'epochs'))
        train_layout.addRow("Epochs:", self.epochs_spin)

        # Batch size
        self.batch_size_combo = QComboBox()
        self.batch_size_combo.addItems(["4", "8", "16", "32", "64", "128"])
        self.batch_size_combo.setCurrentText("16")
        self.batch_size_combo.currentTextChanged.connect(
            lambda: self.on_setting_changed('ai', 'batch_size'))
        train_layout.addRow("Batch Size:", self.batch_size_combo)

        # Learning rate
        self.lr_combo = QComboBox()
        self.lr_combo.addItems(["0.1", "0.01", "0.001", "0.0001", "0.00001"])
        self.lr_combo.setCurrentText("0.0001")
        self.lr_combo.currentTextChanged.connect(
            lambda: self.on_setting_changed('ai', 'learning_rate'))
        train_layout.addRow("Learning Rate:", self.lr_combo)

        # Device
        self.device_combo = QComboBox()
        self.device_combo.addItems(["Auto (GPU if available)", "CPU only", "CUDA GPU", "MPS (Apple)"])
        self.device_combo.currentTextChanged.connect(
            lambda: self.on_setting_changed('ai', 'device'))
        train_layout.addRow("Compute Device:", self.device_combo)

        # Optimizer
        self.optimizer_combo = QComboBox()
        self.optimizer_combo.addItems(["AdamW", "Adam", "SGD", "RMSprop"])
        self.optimizer_combo.currentTextChanged.connect(
            lambda: self.on_setting_changed('ai', 'optimizer'))
        train_layout.addRow("Optimizer:", self.optimizer_combo)

        # Checkpoint
        self.checkpoint_check = QCheckBox("Save checkpoints every N epochs")
        self.checkpoint_check.setChecked(True)
        self.checkpoint_check.stateChanged.connect(
            lambda: self.on_setting_changed('ai', 'save_checkpoints'))
        self.checkpoint_every_spin = QSpinBox()
        self.checkpoint_every_spin.setRange(1, 100)
        self.checkpoint_every_spin.setValue(10)
        self.checkpoint_every_spin.valueChanged.connect(
            lambda: self.on_setting_changed('ai', 'checkpoint_interval'))
        train_layout.addRow(self.checkpoint_check, self.checkpoint_every_spin)

        # Custom dataset path (shown when Custom Dataset mode selected)
        self._dataset_path_row_lbl = QLabel("Dataset Folder:")
        self._dataset_path_row = QWidget()
        _ds_row_lay = QHBoxLayout(self._dataset_path_row)
        _ds_row_lay.setContentsMargins(0, 0, 0, 0)
        self.dataset_path_edit = QLineEdit()
        self.dataset_path_edit.setPlaceholderText("Select folder with class sub-folders…")
        self.dataset_path_edit.setReadOnly(True)
        self.dataset_path_edit.textChanged.connect(
            lambda: self.on_setting_changed('ai', 'custom_dataset_path'))
        _ds_browse_btn = QPushButton("📂 Browse")
        _ds_browse_btn.setFixedWidth(90)
        _ds_browse_btn.clicked.connect(self._browse_dataset_folder)
        _ds_row_lay.addWidget(self.dataset_path_edit, 1)
        _ds_row_lay.addWidget(_ds_browse_btn)
        train_layout.addRow(self._dataset_path_row_lbl, self._dataset_path_row)
        # Show only when Custom Dataset mode is active
        self._dataset_path_row_lbl.setVisible(False)
        self._dataset_path_row.setVisible(False)

        def _toggle_dataset_row(mode_text: str):
            visible = 'custom' in mode_text.lower()
            self._dataset_path_row_lbl.setVisible(visible)
            self._dataset_path_row.setVisible(visible)
        self.training_mode_combo.currentTextChanged.connect(_toggle_dataset_row)

        train_group.setLayout(train_layout)
        layout.addWidget(train_group)

        # ── Inference / runtime section ───────────────────────────────────
        infer_group = QGroupBox("⚡ Inference Settings")
        infer_layout = QFormLayout()

        # Inference precision
        self.precision_combo = QComboBox()
        self.precision_combo.addItems(["FP32 (Full)", "FP16 (Half, faster)", "INT8 (Fastest)"])
        self.precision_combo.currentTextChanged.connect(
            lambda: self.on_setting_changed('ai', 'precision'))
        infer_layout.addRow("Precision:", self.precision_combo)

        # Max image size
        self.max_img_spin = QSpinBox()
        self.max_img_spin.setRange(128, 4096)
        self.max_img_spin.setValue(1024)
        self.max_img_spin.setSingleStep(128)
        self.max_img_spin.setSuffix(" px")
        self.max_img_spin.valueChanged.connect(
            lambda: self.on_setting_changed('ai', 'max_image_size'))
        infer_layout.addRow("Max Image Size:", self.max_img_spin)

        # Threading
        self.ai_threads_spin = QSpinBox()
        self.ai_threads_spin.setRange(1, 16)
        self.ai_threads_spin.setValue(4)
        self.ai_threads_spin.valueChanged.connect(
            lambda: self.on_setting_changed('ai', 'threads'))
        infer_layout.addRow("AI Threads:", self.ai_threads_spin)

        # Use GPU for inference
        self.use_gpu_check = QCheckBox("Use GPU for inference (if available)")
        self.use_gpu_check.setChecked(True)
        self.use_gpu_check.stateChanged.connect(
            lambda: self.on_setting_changed('ai', 'use_gpu'))
        infer_layout.addRow("", self.use_gpu_check)

        infer_group.setLayout(infer_layout)
        layout.addWidget(infer_group)

        # ── Export section ────────────────────────────────────────────────
        export_group = QGroupBox("📤 Export Settings")
        export_layout = QFormLayout()

        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["PyTorch (.pt)", "ONNX (.onnx)", "TorchScript (.pts)", "SafeTensors"])
        self.export_format_combo.currentTextChanged.connect(
            lambda: self.on_setting_changed('ai', 'export_format'))
        export_layout.addRow("Export Format:", self.export_format_combo)

        self.quantize_check = QCheckBox("Quantize on export (smaller file, slight quality loss)")
        self.quantize_check.stateChanged.connect(
            lambda: self.on_setting_changed('ai', 'quantize_export'))
        export_layout.addRow("", self.quantize_check)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # ── Start Training button ─────────────────────────────────────────
        train_btn_group = QGroupBox("▶ Run")
        train_btn_layout = QVBoxLayout()
        self._ai_train_status = QLabel("Ready")
        self._ai_train_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ai_train_progress = QProgressBar()
        self._ai_train_progress.setRange(0, 100)
        self._ai_train_progress.setValue(0)
        self._ai_train_progress.setVisible(False)

        start_btn = QPushButton("▶ Start Training / Export")
        start_btn.setStyleSheet(
            "QPushButton { background: #0d7377; color: #fff; border-radius: 4px; "
            "font-weight: bold; padding: 8px 16px; } "
            "QPushButton:hover { background: #0a5e62; }"
        )
        start_btn.clicked.connect(self._on_start_ai_training)

        train_btn_layout.addWidget(self._ai_train_status)
        train_btn_layout.addWidget(self._ai_train_progress)
        train_btn_layout.addWidget(start_btn)
        train_btn_group.setLayout(train_btn_layout)
        layout.addWidget(train_btn_group)

        layout.addStretch()
        scroll.setWidget(container)
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        return tab

    def create_ai_models_tab(self):
        """Create AI models management tab"""
        error_msg = None
        error_type = "general"
        
        try:
            # Three-tier fallback mirrors ai_models_settings_tab._import_model_manager()
            # so the AI models tab works in dev, running from repo root, and frozen EXE.
            _AIModelsSettingsTab = None
            try:
                from .ai_models_settings_tab import AIModelsSettingsTab as _AIModelsSettingsTab  # noqa: PLC0415
            except (ImportError, ValueError):
                pass
            if _AIModelsSettingsTab is None:
                try:
                    from ui.ai_models_settings_tab import AIModelsSettingsTab as _AIModelsSettingsTab  # noqa: PLC0415
                except (ImportError, OSError, RuntimeError):
                    pass
            if _AIModelsSettingsTab is None:
                import sys
                from pathlib import Path
                _src = str(Path(__file__).resolve().parent.parent)  # .../src/
                if _src not in sys.path:
                    sys.path.insert(0, _src)
                from ui.ai_models_settings_tab import AIModelsSettingsTab as _AIModelsSettingsTab  # noqa: PLC0415
            if _AIModelsSettingsTab is None:
                raise ImportError("AIModelsSettingsTab could not be loaded from any path")
            return _AIModelsSettingsTab(self.config)
        except (ImportError, OSError) as e:
            # Specific handling for import errors
            error_msg = str(e)
            if "PyQt6" in error_msg or "QtWidgets" in error_msg:
                error_type = "pyqt6"
            elif "model_manager" in error_msg or "upscaler" in error_msg:
                error_type = "model_manager"
            else:
                error_type = "dependencies"
            logger.warning(f"AI Models settings tab import error ({error_type}): {e}")
        except Exception as e:
            # Other errors
            error_msg = str(e)
            error_type = "general"
            logger.error(f"AI Models settings tab error: {e}", exc_info=True)
        
        # Return a placeholder widget with detailed error info
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addStretch()
        
        # Create error message based on specific error type
        if error_type == "pyqt6":
            error_text = (
                "🤖 AI Models Management\n\n"
                "❌ Missing PyQt6\n\n"
                "💡 Install with:\n"
                "   pip install PyQt6\n\n"
            )
        elif error_type == "model_manager":
            error_text = (
                "🤖 AI Models Management\n\n"
                "❌ Model manager module not available\n\n"
                "This is OK - the AI models tab is optional.\n"
                "The application works fine without it.\n\n"
                "If you want to use AI model management:\n"
                "1. Ensure upscaler/model_manager.py exists\n"
                "2. Install dependencies:\n"
                "   pip install torch transformers\n\n"
            )
        elif error_type == "dependencies":
            error_text = (
                "🤖 AI Models Management\n\n"
                "❌ Missing AI dependencies\n\n"
                "💡 Try installing AI dependencies:\n"
                "   pip install torch transformers\n\n"
                "Or use minimal install:\n"
                "   pip install -r requirements-minimal.txt\n\n"
            )
        else:
            error_text = (
                f"🤖 AI Models Management\n\n"
                f"❌ Error: {error_msg}\n\n"
                "💡 Try installing dependencies:\n"
                "   pip install torch transformers\n\n"
            )
        
        label = QLabel(error_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                padding: 20px;
                background-color: #fff8dc;
                border: 2px solid #f0ad4e;
                border-radius: 8px;
                color: #333;
            }
        """)
        layout.addWidget(label)
        
        # Add helpful button
        install_btn = QPushButton("📖 View Installation Guide")
        install_btn.clicked.connect(self.show_ai_install_guide)
        install_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 4px;
                max-width: 300px;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
        """)
        layout.addWidget(install_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        return widget

    def show_ai_install_guide(self):
        """Show detailed installation guide for AI features"""
        guide = QMessageBox(self)
        guide.setWindowTitle("AI Models Installation Guide")
        guide.setIcon(QMessageBox.Icon.Information)
        guide.setText("📚 How to Enable AI Model Management")
        guide.setInformativeText(
            "The AI Models tab requires optional dependencies.\n\n"
            "**Basic Installation (CPU):**\n"
            "pip install torch transformers\n\n"
            "**GPU Support (NVIDIA):**\n"
            "Visit https://pytorch.org/ for CUDA versions\n\n"
            "**Minimal Installation (No AI):**\n"
            "pip install -r requirements-minimal.txt\n\n"
            "The application works great without AI features!\n"
            "You can still use all other tools."
        )
        guide.setStandardButtons(QMessageBox.StandardButton.Ok)
        guide.exec()

    def create_hotkeys_tab(self):
        """Create hotkeys settings tab with HotkeyDisplayWidget."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)

        try:
            try:
                from .hotkey_display_qt import HotkeyDisplayWidget
            except (ImportError, OSError, RuntimeError):
                from ui.hotkey_display_qt import HotkeyDisplayWidget

            self.hotkey_widget = HotkeyDisplayWidget(
                parent=tab,
                tooltip_manager=self.tooltip_manager,
            )

            # Persist key rebindings: save to config and emit settingsChanged
            def _on_hotkey_changed(action_id: str, new_key: str) -> None:
                try:
                    self.config.set('hotkeys', action_id, value=new_key)
                    self.config.save()
                    self.settingsChanged.emit(f"hotkeys.{action_id}", new_key)
                except Exception as _e:
                    logger.error(f"Failed to save hotkey {action_id}: {_e}")

            self.hotkey_widget.hotkey_changed.connect(_on_hotkey_changed)

            # Pre-populate widget from saved config
            saved = {}
            try:
                hotkeys_section = self.config.settings.get('hotkeys', {})
                for key, val in hotkeys_section.items():
                    if isinstance(val, str):
                        saved[key] = val
            except Exception:
                pass
            if saved:
                self.hotkey_widget.load_hotkeys(saved)

            layout.addWidget(self.hotkey_widget)
        except (ImportError, OSError) as e:
            logger.warning(f"HotkeyDisplayWidget unavailable: {e}")
            self.hotkey_widget = None
            info = QLabel(
                "⌨️ Hotkey configuration requires PyQt6.\n"
                "Install with: pip install PyQt6"
            )
            info.setWordWrap(True)
            layout.addWidget(info)

        layout.addStretch()
        return tab

    def create_language_tab(self):
        """Create language selection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        lang_group = QGroupBox("Application Language")
        lang_layout = QVBoxLayout()

        lang_layout.addWidget(QLabel(
            "Select the display language for the application UI.\n"
            "Some labels will update immediately; others after restart."
        ))

        self.language_combo = QComboBox()
        _LANGUAGE_OPTIONS = [
            ("English",    "en"),
            ("Español",    "es"),
            ("Français",   "fr"),
            ("Deutsch",    "de"),
            ("日本語",      "ja"),
            ("中文",        "zh"),
            ("Português",  "pt"),
        ]
        for label, code in _LANGUAGE_OPTIONS:
            self.language_combo.addItem(label, userData=code)

        # Pre-select saved language
        saved_lang = self.config.get('ui', 'language', default='en')
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == saved_lang:
                self.language_combo.setCurrentIndex(i)
                break

        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.language_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        layout.addStretch()
        return tab

    def _on_language_changed(self, index: int):
        """Handle language combo box selection change."""
        if self._updating:
            return
        lang_code = self.language_combo.itemData(index)
        if lang_code:
            self.config.set('ui', 'language', value=lang_code)
            self.config.save()
            self.settingsChanged.emit('ui.language', lang_code)
            logger.info(f"Language changed to: {lang_code}")

    def create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Debug options
        debug_group = QGroupBox("Debug Options")
        debug_layout = QVBoxLayout()
        
        self.debug_check = QCheckBox("Enable Debug Mode")
        self.debug_check.stateChanged.connect(lambda: self.on_setting_changed('logging', 'debug_mode'))
        self.set_tooltip(self.debug_check, 'debug_mode')
        debug_layout.addWidget(self.debug_check)
        
        self.verbose_check = QCheckBox("Verbose Logging")
        self.verbose_check.stateChanged.connect(lambda: self.on_setting_changed('logging', 'verbose'))
        self.set_tooltip(self.verbose_check, 'verbose_logging')
        debug_layout.addWidget(self.verbose_check)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        # Import/Export
        io_group = QGroupBox("Settings Management")
        io_layout = QVBoxLayout()
        
        io_info = QLabel("Export your settings to share with others or back them up.\n"
                        "Import settings to restore a previous configuration.")
        io_info.setWordWrap(True)
        io_layout.addWidget(io_info)
        
        export_config_btn = QPushButton("Export Configuration")
        export_config_btn.clicked.connect(self.export_settings)
        self.set_tooltip(export_config_btn, 'export_button')
        io_layout.addWidget(export_config_btn)
        
        import_config_btn = QPushButton("Import Configuration")
        import_config_btn.clicked.connect(self.import_settings)
        self.set_tooltip(import_config_btn, 'import_button')
        io_layout.addWidget(import_config_btn)
        
        io_group.setLayout(io_layout)
        layout.addWidget(io_group)
        
        # Config file location
        location_group = QGroupBox("Configuration File")
        location_layout = QVBoxLayout()
        
        config_path = str(self.config.config_file)
        path_label = QLabel(f"Location: {config_path}")
        path_label.setWordWrap(True)
        location_layout.addWidget(path_label)
        
        open_config_btn = QPushButton("Open Config Folder")
        open_config_btn.clicked.connect(self.open_config_folder)
        self.set_tooltip(open_config_btn, 'open_config')
        location_layout.addWidget(open_config_btn)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        return tab
    
    def load_settings(self):
        """Load settings from config and update UI"""
        self._updating = True
        
        try:
            # Appearance
            theme = self.config.get('ui', 'theme', default='dark')
            theme_map = {
                'dark': 'Dark', 'light': 'Light', 'nord': 'Nord', 'dracula': 'Dracula',
                'solarized dark': 'Solarized Dark', 'solarized_dark': 'Solarized Dark',
                'forest': 'Forest', 'forest_green': 'Forest',
                'ocean': 'Ocean', 'ocean_blue': 'Ocean',
                'sunset': 'Sunset', 'sunset_warm': 'Sunset',
                'cyberpunk': 'Cyberpunk',
                'gore': 'Gore',
                'goth': 'Goth',
            }
            self.theme_combo.setCurrentText(theme_map.get(theme.lower(), theme.capitalize()))
            
            accent = self.config.get('ui', 'accent_color', default='#0d7377')
            self.accent_color_widget.current_color = QColor(accent)
            self.accent_color_widget.update()
            
            opacity = self.config.get('ui', 'window_opacity', default=1.0)
            self.opacity_slider.setValue(int(opacity * 100))
            
            compact = self.config.get('ui', 'compact_view', default=False)
            self.compact_view_check.setChecked(compact)
            
            # Cursor (Appearance tab sub-section + full Cursor tab)
            cursor = self.config.get('ui', 'cursor', default='default')
            self.cursor_type_combo.setCurrentText(cursor.capitalize())
            if hasattr(self, 'appearance_cursor_combo'):
                self.appearance_cursor_combo.setCurrentText(cursor.capitalize())

            cursor_size = self.config.get('ui', 'cursor_size', default='medium')
            self.cursor_size_combo.setCurrentText(cursor_size.capitalize())
            
            trail = self.config.get('ui', 'cursor_trail', default=False)
            self.cursor_trail_check.setChecked(trail)
            if hasattr(self, 'appearance_trail_check'):
                self.appearance_trail_check.setChecked(trail)
            
            trail_color = self.config.get('ui', 'cursor_trail_color', default='rainbow')
            self.cursor_trail_color_combo.setCurrentText(trail_color.capitalize())

            trail_intensity = self.config.get('ui', 'cursor_trail_intensity', default=5)
            self.cursor_trail_intensity.setValue(max(1, min(10, int(trail_intensity))))
            
            # Font (Appearance tab sub-section + full Font tab)
            font_family = self.config.get('ui', 'font_family', default='Segoe UI')
            self.font_family_combo.setCurrentText(font_family)
            if hasattr(self, 'appearance_font_combo'):
                self.appearance_font_combo.setCurrentText(font_family)

            font_size = self.config.get('ui', 'font_size', default=12)
            self.font_size_spin.setValue(font_size)
            if hasattr(self, 'appearance_font_size'):
                self.appearance_font_size.setValue(font_size)
            
            font_weight = self.config.get('ui', 'font_weight', default='normal')
            self.font_weight_combo.setCurrentText(font_weight.capitalize())
            
            icon_size = self.config.get('ui', 'icon_size', default='medium')
            self.icon_size_combo.setCurrentText(icon_size.capitalize())
            
            # Behavior
            anim_speed = self.config.get('ui', 'animation_speed', default=1.0)
            self.animation_slider.setValue(int(anim_speed * 10))
            
            tooltip_enabled = self.config.get('ui', 'tooltip_enabled', default=True)
            self.tooltip_enabled_check.setChecked(tooltip_enabled)
            
            tooltip_mode = self.config.get('ui', 'tooltip_mode', default='normal')
            mode_index_map = {
                'normal': 0,
                'dumbed_down': 1,
                'dumbed-down': 1,
                'vulgar_panda': 2,
            }
            self.tooltip_mode_combo.setCurrentIndex(mode_index_map.get(tooltip_mode, 0))
            
            tooltip_delay = self.config.get('ui', 'tooltip_delay', default=0.5)
            self.tooltip_delay_slider.setValue(int(tooltip_delay * 10))
            
            sound_enabled = self.config.get('ui', 'sound_enabled', default=True)
            self.sound_enabled_check.setChecked(sound_enabled)
            
            sound_volume = self.config.get('ui', 'sound_volume', default=0.7)
            self.sound_volume_slider.setValue(int(sound_volume * 100))
            
            # Performance
            threads = self.config.get('performance', 'max_threads', default=4)
            self.thread_spin.setValue(threads)
            
            memory = self.config.get('performance', 'memory_limit_mb', default=2048)
            self.memory_spin.setValue(memory)
            
            cache = self.config.get('performance', 'cache_size_mb', default=512)
            self.cache_spin.setValue(cache)
            
            quality = self.config.get('performance', 'thumbnail_quality', default='high')
            self.quality_combo.setCurrentText(quality.capitalize())
            
            # Advanced
            debug = self.config.get('logging', 'debug_mode', default=False)
            self.debug_check.setChecked(debug)
            
            verbose = self.config.get('logging', 'verbose', default=False)
            self.verbose_check.setChecked(verbose)

            # AI settings
            if hasattr(self, 'epochs_spin'):
                self.epochs_spin.setValue(int(self.config.get('ai', 'epochs', default=50)))
            if hasattr(self, 'batch_size_combo'):
                self.batch_size_combo.setCurrentText(str(self.config.get('ai', 'batch_size', default=16)))
            if hasattr(self, 'lr_combo'):
                self.lr_combo.setCurrentText(str(self.config.get('ai', 'learning_rate', default=0.0001)))
            if hasattr(self, 'max_img_spin'):
                self.max_img_spin.setValue(int(self.config.get('ai', 'max_image_size', default=1024)))
            if hasattr(self, 'ai_threads_spin'):
                self.ai_threads_spin.setValue(int(self.config.get('ai', 'threads', default=4)))
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}", exc_info=True)
        finally:
            self._updating = False

    def on_setting_changed(self, section: str, key: str):
        """Handle generic setting changes"""
        if self._updating:
            return
        
        try:
            widget = self.sender()
            
            # Determine value based on widget type
            if isinstance(widget, QComboBox):
                raw = widget.currentText().lower().replace(' ', '_')
                # Try to coerce numeric strings (batch_size, epochs etc.) to int/float
                try:
                    value = int(raw)
                except ValueError:
                    try:
                        value = float(raw)
                    except ValueError:
                        value = raw
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                value = widget.value()
            elif isinstance(widget, QSlider):
                value = widget.value()
            elif hasattr(widget, 'text') and not isinstance(widget, QCheckBox):
                # QLineEdit, QLabel — use text() as string value
                value = widget.text()
            else:
                return
            
            # Save to config
            self.config.set(section, key, value=value)
            self.config.save()
            
            # Emit signal for real-time updates
            self.settingsChanged.emit(f"{section}.{key}", value)
            
            # Apply specific changes
            if section == 'ui' and key == 'theme':
                self.apply_theme()
            elif section == 'ui' and key == 'font_family':
                self._apply_font()
            elif section == 'ui' and key == 'font_size':
                self._apply_font()
            elif section == 'ui' and key == 'cursor':
                self._apply_cursor(value)
            elif section == 'ui' and key == 'cursor_trail':
                # Delegate to main window — the settingsChanged signal above already triggers
                # _apply_cursor_trail() via on_settings_changed; no extra action needed here.
                if self.main_window and hasattr(self.main_window, '_apply_cursor_trail'):
                    self.main_window._apply_cursor_trail(bool(value))
                # Update preview widget visibility
                if hasattr(self, '_cursor_trail_preview') and self._cursor_trail_preview is not None:
                    if bool(value):
                        self._cursor_trail_preview.view.start_animation()
                    else:
                        self._cursor_trail_preview.view.stop_animation()
            elif section == 'ui' and key == 'cursor_trail_intensity':
                if self.main_window and hasattr(self.main_window, '_cursor_trail_overlay'):
                    overlay = self.main_window._cursor_trail_overlay
                    if overlay is not None and hasattr(overlay, 'set_intensity'):
                        overlay.set_intensity(int(value))
                # Update preview intensity
                if hasattr(self, '_cursor_trail_preview') and self._cursor_trail_preview is not None:
                    try:
                        self._cursor_trail_preview.set_trail_length(int(value))
                    except Exception:
                        pass
            
        except Exception as e:
            logger.error(f"Error saving setting {section}.{key}: {e}", exc_info=True)
    
    def on_color_changed(self, key: str, color: str):
        """Handle color changes"""
        if self._updating:
            return
        
        try:
            self.config.set('ui', key, value=color)
            self.config.save()
            self.settingsChanged.emit(f"ui.{key}", color)
            self.apply_theme()
        except Exception as e:
            logger.error(f"Error saving color: {e}", exc_info=True)
    
    def on_opacity_changed(self, label: QLabel, value: int):
        """Handle opacity slider changes"""
        opacity = value / 100.0
        label.setText(f"Window Opacity: {value}%")
        
        if not self._updating:
            self.config.set('ui', 'window_opacity', value=opacity)
            self.config.save()
            self.settingsChanged.emit("ui.window_opacity", opacity)
            
            # Apply opacity to main window
            if self.main_window:
                self.main_window.setWindowOpacity(opacity)
    
    def on_animation_speed_changed(self, label: QLabel, value: int):
        """Handle animation speed slider changes"""
        speed = value / 10.0
        label.setText(f"Animation Speed: {speed:.1f}x")
        
        if not self._updating:
            self.config.set('ui', 'animation_speed', value=speed)
            self.config.save()
            self.settingsChanged.emit("ui.animation_speed", speed)
    
    def on_tooltip_mode_changed(self):
        """Handle tooltip mode changes"""
        if self._updating:
            return
        
        try:
            index = self.tooltip_mode_combo.currentIndex()
            mode_map = {
                0: ('normal', 'NORMAL'),           # Normal mode
                1: ('dumbed-down', 'BEGINNER'),    # Beginner mode
                2: ('vulgar_panda', 'PROFANE')     # Profane mode
            }
            
            mode_value, mode_enum_name = mode_map.get(index, ('normal', 'NORMAL'))
            
            self.config.set('ui', 'tooltip_mode', value=mode_value)
            self.config.save()
            self.settingsChanged.emit("ui.tooltip_mode", mode_value)
            
            # Update tooltip system if available
            if self.main_window and hasattr(self.main_window, 'tooltip_manager'):
                from features.tutorial_system import TooltipMode
                mode_enum = getattr(TooltipMode, mode_enum_name, TooltipMode.NORMAL)
                self.main_window.tooltip_manager.set_mode(mode_enum)
                # set_mode already calls refresh_all(), but call explicitly as belt-and-suspenders
                if hasattr(self.main_window.tooltip_manager, 'refresh_all'):
                    self.main_window.tooltip_manager.refresh_all()
                logger.info(f"Tooltip mode changed to: {mode_value} ({mode_enum_name})")
            
        except Exception as e:
            logger.error(f"Error changing tooltip mode: {e}", exc_info=True)
    
    def on_tooltip_delay_changed(self, label: QLabel, value: int):
        """Handle tooltip delay slider changes"""
        delay = value / 10.0
        label.setText(f"Tooltip Delay: {delay:.1f}s")
        
        if not self._updating:
            self.config.set('ui', 'tooltip_delay', value=delay)
            self.config.save()
            self.settingsChanged.emit("ui.tooltip_delay", delay)
    
    def on_volume_changed(self, label: QLabel, value: int):
        """Handle volume slider changes"""
        volume = value / 100.0
        label.setText(f"Volume: {value}%")
        
        if not self._updating:
            self.config.set('ui', 'sound_volume', value=volume)
            self.config.save()
            self.settingsChanged.emit("ui.sound_volume", volume)
    
    def apply_theme(self):
        """Delegate theme application to main window (which has all 9 theme implementations)."""
        if not self.main_window:
            return
        try:
            if hasattr(self.main_window, 'apply_theme'):
                self.main_window.apply_theme()
        except Exception as e:
            logger.error(f"Error delegating apply_theme: {e}", exc_info=True)

    def _apply_font(self):
        """Apply font family + size from config to the main window."""
        if not self.main_window:
            return
        try:
            family = self.config.get('ui', 'font_family', default='Segoe UI')
            size = int(self.config.get('ui', 'font_size', default=12))
            from PyQt6.QtGui import QFont as _QFont
            app_font = _QFont(family, size)
            from PyQt6.QtWidgets import QApplication as _QApp
            _QApp.setFont(app_font)
            logger.info(f"Font applied: {family} {size}pt")
        except Exception as e:
            logger.error(f"Error applying font: {e}", exc_info=True)

    def _apply_cursor(self, cursor_name: str):
        """Apply cursor style to main window."""
        if not self.main_window:
            return
        try:
            from PyQt6.QtCore import Qt as _Qt
            from PyQt6.QtGui import QCursor as _QCursor
            _CURSOR_MAP = {
                'default': _Qt.CursorShape.ArrowCursor,
                'pointer': _Qt.CursorShape.PointingHandCursor,
                'crosshair': _Qt.CursorShape.CrossCursor,
                'panda_paw': _Qt.CursorShape.PointingHandCursor,
                'bamboo': _Qt.CursorShape.PointingHandCursor,
                'star': _Qt.CursorShape.PointingHandCursor,
            }
            shape = _CURSOR_MAP.get(cursor_name.lower().replace(' ', '_'),
                                    _Qt.CursorShape.ArrowCursor)
            self.main_window.setCursor(_QCursor(shape))
        except Exception as e:
            logger.error(f"Error applying cursor: {e}", exc_info=True)

    def _browse_dataset_folder(self) -> None:
        """Open a folder-picker dialog for the custom training dataset path."""
        try:
            from PyQt6.QtWidgets import QFileDialog as _QFD
            folder = _QFD.getExistingDirectory(
                self, "Select Dataset Folder",
                getattr(self, 'dataset_path_edit', None) and self.dataset_path_edit.text() or "",
            )
            if folder:
                self.dataset_path_edit.setReadOnly(False)
                self.dataset_path_edit.setText(folder)
                self.dataset_path_edit.setReadOnly(True)
                self.config.set('ai', 'custom_dataset_path', folder)
                logger.info("Custom dataset path set: %s", folder)
        except Exception as exc:
            logger.error("_browse_dataset_folder: %s", exc)

    def _on_start_ai_training(self) -> None:
        """Handle 'Start Training / Export' button in AI Settings tab."""
        try:
            from ai.training_pytorch import is_pytorch_available, TrainingMode
        except (ImportError, OSError, RuntimeError):
            try:
                from src.ai.training_pytorch import is_pytorch_available, TrainingMode  # type: ignore[no-redef]
            except (ImportError, OSError, RuntimeError):
                if hasattr(self, '_ai_train_status'):
                    self._ai_train_status.setText(
                        "⚠️ PyTorch not installed — cannot train.\n"
                        "Install with: pip install torch torchvision"
                    )
                return

        if not is_pytorch_available():
            if hasattr(self, '_ai_train_status'):
                self._ai_train_status.setText(
                    "⚠️ PyTorch not available — install with:\n"
                    "pip install torch torchvision"
                )
            return

        mode_text = getattr(self, 'training_mode_combo', None)
        mode_str = mode_text.currentText() if mode_text else 'Standard'
        epochs = getattr(self, 'epochs_spin', None)
        epochs_val = epochs.value() if epochs else 10

        if hasattr(self, '_ai_train_status'):
            self._ai_train_status.setText(f"⏳ {mode_str} — {epochs_val} epochs…")
        if hasattr(self, '_ai_train_progress'):
            self._ai_train_progress.setVisible(True)
            self._ai_train_progress.setRange(0, 0)  # pulse

        # Emit so main window knows training started
        self.settingsChanged.emit('ai.training_started', {
            'mode': mode_str,
            'epochs': epochs_val,
        })

        logger.info(f"AI training requested: mode={mode_str}, epochs={epochs_val}")
        # Actual training runs in main window's _start_ai_training_job() handler.
        # The settings panel is not responsible for the QThread — main.py is.

    def adjust_color(self, hex_color: str, factor: float) -> str:
        """Adjust color brightness by factor"""
        try:
            color = QColor(hex_color)
            h, s, v, a = color.getHsv()
            v = int(min(255, v * factor))
            color.setHsv(h, s, v, a)
            return color.name()
        except Exception as e:
            logger.debug(f"Error adjusting color brightness: {e}")
            return hex_color
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config.reset_to_defaults()
                self.config.save(immediate=True)
                self.load_settings()
                self.apply_theme()
                
                QMessageBox.information(
                    self,
                    "Settings Reset",
                    "All settings have been reset to defaults."
                )
                logger.info("Settings reset to defaults")
            except Exception as e:
                logger.error(f"Error resetting settings: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to reset settings: {e}"
                )
    
    def export_settings(self):
        """Export settings to a JSON file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Settings",
                "settings.json",
                "JSON Files (*.json)"
            )
            
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(self.config.settings, f, indent=4)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Settings exported to:\n{file_path}"
                )
                logger.info(f"Settings exported to: {file_path}")
                
        except Exception as e:
            logger.error(f"Error exporting settings: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export settings: {e}"
            )
    
    def import_settings(self):
        """Import settings from a JSON file"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Settings",
                "",
                "JSON Files (*.json)"
            )
            
            if file_path:
                with open(file_path, 'r') as f:
                    imported_settings = json.load(f)
                
                # Merge imported settings with current
                self.config.settings.update(imported_settings)
                self.config.save(immediate=True)
                
                # Reload UI
                self.load_settings()
                self.apply_theme()
                
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Settings imported from:\n{file_path}"
                )
                logger.info(f"Settings imported from: {file_path}")
                
        except Exception as e:
            logger.error(f"Error importing settings: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import settings: {e}"
            )
    
    def open_config_folder(self):
        """Open the configuration folder in file explorer"""
        try:
            import os
            import platform
            
            config_dir = self.config.config_file.parent
            
            if platform.system() == "Windows":
                os.startfile(config_dir)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{config_dir}'")
            else:  # Linux
                os.system(f"xdg-open '{config_dir}'")
                
            logger.info(f"Opened config folder: {config_dir}")
            
        except Exception as e:
            logger.error(f"Error opening config folder: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to open config folder: {e}"
            )
    
    def set_tooltip(self, widget: QWidget, widget_id: str):
        """Set tooltip for a widget using the tooltip manager"""
        try:
            if self.main_window and getattr(self.main_window, 'tooltip_manager', None):
                tm = self.main_window.tooltip_manager
                tooltip_text = tm.get_tooltip(widget_id)
                widget.setToolTip(tooltip_text)
                # Register so the widget gets updated on mode changes and cycles tips
                if hasattr(tm, 'register'):
                    tm.register(widget, widget_id)
            else:
                # Fallback tooltips
                fallback_tooltips = {
                    'theme_selector': "Choose a theme: Dark, Light, Nord, Dracula, or Solarized Dark",
                    'accent_color': "Select the accent color for buttons and highlights",
                    'opacity_slider': "Adjust window transparency (100% = fully opaque)",
                    'compact_view': "Enable a more compact UI layout to fit more on screen",
                    'cursor_selector': "Choose your cursor style. Unlock more through achievements!",
                    'cursor_size': "Set cursor size (Small, Medium, Large, Extra Large)",
                    'cursor_trail': "Enable a visual trail effect that follows your mouse cursor",
                    'cursor_trail_color': "Choose the color scheme for your cursor trail",
                    'font_family': "Select the application font family",
                    'font_size': "Set font size in points (default: 12)",
                    'font_weight': "Choose font weight (Light, Normal, Bold)",
                    'icon_size': "Set icon size throughout the application",
                    'animation_speed': "Adjust UI animation speed (0 = off, 1 = normal, 2 = fast)",
                    'tooltip_enabled': "Enable or disable tooltips throughout the application",
                    'tooltip_mode': "Choose tooltip verbosity:\n• Normal: standard tooltips\n• Dumbed Down: simpler language\n• Vulgar Panda: panda-themed humor",
                    'tooltip_delay': "Set delay in milliseconds before tooltips appear",
                    'sound_enabled': "Enable or disable sound effects and music",
                    'sound_volume': "Adjust sound effect volume (0-100%)",
                    'thread_count': "Number of parallel threads for processing (higher = faster but uses more CPU)",
                    'memory_limit': "Maximum memory usage in MB (lower = safer, higher = faster)",
                    'cache_size': "Cache size in MB for thumbnails and previews",
                    'thumbnail_quality': "Quality of generated thumbnails (Low/Medium/High)",
                    'debug_mode': "Enable debug logging for troubleshooting",
                    'verbose_logging': "Enable verbose log output (logs more detail to file)",
                    'reset_button': "Reset ALL settings to their default values",
                    'export_button': "Export current settings to a JSON file for backup or sharing",
                    'import_button': "Import settings from a previously exported JSON file",
                    'open_config': "Open configuration folder in your file explorer",
                    'input_archive_checkbox': "Process images inside ZIP/7Z/RAR archives",
                    'output_archive_checkbox': "Save processed images into a ZIP archive",
                    'recursive_search_checkbox': "Search subfolders recursively for images",
                    'ai_suggestion_label': "AI-suggested folder for this texture based on content analysis",
                    'ai_confidence_label': "How confident the AI is in its suggestion (0-100%)",
                    'feedback_good_button': "Accept the AI suggestion and improve future recommendations",
                    'feedback_bad_button': "Reject the AI suggestion and provide correct folder manually",
                    'manual_override_input': "Type a custom folder path to override the AI suggestion",
                    'folder_suggestions_list': "List of AI-suggested folders sorted by confidence score",
                }
                widget.setToolTip(fallback_tooltips.get(widget_id, ""))
        except Exception as e:
            logger.debug(f"Could not set tooltip for {widget_id}: {e}")


# Example usage for testing
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    from src.config import Config
    
    app = QApplication(sys.argv)
    
    config = Config()
    panel = SettingsPanelQt(config)
    panel.setWindowTitle("Settings Panel Test")
    panel.resize(800, 600)
    panel.show()
    
    sys.exit(app.exec())
