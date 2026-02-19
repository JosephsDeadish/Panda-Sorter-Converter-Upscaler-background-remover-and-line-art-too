"""
Vision Transformer (ViT) Model Implementation
Advanced classification with transformers
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
    from transformers import ViTImageProcessor, ViTForImageClassification
    AVAILABLE = True
except ImportError as e:
    AVAILABLE = False
    logger.warning(f"transformers library or PyTorch not available: {e}")
    logger.warning("ViT model will be disabled.")
except OSError as e:
    # Handle DLL initialization errors (e.g., missing CUDA DLLs)
    AVAILABLE = False
    logger.warning(f"PyTorch DLL initialization failed: {e}")
    logger.warning("ViT model will be disabled.")
except Exception as e:
    AVAILABLE = False
    logger.warning(f"Unexpected error loading dependencies: {e}")
    logger.warning("ViT model will be disabled.")


class ViTModel:
    """Vision Transformer model for texture classification."""
    
    def __init__(self, model_name: str = 'google/vit-base-patch16-224', device: Optional[str] = None):
        """Initialize ViT model."""
        if not AVAILABLE:
            raise RuntimeError("transformers and PyTorch required for ViT model")
        
        try:
            self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        except (RuntimeError, OSError):
            # Fallback to CPU if CUDA check fails
            self.device = 'cpu'
            logger.info("CUDA check failed, using CPU device")
        
        self.processor = ViTImageProcessor.from_pretrained(model_name)
        self.model = ViTForImageClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()
        logger.info(f"ViT model loaded: {model_name}")
    
    def encode_image(self, image: Union[np.ndarray, Image.Image, Path]) -> np.ndarray:
        """Encode image to feature vector."""
        if isinstance(image, Path):
            image = Image.open(image).convert('RGB')
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            features = outputs.hidden_states[-1][:, 0, :]  # CLS token
        
        return features.cpu().numpy()[0]
