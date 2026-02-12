# Testing Guide for Game Texture Sorter

This document provides testing procedures for the Game Texture Sorter application.

## Quick Module Test

Test core modules without installing dependencies:

```bash
python test_modules.py
```

This will test:
- Configuration system
- Category definitions
- LOD detector
- Database operations

## Full Application Test

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run Application
```bash
python main.py
```

Expected behavior:
1. Splash screen appears with panda drawn art
2. Loading animation shows progress
3. Main window opens with tabs
4. Can switch between tabs
5. Theme toggle works

## Build Test

### Test Build Scripts

**Windows Batch:**
```cmd
build.bat
```

**PowerShell:**
```powershell
.\build.ps1
```

Expected output:
- Virtual environment created (if not exists)
- Dependencies installed
- PyInstaller runs successfully
- EXE created in `dist/GameTextureSorter.exe`

### Verify EXE

After building:

1. **Check file exists:**
   ```cmd
   dir dist\GameTextureSorter.exe
   ```

2. **Check file size:**
   Should be approximately 50-100 MB

3. **Run EXE:**
   ```cmd
   dist\GameTextureSorter.exe
   ```

4. **Test portability:**
   - Copy EXE to different location
   - Run from USB drive
   - Should work without Python installed

## Functional Tests

### Test 1: Basic UI Navigation
- [ ] Splash screen displays
- [ ] Main window opens
- [ ] All tabs are accessible
- [ ] Theme toggle works
- [ ] Window resizes properly

### Test 2: Directory Selection
- [ ] Browse button opens file dialog
- [ ] Selected path appears in text field
- [ ] Both input and output can be selected

### Test 3: Sorting Options
- [ ] Mode dropdown works (automatic, manual, suggested)
- [ ] Style dropdown works (sims, neopets, etc.)
- [ ] Checkboxes toggle correctly
- [ ] Settings are retained

### Test 4: Texture Sorting (Demo)
1. Select input directory with some image files
2. Select output directory
3. Click "Start Sorting"
4. Verify:
   - [ ] Progress bar updates
   - [ ] Log shows file processing
   - [ ] Can pause operation
   - [ ] Can stop operation
   - [ ] Status bar updates

### Test 5: Settings Tab
- [ ] Settings tab displays
- [ ] Thread slider works
- [ ] Settings are saved

### Test 6: Notepad
- [ ] Can type in notepad
- [ ] Text is retained when switching tabs

### Test 7: About Tab
- [ ] Displays app name and version
- [ ] Shows author information
- [ ] Describes features

## Performance Tests

### Small Scale (< 100 files)
- [ ] Processes quickly
- [ ] No lag in UI
- [ ] Memory usage reasonable

### Medium Scale (100-1,000 files)
- [ ] Handles without issues
- [ ] Progress updates smoothly
- [ ] Can pause/resume

### Large Scale (1,000-10,000 files)
- [ ] Database indexing works
- [ ] No memory leaks
- [ ] Progress tracking accurate

### Massive Scale (200,000+ files)
**Note: Full implementation required for this test**
- [ ] Database handles efficiently
- [ ] Multi-threading utilized
- [ ] Streaming processing works
- [ ] Can pause/resume anytime
- [ ] Memory stays within limits

## Compatibility Tests

### Windows Versions
- [ ] Windows 7
- [ ] Windows 8/8.1
- [ ] Windows 10
- [ ] Windows 11

### Python Versions (Development)
- [ ] Python 3.8
- [ ] Python 3.9
- [ ] Python 3.10
- [ ] Python 3.11
- [ ] Python 3.12

### EXE Tests (No Python Required)
- [ ] Runs on clean Windows (no Python)
- [ ] No external dependencies needed
- [ ] Works from any location
- [ ] USB drive compatible

## Error Handling Tests

### Test Invalid Input
- [ ] Empty directory paths
- [ ] Non-existent directories
- [ ] Invalid file formats
- [ ] Corrupted files

### Expected Behavior
- Error messages displayed
- Application doesn't crash
- Can recover and continue
- Logs errors appropriately

## Integration Tests

### Classifier Test
```python
from src.classifier import TextureClassifier
from pathlib import Path

classifier = TextureClassifier()
result = classifier.classify_texture(Path("test_texture.dds"))
print(f"Category: {result[0]}, Confidence: {result[1]}")
```

### LOD Detector Test
```python
from src.lod_detector import LODDetector

detector = LODDetector()
files = [Path("tex_lod0.dds"), Path("tex_lod1.dds")]
groups = detector.group_lods(files)
print(f"LOD Groups: {groups}")
```

### File Handler Test
```python
from src.file_handler import FileHandler
from pathlib import Path

handler = FileHandler()
# Test conversion
handler.convert_dds_to_png(Path("test.dds"))
```

### Database Test
```python
from src.database import TextureDatabase
from pathlib import Path

db = TextureDatabase(Path("test.db"))
stats = db.get_statistics()
print(f"Statistics: {stats}")
db.close()
```

## Build Verification Checklist

After building the EXE:

- [ ] File size is reasonable (50-100 MB)
- [ ] EXE has proper metadata (right-click → Properties)
  - [ ] File version: 1.0.0.0
  - [ ] Product name: Game Texture Sorter
  - [ ] Author: Dead On The Inside / JosephsDeadish
  - [ ] Description present
- [ ] Icon displays (if custom icon provided)
- [ ] Digital signature tab (if signed)
- [ ] No console window appears (GUI mode)
- [ ] All tabs work
- [ ] Theme toggle works
- [ ] Can select directories
- [ ] Demo sorting works

## Known Limitations (Current Version)

- Full image classification requires dependencies
- Some UI features are placeholders (Convert, Browser tabs)
- Custom cursors not yet implemented
- Tooltip system not fully implemented
- Code signing requires certificate (not included)

## Regression Tests

After any code changes, run:

1. **Module test:** `python test_modules.py`
2. **Main app:** `python main.py` (if deps installed)
3. **Build test:** `build.bat` or `build.ps1`
4. **EXE test:** Run `dist\GameTextureSorter.exe`

## Reporting Issues

When reporting bugs, include:

1. Windows version
2. Python version (if applicable)
3. Steps to reproduce
4. Expected vs actual behavior
5. Error messages or logs
6. Screenshots (for UI issues)

## Test Data

For testing, use:
- Sample texture files (DDS, PNG)
- Various file sizes (KB to MB)
- Different resolutions (64x64 to 4096x4096)
- LOD sequences
- Mixed file types

Create test directory structure:
```
test_textures/
├── characters/
│   ├── hero_lod0.dds
│   ├── hero_lod1.dds
│   └── hero_lod2.dds
├── environments/
│   ├── grass.png
│   └── rock_wall.dds
└── ui/
    ├── button.png
    └── icon.png
```

## Automated Testing (Future)

Planned automated tests:
- Unit tests for each module
- Integration tests
- UI automation tests
- Performance benchmarks
- Stress tests with 200,000+ files

---

**Note:** This is a living document. Update as new features are added or issues are discovered.
