"""
2-D Panda Widget — QPainter-based fallback for when PyOpenGL is unavailable.

Draws a simple but charming 2-D panda using QColor / QPainter primitives and
animates it with a QTimer.  Exposes the same public interface as PandaOpenGLWidget
so the rest of main.py can use either widget interchangeably.

Signals
-------
clicked          – emitted when the user clicks the panda
mood_changed     – emitted with the new mood string when mood changes
animation_changed – emitted with the new animation name when animation changes

Public methods (compatible with PandaOpenGLWidget)
--------------------------------------------------
set_mood(mood)
set_animation(animation)
set_color(color_type, color_rgb)
set_trail(trail_type, trail_data)
preview_item(item_id)
equip_item(item_data)
"""

from __future__ import annotations

import logging
import math
import random
from typing import Optional

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
    from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, pyqtSignal, QRectF
    from PyQt6.QtGui import (
        QPainter, QColor, QPen, QBrush, QFont, QMouseEvent,
        QPainterPath, QLinearGradient,
    )
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False
    QWidget = object  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)


class PandaWidget2D(QWidget if _QT_AVAILABLE else object):  # type: ignore[misc]
    """
    QPainter-based 2-D panda — no OpenGL required.

    The panda bounces gently, reacts to clicks, and supports the same signal /
    method interface as PandaOpenGLWidget so main.py can use either widget.
    """

    # ── Signals ────────────────────────────────────────────────────────────────
    if _QT_AVAILABLE:
        clicked = pyqtSignal()
        mood_changed = pyqtSignal(str)
        animation_changed = pyqtSignal(str)
    else:
        clicked = None       # type: ignore[assignment]
        mood_changed = None  # type: ignore[assignment]
        animation_changed = None  # type: ignore[assignment]

    # ── Mood → background gradient colours ─────────────────────────────────────
    _MOOD_COLOURS: dict[str, tuple[str, str]] = {
        'happy':    ('#e8f5e9', '#c8e6c9'),
        'excited':  ('#fff9c4', '#fff176'),
        'sad':      ('#e3f2fd', '#bbdefb'),
        'tired':    ('#fafafa', '#e0e0e0'),
        'angry':    ('#ffebee', '#ffcdd2'),
        'curious':  ('#e8eaf6', '#c5cae9'),
        'neutral':  ('#f5f5f5', '#eeeeee'),
    }

    def __init__(self, panda_character=None, parent: Optional[QWidget] = None) -> None:
        if not _QT_AVAILABLE:
            raise ImportError("PyQt6 is required for PandaWidget2D")
        super().__init__(parent)

        self.panda = panda_character  # PandaCharacter or None

        # State
        self._mood = 'neutral'
        self._animation = 'idle'
        self._body_color = QColor(245, 245, 245)   # white body
        self._ear_color  = QColor(30, 30, 30)       # black ears/patches
        self._hat: Optional[str] = None
        self._equipped_items: list[str] = []

        # Animation variables
        self._tick = 0.0
        self._bob = 0.0       # vertical bob offset (pixels)
        self._blink_timer = 0
        self._blink_open = True
        self._is_bouncing = False
        self._bounce_vel = 0.0
        self._bounce_y = 0.0
        self._particles: list[dict] = []

        # Timer drives the animation loop
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_animation)
        self._timer.start(33)  # ~30 fps — gentle, low CPU

        self.setMinimumSize(200, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── Animation loop ──────────────────────────────────────────────────────────

    def _tick_animation(self) -> None:
        self._tick += 0.05

        # Idle bob
        if self._animation == 'idle':
            self._bob = math.sin(self._tick) * 4.0
        elif self._animation in ('happy', 'excited'):
            self._bob = math.sin(self._tick * 2) * 8.0
        elif self._animation in ('sad', 'tired'):
            self._bob = math.sin(self._tick * 0.5) * 2.0
        else:
            self._bob = math.sin(self._tick) * 4.0

        # Blink every ~120 ticks
        self._blink_timer += 1
        if self._blink_timer > 120:
            self._blink_open = False
            if self._blink_timer > 124:
                self._blink_open = True
                self._blink_timer = 0

        # Bounce physics
        if self._is_bouncing:
            self._bounce_vel -= 0.8   # gravity
            self._bounce_y   += self._bounce_vel
            if self._bounce_y <= 0:
                self._bounce_y = 0
                self._bounce_vel = 0
                self._is_bouncing = False

        # Age / remove particles
        self._particles = [p for p in self._particles if p['life'] > 0]
        for p in self._particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.15   # gravity
            p['life'] -= 1

        self.update()

    # ── Qt paint ───────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # Background gradient
        top_c, bot_c = self._MOOD_COLOURS.get(self._mood, ('#f5f5f5', '#eeeeee'))
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(top_c))
        grad.setColorAt(1, QColor(bot_c))
        painter.fillRect(0, 0, w, h, QBrush(grad))

        # Centre the panda
        cx = w // 2
        cy = int(h * 0.52 - self._bob - self._bounce_y)

        scale = min(w, h) / 320.0  # scale to fit widget
        self._draw_panda(painter, cx, cy, scale)
        self._draw_particles(painter)
        self._draw_mood_label(painter, w, h)

        painter.end()

    def _draw_panda(self, p: QPainter, cx: int, cy: int, s: float) -> None:
        """Draw the full panda at (cx, cy) with scale s."""
        # Shadow
        shadow = QColor(0, 0, 0, 30)
        p.setBrush(QBrush(shadow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 45*s), int(cy + 70*s), int(90*s), int(20*s))

        # Body
        p.setBrush(QBrush(self._body_color))
        p.setPen(QPen(QColor(200, 200, 200), max(1, int(1.5*s))))
        p.drawEllipse(int(cx - 42*s), int(cy + 5*s), int(84*s), int(75*s))

        # Tummy patch
        p.setBrush(QBrush(QColor(230, 230, 230)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 22*s), int(cy + 20*s), int(44*s), int(40*s))

        # Black leg patches
        p.setBrush(QBrush(self._ear_color))
        p.drawEllipse(int(cx - 38*s), int(cy + 55*s), int(28*s), int(28*s))   # left leg
        p.drawEllipse(int(cx + 10*s), int(cy + 55*s), int(28*s), int(28*s))   # right leg

        # Arms
        arm_angle = math.sin(self._tick * 1.2) * 8 if self._animation == 'idle' else math.sin(self._tick * 3) * 20
        # left arm
        p.save()
        p.translate(int(cx - 40*s), int(cy + 25*s))
        p.rotate(-30 + arm_angle)
        p.setBrush(QBrush(self._ear_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(-10*s), 0, int(22*s), int(36*s))
        p.restore()
        # right arm
        p.save()
        p.translate(int(cx + 40*s), int(cy + 25*s))
        p.rotate(30 - arm_angle)
        p.setBrush(QBrush(self._ear_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(-12*s), 0, int(22*s), int(36*s))
        p.restore()

        # Head
        p.setBrush(QBrush(self._body_color))
        p.setPen(QPen(QColor(200, 200, 200), max(1, int(1.5*s))))
        p.drawEllipse(int(cx - 40*s), int(cy - 78*s), int(80*s), int(80*s))

        # Ears
        p.setBrush(QBrush(self._ear_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 48*s), int(cy - 90*s), int(28*s), int(28*s))  # left
        p.drawEllipse(int(cx + 20*s), int(cy - 90*s), int(28*s), int(28*s))  # right

        # Eye patches
        p.drawEllipse(int(cx - 28*s), int(cy - 55*s), int(22*s), int(18*s))  # left
        p.drawEllipse(int(cx + 6*s),  int(cy - 55*s), int(22*s), int(18*s))  # right

        # Eyes
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.setPen(Qt.PenStyle.NoPen)
        if self._blink_open:
            eye_h = int(12*s)
        else:
            eye_h = max(2, int(3*s))
        p.drawEllipse(int(cx - 26*s), int(cy - 53*s), int(18*s), eye_h)  # left
        p.drawEllipse(int(cx + 8*s),  int(cy - 53*s), int(18*s), eye_h)  # right

        # Pupils
        if self._blink_open:
            p.setBrush(QBrush(QColor(20, 20, 20)))
            p.drawEllipse(int(cx - 21*s), int(cy - 51*s), int(8*s), int(8*s))
            p.drawEllipse(int(cx + 13*s), int(cy - 51*s), int(8*s), int(8*s))
            # Highlight
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(int(cx - 19*s), int(cy - 50*s), int(3*s), int(3*s))
            p.drawEllipse(int(cx + 15*s), int(cy - 50*s), int(3*s), int(3*s))

        # Nose
        p.setBrush(QBrush(QColor(60, 40, 40)))
        p.drawEllipse(int(cx - 7*s), int(cy - 38*s), int(14*s), int(8*s))

        # Mouth — smile or frown based on mood
        mouth_path = QPainterPath()
        if self._mood in ('happy', 'excited'):
            mouth_path.moveTo(cx - 10*s, cy - 30*s)
            mouth_path.quadTo(cx, cy - 22*s, cx + 10*s, cy - 30*s)
        elif self._mood in ('sad', 'angry'):
            mouth_path.moveTo(cx - 10*s, cy - 24*s)
            mouth_path.quadTo(cx, cy - 32*s, cx + 10*s, cy - 24*s)
        else:
            mouth_path.moveTo(cx - 8*s, cy - 28*s)
            mouth_path.lineTo(cx + 8*s, cy - 28*s)
        p.setPen(QPen(QColor(80, 50, 50), max(2, int(2*s))))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(mouth_path)

        # Mood sparkle emoji above head
        if self._mood == 'happy':
            self._draw_text(p, cx, int(cy - 100*s), '✨', int(14*s))
        elif self._mood == 'excited':
            self._draw_text(p, cx, int(cy - 100*s), '🎉', int(14*s))
        elif self._mood == 'sad':
            self._draw_text(p, cx, int(cy - 100*s), '💧', int(14*s))
        elif self._mood == 'tired':
            self._draw_text(p, cx, int(cy - 100*s), '💤', int(14*s))
        elif self._mood == 'curious':
            self._draw_text(p, cx, int(cy - 100*s), '❓', int(14*s))
        elif self._mood == 'angry':
            self._draw_text(p, cx, int(cy - 100*s), '💢', int(14*s))

        # Equipped hat
        if self._hat:
            self._draw_text(p, cx, int(cy - 108*s), self._hat, int(20*s))

    @staticmethod
    def _draw_text(p: QPainter, cx: int, y: int, text: str, size: int) -> None:
        font = QFont()
        font.setPixelSize(max(8, size))
        p.setFont(font)
        p.setPen(QPen(Qt.GlobalColor.black))
        metrics = p.fontMetrics()
        tw = metrics.horizontalAdvance(text)
        p.drawText(cx - tw // 2, y, text)

    def _draw_particles(self, p: QPainter) -> None:
        for part in self._particles:
            c = QColor(part['r'], part['g'], part['b'], max(0, int(part['life'] * 5)))
            p.setBrush(QBrush(c))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(part['x'] - 3, part['y'] - 3, 6, 6))

    def _draw_mood_label(self, p: QPainter, w: int, h: int) -> None:
        font = QFont()
        font.setPixelSize(11)
        p.setFont(font)
        p.setPen(QPen(QColor(100, 100, 100)))
        label = f"Mood: {self._mood}"
        p.drawText(QRect(0, h - 24, w, 20), Qt.AlignmentFlag.AlignCenter, label)

    # ── Interaction ─────────────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_bouncing = True
            self._bounce_vel = 12.0
            self._spawn_particles()
            self.clicked.emit()
        super().mousePressEvent(event)

    def _spawn_particles(self) -> None:
        cx, cy = self.width() // 2, int(self.height() * 0.45)
        for _ in range(12):
            self._particles.append({
                'x': cx + random.randint(-20, 20),
                'y': cy,
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-6, -2),
                'r': random.randint(200, 255),
                'g': random.randint(150, 255),
                'b': random.randint(50, 200),
                'life': 30,
            })

    # ── Public interface (matches PandaOpenGLWidget) ────────────────────────────

    def set_mood(self, mood: str) -> None:
        if mood != self._mood:
            self._mood = mood
            self._animation = mood
            self.mood_changed.emit(mood)
            self.update()

    def set_animation(self, animation: str) -> None:
        if animation != self._animation:
            self._animation = animation
            self.animation_changed.emit(animation)

    def set_color(self, color_type: str, color_rgb: tuple) -> None:
        try:
            color = QColor(*color_rgb[:3])
            if color_type in ('body', 'fur'):
                self._body_color = color
            elif color_type in ('patch', 'ear', 'accent'):
                self._ear_color = color
            self.update()
        except Exception as exc:
            logger.debug("set_color error: %s", exc)

    def set_trail(self, trail_type: str, trail_data: dict) -> None:
        # Trail effects are visual-only; log and ignore for the 2D widget
        logger.debug("PandaWidget2D.set_trail: %s %s", trail_type, trail_data)

    def preview_item(self, item_id: str) -> None:
        # Hat / accessory preview — map known items to emoji
        _hats = {
            'party_hat': '🎉', 'crown': '👑', 'wizard_hat': '🧙',
            'flower': '🌸', 'bow': '🎀', 'santa': '🎅',
        }
        self._hat = _hats.get(str(item_id).lower())
        self.update()

    def equip_item(self, item_data: dict) -> None:
        item_id = item_data.get('id', '') if isinstance(item_data, dict) else str(item_data)
        if item_id and item_id not in self._equipped_items:
            self._equipped_items.append(item_id)
        self.preview_item(item_id)

    def update_appearance(self) -> None:
        """Trigger a full redraw of the panda widget.  Called by CustomizationPanelQt."""
        self.update()
