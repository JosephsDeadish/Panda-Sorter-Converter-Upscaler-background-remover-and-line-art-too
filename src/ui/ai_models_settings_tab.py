"""AI Models Settings Tab - Manage model downloads"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QCheckBox, QGroupBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)

# Try to import model manager
try:
    from src.upscaler.model_manager import AIModelManager, ModelStatus
    MODEL_MANAGER_AVAILABLE = True
except ImportError:
    try:
        from upscaler.model_manager import AIModelManager, ModelStatus
        MODEL_MANAGER_AVAILABLE = True
    except ImportError:
        logger.warning("Model manager not available")
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
        success = self.model_manager.download_model(
            self.model_name,
            progress_callback=lambda d, t: self.progress.emit(d, t)
        )
        self.finished.emit(success)


class AIModelsSettingsTab(QWidget):
    """Settings tab for managing AI models"""
    
    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        self.download_threads = {}
        
        if MODEL_MANAGER_AVAILABLE:
            self.model_manager = AIModelManager()
        else:
            self.model_manager = None
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("AI Models")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Info text
        info = QLabel(
            "Manage AI model downloads for upscaling and other features.\n"
            "Models are stored in the 'models' folder next to the application."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(info)
        
        if not MODEL_MANAGER_AVAILABLE:
            error_label = QLabel("❌ Model manager not available")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(error_label)
            layout.addStretch()
            self.setLayout(layout)
            return
        
        # Models info
        models_info = self.model_manager.get_models_info()
        
        # Group models by tool
        tools = {}
        for model_name, info in models_info.items():
            tool = info.get('tool', 'other')
            if tool not in tools:
                tools[tool] = []
            tools[tool].append((model_name, info))
        
        # Create sections for each tool
        for tool_name, models in sorted(tools.items()):
            group = QGroupBox(tool_name.capitalize())
            group_layout = QVBoxLayout()
            
            for model_name, info in models:
                frame = self.create_model_frame(model_name, info)
                group_layout.addWidget(frame)
            
            group.setLayout(group_layout)
            layout.addWidget(group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_model_frame(self, model_name: str, info: dict) -> QFrame:
        """Create UI for a single model"""
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 4px; padding: 10px; }")
        
        layout = QVBoxLayout()
        
        # Model name and status
        header = QHBoxLayout()
        name_label = QLabel(f"📦 {info['description']}")
        font = QFont()
        font.setBold(True)
        name_label.setFont(font)
        header.addWidget(name_label)
        
        status_label = QLabel()
        if info['installed']:
            status_label.setText("✅ Installed")
            status_label.setStyleSheet("color: green;")
        else:
            status_label.setText("❌ Not Installed")
            status_label.setStyleSheet("color: red;")
        
        header.addWidget(status_label)
        header.addStretch()
        layout.addLayout(header)
        
        # Size info
        if 'size_mb' in info:
            size_label = QLabel(f"Size: {info['size_mb']} MB")
            size_label.setStyleSheet("color: gray; font-size: 10px;")
            layout.addWidget(size_label)
        
        # Auto-download info
        if info.get('auto_download'):
            auto_label = QLabel("Auto-downloads via package manager")
            auto_label.setStyleSheet("color: gray; font-size: 10px; font-style: italic;")
            layout.addWidget(auto_label)
        
        # Progress bar (hidden by default)
        progress = QProgressBar()
        progress.setVisible(False)
        progress.setObjectName(f"progress_{model_name}")
        layout.addWidget(progress)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        if not info.get('auto_download'):
            if not info['installed']:
                download_btn = QPushButton(f"Download Now ({info.get('size_mb', '?')} MB)")
                download_btn.setObjectName(f"download_{model_name}")
                download_btn.clicked.connect(
                    lambda checked, mn=model_name: self.download_model(mn)
                )
                button_layout.addWidget(download_btn)
            else:
                delete_btn = QPushButton(f"Delete ({info.get('size_mb', '?')} MB)")
                delete_btn.setStyleSheet("background-color: #ffcccc;")
                delete_btn.setObjectName(f"delete_{model_name}")
                delete_btn.clicked.connect(
                    lambda checked, mn=model_name: self.delete_model(mn)
                )
                button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        frame.setLayout(layout)
        frame.setObjectName(f"frame_{model_name}")
        return frame
    
    def download_model(self, model_name: str):
        """Download a model"""
        # Find the button and progress bar
        download_btn = self.findChild(QPushButton, f"download_{model_name}")
        progress = self.findChild(QProgressBar, f"progress_{model_name}")
        
        if download_btn:
            download_btn.setEnabled(False)
        if progress:
            progress.setVisible(True)
            progress.setValue(0)
        
        thread = ModelDownloadThread(self.model_manager, model_name)
        thread.progress.connect(
            lambda d, t: self.update_progress(model_name, d, t)
        )
        thread.finished.connect(
            lambda success: self.on_download_finished(model_name, success)
        )
        
        self.download_threads[model_name] = thread
        thread.start()
    
    def update_progress(self, model_name: str, downloaded: int, total: int):
        """Update download progress"""
        progress = self.findChild(QProgressBar, f"progress_{model_name}")
        if progress and total > 0:
            progress.setValue(int((downloaded / total) * 100))
    
    def on_download_finished(self, model_name: str, success: bool):
        """Handle download completion"""
        progress = self.findChild(QProgressBar, f"progress_{model_name}")
        download_btn = self.findChild(QPushButton, f"download_{model_name}")
        
        if progress:
            progress.setVisible(False)
        
        if success:
            logger.info(f"✅ {model_name} downloaded successfully")
            QMessageBox.information(
                self,
                "Download Complete",
                f"{model_name} has been downloaded successfully!"
            )
            # Refresh the UI
            self.refresh_ui()
        else:
            logger.error(f"❌ Failed to download {model_name}")
            QMessageBox.critical(
                self,
                "Download Failed",
                f"Failed to download {model_name}. Please check your internet connection and try again."
            )
            if download_btn:
                download_btn.setEnabled(True)
    
    def delete_model(self, model_name: str):
        """Delete a model"""
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {model_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        if self.model_manager.delete_model(model_name):
            logger.info(f"✅ Deleted {model_name}")
            QMessageBox.information(
                self,
                "Model Deleted",
                f"{model_name} has been deleted successfully."
            )
            # Refresh the UI
            self.refresh_ui()
        else:
            QMessageBox.critical(
                self,
                "Deletion Failed",
                f"Failed to delete {model_name}."
            )
    
    def refresh_ui(self):
        """Refresh the UI to reflect current model status"""
        # Clear current layout
        layout = self.layout()
        if layout:
            # Collect all items first
            items = []
            while layout.count():
                items.append(layout.takeAt(0))
            
            # Delete widgets
            for item in items:
                if item.widget():
                    item.widget().deleteLater()
        
        # Rebuild UI
        self.setup_ui()
