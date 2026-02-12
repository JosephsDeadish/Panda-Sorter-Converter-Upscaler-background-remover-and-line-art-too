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
    Complete preprocessing pipeline for PS2 textures with HD/4K support.
    
    Features:
    - Conditional preprocessing based on texture resolution
    - Upscaling small textures (bicubic, ESRGAN, Real-ESRGAN)
    - Sharpening filters (Laplacian, Unsharp mask)
    - Denoising (non-local means, bilateral filtering)
    - Alpha channel handling
    - Color normalization
    - Edge detection
    - Retro mode for low-res textures (<256px): upscale + denoise/sharpen
    - HD mode for high-res textures (>1024px): downscale only + minimal processing
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
        edge_method: str = 'canny',  # 'canny', 'sobel'
        retro_threshold: int = 256,  # Threshold for retro mode
        hd_threshold: int = 1024,  # Threshold for HD mode
        target_model_size: int = 224  # Target size for vision models (CLIP, ViT, DINOv2)
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
            retro_threshold: Resolution threshold for retro mode processing
            hd_threshold: Resolution threshold for HD mode processing
            target_model_size: Target input size for vision models
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
        self.retro_threshold = retro_threshold
        self.hd_threshold = hd_threshold
        self.target_model_size = target_model_size
        
        # Initialize components
        self.upscaler = TextureUpscaler() if upscale_enabled else None
        self.filters = TextureFilters()
        self.alpha_handler = AlphaChannelHandler() if handle_alpha else None
        
        logger.info(f"PreprocessingPipeline initialized: upscale={upscale_enabled}, "
                   f"sharpen={sharpen_enabled}, denoise={denoise_enabled}, "
                   f"retro_threshold={retro_threshold}, hd_threshold={hd_threshold}")
    
    def process(
        self,
        image: Union[np.ndarray, Image.Image, Path],
        min_size_for_upscale: int = 128,
        for_model_input: bool = False
    ) -> Dict[str, Any]:
        """
        Process an image through the preprocessing pipeline.
        Uses conditional preprocessing based on texture resolution:
        - Retro mode (<256px): upscale + denoise/sharpen
        - HD mode (>1024px): downscale + minimal processing
        - Standard mode (256-1024px): normal processing
        
        Args:
            image: Input image (numpy array, PIL Image, or Path)
            min_size_for_upscale: Minimum size to trigger upscaling
            for_model_input: Whether to prepare for vision model input
            
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
            
            # Determine preprocessing mode based on resolution
            h, w = img.shape[:2]
            min_dim = min(h, w)
            max_dim = max(h, w)
            
            # Use min_dim for retro check (any dimension too small needs upscaling)
            # Use max_dim for HD check (any dimension very large needs minimal processing)
            # This handles edge cases like 200x2000 (retro) and 1000x4000 (HD)
            if min_dim < self.retro_threshold:
                mode = 'retro'
            elif max_dim > self.hd_threshold:
                mode = 'hd'
            else:
                mode = 'standard'
            
            logger.debug(f"Preprocessing mode: {mode} (resolution: {w}x{h})")
            
            # Store alpha channel if present
            alpha_channel = None
            if has_alpha and self.handle_alpha:
                alpha_channel = img[:, :, 3]
                img = img[:, :, :3]
            
            # Apply mode-specific preprocessing
            if mode == 'retro':
                img = self._process_retro_mode(img, min_size_for_upscale)
            elif mode == 'hd':
                img = self._process_hd_mode(img)
            else:
                img = self._process_standard_mode(img, min_size_for_upscale)
            
            # Final model preprocessing if requested
            if for_model_input:
                img = self._prepare_for_model(img)
            
            # Edge detection (for analysis, not modifying image)
            edge_info = None
            if self.detect_edges:
                edge_info = self.filters.detect_edges(img, method=self.edge_method)
            
            # Restore alpha channel
            if alpha_channel is not None and not for_model_input:
                # Ensure alpha channel matches processed image dimensions
                if alpha_channel.shape[:2] != img.shape[:2]:
                    alpha_channel = cv2.resize(
                        alpha_channel,
                        (img.shape[1], img.shape[0]),
                        interpolation=cv2.INTER_CUBIC
                    )
                img = np.dstack([img, alpha_channel])
            
            return {
                'image': img,
                'original_shape': original_shape,
                'processed_shape': img.shape,
                'preprocessing_mode': mode,
                'upscaled': mode == 'retro',
                'downscaled': mode == 'hd',
                'has_alpha': has_alpha,
                'edges': edge_info,
                'model_ready': for_model_input
            }
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise
    
    def _process_retro_mode(self, img: np.ndarray, min_size: int) -> np.ndarray:
        """
        Process low-resolution texture (retro mode).
        Applies upscaling + light denoise/sharpen.
        
        Args:
            img: Input image
            min_size: Minimum size for upscaling
            
        Returns:
            Processed image
        """
        # Upscale small textures
        if self.upscale_enabled and self._should_upscale(img, min_size):
            logger.debug(f"Retro mode: Upscaling texture from {img.shape[:2]}")
            img = self.upscaler.upscale(
                img,
                scale_factor=self.upscale_factor,
                method=self.upscale_method
            )
        
        # Light denoising for retro textures
        if self.denoise_enabled:
            logger.debug("Retro mode: Applying light denoising")
            img = self.filters.denoise(img, method=self.denoise_method)
        
        # Sharpen to restore details after upscaling
        if self.sharpen_enabled:
            logger.debug("Retro mode: Applying sharpening")
            img = self.filters.sharpen(img, method=self.sharpen_method)
        
        # Color normalization
        if self.normalize_colors:
            logger.debug("Retro mode: Normalizing colors")
            img = self.filters.normalize_colors(img)
        
        return img
    
    def _process_hd_mode(self, img: np.ndarray) -> np.ndarray:
        """
        Process high-resolution texture (HD mode).
        Applies minimal processing to preserve detail.
        
        Args:
            img: Input image
            
        Returns:
            Processed image
        """
        logger.debug(f"HD mode: Minimal processing for {img.shape[:2]} texture")
        
        # NO aggressive sharpening or denoising for HD/4K textures
        # to avoid hurting detail
        
        # Only apply minimal color normalization
        if self.normalize_colors:
            logger.debug("HD mode: Gentle color normalization")
            img = self.filters.normalize_colors(img)
        
        # Downscaling for model input happens later in _prepare_for_model
        
        return img
    
    def _process_standard_mode(self, img: np.ndarray, min_size: int) -> np.ndarray:
        """
        Process standard resolution texture (256-1024px).
        Applies normal processing pipeline.
        
        Args:
            img: Input image
            min_size: Minimum size for upscaling
            
        Returns:
            Processed image
        """
        # Standard upscaling if needed
        if self.upscale_enabled and self._should_upscale(img, min_size):
            logger.debug(f"Standard mode: Upscaling texture from {img.shape[:2]}")
            img = self.upscaler.upscale(
                img,
                scale_factor=self.upscale_factor,
                method=self.upscale_method
            )
        
        # Standard denoising
        if self.denoise_enabled:
            logger.debug("Standard mode: Applying denoising")
            img = self.filters.denoise(img, method=self.denoise_method)
        
        # Standard sharpening
        if self.sharpen_enabled:
            logger.debug("Standard mode: Applying sharpening")
            img = self.filters.sharpen(img, method=self.sharpen_method)
        
        # Color normalization
        if self.normalize_colors:
            logger.debug("Standard mode: Normalizing colors")
            img = self.filters.normalize_colors(img)
        
        return img
    
    def _prepare_for_model(self, img: np.ndarray) -> np.ndarray:
        """
        Prepare image for vision model input (CLIP, ViT, DINOv2).
        Resizes and center-crops to target model size (typically 224x224).
        
        Args:
            img: Input image
            
        Returns:
            Model-ready image
        """
        h, w = img.shape[:2]
        target = self.target_model_size
        
        # Resize shortest side to target size
        if h < w:
            new_h = target
            new_w = int(w * target / h)
        else:
            new_w = target
            new_h = int(h * target / w)
        
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Center crop to square
        h, w = img.shape[:2]
        start_y = (h - target) // 2
        start_x = (w - target) // 2
        img = img[start_y:start_y + target, start_x:start_x + target]
        
        logger.debug(f"Prepared image for model: {img.shape}")
        return img
    
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
