# Quick Start Guide - PS2 Texture Sorter

**Get up and running in 5 minutes! 🐼**

## For End Users (No Programming Experience Needed)

### Step 1: Download
Download `PS2TextureSorter.exe` from the [Releases](https://github.com/JosephsDeadish/PS2-texture-sorter/releases) page.

### Step 2: Run
Double-click `PS2TextureSorter.exe` - that's it! No installation required.

### Step 3: Sort Your Textures
1. Click **"Sort Textures"** tab
2. Click **"Browse..."** next to Input Directory
3. Select folder with your PS2 textures
4. Click **"Browse..."** next to Output Directory
5. Choose where to save sorted textures
6. Choose options (Automatic mode recommended for first time)
7. Click **"▶️ Start Sorting"**
8. Watch the magic happen! 🎉

---

## For Developers (Building from Source)

### Option A: Automated Build (Easiest)

**Windows Batch:**
```cmd
git clone https://github.com/JosephsDeadish/PS2-texture-sorter.git
cd PS2-texture-sorter
build.bat
```

**PowerShell (Recommended):**
```powershell
git clone https://github.com/JosephsDeadish/PS2-texture-sorter.git
cd PS2-texture-sorter
.\build.ps1
```

The script will:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Build single EXE
- ✅ Place it in `dist/PS2TextureSorter.exe`

**Done! Your EXE is ready.**

### Option B: Run from Source (Testing/Development)

```bash
# 1. Clone
git clone https://github.com/JosephsDeadish/PS2-texture-sorter.git
cd PS2-texture-sorter

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python main.py
```

### Option C: Quick Module Test (No Dependencies)

Want to test core modules without installing anything?

```bash
python test_modules.py
```

This tests:
- Configuration system
- LOD detector
- Database operations
- Category definitions

---

## Features At A Glance

| Feature | Status | Description |
|---------|--------|-------------|
| 🗂️ **Sort Textures** | ✅ Working | Automatic classification into 50+ categories |
| 🔄 **Convert Files** | 🚧 Planned | DDS ↔ PNG batch conversion |
| 📁 **File Browser** | 🚧 Planned | Browse sorted textures with previews |
| ⚙️ **Settings** | 🚧 Partial | Customize sorting behavior |
| 📝 **Notepad** | ✅ Working | Built-in notepad for notes |
| 🐼 **Panda Theme** | ✅ Working | Fun, modern interface |
| 🌓 **Dark/Light Mode** | ✅ Working | Toggle between themes |
| 📊 **Progress Tracking** | ✅ Working | Real-time progress for operations |

---

## Sorting Options Explained

### Modes
- **Automatic**: AI decides categories (recommended for most users)
- **Manual**: You choose category for each file
- **Suggested**: AI suggests, you confirm

### Organization Styles
- **Sims Style**: Gender/Skin/BodyPart structure
- **Neopets Style**: Category/Type/Individual folders
- **Flat Style**: Simple category folders
- **Game Area**: Organized by game levels/areas
- **Modular**: Character/Vehicle/Environment separation

### Options
- ✅ **Detect LODs**: Find texture LOD sets (lod0, lod1, high, med, low)
- ✅ **Group LODs**: Keep LOD sets together in same folder
- ✅ **Detect Duplicates**: Find duplicate files by hash

---

## Common Questions

### Q: Do I need to install Python?
**A:** No! The EXE is standalone. Python only needed for building from source.

### Q: Is my data safe?
**A:** Yes! The app creates backups before moving files. You can enable "Create Backup" in settings.

### Q: How many files can it handle?
**A:** The app is designed for massive scale - tested up to 200,000+ textures.

### Q: Does it work offline?
**A:** Yes! 100% offline operation. No internet required.

### Q: What file formats are supported?
**A:** Currently DDS, PNG, JPG, JPEG, TGA, BMP. More formats coming soon.

### Q: Can I customize the categories?
**A:** Yes! Custom categories coming in next update. Currently 50+ built-in categories.

### Q: Why is the EXE so large (~50-100 MB)?
**A:** It includes all dependencies (Python runtime, libraries, UI framework) so you don't need to install anything.

---

## Troubleshooting

### "Windows protected your PC" warning
This is Windows SmartScreen. Click "More info" → "Run anyway". Or see [CODE_SIGNING.md](CODE_SIGNING.md) to sign the EXE yourself.

### Application won't start
- Make sure you have Windows 7 or later
- Try running as administrator (right-click → "Run as administrator")
- Check for error logs in: `%USERPROFILE%\.ps2_texture_sorter\logs\`

### "Python not found" (when building)
- Install Python 3.8+ from [python.org](https://www.python.org/)
- Make sure to check "Add Python to PATH" during installation

### Build fails
- Make sure you have internet connection (to download dependencies)
- Try deleting `venv` folder and running build script again
- See [BUILD.md](BUILD.md) for detailed troubleshooting

---

## Next Steps

### After Basic Sorting
1. Browse sorted textures in output directory
2. Verify categories are correct
3. Adjust settings if needed
4. Sort more texture packs!

### Advanced Usage
- Read [TESTING.md](TESTING.md) for detailed features
- Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for roadmap
- See [BUILD.md](BUILD.md) for building options

### Contributing
- Found a bug? Open an issue on GitHub
- Have a feature idea? Open a discussion
- Want to contribute code? Fork and PR!

---

## Support & Resources

- 📖 **Full Documentation**: See [README.md](README.md)
- 🔨 **Build Guide**: [BUILD.md](BUILD.md)
- ✍️ **Code Signing**: [CODE_SIGNING.md](CODE_SIGNING.md)
- 🧪 **Testing**: [TESTING.md](TESTING.md)
- 📊 **Project Status**: [PROJECT_STATUS.md](PROJECT_STATUS.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/JosephsDeadish/PS2-texture-sorter/issues)

---

## Credits

**Author:** Dead On The Inside / JosephsDeadish  
**Repository:** [JosephsDeadish/PS2-texture-sorter](https://github.com/JosephsDeadish/PS2-texture-sorter)

---

🐼 **Happy Texture Sorting!** 🐼
