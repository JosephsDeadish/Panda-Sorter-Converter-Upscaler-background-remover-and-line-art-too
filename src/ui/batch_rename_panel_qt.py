"""
Batch Rename Panel UI - PyQt6 Version
User interface for batch renaming files with various patterns.
"""

import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QLineEdit, QSpinBox, QCheckBox,
    QTextEdit, QFileDialog, QMessageBox, QProgressBar, QFrame,
    QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import List, Optional

from tools.batch_renamer import BatchRenamer, RenamePattern

logger = logging.getLogger(__name__)

# Try to import SVG icon helper
try:
    from utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    load_icon = None
    SVG_ICONS_AVAILABLE = False

# Try to import tooltip system
try:
    from features.tutorial_system import WidgetTooltip
    TOOLTIPS_AVAILABLE = True
except ImportError:
    WidgetTooltip = None
    TOOLTIPS_AVAILABLE = False


class RenameWorker(QThread):
    """Worker thread for batch renaming."""
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(int, list)  # successes count, errors list
    
    def __init__(self, renamer, files, pattern, template, start_index, metadata):
        super().__init__()
        self.renamer = renamer
        self.files = files
        self.pattern = pattern
        self.template = template
        self.start_index = start_index
        self.metadata = metadata
    
    def run(self):
        """Execute rename in background thread."""
        try:
            def progress_callback(current, total, filename):
                self.progress.emit(current, total, filename)
            
            successes, errors = self.renamer.batch_rename(
                self.files,
                self.pattern,
                self.template,
                self.start_index,
                self.metadata,
                progress_callback
            )
            
            self.finished.emit(len(successes), errors)
        except Exception as e:
            logger.error(f"Rename failed: {e}")
            self.finished.emit(0, [str(e)])


