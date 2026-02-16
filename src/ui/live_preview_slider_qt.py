"""
Live Preview with Comparison Slider - PyQt6
Provides before/after comparison with draggable vertical slider
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPixmap, QColor, QCursor
import logging

logger = logging.getLogger(__name__)


class ComparisonSliderWidget(QWidget):
    """Before/After comparison with draggable vertical slider"""
    
    slider_moved = pyqtSignal(int)  # Emit slider position (0-100%)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.before_pixmap = None
        self.after_pixmap = None
        self.slider_position = 50  # 0-100, percentage from left
        self.is_dragging = False
        self.comparison_mode = "slider"  # slider, toggle, overlay
        self.showing_after = True  # For toggle mode
        
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.SplitHCursor))
        
    def set_before_image(self, pixmap):
        """Set the 'before' image"""
        if isinstance(pixmap, str):
            self.before_pixmap = QPixmap(pixmap)
        else:
            self.before_pixmap = pixmap
        self.update()
        
    def set_after_image(self, pixmap):
        """Set the 'after' image"""
        if isinstance(pixmap, str):
            self.after_pixmap = QPixmap(pixmap)
        else:
            self.after_pixmap = pixmap
        self.update()
        
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
                           "No images loaded")
            return
        
        if self.comparison_mode == "slider":
            self._paint_slider_mode(painter, widget_rect)
        elif self.comparison_mode == "toggle":
            self._paint_toggle_mode(painter, widget_rect)
        elif self.comparison_mode == "overlay":
            self._paint_overlay_mode(painter, widget_rect)
            
    def _paint_slider_mode(self, painter, widget_rect):
        """Paint slider comparison mode"""
        # Calculate slider position in pixels
        slider_x = int(widget_rect.width() * (self.slider_position / 100.0))
        
        # Scale images to fit
        before_scaled = self._scale_to_fit(self.before_pixmap, widget_rect.size())
        after_scaled = self._scale_to_fit(self.after_pixmap, widget_rect.size())
        
        if not before_scaled or not after_scaled:
            return
        
        # Center images
        x_offset = (widget_rect.width() - before_scaled.width()) // 2
        y_offset = (widget_rect.height() - before_scaled.height()) // 2
        
        # Draw before image (left side)
        if self.before_pixmap and slider_x > 0:
            # Create clipping region for left side
            before_rect = QRect(x_offset, y_offset, slider_x - x_offset, before_scaled.height())
            painter.setClipRect(before_rect)
            painter.drawPixmap(x_offset, y_offset, before_scaled)
        
        # Draw after image (right side)
        if self.after_pixmap and slider_x < widget_rect.width():
            # Create clipping region for right side
            after_rect = QRect(slider_x, y_offset, 
                             widget_rect.width() - slider_x, after_scaled.height())
            painter.setClipRect(after_rect)
            painter.drawPixmap(x_offset, y_offset, after_scaled)
        
        # Reset clipping
        painter.setClipping(False)
        
        # Draw slider line
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(slider_x, 0, slider_x, widget_rect.height())
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawLine(slider_x, 0, slider_x, widget_rect.height())
        
        # Draw slider handle (circle in the middle)
        handle_y = widget_rect.height() // 2
        handle_radius = 15
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawEllipse(slider_x - handle_radius, handle_y - handle_radius,
                          handle_radius * 2, handle_radius * 2)
        
        # Draw arrows in handle
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        # Left arrow
        painter.drawLine(slider_x - 6, handle_y, slider_x - 2, handle_y - 4)
        painter.drawLine(slider_x - 6, handle_y, slider_x - 2, handle_y + 4)
        # Right arrow
        painter.drawLine(slider_x + 6, handle_y, slider_x + 2, handle_y - 4)
        painter.drawLine(slider_x + 6, handle_y, slider_x + 2, handle_y + 4)
        
        # Draw labels
        self._draw_labels(painter, widget_rect, x_offset, y_offset, 
                         before_scaled.height())
        
    def _paint_toggle_mode(self, painter, widget_rect):
        """Paint toggle comparison mode"""
        pixmap = self.after_pixmap if self.showing_after else self.before_pixmap
        
        if not pixmap:
            return
            
        scaled = self._scale_to_fit(pixmap, widget_rect.size())
        if not scaled:
            return
            
        # Center image
        x_offset = (widget_rect.width() - scaled.width()) // 2
        y_offset = (widget_rect.height() - scaled.height()) // 2
        
        painter.drawPixmap(x_offset, y_offset, scaled)
        
        # Draw label
        label_text = "AFTER" if self.showing_after else "BEFORE"
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(10, 30, label_text)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(11, 31, label_text)
        
    def _paint_overlay_mode(self, painter, widget_rect):
        """Paint overlay comparison mode"""
        if not self.before_pixmap or not self.after_pixmap:
            return
            
        before_scaled = self._scale_to_fit(self.before_pixmap, widget_rect.size())
        after_scaled = self._scale_to_fit(self.after_pixmap, widget_rect.size())
        
        if not before_scaled or not after_scaled:
            return
            
        # Center images
        x_offset = (widget_rect.width() - before_scaled.width()) // 2
        y_offset = (widget_rect.height() - before_scaled.height()) // 2
        
        # Draw before image at full opacity
        painter.drawPixmap(x_offset, y_offset, before_scaled)
        
        # Draw after image at 50% opacity
        painter.setOpacity(0.5)
        painter.drawPixmap(x_offset, y_offset, after_scaled)
        painter.setOpacity(1.0)
        
        # Draw labels
        self._draw_labels(painter, widget_rect, x_offset, y_offset,
                         before_scaled.height(), overlay=True)
        
    def _draw_labels(self, painter, widget_rect, x_offset, y_offset, 
                    img_height, overlay=False):
        """Draw BEFORE/AFTER labels"""
        if overlay:
            # For overlay mode, show both labels
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x_offset + 10, y_offset + 30, "BEFORE (100%)")
            painter.drawText(x_offset + 10, y_offset + 55, "AFTER (50%)")
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(x_offset + 11, y_offset + 31, "BEFORE (100%)")
            painter.drawText(x_offset + 11, y_offset + 56, "AFTER (50%)")
        else:
            # For slider mode, show labels on respective sides
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x_offset + 10, y_offset + 30, "BEFORE")
            painter.drawText(widget_rect.width() - x_offset - 80, y_offset + 30, "AFTER")
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(x_offset + 11, y_offset + 31, "BEFORE")
            painter.drawText(widget_rect.width() - x_offset - 79, y_offset + 31, "AFTER")
        
    def _scale_to_fit(self, pixmap, size):
        """Scale pixmap to fit within size while maintaining aspect ratio"""
        if not pixmap or pixmap.isNull():
            return None
        return pixmap.scaled(size.width(), size.height(), 
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if self.comparison_mode == "slider" and event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self._update_slider_from_mouse(event.pos())
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.comparison_mode == "slider":
            # Update cursor when hovering near slider
            slider_x = int(self.width() * (self.slider_position / 100.0))
            if abs(event.pos().x() - slider_x) < 20:
                self.setCursor(QCursor(Qt.CursorShape.SplitHCursor))
            
            if self.is_dragging:
                self._update_slider_from_mouse(event.pos())
                
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            
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
        self.status_label = QLabel("Drag the slider to compare images")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
    def _on_mode_changed(self, mode_text):
        """Handle mode change"""
        mode = mode_text.lower()
        self.comparison_widget.set_mode(mode)
        
        if mode == "slider":
            self.status_label.setText("Drag the slider to compare images")
        elif mode == "toggle":
            self.status_label.setText("Click to toggle between before and after")
        elif mode == "overlay":
            self.status_label.setText("Images overlaid with 50% opacity")
            
    def set_before_image(self, pixmap):
        """Set before image"""
        self.comparison_widget.set_before_image(pixmap)
        
    def set_after_image(self, pixmap):
        """Set after image"""
        self.comparison_widget.set_after_image(pixmap)
