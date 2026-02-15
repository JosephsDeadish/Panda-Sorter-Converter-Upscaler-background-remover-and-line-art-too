"""
Preview Viewer - Image preview with zoom, pan, and properties
Provides a non-blocking, moveable preview window for texture files
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import Optional, List
from collections import deque
from PIL import Image
import os

logger = logging.getLogger(__name__)

# Try to import GUI libraries
try:
    from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFrame, 
                                  QLabel, QPushButton, QGraphicsView, QGraphicsScene,
                                  QGraphicsPixmapItem, QScrollArea, QWidget, QFileDialog)
    from PyQt6.QtCore import Qt, QRectF, pyqtSignal
    from PyQt6.QtGui import QPixmap, QImage, QWheelEvent, QMouseEvent, QKeyEvent
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


class PreviewViewer:
    """
    Moveable preview window with zoom, pan, and navigation controls
    """
    
    def __init__(self, master_window):
        self.master = master_window
        self.preview_window = None
        self.current_file = None
        self.file_list = []
        self.current_index = 0
        
        # Image display state
        self.original_image = None
        self.zoom_level = 1.0
        
        # QGraphicsView components
        self.graphics_view = None
        self.graphics_scene = None
        self.pixmap_item = None
        
        # UI components
        self.zoom_label = None
        self.status_label = None
        self.properties_panel = None
        self.properties_scroll = None
        self.properties_visible = False
        
    def open_preview(self, file_path: str, file_list: Optional[List[str]] = None):
        """
        Open preview window for a texture file
        
        Args:
            file_path: Path to the texture file to preview
            file_list: Optional list of files for navigation
        """
        if not GUI_AVAILABLE:
            logger.warning("GUI not available, cannot open preview")
            return
        
        self.current_file = Path(file_path)
        
        # Set up file list for navigation
        if file_list:
            self.file_list = [Path(f) for f in file_list]
            try:
                self.current_index = self.file_list.index(self.current_file)
            except ValueError:
                self.file_list = [self.current_file]
                self.current_index = 0
        else:
            # Get all texture files in the same directory
            self.file_list = self._get_sibling_textures(self.current_file)
            try:
                self.current_index = self.file_list.index(self.current_file)
            except ValueError:
                self.current_index = 0
        
        # Create or update window
        if self.preview_window is None or not self.preview_window.isVisible():
            self._create_preview_window()
        
        # Load and display the image
        self._load_image(self.current_file)
        
        # Update window title and properties
        self._update_window_title()
        
        # Bring window to front
        self.preview_window.raise_()
        self.preview_window.activateWindow()
    
    def _create_preview_window(self):
        """Create the preview window UI"""
        self.preview_window = QDialog(self.master)
        self.preview_window.setWindowTitle("Preview Viewer")
        self.preview_window.resize(900, 700)
        
        # Main layout
        main_layout = QVBoxLayout(self.preview_window)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # === TOOLBAR ===
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Navigation buttons
        prev_btn = QPushButton("◀ Previous")
        prev_btn.setFixedWidth(100)
        prev_btn.clicked.connect(self._show_previous)
        toolbar_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("Next ▶")
        next_btn.setFixedWidth(100)
        next_btn.clicked.connect(self._show_next)
        toolbar_layout.addWidget(next_btn)
        
        toolbar_layout.addSpacing(20)
        
        # Zoom controls
        zoom_out_btn = QPushButton("🔍−")
        zoom_out_btn.setFixedWidth(50)
        zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar_layout.addWidget(zoom_out_btn)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(60)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar_layout.addWidget(self.zoom_label)
        
        zoom_in_btn = QPushButton("🔍+")
        zoom_in_btn.setFixedWidth(50)
        zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar_layout.addWidget(zoom_in_btn)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(70)
        reset_btn.clicked.connect(self._reset_view)
        toolbar_layout.addWidget(reset_btn)
        
        fit_btn = QPushButton("Fit")
        fit_btn.setFixedWidth(60)
        fit_btn.clicked.connect(self._fit_to_window)
        toolbar_layout.addWidget(fit_btn)
        
        actual_size_btn = QPushButton("1:1")
        actual_size_btn.setFixedWidth(50)
        actual_size_btn.clicked.connect(self._actual_size)
        toolbar_layout.addWidget(actual_size_btn)
        
        toolbar_layout.addStretch()
        
        # Properties toggle
        props_btn = QPushButton("ℹ️ Properties")
        props_btn.setFixedWidth(100)
        props_btn.clicked.connect(self._toggle_properties)
        toolbar_layout.addWidget(props_btn)
        
        # Export button
        export_btn = QPushButton("💾 Export")
        export_btn.setFixedWidth(100)
        export_btn.clicked.connect(self._export_image)
        toolbar_layout.addWidget(export_btn)
        
        main_layout.addWidget(toolbar)
        
        # === MAIN CONTENT AREA ===
        content_layout = QHBoxLayout()
        
        # QGraphicsView for image display
        self.graphics_scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.graphics_scene)
        self.graphics_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.graphics_view.setRenderHint(self.graphics_view.renderHints())
        self.graphics_view.setBackgroundBrush(Qt.GlobalColor.darkGray)
        self.graphics_view.setFrameStyle(0)
        
        # Enable wheel zoom
        self.graphics_view.wheelEvent = self._graphics_wheel_event
        
        content_layout.addWidget(self.graphics_view, stretch=1)
        
        # Properties panel (initially hidden)
        self.properties_panel = QFrame()
        self.properties_panel.setFixedWidth(250)
        self.properties_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        self.properties_visible = False
        
        self._setup_properties_panel()
        
        main_layout.addLayout(content_layout)
        
        # === STATUS BAR ===
        status_bar = QFrame()
        status_bar.setFrameStyle(QFrame.Shape.StyledPanel)
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        main_layout.addWidget(status_bar)
        
        # Install event filter for keyboard shortcuts
        self.preview_window.keyPressEvent = self._key_press_event
        
        self.preview_window.show()
    
    def _setup_properties_panel(self):
        """Setup the properties panel"""
        panel_layout = QVBoxLayout(self.properties_panel)
        
        # Title
        title = QLabel("Properties")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        panel_layout.addWidget(title)
        
        # Scrollable area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(0)
        
        self.properties_scroll = QWidget()
        self.properties_scroll_layout = QVBoxLayout(self.properties_scroll)
        self.properties_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.properties_scroll)
        panel_layout.addWidget(scroll_area)
    
    def _toggle_properties(self):
        """Toggle visibility of properties panel"""
        if self.properties_visible:
            self.properties_panel.setVisible(False)
            self.preview_window.layout().itemAt(1).removeWidget(self.properties_panel)
            self.properties_visible = False
        else:
            content_layout = self.preview_window.layout().itemAt(1)
            if hasattr(content_layout, 'addWidget'):
                content_layout.addWidget(self.properties_panel)
            self.properties_panel.setVisible(True)
            self.properties_visible = True
            self._update_properties()
    
    def _update_properties(self):
        """Update properties panel with current image info"""
        # Clear existing widgets
        while self.properties_scroll_layout.count():
            item = self.properties_scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.current_file or not self.current_file.exists():
            return
        
        # File properties
        file_stats = self.current_file.stat()
        file_size = file_stats.st_size
        file_size_str = self._format_file_size(file_size)
        
        properties = {
            "File Name": self.current_file.name,
            "File Path": str(self.current_file.parent),
            "File Size": file_size_str,
            "Format": self.current_file.suffix.upper().replace('.', ''),
        }
        
        # Image properties
        if self.original_image:
            properties.update({
                "Dimensions": f"{self.original_image.width} × {self.original_image.height}",
                "Mode": self.original_image.mode,
                "Aspect Ratio": f"{self.original_image.width / self.original_image.height:.2f}",
            })
            
            # Additional image info if available
            if hasattr(self.original_image, 'info'):
                info = self.original_image.info
                if 'dpi' in info:
                    properties["DPI"] = str(info['dpi'])
        
        # Display properties
        for key, value in properties.items():
            key_label = QLabel(f"{key}:")
            key_label.setStyleSheet("font-weight: bold;")
            self.properties_scroll_layout.addWidget(key_label)
            
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setStyleSheet("margin-left: 10px; margin-bottom: 5px;")
            self.properties_scroll_layout.addWidget(value_label)
    
    def _load_image(self, file_path: Path):
        """Load an image file"""
        try:
            # Clean up old image
            if self.original_image is not None:
                try:
                    self.original_image.close()
                except Exception as e:
                    logger.debug(f"Error closing original_image: {e}")
                self.original_image = None
            
            # Handle DDS files with special support
            if file_path.suffix.lower() == '.dds':
                try:
                    self.original_image = Image.open(file_path)
                    if self.original_image.mode not in ('RGB', 'RGBA'):
                        self.original_image = self.original_image.convert('RGBA')
                except Exception as dds_error:
                    logger.warning(f"DDS direct load failed, trying conversion: {dds_error}")
                    img = Image.open(file_path)
                    self.original_image = img.convert('RGBA')
            else:
                self.original_image = Image.open(file_path)
            
            self.zoom_level = 1.0
            
            self._update_display()
            self._update_status(f"Loaded: {file_path.name}")
            
            if self.properties_visible:
                self._update_properties()
                
        except Exception as e:
            logger.error(f"Failed to load image {file_path}: {e}")
            self._update_status(f"Error loading image: {e}")
    
    def _update_display(self):
        """Update the graphics view with the current image at current zoom"""
        if not self.original_image:
            return
        
        try:
            # Convert PIL Image to QPixmap
            img = self.original_image
            if img.mode == "RGB":
                data = img.tobytes("raw", "RGB")
                qimage = QImage(data, img.width, img.height, QImage.Format.Format_RGB888)
            elif img.mode == "RGBA":
                data = img.tobytes("raw", "RGBA")
                qimage = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
            else:
                img = img.convert("RGBA")
                data = img.tobytes("raw", "RGBA")
                qimage = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
            
            pixmap = QPixmap.fromImage(qimage)
            
            # Clear scene and add pixmap
            self.graphics_scene.clear()
            self.pixmap_item = self.graphics_scene.addPixmap(pixmap)
            
            # Set scene rect to image size
            self.graphics_scene.setSceneRect(QRectF(pixmap.rect()))
            
            # Apply zoom
            self.graphics_view.resetTransform()
            self.graphics_view.scale(self.zoom_level, self.zoom_level)
            
            # Update zoom label
            self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
            self._update_status(f"Error displaying image: {e}")
    
    def _zoom_in(self):
        """Zoom in"""
        self.zoom_level *= 1.2
        if self.zoom_level > 10.0:
            self.zoom_level = 10.0
        self._update_display()
    
    def _zoom_out(self):
        """Zoom out"""
        self.zoom_level /= 1.2
        if self.zoom_level < 0.1:
            self.zoom_level = 0.1
        self._update_display()
    
    def _reset_view(self):
        """Reset zoom and pan to defaults"""
        self.zoom_level = 1.0
        self._update_display()
    
    def _fit_to_window(self):
        """Fit image to window size"""
        if not self.original_image:
            return
        
        # Get view size
        view_width = self.graphics_view.viewport().width()
        view_height = self.graphics_view.viewport().height()
        
        # Calculate zoom level to fit
        zoom_w = view_width / self.original_image.width
        zoom_h = view_height / self.original_image.height
        
        # Use the smaller zoom to fit entirely
        self.zoom_level = min(zoom_w, zoom_h) * 0.95
        self._update_display()
    
    def _actual_size(self):
        """Show image at actual size (1:1)"""
        self.zoom_level = 1.0
        self._update_display()
    
    def _export_image(self):
        """Export current texture to a different format"""
        if not self.current_file or not self.original_image:
            return
        
        try:
            default_name = self.current_file.stem + "_exported.png"
            default_path = str(self.current_file.parent / default_name)
            
            save_path, _ = QFileDialog.getSaveFileName(
                self.preview_window,
                "Export Texture",
                default_path,
                "PNG files (*.png);;JPEG files (*.jpg);;BMP files (*.bmp);;TIFF files (*.tif);;All files (*.*)"
            )
            
            if save_path:
                self.original_image.save(save_path)
                self._update_status(f"Exported to: {Path(save_path).name}")
                logger.info(f"Exported texture to {save_path}")
                
        except Exception as e:
            logger.error(f"Failed to export image: {e}")
            self._update_status(f"Export failed: {e}")
    
    def _graphics_wheel_event(self, event: QWheelEvent):
        """Handle mouse wheel zoom in graphics view"""
        if event.angleDelta().y() > 0:
            self._zoom_in()
        else:
            self._zoom_out()
        event.accept()
    
    def _key_press_event(self, event: QKeyEvent):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Left:
            self._show_previous()
        elif event.key() == Qt.Key.Key_Right:
            self._show_next()
        elif event.key() == Qt.Key.Key_Escape:
            self.preview_window.close()
        else:
            QDialog.keyPressEvent(self.preview_window, event)
    
    def _show_previous(self):
        """Show previous image in the list"""
        if not self.file_list:
            return
        
        self.current_index = (self.current_index - 1) % len(self.file_list)
        self.current_file = self.file_list[self.current_index]
        self._load_image(self.current_file)
        self._update_window_title()
    
    def _show_next(self):
        """Show next image in the list"""
        if not self.file_list:
            return
        
        self.current_index = (self.current_index + 1) % len(self.file_list)
        self.current_file = self.file_list[self.current_index]
        self._load_image(self.current_file)
        self._update_window_title()
    
    def _update_window_title(self):
        """Update window title with current file info"""
        if self.current_file:
            title = f"Preview: {self.current_file.name} ({self.current_index + 1}/{len(self.file_list)})"
            self.preview_window.setWindowTitle(title)
    
    def _update_status(self, message: str):
        """Update status bar message"""
        if self.status_label:
            self.status_label.setText(message)
    
    def _get_sibling_textures(self, file_path: Path) -> List[Path]:
        """Get all texture files in the same directory"""
        if not file_path.exists():
            return [file_path]
        
        parent_dir = file_path.parent
        texture_extensions = {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga'}
        
        textures = []
        try:
            for item in parent_dir.iterdir():
                if item.is_file() and item.suffix.lower() in texture_extensions:
                    textures.append(item)
        except Exception as e:
            logger.warning(f"Failed to list sibling textures: {e}")
            return [file_path]
        
        # Sort by name
        textures.sort(key=lambda x: x.name.lower())
        
        return textures if textures else [file_path]
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def close(self):
        """Close the preview window"""
        if self.preview_window and self.preview_window.isVisible():
            self.preview_window.close()