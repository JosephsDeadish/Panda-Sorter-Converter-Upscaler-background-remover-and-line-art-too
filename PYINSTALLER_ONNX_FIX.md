# PyInstaller ONNX Build Fix - Implementation Summary

## Problem Statement

The PyInstaller build was failing due to ONNX-related issues:
- **Exit Code 3221225477**: DLL initialization failure in isolated subprocess
- **Root Cause**: PyInstaller tried to introspect `onnx.reference` module which caused crashes
- **Cascading Effect**: Torch hook attempted to collect ONNX submodules, triggering the crash

## Solution Overview

The fix implements a multi-layered approach to prevent ONNX-related build crashes while maintaining optional ONNX support at runtime.

## Changes Made

### 1. New PyInstaller Hooks

#### `.github/hooks/hook-onnx.py`
- **Purpose**: Handle ONNX model format library safely
- **Key Features**:
  - Excludes problematic `onnx.reference` module
  - Bundles ONNX as data files instead of introspecting
  - Prevents isolated subprocess crash
  - Graceful fallback if ONNX not available

#### `.github/hooks/hook-onnxruntime.py`
- **Purpose**: Handle ONNX Runtime inference library
- **Key Features**:
  - Filters out CUDA DLLs to prevent loading errors
  - Collects CPU-only runtime libraries
  - Bundles safely without introspection

### 2. Updated Hooks

#### `hook-torch.py`
- **Added**: `excludedimports` list to prevent importing problematic modules
  - `onnx.reference` - Causes DLL initialization failure
  - `onnx.reference.ops`
  - `onnxscript` - Optional extension that may not be available
- **Updated**: Submodule collection filter to skip ONNX reference modules
- **Result**: PyTorch hook no longer triggers ONNX introspection crashes

### 3. Updated Spec Files

#### `build_spec_onefolder.spec` & `build_spec_with_svg.spec`
- **Added** to `excludes` section:
  ```python
  # ONNX: Exclude problematic modules that cause isolated subprocess crashes
  'onnx.reference',  # Causes exit code 3221225477 (DLL initialization failure)
  'onnx.reference.ops',
  'onnx.reference.ops._op_list',
  'onnxscript',  # Optional scripting extension
  'onnxscript.onnx_opset',
  ```
- **Purpose**: Global exclusion prevents PyInstaller from attempting to analyze these modules

### 4. Enhanced Startup Diagnostics

#### `main.py`
- **Updated** `check_feature_availability()`:
  - Added `'onnx': False` to features dict
  - Added `'onnxruntime': False` to features dict
  - Added ONNX import checks with exception handling

- **Updated** `log_startup_diagnostics()`:
  - Added ONNX features section showing availability status
  - Shows if ONNX Runtime is available for model inference
  - Shows if ONNX model format is available
  - Provides installation instructions if missing
  - Clarifies app works without ONNX

### 5. Requirements Documentation

#### `requirements.txt`
- **Updated** comments to clarify:
  - ONNX is optional but recommended
  - ONNX Runtime is optional for rembg background removal
  - Application gracefully degrades without ONNX
  - onnxscript is commented as truly optional

### 6. CI/CD Improvements

#### `.github/workflows/build-exe.yml`
- **Added** "Verify PyInstaller Hooks Directory" step:
  - Checks `.github/hooks` directory exists
  - Lists available hooks for debugging
  - Fails early if hooks missing
- **Enhanced** build step with better messaging:
  - Shows which hook directories are being used
  - More informative console output

### 7. Test Updates

#### `test_startup_diagnostics.py`
- **Added** ONNX to feature availability checks
- **Updated** test to verify ONNX features are reported correctly

#### `test_pyinstaller_config.py`
- **Added** test for `hook-torch.py` excludedimports
- **Updated** spec file tests to verify onnx.reference exclusion

## How It Works

### Build Time (PyInstaller Analysis)

1. **PyInstaller starts analyzing** dependencies
2. **Encounters ONNX** via torch imports
3. **Checks excludedimports** in hooks:
   - `hook-torch.py` excludes `onnx.reference`
   - `hook-onnx.py` excludes `onnx.reference`
4. **Checks excludes** in spec files:
   - Both spec files exclude `onnx.reference` and `onnxscript`
5. **PyInstaller skips** introspecting problematic modules
6. **ONNX bundled as data** instead of being analyzed
7. **Build completes** without isolated subprocess crash

### Runtime (Application Execution)

1. **Application starts**
2. **Runs feature checks** in `check_feature_availability()`:
   - Attempts to import `onnx` (try/except)
   - Attempts to import `onnxruntime` (try/except)
3. **Displays diagnostics** showing what's available
4. **Uses ONNX if available**, skips if not
5. **Application works** with or without ONNX

## Testing Strategy

### Local Testing
```bash
# Test startup diagnostics
python test_startup_diagnostics.py

# Test PyInstaller configuration
python test_pyinstaller_config.py

# Validate hook syntax
python -m py_compile .github/hooks/hook-*.py
python -m py_compile hook-*.py

# Validate spec files
python -m py_compile build_spec_*.spec
```

### CI Testing
The GitHub Actions workflow now:
1. Verifies hooks directory exists
2. Shows which hooks are available
3. Runs PyInstaller build
4. Verifies EXE is created
5. Tests EXE launches (in future updates)

## Expected Outcomes

### ✅ Build Success
- PyInstaller analysis completes without crashes
- No exit code 3221225477 errors
- EXE file created successfully

### ✅ Runtime Success
- Application launches without errors
- Startup diagnostics display correctly
- ONNX features shown as available or unavailable
- Graceful degradation when ONNX missing

### ✅ Feature Support
- If ONNX installed: Full model export/import support
- If ONNX Runtime installed: Background removal works
- If neither installed: App works with basic features

## Rollback Plan

If issues occur:
1. Remove excludedimports from `hook-torch.py`
2. Remove ONNX excludes from spec files
3. Delete `.github/hooks/hook-onnx.py`
4. Revert to previous working state

## Future Improvements

1. **Add more runtime checks** for other optional dependencies
2. **Enhanced error reporting** with specific missing module info
3. **Automatic fallback modes** for missing features
4. **Build variants** (full AI vs minimal)

## References

- PyInstaller hooks documentation: https://pyinstaller.org/en/stable/hooks.html
- ONNX documentation: https://onnx.ai/
- Issue: Exit code 3221225477 is Windows DLL initialization failure

## Author

Dead On The Inside / JosephsDeadish
Date: 2026-02-16
