"""
Game Texture Sorter
Author: Dead On The Inside / JosephsDeadish

A professional Windows application for automatically sorting game texture 
dumps with advanced AI classification and massive-scale support 
(200,000+ textures).
"""

__version__ = "1.0.0"
__author__ = "Dead On The Inside / JosephsDeadish"
__project__ = "Game Texture Sorter"

# Ensure Qt can start in headless/CI Linux environments before any UI import.
# This is a no-op on Windows/macOS and a no-op when a display is available.
try:
    import qt_platform_setup  # noqa: F401
except ImportError:
    pass
