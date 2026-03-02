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
except (ImportError, OSError, RuntimeError):
    HAS_PIL = False

try:
    from ui import IMAGE_EXTENSIONS
except ImportError:
    IMAGE_EXTENSIONS = frozenset({'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.dds', '.tga', '.gif', '.avif', '.qoi', '.apng', '.jfif', '.ico', '.icns'})


try:
    from preprocessing.alpha_correction import AlphaCorrector, AlphaCorrectionPresets
    _ALPHA_TOOL_AVAILABLE = True
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"alpha_correction tool not available: {_e}")
    AlphaCorrector = None  # type: ignore[assignment,misc]
    AlphaCorrectionPresets = None  # type: ignore[assignment,misc]
    _ALPHA_TOOL_AVAILABLE = False

logger = logging.getLogger(__name__)

try:
    from ui.live_preview_slider_qt import ComparisonSliderWidget
    _SLIDER_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    try:
        from live_preview_slider_qt import ComparisonSliderWidget  # type: ignore[no-redef]
        _SLIDER_AVAILABLE = True
    except (ImportError, OSError, RuntimeError):
        ComparisonSliderWidget = None  # type: ignore[assignment,misc]
        _SLIDER_AVAILABLE = False

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")


class AlphaFixWorker(QThread):
    """Worker thread for alpha fixing."""
    progress = pyqtSignal(float, str)  # progress, message
    finished = pyqtSignal(bool, str, int)  # success, message, files_processed

    def __init__(self, corrector, files, output_dir, preset_key, skip_existing=False):
        super().__init__()
        self.corrector = corrector
        self.files = files
        self.output_dir = output_dir
        self.preset_key = preset_key
        self.skip_existing = skip_existing

    def run(self):
        """Execute alpha fixing in background thread."""
        try:
            processed = 0
            skipped = 0
            for i, filepath in enumerate(self.files):
                if self.isInterruptionRequested():
                    self.finished.emit(False, f"Cancelled after processing {processed} images", processed)
                    return
                progress = ((i + 1) / len(self.files)) * 100
                self.progress.emit(progress, f"Processing ({i+1}/{len(self.files)}): {Path(filepath).name}")

                if not os.path.exists(filepath):
                    logger.warning(f"File not found, skipping: {filepath}")
                    continue
                if not os.access(filepath, os.R_OK):
                    logger.warning(f"File not readable, skipping: {filepath}")
                    continue

                # Use the higher-level process_image() which handles PIL loading,
                # RGBA conversion, numpy conversion and saving internally.
                output_path = Path(self.output_dir) / Path(filepath).name
                # Guard: never overwrite the source file
                if output_path.resolve() == Path(filepath).resolve():
                    src = Path(filepath)
                    output_path = Path(self.output_dir) / f"{src.stem}_fixed{src.suffix}"
                if self.skip_existing and output_path.exists():
                    skipped += 1
                    logger.debug(f"Skipped (exists): {output_path.name}")
                    continue
                result = self.corrector.process_image(
                    Path(filepath),
                    output_path=output_path,
                    preset=self.preset_key,
                    overwrite=False,
                    backup=False,
                )
                if result.get('success'):
                    processed += 1
                else:
                    logger.warning(f"Skipped {filepath}: {result.get('reason', 'unknown')}")

            parts = [f"Processed {processed} image{'s' if processed != 1 else ''}"]
            if skipped:
                parts.append(f"{skipped} skipped (already existed)")
            self.progress.emit(100.0, "Done")
            self.finished.emit(True, ", ".join(parts), processed)
        except Exception as e:
            logger.error(f"Alpha fixing failed: {e}")
            self.finished.emit(False, f"Processing failed: {str(e)}", 0)


