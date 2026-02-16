"""
Quality Checker UI Panel - PyQt6 Version
Provides UI for image quality analysis with detailed reports
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QTextEdit,
    QGroupBox, QListWidget, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QFont
from pathlib import Path
from typing import List, Optional
import logging
from PIL import Image

from tools.quality_checker import ImageQualityChecker, format_quality_report, QualityLevel

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}


class QualityCheckWorker(QThread):
    """Worker thread for quality checking."""
    progress = pyqtSignal(str)  # message
    result = pyqtSignal(object, str)  # report, filename
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, checker, files):
        super().__init__()
        self.checker = checker
        self.files = files
        self.results = []
    
    def run(self):
        """Execute quality check in background thread."""
        try:
            for i, filepath in enumerate(self.files):
                self.progress.emit(f"Checking {i+1}/{len(self.files)}: {Path(filepath).name}")
                
                report = self.checker.check_image(filepath)
                self.results.append((filepath, report))
                self.result.emit(report, Path(filepath).name)
            
            self.finished.emit(True, f"Checked {len(self.files)} images")
        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            self.finished.emit(False, f"Quality check failed: {str(e)}")


class QualityCheckerPanelQt(QWidget):
    """PyQt6 panel for image quality checking."""
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.checker = ImageQualityChecker()
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
        select_btn = QPushButton("Select Images")
        select_btn.clicked.connect(self._select_files)
        group_layout.addWidget(select_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear Selection")
        clear_btn.clicked.connect(self._clear_files)
        group_layout.addWidget(clear_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_controls(self, layout):
        """Create control buttons."""
        group = QGroupBox("🎯 Actions")
        group_layout = QVBoxLayout()
        
        # Check quality button
        self.check_btn = QPushButton("🔍 Check Quality")
        self.check_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.check_btn.clicked.connect(self._check_quality)
        group_layout.addWidget(self.check_btn)
        
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
    
    def _check_quality(self):
        """Start quality check process."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to check")
            return
        
        # Disable button
        self.check_btn.setEnabled(False)
        self.status_label.setText("Checking...")
        self.report_text.clear()
        
        # Start worker thread
        self.worker_thread = QualityCheckWorker(self.checker, self.selected_files)
        self.worker_thread.progress.connect(self._on_progress)
        self.worker_thread.result.connect(self._on_result)
        self.worker_thread.finished.connect(self._on_finished)
        self.worker_thread.start()
    
    def _on_progress(self, message):
        """Handle progress updates."""
        self.status_label.setText(message)
    
    def _on_result(self, report, filename):
        """Handle individual result."""
        # Add to report text
        report_text = format_quality_report(report)
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
        colors = {
            QualityLevel.EXCELLENT: "#4CAF50",
            QualityLevel.GOOD: "#8BC34A",
            QualityLevel.FAIR: "#FFC107",
            QualityLevel.POOR: "#FF9800",
            QualityLevel.VERY_POOR: "#F44336"
        }
        color = colors.get(report.overall_quality, "gray")
        
        summary = f"""
        <div style='background-color: {color}; color: white; padding: 10px; border-radius: 5px;'>
        <b>Quality:</b> {report.overall_quality.value}<br/>
        <b>Score:</b> {report.quality_score:.1f}/100<br/>
        <b>Resolution:</b> {report.resolution[0]}×{report.resolution[1]}<br/>
        <b>Format:</b> {report.format}
        </div>
        """
        self.summary_label.setText(summary)
    
    def _on_finished(self, success, message):
        """Handle completion."""
        self.check_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(f"✓ {message}")
            self.status_label.setStyleSheet("color: green;")
        else:
            QMessageBox.critical(self, "Error", message)
            self.status_label.setText("✗ Check failed")
            self.status_label.setStyleSheet("color: red;")
