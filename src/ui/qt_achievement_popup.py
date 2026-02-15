"""
Qt Achievement Popup Widget

Replacement for tk.Canvas-based achievement popup.
Uses Qt widgets with CSS styling for modern appearance.
"""

try:
    from PyQt6.QtWidgets import (QDialog, QLabel, QVBoxLayout, QHBoxLayout, 
                                  QFrame, QPushButton)
    from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
    from PyQt6.QtGui import QFont, QIcon, QPixmap
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class AchievementPopup(QDialog):
    """Modern achievement popup using Qt widgets."""
    
    def __init__(self, achievement_data, parent=None):
        """
        Initialize achievement popup.
        
        Args:
            achievement_data: Dict with 'name', 'emoji', 'description'
            parent: Parent widget
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for Qt achievement popups")
            
        super().__init__(parent)
        
        self.achievement_data = achievement_data
        self._setup_window()
        self._setup_ui()
        self._setup_animations()
        self._auto_close_timer = None
        
    def _setup_window(self):
        """Configure window properties."""
        # Frameless with rounded corners
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Size
        self.setFixedSize(400, 120)
        
    def _setup_ui(self):
        """Create UI elements."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container frame with rounded corners
        container = QFrame()
        container.setObjectName("achievementContainer")
        container.setStyleSheet("""
            QFrame#achievementContainer {
                background-color: #2b2b2b;
                border: 2px solid #ffd700;
                border-radius: 12px;
            }
        """)
        
        # Container layout
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 15, 20, 15)
        container_layout.setSpacing(10)
        
        # Top row: emoji and title
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        
        # Emoji label
        emoji_label = QLabel(self.achievement_data.get('emoji', '🏆'))
        emoji_label.setFont(QFont('Segoe UI Emoji', 36))
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setFixedSize(60, 60)
        top_layout.addWidget(emoji_label)
        
        # Title and description
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        
        # Title
        title_label = QLabel(f"🎉 {self.achievement_data.get('name', 'Achievement Unlocked!')}")
        title_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffd700;")
        text_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.achievement_data.get('description', ''))
        desc_label.setFont(QFont('Arial', 11))
        desc_label.setStyleSheet("color: #ffffff;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        top_layout.addLayout(text_layout, 1)
        container_layout.addLayout(top_layout)
        
        main_layout.addWidget(container)
        
    def _setup_animations(self):
        """Setup slide-in and slide-out animations."""
        # Slide in from right
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(500)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def show_popup(self, parent_geometry=None):
        """
        Show the popup with animation.
        
        Args:
            parent_geometry: Parent window geometry to position relative to
        """
        # Position in bottom-right corner
        if parent_geometry:
            # Calculate position relative to parent
            margin = 20
            x = parent_geometry.x() + parent_geometry.width() - self.width() - margin
            y = parent_geometry.y() + parent_geometry.height() - self.height() - margin
        else:
            # Default position
            from PyQt6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen().geometry()
            margin = 20
            x = screen.width() - self.width() - margin
            y = screen.height() - self.height() - margin
        
        # Start position (off-screen right)
        start_pos = QPoint(x + 100, y)
        end_pos = QPoint(x, y)
        
        self.move(start_pos)
        self.show()
        
        # Animate slide in
        self.slide_animation.setStartValue(start_pos)
        self.slide_animation.setEndValue(end_pos)
        self.slide_animation.start()
        
        # Auto-close after 5 seconds
        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.timeout.connect(self.hide_popup)
        self._auto_close_timer.start(5000)
        
    def hide_popup(self):
        """Hide the popup with animation."""
        if self._auto_close_timer:
            self._auto_close_timer.stop()
        
        # Slide out to right
        current_pos = self.pos()
        end_pos = QPoint(current_pos.x() + 100, current_pos.y())
        
        self.slide_animation.setStartValue(current_pos)
        self.slide_animation.setEndValue(end_pos)
        self.slide_animation.finished.connect(self.close)
        self.slide_animation.start()
        
    def mousePressEvent(self, event):
        """Close on click."""
        self.hide_popup()


def show_achievement_popup(achievement_data, parent=None, parent_geometry=None):
    """
    Show an achievement popup.
    
    Args:
        achievement_data: Dict with 'name', 'emoji', 'description'
        parent: Parent widget
        parent_geometry: Parent geometry for positioning
        
    Returns:
        AchievementPopup instance
    """
    if not PYQT_AVAILABLE:
        print(f"Achievement: {achievement_data.get('name')} - {achievement_data.get('description')}")
        return None
        
    popup = AchievementPopup(achievement_data, parent)
    popup.show_popup(parent_geometry)
    return popup


# Backwards compatibility for Tkinter code
class TkinterAchievementPopupBridge:
    """Bridge class to maintain API compatibility with Tkinter code."""
    
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        self.current_popup = None
        
    def show_achievement(self, achievement_data):
        """
        Show achievement using Qt popup.
        
        Args:
            achievement_data: Dict with 'name', 'emoji', 'description'
        """
        if not PYQT_AVAILABLE:
            # Fallback: just print
            print(f"🏆 Achievement: {achievement_data.get('name')}")
            return
            
        # Get parent geometry if available
        parent_geom = None
        if self.parent_window and hasattr(self.parent_window, 'geometry'):
            try:
                # Try to parse Tkinter geometry string
                geom = self.parent_window.geometry()
                # Format: widthxheight+x+y
                parts = geom.replace('x', '+').split('+')
                if len(parts) >= 4:
                    from PyQt6.QtCore import QRect
                    parent_geom = QRect(
                        int(parts[2]), int(parts[3]),
                        int(parts[0]), int(parts[1])
                    )
            except:
                pass
        
        # Show Qt popup
        self.current_popup = show_achievement_popup(
            achievement_data,
            parent=None,
            parent_geometry=parent_geom
        )


if __name__ == "__main__":
    # Test the achievement popup
    if PYQT_AVAILABLE:
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication(sys.argv)
        
        # Test achievement
        achievement = {
            'name': 'First Steps',
            'emoji': '👟',
            'description': 'Processed your first image!'
        }
        
        popup = show_achievement_popup(achievement)
        
        sys.exit(app.exec())
