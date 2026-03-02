"""
Achievement Display Panel - Trophy Shelf
Achievements displayed as trophies on a wooden bookshelf.
Locked trophies appear greyed-out / translucent; achievement info
is "carved" on a small wooden plaque in front of each trophy.
"""

import logging

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QGridLayout, QProgressBar, QComboBox,
        QSizePolicy, QLineEdit,
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object

logger = logging.getLogger(__name__)

# Try to import achievement system
try:
    from features.achievements import AchievementSystem, Achievement, AchievementTier
    ACHIEVEMENTS_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    try:
        from ..features.achievements import AchievementSystem, Achievement, AchievementTier
        ACHIEVEMENTS_AVAILABLE = True
    except (ImportError, OSError, RuntimeError):
        logger.warning("Achievement system not available")
        ACHIEVEMENTS_AVAILABLE = False
        AchievementSystem = None
        Achievement = None
        AchievementTier = None


# ── Tier colour palette for trophies ──────────────────────────────────────────
_TIER_COLOURS = {
    'bronze':    ('#cd7f32', '#a0522d', '#ffd39b'),
    'silver':    ('#a8a9ad', '#808080', '#e8e8e8'),
    'gold':      ('#ffd700', '#c8a800', '#fffacd'),
    'platinum':  ('#e5e4e2', '#9c9c9c', '#ffffff'),
    'legendary': ('#9b59b6', '#6c3483', '#f5eafb'),
}
_DEFAULT_TIER = ('#888', '#555', '#ddd')

# Wooden shelf / plaque colours
_SHELF_BG       = '#2d1a0e'      # dark walnut
_SHELF_EDGE     = '#5c3317'      # lighter grain
_PLAQUE_BG      = '#8b6914'      # burnished oak
_PLAQUE_BORDER  = '#5c4200'      # dark oak edge
_PLAQUE_TEXT    = '#ffe8b0'      # carved lettering colour


class TrophyWidget(QWidget):
    """Single trophy on the shelf — icon + carved plaque beneath it."""

    def __init__(self, achievement: 'Achievement', parent=None):
        super().__init__(parent)
        self.achievement = achievement
        self._build()

    def _tier_colours(self):
        if self.achievement is None:
            return _DEFAULT_TIER
        tier_name = getattr(
            getattr(self.achievement, 'tier', None), 'value', 'bronze'
        ) or 'bronze'
        return _TIER_COLOURS.get(tier_name.lower(), _DEFAULT_TIER)

    def _build(self):
        ach = self.achievement
        unlocked = getattr(ach, 'unlocked', False)
        hidden   = getattr(ach, 'hidden',   False)

        primary, shadow, glow = self._tier_colours()

        # Container: fixed width so the shelf grid stays uniform
        self.setFixedWidth(136)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 6, 4, 4)
        outer.setSpacing(0)

        # ── Trophy area ────────────────────────────────────────────────────
        trophy_frame = QFrame()
        trophy_frame.setFixedHeight(96)

        if unlocked:
            trophy_frame.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {glow}, stop:1 {primary});
                    border: 2px solid {shadow};
                    border-radius: 10px;
                }}
            """)
        else:
            # Locked — greyed out, partially translucent look via dull colours
            trophy_frame.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #4a4a4a, stop:1 #2a2a2a);
                    border: 2px solid #333;
                    border-radius: 10px;
                }
            """)

        t_inner = QVBoxLayout(trophy_frame)
        t_inner.setContentsMargins(4, 4, 4, 4)
        t_inner.setSpacing(2)

        # Trophy icon (emoji)
        icon_lbl = QLabel(getattr(ach, 'icon', '🏆'))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont("Segoe UI Emoji", 32)
        icon_lbl.setFont(icon_font)
        if not unlocked:
            icon_lbl.setStyleSheet("color: rgba(200,200,200,80);")
        t_inner.addWidget(icon_lbl)

        # Unlocked check or lock overlay
        status_lbl = QLabel("✓ Unlocked" if unlocked else "🔒")
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont("Segoe UI", 8, QFont.Weight.Bold if unlocked else QFont.Weight.Normal)
        status_lbl.setFont(status_font)
        if unlocked:
            status_lbl.setStyleSheet(f"color: {shadow}; font-weight: bold;")
        else:
            status_lbl.setStyleSheet("color: #666; font-size: 16px;")
        t_inner.addWidget(status_lbl)

        outer.addWidget(trophy_frame)

        # ── Wooden plaque (carved info) ────────────────────────────────────
        plaque = QFrame()
        plaque.setStyleSheet(f"""
            QFrame {{
                background: {_PLAQUE_BG};
                border: 2px solid {_PLAQUE_BORDER};
                border-radius: 4px;
                margin-top: 2px;
            }}
        """)
        p_inner = QVBoxLayout(plaque)
        p_inner.setContentsMargins(4, 3, 4, 3)
        p_inner.setSpacing(1)

        # Achievement name (carved on plaque)
        name_lbl = QLabel(getattr(ach, 'name', 'Unknown'))
        name_lbl.setWordWrap(True)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        name_lbl.setFont(name_font)
        name_lbl.setStyleSheet(f"color: {_PLAQUE_TEXT};")
        p_inner.addWidget(name_lbl)

        # Description or hint
        if unlocked or not hidden:
            desc = getattr(ach, 'description', '')
        else:
            desc = "Hidden — keep exploring to discover this trophy"
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_font = QFont("Segoe UI", 6)
        desc_lbl.setFont(desc_font)
        locked_colour = '#bbb' if not unlocked else _PLAQUE_TEXT
        desc_lbl.setStyleSheet(
            f"color: {locked_colour}; font-style: {'italic' if not unlocked else 'normal'};"
        )
        p_inner.addWidget(desc_lbl)

        # Points & tier
        tier_name = getattr(getattr(ach, 'tier', None), 'value', 'bronze') or 'bronze'
        pts  = getattr(ach, 'points', 0)
        tier_lbl = QLabel(f"{tier_name.capitalize()} • {pts} pts")
        tier_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tier_font = QFont("Segoe UI", 6)
        tier_lbl.setFont(tier_font)
        tier_lbl.setStyleSheet(f"color: {_PLAQUE_TEXT if unlocked else '#999'};")
        p_inner.addWidget(tier_lbl)

        # Progress bar for locked achievements
        if not unlocked:
            prog = getattr(ach, 'get_progress_percent', None)
            pct  = int(prog()) if callable(prog) else 0
            if pct > 0:
                bar = QProgressBar()
                bar.setMaximum(100)
                bar.setValue(pct)
                bar.setTextVisible(False)
                bar.setFixedHeight(5)
                bar.setStyleSheet("""
                    QProgressBar { background:#3a2a0a; border:1px solid #5c4200;
                                   border-radius:2px; }
                    QProgressBar::chunk { background:#c8a800; border-radius:2px; }
                """)
                p_inner.addWidget(bar)

        outer.addWidget(plaque)


