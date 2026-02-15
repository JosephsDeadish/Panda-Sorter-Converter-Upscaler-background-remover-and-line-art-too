"""
PyQt6 Weapon Positioning System
Replaces canvas-based weapon positioning with QGraphicsView
"""

try:
    from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                                 QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                 QLabel, QSlider, QSpinBox)
    from PyQt6.QtCore import Qt, QPointF, pyqtSignal
    from PyQt6.QtGui import QPixmap, QPainter, QTransform
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class WeaponPositioningView(QGraphicsView):
    """QGraphicsView for weapon positioning with drag support"""
    
    position_changed = pyqtSignal(float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Weapon item
        self.weapon_item = None
        self.dragging = False
        self.drag_start = QPointF()
        
        # Setup
        self.setSceneRect(-200, -200, 400, 400)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
    def set_weapon_image(self, pixmap):
        """Set weapon image"""
        if self.weapon_item:
            self.scene.removeItem(self.weapon_item)
        
        self.weapon_item = QGraphicsPixmapItem(pixmap)
        self.weapon_item.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable)
        self.scene.addItem(self.weapon_item)
        self.weapon_item.setPos(0, 0)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.weapon_item:
            self.dragging = True
            self.drag_start = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.dragging and self.weapon_item:
            pos = self.weapon_item.pos()
            self.position_changed.emit(pos.x(), pos.y())
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        self.dragging = False
        super().mouseReleaseEvent(event)


class WeaponPositioningWidget(QWidget):
    """Complete weapon positioning widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Graphics view
        self.view = WeaponPositioningView()
        layout.addWidget(self.view)
        
        # Controls
        controls = QHBoxLayout()
        
        # X position
        controls.addWidget(QLabel("X:"))
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-200, 200)
        controls.addWidget(self.x_spin)
        
        # Y position  
        controls.addWidget(QLabel("Y:"))
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-200, 200)
        controls.addWidget(self.y_spin)
        
        # Rotation
        controls.addWidget(QLabel("Rotation:"))
        self.rotation_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotation_slider.setRange(0, 360)
        controls.addWidget(self.rotation_slider)
        
        layout.addLayout(controls)
        
        # Buttons
        buttons = QHBoxLayout()
        self.reset_btn = QPushButton("Reset")
        self.save_btn = QPushButton("Save")
        buttons.addWidget(self.reset_btn)
        buttons.addWidget(self.save_btn)
        layout.addLayout(buttons)
        
        # Connect signals
        self.view.position_changed.connect(self.on_position_changed)
        self.x_spin.valueChanged.connect(self.on_spin_changed)
        self.y_spin.valueChanged.connect(self.on_spin_changed)
        self.rotation_slider.valueChanged.connect(self.on_rotation_changed)
        
    def on_position_changed(self, x, y):
        self.x_spin.setValue(int(x))
        self.y_spin.setValue(int(y))
        
    def on_spin_changed(self):
        if self.view.weapon_item:
            self.view.weapon_item.setPos(self.x_spin.value(), self.y_spin.value())
            
    def on_rotation_changed(self, angle):
        if self.view.weapon_item:
            transform = QTransform()
            transform.rotate(angle)
            self.view.weapon_item.setTransform(transform)
            
    def set_weapon(self, weapon_data):
        """Set weapon to position"""
        # Load weapon image
        if 'image_path' in weapon_data:
            pixmap = QPixmap(weapon_data['image_path'])
            if not pixmap.isNull():
                self.view.set_weapon_image(pixmap)
                
    def get_weapon_transform(self):
        """Get current weapon positioning"""
        if not self.view.weapon_item:
            return None
        
        pos = self.view.weapon_item.pos()
        return {
            'x': pos.x(),
            'y': pos.y(),
            'rotation': self.rotation_slider.value()
        }


def create_weapon_positioning_widget(parent=None):
    """Factory function"""
    if not PYQT_AVAILABLE:
        return None
    return WeaponPositioningWidget(parent)
