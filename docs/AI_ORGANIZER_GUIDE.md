# AI-Powered Texture Organizer Documentation

## Overview

The AI-Powered Texture Organizer is a comprehensive system for automatically classifying and organizing PS2 game textures using machine learning models. It features a learning system that improves over time based on user feedback.

## Features

### 1. Game Detection
- **Auto-detects PS2 games** from SLUS/SCUS codes in folder paths
- Shows game name, serial, and detection confidence
- Loads game-specific learning profiles automatically
- Supports manual game selection

### 2. Organization Modes

#### Automatic Mode 🚀
- AI analyzes textures and automatically moves them to appropriate folders
- Files are moved instantly if confidence is above threshold (default: 80%)
- Best for: Large batches with high-confidence classifications

#### Suggested Mode 💡
- AI suggests a folder for each texture
- User reviews and confirms or rejects each suggestion
- Feedback helps AI learn preferences
- Best for: Curating organization, training the AI

#### Manual Mode ✍️
- User manually types folder path for each texture
- AI observes choices and learns patterns
- Auto-complete suggestions based on existing folders
- Best for: Full control, teaching AI new categories

### 3. AI Models

#### CLIP (Recommended)
- Image-text embedding model
- Excellent for semantic understanding
- Can classify based on natural language categories
- Examples: "character", "environment", "weapon"

#### DINOv2
- Visual similarity clustering
- Groups textures by appearance
- No text labels needed
- Examples: Similar patterns, colors, structures

#### Hybrid (Highest Accuracy)
- Uses both CLIP and DINOv2
- Combines semantic and visual understanding
- Slower but most accurate

### 4. Learning System

The learning system tracks your classification choices and uses them to improve future suggestions.

#### Learning Profile Structure
```json
{
  "metadata": {
    "version": "1.0",
    "game": "God of War II",
    "game_serial": "SLUS-20917",
    "author": "YourName",
    "created_at": "2024-02-16T10:30:00Z",
    "updated_at": "2024-02-16T15:45:00Z",
    "description": "Custom learning profile for GOW2 textures",
    "encrypted": false
  },
  "learned_mappings": [
    {
      "filename_pattern": "kratos_*",
      "suggested_folder": "character/kratos",
      "user_choice": "character/kratos",
      "confidence": 0.95,
      "accepted": true,
      "timestamp": "2024-02-16T10:35:00Z"
    }
  ],
  "custom_categories": {
    "character/kratos": ["kratos", "god", "warrior"]
  }
}
```

#### Good/Bad Feedback
- **Good Button ✅**: Confirms AI suggestion is correct
  - Saves pattern to learning profile
  - Increases confidence for similar files
  - Helps AI learn your preferences
  
- **Bad Button ❌**: Rejects AI suggestion
  - Records incorrect suggestion
  - Prompts for correct folder
  - AI learns to avoid similar mistakes

#### Profile Operations

**Export Profile**
- Save as `.json` (plain text) or `.enc` (encrypted)
- Include all learned patterns and custom categories
- Share with others or backup

**Import Profile**
- Load `.json` or `.enc` files
- Merge with existing data or replace
- Shows import summary

**Encryption**
- Password-protected profiles
- Uses AES encryption via Fernet
- Requires `cryptography` package

### 5. UI Components

#### Game Detection Section
```
┌─ Game Detection ────────────────────────────────┐
│ ✓ God of War II (SLUS-20917) - Confidence: 95% │
│ [Detect] [Change] [?]                           │
└─────────────────────────────────────────────────┘
```

#### File Input Section
```
┌─ File Input/Output ─────────────────────────────┐
│ Source: /path/to/textures                       │
│ Target: /path/to/organized                      │
│ ☐ Archive Input  ☐ Archive Output  ☑ Subfolders│
│ 1,234 files selected                            │
└─────────────────────────────────────────────────┘
```

#### Work Area (Suggested/Manual Mode)
```
┌─ Work Area ─────────────────────────────────────┐
│ [Image Preview]    │ AI Suggestion: character   │
│                    │ Confidence: 95%            │
│                    │ [✅ Good] [❌ Bad]          │
│                    │                            │
│                    │ Manual Override:           │
│                    │ [character/kratos▼]        │
│                    │ - character                │
│                    │ - character/kratos         │
│                    │ - character/gods           │
│                    │                            │
│                    │ Path: /target/character/   │
│                    │       kratos               │
└─────────────────────────────────────────────────┘
```

