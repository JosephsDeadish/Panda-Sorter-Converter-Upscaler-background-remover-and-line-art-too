"""
Alpha Fixer UI Panel - PyQt6 Version
Provides UI for comprehensive alpha channel editing and fixing
"""


from __future__ import annotations
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
        QGroupBox, QComboBox, QSlider, QCheckBox, QSpinBox, QListWidget,
        QSplitter
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QPixmap, QImage
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    QThread = object
    QSplitter = object
    QScrollArea = object
    QGroupBox = object
    def pyqtSignal(*args, **kwargs): return property(lambda self: None)
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
    class QPixmap:
        def __init__(self, *a): pass
        def isNull(self): return True
    class QImage:
        def __init__(self, *a): pass
    QCheckBox = object
    QComboBox = object
    QFileDialog = object
    QHBoxLayout = object
    QLabel = object
    QListWidget = object
    QMessageBox = object
    QProgressBar = object
    QPushButton = object
    QSlider = object
    QSpinBox = object
    QVBoxLayout = object
from pathlib import Path
from typing import List, Optional
import logging
import os
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


from preprocessing.alpha_correction import AlphaCorrector, AlphaCorrectionPresets

logger = logging.getLogger(__name__)

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except ImportError:
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}


class AlphaFixWorker(QThread):
    """Worker thread for alpha fixing."""
    progress = pyqtSignal(float, str)  # progress, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, corrector, files, output_dir, settings):
        super().__init__()
        self.corrector = corrector
        self.files = files
        self.output_dir = output_dir
        self.settings = settings
    
    def run(self):
        """Execute alpha fixing in background thread."""
        try:
            for i, filepath in enumerate(self.files):
                progress = ((i + 1) / len(self.files)) * 100
                self.progress.emit(progress, f"Processing: {Path(filepath).name}")
                
                # Validate file exists and is readable
                if not os.path.exists(filepath):
                    logger.warning(f"File not found, skipping: {filepath}")
                    continue
                if not os.access(filepath, os.R_OK):
                    logger.warning(f"File not readable, skipping: {filepath}")
                    continue
                
                # Process image
                image = Image.open(filepath)
                result = self.corrector.correct_alpha(image, **self.settings)
                
                # Save result
                output_path = Path(self.output_dir) / Path(filepath).name
                result.save(output_path)
            
            self.finished.emit(True, f"Successfully processed {len(self.files)} images")
        except Exception as e:
            logger.error(f"Alpha fixing failed: {e}")
            self.finished.emit(False, f"Processing failed: {str(e)}")


