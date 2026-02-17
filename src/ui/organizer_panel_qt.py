"""
Comprehensive Texture Organizer UI Panel - PyQt6 Version
AI-powered texture classification with learning system
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import time
import threading
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QComboBox,
    QCheckBox, QGroupBox, QScrollArea, QFrame, QPlainTextEdit,
    QToolButton, QGridLayout, QLineEdit, QCompleter, QListWidget,
    QSplitter, QTextEdit, QSpinBox, QDoubleSpinBox, QTabWidget,
    QListWidgetItem, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QStringListModel, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage

logger = logging.getLogger(__name__)

# Import organizer settings panel
try:
    from ui.organizer_settings_panel import OrganizerSettingsPanel
    ORGANIZER_SETTINGS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Organizer settings panel not available: {e}")
    ORGANIZER_SETTINGS_AVAILABLE = False

# Import dependencies
try:
    from organizer import OrganizationEngine, TextureInfo, ORGANIZATION_STYLES
    from organizer.learning_system import AILearningSystem
    ORGANIZER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Organizer not available: {e}")
    ORGANIZER_AVAILABLE = False

try:
    from features.game_identifier import GameIdentifier
    GAME_IDENTIFIER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"GameIdentifier not available: {e}")
    GAME_IDENTIFIER_AVAILABLE = False

try:
    from vision_models.clip_model import CLIPModel
    from vision_models.dinov2_model import DINOv2Model
    VISION_MODELS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Vision models not available: {e}")
    logger.warning("Please install required dependencies: pip install torch transformers open_clip_torch")
    VISION_MODELS_AVAILABLE = False
    CLIPModel = None
    DINOv2Model = None
except Exception as e:
    # Handle runtime errors like PIL missing, DLL issues, etc.
    logger.warning(f"Vision models could not be loaded: {e}")
    logger.warning("This may be due to missing PIL, torch, or other dependencies")
    VISION_MODELS_AVAILABLE = False
    CLIPModel = None
    DINOv2Model = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available - image preview disabled")
    logger.warning("To enable: pip install pillow")
except Exception as e:
    PIL_AVAILABLE = False
    logger.warning(f"PIL could not be loaded: {e}")

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except ImportError:
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")


class OrganizerWorker(QThread):
    """Worker thread for organizing textures with AI classification."""
    
    progress = pyqtSignal(int, int, str, float)  # current, total, filename, confidence
    finished = pyqtSignal(bool, str, dict)  # success, message, stats
    log = pyqtSignal(str)  # log message
    classification_ready = pyqtSignal(str, str, float, object)  # filename, suggested_folder, confidence, image
    
    def __init__(self, settings: Dict[str, Any]):
        super().__init__()
        self.settings = settings
        self._is_cancelled = False
        self._start_time = 0
        self._files_processed = 0
        self._advance_event = threading.Event()
        self._current_file_path = None  # Full path for suggested/manual modes
        
        # Initialize AI models - ALWAYS attempt to load them
        self.clip_model = None
        self.dinov2_model = None
        
        # Always use AI if available
        use_ai = settings.get('use_ai', True)  # Default to True
        
        if use_ai:
            if not VISION_MODELS_AVAILABLE:
                self.log.emit("⚠️ WARNING: Vision models not available!")
                if not PIL_AVAILABLE:
                    self.log.emit("Missing dependency: PIL/Pillow (pip install pillow)")
                self.log.emit("Missing dependencies: torch transformers open_clip_torch")
                self.log.emit("Install with: pip install torch transformers open-clip-torch pillow")
                self.log.emit("Falling back to pattern-based classification")
            else:
                try:
                    model_type = settings.get('ai_model', 'clip')
                    if model_type in ['clip', 'hybrid']:
                        self.clip_model = CLIPModel()
                        self.log.emit("✓ CLIP model loaded successfully")
                    
                    if model_type in ['dinov2', 'hybrid']:
                        self.dinov2_model = DINOv2Model()
                        self.log.emit("✓ DINOv2 model loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to load AI models: {e}")
                    self.log.emit(f"⚠️ AI models failed to load: {e}")
                    self.log.emit("Falling back to pattern-based classification")
    
    def run(self):
        """Execute organization with AI classification."""
        self._start_time = time.time()
        self._files_processed = 0
        
        try:
            mode = self.settings.get('mode', 'automatic')
            
            if mode == 'automatic':
                self._run_automatic()
            elif mode == 'suggested':
                self._run_suggested()
            elif mode == 'manual':
                self._run_manual()
            
        except Exception as e:
            logger.error(f"Organization failed: {e}", exc_info=True)
            self.finished.emit(False, f"Organization failed: {str(e)}", {})
    
    def _run_automatic(self):
        """Automatic mode: AI classifies and moves files instantly."""
        source_dir = Path(self.settings['source_dir'])
        target_dir = Path(self.settings['target_dir'])
        
        # Collect files
        files = self._collect_files(source_dir)
        total_files = len(files)
        
        self.log.emit(f"Processing {total_files} files in automatic mode...")
        
        moved_count = 0
        for idx, file_path in enumerate(files):
            if self._is_cancelled:
                break
            
            # Classify with AI
            suggested_folder, confidence = self._classify_texture(file_path)
            
            # Auto-accept if confidence above threshold
            threshold = self.settings.get('confidence_threshold', 0.8)
            if confidence >= threshold:
                # Move file
                target_path = target_dir / suggested_folder / file_path.name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    file_path.rename(target_path)
                    moved_count += 1
                    self._files_processed += 1
                except Exception as e:
                    self.log.emit(f"⚠ Failed to move {file_path.name}: {e}")
            
            self.progress.emit(idx + 1, total_files, file_path.name, confidence)
        
        elapsed = time.time() - self._start_time
        stats = {
            'files_moved': moved_count,
            'files_skipped': total_files - moved_count,
            'elapsed_time': elapsed
        }
        
        self.finished.emit(True, f"Moved {moved_count}/{total_files} files", stats)
    
    def _run_suggested(self):
        """Suggested mode: AI suggests, user confirms (handled by UI)."""
        source_dir = Path(self.settings['source_dir'])
        
        # Collect files
        files = self._collect_files(source_dir)
        total_files = len(files)
        
        self.log.emit(f"Ready to process {total_files} files in suggested mode")
        
        if not files:
            self.finished.emit(True, "No files to process", {'files_processed': 0, 'elapsed_time': 0})
            return
        
        # Loop through files, waiting for user response after each
        for index, file_path in enumerate(files):
            if self._is_cancelled:
                break
            
            self._current_file_path = file_path
            
            # Classify with AI
            suggested_folder, confidence = self._classify_texture(file_path)
            
            # Load image for preview
            image = None
            if PIL_AVAILABLE:
                try:
                    image = Image.open(file_path)
                except Exception as e:
                    logger.warning(f"Could not load image {file_path}: {e}")
            
            # Emit for UI handling
            self.classification_ready.emit(str(file_path), suggested_folder, confidence, image)
            self.progress.emit(index + 1, total_files, file_path.name, confidence)
            
            # Wait for user to accept/reject before continuing
            self._advance_event.wait()
            self._advance_event.clear()
            
            if self._is_cancelled:
                break
        
        elapsed = time.time() - self._start_time
        stats = {'files_processed': self._files_processed, 'elapsed_time': elapsed}
        self.finished.emit(True, f"Processed {self._files_processed}/{total_files} files", stats)
    
    def _run_manual(self):
        """Manual mode: User types folder, AI learns (handled by UI).
        
        Same flow as suggested mode - the UI differentiates the experience
        by de-emphasizing the AI suggestion and highlighting the manual input.
        """
        self._run_suggested()
    
    def advance(self):
        """Signal the worker to advance to the next file (called from UI thread)."""
        self._files_processed += 1
        self._advance_event.set()
    
    def get_current_file_path(self) -> Optional[Path]:
        """Get the full path of the file currently being reviewed."""
        return self._current_file_path
    
    def _collect_files(self, source_dir: Path) -> List[Path]:
        """Collect texture files from source directory."""
        extensions = {'.dds', '.png', '.jpg', '.jpeg', '.tga', '.bmp'}
        files = []
        
        recursive = self.settings.get('recursive', True)
        
        if recursive:
            for ext in extensions:
                files.extend(source_dir.rglob(f'*{ext}'))
        else:
            for ext in extensions:
                files.extend(source_dir.glob(f'*{ext}'))
        
        return sorted(files)
    
    def _classify_texture(self, file_path: Path) -> Tuple[str, float]:
        """
        Classify texture using AI models.
        
        Returns:
            (suggested_folder, confidence)
        """
        if not self.clip_model and not self.dinov2_model:
            # Fallback to simple heuristic
            return self._heuristic_classification(file_path)
        
        try:
            # Use CLIP for text-based classification
            if self.clip_model:
                categories = [
                    "character", "environment", "ui", "weapon", 
                    "vehicle", "effect", "texture"
                ]
                
                # Classify
                results = self.clip_model.classify_image(str(file_path), categories)
                if results:
                    top_category = max(results.items(), key=lambda x: x[1])
                    return top_category[0], top_category[1]
            
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
        
        return self._heuristic_classification(file_path)
    
    def _heuristic_classification(self, file_path: Path) -> Tuple[str, float]:
        """Simple filename-based classification."""
        name_lower = file_path.stem.lower()
        
        # Simple keyword matching
        if any(kw in name_lower for kw in ['char', 'player', 'npc', 'enemy']):
            return "character", 0.7
        elif any(kw in name_lower for kw in ['env', 'world', 'scene', 'level']):
            return "environment", 0.7
        elif any(kw in name_lower for kw in ['ui', 'hud', 'menu', 'button']):
            return "ui", 0.7
        elif any(kw in name_lower for kw in ['weapon', 'gun', 'sword', 'item']):
            return "weapon", 0.7
        else:
            return "misc", 0.5
    
    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True
        self._advance_event.set()  # Unblock if waiting for user input


class OrganizerPanelQt(QWidget):
    """
    Comprehensive Texture Organizer Panel with AI-powered classification.
    
    Features:
    - Game detection from SLUS/SCUS codes
    - Three modes: Automatic, Suggested, Manual
    - Archive input/output support
    - AI classification with CLIP/DINOv2
    - Learning system with profile import/export
    - Live progress display
    - Settings panel
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not ORGANIZER_AVAILABLE:
            self._show_unavailable()
            return
        
        # Initialize systems
        self.engine = None  # Created when starting organization with style + output dir
        self.learning_system = AILearningSystem()
        
        if GAME_IDENTIFIER_AVAILABLE:
            self.game_identifier = GameIdentifier()
        else:
            self.game_identifier = None
        
        # State
        self.source_directory = None
        self.target_directory = None
        self.current_mode = 'automatic'
        self.detected_game = None
        self.worker_thread = None
        self.current_files = []
        self.current_file_index = 0
        
        # Store current classification data to avoid parsing UI text
        self.current_filename = None
        self.current_file_path_str = None
        self.current_suggested_folder = None
        self.current_confidence = None
        
        self._create_ui()
        self._setup_learning_system()
    
    def _show_unavailable(self):
        """Show message when organizer is not available."""
        layout = QVBoxLayout(self)
        label = QLabel(
            "⚠️ Texture Organizer Unavailable\n\n"
            "Required dependencies not installed."
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = label.font()
        font.setPointSize(14)
        label.setFont(font)
        layout.addWidget(label)
    
    def _create_ui(self):
        """Create the comprehensive UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("🤖 AI-Powered Texture Organizer")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # AI Status indicator with detailed information
        if VISION_MODELS_AVAILABLE:
            status_label = QLabel("✓ AI Models Ready")
            status_label.setStyleSheet("color: green; font-size: 10pt; font-weight: bold;")
        else:
            status_text = "⚠️ AI Models Not Available\n"
            status_text += "📦 Missing dependencies: PyTorch and/or Transformers\n"
            status_text += "💡 Install: pip install torch torchvision transformers\n"
            status_text += "ℹ️ Organizer will use basic classification without AI"
            status_label = QLabel(status_text)
            status_label.setStyleSheet("color: orange; font-size: 9pt; font-weight: bold;")
            status_label.setWordWrap(True)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        main_layout = QVBoxLayout(container)
        
        # Game Detection Section
        self._create_game_detection_section(main_layout)
        
        # Mode Selection
        self._create_mode_selection_section(main_layout)
        
        # File Input Section
        self._create_file_input_section(main_layout)
        
        # Work Area (Preview + Classification)
        self._create_work_area_section(main_layout)
        
        # Progress Section
        self._create_progress_section(main_layout)
        
        # Action Buttons
        self._create_action_buttons(main_layout)
        
        # Settings (collapsible)
        self._create_settings_section(main_layout)
        
        main_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _create_game_detection_section(self, layout):
        """Create game detection section."""
        group = QGroupBox("🎮 Game Detection")
        group_layout = QHBoxLayout()
        
        self.game_label = QLabel("No game detected")
        self.game_label.setStyleSheet("font-size: 11pt; color: gray;")
        group_layout.addWidget(self.game_label, 1)
        
        detect_btn = QPushButton("🔍 Detect")
        detect_btn.clicked.connect(self._detect_game)
        group_layout.addWidget(detect_btn)
        
        change_btn = QPushButton("Change")
        change_btn.clicked.connect(self._change_game)
        group_layout.addWidget(change_btn)
        
        help_btn = QPushButton("?")
        help_btn.setMaximumWidth(30)
        help_btn.clicked.connect(self._show_game_detection_help)
        group_layout.addWidget(help_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_mode_selection_section(self, layout):
        """Create mode selection section."""
        group = QGroupBox("⚙️ Organization Mode")
        group_layout = QVBoxLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("🚀 Automatic - AI classifies and moves instantly", "automatic")
        self.mode_combo.addItem("💡 Suggested - AI suggests, you confirm", "suggested")
        self.mode_combo.addItem("✍️ Manual - You type folder, AI learns", "manual")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        group_layout.addWidget(self.mode_combo)
        
        # Mode description
        self.mode_description = QLabel()
        self.mode_description.setWordWrap(True)
        self.mode_description.setStyleSheet("color: gray; padding: 5px;")
        group_layout.addWidget(self.mode_description)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        self._update_mode_description()
    
    def _create_file_input_section(self, layout):
        """Create file input section."""
        group = QGroupBox("📁 File Input/Output")
        group_layout = QVBoxLayout()
        
        # Directory selection
        dir_layout = QHBoxLayout()
        
        self.source_label = QLabel("No source selected")
        self.source_label.setStyleSheet("color: gray;")
        dir_layout.addWidget(QLabel("Source:"))
        dir_layout.addWidget(self.source_label, 1)
        
        select_source_btn = QPushButton("Browse...")
        select_source_btn.clicked.connect(self._select_source_directory)
        dir_layout.addWidget(select_source_btn)
        
        group_layout.addLayout(dir_layout)
        
        target_layout = QHBoxLayout()
        self.target_label = QLabel("No target selected")
        self.target_label.setStyleSheet("color: gray;")
        target_layout.addWidget(QLabel("Target:"))
        target_layout.addWidget(self.target_label, 1)
        
        select_target_btn = QPushButton("Browse...")
        select_target_btn.clicked.connect(self._select_target_directory)
        target_layout.addWidget(select_target_btn)
        
        group_layout.addLayout(target_layout)
        
        # Options - Always enabled with helpful tooltips
        options_layout = QHBoxLayout()
        
        self.archive_input_cb = QCheckBox("📦 Archive Input")
        if not ARCHIVE_AVAILABLE:
            self.archive_input_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_input_cb.setStyleSheet("color: gray;")
        else:
            self.archive_input_cb.setToolTip("Select ZIP/7Z/RAR archives as input")
        options_layout.addWidget(self.archive_input_cb)
        
        self.archive_output_cb = QCheckBox("📦 Archive Output")
        if not ARCHIVE_AVAILABLE:
            self.archive_output_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_output_cb.setStyleSheet("color: gray;")
        else:
            self.archive_output_cb.setToolTip("Save organized files to archive")
        options_layout.addWidget(self.archive_output_cb)
        
        self.subfolders_cb = QCheckBox("📂 Include Subfolders")
        self.subfolders_cb.setChecked(True)
        options_layout.addWidget(self.subfolders_cb)
        
        options_layout.addStretch()
        group_layout.addLayout(options_layout)
        
        # File count
        self.file_count_label = QLabel("0 files selected")
        self.file_count_label.setStyleSheet("color: gray; font-style: italic;")
        group_layout.addWidget(self.file_count_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_work_area_section(self, layout):
        """Create preview and classification work area."""
        group = QGroupBox("🖼️ Work Area")
        group_layout = QHBoxLayout()
        
        # Left: Preview Panel
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_title = QLabel("Image Preview")
        preview_title.setStyleSheet("font-weight: bold;")
        preview_layout.addWidget(preview_title)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(300, 300)
        self.preview_label.setStyleSheet("border: 1px solid gray; background: #f0f0f0;")
        self.preview_label.setText("No image loaded")
        preview_layout.addWidget(self.preview_label)
        
        self.preview_info_label = QLabel()
        self.preview_info_label.setStyleSheet("color: gray; font-size: 9pt;")
        preview_layout.addWidget(self.preview_info_label)
        
        # Right: Classification Panel
        classification_container = QWidget()
        classification_layout = QVBoxLayout(classification_container)
        classification_layout.setContentsMargins(0, 0, 0, 0)
        
        classification_title = QLabel("Classification")
        classification_title.setStyleSheet("font-weight: bold;")
        classification_layout.addWidget(classification_title)
        
        # AI Suggestion display
        self.suggestion_label = QLabel("AI Suggestion: —")
        self.suggestion_label.setStyleSheet("font-size: 12pt; padding: 5px;")
        classification_layout.addWidget(self.suggestion_label)
        
        self.confidence_label = QLabel("Confidence: —")
        self.confidence_label.setStyleSheet("color: gray; padding: 5px;")
        classification_layout.addWidget(self.confidence_label)
        
        # Feedback buttons
        feedback_layout = QHBoxLayout()
        self.good_btn = QPushButton("✅ Good")
        self.good_btn.setStyleSheet("background: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        self.good_btn.clicked.connect(self._on_good_feedback)
        self.good_btn.setEnabled(False)
        feedback_layout.addWidget(self.good_btn)
        
        self.bad_btn = QPushButton("❌ Bad")
        self.bad_btn.setStyleSheet("background: #f44336; color: white; padding: 10px; font-weight: bold;")
        self.bad_btn.clicked.connect(self._on_bad_feedback)
        self.bad_btn.setEnabled(False)
        feedback_layout.addWidget(self.bad_btn)
        
        classification_layout.addLayout(feedback_layout)
        
        # Manual override / folder input
        classification_layout.addWidget(QLabel("Manual Override:"))
        
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Type folder name or path...")
        self.folder_input.textChanged.connect(self._on_folder_text_changed)
        classification_layout.addWidget(self.folder_input)
        
        # Auto-complete suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(150)
        self.suggestions_list.itemClicked.connect(self._on_suggestion_selected)
        classification_layout.addWidget(self.suggestions_list)
        
        # Path preview
        self.path_preview_label = QLabel("Path: —")
        self.path_preview_label.setStyleSheet("color: gray; font-style: italic; padding: 5px;")
        classification_layout.addWidget(self.path_preview_label)
        
        classification_layout.addStretch()
        
        # Add to splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(preview_container)
        splitter.addWidget(classification_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        group_layout.addWidget(splitter)
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_progress_section(self, layout):
        """Create progress display section."""
        group = QGroupBox("📊 Progress")
        group_layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        group_layout.addWidget(self.progress_bar)
        
        # Status labels
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.status_label, 1)
        
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("color: gray;")
        status_layout.addWidget(self.speed_label)
        
        self.eta_label = QLabel("")
        self.eta_label.setStyleSheet("color: gray;")
        status_layout.addWidget(self.eta_label)
        
        group_layout.addLayout(status_layout)
        
        # Recent actions log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 9pt;")
        group_layout.addWidget(self.log_text)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Start Organization")
        self.start_btn.setStyleSheet("background: #4CAF50; color: white; padding: 12px; font-size: 12pt; font-weight: bold;")
        self.start_btn.clicked.connect(self._start_organization)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_organization)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.export_learning_btn = QPushButton("📤 Export Learning")
        self.export_learning_btn.clicked.connect(self._export_learning_profile)
        button_layout.addWidget(self.export_learning_btn)
        
        self.import_learning_btn = QPushButton("📥 Import Learning")
        self.import_learning_btn.clicked.connect(self._import_learning_profile)
        button_layout.addWidget(self.import_learning_btn)
        
        self.clear_log_btn = QPushButton("🗑️ Clear Log")
        self.clear_log_btn.clicked.connect(self._clear_log)
        button_layout.addWidget(self.clear_log_btn)
        
        layout.addLayout(button_layout)
    
    def _create_settings_section(self, layout):
        """Create settings section with comprehensive organizer settings panel."""
        # Create collapsible settings group
        settings_container = QWidget()
        settings_layout = QVBoxLayout(settings_container)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(5)
        
        # Toggle button for settings visibility
        toggle_btn = QPushButton("⚙️ Show Advanced Settings")
        toggle_btn.setCheckable(True)
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        settings_layout.addWidget(toggle_btn)
        
        # Create settings panel
        if ORGANIZER_SETTINGS_AVAILABLE:
            self.settings_panel = OrganizerSettingsPanel(config=self.get_config())
            self.settings_panel.settings_changed.connect(self._on_settings_changed)
            self.settings_panel.setVisible(False)  # Hidden by default
            settings_layout.addWidget(self.settings_panel)
            
            # Connect toggle
            toggle_btn.toggled.connect(lambda checked: self._toggle_settings(checked, toggle_btn))
        else:
            # Fallback to basic settings if comprehensive panel not available
            self._create_basic_settings(settings_layout)
            basic_settings = settings_layout.itemAt(1).widget()
            basic_settings.setVisible(False)
            toggle_btn.toggled.connect(lambda checked: basic_settings.setVisible(checked))
        
        layout.addWidget(settings_container)
    
    def _toggle_settings(self, visible: bool, button: QPushButton):
        """Toggle settings panel visibility."""
        self.settings_panel.setVisible(visible)
        if visible:
            button.setText("⚙️ Hide Advanced Settings")
        else:
            button.setText("⚙️ Show Advanced Settings")
    
    def _create_basic_settings(self, layout):
        """Create basic settings (fallback if comprehensive panel not available)."""
        group = QGroupBox("🔧 Basic Settings")
        group_layout = QVBoxLayout()
        
        # AI Model Selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("AI Model:"))
        
        self.ai_model_combo = QComboBox()
        if VISION_MODELS_AVAILABLE:
            self.ai_model_combo.addItem("CLIP (Recommended)", "clip")
            self.ai_model_combo.addItem("DINOv2 (Visual Similarity)", "dinov2")
            self.ai_model_combo.addItem("Hybrid (Both, Highest Accuracy)", "hybrid")
            self.ai_model_combo.setCurrentIndex(0)  # Default to CLIP
        else:
            # Vision models not available - show disabled option
            self.ai_model_combo.addItem("Not Available (Install PyTorch)", "none")
            self.ai_model_combo.setEnabled(False)
        
        model_layout.addWidget(self.ai_model_combo)
        
        # Show warning/info if models not available
        if not VISION_MODELS_AVAILABLE:
            if not PIL_AVAILABLE:
                pil_warning_label = QLabel("⚠️ Missing PIL: pip install pillow")
                pil_warning_label.setStyleSheet("color: red; font-size: 8pt;")
                model_layout.addWidget(pil_warning_label)
            deps_warning_label = QLabel("⚠️ Install: pip install torch transformers open-clip-torch")
            deps_warning_label.setStyleSheet("color: orange; font-size: 8pt;")
            model_layout.addWidget(deps_warning_label)
        
        model_layout.addStretch()
        
        group_layout.addLayout(model_layout)
        
        # Learning settings
        learning_layout = QHBoxLayout()
        
        self.enable_learning_cb = QCheckBox("Enable Learning")
        self.enable_learning_cb.setChecked(True)
        learning_layout.addWidget(self.enable_learning_cb)
        
        learning_layout.addWidget(QLabel("Confidence Threshold:"))
        self.confidence_threshold_spin = QDoubleSpinBox()
        self.confidence_threshold_spin.setRange(0.0, 1.0)
        self.confidence_threshold_spin.setValue(0.8)
        self.confidence_threshold_spin.setSingleStep(0.05)
        learning_layout.addWidget(self.confidence_threshold_spin)
        
        learning_layout.addStretch()
        
        group_layout.addLayout(learning_layout)
        
        # Organization settings
        org_settings_layout = QHBoxLayout()
        
        org_settings_layout.addWidget(QLabel("Conflict Resolution:"))
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItem("Skip", "skip")
        self.conflict_combo.addItem("Overwrite", "overwrite")
        self.conflict_combo.addItem("Number (file_1, file_2...)", "number")
        org_settings_layout.addWidget(self.conflict_combo)
        
        self.create_backup_cb = QCheckBox("Create Backup")
        self.create_backup_cb.setChecked(True)
        org_settings_layout.addWidget(self.create_backup_cb)
        
        org_settings_layout.addStretch()
        
        group_layout.addLayout(org_settings_layout)
        
        # Clear learning button
        clear_learning_btn = QPushButton("🗑️ Clear Learning History")
        clear_learning_btn.clicked.connect(self._clear_learning_history)
        group_layout.addWidget(clear_learning_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _on_settings_changed(self, settings: dict):
        """Handle settings changes from settings panel."""
        # Update internal state based on new settings
        logger.info(f"Settings updated: {settings}")
        # Settings will be applied when starting organization
    
    def get_config(self) -> dict:
        """Get current configuration for settings panel."""
        return {
            'organizer': {
                'clip_model': 'CLIP_ViT-B/32 (340 MB - Balanced)',
                'dinov2_model': 'DINOv2_base (340 MB - Balanced)',
                'organization_mode': 'Automatic (AI instantly classifies)',
                'confidence_threshold': 75,
                'auto_accept': False,
                'sensitivity': 1.0,
                'learning_enabled': True,
                'process_subfolders': True,
                'archive_input': False,
                'archive_output': False,
                'backup_files': True,
                'naming_pattern': '{category}/{filename}',
                'case_sensitive': False,
                'conflict_resolution': 'Number (add suffix: _1, _2, etc.)',
            }
        }
    
    def _setup_learning_system(self):
        """Initialize learning system with current profile."""
        # Try to detect game and load corresponding profile
        if self.game_identifier and self.source_directory:
            self._detect_game()
    
    def _detect_game(self):
        """Detect game from source directory path."""
        if not self.game_identifier or not self.source_directory:
            return
        
        try:
            game_info = self.game_identifier.identify_game(Path(self.source_directory))
            
            if game_info and game_info.confidence > 0.5:
                self.detected_game = game_info
                self.game_label.setText(
                    f"✓ {game_info.title} ({game_info.serial}) - "
                    f"Confidence: {game_info.confidence:.0%}"
                )
                self.game_label.setStyleSheet("font-size: 11pt; color: green; font-weight: bold;")
                
                self._log(f"Detected game: {game_info.title} ({game_info.serial})")
                
                # Try to load corresponding learning profile
                self._load_game_profile(game_info)
            else:
                self.game_label.setText("No game detected")
                self.game_label.setStyleSheet("font-size: 11pt; color: gray;")
                
        except Exception as e:
            logger.error(f"Game detection failed: {e}")
            self._log(f"Game detection failed: {e}")
    
    def _load_game_profile(self, game_info):
        """Load learning profile for detected game."""
        # Look for existing profiles matching this game
        profiles = self.learning_system.list_profiles()
        
        for profile_info in profiles:
            if profile_info.get('game_serial') == game_info.serial:
                try:
                    self.learning_system.load_profile(profile_info['filepath'])
                    self._log(f"Loaded learning profile for {game_info.title}")
                    return
                except Exception as e:
                    logger.error(f"Failed to load profile: {e}")
        
        # Create new profile
        self.learning_system.create_new_profile(
            game_name=game_info.title,
            game_serial=game_info.serial
        )
        self._log(f"Created new learning profile for {game_info.title}")
    
    def _change_game(self):
        """Manually select game."""
        # Show dialog to list available profiles or enter game info
        QMessageBox.information(
            self,
            "Change Game",
            "Game profile selection dialog would appear here.\n"
            "This feature allows manual game selection."
        )
    
    def _show_game_detection_help(self):
        """Show help about game detection."""
        QMessageBox.information(
            self,
            "Game Detection Help",
            "Game detection looks for PS2 serial codes (SLUS-xxxxx, SCUS-xxxxx, etc.) "
            "in folder paths and filenames.\n\n"
            "Detected games enable game-specific texture organization profiles "
            "and learning data.\n\n"
            "Examples:\n"
            "• /textures/SLUS-20917/... → God of War II\n"
            "• /PCSX2/SCUS-97268/... → GTA San Andreas"
        )
    
    def _on_mode_changed(self):
        """Handle mode change."""
        self.current_mode = self.mode_combo.currentData()
        self._update_mode_description()
        self._log(f"Mode changed to: {self.mode_combo.currentText()}")
    
    def _update_mode_description(self):
        """Update mode description."""
        descriptions = {
            'automatic': "AI analyzes each texture and automatically organizes it into the appropriate folder. "
                        "Files are moved immediately if confidence is above the threshold. "
                        "Best for: large batches where speed matters more than manual control.",
            'suggested': "AI suggests a folder for each texture and shows a review window with image preview. "
                        "You can accept the suggestion, override it with your own folder, or skip. "
                        "Feedback helps AI learn your preferences. Best for: curated sorting with AI assistance.",
            'manual': "You type the target folder for each texture while seeing an image preview. "
                     "AI provides a subtle hint but your input takes priority. "
                     "The system learns from your choices for future sessions. Best for: training the AI on your preferences."
        }
        self.mode_description.setText(descriptions.get(self.current_mode, ""))
    
    def _select_source_directory(self):
        """Select source directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Source Directory"
        )
        
        if directory:
            self.source_directory = directory
            self.source_label.setText(directory)
            self.source_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Count files
            self._update_file_count()
            
            # Try to detect game
            self._detect_game()
            
            self._check_ready()
    
    def _select_target_directory(self):
        """Select target directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Target Directory"
        )
        
        if directory:
            self.target_directory = directory
            self.target_label.setText(directory)
            self.target_label.setStyleSheet("color: green; font-weight: bold;")
            self._check_ready()
    
    def _update_file_count(self):
        """Update file count label."""
        if not self.source_directory:
            self.file_count_label.setText("0 files selected")
            return
        
        source_path = Path(self.source_directory)
        extensions = {'.dds', '.png', '.jpg', '.jpeg', '.tga', '.bmp'}
        
        file_count = 0
        for ext in extensions:
            if self.subfolders_cb.isChecked():
                file_count += len(list(source_path.rglob(f'*{ext}')))
            else:
                file_count += len(list(source_path.glob(f'*{ext}')))
        
        self.file_count_label.setText(f"{file_count} files selected")
    
    def _check_ready(self):
        """Check if ready to start."""
        ready = bool(self.source_directory and self.target_directory)
        self.start_btn.setEnabled(ready)
    
    def _on_folder_text_changed(self, text):
        """Handle folder input text change - show suggestions."""
        if not text:
            self.suggestions_list.clear()
            self.path_preview_label.setText("Path: —")
            return
        
        # Generate suggestions
        suggestions = self._get_folder_suggestions(text)
        
        # Update list
        self.suggestions_list.clear()
        for suggestion in suggestions[:10]:  # Top 10
            self.suggestions_list.addItem(suggestion)
        
        # Update path preview
        if self.target_directory:
            full_path = Path(self.target_directory) / text
            self.path_preview_label.setText(f"Path: {full_path}")
    
    def _get_folder_suggestions(self, partial_text: str) -> List[str]:
        """Get folder suggestions based on partial input."""
        suggestions = set()
        
        # 1. From learning system
        if self.learning_system:
            learned_suggestions = self.learning_system.get_suggestion(
                partial_text + ".png"  # Dummy filename
            )
            for folder, _ in learned_suggestions:
                suggestions.add(folder)
        
        # 2. From standard categories
        standard_categories = [
            "character", "environment", "ui", "weapon", "vehicle",
            "effect", "texture", "misc", "background", "foreground"
        ]
        for category in standard_categories:
            if partial_text.lower() in category.lower():
                suggestions.add(category)
        
        # 3. From existing folders in target directory
        if self.target_directory:
            target_path = Path(self.target_directory)
            try:
                for folder in target_path.iterdir():
                    if folder.is_dir() and partial_text.lower() in folder.name.lower():
                        suggestions.add(folder.name)
            except Exception:
                pass
        
        return sorted(suggestions)
    
    def _on_suggestion_selected(self, item: QListWidgetItem):
        """Handle suggestion selection."""
        self.folder_input.setText(item.text())
    
    def _on_good_feedback(self):
        """Handle Good/Accept button click - move file and advance."""
        if not self.current_suggested_folder or not self.current_filename:
            self._log("⚠ No current classification to accept")
            return
        
        # Determine which folder to use (manual override takes priority)
        target_folder = self.folder_input.text().strip() or self.current_suggested_folder
        
        # Move the file to target directory
        if self.target_directory and hasattr(self, 'current_file_path_str'):
            source_path = Path(self.current_file_path_str)
            target_path = Path(self.target_directory) / target_folder / source_path.name
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(source_path), str(target_path))
                self._log(f"✓ Copied: {self.current_filename} → {target_folder}/")
            except Exception as e:
                self._log(f"⚠ Failed to copy {self.current_filename}: {e}")
        
        # Add to learning system
        enable_learning = self._get_learning_enabled()
        if enable_learning:
            self.learning_system.add_learning(
                filename=self.current_filename,
                suggested_folder=self.current_suggested_folder,
                user_choice=target_folder,
                confidence=self.current_confidence or 0.0,
                accepted=True
            )
        
        # Disable buttons while waiting for next file
        self.good_btn.setEnabled(False)
        self.bad_btn.setEnabled(False)
        
        # Advance worker to next file
        self._advance_worker()
    
    def _on_bad_feedback(self):
        """Handle Bad/Skip button click."""
        if not self.current_suggested_folder or not self.current_filename:
            self._log("⚠ No current classification to reject")
            return
        
        manual_choice = self.folder_input.text().strip()
        enable_learning = self._get_learning_enabled()
        
        if manual_choice:
            # User provided an override folder - move file there
            if self.target_directory and hasattr(self, 'current_file_path_str'):
                source_path = Path(self.current_file_path_str)
                target_path = Path(self.target_directory) / manual_choice / source_path.name
                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(source_path), str(target_path))
                    self._log(f"✓ Copied: {self.current_filename} → {manual_choice}/ (overridden)")
                except Exception as e:
                    self._log(f"⚠ Failed to copy {self.current_filename}: {e}")
            
            if enable_learning:
                self.learning_system.add_learning(
                    filename=self.current_filename,
                    suggested_folder=self.current_suggested_folder,
                    user_choice=manual_choice,
                    confidence=self.current_confidence or 0.0,
                    accepted=False
                )
            self._log(f"✗ Rejected: {self.current_filename}. AI: {self.current_suggested_folder} → User: {manual_choice}")
        else:
            # No override provided - skip the file
            self._log(f"⏭ Skipped: {self.current_filename} (AI suggested: {self.current_suggested_folder})")
        
        # Disable buttons while waiting for next file
        self.good_btn.setEnabled(False)
        self.bad_btn.setEnabled(False)
        
        # Advance worker to next file
        self._advance_worker()
    
    def _advance_worker(self):
        """Tell the worker thread to advance to the next file."""
        if self.worker_thread and hasattr(self.worker_thread, 'advance'):
            self.worker_thread.advance()
    
    def _get_learning_enabled(self) -> bool:
        """Get whether learning is enabled, handling both settings panel types."""
        if ORGANIZER_SETTINGS_AVAILABLE and hasattr(self, 'settings_panel'):
            settings = self.settings_panel.get_settings()
            return settings.get('learning_enabled', True)
        elif hasattr(self, 'enable_learning_cb'):
            return self.enable_learning_cb.isChecked()
        return True
    
    def _process_next_file(self):
        """Process next file in suggested/manual mode."""
        self._advance_worker()
    
    def _start_organization(self):
        """Start the organization process."""
        if not self.source_directory or not self.target_directory:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Please select source and target directories."
            )
            return
        
        # Check if user selected archive options without archive support
        if (self.archive_input_cb.isChecked() or self.archive_output_cb.isChecked()) and not ARCHIVE_AVAILABLE:
            reply = QMessageBox.warning(
                self,
                "Archive Support Not Available",
                "Archive support is not available.\n\n"
                "Install required packages:\n"
                "  pip install py7zr rarfile\n\n"
                "Continue without archive support?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            # Uncheck archive options
            self.archive_input_cb.setChecked(False)
            self.archive_output_cb.setChecked(False)
        
        # Confirm action
        # Gather settings from whichever panel is available
        if ORGANIZER_SETTINGS_AVAILABLE and hasattr(self, 'settings_panel'):
            panel_settings = self.settings_panel.get_settings()
            ai_model_text = panel_settings.get('feature_extractor', 'CLIP')
            learning_enabled = panel_settings.get('learning_enabled', True)
            confidence_threshold = panel_settings.get('confidence_threshold', 75) / 100.0
            conflict_res = panel_settings.get('conflict_resolution', 'Number')
            backup = panel_settings.get('backup_files', True)
            ai_model_data = 'clip'  # Default
            if 'DINOv2' in ai_model_text and 'CLIP' in ai_model_text:
                ai_model_data = 'hybrid'
            elif 'DINOv2' in ai_model_text:
                ai_model_data = 'dinov2'
        else:
            ai_model_text = self.ai_model_combo.currentText() if hasattr(self, 'ai_model_combo') else 'CLIP'
            learning_enabled = self.enable_learning_cb.isChecked() if hasattr(self, 'enable_learning_cb') else True
            confidence_threshold = self.confidence_threshold_spin.value() if hasattr(self, 'confidence_threshold_spin') else 0.8
            conflict_res = self.conflict_combo.currentData() if hasattr(self, 'conflict_combo') else 'number'
            backup = self.create_backup_cb.isChecked() if hasattr(self, 'create_backup_cb') else True
            ai_model_data = self.ai_model_combo.currentData() if hasattr(self, 'ai_model_combo') else 'clip'
        
        reply = QMessageBox.question(
            self,
            "Confirm Organization",
            f"Mode: {self.mode_combo.currentText()}\n"
            f"Source: {self.source_directory}\n"
            f"Target: {self.target_directory}\n\n"
            f"AI Model: {ai_model_text}\n"
            f"Learning: {'Enabled' if learning_enabled else 'Disabled'}\n\n"
            "Start organization?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Prepare settings
        settings = {
            'mode': self.current_mode,
            'source_dir': self.source_directory,
            'target_dir': self.target_directory,
            'recursive': self.subfolders_cb.isChecked(),
            'use_ai': True,  # Always try to use AI
            'ai_model': ai_model_data,
            'confidence_threshold': confidence_threshold,
            'enable_learning': learning_enabled,
            'conflict_resolution': conflict_res,
            'create_backup': backup
        }
        
        # Disable UI
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setVisible(True)
        
        # Show progress
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        
        # Start worker
        self.worker_thread = OrganizerWorker(settings)
        self.worker_thread.progress.connect(self._update_progress)
        self.worker_thread.log.connect(self._log)
        self.worker_thread.finished.connect(self._organization_finished)
        self.worker_thread.classification_ready.connect(self._handle_classification)
        self.worker_thread.start()
        
        self._log(f"Started organization in {self.mode_combo.currentText()} mode")
    
    def _cancel_organization(self):
        """Cancel organization."""
        if self.worker_thread:
            self.worker_thread.cancel()
            self.status_label.setText("Cancelling...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            self._log("Cancelling...")
    
    def _update_progress(self, current: int, total: int, filename: str, confidence: float):
        """Update progress bar."""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        
        self.status_label.setText(f"Processing: {filename} ({current}/{total})")
        
        # Calculate speed and ETA
        if hasattr(self.worker_thread, '_start_time'):
            elapsed = time.time() - self.worker_thread._start_time
            if elapsed > 0 and current > 0:
                speed = current / elapsed
                remaining = total - current
                eta = remaining / speed if speed > 0 else 0
                
                self.speed_label.setText(f"{speed:.1f} files/sec")
                self.eta_label.setText(f"ETA: {eta:.0f}s")
    
    def _handle_classification(self, file_path_str: str, suggested_folder: str, 
                              confidence: float, image):
        """Handle classification result in suggested/manual mode."""
        # Store current classification data (full file path)
        self.current_filename = Path(file_path_str).name
        self.current_file_path_str = file_path_str
        self.current_suggested_folder = suggested_folder
        self.current_confidence = confidence
        
        is_manual = (self.current_mode == 'manual')
        
        # Update suggestion display
        if is_manual:
            # Manual mode: de-emphasize AI suggestion, highlight manual input
            self.suggestion_label.setText(f"AI Hint: {suggested_folder} (type your own below)")
            self.suggestion_label.setStyleSheet("font-size: 10pt; color: gray; padding: 5px;")
            self.folder_input.setPlaceholderText("Type the target folder for this texture...")
            self.folder_input.setFocus()
            self.folder_input.clear()
        else:
            # Suggested mode: show AI suggestion prominently
            self.suggestion_label.setText(f"AI Suggestion: {suggested_folder}")
            self.suggestion_label.setStyleSheet("font-size: 12pt; padding: 5px;")
            self.folder_input.setPlaceholderText("Override: type a different folder or accept above")
            self.folder_input.clear()
        
        self.confidence_label.setText(f"Confidence: {confidence:.0%}")
        
        # Update confidence color
        if confidence >= 0.8:
            color = "green"
        elif confidence >= 0.6:
            color = "orange"
        else:
            color = "red"
        self.confidence_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 5px;")
        
        # Enable feedback buttons
        self.good_btn.setEnabled(True)
        self.bad_btn.setEnabled(True)
        
        if is_manual:
            self.good_btn.setText("✅ Accept & Move")
            self.bad_btn.setText("⏭️ Skip")
        else:
            self.good_btn.setText("✅ Good")
            self.bad_btn.setText("❌ Bad")
        
        # Show image preview
        if image and PIL_AVAILABLE:
            self._show_image_preview(image, self.current_filename)
    
    def _show_image_preview(self, image, filename: str):
        """Show image preview."""
        try:
            # Convert PIL image to QPixmap
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for preview
            image.thumbnail((300, 300))
            
            # Convert to QImage
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, image.width * 3, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            
            self.preview_label.setPixmap(pixmap)
            self.preview_info_label.setText(f"{filename} - {image.width}x{image.height}")
            
        except Exception as e:
            logger.error(f"Failed to show preview: {e}")
            self.preview_label.setText(f"Preview error: {e}")
    
    def _organization_finished(self, success: bool, message: str, stats: Dict[str, Any]):
        """Handle organization completion."""
        # Re-enable UI
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        
        # Update status
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Show stats
            stats_msg = f"{message}\n\n"
            if 'elapsed_time' in stats:
                stats_msg += f"Time: {stats['elapsed_time']:.1f}s\n"
            if 'files_moved' in stats:
                stats_msg += f"Files moved: {stats['files_moved']}\n"
            
            QMessageBox.information(self, "Success", stats_msg)
            
            # Save learning profile
            if self._get_learning_enabled():
                try:
                    self.learning_system.save_profile()
                    self._log("Learning profile saved")
                except Exception as e:
                    logger.error(f"Failed to save profile: {e}")
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.warning(self, "Error", message)
        
        self.worker_thread = None
        self._log(f"Organization completed: {message}")
    
    def _export_learning_profile(self):
        """Export learning profile."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Learning Profile",
            str(Path.home() / "texture_learning_profile.json"),
            "JSON Files (*.json);;Encrypted Files (*.enc)"
        )
        
        if not filepath:
            return
        
        try:
            # Ask for password if .enc
            password = None
            if filepath.endswith('.enc'):
                password, ok = QInputDialog.getText(
                    self,
                    "Encryption Password",
                    "Enter password for encryption:",
                    QLineEdit.EchoMode.Password
                )
                if not ok or not password:
                    return
            
            exported_path = self.learning_system.export_profile(Path(filepath), password)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Learning profile exported to:\n{exported_path}\n\n"
                f"Entries: {len(self.learning_system.learned_mappings)}\n"
                f"Game: {self.learning_system.metadata.game}"
            )
            
            self._log(f"Exported learning profile to {exported_path}")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(self, "Export Failed", str(e))
    
    def _import_learning_profile(self):
        """Import learning profile."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Learning Profile",
            str(Path.home()),
            "Profile Files (*.json *.enc);;All Files (*.*)"
        )
        
        if not filepath:
            return
        
        try:
            # Ask for password if .enc
            password = None
            if filepath.endswith('.enc'):
                password, ok = QInputDialog.getText(
                    self,
                    "Decryption Password",
                    "Enter password for decryption:",
                    QLineEdit.EchoMode.Password
                )
                if not ok:
                    return
            
            # Ask merge or replace
            reply = QMessageBox.question(
                self,
                "Import Mode",
                "Merge with existing learning data?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            
            merge = (reply == QMessageBox.StandardButton.Yes)
            
            summary = self.learning_system.import_profile(Path(filepath), password, merge)
            
            QMessageBox.information(
                self,
                "Import Successful",
                f"Profile imported successfully!\n\n"
                f"Game: {summary['game']}\n"
                f"Entries imported: {summary['entries_imported']}\n"
                f"Entries skipped: {summary['entries_skipped']}\n"
                f"Categories imported: {summary['categories_imported']}"
            )
            
            self._log(f"Imported learning profile: {summary['game']}")
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            QMessageBox.critical(self, "Import Failed", str(e))
    
    def _clear_log(self):
        """Clear the log."""
        self.log_text.clear()
    
    def _clear_learning_history(self):
        """Clear learning history."""
        reply = QMessageBox.question(
            self,
            "Clear Learning History",
            "Are you sure you want to clear all learned data?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.learning_system.clear_learning_history()
            QMessageBox.information(self, "Cleared", "Learning history cleared.")
            self._log("Learning history cleared")
    
    def _log(self, message: str):
        """Add message to log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
