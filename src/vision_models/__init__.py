"""
Vision Models Module
CLIP, DINOv2, ViT, EfficientNet, ResNet, SAM models
Author: Dead On The Inside / JosephsDeadish
"""

import logging as _logging
_logger = _logging.getLogger(__name__)

# Import each model independently so one failure does NOT prevent the others
# from loading.  Callers should check the availability flags before using a model.

try:
    from .clip_model import CLIPModel, CLIP_AVAILABLE
except Exception as _e:
    _logger.warning("CLIPModel unavailable: %s", _e)
    CLIPModel = None  # type: ignore[assignment]
    CLIP_AVAILABLE = False

try:
    from .dinov2_model import DINOv2Model
    DINO_AVAILABLE = True
except Exception as _e:
    _logger.warning("DINOv2Model unavailable: %s", _e)
    DINOv2Model = None  # type: ignore[assignment]
    DINO_AVAILABLE = False

try:
    from .vit_model import ViTModel
    VIT_AVAILABLE = True
except Exception as _e:
    _logger.warning("ViTModel unavailable: %s", _e)
    ViTModel = None  # type: ignore[assignment]
    VIT_AVAILABLE = False

try:
    from .efficientnet_model import EfficientNetModel
    EFFICIENTNET_AVAILABLE = True
except Exception as _e:
    _logger.warning("EfficientNetModel unavailable: %s", _e)
    EfficientNetModel = None  # type: ignore[assignment]
    EFFICIENTNET_AVAILABLE = False

try:
    from .sam_model import SAMModel
    SAM_AVAILABLE = True
except Exception as _e:
    _logger.warning("SAMModel unavailable: %s", _e)
    SAMModel = None  # type: ignore[assignment]
    SAM_AVAILABLE = False

__all__ = [
    'CLIPModel',      'CLIP_AVAILABLE',
    'DINOv2Model',    'DINO_AVAILABLE',
    'ViTModel',       'VIT_AVAILABLE',
    'EfficientNetModel', 'EFFICIENTNET_AVAILABLE',
    'SAMModel',       'SAM_AVAILABLE',
]
