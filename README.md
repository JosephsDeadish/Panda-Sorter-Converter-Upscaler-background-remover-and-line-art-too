# Game Texture Sorter 🐼

**Author:** Dead On The Inside / JosephsDeadish  
**Version:** 1.0.0  
**License:** TBD

A professional Windows application for automatically sorting game texture dumps with advanced AI classification, massive-scale support (200,000+ textures), and a modern panda-themed UI. Distributed as a one-folder package for fast startup and easy customization.

---

## 🧠 Hybrid PyTorch + ONNX Architecture

The app uses a **hybrid AI architecture** designed for batch automation, offline inference, and optional training — all on old/low-spec hardware.

```
┌───────────────────────────────────────────────────────────┐
│                     TRAINING SIDE                          │
│  (optional — requires PyTorch, dev / power-user only)      │
│                                                            │
│  src/ai/training_pytorch.py                                │
│  • Train custom upscalers / classifiers                    │
│  • Fine-tune segmentation models                           │
│  • Experimental architecture search                        │
│  • Export weights → ONNX  ──────────────────┐             │
└─────────────────────────────────────────────┼─────────────┘
                                              │ export_to_onnx()
┌─────────────────────────────────────────────▼─────────────┐
│                    INFERENCE SIDE                          │
│  (always-on, EXE-safe, no torch dependency)                │
│                                                            │
│  src/ai/inference.py  →  OnnxInferenceSession              │
│  • Batch upscaling pipelines                               │
│  • Automated background removal                            │
│  • Offline texture classification                          │
│  • Fast, low-memory, predictable performance               │
└────────────────────────────────────────────────────────────┘
```

### Why this split?

| Concern | Training side (PyTorch) | Inference side (ONNX) |
|---|---|---|
| Flexibility | ✅ Dynamic graphs, autograd | — |
| Cold-start speed | ❌ JIT compilation | ✅ Instant |
| Memory overhead | ❌ High (training state) | ✅ Low |
| Batch throughput | Fine | ✅ Excellent |
| EXE bundle size | ❌ ~700 MB | ✅ ~10 MB |
| Old hardware | ❌ May OOM | ✅ CPU-first |
| Required for main app | ❌ **No** | ✅ **Yes** |

### Installing training extras

Training features are **not** required to run the app. Install PyTorch separately:

```bash
# CPU-only (smallest download)
pip install torch torchvision

# GPU (CUDA 12.1) — see https://pytorch.org/get-started/locally/
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

When PyTorch is absent, training panels are disabled with a clear "install extras" message. Everything else keeps working.

### Background removal (optional rembg)

Background removal uses `rembg` which depends on `onnxruntime`. It is **not** required for the main app and is **lazy-imported** at call time, so a failed DLL load cannot crash the app or the EXE build.

```bash
# CPU backend (recommended)
pip install "rembg[cpu]"

