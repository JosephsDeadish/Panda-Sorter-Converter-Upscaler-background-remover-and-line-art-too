# SVG Build Guide - Game Texture Sorter

This guide explains how to build the Game Texture Sorter with SVG support enabled.

## Table of Contents
- [Why SVG Support is Optional](#why-svg-support-is-optional)
- [Quick Start](#quick-start)
- [Installing Cairo DLLs](#installing-cairo-dlls)
  - [Windows](#windows)
  - [Linux](#linux)
  - [macOS](#macos)
- [Building with SVG Support](#building-with-svg-support)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Alternative: Running from Source](#alternative-running-from-source)

---

## Why SVG Support is Optional

SVG (Scalable Vector Graphics) support requires the Cairo graphics library and its dependencies. On Windows, this means bundling 13+ DLL files with the executable.

**The challenges:**
- Cairo DLLs are not available on GitHub Actions Windows CI runners by default
- Installing GTK3/MSYS2 on CI adds 10+ minutes to build time
- Cairo DLLs add ~15-20 MB to the executable size
- Most users don't work with SVG texture files (they're rare in PS2 game dumps)

**The solution:**
We provide two build options:
1. **Standard build** (`build_spec_onefolder.spec`) - No SVG support, CI-compatible, smaller size
2. **SVG-enabled build** (`build_spec_with_svg.spec`) - Full SVG support, requires Cairo DLLs

The application handles missing SVG support gracefully - it will simply log a warning if you try to load an SVG file without Cairo DLLs.

---

## Quick Start

### Automated Build (Recommended)

The easiest way to build with SVG support:

```bash
python scripts/build_with_svg.py
```

This script will:
1. Check if Cairo DLLs are installed
2. Install required Python packages (cairosvg, cairocffi)
3. Run PyInstaller with SVG support enabled
4. Verify the build and provide instructions

### Manual Build

If you prefer manual control:

```bash
# 1. Set up Cairo DLLs (if not already installed)
python scripts/setup_cairo_dlls.py

# 2. Install Python packages
pip install cairosvg cairocffi pyinstaller

# 3. Build with SVG support
pyinstaller build_spec_with_svg.spec --clean --noconfirm
```

---

## Installing Cairo DLLs

### Windows

#### Option 1: GTK3 Runtime (Recommended for most users)

The GTK3 Runtime is the easiest way to get all Cairo DLLs in one package.

1. **Download the installer:**
   - Visit: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   - Download the latest `gtk3-runtime-x.x.x-x-x-x-ts-win64.exe`

2. **Run the installer:**
   - Use default installation path: `C:\Program Files\GTK3-Runtime Win64`
   - Check "Add to PATH" if prompted (optional but helpful)

3. **Verify installation:**
   ```cmd
   dir "C:\Program Files\GTK3-Runtime Win64\bin\libcairo-2.dll"
   ```

4. **Build:**
   ```bash
   python scripts/build_with_svg.py
   ```

#### Option 2: MSYS2 (For developers)

MSYS2 provides a complete Unix-like environment with package management.

1. **Install MSYS2:**
   - Download from: https://www.msys2.org/
   - Run the installer (default path: `C:\msys64`)

2. **Install GTK3 package:**
   ```bash
   # Open MSYS2 MINGW64 terminal
   pacman -S mingw-w64-x86_64-gtk3
   ```

3. **Verify installation:**
   ```bash
   ls /mingw64/bin/libcairo-2.dll
   # Or in Windows: dir C:\msys64\mingw64\bin\libcairo-2.dll
   ```

4. **Build:**
   ```bash
   python scripts/build_with_svg.py
   ```

#### Option 3: Portable Installation

Create a portable Cairo installation that can be committed to your repository or shared.

1. **Run the setup script:**
   ```bash
   python scripts/setup_cairo_dlls.py
   ```

2. **Follow the prompts:**
   - The script will detect existing Cairo installations
   - Choose to copy DLLs to `cairo_dlls/` folder
   - This creates a portable installation

3. **Commit to repository (optional):**
   ```bash
   git add cairo_dlls/
   git commit -m "Add Cairo DLLs for portable SVG support"
   ```

4. **Build:**
   ```bash
   pyinstaller build_spec_with_svg.spec
   ```

#### Option 4: Environment Variable

If Cairo is installed in a non-standard location:

```cmd
# Set environment variable
set CAIRO_DLL_PATH=C:\path\to\cairo\bin

# Or in PowerShell:
$env:CAIRO_DLL_PATH = "C:\path\to\cairo\bin"

# Build
pyinstaller build_spec_with_svg.spec
```

### Linux

On Linux, Cairo is typically available through the system package manager.

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install libcairo2-dev pkg-config python3-dev

# Install Python packages
pip install cairosvg cairocffi
```

#### Fedora/RHEL:
```bash
sudo dnf install cairo-devel pkg-config python3-devel

# Install Python packages
pip install cairosvg cairocffi
```

#### Arch Linux:
```bash
sudo pacman -S cairo pkgconf

# Install Python packages
pip install cairosvg cairocffi
```

**Note:** On Linux, you typically run the application from source rather than building an executable. PyInstaller on Linux will automatically find system Cairo libraries.

### macOS

On macOS, use Homebrew to install Cairo.

```bash
# Install Cairo via Homebrew
brew install cairo pkg-config

# Install Python packages
pip install cairosvg cairocffi
```

**Note:** On macOS, you typically run the application from source. PyInstaller can create `.app` bundles that include Cairo.

---

## Building with SVG Support

### Automated Build Script

The `build_with_svg.py` script handles everything:

```bash
python scripts/build_with_svg.py
```

**What it does:**
1. Checks Python version (requires 3.8+)
2. Detects Cairo DLLs in common locations
3. Installs PyInstaller if needed
4. Installs cairosvg and cairocffi if needed
5. Runs PyInstaller with `build_spec_with_svg.spec`
6. Verifies the build output
7. Provides next steps and testing instructions

### Manual Build Process

If you prefer to build manually:

**Step 1: Install Prerequisites**
```bash
# Install Python packages
pip install pyinstaller cairosvg cairocffi

# Ensure Cairo DLLs are installed (see sections above)
```

**Step 2: Clean Previous Builds**
```bash
# Windows
rmdir /s /q build dist

# Linux/macOS
rm -rf build dist
```

**Step 3: Run PyInstaller**
```bash
pyinstaller build_spec_with_svg.spec --clean --noconfirm
```

**Step 4: Find Your Executable**
```
dist/
└── GameTextureSorter.exe    (Windows)
    GameTextureSorter         (Linux)
    GameTextureSorter.app     (macOS)
```

### Build Output

When building with SVG support, you'll see:

```
======================================================================
CAIRO DLL DETECTION FOR SVG SUPPORT
======================================================================

Searching for Cairo DLLs in:
  - C:\Program Files\GTK3-Runtime Win64\bin
  - C:\msys64\mingw64\bin

✓ Found 13 Cairo DLLs:
  ✓ libcairo-2.dll
  ✓ libcairo-gobject-2.dll
  ✓ libpng16.dll
  ✓ zlib1.dll
  ... (and 9 more)

✓ All required Cairo DLLs found! SVG support will be available.
======================================================================
```

If DLLs are missing, you'll see warnings about which ones couldn't be found.

---

## Verification

### Verify SVG Support in Built Executable

**Method 1: Check File Size**
- Standard build: ~50-100 MB
- With Cairo DLLs: ~65-120 MB (15-20 MB larger)

**Method 2: Run and Check Logs**

1. Run the executable
2. Open the application
3. Check the console output or log file for:
   ```
   ✓ cairosvg available
   ```

If you see:
```
⚠ cairosvg not available. SVG conversion disabled.
```

Then Cairo DLLs were not properly bundled.

**Method 3: Try Loading an SVG File**

1. Create a simple test SVG file:
   ```xml
   <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
     <circle cx="50" cy="50" r="40" fill="red" />
   </svg>
   ```

2. Save as `test.svg`

3. Try to load it in the application

4. Check if it:
   - ✓ Loads successfully and displays
   - ✗ Shows "cairosvg not available" error

### Verify Python Package Installation

```bash
# Check if packages are installed
python -c "import cairosvg; print('cairosvg:', cairosvg.__version__)"
python -c "import cairocffi; print('cairocffi:', cairocffi.__version__)"
```

Expected output:
```
cairosvg: 2.7.0 (or later)
cairocffi: 1.6.0 (or later)
```

---

## Troubleshooting

### Build succeeds but SVG doesn't work in exe

**Problem:** The exe builds without errors, but SVG files don't load.

**Solutions:**
1. Check that Cairo DLLs were actually found during build:
   - Look for the "CAIRO DLL DETECTION" section in build output
   - Should show "✓ Found X Cairo DLLs"

2. Verify DLLs are in the search paths:
   ```bash
   python scripts/setup_cairo_dlls.py
   ```

3. Try the portable installation method:
   - Copy DLLs to `cairo_dlls/` folder
   - Rebuild

4. Check for DLL version mismatches:
   - Some systems have `libffi-7.dll` instead of `libffi-8.dll`
   - The spec file handles this automatically

### "cairosvg" import error during build

**Problem:** PyInstaller fails with `ModuleNotFoundError: No module named 'cairosvg'`

**Solution:**
```bash
pip install cairosvg cairocffi
```

### Cairo DLLs not found during build

**Problem:** Build output shows "⚠ Missing X Cairo DLLs"

**Solutions:**

1. **Install GTK3 Runtime:**
   - Download from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   - Install to default location
   - Rebuild

2. **Set CAIRO_DLL_PATH:**
   ```cmd
   set CAIRO_DLL_PATH=C:\path\to\your\cairo\bin
   pyinstaller build_spec_with_svg.spec
   ```

3. **Use the setup script:**
   ```bash
   python scripts/setup_cairo_dlls.py
   ```

### "ImportError: DLL load failed" when running exe

**Problem:** The exe runs but crashes when loading SVG files with a DLL error.

**Possible causes:**
1. **Missing DLLs:** Not all required DLLs were bundled
   - Re-run setup script to verify all DLLs
   - Check that all 13+ DLLs are present

2. **Architecture mismatch:** 32-bit vs 64-bit
   - Ensure you're using 64-bit Python and 64-bit Cairo DLLs
   - Check: `python --version` and `python -c "import sys; print(sys.maxsize > 2**32)"`

3. **Dependency DLLs missing:**
   - Some Cairo DLLs depend on others (e.g., libcairo-2.dll needs libpng16.dll)
   - The spec file should bundle all dependencies automatically

### Build is very slow

**Problem:** PyInstaller takes 10+ minutes to build.

**Solutions:**
1. **Disable UPX compression:**
   - Edit `build_spec_with_svg.spec`
   - Change `upx=True` to `upx=False`

2. **Use SSD:** Building on SSD is much faster than HDD

3. **Exclude unnecessary modules:** Already optimized in the spec file

### Exe size is huge (>200 MB)

**Problem:** The executable is larger than expected.

**Explanation:**
- Standard build: ~50-100 MB
- With Cairo: ~65-120 MB
- With AI models: Can be 200+ MB

This is normal for PyInstaller applications. The benefit is zero dependencies for end users.

**To reduce size:**
1. Remove AI/ML features if not needed (see `requirements-minimal.txt`)
2. Enable UPX compression (already enabled by default)
3. Exclude unused packages in the spec file

### "Permission denied" when copying DLLs

**Problem:** Setup script fails to copy DLLs.

**Solutions:**
1. Run as administrator (right-click → "Run as administrator")
2. Check that destination folder is writable
3. Close any running instances of the application

### Linux/macOS: "cairo-devel not found"

**Problem:** Installing cairocffi fails with "cairo-devel not found".

**Solutions:**

**Ubuntu/Debian:**
```bash
sudo apt-get install libcairo2-dev pkg-config python3-dev
```

**macOS:**
```bash
brew install cairo pkg-config
```

**Fedora:**
```bash
sudo dnf install cairo-devel pkg-config python3-devel
```

---

## Alternative: Running from Source

If building with SVG support is too complex, you can run the application directly from Python source with full SVG support.

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Cairo (if not already installed)
# Windows: Install GTK3 Runtime
# Linux: sudo apt-get install libcairo2-dev
# macOS: brew install cairo

# 3. Install SVG packages
pip install cairosvg cairocffi

# 4. Run the application
python main.py
```

### Advantages of Running from Source
- ✓ Full SVG support without building
- ✓ Easier to update and modify
- ✓ Better for development
- ✓ No build complexity

### Disadvantages
- ✗ Requires Python installation
- ✗ Users must install dependencies
- ✗ Not portable (can't run from USB)
- ✗ Startup is slightly slower

---

## Summary

### For Most Users (Windows)

1. Install GTK3 Runtime: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
2. Run: `python scripts/build_with_svg.py`
3. Find your exe in `dist/GameTextureSorter/GameTextureSorter.exe`

### For Developers

1. Run: `python scripts/setup_cairo_dlls.py`
2. Verify DLLs are detected
3. Build: `pyinstaller build_spec_with_svg.spec`

### For CI/CD

Use the standard build without SVG:
```yaml
- name: Build (no SVG)
  run: pyinstaller build_spec_onefolder.spec --clean --noconfirm
```

SVG support can be added in a separate release build with Cairo DLLs.

### For Linux/macOS Users

Install system Cairo package and run from source:
```bash
# Install Cairo
sudo apt-get install libcairo2-dev  # Ubuntu/Debian
brew install cairo                  # macOS

# Install Python packages
pip install cairosvg cairocffi

# Run
python main.py
```

---

## Support

If you encounter issues not covered in this guide:

1. Check the [main BUILD.md](../BUILD.md) guide
2. Review error messages carefully
3. Try the alternative methods above
4. Run diagnostics:
   ```bash
   python scripts/setup_cairo_dlls.py
   ```

---

**Author:** Dead On The Inside / JosephsDeadish  
**Last Updated:** 2024
