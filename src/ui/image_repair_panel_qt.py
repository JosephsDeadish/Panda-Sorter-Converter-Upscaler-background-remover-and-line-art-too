"""
Image Repair Panel - PyQt6 Version
UI for repairing corrupted PNG and JPEG files.
"""

import os
import logging
from typing import List, Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QProgressBar,
    QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

try:
    from tools.image_repairer import ImageRepairer, CorruptionType, RepairResult
    REPAIRER_AVAILABLE = True
except ImportError:
    ImageRepairer = None
    CorruptionType = None
    RepairResult = None
    REPAIRER_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except ImportError:
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
                result = self.repairer.diagnose(filepath)
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
    
    def __init__(self, repairer, files, output_dir):
        super().__init__()
        self.repairer = repairer
        self.files = files
        self.output_dir = output_dir
        self._should_cancel = False
    
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
                    result = self.repairer.repair(filepath, self.output_dir)
                    if result.success:
                        successes += 1
                        self.result.emit(filepath, True, f"✓ {filename}: {result.message}")
                    else:
                        failures += 1
                        self.result.emit(filepath, False, f"✗ {filename}: {result.message}")
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
        btn_layout.addWidget(self.select_files_btn)
        
        self.select_folder_btn = QPushButton("Select Folder")
        self.select_folder_btn.clicked.connect(self._select_folder)
        btn_layout.addWidget(self.select_folder_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_files)
        btn_layout.addWidget(self.clear_btn)
        
        group_layout.addLayout(btn_layout)
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
        group_layout.addWidget(self.output_dir_btn)
        
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
    
    def _create_diagnostic_section(self, layout):
        """Create diagnostic results section."""
        group = QGroupBox("🔍 Diagnostic Results")
        group_layout = QVBoxLayout()
        
        self.diagnostic_text = QTextEdit()
        self.diagnostic_text.setReadOnly(True)
        self.diagnostic_text.setMinimumHeight(200)
        self.diagnostic_text.setPlaceholderText("Run diagnostics to see corruption analysis...")
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
        
        self.repair_btn = QPushButton("🔧 Repair Files")
        self.repair_btn.setStyleSheet("background-color: green; color: white; padding: 8px;")
        self.repair_btn.clicked.connect(self._repair_files)
        btn_layout.addWidget(self.repair_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_operation)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _select_files(self):
        """Select image files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",
            "Image files (*.png *.jpg *.jpeg);;PNG files (*.png);;JPEG files (*.jpg *.jpeg);;All files (*.*)"
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
            # Find all image files in folder
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        filepath = os.path.join(root, file)
                        self.selected_files.append(filepath)
            
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
                self.diagnostic_text.append(f"   Details: {result.message}\n")
            else:
                self.diagnostic_text.append(f"✓ {filename}")
                self.diagnostic_text.append(f"   Status: OK\n")
        
        self.progress_label.setText("Diagnostic complete")
    
    def _on_diagnostic_error(self, error_msg):
        """Handle diagnostic error."""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        QMessageBox.critical(self, "Error", f"Diagnostic failed: {error_msg}")
        self.progress_label.setText("Diagnostic failed")
    
    def _repair_files(self):
        """Repair selected files."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to repair.")
            return
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm Repair",
            f"Repair {len(self.selected_files)} files?\n\nRepaired files will be saved with '_repaired' suffix.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.diagnostic_text.clear()
        self.diagnostic_text.append("Starting repair...\n")
        
        # Disable buttons
        self._set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.selected_files))
        self.progress_bar.setValue(0)
        
        # Start repair worker
        self.repair_worker = RepairWorker(self.repairer, self.selected_files, self.output_dir)
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
    
    def _on_repair_error(self, error_msg):
        """Handle repair error."""
        self.progress_bar.setVisible(False)
        self._set_ui_enabled(True)
        QMessageBox.critical(self, "Error", f"Repair failed: {error_msg}")
        self.progress_label.setText("Repair failed")
    
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

    def _set_tooltip(self, widget, text):
        """Set tooltip on a widget using tooltip manager if available."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'set_tooltip'):
            self.tooltip_manager.set_tooltip(widget, text)
        else:
            widget.setToolTip(text)
