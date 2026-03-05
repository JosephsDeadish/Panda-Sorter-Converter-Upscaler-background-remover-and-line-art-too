"""
Live Preview with Comparison Slider - PyQt6
Provides before/after comparison with draggable vertical slider
"""


from __future__ import annotations
try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
    from PyQt6.QtCore import Qt, QRect, pyqtSignal
    from PyQt6.QtGui import QPainter, QPen, QPixmap, QColor, QCursor
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    class _SignalStub:  # noqa: E301
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SignalStub()  # noqa: E301
    class Qt:
        class AlignmentFlag:
            AlignLeft = AlignRight = AlignCenter = AlignTop = AlignBottom = AlignHCenter = AlignVCenter = 0
        class WindowType:
            FramelessWindowHint = WindowStaysOnTopHint = Tool = Window = Dialog = 0
        class CursorShape:
            ArrowCursor = PointingHandCursor = BusyCursor = WaitCursor = CrossCursor = 0
        class DropAction:
            CopyAction = MoveAction = IgnoreAction = 0
        class Key:
            Key_Escape = Key_Return = Key_Space = Key_Delete = Key_Up = Key_Down = Key_Left = Key_Right = 0
        class ScrollBarPolicy:
            ScrollBarAlwaysOff = ScrollBarAsNeeded = ScrollBarAlwaysOn = 0
        class ItemFlag:
            ItemIsEnabled = ItemIsSelectable = ItemIsEditable = 0
        class CheckState:
            Unchecked = Checked = PartiallyChecked = 0
        class Orientation:
            Horizontal = Vertical = 0
        class SortOrder:
            AscendingOrder = DescendingOrder = 0
        class MatchFlag:
            MatchExactly = MatchContains = 0
        class ItemDataRole:
            DisplayRole = UserRole = DecorationRole = 0
    class QColor:
        def __init__(self, *a): pass
        def name(self): return "#000000"
        def isValid(self): return False
    class QPixmap:
        def __init__(self, *a): pass
        def isNull(self): return True
    class QPainter:
        def __init__(self, *a): pass
    class QPen:
        def __init__(self, *a): pass
    class QRect:
        def __init__(self, *a): pass
    class QCursor:
        def __init__(self, *a): pass
    QComboBox = object
    QHBoxLayout = object
    QLabel = object
    QVBoxLayout = object
import logging

logger = logging.getLogger(__name__)


