"""Closet item detail dialog — shown when user double-clicks a closet card."""
import logging

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    )
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QFont
    _PYQT = True
except (ImportError, OSError, RuntimeError):
    _PYQT = False

logger = logging.getLogger(__name__)

# Rarity colours — imported from closet_display_qt to avoid duplication.
try:
    from ui.closet_display_qt import _RARITY_COLORS
except (ImportError, OSError, RuntimeError):
    try:
        from closet_display_qt import _RARITY_COLORS  # type: ignore[no-redef]
    except (ImportError, OSError, RuntimeError):
        _RARITY_COLORS = {
            'common': '#aaaaaa', 'uncommon': '#55cc55',
            'rare': '#5599ff', 'epic': '#cc55ff', 'legendary': '#ffaa00',
        }


class ClosetItemDetailDialog:
    """Modal dialog with item details and an Equip button.

    Usage::

        dlg = ClosetItemDetailDialog(item_data, parent=self)
        if dlg.exec() and dlg.equip_requested:
            # item_data['id'] should be equipped
    """

    equip_requested: bool = False

    def __init__(self, item_data: dict, parent=None):
        self._dlg = None
        if not _PYQT:
            return

        unlocked = item_data.get('unlocked', True)
        equipped  = item_data.get('equipped',  False)
        rarity    = str(item_data.get('rarity', 'common')).lower()
        rarity_col = _RARITY_COLORS.get(rarity, '#9e9e9e')

        dlg = QDialog(parent)
        dlg.setWindowTitle(item_data.get('name', 'Item'))
        dlg.setFixedSize(QSize(320, 440))
        dlg.setStyleSheet(
            "QDialog { background:#1a1a2e; color:#e0e0e0; border-radius:8px; }"
            "QLabel  { color:#e0e0e0; }"
        )

        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Large emoji ───────────────────────────────────────────────────────
        icon_lbl = QLabel(item_data.get('emoji', '🎁'))
        icon_lbl.setFont(QFont("Segoe UI", 52))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        # ── Item name ─────────────────────────────────────────────────────────
        name_lbl = QLabel(item_data.get('name', ''))
        name_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color:#ffffff;")
        layout.addWidget(name_lbl)

        # ── Rarity badge ──────────────────────────────────────────────────────
        rar_lbl = QLabel(rarity.capitalize())
        rar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rar_lbl.setStyleSheet(
            f"color:{rarity_col}; font-weight:bold; font-size:11px;"
            f" border:1px solid {rarity_col}; border-radius:4px;"
            " padding:2px 8px; margin:0 60px;"
        )
        layout.addWidget(rar_lbl)

        # ── Description ───────────────────────────────────────────────────────
        desc = item_data.get('description', '')
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_lbl.setStyleSheet("color:#b0b0b0; font-size:11px;")
            layout.addWidget(desc_lbl)

        # ── Cost / status ─────────────────────────────────────────────────────
        if not unlocked:
            cost = item_data.get('cost', 0)
            cost_lbl = QLabel(f"🔒 Locked — costs 💰 {cost:,}")
            cost_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cost_lbl.setStyleSheet("color:#ffaa55; font-weight:bold;")
            layout.addWidget(cost_lbl)
        elif equipped:
            eq_lbl = QLabel("✅ Currently equipped")
            eq_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            eq_lbl.setStyleSheet("color:#4CAF50; font-weight:bold;")
            layout.addWidget(eq_lbl)

        layout.addStretch()

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()

        close_btn = QPushButton("✕ Close")
        close_btn.setStyleSheet(
            "background:#444; color:#ccc; padding:9px 20px;"
            " border-radius:6px; font-size:12px;"
        )
        close_btn.setToolTip("Close this detail view")
        close_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(close_btn)

        if unlocked and not equipped:
            equip_btn = QPushButton("👔 Equip")
            equip_btn.setStyleSheet(
                "background:#4CAF50; color:white; padding:9px 20px;"
                " border-radius:6px; font-size:12px; font-weight:bold;"
            )
            equip_btn.setToolTip("Equip this item on your panda")
            equip_btn.clicked.connect(lambda: (
                setattr(self, 'equip_requested', True),
                dlg.accept(),
            ))
            btn_row.addWidget(equip_btn)

        layout.addLayout(btn_row)

        self._dlg = dlg

    # ------------------------------------------------------------------
    def exec(self) -> int:
        try:
            return self._dlg.exec() if self._dlg else 0
        except (RuntimeError, AttributeError) as e:
            logger.debug(f"ClosetItemDetailDialog.exec: {e}")
            return 0
