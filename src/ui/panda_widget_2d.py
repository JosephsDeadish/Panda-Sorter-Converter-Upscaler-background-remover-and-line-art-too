"""
2-D Panda Widget — QPainter-based fallback for when PyOpenGL is unavailable.

Draws a charming 2-D panda using QPainter primitives with full secondary motion:
- Fatigue accumulation / auto-sleep
- Personality randomness (asymmetric blink, ear twitch bias, breathing amplitude)
- Cursor awareness (looks toward cursor, saccades)
- Ear spring follow-through physics
- Idle micro-loop pauses and reaction delays
- Smooth easing on animation transitions

Exposes the same public interface as PandaOpenGLWidget so main.py uses either
widget interchangeably.
"""

from __future__ import annotations

import logging
import math
import random
import time
from typing import Optional

try:
    from PyQt6.QtWidgets import QWidget, QSizePolicy
    from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, pyqtSignal, QRectF, QPointF
    from PyQt6.QtGui import (
        QPainter, QColor, QPen, QBrush, QFont, QMouseEvent,
        QPainterPath, QLinearGradient,
    )
    _QT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    _QT_AVAILABLE = False
    QWidget = object  # type: ignore[misc,assignment]

logger = logging.getLogger(__name__)

# ── module-level easing helpers ───────────────────────────────────────────────

def _ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3

def _ease_in_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2

BOUNCE_INITIAL_VEL = 120.0   # px/s upward velocity given to panda on click


