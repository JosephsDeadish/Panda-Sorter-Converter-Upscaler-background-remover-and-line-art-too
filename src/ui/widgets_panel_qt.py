"""
Qt implementation of the widgets panel.
Pure PyQt6 UI for interactive widgets and tools.
"""

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                  QLabel, QLineEdit, QComboBox, QScrollArea)
    from PyQt6.QtCore import Qt, pyqtSignal
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    # Dummy classes for when PyQt6 not available
    class QWidget: pass
    class pyqtSignal: pass


class WidgetsPanelQt(QWidget):
    """Qt-based widgets panel for managing panda toys and items."""
    
    # Signals for compatibility
    widget_selected = pyqtSignal(object) if PYQT_AVAILABLE else None
    
    def __init__(self, widget_collection, panda_widget, parent=None, tooltip_manager=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for WidgetsPanelQt")
        
        super().__init__(parent)
        self.widget_collection = widget_collection
        self.panda_widget = panda_widget
        self.current_category = "all"
        self.tooltip_manager = tooltip_manager
        
        self.setup_ui()
        self.load_widgets()
    
    def setup_ui(self):
        """Create the UI layout."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎮 Panda Widgets & Toys")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Search and filter row
        filter_layout = QHBoxLayout()
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search widgets...")
        self.search_box.textChanged.connect(self.filter_widgets)
        filter_layout.addWidget(self.search_box)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Toys", "Food", "Tools", "Decorations"])
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        filter_layout.addWidget(self.category_combo)
        
        layout.addLayout(filter_layout)
        
        # Widgets display area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)
        
        self.widgets_container = QWidget()
        self.widgets_layout = QVBoxLayout(self.widgets_container)
        scroll.setWidget(self.widgets_container)
        
        layout.addWidget(scroll)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add to Scene")
        add_btn.clicked.connect(self.add_selected_widget)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("❌ Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_widget)
        button_layout.addWidget(remove_btn)
        
        layout.addLayout(button_layout)
    
    def load_widgets(self):
        """Load widgets from collection."""
        # Clear existing
        while self.widgets_layout.count():
            child = self.widgets_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get widgets from collection
        if hasattr(self.widget_collection, 'get_all_widgets'):
            widgets = self.widget_collection.get_all_widgets()
        else:
            widgets = []
        
        # Add widget items
        for widget in widgets:
            self.add_widget_item(widget)
    
    def add_widget_item(self, widget):
        """Add a widget item to the display."""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        
        # Icon/emoji
        icon = QLabel(widget.get('emoji', '🎮'))
        icon.setStyleSheet("font-size: 24px;")
        item_layout.addWidget(icon)
        
        # Name
        name = QLabel(widget.get('name', 'Widget'))
        item_layout.addWidget(name)
        
        item_layout.addStretch()
        
        # Select button
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(lambda: self.select_widget(widget))
        item_layout.addWidget(select_btn)
        
        self.widgets_layout.addWidget(item_widget)
    
    def select_widget(self, widget):
        """Select a widget."""
        if self.widget_selected:
            self.widget_selected.emit(widget)
    
    def filter_widgets(self):
        """Filter widgets based on search."""
        self.load_widgets()
    
    def on_category_changed(self, category):
        """Handle category change."""
        self.current_category = category.lower()
        self.load_widgets()
    
    def add_selected_widget(self):
        """Add selected widget to scene."""
        # Implementation depends on panda widget API
        pass
    
    def remove_selected_widget(self):
        """Remove selected widget from scene."""
        # Implementation depends on panda widget API
        pass
    
    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager:
            tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tooltip:
                widget.setToolTip(tooltip)
