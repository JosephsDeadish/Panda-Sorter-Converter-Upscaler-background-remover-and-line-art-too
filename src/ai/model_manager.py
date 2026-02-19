"""
AI Model Manager - Orchestrates offline and online models
Implements fallback logic and confidence-weighted blending
Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.error("numpy not available - limited functionality")
    logger.error("Install with: pip install numpy")
from collections import defaultdict

from .offline_model import OfflineModel, create_default_model
from .online_model import OnlineModel, create_online_model_from_config




class ModelManager:
    """
    Main AI model orchestration system.
    
    Features:
    - Manages both offline and online models
    - Implements fallback logic (online → offline)
    - Blends predictions from multiple models (confidence-weighted)
    - Thread-safe operations
    - Graceful degradation when models unavailable
    """
    
    def __init__(
        self,
        offline_model: Optional[OfflineModel] = None,
        online_model: Optional[OnlineModel] = None,
        blend_mode: str = 'confidence_weighted',
        min_confidence: float = 0.3
    ):
        """
        Initialize model manager.
        
        Args:
            offline_model: Offline ONNX model instance
            online_model: Online API model instance
            blend_mode: How to blend predictions ('confidence_weighted', 'max', 'average')
            min_confidence: Minimum confidence threshold for predictions
        """
        self.offline_model = offline_model
        self.online_model = online_model
        self.blend_mode = blend_mode
        self.min_confidence = min_confidence
        
        self._lock = threading.RLock()
        self._stats = {
            'total_predictions': 0,
            'offline_predictions': 0,
            'online_predictions': 0,
            'blended_predictions': 0,
            'fallback_predictions': 0
        }
        
        # Validate setup
        has_offline = offline_model and offline_model.is_loaded()
        has_online = online_model and online_model.is_enabled()
        
        logger.info(f"ModelManager initialized - Offline: {has_offline}, Online: {has_online}")
        
        if not has_offline and not has_online:
            logger.warning("No AI models available. Using rule-based classification only.")
    
    @classmethod
    def create_default(cls, config: Optional[Dict[str, Any]] = None) -> 'ModelManager':
        """
        Create model manager with default configuration.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            ModelManager instance
        """
        config = config or {}
        
        # Create offline model
        offline_model = None
        if config.get('offline_enabled', True):
            model_path = config.get('offline_model_path')
            if model_path:
                offline_model = OfflineModel(Path(model_path))
            else:
                offline_model = create_default_model()
        
        # Create online model
        online_model = None
        if config.get('online_enabled', False):
            online_config = config.get('online', {})
            online_model = create_online_model_from_config(online_config)
        
        return cls(
            offline_model=offline_model,
            online_model=online_model,
            blend_mode=config.get('blend_mode', 'confidence_weighted'),
            min_confidence=config.get('min_confidence', 0.3)
        )
    
    def has_models(self) -> bool:
        """Check if any models are available."""
        has_offline = self.offline_model and self.offline_model.is_loaded()
        has_online = self.online_model and self.online_model.is_enabled()
        return has_offline or has_online
    
    def predict(
        self,
        image: np.ndarray,
        categories: Optional[List[str]] = None,
        top_k: int = 5,
        use_online: bool = True
    ) -> List[Dict[str, float]]:
        """
        Predict texture category with fallback and blending.
        
        Args:
            image: Input image as numpy array
            categories: Optional list of categories for online model
            top_k: Number of predictions to return
            use_online: Whether to try online model first
            
        Returns:
            List of predictions sorted by confidence
        """
        with self._lock:
            self._stats['total_predictions'] += 1
        
        online_predictions = []
        offline_predictions = []
        
        # Try online model first if enabled
        if use_online and self.online_model and self.online_model.is_enabled():
            try:
                logger.debug("Attempting online prediction")
                online_predictions = self.online_model.predict(
                    image,
                    categories or [],
                    top_k=top_k
                )
                
                if online_predictions:
                    with self._lock:
                        self._stats['online_predictions'] += 1
                    logger.debug(f"Online prediction successful: {online_predictions[0]}")
            
            except Exception as e:
                logger.warning(f"Online prediction failed: {e}")
        
        # Try offline model
        if self.offline_model and self.offline_model.is_loaded():
            try:
                logger.debug("Running offline prediction")
                offline_predictions = self.offline_model.predict(image, top_k=top_k)
                
                if offline_predictions:
                    with self._lock:
                        self._stats['offline_predictions'] += 1
                    logger.debug(f"Offline prediction successful: {offline_predictions[0]}")
            
            except Exception as e:
                logger.warning(f"Offline prediction failed: {e}")
        
        # Blend predictions if both available
        if online_predictions and offline_predictions:
            with self._lock:
                self._stats['blended_predictions'] += 1
            predictions = self._blend_predictions(
                online_predictions,
                offline_predictions,
                top_k
            )
            logger.debug("Using blended predictions")
        
        # Fallback to whichever is available
        elif online_predictions:
            predictions = online_predictions
            logger.debug("Using online predictions only")
        
        elif offline_predictions:
            with self._lock:
                self._stats['fallback_predictions'] += 1
            predictions = offline_predictions
            logger.debug("Using offline predictions (fallback)")
        
        else:
            logger.warning("No predictions available from any model")
            predictions = []
        
        # Filter by minimum confidence
        predictions = [
            p for p in predictions
            if p['confidence'] >= self.min_confidence
        ]
        
        return predictions[:top_k]
    
    def _blend_predictions(
        self,
        online_preds: List[Dict[str, float]],
        offline_preds: List[Dict[str, float]],
        top_k: int
    ) -> List[Dict[str, float]]:
        """
        Blend predictions from multiple models.
        
        Args:
            online_preds: Online model predictions
            offline_preds: Offline model predictions
            top_k: Number of predictions to return
            
        Returns:
            Blended predictions
        """
        if self.blend_mode == 'max':
            # Take maximum confidence for each category
            return self._blend_max(online_preds, offline_preds, top_k)
        
        elif self.blend_mode == 'average':
            # Average confidence scores
            return self._blend_average(online_preds, offline_preds, top_k)
        
        else:  # confidence_weighted (default)
            # Weight by total confidence from each model
            return self._blend_confidence_weighted(online_preds, offline_preds, top_k)
    
    def _blend_max(
        self,
        online_preds: List[Dict[str, float]],
        offline_preds: List[Dict[str, float]],
        top_k: int
    ) -> List[Dict[str, float]]:
        """Take maximum confidence for each category."""
        category_scores = {}
        
        for pred in online_preds + offline_preds:
            cat = pred['category']
            conf = pred['confidence']
            
            if cat not in category_scores or conf > category_scores[cat]:
                category_scores[cat] = conf
        
        # Sort by confidence
        results = [
            {'category': cat, 'confidence': conf}
            for cat, conf in sorted(
                category_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]
        
        return results[:top_k]
    
    def _blend_average(
        self,
        online_preds: List[Dict[str, float]],
        offline_preds: List[Dict[str, float]],
        top_k: int
    ) -> List[Dict[str, float]]:
        """Average confidence scores."""
        category_scores = defaultdict(list)
        
        for pred in online_preds + offline_preds:
            category_scores[pred['category']].append(pred['confidence'])
        
        # Calculate averages
        results = [
            {
                'category': cat,
                'confidence': sum(scores) / len(scores)
            }
            for cat, scores in category_scores.items()
        ]
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results[:top_k]
    
    def _blend_confidence_weighted(
        self,
        online_preds: List[Dict[str, float]],
        offline_preds: List[Dict[str, float]],
        top_k: int
    ) -> List[Dict[str, float]]:
        """Weight predictions by model confidence."""
        # Calculate total confidence for each model
        online_total = sum(p['confidence'] for p in online_preds)
        offline_total = sum(p['confidence'] for p in offline_preds)
        
        total = online_total + offline_total
        if total == 0:
            return []
        
        online_weight = online_total / total
        offline_weight = offline_total / total
        
        logger.debug(f"Blend weights - Online: {online_weight:.2f}, Offline: {offline_weight:.2f}")
        
        # Weighted average
        category_scores = defaultdict(float)
        category_counts = defaultdict(int)
        
        for pred in online_preds:
            category_scores[pred['category']] += pred['confidence'] * online_weight
            category_counts[pred['category']] += 1
        
        for pred in offline_preds:
            category_scores[pred['category']] += pred['confidence'] * offline_weight
            category_counts[pred['category']] += 1
        
        # Normalize by count (average)
        results = [
            {
                'category': cat,
                'confidence': score / category_counts[cat]
            }
            for cat, score in category_scores.items()
        ]
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results[:top_k]
    
    def predict_batch(
        self,
        images: List[np.ndarray],
        categories: Optional[List[str]] = None,
        top_k: int = 5,
        use_online: bool = True
    ) -> List[List[Dict[str, float]]]:
        """
        Batch prediction with fallback and blending.
        
        Args:
            images: List of input images
            categories: Optional categories for online model
            top_k: Predictions per image
            use_online: Whether to use online model
            
        Returns:
            List of prediction lists
        """
        results = []
        for image in images:
            predictions = self.predict(image, categories, top_k, use_online)
            results.append(predictions)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            stats = self._stats.copy()
        
        stats['offline_available'] = bool(self.offline_model and self.offline_model.is_loaded())
        stats['online_available'] = bool(self.online_model and self.online_model.is_enabled())
        
        if self.offline_model:
            stats['offline_info'] = self.offline_model.get_model_info()
        
        if self.online_model:
            stats['online_info'] = self.online_model.get_stats()
        
        return stats
    
    def reset_stats(self):
        """Reset usage statistics."""
        with self._lock:
            self._stats = {
                'total_predictions': 0,
                'offline_predictions': 0,
                'online_predictions': 0,
                'blended_predictions': 0,
                'fallback_predictions': 0
            }
    
    def set_offline_model(self, model_path: Path) -> bool:
        """
        Load new offline model.
        
        Args:
            model_path: Path to ONNX model
            
        Returns:
            True if loaded successfully
        """
        with self._lock:
            try:
                new_model = OfflineModel(model_path)
                if new_model.is_loaded():
                    # Unload old model
                    if self.offline_model:
                        self.offline_model.unload()
                    
                    self.offline_model = new_model
                    logger.info(f"Offline model updated: {model_path}")
                    return True
                else:
                    logger.error("Failed to load new offline model")
                    return False
            
            except Exception as e:
                logger.error(f"Error loading offline model: {e}")
                return False
    
    def set_online_model(self, config: Dict[str, Any]) -> bool:
        """
        Configure online model.
        
        Args:
            config: Online model configuration
            
        Returns:
            True if configured successfully
        """
        with self._lock:
            try:
                new_model = create_online_model_from_config(config)
                self.online_model = new_model
                
                if new_model:
                    logger.info("Online model configured")
                    return True
                else:
                    logger.info("Online model disabled")
                    return True
            
            except Exception as e:
                logger.error(f"Error configuring online model: {e}")
                return False
    
    def cleanup(self):
        """Cleanup and release resources."""
        with self._lock:
            if self.offline_model:
                self.offline_model.unload()
            
            logger.info("ModelManager cleanup complete")
