"""
Shop Panel - Buy items for panda customization
Qt implementation of the shop system
"""

import logging
import math
import random
from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QGridLayout, QComboBox, QMessageBox,
        QLineEdit, QStackedWidget
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    QStackedWidget = object
    class QTimer:
        @staticmethod
        def singleShot(*a): pass
        def __init__(self, *a): pass
        def start(self, *a): pass
        def stop(self): pass
        def setInterval(self, *a): pass
        timeout = type('_Sig', (), {'connect': lambda *a: None})()  # type: ignore[misc]
    class pyqtSignal:
        def __init__(self, *args): pass
        def connect(self, *args): pass
        def emit(self, *args): pass
    class Qt:
        class AlignmentFlag:
            AlignCenter = 0
        class CursorShape:
            PointingHandCursor = 0

# ── Optional QOpenGLWidget for 3-D Livy avatar ───────────────────────────────
try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget as _QOpenGLWidget
    _QOGL_SHOP = True
except (ImportError, OSError, RuntimeError):
    _QOGL_SHOP = False
    _QOpenGLWidget = QWidget  # fallback base class

logger = logging.getLogger(__name__)

# Try to import shop system
try:
    from features.shop_system import ShopSystem, ShopCategory, ShopItem
    from features.currency_system import CurrencySystem
    SHOP_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    try:
        from ..features.shop_system import ShopSystem, ShopCategory, ShopItem
        from ..features.currency_system import CurrencySystem
        SHOP_AVAILABLE = True
    except (ImportError, OSError, RuntimeError):
        logger.warning("Shop system not available")
        SHOP_AVAILABLE = False
        ShopSystem = None
        ShopCategory = None
        ShopItem = None
        CurrencySystem = None


class LivyOtterWidget(_QOpenGLWidget):
    """Small OpenGL widget showing Livy the otter in the shop banner.

    Renders the same detailed 3-D otter as ``PandaWorldGL._draw_otter()``
    by importing the drawing code from that module.  Falls back gracefully
    to an emoji QLabel when OpenGL is unavailable.
    """

    def __init__(self, parent=None):
        if not (_QOGL_SHOP and PYQT_AVAILABLE):
            super().__init__(parent)
            return
        super().__init__(parent)
        self.setFixedSize(100, 110)

        # Animation state (mirrors PandaWorldGL — all attrs read by _draw_otter)
        self._frame: int = 0
        self._gl_ready: bool = False
        self._otter_happy_t: int = 0
        self._otter_wave_t: int = 0
        self._otter_head_bob: float = 0.0
        self._otter_tail_angle: float = 0.0
        self._otter_look_x: float = 0.0
        self._otter_look_tgt: float = 0.0
        self._otter_look_phase: int = 0    # countdown to next random look-event
        self._otter_eye_close: int = 0
        self._otter_blink: int = 180       # countdown frames to next blink
        self._otter_shuffle_t: int = 0     # counter-shuffle animation timer

        # Tick timer — ~30 fps
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    # ------------------------------------------------------------------
    def _tick(self):
        import math as _m
        import random as _r
        self._frame += 1
        self._otter_head_bob = _m.sin(self._frame * 0.025) * 4.0
        self._otter_tail_angle = _m.sin(self._frame * 0.04) * 18.0
        if self._otter_happy_t > 0:
            self._otter_happy_t -= 1
        if self._otter_wave_t > 0:
            self._otter_wave_t -= 1
        # Blink
        if self._otter_blink <= 0:
            self._otter_blink = _r.randint(100, 280)
            self._otter_eye_close = 4
        else:
            self._otter_blink -= 1
        if self._otter_eye_close > 0:
            self._otter_eye_close -= 1
        # Random look-around
        if self._otter_look_phase <= 0:
            self._otter_look_tgt = (
                _r.uniform(-14.0, 14.0) if _r.random() < 0.7 else 0.0
            )
            self._otter_look_phase = _r.randint(80, 200)
        else:
            self._otter_look_phase -= 1
        self._otter_look_x += (self._otter_look_tgt - self._otter_look_x) * 0.07
        # Counter-shuffle
        if self._otter_shuffle_t > 0:
            self._otter_shuffle_t -= 1
        elif _r.random() < 0.003:
            self._otter_shuffle_t = _r.randint(20, 50)
        self.update()

    # ------------------------------------------------------------------
    def initializeGL(self):
        try:
            # Import GL lazily so the module compiles without PyOpenGL
            from OpenGL.GL import (
                glClearColor, glEnable, glDisable, GL_DEPTH_TEST, GL_LIGHTING,
                GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_BLEND, GL_COLOR_MATERIAL,
                glLightfv, GL_POSITION, GL_DIFFUSE, GL_SPECULAR, GL_AMBIENT,
                GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, glBlendFunc,
                glMatrixMode, GL_MODELVIEW, glLoadIdentity, GL_SMOOTH,
                GL_MULTISAMPLE, GL_LINE_SMOOTH, glHint, GL_LINE_SMOOTH_HINT, GL_NICEST,
                glShadeModel,
            )
            glClearColor(0.05, 0.28, 0.28, 1.0)   # turquoise background
            glEnable(GL_DEPTH_TEST)
            try:
                glShadeModel(GL_SMOOTH)
                glEnable(GL_MULTISAMPLE)
                glEnable(GL_LINE_SMOOTH)
                glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
            except Exception:
                pass
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_LIGHT1)
            glEnable(GL_COLOR_MATERIAL)
            glLightfv(GL_LIGHT0, GL_POSITION, [3.0, 6.0,  4.0, 1.0])
            glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.35, 0.33, 0.30, 1.0])
            glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.85, 0.82, 0.78, 1.0])
            glLightfv(GL_LIGHT0, GL_SPECULAR, [0.4,  0.4,  0.3,  1.0])
            glLightfv(GL_LIGHT1, GL_POSITION, [-3.0, 4.0, -2.0, 1.0])
            glLightfv(GL_LIGHT1, GL_AMBIENT,  [0.08, 0.08, 0.10, 1.0])
            glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.25, 0.30, 0.40, 1.0])
            glEnable(GL_LIGHT2)
            glLightfv(GL_LIGHT2, GL_POSITION, [0.0, 5.0, -4.0, 1.0])
            glLightfv(GL_LIGHT2, GL_DIFFUSE,  [0.12, 0.14, 0.16, 1.0])
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            self._gl_ready = True
        except Exception as _e:
            logger.debug("LivyOtterWidget initializeGL failed: %s", _e)

    def resizeGL(self, w: int, h: int):
        if not self._gl_ready:
            return
        try:
            from OpenGL.GL import glViewport, glMatrixMode, GL_PROJECTION, GL_MODELVIEW, glLoadIdentity
            from OpenGL.GLU import gluPerspective
            glViewport(0, 0, max(1, w), max(1, h))
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(50.0, w / max(1, h), 0.1, 30.0)
            glMatrixMode(GL_MODELVIEW)
        except Exception:
            pass

    def paintGL(self):
        if not self._gl_ready:
            return
        try:
            from OpenGL.GL import glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, glLoadIdentity, glTranslatef, glRotatef
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            # Position camera so otter fills the widget: pull back and look slightly down
            glTranslatef(0.0, -0.5, -3.8)
            glRotatef(8.0, 1.0, 0.0, 0.0)
            # Draw the otter using the shared implementation from panda_world_gl
            from ui.panda_world_gl import PandaWorldGL
            PandaWorldGL._draw_otter(self)  # type: ignore[arg-type]
        except Exception as _e:
            logger.debug("LivyOtterWidget paintGL error: %s", _e)

    # ------------------------------------------------------------------
    # Helpers that _draw_otter() calls on ``self``
    @staticmethod
    def _sphere(r: float, sl: int, st: int):
        try:
            from OpenGL.GLU import gluNewQuadric, GLU_SMOOTH, gluQuadricNormals, gluSphere, gluDeleteQuadric
            q = gluNewQuadric()
            gluQuadricNormals(q, GLU_SMOOTH)
            gluSphere(q, r, sl, st)
            gluDeleteQuadric(q)
        except Exception:
            pass

    @staticmethod
    def _cylinder(r: float, h: float, sl: int):
        try:
            from OpenGL.GLU import gluNewQuadric, GLU_SMOOTH, gluQuadricNormals, gluCylinder, gluDisk, gluDeleteQuadric
            from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslatef
            q = gluNewQuadric()
            gluQuadricNormals(q, GLU_SMOOTH)
            gluCylinder(q, r, r, h, sl, 1)
            gluDisk(q, 0, r, sl, 1)
            glPushMatrix(); glTranslatef(0, 0, h); gluDisk(q, 0, r, sl, 1); glPopMatrix()
            gluDeleteQuadric(q)
        except Exception:
            pass


