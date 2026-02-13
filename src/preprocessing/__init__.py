"""
Preprocessing Module for PS2 Textures
Author: Dead On The Inside / JosephsDeadish
"""

from .preprocessing_pipeline import PreprocessingPipeline
from .upscaler import TextureUpscaler
from .filters import TextureFilters
from .alpha_handler import AlphaChannelHandler
from .alpha_correction import AlphaCorrector, AlphaCorrectionPresets

# Re-export native availability check
try:
    from src.native_ops import NATIVE_AVAILABLE
except ImportError:
    try:
        from native_ops import NATIVE_AVAILABLE
    except ImportError:
        NATIVE_AVAILABLE = False

__all__ = [
    'PreprocessingPipeline',
    'TextureUpscaler',
    'TextureFilters',
    'AlphaChannelHandler',
    'AlphaCorrector',
    'AlphaCorrectionPresets',
    'NATIVE_AVAILABLE',
]