def _spring_step(pos: float, vel: float, target: float,
                 stiff: float, damp: float, dt: float) -> tuple[float, float]:
    """Advance one spring simulation step. Returns (new_pos, new_vel)."""
    acc = -stiff * (pos - target) - damp * vel
    vel = vel + acc * dt
    pos = pos + vel * dt
    return pos, vel


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
        class _SigStub:
            def __init__(self, *a): pass
            def connect(self, *a): pass
            def disconnect(self, *a): pass
            def emit(self, *a): pass
        clicked = _SigStub()        # type: ignore[assignment]
        mood_changed = _SigStub()   # type: ignore[assignment]
        animation_changed = _SigStub()  # type: ignore[assignment]

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

        # Make the widget fully transparent — no white or coloured panel behind the panda.
        # WA_TranslucentBackground + NoSystemBackground tells Qt to not fill the widget
        # background at all; the panda is painted directly on whatever is behind it.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)

        self.panda = panda_character  # PandaCharacter or None

        # ── State ─────────────────────────────────────────────────────────────
        self._mood = 'neutral'
        self._animation = 'idle'
        self._body_color = QColor(245, 245, 245)
        self._ear_color  = QColor(30, 30, 30)
        self._hat: Optional[str] = None
        self._hair_style: str = ''
        self._fur_style: str = 'classic'
        self._equipped_items: dict = {}   # slot → item_id

        # ── Per-instance personality randomness ────────────────────────────────
        r = random.Random()   # seeded fresh each time — unique per panda instance
        self._micro = {
            'blink_base':        r.uniform(2.8, 5.5),   # seconds between blinks
            'blink_double_prob': r.uniform(0.06, 0.18),
            'breathe_amp':       r.uniform(3.0, 6.5),   # idle bob amplitude px
            'breathe_speed':     r.uniform(0.8, 1.4),   # multiplier
            'sway_speed':        r.uniform(0.9, 1.25),
            'ear_twitch_bias':   r.choice([0, 1]),       # which ear twitches more
            'head_tilt':         r.uniform(-3.5, 3.5),  # degrees, fixed per instance
            'reaction_delay':    r.uniform(0.05, 0.25), # seconds before reacting
        }

        # ── Animation tick vars ────────────────────────────────────────────────
        self._tick = 0.0
        self._last_t = time.time()
        self._bob = 0.0
        self._arm_l = 0.0      # arm swing angle degrees
        self._arm_r = 0.0
        self._arm_vel_l = 0.0  # arm spring velocities
        self._arm_vel_r = 0.0

        # ── Blink state ────────────────────────────────────────────────────────
        self._blink_phase = 0.0          # 0=open, >0 closing/opening
        self._blink_speed = 8.0
        self._double_blink = False
        self._next_blink_t = time.time() + self._micro['blink_base']

        # ── Ear spring physics (follow-through) ────────────────────────────────
        self._ear_pos = [0.0, 0.0]   # deflection degrees
        self._ear_vel = [0.0, 0.0]

        # ── Cursor / saccade tracking ──────────────────────────────────────────
        self._cursor_norm = QPointF(0.5, 0.5)   # 0-1 in widget space
        self._eye_x = 0.0   # px offset for pupils (−ve = look left)
        self._eye_y = 0.0
        self._saccade_target_x = 0.0
        self._saccade_target_y = 0.0
        self._next_saccade_t = time.time() + random.uniform(3.0, 6.0)
        self._surprised_eye_t = 0.0    # remaining seconds of wide-eye
        self.setMouseTracking(True)

        # ── Fatigue / emotion ──────────────────────────────────────────────────
        self._fatigue = 0.0
        self._fatigue_rate     = 0.004 / 30.0   # per frame at 30 fps
        self._fatigue_recovery = 0.012 / 30.0
        self._boredom_t   = 0.0
        self._boredom_threshold = random.uniform(20.0, 35.0)

        # ── Idle-loop pause ────────────────────────────────────────────────────
        self._idle_pause_t = 0.0    # remaining pause seconds
        self._next_pause_in = random.uniform(9.0, 20.0)

        # ── Bounce physics ─────────────────────────────────────────────────────
        self._is_bouncing = False
        self._bounce_vel = 0.0
        self._bounce_y = 0.0

        # ── Particles ─────────────────────────────────────────────────────────
        self._particles: list[dict] = []

        # ── Timer ──────────────────────────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_animation)
        self._timer.start(33)   # ~30 fps

        self.setMinimumSize(200, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ── Animation loop ──────────────────────────────────────────────────────────

    def _tick_animation(self) -> None:
        now = time.time()
        dt = min(now - self._last_t, 0.10)
        self._last_t = now
        self._tick += dt

        # ── Fatigue ────────────────────────────────────────────────────────────
        if self._animation == 'sleeping':
            self._fatigue = max(0.0, self._fatigue - self._fatigue_recovery)
        else:
            self._fatigue = min(1.0, self._fatigue + self._fatigue_rate)
        if self._fatigue >= 0.98 and self._animation not in ('sleeping',):
            self._animation = 'sleeping'
            self.animation_changed.emit('sleeping')

        # ── Boredom ────────────────────────────────────────────────────────────
        if self._animation == 'idle':
            self._boredom_t += dt
        else:
            self._boredom_t = 0.0

        # ── Idle-loop pause ────────────────────────────────────────────────────
        if self._idle_pause_t > 0:
            self._idle_pause_t -= dt
        else:
            self._next_pause_in -= dt
            if self._next_pause_in <= 0:
                self._idle_pause_t = random.uniform(0.1, 0.35)
                self._next_pause_in = random.uniform(9.0, 20.0)

        # ── Idle bob (layered breathing + tiny sway) ───────────────────────────
        sp = self._micro['breathe_speed']
        amp = self._micro['breathe_amp']
        if self._idle_pause_t > 0:
            self._bob = self._bob * 0.85   # freeze: ease to 0
        elif self._animation == 'sleeping':
            self._bob = math.sin(self._tick * 0.4 * sp) * 2.0
        elif self._animation in ('excited', 'celebrating'):
            self._bob = math.sin(self._tick * 3.5 * sp) * 10.0 + math.sin(self._tick * 7.0) * 3.0
        elif self._animation in ('sad', 'tired', 'working'):
            self._bob = math.sin(self._tick * 0.5 * sp) * 2.0
        else:
            self._bob = (math.sin(self._tick * 1.0 * sp) * amp
                         + math.sin(self._tick * 2.7 * sp) * amp * 0.15)

        # ── Arm spring physics (overshoot + settle) ────────────────────────────
        target_l, target_r = 0.0, 0.0
        if self._animation in ('waving', 'celebrating'):
            target_l = -25.0
            target_r = -25.0 + math.sin(self._tick * 3.0) * 18.0
        elif self._animation == 'idle':
            swing = math.sin(self._tick * 1.0 * self._micro['sway_speed']) * 7.0
            target_l = swing
            target_r = -swing
        stiff, damp = 18.0, 5.5
        self._arm_l, self._arm_vel_l = _spring_step(self._arm_l, self._arm_vel_l, target_l, stiff, damp, dt)
        self._arm_r, self._arm_vel_r = _spring_step(self._arm_r, self._arm_vel_r, target_r, stiff, damp, dt)

        # ── Ear spring follow-through ──────────────────────────────────────────
        body_jerk = abs(self._bob - getattr(self, '_prev_bob', self._bob)) * 80.0
        self._prev_bob = self._bob
        stiff_e, damp_e = 22.0, 6.0
        # Asymmetric twitch
        for i in range(2):
            nudge = body_jerk * 0.05 * (1 - 2 * i)   # opposite phases
            if random.random() < (0.006 if i == self._micro['ear_twitch_bias'] else 0.002):
                nudge += random.uniform(4.0, 12.0) * (-1 if i == 0 else 1)
            self._ear_vel[i] += (-stiff_e * self._ear_pos[i]
                                 - damp_e * self._ear_vel[i] + nudge) * dt
            self._ear_pos[i] += self._ear_vel[i] * dt
            self._ear_pos[i] = max(-15.0, min(15.0, self._ear_pos[i]))

        # ── Time-based blink ───────────────────────────────────────────────────
        if now >= self._next_blink_t:
            self._blink_phase = 0.001
            self._double_blink = random.random() < self._micro['blink_double_prob']
            jitter = random.uniform(-0.5, 0.5)
            self._next_blink_t = (now + self._micro['blink_base']
                                  + (3.0 if self._double_blink else 0.0) + jitter)
            self._blink_speed = max(5.0, 8.0 - 3.0 * self._fatigue)
        if self._blink_phase > 0.0:
            self._blink_phase += self._blink_speed * dt
            if self._blink_phase >= 2.0:
                if self._double_blink:
                    self._blink_phase = 0.0
                    self._double_blink = False
                    self._next_blink_t = now + 0.15
                else:
                    self._blink_phase = 0.0

        # ── Saccade / eye tracking ─────────────────────────────────────────────
        if now >= self._next_saccade_t:
            self._saccade_target_x = random.uniform(-4.0, 4.0)
            self._saccade_target_y = random.uniform(-2.0, 2.0)
            self._next_saccade_t = now + random.uniform(2.5, 5.5)
        # Cursor pull (soft, eyes lead head)
        cx_pull = (self._cursor_norm.x() - 0.5) * 5.0
        cy_pull = (self._cursor_norm.y() - 0.5) * 3.0
        target_ex = cx_pull + self._saccade_target_x
        target_ey = cy_pull + self._saccade_target_y
        self._eye_x += (target_ex - self._eye_x) * min(1.0, 8.0 * dt)
        self._eye_y += (target_ey - self._eye_y) * min(1.0, 8.0 * dt)

        # ── Surprised eye timer ────────────────────────────────────────────────
        if self._surprised_eye_t > 0:
            self._surprised_eye_t = max(0.0, self._surprised_eye_t - dt)

        # ── Bounce physics ─────────────────────────────────────────────────────
        if self._is_bouncing:
            self._bounce_vel -= 35.0 * dt
            self._bounce_y   += self._bounce_vel * dt
            if self._bounce_y <= 0:
                self._bounce_y = 0.0
                self._bounce_vel = 0.0
                self._is_bouncing = False

        # ── Particles ─────────────────────────────────────────────────────────
        self._particles = [p for p in self._particles if p['life'] > 0]
        for p in self._particles:
            p['x']  += p['vx']
            p['y']  += p['vy']
            p['vy'] += 0.15
            p['life'] -= 1

        self.update()

    # ── Qt paint ───────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # WA_TranslucentBackground + WA_NoSystemBackground tell Qt not to fill
        # the backing store.  We must NOT use CompositionMode_Source here: on
        # platforms without window-manager compositing (X11 without a compositor,
        # virtual displays) Source-mode fills each frame with opaque black, making
        # the entire overlay solid black and hiding the application content behind
        # the panda.  Skipping the fill entirely lets the Qt backing store stay
        # transparent — old panda pixels are erased by Qt before paintEvent is
        # called (Qt always calls begin() on a clean buffer for top-level
        # transparent windows), so animation trails do not accumulate.
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

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
        p.setBrush(QBrush(QColor(0, 0, 0, 30)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 45*s), int(cy + 70*s), int(90*s), int(20*s))

        # Body — slight squash on hard landing
        body_sx = 1.0
        body_sy = 1.0
        if abs(self._bounce_y) > 3:   # visible while descending or at peak
            body_sx = 0.93
            body_sy = 1.07
        p.setBrush(QBrush(self._body_color))
        p.setPen(QPen(QColor(200, 200, 200), max(1, int(1.5*s))))
        p.save()
        p.translate(cx, int(cy + 42*s))
        p.scale(body_sx, body_sy)
        p.drawEllipse(int(-42*s), int(-37*s), int(84*s), int(75*s))
        p.restore()

        # Tummy patch
        p.setBrush(QBrush(QColor(230, 230, 230)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 22*s), int(cy + 20*s), int(44*s), int(40*s))

        # Black leg patches
        p.setBrush(QBrush(self._ear_color))
        p.drawEllipse(int(cx - 38*s), int(cy + 55*s), int(28*s), int(28*s))
        p.drawEllipse(int(cx + 10*s), int(cy + 55*s), int(28*s), int(28*s))

        # Arms — driven by spring physics
        for side, base_x, sign in (('l', -40, -1), ('r', 40, 1)):
            ang = self._arm_l if side == 'l' else self._arm_r
            p.save()
            p.translate(int(cx + base_x*s), int(cy + 25*s))
            p.rotate(sign * 30 + ang)
            p.setBrush(QBrush(self._ear_color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(-11*s), 0, int(22*s), int(36*s))
            # paw pad
            p.setBrush(QBrush(QColor(220, 150, 160)))
            p.drawEllipse(int(-6*s), int(28*s), int(12*s), int(8*s))
            p.restore()

        # Head — apply head-tilt preference + cursor-driven micro tilt
        head_tilt = self._micro['head_tilt'] + (self._cursor_norm.x() - 0.5) * 4.0
        p.save()
        p.translate(cx, int(cy - 38*s))
        p.rotate(head_tilt)
        p.setBrush(QBrush(self._body_color))
        p.setPen(QPen(QColor(200, 200, 200), max(1, int(1.5*s))))
        p.drawEllipse(int(-40*s), int(-40*s), int(80*s), int(80*s))

        # ── Ears (with spring deflection) ──────────────────────────────────────
        p.setBrush(QBrush(self._ear_color))
        p.setPen(Qt.PenStyle.NoPen)
        for i, (ex, ey) in enumerate(((-34, -32), (20, -32))):
            ep = self._ear_pos[i]   # spring deflection degrees
            p.save()
            p.translate(int(ex*s), int(ey*s))
            p.rotate(ep)
            p.drawEllipse(int(-14*s), int(-14*s), int(28*s), int(28*s))
            # Inner ear pink
            p.setBrush(QBrush(QColor(220, 150, 160)))
            p.drawEllipse(int(-8*s), int(-8*s), int(16*s), int(16*s))
            p.restore()
            p.setBrush(QBrush(self._ear_color))

        # ── Eye patches ────────────────────────────────────────────────────────
        p.setBrush(QBrush(self._ear_color))
        p.drawEllipse(int(-28*s), int(-18*s), int(22*s), int(18*s))
        p.drawEllipse(int(6*s),   int(-18*s), int(22*s), int(18*s))

        # ── Eyes ───────────────────────────────────────────────────────────────
        # Blink scale: phase 0-1 closing, 1-2 opening
        if self._blink_phase > 0.0:
            if self._blink_phase < 1.0:
                blink_scale = max(0.05, 1.0 - _ease_in_out_cubic(self._blink_phase))
            else:
                blink_scale = max(0.05, _ease_out_cubic(self._blink_phase - 1.0))
        else:
            droop = self._fatigue * 0.30
            blink_scale = max(0.35, 1.0 - droop)

        # Wide-eye on surprised
        if self._surprised_eye_t > 0:
            blink_scale = min(1.25, blink_scale + 0.3)

        eye_h = max(2, int(12 * s * blink_scale))

        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(-26*s), int(-16*s), int(18*s), eye_h)
        p.drawEllipse(int(8*s),   int(-16*s), int(18*s), eye_h)

        # Pupils with eye-tracking offset
        if blink_scale > 0.3:
            ex_off = int(self._eye_x * s)
            ey_off = int(self._eye_y * s)
            p.setBrush(QBrush(QColor(20, 20, 20)))
            p.drawEllipse(int(-21*s + ex_off), int(-14*s + ey_off), int(8*s), int(8*s))
            p.drawEllipse(int(13*s + ex_off),  int(-14*s + ey_off), int(8*s), int(8*s))
            # Specular highlights
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(int(-19*s + ex_off), int(-13*s + ey_off), int(3*s), int(3*s))
            p.drawEllipse(int(15*s + ex_off),  int(-13*s + ey_off), int(3*s), int(3*s))

        # ── Snout / nose / mouth ────────────────────────────────────────────────
        p.setBrush(QBrush(QColor(235, 225, 215)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(-12*s), int(-2*s), int(24*s), int(14*s))   # muzzle

        p.setBrush(QBrush(QColor(50, 35, 35)))
        p.drawEllipse(int(-7*s), int(-2*s), int(14*s), int(8*s))      # nose

        mouth = QPainterPath()
        if self._mood in ('happy', 'excited'):
            mouth.moveTo(-9*s, 10*s)
            mouth.quadTo(0, 17*s, 9*s, 10*s)
        elif self._mood in ('sad', 'angry'):
            mouth.moveTo(-9*s, 14*s)
            mouth.quadTo(0, 8*s, 9*s, 14*s)
        else:
            mouth.moveTo(-7*s, 12*s)
            mouth.lineTo(7*s, 12*s)
        p.setPen(QPen(QColor(80, 50, 50), max(2, int(2*s))))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(mouth)

        p.restore()   # restore head matrix

        # ── Mood emoji above head ──────────────────────────────────────────────
        mood_emoji = {
            'happy': '✨', 'excited': '🎉', 'sad': '💧', 'tired': '💤',
            'sleeping': '💤', 'curious': '❓', 'angry': '💢',
            'bored': '😐', 'celebrating': '🎊',
        }
        emoji = mood_emoji.get(self._mood)
        if emoji:
            self._draw_text(p, cx, int(cy - 100*s), emoji, int(14*s))

        # Hat
        if self._hat:
            self._draw_text(p, cx, int(cy - 112*s), self._hat, int(20*s))

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

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        """Track cursor for eye-following."""
        w, h = max(1, self.width()), max(1, self.height())
        self._cursor_norm = QPointF(event.position().x() / w, event.position().y() / h)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_bouncing = True
            self._bounce_vel = BOUNCE_INITIAL_VEL
            self._surprised_eye_t = 0.25
            # Arm kick toward surprise
            self._arm_vel_l = -15.0
            self._arm_vel_r = -15.0
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
        if hasattr(mood, 'value'):
            mood = mood.value
        mood = str(mood)
        if mood != self._mood:
            self._mood = mood
            # kick surprise eyes on positive transitions
            if mood in ('happy', 'excited', 'celebrating'):
                self._surprised_eye_t = 0.2
                self._arm_vel_l = -12.0
                self._arm_vel_r = -12.0
            self.mood_changed.emit(mood)
            self.update()

    def set_animation(self, animation: str) -> None:
        if hasattr(animation, 'value'):
            animation = animation.value
        animation = str(animation)
        if animation != self._animation:
            self._animation = animation
            self.animation_changed.emit(animation)

    # ── GL-compatible API stubs ──────────────────────────────────────────────
    # These methods mirror the PandaOpenGLWidget API so that main.py can call
    # them on self.panda_widget regardless of whether it's a GL or 2D widget.

    def set_animation_state(self, state: str) -> None:
        """GL-compatible alias for set_animation + mood update."""
        _STATE_TO_MOOD = {
            'idle': 'neutral', 'walking': 'neutral', 'running': 'excited',
            'sleeping': 'tired', 'eating': 'happy', 'celebrating': 'excited',
            'waving': 'happy', 'sitting': 'neutral', 'sad': 'sad',
            'angry': 'angry', 'surprised': 'surprised', 'wall_hit': 'angry',
            'rolling': 'playful', 'spinning': 'excited', 'dancing': 'excited',
            'thinking': 'curious', 'grooming': 'content', 'sniffing': 'curious',
        }
        self.set_animation(state)
        mood = _STATE_TO_MOOD.get(state, 'neutral')
        self.set_mood(mood)

    @property
    def animation_state(self) -> str:
        """GL-compatible property: current animation name."""
        return self._animation

    def walk_to_position(self, x: float, y: float, z: float,
                         callback=None, speed: float = 2.0) -> None:
        """GL-compatible stub: 2D panda can't physically walk; bounce and call callback."""
        self.set_animation_state('walking')
        self._is_bouncing = True
        self._bounce_vel = 8.0
        if callback is not None:
            QTimer.singleShot(600, callback)

    def set_micro_emotion(self, emotion_name: str, weight: float = 0.8) -> None:
        """GL-compatible stub: map to nearest mood or eye reaction."""
        _MICRO_TO_MOOD = {
            'happy': 'happy', 'curious': 'curious', 'playful': 'playful',
            'sad': 'sad', 'angry': 'angry', 'surprised': 'surprised',
            'excited': 'excited', 'tired': 'tired', 'content': 'content',
        }
        if weight > 0.5:
            mood = _MICRO_TO_MOOD.get(emotion_name.lower(), self._mood)
            if mood != self._mood:
                self.set_mood(mood)
        if emotion_name.lower() in ('surprised', 'curious', 'excited'):
            self._surprised_eye_t = 0.3 * weight

    def notify_file_dragged(self, file_path: str) -> None:
        """GL-compatible: trigger a sniff/curious reaction."""
        self.set_micro_emotion('curious', 0.8)
        self._surprised_eye_t = 0.25

    def notify_button_nearby(self) -> None:
        """GL-compatible: cursor is near a UI button — trigger a small poke reaction."""
        self._arm_vel_r += -8.0
        self._surprised_eye_t = 0.1

    def get_idle_sub_state(self) -> str:
        """GL-compatible: 2D widget doesn't have sub-states; return empty string."""
        return ''

    def set_fur_style(self, style_id: str) -> None:
        """GL-compatible: map fur-style id to nearest body/ear colour pair."""
        _FUR_COLORS = {
            'classic':       (QColor(245, 245, 245), QColor(30, 30, 30)),
            'albino':        (QColor(255, 248, 240), QColor(220, 180, 180)),
            'snow_panda':    (QColor(240, 248, 255), QColor(180, 200, 220)),
            'golden':        (QColor(255, 230, 160), QColor(160, 110, 40)),
            'red_panda':     (QColor(200, 100, 50),  QColor(60, 40, 20)),
            'midnight':      (QColor(30, 30, 60),    QColor(10, 10, 30)),
            'galaxy':        (QColor(60, 40, 90),    QColor(20, 10, 50)),
            'cherry_blossom':(QColor(255, 210, 220), QColor(190, 100, 120)),
            'ocean':         (QColor(160, 210, 230), QColor(40, 80, 130)),
            'forest':        (QColor(130, 180, 120), QColor(40, 80, 40)),
        }
        sid = str(style_id).lower()
        body_col, ear_col = _FUR_COLORS.get(sid, _FUR_COLORS['classic'])
        self._fur_style = sid
        self._body_color = body_col
        self._ear_color  = ear_col
        self.update()

    def set_hair_style(self, style_id: str) -> None:
        """GL-compatible: store hair style id (used in accessory overlay)."""
        self._hair_style = str(style_id)
        self.update()

    def equip_clothing(self, slot: str, clothing_item) -> None:
        """GL-compatible: record equipped clothing and refresh."""
        item_id = (clothing_item.get('id', '') if isinstance(clothing_item, dict)
                   else str(clothing_item))
        if item_id:
            self._equipped_items[slot] = item_id
        self.preview_item(item_id)

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
        slot = item_data.get('slot', 'misc') if isinstance(item_data, dict) else 'misc'
        if item_id:
            self._equipped_items[slot] = item_id
        self.preview_item(item_id)

    def update_appearance(self) -> None:
        """Trigger a full redraw of the panda widget.  Called by CustomizationPanelQt."""
        self.update()

    def add_item_3d(self, item_type: str, x: float = 0.0, y: float = 0.0,
                    z: float = 0.0, **kwargs) -> None:
        """GL-compatible stub: 3D items are not rendered in the 2D widget."""
        logger.debug("PandaWidget2D.add_item_3d: %s ignored (2D mode)", item_type)

    def add_item_from_emoji(self, emoji: str, name: str = None,
                            position: tuple = (0, 0), **kwargs) -> None:
        """GL-compatible stub: show emoji as a transient hat/overlay in 2D mode."""
        self._hat = emoji
        self.update()

    def clear_items(self) -> None:
        """GL-compatible stub: clear all 3D scene items."""
        self._hat = None
        self._equipped_items.clear()
        self.update()

    # ------------------------------------------------------------------
    # GL-compatible stubs — these methods exist on PandaOpenGLWidget and
    # are called via hasattr() guards in main.py.  The 2D widget silently
    # ignores calls that would require a 3D scene.
    # ------------------------------------------------------------------

    def open_furniture(self, furniture_id: str) -> None:
        """GL-compatible stub: play furniture-open animation (2D: no-op)."""
        pass

    def unequip_clothing(self, slot: str) -> None:
        """GL-compatible stub: remove a clothing slot (2D: clear equipped)."""
        self._equipped_items.pop(slot, None)
        self.update()

    def play_animation_sequence(self, states: list, durations: list) -> None:
        """GL-compatible stub: play a scripted animation sequence (2D: set first state)."""
        if states:
            self.set_animation_state(states[0])

    def set_autonomous_mode(self, enabled: bool) -> None:
        """GL-compatible stub: enable/disable autonomous panda behaviour (2D: no-op)."""
        pass

    def apply_squash_effect(self, scale: float = 0.85) -> None:
        """GL-compatible stub: apply squash/stretch deformation (2D: no-op)."""
        pass

    def interact_with_item(self, item_index: int, interaction_type: str = 'auto') -> None:
        """GL-compatible stub: panda interacts with a 3D scene item (2D: no-op)."""
        pass

    def walk_to_item(self, item_index: int, callback=None) -> None:
        """GL-compatible stub: walk to a 3D item position (2D: invoke callback directly)."""
        if callable(callback):
            callback()

    def get_info(self) -> dict:
        """GL-compatible stub: return panda state info dict."""
        return {
            'mood': self._mood,
            'animation': self._animation_state,
            'fur_style': self._fur_style,
            'widget_type': '2d',
        }

    # ------------------------------------------------------------------
    # Interaction animation stubs — mirror the GL widget API so that the
    # overlay (transparent_panda_overlay) and PandaInteractionBehavior can
    # call these with hasattr() checks and the 2D widget responds sensibly.
    # ------------------------------------------------------------------

    def start_bite_tab(self) -> None:
        """GL-compatible: panda bites a tab — play surprised + curious reaction in 2D."""
        self._surprised_eye_t = 0.4
        self._micro_emotion['playful'] = 0.9
        self._micro_emotion['curious'] = 0.6
        self.set_animation_state('waving')
        QTimer.singleShot(1200, lambda: self.set_animation_state('idle')
                          if self._animation_state == 'waving' else None)

    def start_hug_window(self) -> None:
        """GL-compatible: panda hugs a window edge — play climbing_wall in 2D."""
        self.set_animation_state('climbing_wall')
        self._micro_emotion['playful'] = 0.8
        QTimer.singleShot(3000, lambda: self.set_animation_state('falling_back')
                          if self._animation_state == 'climbing_wall' else None)
        QTimer.singleShot(4200, lambda: self.set_animation_state('idle')
                          if self._animation_state == 'falling_back' else None)

    def start_sit_on_panel(self) -> None:
        """GL-compatible: panda sits on a panel — play sitting_back state in 2D."""
        self.set_animation_state('sitting_back')
        self._micro_emotion['content'] = 0.9

    def start_working(self) -> None:
        """GL-compatible: panda starts working animation."""
        self.set_animation_state('working')
        self._micro_emotion['content'] = 0.7

    def stop_working(self) -> None:
        """GL-compatible: panda stops working animation."""
        self.set_animation_state('idle')
