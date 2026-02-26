"""
Panda Bedroom — Interactive 2D room scene.

The panda's bedroom contains 5 clickable pieces of furniture.  When the user
clicks one, the panda walks over and "opens" it before the relevant inventory
panel is revealed.

Furniture → inventory category mapping
  wardrobe     → clothing (shirts, pants, hats, shoes, accessories)
  armor_rack   → armor (armor, shield, helmet)
  weapons_rack → weapons (melee, magic, bow, gun)
  toy_box      → toys
  fridge       → food
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFrame, QGraphicsOpacityEffect, QSizePolicy,
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QRect, QRectF, QTimer, QPropertyAnimation, QEasingCurve
    from PyQt6.QtGui import (
        QPainter, QColor, QPen, QBrush, QFont, QPainterPath,
        QLinearGradient, QRadialGradient,
    )
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    class pyqtSignal:
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def emit(self, *a): pass


# ── Scene constants ────────────────────────────────────────────────────────────
_W = 400   # logical scene width
_H = 320   # logical scene height

_WALL_COLOR   = QColor(245, 230, 205) if PYQT_AVAILABLE else None
_FLOOR_COLOR  = QColor(180, 130,  80) if PYQT_AVAILABLE else None
_FLOOR_DARK   = QColor(155, 108,  60) if PYQT_AVAILABLE else None
_RUG_COLOR    = QColor(180,  60,  60) if PYQT_AVAILABLE else None
_RUG_BORDER   = QColor(220, 160,  80) if PYQT_AVAILABLE else None


@dataclass
class _Furniture:
    """A single piece of bedroom furniture."""
    id: str
    label: str
    emoji: str
    rect: 'QRect'                # click/hover area in logical scene coords
    panda_walk_x: float          # panda 3D-space x to walk to
    panda_walk_z: float          # panda 3D-space z to walk to
    inventory_category: str      # category string for inventory filter
    description: str


_FURNITURE: list = []   # filled after PYQT_AVAILABLE check


def _build_furniture() -> list:
    return [
        _Furniture(
            id='wardrobe', label='Wardrobe', emoji='👔',
            rect=QRect(18,  28, 90, 170),
            panda_walk_x=-1.5, panda_walk_z=0.0,
            inventory_category='Clothes',
            description='Browse your clothes collection: shirts, pants, jackets, dresses.',
        ),
        _Furniture(
            id='armor_rack', label='Armor Rack', emoji='🛡️',
            rect=QRect(292, 28, 110, 90),
            panda_walk_x=1.5, panda_walk_z=0.0,
            inventory_category='Accessories',
            description='Equip armor, shields, and helmets for your panda.',
        ),
        _Furniture(
            id='weapons_rack', label='Weapons Rack', emoji='⚔️',
            rect=QRect(292, 128, 110, 70),
            panda_walk_x=1.5, panda_walk_z=0.3,
            inventory_category='Accessories',
            description='Choose from swords, bows, staffs and magic weapons.',
        ),
        _Furniture(
            id='toy_box', label='Toy Box', emoji='🧸',
            rect=QRect(18, 220, 110, 80),
            panda_walk_x=-1.0, panda_walk_z=1.0,
            inventory_category='Toys',
            description='Pull out a toy for the panda to play with!',
        ),
        _Furniture(
            id='fridge', label='Fridge', emoji='🍎',
            rect=QRect(282, 210, 100, 100),
            panda_walk_x=1.0, panda_walk_z=1.0,
            inventory_category='Food',
            description='Feed your panda! Bamboo, fish, dumplings and more.',
        ),
    ]


class BedroomSceneWidget(QWidget if PYQT_AVAILABLE else object):
    """
    2D painted bedroom scene.  Emits ``furniture_clicked(str)`` with the
    furniture id when the user clicks a piece of furniture.
    """
    furniture_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        if not PYQT_AVAILABLE:
            return
        super().__init__(parent)
        self._furniture: list[_Furniture] = _build_furniture()
        self._hovered_id: Optional[str] = None
        self.setMouseTracking(True)
        self.setMinimumSize(200, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    # ── Coordinate helpers ─────────────────────────────────────────────────────
    def _scale(self) -> tuple[float, float, float, float]:
        """Return (sx, sy, ox, oy) — scale + offset mapping logical → widget coords."""
        w, h = self.width(), self.height()
        sx = w / _W
        sy = h / _H
        s  = min(sx, sy)
        ox = (w - _W * s) / 2.0
        oy = (h - _H * s) / 2.0
        return s, s, ox, oy

    def _to_widget(self, lx: int, ly: int) -> tuple[float, float]:
        s, _, ox, oy = self._scale()
        return ox + lx * s, oy + ly * s

    def _from_widget(self, wx: float, wy: float) -> tuple[float, float]:
        s, _, ox, oy = self._scale()
        return (wx - ox) / s, (wy - oy) / s

    def _scaled_rect(self, rect: 'QRect') -> 'QRectF':
        s, _, ox, oy = self._scale()
        return QRectF(ox + rect.x() * s, oy + rect.y() * s,
                      rect.width() * s,  rect.height() * s)

    def _furniture_at(self, wx: float, wy: float) -> Optional[_Furniture]:
        lx, ly = self._from_widget(wx, wy)
        for f in self._furniture:
            if f.rect.contains(int(lx), int(ly)):
                return f
        return None

    # ── Events ─────────────────────────────────────────────────────────────────
    def mouseMoveEvent(self, event):
        f = self._furniture_at(event.position().x(), event.position().y())
        new_id = f.id if f else None
        if new_id != self._hovered_id:
            self._hovered_id = new_id
            self.setCursor(Qt.CursorShape.PointingHandCursor if new_id
                           else Qt.CursorShape.ArrowCursor)
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            f = self._furniture_at(event.position().x(), event.position().y())
            if f:
                self.furniture_clicked.emit(f.id)

    def leaveEvent(self, event):
        self._hovered_id = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    # ── Painting ───────────────────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        s, _, ox, oy = self._scale()
        p.translate(ox, oy)
        p.scale(s, s)

        self._paint_room(p)
        self._paint_furniture(p)
        p.end()

    def _paint_room(self, p: 'QPainter'):
        """Draw wall, floor, and rug."""
        floor_y = 210

        # Wall (upper area)
        wall_grad = QLinearGradient(0, 0, 0, floor_y)
        wall_grad.setColorAt(0.0, QColor(255, 242, 220))
        wall_grad.setColorAt(1.0, QColor(240, 218, 185))
        p.fillRect(QRectF(0, 0, _W, floor_y), wall_grad)

        # Baseboard
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(195, 155, 105)))
        p.drawRect(QRectF(0, floor_y - 8, _W, 10))

        # Floor planks
        plank_colors = [QColor(185, 140, 85), QColor(170, 125, 70)]
        plank_h = 22
        plank_w = 100
        for row_i, fy in enumerate(range(floor_y, _H, plank_h)):
            for col_i, fx in enumerate(range(0, _W, plank_w)):
                c = plank_colors[(row_i + col_i) % 2]
                p.setBrush(QBrush(c))
                p.drawRect(QRectF(fx, fy, plank_w - 1, plank_h - 1))

        # Rug
        rug_rect = QRectF(118, 225, 165, 80)
        p.setBrush(QBrush(QColor(180, 55, 55)))
        p.setPen(QPen(QColor(220, 160, 75), 3))
        p.drawRoundedRect(rug_rect, 8, 8)
        inner_rug = rug_rect.adjusted(8, 6, -8, -6)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(240, 195, 100), 1.5))
        p.drawRoundedRect(inner_rug, 5, 5)

        # Wall decorations — picture frame
        p.setPen(QPen(QColor(140, 100, 55), 2))
        p.setBrush(QBrush(QColor(200, 220, 240)))
        p.drawRect(QRectF(148, 45, 65, 48))
        p.setPen(QPen(QColor(110, 80, 40), 1))
        # Simple mountain scene
        pts_path = QPainterPath()
        pts_path.moveTo(153, 88); pts_path.lineTo(165, 60); pts_path.lineTo(180, 78)
        pts_path.lineTo(195, 55); pts_path.lineTo(208, 88); pts_path.closeSubpath()
        p.setBrush(QBrush(QColor(90, 140, 90)))
        p.drawPath(pts_path)
        # Sun in picture
        p.setBrush(QBrush(QColor(255, 220, 80)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(192, 52, 10, 10))

        # Wall lamp
        p.setPen(QPen(QColor(140, 100, 55), 2))
        p.setBrush(QBrush(QColor(245, 200, 100, 200)))
        p.drawEllipse(QRectF(238, 50, 22, 28))
        p.setPen(QPen(QColor(140, 100, 55), 1))
        p.drawLine(249, 50, 249, 38)

    def _paint_furniture(self, p: 'QPainter'):
        for f in self._furniture:
            is_hovered = (f.id == self._hovered_id)
            r = f.rect
            getattr(self, f'_paint_{f.id}', self._paint_generic)(p, r, is_hovered, f)
            # Hover glow
            if is_hovered:
                glow = QRadialGradient(r.center().x(), r.center().y(),
                                       max(r.width(), r.height()) * 0.7)
                glow.setColorAt(0.0, QColor(255, 255, 150, 60))
                glow.setColorAt(1.0, QColor(255, 255, 150, 0))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(glow))
                p.drawRect(QRectF(r))
            # Label
            lf = QFont('Arial', int(6 * max(0.5, min(1.0, r.width() / 90.0))), QFont.Weight.Bold)
            p.setFont(lf)
            label_color = QColor(255, 215, 0) if is_hovered else QColor(50, 30, 10)
            p.setPen(QPen(label_color))
            label_rect = QRectF(r.x(), r.y() + r.height() - 14, r.width(), 14)
            p.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, f"{f.emoji} {f.label}")

    # ── Individual furniture painters ──────────────────────────────────────────
    def _paint_wardrobe(self, p, r: 'QRect', hov: bool, f):
        """Tall double-door wardrobe on left wall."""
        rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()

        # Cabinet body
        p.setPen(QPen(QColor(100, 65, 30), 2))
        p.setBrush(QBrush(QColor(185, 130, 70)))
        p.drawRoundedRect(QRectF(rx, ry, rw, rh - 14), 4, 4)

        # Crown moulding
        p.setBrush(QBrush(QColor(200, 150, 85)))
        p.drawRect(QRectF(rx - 3, ry, rw + 6, 10))

        # Left door
        mid = rx + rw // 2
        p.setPen(QPen(QColor(80, 50, 20), 1))
        p.setBrush(QBrush(QColor(210, 155, 85) if not hov else QColor(230, 175, 105)))
        p.drawRoundedRect(QRectF(rx + 4, ry + 14, rw // 2 - 6, rh - 32), 2, 2)
        # Right door
        p.drawRoundedRect(QRectF(mid + 2, ry + 14, rw // 2 - 6, rh - 32), 2, 2)

        # Mirror on left door
        p.setBrush(QBrush(QColor(195, 220, 240, 160)))
        p.setPen(QPen(QColor(140, 100, 50), 1))
        p.drawRoundedRect(QRectF(rx + 8, ry + 22, rw // 2 - 14, 70), 3, 3)

        # Door handles
        handle_color = QColor(210, 175, 80) if not hov else QColor(255, 215, 0)
        p.setBrush(QBrush(handle_color))
        p.setPen(QPen(QColor(160, 120, 40), 1))
        p.drawEllipse(QRectF(mid - 8, ry + 90, 5, 10))
        p.drawEllipse(QRectF(mid + 3, ry + 90, 5, 10))

        # Hanging clothes visible at top (coloured strips)
        hanger_colors = [QColor(200, 80, 80), QColor(80, 130, 200), QColor(80, 180, 80),
                         QColor(200, 180, 80), QColor(160, 80, 200)]
        for i, hc in enumerate(hanger_colors):
            hx = rx + 6 + i * (rw - 12) // len(hanger_colors)
            p.setPen(QPen(QColor(90, 60, 30), 1))
            p.drawLine(hx + 3, ry + 14, hx + 3, ry + 18)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(hc.lighter(130) if hov else hc))
            p.drawRoundedRect(QRectF(hx, ry + 18, 8, 22), 1, 1)

    def _paint_armor_rack(self, p, r: 'QRect', hov: bool, f):
        """T-bar stand with hanging breastplate and shield."""
        rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()

        # Wall-mounted plaque
        p.setPen(QPen(QColor(80, 55, 25), 1))
        p.setBrush(QBrush(QColor(210, 175, 100)))
        p.drawRect(QRectF(rx, ry, rw, 14))
        p.setPen(QPen(QColor(50, 35, 10), 1))
        p.setFont(QFont('Arial', 5, QFont.Weight.Bold))
        p.drawText(QRectF(rx, ry + 2, rw, 10), Qt.AlignmentFlag.AlignCenter, "ARMORY")

        # T-bar stand
        mid = rx + rw // 2
        stand_color = QColor(140, 140, 150) if not hov else QColor(180, 180, 200)
        p.setPen(QPen(QColor(80, 80, 90), 1))
        p.setBrush(QBrush(stand_color))
        # Vertical pole
        p.drawRect(QRectF(mid - 3, ry + 14, 6, rh - 30))
        # Horizontal bar
        p.drawRect(QRectF(rx + 4, ry + 22, rw - 8, 6))

        # Breastplate
        plate_color = QColor(180, 185, 200) if not hov else QColor(210, 215, 235)
        p.setBrush(QBrush(plate_color))
        p.setPen(QPen(QColor(90, 90, 100), 1))
        path = QPainterPath()
        path.moveTo(mid - 20, ry + 32)
        path.quadTo(mid - 22, ry + 58, mid - 12, ry + 72)
        path.lineTo(mid, ry + 76)
        path.lineTo(mid + 12, ry + 72)
        path.quadTo(mid + 22, ry + 58, mid + 20, ry + 32)
        path.quadTo(mid, ry + 28, mid - 20, ry + 32)
        p.drawPath(path)
        # Plate highlights
        p.setBrush(QBrush(QColor(210, 215, 240, 130)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(mid - 10, ry + 38, 8, 14))

        # Shield (leaning against stand)
        shield_x = rx + 3
        p.setPen(QPen(QColor(100, 60, 30), 1))
        p.setBrush(QBrush(QColor(170, 85, 85) if not hov else QColor(200, 110, 110)))
        spath = QPainterPath()
        spath.moveTo(shield_x, ry + 30)
        spath.lineTo(shield_x + 24, ry + 30)
        spath.lineTo(shield_x + 24, ry + 56)
        spath.quadTo(shield_x + 12, ry + 70, shield_x, ry + 56)
        spath.closeSubpath()
        p.drawPath(spath)
        # Shield cross emblem
        p.setPen(QPen(QColor(220, 200, 160), 1.5))
        p.drawLine(shield_x + 12, ry + 34, shield_x + 12, ry + 62)
        p.drawLine(shield_x + 4,  ry + 46, shield_x + 20, ry + 46)

    def _paint_weapons_rack(self, p, r: 'QRect', hov: bool, f):
        """Horizontal wall-mounted weapons rack."""
        rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()

        # Wall bracket
        p.setPen(QPen(QColor(80, 55, 25), 1))
        p.setBrush(QBrush(QColor(140, 95, 45)))
        p.drawRect(QRectF(rx, ry, rw, 12))
        p.setFont(QFont('Arial', 4, QFont.Weight.Bold))
        p.setPen(QPen(QColor(230, 200, 150)))
        p.drawText(QRectF(rx, ry + 2, rw, 8), Qt.AlignmentFlag.AlignCenter, "WEAPONS")

        # Horizontal bar
        bar_y = ry + 22
        p.setPen(QPen(QColor(90, 90, 100), 1))
        p.setBrush(QBrush(QColor(130, 130, 145) if not hov else QColor(160, 160, 175)))
        p.drawRect(QRectF(rx + 2, bar_y - 3, rw - 4, 6))

        # Hanging hooks
        hk_color = QColor(160, 160, 170)
        p.setBrush(QBrush(hk_color))
        for hx in [rx + 15, rx + 40, rx + 65, rx + 90]:
            p.drawEllipse(QRectF(hx - 2, bar_y - 1, 5, 5))

        # Sword (first hook)
        sw_x = rx + 14
        sword_col = QColor(200, 205, 220) if not hov else QColor(230, 235, 255)
        p.setPen(QPen(QColor(90, 90, 100), 1))
        p.setBrush(QBrush(sword_col))
        p.drawRect(QRectF(sw_x - 1, bar_y + 4, 3, 36))
        p.setBrush(QBrush(QColor(160, 100, 40)))
        p.drawRect(QRectF(sw_x - 5, bar_y + 34, 11, 8))
        p.setPen(QPen(QColor(120, 80, 30), 1))
        p.drawLine(sw_x + 1, bar_y + 34, sw_x + 1, bar_y + 42)

        # Staff (second hook)
        st_x = rx + 39
        p.setPen(QPen(QColor(100, 65, 30), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(st_x, bar_y + 4, st_x, bar_y + 46)
        p.setBrush(QBrush(QColor(100, 170, 255) if not hov else QColor(140, 210, 255)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(st_x - 5, bar_y + 4, 10, 10))

        # Bow (third hook)
        bw_x = rx + 65
        for angle_deg in range(-100, 101, 25):
            a = math.radians(angle_deg)
            bpx = bw_x + 14 * math.sin(a)
            bpy = bar_y + 28 + 20 * math.cos(a) - 20
            p.setPen(QPen(QColor(130, 85, 40) if not hov else QColor(165, 115, 60), 2))
            if abs(angle_deg) <= 75:
                p.drawPoint(int(bpx), int(bpy))
        p.setPen(QPen(QColor(220, 215, 195), 1))
        p.drawLine(bw_x, bar_y + 8, bw_x, bar_y + 48)

        # Gun/crossbow silhouette (fourth hook)
        gx = rx + 85
        p.setPen(QPen(QColor(60, 60, 65), 1))
        p.setBrush(QBrush(QColor(75, 75, 80) if not hov else QColor(100, 100, 110)))
        p.drawRect(QRectF(gx - 6, bar_y + 20, 18, 8))
        p.drawRect(QRectF(gx - 1, bar_y + 12, 4, 12))

    def _paint_toy_box(self, p, r: 'QRect', hov: bool, f):
        """Wooden toy chest with colourful toys poking out the top."""
        rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()

        # Box body
        wood = QColor(165, 100, 40) if not hov else QColor(190, 125, 60)
        p.setPen(QPen(QColor(90, 55, 20), 1.5))
        p.setBrush(QBrush(wood))
        body_h = rh - 28
        p.drawRoundedRect(QRectF(rx, ry + 28, rw, body_h - 14), 5, 5)

        # Box lid (slightly open, showing contents)
        lid_color = QColor(185, 115, 50) if not hov else QColor(210, 140, 70)
        p.setBrush(QBrush(lid_color))
        lid_path = QPainterPath()
        lid_path.moveTo(rx, ry + 30)
        lid_path.lineTo(rx + rw, ry + 30)
        lid_path.lineTo(rx + rw - 4, ry + 18)
        lid_path.lineTo(rx + 4, ry + 18)
        lid_path.closeSubpath()
        p.drawPath(lid_path)

        # Latch / lock
        p.setBrush(QBrush(QColor(210, 175, 80)))
        p.setPen(QPen(QColor(150, 115, 40), 1))
        p.drawRoundedRect(QRectF(rx + rw // 2 - 6, ry + 44, 12, 9), 2, 2)
        p.drawLine(rx + rw // 2, ry + 48, rx + rw // 2, ry + 56)

        # Toys poking out: ball, teddy bear ear, small wand
        # Ball
        ball_col = QColor(220, 80, 80) if not hov else QColor(255, 100, 100)
        p.setBrush(QBrush(ball_col))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(rx + 8, ry + 8, 16, 16))
        p.setBrush(QBrush(QColor(255, 255, 255, 100)))
        p.drawEllipse(QRectF(rx + 11, ry + 10, 6, 5))

        # Teddy ear
        p.setBrush(QBrush(QColor(200, 150, 80)))
        p.setPen(QPen(QColor(140, 95, 40), 1))
        p.drawEllipse(QRectF(rx + 32, ry + 6, 18, 18))
        p.setBrush(QBrush(QColor(235, 185, 120)))
        p.drawEllipse(QRectF(rx + 37, ry + 10, 9, 9))

        # Wand
        p.setPen(QPen(QColor(120, 80, 30), 1.5))
        p.drawLine(rx + rw - 18, ry + 20, rx + rw - 10, ry + 4)
        p.setBrush(QBrush(QColor(255, 220, 60)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(rx + rw - 15, ry + 0, 9, 9))

        # Wood grain lines
        p.setPen(QPen(QColor(130, 80, 30, 80), 0.8))
        for gy in range(ry + 32, ry + body_h + 28 - 14, 10):
            p.drawLine(rx + 6, gy, rx + rw - 6, gy)

    def _paint_fridge(self, p, r: 'QRect', hov: bool, f):
        """Tall white refrigerator with chrome handle and magnets."""
        rx, ry, rw, rh = r.x(), r.y(), r.width(), r.height()

        fridge_color = QColor(245, 245, 248) if not hov else QColor(255, 255, 255)
        p.setPen(QPen(QColor(180, 180, 188), 1.5))
        p.setBrush(QBrush(fridge_color))
        p.drawRoundedRect(QRectF(rx, ry, rw, rh - 14), 6, 6)

        # Highlight (top-left gloss)
        grad = QLinearGradient(rx, ry, rx + rw * 0.35, ry + rh * 0.3)
        grad.setColorAt(0.0, QColor(255, 255, 255, 120))
        grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(QRectF(rx, ry, rw, rh - 14), 6, 6)

        # Freezer compartment divider
        p.setPen(QPen(QColor(190, 190, 198), 1))
        p.drawLine(rx + 3, ry + 52, rx + rw - 3, ry + 52)

        # Handles
        handle_col = QColor(195, 195, 205) if not hov else QColor(215, 215, 225)
        p.setPen(QPen(QColor(150, 150, 160), 1))
        p.setBrush(QBrush(handle_col))
        # Top (freezer) handle
        p.drawRoundedRect(QRectF(rx + rw - 11, ry + 16, 6, 22), 3, 3)
        # Bottom (main) handle
        p.drawRoundedRect(QRectF(rx + rw - 11, ry + 60, 6, 30), 3, 3)

        # Fridge magnets (cute)
        magnet_data = [
            (rx + 10, ry + 65, QColor(255, 80, 80),   '🌸'),
            (rx + 30, ry + 58, QColor(80, 170, 255),  '⭐'),
            (rx + 18, ry + 80, QColor(80, 220, 80),   '🎀'),
        ]
        p.setFont(QFont('Segoe UI Emoji', 8))
        for mx, my, mc, emoji in magnet_data:
            p.setBrush(QBrush(mc))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(mx, my, 18, 16), 3, 3)
            p.setPen(QPen(QColor(40, 40, 40)))
            p.drawText(QRectF(mx, my, 18, 16), Qt.AlignmentFlag.AlignCenter, emoji)

        # Vent at bottom
        p.setPen(QPen(QColor(200, 200, 205), 0.8))
        for vx in range(rx + 4, rx + rw - 4, 5):
            p.drawLine(vx, ry + rh - 22, vx, ry + rh - 16)

    def _paint_generic(self, p, r: 'QRect', hov: bool, f):
        p.setPen(QPen(QColor(100, 70, 30), 1))
        p.setBrush(QBrush(QColor(190, 145, 80) if not hov else QColor(220, 175, 110)))
        p.drawRoundedRect(QRectF(r), 6, 6)


class PandaBedroomWidget(QWidget if PYQT_AVAILABLE else object):
    """
    Full bedroom panel: painted scene on top, info/action panel on bottom.
    Emits ``furniture_clicked(str)`` when the user clicks a furniture piece.
    """
    furniture_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        if not PYQT_AVAILABLE:
            return
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Scene ──────────────────────────────────────────────────────────────
        self._scene = BedroomSceneWidget()
        self._scene.furniture_clicked.connect(self._on_furniture_clicked)
        layout.addWidget(self._scene, stretch=4)

        # ── Info panel (shown when furniture is hovered/clicked) ───────────────
        self._info_frame = QFrame()
        self._info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self._info_frame.setStyleSheet(
            "QFrame { background:#2b1e0f; border-top:2px solid #8b6030; }"
        )
        info_layout = QHBoxLayout(self._info_frame)
        info_layout.setContentsMargins(10, 6, 10, 6)

        self._info_emoji = QLabel("🛏️")
        self._info_emoji.setStyleSheet("font-size:22px; background:transparent;")
        info_layout.addWidget(self._info_emoji)

        self._info_label = QLabel("Click a piece of furniture for the panda to interact with it.")
        self._info_label.setStyleSheet("color:#e8d8b0; font-size:11px; background:transparent;")
        self._info_label.setWordWrap(True)
        info_layout.addWidget(self._info_label, stretch=1)

        self._open_btn = QPushButton("Open")
        self._open_btn.setStyleSheet(
            "QPushButton { background:#7b4b1a; color:#ffe0a0; border:1px solid #c88030; "
            "border-radius:4px; padding:4px 12px; font-weight:bold; }"
            "QPushButton:hover { background:#9b6030; }"
        )
        self._open_btn.setVisible(False)
        self._open_btn.clicked.connect(self._on_open_clicked)
        info_layout.addWidget(self._open_btn)

        layout.addWidget(self._info_frame)

        self._pending_furniture_id: Optional[str] = None
        self._furniture_map = {f.id: f for f in _build_furniture()}

    def _on_furniture_clicked(self, furniture_id: str):
        f = self._furniture_map.get(furniture_id)
        if not f:
            return
        self._pending_furniture_id = furniture_id
        self._info_emoji.setText(f.emoji)
        self._info_label.setText(f.description)
        self._open_btn.setText(f"Open {f.label}")
        self._open_btn.setVisible(True)
        self.furniture_clicked.emit(furniture_id)

    def _on_open_clicked(self):
        if self._pending_furniture_id:
            self.furniture_clicked.emit(self._pending_furniture_id)

    def get_furniture(self, furniture_id: str) -> Optional[_Furniture]:
        return self._furniture_map.get(furniture_id)
