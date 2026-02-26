"""
Qt Dungeon Renderer Viewport

Pure PyQt6 implementation for dungeon visualization with OpenGL support.
Uses QOpenGLWidget for hardware-accelerated 3D dungeon rendering.
"""

try:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    from PyQt6.QtGui import QPainter, QColor
    from OpenGL.GL import *
    from OpenGL.GLU import *
    import math
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QOpenGLWidget = object  # Dummy for type hints
    class QWidget:  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass


class DungeonViewport(QOpenGLWidget):
    """
    OpenGL viewport for rendering dungeons.
    
    Provides 3D dungeon visualization with:
    - Hardware-accelerated rendering
    - Camera controls
    - Floor selection
    - Wall and floor rendering
    """
    
    def __init__(self, dungeon_data=None, parent=None):
        """
        Initialize dungeon viewport.
        
        Args:
            dungeon_data: Dungeon structure data
            parent: Parent widget
        """
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 and PyOpenGL required for dungeon viewport")
            
        super().__init__(parent)
        
        self.dungeon_data = dungeon_data
        self.current_floor = 0
        self.camera_angle = 45.0
        self.camera_height = 5.0
        self.camera_distance = 10.0
        
        # Animation
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(33)  # ~30 FPS
        
    def initializeGL(self):
        """Initialize OpenGL context."""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        
        # Light setup
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 10.0, 0.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
        
        glClearColor(0.1, 0.1, 0.15, 1.0)
        
    def resizeGL(self, w, h):
        """Handle window resize."""
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / h if h > 0 else 1, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        
    def paintGL(self):
        """Render the dungeon."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Camera position
        camera_x = self.camera_distance * math.cos(math.radians(self.camera_angle))
        camera_z = self.camera_distance * math.sin(math.radians(self.camera_angle))
        
        gluLookAt(
            camera_x, self.camera_height, camera_z,  # Eye
            0.0, 0.0, 0.0,  # Center
            0.0, 1.0, 0.0   # Up
        )
        
        # Draw dungeon
        self._draw_dungeon()
        
    def _draw_dungeon(self):
        """Draw the dungeon geometry."""
        if not self.dungeon_data:
            self._draw_placeholder()
            return
            
        # Draw floor
        glColor3f(0.3, 0.3, 0.4)
        glBegin(GL_QUADS)
        size = 10
        glVertex3f(-size, 0.0, -size)
        glVertex3f(size, 0.0, -size)
        glVertex3f(size, 0.0, size)
        glVertex3f(-size, 0.0, size)
        glEnd()
        
        # Draw walls (simplified - would use dungeon_data structure)
        self._draw_sample_walls()
        
    def _draw_placeholder(self):
        """Draw placeholder cube when no dungeon data."""
        glColor3f(0.5, 0.5, 0.6)
        
        # Draw a simple cube
        size = 1.0
        glBegin(GL_QUADS)
        
        # Front
        glVertex3f(-size, -size, size)
        glVertex3f(size, -size, size)
        glVertex3f(size, size, size)
        glVertex3f(-size, size, size)
        
        # Back
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, size, -size)
        glVertex3f(size, size, -size)
        glVertex3f(size, -size, -size)
        
        # Top
        glVertex3f(-size, size, -size)
        glVertex3f(-size, size, size)
        glVertex3f(size, size, size)
        glVertex3f(size, size, -size)
        
        # Bottom
        glVertex3f(-size, -size, -size)
        glVertex3f(size, -size, -size)
        glVertex3f(size, -size, size)
        glVertex3f(-size, -size, size)
        
        # Left
        glVertex3f(-size, -size, -size)
        glVertex3f(-size, -size, size)
        glVertex3f(-size, size, size)
        glVertex3f(-size, size, -size)
        
        # Right
        glVertex3f(size, -size, -size)
        glVertex3f(size, size, -size)
        glVertex3f(size, size, size)
        glVertex3f(size, -size, size)
        
        glEnd()
        
    def _draw_sample_walls(self):
        """Draw sample walls for demonstration."""
        glColor3f(0.6, 0.5, 0.4)
        
        # Simple maze-like walls
        walls = [
            (-3, 0, 0, 3),  # x1, z1, x2, z2
            (0, -3, 0, 3),
            (3, -3, 3, 0),
        ]
        
        for wall in walls:
            self._draw_wall(wall[0], wall[1], wall[2], wall[3])
            
    def _draw_wall(self, x1, z1, x2, z2):
        """Draw a single wall segment."""
        height = 2.0
        
        glBegin(GL_QUADS)
        glVertex3f(x1, 0.0, z1)
        glVertex3f(x2, 0.0, z2)
        glVertex3f(x2, height, z2)
        glVertex3f(x1, height, z1)
        glEnd()
        
    def set_floor(self, floor_index):
        """
        Set the current floor to display.
        
        Args:
            floor_index: Floor number to display
        """
        self.current_floor = floor_index
        self.update()
        
    def set_dungeon(self, dungeon_data):
        """
        Set new dungeon data.
        
        Args:
            dungeon_data: Dungeon structure to render
        """
        self.dungeon_data = dungeon_data
        self.update()
        
    def mousePressEvent(self, event):
        """Handle mouse press for camera control."""
        self.last_mouse_pos = event.pos()
        
    def mouseMoveEvent(self, event):
        """Handle mouse drag for camera rotation."""
        if hasattr(self, 'last_mouse_pos'):
            dx = event.pos().x() - self.last_mouse_pos.x()
            self.camera_angle += dx * 0.5
            self.last_mouse_pos = event.pos()
            self.update()
            
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom."""
        delta = event.angleDelta().y()
        self.camera_distance -= delta * 0.01
        self.camera_distance = max(3.0, min(20.0, self.camera_distance))
        self.update()


class DungeonViewportWidget(QWidget):
    """
    Complete dungeon viewport widget with controls.
    
    Includes:
    - OpenGL viewport
    - Floor selector
    - Camera controls
    """
    
    def __init__(self, dungeon_data=None, parent=None):
        """
        Initialize dungeon widget.
        
        Args:
            dungeon_data: Dungeon structure
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._setup_ui(dungeon_data)
        
    def _setup_ui(self, dungeon_data):
        """Create UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Info label
        info_label = QLabel("🏰 Dungeon View - Drag to rotate, scroll to zoom")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 5px;
                font-size: 12pt;
            }
        """)
        layout.addWidget(info_label)
        
        # OpenGL viewport
        self.viewport = DungeonViewport(dungeon_data, self)
        layout.addWidget(self.viewport, 1)
        
    def set_floor(self, floor_index):
        """Set current floor."""
        self.viewport.set_floor(floor_index)
        
    def set_dungeon(self, dungeon_data):
        """Set dungeon data."""
        self.viewport.set_dungeon(dungeon_data)


# Test/demo
if __name__ == "__main__":
    if PYQT_AVAILABLE:
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication(sys.argv)
        
        widget = DungeonViewportWidget()
        widget.setWindowTitle("Dungeon Viewport Demo")
        widget.resize(800, 600)
        widget.show()
        
        sys.exit(app.exec())