class AlphaFixerPanelQt(QWidget):
    """PyQt6 panel for alpha channel fixing."""

    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.corrector = AlphaCorrector()
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.worker_thread = None
        self.current_image = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("⚡ Alpha Channel Fixer")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Fix, enhance, and correct alpha channels with advanced tools")
        subtitle_label.setStyleSheet("color: gray; font-size: 12pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Splitter for left/right sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Settings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self._create_file_selection(scroll_layout)
        self._create_correction_presets(scroll_layout)
        self._create_defringe_settings(scroll_layout)
        self._create_matte_removal_settings(scroll_layout)
        self._create_alpha_edge_settings(scroll_layout)
        self._create_action_buttons(scroll_layout)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        left_layout.addWidget(scroll)
        
        splitter.addWidget(left_widget)
        
        # Right side - Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self._create_preview_section(right_layout)
        splitter.addWidget(right_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
    
    def _create_file_selection(self, layout):
        """Create file selection section."""
        group = QGroupBox("📁 File Selection")
        group_layout = QVBoxLayout()
        
        # Files list
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(100)
        group_layout.addWidget(self.files_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        select_btn = QPushButton("Select Images")
        select_btn.clicked.connect(self._select_files)
        btn_layout.addWidget(select_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_files)
        btn_layout.addWidget(clear_btn)
        
        group_layout.addLayout(btn_layout)
        
        # Output directory
        self.output_label = QLabel("Output: Not set")
        self.output_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.output_label)
        
        output_btn = QPushButton("Set Output Directory")
        output_btn.clicked.connect(self._select_output)
        group_layout.addWidget(output_btn)
        
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
    
    def _create_correction_presets(self, layout):
        """Create correction presets section."""
        group = QGroupBox("🎨 Correction Presets")
        group_layout = QVBoxLayout()
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Standard",
            "Aggressive",
            "Conservative",
            "Photo Cutout",
            "Game Asset",
            "Custom"
        ])
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        group_layout.addWidget(self.preset_combo)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_defringe_settings(self, layout):
        """Create de-fringing settings section."""
        group = QGroupBox("🧹 De-fringing")
        group_layout = QVBoxLayout()
        
        self.defringe_check = QCheckBox("Enable De-fringing")
        self.defringe_check.setChecked(True)
        group_layout.addWidget(self.defringe_check)
        
        # Threshold slider
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Threshold:"))
        self.defringe_slider = QSlider(Qt.Orientation.Horizontal)
        self.defringe_slider.setRange(1, 100)
        self.defringe_slider.setValue(30)
        threshold_layout.addWidget(self.defringe_slider)
        self.defringe_value = QLabel("30")
        threshold_layout.addWidget(self.defringe_value)
        self.defringe_slider.valueChanged.connect(
            lambda v: self.defringe_value.setText(str(v))
        )
        group_layout.addLayout(threshold_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_matte_removal_settings(self, layout):
        """Create matte removal settings section."""
        group = QGroupBox("🎭 Matte Removal")
        group_layout = QVBoxLayout()
        
        self.matte_check = QCheckBox("Enable Matte Removal")
        self.matte_check.setChecked(False)
        group_layout.addWidget(self.matte_check)
        
        # Background color combo
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background:"))
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["Black", "White", "Auto-detect"])
        bg_layout.addWidget(self.bg_combo)
        group_layout.addLayout(bg_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_alpha_edge_settings(self, layout):
        """Create alpha edge settings section."""
        group = QGroupBox("✨ Alpha Edge Enhancement")
        group_layout = QVBoxLayout()
        
        self.edge_check = QCheckBox("Enhance Alpha Edges")
        self.edge_check.setChecked(False)
        group_layout.addWidget(self.edge_check)
        
        # Smoothing amount
        smooth_layout = QHBoxLayout()
        smooth_layout.addWidget(QLabel("Smoothing:"))
        self.smooth_spin = QSpinBox()
        self.smooth_spin.setRange(0, 10)
        self.smooth_spin.setValue(2)
        smooth_layout.addWidget(self.smooth_spin)
        group_layout.addLayout(smooth_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        group = QGroupBox("🚀 Actions")
        group_layout = QVBoxLayout()
        
        # Process button
        self.process_btn = QPushButton("Process Images")
        self.process_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.process_btn.clicked.connect(self._process_images)
        group_layout.addWidget(self.process_btn)
        
        # Preview button
        preview_btn = QPushButton("Preview First Image")
        preview_btn.clicked.connect(self._preview_first)
        group_layout.addWidget(preview_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        group_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.progress_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_preview_section(self, layout):
        """Create preview section."""
        group = QGroupBox("👁️ Preview")
        group_layout = QVBoxLayout()
        
        self.preview_label = QLabel("Select files to preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setStyleSheet("border: 2px dashed gray; background-color: #f0f0f0;")
        group_layout.addWidget(self.preview_label)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.info_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _select_files(self):
        """Select image files."""
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
    
    def _clear_files(self):
        """Clear file selection."""
        self.selected_files = []
        self.files_list.clear()
    
    def _select_output(self):
        """Select output directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_directory = directory
            self.output_label.setText(f"Output: {directory}")
            self.output_label.setStyleSheet("color: green;")
    
    def _on_preset_changed(self, index):
        """Handle preset change."""
        # Update settings based on preset
        presets = {
            0: {"defringe": True, "threshold": 30},  # Standard
            1: {"defringe": True, "threshold": 50},  # Aggressive
            2: {"defringe": True, "threshold": 15},  # Conservative
            3: {"defringe": True, "threshold": 40},  # Photo Cutout
            4: {"defringe": True, "threshold": 35},  # Game Asset
        }
        
        # Get preset settings with bounds checking
        if index < 5:
            settings = presets.get(index, presets[0])  # Use .get() for safety
            self.defringe_slider.setValue(settings["threshold"])
    
    def _preview_first(self):
        """Preview first selected image."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files first")
            return
        
        try:
            image = Image.open(self.selected_files[0])
            image.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            data = image.convert("RGBA").tobytes("raw", "RGBA")
            qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            
            self.preview_label.setPixmap(pixmap)
            self.info_label.setText(f"Preview: {Path(self.selected_files[0]).name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Preview failed: {str(e)}")
    
    def _process_images(self):
        """Process selected images."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to process")
            return
        
        if not self.output_directory:
            QMessageBox.warning(self, "No Output", "Please select output directory")
            return
        
        # Get settings
        settings = {
            "remove_fringes": self.defringe_check.isChecked(),
            "fringe_threshold": self.defringe_slider.value(),
            "remove_matte": self.matte_check.isChecked(),
            "enhance_edges": self.edge_check.isChecked(),
            "edge_smooth": self.smooth_spin.value()
        }
        
        # Disable button
        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start worker
        self.worker_thread = AlphaFixWorker(
            self.corrector,
            self.selected_files,
            self.output_directory,
            settings
        )
        self.worker_thread.progress.connect(self._on_progress)
        self.worker_thread.finished.connect(self._on_finished)
        self.worker_thread.start()
    
    def _on_progress(self, progress, message):
        """Handle progress updates."""
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(message)
    
    def _on_finished(self, success, message):
        """Handle completion."""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Complete", message)
            self.progress_label.setText("✓ Processing complete")
        else:
            QMessageBox.critical(self, "Error", message)
            self.progress_label.setText("✗ Processing failed")
    
    def _set_tooltip(self, widget, tooltip_text_or_id):
        """Set tooltip on widget, using tooltip manager if available."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'set_tooltip'):
            self.tooltip_manager.set_tooltip(widget, tooltip_text_or_id)
        else:
            # Fallback to direct tooltip setting
            widget.setToolTip(str(tooltip_text_or_id))