# GPU backend
pip install "rembg[gpu]"
```

If `rembg` fails to import (DLL error, missing onnxruntime provider, `sys.exit(1)` from rembg itself), the app catches `Exception` **and** `SystemExit`, logs a warning, and reports "background removal unavailable" — it does **not** crash.

---

## 🎉 Technical Highlights

### Modern Qt6 Architecture
- **✨ Pure Qt6/PyQt6 UI** - Professional native Qt widgets (tabs, buttons, layouts, events)
- **🎮 OpenGL 3D Rendering** - Hardware-accelerated 3D panda with 60 FPS rendering
- **⚡ Qt State Machine** - Professional animation state control system
- **🔧 Clean Architecture** - No legacy UI frameworks, no compatibility bridges
- Hardware-accelerated graphics with real-time lighting and shadows

## 🌟 Features

### Core Functionality
- **🤖 Automatic Classification** - 50+ texture categories with AI-powered classification
- **🔄 Format Conversion** - Extended format support: DDS, PNG, JPEG, WEBP, SVG, BMP, TGA, TIFF, GIF, PCX
- **📦 Archive Support** - Extract from and compress to ZIP, 7Z, RAR, TAR archives (NEW!)
- **🎮 Game Recognition** - Automatically identifies 70+ PS2 games with texture profiles (EXPANDED!)
- **🎨 HD/4K Support** - NEW: Conditional preprocessing for both PS2 textures AND HD/4K textures
- **🔍 Keyword Search** - NEW: Search textures by typing keywords like "gun", "character face", etc.
- **✨ Alpha Correction** - NEW: Automatically detect and fix alpha colors with PS2 presets and batch processing
- **📊 Massive Scale** - Handle 200,000+ textures efficiently with database indexing
- **🎮 LOD Detection** - Automatically detect and group Level-of-Detail texture sets
- **🗂️ Smart Organization** - 9+ hierarchical organization presets (Sims style, Neopets style, etc.)
- **🔍 Duplicate Detection** - Find duplicate textures by hash or name+size
- **🛡️ File Integrity** - Corruption detection and safe file operations
- **💾 Progress Saving** - Pause/resume operations anytime with auto-save

### AI-Powered Tools
- **🎭 Background Remover** - One-click AI background removal with transparent PNG export
  - 8 optimized alpha presets (PS2 Textures, Gaming Assets, Photography, etc.)
  - Edge refinement controls (feathering, dilation, erosion)
  - 4 AI models (U2-Net, U2-Net Portrait, ISNet variants)
  - Alpha matting for semi-transparent objects
  - Live preview with before/after comparison
  - Archive support (ZIP, 7Z, RAR, TAR)
  - Batch processing with queue management
- **✏️ Object Remover** - Interactive object removal with mask painting
  - 4 selection tools: Brush, Rectangle, Lasso, Magic Wand
  - Adjustable brush size (5-50px) and opacity (10-100%)
  - Undo/Redo stack (50 levels)
  - Color-based selection with tolerance control
  - Real-time mask overlay preview
  - AI-powered content-aware fill
- **📝 Batch Rename Tool** - Professional file renaming with multiple patterns
  - 7 rename patterns: Date, Resolution, Sequential, Custom Templates, Privacy Mode
  - Custom template system with variables ({name}, {index}, {date}, {res})
  - Metadata injection (copyright, author, description) for PNG/JPEG
  - Preview before rename with collision detection
  - Undo support (10 levels) for safety
  - Batch processing with progress tracking
- **🎨 Color Correction Tool** - Professional color grading and enhancement
  - Auto white balance (gray world algorithm)
  - Exposure correction (-3 to +3 EV stops)
  - Vibrance enhancement (selective saturation boost)
  - Clarity enhancement (local contrast/mid-tone sharpness)
  - LUT support (.cube files with adjustable strength 0-100%)
  - Live preview with before/after comparison
  - Batch processing with preset saving
- **🔧 Image Repair Tool** - Fix and recover corrupted images
  - PNG repair (chunk validation, CRC verification, header repair)
  - JPEG repair (marker validation, SOI/EOI recovery)
  - Diagnostic engine (corruption type detection and analysis)
  - Partial recovery (extract readable portions from damaged files)
  - Batch repair with progress tracking
  - Detailed diagnostic reports

### Advanced Features
- **📊 Performance Dashboard** - Real-time system monitoring
  - Processing speed metrics (files/sec, MB/sec)
  - Memory usage tracking (current/peak/available)
  - Queue status display (pending/processing/completed)
  - CPU/GPU usage monitoring
  - Thread count control (1-16 workers)
  - Estimated completion time calculation
- **💾 Auto Backup System** - Automatic crash recovery
  - Periodic auto-save every 5 minutes
  - Crash detection on startup with recovery dialog
  - State preservation (settings, projects, queues, recent files)
  - Configurable retention policy (keep last 10 backups)
  - Manual backup creation option
- **🔍 Quality Checker** - Image quality analysis
  - Resolution detection and warnings
  - DPI calculation for current size
  - Compression artifact detection
  - Upscaling safety warnings
  - Batch quality reports
- **📏 Batch Normalizer** - Standardize image formats
  - Auto-resize to target dimensions
  - Pad to square with transparency
  - Center subject intelligently
  - Format standardization (PNG/JPEG/WebP)
  - Rename according to patterns
- **✏️ Line Art Converter** - Create stencils and line art
  - Convert to pure black linework
  - Adjustable threshold slider
  - Remove midtones automatically
  - 1-bit stencil conversion
  - Expand/contract lines (morphological operations)
  - Clean speckles and noise

### User Interface
- **🐼 Interactive Panda Character** - Animated companion with 13 mood states, leveling system, and personality
- **🎨 Full Customization** - Colors, cursors (skull, panda, sword), themes, layouts, custom color palettes
- **💡 3-Mode Tooltip System** - 210+ tooltips in Normal, Dumbed-Down, and Cursing/Unhinged modes
- **🌓 Dark/Light Mode** - Built-in theme switching with 6+ preset themes (themes only affect colors)
- **📊 Real-Time Monitoring** - Live progress for massive operations with detailed statistics
- **📝 Built-in Notepad** - Multi-tab notepad with pop-out support
- **🏆 Achievements & Unlockables** - 50+ achievements, unlockable features, and rewards
- **🛒 In-App Shop** - Spend earned currency on themes, cursors, and customizations
- **🔊 Sound Effects** - Audio feedback with customizable volume
- **❓ Context-Sensitive Help** - Press F1 for help anywhere in the app
- **🖼️ File Browser Thumbnails** - Preview textures directly in the file browser with toggle control
- **📌 Undockable Tabs** - Pop out any tab into its own window for multi-monitor setups
- **🎨 130+ Animated SVG Icons** - Professional animated icons throughout the UI with smooth easing

### Panda Companion
- **🐼 OpenGL 3D Rendering** - Hardware-accelerated 3D panda with real-time lighting and shadows
- **🎭 20+ Animations** - Including idle, dancing, celebrating, sleeping, working, spinning, shaking, rolling, cartwheel, backflip, stretching, waving, jumping, yawning, sneezing, tail wagging, and more
- **🐾 Drag & Toss** - Drag the panda around the screen, throw it to watch it bounce with realistic physics
- **🎮 Interactive** - Click for random reactions (waving, jumping, celebrating, etc.), pet by rubbing, shake, and spin
- **🎨 Cursor Trail** - Optional colorful cursor trail effect with multiple color themes (rainbow, fire, ice, nature, galaxy, gold)
- **📈 Leveling System** - Both you and the panda gain experience and level up through interactions
- **👔 Full Customization** - Dress your panda with hats, clothing, shoes, and accessories that persist across all animations
- **💬 Speech Bubbles** - Dynamic speech bubbles with context-aware responses
- **🎭 13 Mood States** - Happy, excited, working, tired, celebrating, sleeping, sarcastic, rage, drunk, existential, motivating, tech_support, sleepy
- **🎨 Advanced Animations** - Multiple eye styles (normal, happy, angry, squint, wink, surprised, dizzy, spinning) and mouth expressions (smile, grin, angry, eating, wavy, sleep)

### Performance
- **⚡ Multi-threaded** - Utilize all CPU cores for scanning and processing
- **🗄️ Database Indexing** - SQLite-based indexing for instant searches
- **💨 Streaming Processing** - Low memory footprint for huge files
- **🔄 Incremental Processing** - Pause/resume with session recovery
- **💾 Smart Caching** - LRU cache for thumbnails and previews

### Reliability
- **🔒 Safe Operations** - Transaction-based with rollback on failure
- **📦 Backup System** - Automatic backups before operations
- **🔁 Undo/Redo** - Configurable undo history
- **💥 Crash Recovery** - Automatic session recovery after crashes
- **📋 Operation Logging** - Complete audit trail of all operations

## 📥 Quick Start

### For Users (Pre-built Application)

1. **Download** the latest `GameTextureSorter` folder from the releases page
2. **Run** GameTextureSorter.exe from the folder - No installation required!
3. **Start Sorting** - Select your texture folder and let the magic happen 🐼

### For Developers (Python Installation)

#### Quick Install

**Minimal installation** (recommended for most users):
```bash
pip install -r requirements-minimal.txt
python main.py
```

**Full installation** (with AI features):
```bash
pip install torch torchvision
pip install timm basicsr realesrgan transformers open-clip-torch
pip install -r requirements.txt
python main.py
```

See [INSTALL.md](INSTALL.md) for detailed platform-specific installation instructions (Windows, Linux, macOS).

#### Build from Source

Build a standalone executable using build scripts:

**Windows Batch:**
```cmd
build.bat           # One-folder build
```

**PowerShell:**
```powershell
.\build.ps1         # One-folder build
```

**One-Folder Build** ⭐
- Fast startup (1-3 seconds, no extraction to temp)
- Best overall performance
- External assets for easy modification
- Output: `dist/GameTextureSorter/` folder with EXE + resources

The build scripts automatically:
- Set up virtual environment
- Install dependencies
- Build with PyInstaller
- Create output in `dist/` folder

See [BUILD.md](BUILD.md) for detailed build instructions and troubleshooting.

#### Building with SVG Support

SVG support is optional and requires Cairo DLLs. Two build options are available:

**Standard Build (no SVG):**
```bash
pyinstaller build_spec_onefolder.spec
```

**Build with SVG Support:**
```bash
python scripts/build_with_svg.py
```

The automated script will:
- Detect Cairo DLLs on your system
- Install required Python packages (cairosvg, cairocffi)
- Build the executable with SVG support enabled
- Verify the build output

**Why two build options?**
- Cairo DLLs are not available on CI and add ~15-20 MB to exe size
- Most users don't need SVG support (SVG textures are rare in PS2 dumps)
- Standard build is CI-compatible and smaller
- SVG build provides full format support for users who need it

See [docs/SVG_BUILD_GUIDE.md](docs/SVG_BUILD_GUIDE.md) for detailed instructions including:
- Installing Cairo DLLs (Windows, Linux, macOS)
- Manual build process
- Troubleshooting
- Verification steps


## 🎯 Usage

### Basic Workflow

1. **Launch Application** - Run GameTextureSorter.exe
2. **Select Input Folder** - Choose folder containing PS2 textures
3. **Choose Organization Style** - Select from 9+ presets or create custom
4. **Configure Settings** - Adjust classification, grouping, LOD detection
5. **Start Sorting** - Watch real-time progress as textures are organized
6. **Browse Results** - Use built-in file browser to view organized textures

### Classification Modes

- **Automatic Mode** - AI classifies everything automatically
- **Manual Mode** - You choose category for each texture
- **Suggested Mode** - AI suggests, you confirm
- **Custom Rules** - Create regex patterns for specific files

### Organization Styles

1. **Sims Style** - Gender/Skin/BodyPart/Variant
2. **Neopets Style** - Category/Type/Individual LOD folders
3. **Flat Style** - All LODs in category root
4. **Game Area Style** - Level/Area/Type/Asset
5. **Asset Pipeline Style** - Type/Resolution/Format
6. **Modular Style** - Character/Vehicle/Environment/UI
7. **Minimalist Style** - Simple categories only
8. **Maximum Detail Style** - Deep nested hierarchies
9. **Custom Style** - Build your own with drag-and-drop

### LOD (Level of Detail) Features

Automatically detects and groups:
- `texture_lod0`, `texture_lod1`, `texture_lod2`
- `texture_high`, `texture_med`, `texture_low`
- `texture_0`, `texture_1`, `texture_2`
- Visual similarity detection for unnumbered LODs

## 🔧 Configuration

Settings are stored in: `%USERPROFILE%\.ps2_texture_sorter\config.json`

### Key Settings Categories

- **UI Settings** - Theme, colors, cursors, tooltips (normal/beginner/vulgar), layout, animation speed, thumbnail controls
- **Performance** - Thread count, memory limits, cache size, batch sizes, thumbnail cache
- **File Handling** - Backup options, overwrite behavior, auto-save, undo depth (default 50)
- **Sorting** - Classification mode, organization style, grouping options, LOD detection
- **Logging** - Log level, crash reports, performance metrics
- **Notifications** - Sounds, alerts, completion notifications
- **Panda Settings** - Panda name, gender, position, mood displays, interaction history
- **Tooltip Modes** - Normal, Beginner, Vulgar/Sarcastic Panda (opt-in, controls tooltip text style only)
- **Achievement Tracking** - Enable/disable achievements, notification preferences
- **Hotkeys** - Customizable keyboard shortcuts for all major functions

## 📚 Documentation

- **[README.md](README.md)** - This file: overview and quick start
- **[INSTALL.md](INSTALL.md)** - Installation guide for all platforms (Windows/Linux/macOS)
- **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - Detailed step-by-step setup for every platform
- **[BUILD.md](BUILD.md)** - Build instructions for developers (PyInstaller, CI, hooks)
- **[FAQ.md](FAQ.md)** - Frequently asked questions
- **[docs/SVG_BUILD_GUIDE.md](docs/SVG_BUILD_GUIDE.md)** - SVG support and Cairo build guide
- **[TESTING.md](TESTING.md)** - Testing guide
- **Built-in Help** - Press F1 anywhere in the application for context-sensitive help

## 🆕 What's New

### Alpha Color Correction Tool (NEW!)
Automatically detect and fix alpha channel colors:
- **Intelligent detection**: Analyze alpha distribution and patterns
- **PS2 presets**: Binary, three-level, UI, and smooth gradient presets
- **Batch processing**: Fix multiple images at once with CLI tool
- **Custom thresholds**: Define your own alpha correction rules
- See [INSTALL.md](INSTALL.md#optional-features) for complete alpha correction setup guide

### Archive Support (NEW!)
Full support for working with compressed archives:
- **Extract from archives**: ZIP, 7Z, RAR, TAR.GZ support
- **Compress to archives**: Create ZIP files of sorted/converted textures
- **Browse archives**: View archive contents in file browser
- See [INSTALL.md](INSTALL.md) for archive support details

### Expanded Game Recognition (NEW!)
Comprehensive PS2 game database:
- **70+ games** recognized automatically (expanded from 14)
- All major franchises: GTA, Ratchet & Clank, Tekken, Sly Cooper, etc.
- Popular titles: Okami, Katamari, Psychonauts, Bully, etc.
- Game series: Devil May Cry, Resident Evil, Silent Hill, Final Fantasy, etc.
- See [FAQ.md](FAQ.md) for full game list and recognition details

### HD/4K Texture Support
The preprocessing pipeline now intelligently handles both low-resolution PS2 textures AND high-resolution HD/4K textures:
- **Retro mode** (< 256px): Upscaling + sharpening for PS2 textures
- **HD mode** (> 1024px): Minimal processing to preserve detail in HD/4K textures
- **Consistent embeddings**: Same vision models work across all resolutions
- See [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) for vision model install details

### Extended Format Support
Support for 16+ image formats:
- **Vector**: SVG (with automatic rasterization)
- **Modern**: WEBP, TIFF
- **Standard**: PNG, JPEG, BMP, TGA, GIF, PCX
- **Game**: DDS (with compression support)
- See [docs/SVG_BUILD_GUIDE.md](docs/SVG_BUILD_GUIDE.md) for SVG format details

### Keyword-Based Texture Search
Search for textures using natural language:
- Type "gun" to find weapon textures
- Type "character face" to find portraits
- Type "metal surface" to find metallic textures
- Uses CLIP model for semantic understanding
- Works across all texture resolutions

## 📚 Documentation

### Project Structure

```
GameTextureSorter/
├── main.py                      # Application entry point
├── src/                         # Source code
│   ├── config.py                # Configuration management
│   ├── classifier/              # Texture classification engine
│   │   ├── categories.py        # 50+ category definitions
│   │   └── classifier_engine.py # AI classification logic
│   ├── ai/                      # AI/ML models (offline & online)
│   ├── core/                    # Threading & performance management
│   ├── lod_detector/            # LOD detection system
│   ├── file_handler/            # File operations & conversion
│   ├── database/                # SQLite indexing
│   ├── organizer/               # 9+ organization style presets
│   ├── features/                # Feature modules
│   │   ├── panda_character.py   # Panda moods, animations, interactions
│   │   ├── panda_closet.py      # Panda outfit system
│   │   ├── tutorial_system.py   # Tutorial, tooltips (250+ variants) & help
│   │   ├── achievements.py      # 50+ achievements
│   │   ├── shop_system.py       # In-app shop
│   │   ├── currency_system.py   # Bamboo Bucks currency
│   │   ├── level_system.py      # User & panda leveling
│   │   ├── unlockables_system.py # Unlockable content
│   │   ├── minigame_system.py   # Mini-games for rewards
│   │   ├── hotkey_manager.py    # Global hotkeys
│   │   ├── sound_manager.py     # Audio effects
│   │   ├── statistics.py        # Operation statistics
│   │   └── ...                  # Additional feature modules
│   ├── ui/                      # User interface components
│   │   ├── panda_widget_gl.py    # OpenGL 3D panda widget (replaces old panda_widget.py)
│   │   ├── panda_widget_loader.py # Auto-loader for panda widget
│   │   ├── customization_panel.py # Theme & color customization
│   │   ├── closet_panel.py      # Panda outfit selector
│   │   └── ...                  # Additional UI panels
│   ├── utils/                   # Helper utilities
│   └── resources/               # Icons, cursors, themes, sounds
├── requirements.txt             # Python dependencies
├── build_spec_onefolder.spec     # PyInstaller configuration (one-folder build)
├── file_version_info.txt        # EXE metadata
├── build.bat                    # Automated build (Batch)
├── build.ps1                    # Automated build (PowerShell)
├── sign.bat                     # Code signing script
├── BUILD.md                     # Build guide
└── SETUP_INSTRUCTIONS.md        # Setup guide (all platforms)
```

### Technologies Used

- **Python 3.8+** - Core language
- **PyQt6** - Modern Qt6 UI framework
- **OpenGL** - Hardware-accelerated 3D rendering
- **Pillow (PIL)** - Image processing
- **OpenCV** - Advanced image analysis
- **NumPy** - Numerical operations
- **scikit-learn** - Machine learning
- **SQLite** - Database indexing
- **PyInstaller** - Application packaging (one-folder build)

## 🔐 Code Signing

For Windows SmartScreen compatibility and trust:

1. Obtain code signing certificate ($179-$600/year)
2. Run: `sign.bat`

See [BUILD.md](BUILD.md) for complete build and signing details.

## 📦 Building Application

The application is built as a one-folder distribution for fast startup:

- **No Installation Required** - Run from the folder
- **USB Compatible** - Fully portable
- **Offline** - Works 100% offline, no internet required
- **Zero Dependencies** - Everything is included
- **Fast Startup** - 1-3 seconds (no extraction needed)
- **Customizable** - Modify themes, sounds, and other assets

### Automated Build

```cmd
# Windows Batch
build.bat

