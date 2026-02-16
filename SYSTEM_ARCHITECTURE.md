# System Architecture - AI-Powered Organizer Panel

## Complete Integration Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          MAIN APPLICATION                           │
│                          (main.py:413)                              │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   │ instantiates
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OrganizerPanelQt (UI Layer)                      │
│                  (src/ui/organizer_panel_qt.py)                     │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Game       │  │    Mode      │  │   File I/O   │            │
│  │  Detection   │  │  Selection   │  │   Section    │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                  │                  │                     │
│  ┌──────▼──────────────────▼──────────────────▼───────┐            │
│  │            Work Area (Preview + Classification)     │            │
│  └──────────────────────────────────────────────────────┘            │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Progress   │  │   Actions    │  │   Settings   │            │
│  │   Display    │  │   Buttons    │  │    Panel     │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└──────────┬────────────────┬──────────────────┬──────────────────────┘
           │                │                  │
           │                │                  │
           ▼                ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  OrganizerWorker │ │ AILearningSystem │ │ GameIdentifier   │
│  (QThread)       │ │ (Learning Core)  │ │ (Game Detection) │
│                  │ │                  │ │                  │
│ - classify       │ │ - add_learning   │ │ - identify_game  │
│ - organize       │ │ - get_suggestion │ │ - detect_serial  │
│ - emit progress  │ │ - save_profile   │ │ - load_profile   │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Vision Models    │ │ Profile Storage  │ │ Game Database    │
│                  │ │                  │ │                  │
│ - CLIPModel      │ │ - JSON files     │ │ - Known games    │
│ - DINOv2Model    │ │ - Encryption     │ │ - Serials        │
│ - (optional)     │ │ - Export/Import  │ │ - Profiles       │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  OrganizationEngine                          │
│              (src/organizer/organization_engine.py)          │
│                                                              │
│  - organize()                                                │
│  - classify_texture()                                        │
│  - move_files()                                              │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Interaction Flow
```
User Action
    │
    ▼
UI Event Handler
    │
    ├─→ _on_good_feedback()     → AILearningSystem.add_learning()
    ├─→ _on_bad_feedback()      → AILearningSystem.add_learning(accepted=False)
    ├─→ _detect_game()          → GameIdentifier.identify_game()
    ├─→ _start_organization()   → OrganizerWorker.start()
    ├─→ _export_learning()      → AILearningSystem.export_profile()
    └─→ _import_learning()      → AILearningSystem.import_profile()
```

### 2. Classification Flow
```
Texture File
    │
    ▼
OrganizerWorker._classify_texture()
    │
    ├─→ CLIP Model (semantic)        ─┐
    ├─→ DINOv2 Model (visual)        ─┤
    └─→ Pattern-based (fallback)     ─┤
                                      │
                                      ▼
                              Suggested Folder
                                      │
                                      ├─→ Automatic Mode: Move if confidence > threshold
                                      ├─→ Suggested Mode: Show to user for confirmation
                                      └─→ Manual Mode:    User types, AI learns
```

### 3. Learning Flow
```
User Feedback (Good/Bad)
    │
    ▼
AILearningSystem.add_learning()
    │
    ├─→ Extract pattern from filename
    ├─→ Store: (pattern, suggested_folder, user_choice, confidence, accepted)
    └─→ Save to profile JSON
        │
        ▼
Future Classification
    │
    ▼
AILearningSystem.get_suggestion()
    │
    ├─→ Match filename against learned patterns
    ├─→ Score based on similarity
    └─→ Return top N suggestions with confidence
```

### 4. Profile Management Flow
```
Learning Profile
    │
    ├─→ Save: .json (plain text)
    │   └─→ AILearningSystem.save_profile()
    │
    ├─→ Export: .json or .enc (encrypted)
    │   └─→ AILearningSystem.export_profile(password=...)
    │       │
    │       ├─→ Generate random salt (16 bytes)
    │       ├─→ Derive key with PBKDF2HMAC (100k iterations)
    │       ├─→ Encrypt with Fernet (AES)
    │       └─→ Prepend salt to encrypted data
    │
    └─→ Import: .json or .enc
        └─→ AILearningSystem.import_profile(password=...)
            │
            ├─→ Validate format
            ├─→ Decrypt if .enc (extract salt, derive key, decrypt)
            └─→ Merge or replace existing data
```