class ComparisonSliderWidget(QWidget):
    """Before/After comparison with draggable vertical slider, pan, and zoom."""
    
    slider_moved = pyqtSignal(int)  # Emit slider position (0-100%)

    # Hit-detection radius around the slider handle (pixels)
    SLIDER_HANDLE_HIT_RADIUS = 20
    # Maximum number of results returned by content search
    MAX_CONTENT_SEARCH_RESULTS = 50
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.before_pixmap = None
        self.after_pixmap = None
        self.slider_position = 50  # 0-100, percentage from left
        self.is_dragging = False
        self.comparison_mode = "slider"  # slider, toggle, overlay
        self.showing_after = True  # For toggle mode

        # Pan / Zoom state
        self._zoom = 1.0           # current zoom level (1.0 = fit-to-widget)
        self._pan_x = 0.0          # horizontal pan offset in *logical* pixels
        self._pan_y = 0.0          # vertical pan offset in *logical* pixels
        self._pan_dragging = False # True while middle-button or Ctrl+LMB panning
        self._pan_last = None      # last QPoint during pan drag

        self.setMinimumSize(250, 200)
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.SplitHCursor))
        
    def set_before_image(self, pixmap):
        """Set the 'before' image"""
        if isinstance(pixmap, str):
            self.before_pixmap = QPixmap(pixmap)
        else:
            self.before_pixmap = pixmap
        self.reset_zoom()
        
    def set_after_image(self, pixmap):
        """Set the 'after' image"""
        if isinstance(pixmap, str):
            self.after_pixmap = QPixmap(pixmap)
        else:
            self.after_pixmap = pixmap
        self.reset_zoom()
        
    def set_mode(self, mode):
        """Set comparison mode: 'slider', 'toggle', or 'overlay'"""
        self.comparison_mode = mode
        if mode == "slider":
            self.setCursor(QCursor(Qt.CursorShape.SplitHCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.update()
        
    def get_slider_position(self):
        """Get slider position as percentage (0-100)"""
        return self.slider_position
        
    def set_slider_position(self, position):
        """Set slider position as percentage (0-100)"""
        self.slider_position = max(0, min(100, position))
        self.update()
        
    def toggle_view(self):
        """Toggle between before and after (toggle mode only)"""
        self.showing_after = not self.showing_after
        self.update()
        
    def reset_zoom(self):
        """Reset zoom and pan to fit-view defaults."""
        self._zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self.update()

    def _apply_zoom_pan(self, painter, widget_rect):
        """Apply current zoom/pan transform to *painter*.

        Returns (x_offset, y_offset, img_w, img_h) of the base-fit image position
        so callers can use these to position the slider line correctly.
        """
        # Determine the base image size from whichever pixmap is available
        pm = self.before_pixmap or self.after_pixmap
        if pm is None or pm.isNull():
            return 0, 0, widget_rect.width(), widget_rect.height()
        fit_pm = pm.scaled(widget_rect.size(),
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        base_w = fit_pm.width()
        base_h = fit_pm.height()
        # Center at fit-size, then apply pan and zoom around widget centre
        cx = widget_rect.width() / 2.0
        cy = widget_rect.height() / 2.0
        painter.translate(cx + self._pan_x, cy + self._pan_y)
        painter.scale(self._zoom, self._zoom)
        painter.translate(-base_w / 2.0, -base_h / 2.0)
        return 0, 0, base_w, base_h

    def _scaled_at_zoom(self, pixmap, widget_rect):
        """Return pixmap scaled to fit-to-widget size (zoom applied via painter transform)."""
        if pixmap is None or pixmap.isNull():
            return None
        return pixmap.scaled(widget_rect.size(),
                             Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)

    def paintEvent(self, event):
        """Custom paint event to draw before/after with slider"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Get widget dimensions
        widget_rect = self.rect()
        
        if not self.before_pixmap and not self.after_pixmap:
            # Draw placeholder
            painter.fillRect(widget_rect, QColor(240, 240, 240))
            painter.setPen(QColor(128, 128, 128))
            painter.drawText(widget_rect, Qt.AlignmentFlag.AlignCenter, 
                           "No images loaded\n\nScroll to zoom · Middle-click/Ctrl+drag to pan")
            return
        
        if self.comparison_mode == "slider":
            self._paint_slider_mode(painter, widget_rect)
        elif self.comparison_mode == "toggle":
            self._paint_toggle_mode(painter, widget_rect)
        elif self.comparison_mode == "overlay":
            self._paint_overlay_mode(painter, widget_rect)

        # Draw zoom level indicator when zoomed
        if abs(self._zoom - 1.0) > 0.01 or self._pan_x != 0 or self._pan_y != 0:
            painter.resetTransform()
            painter.setPen(QColor(255, 255, 255))
            zoom_text = f"Zoom: {self._zoom:.1f}×"
            painter.fillRect(widget_rect.width() - 110, 6, 104, 20, QColor(0, 0, 0, 140))
            painter.drawText(widget_rect.width() - 106, 20, zoom_text)
            
    def _paint_slider_mode(self, painter, widget_rect):
        """Paint slider comparison mode"""
        painter.save()
        img_x, img_y, img_w, img_h = self._apply_zoom_pan(painter, widget_rect)

        before_scaled = self._scaled_at_zoom(self.before_pixmap, widget_rect)
        after_scaled = self._scaled_at_zoom(self.after_pixmap, widget_rect)

        # If only one image is available, show it as a full-widget preview
        if not before_scaled and not after_scaled:
            painter.restore()
            return
        if not before_scaled or not after_scaled:
            # Fall back to single-image mode: show whichever image is present
            only_pm = self.before_pixmap or self.after_pixmap
            only_label = "BEFORE" if self.before_pixmap else "PROCESSED"
            scaled = self._scaled_at_zoom(only_pm, widget_rect)
            if scaled:
                painter.drawPixmap(0, 0, scaled)
            painter.restore()
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(10, 25, only_label)
            return

        # Slider position in *logical* (pre-zoom/pan) image-coordinate x
        # We compute slider_x in original widget coordinates, then map through
        # the inverse transform for clipping.
        painter.restore()

        # Re-do without the zoom transform so we can clip correctly in widget space
        # Determine where the image lands in widget space after zoom+pan
        pm = self.before_pixmap or self.after_pixmap
        fit = pm.scaled(widget_rect.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)
        base_w = fit.width()
        base_h = fit.height()
        cx = widget_rect.width() / 2.0 + self._pan_x
        cy = widget_rect.height() / 2.0 + self._pan_y
        draw_x = cx - base_w * self._zoom / 2.0
        draw_y = cy - base_h * self._zoom / 2.0
        zoomed_w = int(base_w * self._zoom)
        zoomed_h = int(base_h * self._zoom)

        # Scale pixmaps to zoomed size
        b_zoom = self.before_pixmap.scaled(zoomed_w, zoomed_h,
                                           Qt.AspectRatioMode.IgnoreAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
        a_zoom = self.after_pixmap.scaled(zoomed_w, zoomed_h,
                                          Qt.AspectRatioMode.IgnoreAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)

        # Slider x in widget pixels
        slider_x = int(widget_rect.width() * (self.slider_position / 100.0))

        # Draw before (left of slider)
        if slider_x > 0:
            painter.setClipRect(QRect(0, 0, slider_x, widget_rect.height()))
            painter.drawPixmap(int(draw_x), int(draw_y), b_zoom)

        # Draw after (right of slider)
        if slider_x < widget_rect.width():
            painter.setClipRect(QRect(slider_x, 0,
                                      widget_rect.width() - slider_x,
                                      widget_rect.height()))
            painter.drawPixmap(int(draw_x), int(draw_y), a_zoom)

        painter.setClipping(False)

        # Slider line
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(slider_x, 0, slider_x, widget_rect.height())
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawLine(slider_x, 0, slider_x, widget_rect.height())

        # Slider handle
        handle_y = widget_rect.height() // 2
        handle_radius = 15
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawEllipse(slider_x - handle_radius, handle_y - handle_radius,
                          handle_radius * 2, handle_radius * 2)

        # Arrows in handle
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawLine(slider_x - 6, handle_y, slider_x - 2, handle_y - 4)
        painter.drawLine(slider_x - 6, handle_y, slider_x - 2, handle_y + 4)
        painter.drawLine(slider_x + 6, handle_y, slider_x + 2, handle_y - 4)
        painter.drawLine(slider_x + 6, handle_y, slider_x + 2, handle_y + 4)

        # Labels
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(int(draw_x) + 10, int(draw_y) + 30, "BEFORE")
        painter.drawText(widget_rect.width() - int(draw_x) - 80, int(draw_y) + 30, "AFTER")
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(int(draw_x) + 11, int(draw_y) + 31, "BEFORE")
        painter.drawText(widget_rect.width() - int(draw_x) - 79, int(draw_y) + 31, "AFTER")

    def _paint_toggle_mode(self, painter, widget_rect):
        """Paint toggle comparison mode"""
        pixmap = self.after_pixmap if self.showing_after else self.before_pixmap
        
        if not pixmap:
            return

        painter.save()
        img_x, img_y, img_w, img_h = self._apply_zoom_pan(painter, widget_rect)
        scaled = self._scaled_at_zoom(pixmap, widget_rect)
        if scaled:
            painter.drawPixmap(img_x, img_y, scaled)
        painter.restore()

        label_text = "AFTER" if self.showing_after else "BEFORE"
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(10, 30, label_text)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(11, 31, label_text)
        
    def _paint_overlay_mode(self, painter, widget_rect):
        """Paint overlay comparison mode"""
        if not self.before_pixmap or not self.after_pixmap:
            return

        painter.save()
        img_x, img_y, img_w, img_h = self._apply_zoom_pan(painter, widget_rect)
        before_scaled = self._scaled_at_zoom(self.before_pixmap, widget_rect)
        after_scaled = self._scaled_at_zoom(self.after_pixmap, widget_rect)
        if before_scaled:
            painter.drawPixmap(img_x, img_y, before_scaled)
        if after_scaled:
            painter.setOpacity(0.5)
            painter.drawPixmap(img_x, img_y, after_scaled)
            painter.setOpacity(1.0)
        painter.restore()

        painter.setPen(QColor(255, 255, 255))
        painter.drawText(10, 30, "BEFORE (100%)")
        painter.drawText(10, 55, "AFTER (50%)")
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(11, 31, "BEFORE (100%)")
        painter.drawText(11, 56, "AFTER (50%)")
        
    def _scale_to_fit(self, pixmap, size):
        """Scale pixmap to fit within size while maintaining aspect ratio"""
        if not pixmap or pixmap.isNull():
            return None
        return pixmap.scaled(size.width(), size.height(), 
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        
    def mousePressEvent(self, event):
        """Handle mouse press — drag slider when near handle, pan otherwise."""
        # Middle-click or Ctrl+LMB → start panning
        if (event.button() == Qt.MouseButton.MiddleButton or
                (event.button() == Qt.MouseButton.LeftButton and
                 event.modifiers() & Qt.KeyboardModifier.ControlModifier)):
            self._pan_dragging = True
            self._pan_last = event.pos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return

        if self.comparison_mode == "slider" and event.button() == Qt.MouseButton.LeftButton:
            slider_x = int(self.width() * (self.slider_position / 100.0))
            # Only begin dragging when the click lands within the handle area
            if abs(event.pos().x() - slider_x) <= self.SLIDER_HANDLE_HIT_RADIUS:
                self.is_dragging = True
                self._update_slider_from_mouse(event.pos())
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging and panning."""
        # Panning
        if self._pan_dragging and self._pan_last is not None:
            delta = event.pos() - self._pan_last
            self._pan_x += delta.x()
            self._pan_y += delta.y()
            self._pan_last = event.pos()
            self.update()
            return

        if self.comparison_mode == "slider":
            # Update cursor when hovering near slider
            slider_x = int(self.width() * (self.slider_position / 100.0))
            if abs(event.pos().x() - slider_x) < self.SLIDER_HANDLE_HIT_RADIUS:
                self.setCursor(QCursor(Qt.CursorShape.SplitHCursor))
            elif not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            
            if self.is_dragging:
                self._update_slider_from_mouse(event.pos())
                
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self.is_dragging = False
            if self._pan_dragging:
                self._pan_dragging = False
                self._pan_last = None
                if self.comparison_mode == "slider":
                    self.setCursor(QCursor(Qt.CursorShape.SplitHCursor))
                else:
                    self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def wheelEvent(self, event):
        """Scroll wheel → zoom in/out around cursor position."""
        try:
            delta = event.angleDelta().y()
        except Exception:
            return
        zoom_factor = 1.15 if delta > 0 else 1.0 / 1.15
        new_zoom = max(0.25, min(8.0, self._zoom * zoom_factor))
        if new_zoom == self._zoom:
            return
        # Zoom towards cursor — use pos() for compatibility across PyQt6 versions
        try:
            cursor_x = event.position().x() - self.width() / 2.0 - self._pan_x
            cursor_y = event.position().y() - self.height() / 2.0 - self._pan_y
        except AttributeError:
            cursor_x = event.pos().x() - self.width() / 2.0 - self._pan_x
            cursor_y = event.pos().y() - self.height() / 2.0 - self._pan_y
        self._pan_x += cursor_x * (1 - new_zoom / self._zoom)
        self._pan_y += cursor_y * (1 - new_zoom / self._zoom)
        self._zoom = new_zoom
        self.update()
        event.accept()

    def mouseDoubleClickEvent(self, event):
        """Double-click resets zoom/pan."""
        self.reset_zoom()

    def _update_slider_from_mouse(self, pos):
        """Update slider position from mouse position"""
        new_position = (pos.x() / self.width()) * 100
        self.slider_position = max(0, min(100, new_position))
        self.slider_moved.emit(int(self.slider_position))
        self.update()


class LivePreviewSliderPanel(QWidget):
    """Complete panel with comparison slider and controls"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_ui()
        
    def _create_ui(self):
        """Create UI layout"""
        layout = QVBoxLayout(self)
        
        # Mode selector
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Comparison Mode:"))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Slider", "Toggle", "Overlay"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        controls_layout.addWidget(self.mode_combo)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Comparison widget
        self.comparison_widget = ComparisonSliderWidget()
        layout.addWidget(self.comparison_widget)
        
        # Status
        self.status_label = QLabel("Drag the slider handle to compare · Scroll to zoom · Middle-click or Ctrl+drag to pan · Double-click to reset")
        self.status_label.setStyleSheet("color: gray; font-size: 9pt;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
    def _on_mode_changed(self, mode_text):
        """Handle mode change"""
        mode = mode_text.lower()
        self.comparison_widget.set_mode(mode)
        
        hint = " · Scroll to zoom · Middle-click/Ctrl+drag to pan · Double-click to reset"
        if mode == "slider":
            self.status_label.setText("Drag the slider handle to compare" + hint)
        elif mode == "toggle":
            self.status_label.setText("Click to toggle between before and after" + hint)
        elif mode == "overlay":
            self.status_label.setText("Images overlaid with 50% opacity" + hint)
            
    def set_before_image(self, pixmap):
        """Set before image"""
        self.comparison_widget.set_before_image(pixmap)
        
    def set_after_image(self, pixmap):
        """Set after image"""
        self.comparison_widget.set_after_image(pixmap)