class AlphaFixerPanelQt(QWidget):
    """PyQt6 panel for alpha channel fixing."""

    finished = pyqtSignal(bool, str, int)  # success, message, files_processed

    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)

        self.tooltip_manager = tooltip_manager
        self.corrector = AlphaCorrector() if AlphaCorrector is not None else None
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        self.worker_thread = None
        self.current_image = None
        # Default preset key — set correctly by _on_preset_changed when the combo is built
        self._selected_preset_key: Optional[str] = 'generic_binary'

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
        self._set_tooltip(select_btn, 'alpha_fix_input')

        add_folder_btn = QPushButton("📂 Add Folder")
        add_folder_btn.clicked.connect(self._add_folder)
        btn_layout.addWidget(add_folder_btn)
        self._set_tooltip(add_folder_btn, "Add all images from a folder to the selection")

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_files)
        btn_layout.addWidget(clear_btn)
        self._set_tooltip(clear_btn, "Remove all selected files from the list")
        
        group_layout.addLayout(btn_layout)
        
        # Output directory
        self.output_label = QLabel("Output: Not set")
        self.output_label.setStyleSheet("color: gray;")
        group_layout.addWidget(self.output_label)
        
        output_btn = QPushButton("Set Output Directory")
        output_btn.clicked.connect(self._select_output)
        group_layout.addWidget(output_btn)
        self._set_tooltip(output_btn, 'alpha_fix_output')

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
            self._set_tooltip(self.archive_input_cb, 'alpha_fix_extract_archive')
        archive_layout.addWidget(self.archive_input_cb)
        
        self.archive_output_cb = QCheckBox("📦 Export to Archive")
        if not ARCHIVE_AVAILABLE:
            self.archive_output_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_output_cb.setStyleSheet("color: gray;")
        else:
            self._set_tooltip(self.archive_output_cb, 'output_archive_checkbox')
            self._set_tooltip(self.archive_output_cb, 'alpha_fix_compress_archive')
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

        # Map of display label → backend preset key (None = custom/no-op)
        self._preset_items = [
            # General
            ("Generic Binary (PS1 / GBA / Dreamcast / PC)",  "generic_binary"),
            ("Clean Edges (remove fringing)",                "clean_edges"),
            ("Soft Edges (preserve anti-aliasing)",          "soft_edges"),
            ("Fade Out (normalise gradients)",               "fade_out"),
            ("Dithered (fix dithered transparency)",         "dithered"),
            # Nintendo
            ("Nintendo 64 / DS (RGBA5551 / A3RGB5)",         "nintendo_64"),
            ("GameCube / Wii / Wii U (5-bit, 8 levels)",     "gamecube_wii"),
            ("Nintendo 3DS (4-bit RGBA4444, 16 levels)",     "n3ds_rgba4444"),
            ("GBA Sprite (1-bit palette transparency)",      "gba_sprite"),
            # PlayStation
            ("PS2 Binary",                                   "ps2_binary"),
            ("PS2 Three-Level",                              "ps2_three_level"),
            ("PS2 Four-Level",                               "ps2_four_level"),
            ("PS2 Smooth (preserve gradients)",              "ps2_smooth"),
            ("PS2 UI (sharp cutoff)",                        "ps2_ui"),
            ("PSP Binary",                                   "psp_binary"),
            # Microsoft
            ("Xbox Standard",                                "xbox_standard"),
            # Game elements
            ("Foliage / Leaves / Hair (Sharp Cutout)",       "foliage_sharp"),
            ("Particle / Smoke / Fire (Preserve Gradients)", "particle_fade"),
            # Custom
            ("Custom (use sliders below)",                   None),
        ]

        for label, _key in self._preset_items:
            self.preset_combo.addItem(label)

        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        group_layout.addWidget(self.preset_combo)
        self._set_tooltip(self.preset_combo, 'alpha_fix_preset')

        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_defringe_settings(self, layout):
        """Create de-fringing settings section."""
        group = QGroupBox("🧹 De-fringing")
        group_layout = QVBoxLayout()
        
        self.defringe_check = QCheckBox("Enable De-fringing")
        self.defringe_check.setChecked(True)
        group_layout.addWidget(self.defringe_check)
        self._set_tooltip(self.defringe_check, "Remove colour fringing around transparent edges — eliminates halos from cutouts")
        
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
        self._set_tooltip(self.defringe_slider, "Sensitivity for detecting fringe pixels — higher removes more colour bleed")
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_matte_removal_settings(self, layout):
        """Create matte removal settings section."""
        group = QGroupBox("🎭 Matte Removal")
        group_layout = QVBoxLayout()
        
        self.matte_check = QCheckBox("Enable Matte Removal")
        self.matte_check.setChecked(False)
        group_layout.addWidget(self.matte_check)
        self._set_tooltip(self.matte_check, "Remove solid-colour matte backgrounds left over from compositing or format conversion")
        
        # Background color combo
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background:"))
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["Black", "White", "Auto-detect"])
        bg_layout.addWidget(self.bg_combo)
        group_layout.addLayout(bg_layout)
        self._set_tooltip(self.bg_combo, "Colour of the matte to remove — select the background colour that was used when the image was composited")
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_alpha_edge_settings(self, layout):
        """Create alpha edge settings section."""
        group = QGroupBox("✨ Alpha Edge Enhancement")
        group_layout = QVBoxLayout()
        
        self.edge_check = QCheckBox("Enhance Alpha Edges")
        self.edge_check.setChecked(False)
        group_layout.addWidget(self.edge_check)
        self._set_tooltip(self.edge_check, "Refine and smooth the alpha channel boundary for cleaner cutout edges")
        
        # Smoothing amount
        smooth_layout = QHBoxLayout()
        smooth_layout.addWidget(QLabel("Smoothing:"))
        self.smooth_spin = QSpinBox()
        self.smooth_spin.setRange(0, 10)
        self.smooth_spin.setValue(2)
        smooth_layout.addWidget(self.smooth_spin)
        group_layout.addLayout(smooth_layout)
        self._set_tooltip(self.smooth_spin, "Amount of edge smoothing applied to the alpha boundary (0 = none, 10 = maximum)")
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        group = QGroupBox("🚀 Actions")
        group_layout = QVBoxLayout()
        
        btn_row = QHBoxLayout()

        # Process button
        self.process_btn = QPushButton("Process Images")
        self.process_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.process_btn.clicked.connect(self._process_images)
        btn_row.addWidget(self.process_btn)
        self._set_tooltip(self.process_btn, 'alpha_fix_button')

        # Cancel button (hidden until processing starts)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self.cancel_btn.clicked.connect(self._cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self._set_tooltip(self.cancel_btn, 'stop_button')
        btn_row.addWidget(self.cancel_btn)

        group_layout.addLayout(btn_row)

        # Overwrite originals
        self.overwrite_check = QCheckBox("Overwrite original files")
        self.overwrite_check.setChecked(False)
        self._set_tooltip(self.overwrite_check, 'alpha_fix_overwrite')
        group_layout.addWidget(self.overwrite_check)

        # Process subdirectories
        self.recursive_check = QCheckBox("Process subdirectories")
        self.recursive_check.setChecked(False)
        self._set_tooltip(self.recursive_check, 'alpha_fix_recursive')
        group_layout.addWidget(self.recursive_check)
        
        # Preview button
        preview_btn = QPushButton("Preview First Image")
        preview_btn.clicked.connect(self._preview_first)
        group_layout.addWidget(preview_btn)
        self._set_tooltip(preview_btn, 'alpha_fix_preview')
        
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
        """Create preview section with before/after comparison when available."""
        group = QGroupBox("👁️ Preview")
        group_layout = QVBoxLayout()
        
        if _SLIDER_AVAILABLE and ComparisonSliderWidget is not None:
            self._preview_widget = ComparisonSliderWidget()
            self._preview_widget.setMinimumSize(250, 200)
            group_layout.addWidget(self._preview_widget)
        else:
            self._preview_widget = None
            self.preview_label = QLabel("Select files to preview")
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setMinimumSize(250, 200)
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
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.tga *.dds *.gif *.avif *.qoi *.apng *.jfif);;All Files (*.*)"
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

    def _add_folder(self):
        """Add all images from a folder (optionally recursive) to the selection."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        recursive = hasattr(self, 'recursive_check') and self.recursive_check.isChecked()
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
    
    def _select_output(self):
        """Select output directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_directory = directory
            self.output_label.setText(f"Output: {directory}")
            self.output_label.setStyleSheet("color: green;")
    
    def _on_preset_changed(self, index):
        """Handle preset change — store the selected backend preset key."""
        if not hasattr(self, '_preset_items') or index < 0 or index >= len(self._preset_items):
            return
        _, self._selected_preset_key = self._preset_items[index]
        # Update the defringe slider to a sensible default for each category
        slider_hints = {
            "generic_binary": 30, "clean_edges": 20, "soft_edges": 10,
            "fade_out": 15, "dithered": 40, "nintendo_64": 35,
            "gamecube_wii": 35, "n3ds_rgba4444": 25, "gba_sprite": 30,
            "ps2_binary": 30, "ps2_three_level": 30,
            "ps2_four_level": 30, "ps2_smooth": 15, "ps2_ui": 50,
            "psp_binary": 30, "xbox_standard": 30,
            "foliage_sharp": 50, "particle_fade": 5,
        }
        hint = slider_hints.get(self._selected_preset_key or "", 30)
        self.defringe_slider.setValue(hint)
    
    def _preview_first(self):
        """Preview first selected image — 'before' side of the comparison slider."""
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
            
            if self._preview_widget is not None:
                self._preview_widget.set_before_image(pixmap)
                self._preview_widget.set_after_image(pixmap)
            else:
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

        # Resolve the selected preset key (default to 'generic_binary' if none)
        preset_key = getattr(self, '_selected_preset_key', None) or 'generic_binary'

        # Disable process button; show cancel button
        self.process_btn.setEnabled(False)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setEnabled(True)
            self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Start worker
        self.worker_thread = AlphaFixWorker(
            self.corrector,
            self.selected_files,
            self.output_directory,
            preset_key,
            skip_existing=self._skip_existing.isChecked(),
        )
        self.worker_thread.progress.connect(self._on_progress)
        self.worker_thread.finished.connect(self._on_finished)
        self.worker_thread.start()

    def _cancel_processing(self):
        """Cancel the running alpha-fix operation."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.requestInterruption()
            if hasattr(self, 'cancel_btn'):
                self.cancel_btn.setEnabled(False)
            self.progress_label.setText("Cancelling…")
    
    def _on_progress(self, progress, message):
        """Handle progress updates."""
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(message)
    
    def _on_finished(self, success, message, files_processed: int = 0):
        """Handle completion."""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setVisible(False)
        
        if success:
            # Load the processed result into the 'after' side of the comparison slider
            if (self._preview_widget is not None and self.selected_files
                    and self.output_directory):
                try:
                    from pathlib import Path as _Path
                    out_path = _Path(self.output_directory) / _Path(self.selected_files[0]).name
                    if out_path.exists():
                        after_img = Image.open(out_path)
                        after_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                        data = after_img.convert("RGBA").tobytes("raw", "RGBA")
                        qi = QImage(data, after_img.width, after_img.height,
                                    after_img.width * 4, QImage.Format.Format_RGBA8888)
                        self._preview_widget.set_after_image(QPixmap.fromImage(qi))
                except Exception:
                    pass
            QMessageBox.information(self, "Complete", message)
            self.progress_label.setText("✓ Processing complete")
        else:
            QMessageBox.critical(self, "Error", message)
            self.progress_label.setText("✗ Processing failed")
        self.finished.emit(success, message, files_processed)
    
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
