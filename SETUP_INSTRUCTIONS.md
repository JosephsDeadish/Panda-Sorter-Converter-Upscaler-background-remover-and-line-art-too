# Setup Instructions — Game Texture Sorter

This guide covers every install scenario from a clean machine.

---

## 1. Windows — Full Install (Recommended)

```cmd
# 1. Install Python 3.11 from https://www.python.org/downloads/
#    ✅ Check "Add Python to PATH" in the installer.

# 2. Clone or download the repository
git clone https://github.com/JosephsDeadish/Panda-Sorter-Converter-Upscaler-background-remover-and-line-art-too.git
cd Panda-Sorter-Converter-Upscaler-background-remover-and-line-art-too

# 3. Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# 4. Install PyTorch first (CPU build — fast download)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 5. Install all other dependencies
pip install -r requirements.txt

# 6. Launch
python main.py
```

**Verify the install:**
```cmd
python main.py --version
python main.py --check-features
```

---

## 2. Windows — Minimal Install (Faster, No AI Training)

```cmd
pip install -r requirements-minimal.txt
python main.py
```

All core sorting, conversion and batch-rename features work.  
AI training/classification and background removal require the full install.

---

## 3. Windows — Use the Pre-built EXE (No Python Needed)

1. Go to the [Releases](https://github.com/JosephsDeadish/Panda-Sorter-Converter-Upscaler-background-remover-and-line-art-too/releases) page
2. Download `GameTextureSorter-vX.Y.Z.zip`
3. Extract the zip anywhere
4. Run `GameTextureSorter.exe`

> Windows SmartScreen may warn "unrecognized app". Click **More info → Run anyway**.

---

## 4. Linux — Full Install

```bash
# Ubuntu/Debian system deps
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv \
    libcairo2-dev libffi-dev unrar tesseract-ocr \
    libgl1-mesa-glx libegl1 libgles2 libxcb-xinerama0

# Clone
git clone https://github.com/JosephsDeadish/Panda-Sorter-Converter-Upscaler-background-remover-and-line-art-too.git
cd Panda-Sorter-Converter-Upscaler-background-remover-and-line-art-too

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# PyTorch (CPU)
pip install torch torchvision

# All other deps
pip install -r requirements.txt

# Launch
python main.py
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip cairo-devel libffi-devel unrar tesseract
```

**Headless / server (no display):**
```bash
QT_QPA_PLATFORM=offscreen python main.py --check-features
```

---

## 5. macOS — Full Install

```bash
# Homebrew deps
brew install python@3.11 cairo libffi tesseract

# Clone
git clone ...
cd ...

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# PyTorch (Apple Silicon or Intel — same command)
pip install torch torchvision

# All other deps
pip install -r requirements.txt

# Launch
python main.py
```

---

## 6. GPU-Accelerated Install (NVIDIA CUDA)

```bash
# Find your CUDA version
nvidia-smi

# Install CUDA-enabled PyTorch (replace cu121 with your version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# GPU-accelerated similarity search
pip install faiss-gpu

# Rest of deps
pip install -r requirements.txt
```

---

## 7. Hybrid Architecture: Inference-Only (Smallest Footprint)

The application uses a **hybrid PyTorch + ONNX architecture**:

| Side | Purpose | Install size |
|---|---|---|
| ONNX Runtime | Batch pipelines, offline inference, EXE runtime | ~10 MB |
| PyTorch | Training, fine-tuning, advanced vision models | ~700 MB |

To run with **only ONNX** (no PyTorch, no training features):
```bash
pip install -r requirements-minimal.txt   # already includes onnxruntime
python main.py
```

To enable **training features** later:
```bash
pip install torch torchvision
pip install timm transformers open-clip-torch
```

---

## 8. Optional Features à la Carte

```bash
# Background removal
pip install "rembg[cpu]>=2.0.50"      # CPU
pip install "rembg[gpu]>=2.0.50"      # GPU

# SVG support
pip install cairosvg cairocffi         # also needs system Cairo

# OCR (requires Tesseract system package)
pip install pytesseract

# Vector similarity search
pip install faiss-cpu chromadb         # or faiss-gpu

# Super-resolution / upscaling
pip install basicsr realesrgan

# Native Rust acceleration
cd native && pip install maturin && maturin develop --release
```

---

## 9. Install as Python Package

```bash
# Standard install
pip install .

# Development (editable) — changes take effect immediately
pip install -e .

# With optional feature groups
pip install -e ".[onnx,svg,ocr]"          # inference + SVG + OCR
pip install -e ".[ml,upscaling]"           # training + upscaler
pip install -e ".[all]"                    # everything
```

Available extras: `svg`, `onnx`, `ml`, `search`, `search-gpu`, `upscaling`,
`background-removal`, `ocr`, `native`, `build`, `dev`, `all`.

---

## 10. Verify Your Install

```bash
# Show version
python main.py --version

# List available features
python main.py --check-features

# Run import tests
python test_hybrid_architecture.py
python test_main_import.py
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `No module named 'PyQt6'` | PyQt6 not installed | `pip install PyQt6 PyOpenGL PyOpenGL-accelerate` |
| `libEGL` / `libGL` missing (Linux) | Qt needs OpenGL | `sudo apt-get install libegl1 libgl1` |
| `No module named 'torch'` | PyTorch not installed | `pip install torch torchvision` |
| `rembg` sys.exit on import | onnxruntime DLL issue | App handles this gracefully — rembg is lazy-imported |
| `No module named 'onnxruntime'` | Not installed | `pip install onnxruntime` |
| `rarfile` errors on RAR | unrar utility missing | Install unrar / WinRAR |
| PyInstaller build fails | See BUILD.md | [BUILD.md](BUILD.md) |

---

**Author:** Dead On The Inside / JosephsDeadish  
**See also:** [INSTALL.md](INSTALL.md) · [BUILD.md](BUILD.md) · [README.md](README.md)
