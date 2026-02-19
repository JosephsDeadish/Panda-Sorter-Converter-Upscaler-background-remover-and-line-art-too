"""
Texture Structural Analyzer
Size, aspect ratio, color histogram analysis
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import Dict, Any, Union, Tuple
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.error("numpy not available - limited functionality")
    logger.error("Install with: pip install numpy")
from PIL import Image
import cv2
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


class TextureStructuralAnalyzer:
    """
    Analyze structural properties of textures.
    
    Features:
    - Texture size classification (UI vs environment)
    - Aspect ratio analysis (health bars, icons, etc.)
    - Color histogram clustering
    - Border detection
    """
    
    # Default size thresholds (class constants)
    DEFAULT_SMALL_SIZE = 64
    DEFAULT_MEDIUM_SIZE = 256
    DEFAULT_LARGE_SIZE = 512
    
    def __init__(self, config=None):
        """
        Initialize structural analyzer.
        
        Args:
            config: Configuration dict with structural_analysis settings
        """
        # Load thresholds from config or use defaults
        if config and hasattr(config, 'get'):
            self.small_texture_size = config.get('structural_analysis', 'small_texture_size', default=self.DEFAULT_SMALL_SIZE)
            self.medium_texture_size = config.get('structural_analysis', 'medium_texture_size', default=self.DEFAULT_MEDIUM_SIZE)
            self.large_texture_size = config.get('structural_analysis', 'large_texture_size', default=self.DEFAULT_LARGE_SIZE)
            self.low_entropy_threshold = config.get('structural_analysis', 'low_entropy_threshold', default=4.0)
            self.high_entropy_threshold = config.get('structural_analysis', 'high_entropy_threshold', default=6.0)
        else:
            # Use class-level defaults
            self.small_texture_size = self.DEFAULT_SMALL_SIZE
            self.medium_texture_size = self.DEFAULT_MEDIUM_SIZE
            self.large_texture_size = self.DEFAULT_LARGE_SIZE
            self.low_entropy_threshold = 4.0
            self.high_entropy_threshold = 6.0
            
        logger.info("TextureStructuralAnalyzer initialized")
    
    def analyze(
        self,
        image: Union[np.ndarray, Image.Image, Path]
    ) -> Dict[str, Any]:
        """
        Perform complete structural analysis.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with structural analysis results
        """
        # Load image
        if isinstance(image, Path):
            img = np.array(Image.open(image).convert('RGB'))
        elif isinstance(image, Image.Image):
            img = np.array(image)
        else:
            img = image
        
        result = {
            'size_info': self._analyze_size(img),
            'aspect_ratio_info': self._analyze_aspect_ratio(img),
            'color_info': self._analyze_colors(img),
            'border_info': self._analyze_borders(img)
        }
        
        # Determine if likely UI
        result['is_ui_likely'] = self._is_ui_texture(result)
        
        return result
    
    def _analyze_size(self, img: np.ndarray) -> Dict[str, Any]:
        """
        Analyze texture size.
        
        Small textures are more likely to be UI elements.
        """
        h, w = img.shape[:2]
        max_dim = max(h, w)
        min_dim = min(h, w)
        
        # Classify size
        if max_dim <= self.small_texture_size:
            size_class = 'small'
            ui_probability = 0.7
        elif max_dim <= self.medium_texture_size:
            size_class = 'medium'
            ui_probability = 0.4
        elif max_dim <= self.large_texture_size:
            size_class = 'large'
            ui_probability = 0.2
        else:
            size_class = 'very_large'
            ui_probability = 0.1
        
        return {
            'width': w,
            'height': h,
            'max_dimension': max_dim,
            'min_dimension': min_dim,
            'size_class': size_class,
            'ui_probability': ui_probability,
            'is_power_of_two': self._is_power_of_two(w) and self._is_power_of_two(h)
        }
    
    def _analyze_aspect_ratio(self, img: np.ndarray) -> Dict[str, Any]:
        """
        Analyze aspect ratio.
        
        Different aspect ratios indicate different texture types:
        - Wide rectangles: health bars, progress bars
        - Square: icons, portraits
        - Tall rectangles: vertical UI elements
        """
        h, w = img.shape[:2]
        aspect_ratio = w / h
        
        # Classify aspect ratio
        if 0.9 <= aspect_ratio <= 1.1:
            ratio_class = 'square'
            ui_element_type = 'icon'
            ui_probability = 0.6
        elif aspect_ratio > 2.0:
            ratio_class = 'wide'
            ui_element_type = 'health_bar'
            ui_probability = 0.8
        elif aspect_ratio < 0.5:
            ratio_class = 'tall'
            ui_element_type = 'vertical_bar'
            ui_probability = 0.7
        else:
            ratio_class = 'rectangular'
            ui_element_type = 'unknown'
            ui_probability = 0.3
        
        return {
            'aspect_ratio': aspect_ratio,
            'ratio_class': ratio_class,
            'ui_element_type': ui_element_type,
            'ui_probability': ui_probability
        }
    
    def _analyze_colors(self, img: np.ndarray) -> Dict[str, Any]:
        """
        Analyze color histogram.
        
        UI textures often have flat colors.
        World textures have gradients and more color variation.
        """
        # Calculate color histogram
        hist_r = cv2.calcHist([img], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([img], [1], None, [256], [0, 256])
        hist_b = cv2.calcHist([img], [2], None, [256], [0, 256])
        
        # Calculate histogram entropy (measure of color diversity)
        def calculate_entropy(hist):
            hist = hist / hist.sum()
            hist = hist[hist > 0]
            return -np.sum(hist * np.log2(hist))
        
        entropy_r = calculate_entropy(hist_r)
        entropy_g = calculate_entropy(hist_g)
        entropy_b = calculate_entropy(hist_b)
        avg_entropy = (entropy_r + entropy_g + entropy_b) / 3
        
        # Low entropy = flat colors (likely UI)
        # High entropy = gradients (likely world texture)
        if avg_entropy < 4.0:
            color_class = 'flat'
            ui_probability = 0.7
        elif avg_entropy < 6.0:
            color_class = 'moderate'
            ui_probability = 0.4
        else:
            color_class = 'gradient'
            ui_probability = 0.2
        
        # Detect dominant colors
        pixels = img.reshape(-1, 3)
        n_colors = min(5, len(np.unique(pixels, axis=0)))
        if n_colors > 1:
            kmeans = KMeans(n_clusters=n_colors, random_state=0, n_init=10)
            kmeans.fit(pixels)
            dominant_colors = kmeans.cluster_centers_.astype(int).tolist()
        else:
            dominant_colors = [pixels[0].tolist()]
        
        return {
            'entropy': avg_entropy,
            'color_class': color_class,
            'dominant_colors': dominant_colors,
            'num_dominant_colors': len(dominant_colors),
            'ui_probability': ui_probability
        }
    
    def _analyze_borders(self, img: np.ndarray) -> Dict[str, Any]:
        """
        Detect borders around texture.
        
        UI icons often have black borders.
        """
        h, w = img.shape[:2]
        
        # Check border pixels
        border_thickness = min(5, min(h, w) // 10)
        
        top_border = img[:border_thickness, :]
        bottom_border = img[-border_thickness:, :]
        left_border = img[:, :border_thickness]
        right_border = img[:, -border_thickness:]
        
        # Check if borders are dark (black)
        def is_dark(pixels):
            avg_brightness = np.mean(pixels)
            return avg_brightness < 30
        
        has_dark_border = (
            is_dark(top_border) or
            is_dark(bottom_border) or
            is_dark(left_border) or
            is_dark(right_border)
        )
        
        return {
            'has_dark_border': has_dark_border,
            'ui_probability': 0.6 if has_dark_border else 0.3
        }
    
    def _is_ui_texture(self, analysis: Dict[str, Any]) -> bool:
        """
        Determine if texture is likely a UI element.
        
        Combines multiple signals to make a determination.
        """
        # Calculate weighted average of UI probabilities
        weights = {
            'size_info': 0.3,
            'aspect_ratio_info': 0.3,
            'color_info': 0.2,
            'border_info': 0.2
        }
        
        total_probability = 0.0
        for key, weight in weights.items():
            if key in analysis:
                prob = analysis[key].get('ui_probability', 0.0)
                total_probability += prob * weight
        
        return total_probability > 0.5
    
    @staticmethod
    def _is_power_of_two(n: int) -> bool:
        """Check if number is a power of 2."""
        return n > 0 and (n & (n - 1)) == 0
