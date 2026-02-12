# Installation Guide - Game Texture Sorter

This guide covers installation for all platforms with both minimal and full feature sets.

## Table of Contents
- [Quick Start](#quick-start)
- [System Requirements](#system-requirements)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [Windows](#windows)
  - [Linux](#linux)
  - [macOS](#macos)
- [Installation Options](#installation-options)
- [Optional Features](#optional-features)
- [Troubleshooting](#troubleshooting)
- [Verification](#verification)

---

## Quick Start

### Option 1: Minimal Installation (Recommended for most users)
Installs core features without heavy ML dependencies (~200 MB total):
```bash
pip install -r requirements-minimal.txt
python main.py
```

### Option 2: Full Installation
Includes all features including advanced AI classification (~1.5 GB total):
```bash
pip install -r requirements.txt
python main.py
```

### Option 3: Use Pre-built Executable (Windows only)
Download `GameTextureSorter.exe` from releases - no installation needed!

---

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 7+, Linux (Ubuntu 20.04+), macOS 10.15+
- **Python**: 3.8 or later (3.10+ recommended)
- **RAM**: 2 GB (4 GB recommended for large batches)
- **Disk Space**: 
  - Minimal install: 500 MB
  - Full install: 2 GB
- **Display**: 1280x720 or higher

### Recommended Requirements
- **Python**: 3.10 or 3.11
- **RAM**: 8 GB (for AI features and large datasets)
- **Disk Space**: 3 GB (including cache and models)
- **GPU**: CUDA-capable GPU for AI acceleration (optional)

---

## Platform-Specific Instructions

### Windows

#### Step 1: Install Python
1. Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

#### Step 2: Install Dependencies

**Option A - Minimal (Recommended)**
```cmd
pip install -r requirements-minimal.txt
```

**Option B - Full Features**
```cmd
pip install -r requirements.txt
```

#### Step 3: Run Application
```cmd
python main.py
```

#### Optional Windows Features

**RAR Archive Support**
Install WinRAR or 7-Zip, or install unrar command:
```cmd
# Using chocolatey
choco install unrar
```

**OCR Support (for UI text detection)**
1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location (C:\Program Files\Tesseract-OCR)
3. Add to PATH or set environment variable:
   ```cmd
   setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```
4. Install Python wrapper:
   ```cmd
   pip install pytesseract
   ```

---

### Linux

#### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
# Update package list
sudo apt-get update

# Install Python and pip
sudo apt-get install python3 python3-pip python3-venv

# Install system libraries for optional features
sudo apt-get install \
    libcairo2-dev \
    libffi-dev \
    unrar \
    tesseract-ocr \
    libwebp-dev
```

**Fedora/RHEL/CentOS:**
```bash
# Install Python and pip
sudo dnf install python3 python3-pip

# Install system libraries for optional features
sudo dnf install \
    cairo-devel \
    libffi-devel \
    unrar \
    tesseract \
    libwebp-devel
```

**Arch Linux:**
```bash
# Install Python and pip
sudo pacman -S python python-pip

# Install system libraries for optional features
sudo pacman -S cairo unrar tesseract libwebp
```

#### Step 2: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

#### Step 3: Install Python Dependencies

**Option A - Minimal (Recommended)**
```bash
pip install -r requirements-minimal.txt
```

**Option B - Full Features**
```bash
pip install -r requirements.txt
```

#### Step 4: Run Application
```bash
python main.py
```

Or with CLI mode:
```bash
python main.py --cli --input /path/to/textures --output /path/to/sorted
```

#### Linux-Specific Notes

**X11 vs Wayland**: Application works on both X11 and Wayland. If you experience UI issues on Wayland, set:
```bash
export GDK_BACKEND=x11
python main.py
```

**GPU Acceleration (NVIDIA)**: For CUDA support with PyTorch:
```bash
# Check CUDA version
nvidia-smi

# Install CUDA-enabled PyTorch (example for CUDA 11.8)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install GPU-accelerated FAISS
pip install faiss-gpu
```

---

### macOS

#### Step 1: Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Step 2: Install Python and System Dependencies
```bash
# Install Python
brew install python@3.11

# Install system libraries for optional features
brew install cairo libffi tesseract
```

#### Step 3: Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

#### Step 4: Install Python Dependencies

**Option A - Minimal (Recommended)**
```bash
pip install -r requirements-minimal.txt
```

**Option B - Full Features**
```bash
pip install -r requirements.txt
```

#### Step 5: Run Application
```bash
python main.py
```

#### macOS-Specific Notes

**Gatekeeper**: If macOS blocks the application:
```bash
xattr -d com.apple.quarantine /path/to/GameTextureSorter.exe
```

**Apple Silicon (M1/M2/M3)**: PyTorch has native ARM support:
```bash
# Install ARM-optimized PyTorch
pip install torch torchvision
```

---

## Installation Options

### 1. Standard Installation (using pip)
```bash
pip install -r requirements.txt
```

### 2. Package Installation (using setup.py)
```bash
# Install as package
pip install .

# Or in development mode (editable)
pip install -e .

# With optional features
pip install -e ".[svg,ml,ocr]"
```

### 3. With Optional Features (à la carte)
```bash
# Install base + specific features
pip install -r requirements-minimal.txt
pip install cairosvg cairocffi  # SVG support
pip install torch torchvision transformers  # AI features
pip install pytesseract  # OCR support
```

### 4. GPU-Accelerated Installation
```bash
# Install base dependencies
pip install -r requirements-minimal.txt

# Install CUDA-enabled PyTorch (replace cu118 with your CUDA version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install GPU-accelerated FAISS
pip install faiss-gpu

# Install other ML dependencies
pip install transformers timm open-clip-torch chromadb annoy
```

---

## Optional Features

### SVG Vector Graphics Support

**Linux** (Ubuntu/Debian):
```bash
sudo apt-get install libcairo2-dev libffi-dev
pip install cairosvg cairocffi
```

**Linux** (Fedora/RHEL):
```bash
sudo dnf install cairo-devel libffi-devel
pip install cairosvg cairocffi
```

**macOS**:
```bash
brew install cairo libffi
pip install cairosvg cairocffi
```

**Windows**: Works out of the box
```cmd
pip install cairosvg cairocffi
```

### Advanced AI Classification

Requires PyTorch and transformer models (~1 GB download):
```bash
pip install torch torchvision transformers timm open-clip-torch
```

### Vector Similarity Search

For duplicate detection and similar texture finding:
```bash
pip install faiss-cpu chromadb annoy  # CPU version
# OR
pip install faiss-gpu chromadb annoy  # GPU version (requires CUDA)
```

### Image Upscaling (Super-Resolution)

For AI-powered texture upscaling:
```bash
pip install basicsr realesrgan
```

### OCR (Text Detection in UI Elements)

**System Package**: Install Tesseract OCR first
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`

**Python Package**:
```bash
pip install pytesseract
```

---

## Troubleshooting

### Common Issues

#### "Python not found" or "pip not found"
**Solution**: Add Python to PATH
- Windows: Reinstall Python with "Add to PATH" checked
- Linux/macOS: Use `python3` and `pip3` instead

#### "No module named 'tkinter'"
**Solution**: Install tkinter
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora/RHEL
sudo dnf install python3-tkinter

# macOS (usually pre-installed)
brew install python-tk
```

#### "cairosvg not found" or SVG files won't load
**Solution**: Install cairo system library (see [SVG Support](#svg-vector-graphics-support))

#### "torch not found" or AI features disabled
**Solution**: Install PyTorch
```bash
pip install torch torchvision
# Or see https://pytorch.org/get-started/locally/ for your platform
```

#### PIL/Pillow errors
**Solution**: Upgrade Pillow
```bash
pip install --upgrade pillow
```

#### "ImportError: libGL.so.1" (Linux)
**Solution**: Install OpenGL libraries
```bash
sudo apt-get install libgl1-mesa-glx
```

#### "Failed to load _internal/opinfo" (PyTorch warning)
**Solution**: This is a harmless warning. The modules are excluded in PyInstaller builds.

#### Slow performance with large datasets
**Solutions**:
- Ensure numpy and opencv are properly installed
- Use SSD instead of HDD
- Increase RAM allocation
- Enable GPU acceleration (if available)

#### RAR archives won't extract
**Solution**: Install unrar utility
- Windows: Install WinRAR or `choco install unrar`
- Linux: `sudo apt-get install unrar`
- macOS: `brew install unrar`

---

## Verification

### Verify Installation

Run the application with `--version` flag:
```bash
python main.py --version
```

Expected output:
```
Game Texture Sorter v1.0.0
Author: Dead On The Inside / JosephsDeadish
```

### Check Available Features

Run with `--check-features` flag:
```bash
python main.py --check-features
```

This will show which optional dependencies are available.

### Test Basic Functionality

1. **Launch GUI**:
   ```bash
   python main.py
   ```

2. **Test CLI Mode**:
   ```bash
   python main.py --cli --input examples/sample_textures --output test_output
   ```

3. **Check Logs**: Look for errors in the logs directory:
   - Windows: `%APPDATA%\GameTextureSorter\logs`
   - Linux/macOS: `~/.local/share/GameTextureSorter/logs`

---

## Next Steps

After successful installation:

1. **Read the User Guide**: See [README.md](README.md) for usage instructions
2. **Try Examples**: Load sample textures from the `examples/` directory
3. **Configure Settings**: Customize classification and organization rules
4. **Build Executable**: See [BUILD.md](BUILD.md) to create a standalone EXE

---

## Getting Help

If you encounter issues not covered here:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review logs in the application's log directory
3. Search existing issues: https://github.com/JosephsDeadish/PS2-texture-sorter/issues
4. Open a new issue with:
   - Your OS and Python version
   - Full error message and traceback
   - Steps to reproduce the issue

---

**Author**: Dead On The Inside / JosephsDeadish
**Version**: 1.0.0
**Last Updated**: 2026-02-12
