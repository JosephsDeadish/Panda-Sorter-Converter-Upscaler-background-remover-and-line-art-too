"""
File Browser Panel - Browse and preview texture files
Provides comprehensive file browsing with thumbnails, filtering, and preview
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import List, Optional, Set
import json

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QComboBox, QListWidget, QListWidgetItem,
        QFileDialog, QMessageBox, QGroupBox, QCheckBox,
        QScrollArea, QFrame, QGridLayout, QSplitter
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QThread
    from PyQt6.QtGui import QPixmap, QIcon, QImage
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QWidget = object

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available - thumbnails disabled")


class ThumbnailGenerator(QThread):
    """Background thread for generating thumbnails"""
    thumbnail_ready = pyqtSignal(str, QPixmap)  # filepath, pixmap
    
    def __init__(self, files: List[Path], size: int = 128):
        super().__init__()
        self.files = files
        self.size = size
        self._stopped = False
    
    def stop(self):
        """Stop thumbnail generation"""
        self._stopped = True
    
    def run(self):
        """Generate thumbnails"""
        for filepath in self.files:
            if self._stopped:
                break
            
            try:
                if not PIL_AVAILABLE:
                    continue
                    
                # Load and resize image
                img = Image.open(filepath)
                img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
                
                # Convert to QPixmap
                if img.mode == 'RGBA':
                    data = img.tobytes("raw", "RGBA")
                    qimage = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
                elif img.mode == 'RGB':
                    data = img.tobytes("raw", "RGB")
                    qimage = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGB888)
                else:
                    # Convert to RGB for other modes
                    img = img.convert('RGB')
                    data = img.tobytes("raw", "RGB")
                    qimage = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGB888)
                
                pixmap = QPixmap.fromImage(qimage)
                self.thumbnail_ready.emit(str(filepath), pixmap)
                
            except Exception as e:
                logger.debug(f"Failed to generate thumbnail for {filepath}: {e}")
                continue


class FileBrowserPanelQt(QWidget):
    """
    File Browser Panel - Browse textures with thumbnails
    
    Features:
    - Thumbnail view of images
    - File filtering by type
    - Search/filter by name
    - Preview large image
    - Archive file support
    - Recent folders
    """
    
    # Supported file types
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.dds', '.tga'}
    ARCHIVE_EXTENSIONS = {'.zip', '.7z', '.rar', '.tar', '.gz'}
    
    file_selected = pyqtSignal(Path)
    folder_changed = pyqtSignal(Path)
    
    def __init__(self, config=None, tooltip_manager=None, parent=None):
        super().__init__(parent)
        
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 is required for FileBrowserPanelQt")
        
        self.config = config
        self.tooltip_manager = tooltip_manager
        self.current_folder: Optional[Path] = None
        self.current_files: List[Path] = []
        self.thumbnail_cache: dict = {}
        self.thumbnail_generator: Optional[ThumbnailGenerator] = None
        
        # Load recent folders
        self.config_dir = Path.home() / '.ps2_texture_sorter'
        self.config_dir.mkdir(exist_ok=True)
        self.recent_folders_path = self.config_dir / 'recent_folders.json'
        self.recent_folders: List[str] = []
        self.load_recent_folders()
        
        self.setup_ui()
    
    def _set_tooltip(self, widget, tooltip_id: str):
        """Helper to set tooltip from manager"""
        if self.tooltip_manager:
            self.tooltip_manager.set_tooltip(widget, tooltip_id)
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("📁 File Browser")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # === TOP CONTROLS ===
        controls_layout = QHBoxLayout()
        
        # Browse button
        self.browse_btn = QPushButton("📂 Browse Folder")
        self.browse_btn.clicked.connect(self.browse_folder)
        self._set_tooltip(self.browse_btn, 'browse_folder_button')
        controls_layout.addWidget(self.browse_btn)
        
        # Recent folders dropdown
        self.recent_combo = QComboBox()
        self.recent_combo.setMinimumWidth(300)
        self.recent_combo.addItem("-- Recent Folders --")
        for folder in self.recent_folders:
            self.recent_combo.addItem(folder)
        self.recent_combo.currentTextChanged.connect(self.on_recent_folder_selected)
        self._set_tooltip(self.recent_combo, 'recent_folders_combo')
        controls_layout.addWidget(self.recent_combo)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_view)
        self.refresh_btn.setEnabled(False)
        self._set_tooltip(self.refresh_btn, 'refresh_browser_button')
        controls_layout.addWidget(self.refresh_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # === FILTER CONTROLS ===
        filter_layout = QHBoxLayout()
        
        # Search box
        search_label = QLabel("🔍 Search:")
        filter_layout.addWidget(search_label)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter by filename...")
        self.search_box.textChanged.connect(self.filter_files)
        self._set_tooltip(self.search_box, 'file_search_box')
        filter_layout.addWidget(self.search_box)
        
        # File type filter
        type_label = QLabel("Type:")
        filter_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "All Files",
            "Images Only",
            "Archives Only"
        ])
        self.type_combo.currentTextChanged.connect(self.filter_files)
        self._set_tooltip(self.type_combo, 'file_type_filter')
        filter_layout.addWidget(self.type_combo)
        
        # Show archives checkbox
        self.show_archives_cb = QCheckBox("📦 Include Archives")
        self.show_archives_cb.setChecked(True)
        self.show_archives_cb.stateChanged.connect(self.filter_files)
        self._set_tooltip(self.show_archives_cb, 'show_archives_checkbox')
        filter_layout.addWidget(self.show_archives_cb)
        
        layout.addLayout(filter_layout)
        
        # === SPLITTER FOR FILE LIST AND PREVIEW ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === FILE LIST (LEFT) ===
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # File count label
        self.file_count_label = QLabel("No folder selected")
        self.file_count_label.setStyleSheet("font-weight: bold; color: #666;")
        list_layout.addWidget(self.file_count_label)
        
        # File list with thumbnails
        self.file_list = QListWidget()
        self.file_list.setIconSize(QSize(96, 96))
        self.file_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.file_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.file_list.setSpacing(10)
        self.file_list.setWordWrap(True)
        self.file_list.itemClicked.connect(self.on_file_clicked)
        self.file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        list_layout.addWidget(self.file_list)
        
        splitter.addWidget(list_container)
        
        # === PREVIEW PANEL (RIGHT) ===
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        preview_layout.addWidget(preview_label)
        
        # Scroll area for large preview
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.Box)
        
        self.preview_label = QLabel("No file selected")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; padding: 20px;")
        self.preview_label.setScaledContents(False)
        scroll.setWidget(self.preview_label)
        
        preview_layout.addWidget(scroll)
        
        # File info
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("background-color: #ffffff; padding: 10px; border: 1px solid #ccc;")
        preview_layout.addWidget(self.info_label)
        
        splitter.addWidget(preview_container)
        splitter.setStretchFactor(0, 2)  # File list gets more space
        splitter.setStretchFactor(1, 1)  # Preview gets less
        
        layout.addWidget(splitter)
        
        # === BOTTOM STATUS ===
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
    
    def browse_folder(self):
        """Browse for a folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Browse",
            str(self.current_folder) if self.current_folder else str(Path.home())
        )
        
        if folder:
            self.load_folder(Path(folder))
    
    def load_folder(self, folder: Path):
        """Load files from a folder"""
        if not folder.exists():
            QMessageBox.warning(self, "Error", f"Folder does not exist:\n{folder}")
            return
        
        self.current_folder = folder
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Loading folder: {folder.name}...")
        
        # Add to recent folders
        folder_str = str(folder)
        if folder_str not in self.recent_folders:
            self.recent_folders.insert(0, folder_str)
            self.recent_folders = self.recent_folders[:10]  # Keep last 10
            self.save_recent_folders()
            self.update_recent_combo()
        
        # Scan for files
        try:
            all_files = []
            for ext in self.IMAGE_EXTENSIONS:
                all_files.extend(folder.glob(f"*{ext}"))
                all_files.extend(folder.glob(f"*{ext.upper()}"))
            
            if self.show_archives_cb.isChecked():
                for ext in self.ARCHIVE_EXTENSIONS:
                    all_files.extend(folder.glob(f"*{ext}"))
                    all_files.extend(folder.glob(f"*{ext.upper()}"))
            
            self.current_files = sorted(all_files, key=lambda p: p.name.lower())
            self.filter_files()
            
            self.status_label.setText(f"Loaded {len(self.current_files)} files from {folder.name}")
            self.folder_changed.emit(folder)
            
        except Exception as e:
            logger.error(f"Error loading folder: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to load folder:\n{e}")
            self.status_label.setText("Error loading folder")
    
    def filter_files(self):
        """Filter files based on search and type"""
        if not self.current_files:
            return
        
        search_text = self.search_box.text().lower()
        type_filter = self.type_combo.currentText()
        show_archives = self.show_archives_cb.isChecked()
        
        filtered = []
        for filepath in self.current_files:
            # Type filter
            if type_filter == "Images Only" and filepath.suffix.lower() in self.ARCHIVE_EXTENSIONS:
                continue
            if type_filter == "Archives Only" and filepath.suffix.lower() in self.IMAGE_EXTENSIONS:
                continue
            
            # Archive filter
            if not show_archives and filepath.suffix.lower() in self.ARCHIVE_EXTENSIONS:
                continue
            
            # Search filter
            if search_text and search_text not in filepath.name.lower():
                continue
            
            filtered.append(filepath)
        
        self.display_files(filtered)
    
    def display_files(self, files: List[Path]):
        """Display files in the list"""
        self.file_list.clear()
        self.thumbnail_cache.clear()
        
        # Stop any running thumbnail generator
        if self.thumbnail_generator and self.thumbnail_generator.isRunning():
            self.thumbnail_generator.stop()
            self.thumbnail_generator.wait()
        
        self.file_count_label.setText(f"📄 {len(files)} files")
        
        if not files:
            return
        
        # Add items to list
        for filepath in files:
            item = QListWidgetItem()
            item.setText(filepath.name)
            item.setData(Qt.ItemDataRole.UserRole, str(filepath))
            
            # Set icon based on file type
            if filepath.suffix.lower() in self.ARCHIVE_EXTENSIONS:
                item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogContentsView))
            else:
                # Placeholder icon, will be replaced by thumbnail
                item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
            
            self.file_list.addItem(item)
        
        # Generate thumbnails in background
        image_files = [f for f in files if f.suffix.lower() in self.IMAGE_EXTENSIONS]
        if image_files and PIL_AVAILABLE:
            self.thumbnail_generator = ThumbnailGenerator(image_files, size=96)
            self.thumbnail_generator.thumbnail_ready.connect(self.on_thumbnail_ready)
            self.thumbnail_generator.start()
    
    def on_thumbnail_ready(self, filepath: str, pixmap: QPixmap):
        """Handle thumbnail generated"""
        self.thumbnail_cache[filepath] = pixmap
        
        # Find item and update icon
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == filepath:
                item.setIcon(QIcon(pixmap))
                break
    
    def on_file_clicked(self, item: QListWidgetItem):
        """Handle file clicked"""
        filepath = Path(item.data(Qt.ItemDataRole.UserRole))
        self.show_preview(filepath)
        self.file_selected.emit(filepath)
    
    def on_file_double_clicked(self, item: QListWidgetItem):
        """Handle file double-clicked"""
        filepath = Path(item.data(Qt.ItemDataRole.UserRole))
        # Open file with default application
        import subprocess
        import platform
        import os
        
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', str(filepath)))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(str(filepath))
            else:  # linux variants
                subprocess.call(('xdg-open', str(filepath)))
        except Exception as e:
            logger.error(f"Error opening file: {e}")
    
    def show_preview(self, filepath: Path):
        """Show preview of selected file"""
        try:
            if filepath.suffix.lower() in self.ARCHIVE_EXTENSIONS:
                # Show archive info
                self.preview_label.setText(f"📦 Archive File\n\n{filepath.name}")
                size_mb = filepath.stat().st_size / (1024 * 1024)
                self.info_label.setText(f"<b>File:</b> {filepath.name}<br>"
                                      f"<b>Type:</b> Archive ({filepath.suffix})<br>"
                                      f"<b>Size:</b> {size_mb:.2f} MB")
            else:
                # Show image preview
                if PIL_AVAILABLE:
                    img = Image.open(filepath)
                    
                    # Create larger preview (max 512x512)
                    img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                    
                    # Convert to QPixmap
                    if img.mode == 'RGBA':
                        data = img.tobytes("raw", "RGBA")
                        qimage = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGBA8888)
                    elif img.mode == 'RGB':
                        data = img.tobytes("raw", "RGB")
                        qimage = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGB888)
                    else:
                        img = img.convert('RGB')
                        data = img.tobytes("raw", "RGB")
                        qimage = QImage(data, img.size[0], img.size[1], QImage.Format.Format_RGB888)
                    
                    pixmap = QPixmap.fromImage(qimage)
                    self.preview_label.setPixmap(pixmap)
                    
                    # Show file info
                    size_mb = filepath.stat().st_size / (1024 * 1024)
                    original_img = Image.open(filepath)
                    self.info_label.setText(
                        f"<b>File:</b> {filepath.name}<br>"
                        f"<b>Size:</b> {original_img.size[0]} x {original_img.size[1]}<br>"
                        f"<b>Format:</b> {original_img.format}<br>"
                        f"<b>Mode:</b> {original_img.mode}<br>"
                        f"<b>File Size:</b> {size_mb:.2f} MB"
                    )
                else:
                    self.preview_label.setText("PIL not available\nCannot show preview")
                    
        except Exception as e:
            logger.error(f"Error showing preview: {e}", exc_info=True)
            self.preview_label.setText(f"Error loading preview:\n{e}")
    
    def refresh_view(self):
        """Refresh the current folder"""
        if self.current_folder:
            self.load_folder(self.current_folder)
    
    def on_recent_folder_selected(self, text: str):
        """Handle recent folder selection"""
        if text and text != "-- Recent Folders --":
            folder = Path(text)
            if folder.exists():
                self.load_folder(folder)
            else:
                QMessageBox.warning(self, "Error", f"Folder no longer exists:\n{text}")
    
    def load_recent_folders(self):
        """Load recent folders from file"""
        try:
            if self.recent_folders_path.exists():
                with open(self.recent_folders_path, 'r') as f:
                    self.recent_folders = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load recent folders: {e}")
            self.recent_folders = []
    
    def save_recent_folders(self):
        """Save recent folders to file"""
        try:
            with open(self.recent_folders_path, 'w') as f:
                json.dump(self.recent_folders, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save recent folders: {e}")
    
    def update_recent_combo(self):
        """Update recent folders combo box"""
        self.recent_combo.clear()
        self.recent_combo.addItem("-- Recent Folders --")
        for folder in self.recent_folders:
            self.recent_combo.addItem(folder)
