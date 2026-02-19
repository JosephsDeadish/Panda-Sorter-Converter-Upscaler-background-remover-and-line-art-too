"""
Image Filters for Texture Processing
Sharpening, denoising, edge detection, color normalization
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


class TextureFilters:
    """
    Image filtering operations for texture preprocessing.
    
    Features:
    - Sharpening (Laplacian, Unsharp mask)
    - Denoising (Non-local means, Bilateral filtering)
    - Edge detection (Canny, Sobel)
    - Color normalization
    """
    
    def __init__(self):
        """Initialize texture filters."""
        pass
    
    def sharpen(
        self,
        image: np.ndarray,
        method: str = 'unsharp',
        strength: float = 1.0
    ) -> np.ndarray:
        """
        Sharpen an image.
        
        Args:
            image: Input image (H, W, C)
            method: Sharpening method ('laplacian', 'unsharp')
            strength: Sharpening strength (0.0 to 2.0)
            
        Returns:
            Sharpened image
        """
        if method == 'laplacian':
            return self._sharpen_laplacian(image, strength)
        elif method == 'unsharp':
            return self._sharpen_unsharp(image, strength)
        else:
            logger.warning(f"Unknown sharpening method '{method}', using unsharp")
            return self._sharpen_unsharp(image, strength)
    
    def _sharpen_laplacian(self, image: np.ndarray, strength: float) -> np.ndarray:
        """
        Sharpen using Laplacian filter.
        
        Good for enhancing edges and fine details.
        """
        # Convert to float for processing
        img_float = image.astype(np.float32)
        
        # Apply Laplacian
        laplacian = cv2.Laplacian(img_float, cv2.CV_32F)
        
        # Add Laplacian to original image
        sharpened = img_float - strength * laplacian
        
        # Clip values and convert back
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        
        return sharpened
    
    def _sharpen_unsharp(
        self,
        image: np.ndarray,
        strength: float,
        radius: float = 1.0,
        threshold: int = 0
    ) -> np.ndarray:
        """
        Sharpen using unsharp mask.
        
        More natural-looking sharpening than Laplacian.
        """
        # Create Gaussian blur
        blurred = cv2.GaussianBlur(image, (0, 0), radius)
        
        # Calculate unsharp mask
        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
        
        # Apply threshold if specified
        if threshold > 0:
            low_contrast_mask = np.absolute(image - blurred) < threshold
            sharpened = np.where(low_contrast_mask, image, sharpened)
        
        return sharpened
    
    def denoise(
        self,
        image: np.ndarray,
        method: str = 'bilateral',
        strength: float = 10.0
    ) -> np.ndarray:
        """
        Denoise an image.
        
        Args:
            image: Input image (H, W, C)
            method: Denoising method ('nlmeans', 'bilateral')
            strength: Denoising strength
            
        Returns:
            Denoised image
        """
        if method == 'nlmeans':
            return self._denoise_nlmeans(image, strength)
        elif method == 'bilateral':
            return self._denoise_bilateral(image, strength)
        else:
            logger.warning(f"Unknown denoising method '{method}', using bilateral")
            return self._denoise_bilateral(image, strength)
    
    def _denoise_nlmeans(self, image: np.ndarray, strength: float) -> np.ndarray:
        """
        Denoise using non-local means.
        
        Best quality but slower. Good for PS2 textures with compression artifacts.
        """
        # Non-local means denoising
        if len(image.shape) == 3:
            # Color image
            denoised = cv2.fastNlMeansDenoisingColored(
                image,
                None,
                h=strength,
                hColor=strength,
                templateWindowSize=7,
                searchWindowSize=21
            )
        else:
            # Grayscale image
            denoised = cv2.fastNlMeansDenoising(
                image,
                None,
                h=strength,
                templateWindowSize=7,
                searchWindowSize=21
            )
        
        return denoised
    
    def _denoise_bilateral(self, image: np.ndarray, strength: float) -> np.ndarray:
        """
        Denoise using bilateral filter.
        
        Faster than non-local means. Preserves edges while smoothing.
        """
        # Bilateral filtering
        denoised = cv2.bilateralFilter(
            image,
            d=9,
            sigmaColor=strength,
            sigmaSpace=strength
        )
        
        return denoised
    
    def normalize_colors(
        self,
        image: np.ndarray,
        fix_ps2_gamma: bool = True,
        reduce_banding: bool = True
    ) -> np.ndarray:
        """
        Normalize colors in the image.
        
        Args:
            image: Input image (H, W, C)
            fix_ps2_gamma: Fix PS2 gamma shift
            reduce_banding: Reduce color banding
            
        Returns:
            Normalized image
        """
        normalized = image.copy()
        
        # Fix PS2 gamma shift
        if fix_ps2_gamma:
            normalized = self._fix_gamma(normalized, gamma=1.2)
        
        # Normalize brightness
        normalized = self._normalize_brightness(normalized)
        
        # Reduce color banding
        if reduce_banding:
            normalized = self._reduce_banding(normalized)
        
        return normalized
    
    def _fix_gamma(self, image: np.ndarray, gamma: float) -> np.ndarray:
        """Apply gamma correction."""
        inv_gamma = 1.0 / gamma
        table = np.array([
            ((i / 255.0) ** inv_gamma) * 255
            for i in range(256)
        ]).astype(np.uint8)
        
        return cv2.LUT(image, table)
    
    def _normalize_brightness(self, image: np.ndarray) -> np.ndarray:
        """Normalize image brightness."""
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels
        lab = cv2.merge([l, a, b])
        
        # Convert back to RGB
        normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        
        return normalized
    
    def _reduce_banding(self, image: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
        """
        Reduce color banding artifacts.
        
        Applies subtle dithering to smooth color transitions.
        
        Args:
            image: Input image
            seed: Optional random seed for reproducibility
        """
        # Use random number generator with optional seed
        rng = np.random.default_rng(seed)
        
        # Add small amount of noise to break up banding
        noise = rng.normal(0, 1, image.shape).astype(np.float32)
        result = image.astype(np.float32) + noise
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    def detect_edges(
        self,
        image: np.ndarray,
        method: str = 'canny'
    ) -> Dict[str, Any]:
        """
        Detect edges in an image.
        
        Args:
            image: Input image (H, W, C)
            method: Edge detection method ('canny', 'sobel')
            
        Returns:
            Dictionary with edge information
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        if method == 'canny':
            edges = self._detect_edges_canny(gray)
        elif method == 'sobel':
            edges = self._detect_edges_sobel(gray)
        else:
            logger.warning(f"Unknown edge detection method '{method}', using canny")
            edges = self._detect_edges_canny(gray)
        
        # Calculate edge density
        edge_density = np.sum(edges > 0) / edges.size
        
        return {
            'edges': edges,
            'edge_density': edge_density,
            'method': method,
            'is_ui_likely': edge_density > 0.1  # UI textures often have sharp edges
        }
    
    def _detect_edges_canny(self, gray: np.ndarray) -> np.ndarray:
        """Detect edges using Canny edge detector."""
        edges = cv2.Canny(gray, threshold1=50, threshold2=150)
        return edges
    
    def _detect_edges_sobel(self, gray: np.ndarray) -> np.ndarray:
        """Detect edges using Sobel operator."""
        # Calculate gradients
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calculate magnitude
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        magnitude = np.uint8(np.clip(magnitude, 0, 255))
        
        return magnitude
