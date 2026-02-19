"""
PyQt6 Closet Display System
Replaces canvas-based clothing display with Qt widgets
"""

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                                 QLabel, QPushButton, QGridLayout, QFrame, QLineEdit)
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QPixmap, QPainter, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    class pyqtSignal:
        def __init__(self, *args): pass
        def connect(self, *args): pass
        def emit(self, *args): pass
    class Qt:
        class AlignmentFlag:
            AlignCenter = 0
        class CursorShape:
            PointingHandCursor = 0
        class MouseButton:
            LeftButton = 1
        class ScrollBarPolicy:
            ScrollBarAlwaysOff = 1


class ClothingItemWidget(QFrame):
    """Individual clothing item"""
    
    clicked = pyqtSignal(dict)
    
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        
        # Icon
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background-color: #f0f0f0; border-radius: 4px;")
        
        # Set icon if available
        if 'emoji' in self.item_data:
            icon_label.setText(self.item_data['emoji'])
            icon_label.setStyleSheet("font-size: 32pt; background-color: #f0f0f0;")
        
        layout.addWidget(icon_label)
        
        # Name
        name_label = QLabel(self.item_data.get('name', 'Unknown'))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item_data)
        super().mousePressEvent(event)


class ClosetDisplayWidget(QWidget):
    """Complete closet display with clothing items"""
    
    item_equipped = pyqtSignal(dict)
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        self.items = []
        self.tooltip_manager = tooltip_manager
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)
        
        # Category filters
        filter_layout = QHBoxLayout()
        categories = ['All', 'Hats', 'Shirts', 'Pants', 'Shoes', 'Accessories']
        for cat in categories:
            btn = QPushButton(cat)
            btn.clicked.connect(lambda checked, c=cat: self.filter_by_category(c))
            filter_layout.addWidget(btn)
        main_layout.addLayout(filter_layout)
        
        # Scroll area for items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Grid for items
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        scroll.setWidget(self.grid_widget)
        
        main_layout.addWidget(scroll)
        
    def load_clothing_items(self, items):
        """Load list of clothing items"""
        self.items = items
        self.display_items(items)
        
    def display_items(self, items):
        """Display items in grid"""
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add items
        row, col = 0, 0
        cols = 4
        
        for item_data in items:
            item_widget = ClothingItemWidget(item_data)
            item_widget.clicked.connect(self.on_item_clicked)
            self.grid_layout.addWidget(item_widget, row, col)
            
            col += 1
            if col >= cols:
                col = 0
                row += 1
                
    def on_item_clicked(self, item_data):
        """Handle item click"""
        self.item_equipped.emit(item_data)
        
    def filter_by_category(self, category):
        """Filter items by category"""
        if category == 'All':
            filtered = self.items
        else:
            filtered = [item for item in self.items 
                       if item.get('category') == category.lower()]
        self.display_items(filtered)
        
    def filter_items(self, text):
        """Filter by search text"""
        if not text:
            self.display_items(self.items)
            return
            
        text_lower = text.lower()
        filtered = [item for item in self.items
                   if text_lower in item.get('name', '').lower()]
        self.display_items(filtered)
    
    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager:
            tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tooltip:
                widget.setToolTip(tooltip)


def create_closet_display(parent=None, tooltip_manager=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return ClosetDisplayWidget(parent, tooltip_manager)
