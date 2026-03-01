from __future__ import annotations
"""
Image Repair Panel - PyQt6 Version
UI for repairing corrupted PNG and JPEG files.
"""

import os
import logging
from typing import List, Optional
from pathlib import Path
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTextEdit, QFileDialog, QMessageBox, QProgressBar,
        QGroupBox, QScrollArea, QFrame, QCheckBox, QComboBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
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
    QCheckBox = object
    QComboBox = object
    QFileDialog = object
    QHBoxLayout = object
    QLabel = object
    QMessageBox = object
    QProgressBar = object
    QPushButton = object
    QTextEdit = object
    QVBoxLayout = object

try:
    from tools.image_repairer import ImageRepairer, CorruptionType, RepairResult, RepairMode
    REPAIRER_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ImageRepairer = None
    CorruptionType = None
    RepairResult = None
    RepairMode = None
    REPAIRER_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")


class DiagnosticWorker(QThread):
    """Worker thread for diagnosing images."""
    progress = pyqtSignal(str)  # message
    finished = pyqtSignal(list)  # results
    error = pyqtSignal(str)
    
    def __init__(self, repairer, files):
        super().__init__()
        self.repairer = repairer
        self.files = files
        self._should_cancel = False
    
    def run(self):
        """Run diagnostic in background."""
        try:
            results = []
            for filepath in self.files:
                if self._should_cancel:
                    break
                
                self.progress.emit(f"Diagnosing: {Path(filepath).name}")
                result = self.repairer.diagnose_file(filepath)
                results.append((filepath, result))
            
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Diagnostic failed: {e}")
            self.error.emit(str(e))
    
    def cancel(self):
        """Cancel the operation."""
        self._should_cancel = True


class RepairWorker(QThread):
    """Worker thread for repairing images."""
    progress = pyqtSignal(int, int, str)  # current, total, filename
    result = pyqtSignal(str, bool, str)  # filepath, success, message
    finished = pyqtSignal(int, int)  # successes, failures
    error = pyqtSignal(str)
    
    def __init__(self, repairer, files, output_dir, mode=None, skip_existing=False):
        super().__init__()
        self.repairer = repairer
        self.files = files
        self.output_dir = output_dir
        self.mode = mode or RepairMode.BALANCED
        self.skip_existing = skip_existing
        self._should_cancel = False

    @staticmethod
    def _compute_output_path(filepath: str, output_dir) -> str:
        """Return the output file path for *filepath*.

        Mirrors ``ImageRepairer.repair_file()``'s own auto-generation so the
        skip-if-exists check and the actual repair call agree on the path.
        """
        if output_dir is not None:
            return os.path.join(output_dir, Path(filepath).name)
        base, ext = os.path.splitext(filepath)
        return f"{base}_repaired{ext}"
    
    def run(self):
        """Run repair in background."""
        try:
            successes = 0
            failures = 0

            for i, filepath in enumerate(self.files):
                if self._should_cancel:
                    break

                filename = Path(filepath).name
                self.progress.emit(i + 1, len(self.files), filename)

                try:
                    # Use the shared helper so skip-check and repair_file agree on path.
                    output_path = self._compute_output_path(filepath, self.output_dir)

                    if self.skip_existing and os.path.exists(output_path):
                        successes += 1
                        self.result.emit(filepath, True, f"⏭️ {filename}: skipped (already exists)")
                        continue

                    # Pass the computed path, or None for auto-generation when
                    # output_dir wasn't set (repair_file computes the same path).
                    repair_path = output_path if self.output_dir is not None else None
                    result, message = self.repairer.repair_file(filepath, repair_path, self.mode)

                    if result in (RepairResult.SUCCESS, RepairResult.PARTIAL):
                        successes += 1
                        self.result.emit(filepath, True, f"✓ {filename}: {message}")
                    else:
                        failures += 1
                        self.result.emit(filepath, False, f"✗ {filename}: {message}")
                except Exception as e:
                    failures += 1
                    self.result.emit(filepath, False, f"✗ {filename}: {str(e)}")

            self.finished.emit(successes, failures)
        except Exception as e:
            logger.error(f"Repair failed: {e}")
            self.error.emit(str(e))
    
    def cancel(self):
        """Cancel the operation."""
        self._should_cancel = True