#### Progress Display
```
┌─ Progress ──────────────────────────────────────┐
│ ████████████░░░░░░░░ 234/1234 files            │
│ Processing: kratos_head_01.png (234/1234)      │
│ 12 files/sec | ETA: 83s                        │
│                                                 │
│ [09:04:03] Started organization                │
│ [09:04:05] ✓ Learned: kratos_head_01 → char...│
│ [09:04:07] Processing next file...             │
└─────────────────────────────────────────────────┘
```

### 6. Settings

#### AI Model Selection
- Choose between CLIP, DINOv2, Hybrid, or None
- Download/update models button (future feature)

#### Learning Settings
- **Enable Learning**: Toggle to enable/disable learning
- **Confidence Threshold**: 0-100% (default: 80%)
  - Files above threshold are auto-accepted in Automatic mode
- **Auto-accept**: Automatically accept high-confidence suggestions

#### Organization Settings
- **Conflict Resolution**:
  - Skip: Don't overwrite existing files
  - Overwrite: Replace existing files
  - Number: Add _1, _2, etc. to duplicates
  
- **Create Backup**: Backup original files before organizing
- **Naming Pattern**: Template for file naming (future feature)

### 7. Keyboard Shortcuts

- **Enter**: Confirm/Accept suggestion
- **Esc**: Cancel operation
- **Ctrl+E**: Export learning profile
- **Ctrl+I**: Import learning profile
- **Ctrl+L**: Clear log

## Usage Examples

### Example 1: Organize God of War II Textures

1. Select source directory containing SLUS-20917 textures
2. Game is auto-detected: "God of War II (SLUS-20917)"
3. Choose "Suggested" mode for manual curation
4. Select AI Model: "CLIP (Recommended)"
5. Start organization
6. Review each suggestion:
   - `kratos_head.dds` → character/kratos ✅ Good
   - `olympus_bg.dds` → environment/olympus ❌ Bad → environment/temple
7. Export learning profile for later use

### Example 2: Bulk Organize with Automatic Mode

1. Select source directory with 5000+ textures
2. Choose "Automatic" mode
3. Set confidence threshold to 90%
4. Start organization
5. AI processes all files automatically
6. Only low-confidence files (<90%) are skipped for manual review

### Example 3: Train AI from Scratch

1. Select source directory
2. Choose "Manual" mode
3. For each file, type the folder path
4. AI learns patterns from your choices
5. After ~50-100 files, switch to "Suggested" mode
6. AI now makes good suggestions based on learned patterns

## API Usage

### Python API Example

```python
from organizer.learning_system import AILearningSystem

# Create learning system
learning = AILearningSystem()

# Create new profile
learning.create_new_profile(
    game_name="God of War II",
    game_serial="SLUS-20917",
    author="Your Name"
)

# Add learning from user feedback
learning.add_learning(
    filename="kratos_texture.png",
    suggested_folder="character",
    user_choice="character/kratos",
    confidence=0.95,
    accepted=True
)

# Get suggestions for new file
suggestions = learning.get_suggestion("kratos_new_texture.png")
print(f"Top suggestion: {suggestions[0]}")  # ('character/kratos', 0.935)

# Save profile
learning.save_profile()

# Export for sharing
learning.export_profile(Path("my_profile.json"))

# Export encrypted
learning.export_profile(Path("my_profile.enc"), password="secret123")

# Import profile
learning.import_profile(Path("shared_profile.json"), merge=True)
```

## Troubleshooting

### Issue: Game not detected
**Solution**: 
- Ensure folder path contains PS2 serial (SLUS-xxxxx, SCUS-xxxxx)
- Use "Change" button to manually select game
- Check game database in `features/game_identifier.py`

### Issue: AI suggestions are poor
**Solution**:
- Use "Manual" or "Suggested" mode to teach AI
- Provide feedback with Good/Bad buttons
- Collect at least 50-100 examples per category
- Check confidence threshold isn't too high

### Issue: Encryption not available
**Solution**:
- Install cryptography: `pip install cryptography`
- Use plain JSON profiles if encryption isn't needed

### Issue: Slow performance
**Solution**:
- Use "Automatic" mode for bulk operations
- Lower confidence threshold to reduce manual review
- Close other applications to free GPU/CPU resources
- Consider using "None" model for pattern-based classification

## Future Enhancements

- [ ] Fine-tune models on user data
- [ ] Cloud sync for learning profiles
- [ ] Community-shared profiles
- [ ] Automatic category discovery
- [ ] Multi-game batch organization
- [ ] Integration with texture extraction tools
- [ ] Undo/redo for recent actions
- [ ] Preview thumbnails in list view

## Credits

**Author**: Dead On The Inside / JosephsDeadish  
**AI Models**: OpenAI CLIP, Meta DINOv2  
**Framework**: PyQt6, PyTorch  
**License**: See repository LICENSE file
