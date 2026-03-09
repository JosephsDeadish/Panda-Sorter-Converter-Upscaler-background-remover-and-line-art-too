"""
panda_widget_2d.py - 2D QPainter floating overlay panda widget.

Paints an animated panda companion directly onto the application window using
QPainter. All public API symbols are preserved so that existing import sites
and call sites remain valid whether or not PyQt6 is available.
"""

import math

# ── PyQt6 imports ────────────────────────────────────────────────────────────
try:
    from PyQt6.QtWidgets import QWidget
    from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QRectF, QPointF
    from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
    _QT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    _QT_AVAILABLE = False

    class _StubSignal:
        """Minimal signal stub used when PyQt6 is unavailable."""
        def __init__(self, *args, **kwargs):
            pass
        def connect(self, *args, **kwargs):
            pass
        def disconnect(self, *args, **kwargs):
            pass
        def emit(self, *args, **kwargs):
            pass

    def pyqtSignal(*args, **kwargs):  # noqa: N802 – name must match PyQt6 API
        return _StubSignal()

    class QWidget:  # type: ignore[no-redef]
        """Minimal QWidget stub used when PyQt6 is unavailable."""
        def __init__(self, parent=None):
            pass
        def hide(self):
            pass
        def update(self):
            pass
        def width(self):
            return 400
        def height(self):
            return 400

    class QTimer:  # type: ignore[no-redef]
        def __init__(self, *a):
            pass
        def start(self, *a):
            pass
        def stop(self, *a):
            pass
        def timeout(self):
            pass


# Always use QWidget (real or stub) so hide() is always available.
_Base = QWidget

# ── Animation constants ───────────────────────────────────────────────────────
_IDLE_BOB_SPEED:    float = 1.0   # radians / tick
_WALK_BOB_SPEED:    float = 2.5   # 2.5× faster when walking
_RUN_BOB_SPEED:     float = 5.0   # 5× faster when running
_IDLE_BOB_AMP:      float = 3.0   # pixels
_WALK_BOB_AMP:      float = 5.0   # pixels (slightly more than idle)
_RUN_BOB_AMP:       float = 8.0   # pixels (high amplitude for running)
_ARM_SWING_AMP_WALK: float = 25.0  # degrees
_ARM_SWING_AMP_RUN:  float = 45.0  # degrees


