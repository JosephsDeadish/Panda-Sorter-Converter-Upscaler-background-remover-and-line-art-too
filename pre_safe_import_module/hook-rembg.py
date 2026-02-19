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


def pre_safe_import_module(api):  # noqa: ARG001 - api not needed for sys.exit patch
    """
    Pre-safe-import-module hook for rembg.

    Patches sys.exit() so that rembg's import-time sys.exit(1) call (triggered
    when onnxruntime is unavailable) raises SystemExit instead of terminating
    the PyInstaller analysis process.
    """
    def _patched_exit(code=0):
        raise SystemExit(code)

    sys.exit = _patched_exit
