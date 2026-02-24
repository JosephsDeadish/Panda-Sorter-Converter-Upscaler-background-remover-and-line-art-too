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
        class CursorShape:
            PointingHandCursor = 0

logger = logging.getLogger(__name__)

# Try to import shop system
try:
    from features.shop_system import ShopSystem, ShopCategory, ShopItem
    from features.currency_system import CurrencySystem
    SHOP_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    try:
        from ..features.shop_system import ShopSystem, ShopCategory, ShopItem
        from ..features.currency_system import CurrencySystem
        SHOP_AVAILABLE = True
    except (ImportError, OSError, RuntimeError):
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
        """Create the item card UI — turquoise Livy theme."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        # Rarity border colour
        rarity = getattr(getattr(self.item, 'rarity', None), 'value', 'common')
        _rarity_border = {
            'common': '#B0E0E0', 'uncommon': '#2ECC71', 'rare': '#3498DB',
            'epic': '#9B59B6', 'legendary': '#F39C12',
        }.get(str(rarity).lower(), '#B0E0E0')
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {_rarity_border};
                border-radius: 12px;
                padding: 8px;
            }}
            QFrame:hover {{
                border: 2px solid #0BBFBF;
                background: #F0FAFA;
            }}
        """)
        self.setFixedSize(148, 190)

        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(6, 6, 6, 6)

        # Icon
        icon_label = QLabel(getattr(self.item, 'icon', '🎁'))
        icon_label.setFont(QFont("Segoe UI Emoji", 28))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Name
        name_label = QLabel(getattr(self.item, 'name', ''))
        name_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("color: #063040;")
        layout.addWidget(name_label)

        # Price
        price = getattr(self.item, 'price', 0)
        price_label = QLabel("✅ Owned" if self.owned else f"💰 {price:,}")
        price_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("color: #089898;" if self.owned else "color: #B8860B;")
        layout.addWidget(price_label)

        layout.addStretch()

        # Buy / owned button
        if self.owned:
            btn = QPushButton("✓ Owned")
            btn.setEnabled(False)
            btn.setStyleSheet(
                "background: #D0EEEE; color: #089898; border: none;"
                " border-radius: 8px; padding: 5px; font-weight: bold; font-size: 11px;"
            )
        else:
            btn = QPushButton("🛒 Buy")
            btn.clicked.connect(lambda: self.purchase_requested.emit(self.item.id))
            btn.setStyleSheet(
                "background: #0BBFBF; color: white; border: none;"
                " border-radius: 8px; padding: 5px;"
                " font-weight: bold; font-size: 11px;"
                " QPushButton:hover { background: #089898; }"
            )
        layout.addWidget(btn)

    def mouseDoubleClickEvent(self, event):  # type: ignore[override]
        """Open item detail dialog on double-click."""
        try:
            dlg = ItemDetailDialog(self.item, self.owned, parent=self.window())
            dlg.exec()
            if getattr(dlg, 'buy_requested', False) and not self.owned:
                self.purchase_requested.emit(self.item.id)
        except (ImportError, AttributeError, RuntimeError) as _e:
            logger.debug(f"ShopItemWidget double-click dialog: {_e}")
        super().mouseDoubleClickEvent(event)


