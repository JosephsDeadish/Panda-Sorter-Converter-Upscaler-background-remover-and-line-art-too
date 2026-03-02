from __future__ import annotations
"""
Batch Rename Panel UI - PyQt6 Version
User interface for batch renaming files with various patterns.
"""

import os
import logging
from pathlib import Path
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QRadioButton, QButtonGroup, QLineEdit, QSpinBox, QCheckBox,
        QTextEdit, QFileDialog, QMessageBox, QProgressBar, QFrame,
        QScrollArea, QGroupBox, QSplitter
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    QThread = object
    QScrollArea = object
    QGroupBox = object
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
    QButtonGroup = object
    QCheckBox = object
    QFileDialog = object
    QHBoxLayout = object
    QLabel = object
    QLineEdit = object
    QMessageBox = object
    QProgressBar = object
    QPushButton = object
    QRadioButton = object
    QSpinBox = object
    QTextEdit = object
    QVBoxLayout = object
from typing import List, Optional

try:
    from tools.batch_renamer import BatchRenamer, RenamePattern
    _RENAMER_TOOL_AVAILABLE = True
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"batch_renamer tool not available: {_e}")
    BatchRenamer = None  # type: ignore[assignment,misc]
    RenamePattern = None  # type: ignore[assignment]
    _RENAMER_TOOL_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")

# Try to import SVG icon helper
try:
    from utils.svg_icon_helper import load_icon
    SVG_ICONS_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    load_icon = None
    SVG_ICONS_AVAILABLE = False

# Try to import tooltip system
try:
    from features.tutorial_system import WidgetTooltip
    TOOLTIPS_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
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
                if self.isInterruptionRequested():
                    raise InterruptedError("Cancelled by user")
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
        except InterruptedError as e:
            self.finished.emit(0, [str(e)])
        except Exception as e:
            logger.error(f"Rename failed: {e}")
            self.finished.emit(0, [str(e)])