class ShelfRowWidget(QWidget):
    """A single shelf row — a horizontal strip of trophies on a wooden board."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 0, 8, 0)
        self._layout.setSpacing(8)
        self._layout.addStretch()

    def add_trophy(self, trophy: TrophyWidget):
        # Insert before the trailing stretch
        count = self._layout.count()
        self._layout.insertWidget(count - 1, trophy)

    def paintEvent(self, event):
        """Draw the wooden shelf background and edge."""
        super().paintEvent(event)
        if not PYQT_AVAILABLE:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Shelf board
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(_SHELF_EDGE))
        grad.setColorAt(0.3, QColor(_SHELF_BG))
        grad.setColorAt(1.0, QColor(_SHELF_BG))
        p.fillRect(0, 0, w, h, QBrush(grad))

        # Shelf edge highlight (top 4 px)
        p.fillRect(0, 0, w, 4, QBrush(QColor(_SHELF_EDGE)))

        # Bottom shadow line
        p.setPen(QPen(QColor('#111'), 2))
        p.drawLine(0, h - 1, w, h - 1)
        p.end()


class AchievementCardWidget(QFrame):
    """Backwards-compatible thin wrapper — kept so existing callers don't break.

    The trophy-shelf design uses TrophyWidget directly; this class is retained
    in case any external code still instantiates AchievementCardWidget.
    """

    def __init__(self, achievement: 'Achievement', parent=None):
        super().__init__(parent)
        self.achievement = achievement
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(TrophyWidget(achievement))



class AchievementDisplayWidget(QWidget):
    """Main achievement display panel"""
    
    def __init__(self, achievement_system=None, parent=None, tooltip_manager=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 required for AchievementDisplayWidget")
        
        super().__init__(parent)
        self.tooltip_manager = tooltip_manager
        
        # Initialize achievement system if not provided
        if ACHIEVEMENTS_AVAILABLE:
            self.achievement_system = achievement_system or AchievementSystem()
        else:
            self.achievement_system = None
        
        self.current_filter = "All"
        self.current_search = ""
        self.setup_ui()
        self.refresh_achievements()
        
    def setup_ui(self):
        """Create the trophy-shelf achievements UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Wooden panel background for the whole widget ───────────────────
        self.setStyleSheet(f"""
            AchievementDisplayWidget {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #1e0f07, stop:1 #0d0704);
            }}
        """)

        # Header
        header = QHBoxLayout()

        title = QLabel("🏆 Trophy Room")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffd700;")
        header.addWidget(title)

        header.addStretch()

        # Stats
        self.stats_label = QLabel("0/0 Unlocked • 0 Points")
        self.stats_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.stats_label.setStyleSheet("color: #ffe8b0;")
        header.addWidget(self.stats_label)
        self._set_tooltip(self.stats_label, 'achievement_progress')

        layout.addLayout(header)

        # Filter controls
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("color: #d4a96a;")
        filter_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.setStyleSheet("""
            QComboBox { background: #3d1e0a; color: #ffe8b0;
                        border: 1px solid #5c3317; border-radius: 4px; padding: 2px 6px; }
            QComboBox QAbstractItemView { background: #3d1e0a; color: #ffe8b0;
                                          selection-background-color: #5c3317; }
        """)
        filters = ["All", "Unlocked", "Locked", "Bronze", "Silver", "Gold", "Platinum", "Legendary"]
        self.filter_combo.addItems(filters)
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        self._set_tooltip(self.filter_combo, 'achievements_tab')
        filter_layout.addWidget(self.filter_combo)

        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search achievements…")
        self.search_edit.setStyleSheet(
            "QLineEdit { background: #3d1e0a; color: #ffe8b0; border: 1px solid #5c3317;"
            " border-radius: 4px; padding: 2px 6px; }"
        )
        self.search_edit.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self.search_edit, stretch=1)

        filter_layout.addStretch()

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton { background:#5c3317; color:#ffe8b0; border:1px solid #8b6914;
                          border-radius:4px; padding:3px 10px; }
            QPushButton:hover { background:#7a4520; }
        """)
        refresh_btn.clicked.connect(self.refresh_achievements)
        self._set_tooltip(refresh_btn, 'rewards_tab')
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Scroll area containing the shelves
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        # Inner container — vertical stack of shelf rows
        self.shelves_widget = QWidget()
        self.shelves_widget.setStyleSheet("background: transparent;")
        self.shelves_layout = QVBoxLayout(self.shelves_widget)
        self.shelves_layout.setContentsMargins(8, 8, 8, 8)
        self.shelves_layout.setSpacing(24)
        self.shelves_layout.addStretch()
        scroll.setWidget(self.shelves_widget)

        layout.addWidget(scroll, stretch=1)

        # Status message
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #a0724a; font-size: 11px;")
        layout.addWidget(self.status_label)

    # ── Shelf constants ────────────────────────────────────────────────────────
    _TROPHIES_PER_SHELF = 5   # trophies per shelf row

    def refresh_achievements(self):
        """Refresh achievements — rebuild the trophy shelves."""
        if not ACHIEVEMENTS_AVAILABLE or not self.achievement_system:
            self.status_label.setText("⚠️ Achievement system not available")
            return

        # Remove existing shelf rows (keep the trailing stretch)
        while self.shelves_layout.count() > 1:
            item = self.shelves_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get all achievements
        all_achievements = self.achievement_system.get_all_achievements()

        # Filter achievements
        filtered = [a for a in all_achievements if self.matches_filter(a)]

        # Update stats
        unlocked = [a for a in all_achievements if a.unlocked]
        total_points = sum(getattr(a, 'points', 0) for a in unlocked)
        self.stats_label.setText(
            f"{len(unlocked)}/{len(all_achievements)} Unlocked • {total_points} Points"
        )

        if not filtered:
            self.status_label.setText("No achievements match the current filter")
            return

        # Build shelf rows (N trophies per shelf)
        n = self._TROPHIES_PER_SHELF
        for shelf_idx in range(0, len(filtered), n):
            shelf_achs = filtered[shelf_idx:shelf_idx + n]
            shelf_row = ShelfRowWidget()
            shelf_row.setMinimumHeight(200)
            for ach in shelf_achs:
                shelf_row.add_trophy(TrophyWidget(ach))
            # Insert before the trailing stretch
            self.shelves_layout.insertWidget(self.shelves_layout.count() - 1, shelf_row)

        self.status_label.setText(f"Showing {len(filtered)} trophies")
        
    def matches_filter(self, achievement: 'Achievement') -> bool:
        """Check if achievement matches current filter and search query."""
        if self.current_filter == "Unlocked":
            if not achievement.unlocked:
                return False
        elif self.current_filter == "Locked":
            if achievement.unlocked:
                return False
        elif self.current_filter != "All":
            # Tier filter
            if achievement.tier.value.lower() != self.current_filter.lower():
                return False

        # Search query
        query = getattr(self, 'current_search', '').strip().lower()
        if query:
            name = getattr(achievement, 'name', '').lower()
            desc = getattr(achievement, 'description', '').lower()
            if query not in name and query not in desc:
                return False

        return True

    def on_filter_changed(self, filter_text: str):
        """Handle filter change"""
        self.current_filter = filter_text
        self.refresh_achievements()

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self.current_search = text
        self.refresh_achievements()
    
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
