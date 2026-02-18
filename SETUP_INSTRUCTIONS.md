# Setup Instructions for PS2 Texture Sorter

This document provides instructions for setting up the PS2 Texture Sorter application.

## Prerequisites

### System Requirements

The application requires Python 3.9 or higher and several system libraries:

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y \
    libegl1 \
    libgl1 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-cursor0
```

#### Linux (Fedora/RHEL/CentOS)
```bash
sudo dnf install -y \
    mesa-libEGL \
    mesa-libGL \
    libxkbcommon-x11 \
    dbus-libs \
    xcb-util-cursor
```

#### macOS
Most dependencies are available via Homebrew:
```bash
brew install python@3.12
```

#### Windows
No additional system libraries are required on Windows. Just ensure Python 3.9+ is installed.

## Installation

### Option 1: Minimal Installation (Recommended for Basic Use)

For basic texture sorting functionality without heavy ML/AI features:

```bash
pip install -r requirements-minimal.txt
```

This includes:
- PyQt6 (UI framework)
- PyOpenGL (3D rendering)
- Basic image processing (Pillow, OpenCV, scikit-image)
- File operations and utilities

### Option 2: Full Installation (Advanced Features)

For all features including AI classification, upscaling, and advanced tools:

```bash
pip install torch torchvision
pip install timm basicsr realesrgan transformers open-clip-torch
pip install -r requirements.txt
```

**Why three steps?**
- **Step 1** installs PyTorch first, which is large (~700MB) and may require a platform-specific version (e.g., CUDA-enabled). See https://pytorch.org/get-started/locally/ for GPU-specific instructions.
- **Step 2** installs the ML/vision packages that depend on PyTorch.
- **Step 3** installs all remaining dependencies from `requirements.txt`.

This includes everything from minimal installation plus:
- PyTorch and torchvision
- Transformer models (CLIP, ViT)
- Super-resolution models (Real-ESRGAN)
- Open CLIP implementation
- Vector search (FAISS, ChromaDB)
- OCR support

**Note:** The full installation requires ~2-3GB of disk space.

## Running the Application

### GUI Application

To launch the main graphical interface:

```bash
python main.py
```

### Headless/Server Environments

If running on a server without a display (e.g., for testing or CI), use the offscreen platform:

```bash
QT_QPA_PLATFORM=offscreen python main.py
```

Or with Xvfb (virtual framebuffer):

```bash
xvfb-run -a python main.py
```

## Troubleshooting

### ModuleNotFoundError: No module named 'PyQt6'

This error occurs when PyQt6 is not installed. Install the required dependencies:

```bash
pip install PyQt6>=6.6.0 PyOpenGL>=3.1.7 PyOpenGL-accelerate>=3.1.7
```

### ImportError: libEGL.so.1: cannot open shared object file

This error occurs when required system libraries are missing. Install them:

**Ubuntu/Debian:**
```bash
sudo apt-get install libegl1 libgl1 libxkbcommon-x11-0 libdbus-1-3
```

**Fedora/RHEL:**
```bash
sudo dnf install mesa-libEGL mesa-libGL libxkbcommon-x11 dbus-libs
```

### Qt platform plugin error

If you see errors about Qt platform plugins (xcb, etc.), try:

1. Install libxcb-cursor0:
   ```bash
   sudo apt-get install libxcb-cursor0
   ```

2. Use the offscreen platform:
   ```bash
   QT_QPA_PLATFORM=offscreen python main.py
   ```

3. Use Xvfb:
   ```bash
   sudo apt-get install xvfb
   xvfb-run -a python main.py
   ```

### Missing Optional Dependencies

Some features require optional dependencies:

- **Background Removal**: Install `rembg[cpu]` or `rembg[gpu]`
- **SVG Support**: Install `cairosvg` and system Cairo libraries
- **OCR**: Install `pytesseract` and `tesseract-ocr` system package
- **Batch Rename**: Install `piexif`

## Testing the Installation

Run the test script to verify all imports work correctly:

```bash
python test_main_import.py
```

This will verify that:
- PyQt6 can be imported
- Core modules are available
- main.py can be loaded without errors

Expected output:
```
✅ PASS: PyQt6 imports
✅ PASS: Core module imports
✅ PASS: main.py import

🎉 All tests passed! main.py can be imported successfully.
```

## Development

For development, you may want to install additional tools:

```bash
pip install pytest pytest-cov flake8 black mypy
```

## Support

For issues and bug reports, please visit:
https://github.com/JosephsDeadish/PS2-texture-sorter/issues
