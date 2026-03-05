"""
Inventory Panel - View owned items
Qt implementation of inventory display
"""

import logging

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QGridLayout, QComboBox, QLineEdit,
        QApplication, QTabWidget,
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
    from PyQt6.QtGui import QFont, QDrag
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
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

logger = logging.getLogger(__name__)

# Try to import shop system
try:
    from features.shop_system import ShopSystem, ShopItem
    SHOP_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    try:
        from ..features.shop_system import ShopSystem, ShopItem
        SHOP_AVAILABLE = True
    except (ImportError, OSError, RuntimeError):
        logger.warning("Shop system not available for inventory")
        SHOP_AVAILABLE = False
        ShopSystem = None
        ShopItem = None


class InventoryItemWidget(QFrame):
    """Individual inventory item display"""
    
    item_selected = pyqtSignal(str)  # item_id
    
    # Category values whose items can be dragged to the panda
    _DRAGGABLE_CATEGORIES = {'food', 'toys', 'toy', 'food_item'}

    def __init__(self, item: 'ShopItem', parent=None):
        super().__init__(parent)
        self.item = item
        self._drag_start_pos: 'QPoint | None' = None
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
        """Handle click and record drag start position."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.item_selected.emit(self.item.id)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Start a QDrag when dragging a food or toy item."""
        if not PYQT_AVAILABLE:
            return
        if self._drag_start_pos is None:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        dist = (event.pos() - self._drag_start_pos).manhattanLength()
        if dist < QApplication.startDragDistance():
            return
        # Only drag food / toy items to the panda
        item_cat = str(getattr(self.item, 'category', '') or '').lower()
        if item_cat not in self._DRAGGABLE_CATEGORIES:
            return
        try:
            mime = QMimeData()
            mime.setText(f'panda_item:{self.item.id}:{item_cat}')
            drag = QDrag(self)
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)
        except Exception:
            pass
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


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
        """Create the backpack pocket inventory UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # ── Backpack header ────────────────────────────────────────────────────
        header = QHBoxLayout()
        icon_lbl = QLabel("🎒")
        icon_lbl.setFont(QFont("Segoe UI", 28))
        header.addWidget(icon_lbl)
        title = QLabel("Panda's Backpack")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_inventory)
        self._set_tooltip(refresh_btn, "Refresh the inventory display")
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # ── Search bar ─────────────────────────────────────────────────────────
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("🔍 Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search your items…")
        self.search_input.textChanged.connect(self.filter_items)
        self._set_tooltip(self.search_input, 'search_button')
        search_row.addWidget(self.search_input, stretch=1)
        layout.addLayout(search_row)

        # ── Pocket tab widget ──────────────────────────────────────────────────
        # Each tab represents a named "pocket" of the backpack.
        # The hidden category_combo remains for backward-compat with set_category_filter().
        self.category_combo = QComboBox()
        categories = ["All", "Outfits", "Clothes", "Hats", "Shoes", "Accessories",
                      "Fur Styles", "Hair Styles", "Fur Colors", "Weapons",
                      "Armor", "Boots", "Gloves", "Belt", "Backpack",
                      "Toys", "Food", "Special", "Sounds"]
        self.category_combo.addItems(categories)
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        self.category_combo.setVisible(False)  # hidden; driven by pocket tabs

        # Pocket definitions: (tab_label, matching_category_list)
        self._POCKETS = [
            ("🎒 All Items",     ["All"]),
            ("🍎 Food Pocket",   ["Food"]),
            ("🧸 Toy Pocket",    ["Toys"]),
            ("⚔️ Dungeon Pocket", ["Weapons", "Armor", "Boots", "Gloves", "Belt"]),
            ("👗 Closet Pocket", ["Outfits", "Clothes", "Hats", "Shoes",
                                  "Accessories", "Fur Styles", "Hair Styles",
                                  "Fur Colors"]),
            ("🎵 Extras",        ["Special", "Sounds", "Backpack"]),
        ]

        self.pocket_tabs = QTabWidget()
        self.pocket_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.pocket_tabs.setStyleSheet(
            "QTabBar::tab { min-width: 90px; padding: 5px 8px; }"
        )
        # Each tab gets a scroll+grid area for its items
        self._pocket_grids: dict[int, QGridLayout] = {}
        self._pocket_status: dict[int, QLabel] = {}
        for i, (tab_label, _cats) in enumerate(self._POCKETS):
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(4, 4, 4, 4)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.Shape.NoFrame)
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setSpacing(8)
            scroll.setWidget(grid_widget)
            page_layout.addWidget(scroll, stretch=1)
            status = QLabel("")
            status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_layout.addWidget(status)
            self._pocket_grids[i] = grid
            self._pocket_status[i] = status
            self.pocket_tabs.addTab(page, tab_label)

        self.pocket_tabs.currentChanged.connect(self._on_pocket_changed)
        layout.addWidget(self.pocket_tabs, stretch=1)

        # Legacy: grid_layout points at the active pocket grid (for compat)
        self.grid_widget = self.pocket_tabs.widget(0)
        self.grid_layout = self._pocket_grids[0]
        self.status_label = self._pocket_status[0]
        
    def _on_pocket_changed(self, idx: int) -> None:
        """Update grid_layout / status_label aliases when the pocket tab changes."""
        self.grid_layout = self._pocket_grids.get(idx, self.grid_layout)
        self.status_label = self._pocket_status.get(idx, self.status_label)

    def _pocket_for_category(self, category_label: str) -> int:
        """Return the pocket tab index that covers *category_label*."""
        for i, (_tab, cats) in enumerate(self._POCKETS):
            if category_label in cats or category_label == 'All' and i == 0:
                return i
        return 0  # default to All Items

    def refresh_inventory(self):
        """Refresh all pocket grids from the shop system."""
        if not SHOP_AVAILABLE or not self.shop_system:
            for status in self._pocket_status.values():
                status.setText("⚠️ Shop system not available")
            return

        # Get all owned items once
        owned_item_ids = self.shop_system.get_purchased_items()
        all_items: list = []
        for item_id in owned_item_ids:
            item = self.shop_system.get_item(item_id)
            if item:
                all_items.append(item)

        # Apply search filter
        search_text = self.search_input.text().strip().lower()

        # Populate each pocket grid
        for pocket_idx, (_tab_label, pocket_cats) in enumerate(self._POCKETS):
            grid = self._pocket_grids[pocket_idx]
            status = self._pocket_status[pocket_idx]

            # Clear existing widgets
            while grid.count():
                it = grid.takeAt(0)
                if it.widget():
                    it.widget().deleteLater()

            if 'All' in pocket_cats:
                pocket_items = all_items[:]
            else:
                pocket_items = [
                    it for it in all_items
                    if any(self._item_matches_cat_label(it, c) for c in pocket_cats)
                ]

            if search_text:
                pocket_items = [
                    it for it in pocket_items
                    if search_text in it.name.lower() or search_text in it.description.lower()
                ]

            if not pocket_items:
                status.setText("📭 No items in this pocket. Visit the shop!")
                continue

            row, col = 0, 0
            for item in pocket_items:
                widget = InventoryItemWidget(item)
                widget.item_selected.connect(self.item_selected.emit)
                grid.addWidget(widget, row, col)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1

            status.setText(f"📦 {len(pocket_items)} item(s)")
        
    def _item_matches_cat_label(self, item: 'ShopItem', cat_label: str) -> bool:
        """Check if item belongs to the given category label."""
        cat_map = {
            "Outfits": "PANDA_OUTFITS",
            "Clothes": "CLOTHES",
            "Hats": "HATS",
            "Shoes": "SHOES",
            "Accessories": "ACCESSORIES",
            "Fur Styles": "FUR_STYLES",
            "Hair Styles": "HAIRSTYLES",
            "Fur Colors": "FUR_COLORS",
            "Weapons": "WEAPONS",
            "Armor": "ARMOR",
            "Boots": "BOOTS",
            "Gloves": "GLOVES",
            "Belt": "BELT",
            "Backpack": "BACKPACK",
            "Toys": "TOYS",
            "Food": "FOOD",
            "Special": "SPECIAL",
            "Sounds": "SOUNDS",
        }
        target = cat_map.get(cat_label)
        if not target:
            return True
        if item.category is None:
            return False
        return item.category.name == target

    def matches_category(self, item: 'ShopItem') -> bool:
        """Legacy: check if item matches current_category (kept for backward compat)."""
        return self._item_matches_cat_label(item, self.current_category)
        
    def on_category_changed(self, category: str):
        """Handle category change — switch to the matching pocket tab."""
        self.current_category = category
        pocket_idx = self._pocket_for_category(category)
        if hasattr(self, 'pocket_tabs') and self.pocket_tabs.currentIndex() != pocket_idx:
            self.pocket_tabs.setCurrentIndex(pocket_idx)
        self.refresh_inventory()

    def set_category_filter(self, category_label: str) -> None:
        """Public API: select a category by its combo label text.

        Args:
            category_label: One of the combo items ('All', 'Clothes', 'Weapons', …)
        """
        # Update hidden combo for legacy callers
        if hasattr(self, 'category_combo'):
            idx = self.category_combo.findText(category_label)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            else:
                self.category_combo.setCurrentIndex(0)
        # Switch to the matching pocket tab
        pocket_idx = self._pocket_for_category(category_label)
        if hasattr(self, 'pocket_tabs'):
            self.pocket_tabs.setCurrentIndex(pocket_idx)
        self.current_category = category_label
        self.refresh_inventory()

    def filter_items(self, text: str):
        """Filter items by search text"""
        # Re-display inventory with search filter
        self.refresh_inventory()
    
    def _set_tooltip(self, widget, widget_id_or_text: str):
        """Set tooltip via manager (cycling) when available, else plain text."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'register'):
            if ' ' not in widget_id_or_text:
                try:
                    tip = self.tooltip_manager.get_tooltip(widget_id_or_text)
                    if tip:
                        widget.setToolTip(tip)
                        self.tooltip_manager.register(widget, widget_id_or_text)
                        return
                except Exception:
                    pass
        widget.setToolTip(str(widget_id_or_text))
