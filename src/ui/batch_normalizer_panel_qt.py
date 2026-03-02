"""
Batch Normalizer UI Panel - PyQt6 Version
Provides UI for batch format normalization with live preview
"""


from __future__ import annotations
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
        QComboBox, QSpinBox, QCheckBox, QLineEdit, QGroupBox, QTextEdit
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QPixmap, QImage
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
    class QPixmap:
        def __init__(self, *a): pass
        def isNull(self): return True
    class QImage:
        def __init__(self, *a): pass
    class QTimer:
        def __init__(self, *a): pass
        def start(self, *a): pass
        def stop(self): pass
        timeout = property(lambda self: type("S", (), {"connect": lambda s,f: None, "emit": lambda s: None})())
    QCheckBox = object
    QComboBox = object
    QFileDialog = object
    QHBoxLayout = object
    QLabel = object
    QLineEdit = object
    QMessageBox = object
    QProgressBar = object
    QPushButton = object
    QSpinBox = object
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
    IMAGE_EXTENSIONS = frozenset({'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.dds', '.tga', '.gif', '.avif', '.qoi', '.apng', '.jfif', '.ico', '.icns'})


try:
    from tools.batch_normalizer import (
        BatchFormatNormalizer, NormalizationSettings,
        PaddingMode, ResizeMode, OutputFormat, NamingPattern
    )
    _NORMALIZER_TOOL_AVAILABLE = True
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"batch_normalizer tool not available: {_e}")
    BatchFormatNormalizer = None  # type: ignore[assignment,misc]
    NormalizationSettings = None  # type: ignore[assignment,misc]
    PaddingMode = ResizeMode = OutputFormat = NamingPattern = None  # type: ignore[assignment]
    _NORMALIZER_TOOL_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")


class NormalizationWorker(QThread):
    """Worker thread for batch normalization."""
    progress = pyqtSignal(float, str)  # progress, message
    finished = pyqtSignal(bool, str, int)  # success, message, files_processed
    
    def __init__(self, normalizer, files, output_dir, settings):
        super().__init__()
        self.normalizer = normalizer
        self.files = files
        self.output_dir = output_dir
        self.settings = settings
    
    def run(self):
        """Execute normalization in background thread."""
        try:
            def progress_callback(current, total, filename):
                if self.isInterruptionRequested():
                    raise InterruptedError("Cancelled by user")
                progress = (current / total) * 100
                self.progress.emit(progress, f"Processing ({current}/{total}): {filename}")
            
            self.normalizer.normalize_batch(
                self.files,
                self.output_dir,
                self.settings,
                progress_callback=progress_callback
            )
            
            self.progress.emit(100.0, "Done")
            self.finished.emit(True, f"Successfully normalized {len(self.files)} images", len(self.files))
        except InterruptedError as e:
            self.finished.emit(False, str(e), 0)
        except Exception as e:
            self.finished.emit(False, f"Normalization failed: {str(e)}", 0)


