"""
DINOv2 Model Implementation
Visual similarity clustering model
Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations

import logging
from typing import List, Union, Optional
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import torch
    from PIL import Image
    TORCH_AVAILABLE = True
except ImportError as e:
    TORCH_AVAILABLE = False
    logger.warning(f"PyTorch not available: {e}")
    logger.warning("DINOv2 model will be disabled.")
except OSError as e:
    # Handle DLL initialization errors (e.g., missing CUDA DLLs)
    TORCH_AVAILABLE = False
    logger.warning(f"PyTorch DLL initialization failed: {e}")
    logger.warning("DINOv2 model will be disabled.")
except Exception as e:
    TORCH_AVAILABLE = False
    logger.warning(f"Unexpected error loading dependencies: {e}")
    logger.warning("DINOv2 model will be disabled.")


class DINOv2Model:
    """
    DINOv2 model for visual similarity clustering.
    
    Features:
    - Generate dense visual features
    - Excellent for clustering similar textures
    - No text supervision needed
    """
    
    def __init__(self, model_name: str = 'dinov2_vits14', device: Optional[str] = None):
        """
        Initialize DINOv2 model.
        
        Args:
            model_name: Model variant ('dinov2_vits14', 'dinov2_vitb14', 'dinov2_vitl14')
            device: Device to use ('cuda', 'cpu', or None for auto)
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for DINOv2 model")
        
        try:
            self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        except (RuntimeError, OSError):
            # Fallback to CPU if CUDA check fails
            self.device = 'cpu'
            logger.info("CUDA check failed, using CPU device")
        
        logger.info(f"Initializing DINOv2 model on device: {self.device}")
        
        # Load model from torch hub
        self.model = torch.hub.load('facebookresearch/dinov2', model_name)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"DINOv2 model loaded: {model_name}")
    
    def encode_image(self, image: Union[np.ndarray, Image.Image, Path]) -> np.ndarray:
        """
        Encode image to feature vector.
        
        Args:
            image: Input image
            
        Returns:
            Feature vector as numpy array
        """
        # Load image if path
        if isinstance(image, Path):
            image = Image.open(image).convert('RGB')
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Preprocess
        from torchvision import transforms
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        img_tensor = transform(image).unsqueeze(0).to(self.device)
        
        # Extract features
        with torch.no_grad():
            features = self.model(img_tensor)
        
        return features.cpu().numpy()[0]
