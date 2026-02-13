# Build Scripts - Game Texture Sorter

This directory contains helper scripts for building the application with SVG support.

## Scripts

### `setup_cairo_dlls.py`

**Purpose:** Detect and set up Cairo DLLs for SVG support.

**Usage:**
```bash
python scripts/setup_cairo_dlls.py
```

**What it does:**
1. Searches for Cairo installations in common locations
2. Verifies all required DLLs are present
3. Offers to copy DLLs to `cairo_dlls/` for portable builds
4. Provides installation instructions if Cairo is missing
5. Checks Python package installation (cairosvg, cairocffi)

**When to use:**
- Before building with SVG support for the first time
- To verify your Cairo installation is complete
- To create a portable Cairo DLL package
- To troubleshoot SVG-related build issues

### `build_with_svg.py`

**Purpose:** Automated build script for creating executables with SVG support.

**Usage:**
```bash
python scripts/build_with_svg.py
```

**What it does:**
1. Checks Python version (requires 3.8+)
2. Detects Cairo DLL availability
3. Installs PyInstaller if needed
4. Installs cairosvg/cairocffi if needed
5. Runs PyInstaller with `build_spec_with_svg.spec`
6. Verifies the build output
7. Provides testing instructions

**When to use:**
- To build an executable with SVG support
- When you want automated dependency checking
- For one-command building experience

## Requirements

Both scripts require:
- Python 3.8 or later
- Cairo DLLs installed (for SVG support)
- Internet connection (for package installation)

## See Also

- [SVG_BUILD_GUIDE.md](../docs/SVG_BUILD_GUIDE.md) - Complete guide to building with SVG
- [BUILD.md](../BUILD.md) - General build instructions
- [build_spec_with_svg.spec](../build_spec_with_svg.spec) - PyInstaller spec file with SVG support

## Quick Start

```bash
# 1. Set up Cairo DLLs
python scripts/setup_cairo_dlls.py

# 2. Build with SVG support
python scripts/build_with_svg.py

# 3. Test the executable
dist\GameTextureSorter\GameTextureSorter.exe
```

## Troubleshooting

If you encounter issues:

1. **Cairo DLLs not found:**
   - Run `setup_cairo_dlls.py` and follow the installation instructions
   - See [SVG_BUILD_GUIDE.md](../docs/SVG_BUILD_GUIDE.md) for detailed instructions

2. **Build fails:**
   - Check that all dependencies are installed: `pip install -r requirements.txt`
   - Verify PyInstaller is installed: `pip install pyinstaller`
   - Try building manually: `pyinstaller build_spec_with_svg.spec`

3. **Script errors:**
   - Ensure you're using Python 3.8 or later
   - Check that you're in the repository root directory
   - Review error messages carefully

---

**Author:** Dead On The Inside / JosephsDeadish
