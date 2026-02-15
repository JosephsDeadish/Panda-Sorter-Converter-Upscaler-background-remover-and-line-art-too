"""
Qt Preview Widgets - Unified preview system for tool panels
Replaces canvas-based previews in customization, closet, widgets panels
"""

from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                              QScrollArea, QGridLayout, QListWidget,
                              QListWidgetItem, QPushButton, QColorDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QImage, QPen, QBrush, QFont
from typing import List, Optional, Callable
import math


class ColorPreviewWidget(QWidget):
    """Widget for previewing colors - replaces canvas color preview"""
    
    color_selected = pyqtSignal(str)  # Emits hex color
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_color = "#FFFFFF"
        self.setMinimumSize(150, 150)
        self.setMaximumSize(200, 200)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        
        # Color display label
        self.color_label = QLabel()
        self.color_label.setMinimumSize(100, 100)
        self.color_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_label.setStyleSheet(f"""
            QLabel {{
                background: {self.current_color};
                border: 2px solid #333;
                border-radius: 8px;
            }}
        """)
        layout.addWidget(self.color_label)
        
        # Color picker button
        self.pick_button = QPushButton("Pick Color")
        self.pick_button.clicked.connect(self._open_color_picker)
        layout.addWidget(self.pick_button)
    
    def set_color(self, color: str):
        """Set the preview color"""
        self.current_color = color
        self.color_label.setStyleSheet(f"""
            QLabel {{
                background: {self.current_color};
                border: 2px solid #333;
                border-radius: 8px;
            }}
        """)
    
    def _open_color_picker(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.current_color = color.name()
            self.set_color(self.current_color)
            self.color_selected.emit(self.current_color)


class ItemPreviewWidget(QWidget):
    """Widget for previewing items (clothing, toys, etc.) - replaces canvas previews"""
    
    item_clicked = pyqtSignal(dict)  # Emits item data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_item = None
        self.setMinimumSize(200, 200)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        
        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background: #2d2d2d;
                border: 2px solid #333;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.preview_label.setMinimumSize(180, 180)
        layout.addWidget(self.preview_label)
        
        # Item name label
        self.name_label = QLabel("No item selected")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 12pt;
                font-weight: bold;
                padding: 5px;
            }
        """)
        layout.addWidget(self.name_label)
    
    def set_item(self, item: dict):
        """
        Set item to preview
        
        Args:
            item: Dict with 'emoji', 'name', 'type', etc.
        """
        self.current_item = item
        
        # Update name
        self.name_label.setText(item.get('name', 'Unknown'))
        
        # Create pixmap with item
        pixmap = QPixmap(180, 180)
        pixmap.fill(QColor("#2d2d2d"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw item emoji/icon
        emoji = item.get('emoji', '❓')
        font = QFont("Arial", 48)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, emoji)
        
        # Draw item type label
        item_type = item.get('type', 'item')
        font_small = QFont("Arial", 10)
        painter.setFont(font_small)
        painter.setPen(QColor("#888888"))
        painter.drawText(10, 170, item_type.upper())
        
        painter.end()
        
        self.preview_label.setPixmap(pixmap)
    
    def clear(self):
        """Clear preview"""
        self.current_item = None
        self.name_label.setText("No item selected")
        self.preview_label.clear()
        self.preview_label.setStyleSheet("""
            QLabel {
                background: #2d2d2d;
                border: 2px solid #333;
                border-radius: 8px;
            }
        """)


class ItemListWidget(QWidget):
    """Scrollable list of items with previews"""
    
    item_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(48, 48))
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #1e1e1e;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background: #2d2d2d;
            }
            QListWidget::item:selected {
                background: #0d7377;
                color: white;
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)
    
    def set_items(self, items: List[dict]):
        """
        Set items to display
        
        Args:
            items: List of item dicts with 'name', 'emoji', etc.
        """
        self.items = items
        self.list_widget.clear()
        
        for item in items:
            # Create list item
            list_item = QListWidgetItem()
            
            # Create pixmap for icon
            pixmap = QPixmap(48, 48)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw emoji
            emoji = item.get('emoji', '❓')
            font = QFont("Arial", 32)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, emoji)
            painter.end()
            
            list_item.setIcon(QPixmap(pixmap))
            list_item.setText(item.get('name', 'Unknown'))
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            
            self.list_widget.addItem(list_item)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle item click"""
        item_data = item.data(Qt.ItemDataRole.UserRole)
        if item_data:
            self.item_selected.emit(item_data)
    
    def clear(self):
        """Clear list"""
        self.items = []
        self.list_widget.clear()