## Component Dependencies

```
OrganizerPanelQt
    ├── requires: OrganizationEngine
    ├── requires: AILearningSystem
    ├── requires: GameIdentifier (optional, graceful degradation)
    ├── requires: CLIPModel (optional, graceful degradation)
    ├── requires: DINOv2Model (optional, graceful degradation)
    ├── requires: ArchiveHandler (optional, graceful degradation)
    └── requires: PyQt6 (required for UI)

AILearningSystem
    ├── requires: pathlib (standard library)
    ├── requires: json (standard library)
    ├── requires: cryptography (optional, for encryption)
    └── requires: threading.RLock (standard library)

OrganizationEngine
    ├── requires: OrganizationStyles
    ├── requires: TextureInfo
    └── requires: pathlib (standard library)

GameIdentifier
    ├── requires: pathlib (standard library)
    ├── requires: re (standard library)
    └── requires: yaml (optional, for GameIndex.yaml)
```

## File Locations

```
PS2-texture-sorter/
│
├── main.py                                    ← Entry point (Line 413: organizer_panel = OrganizerPanelQt())
│
├── src/
│   ├── ui/
│   │   └── organizer_panel_qt.py            ← Main UI (1,267 lines)
│   │
│   ├── organizer/
│   │   ├── __init__.py                      ← Exports OrganizationEngine, ORGANIZATION_STYLES
│   │   ├── learning_system.py               ← Learning core (590 lines)
│   │   ├── organization_engine.py           ← File organization logic
│   │   └── organization_styles.py           ← 9 organization styles
│   │
│   ├── features/
│   │   ├── game_identifier.py               ← Game detection
│   │   └── profile_manager.py               ← Profile management
│   │
│   ├── vision_models/
│   │   ├── clip_model.py                    ← CLIP integration (optional)
│   │   └── dinov2_model.py                  ← DINOv2 integration (optional)
│   │
│   └── utils/
│       └── archive_handler.py               ← ZIP/7Z support (optional)
│
├── test_organizer_learning.py               ← Unit tests (14 tests)
├── test_organizer_integration.py            ← Integration tests (5 tests)
├── verify_organizer_integration.py          ← Verification script
│
├── docs/
│   ├── AI_ORGANIZER_GUIDE.md                ← User guide
│   ├── AI_ORGANIZER_QUICK_START.md          ← Quick start
│   └── AI_ORGANIZER_UI_LAYOUT.md            ← UI specification
│
├── examples/
│   └── god_of_war_ii_learning_profile.json  ← Example profile
│
├── ORGANIZER_IMPLEMENTATION_SUMMARY.md       ← Technical summary
└── INTEGRATION_STATUS_REPORT.md              ← This verification report
```

## Integration Points in main.py

```python
# Line 74 - Import
from ui.organizer_panel_qt import OrganizerPanelQt

# Lines 413-414 - Instantiation and Tab Addition
organizer_panel = OrganizerPanelQt()
tool_tabs.addTab(organizer_panel, "📁 Texture Organizer")

# Lines 424-429 - Error Handling
except Exception as e:
    logger.error(f"Error loading tool panels: {e}", exc_info=True)
    # Fallback to placeholder
    label = QLabel(f"⚠️ Error loading tool panels: {e}")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    tool_tabs.addTab(label, "Error")
```

## UI Access Path

```
Application Launch (python main.py)
    │
    ▼
Main Window Opens
    │
    ▼
Click "Tools" Tab
    │
    ▼
Click "📁 Texture Organizer" Sub-Tab
    │
    ▼
OrganizerPanelQt UI Displayed
    │
    ├─→ Game Detection Section (top)
    ├─→ Mode Selection Dropdown
    ├─→ File Input/Output Section
    ├─→ Work Area (Preview + Classification)
    ├─→ Progress Display
    ├─→ Action Buttons (Start, Export, Import, Clear)
    └─→ Settings Panel (bottom)
```

## Verification Status

All integration points verified:
- ✅ Import statement present
- ✅ Panel instantiated correctly
- ✅ Tab added to UI
- ✅ Error handling in place
- ✅ All dependencies accessible
- ✅ All methods implemented
- ✅ All tests passing

**System Status**: 🟢 **FULLY INTEGRATED AND OPERATIONAL**
