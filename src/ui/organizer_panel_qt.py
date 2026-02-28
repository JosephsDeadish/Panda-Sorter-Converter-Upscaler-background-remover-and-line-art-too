"""
Comprehensive Texture Organizer UI Panel - PyQt6 Version
AI-powered texture classification with learning system
Author: Dead On The Inside / JosephsDeadish
"""


from __future__ import annotations
import logging
import time
import threading
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
try:
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
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    QThread = object
    QSplitter = object
    QTabWidget = object
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
    class QTimer:
        def __init__(self, *a): pass
        def start(self, *a): pass
        def stop(self): pass
        timeout = property(lambda self: type("S", (), {"connect": lambda s,f: None, "emit": lambda s: None})())
    QCheckBox = object
    QComboBox = object
    QCompleter = object
    QDoubleSpinBox = object
    QFileDialog = object
    QGridLayout = object
    QHBoxLayout = object
    QInputDialog = object
    QLabel = object
    QLineEdit = object
    QListWidget = object
    QListWidgetItem = object
    QMessageBox = object
    QPlainTextEdit = object
    QProgressBar = object
    QPushButton = object
    QSpinBox = object
    QStringListModel = object
    QTextEdit = object
    QToolButton = object
    QVBoxLayout = object

logger = logging.getLogger(__name__)

# Import organizer settings panel
try:
    from ui.organizer_settings_panel import OrganizerSettingsPanel
    ORGANIZER_SETTINGS_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"Organizer settings panel not available: {e}")
    ORGANIZER_SETTINGS_AVAILABLE = False

# Import dependencies
try:
    from organizer import OrganizationEngine, TextureInfo, ORGANIZATION_STYLES
    from organizer.learning_system import AILearningSystem
    ORGANIZER_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"Organizer not available: {e}")
    ORGANIZER_AVAILABLE = False

try:
    from features.game_identifier import GameIdentifier
    GAME_IDENTIFIER_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"GameIdentifier not available: {e}")
    GAME_IDENTIFIER_AVAILABLE = False

try:
    from vision_models.clip_model import CLIPModel
    from vision_models.dinov2_model import DINOv2Model
    VISION_MODELS_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"Vision models not available: {e}")
    logger.warning("Please install required dependencies: pip install torch transformers open-clip-torch")
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
except (ImportError, OSError, RuntimeError):
    PIL_AVAILABLE = False
    logger.warning("PIL not available - image preview disabled")
    logger.warning("To enable: pip install pillow")
except Exception as e:
    PIL_AVAILABLE = False
    logger.warning(f"PIL could not be loaded: {e}")

try:
    from utils.archive_handler import ArchiveHandler
    ARCHIVE_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    ARCHIVE_AVAILABLE = False
    logger.warning("Archive handler not available")