class ItemDetailDialog:
    """Modal dialog showing full item details with buy/equip button."""

    def __init__(self, item, owned: bool, parent=None):
        if not PYQT_AVAILABLE:
            return
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox  # type: ignore
        from PyQt6.QtCore import QSize  # type: ignore

        dlg = QDialog(parent)
        dlg.setWindowTitle(item.name)
        dlg.setFixedSize(QSize(320, 420))
        dlg.setStyleSheet("QDialog { background: #1a1a2e; color: #e0e0e0; }")

        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Large icon
        icon_lbl = QLabel(getattr(item, 'icon', '🎁'))
        icon_lbl.setFont(QFont("Segoe UI", 48))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        # Name
        name_lbl = QLabel(item.name)
        name_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color: #ffffff;")
        layout.addWidget(name_lbl)

        # Rarity badge
        rarity = getattr(item, 'rarity', None)
        if rarity is not None:
            rarity_str = rarity.name if hasattr(rarity, 'name') else str(rarity)
            try:
                from ui.closet_display_qt import _RARITY_COLORS as _RC
            except (ImportError, OSError, RuntimeError):
                _RC = {'common': '#aaaaaa', 'uncommon': '#55cc55',
                       'rare': '#5599ff', 'epic': '#cc55ff', 'legendary': '#ffaa00'}
            col = _RC.get(rarity_str.lower(), '#9e9e9e')
            rar_lbl = QLabel(rarity_str.capitalize())
            rar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rar_lbl.setStyleSheet(
                f"color: {col}; font-weight: bold; font-size: 11px;"
                " border: 1px solid; border-radius: 4px; padding: 2px 8px;"
                f" border-color: {col};"
            )
            layout.addWidget(rar_lbl)

        # Description
        desc = QLabel(getattr(item, 'description', ''))
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        layout.addWidget(desc)

        # Price
        price_lbl = QLabel(
            "✅ Owned" if owned else f"💰 {getattr(item, 'price', 0):,} Bamboo Bucks"
        )
        price_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_lbl.setStyleSheet("color: #4CAF50;" if owned else "color: #FFD700;")
        layout.addWidget(price_lbl)

        layout.addStretch()

        # Action button
        if owned:
            btn = QPushButton("✓ Owned")
            btn.setEnabled(False)
            btn.setStyleSheet(
                "background:#555; color:#aaa; padding:10px; border-radius:6px;"
            )
        else:
            btn = QPushButton("🛒 Buy")
            btn.setStyleSheet(
                "background:#4CAF50; color:white; padding:10px;"
                " border-radius:6px; font-weight:bold; font-size:13px;"
            )
            btn.clicked.connect(lambda: (
                setattr(self, 'buy_requested', True),
                dlg.accept(),
            ))
        layout.addWidget(btn)

        self._dlg = dlg

    def exec(self):
        try:
            return self._dlg.exec()
        except (RuntimeError, AttributeError) as e:
            logger.debug(f"ItemDetailDialog.exec: {e}")
            return 0


