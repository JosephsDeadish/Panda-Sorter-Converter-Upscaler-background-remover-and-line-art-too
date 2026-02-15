# Line 34 Error - Resolution Guide

## The Error

```
Traceback (most recent call last):
  File "main.py", line 20, in <module>
    from PyQt6.QtWidgets import (
ModuleNotFoundError: No module named 'PyQt6'
```

or

```
Traceback (most recent call last):
  File "main.py", line 34, in <module>
    from config import config, APP_NAME, APP_VERSION
  ...
ModuleNotFoundError: No module named 'numpy'
```

## Root Cause

The application requires specific dependencies that weren't properly documented in `requirements-minimal.txt`:

1. **PyQt6** - The UI framework (replaced customtkinter)
2. **PyOpenGL** - For 3D rendering
3. **numpy** - Required by classifier module

The error shows "line 34" but actually starts at line 20 (PyQt6 import) or cascades from line 34 when config imports classifier which needs numpy.

## Solution

### Quick Fix
```bash
pip install -r requirements-minimal.txt
```

or

```bash
pip install -r requirements.txt
```

### What Was Fixed

Updated `requirements-minimal.txt` to include:

```python
# UI Framework - Qt/PyQt6 (REQUIRED - ONLY SUPPORTED UI)
PyQt6>=6.6.0  # Qt6 framework for UI
PyOpenGL>=3.1.7  # OpenGL for 3D rendering
PyOpenGL-accelerate>=3.1.7  # Performance optimizations

# Core dependencies
numpy>=1.24.0  # Required by classifier
scikit-learn>=1.3.0  # Required by classifier
opencv-python>=4.8.1.78  # Image processing
pillow>=10.0.0  # Image loading
```

### Removed Obsolete Dependency

```diff
- customtkinter>=5.2.0  # REMOVED - app now uses Qt6
+ PyQt6>=6.6.0  # ADDED - Qt6 framework
```

## Import Chain

The import sequence in main.py:

1. **Line 20-27**: Import PyQt6 widgets (QApplication, QMainWindow, etc.)
2. **Line 34**: `from config import config, APP_NAME, APP_VERSION`
3. **Line 37**: `from classifier import TextureClassifier`
   - classifier imports numpy
   - classifier imports scikit-learn

## Verification

Test that all dependencies are present:

```bash
python3 test_requirements_minimal.py
```

Expected output:
```
✓ Found 3/3 essential dependencies
✓ No obsolete dependencies found
✓ Config import successful
✓ Classifier import successful
```

## Platform-Specific Notes

### Linux (Headless/CI)
On headless systems, you may see:
```
ImportError: libEGL.so.1: cannot open shared object file
```

This is expected - the application requires a display for Qt/OpenGL. The import tests for config and classifier will still pass.

### Windows/Mac
All dependencies should work out of the box after:
```bash
pip install -r requirements-minimal.txt
```

## Related Files

- `requirements-minimal.txt` - Lightweight installation (Qt + basic features)
- `requirements.txt` - Full installation (includes AI/ML features)
- `MIGRATION_COMPLETE.md` - Complete Qt/OpenGL migration documentation
- `INSTALL.md` - Platform-specific installation guide

## Summary

✅ **Fixed**: Updated requirements-minimal.txt with Qt6 dependencies  
✅ **Removed**: Obsolete customtkinter reference  
✅ **Verified**: Import chain works correctly  
✅ **Tested**: Created test_requirements_minimal.py for validation  

The "line 34 error" is now resolved by installing the correct dependencies.
