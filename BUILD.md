# Build Guide — Game Texture Sorter

How to build a standalone Windows EXE from source.

---

## Quick Build (Windows)

```cmd
# Option A — PowerShell script (recommended)
.\build.ps1

# Option B — Batch file
build.bat

# Option C — Direct PyInstaller
pyinstaller build_spec_onefolder.spec --clean --noconfirm
```

Output: `dist\GameTextureSorter\GameTextureSorter.exe`

---

## Build Variants

| Spec file | When to use |
|---|---|
| `build_spec_onefolder.spec` | Standard build — fast startup, no SVG |
| `build_spec_with_svg.spec` | Includes Cairo DLLs for SVG texture support |

### Standard Build (Recommended)
```cmd
pyinstaller build_spec_onefolder.spec --clean --noconfirm
```
- ~50–100 MB total
- No SVG support (PNG/DDS/JPEG/WEBP/TGA work fine)
- Fastest startup (1–3 seconds)
- Compatible with GitHub Actions CI

### SVG-Enabled Build
```cmd
pyinstaller build_spec_with_svg.spec --clean --noconfirm
```
- ~65–120 MB total
- Requires Cairo DLLs (see [SVG Build Guide](docs/SVG_BUILD_GUIDE.md))

---

## Architecture: What Gets Bundled

The build uses the **hybrid ONNX + PyTorch approach**:

```
EXE bundle
├── Core app   (src/, main.py)
├── ONNX Runtime DLLs          ← always included via hook-onnxruntime.py
├── PyTorch DLLs (CPU)         ← included by default
└── rembg                      ← EXCLUDED (lazy-imported at runtime)
```

**rembg is deliberately excluded** from the EXE.  
It is lazy-imported at call time so the app works without it in the bundle.  
Users who want background removal install it alongside the EXE:
```cmd
pip install "rembg[cpu]"
```

---

## CI / GitHub Actions Build

The workflow `.github/workflows/build-exe.yml` runs automatically on every
push to `main` and on all pull requests. It:

1. Installs Python 3.11 on `windows-latest`
2. Installs all dependencies (PyTorch CPU, optional ML deps)
3. Runs syntax validation (`python -m compileall .`)
4. Runs architecture & import safety tests
5. Runs `pyinstaller build_spec_onefolder.spec`
6. Verifies `dist/GameTextureSorter/GameTextureSorter.exe` exists
7. Uploads the folder as a GitHub Actions artifact (retained 90 days)
8. Creates a release ZIP on version tags (`v*.*.*`)

**Download the latest build:**  
Go to Actions → latest successful run → Artifacts → `GameTextureSorter-<sha>`

---

## Build Requirements

```cmd
pip install "pyinstaller>=6.0.0"
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install onnxruntime
pip install -r requirements.txt
```

> PyInstaller >= 6.0.0 is required for privilege-escalation security fixes.

---

## Build Options (build.ps1)

```powershell
# CPU-only (default — smaller, no CUDA DLLs)
.\build.ps1

# With CUDA GPU support (~500 MB larger)
.\build.ps1 -IncludeCuda

# Exclude PyTorch entirely (~1 GB smaller — basic features only)
.\build.ps1 -ExcludeTorch
```

---

## Hooks & Runtime Hooks

PyInstaller hooks live in two places:

| Location | Files | Purpose |
|---|---|---|
| Project root | `hook-rembg.py`, `hook-torch.py` | Root-level hooks |
| `.github/hooks/` | `hook-onnxruntime.py`, `hook-PIL.py`, etc. | Fine-grained collection |
| `.github/hooks/pre_safe_import_module/` | `hook-rembg.py` | Patches sys.exit before rembg is analysed |
| Project root | `runtime-hook-onnxruntime.py` | Disables CUDA providers at EXE startup |
| Project root | `runtime-hook-torch.py` | Graceful CUDA init in frozen EXE |
| Project root | `runtime-hook-qt-platform.py` | Sets `QT_QPA_PLATFORM=offscreen` on headless Linux |

**Why rembg is excluded from analysis:**  
`rembg.bg` calls `sys.exit(1)` when onnxruntime's DLL fails to load during
PyInstaller's isolated import-analysis subprocess. Since rembg is now
lazy-imported at call time (see `src/tools/background_remover.py`), it is
safe to exclude it from the bundle entirely.

---

## Troubleshooting Builds

### `RuntimeError: Child process call to import_library() failed`
rembg or onnxruntime is triggering `sys.exit` during analysis.  
**Fix:** Ensure rembg is in the `excludes` list (already done in both spec files).

### `ModuleNotFoundError` at runtime
A hidden import is missing from the spec.  
**Fix:** Add it to `hiddenimports` in the relevant spec file or hook.

### EXE crashes on start
Check `dist/GameTextureSorter/_internal/` for missing DLLs.  
Run from a Command Prompt to see the traceback:
```cmd
.\dist\GameTextureSorter\GameTextureSorter.exe
```

### CUDA DLL errors (`nvcuda.dll` not found)
Expected — the build is CPU-only by default.  
The `runtime-hook-onnxruntime.py` and `runtime-hook-torch.py` hooks handle
this gracefully (CUDA is disabled at startup, not a crash).

### SVG not working in standard build
Expected — use `build_spec_with_svg.spec` or install
`cairosvg cairocffi` alongside the EXE.  
See [docs/SVG_BUILD_GUIDE.md](docs/SVG_BUILD_GUIDE.md).

---

## Build Output Structure

```
dist/
└── GameTextureSorter/
    ├── GameTextureSorter.exe      ← main executable
    ├── _internal/                 ← Python runtime + bundled packages
    │   ├── torch/
    │   ├── onnxruntime/
    │   └── ...
    ├── resources/                 ← icons, sounds, themes (editable)
    ├── app_data/
    │   ├── cache/
    │   ├── logs/
    │   ├── themes/
    │   └── models/                ← drop .onnx model files here
    └── GameTextureSorter.zip      ← release archive (on tag builds)
```

---

**Author:** Dead On The Inside / JosephsDeadish  
**See also:** [INSTALL.md](INSTALL.md) · [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) · [docs/SVG_BUILD_GUIDE.md](docs/SVG_BUILD_GUIDE.md)
