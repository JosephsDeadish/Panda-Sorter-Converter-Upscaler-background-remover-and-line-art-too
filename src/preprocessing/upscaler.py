"""
Texture Upscaling Module
Supports bicubic, ESRGAN, Real-ESRGAN, and native Lanczos upscaling
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from typing import Optional, Union
import numpy as np
from PIL import Image
import cv2

logger = logging.getLogger(__name__)

# Check for native Rust acceleration
try:
    from native_ops import lanczos_upscale as _native_lanczos, NATIVE_AVAILABLE
except ImportError as e:
    logger.debug(f"Native acceleration not available: {e}")
    NATIVE_AVAILABLE = False
    _native_lanczos = None

# Check for Real-ESRGAN - with comprehensive error handling
REALESRGAN_AVAILABLE = False
try:
    # Try to import both packages
    try:
        import basicsr
    except ImportError:
        logger.debug("basicsr not available")
        raise
    
    try:
        import realesrgan
    except ImportError:
        logger.debug("realesrgan not available")
        raise
    
    # Try to import the specific classes
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    
    REALESRGAN_AVAILABLE = True
    logger.info("✅ Real-ESRGAN upscaling available")
    
except ImportError as e:
    logger.warning(f"⚠️  Real-ESRGAN not available (optional): {e}")
    REALESRGAN_AVAILABLE = False
except Exception as e:
    logger.warning(f"⚠️  Error loading Real-ESRGAN: {type(e).__name__}: {e}")
    REALESRGAN_AVAILABLE = False


class TextureUpscaler:
    """
    Upscale textures using various methods.
    
    Supported methods:
    - Bicubic interpolation (fast, good quality)
    - Lanczos via native Rust (fast, sharp – uses multi-threaded Rust code)
    - ESRGAN (slow, best quality for general images)
    - Real-ESRGAN (slow, best for PS2/retro textures)
    """
    
    def __init__(self):
        """Initialize upscaler."""
        self.realesrgan_model = None
        self._realesrgan_loaded = False
        if NATIVE_AVAILABLE:
            logger.info("Native Rust Lanczos upscaler available")
        
    def upscale(
        self,
        image: np.ndarray,
        scale_factor: int = 4,
        method: str = 'bicubic'
    ) -> np.ndarray:
        """
        Upscale an image.
        
        Args:
            image: Input image as numpy array (H, W, C)
            scale_factor: Upscaling factor (2, 4, or 8)
            method: Upscaling method ('bicubic', 'lanczos', 'esrgan', 'realesrgan')
            
        Returns:
            Upscaled image as numpy array
        """
        if method == 'lanczos' and NATIVE_AVAILABLE:
            return self._upscale_native_lanczos(image, scale_factor)
        elif method == 'bicubic':
            return self._upscale_bicubic(image, scale_factor)
        elif method == 'realesrgan' and REALESRGAN_AVAILABLE:
            return self._upscale_realesrgan(image, scale_factor)
        elif method == 'esrgan':
            # Fallback to bicubic if ESRGAN not available
            logger.warning("ESRGAN not fully implemented, using bicubic")
            return self._upscale_bicubic(image, scale_factor)
        else:
            logger.warning(f"Unknown upscaling method '{method}', using bicubic")
            return self._upscale_bicubic(image, scale_factor)
    
    def _upscale_bicubic(self, image: np.ndarray, scale_factor: int) -> np.ndarray:
        """
        Upscale using bicubic interpolation with detail enhancement.
        
        Applies a multi-pass pipeline:
        1. cv2 bicubic resize
        2. Unsharp mask to restore detail lost during interpolation
        3. Subtle detail-enhancement pass
        """
        h, w = image.shape[:2]
        new_h = h * scale_factor
        new_w = w * scale_factor
        
        upscaled = cv2.resize(
            image,
            (new_w, new_h),
            interpolation=cv2.INTER_CUBIC
        )
        
        # Unsharp mask: sharpen to counteract interpolation blur
        # gaussian_blur → subtract → weighted add
        blurred = cv2.GaussianBlur(upscaled, (0, 0), sigmaX=1.5)
        upscaled = cv2.addWeighted(upscaled, 1.5, blurred, -0.5, 0)
        
        # Detail enhancement: extract detail layer and amplify it
        smooth = cv2.bilateralFilter(upscaled, d=5, sigmaColor=50, sigmaSpace=50)
        detail = cv2.subtract(upscaled, smooth)
        # Amplify detail layer by 1.5x and recombine
        upscaled = cv2.add(smooth, cv2.multiply(detail, 1.5))
        
        logger.debug(f"Bicubic upscale: {image.shape[:2]} -> {upscaled.shape[:2]}")
        return upscaled
    
    def _upscale_native_lanczos(self, image: np.ndarray, scale_factor: int) -> np.ndarray:
        """
        Upscale using native Rust Lanczos-3 interpolation.
        
        Multi-threaded via Rayon – significantly faster than Python-based
        upscaling for large images.
        """
        try:
            upscaled = _native_lanczos(image, scale_factor)
            logger.debug(f"Native Lanczos upscale: {image.shape[:2]} -> {upscaled.shape[:2]}")
            return upscaled
        except Exception as e:
            logger.warning(f"Native Lanczos failed ({e}), falling back to bicubic")
            return self._upscale_bicubic(image, scale_factor)
    
    def _upscale_realesrgan(
        self,
        image: np.ndarray,
        scale_factor: int
    ) -> np.ndarray:
        """
        Upscale using Real-ESRGAN.
        
        Best quality for retro/PS2 textures but slower.
        """
        if not REALESRGAN_AVAILABLE:
            logger.warning("Real-ESRGAN not available, falling back to bicubic")
            return self._upscale_bicubic(image, scale_factor)
        
        try:
            # Load model if not already loaded
            if not self._realesrgan_loaded:
                self._load_realesrgan_model(scale_factor)
            
            # Real-ESRGAN expects BGR format
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image
            
            # Upscale
            output, _ = self.realesrgan_model.enhance(image_bgr, outscale=scale_factor)
            
            # Convert back to RGB
            if len(output.shape) == 3 and output.shape[2] == 3:
                output = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
            
            logger.debug(f"Real-ESRGAN upscale: {image.shape[:2]} -> {output.shape[:2]}")
            return output
            
        except Exception as e:
            logger.error(f"Real-ESRGAN upscaling failed: {e}")
            return self._upscale_bicubic(image, scale_factor)
    
    def _load_realesrgan_model(self, scale_factor: int):
        """Load Real-ESRGAN model."""
        try:
            # Choose model based on scale factor
            if scale_factor == 4:
                model_name = 'RealESRGAN_x4plus'
                model_path = 'weights/RealESRGAN_x4plus.pth'
            elif scale_factor == 2:
                model_name = 'RealESRGAN_x2plus'
                model_path = 'weights/RealESRGAN_x2plus.pth'
            else:
                # Default to x4
                model_name = 'RealESRGAN_x4plus'
                model_path = 'weights/RealESRGAN_x4plus.pth'
            
            # Create model
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=scale_factor
            )
            
            # Note: In production, model weights should be downloaded automatically
            # For now, we'll use the pre-trained model if available
            self.realesrgan_model = RealESRGANer(
                scale=scale_factor,
                model_path=model_path,
                model=model,
                tile=0,
                tile_pad=10,
                pre_pad=0,
                half=False  # Use FP32 for better compatibility
            )
            
            self._realesrgan_loaded = True
            logger.info(f"Real-ESRGAN model loaded: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load Real-ESRGAN model: {e}")
            self._realesrgan_loaded = False
