# AI-Powered Organizer Panel - UI Layout

## Full Panel Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      🤖 AI-Powered Texture Organizer                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌─ 🎮 Game Detection ────────────────────────────────────────────────────┐ │
│ │ ✓ God of War II (SLUS-20917) - Confidence: 95%                        │ │
│ │ [🔍 Detect] [Change] [?]                                               │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ ⚙️ Organization Mode ───────────────────────────────────────────────────┐ │
│ │ Mode: [🚀 Automatic - AI classifies and moves instantly            ▼] │ │
│ │                                                                         │ │
│ │ AI analyzes each texture and automatically moves it into the           │ │
│ │ appropriate folder. Files are moved immediately if confidence is       │ │
│ │ above the threshold.                                                   │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ 📁 File Input/Output ──────────────────────────────────────────────────┐ │
│ │ Source: /home/user/ps2_textures/SLUS-20917                            │ │
│ │         [Browse...]                                                    │ │
│ │                                                                         │ │
│ │ Target: /home/user/organized_textures                                  │ │
│ │         [Browse...]                                                    │ │
│ │                                                                         │ │
│ │ ☐ 📦 Archive Input  ☐ 📦 Archive Output  ☑ 📂 Include Subfolders      │ │
│ │                                                                         │ │
│ │ 1,234 files selected                                                   │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ 🖼️ Work Area ──────────────────────────────────────────────────────────┐ │
│ │                                                                         │ │
│ │  ┌─ Image Preview ────┐  ┌─ Classification ─────────────────────────┐ │ │
│ │  │                     │  │                                          │ │ │
│ │  │   ╔═════════════╗   │  │  AI Suggestion: character/kratos        │ │ │
│ │  │   ║             ║   │  │  Confidence: 95%                        │ │ │
│ │  │   ║   Texture   ║   │  │                                          │ │ │
│ │  │   ║   Preview   ║   │  │  [✅ Good] [❌ Bad]                     │ │ │
│ │  │   ║             ║   │  │                                          │ │ │
│ │  │   ║   512x512   ║   │  │  Manual Override:                       │ │ │
│ │  │   ╚═════════════╝   │  │  [character/kratos               ▼]    │ │ │
│ │  │                     │  │  Suggestions:                            │ │ │
│ │  │ kratos_head_01.png  │  │  • character                             │ │ │
│ │  │ 512x512             │  │  • character/kratos                      │ │ │
│ │  └─────────────────────┘  │  • character/gods                        │ │ │
│ │                            │                                          │ │ │
│ │                            │  Path: /target/character/kratos/         │ │ │
│ │                            └──────────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ 📊 Progress ────────────────────────────────────────────────────────────┐ │
│ │ ████████████████████░░░░░░░░░░░░ 234/1234 files                       │ │
│ │                                                                         │ │
│ │ Processing: kratos_head_01.png (234/1234)     12 files/sec | ETA: 83s │ │
│ │                                                                         │ │
│ │ ┌─ Log ─────────────────────────────────────────────────────────────┐ │ │
│ │ │ [09:04:03] Started organization in Suggested mode                │ │ │
│ │ │ [09:04:05] ✓ Learned: kratos_head_01 → character/kratos         │ │ │
│ │ │ [09:04:07] Processing next file...                               │ │ │
│ │ │ [09:04:09] ✓ Moved: kratos_body_02.png                           │ │ │
│ │ │ [09:04:11] ⚠ Skipped: low confidence (45%)                       │ │ │
│ │ └──────────────────────────────────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ Actions ───────────────────────────────────────────────────────────────┐ │
│ │ [🚀 Start Organization]  [📤 Export Learning]  [📥 Import Learning]   │ │
│ │                                                [🗑️ Clear Log]          │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ 🔧 Settings ───────────────────────────────────────────────────────────┐ │
│ │ AI Model: [CLIP (Recommended)                                      ▼] │ │
│ │                                                                         │ │
│ │ ☑ Enable Learning    Confidence Threshold: [0.80  ▼]                  │ │
│ │                                                                         │ │
│ │ Conflict Resolution: [Number (file_1, file_2...)                   ▼] │ │
│ │ ☑ Create Backup                                                        │ │
│ │                                                                         │ │
│ │ [🗑️ Clear Learning History]                                            │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Game Detection Section
**Purpose**: Auto-detects PS2 game from path  
**Elements**:
- Game name and serial display
- Confidence percentage
- Detect button (manual trigger)
- Change button (manual selection)
- Help button (?)