class GridItemWidget(QWidget):
    """Grid layout of items with click handlers"""
    
    item_clicked = pyqtSignal(dict)
    
    def __init__(self, columns: int = 3, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.items = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: #1e1e1e;
                border: 1px solid #333;
            }
        """)
        
        # Grid widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        
        scroll.setWidget(self.grid_widget)
        
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
    
    def set_items(self, items: List[dict]):
        """Set items to display in grid"""
        self.items = items
        
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add items to grid
        for i, item in enumerate(items):
            row = i // self.columns
            col = i % self.columns
            
            item_widget = self._create_item_widget(item)
            self.grid_layout.addWidget(item_widget, row, col)
    
    def _create_item_widget(self, item: dict) -> QWidget:
        """Create widget for single item"""
        widget = QWidget()
        widget.setFixedSize(120, 150)
        widget.setStyleSheet("""
            QWidget {
                background: #2d2d2d;
                border: 2px solid #333;
                border-radius: 8px;
            }
            QWidget:hover {
                border-color: #0d7377;
            }
        """)
        
        layout = QVBoxLayout(widget)
        
        # Emoji label
        emoji_label = QLabel(item.get('emoji', '❓'))
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setStyleSheet("font-size: 48pt; background: transparent; border: none;")
        layout.addWidget(emoji_label)
        
        # Name label
        name_label = QLabel(item.get('name', 'Unknown'))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("""
            font-size: 10pt;
            background: transparent;
            border: none;
            padding: 5px;
        """)
        layout.addWidget(name_label)
        
        # Make clickable
        widget.mousePressEvent = lambda e: self.item_clicked.emit(item)
        
        return widget
    
    def clear(self):
        """Clear grid"""
        self.items = []
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class ImagePreviewWidget(QWidget):
    """Widget for previewing images - replaces canvas image preview"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image = None
        self.setMinimumSize(400, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                border: 2px solid #333;
                border-radius: 4px;
            }
        """)
        self.image_label.setScaledContents(False)
        layout.addWidget(self.image_label)
        
        # Info label
        self.info_label = QLabel("No image loaded")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("padding: 5px;")
        layout.addWidget(self.info_label)
    
    def set_image(self, image_path: str = None, pixmap: QPixmap = None):
        """
        Set image to preview
        
        Args:
            image_path: Path to image file
            pixmap: QPixmap to display directly
        """
        if pixmap:
            self.current_image = pixmap
        elif image_path:
            self.current_image = QPixmap(image_path)
        else:
            return
        
        # Scale to fit
        scaled = self.current_image.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled)
        
        # Update info
        if self.current_image:
            w, h = self.current_image.width(), self.current_image.height()
            self.info_label.setText(f"{w} x {h} pixels")
    
    def clear(self):
        """Clear preview"""
        self.current_image = None
        self.image_label.clear()
        self.info_label.setText("No image loaded")
    
    def resizeEvent(self, event):
        """Handle resize"""
        super().resizeEvent(event)
        if self.current_image:
            scaled = self.current_image.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)


# Factory functions for convenience
def create_color_preview() -> ColorPreviewWidget:
    """Create color preview widget"""
    return ColorPreviewWidget()


def create_item_preview() -> ItemPreviewWidget:
    """Create item preview widget"""
    return ItemPreviewWidget()


def create_item_list() -> ItemListWidget:
    """Create item list widget"""
    return ItemListWidget()


def create_item_grid(columns: int = 3) -> GridItemWidget:
    """Create item grid widget"""
    return GridItemWidget(columns)


def create_image_preview() -> ImagePreviewWidget:
    """Create image preview widget"""
    return ImagePreviewWidget()