class BatchRenamePanelQt(QWidget):
    """PyQt6 panel for batch file renaming."""
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.renamer = BatchRenamer()
        self.selected_files: List[str] = []
        self.preview_data: List = []
        self.worker_thread = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("📝 Batch Rename Tool")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Rename multiple files using patterns, dates, resolution, or custom templates")
        subtitle_label.setStyleSheet("color: gray; font-size: 11pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        
        self._create_file_section(main_layout)
        self._create_pattern_section(main_layout)
        self._create_options_section(main_layout)
        self._create_metadata_section(main_layout)
        self._create_preview_section(main_layout)
        self._create_action_buttons(main_layout)
        
        main_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _create_file_section(self, layout):
        """Create file selection section."""
        group = QGroupBox("📁 Select Files")
        group_layout = QVBoxLayout()
        
        # File count label
        self.file_count_label = QLabel("No files selected")
        self.file_count_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.file_count_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        select_files_btn = QPushButton("➕ Select Images")
        select_files_btn.clicked.connect(self._select_files)
        btn_layout.addWidget(select_files_btn)
        
        select_folder_btn = QPushButton("📂 Select Folder")
        select_folder_btn.clicked.connect(self._select_folder)
        btn_layout.addWidget(select_folder_btn)
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self._clear_files)
        btn_layout.addWidget(clear_btn)
        
        group_layout.addLayout(btn_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_pattern_section(self, layout):
        """Create rename pattern section."""
        group = QGroupBox("🎯 Rename Pattern")
        group_layout = QVBoxLayout()
        
        self.pattern_group = QButtonGroup(self)
        
        patterns = [
            ("📅 Date Created", RenamePattern.DATE_CREATED),
            ("📅 Date Modified", RenamePattern.DATE_MODIFIED),
            ("📷 EXIF Date", RenamePattern.DATE_EXIF),
            ("📐 Resolution (WxH)", RenamePattern.RESOLUTION),
            ("🔢 Sequential (1, 2, 3...)", RenamePattern.SEQUENTIAL),
            ("✏️ Custom Template", RenamePattern.CUSTOM),
            ("🔒 Privacy (Random)", RenamePattern.PRIVACY)
        ]
        
        for text, value in patterns:
            radio = QRadioButton(text)
            radio.setProperty("pattern", value)
            self.pattern_group.addButton(radio)
            group_layout.addWidget(radio)
            if value == RenamePattern.SEQUENTIAL:
                radio.setChecked(True)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_options_section(self, layout):
        """Create options section."""
        group = QGroupBox("⚙️ Options")
        group_layout = QVBoxLayout()
        
        # Template for custom pattern
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Custom Template:"))
        self.template_entry = QLineEdit()
        self.template_entry.setPlaceholderText("e.g., image_{index}_{date}")
        template_layout.addWidget(self.template_entry)
        group_layout.addLayout(template_layout)
        
        # Start index for sequential
        index_layout = QHBoxLayout()
        index_layout.addWidget(QLabel("Start Index:"))
        self.start_index_spin = QSpinBox()
        self.start_index_spin.setRange(0, 99999)
        self.start_index_spin.setValue(1)
        index_layout.addWidget(self.start_index_spin)
        index_layout.addStretch()
        group_layout.addLayout(index_layout)
        
        # Options checkboxes
        self.preserve_extension_cb = QCheckBox("Preserve original file extension")
        self.preserve_extension_cb.setChecked(True)
        group_layout.addWidget(self.preserve_extension_cb)
        
        self.confirm_overwrite_cb = QCheckBox("Confirm before overwriting files")
        self.confirm_overwrite_cb.setChecked(True)
        group_layout.addWidget(self.confirm_overwrite_cb)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_metadata_section(self, layout):
        """Create metadata injection section."""
        group = QGroupBox("📋 Metadata Injection")
        group_layout = QVBoxLayout()
        
        self.add_metadata_cb = QCheckBox("Add metadata to files")
        group_layout.addWidget(self.add_metadata_cb)
        
        # Metadata fields
        meta_layout = QVBoxLayout()
        
        self.copyright_entry = QLineEdit()
        self.copyright_entry.setPlaceholderText("Copyright")
        meta_layout.addWidget(QLabel("Copyright:"))
        meta_layout.addWidget(self.copyright_entry)
        
        self.author_entry = QLineEdit()
        self.author_entry.setPlaceholderText("Author")
        meta_layout.addWidget(QLabel("Author:"))
        meta_layout.addWidget(self.author_entry)
        
        self.description_entry = QLineEdit()
        self.description_entry.setPlaceholderText("Description")
        meta_layout.addWidget(QLabel("Description:"))
        meta_layout.addWidget(self.description_entry)
        
        group_layout.addLayout(meta_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_preview_section(self, layout):
        """Create preview section."""
        group = QGroupBox("👁️ Preview")
        group_layout = QVBoxLayout()
        
        # Preview button
        preview_btn = QPushButton("🔍 Generate Preview")
        preview_btn.clicked.connect(self._generate_preview)
        group_layout.addWidget(preview_btn)
        
        # Preview text
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(200)
        self.preview_text.setPlaceholderText("Preview will appear here...")
        group_layout.addWidget(self.preview_text)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        btn_layout = QHBoxLayout()
        
        # Rename button
        self.rename_btn = QPushButton("🚀 Rename Files")
        self.rename_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        self.rename_btn.clicked.connect(self._rename_files)
        btn_layout.addWidget(self.rename_btn)
        
        # Undo button
        self.undo_btn = QPushButton("↩️ Undo Last Rename")
        self.undo_btn.clicked.connect(self._undo_rename)
        btn_layout.addWidget(self.undo_btn)
        
        layout.addLayout(btn_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
    
    def _select_files(self):
        """Open file dialog to select images."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;All Files (*.*)"
        )
        
        if files:
            self.selected_files = files
            self.file_count_label.setText(f"{len(files)} files selected")
            self.file_count_label.setStyleSheet("color: green; font-weight: bold;")
            self.status_label.setText("Files selected. Generate preview or rename.")
    
    def _select_folder(self):
        """Select all images in a folder."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Folder"
        )
        
        if directory:
            # Get all image files in directory
            extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
            files = []
            for file in os.listdir(directory):
                if any(file.lower().endswith(ext) for ext in extensions):
                    files.append(os.path.join(directory, file))
            
            if files:
                self.selected_files = files
                self.file_count_label.setText(f"{len(files)} files selected from folder")
                self.file_count_label.setStyleSheet("color: green; font-weight: bold;")
                self.status_label.setText("Files selected. Generate preview or rename.")
            else:
                QMessageBox.warning(self, "No Images", "No image files found in the selected folder")
    
    def _clear_files(self):
        """Clear selected files."""
        self.selected_files = []
        self.preview_data = []
        self.file_count_label.setText("No files selected")
        self.file_count_label.setStyleSheet("color: gray;")
        self.preview_text.clear()
        self.status_label.setText("Files cleared")
    
    def _get_selected_pattern(self):
        """Get the selected rename pattern."""
        checked_button = self.pattern_group.checkedButton()
        if checked_button:
            return checked_button.property("pattern")
        return RenamePattern.SEQUENTIAL
    
    def _generate_preview(self):
        """Generate rename preview."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files first")
            return
        
        try:
            pattern = self._get_selected_pattern()
            template = self.template_entry.text() if pattern == RenamePattern.CUSTOM else None
            start_index = self.start_index_spin.value()
            
            # Generate preview
            self.preview_data = self.renamer.generate_preview(
                self.selected_files,
                pattern,
                template,
                start_index
            )
            
            # Display preview
            self.preview_text.clear()
            self.preview_text.append("Original → New Name\n")
            self.preview_text.append("=" * 80 + "\n\n")
            
            for original, new_name in self.preview_data:
                original_name = os.path.basename(original)
                self.preview_text.append(f"{original_name}\n  → {new_name}\n\n")
            
            self.status_label.setText(f"Preview generated for {len(self.preview_data)} files")
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            QMessageBox.critical(self, "Error", f"Failed to generate preview: {str(e)}")
    
    def _rename_files(self):
        """Perform the rename operation."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files first")
            return
        
        # Confirm action
        reply = QMessageBox.question(
            self,
            "Confirm Rename",
            f"Rename {len(self.selected_files)} files?\n\nThis action can be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Get settings
        pattern = self._get_selected_pattern()
        template = self.template_entry.text() if pattern == RenamePattern.CUSTOM else None
        start_index = self.start_index_spin.value()
        
        # Get metadata if enabled
        metadata = None
        if self.add_metadata_cb.isChecked():
            metadata = {
                'copyright': self.copyright_entry.text(),
                'author': self.author_entry.text(),
                'description': self.description_entry.text()
            }
        
        # Disable button and show progress
        self.rename_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Renaming files...")
        
        # Start worker thread
        self.worker_thread = RenameWorker(
            self.renamer,
            self.selected_files,
            pattern,
            template,
            start_index,
            metadata
        )
        self.worker_thread.progress.connect(self._on_rename_progress)
        self.worker_thread.finished.connect(self._on_rename_finished)
        self.worker_thread.start()
    
    def _on_rename_progress(self, current, total, filename):
        """Handle rename progress updates."""
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Renaming {current}/{total}: {os.path.basename(filename)}")
    
    def _on_rename_finished(self, successes, errors):
        """Handle rename completion."""
        self.progress_bar.setVisible(False)
        self.rename_btn.setEnabled(True)
        
        if errors:
            error_msg = f"Renamed {successes} files successfully.\n\n"
            error_msg += f"Errors ({len(errors)}):\n"
            error_msg += "\n".join(errors[:10])  # Show first 10 errors
            if len(errors) > 10:
                error_msg += f"\n... and {len(errors) - 10} more"
            
            QMessageBox.warning(self, "Partial Success", error_msg)
            self.status_label.setText(f"Renamed {successes} files with {len(errors)} errors")
        else:
            QMessageBox.information(
                self,
                "Success",
                f"Successfully renamed {successes} files!"
            )
            self.status_label.setText(f"Successfully renamed {successes} files")
        
        # Clear files after successful rename
        if successes > 0:
            self._clear_files()
    
    def _undo_rename(self):
        """Undo the last rename operation."""
        try:
            if self.renamer.can_undo():
                reply = QMessageBox.question(
                    self,
                    "Confirm Undo",
                    "Restore files to their previous names?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    count = self.renamer.undo_last_rename()
                    QMessageBox.information(self, "Undo Complete", f"Restored {count} files")
                    self.status_label.setText(f"Undo complete: {count} files restored")
            else:
                QMessageBox.information(self, "No History", "No rename operation to undo")
        except Exception as e:
            logger.error(f"Error during undo: {e}")
            QMessageBox.critical(self, "Error", f"Failed to undo: {str(e)}")