**States**:
- ✓ Detected (green): `✓ God of War II (SLUS-20917) - Confidence: 95%`
- ⚠ Not detected (gray): `No game detected`

### 2. Organization Mode Section
**Purpose**: Select how AI assists with organization  
**Options**:
1. 🚀 **Automatic**: AI decides, moves files instantly
2. 💡 **Suggested**: AI suggests, user confirms
3. ✍️ **Manual**: User types, AI learns

**Description**: Context-sensitive text explaining selected mode

### 3. File Input/Output Section
**Purpose**: Select source and target directories  
**Elements**:
- Source directory selector with path display
- Target directory selector with path display
- Archive input checkbox (ZIP/7Z/RAR support)
- Archive output checkbox (save as archive)
- Include subfolders checkbox
- File count display

### 4. Work Area Section (Suggested/Manual modes)
**Purpose**: Review and classify textures  

**Left Panel - Image Preview**:
- 300x300 preview area
- Image scaling to fit
- Filename and dimensions below

**Right Panel - Classification**:
- AI suggestion display with confidence
- Good/Bad feedback buttons (green/red)
- Manual override text input
- Auto-complete suggestions list
- Full path preview

### 5. Progress Section
**Purpose**: Show processing status  
**Elements**:
- Progress bar (0-100%)
- Current file being processed
- Files processed count (X/Y)
- Processing speed (files/sec)
- Estimated time remaining (ETA)
- Log window (last 10 actions, auto-scrolling)

### 6. Actions Section
**Purpose**: Primary controls  
**Buttons**:
- Start Organization (green, large)
- Export Learning (save profile)
- Import Learning (load profile)
- Clear Log (clear log window)

### 7. Settings Section
**Purpose**: Configure AI and organization  
**Options**:
- AI Model dropdown (CLIP/DINOv2/Hybrid/None)
- Enable Learning checkbox
- Confidence Threshold slider (0.0-1.0)
- Conflict Resolution dropdown (Skip/Overwrite/Number)
- Create Backup checkbox
- Clear Learning History button

## UI States

### State: Ready
```
Start Organization button: Enabled (green)
Cancel button: Hidden
Progress bar: Hidden
Good/Bad buttons: Disabled
```

### State: Processing (Automatic)
```
Start Organization button: Disabled
Cancel button: Visible, Enabled
Progress bar: Visible, Animating
Status: "Processing: filename.png (X/Y)"
Good/Bad buttons: Disabled
```

### State: Awaiting Feedback (Suggested)
```
Start Organization button: Disabled
Cancel button: Visible, Enabled
Progress bar: Visible
Image preview: Showing current texture
AI suggestion: Displayed with confidence
Good/Bad buttons: Enabled
Manual input: Enabled with suggestions
```

### State: Complete
```
Start Organization button: Enabled
Cancel button: Hidden
Progress bar: 100%
Status: "Successfully organized X files" (green)
Good/Bad buttons: Disabled
```

## Color Scheme

### Status Colors
- **Green**: Success, accepted, high confidence (>80%)
- **Orange**: Warning, medium confidence (60-80%)
- **Red**: Error, rejected, low confidence (<60%)
- **Blue**: Processing, in progress
- **Gray**: Inactive, disabled, not detected

### Confidence Indicators
- 🟢 **90-100%**: Excellent - Very confident
- 🟡 **70-89%**: Good - Reliable
- 🟠 **50-69%**: Fair - Review recommended
- 🔴 **0-49%**: Poor - Manual classification needed

## Keyboard Shortcuts

- **Enter**: Accept suggestion (Good button)
- **Esc**: Reject suggestion (Bad button) / Cancel operation
- **Ctrl+E**: Export learning profile
- **Ctrl+I**: Import learning profile
- **Ctrl+L**: Clear log
- **Ctrl+S**: Start organization
- **↑/↓**: Navigate suggestions list
- **Tab**: Switch between input fields

## Tooltips

All controls have helpful tooltips:
- Hover over buttons for action descriptions
- Hover over checkboxes for feature explanations
- Hover over confidence display for interpretation
- Hover over mode selector for detailed mode descriptions

## Responsive Behavior

- Window resizes: UI elements scale proportionally
- Minimum width: 800px
- Minimum height: 600px
- Splitter between preview and classification is draggable
- Settings section is collapsible (future enhancement)
- Log window has scrollbar for many entries
