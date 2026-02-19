"""
Preprocessing Module for PS2 Textures
Author: Dead On The Inside / JosephsDeadish
"""

import logging

# Logger for this module - used in exception handling and debug messages
logger = logging.getLogger(__name__)

from .preprocessing_pipeline import PreprocessingPipeline
from .upscaler import TextureUpscaler
from .filters import TextureFilters
from .alpha_handler import AlphaChannelHandler
from .alpha_correction import AlphaCorrector, AlphaCorrectionPresets

# Re-export native availability check
try:
    from ..native_ops import NATIVE_AVAILABLE
except ImportError as e:
    logger.debug(f"Native operations not available: {e}")
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