class PandaWidget2D(_Base):
    """
    2-D QPainter panda companion overlay widget.

    Draws an animated panda using QPainter. Designed to be used as a
    transparent full-window overlay: off-panda clicks pass through to the
    application UI below via event.ignore().
    """

    panda = None

    if _QT_AVAILABLE:
        clicked = pyqtSignal()
        mood_changed = pyqtSignal(str)
        animation_changed = pyqtSignal(str)
        food_eaten = pyqtSignal(str)
    else:
        clicked = pyqtSignal()
        mood_changed = pyqtSignal(str)
        animation_changed = pyqtSignal(str)
        food_eaten = pyqtSignal(str)

    def __init__(self, panda_character=None, parent=None):
        super().__init__(parent)
        self.hide()
        self.panda = panda_character
        self.animation_state = 'idle'

        # ── Animation state ───────────────────────────────────────────────────
        self._animation: str = 'idle'
        self._bob: float = 0.0          # current vertical bob offset in pixels
        self._bob_phase: float = 0.0    # oscillation phase (radians)
        self._arm_l: float = 0.0        # left arm angle (degrees)
        self._arm_r: float = 0.0        # right arm angle (degrees)
        self._arm_phase: float = 0.0    # arm swing phase

        # ── Animation timer — ticks at ~30 fps ────────────────────────────────
        if _QT_AVAILABLE:
            self._anim_timer = QTimer(self)
            self._anim_timer.timeout.connect(self._tick_animation)
            self._anim_timer.start(33)

    # ── Animation tick ────────────────────────────────────────────────────────

    def _tick_animation(self) -> None:
        """Advance the animation by one frame (~33 ms)."""
        anim = self._animation

        if anim == 'idle':
            # Idle: gentle bob, arms return to rest
            self._bob_phase += _IDLE_BOB_SPEED * 0.1
            self._bob = math.sin(self._bob_phase) * _IDLE_BOB_AMP
            self._arm_l += (0.0 - self._arm_l) * 0.1
            self._arm_r += (0.0 - self._arm_r) * 0.1

        elif anim in ('walking', 'walking_left', 'walking_right'):
            # Medium-speed bob with alternating arm swing for walking
            self._bob_phase += _WALK_BOB_SPEED * 0.1
            self._bob = math.sin(self._bob_phase) * _WALK_BOB_AMP
            # Arm swing: left and right arms alternate (walking gait)
            self._arm_phase += _WALK_BOB_SPEED * 0.1
            target_l = math.sin(self._arm_phase) * _ARM_SWING_AMP_WALK
            target_r = -target_l   # opposite phase for natural walking swing
            self._arm_l += (target_l - self._arm_l) * 0.3
            self._arm_r += (target_r - self._arm_r) * 0.3

        elif anim == 'running':
            # Fast-speed bob with high-amplitude arm swing for running
            self._bob_phase += _RUN_BOB_SPEED * 0.1
            self._bob = math.sin(self._bob_phase) * _RUN_BOB_AMP
            # Vigorous arm swing during running
            self._arm_phase += _RUN_BOB_SPEED * 0.1
            target_l = math.sin(self._arm_phase) * _ARM_SWING_AMP_RUN
            target_r = -target_l
            self._arm_l += (target_l - self._arm_l) * 0.5
            self._arm_r += (target_r - self._arm_r) * 0.5

        else:
            # Other animations: gentle idle bob
            self._bob_phase += _IDLE_BOB_SPEED * 0.1
            self._bob = math.sin(self._bob_phase) * _IDLE_BOB_AMP
            self._arm_l += (0.0 - self._arm_l) * 0.1
            self._arm_r += (0.0 - self._arm_r) * 0.1

        if _QT_AVAILABLE:
            self.update()

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """Paint the 2-D panda companion.

        Design notes:
        - Does NOT use CompositionMode_Source (causes opaque black fill on
          non-compositing X11 desktops; Qt clears the backing store for
          WA_TranslucentBackground widgets automatically before paintEvent).
        - Scale is capped at 0.8 to prevent the panda from growing too large
          on a full-window overlay (e.g. 1280×800 → max ~130 px tall).
        - Panda is vertically centred (h * 0.50), not pushed to the lower
          portion of the screen.
        """
        if not _QT_AVAILABLE:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Use SourceOver (default) — NOT CompositionMode_Source which would fill
        # the entire overlay with opaque black on non-compositing X11 systems.
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        w = self.width()
        h = self.height()

        # Scale: capped at 0.8 so the panda never becomes obstructive.
        # On a 1280×800 full-window overlay, min(w,h)/320 = 2.5 without the cap,
        # which would make the panda ~500 px tall and block the entire UI centre.
        scale = min(min(w, h) / 320.0, 0.8)
        unit = 40 * scale   # base unit in pixels

        # Panda centre: horizontally centred, vertically centred (h * 0.50).
        cx = w * 0.50
        cy = h * 0.50 + self._bob

        self._paint_panda_body(p, cx, cy, unit)
        p.end()

    def _paint_panda_body(self, p: 'QPainter', cx: float, cy: float, unit: float) -> None:
        """Paint all panda body parts using QPainter."""
        _white = QColor(235, 235, 228)
        _black = QColor(20, 15, 15)

        # Body
        p.setBrush(QBrush(_white))
        p.setPen(QPen(_black, max(1, unit * 0.04)))
        bw, bh = unit * 1.4, unit * 1.0
        p.drawEllipse(QRectF(cx - bw / 2, cy - bh / 2, bw, bh))

        # Head
        hx = cx
        hy = cy - bh * 0.62
        hr = unit * 0.65
        p.setBrush(QBrush(_white))
        p.drawEllipse(QRectF(hx - hr, hy - hr, hr * 2, hr * 2))

        # Ears
        for ex_off in (-0.55, 0.55):
            ex = hx + ex_off * hr
            ey = hy - hr * 0.70
            er = unit * 0.22
            p.setBrush(QBrush(_black))
            p.drawEllipse(QRectF(ex - er, ey - er, er * 2, er * 2))

        # Eye patches
        for ex_off in (-0.32, 0.32):
            ex = hx + ex_off * hr
            ey = hy - hr * 0.05
            p.setBrush(QBrush(_black))
            p.drawEllipse(QRectF(ex - unit * 0.22, ey - unit * 0.18,
                                  unit * 0.44, unit * 0.36))

        # Eyes (white highlights inside patches)
        p.setBrush(QBrush(QColor(255, 255, 255)))
        for ex_off in (-0.28, 0.28):
            ex = hx + ex_off * hr
            ey = hy - hr * 0.05
            p.drawEllipse(QRectF(ex - unit * 0.08, ey - unit * 0.08,
                                  unit * 0.16, unit * 0.16))

        # Nose
        p.setBrush(QBrush(_black))
        p.drawEllipse(QRectF(hx - unit * 0.14, hy + unit * 0.10,
                              unit * 0.28, unit * 0.18))

        # Arms with swing animation
        for side, ax_off, arm_angle in (
            (-1, -0.65, self._arm_l),
            (1,  0.65, self._arm_r),
        ):
            ax = cx + ax_off * unit
            ay = cy - unit * 0.15
            p.save()
            p.translate(ax, ay)
            p.rotate(arm_angle)
            p.setBrush(QBrush(_black))
            p.drawEllipse(QRectF(-unit * 0.20, 0, unit * 0.40, unit * 0.70))
            p.restore()

        # Legs
        for lx_off in (-0.42, 0.42):
            lx = cx + lx_off * unit
            ly = cy + bh * 0.40
            p.setBrush(QBrush(_black))
            p.drawEllipse(QRectF(lx - unit * 0.22, ly, unit * 0.44, unit * 0.60))

        # Belly spot (large white oval)
        p.setBrush(QBrush(_white))
        p.setPen(QPen(Qt.PenStyle.NoPen))
        p.drawEllipse(QRectF(cx - unit * 0.45, cy - unit * 0.30,
                              unit * 0.90, unit * 0.65))

    # ── Mouse interaction ─────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """Accept on-panda clicks; ignore off-panda clicks so they pass through."""
        if not _QT_AVAILABLE:
            return
        w = self.width()
        h = self.height()
        scale = min(min(w, h) / 320.0, 0.8)
        unit = 40 * scale
        cx = w * 0.50
        cy = h * 0.50 + self._bob
        # Simple ellipse hit-test around the panda body
        hit_w = unit * 1.6
        hit_h = unit * 2.2
        try:
            pos = event.position()
        except AttributeError:
            pos = event.pos()
        try:
            px, py = pos.x(), pos.y()
        except AttributeError:
            px, py = float(pos.x()), float(pos.y())
        dx = (px - cx) / (hit_w / 2)
        dy = (py - cy) / (hit_h / 2)
        if dx * dx + dy * dy <= 1.0:
            self.clicked.emit()
            event.accept()
        else:
            # Off-panda click — pass through to the UI below the overlay
            event.ignore()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_mood(self, mood: str = 'happy', *args, **kwargs) -> None:
        self.mood_changed.emit(str(mood))

    def set_animation(self, *args, **kwargs) -> None:
        pass

    def set_animation_state(self, state: str = 'idle', *args, **kwargs) -> None:
        """Update the current animation state."""
        self.animation_state = state
        self._animation = str(state)

    def set_autonomous_mode(self, *args, **kwargs) -> None:
        pass

    def equip_clothing(self, *args, **kwargs) -> None:
        pass

    def equip_item(self, *args, **kwargs) -> None:
        pass

    def update_appearance(self, *args, **kwargs) -> None:
        pass

    def get_info(self, *args, **kwargs) -> dict:
        return {}

    def add_item_from_emoji(self, *args, **kwargs) -> None:
        pass

    def add_item_3d(self, *args, **kwargs) -> None:
        pass

    def clear_items(self, *args, **kwargs) -> None:
        pass

    def set_theme(self, *args, **kwargs) -> None:
        pass

    def set_color(self, *args, **kwargs) -> None:
        pass

    def set_trail(self, *args, **kwargs) -> None:
        pass

    def set_fur_style(self, *args, **kwargs) -> None:
        pass

    def set_hair_style(self, *args, **kwargs) -> None:
        pass

    def preview_item(self, *args, **kwargs) -> None:
        pass

    def walk_to_position(self, *args, **kwargs) -> None:
        pass

    def notify_button_nearby(self, *args, **kwargs) -> None:
        pass

    def notify_file_dragged(self, *args, **kwargs) -> None:
        pass

    def get_idle_sub_state(self, *args, **kwargs) -> str:
        return ''
