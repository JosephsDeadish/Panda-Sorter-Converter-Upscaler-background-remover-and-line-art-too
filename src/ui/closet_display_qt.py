"""
PyQt6 Closet Display System
Replaces canvas-based clothing display with Qt widgets
"""

try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                                 QLabel, QPushButton, QGridLayout, QFrame,
                                 QLineEdit, QComboBox, QSizePolicy, QToolTip)
    from PyQt6.QtCore import Qt, pyqtSignal, QSize
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
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
        class MouseButton:
            LeftButton = 1
        class ScrollBarPolicy:
            ScrollBarAlwaysOff = 1

# Maps category value string → display label shown in the combo box
_CATEGORY_LABELS = {
    'all':         '🗂️ All',
    'fur_style':   '🐼 Fur Styles',
    'fur_color':   '🎨 Fur Colours',
    'hair_style':  '💇 Hair Styles',
    'hat':         '🎩 Hats',
    'clothing':    '👕 Clothing',
    'shoes':       '👟 Shoes',
    'accessory':   '💎 Accessories',
    'gloves':      '🧤 Gloves',
    'armor':       '🛡️ Armor',
    'boots':       '🥾 Boots',
    'belt':        '🔗 Belts',
    'backpack':    '🎒 Backpacks',
    'weapon':      '⚔️ Weapons',
    'toy':         '🧸 Toys',
    'food':        '🍎 Food',
}

_RARITY_COLORS = {
    'common':    '#aaaaaa',
    'uncommon':  '#55cc55',
    'rare':      '#5599ff',
    'epic':      '#cc55ff',
    'legendary': '#ffaa00',
}


class ClothingItemWidget(QFrame):
    """Individual clothing item card: emoji, name, rarity badge, lock overlay."""

    clicked = pyqtSignal(dict)

    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self._setup_ui()

    def _setup_ui(self):
        unlocked = self.item_data.get('unlocked', True)
        equipped  = self.item_data.get('equipped',  False)
        rarity    = self.item_data.get('rarity', 'common')
        rarity_col = _RARITY_COLORS.get(str(rarity).lower(), '#aaaaaa')

        self.setFixedSize(QSize(90, 110))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Frame style — highlight equipped items, dim locked items
        if equipped:
            self.setStyleSheet(
                f"QFrame {{ border: 2px solid #ffdd55; background: #2a2a1e; border-radius: 6px; }}"
            )
        elif unlocked:
            self.setStyleSheet(
                f"QFrame {{ border: 2px solid {rarity_col}; background: #1e1e2e; border-radius: 6px; }}"
            )
        else:
            self.setStyleSheet(
                "QFrame { border: 1px solid #444; background: #111118; border-radius: 6px; }"
            )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Emoji icon
        icon_label = QLabel(self.item_data.get('emoji', '❓'))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 26pt; background: transparent; border: none;")
        if not unlocked:
            icon_label.setText('🔒')
        layout.addWidget(icon_label)

        # Name
        name = self.item_data.get('name', 'Unknown')
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(
            f"color: {'#ffdd55' if equipped else ('#cccccc' if unlocked else '#555555')};"
            "font-size: 8pt; background: transparent; border: none;"
        )
        layout.addWidget(name_label)

        # Rarity badge
        rarity_label = QLabel(rarity.capitalize() if unlocked else 'Locked')
        rarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rarity_label.setStyleSheet(
            f"color: {rarity_col if unlocked else '#444444'}; font-size: 7pt;"
            "background: transparent; border: none;"
        )
        layout.addWidget(rarity_label)

        # Tooltip: description + cost if locked
        desc = self.item_data.get('description', '')
        cost = self.item_data.get('cost', 0)
        tip = f"<b>{name}</b>"
        if desc:
            tip += f"<br>{desc}"
        if not unlocked and cost:
            tip += f"<br><i>Cost: {cost} 🪙</i>"
        if equipped:
            tip += "<br><b>✅ Equipped</b>"
        self.setToolTip(tip)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item_data)
        super().mousePressEvent(event)


class ClosetDisplayWidget(QWidget):
    """Complete closet display with category filter, search, lock/unlock badges."""

    item_equipped = pyqtSignal(dict)

    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        self.items: list = []
        self._active_category = 'all'
        self.tooltip_manager = tooltip_manager
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # ── Top bar: category combo + search ─────────────────────────────────
        top_bar = QHBoxLayout()

        self._cat_combo = QComboBox()
        for val, label in _CATEGORY_LABELS.items():
            self._cat_combo.addItem(label, val)
        self._cat_combo.currentIndexChanged.connect(self._on_category_changed)
        top_bar.addWidget(self._cat_combo)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search items…")
        self._search_input.textChanged.connect(self._apply_filters)
        top_bar.addWidget(self._search_input)

        main_layout.addLayout(top_bar)

        # ── Item count label ──────────────────────────────────────────────────
        self._count_label = QLabel("0 items")
        self._count_label.setStyleSheet("color: #888888; font-size: 8pt;")
        main_layout.addWidget(self._count_label)

        # ── Scroll area with item grid ────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(6)
        scroll.setWidget(self._grid_widget)
        main_layout.addWidget(scroll, 1)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_clothing_items(self, items: list):
        """Load a list of item dicts and refresh the display."""
        self.items = list(items)
        self._apply_filters()

    def set_category_filter(self, category_value: str):
        """Programmatically select a category (used by bedroom furniture wiring)."""
        for i in range(self._cat_combo.count()):
            if self._cat_combo.itemData(i) == category_value:
                self._cat_combo.setCurrentIndex(i)
                return
        # Unknown value — show All
        self._cat_combo.setCurrentIndex(0)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_category_changed(self, _idx: int):
        self._active_category = self._cat_combo.currentData() or 'all'
        self._apply_filters()

    def _apply_filters(self):
        cat   = self._active_category
        text  = self._search_input.text().lower()
        result = []
        for item in self.items:
            if cat != 'all' and item.get('category') != cat:
                continue
            if text and text not in item.get('name', '').lower():
                continue
            result.append(item)
        self._display_items(result)

    def _display_items(self, items: list):
        # Remove old widgets
        while self._grid_layout.count():
            w = self._grid_layout.takeAt(0)
            if w.widget():
                w.widget().deleteLater()

        cols = 4
        for idx, item_data in enumerate(items):
            widget = ClothingItemWidget(item_data)
            widget.clicked.connect(self._on_item_clicked)
            self._grid_layout.addWidget(widget, idx // cols, idx % cols)

        self._count_label.setText(f"{len(items)} item{'s' if len(items) != 1 else ''}")

    def _on_item_clicked(self, item_data: dict):
        self.item_equipped.emit(item_data)

    # Kept for legacy callers
    def load_clothing_items_legacy(self, items):
        self.load_clothing_items(items)

    def filter_by_category(self, category: str):
        """Legacy string filter (old callers use this)."""
        self.set_category_filter(category.lower().replace(' ', '_').replace('é', 'e'))

    def _set_tooltip(self, widget, tooltip_key: str):
        if self.tooltip_manager:
            tip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tip:
                widget.setToolTip(tip)


def create_closet_display(parent=None, tooltip_manager=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return ClosetDisplayWidget(parent, tooltip_manager)


# Alias for callers that use the Qt-suffixed name (e.g. qt_panel_loader.py)
ClosetDisplayQt = ClosetDisplayWidget
