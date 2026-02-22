"""Universal File Picker Widget - Used by all tools"""
from __future__ import annotations

from pathlib import Path
import json
import logging
from typing import List, Optional, Callable, Tuple

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
        QFileDialog, QListWidget, QListWidgetItem, QCheckBox,
        QFrame, QProgressBar, QMessageBox, QScrollArea, QMenu,
        QTabWidget
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QSize, QMimeData, QUrl
    from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    class QWidget: pass  # noqa: E701
    class QFrame: pass  # noqa: E701
    class QThread: pass  # noqa: E701
    class _SignalStub:  # noqa: E301
        """Stub signal — active only when PyQt6 is absent."""
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SignalStub()  # noqa: E301
    class Qt:  # noqa: E301
        AlignCenter = 0; AlignLeft = 0; AlignRight = 0
    class QTimer: pass  # noqa: E701
    class QSize: pass  # noqa: E701
    class QIcon: pass  # noqa: E701
    class QPixmap: pass  # noqa: E701
    class QFont: pass  # noqa: E701
    class QColor: pass  # noqa: E701

logger = logging.getLogger(__name__)

class FilePickerWidget(QWidget):
    """
    Universal File Picker Widget
    
    Used by all tools for selecting files/folders/archives
    Supports single/multi-selection, drag & drop, and recent files
    
    Signals:
        files_selected(list[Path]) - Emitted when files are selected
        folder_selected(Path) - Emitted when folder is selected
        archive_selected(Path) - Emitted when archive is selected
    """
    
    files_selected = pyqtSignal(list)  # List[Path]
    folder_selected = pyqtSignal(Path)
    archive_selected = pyqtSignal(Path)
    
    # Supported file types
    IMAGE_FORMATS = ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp', '*.tiff', '*.tif')
    ARCHIVE_FORMATS = ('*.zip', '*.7z', '*.rar', '*.tar', '*.tar.gz')
    ALL_FORMATS = IMAGE_FORMATS + ARCHIVE_FORMATS
    
    def __init__(
        self,
        file_types: Tuple[str, ...] = IMAGE_FORMATS,
        allow_multiple: bool = False,
        allow_folders: bool = False,
        allow_archives: bool = False,
        parent=None
    ):
        """
        Initialize File Picker
        
        Args:
            file_types: Tuple of allowed file extensions (e.g., ('*.png', '*.jpg'))
            allow_multiple: Enable multi-file selection with checkboxes
            allow_folders: Allow folder selection
            allow_archives: Allow archive file selection
        """
        super().__init__(parent)
        self.file_types = file_types
        self.allow_multiple = allow_multiple
        self.allow_folders = allow_folders
        self.allow_archives = allow_archives
        self.config_dir = Path.home() / '.ps2_texture_sorter'
        self.config_dir.mkdir(exist_ok=True)
        self.recent_files_path = self.config_dir / 'recent_files.json'
        
        self.selected_files: List[Path] = []
        self.setup_ui()
        self.load_recent_files()
    
    def setup_ui(self):
        """Create the widget UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # ===== BUTTON ROW =====
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Browse button
        self.browse_btn = QPushButton("📁 Browse Files")
        self.browse_btn.setMinimumHeight(40)
        self.browse_btn.setMinimumWidth(150)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.browse_btn.clicked.connect(self.on_browse)
        button_layout.addWidget(self.browse_btn)
        
        # Browse folder button (conditional)
        if self.allow_folders:
            self.browse_folder_btn = QPushButton("📂 Browse Folder")
            self.browse_folder_btn.setMinimumHeight(40)
            self.browse_folder_btn.setMinimumWidth(150)
            self.browse_folder_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            self.browse_folder_btn.clicked.connect(self.on_browse_folder)
            button_layout.addWidget(self.browse_folder_btn)
        
        # Browse archive button (conditional)
        if self.allow_archives:
            self.browse_archive_btn = QPushButton("📦 Browse Archive")
            self.browse_archive_btn.setMinimumHeight(40)
            self.browse_archive_btn.setMinimumWidth(150)
            self.browse_archive_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
                QPushButton:pressed {
                    background-color: #E65100;
                }
            """)
            self.browse_archive_btn.clicked.connect(self.on_browse_archive)
            button_layout.addWidget(self.browse_archive_btn)
        
        # Recent files button
        self.recent_btn = QPushButton("⏱️  Recent")
        self.recent_btn.setMinimumHeight(40)
        self.recent_btn.setMinimumWidth(100)
        self.recent_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
        """)
        self.recent_btn.clicked.connect(self.show_recent_menu)
        button_layout.addWidget(self.recent_btn)
        
        # Clear selection button
        self.clear_btn = QPushButton("✕ Clear")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.setMinimumWidth(100)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c9000a;
            }
        """)
        self.clear_btn.clicked.connect(self.on_clear)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # ===== FILE LIST / DISPLAY =====
        if self.allow_multiple:
            # Multi-select with checkboxes
            self.file_list = QListWidget()
            self.file_list.setMinimumHeight(150)
            self.file_list.setStyleSheet("""
                QListWidget {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #fafafa;
                }
                QListWidget::item:hover {
                    background-color: #e3f2fd;
                }
            """)
            layout.addWidget(self.file_list)
        else:
            # Single file display
            self.file_label = QLabel("No files selected")
            self.file_label.setStyleSheet("""
                QLabel {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 12px;
                    background-color: #fafafa;
                    color: #999;
                }
            """)
            layout.addWidget(self.file_label)
        
        # ===== INFO LABEL =====
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
        self.setAcceptDrops(True)
        
        # Update info
        self.update_info()
    
    def on_browse(self):
        """Browse for files"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(
            QFileDialog.FileMode.ExistingFiles if self.allow_multiple
            else QFileDialog.FileMode.ExistingFile
        )
        file_dialog.setNameFilter(self.get_filter_string())
        file_dialog.setDirectory(str(Path.home() / 'Desktop'))
        
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            files = [Path(f) for f in file_dialog.selectedFiles()]
            if files:
                self.set_files(files)
                self.add_to_recent(files[0])
    
    def on_browse_folder(self):
        """Browse for folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            str(Path.home() / 'Desktop')
        )
        if folder:
            folder_path = Path(folder)
            self.selected_files = [folder_path]
            self.update_display()
            self.folder_selected.emit(folder_path)
            self.add_to_recent(folder_path)
    
    def on_browse_archive(self):
        """Browse for archive"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter(self.get_archive_filter_string())
        file_dialog.setDirectory(str(Path.home() / 'Desktop'))
        
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            files = file_dialog.selectedFiles()
            if files:
                archive_path = Path(files[0])
                self.selected_files = [archive_path]
                self.update_display()
                self.archive_selected.emit(archive_path)
                self.add_to_recent(archive_path)
    
    def on_clear(self):
        """Clear selection"""
        self.selected_files = []
        self.update_display()
    
    def set_files(self, files: List[Path]):
        """Set selected files"""
        self.selected_files = files
        self.update_display()
        self.files_selected.emit(files)
    
    def update_display(self):
        """Update UI to show selected files"""
        if self.allow_multiple:
            self.file_list.clear()
            for file_path in self.selected_files:
                item = QListWidgetItem()
                item.setText(f"  {file_path.name}")
                item.setCheckState(Qt.CheckState.Checked)
                self.file_list.addItem(item)
        else:
            if self.selected_files:
                file_path = self.selected_files[0]
                self.file_label.setText(f"📄 {file_path.name}\n{str(file_path)}")
                self.file_label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #4CAF50;
                        border-radius: 4px;
                        padding: 12px;
                        background-color: #f1f8e9;
                        color: #33691e;
                        font-weight: bold;
                    }
                """)
            else:
                self.file_label.setText("No files selected")
                self.file_label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        padding: 12px;
                        background-color: #fafafa;
                        color: #999;
                    }
                """)
        
        self.update_info()
    
    def update_info(self):
        """Update info label"""
        if self.selected_files:
            count = len(self.selected_files)
            self.info_label.setText(f"✅ {count} file(s) selected")
        else:
            self.info_label.setText("ℹ️  Click Browse to select files")
    
    def add_to_recent(self, file_path: Path):
        """Add file to recent files"""
        try:
            recent = self.load_recent_files_list()
            recent_paths = [Path(p) for p in recent]
            
            # Remove if already exists
            recent_paths = [p for p in recent_paths if p != file_path]
            
            # Add to front
            recent_paths.insert(0, file_path)
            
            # Keep last 10
            recent_paths = recent_paths[:10]
            
            # Save
            with open(self.recent_files_path, 'w') as f:
                json.dump([str(p) for p in recent_paths], f)
        except Exception as e:
            logger.error(f"Failed to save recent files: {e}")
    
    def load_recent_files(self):
        """Load recent files from cache"""
        self.recent_files = self.load_recent_files_list()
    
    def load_recent_files_list(self) -> List[Path]:
        """Load recent files list"""
        try:
            if self.recent_files_path.exists():
                with open(self.recent_files_path, 'r') as f:
                    return [Path(p) for p in json.load(f)]
        except Exception as e:
            logger.error(f"Failed to load recent files: {e}")
        return []
    
    def show_recent_menu(self):
        """Show recent files menu"""
        menu = QMenu(self)
        
        recent = self.load_recent_files_list()
        if recent:
            for file_path in recent:
                if file_path.exists():
                    action = menu.addAction(f"  {file_path.name}")
                    action.triggered.connect(
                        lambda checked, p=file_path: self.set_files([p])
                    )
            menu.addSeparator()
        
        menu.addAction("🗑️  Clear History").triggered.connect(self.on_clear_recent)
        
        # Show menu at button position
        pos = self.recent_btn.mapToGlobal(self.recent_btn.rect().bottomLeft())
        menu.exec(pos)
    
    def on_clear_recent(self):
        """Clear recent files history"""
        try:
            if self.recent_files_path.exists():
                self.recent_files_path.unlink()
            self.recent_files = []
        except Exception as e:
            logger.error(f"Failed to clear recent files: {e}")
    
    def get_filter_string(self) -> str:
        """Get file filter string for dialog"""
        types = " ".join(self.file_types)
        return f"Image Files ({types});;All Files (*)"
    
    def get_archive_filter_string(self) -> str:
        """Get archive filter string"""
        types = " ".join(self.ARCHIVE_FORMATS)
        return f"Archive Files ({types});;All Files (*)"
    
    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event - drag & drop files"""
        files = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        valid_files = [f for f in files if self.is_valid_file(f)]
        
        if valid_files:
            self.set_files(valid_files)
            self.add_to_recent(valid_files[0])
    
    def is_valid_file(self, file_path: Path) -> bool:
        """Check if file matches allowed types"""
        suffix = file_path.suffix.lower()
        return any(
            suffix == ext.replace('*', '')
            for ext in self.file_types
        )
    
    def get_selected_files(self) -> List[Path]:
        """Get currently selected files"""
        return self.selected_files.copy()
    
    def get_selected_file(self) -> Optional[Path]:
        """Get single selected file (first)"""
        return self.selected_files[0] if self.selected_files else None
