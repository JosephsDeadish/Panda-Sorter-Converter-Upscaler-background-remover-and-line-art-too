"""
Color Correction Panel UI - PyQt6 Version

Pure PyQt6 implementation with Qt timer integration.
Uses Qt signals/slots for threading and UI updates.
"""

import logging
from pathlib import Path
from typing import Optional, List
import tempfile
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSlider, QSpinBox, QFileDialog,
    QMessageBox, QProgressBar, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except ImportError:
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")

try:
    from tools.color_corrector import ColorCorrector
    COLOR_CORRECTOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Color corrector not available: {e}")
    COLOR_CORRECTOR_AVAILABLE = False

# Try to import comparison slider
try:
    from ui.live_preview_slider_qt import ComparisonSliderWidget
    SLIDER_AVAILABLE = True
except ImportError:
    try:
        from live_preview_slider_qt import ComparisonSliderWidget
        SLIDER_AVAILABLE = True
    except ImportError:
        SLIDER_AVAILABLE = False
        ComparisonSliderWidget = None


class ColorCorrectionWorker(QThread):
    """Worker thread for color correction processing."""
    
    progress_updated = pyqtSignal(int, str)  # progress, status
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, corrector, input_files, output_dir, settings):
        super().__init__()
        self.corrector = corrector
        self.input_files = input_files
        self.output_dir = output_dir
        self.settings = settings
        self._is_cancelled = False
    
    def run(self):
        """Run color correction in background thread."""
        try:
            total = len(self.input_files)
            for i, file_path in enumerate(self.input_files):
                if self._is_cancelled:
                    self.finished.emit(False, "Cancelled")
                    return
                
                # Update progress
                progress = int((i / total) * 100)
                self.progress_updated.emit(progress, f"Processing {file_path.name}...")
                
                # Process file
                output_path = Path(self.output_dir) / file_path.name
                self.corrector.correct_file(
                    str(file_path),
                    str(output_path),
                    **self.settings
                )
            
            self.finished.emit(True, f"✅ Corrected {total} images successfully!")
        
        except Exception as e:
            logger.error(f"Color correction failed: {e}")
            self.finished.emit(False, f"❌ Error: {str(e)}")
    
    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True