# Human-readable descriptions for every organisation style key.
# Defined once here and referenced by both _create_mode_selection_section
# and _on_style_changed so they never drift out of sync.
_STYLE_DESCRIPTIONS: dict = {
    "appearance":    "Groups files by visual look — skin tones, stone, metal, wood, fabric, etc.",
    "by_appearance": "Groups files by visual look — skin tones, stone, metal, wood, fabric, etc.",
    "type":          "Groups by subject type — characters, props, environments, UI elements…",
    "by_type":       "Groups by subject type — characters, props, environments, UI elements…",
    "location":      "Groups by in-scene location — interior rooms, exterior environments, terrain…",
    "by_location":   "Groups by in-scene location — interior rooms, exterior environments, terrain…",
    "resolution":    "Groups by pixel dimensions — separate folders for 512, 1K, 2K, 4K images.",
    "by_resolution": "Groups by pixel dimensions — separate folders for 512, 1K, 2K, 4K images.",
    "system":        "Groups by map/usage role — Diffuse, Normal, Specular, Alpha, Emissive…",
    "by_system":     "Groups by map/usage role — Diffuse, Normal, Specular, Alpha, Emissive…",
    "flat":          "All files go into one output folder, sorted alphabetically.",
    "minimalist":    "Two-level hierarchy: broad category → filename only.",
    "maximum_detail": "Deep hierarchy: category → sub-type → resolution sub-folder.",
    "custom":        "Applies rules from your custom_style.json configuration file.",
}

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
        self._retry_event = threading.Event()
        self._current_file_path = None  # Full path for suggested/manual modes
        self._retry_count = 0  # How many times current file has been retried
        
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
                self.log.emit("Missing dependencies: torch transformers open-clip-torch")
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

        # Optionally use OrganizationEngine for folder structure
        org_engine = None
        style_key = self.settings.get('style_key')
        if style_key:
            try:
                from organizer import ORGANIZATION_STYLES, OrganizationEngine
                style_cls = ORGANIZATION_STYLES.get(style_key)
                if style_cls:
                    org_engine = OrganizationEngine(
                        style_class=style_cls,
                        output_dir=str(target_dir),
                    )
                    self.log.emit(f"🗂️ Using style: {org_engine.get_style_name()}")
            except Exception as _e:
                self.log.emit(f"⚠️ Could not load style '{style_key}': {_e}")

        moved_count = 0
        for idx, file_path in enumerate(files):
            if self._is_cancelled:
                break

            # Classify with AI
            suggested_folder, confidence = self._classify_texture(file_path)

            # Auto-accept if confidence above threshold
            threshold = self.settings.get('confidence_threshold', 0.8)
            if confidence >= threshold:
                if org_engine:
                    try:
                        from organizer.organization_engine import TextureInfo as _TI
                        ti = _TI(
                            file_path=str(file_path),
                            filename=file_path.name,
                            category=suggested_folder,
                            confidence=confidence,
                        )
                        result = org_engine.organize_textures([ti])
                        if result and result.get('success'):
                            moved_count += 1
                            self._files_processed += 1
                            self.progress.emit(idx + 1, total_files, file_path.name, confidence)
                            continue
                    except Exception as _oe:
                        self.log.emit(f"⚠ Style engine failed for {file_path.name}: {_oe}")

                # Default: move to target_dir / suggested_folder
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
            'elapsed_time': elapsed,
            'files_processed': moved_count,
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
            self._retry_count = 0

            # Inner loop: keep re-classifying the same file until advance() or cancel
            while not self._is_cancelled:
                # Classify: first attempt uses primary strategy; retries use alternatives
                suggested_folder, confidence = self._classify_texture(
                    file_path, skip_top=self._retry_count
                )

                # Load image for preview (only on first pass — PIL already cached)
                image = None
                if PIL_AVAILABLE:
                    try:
                        image = Image.open(file_path)
                    except Exception as e:
                        logger.warning(f"Could not load image {file_path}: {e}")

                # Emit for UI handling
                self.classification_ready.emit(str(file_path), suggested_folder, confidence, image)
                self.progress.emit(index + 1, total_files, file_path.name, confidence)

                # Wait for advance OR retry signal
                self._advance_event.clear()
                self._retry_event.clear()
                # Block until either event fires
                while not self._advance_event.is_set() and not self._retry_event.is_set():
                    if self._is_cancelled:
                        break
                    self._advance_event.wait(timeout=0.1)

                if self._advance_event.is_set():
                    self._advance_event.clear()
                    break  # Move on to next file

                if self._retry_event.is_set():
                    self._retry_event.clear()
                    self._retry_count += 1
                    continue  # Re-classify same file

                if self._is_cancelled:
                    break
            
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
        self._retry_event.clear()

    def retry(self):
        """Signal the worker to re-classify the current file with an alternative suggestion."""
        self._retry_event.set()
        self._advance_event.clear()
    
    def get_current_file_path(self) -> Optional[Path]:
        """Get the full path of the file currently being reviewed."""
        return self._current_file_path
    
    def _collect_files(self, source_dir: Path) -> List[Path]:
        """Collect texture files from source directory."""
        extensions = {'.dds', '.png', '.jpg', '.jpeg', '.tga', '.bmp'}
        files = []
        
        # Get recursive setting from settings dict (thread-safe)
        # Never access UI widgets from worker thread
        recursive = self.settings.get('recursive', True)
        
        if recursive:
            for ext in extensions:
                files.extend(source_dir.rglob(f'*{ext}'))
        else:
            for ext in extensions:
                files.extend(source_dir.glob(f'*{ext}'))
        
        return sorted(files)
    
    # Visual CLIP prompts — describe what the texture LOOKS LIKE, not game names
    _VISUAL_PROMPTS: dict = {
        "character_skin":     "a human or creature skin texture with skin tone colours",
        "character_clothing": "a fabric or cloth texture worn as clothing",
        "character_face":     "a face or head texture with eyes nose and mouth features",
        "environment_ground": "a ground surface texture like dirt grass stone or pavement",
        "environment_wall":   "a wall or building facade texture with bricks tiles or plaster",
        "environment_nature": "a natural organic texture like bark leaves moss or rock",
        "ui_icon":            "a flat icon or symbol graphic on a solid or transparent background",
        "ui_button":          "a user interface button or panel graphic",
        "ui_hud":             "a heads-up display or meter graphic",
        "weapon_metal":       "a metallic weapon surface with specular highlights",
        "vehicle_body":       "a vehicle paint or body panel texture with smooth colour",
        "vehicle_interior":   "a vehicle interior texture with fabric or leather",
        "effect_particle":    "a particle or smoke effect texture with alpha transparency",
        "effect_glow":        "a glow or energy effect texture with bright emissive areas",
        "prop_generic":       "a generic object or prop surface texture",
    }

    # Mapping from CLIP label → folder category name
    _LABEL_TO_CATEGORY: dict = {
        "character_skin":     "Characters/Skin",
        "character_clothing": "Characters/Clothing",
        "character_face":     "Characters/Face",
        "environment_ground": "Environment/Ground",
        "environment_wall":   "Environment/Walls",
        "environment_nature": "Environment/Nature",
        "ui_icon":            "UI/Icons",
        "ui_button":          "UI/Buttons",
        "ui_hud":             "UI/HUD",
        "weapon_metal":       "Weapons",
        "vehicle_body":       "Vehicles/Body",
        "vehicle_interior":   "Vehicles/Interior",
        "effect_particle":    "Effects/Particles",
        "effect_glow":        "Effects/Glow",
        "prop_generic":       "Props",
    }

    def _classify_texture(self, file_path: Path, skip_top: int = 0) -> Tuple[str, float]:
        """
        Classify texture using AI visual analysis (appearance-based, not filename-based).

        Args:
            file_path: Path to the texture file.
            skip_top: Skip the top N results and return the next best alternative.
                      Used by the retry mechanism to suggest alternatives.

        Returns:
            (suggested_folder, confidence)
        """
        if not self.clip_model and not self.dinov2_model:
            return self._heuristic_classification(file_path, skip_top=skip_top)

        try:
            if self.clip_model:
                # Use descriptive visual prompts so CLIP classifies by what it SEES
                results = self.clip_model.classify_image(
                    str(file_path), list(self._VISUAL_PROMPTS.values())
                )
                if results:
                    # Map back from prompt string to label key
                    prompt_to_label = {v: k for k, v in self._VISUAL_PROMPTS.items()}
                    # Sort all results by score descending, skip the top N
                    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
                    # Skip already-suggested top results to surface alternatives
                    idx = min(skip_top, len(sorted_results) - 1)
                    top_prompt, score = sorted_results[idx]
                    label = prompt_to_label.get(top_prompt, "prop_generic")
                    folder = self._LABEL_TO_CATEGORY.get(label, "Misc")
                    # Mark confidence reduction for alternatives so UI can show it
                    adjusted_confidence = float(score) * (0.9 ** skip_top)
                    return folder, adjusted_confidence

        except Exception as e:
            logger.error(f"AI classification failed: {e}")

        return self._heuristic_classification(file_path, skip_top=skip_top)

    def _heuristic_classification(self, file_path: Path, skip_top: int = 0) -> Tuple[str, float]:
        """Filename-based fallback classification with alternative support for retry."""
        name_lower = file_path.stem.lower()

        # Build ordered list of (folder, confidence) candidates by keyword match
        candidates: list = []
        keyword_map = [
            (['skin', 'char', 'player', 'npc', 'enemy', 'body'], "Characters/Skin", 0.65),
            (['face', 'head', 'hair'],                             "Characters/Face", 0.65),
            (['cloth', 'shirt', 'pants', 'outfit'],                "Characters/Clothing", 0.65),
            (['ground', 'floor', 'grass', 'dirt', 'stone', 'pave'], "Environment/Ground", 0.65),
            (['wall', 'brick', 'plaster', 'facade'],               "Environment/Walls", 0.65),
            (['bark', 'leaf', 'moss', 'rock', 'tree', 'nature'],   "Environment/Nature", 0.65),
            (['ui', 'hud', 'menu', 'button', 'icon'],              "UI/Icons", 0.65),
            (['weapon', 'gun', 'sword', 'blade', 'rifle'],         "Weapons", 0.65),
            (['car', 'vehicle', 'bike', 'truck', 'van'],           "Vehicles/Body", 0.65),
            (['smoke', 'fire', 'particle', 'glow', 'spark'],       "Effects/Particles", 0.65),
        ]

        for keywords, folder, confidence in keyword_map:
            if any(kw in name_lower for kw in keywords):
                candidates.append((folder, confidence))

        # Always add Props as the catch-all fallback
        candidates.append(("Props", 0.45))

        # Deduplicate while preserving order
        seen: set = set()
        unique_candidates: list = []
        for folder, conf in candidates:
            if folder not in seen:
                seen.add(folder)
                unique_candidates.append((folder, conf))

        idx = min(skip_top, len(unique_candidates) - 1)
        folder, confidence = unique_candidates[idx]
        adjusted_confidence = confidence * (0.9 ** skip_top)
        return folder, adjusted_confidence
    
    def cancel(self):
        """Cancel the operation."""
        self._is_cancelled = True
        self._advance_event.set()  # Unblock if waiting for user input
        self._retry_event.set()    # Also unblock if waiting in retry loop


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

    finished = pyqtSignal(bool, str, dict)  # success, message, stats
    log = pyqtSignal(str)                  # log message (forwarded from worker)
    
    def __init__(self, parent=None, tooltip_manager=None):
        super().__init__(parent)
        self.tooltip_manager = tooltip_manager
        
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
        """Create the comprehensive UI — left controls, right work area."""
        self.setMinimumSize(700, 500)  # prevent squashed layout
        root = QVBoxLayout(self)
        root.setSpacing(4)
        root.setContentsMargins(8, 8, 8, 8)

        # ── Title bar ──────────────────────────────────────────────────────
        title_label = QLabel("🤖 AI-Powered Texture Organizer")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title_label)

        if VISION_MODELS_AVAILABLE:
            status_label = QLabel("✓ AI Vision Ready — organizes by visual appearance")
            status_label.setStyleSheet("color: #4caf50; font-size: 9pt; font-weight: bold;")
        else:
            status_label = QLabel(
                "⚠️ AI not available — using filename/size heuristics  "
                "│  Install: pip install torch torchvision transformers"
            )
            status_label.setStyleSheet("color: #ff9800; font-size: 9pt;")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(status_label)

        # ── Main horizontal splitter: LEFT = controls, RIGHT = work area ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # ── LEFT PANEL (settings + file IO + buttons) ─────────────────────
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setMinimumWidth(300)
        left_scroll.setMaximumWidth(520)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(4, 4, 4, 4)

        self._create_mode_selection_section(left_layout)
        self._create_file_input_section(left_layout)
        self._create_progress_section(left_layout)
        self._create_action_buttons(left_layout)
        self._create_settings_section(left_layout)
        left_layout.addStretch()

        left_scroll.setWidget(left_container)
        splitter.addWidget(left_scroll)

        # ── RIGHT PANEL (preview + classification) ─────────────────────────
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(6)
        right_layout.setContentsMargins(4, 4, 4, 4)
        self._create_work_area_section(right_layout)
        splitter.addWidget(right_container)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter, 1)

    
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
        self._set_tooltip(help_btn, 'help_button')
        group_layout.addWidget(help_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def _create_mode_selection_section(self, layout):
        """Create mode selection section with descriptive style tooltips."""
        group = QGroupBox("⚙️ Organization Mode & Style")
        group_layout = QVBoxLayout()
        group_layout.setSpacing(6)

        # --- Mode row ---
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("🚀 Automatic — AI classifies & moves instantly", "automatic")
        self.mode_combo.addItem("💡 Suggested — AI proposes, you approve each", "suggested")
        self.mode_combo.addItem("✍️ Manual — you choose folder, AI learns your style", "manual")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self._set_tooltip(self.mode_combo, 'category_selection')
        mode_row.addWidget(self.mode_combo, 1)
        group_layout.addLayout(mode_row)

        # --- Style row with descriptive tooltips ---
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self.style_combo = QComboBox()

        if ORGANIZATION_STYLES:
            for key, style_cls in ORGANIZATION_STYLES.items():
                try:
                    instance = style_cls()
                    display = getattr(instance, 'get_name', lambda: key)()
                except Exception:
                    display = key.replace('_', ' ').title()
                self.style_combo.addItem(display, key)
                tip = _STYLE_DESCRIPTIONS.get(str(key), display)
                self.style_combo.setItemData(
                    self.style_combo.count() - 1, tip,
                    Qt.ItemDataRole.ToolTipRole,
                )
        else:
            self.style_combo.addItem("Default (flat list)", "flat")

        self.style_combo.currentIndexChanged.connect(self._on_style_changed)
        style_row.addWidget(self.style_combo, 1)
        group_layout.addLayout(style_row)

        # Style description label (updates when style changes)
        self.style_description = QLabel()
        self.style_description.setWordWrap(True)
        self.style_description.setStyleSheet(
            "color: #888; font-style: italic; font-size: 9pt; padding: 2px 4px;"
        )
        group_layout.addWidget(self.style_description)

        # Mode description
        self.mode_description = QLabel()
        self.mode_description.setWordWrap(True)
        self.mode_description.setStyleSheet("color: gray; font-size: 9pt; padding: 2px 4px;")
        group_layout.addWidget(self.mode_description)

        group.setLayout(group_layout)
        layout.addWidget(group)

        self._update_mode_description()
        self._on_style_changed(0)   # populate style_description on startup
    
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
        self._set_tooltip(select_source_btn, 'input_browse')
        dir_layout.addWidget(select_source_btn)
        
        group_layout.addLayout(dir_layout)
        
        target_layout = QHBoxLayout()
        self.target_label = QLabel("No target selected")
        self.target_label.setStyleSheet("color: gray;")
        target_layout.addWidget(QLabel("Target:"))
        target_layout.addWidget(self.target_label, 1)
        
        select_target_btn = QPushButton("Browse...")
        select_target_btn.clicked.connect(self._select_target_directory)
        self._set_tooltip(select_target_btn, 'output_browse')
        target_layout.addWidget(select_target_btn)
        
        group_layout.addLayout(target_layout)
        
        # Options - Always enabled with helpful tooltips
        options_layout = QHBoxLayout()
        
        self.archive_input_cb = QCheckBox("📦 Archive Input")
        if not ARCHIVE_AVAILABLE:
            self.archive_input_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_input_cb.setStyleSheet("color: gray;")
        else:
            self._set_tooltip(self.archive_input_cb, 'input_archive_checkbox')
        options_layout.addWidget(self.archive_input_cb)
        
        self.archive_output_cb = QCheckBox("📦 Archive Output")
        if not ARCHIVE_AVAILABLE:
            self.archive_output_cb.setToolTip("⚠️ Archive support not available. Install: pip install py7zr rarfile")
            self.archive_output_cb.setStyleSheet("color: gray;")
        else:
            self._set_tooltip(self.archive_output_cb, 'output_archive_checkbox')
        options_layout.addWidget(self.archive_output_cb)
        
        self.subfolders_cb = QCheckBox("📂 Include Subfolders")
        self.subfolders_cb.setChecked(True)
        self._set_tooltip(self.subfolders_cb, 'recursive_search_checkbox')
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
        group = QGroupBox("🖼️ Preview & Classification")
        group_layout = QVBoxLayout()

        # Horizontal splitter: image preview | classification controls
        work_splitter = QSplitter(Qt.Orientation.Horizontal)
        work_splitter.setChildrenCollapsible(False)

        # Left: Preview Panel
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(4, 4, 4, 4)

        preview_title = QLabel("Image Preview")
        preview_title.setStyleSheet("font-weight: bold; font-size: 10pt;")
        preview_layout.addWidget(preview_title)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(240, 240)
        self.preview_label.setStyleSheet(
            "border: 1px solid #555; background: #1e1e2a; color: #888;"
            "border-radius: 4px;"
        )
        self.preview_label.setText("No image loaded")
        preview_layout.addWidget(self.preview_label, 1)

        self.preview_info_label = QLabel()
        self.preview_info_label.setStyleSheet("color: gray; font-size: 9pt;")
        preview_layout.addWidget(self.preview_info_label)

        work_splitter.addWidget(preview_container)
        
        # Right: Classification Panel
        classification_container = QWidget()
        classification_layout = QVBoxLayout(classification_container)
        classification_layout.setContentsMargins(4, 4, 4, 4)
        classification_layout.setSpacing(6)

        classification_title = QLabel("Classification")
        classification_title.setStyleSheet("font-weight: bold; font-size: 10pt;")
        classification_layout.addWidget(classification_title)

        # AI Suggestion display
        self.suggestion_label = QLabel("AI Suggestion: —")
        self.suggestion_label.setStyleSheet("font-size: 11pt; padding: 4px;")
        self._set_tooltip(self.suggestion_label, 'ai_suggestion_label')
        classification_layout.addWidget(self.suggestion_label)

        self.confidence_label = QLabel("Confidence: —")
        self.confidence_label.setStyleSheet("color: gray; padding: 4px;")
        self._set_tooltip(self.confidence_label, 'ai_confidence_label')
        classification_layout.addWidget(self.confidence_label)

        # Feedback buttons
        feedback_layout = QHBoxLayout()
        self.good_btn = QPushButton("✅ Correct")
        self.good_btn.setStyleSheet("background: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.good_btn.clicked.connect(self._on_good_feedback)
        self.good_btn.setEnabled(False)
        self._set_tooltip(self.good_btn, 'feedback_good_button')
        feedback_layout.addWidget(self.good_btn)

        self.bad_btn = QPushButton("❌ Wrong")
        self.bad_btn.setStyleSheet("background: #f44336; color: white; padding: 8px; font-weight: bold;")
        self.bad_btn.clicked.connect(self._on_bad_feedback)
        self.bad_btn.setEnabled(False)
        # ai_feedback_bad registered first so feedback_bad_button tooltip shows by default
        self._set_tooltip(self.bad_btn, 'ai_feedback_bad')
        self._set_tooltip(self.bad_btn, 'feedback_bad_button')
        feedback_layout.addWidget(self.bad_btn)

        # Retry AI suggestion button
        self.retry_btn = QPushButton("🔄 Retry")
        self.retry_btn.setStyleSheet("padding: 8px;")
        self.retry_btn.clicked.connect(self._on_retry_classification)
        self.retry_btn.setEnabled(False)
        self._set_tooltip(self.retry_btn, 'ai_feedback_retry')
        feedback_layout.addWidget(self.retry_btn)
        classification_layout.addLayout(feedback_layout)

        # Manual override / folder input
        classification_layout.addWidget(QLabel("Manual folder override:"))
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Type target folder name…")
        self.folder_input.textChanged.connect(self._on_folder_text_changed)
        self._set_tooltip(self.folder_input, 'manual_override_input')
        classification_layout.addWidget(self.folder_input)

        # Auto-complete suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(200)
        self.suggestions_list.setMinimumHeight(60)
        self.suggestions_list.itemClicked.connect(self._on_suggestion_selected)
        self._set_tooltip(self.suggestions_list, 'folder_suggestions_list')
        classification_layout.addWidget(self.suggestions_list)

        # Path preview
        self.path_preview_label = QLabel("Path: —")
        self.path_preview_label.setStyleSheet("color: gray; font-style: italic; font-size: 9pt; padding: 3px;")
        classification_layout.addWidget(self.path_preview_label)
        classification_layout.addStretch()

        work_splitter.addWidget(classification_container)
        work_splitter.setStretchFactor(0, 1)
        work_splitter.setStretchFactor(1, 1)

        group_layout.addWidget(work_splitter, 1)
        group.setLayout(group_layout)
        layout.addWidget(group, 1)
    
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
        self.log_text.setMaximumHeight(180)
        self.log_text.setMinimumHeight(60)
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
        # sort_button is the primary ID; analysis_button and batch_operations are
        # also registered so the tutorial covers them when the user hovers here
        self._set_tooltip(self.start_btn, 'analysis_button')
        self._set_tooltip(self.start_btn, 'batch_operations')
        self._set_tooltip(self.start_btn, 'sort_button')  # last = shown first
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel_organization)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)
        self._set_tooltip(self.cancel_btn, 'stop_button')
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.export_learning_btn = QPushButton("📤 Export Learning")
        self.export_learning_btn.clicked.connect(self._export_learning_profile)
        self._set_tooltip(self.export_learning_btn, 'ai_export_training')
        button_layout.addWidget(self.export_learning_btn)
        
        self.import_learning_btn = QPushButton("📥 Import Learning")
        self.import_learning_btn.clicked.connect(self._import_learning_profile)
        self._set_tooltip(self.import_learning_btn, 'ai_import_training')
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
        self._set_tooltip(self.conflict_combo, 'sort_mode_menu')
        org_settings_layout.addWidget(self.conflict_combo)
        
        self.create_backup_cb = QCheckBox("Create Backup")
        self.create_backup_cb.setChecked(True)
        self._set_tooltip(self.create_backup_cb, 'alpha_fix_backup')
        org_settings_layout.addWidget(self.create_backup_cb)
        
        org_settings_layout.addStretch()
        
        group_layout.addLayout(org_settings_layout)
        
        # Clear learning button
        clear_learning_btn = QPushButton("🗑️ Clear Learning History")
        clear_learning_btn.clicked.connect(self._clear_learning_history)
        group_layout.addWidget(clear_learning_btn)

        # Organization Profile Management
        profile_group_layout = QHBoxLayout()

        new_profile_btn = QPushButton("➕ New Profile")
        new_profile_btn.setToolTip("Create a new game organization profile")
        new_profile_btn.clicked.connect(self._new_org_profile)
        self._set_tooltip(new_profile_btn, 'profile_new')
        profile_group_layout.addWidget(new_profile_btn)

        save_profile_btn = QPushButton("💾 Save Profile")
        save_profile_btn.clicked.connect(self._save_org_profile)
        self._set_tooltip(save_profile_btn, 'profile_save')
        profile_group_layout.addWidget(save_profile_btn)

        load_profile_btn = QPushButton("📂 Load Profile")
        load_profile_btn.clicked.connect(self._load_org_profile)
        self._set_tooltip(load_profile_btn, 'profile_load')
        profile_group_layout.addWidget(load_profile_btn)

        group_layout.addLayout(profile_group_layout)
        
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

    def _on_style_changed(self, index: int):
        """Update style description label when style combo changes."""
        key = self.style_combo.currentData() if hasattr(self, 'style_combo') else ""
        desc = _STYLE_DESCRIPTIONS.get(str(key), "")
        if hasattr(self, 'style_description'):
            self.style_description.setText(desc)
    
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
        if hasattr(self, 'retry_btn'):
            self.retry_btn.setEnabled(False)
            self.retry_btn.setToolTip("Ask the AI to try classifying this texture again")
        
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
        if hasattr(self, 'retry_btn'):
            self.retry_btn.setEnabled(False)
        
        # Advance worker to next file
        self._advance_worker()
    
    def _on_retry_classification(self):
        """Re-run AI classification on the current file with an alternative suggestion.

        Records the rejection of the current suggestion to the learning system so
        future classifications improve, then signals the worker to try again.
        """
        if not self.current_filename:
            self._log("⚠ No current file to retry")
            return

        # Record that the current suggestion was rejected — this trains the learning system
        enable_learning = self._get_learning_enabled()
        if enable_learning and self.current_suggested_folder and self.learning_system:
            try:
                self.learning_system.add_learning(
                    filename=self.current_filename,
                    suggested_folder=self.current_suggested_folder,
                    user_choice=self.current_suggested_folder,  # same folder flagged as wrong
                    confidence=self.current_confidence or 0.0,
                    accepted=False,
                )
            except Exception as e:
                logger.debug(f"Learning system update during retry: {e}")

        retry_num = getattr(self.worker_thread, '_retry_count', 0) + 1 if self.worker_thread else 1
        self._log(f"🔄 Retrying classification (attempt #{retry_num}): {self.current_filename}")

        # Disable buttons while the worker re-classifies
        self.good_btn.setEnabled(False)
        self.bad_btn.setEnabled(False)
        if hasattr(self, 'retry_btn'):
            self.retry_btn.setEnabled(False)

        if self.worker_thread and hasattr(self.worker_thread, 'retry'):
            self.worker_thread.retry()
        else:
            # Fallback: advance to next file if retry not supported
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
            'create_backup': backup,
            'style_key': getattr(self.style_combo, 'currentData', lambda: None)(),
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
        retry_count = getattr(self.worker_thread, '_retry_count', 0) if self.worker_thread else 0

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
            if retry_count > 0:
                self.suggestion_label.setText(
                    f"AI Suggestion #{retry_count + 1}: {suggested_folder}"
                )
                self.suggestion_label.setStyleSheet(
                    "font-size: 12pt; color: #1565C0; padding: 5px;"
                )
            else:
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
        if hasattr(self, 'retry_btn'):
            self.retry_btn.setEnabled(True)
            # Update retry button tooltip to show attempt context
            if retry_count > 0:
                self.retry_btn.setToolTip(
                    f"Try another suggestion (attempt #{retry_count + 1})"
                )

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

            # Save operation log to target directory
            try:
                target_dir = self.target_directory or ""
                if target_dir:
                    from organizer import OrganizationEngine
                    _log_path = str(Path(target_dir) / "organization_log.txt")
                    # Write stats-only log (no engine ref here since it lives in the worker)
                    with open(_log_path, 'w', encoding='utf-8') as _lf:
                        _lf.write(f"Organization completed: {message}\n")
                        for k, v in stats.items():
                            _lf.write(f"  {k}: {v}\n")
                    self._log(f"📋 Log saved to {_log_path}")
            except Exception as _le:
                logger.debug(f"Could not save operation log: {_le}")
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

    def _new_org_profile(self):
        """Create a new (blank) organization profile."""
        try:
            from PyQt6.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(
                self, "New Organization Profile", "Profile name:"
            )
            if ok and name.strip():
                self._log(f"New organization profile created: {name.strip()}")
                QMessageBox.information(self, "Profile Created",
                    f"Organization profile '{name.strip()}' created.\n"
                    "Configure the settings above and use Save Profile to persist them.")
        except Exception as e:
            logger.error(f"_new_org_profile: {e}", exc_info=True)

    def _save_org_profile(self):
        """Save current organizer settings to a profile file."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            import json
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Organization Profile", "", "JSON Profile (*.json)"
            )
            if path:
                profile = {
                    'mode': self.mode_combo.currentData() if hasattr(self, 'mode_combo') else 'automatic',
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(profile, f, indent=2)
                self._log(f"Organization profile saved: {path}")
                QMessageBox.information(self, "Saved", f"Profile saved to:\n{path}")
        except Exception as e:
            logger.error(f"_save_org_profile: {e}", exc_info=True)
            QMessageBox.warning(self, "Save Failed", str(e))

    def _load_org_profile(self):
        """Load an organization profile from a file."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            import json
            path, _ = QFileDialog.getOpenFileName(
                self, "Load Organization Profile", "", "JSON Profile (*.json)"
            )
            if path:
                with open(path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                mode = profile.get('mode', 'automatic')
                if hasattr(self, 'mode_combo'):
                    for i in range(self.mode_combo.count()):
                        if self.mode_combo.itemData(i) == mode:
                            self.mode_combo.setCurrentIndex(i)
                            break
                self._log(f"Organization profile loaded: {path}")
                QMessageBox.information(self, "Loaded", f"Profile loaded from:\n{path}")
        except Exception as e:
            logger.error(f"_load_org_profile: {e}", exc_info=True)
            QMessageBox.warning(self, "Load Failed", str(e))
    
    def _log(self, message: str):
        """Add message to log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _set_tooltip(self, widget, text_or_id: str):
        """Set tooltip on a widget — register with cycling system when a widget ID is given."""
        if self.tooltip_manager:
            tip = self.tooltip_manager.get_tooltip(text_or_id) if ' ' not in text_or_id else text_or_id
            widget.setToolTip(tip)
            if hasattr(self.tooltip_manager, 'register'):
                self.tooltip_manager.register(widget, text_or_id if ' ' not in text_or_id else None)
        else:
            widget.setToolTip(text_or_id)
