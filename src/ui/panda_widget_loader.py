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

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Attempt 1: hardware-accelerated 3-D OpenGL widget
# ------------------------------------------------------------------
OPENGL_AVAILABLE = False
PandaWidget = None

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