# PowerShell
.\build.ps1
```

Output: `dist/GameTextureSorter/GameTextureSorter.exe`

## 🐛 Troubleshooting

### Common Issues

**"Python not found"**
- Install Python 3.8+ from [python.org](https://www.python.org/)
- Ensure "Add to PATH" was checked during installation

**"Module not found" errors**
- Activate virtual environment: `venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Application won't start**
- Check crash logs in `%USERPROFILE%\.ps2_texture_sorter\logs\`
- Try safe mode (feature coming soon)
- Report issue with log file

**Performance issues with 200,000+ files**
- Increase memory limit in settings
- Disable image analysis for speed
- Use incremental processing mode

**Theme switching causes invisible elements or unresponsive UI**
- The application now includes automatic error handling and recovery
- If issues persist, restart the application
- Theme changes are saved and will be restored on next launch

**Panda doesn't appear or is in wrong location**
- The panda uses a separate transparent window and should appear in the bottom-right corner
- Try dragging it to reposition, position is automatically saved
- If panda is off-screen, delete the position config and restart

**Cursor trail not working**
- Enable cursor trail in Settings → UI & Appearance
- Choose from 6 color themes: rainbow, fire, ice, nature, galaxy, gold
- Trail now works across the entire window, not just borders

**Panda animations look choppy**
- Animations use 48 frames for smooth rendering
- Disable panda animations in Settings → Performance for low-end systems
- Ensure no other heavy applications are running

## 📊 Performance

Tested with:
- ✅ 200,000+ texture files
- ✅ 4K, 8K, 16K textures
- ✅ Multi-GB file sizes
- ✅ Mixed DDS and PNG formats
- ✅ Windows 7, 8, 10, 11

## 🎯 Roadmap

- [x] Complete UI implementation with modern PyQt6 interface
- [x] Hardware-accelerated OpenGL rendering for 3D panda companion
- [x] Qt State Machine for animation state control
- [x] Implement all 9 organization presets (Sims, Neopets, Flat, Game Area, Asset Pipeline, Modular, Minimalist, Maximum Detail, Custom)
- [x] Add interactive panda character with moods, animations, and level system
- [x] Achievement system with unlockables
- [x] Currency system and in-app shop
- [x] Comprehensive tutorial system with context-sensitive help
- [x] Advanced statistics tracking
- [ ] Add machine learning training mode
- [ ] Create video tutorials
- [ ] Multi-language support
- [ ] macOS/Linux versions (future consideration)

## 📄 License

License TBD by author. All rights reserved to Dead On The Inside / JosephsDeadish.

## 🙏 Credits

**Author:** Dead On The Inside / JosephsDeadish

## 🐼 About the Panda Theme

The panda character is more than just a mascot - it's an interactive companion that:
- **Hardware-Accelerated 3D Rendering** - OpenGL 3.3 with 60 FPS for smooth, professional animations
- **Real-Time Lighting & Shadows** - Dynamic lighting system with ambient, diffuse, and specular components
- **20+ Unique Animations** - Idle, dancing, celebrating, sleeping, working, spinning, shaking, rolling, cartwheel, backflip, stretching, waving, jumping, yawning, sneezing, tail wagging, and more
- **Reacts to Your Actions** - 13 mood states including happy, working, celebrating, rage, and even drunk mode
- **Multiple Click Responses** - Random animations when clicked including waving, jumping, celebrating, stretching, and dancing for variety
- **Can Be Tossed** - Drag and throw the panda to watch it bounce off walls and floor with realistic physics simulation
- **Exaggerated Physics** - More dramatic movements for spinning (4x faster), shaking (8x faster), and throwing
- **Reduced Sensitivity** - Less likely to trigger spinning/shaking accidentally during normal dragging
- **Cursor Trail Effects** - Optional colorful cursor trail with 6 themes (rainbow, fire, ice, nature, galaxy, gold) that works across the entire window
- **Levels Up** - Both you and the panda gain experience and level up through app usage
- **Provides Personality** - 250+ tooltip variations ranging from helpful to hilariously sarcastic, with random variants shown each hover
- **Offers Rewards** - Earn Bamboo Bucks currency and unlock achievements through interactions
- **Gives Context Help** - Click, hover, or right-click the panda for tips and Easter eggs
- **Fully Customizable** - Dress up the panda with unlockable outfits, hats, shoes, and accessories that persist across all animations
- **Dynamic Speech Bubbles** - Floating speech bubbles with context-aware responses and text wrapping
- **Stays Fun** - Optional vulgar/sarcastic tooltip mode for uncensored panda commentary (independent of theme selection)
- **Tooltip Modes** - Switch between Normal, Beginner, and Vulgar Panda tooltip modes instantly without restart
- **Themes** - 6+ color themes (Dark Panda, Light, Cyberpunk, Neon Dreams, Classic Windows, Red Panda) with improved error handling and recovery

The panda makes texture sorting enjoyable while maintaining professional functionality!

---

**Made with 🐼 by Dead On The Inside / JosephsDeadish**