class ShopItemWidget(QFrame):
    """Individual shop item display"""
    
    purchase_requested = pyqtSignal(str)   # item_id
    item_hovered       = pyqtSignal(object)  # ShopItem — emitted on mouse-enter

    def __init__(self, item: 'ShopItem', owned: bool = False,
                 parent=None, tooltip_manager=None):
        super().__init__(parent)
        self.item = item
        self.owned = owned
        self._tooltip_mgr = tooltip_manager
        self.setMouseTracking(True)  # enables enterEvent without a pressed button
        self.setup_ui()

    def setup_ui(self):
        """Create the item card UI — turquoise Livy theme."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        # Rarity border colour
        rarity = getattr(getattr(self.item, 'rarity', None), 'value', 'common')
        _rarity_border = {
            'common': '#B0E0E0', 'uncommon': '#2ECC71', 'rare': '#3498DB',
            'epic': '#9B59B6', 'legendary': '#F39C12',
        }.get(str(rarity).lower(), '#B0E0E0')
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 2px solid {_rarity_border};
                border-radius: 12px;
                padding: 8px;
            }}
            QFrame:hover {{
                border: 2px solid #0BBFBF;
                background: #F0FAFA;
            }}
        """)
        self.setFixedSize(148, 190)

        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(6, 6, 6, 6)

        # Icon
        icon_label = QLabel(getattr(self.item, 'icon', '🎁'))
        icon_label.setFont(QFont("Segoe UI Emoji", 28))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Name
        name_label = QLabel(getattr(self.item, 'name', ''))
        name_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("color: #063040;")
        self._wire_tip(name_label, 'shop_item_name',
                       getattr(self.item, 'name', ''))
        layout.addWidget(name_label)

        # Price
        price = getattr(self.item, 'price', 0)
        price_label = QLabel("✅ Owned" if self.owned else f"💰 {price:,}")
        price_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("color: #089898;" if self.owned else "color: #B8860B;")
        self._wire_tip(price_label, 'shop_price',
                       f"Price: {price:,} coins" if not self.owned else "Already owned")
        layout.addWidget(price_label)

        layout.addStretch()

        # Buy / owned button
        if self.owned:
            btn = QPushButton("✓ Owned")
            btn.setEnabled(False)
            btn.setStyleSheet(
                "background: #D0EEEE; color: #089898; border: none;"
                " border-radius: 8px; padding: 5px; font-weight: bold; font-size: 11px;"
            )
        else:
            btn = QPushButton("🛒 Buy")
            btn.clicked.connect(lambda: self.purchase_requested.emit(self.item.id))
            btn.setStyleSheet(
                "background: #0BBFBF; color: white; border: none;"
                " border-radius: 8px; padding: 5px;"
                " font-weight: bold; font-size: 11px;"
                " QPushButton:hover { background: #089898; }"
            )
        self._wire_tip(btn, 'shop_buy_button', "Purchase this item")
        layout.addWidget(btn)

    def _wire_tip(self, widget, tip_id: str, fallback: str = '') -> None:
        """Set tooltip on widget, registering with tooltip_manager when available."""
        mgr = self._tooltip_mgr
        if mgr is not None and hasattr(mgr, 'register'):
            try:
                text = mgr.get_tooltip(tip_id) or fallback
                widget.setToolTip(text)
                mgr.register(widget, tip_id)
                return
            except Exception:
                pass
        widget.setToolTip(fallback or tip_id)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        """Notify parent shop panel when the mouse enters this card."""
        try:
            self.item_hovered.emit(self.item)
        except Exception:
            pass
        super().enterEvent(event)

    def mouseDoubleClickEvent(self, event):  # type: ignore[override]
        """Open item detail dialog on double-click."""
        try:
            dlg = ItemDetailDialog(self.item, self.owned, parent=self.window())
            dlg.exec()
            if getattr(dlg, 'buy_requested', False) and not self.owned:
                self.purchase_requested.emit(self.item.id)
        except (ImportError, AttributeError, RuntimeError) as _e:
            logger.debug(f"ShopItemWidget double-click dialog: {_e}")
        super().mouseDoubleClickEvent(event)


