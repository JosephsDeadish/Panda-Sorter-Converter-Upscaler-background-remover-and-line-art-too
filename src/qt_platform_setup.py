"""
Qt Platform Setup — imported by ui/ modules before any PyQt6 import.

On headless Linux environments (CI, Docker, servers) PyQt6 requires either:
  - A running X11/Wayland display server, OR
  - QT_QPA_PLATFORM=offscreen  (renders off-screen; no display needed)

This module detects the headless case and sets the environment variable so
that ``from PyQt6.QtWidgets import ...`` succeeds everywhere.

Usage
-----
In every file that imports PyQt6, add this BEFORE the try/except::

    import qt_platform_setup  # noqa: F401 — sets QT_QPA_PLATFORM if needed

This is a no-op on Windows and macOS, and a no-op on Linux when a
real display is already available.
"""

from __future__ import annotations

import os
import sys


def _setup_qt_platform() -> None:
    """Set QT_QPA_PLATFORM=offscreen on headless Linux when not already set."""
    if not sys.platform.startswith('linux'):
        return  # Windows / macOS always have a compatible backend
    if 'QT_QPA_PLATFORM' in os.environ:
        return  # already configured by caller or environment
    display = os.environ.get('DISPLAY', '')
    wayland = os.environ.get('WAYLAND_DISPLAY', '')
    if not display and not wayland:
        # No display server detected — use offscreen renderer
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'


_setup_qt_platform()
