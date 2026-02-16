"""AI Models Settings Tab - Manage model downloads with beautiful UI"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QScrollArea, QFrame, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QFont, QColor
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
        
        # Progress bar (hidden by default)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        self.details_layout.addWidget(self.progress)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)
        
        if not self.model_info.get('installed', False):
            # Download button
            download_btn = QPushButton(f"⬇️  Download Now")
            # Only show size if it's defined and not variable
            if self.model_info.get('size_mb', 0) > 0 and not self.model_info.get('size_varies', False):
                download_btn.setText(f"⬇️  Download Now ({self.model_info['size_mb']} MB)")
            download_btn.setMinimumHeight(40)
            download_btn.setMinimumWidth(200)
            download_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            download_btn.clicked.connect(self.download_model)
            button_layout.addWidget(download_btn)
        else:
            # Delete button
            delete_text = "🗑️  Delete"
            # Only show size if it's defined and not variable
            if self.model_info.get('size_mb', 0) > 0 and not self.model_info.get('size_varies', False):
                delete_text = f"🗑️  Delete ({self.model_info.get('size_mb', 0)} MB)"
            delete_btn = QPushButton(delete_text)
            delete_btn.setMinimumHeight(40)
            delete_btn.setMinimumWidth(200)
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
    
    def download_model(self):
        """Start downloading the model"""
        # Check if auto-download model
        if self.model_info.get('auto_download'):
            QMessageBox.information(
                self,
                "Package Install Required",
                f"{self.model_name} is installed via package manager.\n\n"
                f"Run: pip install {' '.join(self.model_info.get('required_packages', []))}"
            )
            return
        
        # Check if native module
        if self.model_info.get('native_module'):
            QMessageBox.information(
                self,
                "Native Module",
                f"{self.model_name} is a native module built into the application."
            )
            return
        
        self.expand_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        self.download_thread = ModelDownloadThread(self.model_manager, self.model_name)
        self.download_thread.progress.connect(
            lambda d, t: self.progress.setValue(int((d / t) * 100)) if t > 0 else None
        )
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_finished(self, success: bool):
        """Handle download completion"""
        self.progress.setVisible(False)
        self.expand_btn.setEnabled(True)
        
        if success:
            logger.info(f"✅ {self.model_name} downloaded successfully")
            QMessageBox.information(
                self,
                "Download Complete",
                f"{self.model_name} has been downloaded successfully!"
            )
            # Update UI to show installed status
            self.model_info['installed'] = True
            self.model_info['status'] = 'installed'
            self.recreate_ui()
        else:
            logger.error(f"❌ Failed to download {self.model_name}")
            # Show detailed error message with troubleshooting tips
            error_msg = (
                f"❌ Could not download {self.model_name}\n\n"
                f"Possible causes:\n"
                f"• No internet connection\n"
                f"• Server temporarily unavailable\n"
                f"• Insufficient disk space\n"
                f"• Firewall blocking downloads\n\n"
                f"💡 Troubleshooting:\n"
                f"• Check your internet connection\n"
                f"• Try again in a few minutes\n"
                f"• Free up disk space if needed\n"
                f"• Check firewall settings\n\n"
                f"The system tried both primary and mirror URLs."
            )
            QMessageBox.critical(
                self,
                "Download Failed",
                error_msg
            )
    
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


class AIModelsSettingsTab(QWidget):
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
        title = QLabel("🤖 AI Models Management")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Download AI models on-demand or manage existing installations")
        subtitle.setStyleSheet("color: #666; font-size: 11px;")
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
        
        self.setLayout(layout)
