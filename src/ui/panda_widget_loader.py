"""
Panda Widget Loader - Automatic selection of best available panda widget
Tries OpenGL first (hardware-accelerated 3D), falls back to Canvas if needed
"""

import logging
import warnings

logger = logging.getLogger(__name__)

# Try to load OpenGL widget first (preferred)
OPENGL_AVAILABLE = False
CANVAS_AVAILABLE = False
PandaWidget = None

try:
    from src.ui.panda_widget_gl import PandaWidgetGLBridge, QT_AVAILABLE
    if QT_AVAILABLE:
        PandaWidget = PandaWidgetGLBridge
        OPENGL_AVAILABLE = True
        logger.info("✅ OpenGL panda widget available (hardware-accelerated 3D)")
    else:
        raise ImportError("Qt/OpenGL not available")
except ImportError as e:
    logger.info(f"OpenGL widget not available: {e}")
    
    # Fall back to canvas widget
    try:
        # Suppress deprecation warning for fallback case
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from src.ui.panda_widget import PandaWidget as CanvasPandaWidget
        
        PandaWidget = CanvasPandaWidget
        CANVAS_AVAILABLE = True
        logger.info("⚠️  Using canvas panda widget (2D fallback)")
        logger.info("   Install PyQt6 and PyOpenGL for hardware-accelerated 3D:")
        logger.info("   pip install PyQt6 PyOpenGL PyOpenGL-accelerate")
    except ImportError as e2:
        logger.error(f"❌ No panda widget available: {e2}")
        PandaWidget = None


def get_panda_widget_info():
    """
    Get information about which panda widget is being used.
    
    Returns:
        Dictionary with widget information
    """
    return {
        'widget_type': 'opengl' if OPENGL_AVAILABLE else ('canvas' if CANVAS_AVAILABLE else 'none'),
        'opengl_available': OPENGL_AVAILABLE,
        'canvas_available': CANVAS_AVAILABLE,
        'hardware_accelerated': OPENGL_AVAILABLE,
        '3d_rendering': OPENGL_AVAILABLE,
        'realtime_lighting': OPENGL_AVAILABLE,
        'shadows': OPENGL_AVAILABLE,
        'description': (
            "Hardware-accelerated 3D OpenGL widget with real lighting and shadows"
            if OPENGL_AVAILABLE else
            "Canvas-based 2D widget (legacy fallback)"
            if CANVAS_AVAILABLE else
            "No panda widget available"
        )
    }


def is_opengl_available():
    """Check if OpenGL widget is available."""
    return OPENGL_AVAILABLE


def is_canvas_available():
    """Check if canvas widget is available."""
    return CANVAS_AVAILABLE


def get_panda_widget_class():
    """
    Get the panda widget class to use.
    
    Returns:
        PandaWidget class (OpenGL or Canvas) or None
    """
    return PandaWidget


# Export for easy importing
__all__ = [
    'PandaWidget',
    'OPENGL_AVAILABLE',
    'CANVAS_AVAILABLE',
    'get_panda_widget_info',
    'is_opengl_available',
    'is_canvas_available',
    'get_panda_widget_class',
]
