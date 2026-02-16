"""
Panda Widget Loader - Qt OpenGL Widget for 3D Panda Rendering
Uses PyQt6 with OpenGL for hardware-accelerated 3D rendering with real-time lighting and shadows.
Qt is now required - canvas rendering has been removed.
"""

import logging

logger = logging.getLogger(__name__)

# Load Qt OpenGL widget (required)
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
except ImportError as e:
    logger.error(f"❌ PyQt6/OpenGL required but not available: {e}")
    logger.error("   Install with: pip install PyQt6 PyOpenGL PyOpenGL-accelerate")
    PandaWidget = None


def get_panda_widget_info():
    """
    Get information about the Qt OpenGL panda widget.
    
    Returns:
        Dictionary with widget information
    """
    return {
        'widget_type': 'opengl' if OPENGL_AVAILABLE else 'none',
        'opengl_available': OPENGL_AVAILABLE,
        'hardware_accelerated': OPENGL_AVAILABLE,
        '3d_rendering': OPENGL_AVAILABLE,
        'realtime_lighting': OPENGL_AVAILABLE,
        'shadows': OPENGL_AVAILABLE,
        'description': (
            "Hardware-accelerated 3D OpenGL widget with real lighting and shadows"
            if OPENGL_AVAILABLE else
            "PyQt6/OpenGL not available - install required dependencies"
        )
    }


def is_opengl_available():
    """Check if OpenGL widget is available."""
    return OPENGL_AVAILABLE


def get_panda_widget_class():
    """
    Get the Qt OpenGL panda widget class.
    
    Returns:
        PandaWidget class (OpenGL) or None if Qt/OpenGL not available
    """
    return PandaWidget


# Export for easy importing
__all__ = [
    'PandaWidget',
    'OPENGL_AVAILABLE',
    'get_panda_widget_info',
    'is_opengl_available',
    'get_panda_widget_class',
]
