"""
PS2 Texture Preprocessing Pipeline
Handles upscaling, sharpening, denoising, color normalization for PS2 textures
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
import numpy as np
from PIL import Image
import cv2

from .upscaler import TextureUpscaler
from .filters import TextureFilters
from .alpha_handler import AlphaChannelHandler

logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """
    Complete preprocessing pipeline for PS2 textures.
    
    Features:
    - Upscaling small textures (bicubic, ESRGAN, Real-ESRGAN)
    - Sharpening filters (Laplacian, Unsharp mask)
    - Denoising (non-local means, bilateral filtering)
    - Alpha channel handling
    - Color normalization
    - Edge detection
    """
    
    def __init__(
        self,
        upscale_enabled: bool = True,
        upscale_factor: int = 4,
        upscale_method: str = 'bicubic',  # 'bicubic', 'esrgan', 'realesrgan'
        sharpen_enabled: bool = True,
        sharpen_method: str = 'unsharp',  # 'laplacian', 'unsharp'
        denoise_enabled: bool = False,
        denoise_method: str = 'bilateral',  # 'nlmeans', 'bilateral'
        normalize_colors: bool = True,
        handle_alpha: bool = True,
        detect_edges: bool = False,
        edge_method: str = 'canny'  # 'canny', 'sobel'
    ):
        """
        Initialize preprocessing pipeline.
        
        Args:
            upscale_enabled: Enable upscaling for small textures
            upscale_factor: Upscaling factor (4x or 8x)
            upscale_method: Upscaling method
            sharpen_enabled: Enable sharpening filters
            sharpen_method: Sharpening method
            denoise_enabled: Enable denoising
            denoise_method: Denoising method
            normalize_colors: Enable color normalization
            handle_alpha: Enable alpha channel handling
            detect_edges: Enable edge detection
            edge_method: Edge detection method
        """
        self.upscale_enabled = upscale_enabled
        self.upscale_factor = upscale_factor
        self.upscale_method = upscale_method
        self.sharpen_enabled = sharpen_enabled
        self.sharpen_method = sharpen_method
        self.denoise_enabled = denoise_enabled
        self.denoise_method = denoise_method
        self.normalize_colors = normalize_colors
        self.handle_alpha = handle_alpha
        self.detect_edges = detect_edges
        self.edge_method = edge_method
        
        # Initialize components
        self.upscaler = TextureUpscaler() if upscale_enabled else None
        self.filters = TextureFilters()
        self.alpha_handler = AlphaChannelHandler() if handle_alpha else None
        
        logger.info(f"PreprocessingPipeline initialized: upscale={upscale_enabled}, "
                   f"sharpen={sharpen_enabled}, denoise={denoise_enabled}")
    
    def process(
        self,
        image: Union[np.ndarray, Image.Image, Path],
        min_size_for_upscale: int = 128
    ) -> Dict[str, Any]:
        """
        Process an image through the preprocessing pipeline.
        
        Args:
            image: Input image (numpy array, PIL Image, or Path)
            min_size_for_upscale: Minimum size to trigger upscaling
            
        Returns:
            Dictionary containing processed image and metadata
        """
        try:
            # Load image
            if isinstance(image, Path):
                img = np.array(Image.open(image))
            elif isinstance(image, Image.Image):
                img = np.array(image)
            else:
                img = image
            
            original_shape = img.shape
            has_alpha = img.shape[2] == 4 if len(img.shape) == 3 else False
            
            # Store alpha channel if present
            alpha_channel = None
            if has_alpha and self.handle_alpha:
                alpha_channel = img[:, :, 3]
                img = img[:, :, :3]
            
            # Upscale small textures
            if self.upscale_enabled and self._should_upscale(img, min_size_for_upscale):
                logger.debug(f"Upscaling texture from {img.shape[:2]}")
                img = self.upscaler.upscale(
                    img,
                    scale_factor=self.upscale_factor,
                    method=self.upscale_method
                )
                if alpha_channel is not None:
                    # Upscale alpha channel
                    alpha_channel = cv2.resize(
                        alpha_channel,
                        (img.shape[1], img.shape[0]),
                        interpolation=cv2.INTER_CUBIC
                    )
            
            # Denoise
            if self.denoise_enabled:
                logger.debug("Applying denoising")
                img = self.filters.denoise(img, method=self.denoise_method)
            
            # Sharpen
            if self.sharpen_enabled:
                logger.debug("Applying sharpening")
                img = self.filters.sharpen(img, method=self.sharpen_method)
            
            # Color normalization
            if self.normalize_colors:
                logger.debug("Normalizing colors")
                img = self.filters.normalize_colors(img)
            
            # Edge detection (for analysis, not modifying image)
            edge_info = None
            if self.detect_edges:
                edge_info = self.filters.detect_edges(img, method=self.edge_method)
            
            # Restore alpha channel
            if alpha_channel is not None:
                img = np.dstack([img, alpha_channel])
            
            return {
                'image': img,
                'original_shape': original_shape,
                'processed_shape': img.shape,
                'upscaled': self.upscale_enabled and self._should_upscale(
                    np.ones((original_shape[0], original_shape[1])), min_size_for_upscale
                ),
                'has_alpha': has_alpha,
                'edges': edge_info
            }
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise
    
    def _should_upscale(self, img: np.ndarray, min_size: int) -> bool:
        """Check if image should be upscaled."""
        h, w = img.shape[:2]
        return min(h, w) < min_size
    
    def process_batch(
        self,
        images: list,
        min_size_for_upscale: int = 128
    ) -> list:
        """
        Process multiple images in batch.
        
        Args:
            images: List of images
            min_size_for_upscale: Minimum size to trigger upscaling
            
        Returns:
            List of processed results
        """
        results = []
        for img in images:
            try:
                result = self.process(img, min_size_for_upscale)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process image in batch: {e}")
                results.append(None)
        return results