class ItemDetailDialog:
    """Modal dialog showing full item details with buy/equip button."""

    def __init__(self, item, owned: bool, parent=None):
        if not PYQT_AVAILABLE:
            return
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox  # type: ignore
        from PyQt6.QtCore import QSize  # type: ignore

        dlg = QDialog(parent)
        dlg.setWindowTitle(item.name)
        dlg.setFixedSize(QSize(320, 420))
        dlg.setStyleSheet("QDialog { background: #1a1a2e; color: #e0e0e0; }")

        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Large icon
        icon_lbl = QLabel(getattr(item, 'icon', '🎁'))
        icon_lbl.setFont(QFont("Segoe UI", 48))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        # Name
        name_lbl = QLabel(item.name)
        name_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color: #ffffff;")
        layout.addWidget(name_lbl)

        # Rarity badge
        rarity = getattr(item, 'rarity', None)
        if rarity is not None:
            rarity_str = rarity.name if hasattr(rarity, 'name') else str(rarity)
            try:
                from ui.closet_display_qt import _RARITY_COLORS as _RC
            except (ImportError, OSError, RuntimeError):
                _RC = {'common': '#aaaaaa', 'uncommon': '#55cc55',
                       'rare': '#5599ff', 'epic': '#cc55ff', 'legendary': '#ffaa00'}
            col = _RC.get(rarity_str.lower(), '#9e9e9e')
            rar_lbl = QLabel(rarity_str.capitalize())
            rar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rar_lbl.setStyleSheet(
                f"color: {col}; font-weight: bold; font-size: 11px;"
                " border: 1px solid; border-radius: 4px; padding: 2px 8px;"
                f" border-color: {col};"
            )
            layout.addWidget(rar_lbl)

        # Description
        desc = QLabel(getattr(item, 'description', ''))
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #b0b0b0; font-size: 11px;")
        layout.addWidget(desc)

        # Price
        price_lbl = QLabel(
            "✅ Owned" if owned else f"💰 {getattr(item, 'price', 0):,} Bamboo Bucks"
        )
        price_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_lbl.setStyleSheet("color: #4CAF50;" if owned else "color: #FFD700;")
        layout.addWidget(price_lbl)

        layout.addStretch()

        # Action button
        if owned:
            btn = QPushButton("✓ Owned")
            btn.setEnabled(False)
            btn.setStyleSheet(
                "background:#555; color:#aaa; padding:10px; border-radius:6px;"
            )
        else:
            btn = QPushButton("🛒 Buy")
            btn.setStyleSheet(
                "background:#4CAF50; color:white; padding:10px;"
                " border-radius:6px; font-weight:bold; font-size:13px;"
            )
            btn.clicked.connect(lambda: (
                setattr(self, 'buy_requested', True),
                dlg.accept(),
            ))
        btn.setToolTip("🛒 Purchase this item from the shop")
        layout.addWidget(btn)

        self._dlg = dlg

    def exec(self):
        try:
            return self._dlg.exec()
        except (RuntimeError, AttributeError) as e:
            logger.debug(f"ItemDetailDialog.exec: {e}")
            return 0


