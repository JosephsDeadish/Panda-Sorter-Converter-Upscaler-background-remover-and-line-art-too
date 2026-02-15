"""
PyQt6 Widgets Display
Replaces canvas-based widgets panel preview
"""

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                                 QListWidgetItem, QLabel, QPushButton, QLineEdit,
                                 QGraphicsView, QGraphicsScene, QGraphicsPixmapItem)
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QPixmap, QPainter, QIcon
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class WidgetsDisplayWidget(QWidget):
    """Widget items display and preview"""
    
    item_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Left side: List
        left_layout = QVBoxLayout()
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)
        
        # Category filter
        filter_layout = QHBoxLayout()
        categories = ['All', 'Toys', 'Food', 'Tools', 'Decorations']
        for cat in categories:
            btn = QPushButton(cat)
            btn.clicked.connect(lambda checked, c=cat: self.filter_by_category(c))
            filter_layout.addWidget(btn)
        left_layout.addLayout(filter_layout)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        left_layout.addWidget(self.list_widget)
        
        layout.addLayout(left_layout, 2)
        
        # Right side: Preview
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Preview:"))
        
        self.preview_view = QGraphicsView()
        self.preview_scene = QGraphicsScene()
        self.preview_view.setScene(self.preview_scene)
        self.preview_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        right_layout.addWidget(self.preview_view)
        
        # Item info
        self.info_label = QLabel("Select an item...")
        self.info_label.setWordWrap(True)
        right_layout.addWidget(self.info_label)
        
        layout.addLayout(right_layout, 1)
        
    def load_widgets(self, items):
        """Load widget items"""
        self.items = items
        self.display_items(items)
        
    def display_items(self, items):
        """Display items in list"""
        self.list_widget.clear()
        
        for item in items:
            list_item = QListWidgetItem(item.get('name', 'Unknown'))
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            
            # Add emoji icon if available
            if 'emoji' in item:
                list_item.setText(f"{item['emoji']} {item.get('name', 'Unknown')}")
            
            self.list_widget.addItem(list_item)
            
    def on_item_clicked(self, item):
        """Handle item selection"""
        item_data = item.data(Qt.ItemDataRole.UserRole)
        self.preview_item(item_data)
        self.item_selected.emit(item_data)
        
    def preview_item(self, item_data):
        """Show item preview"""
        self.preview_scene.clear()
        
        # Show item emoji/icon large
        if 'emoji' in item_data:
            text_item = self.preview_scene.addText(item_data['emoji'])
            font = text_item.font()
            font.setPointSize(48)
            text_item.setFont(font)
            
        # Update info
        info_text = f"Name: {item_data.get('name', 'Unknown')}\n"
        info_text += f"Type: {item_data.get('type', 'Unknown')}\n"
        info_text += f"Category: {item_data.get('category', 'Unknown')}\n"
        if 'description' in item_data:
            info_text += f"\n{item_data['description']}"
        self.info_label.setText(info_text)
        
    def filter_by_category(self, category):
        """Filter by category"""
        if category == 'All':
            filtered = self.items
        else:
            filtered = [item for item in self.items
                       if item.get('category', '').lower() == category.lower()]
        self.display_items(filtered)
        
    def filter_items(self, text):
        """Filter by search"""
        if not text:
            self.display_items(self.items)
            return
            
        text_lower = text.lower()
        filtered = [item for item in self.items
                   if text_lower in item.get('name', '').lower()]
        self.display_items(filtered)


def create_widgets_display(parent=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return WidgetsDisplayWidget(parent)