class BatchNormalizerPanelQt(QWidget):
    """PyQt6 panel for batch format normalization."""

    finished = pyqtSignal(bool, str, int)  # success, message, files_processed
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        
        self.tooltip_manager = tooltip_manager
        self.normalizer = BatchFormatNormalizer() if BatchFormatNormalizer is not None else None
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.worker_thread = None
        self.preview_pixmap = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("📏 Batch Format Normalizer")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Resize, pad, and normalize images to consistent format")
        subtitle_label.setStyleSheet("color: gray; font-size: 12pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Main container with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        main_layout = QHBoxLayout(container)
        
        # Left side - Settings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(5)
        
        self._create_file_selection(left_layout)
        self._create_size_settings(left_layout)
        self._create_format_settings(left_layout)
        self._create_naming_settings(left_layout)
        self._create_action_buttons(left_layout)
        
        left_layout.addStretch()
        main_layout.addWidget(left_widget, 1)
        
        # Right side - Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self._create_preview_section(right_layout)
        main_layout.addWidget(right_widget, 1)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _create_file_selection(self, layout):
        """Create file selection section."""
        group = QGroupBox("📁 File Selection")
        group_layout = QVBoxLayout()
        
        # Selected files label
        self.files_label = QLabel("No files selected")
        self.files_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.files_label)
        
        # Select files button
        btn_row = QHBoxLayout()

        select_btn = QPushButton("Select Images")
        select_btn.clicked.connect(self._select_files)
        btn_row.addWidget(select_btn)
        self._set_tooltip(select_btn, "Select image files to normalize")

        add_folder_btn = QPushButton("📂 Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        btn_row.addWidget(add_folder_btn)
        self._set_tooltip(add_folder_btn, "Add all images from a folder to the selection")

        clear_btn = QPushButton("✖ Clear")
        clear_btn.clicked.connect(self._clear_files)
        clear_btn.setFixedWidth(65)
        btn_row.addWidget(clear_btn)
        self._set_tooltip(clear_btn, "Remove all selected files from the list")

        group_layout.addLayout(btn_row)

        # Recursive checkbox
        self.recursive_cb = QCheckBox("Process subfolders")
        self.recursive_cb.setChecked(False)
        self._set_tooltip(self.recursive_cb, "When adding a folder, also include images in sub-folders")
        group_layout.addWidget(self.recursive_cb)
        
        # Output directory
        output_label = QLabel("Output Directory:")
        group_layout.addWidget(output_label)
        
        self.output_label = QLabel("Not set")
        self.output_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.output_label)
        
        output_btn = QPushButton("Set Output Directory")
        output_btn.clicked.connect(self._select_output)
        group_layout.addWidget(output_btn)
        self._set_tooltip(output_btn, "Choose the folder where normalised images will be saved")

        self._skip_existing = QCheckBox("Skip if output file already exists")
        self._skip_existing.setChecked(False)
        self._set_tooltip(self._skip_existing, "When checked, files are not re-processed if the output already exists")
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
        
        # Processing options
        options_layout = QHBoxLayout()
        
        self.make_square_cb = QCheckBox("⬛ Make Square")
        self.make_square_cb.setChecked(True)
        options_layout.addWidget(self.make_square_cb)
        self._set_tooltip(self.make_square_cb, "Force output images to be square (width = height)")
        
        self.preserve_alpha_cb = QCheckBox("🎭 Preserve Alpha")
        self.preserve_alpha_cb.setChecked(True)
        options_layout.addWidget(self.preserve_alpha_cb)
        self._set_tooltip(self.preserve_alpha_cb, "Preserve alpha channel (transparency) in output images")
        
        self.strip_metadata_cb = QCheckBox("🧹 Strip Metadata")
        self.strip_metadata_cb.setChecked(False)
        options_layout.addWidget(self.strip_metadata_cb)
        self._set_tooltip(self.strip_metadata_cb, "Remove EXIF and other metadata from output images (reduces file size)")
        
        options_layout.addStretch()
        group_layout.addLayout(options_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_size_settings(self, layout):
        """Create size settings section."""
        group = QGroupBox("📐 Size Settings")
        group_layout = QVBoxLayout()
        
        # Target size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Target Size:"))
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 8192)
        self.width_spin.setValue(512)
        size_layout.addWidget(self.width_spin)
        self._set_tooltip(self.width_spin, 'bn_resolution')
        
        size_layout.addWidget(QLabel("×"))
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 8192)
        self.height_spin.setValue(512)
        size_layout.addWidget(self.height_spin)
        self._set_tooltip(self.height_spin, 'bn_resolution')
        
        group_layout.addLayout(size_layout)
        
        # Resize mode
        group_layout.addWidget(QLabel("Resize Mode:"))
        self.resize_combo = QComboBox()
        self.resize_combo.addItems(["Fit (preserve aspect)", "Fill (crop)", "Stretch"])
        group_layout.addWidget(self.resize_combo)
        self._set_tooltip(self.resize_combo, 'bn_resize_mode')
        
        # Padding mode
        group_layout.addWidget(QLabel("Padding Mode:"))
        self.padding_combo = QComboBox()
        self.padding_combo.addItems(["Transparent", "Black", "White", "Blur Edge"])
        group_layout.addWidget(self.padding_combo)
        self._set_tooltip(self.padding_combo, 'bn_padding')
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_format_settings(self, layout):
        """Create format settings section."""
        group = QGroupBox("💾 Format Settings")
        group_layout = QVBoxLayout()
        
        # Output format
        group_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "WebP"])
        group_layout.addWidget(self.format_combo)
        self._set_tooltip(self.format_combo, 'bn_format')
        self._set_tooltip(self.format_combo, 'bn_output_format')
        
        # Quality (for JPEG/WebP)
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        quality_layout.addWidget(self.quality_spin)
        group_layout.addLayout(quality_layout)
        self._set_tooltip(self.quality_spin, 'bn_quality')
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_naming_settings(self, layout):
        """Create naming settings section."""
        group = QGroupBox("🏷️ Naming Settings")
        group_layout = QVBoxLayout()
        
        # Naming pattern
        group_layout.addWidget(QLabel("Naming Pattern:"))
        self.naming_combo = QComboBox()
        self.naming_combo.addItems(["Keep Original", "Sequential", "Custom Prefix"])
        group_layout.addWidget(self.naming_combo)
        
        # Custom prefix (optional)
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Prefix:"))
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText("Optional prefix")
        prefix_layout.addWidget(self.prefix_edit)
        group_layout.addLayout(prefix_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        buttons_layout = QHBoxLayout()
        
        # Normalize button
        self.normalize_btn = QPushButton("🚀 Start Normalization")
        self.normalize_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
        self.normalize_btn.clicked.connect(self._start_normalization)
        buttons_layout.addWidget(self.normalize_btn)
        self._set_tooltip(self.normalize_btn, 'bn_normalize')

        # Cancel button (hidden until normalization starts)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self.cancel_btn.clicked.connect(self._cancel_normalization)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self._set_tooltip(self.cancel_btn, 'stop_button')
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: gray;")
        layout.addWidget(self.progress_label)

        # Activity log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet(
            "background:#0d1117; color:#c9d1d9; font-family:Consolas,monospace; font-size:10px;"
        )
        self.log_text.setPlaceholderText("Normalisation log will appear here…")
        layout.addWidget(self.log_text)
    
    def _create_preview_section(self, layout):
        """Create preview section."""
        group = QGroupBox("👁️ Preview")
        group_layout = QVBoxLayout()
        
        # Preview label
        self.preview_label = QLabel("Select files to see preview")
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
        """Open file dialog to select images."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.tga *.dds *.gif *.avif *.qoi *.apng *.jfif);;All Files (*.*)"
        )
        
        if files:
            self.selected_files = files
            self.files_label.setText(f"{len(files)} files selected")
            self.files_label.setStyleSheet("color: green;")
            self._update_preview()

    def _clear_files(self):
        """Clear the selected files list."""
        self.selected_files = []
        self.files_label.setText("No files selected")
        self.files_label.setStyleSheet("color: gray;")
    
    def _select_output(self):
        """Select output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory"
        )

        if directory:
            self.output_directory = directory
            self.output_label.setText(directory)
            self.output_label.setStyleSheet("color: green;")

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
        count = len(self.selected_files)
        self.files_label.setText(f"{count} file{'s' if count != 1 else ''} selected")
        self.files_label.setStyleSheet("color: green;")
        if added:
            self._update_preview()
    
    def _update_preview(self):
        """Update preview with first selected image."""
        if not self.selected_files:
            return
        
        try:
            # Load first image
            first_file = self.selected_files[0]
            image = Image.open(first_file)
            
            # Resize for preview
            image.thumbnail((400, 400), Image.Resampling.LANCZOS)
            
            # Convert to QPixmap
            data = image.convert("RGBA").tobytes("raw", "RGBA")
            qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            
            self.preview_label.setPixmap(pixmap)
            self.info_label.setText(f"Original: {Image.open(first_file).size[0]}×{Image.open(first_file).size[1]}")
        except Exception as e:
            self.preview_label.setText(f"Error loading preview: {str(e)}")
    
    def _start_normalization(self):
        """Start the normalization process."""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to normalize")
            return
        
        if not self.output_directory:
            QMessageBox.warning(self, "No Output", "Please select an output directory")
            return
        
        # Create settings
        settings = NormalizationSettings(
            target_width=self.width_spin.value(),
            target_height=self.height_spin.value(),
            make_square=self.make_square_cb.isChecked(),
            resize_mode=self._get_resize_mode(),
            padding_mode=self._get_padding_mode(),
            output_format=self._get_output_format(),
            quality=self.quality_spin.value(),
            naming_pattern=self._get_naming_pattern(),
            prefix=self.prefix_edit.text() if self.prefix_edit.text() else None,
            preserve_alpha=self.preserve_alpha_cb.isChecked(),
            strip_metadata=self.strip_metadata_cb.isChecked(),
            skip_existing=self._skip_existing.isChecked(),
        )
        
        # Disable normalize button; show cancel button
        self.normalize_btn.setEnabled(False)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setEnabled(True)
            self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting...")
        
        # Start worker thread
        self.worker_thread = NormalizationWorker(
            self.normalizer,
            self.selected_files,
            self.output_directory,
            settings
        )
        self.worker_thread.progress.connect(self._on_progress)
        self.worker_thread.finished.connect(self._on_finished)
        self.worker_thread.start()

    def _cancel_normalization(self):
        """Cancel the running normalization operation."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            if hasattr(self, 'cancel_btn'):
                self.cancel_btn.setEnabled(False)
            self.progress_label.setText("Cancelling…")
    
    def _on_progress(self, progress, message):
        """Handle progress updates."""
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(message)
        if hasattr(self, 'log_text') and message and message != "Done":
            self.log_text.append(message)

    def _on_finished(self, success, message, files_processed: int = 0):
        """Handle completion."""
        self.progress_bar.setVisible(False)
        self.normalize_btn.setEnabled(True)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setVisible(False)
        if hasattr(self, 'log_text'):
            icon = "✅" if success else "❌"
            self.log_text.append(f"{icon} {message}")
        if success:
            QMessageBox.information(self, "Complete", message)
            self.progress_label.setText("✓ Normalization complete")
        else:
            QMessageBox.critical(self, "Error", message)
            self.progress_label.setText("✗ Normalization failed")
        self.finished.emit(success, message, files_processed)
    
    def _get_resize_mode(self):
        """Get resize mode from combo box."""
        modes = {
            0: ResizeMode.FIT,
            1: ResizeMode.FILL,
            2: ResizeMode.STRETCH
        }
        return modes.get(self.resize_combo.currentIndex(), ResizeMode.FIT)
    
    def _get_padding_mode(self):
        """Get padding mode from combo box."""
        modes = {
            0: PaddingMode.TRANSPARENT,
            1: PaddingMode.BLACK,
            2: PaddingMode.WHITE,
            3: PaddingMode.BLUR_EDGE
        }
        return modes.get(self.padding_combo.currentIndex(), PaddingMode.TRANSPARENT)
    
    def _get_output_format(self):
        """Get output format from combo box."""
        formats = {
            0: OutputFormat.PNG,
            1: OutputFormat.JPEG,
            2: OutputFormat.WEBP
        }
        return formats.get(self.format_combo.currentIndex(), OutputFormat.PNG)
    
    def _get_naming_pattern(self):
        """Get naming pattern from combo box."""
        patterns = {
            0: NamingPattern.KEEP_ORIGINAL,
            1: NamingPattern.SEQUENTIAL,
            2: NamingPattern.CUSTOM_PREFIX
        }
        return patterns.get(self.naming_combo.currentIndex(), NamingPattern.KEEP_ORIGINAL)

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
