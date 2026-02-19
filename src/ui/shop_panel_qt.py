"""
Shop Panel - Buy items for panda customization
Qt implementation of the shop system
"""

import logging
from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QGridLayout, QComboBox, QMessageBox,
        QLineEdit
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
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

logger = logging.getLogger(__name__)

# Try to import shop system
try:
    from features.shop_system import ShopSystem, ShopCategory, ShopItem
    from features.currency_system import CurrencySystem
    SHOP_AVAILABLE = True
except ImportError:
    try:
        from ..features.shop_system import ShopSystem, ShopCategory, ShopItem
        from ..features.currency_system import CurrencySystem
        SHOP_AVAILABLE = True
    except ImportError:
        logger.warning("Shop system not available")
        SHOP_AVAILABLE = False
        ShopSystem = None
        ShopCategory = None
        ShopItem = None
        CurrencySystem = None


class ShopItemWidget(QFrame):
    """Individual shop item display"""
    
    purchase_requested = pyqtSignal(str)  # item_id
    
    def __init__(self, item: 'ShopItem', owned: bool = False, parent=None):
        super().__init__(parent)
        self.item = item
        self.owned = owned
        self.setup_ui()
        
    def setup_ui(self):
        """Create the item UI"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                border: 2px solid #4CAF50;
                background-color: #ffffff;
            }
        """)
        
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
        
        # Price
        price_label = QLabel(f"💰 {self.item.price} Bamboo Bucks")
        price_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(price_label)
        
        # Buy button
        if self.owned:
            btn = QPushButton("✓ Owned")
            btn.setEnabled(False)
            btn.setStyleSheet("background-color: #888; color: white;")
        else:
            btn = QPushButton("🛒 Buy")
            btn.clicked.connect(lambda: self.purchase_requested.emit(self.item.id))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        layout.addWidget(btn)


class ShopPanelQt(QWidget):
    """Main shop panel for purchasing items"""
    
    item_purchased = pyqtSignal(str)  # item_id
    
    def __init__(self, shop_system: Optional['ShopSystem'] = None, 
                 currency_system: Optional['CurrencySystem'] = None,
                 parent=None, tooltip_manager=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 required for ShopPanelQt")
        
        super().__init__(parent)
        self.tooltip_manager = tooltip_manager
        
        # Initialize systems if not provided
        if SHOP_AVAILABLE:
            self.shop_system = shop_system or ShopSystem()
            self.currency_system = currency_system or CurrencySystem()
        else:
            self.shop_system = None
            self.currency_system = None
        
        self.current_category = "All"
        self.setup_ui()
        self.refresh_shop()
        
    def setup_ui(self):
        """Create the shop UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🛒 Panda Shop")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        # Currency display
        self.currency_label = QLabel("💰 0 Bamboo Bucks")
        self.currency_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.currency_label.setStyleSheet("color: #4CAF50; padding: 8px;")
        header.addWidget(self.currency_label)
        
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
        self.search_input.setPlaceholderText("Search items...")
        self.search_input.textChanged.connect(self.filter_items)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_shop)
        filter_layout.addWidget(refresh_btn)
        
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
        
    def refresh_shop(self):
        """Refresh shop items and currency display"""
        if not SHOP_AVAILABLE or not self.shop_system:
            self.status_label.setText("⚠️ Shop system not available")
            return
        
        # Update currency
        if self.currency_system:
            balance = self.currency_system.get_balance()
            self.currency_label.setText(f"💰 {balance} Bamboo Bucks")
        
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get items
        all_items = self.shop_system.get_available_items()
        owned_items = self.shop_system.get_purchased_items()
        
        # Filter by category
        if self.current_category != "All":
            all_items = [item for item in all_items if self.matches_category(item)]
        
        # Filter by search text
        search_text = self.search_input.text().strip().lower()
        if search_text:
            all_items = [
                item for item in all_items
                if search_text in item.name.lower() or search_text in item.description.lower()
            ]
        
        # Add items to grid
        row, col = 0, 0
        for item in all_items[:50]:  # Limit to 50 items
            owned = item.id in owned_items
            widget = ShopItemWidget(item, owned)
            widget.purchase_requested.connect(self.purchase_item)
            self.grid_layout.addWidget(widget, row, col)
            
            col += 1
            if col >= 4:  # 4 columns
                col = 0
                row += 1
        
        self.status_label.setText(f"📦 Showing {len(all_items)} items")
        
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
        self.refresh_shop()
        
    def filter_items(self, text: str):
        """Filter items by search text"""
        # Re-display items with search filter
        self.refresh_shop()
        
    def purchase_item(self, item_id: str):
        """Purchase an item"""
        if not SHOP_AVAILABLE or not self.shop_system or not self.currency_system:
            return
        
        # Get item
        item = self.shop_system.get_item(item_id)
        if not item:
            return
        
        # Check balance
        balance = self.currency_system.get_balance()
        if balance < item.price:
            QMessageBox.warning(
                self,
                "Insufficient Funds",
                f"You need {item.price} Bamboo Bucks but only have {balance}.\n\n"
                "Earn more by completing tasks!"
            )
            return
        
        # Confirm purchase
        reply = QMessageBox.question(
            self,
            "Confirm Purchase",
            f"Buy {item.name} for {item.price} Bamboo Bucks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Purchase
            success = self.shop_system.purchase_item(item_id)
            if success:
                self.currency_system.subtract('bamboo_bucks', item.price)
                QMessageBox.information(
                    self,
                    "Purchase Successful",
                    f"You bought {item.name}!\n\nCheck your closet to equip it."
                )
                self.item_purchased.emit(item_id)
                self.refresh_shop()
            else:
                QMessageBox.warning(
                    self,
                    "Purchase Failed",
                    "Could not complete purchase. Item may already be owned."
                )
    
    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager:
            tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tooltip:
                widget.setToolTip(tooltip)
