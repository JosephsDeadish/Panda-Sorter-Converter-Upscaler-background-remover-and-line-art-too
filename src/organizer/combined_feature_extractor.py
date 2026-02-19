"""
Backend Logic for Combined Feature Extractor Models

This module provides utilities for working with combined AI models in the organizer.
Handles model initialization, feature extraction, and ensemble predictions.

Author: GitHub Copilot for PR #168
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class CombinedFeatureExtractor:
    """
    Handles feature extraction using single or combined AI models.
    
    Supports:
    - Single models: CLIP, DINOv2, timm
    - Combined models: CLIP+DINOv2, CLIP+timm, DINOv2+timm, CLIP+DINOv2+timm
    
    Note: timm models are NOT compiled with TorchScript to avoid source access errors.
    """
    
    def __init__(self, model_config: str):
        """
        Initialize the feature extractor(s).
        
        Args:
            model_config: Model configuration string (e.g., "CLIP", "CLIP+DINOv2", etc.)
        """
        self.model_config = model_config
        self.models = []
        self.model_names = self._parse_model_config(model_config)
        self._initialize_models()
    
    def _parse_model_config(self, config: str) -> List[str]:
        """Parse model configuration string to extract individual model names."""
        # Extract the core part before any description in parentheses
        core_config = config.split('(')[0].strip()
        
        # Split by '+' to get individual models
        if '+' in core_config:
            models = [m.strip() for m in core_config.split('+')]
        else:
            models = [core_config]
        
        return models
    
    def _initialize_models(self):
        """Initialize the required models based on configuration."""
        logger.info(f"Initializing feature extractor(s): {', '.join(self.model_names)}")
        
        for model_name in self.model_names:
            if model_name == 'CLIP':
                self._init_clip()
            elif model_name == 'DINOv2':
                self._init_dinov2()
            elif model_name == 'timm':
                self._init_timm()
            else:
                logger.warning(f"Unknown model: {model_name}")
        
        if len(self.models) > 1:
            logger.warning(
                f"Using {len(self.models)} combined models. "
                f"This will impact performance but may improve accuracy."
            )
    
    def _init_clip(self):
        """Initialize CLIP model."""
        try:
            from src.vision_models.clip_model import CLIPModel
            model = CLIPModel()
            self.models.append(('CLIP', model))
            logger.info("✅ CLIP model initialized")
        except ImportError as e:
            logger.error(f"Failed to import CLIP model: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize CLIP: {e}")
    
    def _init_dinov2(self):
        """Initialize DINOv2 model."""
        try:
            from src.vision_models.dinov2_model import DINOv2Model
            model = DINOv2Model()
            self.models.append(('DINOv2', model))
            logger.info("✅ DINOv2 model initialized")
        except ImportError as e:
            logger.error(f"Failed to import DINOv2 model: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize DINOv2: {e}")
    
    def _init_timm(self):
        """
        Initialize timm (EfficientNet) model.
        
        IMPORTANT: Model is NOT compiled with TorchScript to avoid source access errors.
        Uses standard PyTorch .eval() mode only.
        """
        try:
            from src.vision_models.efficientnet_model import EfficientNetModel
            # Default to efficientnet_b0 - NOT compiled with TorchScript
            model = EfficientNetModel('efficientnet_b0')
            self.models.append(('timm', model))
            logger.info("✅ timm (EfficientNet) model initialized (NOT TorchScript compiled)")
        except ImportError as e:
            logger.error(f"Failed to import timm model: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize timm: {e}")
    
    def extract_features(self, image_path: Path) -> np.ndarray:
        """
        Extract features from an image using configured model(s).
        
        For combined models, features are concatenated.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Feature vector as numpy array
        """
        if not self.models:
            raise RuntimeError("No models initialized")
        
        features_list = []
        
        for model_name, model in self.models:
            try:
                # Each model's encode_image returns a feature vector
                features = model.encode_image(image_path)
                features_list.append(features)
                logger.debug(f"{model_name} extracted {features.shape} features")
            except Exception as e:
                logger.error(f"Error extracting features with {model_name}: {e}")
                # Continue with other models even if one fails
        
        if not features_list:
            raise RuntimeError("All models failed to extract features")
        
        # Concatenate features from all models
        combined_features = np.concatenate(features_list)
        
        logger.debug(
            f"Combined features shape: {combined_features.shape} "
            f"(from {len(features_list)} model(s))"
        )
        
        return combined_features
    
    def is_combined(self) -> bool:
        """Check if this is a combined model configuration."""
        return len(self.models) > 1
    
    def get_model_count(self) -> int:
        """Get the number of models in this configuration."""
        return len(self.models)
    
    def get_model_names(self) -> List[str]:
        """Get list of model names in this configuration."""
        return [name for name, _ in self.models]


def create_feature_extractor(settings: Dict[str, Any]) -> CombinedFeatureExtractor:
    """
    Factory function to create a feature extractor from settings.
    
    Args:
        settings: Settings dictionary containing 'feature_extractor' key
        
    Returns:
        CombinedFeatureExtractor instance
        
    Example:
        >>> settings = {'feature_extractor': 'CLIP+DINOv2 (Combined: text + visual)'}
        >>> extractor = create_feature_extractor(settings)
        >>> features = extractor.extract_features(image_path)
    """
    model_config = settings.get('feature_extractor', 'CLIP (image-to-text classification)')
    return CombinedFeatureExtractor(model_config)


def estimate_processing_time(model_config: str, num_images: int = 1) -> Tuple[float, str]:
    """
    Estimate processing time for a given model configuration.
    
    Args:
        model_config: Model configuration string
        num_images: Number of images to process
        
    Returns:
        Tuple of (estimated_seconds, human_readable_string)
        
    Example:
        >>> time_s, time_str = estimate_processing_time("CLIP+DINOv2+timm", 100)
        >>> print(f"Estimated time: {time_str}")
        Estimated time: ~8 minutes
    """
    # Base processing times per image (rough estimates in seconds)
    base_times = {
        'CLIP': 0.5,
        'DINOv2': 0.8,
        'timm': 0.3,
    }
    
    # Parse model config
    core_config = model_config.split('(')[0].strip()
    models = [m.strip() for m in core_config.split('+')] if '+' in core_config else [core_config]
    
    # Calculate total time
    total_time = 0
    for model in models:
        total_time += base_times.get(model, 0.5)
    
    total_time *= num_images
    
    # Format human-readable string
    if total_time < 60:
        time_str = f"~{int(total_time)} seconds"
    elif total_time < 3600:
        time_str = f"~{int(total_time / 60)} minutes"
    else:
        time_str = f"~{int(total_time / 3600)} hours"
    
    return total_time, time_str
