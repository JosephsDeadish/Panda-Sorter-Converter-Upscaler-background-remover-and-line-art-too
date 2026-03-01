from __future__ import annotations
"""
Quality Checker UI Panel - PyQt6 Version
Provides UI for image quality analysis with detailed reports
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QFileDialog, QMessageBox, QTextEdit,
        QGroupBox, QListWidget, QSplitter, QCheckBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QPixmap, QImage, QFont
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    QThread = object
    QSplitter = object
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
    class QFont:
        def __init__(self, *a): pass
    class QPixmap:
        def __init__(self, *a): pass
        def isNull(self): return True
    class QImage:
        def __init__(self, *a): pass
    QCheckBox = object
    QFileDialog = object
    QHBoxLayout = object
    QLabel = object
    QListWidget = object
    QMessageBox = object
    QPushButton = object
    QTextEdit = object
    QVBoxLayout = object
from pathlib import Path
from typing import List, Optional
import logging
try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, OSError, RuntimeError):
    HAS_PIL = False

try:
    from ui import IMAGE_EXTENSIONS
except ImportError:
    IMAGE_EXTENSIONS = frozenset({'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.dds', '.tga', '.gif'})


try:
    from tools.quality_checker import ImageQualityChecker, format_quality_report, QualityLevel, QualityCheckOptions
    _QUALITY_TOOL_AVAILABLE = True
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"quality_checker tool not available: {_e}")
    ImageQualityChecker = None  # type: ignore[assignment,misc]
    format_quality_report = None  # type: ignore[assignment]
    QualityLevel = QualityCheckOptions = None  # type: ignore[assignment]
    _QUALITY_TOOL_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")


class QualityCheckWorker(QThread):
    """Worker thread for quality checking."""
    progress = pyqtSignal(str)  # message
    result = pyqtSignal(object, str)  # report, filename
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, checker, files, options=None):
        super().__init__()
        self.checker = checker
        self.files = files
        self.options = options or QualityCheckOptions()
        self.results = []
    
    def run(self):
        """Execute quality check in background thread."""
        try:
            for i, filepath in enumerate(self.files):
                if self.isInterruptionRequested():
                    self.finished.emit(False, f"Cancelled after checking {i} images")
                    return
                self.progress.emit(f"Checking {i+1}/{len(self.files)}: {Path(filepath).name}")
                
                report = self.checker.check_quality(filepath, self.options)
                self.results.append((filepath, report))
                self.result.emit(report, Path(filepath).name)
            
            self.finished.emit(True, f"Checked {len(self.files)} images")
        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            self.finished.emit(False, f"Quality check failed: {str(e)}")


class QualityCheckerPanelQt(QWidget):
    """PyQt6 panel for image quality checking."""

    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.checker = ImageQualityChecker() if ImageQualityChecker is not None else None
        self.selected_files: List[str] = []
        self.current_report = None
        self.worker_thread = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("🔍 Image Quality Checker")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Analyze image quality with detailed reports")
        subtitle_label.setStyleSheet("color: gray; font-size: 12pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Splitter for left/right sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - File selection and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self._create_file_section(left_layout)
        self._create_controls(left_layout)
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # Right side - Results
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self._create_results_section(right_layout)
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
    
    def _create_file_section(self, layout):
        """Create file selection section."""
        group = QGroupBox("📁 File Selection")
        group_layout = QVBoxLayout()
        
        # Files list
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(150)
        group_layout.addWidget(self.files_list)
        
        # Select button
        btn_layout = QHBoxLayout()

        select_btn = QPushButton("Select Images")
        select_btn.clicked.connect(self._select_files)
        self._set_tooltip(select_btn, 'qc_analyze')
        btn_layout.addWidget(select_btn)

        add_folder_btn = QPushButton("📂 Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        self._set_tooltip(add_folder_btn, "Add all images from a folder to the selection")
        btn_layout.addWidget(add_folder_btn)

        group_layout.addLayout(btn_layout)

        # Recursive and clear row
        sub_layout = QHBoxLayout()
        self.recursive_cb = QCheckBox("Process subfolders")
        self.recursive_cb.setChecked(False)
        self._set_tooltip(self.recursive_cb, "When adding a folder, also include images in sub-folders")
        sub_layout.addWidget(self.recursive_cb)
        sub_layout.addStretch()

        # Clear button
        clear_btn = QPushButton("Clear Selection")
        clear_btn.clicked.connect(self._clear_files)
        self._set_tooltip(clear_btn, "Clear the selected images list")
        sub_layout.addWidget(clear_btn)
        group_layout.addLayout(sub_layout)
        
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
        
        # Check options
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Quality Checks:"))
        
        self.check_resolution_cb = QCheckBox("📏 Resolution")
        self.check_resolution_cb.setChecked(True)
        options_layout.addWidget(self.check_resolution_cb)
        self._set_tooltip(self.check_resolution_cb, "Analyze image resolution and dimensions")
        
        self.check_compression_cb = QCheckBox("📦 Compression")
        self.check_compression_cb.setChecked(True)
        options_layout.addWidget(self.check_compression_cb)
        self._set_tooltip(self.check_compression_cb, "Detect compression artifacts and quality")
        
        self.check_dpi_cb = QCheckBox("🖨️ DPI")
        self.check_dpi_cb.setChecked(True)
        options_layout.addWidget(self.check_dpi_cb)
        self._set_tooltip(self.check_dpi_cb, 'qc_dpi')
        
        options_layout.addStretch()
        group_layout.addLayout(options_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_controls(self, layout):
        """Create control buttons."""
        group = QGroupBox("🎯 Actions")
        group_layout = QVBoxLayout()
        
        # Check quality button
        check_row = QHBoxLayout()
        self.check_btn = QPushButton("🔍 Check Quality")
        self.check_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.check_btn.clicked.connect(self._check_quality)
        check_row.addWidget(self.check_btn)
        self._set_tooltip(self.check_btn, 'qc_analyze')

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self.cancel_btn.clicked.connect(self._cancel_check)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self._set_tooltip(self.cancel_btn, 'stop_button')
        check_row.addWidget(self.cancel_btn)
        group_layout.addLayout(check_row)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group_layout.addWidget(self.status_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_results_section(self, layout):
        """Create results section."""
        group = QGroupBox("📊 Quality Report")
        group_layout = QVBoxLayout()
        
        # Summary area
        self.summary_label = QLabel("No results yet")
        self.summary_label.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        self.summary_label.setWordWrap(True)
        group_layout.addWidget(self.summary_label)
        
        # Detailed report area
        report_label = QLabel("Detailed Report:")
        group_layout.addWidget(report_label)
        
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Courier", 9))
        group_layout.addWidget(self.report_text)
        self._set_tooltip(self.report_text, 'qc_results')
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
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
            self.files_list.clear()
            for f in files:
                self.files_list.addItem(Path(f).name)
            self.status_label.setText(f"{len(files)} files selected")
            self.status_label.setStyleSheet("color: green;")
    
    def _clear_files(self):
        """Clear file selection."""
        self.selected_files = []
        self.files_list.clear()
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: gray;")

    def _add_folder(self):
        """Add all images from a folder (optionally recursive) to the selection."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        recursive = hasattr(self, 'recursive_cb') and self.recursive_cb.isChecked()
        folder_path = Path(folder)
        new_files = []
        pattern = '**/*' if recursive else '*'
        for ext in IMAGE_EXTENSIONS:
            new_files.extend(folder_path.glob(f'{pattern}{ext}'))
            new_files.extend(folder_path.glob(f'{pattern}{ext.upper()}'))
        new_paths = sorted({str(p) for p in new_files})
        existing = set(self.selected_files)
        added = [p for p in new_paths if p not in existing]
        self.selected_files.extend(added)
        for p in added:
            self.files_list.addItem(Path(p).name)
        count = len(self.selected_files)
        self.status_label.setText(f"{count} file{'s' if count != 1 else ''} selected")
        self.status_label.setStyleSheet("color: green;")
    
    def _check_quality(self):
        """Start quality check process."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to check")
            return
        
        # Create options from checkboxes
        options = QualityCheckOptions(
            check_resolution=self.check_resolution_cb.isChecked(),
            check_compression=self.check_compression_cb.isChecked(),
            check_dpi=self.check_dpi_cb.isChecked(),
            check_sharpness=True,  # Always check sharpness
            check_noise=True,  # Always check noise
            target_dpi=72.0
        )
        
        # Disable check button; show cancel button
        self.check_btn.setEnabled(False)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setEnabled(True)
            self.cancel_btn.setVisible(True)
        self.status_label.setText("Checking...")
        self.report_text.clear()
        
        # Start worker thread with options
        self.worker_thread = QualityCheckWorker(self.checker, self.selected_files, options)
        self.worker_thread.progress.connect(self._on_progress)
        self.worker_thread.result.connect(self._on_result)
        self.worker_thread.finished.connect(self._on_finished)
        self.worker_thread.start()

    def _cancel_check(self):
        """Cancel the running quality-check operation."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            if hasattr(self, 'cancel_btn'):
                self.cancel_btn.setEnabled(False)
            self.status_label.setText("Cancelling…")
    
    def _on_progress(self, message):
        """Handle progress updates."""
        self.status_label.setText(message)
    
    def _on_result(self, report, filename):
        """Handle individual result."""
        # Add to report text
        if format_quality_report is not None:
            report_text = format_quality_report(report)
        else:
            ql = getattr(report, 'quality_level', None) or getattr(report, 'overall_quality', '?')
            ql_val = ql.value if hasattr(ql, 'value') else str(ql)
            score = getattr(report, 'overall_score', None) or getattr(report, 'quality_score', 0)
            report_text = f"Quality: {ql_val}, Score: {score:.1f}/100"
        self.report_text.append(f"\n{'='*60}\n")
        self.report_text.append(f"File: {filename}\n")
        self.report_text.append(report_text)
        
        # Update summary
        self._update_summary(report)
    
    def _update_summary(self, report):
        """Update summary label with report."""
        if not report:
            return
        
        # Get quality level color
        # Use correct field names from QualityReport dataclass:
        # quality_level (not overall_quality), overall_score (not quality_score),
        # width/height (not resolution tuple).  Fall back gracefully if old field
        # names somehow appear (e.g. future refactor).
        ql = (getattr(report, 'quality_level', None)
              or getattr(report, 'overall_quality', None))
        score = (getattr(report, 'overall_score', None)
                 or getattr(report, 'quality_score', 0) or 0)
        width  = getattr(report, 'width',  None) or (getattr(report, 'resolution', (0, 0))[0])
        height = getattr(report, 'height', None) or (getattr(report, 'resolution', (0, 0))[1])
        fmt    = getattr(report, 'format', '?')
        if QualityLevel is not None:
            colors = {
                QualityLevel.EXCELLENT:    "#4CAF50",
                QualityLevel.GOOD:         "#8BC34A",
                QualityLevel.FAIR:         "#FFC107",
                QualityLevel.POOR:         "#FF9800",
                getattr(QualityLevel, 'UNACCEPTABLE', None): "#F44336",
                getattr(QualityLevel, 'VERY_POOR',    None): "#F44336",
            }
        else:
            colors = {}
        color = colors.get(ql, "gray")
        ql_str = ql.value if hasattr(ql, 'value') else str(ql) if ql else '?'
        summary = f"""
        <div style='background-color: {color}; color: white; padding: 10px; border-radius: 5px;'>
        <b>Quality:</b> {ql_str}<br/>
        <b>Score:</b> {score:.1f}/100<br/>
        <b>Resolution:</b> {width}×{height}<br/>
        <b>Format:</b> {fmt}
        </div>
        """
        self.summary_label.setText(summary)
    
    def _on_finished(self, success, message):
        """Handle completion."""
        self.check_btn.setEnabled(True)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setVisible(False)
        
        if success:
            self.status_label.setText(f"✓ {message}")
            self.status_label.setStyleSheet("color: green;")
        else:
            QMessageBox.critical(self, "Error", message)
            self.status_label.setText("✗ Check failed")
            self.status_label.setStyleSheet("color: red;")
        self.finished.emit(success, message)

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
