# Building Game Texture Sorter

This guide explains how to build the Game Texture Sorter for Windows.

## Build Mode

There is **ONE build mode** available:

### One-Folder Mode ⭐
- **Command**: `build.bat` or `.\build.ps1`
- **Output**: Folder with EXE + external assets
- **Pros**: **Much faster startup (1-3 seconds)**, easier asset modification, better performance
- **Cons**: Multiple files to distribute (but as a single folder)
- **Best for**: All use cases - general use, development, testing, distribution

**Note**: Single-EXE mode has been removed because the one-folder mode provides significantly better startup performance and user experience.

## Quick Start - Automated Build

The easiest way to build is using the automated build scripts:

### Option 1: Windows Batch File (Recommended)
```cmd
build.bat           # One-folder build
```

### Option 2: PowerShell Script (Better error handling)
```powershell
.\build.ps1         # One-folder build
```

Both scripts will:
1. Check for Python installation
2. Create/activate a virtual environment
3. Install all dependencies
4. Clean previous builds
5. Run PyInstaller to create the output
6. Report success and provide the location

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

For **one-folder** build:
```cmd
pyinstaller build_spec_onefolder.spec --clean --noconfirm
```

### 6. Find Your Build

The application will be in: `dist\GameTextureSorter\`

## Build Output

### One-Folder Build
After a successful build, you'll find:

```
dist/
└── GameTextureSorter/
    ├── GameTextureSorter.exe     <- Main executable (~10-20 MB)
    ├── _internal/                <- Python runtime + libraries
    ├── resources/                <- Icons, sounds, cursors
    └── app_data/                 <- Config, cache, themes, models
        ├── cache/
        ├── logs/
        ├── themes/
        └── models/
```

**Properties**:
- **Folder Size**: ~100-150 MB total
- **Startup**: **Fast** (1-3 seconds, no extraction needed)
- **Portability**: ✓ Portable folder (copy entire folder)
- **Assets**: ✓ Easily accessible and modifiable
- **Performance**: ✓ Best overall performance

**Common Properties**:
- **Version**: 1.0.0
- **Author**: Dead On The Inside / JosephsDeadish
- **Description**: Game Texture Sorter - Automatic texture classification
- **Icon**: Panda icon (if available)
- **No external dependencies** - no installation required

## Troubleshooting

### Incomplete Extraction Errors

**Error**: Missing libraries or incomplete directory structure

**This is the #1 user error** - it almost always means incomplete extraction!

**Solution**: See [EXTRACTION_TROUBLESHOOTING.md](EXTRACTION_TROUBLESHOOTING.md) for detailed solutions.

**Quick Fix**:
1. Delete the partially extracted folder
2. Re-extract the ENTIRE archive (not just the .exe)
3. Wait for extraction to complete 100%
4. Run from the extracted folder

The application includes automatic detection and user-friendly error messages for this issue.

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

This is normal for PyInstaller applications. The benefit is **zero dependencies** for end users.

### UPX Compression Errors
If you get UPX-related errors, edit `build_spec_onefolder.spec` and change:
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

1. **Run directly**: Double-click `dist\GameTextureSorter\GameTextureSorter.exe`
2. **Test portability**: Copy the entire `GameTextureSorter` folder to a USB drive and run from there
3. **Test on clean Windows**: Copy the folder to a machine without Python installed
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
    pyinstaller build_spec_onefolder.spec --clean --noconfirm
    
- name: Upload Artifact
  uses: actions/upload-artifact@v3
  with:
    name: GameTextureSorter
    path: dist/GameTextureSorter/
```

## Troubleshooting Build Issues

### onnxruntime DLL Load Failed Error

**Error**: `ImportError: DLL load failed while importing onnxruntime_pybind11_state`

**Cause**: onnxruntime's DLL dependencies are not being properly collected by PyInstaller.

**Solution**: The project includes PyInstaller hooks (`hook-onnxruntime.py` and `hook-rembg.py`) that automatically handle this issue. These hooks are automatically used when building with the provided spec files.

If you still encounter this error:

