"""
Inventory Panel - View owned items
Qt implementation of inventory display
"""

import logging

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QGridLayout, QComboBox, QLineEdit
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QWidget = object

logger = logging.getLogger(__name__)

# Try to import shop system
try:
    from features.shop_system import ShopSystem, ShopItem
    SHOP_AVAILABLE = True
except ImportError:
    try:
        from ..features.shop_system import ShopSystem, ShopItem
        SHOP_AVAILABLE = True
    except ImportError:
        logger.warning("Shop system not available for inventory")
        SHOP_AVAILABLE = False
        ShopSystem = None
        ShopItem = None


class InventoryItemWidget(QFrame):
    """Individual inventory item display"""
    
    item_selected = pyqtSignal(str)  # item_id
    
    def __init__(self, item: 'ShopItem', parent=None):
        super().__init__(parent)
        self.item = item
        self.setup_ui()
        
    def setup_ui(self):
        """Create the item UI"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                border: 2px solid #45a049;
                background-color: #c8e6c9;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Icon
        icon_label = QLabel(self.item.icon)
        icon_label.setFont(QFont("Segoe UI", 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Name
        name_label = QLabel(self.item.name)
        name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(self.item.description)
        desc_label.setFont(QFont("Segoe UI", 8))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(40)
        layout.addWidget(desc_label)
        
        # Owned indicator
        owned_label = QLabel("✓ Owned")
        owned_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        owned_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        owned_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(owned_label)
        
    def mousePressEvent(self, event):
        """Handle click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.item_selected.emit(self.item.id)
        super().mousePressEvent(event)


class InventoryPanelQt(QWidget):
    """Main inventory panel for viewing owned items"""
    
    item_selected = pyqtSignal(str)  # item_id
    
    def __init__(self, shop_system=None, parent=None, tooltip_manager=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 required for InventoryPanelQt")
        
        super().__init__(parent)
        self.tooltip_manager = tooltip_manager
        
        # Initialize shop system if not provided
        if SHOP_AVAILABLE:
            self.shop_system = shop_system or ShopSystem()
        else:
            self.shop_system = None
        
        self.current_category = "All"
        self.setup_ui()
        self.refresh_inventory()
        
    def setup_ui(self):
        """Create the inventory UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📦 Your Inventory")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_inventory)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Category filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        
        self.category_combo = QComboBox()
        categories = ["All", "Outfits", "Clothes", "Hats", "Shoes", "Accessories", 
                     "Fur Styles", "Fur Colors", "Toys", "Food", "Special"]
        self.category_combo.addItems(categories)
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        filter_layout.addWidget(self.category_combo)
        
        # Search
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search your items...")
        self.search_input.textChanged.connect(self.filter_items)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Items grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        scroll.setWidget(self.grid_widget)
        
        layout.addWidget(scroll)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
    def refresh_inventory(self):
        """Refresh inventory display"""
        if not SHOP_AVAILABLE or not self.shop_system:
            self.status_label.setText("⚠️ Shop system not available")
            return
        
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get owned items
        owned_item_ids = self.shop_system.get_purchased_items()
        owned_items = []
        
        for item_id in owned_item_ids:
            item = self.shop_system.get_item(item_id)
            if item:
                # Filter by category
                if self.current_category == "All" or self.matches_category(item):
                    owned_items.append(item)
        
        # Filter by search text
        search_text = self.search_input.text().strip().lower()
        if search_text:
            owned_items = [
                item for item in owned_items
                if search_text in item.name.lower() or search_text in item.description.lower()
            ]
        
        if not owned_items:
            self.status_label.setText("📭 No items in inventory. Visit the shop to buy items!")
            return
        
        # Add items to grid
        row, col = 0, 0
        for item in owned_items:
            widget = InventoryItemWidget(item)
            widget.item_selected.connect(self.item_selected.emit)
            self.grid_layout.addWidget(widget, row, col)
            
            col += 1
            if col >= 4:  # 4 columns
                col = 0
                row += 1
        
        self.status_label.setText(f"📦 {len(owned_items)} items owned")
        
    def matches_category(self, item: 'ShopItem') -> bool:
        """Check if item matches current category"""
        cat_map = {
            "Outfits": "PANDA_OUTFITS",
            "Clothes": "CLOTHES",
            "Hats": "HATS",
            "Shoes": "SHOES",
            "Accessories": "ACCESSORIES",
            "Fur Styles": "FUR_STYLES",
            "Fur Colors": "FUR_COLORS",
            "Toys": "TOYS",
            "Food": "FOOD",
            "Special": "SPECIAL"
        }
        
        target_cat = cat_map.get(self.current_category)
        if not target_cat:
            return True
        
        return item.category.name == target_cat
        
    def on_category_changed(self, category: str):
        """Handle category change"""
        self.current_category = category
        self.refresh_inventory()
        
    def filter_items(self, text: str):
        """Filter items by search text"""
        # Re-display inventory with search filter
        self.refresh_inventory()
    
    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager:
            tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tooltip:
                widget.setToolTip(tooltip)
