# Building Game Texture Sorter

This guide explains how to build the Game Texture Sorter as a single Windows EXE file.

## Quick Start - Automated Build

The easiest way to build is using the automated build scripts:

### Option 1: Windows Batch File (Recommended for most users)
```cmd
build.bat
```

### Option 2: PowerShell Script (Better error handling and progress reporting)
```powershell
.\build.ps1
```

Both scripts will:
1. Check for Python installation
2. Create/activate a virtual environment
3. Install all dependencies
4. Clean previous builds
5. Run PyInstaller to create the single EXE
6. Report success and provide the EXE location

**The build process is fully automated - just run the script!**

## Requirements

- **Python 3.8 or later** (Download from [python.org](https://www.python.org/))
- **Windows 7, 8, 10, or 11**
- **~500 MB free disk space** for dependencies and build
- **Internet connection** (for initial dependency download)

## Manual Build Process

If you prefer to build manually, follow these steps:

### 1. Install Python
Download and install Python 3.8+ from https://www.python.org/
Make sure to check "Add Python to PATH" during installation.

### 2. Set Up Source

Ensure you have the source code, then navigate to the project directory.

### 3. Create Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies
```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Build with PyInstaller
```cmd
pyinstaller build_spec.spec --clean --noconfirm
```

### 6. Find Your EXE
The executable will be in: `dist\GameTextureSorter.exe`

## Build Output

After a successful build, you'll find:

```
dist/
└── GameTextureSorter.exe    <- The standalone executable (50-100 MB)

build/                       <- Temporary build files (can be deleted)
```

## EXE Properties

The built EXE will have:
- **File Name**: GameTextureSorter.exe
- **Version**: 1.0.0
- **Author**: Dead On The Inside / JosephsDeadish
- **Description**: Game Texture Sorter - Automatic texture classification
- **Size**: ~50-100 MB (depending on included resources)
- **Icon**: Panda icon (if available)
- **No external dependencies** - completely standalone
- **Portable** - can run from any location (USB drive compatible)

## Troubleshooting

### Python Not Found
**Error**: `'python' is not recognized as an internal or external command`

**Solution**: Install Python and make sure "Add to PATH" was checked during installation. Or add Python to your PATH manually.

### PyInstaller Not Found
**Error**: `'pyinstaller' is not recognized`

**Solution**: Make sure you activated the virtual environment:
```cmd
venv\Scripts\activate
pip install pyinstaller
```

### Import Errors During Build
**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**: Install the missing dependency:
```cmd
pip install xxx
```
Or reinstall all dependencies:
```cmd
pip install -r requirements.txt --force-reinstall
```

### Large EXE Size
The EXE is large (~50-100 MB) because it includes:
- Python runtime
- All required libraries (PIL, OpenCV, NumPy, etc.)
- UI framework
- Resources

This is normal for single-EXE applications. The benefit is **zero dependencies** for end users.

### UPX Compression Errors
If you get UPX-related errors, edit `build_spec.spec` and change:
```python
upx=True,
```
to:
```python
upx=False,
```

### Icon Not Found
If the build fails due to missing icon, the script will use the default PyInstaller icon. To add a custom panda icon:
1. Create or download a `.ico` file
2. Place it at: `src/resources/icons/panda_icon.ico`
3. Rebuild

## Testing the EXE

After building:

1. **Run directly**: Double-click `dist\GameTextureSorter.exe`
2. **Test portability**: Copy the EXE to a USB drive and run from there
3. **Test on clean Windows**: Copy to a machine without Python installed
4. **Test with 200,000+ files**: Verify massive-scale performance

## Clean Build

To perform a completely clean build:

```cmd
# Delete build artifacts
rmdir /s /q build dist
del *.spec

# Rebuild
build.bat
```

Or in PowerShell:
```powershell
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
.\build.ps1
```

## CI/CD Integration

To integrate with CI/CD pipelines (GitHub Actions, etc.):

```yaml
- name: Build EXE
  run: |
    python -m pip install -r requirements.txt
    pyinstaller build_spec.spec --clean --noconfirm
    
- name: Upload Artifact
  uses: actions/upload-artifact@v3
  with:
    name: GameTextureSorter
    path: dist/GameTextureSorter.exe
```

## Next Steps

After building:
1. Test the EXE thoroughly
2. **Code sign it** (see [CODE_SIGNING.md](CODE_SIGNING.md))
3. Create release package with README
4. Distribute to users

## Support

If you encounter issues:
1. Check this BUILD.md guide
2. Review error messages carefully

---

**Author**: Dead On The Inside / JosephsDeadish
