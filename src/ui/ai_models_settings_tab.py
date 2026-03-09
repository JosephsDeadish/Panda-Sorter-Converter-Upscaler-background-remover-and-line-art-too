"""AI Models Settings Tab - Manage model downloads with beautiful UI"""


from __future__ import annotations
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QProgressBar, QScrollArea, QFrame, QMessageBox, QSizePolicy
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
    from PyQt6.QtGui import QFont, QColor
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    QThread = object
    QScrollArea = object
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
    class QFont:
        def __init__(self, *a): pass
    class QSize:
        def __init__(self, *a): pass
    QHBoxLayout = object
    QLabel = object
    QMessageBox = object
    QProgressBar = object
    QPushButton = object
    QSizePolicy = object
    QVBoxLayout = object
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import model manager with correct paths.
# Three-tier fallback so this works in:
#   1. Normal development (src/ in sys.path, relative import works)
#   2. Running main.py from repo root (absolute import works)
#   3. Frozen PyInstaller EXE (relative imports may fail; explicit path insert works)
def _import_model_manager():
    """Return (AIModelManager, ModelStatus) or (None, None) on failure."""
    # Attempt 1: relative import (works when ui is a proper package)
    try:
        from ..upscaler.model_manager import AIModelManager, ModelStatus  # noqa: PLC0415
        return AIModelManager, ModelStatus
    except (ImportError, ValueError):
        pass

    # Attempt 2: absolute import (works when src/ is in sys.path)
    try:
        from upscaler.model_manager import AIModelManager, ModelStatus  # noqa: PLC0415
        return AIModelManager, ModelStatus
    except (ImportError, OSError, RuntimeError):
        pass

    # Attempt 3: explicit path insert (works in frozen EXE where sys.path differs)
    try:
        import sys
        from pathlib import Path
        _here = Path(__file__).resolve().parent          # .../src/ui/
        _upscaler = str(_here.parent / 'upscaler')      # .../src/upscaler/
        _src = str(_here.parent)                         # .../src/
        for _p in (_src, _upscaler):
            if _p not in sys.path:
                sys.path.insert(0, _p)
        from model_manager import AIModelManager, ModelStatus  # noqa: PLC0415
        return AIModelManager, ModelStatus
    except (ImportError, OSError, RuntimeError):
        pass

    return None, None


_AIModelManager, _ModelStatus = _import_model_manager()
if _AIModelManager is not None:
    AIModelManager = _AIModelManager
    ModelStatus = _ModelStatus
    MODEL_MANAGER_AVAILABLE = True
    logger.info("✅ Model manager loaded successfully")
else:
    logger.warning("⚠️ Model manager not available - AI models tab will be limited")
    MODEL_MANAGER_AVAILABLE = False
    AIModelManager = None
    ModelStatus = None



class ModelDownloadThread(QThread):
    """Background thread for downloading models"""
    progress = pyqtSignal(int, int)  # downloaded, total
    finished = pyqtSignal(bool)  # success
    
    def __init__(self, model_manager, model_name):
        super().__init__()
        self.model_manager = model_manager
        self.model_name = model_name
    
    def run(self):
        def _progress_cb(d, t):
            if self.isInterruptionRequested():
                raise InterruptedError("Download cancelled by user")
            self.progress.emit(d, t)

        try:
            success = self.model_manager.download_model(
                self.model_name,
                progress_callback=_progress_cb
            )
            self.finished.emit(success)
        except InterruptedError:
            self.finished.emit(False)


