"""
Online AI Model API Client
Optional OpenAI CLIP API wrapper with fallback support
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("Requests library not available. Online AI features disabled.")


logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    retry_after_seconds: int = 60


class OnlineModel:
    """
    Online AI API client for texture classification.
    
    Supports configurable API endpoints (OpenAI CLIP, custom APIs).
    Includes timeout handling, rate limiting, and graceful fallback.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = "https://api.openai.com/v1",
        model: str = "clip-vit-base-patch32",
        timeout: int = 30,
        rate_limit: Optional[RateLimitConfig] = None
    ):
        """
        Initialize online model client.
        
        Args:
            api_key: API key for authentication
            api_url: Base URL for API endpoint
            model: Model identifier
            timeout: Request timeout in seconds
            rate_limit: Rate limiting configuration
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.rate_limit = rate_limit or RateLimitConfig()
        
        self._enabled = bool(api_key and REQUESTS_AVAILABLE)
        self._request_times: List[float] = []
        self._lock = threading.Lock()
        self._retry_after: Optional[float] = None
        
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available")
        elif not api_key:
            logger.info("No API key provided. Online AI features disabled.")
        else:
            logger.info(f"Online model initialized: {model}")
    
    def is_enabled(self) -> bool:
        """Check if online model is enabled and available."""
        return self._enabled
    
    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit allows new request.
        
        Returns:
            True if request is allowed, False otherwise
        """
        with self._lock:
            now = time.time()
            
            # Check retry-after cooldown
            if self._retry_after and now < self._retry_after:
                logger.debug(f"Rate limited. Retry after {self._retry_after - now:.1f}s")
                return False
            
            # Clean old request times
            self._request_times = [t for t in self._request_times if now - t < 3600]
            
            # Check limits
            recent_minute = sum(1 for t in self._request_times if now - t < 60)
            recent_hour = len(self._request_times)
            
            if recent_minute >= self.rate_limit.max_requests_per_minute:
                logger.warning("Rate limit exceeded (per minute)")
                return False
            
            if recent_hour >= self.rate_limit.max_requests_per_hour:
                logger.warning("Rate limit exceeded (per hour)")
                return False
            
            # Record request
            self._request_times.append(now)
            return True
    
    def _set_retry_after(self, seconds: int):
        """Set retry-after cooldown period."""
        with self._lock:
            self._retry_after = time.time() + seconds
    
    def _encode_image_base64(self, image: np.ndarray) -> str:
        """
        Encode image to base64 for API transmission.
        
        Args:
            image: Image as numpy array
            
        Returns:
            Base64 encoded image string
        """
        import base64
        import io
        from PIL import Image
        
        # Convert to PIL Image
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        img_pil = Image.fromarray(image)
        
        # Encode as JPEG to reduce size
        buffer = io.BytesIO()
        img_pil.save(buffer, format='JPEG', quality=85)
        img_bytes = buffer.getvalue()
        
        # Base64 encode
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"
    
    def predict(
        self,
        image: np.ndarray,
        categories: List[str],
        top_k: int = 5
    ) -> List[Dict[str, float]]:
        """
        Classify image using online API.
        
        Args:
            image: Input image as numpy array
            categories: List of possible categories
            top_k: Number of top predictions to return
            
        Returns:
            List of predictions with category and confidence
        """
        if not self.is_enabled():
            logger.debug("Online model not enabled")
            return []
        
        if not self._check_rate_limit():
            logger.warning("Rate limit exceeded, skipping online prediction")
            return []
        
        try:
            # Encode image
            image_b64 = self._encode_image_base64(image)
            
            # Prepare request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Build prompt for zero-shot classification
            category_text = ", ".join(categories[:20])  # Limit categories
            
            payload = {
                'model': self.model,
                'image': image_b64,
                'labels': categories[:20],
                'top_k': top_k
            }
            
            # Make API request
            endpoint = f"{self.api_url}/classify"
            logger.debug(f"Making request to {endpoint}")
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                predictions = self._parse_predictions(result, top_k)
                logger.info(f"Online prediction successful: {predictions[:2]}")
                return predictions
            
            elif response.status_code == 429:
                # Rate limited by API
                retry_after = int(response.headers.get('Retry-After', 60))
                self._set_retry_after(retry_after)
                logger.warning(f"API rate limited. Retry after {retry_after}s")
                return []
            
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return []
        
        except requests.exceptions.Timeout:
            logger.warning(f"API request timed out after {self.timeout}s")
            return []
        
        except requests.exceptions.ConnectionError:
            logger.warning("API connection failed. Check internet connection.")
            return []
        
        except Exception as e:
            logger.error(f"Online prediction error: {e}", exc_info=True)
            return []
    
    def _parse_predictions(self, response: Dict[str, Any], top_k: int) -> List[Dict[str, float]]:
        """
        Parse API response into standardized predictions.
        
        Args:
            response: API response dictionary
            top_k: Number of predictions to return
            
        Returns:
            List of predictions
        """
        predictions = []
        
        # Try different response formats
        if 'predictions' in response:
            results = response['predictions']
        elif 'labels' in response and 'scores' in response:
            results = [
                {'label': label, 'score': score}
                for label, score in zip(response['labels'], response['scores'])
            ]
        else:
            logger.warning(f"Unknown response format: {response.keys()}")
            return []
        
        # Extract predictions
        for item in results[:top_k]:
            category = item.get('label') or item.get('category') or item.get('class')
            confidence = item.get('score') or item.get('confidence') or item.get('probability')
            
            if category and confidence is not None:
                predictions.append({
                    'category': str(category),
                    'confidence': float(confidence)
                })
        
        return predictions
    
    def predict_batch(
        self,
        images: List[np.ndarray],
        categories: List[str],
        top_k: int = 5
    ) -> List[List[Dict[str, float]]]:
        """
        Batch prediction (sequential for now to respect rate limits).
        
        Args:
            images: List of images
            categories: List of categories
            top_k: Top predictions per image
            
        Returns:
            List of prediction lists
        """
        results = []
        for image in images:
            predictions = self.predict(image, categories, top_k)
            results.append(predictions)
            
            # Small delay to respect rate limits
            time.sleep(0.1)
        
        return results
    
    def test_connection(self) -> bool:
        """
        Test API connection and authentication.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.is_enabled():
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Try a simple health check endpoint
            endpoint = f"{self.api_url}/health"
            response = requests.get(endpoint, headers=headers, timeout=5)
            
            if response.status_code == 200:
                logger.info("Online API connection successful")
                return True
            else:
                logger.warning(f"API health check failed: {response.status_code}")
                return False
        
        except Exception as e:
            logger.warning(f"API connection test failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            now = time.time()
            recent_minute = sum(1 for t in self._request_times if now - t < 60)
            recent_hour = sum(1 for t in self._request_times if now - t < 3600)
            
            return {
                'enabled': self._enabled,
                'requests_last_minute': recent_minute,
                'requests_last_hour': recent_hour,
                'rate_limited': self._retry_after is not None and now < self._retry_after,
                'retry_after': max(0, self._retry_after - now) if self._retry_after else 0,
                'model': self.model,
                'api_url': self.api_url
            }


def create_online_model_from_config(config: Dict[str, Any]) -> Optional[OnlineModel]:
    """
    Create online model from configuration dictionary.
    
    Args:
        config: Configuration with api_key, api_url, etc.
        
    Returns:
        OnlineModel instance or None if disabled
    """
    if not config.get('enabled', False):
        return None
    
    api_key = config.get('api_key')
    if not api_key:
        logger.info("No API key in config. Online features disabled.")
        return None
    
    return OnlineModel(
        api_key=api_key,
        api_url=config.get('api_url', 'https://api.openai.com/v1'),
        model=config.get('model', 'clip-vit-base-patch32'),
        timeout=config.get('timeout', 30),
        rate_limit=RateLimitConfig(
            max_requests_per_minute=config.get('max_requests_per_minute', 60),
            max_requests_per_hour=config.get('max_requests_per_hour', 1000)
        )
    )
