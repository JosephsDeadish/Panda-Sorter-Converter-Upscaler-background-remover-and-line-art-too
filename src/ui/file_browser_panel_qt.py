"""
File Browser Panel - Browse and preview texture files
Provides comprehensive file browsing with thumbnails, filtering, and preview
Author: Dead On The Inside / JosephsDeadish
"""


from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Optional, Set
import json

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QComboBox, QListWidget, QListWidgetItem,
        QFileDialog, QMessageBox, QGroupBox, QCheckBox,
        QScrollArea, QFrame, QGridLayout, QSplitter, QMainWindow
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QThread
    from PyQt6.QtGui import QPixmap, QIcon, QImage
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    class QObject:  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class QWidget(QObject):  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class QMainWindow(QWidget):  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class QThread(QObject):  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class QPixmap:  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class _SignalStub:  # noqa: E301
        """Stub signal — active only when PyQt6 is absent."""
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SignalStub()  # noqa: E301

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PIL_AVAILABLE = False
    logger.warning("PIL not available - thumbnails disabled")

try:
    from features.search_filter import SearchFilter, FilterCriteria
    _SEARCH_FILTER = SearchFilter()
except Exception:
    _SEARCH_FILTER = None  # type: ignore[assignment]



class ThumbnailGenerator(QThread):
    """Background thread for generating thumbnails"""
    thumbnail_ready = pyqtSignal(str, QImage)  # filepath, qimage (QPixmap must be created in main thread)

    def __init__(self, files: List[Path], size: int = 128):
        super().__init__()
        self.files = files
        self.size = size
        self._stopped = False

    def stop(self):
        """Stop thumbnail generation"""
        self._stopped = True

    def run(self):
        """Generate thumbnails (produce QImage — caller converts to QPixmap in main thread)."""
        for filepath in self.files:
            if self._stopped:
                break

            try:
                if not PIL_AVAILABLE:
                    continue

                # Load and resize image
                img = Image.open(filepath)
                img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)

                # Convert to QImage (safe to create in any thread; QPixmap is GUI-only)
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

                # QImage.copy() ensures the underlying buffer outlives the local `data` bytes
                self.thumbnail_ready.emit(str(filepath), qimage.copy())

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
    IMAGE_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp',
        '.dds', '.tga', '.gif', '.avif', '.qoi', '.apng', '.jfif',
        '.ico', '.icns',
    }
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
        # Track floating pop-out windows so they aren't garbage collected
        self._popout_windows: list = []
        
        # Load recent folders
        try:
            from config import get_data_dir as _gdd
            self.config_dir = _gdd()
        except (ImportError, Exception):
            try:
                from src.config import get_data_dir as _gdd
                self.config_dir = _gdd()
            except (ImportError, Exception):
                self.config_dir = Path.home() / '.ps2_texture_sorter'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.recent_folders_path = self.config_dir / 'recent_folders.json'
        self.recent_folders: List[str] = []
        self.load_recent_folders()
        
        self.setup_ui()
    
    def _set_tooltip(self, widget, widget_id_or_text: str):
        """Set tooltip via manager (cycling) when available, else plain text."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'register'):
            if ' ' not in widget_id_or_text:
                try:
                    tip = self.tooltip_manager.get_tooltip(widget_id_or_text)
                    if tip:
                        widget.setToolTip(tip)
                        self.tooltip_manager.register(widget, widget_id_or_text)
                        return
                except Exception:
                    pass
        widget.setToolTip(str(widget_id_or_text))
    
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
        self._set_tooltip(self.browse_btn, 'browser_browse_button')
        controls_layout.addWidget(self.browse_btn)
        
        # Recent folders dropdown
        self.recent_combo = QComboBox()
        self.recent_combo.setMinimumWidth(300)
        self.recent_combo.addItem("-- Recent Folders --")
        for folder in self.recent_folders:
            self.recent_combo.addItem(folder)
        self.recent_combo.currentTextChanged.connect(self.on_recent_folder_selected)
        self._set_tooltip(self.recent_combo, 'recent_folders_combo')
        self._set_tooltip(self.recent_combo, 'recent_files')
        controls_layout.addWidget(self.recent_combo)

        # Clear recent folders button
        self._clear_recent_btn = QPushButton("✖")
        self._clear_recent_btn.setFixedWidth(28)
        self._clear_recent_btn.setFixedHeight(24)
        self._clear_recent_btn.clicked.connect(self._clear_recent_folders)
        self._set_tooltip(self._clear_recent_btn, "Clear recent folders history")
        controls_layout.addWidget(self._clear_recent_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_view)
        self.refresh_btn.setEnabled(False)
        self._set_tooltip(self.refresh_btn, 'browser_refresh_button')
        controls_layout.addWidget(self.refresh_btn)

        # Pop-out button — opens this browser in a standalone floating window
        self.popout_btn = QPushButton("⎊ Pop Out")
        self.popout_btn.clicked.connect(self._popout_to_window)
        self._set_tooltip(self.popout_btn, 'popout_button')
        controls_layout.addWidget(self.popout_btn)

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
        self._set_tooltip(self.search_box, 'browser_search')
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
        self._set_tooltip(self.show_archives_cb, 'browser_show_archives')
        filter_layout.addWidget(self.show_archives_cb)

        # Favorites filter button — shows only files bookmarked as favorites
        self.favorites_btn = QPushButton("⭐ Favorites")
        self.favorites_btn.setCheckable(True)
        self.favorites_btn.setChecked(False)
        self.favorites_btn.toggled.connect(self._on_favorites_toggled)
        self._set_tooltip(self.favorites_btn, 'favorites_button')
        filter_layout.addWidget(self.favorites_btn)

        layout.addLayout(filter_layout)

        # === IMAGE CONTENT SEARCH ===
        content_search_layout = QHBoxLayout()
        content_search_label = QLabel("🖼 Content Search:")
        self._set_tooltip(content_search_label, "Search images by what they contain (requires CLIP/transformers)")
        content_search_layout.addWidget(content_search_label)

        self.content_search_box = QLineEdit()
        self.content_search_box.setPlaceholderText("Describe image content, e.g. 'panda eating bamboo'...")
        self._set_tooltip(
            self.content_search_box,
            "Search images by visual content using CLIP AI. Requires: pip install transformers open-clip-torch torch"
        )
        content_search_layout.addWidget(self.content_search_box)

        self.content_search_btn = QPushButton("🔎 Search Content")
        self._set_tooltip(
            self.content_search_btn,
            'browser_smart_search'
        )
        self.content_search_btn.clicked.connect(self._search_by_content)
        content_search_layout.addWidget(self.content_search_btn)

        self.content_search_status = QLabel("")
        self.content_search_status.setStyleSheet("color: #888; font-size: 10px;")
        content_search_layout.addWidget(self.content_search_status)

        layout.addLayout(content_search_layout)
        
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
        """Filter files based on search and type, using SearchFilter when available."""
        if not self.current_files:
            return

        search_text = self.search_box.text().lower()
        type_filter = self.type_combo.currentText()
        show_archives = self.show_archives_cb.isChecked()

        # Apply type / archive pre-filter first (fast, no SearchFilter needed)
        candidates = []
        for filepath in self.current_files:
            if type_filter == "Images Only" and filepath.suffix.lower() in self.ARCHIVE_EXTENSIONS:
                continue
            if type_filter == "Archives Only" and filepath.suffix.lower() in self.IMAGE_EXTENSIONS:
                continue
            if not show_archives and filepath.suffix.lower() in self.ARCHIVE_EXTENSIONS:
                continue
            candidates.append(filepath)

        # Use SearchFilter for text search when available; fall back to plain substring
        if search_text:
            if _SEARCH_FILTER is not None:
                try:
                    criteria = FilterCriteria(name=search_text)
                    filtered = _SEARCH_FILTER.search(candidates, criteria)
                except Exception:
                    # Fallback to simple substring match on any error
                    filtered = [p for p in candidates if search_text in p.name.lower()]
            else:
                filtered = [p for p in candidates if search_text in p.name.lower()]
        else:
            filtered = candidates

        # Apply favorites filter when the button is active
        if hasattr(self, 'favorites_btn') and self.favorites_btn.isChecked():
            if _SEARCH_FILTER is not None:
                try:
                    filtered = _SEARCH_FILTER.quick_filter_favorites(filtered)
                except Exception:
                    pass

        self.display_files(filtered)

    def _on_favorites_toggled(self, checked: bool):
        """Handle Favorites filter toggle — re-run the filter with/without favorites."""
        self.favorites_btn.setStyleSheet(
            "background: #FFC107; color: black; font-weight: bold;" if checked else ""
        )
        self.filter_files()

    def _popout_to_window(self):
        """Open this file browser panel in its own floating window.

        Multiple pop-out windows are supported; references are kept in
        `_popout_windows` to prevent garbage collection.
        """
        try:
            win = QMainWindow(None)
            win.setWindowTitle("📂 File Browser — Floating")
            win.resize(900, 600)
            # Create a standalone browser instance sharing config / tooltip_manager
            clone = FileBrowserPanelQt(
                config=self.config,
                tooltip_manager=self.tooltip_manager,
                parent=win,
            )
            if self.current_folder:
                clone.load_folder(self.current_folder)
            win.setCentralWidget(clone)
            # Clean up the reference when the window is closed
            win.destroyed.connect(lambda: self._popout_windows.remove(win) if win in self._popout_windows else None)
            self._popout_windows.append(win)
            win.show()
        except Exception as e:
            logger.warning(f"Pop-out window failed: {e}")

    def _search_by_content(self):
        """Search displayed images by visual content description using CLIP."""
        query = self.content_search_box.text().strip()
        if not query:
            self.content_search_status.setText("Enter a description first.")
            return

        # Only search image files currently shown
        image_files = [
            p for p in self.current_files
            if p.suffix.lower() in self.IMAGE_EXTENSIONS
        ]
        if not image_files:
            self.content_search_status.setText("No images loaded. Browse a folder first.")
            return

        # Try CLIP-based content search
        try:
            import torch
            try:
                import open_clip
                _clip_backend = "open_clip"
            except ImportError:
                open_clip = None
                _clip_backend = None

            try:
                from transformers import CLIPProcessor, CLIPModel
                _hf_available = True
            except ImportError:
                _hf_available = False

            if not _clip_backend and not _hf_available:
                raise ImportError("Neither open-clip-torch nor transformers is installed")

            def _process_events():
                try:
                    from PyQt6.QtWidgets import QApplication as _QApp
                    _QApp.processEvents()
                except Exception:
                    pass

            self.content_search_status.setText("⏳ Loading CLIP model…")
            _process_events()

            from PIL import Image as _PILImage

            if _clip_backend == "open_clip":
                model, _, preprocess = open_clip.create_model_and_transforms(
                    'ViT-B-32', pretrained='openai'
                )
                tokenizer = open_clip.get_tokenizer('ViT-B-32')
                model.eval()

                text_tokens = tokenizer([query])
                with torch.no_grad():
                    text_features = model.encode_text(text_tokens)
                    text_features /= text_features.norm(dim=-1, keepdim=True)

                scores: list = []
                self.content_search_status.setText("⏳ Scoring images…")
                _process_events()
                for fp in image_files:
                    try:
                        img = preprocess(_PILImage.open(fp).convert("RGB")).unsqueeze(0)
                        with torch.no_grad():
                            img_feat = model.encode_image(img)
                            img_feat /= img_feat.norm(dim=-1, keepdim=True)
                        score = (img_feat @ text_features.T).item()
                        scores.append((score, fp))
                    except Exception:
                        pass
            else:
                processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                model.eval()

                scores = []
                self.content_search_status.setText("⏳ Scoring images…")
                _process_events()
                for fp in image_files:
                    try:
                        img = _PILImage.open(fp).convert("RGB")
                        inputs = processor(text=[query], images=img, return_tensors="pt", padding=True)
                        with torch.no_grad():
                            outputs = model(**inputs)
                        score = outputs.logits_per_image.item()
                        scores.append((score, fp))
                    except Exception:
                        pass

            if not scores:
                self.content_search_status.setText("No images could be scored.")
                return

            _MAX_RESULTS = 50
            scores.sort(reverse=True)
            top_files = [fp for _, fp in scores[:_MAX_RESULTS]]
            self.display_files(top_files)
            self.content_search_status.setText(
                f"✅ Showing {len(top_files)} best matches for \"{query}\""
            )

        except ImportError as _ie:
            self.content_search_status.setText("⚠️ CLIP not installed")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Content Search Unavailable",
                f"Image content search requires AI libraries.\n\n"
                f"Install with:\n  pip install open-clip-torch torch\n"
                f"or:\n  pip install transformers torch\n\n"
                f"Technical details: {_ie}"
            )
        except Exception as _e:
            logger.error(f"Content search failed: {_e}", exc_info=True)
            self.content_search_status.setText(f"❌ Error: {_e}")

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
                # Initial icon — replaced by async thumbnail when ready
                item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
            
            self.file_list.addItem(item)
        
        # Generate thumbnails in background
        image_files = [f for f in files if f.suffix.lower() in self.IMAGE_EXTENSIONS]
        if image_files and PIL_AVAILABLE:
            self.thumbnail_generator = ThumbnailGenerator(image_files, size=96)
            self.thumbnail_generator.thumbnail_ready.connect(self.on_thumbnail_ready)
            self.thumbnail_generator.start()
    
    def on_thumbnail_ready(self, filepath: str, qimage: QImage):
        """Handle thumbnail generated — convert QImage → QPixmap in the main (GUI) thread."""
        try:
            pixmap = QPixmap.fromImage(qimage)
        except Exception as _e:
            logger.debug(f"QImage→QPixmap conversion failed: {_e}")
            return
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
        """Handle file double-clicked — open with default OS application."""
        filepath = Path(item.data(Qt.ItemDataRole.UserRole))
        import subprocess
        import platform
        import os
        
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.Popen(('open', str(filepath)))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(str(filepath))
            else:  # Linux / other POSIX
                subprocess.Popen(('xdg-open', str(filepath)))
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
                    # Capture original dimensions before thumbnail() resizes in-place
                    original_width, original_height = img.size
                    original_format = img.format
                    original_mode = img.mode
                    
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
                    
                    # Show file info using saved original dimensions (no second file-open)
                    size_mb = filepath.stat().st_size / (1024 * 1024)
                    self.info_label.setText(
                        f"<b>File:</b> {filepath.name}<br>"
                        f"<b>Size:</b> {original_width} x {original_height}<br>"
                        f"<b>Format:</b> {original_format}<br>"
                        f"<b>Mode:</b> {original_mode}<br>"
                        f"<b>File Size:</b> {size_mb:.2f} MB"
                    )
                else:
                    self.preview_label.setText("PIL not available\nCannot show preview")
                    
        except Exception as e:
            logger.error(f"Error showing preview: {e}", exc_info=True)
            self.preview_label.setText(f"Error loading preview:\n{e}")
    
    def closeEvent(self, event):
        """Stop the thumbnail generator thread before the widget is destroyed.

        Without this, the thread may emit ``thumbnail_ready`` after the widget
        is gone, causing a RuntimeError or segfault (Qt uses-after-free).
        """
        if self.thumbnail_generator is not None and self.thumbnail_generator.isRunning():
            self.thumbnail_generator.stop()
            self.thumbnail_generator.wait(500)  # 500 ms grace period
        super().closeEvent(event)

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

    def _clear_recent_folders(self):
        """Clear recent folders history."""
        self.recent_folders = []
        self.update_recent_combo()
        self.save_recent_folders()
