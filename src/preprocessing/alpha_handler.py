"""
Alpha Channel Handler
Separate, analyze, and manipulate alpha channels in textures
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from typing import Optional, Tuple, Dict, Any
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.error("numpy not available - limited functionality")
    logger.error("Install with: pip install numpy")
import cv2

logger = logging.getLogger(__name__)


class AlphaChannelHandler:
    """
    Handle alpha channel operations for textures.
    
    Features:
    - Separate alpha channel from image
    - Detect UI transparency patterns
    - Remove background based on alpha
    - Analyze alpha mask shapes
    """
    
    def __init__(self):
        """Initialize alpha channel handler."""
        pass
    
    def separate_alpha(
        self,
        image: np.ndarray
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Separate alpha channel from image.
        
        Args:
            image: Input image (H, W, C) or (H, W, RGBA)
            
        Returns:
            Tuple of (rgb_image, alpha_channel)
        """
        if len(image.shape) != 3:
            return image, None
        
        if image.shape[2] == 4:
            # Has alpha channel
            rgb = image[:, :, :3]
            alpha = image[:, :, 3]
            return rgb, alpha
        elif image.shape[2] == 3:
            # No alpha channel
            return image, None
        else:
            return image, None
    
    def analyze_alpha(
        self,
        alpha: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze alpha channel properties.
        
        Args:
            alpha: Alpha channel (H, W)
            
        Returns:
            Dictionary with alpha analysis results
        """
        if alpha is None:
            return {
                'has_alpha': False,
                'has_transparency': False,
                'transparency_ratio': 0.0,
                'is_binary': False,
                'is_ui_likely': False
            }
        
        # Calculate transparency statistics
        fully_transparent = np.sum(alpha == 0)
        fully_opaque = np.sum(alpha == 255)
        partial_transparent = alpha.size - fully_transparent - fully_opaque
        
        transparency_ratio = fully_transparent / alpha.size
        has_transparency = transparency_ratio > 0.01
        is_binary = partial_transparent < (0.1 * alpha.size)  # Less than 10% partial transparency
        
        # Detect sharp UI silhouettes (common in UI textures)
        is_ui_likely = self._is_ui_silhouette(alpha)
        
        return {
            'has_alpha': True,
            'has_transparency': has_transparency,
            'transparency_ratio': transparency_ratio,
            'fully_transparent_pixels': fully_transparent,
            'fully_opaque_pixels': fully_opaque,
            'partial_transparent_pixels': partial_transparent,
            'is_binary': is_binary,
            'is_ui_likely': is_ui_likely
        }
    
    def _is_ui_silhouette(self, alpha: np.ndarray) -> bool:
        """
        Detect if alpha channel represents a UI silhouette.
        
        UI elements typically have:
        - Sharp edges in alpha channel
        - High contrast between transparent and opaque
        - Relatively simple shapes
        """
        # Calculate edge density in alpha channel
        edges = cv2.Canny(alpha, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # UI silhouettes typically have edge density between 0.05 and 0.3
        is_sharp_silhouette = 0.05 < edge_density < 0.3
        
        # Check for binary alpha (UI icons are usually fully transparent or opaque)
        unique_values = len(np.unique(alpha))
        is_mostly_binary = unique_values < 10
        
        return is_sharp_silhouette and is_mostly_binary
    
    def detect_ui_transparency(
        self,
        image: np.ndarray,
        alpha: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Detect UI transparency patterns.
        
        Args:
            image: Input image (H, W, C)
            alpha: Optional alpha channel
            
        Returns:
            Dictionary with UI transparency detection results
        """
        if alpha is None:
            # Try to extract alpha from image
            _, alpha = self.separate_alpha(image)
        
        if alpha is None:
            return {
                'is_ui': False,
                'confidence': 0.0,
                'reason': 'No alpha channel'
            }
        
        # Analyze alpha channel
        alpha_info = self.analyze_alpha(alpha)
        
        # UI detection heuristics
        ui_score = 0.0
        reasons = []
        
        # Sharp silhouettes are common in UI
        if alpha_info['is_ui_likely']:
            ui_score += 0.4
            reasons.append('Sharp UI silhouette detected')
        
        # Binary alpha is common in UI icons
        if alpha_info['is_binary']:
            ui_score += 0.3
            reasons.append('Binary alpha channel')
        
        # High transparency ratio (icons with transparent backgrounds)
        if 0.3 < alpha_info['transparency_ratio'] < 0.8:
            ui_score += 0.2
            reasons.append('Typical UI transparency ratio')
        
        # Small texture size (checked elsewhere, but common for UI)
        # This would be added by the caller
        
        return {
            'is_ui': ui_score > 0.5,
            'confidence': ui_score,
            'reasons': reasons,
            'alpha_info': alpha_info
        }
    
    def remove_background(
        self,
        image: np.ndarray,
        alpha: Optional[np.ndarray] = None,
        threshold: int = 10
    ) -> np.ndarray:
        """
        Remove background based on alpha channel.
        
        Args:
            image: Input image (H, W, C)
            alpha: Optional alpha channel
            threshold: Transparency threshold (0-255)
            
        Returns:
            Image with background removed
        """
        if alpha is None:
            _, alpha = self.separate_alpha(image)
        
        if alpha is None:
            logger.warning("No alpha channel to use for background removal")
            return image
        
        # Create mask from alpha
        mask = alpha > threshold
        
        # Apply mask to image
        result = image.copy()
        result[~mask] = 0  # Set background to black
        
        return result
    
    def create_alpha_mask(
        self,
        image: np.ndarray,
        method: str = 'threshold'
    ) -> np.ndarray:
        """
        Create alpha mask from image.
        
        Args:
            image: Input image (H, W, C)
            method: Mask creation method ('threshold', 'edge', 'color')
            
        Returns:
            Alpha mask (H, W)
        """
        if method == 'threshold':
            return self._create_mask_threshold(image)
        elif method == 'edge':
            return self._create_mask_edge(image)
        elif method == 'color':
            return self._create_mask_color(image)
        else:
            logger.warning(f"Unknown mask method '{method}', using threshold")
            return self._create_mask_threshold(image)
    
    def _create_mask_threshold(self, image: np.ndarray) -> np.ndarray:
        """Create mask based on brightness threshold."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply threshold
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        
        return mask
    
    def _create_mask_edge(self, image: np.ndarray) -> np.ndarray:
        """Create mask based on edge detection."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate edges to create mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(edges, kernel, iterations=2)
        
        return mask
    
    def _create_mask_color(
        self,
        image: np.ndarray,
        background_color: Tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """Create mask based on background color."""
        # Calculate distance from background color
        if len(image.shape) == 3:
            diff = np.sqrt(np.sum((image - background_color) ** 2, axis=2))
        else:
            diff = np.abs(image - background_color[0])
        
        # Create mask
        mask = (diff > 10).astype(np.uint8) * 255
        
        return mask