1. **Ensure hooks are being loaded**:
   - Check that `hookspath=[str(SCRIPT_DIR)]` is in your spec file
   - Verify `hook-onnxruntime.py` and `hook-rembg.py` exist in project root

2. **Manually collect DLLs** (if hooks don't work):
   ```python
   # In your spec file, add to binaries:
   import onnxruntime
   onnx_path = os.path.dirname(onnxruntime.__file__)
   capi_dll = os.path.join(onnx_path, 'capi', 'onnxruntime_pybind11_state.pyd')
   binaries.append((capi_dll, 'onnxruntime/capi'))
   ```

3. **Alternative**: Exclude rembg/onnxruntime if not needed:
   ```python
   # In spec file, add to excludes:
   excludes=[
       'onnxruntime',
       'rembg',
   ]
   ```

**Note**: The hooks are already configured in the provided spec files, so this error should not occur with standard builds.

### Other Build Issues

For other build issues, see the error message and:
1. Try cleaning build artifacts: `rmdir /s /q build dist`
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Check Python version is 3.8 or later
4. Try running with `--clean --noconfirm` flags

## Next Steps

After building:
1. Test the EXE thoroughly
2. **Code sign it** (see [CODE_SIGNING.md](CODE_SIGNING.md))
3. Create release package with README
4. Distribute to users

## Native Rust Acceleration (Optional)

The project includes an optional Rust extension module (`native/`) built with
[PyO3](https://pyo3.rs) that significantly speeds up image processing:

- **Lanczos upscaling** – multi-threaded via Rayon, much faster than Python/PIL
- **Perceptual hashing** – fast duplicate/similarity detection
- **Color histogram** – efficient per-channel histogram computation
- **Edge density** – Sobel-based edge measurement
- **Bitmap to SVG** – offline vector tracing via vtracer (NEW!)
- **Batch operations** – process multiple images in parallel

### Dual Vector Conversion Support

The native module now supports **offline bitmap-to-SVG conversion** using pure Rust
libraries (vtracer), eliminating the need for external system dependencies like Cairo.

**Conversion Modes:**

1. **Offline Mode (Native Rust)** ⭐ Recommended
   - Uses vtracer for bitmap-to-vector tracing
   - Zero external dependencies
   - Single binary distribution
   - Multi-threaded via Rayon
   - Good for monochrome and edge-heavy images
   - ~100-300ms per image

2. **Online Mode (cairosvg)** - Optional
   - Only for SVG-to-raster conversion
   - Requires system Cairo libraries
   - Not needed for raster-to-SVG conversion

**Auto Mode:**
- Automatically uses native tracing when available
- Falls back gracefully if unavailable
- Maximum compatibility

### Prerequisites

- [Rust toolchain](https://rustup.rs/) (1.63+)
- Python development headers (usually included with Python)
- [maturin](https://www.maturin.rs/) (`pip install maturin`)

### Building the Native Module

```bash
cd native
maturin build --release
pip install target/wheels/texture_ops-*.whl
```

Or for development (installs directly into current environment):
```bash
cd native
maturin develop --release
```

When the native module is installed the application automatically uses it.
If not installed, pure-Python fallbacks are used – no functionality is lost.

### Installation Paths

**Offline-Only Mode (Recommended):**
```bash
# Install base requirements
pip install -r requirements.txt

# Build and install native module
cd native
maturin develop --release
cd ..
```
Result: Full functionality with zero external dependencies, including offline vector tracing.

**Online Mode (Cairo for SVG-to-raster):**
```bash
# Install base requirements with Cairo support
pip install -r requirements.txt

# Linux only: Install system Cairo libraries
sudo apt-get install libcairo2-dev libffi-dev  # Ubuntu/Debian
sudo dnf install cairo-devel libffi-devel      # Fedora/RHEL
```
Result: Can load existing SVG files as raster, but no raster-to-vector conversion.

**Both Modes (Maximum Features):**
```bash
# Install everything
pip install -r requirements.txt

# Build native module
cd native
maturin develop --release
cd ..
```
Result: Offline vector tracing + Cairo SVG-to-raster support.

## Support

If you encounter issues:
1. Check this BUILD.md guide
2. Review error messages carefully

---

**Author**: Dead On The Inside / JosephsDeadish
