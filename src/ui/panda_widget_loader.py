"""
Panda Widget Loader - selects the best available panda widget.

Priority:
  1. PandaOpenGLWidget  -- hardware-accelerated 3-D OpenGL rendering
  2. PandaWidget2D      -- QPainter-based 2-D fallback (no OpenGL required)
  3. None              -- returned when both fail (app shows placeholder)

This module is the single authoritative source for obtaining a panda widget
class.  main.py and any other consumer should prefer this loader over
importing PandaOpenGLWidget or PandaWidget2D directly.
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Pre-configure OpenGL environment BEFORE importing the GL widget.
# This mirrors what main._setup_opengl_for_exe() does, so the loader
# works correctly even when imported before main.py runs.
# ------------------------------------------------------------------
def _pre_configure_opengl() -> None:
    """Block opengl_accelerate and set up DLL search paths early."""
    if not sys.platform.startswith('win'):
        return
    # Skip desktop GL configuration when running on the offscreen/headless Qt
    # platform (e.g. CI with QT_QPA_PLATFORM=offscreen).  The offscreen backend
    # uses software rendering and does NOT expose a real WGL surface; forcing
    # AA_UseDesktopOpenGL or QT_OPENGL=desktop in that context causes Qt to call
    # exit(1) on VMs without a GPU.
    if os.environ.get('QT_QPA_PLATFORM') == 'offscreen':
        return
    # Force Qt to use native opengl32.dll NOT ANGLE (Direct3D translation layer).
    # ANGLE supports only OpenGL ES — glShadeModel/glLightfv/glBegin/glEnd all raise
    # GLError(1282 INVALID_OPERATION) under ANGLE, causing initializeGL to fail and
    # fall back to the 2D panda.  Must be set before QApplication is created.
    os.environ.setdefault('QT_OPENGL', 'desktop')
    os.environ.setdefault('PYOPENGL_PLATFORM_HANDLER', 'win32')
    import types as _tm
    _stub = _tm.ModuleType('opengl_accelerate')
    _stub.USE_ACCELERATE = False  # type: ignore[attr-defined]
    for _name in ('opengl_accelerate', 'OpenGL_accelerate', 'OpenGL.arrays.numpymodule'):
        if _name not in sys.modules:
            sys.modules[_name] = _stub  # type: ignore[assignment]
    try:
        import OpenGL as _ogl; _ogl.USE_ACCELERATE = False
    except Exception:
        pass
    _sys32 = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32')
    if getattr(sys, 'frozen', False):
        _app_dir = os.path.dirname(sys.executable)
        _dirs = [_sys32, _app_dir, getattr(sys, '_MEIPASS', _app_dir)]
    else:
        _dirs = [_sys32]
    for _d in _dirs:
        try:
            if os.path.isdir(_d):
                os.add_dll_directory(_d)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
    # Also set Qt application-level attribute for desktop OpenGL, which is
    # more reliable than the env var alone on some Qt6 Windows installations.
    # This can be set before QApplication is created (it's a static attr).
    try:
        from PyQt6.QtWidgets import QApplication as _QAppCls
        from PyQt6.QtCore import Qt as _Qt6
        _QAppCls.setAttribute(_Qt6.ApplicationAttribute.AA_UseDesktopOpenGL)
    except Exception:
        pass

_pre_configure_opengl()

# ------------------------------------------------------------------
# Attempt 1: hardware-accelerated 3-D OpenGL widget
# ------------------------------------------------------------------
OPENGL_AVAILABLE = False
PandaWidget = None

# Skip the OpenGL widget entirely on the offscreen/headless Qt platform.
# The offscreen backend provides no real WGL/EGL surface; importing
# panda_widget_gl causes QSurfaceFormat.setDefaultFormat() to run which can
# trigger Qt to call exit(1) on CI VMs without a GPU.
if os.environ.get('QT_QPA_PLATFORM') != 'offscreen':
    try:
        from ui.panda_widget_gl import PandaOpenGLWidget, QT_AVAILABLE
        if QT_AVAILABLE:
            PandaWidget = PandaOpenGLWidget
            OPENGL_AVAILABLE = True
            logger.info("✅ OpenGL panda widget loaded (hardware-accelerated 3D)")
        else:
            raise ImportError("Qt/OpenGL not available")
    except (ImportError, OSError, RuntimeError) as _gl_err:
        logger.warning(f"OpenGL panda widget unavailable ({_gl_err}), trying 2D fallback")

# ------------------------------------------------------------------
# Attempt 2: 2-D QPainter fallback (works without hardware OpenGL)
# ------------------------------------------------------------------
PANDA_2D_AVAILABLE = False

if PandaWidget is None:
    try:
        from ui.panda_widget_2d import PandaWidget2D
        PandaWidget = PandaWidget2D
        PANDA_2D_AVAILABLE = True
        logger.info("✅ 2D QPainter panda widget loaded (OpenGL unavailable)")
    except (ImportError, OSError, RuntimeError) as _2d_err:
        logger.error(
            f"Both OpenGL and 2D panda widgets failed: {_2d_err}\n"
            "   Install PyQt6 and optionally PyOpenGL for 3D rendering:\n"
            "   pip install PyQt6 PyOpenGL PyOpenGL-accelerate"
        )
        PandaWidget = None


def get_panda_widget_info():
    """Return a status dict describing which panda widget backend is active."""
    if OPENGL_AVAILABLE:
        widget_type = 'opengl'
        desc = "Hardware-accelerated 3D OpenGL widget with real lighting and shadows"
    elif PANDA_2D_AVAILABLE:
        widget_type = '2d'
        desc = "2D QPainter panda widget (OpenGL unavailable — install PyOpenGL for 3D)"
    else:
        widget_type = 'none'
        desc = "No panda widget available — install PyQt6 (and optionally PyOpenGL)"
    return {
        'widget_type': widget_type,
        'opengl_available': OPENGL_AVAILABLE,
        'panda_2d_available': PANDA_2D_AVAILABLE,
        'hardware_accelerated': OPENGL_AVAILABLE,
        '3d_rendering': OPENGL_AVAILABLE,
        'realtime_lighting': OPENGL_AVAILABLE,
        'shadows': OPENGL_AVAILABLE,
        'description': desc,
    }


def is_opengl_available():
    """Return True if the 3-D OpenGL widget loaded successfully."""
    return OPENGL_AVAILABLE


def is_panda_available():
    """Return True if *any* panda widget (3D or 2D) is available."""
    return PandaWidget is not None


def get_panda_widget_class():
    """Return the best available panda widget class (OpenGL → 2D → None)."""
    return PandaWidget


# Export for easy importing
__all__ = [
    'PandaWidget',
    'OPENGL_AVAILABLE',
    'PANDA_2D_AVAILABLE',
    'get_panda_widget_info',
    'is_opengl_available',
    'is_panda_available',
    'get_panda_widget_class',
]