class ColorCorrectionPanelQt(QWidget):
    """PyQt6 panel for color correction and enhancement."""
    
    def __init__(self, parent=None, unlockables_system=None, tooltip_manager=None):
        super().__init__(parent)
        
        if not COLOR_CORRECTOR_AVAILABLE:
            self._show_unavailable()
            return
        
        self.unlockables_system = unlockables_system
        self.tooltip_manager = tooltip_manager
        self.corrector = ColorCorrector()
        self.input_files = []
        self.output_dir = ""
        self.current_lut = None
        self.worker = None
        self.preview_file = None  # Current file for preview
        
        self._create_ui()
    
    def _show_unavailable(self):
        """Show message when color corrector is not available."""
        layout = QVBoxLayout(self)
        label = QLabel(
            "⚠️ Color Correction Tool Unavailable\n\n"
            "Required dependencies not installed."
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(14)
        label.setFont(font)
        layout.addWidget(label)
    
    def _create_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # Title
        title = QLabel("🎨 Color Correction & Enhancement")
        font = title.font()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)
        container_layout.addWidget(title)
        container_layout.addSpacing(20)
        
        # File selection section
        self._create_file_section(container_layout)
        
        # Adjustment controls section
        self._create_controls_section(container_layout)
        
        # Live Preview section
        if SLIDER_AVAILABLE:
            self._create_preview_section(container_layout)
        
        # Actions section
        self._create_actions_section(container_layout)
        
        container_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _create_file_section(self, layout):
        """Create file selection controls."""
        group = QGroupBox("📁 File Selection")
        group_layout = QVBoxLayout()
        
        # Input files
        input_layout = QHBoxLayout()
        self.input_label = QLabel("No files selected")
        input_layout.addWidget(self.input_label, 1)
        
        self.select_btn = QPushButton("Select Images...")
        self.select_btn.clicked.connect(self._select_files)
        self._set_tooltip(self.select_btn, "Select image files to apply color correction")
        input_layout.addWidget(self.select_btn)
        
        group_layout.addLayout(input_layout)
        
        # Output directory
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Output: Not set")
        output_layout.addWidget(self.output_label, 1)
        
        self.output_btn = QPushButton("Set Output...")
        self.output_btn.clicked.connect(self._select_output)
        self._set_tooltip(self.output_btn, "Choose where to save corrected images")
        output_layout.addWidget(self.output_btn)
        
        group_layout.addLayout(output_layout)
        
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
    
    def _create_controls_section(self, layout):
        """Create adjustment controls."""
        group = QGroupBox("⚙️ Adjustments")
        group_layout = QVBoxLayout()
        
        # Brightness
        self.brightness_slider = self._create_slider(
            group_layout, "Brightness", -100, 100, 0, "Adjust image brightness"
        )
        
        # Contrast
        self.contrast_slider = self._create_slider(
            group_layout, "Contrast", -100, 100, 0, "Adjust image contrast"
        )
        
        # Saturation
        self.saturation_slider = self._create_slider(
            group_layout, "Saturation", -100, 100, 0, "Adjust color saturation"
        )
        
        # Sharpness
        self.sharpness_slider = self._create_slider(
            group_layout, "Sharpness", 0, 200, 100, "Adjust image sharpness"
        )
        
        # LUT selection
        lut_layout = QHBoxLayout()
        lut_layout.addWidget(QLabel("LUT:"))
        self.lut_combo = QComboBox()
        self.lut_combo.addItems(["None", "Warm", "Cool", "Cinematic", "Vintage"])
        self._set_tooltip(self.lut_combo, "Apply color lookup table for stylized color grading")
        lut_layout.addWidget(self.lut_combo, 1)
        group_layout.addLayout(lut_layout)
        
        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_controls)
        self._set_tooltip(reset_btn, "Reset all adjustments to default values")
        group_layout.addWidget(reset_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_slider(self, layout, label, min_val, max_val, default, tooltip=""):
        """Create a labeled slider with value display."""
        row = QHBoxLayout()
        
        label_widget = QLabel(f"{label}:")
        label_widget.setMinimumWidth(80)
        row.addWidget(label_widget)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(default)
        if tooltip:
            self._set_tooltip(slider, tooltip)
        row.addWidget(slider, 1)
        
        value_label = QLabel(str(default))
        value_label.setMinimumWidth(40)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(value_label)
        
        slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
        slider.valueChanged.connect(self._update_preview)
        
        layout.addLayout(row)
        return slider
    
    def _create_actions_section(self, layout):
        """Create action buttons and progress display."""
        group = QGroupBox("🚀 Actions")
        group_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        group_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        group_layout.addWidget(self.status_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("🎨 Apply Color Correction")
        self.process_btn.clicked.connect(self._start_processing)
        self.process_btn.setEnabled(False)
        self._set_tooltip(self.process_btn, "Apply color corrections to all selected images")
        btn_layout.addWidget(self.process_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_processing)
        self.cancel_btn.setEnabled(False)
        self._set_tooltip(self.cancel_btn, "Cancel current processing")
        btn_layout.addWidget(self.cancel_btn)
        
        group_layout.addLayout(btn_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_preview_section(self, layout):
        """Create live preview section with comparison slider."""
        group = QGroupBox("👁️ Live Preview (Before/After)")
        group_layout = QVBoxLayout()
        
        # File selector for preview
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Preview file:"))
        self.preview_file_combo = QComboBox()
        self.preview_file_combo.currentTextChanged.connect(self._load_preview_file)
        self._set_tooltip(self.preview_file_combo, "Select which file to preview")
        file_layout.addWidget(self.preview_file_combo, 1)
        group_layout.addLayout(file_layout)
        
        # Comparison mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Comparison:"))
        self.comparison_mode_combo = QComboBox()
        self.comparison_mode_combo.addItems(["Slider", "Toggle", "Overlay"])
        self.comparison_mode_combo.currentTextChanged.connect(self._on_comparison_mode_changed)
        self._set_tooltip(self.comparison_mode_combo, "Choose comparison mode")
        mode_layout.addWidget(self.comparison_mode_combo)
        mode_layout.addStretch()
        group_layout.addLayout(mode_layout)
        
        # Comparison slider widget
        self.preview_widget = ComparisonSliderWidget()
        self.preview_widget.setMinimumHeight(300)
        self._set_tooltip(self.preview_widget, "Drag slider to compare before/after color correction")
        group_layout.addWidget(self.preview_widget)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _select_files(self):
        """Select input files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)"
        )
        
        if files:
            self.input_files = [Path(f) for f in files]
            self.input_label.setText(f"Selected: {len(self.input_files)} files")
            
            # Update preview file combo
            if SLIDER_AVAILABLE and hasattr(self, 'preview_file_combo'):
                self.preview_file_combo.clear()
                for f in self.input_files:
                    self.preview_file_combo.addItem(f.name, str(f))
                if self.input_files:
                    self._load_preview_file(self.input_files[0].name)
            
            self._update_ui_state()
    
    def _select_output(self):
        """Select output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )
        
        if directory:
            self.output_dir = directory
            self.output_label.setText(f"Output: {directory}")
            self._update_ui_state()
    
    def _update_ui_state(self):
        """Update button states based on current state."""
        can_process = (
            len(self.input_files) > 0 and
            self.output_dir and
            self.worker is None
        )
        self.process_btn.setEnabled(can_process)
    
    def _reset_controls(self):
        """Reset all controls to defaults."""
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.saturation_slider.setValue(0)
        self.sharpness_slider.setValue(100)
        self.lut_combo.setCurrentIndex(0)
    
    def _start_processing(self):
        """Start color correction processing."""
        if self.worker is not None:
            return
        
        # Get settings from UI
        settings = {
            'brightness': self.brightness_slider.value(),
            'contrast': self.contrast_slider.value(),
            'saturation': self.saturation_slider.value(),
            'sharpness': self.sharpness_slider.value(),
            'lut': self.lut_combo.currentText() if self.lut_combo.currentIndex() > 0 else None
        }
        
        # Create and start worker
        self.worker = ColorCorrectionWorker(
            self.corrector,
            self.input_files,
            self.output_dir,
            settings
        )
        
        # Connect signals
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        
        # Update UI
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.process_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("Starting color correction...")
        
        # Start processing
        self.worker.start()
    
    def _cancel_processing(self):
        """Cancel current processing."""
        if self.worker:
            self.worker.cancel()
            self.status_label.setText("Cancelling...")
            self.cancel_btn.setEnabled(False)
    
    def _on_progress(self, progress, status):
        """Handle progress updates from worker thread."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def _on_finished(self, success, message):
        """Handle completion from worker thread."""
        # Clean up worker
        if self.worker:
            self.worker.wait()
            self.worker = None
        
        # Update UI
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        self.process_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        # Show message
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Error", message)
    
    def cleanup(self):
        """Clean up resources."""
        if self.worker:
            self.worker.cancel()
            self.worker.wait()
            self.worker = None
    
    def _load_preview_file(self, filename):
        """Load a file for preview."""
        if not SLIDER_AVAILABLE or not hasattr(self, 'preview_widget'):
            return
        
        # Find the full path for this filename
        for f in self.input_files:
            if f.name == filename:
                self.preview_file = f
                pixmap = QPixmap(str(f))
                self.preview_widget.set_before_image(pixmap)
                # Trigger preview update
                self._update_preview()
                break
    
    def _update_preview(self):
        """Update the preview with current adjustments."""
        if not SLIDER_AVAILABLE or not hasattr(self, 'preview_widget'):
            return
        if not self.preview_file:
            return
        
        try:
            # Load original image
            img = Image.open(str(self.preview_file))
            
            # Get current slider values
            brightness = self.brightness_slider.value() / 100.0  # -1.0 to 1.0
            contrast = self.contrast_slider.value() / 100.0
            saturation = self.saturation_slider.value() / 100.0
            sharpness = self.sharpness_slider.value() / 100.0  # 0.0 to 2.0
            
            # Apply adjustments
            if brightness != 0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.0 + brightness)
            
            if contrast != 0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.0 + contrast)
            
            if saturation != 0:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.0 + saturation)
            
            if sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(sharpness)
            
            # Convert PIL image to QPixmap
            # Use temp file and clean it up properly
            tmp_fd, tmp_path = tempfile.mkstemp(suffix='.png')
            try:
                os.close(tmp_fd)  # Close file descriptor
                img.save(tmp_path, 'PNG')
                pixmap = QPixmap(tmp_path)
                self.preview_widget.set_after_image(pixmap)
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass  # Ignore cleanup errors
                
        except Exception as e:
            logger.error(f"Preview update failed: {e}")
    
    def _on_comparison_mode_changed(self, mode_text):
        """Handle comparison mode change."""
        if not SLIDER_AVAILABLE or not hasattr(self, 'preview_widget'):
            return
        
        mode_map = {
            "Slider": "slider",
            "Toggle": "toggle",
            "Overlay": "overlay"
        }
        self.preview_widget.set_mode(mode_map.get(mode_text, "slider"))
    
    def _set_tooltip(self, widget, text):
        """Set tooltip on a widget using tooltip manager if available."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'set_tooltip'):
            self.tooltip_manager.set_tooltip(widget, text)
        else:
            widget.setToolTip(text)
