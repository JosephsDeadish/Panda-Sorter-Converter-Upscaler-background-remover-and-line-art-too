"""
Offline AI Model Wrapper - ONNX Runtime Integration
Provides CPU-optimized offline inference for texture classification
Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logging.warning("ONNX Runtime not available. Offline AI models disabled.")


logger = logging.getLogger(__name__)


class OfflineModel:
    """
    ONNX Runtime wrapper for offline texture classification.
    
    Supports MobileNetV3-like models optimized for CPU inference.
    Thread-safe model loading and inference with confidence scoring.
    """
    
    def __init__(self, model_path: Optional[Path] = None, num_threads: int = 4):
        """
        Initialize the offline model.
        
        Args:
            model_path: Path to ONNX model file (.onnx)
            num_threads: Number of CPU threads for inference
        """
        self.model_path = model_path
        self.num_threads = num_threads
        self.session: Optional[ort.InferenceSession] = None
        self.input_name: Optional[str] = None
        self.output_name: Optional[str] = None
        self.input_shape: Optional[Tuple[int, ...]] = None
        self.categories: List[str] = []
        self._lock = threading.Lock()
        self._loaded = False
        
        if model_path and model_path.exists():
            self.load_model(model_path)
    
    def load_model(self, model_path: Path) -> bool:
        """
        Load ONNX model from file.
        
        Args:
            model_path: Path to .onnx model file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if not ONNX_AVAILABLE:
            logger.error("ONNX Runtime not available")
            return False
        
        with self._lock:
            try:
                logger.info(f"Loading ONNX model from {model_path}")
                
                # Configure ONNX Runtime session options
                sess_options = ort.SessionOptions()
                sess_options.intra_op_num_threads = self.num_threads
                sess_options.inter_op_num_threads = self.num_threads
                sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                
                # Create inference session
                self.session = ort.InferenceSession(
                    str(model_path),
                    sess_options,
                    providers=['CPUExecutionProvider']
                )
                
                # Get input/output metadata
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
                self.input_shape = self.session.get_inputs()[0].shape
                
                # Load categories from model metadata if available
                metadata = self.session.get_modelmeta()
                if metadata.custom_metadata_map and 'categories' in metadata.custom_metadata_map:
                    import json
                    self.categories = json.loads(metadata.custom_metadata_map['categories'])
                
                self.model_path = model_path
                self._loaded = True
                
                logger.info(f"Model loaded successfully. Input: {self.input_shape}, Categories: {len(self.categories)}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}", exc_info=True)
                self.session = None
                self._loaded = False
                return False
    
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self._loaded and self.session is not None
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for model input.
        
        Args:
            image: Input image as numpy array (H, W, C)
            
        Returns:
            Preprocessed image tensor (N, C, H, W)
        """
        if not self.is_loaded() or self.input_shape is None:
            raise RuntimeError("Model not loaded")
        
        # Expected shape: (batch, channels, height, width)
        target_h = self.input_shape[2] if len(self.input_shape) > 2 else 224
        target_w = self.input_shape[3] if len(self.input_shape) > 3 else 224
        
        # Resize image
        from PIL import Image
        if image.dtype == np.uint8:
            img_pil = Image.fromarray(image)
        else:
            img_pil = Image.fromarray((image * 255).astype(np.uint8))
        
        img_resized = img_pil.resize((target_w, target_h), Image.Resampling.BILINEAR)
        img_array = np.array(img_resized).astype(np.float32)
        
        # Normalize to [0, 1]
        img_array = img_array / 255.0
        
        # ImageNet normalization (standard for most models)
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        
        if img_array.ndim == 2:
            # Grayscale - convert to RGB
            img_array = np.stack([img_array] * 3, axis=-1)
        
        if img_array.shape[2] == 4:
            # RGBA - drop alpha channel
            img_array = img_array[:, :, :3]
        
        # Normalize
        img_array = (img_array - mean) / std
        
        # Convert HWC to CHW
        img_array = np.transpose(img_array, (2, 0, 1))
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    def predict(self, image: np.ndarray, top_k: int = 5) -> List[Dict[str, float]]:
        """
        Run inference on image and return predictions.
        
        Args:
            image: Input image as numpy array
            top_k: Number of top predictions to return
            
        Returns:
            List of predictions with category and confidence
            Example: [{'category': 'metal', 'confidence': 0.85}, ...]
        """
        if not self.is_loaded():
            logger.warning("Model not loaded, returning empty predictions")
            return []
        
        try:
            # Preprocess image
            input_tensor = self.preprocess_image(image)
            
            # Run inference
            with self._lock:
                outputs = self.session.run(
                    [self.output_name],
                    {self.input_name: input_tensor}
                )
            
            # Get predictions
            logits = outputs[0][0]  # Remove batch dimension
            
            # Apply softmax
            exp_logits = np.exp(logits - np.max(logits))
            probabilities = exp_logits / np.sum(exp_logits)
            
            # Get top-k predictions
            top_indices = np.argsort(probabilities)[-top_k:][::-1]
            
            predictions = []
            for idx in top_indices:
                category = self.categories[idx] if idx < len(self.categories) else f"class_{idx}"
                confidence = float(probabilities[idx])
                predictions.append({
                    'category': category,
                    'confidence': confidence
                })
            
            logger.debug(f"Predictions: {predictions[:3]}")
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            return []
    
    def predict_batch(self, images: List[np.ndarray], top_k: int = 5) -> List[List[Dict[str, float]]]:
        """
        Run batch inference on multiple images.
        
        Args:
            images: List of input images
            top_k: Number of top predictions per image
            
        Returns:
            List of prediction lists
        """
        results = []
        for image in images:
            predictions = self.predict(image, top_k)
            results.append(predictions)
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata and information.
        
        Returns:
            Dictionary with model information
        """
        info = {
            'loaded': self._loaded,
            'model_path': str(self.model_path) if self.model_path else None,
            'input_shape': self.input_shape,
            'num_categories': len(self.categories),
            'categories': self.categories,
            'num_threads': self.num_threads
        }
        
        if self.session:
            try:
                metadata = self.session.get_modelmeta()
                info['version'] = metadata.version
                info['producer'] = metadata.producer_name
                info['description'] = metadata.description
            except Exception:
                pass
        
        return info
    
    def unload(self):
        """Unload model and free resources."""
        with self._lock:
            if self.session:
                logger.info("Unloading model")
                self.session = None
                self._loaded = False
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.unload()


def get_default_model_path() -> Optional[Path]:
    """
    Get path to default offline model.
    
    Returns:
        Path to model or None if not found
    """
    # Check multiple possible locations (including portable app_data folder)
    from ..config import get_app_dir
    _app = get_app_dir()
    possible_paths = [
        _app / "app_data" / "models" / "texture_classifier.onnx",
        Path(__file__).parent / "models" / "texture_classifier.onnx",
        Path.home() / ".ps2_texture_sorter" / "models" / "texture_classifier.onnx",
        Path("models") / "texture_classifier.onnx",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None


def create_default_model() -> Optional[OfflineModel]:
    """
    Create offline model with default settings.
    
    Returns:
        OfflineModel instance or None if no model available
    """
    model_path = get_default_model_path()
    
    if model_path:
        logger.info(f"Using default model: {model_path}")
        return OfflineModel(model_path)
    else:
        logger.info("No default model found. AI features will use rule-based fallback.")
        return None
