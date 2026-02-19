"""
PyInstaller pre-safe-import hook for rembg

This hook runs BEFORE rembg is imported during PyInstaller's analysis phase.
It patches sys.exit() to prevent rembg from calling sys.exit(1) when
onnxruntime fails to load, which would kill the PyInstaller build process.

The rembg package checks for onnxruntime at import time and calls sys.exit(1)
if it's not available. This is problematic for PyInstaller builds where
onnxruntime DLL initialization may fail in the isolated subprocess used
for dependency analysis.

Author: Dead On The Inside / JosephsDeadish
"""

import sys

# Save the original sys.exit
_original_exit = sys.exit

def _patched_exit(code=0):
    """
    Patched sys.exit that raises SystemExit instead of calling os._exit().
    This allows PyInstaller to catch the exception and continue building.
    """
    raise SystemExit(code)

# Patch sys.exit BEFORE rembg is imported
# Note: This patch remains in effect for the subprocess lifetime
sys.exit = _patched_exit
