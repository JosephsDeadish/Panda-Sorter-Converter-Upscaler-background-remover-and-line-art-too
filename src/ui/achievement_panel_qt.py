"""
Achievement Display Panel - View and track achievements
Qt implementation with progress tracking
"""

import logging

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QGridLayout, QProgressBar, QComboBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object

logger = logging.getLogger(__name__)

# Try to import achievement system
try:
    from features.achievements import AchievementSystem, Achievement, AchievementTier
    ACHIEVEMENTS_AVAILABLE = True
except ImportError:
    try:
        from ..features.achievements import AchievementSystem, Achievement, AchievementTier
        ACHIEVEMENTS_AVAILABLE = True
    except ImportError:
        logger.warning("Achievement system not available")
        ACHIEVEMENTS_AVAILABLE = False
        AchievementSystem = None
        Achievement = None
        AchievementTier = None


class AchievementCardWidget(QFrame):
    """Individual achievement card"""
    
    def __init__(self, achievement: 'Achievement', parent=None):
        super().__init__(parent)
        self.achievement = achievement
        self.setup_ui()
        
    def setup_ui(self):
        """Create the achievement card UI"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        
        # Style based on unlocked status and tier
        if self.achievement.unlocked:
            bg_color = "#e8f5e9"
            border_color = "#4CAF50"
        else:
            bg_color = "#f5f5f5"
            border_color = "#ccc"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                border: 2px solid #2196F3;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header with icon and name
        header = QHBoxLayout()
        
        # Icon
        icon_label = QLabel(self.achievement.icon)
        icon_label.setFont(QFont("Segoe UI", 24))
        header.addWidget(icon_label)
        
        # Name and tier
        name_layout = QVBoxLayout()
        name_label = QLabel(self.achievement.name)
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_layout.addWidget(name_label)
        
        tier_label = QLabel(f"{self.achievement.tier.value.title()} • {self.achievement.points} pts")
        tier_label.setFont(QFont("Segoe UI", 8))
        tier_label.setStyleSheet("color: #666;")
        name_layout.addWidget(tier_label)
        
        header.addLayout(name_layout)
        header.addStretch()
        
        # Unlocked indicator
        if self.achievement.unlocked:
            unlocked_label = QLabel("✓ Unlocked")
            unlocked_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            unlocked_label.setStyleSheet("color: #4CAF50;")
            header.addWidget(unlocked_label)
        else:
            locked_label = QLabel("🔒 Locked")
            locked_label.setFont(QFont("Segoe UI", 9))
            locked_label.setStyleSheet("color: #999;")
            header.addWidget(locked_label)
        
        layout.addLayout(header)
        
        # Description
        if not self.achievement.hidden or self.achievement.unlocked:
            desc_label = QLabel(self.achievement.description)
            desc_label.setFont(QFont("Segoe UI", 9))
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        else:
            desc_label = QLabel("🔒 Hidden achievement - keep exploring to discover!")
            desc_label.setFont(QFont("Segoe UI", 9))
            desc_label.setStyleSheet("color: #999; font-style: italic;")
            layout.addWidget(desc_label)
        
        # Progress bar (if not complete)
        if not self.achievement.unlocked:
            progress_layout = QVBoxLayout()
            
            progress_label = QLabel(f"Progress: {self.achievement.get_progress_percent():.1f}%")
            progress_label.setFont(QFont("Segoe UI", 8))
            progress_layout.addWidget(progress_label)
            
            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            progress_bar.setValue(int(self.achievement.get_progress_percent()))
            progress_bar.setTextVisible(False)
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f0f0f0;
                    height: 8px;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 2px;
                }
            """)
            progress_layout.addWidget(progress_bar)
            
            layout.addLayout(progress_layout)
        
        # Unlock date (if unlocked)
        if self.achievement.unlocked and self.achievement.unlock_date:
            date_label = QLabel(f"Unlocked: {self.achievement.unlock_date}")
            date_label.setFont(QFont("Segoe UI", 7))
            date_label.setStyleSheet("color: #666;")
            layout.addWidget(date_label)


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
        self.setup_ui()
        self.refresh_achievements()
        
    def setup_ui(self):
        """Create the achievements UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🏆 Achievements")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        # Stats
        self.stats_label = QLabel("0/0 Unlocked • 0 Points")
        self.stats_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.stats_label.setStyleSheet("color: #4CAF50;")
        header.addWidget(self.stats_label)
        
        layout.addLayout(header)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.filter_combo = QComboBox()
        filters = ["All", "Unlocked", "Locked", "Bronze", "Silver", "Gold", "Platinum", "Legendary"]
        self.filter_combo.addItems(filters)
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_achievements)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Achievements grid
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
        
    def refresh_achievements(self):
        """Refresh achievements display"""
        if not ACHIEVEMENTS_AVAILABLE or not self.achievement_system:
            self.status_label.setText("⚠️ Achievement system not available")
            return
        
        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get all achievements
        all_achievements = self.achievement_system.get_all_achievements()
        
        # Filter achievements
        filtered = []
        for ach in all_achievements:
            if self.matches_filter(ach):
                filtered.append(ach)
        
        # Update stats
        unlocked = [a for a in all_achievements if a.unlocked]
        total_points = sum(a.points for a in unlocked)
        self.stats_label.setText(
            f"{len(unlocked)}/{len(all_achievements)} Unlocked • {total_points} Points"
        )
        
        # Add to grid
        row, col = 0, 0
        for achievement in filtered:
            card = AchievementCardWidget(achievement)
            self.grid_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
        
        if not filtered:
            self.status_label.setText("No achievements match the current filter")
        else:
            self.status_label.setText(f"Showing {len(filtered)} achievements")
        
    def matches_filter(self, achievement: 'Achievement') -> bool:
        """Check if achievement matches current filter"""
        if self.current_filter == "All":
            return True
        elif self.current_filter == "Unlocked":
            return achievement.unlocked
        elif self.current_filter == "Locked":
            return not achievement.unlocked
        else:
            # Tier filter
            return achievement.tier.value.lower() == self.current_filter.lower()
        
    def on_filter_changed(self, filter_text: str):
        """Handle filter change"""
        self.current_filter = filter_text
        self.refresh_achievements()
    
    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager:
            tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
            if tooltip:
                widget.setToolTip(tooltip)
