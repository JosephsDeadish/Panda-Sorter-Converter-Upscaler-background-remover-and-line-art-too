# PS2 Texture Sorter 🐼

**Author:** Dead On The Inside / JosephsDeadish  
**Version:** 1.0.0  
**License:** TBD

A professional, single-executable Windows application for automatically sorting PS2 texture dumps with advanced AI classification, massive-scale support (200,000+ textures), and a modern panda-themed UI.

![PS2 Texture Sorter](https://img.shields.io/badge/Status-In%20Development-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)

## 🌟 Features

### Core Functionality
- **🤖 Automatic Classification** - 50+ texture categories with AI-powered classification
- **🔄 Format Conversion** - Bidirectional DDS ↔ PNG conversion with quality preservation
- **📊 Massive Scale** - Handle 200,000+ textures efficiently with database indexing
- **🎮 LOD Detection** - Automatically detect and group Level-of-Detail texture sets
- **🗂️ Smart Organization** - 9+ hierarchical organization presets (Sims style, Neopets style, etc.)
- **🔍 Duplicate Detection** - Find duplicate textures by hash or name+size
- **🛡️ File Integrity** - Corruption detection and safe file operations
- **💾 Progress Saving** - Pause/resume operations anytime with auto-save

### User Interface
- **🐼 Interactive Panda Character** - Animated companion with 13 mood states, leveling system, and personality
- **🎨 Full Customization** - Colors, cursors (skull, panda, sword), themes, layouts, custom color palettes
- **💡 4-Level Tooltips** - From expert mode to "Panda Explains It" mode with 250+ tooltip variations that change dynamically
- **🌓 Dark/Light Mode** - Built-in theme switching with 6+ preset themes (themes only affect colors)
- **📊 Real-Time Monitoring** - Live progress for massive operations with detailed statistics
- **📝 Built-in Notepad** - Multi-tab notepad with pop-out support
- **🏆 Achievements & Unlockables** - 50+ achievements, unlockable features, and rewards
- **🛒 In-App Shop** - Spend earned currency on themes, cursors, and customizations
- **🔊 Sound Effects** - Audio feedback with customizable volume
- **❓ Context-Sensitive Help** - Press F1 for help anywhere in the app
- **🖼️ File Browser Thumbnails** - Preview textures directly in the file browser with toggle control
- **📌 Undockable Tabs** - Pop out any tab into its own window for multi-monitor setups

### Panda Companion
- **🐼 Drag & Toss** - Drag the panda and throw it to watch it bounce off walls and floor
- **🎭 13 Mood States** - Happy, excited, working, tired, celebrating, sleeping, sarcastic, rage, drunk, existential, motivating, tech_support, sleepy
- **🎮 Interactive** - Click, pet, rub, shake, spin, feed, and dress up your panda
- **📈 Leveling System** - Both you and the panda gain experience and level up
- **👔 Outfit System** - Dress up your panda with unlocked hats, clothing, shoes, and accessories

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

### For Users (Pre-built EXE)

1. **Download** the latest `PS2TextureSorter.exe` from [Releases](https://github.com/JosephsDeadish/PS2-texture-sorter/releases)
2. **Run** the EXE - No installation required!
3. **Start Sorting** - Select your texture folder and let the magic happen 🐼

### For Developers (Build from Source)

#### Automated Build (Recommended)

**Windows Batch:**
```cmd
git clone https://github.com/JosephsDeadish/PS2-texture-sorter.git
cd PS2-texture-sorter
build.bat
```

**PowerShell:**
```powershell
git clone https://github.com/JosephsDeadish/PS2-texture-sorter.git
cd PS2-texture-sorter
.\build.ps1
```

The build scripts automatically:
- Set up virtual environment
- Install dependencies
- Build single EXE with PyInstaller
- Create `dist/PS2TextureSorter.exe`

#### Manual Build

See [BUILD.md](BUILD.md) for detailed manual build instructions.

## 🎯 Usage

### Basic Workflow

1. **Launch Application** - Run PS2TextureSorter.exe
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

- **UI Settings** - Theme, colors, cursors, tooltips (expert/normal/beginner/panda modes), layout, animation speed, thumbnail controls
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
- **[BUILD.md](BUILD.md)** - Detailed build instructions for developers
- **[CODE_SIGNING.md](CODE_SIGNING.md)** - Guide to signing the EXE for Windows SmartScreen
- **[PANDA_MODE_GUIDE.md](PANDA_MODE_GUIDE.md)** - Complete guide to panda features and interactions
- **[UNLOCKABLES_GUIDE.md](UNLOCKABLES_GUIDE.md)** - Achievement and unlockables system documentation
- **[UI_CUSTOMIZATION_GUIDE.md](UI_CUSTOMIZATION_GUIDE.md)** - UI theming and customization guide
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for new users
- **Built-in Help** - Press F1 anywhere in the application for context-sensitive help

## 🛠️ Development

### Project Structure

```
PS2-texture-sorter/
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
│   │   ├── panda_mode.py        # 250+ tooltip variants & facts
│   │   ├── panda_closet.py      # Panda outfit system
│   │   ├── tutorial_system.py   # Tutorial, tooltips & help
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
│   │   ├── panda_widget.py      # Interactive panda canvas widget
│   │   ├── customization_panel.py # Theme & color customization
│   │   ├── closet_panel.py      # Panda outfit selector
│   │   └── ...                  # Additional UI panels
│   ├── utils/                   # Helper utilities
│   └── resources/               # Icons, cursors, themes, sounds
├── requirements.txt             # Python dependencies
├── build_spec.spec              # PyInstaller configuration
├── file_version_info.txt        # EXE metadata
├── build.bat                    # Automated build (Batch)
├── build.ps1                    # Automated build (PowerShell)
├── sign.bat                     # Code signing script
├── BUILD.md                     # Build guide
└── CODE_SIGNING.md              # Signing guide
```

### Technologies Used

- **Python 3.8+** - Core language
- **CustomTkinter** - Modern UI framework
- **Pillow (PIL)** - Image processing
- **OpenCV** - Advanced image analysis
- **NumPy** - Numerical operations
- **scikit-learn** - Machine learning
- **SQLite** - Database indexing
- **PyInstaller** - Single EXE creation

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🔐 Code Signing

For Windows SmartScreen compatibility and trust:

1. Obtain code signing certificate ($179-$600/year)
2. Update certificate details in `sign.bat`
3. Run: `sign.bat`

See [CODE_SIGNING.md](CODE_SIGNING.md) for complete guide.

## 📦 Building Single EXE

The application is built as a single, portable EXE file:

- **Size:** ~50-100 MB (all dependencies included)
- **No Installation Required** - Run from anywhere
- **USB Compatible** - Fully portable
- **Offline** - Works 100% offline, no internet required
- **Zero Dependencies** - Everything is embedded

### Automated Build

```cmd
# Windows Batch
build.bat

# PowerShell
.\build.ps1
```

Output: `dist/PS2TextureSorter.exe`

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

## 📊 Performance

Tested with:
- ✅ 200,000+ texture files
- ✅ 4K, 8K, 16K textures
- ✅ Multi-GB file sizes
- ✅ Mixed DDS and PNG formats
- ✅ Windows 7, 8, 10, 11

## 🎯 Roadmap

- [x] Complete UI implementation with modern CustomTkinter interface
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
**Repository:** [JosephsDeadish/PS2-texture-sorter](https://github.com/JosephsDeadish/PS2-texture-sorter)

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/JosephsDeadish/PS2-texture-sorter/issues)
- **Discussions:** [GitHub Discussions](https://github.com/JosephsDeadish/PS2-texture-sorter/discussions)

## 🐼 About the Panda Theme

The panda character is more than just a mascot - it's an interactive companion that:
- **Reacts to Your Actions** - 13 mood states including happy, working, celebrating, rage, and even drunk mode
- **Can Be Tossed** - Drag and throw the panda to watch it bounce off walls and floor with physics simulation
- **Levels Up** - Both you and the panda gain experience and level up through app usage
- **Provides Personality** - 250+ tooltip variations ranging from helpful to hilariously sarcastic, with random variants shown each hover
- **Offers Rewards** - Earn Bamboo Bucks currency and unlock achievements through interactions
- **Gives Context Help** - Click, hover, or right-click the panda for tips and Easter eggs
- **Customizable** - Dress up the panda with unlockable outfits, hats, shoes, and accessories
- **Stays Fun** - Optional vulgar/sarcastic tooltip mode for uncensored panda commentary (independent of theme selection)
- **Tooltip Modes** - Switch between Normal, Beginner, and Vulgar Panda tooltip modes instantly without restart
- **Themes** - 6+ color themes (Dark Panda, Light, Cyberpunk, Neon Dreams, Classic Windows, Red Panda) — themes only affect colors, not behavior

The panda makes texture sorting enjoyable while maintaining professional functionality!

---

**Made with 🐼 by Dead On The Inside / JosephsDeadish**