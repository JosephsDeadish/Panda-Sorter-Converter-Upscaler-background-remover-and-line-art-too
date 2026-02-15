"""
Achievement display using Qt native animations (QPropertyAnimation).
Uses Qt's event loop integrated timing for smooth animations.
"""

try:
    from PyQt6.QtWidgets import QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout
    from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
    from PyQt6.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class AchievementPopupQt(QWidget):
    """
    Achievement popup using Qt native animations.
    Uses QPropertyAnimation for fade effects with Qt's animation framework.
    """
    
    def __init__(self, achievement, parent=None, accent_color='#ffd700', bg_color='#ffd700'):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 not available")
            
        super().__init__(parent)
        self.achievement = achievement
        self.accent_color = accent_color
        self.bg_color = bg_color
        
        self._setup_window()
        self._create_ui()
        self._start_animations()
        
    def _setup_window(self):
        """Setup window properties"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                          Qt.WindowType.WindowStaysOnTopHint |
                          Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Set size and position
        self.setFixedSize(340, 110)
        
        # Position in top-right
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.right() - 360
            y = parent_rect.top() + 20
            self.move(x, y)
            
    def _create_ui(self):
        """Create the UI elements"""
        # Main frame
        main_frame = QFrame(self)
        main_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1e1e2e;
                border: 2px solid {self.bg_color};
                border-radius: 5px;
            }}
        """)
        main_frame.setGeometry(0, 0, 340, 110)
        
        # Layout
        layout = QHBoxLayout(main_frame)
        layout.setContentsMargins(5, 10, 10, 10)
        layout.setSpacing(10)
        
        # Accent bar
        accent_bar = QFrame()
        accent_bar.setFixedWidth(5)
        accent_bar.setStyleSheet(f"background-color: {self.bg_color};")
        layout.addWidget(accent_bar)
        
        # Content layout
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        
        # Top row with icon and text
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel(getattr(self.achievement, 'icon', '🏆'))
        icon_label.setFont(QFont('Arial', 24))
        icon_label.setStyleSheet("color: white; background: transparent;")
        top_layout.addWidget(icon_label)
        
        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        
        # Header
        header = QLabel('Achievement Unlocked!')
        header.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {self.bg_color}; background: transparent;")
        text_layout.addWidget(header)
        
        # Name
        name_text = getattr(self.achievement, 'name', 'Achievement')
        if len(name_text) > 32:
            name_text = name_text[:30] + '…'
        name = QLabel(name_text)
        name.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        name.setStyleSheet("color: white; background: transparent;")
        text_layout.addWidget(name)
        
        # Description
        desc_text = getattr(self.achievement, 'description', '')
        if desc_text:
            if len(desc_text) > 42:
                desc_text = desc_text[:40] + '…'
            desc = QLabel(desc_text)
            desc.setFont(QFont('Arial', 9))
            desc.setStyleSheet("color: #aaaaaa; background: transparent;")
            text_layout.addWidget(desc)
        
        top_layout.addLayout(text_layout)
        top_layout.addStretch()
        content_layout.addLayout(top_layout)
        
        # Reward
        if hasattr(self.achievement, 'reward') and self.achievement.reward:
            reward_text = f"🎁 {self.achievement.reward.get('description', '')}"
            if len(reward_text) > 45:
                reward_text = reward_text[:43] + '…'
            reward = QLabel(reward_text)
            reward.setFont(QFont('Arial', 9))
            reward.setStyleSheet(f"color: {self.bg_color}; background: transparent; font-style: italic;")
            content_layout.addWidget(reward)
        
        layout.addLayout(content_layout)
        
        # Click to close
        main_frame.mousePressEvent = lambda e: self.close()
        
    def _start_animations(self):
        """
        Start Qt native animations.
        Uses QTimer for delay and QPropertyAnimation for fade.
        """
        # Show with full opacity initially
        self.setWindowOpacity(0.95)
        self.show()
        
        # Create fade-out animation using QPropertyAnimation (Qt native)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(1000)  # 1 second fade
        self.fade_animation.setStartValue(0.95)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Close window when fade completes
        self.fade_animation.finished.connect(self.close)
        
        # Use QTimer to start fade after 5 seconds
        QTimer.singleShot(5000, self.fade_animation.start)


def show_achievement_qt(parent, achievement, accent_color='#ffd700', bg_color='#ffd700'):
    """
    Show achievement popup using Qt native animations.
    
    Args:
        parent: Qt parent widget
        achievement: Achievement object
        accent_color: Accent color
        bg_color: Background color
    
    Returns:
        AchievementPopupQt instance
    """
    if not PYQT_AVAILABLE:
        return None
        
    popup = AchievementPopupQt(achievement, parent, accent_color, bg_color)
    return popup