class ShopPanelQt(QWidget):
    """Main shop panel for purchasing items."""

    item_purchased = pyqtSignal(str)  # item_id

    # Maps shop category IDs to specific tooltip catalog keys
    _CATEGORY_TOOLTIP_IDS = {
        "Outfits":     'shop_outfits_cat',
        "Clothes":     'shop_clothes_cat',
        "Hats":        'shop_hats_cat',
        "Shoes":       'shop_shoes_cat',
        "Accessories": 'shop_accessories_cat',
        "Toys":        'shop_toys_cat',
        "Food":        'shop_food_cat',
        "Special":     'shop_special_cat',
    }
    def __init__(self, shop_system: Optional['ShopSystem'] = None, 
                 currency_system: Optional['CurrencySystem'] = None,
                 parent=None, tooltip_manager=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 required for ShopPanelQt")
        
        super().__init__(parent)
        self.tooltip_manager = tooltip_manager
        
        # Initialize systems if not provided
        if SHOP_AVAILABLE:
            self.shop_system = shop_system or ShopSystem()
            self.currency_system = currency_system or CurrencySystem()
        else:
            self.shop_system = None
            self.currency_system = None
        
        self.current_category = "All"
        self._livy_idle_timer: Optional[QTimer] = None  # fires idle chatter
        self.setup_ui()
        self._start_livy_idle_timer()
        self.refresh_shop()

    # ─────────────────────────── Turquoise colour palette ────────────────────
    _TURQ      = "#0BBFBF"    # Livy's signature turquoise
    _TURQ_D    = "#089898"    # darker turquoise for accents
    _TURQ_L    = "#E0FAFA"    # very light turquoise background
    _TURQ_HDR  = "#063040"    # deep cosmic header background
    _STAR_GOLD = "#FFD700"    # gold stars

    _SHOP_STYLESHEET = f"""
        QWidget {{
            background: #F0FAFA;
        }}
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background: #D0EEEE;
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: #0BBFBF;
            border-radius: 4px;
        }}
        QComboBox {{
            background: white;
            border: 2px solid #0BBFBF;
            border-radius: 10px;
            padding: 4px 10px;
            color: #063040;
            font-weight: bold;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QLineEdit {{
            background: white;
            border: 2px solid #0BBFBF;
            border-radius: 10px;
            padding: 4px 10px;
            color: #063040;
        }}
    """

    def setup_ui(self):
        """Create the Cosmic Otter Supply Co. shop UI — Livy's turquoise world."""
        self.setStyleSheet(self._SHOP_STYLESHEET)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Banner header ─────────────────────────────────────────────────────
        banner = QWidget()
        banner.setFixedHeight(120)
        banner.setStyleSheet(f"background: {self._TURQ_HDR}; border-radius: 0px;")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(18, 8, 18, 8)

        # Otter avatar — 3-D GL widget (falls back to emoji when OpenGL unavailable)
        if _QOGL_SHOP and PYQT_AVAILABLE:
            otter_avatar = LivyOtterWidget(banner)
        else:
            otter_avatar = QLabel("🦦")
            otter_avatar.setStyleSheet("font-size: 42px;")
            otter_avatar.setFixedWidth(58)
            otter_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addWidget(otter_avatar)

        # Otter name + speech bubble column
        otter_col = QVBoxLayout()
        otter_col.setSpacing(2)
        livy_name = QLabel("Livy's  Cosmic Otter Supply Co. ✨")
        livy_name.setStyleSheet(f"color: {self._STAR_GOLD}; font-size: 13px; font-weight: bold; letter-spacing: 1px;")
        self._set_tooltip(livy_name, 'shop_tab')
        tagline = QLabel("Galactic Goods for Adventurous Pandas 🌌")
        tagline.setStyleSheet("color: #90E0E0; font-size: 10px; font-style: italic;")
        self._set_tooltip(tagline, 'shop_level')

        # Livy's speech bubble — shows commentary
        self.livy_bubble = QLabel("👀  Welcome! Looking for something great?")
        self.livy_bubble.setWordWrap(True)
        self.livy_bubble.setStyleSheet(
            "background: #0BBFBF; color: white; border-radius: 10px;"
            " padding: 5px 10px; font-size: 11px; font-style: italic;"
        )
        self.livy_bubble.setMaximumWidth(380)
        self._set_tooltip(self.livy_bubble, 'shop_tab')

        otter_col.addWidget(livy_name)
        otter_col.addWidget(tagline)
        otter_col.addWidget(self.livy_bubble)
        banner_layout.addLayout(otter_col)

        banner_layout.addStretch()

        # Coin display
        coin_col = QVBoxLayout()
        coin_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.currency_label = QLabel("💰 0 Bamboo Bucks")
        self.currency_label.setStyleSheet(
            f"color: {self._STAR_GOLD}; font-size: 14px; font-weight: bold;"
            " background: rgba(255,215,0,0.12); border-radius: 10px; padding: 6px 14px;"
        )
        self.currency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coin_col.addWidget(self.currency_label)
        self._set_tooltip(self.currency_label, 'shop_balance')
        banner_layout.addLayout(coin_col)

        layout.addWidget(banner)

        # ── Search + filter bar ───────────────────────────────────────────────
        filter_bar = QWidget()
        filter_bar.setStyleSheet(f"background: {self._TURQ_D}; padding: 6px;")
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(12, 4, 12, 4)
        filter_layout.setSpacing(8)

        search_lbl = QLabel("🔍")
        search_lbl.setStyleSheet("color: white; font-size: 14px;")
        filter_layout.addWidget(search_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Livy's shelves…")
        self.search_input.setFixedHeight(30)
        self.search_input.textChanged.connect(self.filter_items)
        self.search_input.setStyleSheet(
            "background: white; border: none; border-radius: 8px;"
            " padding: 2px 8px; color: #063040;"
        )
        self._set_tooltip(self.search_input, 'search_button')
        filter_layout.addWidget(self.search_input, 1)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 30)
        self._set_tooltip(refresh_btn, "Refresh shop")
        refresh_btn.setStyleSheet(
            f"background: {self._TURQ}; color: white; border: none;"
            " border-radius: 8px; font-size: 14px; font-weight: bold;"
        )
        refresh_btn.clicked.connect(self.refresh_shop)
        filter_layout.addWidget(refresh_btn)

        layout.addWidget(filter_bar)

        # ── Buy / Sell mode toggle ────────────────────────────────────────────
        mode_bar = QWidget()
        mode_bar.setStyleSheet(f"background: {self._TURQ_HDR};")
        mode_layout = QHBoxLayout(mode_bar)
        mode_layout.setContentsMargins(12, 4, 12, 4)
        mode_layout.setSpacing(8)

        self._buy_tab_btn = QPushButton("🛒  Buy")
        self._sell_tab_btn = QPushButton("💰  Sell")
        for btn in (self._buy_tab_btn, self._sell_tab_btn):
            btn.setFixedHeight(30)
            btn.setCheckable(True)
        self._buy_tab_btn.setChecked(True)

        _tab_active = (
            f"QPushButton {{ background: {self._TURQ}; color: white; border: none;"
            " border-radius: 8px; padding: 4px 18px; font-size: 11px; font-weight: bold; }}"
        )
        _tab_inactive = (
            f"QPushButton {{ background: transparent; color: #90E0E0; border: none;"
            " border-radius: 8px; padding: 4px 18px; font-size: 11px; }}"
            f"QPushButton:hover {{ background: {self._TURQ_D}; }}"
        )
        self._buy_tab_btn.setStyleSheet(_tab_active)
        self._sell_tab_btn.setStyleSheet(_tab_inactive)

        self._buy_tab_btn.clicked.connect(lambda: self._switch_mode('buy'))
        self._sell_tab_btn.clicked.connect(lambda: self._switch_mode('sell'))

        mode_layout.addWidget(self._buy_tab_btn)
        mode_layout.addWidget(self._sell_tab_btn)
        mode_layout.addStretch()
        layout.addWidget(mode_bar)

        # ── Stacked content (buy vs sell) ─────────────────────────────────────
        self._mode_stack = QStackedWidget()

        # Page 0 — Buy (category pills + item grid)
        buy_page = QWidget()
        buy_layout = QVBoxLayout(buy_page)
        buy_layout.setContentsMargins(0, 0, 0, 0)
        buy_layout.setSpacing(0)

        # ── Category pills ────────────────────────────────────────────────────
        cat_scroll = QScrollArea()
        cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cat_scroll.setFixedHeight(46)
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cat_scroll.setStyleSheet(f"background: {self._TURQ_L}; border: none;")

        cat_widget = QWidget()
        cat_widget.setStyleSheet(f"background: {self._TURQ_L};")
        cat_row = QHBoxLayout(cat_widget)
        cat_row.setContentsMargins(8, 4, 8, 4)
        cat_row.setSpacing(6)

        self._cat_buttons: list = []
        _categories = [
            ("⭐ All", "All"), ("👗 Outfits", "Outfits"), ("👕 Clothes", "Clothes"),
            ("🎩 Hats", "Hats"), ("👟 Shoes", "Shoes"), ("💎 Accessories", "Accessories"),
            ("🐾 Fur", "Fur Styles"), ("🎨 Colours", "Fur Colors"),
            ("💇 Hair", "Hair Styles"), ("⚔️ Weapons", "Weapons"),
            ("🛡️ Armor", "Armor"), ("👢 Boots", "Boots"), ("🧤 Gloves", "Gloves"),
            ("🔗 Belt", "Belt"), ("🎒 Backpack", "Backpack"),
            ("🧸 Toys", "Toys"), ("🍎 Food", "Food"), ("✨ Special", "Special"),
        ]
        for label, cat_id in _categories:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(30)
            btn.setStyleSheet(self._pill_style(active=(cat_id == "All")))
            btn.clicked.connect(lambda checked, c=cat_id: self._on_cat_pill(c))
            btn.setProperty("cat_id", cat_id)
            tip_id = self._CATEGORY_TOOLTIP_IDS.get(cat_id, 'shop_category_button')
            self._set_tooltip(btn, tip_id)
            cat_row.addWidget(btn)
            self._cat_buttons.append(btn)
        cat_row.addStretch()
        cat_scroll.setWidget(cat_widget)
        buy_layout.addWidget(cat_scroll)

        # ── Items scroll grid ─────────────────────────────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.scroll_area.setWidget(self.grid_widget)
        buy_layout.addWidget(self.scroll_area, 1)

        self._mode_stack.addWidget(buy_page)   # index 0

        # Page 1 — Sell (owned items list)
        sell_page = QWidget()
        sell_page_layout = QVBoxLayout(sell_page)
        sell_page_layout.setContentsMargins(0, 0, 0, 0)
        sell_page_layout.setSpacing(0)

        sell_header = QLabel("💰  Sell items from your collection — you'll receive 50% of the original price.")
        sell_header.setWordWrap(True)
        sell_header.setStyleSheet(
            f"background: {self._TURQ_L}; color: {self._TURQ_D};"
            " font-size: 11px; padding: 8px 14px; font-style: italic;"
        )
        sell_page_layout.addWidget(sell_header)

        self.sell_scroll_area = QScrollArea()
        self.sell_scroll_area.setWidgetResizable(True)
        self.sell_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.sell_scroll_area.setStyleSheet("background: transparent; border: none;")

        self.sell_list_widget = QWidget()
        self.sell_list_widget.setStyleSheet("background: transparent;")
        self.sell_list_layout = QVBoxLayout(self.sell_list_widget)
        self.sell_list_layout.setSpacing(6)
        self.sell_list_layout.setContentsMargins(12, 12, 12, 12)
        self.sell_list_layout.addStretch()
        self.sell_scroll_area.setWidget(self.sell_list_widget)
        sell_page_layout.addWidget(self.sell_scroll_area, 1)

        self._mode_stack.addWidget(sell_page)  # index 1

        layout.addWidget(self._mode_stack, 1)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(24)
        self.status_label.setStyleSheet(
            f"background: {self._TURQ_HDR}; color: {self._TURQ};"
            " font-size: 11px; padding: 0 8px;"
        )
        layout.addWidget(self.status_label)

    def _pill_style(self, active: bool = False) -> str:
        if active:
            return (
                f"QPushButton {{ background: {self._TURQ}; color: white;"
                " border: none; border-radius: 13px; padding: 4px 12px;"
                " font-size: 11px; font-weight: bold; }}"
            )
        return (
            f"QPushButton {{ background: white; color: {self._TURQ_D};"
            f" border: 2px solid {self._TURQ}; border-radius: 13px; padding: 3px 12px;"
            " font-size: 11px; }}"
            f"QPushButton:hover {{ background: {self._TURQ_L}; }}"
        )

    def _on_cat_pill(self, cat_id: str) -> None:
        self.current_category = cat_id
        for btn in self._cat_buttons:
            btn.setStyleSheet(self._pill_style(active=(btn.property("cat_id") == cat_id)))
        self.refresh_shop()

    def _switch_mode(self, mode: str) -> None:
        """Switch between 'buy' and 'sell' views."""
        _tab_active = (
            f"QPushButton {{ background: {self._TURQ}; color: white; border: none;"
            " border-radius: 8px; padding: 4px 18px; font-size: 11px; font-weight: bold; }}"
        )
        _tab_inactive = (
            f"QPushButton {{ background: transparent; color: #90E0E0; border: none;"
            " border-radius: 8px; padding: 4px 18px; font-size: 11px; }}"
            f"QPushButton:hover {{ background: {self._TURQ_D}; }}"
        )
        if mode == 'buy':
            self._mode_stack.setCurrentIndex(0)
            self._buy_tab_btn.setStyleSheet(_tab_active)
            self._sell_tab_btn.setStyleSheet(_tab_inactive)
            self._buy_tab_btn.setChecked(True)
            self._sell_tab_btn.setChecked(False)
        else:
            self._mode_stack.setCurrentIndex(1)
            self._buy_tab_btn.setStyleSheet(_tab_inactive)
            self._sell_tab_btn.setStyleSheet(_tab_active)
            self._buy_tab_btn.setChecked(False)
            self._sell_tab_btn.setChecked(True)
            self._populate_sell_list()

    def _populate_sell_list(self) -> None:
        """Populate the sell-page list with owned items and sell buttons."""
        # Clear existing rows
        while self.sell_list_layout.count() > 1:  # keep the stretch at end
            item = self.sell_list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not SHOP_AVAILABLE or not self.shop_system:
            lbl = QLabel("⚠️ Shop system not available.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sell_list_layout.insertWidget(0, lbl)
            return

        purchased = self.shop_system.get_purchased_items()
        if not purchased:
            lbl = QLabel("🛍️  You don't own any items yet.\n\nBuy something from the shop first!")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #888; font-size: 12pt; padding: 30px;")
            self.sell_list_layout.insertWidget(0, lbl)
            return

        for idx, item_id in enumerate(sorted(purchased)):
            catalog_item = self.shop_system.CATALOG.get(item_id)
            if catalog_item is None:
                continue
            refund = math.ceil(catalog_item.price * self.shop_system.SELL_REFUND_FRACTION)

            row = QFrame()
            row.setFrameStyle(QFrame.Shape.StyledPanel)
            row.setStyleSheet(
                f"QFrame {{ background: white; border: 1px solid {self._TURQ_L};"
                " border-radius: 8px; }}"
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 6, 12, 6)

            icon_lbl = QLabel(catalog_item.icon)
            icon_lbl.setStyleSheet("font-size: 22px;")
            icon_lbl.setFixedWidth(34)
            row_layout.addWidget(icon_lbl)

            info = QVBoxLayout()
            name_lbl = QLabel(f"<b>{catalog_item.name}</b>")
            name_lbl.setStyleSheet(f"color: {self._TURQ_D}; font-size: 11px;")
            desc_lbl = QLabel(catalog_item.description)
            desc_lbl.setStyleSheet("color: #666; font-size: 10px;")
            desc_lbl.setWordWrap(True)
            info.addWidget(name_lbl)
            info.addWidget(desc_lbl)
            row_layout.addLayout(info, 1)

            sell_btn = QPushButton(f"Sell  {refund} 💰")
            sell_btn.setFixedWidth(110)
            sell_btn.setFixedHeight(30)
            sell_btn.setStyleSheet(
                f"QPushButton {{ background: {self._STAR_GOLD}; color: #333; border: none;"
                " border-radius: 8px; font-size: 11px; font-weight: bold; }}"
                "QPushButton:hover { background: #F5C518; }"
                "QPushButton:disabled { background: #ddd; color: #999; }"
            )
            sell_btn.clicked.connect(
                lambda _checked, iid=item_id, r=row: self._on_sell_clicked(iid, r)
            )
            row_layout.addWidget(sell_btn)

            self.sell_list_layout.insertWidget(idx, row)

    def _on_sell_clicked(self, item_id: str, row_widget: QWidget) -> None:
        """Handle a sell-button click — confirm, sell, update balance."""
        if not SHOP_AVAILABLE or not self.shop_system:
            return

        catalog_item = self.shop_system.CATALOG.get(item_id)
        if catalog_item is None:
            return

        refund = math.ceil(catalog_item.price * self.shop_system.SELL_REFUND_FRACTION)

        reply = QMessageBox.question(
            self,
            "Sell item?",
            f"Sell <b>{catalog_item.name}</b> for <b>{refund} 💰 Bamboo Bucks</b>?<br>"
            f"<small>Original price: {catalog_item.price} 💰 — you get 50% back</small>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        success, message, amount = self.shop_system.sell_item(item_id)
        if success:
            if self.currency_system:
                try:
                    self.currency_system.add_coins(amount)
                    balance = self.currency_system.get_balance()
                    self.currency_label.setText(f"💰 {balance:,} Bamboo Bucks")
                except Exception:
                    pass
            self.status_label.setText(f"✅ {message}")
            # Animate the row away
            row_widget.setVisible(False)
            row_widget.deleteLater()
            self.livy_says(
                f"Sold! Hope you made the right call… 🦦 {catalog_item.icon}",
                duration_ms=4000
            )
        else:
            self.status_label.setText(f"❌ {message}")

    def showEvent(self, event):
        """Refresh coin balance and items when the shop panel becomes visible."""
        super().showEvent(event)
        try:
            self.refresh_shop()
        except Exception:
            pass

    def refresh_shop(self):
        """Refresh shop items and currency display."""
        if not SHOP_AVAILABLE or not self.shop_system:
            self.status_label.setText("⚠️ Livy's shelves are empty right now…")
            return

        # Update currency
        if self.currency_system:
            try:
                balance = self.currency_system.get_balance()
                self.currency_label.setText(f"💰 {balance:,} Bamboo Bucks")
            except Exception:
                pass

        # Clear grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get + filter items
        all_items = self.shop_system.get_available_items()
        owned_items = self.shop_system.get_purchased_items()

        if self.current_category != "All":
            all_items = [i for i in all_items if self.matches_category(i)]

        search_text = self.search_input.text().strip().lower()
        if search_text:
            all_items = [
                i for i in all_items
                if search_text in getattr(i, 'name', '').lower()
                   or search_text in getattr(i, 'description', '').lower()
            ]

        # Populate grid (3 columns)
        row, col = 0, 0
        for item in all_items[:60]:
            owned = item.id in owned_items
            widget = ShopItemWidget(item, owned,
                                    tooltip_manager=self.tooltip_manager)
            widget.purchase_requested.connect(self.purchase_item)
            widget.item_hovered.connect(self._on_item_hovered)
            self.grid_layout.addWidget(widget, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        self.status_label.setText(
            f"✨ {len(all_items)} items from across the galaxy  •  Livy says: Happy shopping! 🦦"
        )

    def matches_category(self, item: 'ShopItem') -> bool:
        """Check if item matches current category."""
        cat_map = {
            "Outfits":     "PANDA_OUTFITS",
            "Clothes":     "CLOTHES",
            "Hats":        "HATS",
            "Shoes":       "SHOES",
            "Accessories": "ACCESSORIES",
            "Fur Styles":  "FUR_STYLES",
            "Fur Colors":  "FUR_COLORS",
            "Hair Styles": "HAIRSTYLES",
            "Weapons":     "WEAPONS",
            "Armor":       "ARMOR",
            "Boots":       "BOOTS",
            "Gloves":      "GLOVES",
            "Belt":        "BELT",
            "Backpack":    "BACKPACK",
            "Toys":        "TOYS",
            "Food":        "FOOD",
            "Special":     "SPECIAL",
        }
        target_cat = cat_map.get(self.current_category)
        if not target_cat:
            return True
        return getattr(getattr(item, 'category', None), 'name', '') == target_cat

    def on_category_changed(self, category: str):
        self.current_category = category
        self.refresh_shop()

    def filter_items(self, text: str):
        self.refresh_shop()
        
    def purchase_item(self, item_id: str):
        """Purchase an item — Livy confirms the sale!"""
        if not SHOP_AVAILABLE or not self.shop_system or not self.currency_system:
            return
        item = self.shop_system.get_item(item_id)
        if not item:
            return

        balance = self.currency_system.get_balance()
        price   = getattr(item, 'price', 0)
        name    = getattr(item, 'name', item_id)
        icon    = getattr(item, 'icon', '🎁')

        if balance < price:
            QMessageBox.warning(
                self,
                "💸 Livy says: Not enough Bamboo Bucks!",
                f"{icon} {name} costs {price:,} Bamboo Bucks.\n"
                f"You have {balance:,} — earn more by completing tasks! 🌟"
            )
            self._livy_react_low_balance()
            return

        reply = QMessageBox.question(
            self,
            "🦦 Livy's Checkout",
            f"Buy {icon} {name}\nfor 💰 {price:,} Bamboo Bucks?\n\n"
            "Livy happily wraps it up for you! 🎀",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg, _ = self.shop_system.purchase_item(item_id, balance, level=0)
            if success:
                try:
                    self.currency_system.subtract('bamboo_bucks', price)
                except Exception:
                    pass
                QMessageBox.information(
                    self,
                    "✨ Purchase Complete!",
                    f"Livy hands you {icon} {name}!\n\n"
                    "Check your closet or backpack to equip it. 🎒"
                )
                self.item_purchased.emit(item_id)
                self._livy_react_purchase(item_id)
                self.refresh_shop()
            else:
                QMessageBox.warning(
                    self,
                    "⚠️ Oops!",
                    msg or "Something went wrong — Livy will investigate! 🔍"
                )
    
    def update_coin_display(self, balance: int) -> None:
        """Update the coin balance label (called by main.py after purchase/earn)."""
        try:
            self.currency_label.setText(f"💰 {balance:,} Bamboo Bucks")
        except Exception:
            pass

    # ──────────────── Livy commentary ────────────────────────────────────────

    # Idle quips Livy says while you browse (randomly selected)
    _LIVY_IDLE = [
        "👀  Browsing? Take your time, no rush!",
        "✨  Everything's fresh from the galaxy!",
        "🌌  Did you see the new arrivals?",
        "💎  Rare items don't stay long… just saying!",
        "🍵  *sips chocolate milk* …amazing selection today.",
        "🦦  I picked these items myself, you know.",
        "🌟  Pssst — the legendary stuff is *chef's kiss*.",
        "🎀  Every purchase comes gift-wrapped in cosmic energy!",
        "🐾  Panda-approved, otter-curated!",
        "💫  Quality galactic goods — that's my promise!",
        "🎵  *hums a little otter tune*",
        "🌊  Fresh stock, just like the ocean breeze!",
        "🔭  Spotted anything that sparks joy yet?",
        "✨  The accessories section is *particularly* divine today.",
        "🦦  *adjusts turquoise bow tie*  Looking sharp, as always.",
    ]

    # What Livy says when you hover over an item (templates — {name} filled in)
    _LIVY_HOVER = [
        "👀  Ooh, {name}! Great taste!",
        "✨  {name} — one of my personal favourites!",
        "💎  {name} would look *amazing* on you!",
        "🌟  Oh, you're eyeing {name}? Excellent choice!",
        "🦦  {name}? You have impeccable taste!",
        "🎀  I *love* {name} — goes with everything!",
        "💫  {name} is selling fast, just so you know…",
        "🔥  {name}! The adventurers adore that one.",
        "🌌  {name} — straight from the outer galaxy!",
        "🐾  {name} screams YOU. Just saying.",
    ]

    # What Livy says when you buy something
    _LIVY_PURCHASE = [
        "🎉  Woohoo! {name} is going home with you!",
        "✨  Excellent choice! {name} is gift-wrapped!",
        "🦦  *happy otter noises* You bought {name}!",
        "💫  {name}? PERFECT. You have the best taste.",
        "🌟  Ooh! {name}! You're going to love it!",
        "🎀  {name} is all yours — enjoy, darling!",
    ]

    # What Livy says when your balance is low
    _LIVY_LOW_BALANCE = [
        "💸  Hmm, Bamboo Bucks are a bit low… keep up the great work!",
        "🌟  Finish some tasks and you'll be rolling in Bamboo Bucks!",
        "💰  Not enough yet — but adventures earn great rewards!",
        "🦦  Don't worry! Sort some files and top up your bucks!",
        "💡  Pro tip: converting lots of files at once earns extra coins!",
    ]

    def livy_says(self, text: str, duration_ms: int = 5000) -> None:
        """Display *text* in Livy's speech bubble for *duration_ms* milliseconds."""
        try:
            self.livy_bubble.setText(text)
            # Revert to idle message after the duration
            if PYQT_AVAILABLE:
                QTimer.singleShot(duration_ms, self._livy_idle_message)
        except Exception:
            pass

    def _livy_idle_message(self) -> None:
        """Show a random idle quip in the speech bubble."""
        try:
            self.livy_bubble.setText(random.choice(self._LIVY_IDLE))
        except Exception:
            pass

    def _start_livy_idle_timer(self) -> None:
        """Start the periodic idle-commentary timer."""
        if not PYQT_AVAILABLE:
            return
        try:
            self._livy_idle_timer = QTimer(self)
            self._livy_idle_timer.setInterval(8000)  # fire every 8 seconds
            self._livy_idle_timer.timeout.connect(self._livy_idle_message)  # type: ignore[attr-defined]
            self._livy_idle_timer.start()
        except Exception:
            pass

    def _on_item_hovered(self, item: 'ShopItem') -> None:
        """Livy comments when the mouse enters an item card."""
        try:
            name = getattr(item, 'name', 'that')
            template = random.choice(self._LIVY_HOVER)
            self.livy_says(template.format(name=name), duration_ms=4000)
        except Exception:
            pass

    def _livy_react_purchase(self, item_id: str) -> None:
        """Called after a successful purchase — Livy celebrates."""
        try:
            if self.shop_system:
                item = self.shop_system.get_item(item_id)
                name = getattr(item, 'name', 'it') if item else 'it'
            else:
                name = 'it'
            template = random.choice(self._LIVY_PURCHASE)
            self.livy_says(template.format(name=name), duration_ms=6000)
        except Exception:
            pass

    def _livy_react_low_balance(self) -> None:
        """Livy sympathetically comments when user can't afford an item."""
        try:
            self.livy_says(random.choice(self._LIVY_LOW_BALANCE), duration_ms=6000)
        except Exception:
            pass

    def _set_tooltip(self, widget, tooltip_key: str):
        """Set tooltip using tooltip manager if available."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'register'):
            if ' ' not in tooltip_key:
                try:
                    tooltip = self.tooltip_manager.get_tooltip(tooltip_key)
                    if tooltip:
                        widget.setToolTip(tooltip)
                        self.tooltip_manager.register(widget, tooltip_key)
                        return
                except Exception:
                    pass
        widget.setToolTip(str(tooltip_key))