class ImageRepairPanelQt(QWidget):
    """PyQt6 panel for repairing corrupted images."""

    finished = pyqtSignal(bool, str, int)  # success, message, files_processed
    error = pyqtSignal(str)  # error message

    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.selected_files: List[str] = []
        self.output_dir: Optional[str] = None
        self.diagnostic_worker = None
        self.repair_worker = None
        
        if not REPAIRER_AVAILABLE:
            self._show_import_error()
            return
        
        self.repairer = ImageRepairer()
        self._create_widgets()
    
    def _show_import_error(self):
        """Show error if ImageRepairer cannot be imported."""
        layout = QVBoxLayout(self)
        error_label = QLabel("❌ Image Repair Tool could not be loaded.\nPlease check installation.")
        error_label.setStyleSheet("color: red; font-size: 14pt;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
    
    def _create_widgets(self):
        """Create UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("🔧 Image Repair Tool")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Repair corrupted PNG and JPEG image files")
        subtitle_label.setStyleSheet("color: gray; font-size: 12pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        
        self._create_file_section(main_layout)
        self._create_output_section(main_layout)
        self._create_diagnostic_section(main_layout)
        self._create_action_buttons(main_layout)
        
        main_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _create_file_section(self, layout):
        """Create file selection section."""
        group = QGroupBox("📁 Input Files")
        group_layout = QVBoxLayout()
        
        # File count
        self.file_count_label = QLabel("No files selected")
        self.file_count_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.file_count_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.select_files_btn = QPushButton("Select Files")
        self.select_files_btn.clicked.connect(self._select_files)
        self._set_tooltip(self.select_files_btn, 'input_browse')
        btn_layout.addWidget(self.select_files_btn)

        self.select_folder_btn = QPushButton("Select Folder")
        self.select_folder_btn.clicked.connect(self._select_folder)
        self._set_tooltip(self.select_folder_btn, 'input_browse')
        btn_layout.addWidget(self.select_folder_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_files)
        self._set_tooltip(self.clear_btn, "Clear the selected files list")
        btn_layout.addWidget(self.clear_btn)

        group_layout.addLayout(btn_layout)

        self.recursive_cb = QCheckBox("📂 Process sub-folders recursively")
        self.recursive_cb.setChecked(True)
        self._set_tooltip(self.recursive_cb, "When enabled, also searches sub-folders when a folder is selected")
        group_layout.addWidget(self.recursive_cb)

        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_output_section(self, layout):
        """Create output directory section."""
        group = QGroupBox("💾 Output Directory")
        group_layout = QVBoxLayout()
        
        self.output_dir_label = QLabel("Not set (will use same directory as input)")
        self.output_dir_label.setStyleSheet("color: gray;")
        self.output_dir_label.setWordWrap(True)
        group_layout.addWidget(self.output_dir_label)
        
        self.output_dir_btn = QPushButton("Select Output Directory")
        self.output_dir_btn.clicked.connect(self._select_output_dir)
        self._set_tooltip(self.output_dir_btn, 'output_browse')
        group_layout.addWidget(self.output_dir_btn)

        self._skip_existing = QCheckBox("Skip if output file already exists")
        self._skip_existing.setChecked(False)
        self._set_tooltip(self._skip_existing,
            "When checked, files are not re-processed if the output already exists.\n"
            "Without an output directory, the auto-generated '<name>_repaired.ext' path is checked."
        )
        group_layout.addWidget(self._skip_existing)
        
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
        
        # Repair mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Repair Mode:"))
        
        self.repair_mode_combo = QComboBox()
        self.repair_mode_combo.addItems(["Safe (PIL only)", "Balanced (Recommended)", "Aggressive (All methods)"])
        self.repair_mode_combo.setCurrentIndex(1)  # Default to Balanced
        self._set_tooltip(
            self.repair_mode_combo,
            "Safe: Only uses PIL recovery methods (safest, may miss some repairs)\n"
            "Balanced: Tries PIL first, then manual repairs (recommended)\n"
            "Aggressive: Attempts all recovery methods including segment extraction (risky but may recover more data)"
        )
        mode_layout.addWidget(self.repair_mode_combo)
        mode_layout.addStretch()
        group_layout.addLayout(mode_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_diagnostic_section(self, layout):
        """Create diagnostic results section."""
        group = QGroupBox("🔍 Diagnostic Results")
        group_layout = QVBoxLayout()
        
        self.diagnostic_text = QTextEdit()
        self.diagnostic_text.setReadOnly(True)
        self.diagnostic_text.setMinimumHeight(200)
        self.diagnostic_text.setPlaceholderText("Run diagnostics to see corruption analysis...")
        self._set_tooltip(self.diagnostic_text, 'repair_results')
        group_layout.addWidget(self.diagnostic_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        group_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.progress_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        btn_layout = QHBoxLayout()
        
        self.diagnose_btn = QPushButton("🔍 Diagnose")
        self.diagnose_btn.clicked.connect(self._diagnose_files)
        btn_layout.addWidget(self.diagnose_btn)
        self._set_tooltip(self.diagnose_btn, 'repair_diagnose')
        
        self.repair_btn = QPushButton("🔧 Repair Files")
        self.repair_btn.setStyleSheet("background-color: green; color: white; padding: 8px;")
        self.repair_btn.clicked.connect(self._repair_files)
        btn_layout.addWidget(self.repair_btn)
        self._set_tooltip(self.repair_btn, 'repair_fix')
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_operation)
        btn_layout.addWidget(self.cancel_btn)
        self._set_tooltip(self.cancel_btn, "Cancel the current operation")
        
        layout.addLayout(btn_layout)
    
    def _select_files(self):
        """Select image files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",
            "Image files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.tga *.gif);;"
            "PNG files (*.png);;JPEG files (*.jpg *.jpeg);;BMP files (*.bmp);;"
            "TIFF files (*.tiff *.tif);;WebP files (*.webp);;TGA files (*.tga);;"
            "GIF files (*.gif);;All files (*.*)"
        )
        
        if files:
            self.selected_files.extend(files)
            self._update_file_count()
    
    def _select_folder(self):
        """Select folder containing images."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder"
        )

        if folder:
            _REPAIR_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif',
                            '.webp', '.tga', '.gif', '.avif', '.qoi', '.apng',
                            '.jfif', '.ico', '.icns', '.dds')
            recursive = self.recursive_cb.isChecked()
            if recursive:
                for root, _dirs, files in os.walk(folder):
                    for file in files:
                        if file.lower().endswith(_REPAIR_EXTS):
                            self.selected_files.append(os.path.join(root, file))
            else:
                for file in os.listdir(folder):
                    fp = os.path.join(folder, file)
                    if os.path.isfile(fp) and file.lower().endswith(_REPAIR_EXTS):
                        self.selected_files.append(fp)

            self._update_file_count()
    
    def _clear_files(self):
        """Clear selected files."""
        self.selected_files.clear()
        self._update_file_count()
        self.diagnostic_text.clear()
    
    def _update_file_count(self):
        """Update file count label."""
        count = len(self.selected_files)
        if count == 0:
            self.file_count_label.setText("No files selected")
            self.file_count_label.setStyleSheet("color: gray;")
        elif count == 1:
            self.file_count_label.setText("1 file selected")
            self.file_count_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.file_count_label.setText(f"{count} files selected")
            self.file_count_label.setStyleSheet("color: green; font-weight: bold;")
    
    def _select_output_dir(self):
        """Select output directory."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        
        if folder:
            self.output_dir = folder
            self.output_dir_label.setText(folder)
            self.output_dir_label.setStyleSheet("color: green; font-weight: bold;")
    
    def _diagnose_files(self):
        """Diagnose selected files."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to diagnose.")
            return
        
        self.diagnostic_text.clear()
        self.diagnostic_text.append("Running diagnostics...\n")
        
        # Disable buttons
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Start diagnostic worker
        self.diagnostic_worker = DiagnosticWorker(self.repairer, self.selected_files)
        self.diagnostic_worker.progress.connect(self._on_diagnostic_progress)
        self.diagnostic_worker.finished.connect(self._on_diagnostic_finished)
        self.diagnostic_worker.error.connect(self._on_diagnostic_error)
        self.diagnostic_worker.start()
    
    def _on_diagnostic_progress(self, message):
        """Handle diagnostic progress."""
        self.progress_label.setText(message)
    
    def _on_diagnostic_finished(self, results):
        """Handle diagnostic completion."""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        
        self.diagnostic_text.clear()
        self.diagnostic_text.append("=== Diagnostic Results ===\n\n")
        
        for filepath, result in results:
            filename = Path(filepath).name
            if result.is_corrupted:
                self.diagnostic_text.append(f"⚠️ {filename}")
                self.diagnostic_text.append(f"   Status: CORRUPTED")
                self.diagnostic_text.append(f"   Type: {result.corruption_type}")
                if result.repairable:
                    self.diagnostic_text.append(f"   Recovery: {result.recovery_percentage:.0f}% recoverable")
                details = '; '.join(result.notes) if result.notes else 'No additional details'
                self.diagnostic_text.append(f"   Details: {details}\n")
            else:
                self.diagnostic_text.append(f"✓ {filename}")
                extra = f' ({"; ".join(result.notes)})' if result.notes else ''
                self.diagnostic_text.append(f"   Status: OK{extra}\n")
        
        self.progress_label.setText("Diagnostic complete")
    
    def _on_diagnostic_error(self, error_msg):
        """Handle diagnostic error."""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        QMessageBox.critical(self, "Error", f"Diagnostic failed: {error_msg}")
        self.progress_label.setText("Diagnostic failed")
        self.error.emit(error_msg)
    
    def _repair_files(self):
        """Repair selected files."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to repair.")
            return
        
        # Get selected repair mode
        mode_index = self.repair_mode_combo.currentIndex()
        if mode_index == 0:
            mode = RepairMode.SAFE
        elif mode_index == 1:
            mode = RepairMode.BALANCED
        else:  # index == 2
            mode = RepairMode.AGGRESSIVE
        
        # Confirm
        mode_name = ["Safe", "Balanced", "Aggressive"][mode_index]
        reply = QMessageBox.question(
            self,
            "Confirm Repair",
            f"Repair {len(self.selected_files)} files using {mode_name} mode?\n\nRepaired files will be saved with '_repaired' suffix.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.diagnostic_text.clear()
        self.diagnostic_text.append(f"Starting repair in {mode_name} mode...\n")
        
        # Disable buttons
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.selected_files))
        self.progress_bar.setValue(0)
        
        # Start repair worker with selected mode
        self.repair_worker = RepairWorker(
            self.repairer, self.selected_files, self.output_dir, mode,
            skip_existing=self._skip_existing.isChecked(),
        )
        self.repair_worker.progress.connect(self._on_repair_progress)
        self.repair_worker.result.connect(self._on_repair_result)
        self.repair_worker.finished.connect(self._on_repair_finished)
        self.repair_worker.error.connect(self._on_repair_error)
        self.repair_worker.start()
    
    def _on_repair_progress(self, current, total, filename):
        """Handle repair progress."""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"Repairing {current}/{total}: {filename}")
    
    def _on_repair_result(self, filepath, success, message):
        """Handle individual repair result."""
        self.diagnostic_text.append(message)
    
    def _on_repair_finished(self, successes, failures):
        """Handle repair completion."""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        
        self.diagnostic_text.append(f"\n=== Repair Complete ===")
        self.diagnostic_text.append(f"Successful: {successes}")
        self.diagnostic_text.append(f"Failed: {failures}")
        
        QMessageBox.information(
            self,
            "Repair Complete",
            f"Repaired {successes} files successfully.\n{failures} files failed."
        )
        
        self.progress_label.setText("Repair complete")
        success = failures == 0
        self.finished.emit(success, f"Repaired {successes} files" + (f" ({failures} failed)" if failures else ""), successes)
    
    def _on_repair_error(self, error_msg):
        """Handle repair error."""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        QMessageBox.critical(self, "Error", f"Repair failed: {error_msg}")
        self.progress_label.setText("Repair failed")
        self.error.emit(error_msg)
    
    def _cancel_operation(self):
        """Cancel current operation."""
        if self.diagnostic_worker and self.diagnostic_worker.isRunning():
            self.diagnostic_worker.cancel()
            self.diagnostic_worker.wait()
            self.progress_label.setText("Diagnostic cancelled")
        
        if self.repair_worker and self.repair_worker.isRunning():
            self.repair_worker.cancel()
            self.repair_worker.wait()
            self.progress_label.setText("Repair cancelled")
        
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
    
    def _set_ui_enabled(self, enabled):
        """Enable/disable UI elements."""
        self.select_files_btn.setEnabled(enabled)
        self.select_folder_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.output_dir_btn.setEnabled(enabled)
        self.diagnose_btn.setEnabled(enabled)
        self.repair_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(not enabled)

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
