"""
PyQt6-based enemy widget using QGraphicsView.
Pure PyQt implementation for enemy rendering and animation.
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsPolygonItem
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QColor, QPen, QBrush, QPolygonF, QPainter
import math
import random
from typing import Optional, Callable


class EnemyGraphicsWidget(QGraphicsView):
    """
    PyQt6-based enemy widget using QGraphicsView.
    
    Displays animated enemy with:
    - Smooth animations
    - Hardware acceleration
    - No canvas dependencies
    - Collision detection ready
    """
    
    # Constants
    WIDTH = 120
    HEIGHT = 120
    MOVEMENT_INTERVAL = 50  # ms between updates (20 FPS)
    MOVE_SPEED_BASE = 2.0
    ATTACK_RANGE = 80
    BOUNCE_AMPLITUDE = 5
    
    def __init__(self, enemy, target_widget=None, on_attack=None, on_death=None, parent=None):
        super().__init__(parent)
        
        self.enemy = enemy
        self.target_widget = target_widget
        self.on_attack = on_attack
        self.on_death = on_death
        
        # Setup scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Configure view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Transparent background
        self.setStyleSheet("background: transparent;")
        self.setFrameStyle(0)
        
        # Animation state
        self.animation_phase = 0
        self.bounce_offset = 0
        self.position = QPointF(0, 0)
        
        # Create graphics items
        self._create_enemy_graphics()
        
        # Setup timers
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(self.MOVEMENT_INTERVAL)
        
        self.movement_timer = QTimer()
        self.movement_timer.timeout.connect(self._update_movement)
        self.movement_timer.start(self.MOVEMENT_INTERVAL)
    
    def _create_enemy_graphics(self):
        """Create enemy visual representation."""
        center_x = self.WIDTH / 2
        center_y = self.HEIGHT / 2
        
        # Get enemy color based on type
        enemy_type = getattr(self.enemy, 'enemy_type', 'slime')
        colors = {
            'slime': QColor(0, 200, 0),
            'goblin': QColor(150, 200, 50),
            'orc': QColor(100, 150, 50),
            'skeleton': QColor(220, 220, 220),
            'dragon': QColor(200, 50, 50),
            'wolf': QColor(150, 150, 150),
        }
        color = colors.get(enemy_type, QColor(200, 0, 0))
        
        # Draw enemy body (circle)
        radius = 30
        self.body = QGraphicsEllipseItem(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2
        )
        self.body.setBrush(QBrush(color))
        self.body.setPen(QPen(QColor(0, 0, 0), 2))
        self.scene.addItem(self.body)
        
        # Draw eyes
        eye_offset = 10
        eye_size = 8
        
        # Left eye
        self.left_eye = QGraphicsEllipseItem(
            center_x - eye_offset - eye_size/2,
            center_y - 5 - eye_size/2,
            eye_size, eye_size
        )
        self.left_eye.setBrush(QBrush(QColor(255, 255, 255)))
        self.left_eye.setPen(QPen(QColor(0, 0, 0), 1))
        self.scene.addItem(self.left_eye)
        
        # Right eye
        self.right_eye = QGraphicsEllipseItem(
            center_x + eye_offset - eye_size/2,
            center_y - 5 - eye_size/2,
            eye_size, eye_size
        )
        self.right_eye.setBrush(QBrush(QColor(255, 255, 255)))
        self.right_eye.setPen(QPen(QColor(0, 0, 0), 1))
        self.scene.addItem(self.right_eye)
        
        # Draw mouth
        mouth_y = center_y + 10
        mouth_points = QPolygonF([
            QPointF(center_x - 15, mouth_y),
            QPointF(center_x - 10, mouth_y + 5),
            QPointF(center_x, mouth_y + 3),
            QPointF(center_x + 10, mouth_y + 5),
            QPointF(center_x + 15, mouth_y),
        ])
        self.mouth = QGraphicsPolygonItem(mouth_points)
        self.mouth.setPen(QPen(QColor(0, 0, 0), 2))
        self.scene.addItem(self.mouth)
    
    def _update_animation(self):
        """Update animation (bouncing, etc.)."""
        self.animation_phase += 0.2
        self.bounce_offset = math.sin(self.animation_phase) * self.BOUNCE_AMPLITUDE
        
        # Update body position for bounce
        if self.body:
            rect = self.body.rect()
            center_y = self.HEIGHT / 2 + self.bounce_offset
            self.body.setRect(
                rect.x(),
                center_y - rect.height() / 2,
                rect.width(),
                rect.height()
            )
    
    def _update_movement(self):
        """Update position toward target."""
        if not self.target_widget:
            return
        
        # Simple movement logic
        # In full implementation, would move toward target
        # For now, just animate in place
        pass
    
    def is_alive(self):
        """Check if enemy is still alive."""
        return getattr(self.enemy, 'health', 0) > 0
    
    def take_damage(self, amount: int):
        """Take damage and check for death."""
        if hasattr(self.enemy, 'take_damage'):
            self.enemy.take_damage(amount)
        
        if not self.is_alive() and self.on_death:
            self.on_death(self.enemy)
    
    def attack_target(self):
        """Attack the target."""
        if self.on_attack:
            self.on_attack(self.enemy)
    
    def cleanup(self):
        """Clean up resources."""
        self.animation_timer.stop()
        self.movement_timer.stop()
