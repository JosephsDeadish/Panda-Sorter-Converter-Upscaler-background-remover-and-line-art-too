"""
Texture Organizer UI Panel - PyQt6 Version
Provides UI for organizing textures with visual style selection
"""

import logging
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QComboBox,
    QCheckBox, QGroupBox, QScrollArea, QFrame, QPlainTextEdit,
    QToolButton, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

try:
    from organizer import (
        OrganizationEngine, TextureInfo, ORGANIZATION_STYLES
    )
    ORGANIZER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Organizer not available: {e}")
    ORGANIZER_AVAILABLE = False


class OrganizerWorker(QThread):
    """Worker thread for organizing textures."""
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(bool, str)  # success, message
    log = pyqtSignal(str)  # log message
    
    def __init__(self, engine, source_dir, target_dir, style_id, settings):
        super().__init__()
        self.engine = engine
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.style_id = style_id
        self.settings = settings
        self._is_cancelled = False
    
    def run(self):
        """Execute organization in background."""
        try:
            self.log.emit(f"Starting organization with {self.style_id} style...")
            
            # Get the style class
            style_class = ORGANIZATION_STYLES.get(self.style_id)
            if not style_class:
                self.finished.emit(False, f"Unknown style: {self.style_id}")
                return
            
            # Create style instance
            style = style_class()
            
            # Organize
            result = self.engine.organize(
                source_dir=self.source_dir,
                target_dir=self.target_dir,
                style=style,
                recursive=self.settings.get('recursive', True),
                create_backup=self.settings.get('backup', True),
                dry_run=self.settings.get('dry_run', False),
                progress_callback=self._progress_callback,
                log_callback=self._log_callback
            )
            
            if self._is_cancelled:
                self.finished.emit(False, "Cancelled by user")
                return
            
            if self.settings.get('dry_run', False):
                self.finished.emit(True, "Dry run complete - no files were moved")
            else:
                self.finished.emit(True, f"Successfully organized {result.get('files_moved', 0)} files")
                
        except Exception as e:
            logger.error(f"Organization failed: {e}", exc_info=True)
            self.finished.emit(False, f"Organization failed: {str(e)}")
    
    def _progress_callback(self, current, total, message):
        """Handle progress callback."""
        if not self._is_cancelled:
            self.progress.emit(current, total, message)
    
    def _log_callback(self, message):
        """Handle log callback."""
        if not self._is_cancelled:
            self.log.emit(message)
    
    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True


