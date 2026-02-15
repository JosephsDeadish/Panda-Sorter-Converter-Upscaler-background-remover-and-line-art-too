"""
Qt Travel Animation Widget - Replaces canvas travel animation
Uses Qt animations and QLabel for clean widget-based animation
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from enum import Enum
from typing import List, NamedTuple


class SceneType(Enum):
    """Travel scene types"""
    WALK_TO_CAR = "walk_to_car"
    GET_IN_CAR = "get_in_car"
    DRIVING = "driving"
    ARRIVE = "arrive"


class TravelScene(NamedTuple):
    """Travel scene configuration"""
    scene_type: SceneType
    sky_color: str
    ground_color: str
    road_color: str
    detail_emoji: str
    description: str
    duration_ms: int


class TravelAnimationWidget(QWidget):
    """Qt widget for travel animations"""
    
    animation_complete = pyqtSignal()
    
    def __init__(self, scenes: List[TravelScene] = None, parent=None):
        super().__init__(parent)
        self.scenes = scenes or self._get_default_scenes()
        self.current_scene = 0
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        
        # Animation canvas (QLabel with custom painting)
        self.canvas_label = QLabel()
        self.canvas_label.setMinimumSize(500, 300)
        self.canvas_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_label.setStyleSheet("background: #87CEEB;")  # Sky color
        layout.addWidget(self.canvas_label)
        
        # Description label
        self.desc_label = QLabel()
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setStyleSheet("""
            QLabel {
                font-size: 16pt;
                font-weight: bold;
                padding: 10px;
            }
        """)
        layout.addWidget(self.desc_label)
        
        # Timer for scene progression
        self.scene_timer = QTimer()
        self.scene_timer.timeout.connect(self._next_scene)
        
    def _get_default_scenes(self) -> List[TravelScene]:
        """Get default travel scenes"""
        return [
            TravelScene(
                scene_type=SceneType.WALK_TO_CAR,
                sky_color="#87CEEB",
                ground_color="#90EE90",
                road_color="#808080",
                detail_emoji="🌳",
                description="Walking to the car...",
                duration_ms=2000
            ),
            TravelScene(
                scene_type=SceneType.GET_IN_CAR,
                sky_color="#87CEEB",
                ground_color="#90EE90",
                road_color="#808080",
                detail_emoji="🌳",
                description="Getting in the car...",
                duration_ms=1500
            ),
            TravelScene(
                scene_type=SceneType.DRIVING,
                sky_color="#87CEEB",
                ground_color="#90EE90",
                road_color="#808080",
                detail_emoji="🌳",
                description="Driving...",
                duration_ms=3000
            ),
            TravelScene(
                scene_type=SceneType.ARRIVE,
                sky_color="#87CEEB",
                ground_color="#90EE90",
                road_color="#808080",
                detail_emoji="🏛️",
                description="Arriving at destination!",
                duration_ms=2000
            ),
        ]
    
    def start_animation(self):
        """Start the travel animation"""
        self.current_scene = 0
        self._show_scene()
    
    def _show_scene(self):
        """Show current scene"""
        if self.current_scene >= len(self.scenes):
            # Animation complete
            self.animation_complete.emit()
            return
        
        scene = self.scenes[self.current_scene]
        
        # Update description
        self.desc_label.setText(scene.description)
        
        # Draw scene on pixmap
        pixmap = QPixmap(500, 300)
        pixmap.fill(QColor(scene.sky_color))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw ground
        painter.fillRect(0, 200, 500, 100, QColor(scene.ground_color))
        
        # Draw road
        painter.fillRect(0, 220, 500, 50, QColor(scene.road_color))
        
        # Draw road dashes
        painter.setBrush(QColor("#FFFFFF"))
        for rx in range(0, 500, 60):
            painter.drawRect(rx + 10, 243, 30, 4)
        
        # Draw detail emojis
        font = QFont("Arial", 20)
        painter.setFont(font)
        for dx in range(50, 500, 120):
            painter.drawText(dx, 195, scene.detail_emoji)
        
        # Draw scene-specific elements
        emoji_font = QFont("Arial", 36)
        painter.setFont(emoji_font)
        
        if scene.scene_type == SceneType.WALK_TO_CAR:
            painter.drawText(350, 230, "🚗")
            small_font = QFont("Arial", 30)
            painter.setFont(small_font)
            painter.drawText(200, 230, "🐼")
        elif scene.scene_type == SceneType.GET_IN_CAR:
            painter.drawText(350, 230, "🚗")
            small_font = QFont("Arial", 20)
            painter.setFont(small_font)
            painter.drawText(340, 220, "🐼")
        elif scene.scene_type == SceneType.ARRIVE:
            painter.drawText(250, 230, "🚗")
            big_font = QFont("Arial", 40)
            painter.setFont(big_font)
            painter.drawText(250, 170, scene.detail_emoji)
        else:  # DRIVING
            painter.drawText(250, 230, "🚗")
        
        painter.end()
        
        # Set pixmap to label
        self.canvas_label.setPixmap(pixmap)
        
        # Schedule next scene
        self.scene_timer.start(scene.duration_ms)
    
    def _next_scene(self):
        """Move to next scene"""
        self.scene_timer.stop()
        self.current_scene += 1
        self._show_scene()


# Tkinter compatibility bridge
try:
    import tkinter as tk
    
    class TkinterTravelAnimationBridge:
        """Bridge for Tkinter compatibility"""
        
        @staticmethod
        def create_travel_animation(parent_frame, scenes, on_complete=None):
            """Create travel animation (tries Qt first, falls back to canvas)"""
            try:
                from PyQt6.QtWidgets import QApplication
                
                # Check if Qt application exists
                if QApplication.instance() is None:
                    raise RuntimeError("Qt not initialized")
                
                widget = TravelAnimationWidget(scenes)
                if on_complete:
                    widget.animation_complete.connect(on_complete)
                widget.start_animation()
                return widget
                
            except Exception:
                # Fallback: Return None, caller should use canvas
                return None
                
except ImportError:
    # PyQt6 not available
    class TkinterTravelAnimationBridge:
        @staticmethod
        def create_travel_animation(parent_frame, scenes, on_complete=None):
            return None