class BatchRenamePanelQt(QWidget):
    """PyQt6 panel for batch file renaming."""

    finished = pyqtSignal(int, list)  # successes count, errors list
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.renamer = BatchRenamer() if BatchRenamer is not None else None
        self.selected_files: List[str] = []
        self.preview_data: List = []
        self.worker_thread = None
        self.setAcceptDrops(True)  # drag-and-drop files onto the panel

        # Debounce timer for auto-preview (fires 400 ms after last keystroke)
        if PYQT_AVAILABLE:
            self._preview_timer = QTimer(self)
            self._preview_timer.setSingleShot(True)
            self._preview_timer.setInterval(400)
            self._preview_timer.timeout.connect(self._generate_preview)
        else:
            self._preview_timer = None
        
        self._create_widgets()

    # ── Drag-and-drop support ──────────────────────────────────────────────
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """Accept dropped files into the batch rename queue."""
        existing = set(self.selected_files)
        added = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                s = str(path)
                if s not in existing:
                    added.append(s)
                    existing.add(s)
            elif path.is_dir():
                for child in sorted(path.iterdir()):
                    if child.is_file():
                        s = str(child)
                        if s not in existing:
                            added.append(s)
                            existing.add(s)
        if added:
            self.selected_files.extend(added)
            count = len(self.selected_files)
            if hasattr(self, 'file_count_label'):
                self.file_count_label.setText(f"{count} files selected")
                self.file_count_label.setStyleSheet("color: green; font-weight: bold;")
            if self._preview_timer is not None:
                self._preview_timer.start()
        event.acceptProposedAction()
    
    def _create_widgets(self):
        """Create the UI widgets with left-controls / right-preview QSplitter layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # Title
        title_label = QLabel("📝 Batch Rename Tool")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Rename multiple files using patterns, dates, resolution, or custom templates")
        subtitle_label.setStyleSheet("color: gray; font-size: 10pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # ── Main splitter: LEFT = controls, RIGHT = preview ───────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, stretch=1)

        # ── LEFT: scrollable controls ─────────────────────────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setMinimumWidth(280)
        left_scroll.setMaximumWidth(520)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(2, 2, 4, 2)

        self._create_file_section(left_layout)
        self._create_pattern_section(left_layout)
        self._create_options_section(left_layout)
        self._create_metadata_section(left_layout)
        self._create_action_buttons(left_layout)
        left_layout.addStretch()

        left_scroll.setWidget(left_widget)
        splitter.addWidget(left_scroll)

        # ── RIGHT: rename preview ─────────────────────────────────────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 0, 0, 0)
        self._create_preview_section(right_layout)
        splitter.addWidget(right_widget)

        # Controls: 380 px; preview gets the rest
        splitter.setSizes([380, 400])
    
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
        self._set_tooltip(select_files_btn, 'input_browse')
        btn_layout.addWidget(select_files_btn)

        select_folder_btn = QPushButton("📂 Select Folder")
        select_folder_btn.clicked.connect(self._select_folder)
        self._set_tooltip(select_folder_btn, 'input_browse')
        btn_layout.addWidget(select_folder_btn)

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self._clear_files)
        self._set_tooltip(clear_btn, "Clear the selected files list")
        btn_layout.addWidget(clear_btn)
        
        group_layout.addLayout(btn_layout)

        self.recursive_cb = QCheckBox("📂 Process sub-folders recursively")
        self.recursive_cb.setChecked(False)
        self._set_tooltip(self.recursive_cb, "When adding a folder, also include images in sub-folders")
        group_layout.addWidget(self.recursive_cb)

        # Archive options
        archive_layout = QHBoxLayout()
        
        self.archive_input_cb = QCheckBox("📦 Input is Archive")
        if not ARCHIVE_AVAILABLE:
            self.archive_input_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_input_cb.setStyleSheet("color: gray;")
        else:
            self._set_tooltip(self.archive_input_cb, 'input_archive_checkbox')
        archive_layout.addWidget(self.archive_input_cb)
        
        self.archive_output_cb = QCheckBox("📦 Export to Archive")
        if not ARCHIVE_AVAILABLE:
            self.archive_output_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_output_cb.setStyleSheet("color: gray;")
        else:
            self._set_tooltip(self.archive_output_cb, 'output_archive_checkbox')
        archive_layout.addWidget(self.archive_output_cb)
        
        archive_layout.addStretch()
        group_layout.addLayout(archive_layout)
        
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
            if value in (RenamePattern.DATE_CREATED, RenamePattern.DATE_MODIFIED, RenamePattern.DATE_EXIF):
                self._set_tooltip(radio, 'rename_date')
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
        self.template_entry.textChanged.connect(self._auto_preview)
        template_layout.addWidget(self.template_entry)
        self._set_tooltip(self.template_entry, 'rename_template')
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
        self._set_tooltip(self.copyright_entry, 'rename_copyright')
        
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
        self._set_tooltip(preview_btn, 'preview_button')
        group_layout.addWidget(preview_btn)
        
        # Preview text
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(80)  # right pane stretches to fill
        self.preview_text.setPlaceholderText("Preview will appear here...")
        group_layout.addWidget(self.preview_text)
        self._set_tooltip(self.preview_text, 'rename_preview')
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        btn_layout = QHBoxLayout()
        
        # Rename button
        self.rename_btn = QPushButton("🚀 Rename Files")
        self.rename_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        self.rename_btn.clicked.connect(self._rename_files)
        self._set_tooltip(self.rename_btn, 'file_selection')
        btn_layout.addWidget(self.rename_btn)

        # Cancel button (hidden until rename starts)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self.cancel_btn.clicked.connect(self._cancel_rename)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self._set_tooltip(self.cancel_btn, 'stop_button')
        btn_layout.addWidget(self.cancel_btn)
        
        # Undo button
        self.undo_btn = QPushButton("↩️ Undo Last Rename")
        self.undo_btn.clicked.connect(self._undo_rename)
        btn_layout.addWidget(self.undo_btn)
        self._set_tooltip(self.undo_btn, 'rename_undo')
        
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
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.tga *.dds *.gif *.avif *.qoi *.apng *.jfif);;All Files (*.*)"
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
            extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif',
                          '.webp', '.tga', '.gif', '.dds', '.avif', '.qoi',
                          '.apng', '.jfif', '.ico', '.icns'}
            files = []
            recursive = hasattr(self, 'recursive_cb') and self.recursive_cb.isChecked()
            try:
                if recursive:
                    for root, _dirs, file_list in os.walk(directory):
                        for file in file_list:
                            if any(file.lower().endswith(ext) for ext in extensions):
                                files.append(os.path.join(root, file))
                else:
                    for file in os.listdir(directory):
                        fp = os.path.join(directory, file)
                        if os.path.isfile(fp) and any(file.lower().endswith(ext) for ext in extensions):
                            files.append(fp)
            except (OSError, PermissionError) as e:
                logger.error(f"Error accessing directory {directory}: {e}")
                QMessageBox.warning(
                    self,
                    "Directory Access Error",
                    f"Could not access directory:\n{directory}\n\n{str(e)}"
                )
                return

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
    
    def _auto_preview(self):
        """Restart the debounce timer so preview updates 400 ms after last keystroke."""
        if self._preview_timer is not None and self.selected_files:
            self._preview_timer.start()

    def _generate_preview(self):
        """Generate rename preview (also called automatically on template changes)."""
        if not self.selected_files:
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
        
        # Disable rename button; show cancel button
        self.rename_btn.setEnabled(False)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setEnabled(True)
            self.cancel_btn.setVisible(True)
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

    def _cancel_rename(self):
        """Cancel the running rename operation."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            if hasattr(self, 'cancel_btn'):
                self.cancel_btn.setEnabled(False)
            self.status_label.setText("Cancelling…")
    
    def _on_rename_progress(self, current, total, filename):
        """Handle rename progress updates."""
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Renaming {current}/{total}: {os.path.basename(filename)}")
    
    def _on_rename_finished(self, successes, errors):
        """Handle rename completion."""
        self.progress_bar.setVisible(False)
        self.rename_btn.setEnabled(True)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setVisible(False)
        
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

        # Notify listeners (e.g. main window status bar)
        self.finished.emit(successes, errors)
    
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

    def _set_tooltip(self, widget, text_or_id: str):
        """Set tooltip on a widget using tooltip manager if available.

        If *text_or_id* has no spaces it is treated as a widget-ID key and
        registered with the cycling tooltip system so that mode changes and
        repeated hovers cycle through the full tip list.
        """
        if self.tooltip_manager:
            tip = self.tooltip_manager.get_tooltip(text_or_id) if ' ' not in text_or_id else text_or_id
            widget.setToolTip(tip)
            if hasattr(self.tooltip_manager, 'register'):
                self.tooltip_manager.register(widget, text_or_id if ' ' not in text_or_id else None)
        else:
            widget.setToolTip(text_or_id)