class ShopPanelQt(QWidget):
    """Main shop panel for purchasing items."""

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

    # ─────────────────────────── Turquoise colour palette ────────────────────
    _TURQ      = "#0BBFBF"    # Livy's signature turquoise
    _TURQ_D    = "#089898"    # darker turquoise for accents
    _TURQ_L    = "#E0FAFA"    # very light turquoise background
    _TURQ_HDR  = "#063040"    # deep cosmic header background
    _STAR_GOLD = "#FFD700"    # gold stars

    _SHOP_STYLESHEET = f"""
        QWidget {{
            background: #F0FAFA;
        }}
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background: #D0EEEE;
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: #0BBFBF;
            border-radius: 4px;
        }}
        QComboBox {{
            background: white;
            border: 2px solid #0BBFBF;
            border-radius: 10px;
            padding: 4px 10px;
            color: #063040;
            font-weight: bold;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QLineEdit {{
            background: white;
            border: 2px solid #0BBFBF;
            border-radius: 10px;
            padding: 4px 10px;
            color: #063040;
        }}
    """

    def setup_ui(self):
        """Create the Cosmic Otter Supply Co. shop UI — Livy's turquoise world."""
        self.setStyleSheet(self._SHOP_STYLESHEET)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Banner header ─────────────────────────────────────────────────────
        banner = QWidget()
        banner.setFixedHeight(90)
        banner.setStyleSheet(f"background: {self._TURQ_HDR}; border-radius: 0px;")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(18, 8, 18, 8)

        # Otter avatar (emoji + name)
        otter_col = QVBoxLayout()
        livy_name = QLabel("🦦  Livy's")
        livy_name.setStyleSheet(f"color: {self._TURQ}; font-size: 18px; font-weight: bold;")
        shop_name_lbl = QLabel("Cosmic Otter Supply Co. ✨")
        shop_name_lbl.setStyleSheet(f"color: {self._STAR_GOLD}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")
        tagline = QLabel("Galactic Goods for Adventurous Pandas 🌌")
        tagline.setStyleSheet("color: #90E0E0; font-size: 10px; font-style: italic;")
        otter_col.addWidget(livy_name)
        otter_col.addWidget(shop_name_lbl)
        otter_col.addWidget(tagline)
        banner_layout.addLayout(otter_col)

        banner_layout.addStretch()

        # Coin display
        coin_col = QVBoxLayout()
        coin_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.currency_label = QLabel("💰 0 Bamboo Bucks")
        self.currency_label.setStyleSheet(
            f"color: {self._STAR_GOLD}; font-size: 14px; font-weight: bold;"
            " background: rgba(255,215,0,0.12); border-radius: 10px; padding: 6px 14px;"
        )
        self.currency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coin_col.addWidget(self.currency_label)
        banner_layout.addLayout(coin_col)

        layout.addWidget(banner)

        # ── Search + filter bar ───────────────────────────────────────────────
        filter_bar = QWidget()
        filter_bar.setStyleSheet(f"background: {self._TURQ_D}; padding: 6px;")
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(12, 4, 12, 4)
        filter_layout.setSpacing(8)

        search_lbl = QLabel("🔍")
        search_lbl.setStyleSheet("color: white; font-size: 14px;")
        filter_layout.addWidget(search_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Livy's shelves…")
        self.search_input.setFixedHeight(30)
        self.search_input.textChanged.connect(self.filter_items)
        self.search_input.setStyleSheet(
            "background: white; border: none; border-radius: 8px;"
            " padding: 2px 8px; color: #063040;"
        )
        filter_layout.addWidget(self.search_input, 1)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 30)
        refresh_btn.setToolTip("Refresh shop")
        refresh_btn.setStyleSheet(
            f"background: {self._TURQ}; color: white; border: none;"
            " border-radius: 8px; font-size: 14px; font-weight: bold;"
        )
        refresh_btn.clicked.connect(self.refresh_shop)
        filter_layout.addWidget(refresh_btn)

        layout.addWidget(filter_bar)

        # ── Category pills ────────────────────────────────────────────────────
        cat_scroll = QScrollArea()
        cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cat_scroll.setFixedHeight(46)
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cat_scroll.setStyleSheet(f"background: {self._TURQ_L}; border: none;")

        cat_widget = QWidget()
        cat_widget.setStyleSheet(f"background: {self._TURQ_L};")
        cat_row = QHBoxLayout(cat_widget)
        cat_row.setContentsMargins(8, 4, 8, 4)
        cat_row.setSpacing(6)

        self._cat_buttons: list = []
        _categories = [
            ("⭐ All", "All"), ("👗 Outfits", "Outfits"), ("👕 Clothes", "Clothes"),
            ("🎩 Hats", "Hats"), ("👟 Shoes", "Shoes"), ("💎 Accessories", "Accessories"),
            ("🐾 Fur", "Fur Styles"), ("🎨 Colours", "Fur Colors"),
            ("💇 Hair", "Hair Styles"), ("⚔️ Weapons", "Weapons"),
            ("🛡️ Armor", "Armor"), ("👢 Boots", "Boots"), ("🧤 Gloves", "Gloves"),
            ("🔗 Belt", "Belt"), ("🎒 Backpack", "Backpack"),
            ("🧸 Toys", "Toys"), ("🍎 Food", "Food"), ("✨ Special", "Special"),
        ]
        for label, cat_id in _categories:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(30)
            btn.setStyleSheet(self._pill_style(active=(cat_id == "All")))
            btn.clicked.connect(lambda checked, c=cat_id: self._on_cat_pill(c))
            btn.setProperty("cat_id", cat_id)
            cat_row.addWidget(btn)
            self._cat_buttons.append(btn)
        cat_row.addStretch()
        cat_scroll.setWidget(cat_widget)
        layout.addWidget(cat_scroll)

        # ── Items scroll grid ─────────────────────────────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area, 1)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(24)
        self.status_label.setStyleSheet(
            f"background: {self._TURQ_HDR}; color: {self._TURQ};"
            " font-size: 11px; padding: 0 8px;"
        )
        layout.addWidget(self.status_label)

    def _pill_style(self, active: bool = False) -> str:
        if active:
            return (
                f"QPushButton {{ background: {self._TURQ}; color: white;"
                " border: none; border-radius: 13px; padding: 4px 12px;"
                " font-size: 11px; font-weight: bold; }}"
            )
        return (
            f"QPushButton {{ background: white; color: {self._TURQ_D};"
            f" border: 2px solid {self._TURQ}; border-radius: 13px; padding: 3px 12px;"
            " font-size: 11px; }}"
            f"QPushButton:hover {{ background: {self._TURQ_L}; }}"
        )

    def _on_cat_pill(self, cat_id: str) -> None:
        self.current_category = cat_id
        for btn in self._cat_buttons:
            btn.setStyleSheet(self._pill_style(active=(btn.property("cat_id") == cat_id)))
        self.refresh_shop()

    def refresh_shop(self):
        """Refresh shop items and currency display."""
        if not SHOP_AVAILABLE or not self.shop_system:
            self.status_label.setText("⚠️ Livy's shelves are empty right now…")
            return

        # Update currency
        if self.currency_system:
            try:
                balance = self.currency_system.get_balance()
                self.currency_label.setText(f"💰 {balance:,} Bamboo Bucks")
            except Exception:
                pass

        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get + filter items
        all_items = self.shop_system.get_available_items()
        owned_items = self.shop_system.get_purchased_items()

        if self.current_category != "All":
            all_items = [i for i in all_items if self.matches_category(i)]

        search_text = self.search_input.text().strip().lower()
        if search_text:
            all_items = [
                i for i in all_items
                if search_text in getattr(i, 'name', '').lower()
                   or search_text in getattr(i, 'description', '').lower()
            ]

        # Populate grid (3 columns)
        row, col = 0, 0
        for item in all_items[:60]:
            owned = item.id in owned_items
            widget = ShopItemWidget(item, owned)
            widget.purchase_requested.connect(self.purchase_item)
            self.grid_layout.addWidget(widget, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        self.status_label.setText(
            f"✨ {len(all_items)} items from across the galaxy  •  Livy says: Happy shopping! 🦦"
        )

    def matches_category(self, item: 'ShopItem') -> bool:
        """Check if item matches current category."""
        cat_map = {
            "Outfits":     "PANDA_OUTFITS",
            "Clothes":     "CLOTHES",
            "Hats":        "HATS",
            "Shoes":       "SHOES",
            "Accessories": "ACCESSORIES",
            "Fur Styles":  "FUR_STYLES",
            "Fur Colors":  "FUR_COLORS",
            "Hair Styles": "HAIRSTYLES",
            "Weapons":     "WEAPONS",
            "Armor":       "ARMOR",
            "Boots":       "BOOTS",
            "Gloves":      "GLOVES",
            "Belt":        "BELT",
            "Backpack":    "BACKPACK",
            "Toys":        "TOYS",
            "Food":        "FOOD",
            "Special":     "SPECIAL",
        }
        target_cat = cat_map.get(self.current_category)
        if not target_cat:
            return True
        return getattr(getattr(item, 'category', None), 'name', '') == target_cat

    def on_category_changed(self, category: str):
        self.current_category = category
        self.refresh_shop()

    def filter_items(self, text: str):
        self.refresh_shop()
        
    def purchase_item(self, item_id: str):
        """Purchase an item — Livy confirms the sale!"""
        if not SHOP_AVAILABLE or not self.shop_system or not self.currency_system:
            return
        item = self.shop_system.get_item(item_id)
        if not item:
            return

        balance = self.currency_system.get_balance()
        price   = getattr(item, 'price', 0)
        name    = getattr(item, 'name', item_id)
        icon    = getattr(item, 'icon', '🎁')

        if balance < price:
            QMessageBox.warning(
                self,
                "💸 Livy says: Not enough Bamboo Bucks!",
                f"{icon} {name} costs {price:,} Bamboo Bucks.\n"
                f"You have {balance:,} — earn more by completing tasks! 🌟"
            )
            return

        reply = QMessageBox.question(
            self,
            "🦦 Livy's Checkout",
            f"Buy {icon} {name}\nfor 💰 {price:,} Bamboo Bucks?\n\n"
            "Livy happily wraps it up for you! 🎀",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg, _ = self.shop_system.purchase_item(item_id, balance, level=0)
            if success:
                try:
                    self.currency_system.subtract('bamboo_bucks', price)
                except Exception:
                    pass
                QMessageBox.information(
                    self,
                    "✨ Purchase Complete!",
                    f"Livy hands you {icon} {name}!\n\n"
                    "Check your closet or backpack to equip it. 🎒"
                )
                self.item_purchased.emit(item_id)
                self.refresh_shop()
            else:
                QMessageBox.warning(
                    self,
                    "⚠️ Oops!",
                    msg or "Something went wrong — Livy will investigate! 🔍"
                )
    
    def update_coin_display(self, balance: int) -> None:
        """Update the coin balance label (called by main.py after purchase/earn)."""
        try:
            self.currency_label.setText(f"💰 {balance:,} Bamboo Bucks")
        except Exception:
            pass

    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager:
            tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tooltip:
                widget.setToolTip(tooltip)
