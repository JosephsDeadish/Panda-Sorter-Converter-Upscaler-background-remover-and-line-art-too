"""
Qt Enemy Display Widget

Pure PyQt6 implementation for enemy display and combat.
Uses QLabel with animated QPixmap for 2D enemies, or QOpenGLWidget for 3D.
"""

try:
    from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class EnemyDisplayWidget(QWidget):
    """
    Widget for displaying animated enemies.
    
    Uses QPixmap rendering for 2D enemy sprites with animations.
    """
    
    clicked = pyqtSignal()  # Signal when enemy is clicked
    
    def __init__(self, enemy=None, width=200, height=200, parent=None):
        """
        Initialize enemy display.
        
        Args:
            enemy: Enemy instance to display
            width: Widget width
            height: Widget height
            parent: Parent widget
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 required for Qt enemy widget")
            
        super().__init__(parent)
        
        self.enemy = enemy
        self.display_width = width
        self.display_height = height
        self.animation_phase = 0.0
        
        self._setup_ui()
        self._setup_animation()
        
    def _setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label for rendering
        self.render_label = QLabel()
        self.render_label.setFixedSize(self.display_width, self.display_height)
        self.render_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.render_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #444444;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.render_label)
        
        # Initial render
        self._render_enemy()
        
    def _setup_animation(self):
        """Setup animation timer."""
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(50)  # 20 FPS for enemy animation
        
    def _update_animation(self):
        """Update animation frame."""
        self.animation_phase += 0.1
        if self.animation_phase > 2 * 3.14159:
            self.animation_phase = 0.0
        self._render_enemy()
        
    def _render_enemy(self):
        """Render the enemy to a QPixmap."""
        import math
        
        # Create pixmap
        pixmap = QPixmap(self.display_width, self.display_height)
        pixmap.fill(QColor(43, 43, 43))  # Background
        
        # Draw on pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.enemy:
            self._draw_enemy_on_painter(painter)
        else:
            self._draw_placeholder(painter)
            
        painter.end()
        
        # Set pixmap
        self.render_label.setPixmap(pixmap)
        
    def _draw_enemy_on_painter(self, painter):
        """
        Draw enemy using QPainter.
        
        Args:
            painter: QPainter instance
        """
        import math
        
        cx = self.display_width // 2
        cy = self.display_height // 2
        
        # Get enemy properties
        enemy_name = getattr(self.enemy, 'name', 'Enemy')
        enemy_level = getattr(self.enemy, 'level', 1)
        enemy_color = getattr(self.enemy, 'color', 'red')
        
        # Color mapping
        color_map = {
            'red': QColor(200, 50, 50),
            'blue': QColor(50, 100, 200),
            'green': QColor(50, 200, 50),
            'purple': QColor(150, 50, 200),
            'orange': QColor(255, 140, 0),
        }
        base_color = color_map.get(enemy_color, QColor(150, 150, 150))
        
        # Breathing animation
        breath_offset = math.sin(self.animation_phase) * 5
        
        # Body (circle)
        body_radius = 40 + breath_offset
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(QBrush(base_color))
        painter.drawEllipse(
            int(cx - body_radius),
            int(cy - body_radius),
            int(body_radius * 2),
            int(body_radius * 2)
        )
        
        # Eyes
        eye_color = QColor(255, 255, 255)
        pupil_color = QColor(0, 0, 0)
        
        # Left eye
        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(cx - 20, cy - 10, 15, 15)
        painter.setBrush(QBrush(pupil_color))
        painter.drawEllipse(cx - 15, cy - 5, 6, 6)
        
        # Right eye
        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(cx + 5, cy - 10, 15, 15)
        painter.setBrush(QBrush(pupil_color))
        painter.drawEllipse(cx + 10, cy - 5, 6, 6)
        
        # Mouth
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.drawArc(cx - 15, cy + 5, 30, 20, 0, -180 * 16)
        
        # Level indicator
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        painter.drawText(
            cx - 30, cy + body_radius + 20,
            f"Lv.{enemy_level}"
        )
        
        # Name
        painter.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        painter.drawText(
            cx - 50, cy - body_radius - 10,
            enemy_name[:15]  # Truncate long names
        )
        
    def _draw_placeholder(self, painter):
        """Draw placeholder when no enemy set."""
        cx = self.display_width // 2
        cy = self.display_height // 2
        
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.setFont(QFont('Arial', 14))
        painter.drawText(
            cx - 60, cy,
            "No Enemy"
        )
        
    def set_enemy(self, enemy):
        """
        Set the enemy to display.
        
        Args:
            enemy: Enemy instance
        """
        self.enemy = enemy
        self._render_enemy()
        
    def mousePressEvent(self, event):
        """Handle mouse click."""
        self.clicked.emit()
        super().mousePressEvent(event)


class EnemyListWidget(QWidget):
    """
    Widget for displaying multiple enemies in a list.
    """
    
    enemy_clicked = pyqtSignal(object)  # Emits clicked enemy
    
    def __init__(self, enemies=None, parent=None):
        """
        Initialize enemy list widget.
        
        Args:
            enemies: List of enemy instances
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.enemies = enemies or []
        self.enemy_widgets = []
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Create UI layout."""
        from PyQt6.QtWidgets import QHBoxLayout, QScrollArea
        
        # Scroll area for multiple enemies
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for enemy widgets
        container = QWidget()
        self.enemy_layout = QHBoxLayout(container)
        self.enemy_layout.setSpacing(10)
        
        scroll.setWidget(container)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Add enemy widgets
        self._populate_enemies()
        
    def _populate_enemies(self):
        """Create widgets for each enemy."""
        for enemy in self.enemies:
            enemy_widget = EnemyDisplayWidget(enemy, 150, 150, self)
            enemy_widget.clicked.connect(
                lambda e=enemy: self.enemy_clicked.emit(e)
            )
            self.enemy_layout.addWidget(enemy_widget)
            self.enemy_widgets.append(enemy_widget)
            
    def set_enemies(self, enemies):
        """
        Set new enemy list.
        
        Args:
            enemies: List of enemy instances
        """
        # Clear old widgets
        for widget in self.enemy_widgets:
            widget.deleteLater()
        self.enemy_widgets.clear()
        
        # Set new enemies
        self.enemies = enemies
        self._populate_enemies()


# Test/demo
if __name__ == "__main__":
    if PYQT_AVAILABLE:
        from PyQt6.QtWidgets import QApplication
        import sys
        
        # Mock enemy for testing
        class MockEnemy:
            def __init__(self, name, level, color):
                self.name = name
                self.level = level
                self.color = color
        
        app = QApplication(sys.argv)
        
        # Test single enemy
        enemy = MockEnemy("Goblin", 5, "green")
        widget = EnemyDisplayWidget(enemy, 250, 250)
        widget.setWindowTitle("Enemy Display Demo")
        widget.show()
        
        sys.exit(app.exec())
