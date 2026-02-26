# SVG Build Guide — Game Texture Sorter

How to build the SVG-enabled executable and use SVG textures.

---

## Overview

SVG support requires the **Cairo graphics library** and its Python bindings
(`cairosvg`, `cairocffi`). Cairo is:

- Included automatically when running from Python source (just `pip install cairosvg cairocffi`)
- **Not included** in the standard EXE (Cairo needs 13+ native Windows DLLs)
- Bundled in the SVG-enabled EXE via `build_spec_with_svg.spec`

For most users working with PS2 texture dumps, SVG files are rare.  
The standard build (no SVG) is recommended for general use.

---

## Running from Source with SVG

### Windows

1. Install the GTK3 runtime (provides Cairo DLLs):
   - Download from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   - Install to the default location

2. Install Python packages:
   ```cmd
   pip install cairosvg cairocffi
   ```

3. Run:
   ```cmd
   python main.py
   ```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get install libcairo2-dev pkg-config python3-dev
pip install cairosvg cairocffi
python main.py
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install cairo-devel pkg-config python3-devel
pip install cairosvg cairocffi
python main.py
```

### macOS

```bash
brew install cairo pkg-config
pip install cairosvg cairocffi
python main.py
```

---

## Building the SVG-Enabled EXE (Windows)

### Automated Build

```cmd
python scripts\build_with_svg.py
```

This script:
1. Detects Cairo DLLs on your system
2. Copies them to the correct location
3. Runs `pyinstaller build_spec_with_svg.spec`
4. Verifies the output

### Manual Build

1. Ensure Cairo DLLs are accessible (install GTK3 Runtime, see above)

2. Install Python packages:
   ```cmd
   pip install cairosvg cairocffi
   ```

3. Run PyInstaller:
   ```cmd
   pyinstaller build_spec_with_svg.spec --clean --noconfirm
   ```

4. Output: `dist\GameTextureSorter\GameTextureSorter.exe`

### Using the PowerShell Build Script

```powershell
.\build.ps1  # Standard build (no SVG)
```

For SVG support, use the `build_spec_with_svg.spec` directly:
```powershell
pyinstaller build_spec_with_svg.spec --clean --noconfirm
```

---

## Cairo DLLs Required on Windows

The SVG spec collects these DLLs automatically when cairosvg/cairocffi are installed:

```
libcairo-2.dll
libglib-2.0-0.dll
libgobject-2.0-0.dll
libgmodule-2.0-0.dll
libffi-7.dll  (or libffi-8.dll)
libpng16-16.dll
libpixman-1-0.dll
libfreetype-6.dll
libfontconfig-1.dll
libexpat-1.dll
zlib1.dll
libbrotlidec.dll
libbrotlicommon.dll
```

If the build fails to collect these, install the GTK3 Runtime first.

---

## Why the Standard Build Excludes SVG

1. **Size**: Cairo DLLs add ~15–20 MB to the EXE
2. **CI compatibility**: GitHub Actions `windows-latest` runners don't have Cairo by default
3. **Rarity**: SVG texture files are uncommon in PS2 game dumps
4. **Graceful fallback**: The app shows a clear message when SVG isn't supported

---

## SVG Behaviour Without Cairo

When Cairo/cairosvg is not available:

- Attempting to load an SVG file shows:
  ```
  ⚠  cairosvg not available. Cannot convert SVG files.
     Install: pip install cairosvg cairocffi
  ```
- All other formats (PNG, DDS, JPEG, WEBP, TGA, TIF, GIF, PCX, BMP) work normally
- The rest of the application is fully functional

---

## Verifying SVG Support

```python
# In Python
try:
    import cairosvg
    print("SVG support: available")
except Exception as e:
    print(f"SVG support: unavailable ({e})")
```

Or using the CLI:
```bash
python main.py --check-features
# Look for:  ✅  SVG support (cairosvg)
```

---

**Author:** Dead On The Inside / JosephsDeadish  
**See also:** [BUILD.md](../BUILD.md) · [INSTALL.md](../INSTALL.md)