class OrganizerPanelQt(QWidget):
    """PyQt6 panel for texture organization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not ORGANIZER_AVAILABLE:
            self._show_unavailable()
            return
        
        self.engine = OrganizationEngine()
        self.source_directory = None
        self.target_directory = None
        self.selected_style = 'minimalist'
        self.worker_thread = None
        
        self._create_widgets()
    
    def _show_unavailable(self):
        """Show message when organizer is not available."""
        layout = QVBoxLayout(self)
        label = QLabel(
            "⚠️ Texture Organizer Unavailable\n\n"
            "Required dependencies not installed."
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(14)
        label.setFont(font)
        layout.addWidget(label)
    
    def _create_widgets(self):
        """Create the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("📁 Texture Organizer")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Organize textures into structured folder hierarchies")
        subtitle_label.setStyleSheet("color: gray; font-size: 12pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Main container with scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        
        # Directory selection
        self._create_directory_section(main_layout)
        
        # Style selection
        self._create_style_section(main_layout)
        
        # Preview
        self._create_preview_section(main_layout)
        
        # Settings
        self._create_settings_section(main_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.status_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.organize_btn = QPushButton("🚀 Start Organization")
        self.organize_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.organize_btn.clicked.connect(self._start_organization)
        self.organize_btn.setEnabled(False)
        button_layout.addWidget(self.organize_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_organization)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _create_directory_section(self, layout):
        """Create directory selection section."""
        group = QGroupBox("📂 Directories")
        group_layout = QVBoxLayout()
        
        # Source directory
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))
        self.source_label = QLabel("No source selected")
        self.source_label.setStyleSheet("color: gray;")
        source_layout.addWidget(self.source_label, 1)
        select_source_btn = QPushButton("Browse...")
        select_source_btn.clicked.connect(self._select_source_directory)
        source_layout.addWidget(select_source_btn)
        group_layout.addLayout(source_layout)
        
        # Target directory
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target:"))
        self.target_label = QLabel("No target selected")
        self.target_label.setStyleSheet("color: gray;")
        target_layout.addWidget(self.target_label, 1)
        select_target_btn = QPushButton("Browse...")
        select_target_btn.clicked.connect(self._select_target_directory)
        target_layout.addWidget(select_target_btn)
        group_layout.addLayout(target_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_style_section(self, layout):
        """Create style selection section."""
        group = QGroupBox("🎨 Organization Styles")
        group_layout = QVBoxLayout()
        
        # Style info
        STYLE_INFO = {
            'minimalist': {
                'name': '📄 Minimalist',
                'desc': 'Simple: Category → Files',
                'example': 'Characters/texture.dds'
            },
            'flat': {
                'name': '📂 Flat',
                'desc': 'Category → Files (all LODs)',
                'example': 'Characters/character_lod0.dds'
            },
            'neopets': {
                'name': '🐾 Neopets',
                'desc': 'Category → Type → Individual',
                'example': 'Pets/Blumaroo/blumaroo_red.dds'
            },
            'sims': {
                'name': '👥 The Sims',
                'desc': 'Gender → Skin → Part → Variant',
                'example': 'Male/DarkSkin/Head/variant_01.dds'
            },
            'game_area': {
                'name': '🎮 Game Area',
                'desc': 'Level → Area → Type → Asset',
                'example': 'Level_01/Downtown/Buildings/shop.dds'
            },
            'asset_pipeline': {
                'name': '🏭 Asset Pipeline',
                'desc': 'Type → Resolution → Format',
                'example': 'Textures/2K/DDS/building_wall.dds'
            },
            'modular': {
                'name': '🔧 Modular',
                'desc': 'Character/Vehicle/Environment/UI',
                'example': 'Characters/Body/head_texture.dds'
            },
            'maximum_detail': {
                'name': '📊 Maximum Detail',
                'desc': 'Deep nested hierarchies',
                'example': 'Characters/Male/Adult/Casual/Shirt/Blue/LOD0/shirt.dds'
            },
            'custom': {
                'name': '⚙️ Custom',
                'desc': 'User-defined hierarchy',
                'example': 'custom/structure/here.dds'
            }
        }
        
        # Create grid of style buttons
        grid = QGridLayout()
        self.style_buttons = {}
        
        row = 0
        col = 0
        max_cols = 3
        
        for style_id, info in STYLE_INFO.items():
            btn = QToolButton()
            btn.setText(f"{info['name']}\n{info['desc']}")
            btn.setToolTip(f"Example: {info['example']}")
            btn.setCheckable(True)
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(200)
            btn.clicked.connect(lambda checked, s=style_id: self._select_style(s))
            self.style_buttons[style_id] = btn
            
            grid.addWidget(btn, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        group_layout.addLayout(grid)
        
        # Set minimalist as default
        self.style_buttons['minimalist'].setChecked(True)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_preview_section(self, layout):
        """Create preview section."""
        group = QGroupBox("👀 Folder Structure Preview")
        group_layout = QVBoxLayout()
        
        self.preview_text = QPlainTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setFont(QFont("Courier", 9))
        group_layout.addWidget(self.preview_text)
        
        # Update preview button
        update_preview_btn = QPushButton("🔄 Update Preview")
        update_preview_btn.clicked.connect(self._update_preview)
        group_layout.addWidget(update_preview_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        # Show initial preview
        self._update_preview()
    
    def _create_settings_section(self, layout):
        """Create settings section."""
        group = QGroupBox("⚙️ Settings")
        group_layout = QVBoxLayout()
        
        self.recursive_cb = QCheckBox("Process subdirectories recursively")
        self.recursive_cb.setChecked(True)
        group_layout.addWidget(self.recursive_cb)
        
        self.backup_cb = QCheckBox("Create backup before organizing")
        self.backup_cb.setChecked(True)
        group_layout.addWidget(self.backup_cb)
        
        self.dry_run_cb = QCheckBox("Dry run (preview only, don't move files)")
        self.dry_run_cb.setChecked(False)
        group_layout.addWidget(self.dry_run_cb)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _select_source_directory(self):
        """Select source directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Source Directory"
        )
        
        if directory:
            self.source_directory = directory
            self.source_label.setText(directory)
            self.source_label.setStyleSheet("color: green; font-weight: bold;")
            self._check_ready()
    
    def _select_target_directory(self):
        """Select target directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Target Directory"
        )
        
        if directory:
            self.target_directory = directory
            self.target_label.setText(directory)
            self.target_label.setStyleSheet("color: green; font-weight: bold;")
            self._check_ready()
    
    def _check_ready(self):
        """Check if ready to organize."""
        ready = bool(self.source_directory and self.target_directory)
        self.organize_btn.setEnabled(ready)
    
    def _select_style(self, style_id):
        """Select organization style and update preview."""
        self.selected_style = style_id
        
        # Uncheck other buttons
        for sid, btn in self.style_buttons.items():
            if sid != style_id:
                btn.setChecked(False)
        
        # Update preview
        self._update_preview()
    
    def _update_preview(self):
        """Show folder structure preview for selected style."""
        style_class = ORGANIZATION_STYLES.get(self.selected_style)
        if not style_class:
            return
        
        style = style_class()
        
        # Generate example preview
        example_textures = [
            TextureInfo(
                file_path="character_male.dds",
                filename="character_male.dds",
                category="Characters",
                confidence=0.95,
                dimensions=(512, 512),
                format="dds"
            ),
            TextureInfo(
                file_path="building_wall_lod0.png",
                filename="building_wall_lod0.png",
                category="Environment",
                confidence=0.92,
                lod_group="building_wall",
                lod_level=0,
                dimensions=(1024, 1024),
                format="png"
            ),
            TextureInfo(
                file_path="ui_button_blue.dds",
                filename="ui_button_blue.dds",
                category="UI",
                confidence=0.98,
                dimensions=(256, 256),
                format="dds"
            ),
        ]
        
        preview_lines = []
        preview_lines.append(f"📁 {style.get_name()}")
        preview_lines.append(f"   {style.get_description()}\n")
        preview_lines.append("Example structure:")
        
        for texture in example_textures:
            path = style.get_target_path(texture)
            preview_lines.append(f"   {path}")
        
        self.preview_text.setPlainText("\n".join(preview_lines))
    
    def _start_organization(self):
        """Start the organization process."""
        if not self.source_directory or not self.target_directory:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please select source and target directories."
            )
            return
        
        # Confirm action
        if not self.dry_run_cb.isChecked():
            reply = QMessageBox.question(
                self,
                "Confirm Organization",
                f"This will organize textures from:\n{self.source_directory}\n\n"
                f"To:\n{self.target_directory}\n\n"
                f"Backup: {'Yes' if self.backup_cb.isChecked() else 'No'}\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Gather settings
        settings = {
            'recursive': self.recursive_cb.isChecked(),
            'backup': self.backup_cb.isChecked(),
            'dry_run': self.dry_run_cb.isChecked()
        }
        
        # Disable UI
        self.organize_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setVisible(True)
        
        # Show progress
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting organization...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        
        # Start worker
        self.worker_thread = OrganizerWorker(
            self.engine,
            self.source_directory,
            self.target_directory,
            self.selected_style,
            settings
        )
        self.worker_thread.progress.connect(self._update_progress)
        self.worker_thread.log.connect(self._update_log)
        self.worker_thread.finished.connect(self._organization_finished)
        self.worker_thread.start()
    
    def _cancel_organization(self):
        """Cancel the organization."""
        if self.worker_thread:
            self.worker_thread.cancel()
            self.status_label.setText("Cancelling...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
    
    def _update_progress(self, current, total, filename):
        """Update progress bar and status."""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        self.status_label.setText(f"Processing: {filename} ({current}/{total})")
    
    def _update_log(self, message):
        """Update log message."""
        logger.info(message)
    
    def _organization_finished(self, success, message):
        """Handle organization completion."""
        # Re-enable UI
        self.organize_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        
        # Update status
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.warning(self, "Error", message)
        
        self.worker_thread = None