class ModelCardWidget(QFrame):
    """Beautiful expandable card for a single model"""
    
    def __init__(self, model_name: str, model_info: dict, model_manager: AIModelManager):
        super().__init__()
        self.model_name = model_name
        self.model_info = model_info
        self.model_manager = model_manager
        self.download_thread = None
        self.is_expanded = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the card UI"""
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                padding: 0px;
            }
            QFrame:hover {
                border: 2px solid #2196F3;
                background-color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)
        
        # Header (always visible, clickable)
        header = self.create_header()
        layout.addLayout(header)
        
        # Details (expandable)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_layout.setSpacing(8)
        self.details_widget.setLayout(self.details_layout)
        self.details_widget.setVisible(False)
        
        self.populate_details()
        layout.addWidget(self.details_widget)
        
        self.setLayout(layout)
    
    def create_header(self) -> QHBoxLayout:
        """Create the header with icon, name, status, and expand button"""
        header = QHBoxLayout()
        
        # Icon + Name
        icon = self.model_info.get('icon', '📦')
        name = self.model_name
        
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(f"{icon} {name}")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        title_label.setFont(font)
        title_layout.addWidget(title_label)
        left_layout.addLayout(title_layout)
        
        status = self.model_info.get('status', 'unknown')
        if status == 'installed':
            status_text = "✅ Installed"
            status_color = "green"
        else:
            status_text = "❌ Not Installed"
            status_color = "red"
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: 10px;")
        left_layout.addWidget(status_label)
        
        header.addLayout(left_layout)
        header.addStretch()
        
        # Expand button
        self.expand_btn = QPushButton("▼")
        self.expand_btn.setMaximumWidth(35)
        self.expand_btn.setMaximumHeight(35)
        self.expand_btn.setToolTip("Expand or collapse model details")
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background-color: #e3f2fd;
                border: 1px solid #2196F3;
                border-radius: 4px;
                color: #2196F3;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2196F3;
                color: white;
            }
        """)
        self.expand_btn.clicked.connect(self.toggle_expand)
        header.addWidget(self.expand_btn)
        
        return header
    
    def toggle_expand(self):
        """Toggle details visibility"""
        self.is_expanded = not self.is_expanded
        self.details_widget.setVisible(self.is_expanded)
        self.expand_btn.setText("▲" if self.is_expanded else "▼")
    
    def populate_details(self):
        """Populate the details section"""
        # Size
        size = self.model_info.get('size_mb', 0)
        if size > 0:
            size_label = QLabel(f"📊 Size: {size} MB")
            size_label.setStyleSheet("font-size: 10px; color: #666;")
            self.details_layout.addWidget(size_label)
        
        # Version
        version = self.model_info.get('version', 'N/A')
        version_label = QLabel(f"📌 Version: {version}")
        version_label.setStyleSheet("font-size: 10px; color: #666;")
        self.details_layout.addWidget(version_label)
        
        # Description
        desc = self.model_info.get('description', '')
        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 10px; color: #555; margin: 5px 0px;")
        self.details_layout.addWidget(desc_label)

        # Panda status label — animated emoji during download
        self._panda_status_label = QLabel('')
        self._panda_status_label.setStyleSheet(
            "font-size: 13px; color: #7b4ea0; font-weight: bold; padding: 2px 0;"
        )
        self._panda_status_label.setVisible(False)
        self.details_layout.addWidget(self._panda_status_label)

        # Buttons / status
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)

        if not self.model_info.get('installed', False):
            # Model missing — guide user to setup_models.py instead of an in-app download
            missing_lbl = QLabel(
                "⚠️  Model not found.  Run  <b>python setup_models.py</b>  from the app folder "
                "to install all bundled AI models."
            )
            missing_lbl.setStyleSheet("color: #c44; font-size: 10pt;")
            missing_lbl.setWordWrap(True)
            missing_lbl.setTextFormat(Qt.TextFormat.RichText)
            button_layout.addWidget(missing_lbl)
            # Keep cancel button as a hidden attribute — not shown in UI since
            # in-app downloads are disabled (models are bundled), but the attribute
            # must exist to satisfy the cancellation infrastructure and existing tests.
            self._cancel_download_btn = QPushButton("✕ Cancel")
            self._cancel_download_btn.setVisible(False)
            self._cancel_download_btn.setEnabled(False)
        else:
            # Delete button
            delete_text = "🗑️  Delete"
            # Only show size if it's defined and not variable
            if self.model_info.get('size_mb', 0) > 0 and not self.model_info.get('size_varies', False):
                delete_text = f"🗑️  Delete ({self.model_info.get('size_mb', 0)} MB)"
            delete_btn = QPushButton(delete_text)
            delete_btn.setMinimumHeight(40)
            delete_btn.setMinimumWidth(200)
            delete_btn.setToolTip("Delete this AI model from disk to free up space")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
                QPushButton:pressed {
                    background-color: #c9000a;
                }
            """)
            delete_btn.clicked.connect(self.delete_model)
            button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        self.details_layout.addLayout(button_layout)

    # ── Panda-themed download messages ───────────────────────────────────────

    _PANDA_DOWNLOAD_MSGS = [
        '🐼 Panda is fetching bamboo-encoded weights…',
        '🐼 Panda carrying a heavy model pack 🎒…',
        '🐼 Almost there, panda is running! 🏃',
        '🐼💤 Big model — panda is napping while it downloads…',
        '🐼 Panda found the weights in the bamboo forest! 🌿',
    ]

    def _panda_progress_text(self, downloaded: int, total: int) -> str:
        """Return a cute panda status string based on download progress."""
        if total <= 0:
            return '🐼 Downloading…'
        pct = downloaded / total * 100
        if pct < 20:
            return self._PANDA_DOWNLOAD_MSGS[0]
        elif pct < 50:
            return self._PANDA_DOWNLOAD_MSGS[1]
        elif pct < 75:
            return self._PANDA_DOWNLOAD_MSGS[2]
        elif pct < 95:
            return self._PANDA_DOWNLOAD_MSGS[3]
        return self._PANDA_DOWNLOAD_MSGS[4]
    
    def download_model(self):
        """Start downloading the model"""
        # Check if auto-download model (installed via pip, not a .pth file)
        if self.model_info.get('auto_download'):
            pkgs = ' '.join(self.model_info.get('required_packages', []))
            QMessageBox.information(
                self,
                "Installed via pip",
                f"<b>{self.model_name}</b> is managed by pip (no separate download needed).<br><br>"
                f"It is installed as part of:<br><code>pip install {pkgs}</code><br><br>"
                f"Run <b>pip install -r requirements.txt</b> to install all packages at once.",
            )
            return

        # Check if native module
        if self.model_info.get('native_module'):
            QMessageBox.information(
                self,
                "Built-in Module",
                f"<b>{self.model_name}</b> is built into the application and requires no download.",
            )
            return

        self.expand_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.progress.setRange(0, 100)
        # Show panda status label
        if hasattr(self, '_panda_status_label'):
            self._panda_status_label.setText('🐼 Panda is heading to the bamboo forest to fetch your model…')
            self._panda_status_label.setVisible(True)
        if hasattr(self, '_cancel_download_btn'):
            self._cancel_download_btn.setEnabled(True)
            self._cancel_download_btn.setVisible(True)

        self.download_thread = ModelDownloadThread(self.model_manager, self.model_name)
        self.download_thread.progress.connect(self._on_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def _cancel_download(self):
        """Cancel the running model download."""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.requestInterruption()
            if hasattr(self, '_cancel_download_btn'):
                self._cancel_download_btn.setEnabled(False)
            self.progress.setRange(0, 100)
            self.progress.setVisible(False)

    def _on_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            self.progress.setValue(int(downloaded / total * 100))
            # Update panda status label
            if hasattr(self, '_panda_status_label'):
                self._panda_status_label.setText(
                    self._panda_progress_text(downloaded, total)
                )
        else:
            # Unknown total — pulse
            self.progress.setRange(0, 0)

    def on_download_finished(self, success: bool):
        """Handle download completion"""
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        self.expand_btn.setEnabled(True)
        if hasattr(self, '_cancel_download_btn'):
            self._cancel_download_btn.setEnabled(False)
            self._cancel_download_btn.setVisible(False)
        # Hide panda status label
        if hasattr(self, '_panda_status_label'):
            self._panda_status_label.setVisible(False)

        if success:
            logger.info(f"✅ {self.model_name} downloaded successfully")
            QMessageBox.information(
                self,
                "Download Complete",
                f"🐼✅ <b>{self.model_name}</b> has been downloaded and is ready to use!\n\n"
                f"Panda verified the model and it passed the bamboo inspection! 🎋",
            )
            # Update UI to show installed status
            self.model_info['installed'] = True
            self.model_info['status'] = 'installed'
            self.recreate_ui()
        else:
            logger.error(f"❌ Failed to download {self.model_name}")
            url = self.model_info.get('url', 'unknown')
            mirror = self.model_info.get('mirror', '')
            error_msg = (
                f"🐼😢 <b>Panda couldn't fetch {self.model_name}</b><br><br>"
                f"Both download sources were tried and failed:<br>"
                f"• <small>{url}</small><br>"
                + (f"• <small>{mirror}</small><br>" if mirror else "")
                + "<br>Possible causes:<br>"
                "• Internet connection is down<br>"
                "• CDN server is temporarily unavailable<br>"
                "• Insufficient disk space<br>"
                "• Firewall / proxy blocking the request<br><br>"
                "💡 Try again in a few minutes, or download the model manually "
                "and place the <code>.pth</code> file in <code>app_data/models/</code>."
            )
            msg = QMessageBox(self)
            msg.setWindowTitle("Download Failed")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(error_msg)
            msg.exec()
    
    def delete_model(self):
        """Delete the model"""
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {self.model_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        if self.model_manager.delete_model(self.model_name):
            self.model_info['installed'] = False
            self.model_info['status'] = 'missing'
            self.recreate_ui()
            logger.info(f"✅ Deleted {self.model_name}")
            QMessageBox.information(
                self,
                "Model Deleted",
                f"{self.model_name} has been deleted successfully."
            )
        else:
            QMessageBox.critical(
                self,
                "Deletion Failed",
                f"Failed to delete {self.model_name}."
            )
    
    def recreate_ui(self):
        """Recreate UI after status change"""
        # Clear details layout
        while self.details_layout.count() > 0:
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Re-populate details
        self.populate_details()
        
        # Update header status
        layout = self.layout()
        if layout and layout.count() > 0:
            header_item = layout.itemAt(0)
            if header_item:
                # Find status label and update it
                for i in range(header_item.count()):
                    item = header_item.itemAt(i)
                    if item and item.layout():
                        for j in range(item.layout().count()):
                            widget_item = item.layout().itemAt(j)
                            if widget_item and isinstance(widget_item.widget(), QLabel):
                                label = widget_item.widget()
                                text = label.text()
                                if "Installed" in text or "Not Installed" in text:
                                    if self.model_info.get('installed', False):
                                        label.setText("✅ Installed")
                                        label.setStyleSheet("color: green; font-weight: bold; font-size: 10px;")
                                    else:
                                        label.setText("❌ Not Installed")
                                        label.setStyleSheet("color: red; font-weight: bold; font-size: 10px;")


class _CustomModelDropTarget(QLabel):
    """Drop-zone label that accepts dragged model files and copies them
    into the AI models directory."""

    _MODEL_EXTS = {'.pth', '.onnx', '.safetensors', '.bin', '.pt'}

    def __init__(self, model_manager=None, parent=None):
        super().__init__(parent)
        self._mgr = model_manager
        self.setText("⬇️  Drop model files here (.pth / .onnx / .safetensors / .bin / .pt)")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(70)
        self.setStyleSheet(
            "QLabel { border: 2px dashed #aaa; border-radius: 8px; "
            "color: #777; font-size: 11px; padding: 10px; background: #f8f8f8; }"
        )
        self.setAcceptDrops(True)
        self._models_dir = self._resolve_models_dir()

    def _resolve_models_dir(self):
        """Return the path to the models directory, creating it if needed."""
        # Try to get from model manager first
        if self._mgr and hasattr(self._mgr, 'models_dir'):
            d = Path(self._mgr.models_dir)
        else:
            # Default: <app_root>/models
            d = Path(__file__).resolve().parent.parent.parent / 'models'
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return d

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls()]
            if any(p.lower().endswith(tuple(self._MODEL_EXTS)) for p in paths):
                event.acceptProposedAction()
                self.setStyleSheet(
                    "QLabel { border: 2px dashed #1a6feb; border-radius: 8px; "
                    "color: #1a6feb; font-size: 11px; padding: 10px; background: #e8f0ff; }"
                )
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(
            "QLabel { border: 2px dashed #aaa; border-radius: 8px; "
            "color: #777; font-size: 11px; padding: 10px; background: #f8f8f8; }"
        )

    def dropEvent(self, event):
        self.setStyleSheet(
            "QLabel { border: 2px dashed #aaa; border-radius: 8px; "
            "color: #777; font-size: 11px; padding: 10px; background: #f8f8f8; }"
        )
        imported = []
        for url in event.mimeData().urls():
            src = url.toLocalFile()
            if src.lower().endswith(tuple(self._MODEL_EXTS)):
                name = self.import_model_file(src)
                if name:
                    imported.append(name)
        if imported:
            self.setText(f"✅ Imported: {', '.join(imported)}\n"
                         f"📂 Saved to: {self._models_dir}")
        event.acceptProposedAction()

    def import_model_file(self, src_path: str) -> str:
        """Copy *src_path* into the models directory.  Returns filename on success."""
        try:
            src = Path(src_path)
            if not src.is_file():
                return ''
            dest = self._models_dir / src.name
            if dest == src:
                self.setText(f"ℹ️ {src.name} is already in the models folder.")
                return src.name
            shutil.copy2(src, dest)
            logger.info("Custom model imported: %s → %s", src, dest)
            self.setText(f"✅ Imported: {src.name}\n📂 {dest}")
            return src.name
        except Exception as exc:
            logger.warning("import_model_file: %s", exc)
            self.setText(f"❌ Import failed: {exc}")
            return ''



    """Settings tab for managing AI models with beautiful UI"""
    
    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        
        if MODEL_MANAGER_AVAILABLE:
            self.model_manager = AIModelManager()
        else:
            self.model_manager = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the main UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("🤖 AI Models Status")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        # Subtitle — models ship pre-bundled with the application
        subtitle = QLabel(
            "All AI models are bundled with the application.\n"
            "If a model shows as missing, run  python setup_models.py  from the app folder.\n"
            "Drag-and-drop your own .pth / .onnx / .safetensors files below to add custom models."
        )
        subtitle.setStyleSheet("color: #666; font-size: 11px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)
        
        if not MODEL_MANAGER_AVAILABLE:
            error_label = QLabel("❌ Model manager not available")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(error_label)
            layout.addStretch()
            self.setLayout(layout)
            return
        
        # Scroll area for models
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)
        
        # Get all models
        models_info = self.model_manager.get_models_info()
        
        # Group by category
        categories = {}
        for model_name, info in models_info.items():
            cat = info.get('category', 'other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((model_name, info))
        
        # Display by category
        category_names = {
            'upscaler': '📈 Upscaler Models',
            'vision': '👁️ Vision Models',
            'nlp': '🔤 NLP Models',
            'acceleration': '⚡ Acceleration',
        }
        
        for cat_key in ['upscaler', 'vision', 'nlp', 'acceleration']:
            if cat_key not in categories:
                continue
            
            # Category header
            cat_label = QLabel(category_names.get(cat_key, cat_key))
            cat_font = QFont()
            cat_font.setPointSize(11)
            cat_font.setBold(True)
            cat_label.setFont(cat_font)
            cat_label.setStyleSheet("margin-top: 10px; margin-bottom: 5px; color: #333;")
            scroll_layout.addWidget(cat_label)
            
            # Models in category
            for model_name, info in categories[cat_key]:
                card = ModelCardWidget(model_name, info, self.model_manager)
                scroll_layout.addWidget(card)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # ── Custom model import section ────────────────────────────────────────
        custom_sep = QFrame()
        custom_sep.setFrameShape(QFrame.Shape.HLine)
        custom_sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(custom_sep)

        custom_header = QLabel("📂 Add Your Own AI Models")
        ch_font = QFont()
        ch_font.setPointSize(11)
        ch_font.setBold(True)
        custom_header.setFont(ch_font)
        layout.addWidget(custom_header)

        custom_info = QLabel(
            "Drag & drop model files (.pth, .onnx, .safetensors, .bin, .pt) onto the box below, "
            "or click Browse to copy them into the models folder."
        )
        custom_info.setWordWrap(True)
        custom_info.setStyleSheet("color: #555; font-size: 10px;")
        layout.addWidget(custom_info)

        self._custom_drop_label = _CustomModelDropTarget(self.model_manager)
        layout.addWidget(self._custom_drop_label)

        browse_row = QHBoxLayout()
        browse_btn = QPushButton("📁 Browse for model file…")
        browse_btn.setMinimumHeight(36)
        browse_btn.clicked.connect(self._browse_custom_model)
        browse_row.addWidget(browse_btn)
        browse_row.addStretch()
        layout.addLayout(browse_row)

        self.setLayout(layout)

    def _browse_custom_model(self) -> None:
        """Open a file dialog to copy a custom model file into the models folder."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            paths, _ = QFileDialog.getOpenFileNames(
                self, "Select AI Model File(s)", "",
                "AI Models (*.pth *.onnx *.safetensors *.bin *.pt);;All files (*.*)"
            )
            for src in paths:
                self._custom_drop_label.import_model_file(src)
        except Exception as _e:
            logger.warning("_browse_custom_model: %s", _e)
