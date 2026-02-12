"""
EfficientNet/ResNet Model Implementation
Custom classifier support
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from typing import List, Union, Optional
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import torch
    from PIL import Image
    import timm
    AVAILABLE = True
except ImportError:
    AVAILABLE = False
    logger.warning("timm library not available. EfficientNet model disabled.")


class EfficientNetModel:
    """EfficientNet or ResNet model for texture classification."""
    
    def __init__(
        self,
        model_name: str = 'efficientnet_b0',
        pretrained: bool = True,
        device: Optional[str] = None
    ):
        """Initialize EfficientNet/ResNet model."""
        if not AVAILABLE:
            raise RuntimeError("timm and PyTorch required")
        
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = timm.create_model(model_name, pretrained=pretrained, num_classes=0)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Get data config for preprocessing
        self.data_config = timm.data.resolve_model_data_config(self.model)
        self.transforms = timm.data.create_transform(**self.data_config, is_training=False)
        
        logger.info(f"EfficientNet model loaded: {model_name}")
    
    def encode_image(self, image: Union[np.ndarray, Image.Image, Path]) -> np.ndarray:
        """Encode image to feature vector."""
        if isinstance(image, Path):
            image = Image.open(image).convert('RGB')
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        img_tensor = self.transforms(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            features = self.model(img_tensor)
        
        return features.cpu().numpy()[0]
