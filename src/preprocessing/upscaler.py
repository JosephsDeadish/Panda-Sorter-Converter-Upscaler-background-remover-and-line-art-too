"""
Texture Upscaling Module
Supports bicubic, ESRGAN, Real-ESRGAN, and native Lanczos upscaling
Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Union
from pathlib import Path
try:
    import numpy as np
    HAS_NUMPY = True
except (ImportError, OSError):
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False
try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, OSError):
    HAS_PIL = False

try:
    import cv2
    HAS_CV2 = True
except (ImportError, OSError):
    HAS_CV2 = False
    cv2 = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

# Import model manager for smart model downloads
# Try direct import first (frozen EXE / src/ on sys.path), then src-prefixed fallback
try:
    from upscaler.model_manager import AIModelManager, ModelStatus
    model_manager = AIModelManager()
except (ImportError, OSError):
    try:
        from src.upscaler.model_manager import AIModelManager, ModelStatus
        model_manager = AIModelManager()
    except (ImportError, OSError):
        logger.warning("Model manager not available - model downloads disabled")
        model_manager = None
        ModelStatus = None

# Check for native Rust acceleration
# native_ops.py is a wrapper that tries to import 'texture_ops' (the compiled Rust
# extension) and falls back to pure-Python/PIL implementations automatically.
try:
    from native_ops import lanczos_upscale as _native_lanczos, NATIVE_AVAILABLE
except (ImportError, OSError):
    # Fallback: try importing texture_ops (the Rust wheel) directly
    try:
        import texture_ops as _tx
        NATIVE_AVAILABLE = True
        def _native_lanczos(image, scale_factor):
            import numpy as np
            flat = image.tobytes()
            h, w = image.shape[:2]
            channels = image.shape[2] if len(image.shape) == 3 else 1
            result_bytes, new_w, new_h = _tx.lanczos_upscale(flat, w, h, channels, scale_factor)
            return np.frombuffer(result_bytes, dtype=np.uint8).reshape(new_h, new_w, channels)
    except Exception as e:
        logger.debug(f"Native acceleration not available: {e}")
        NATIVE_AVAILABLE = False
        _native_lanczos = None
except Exception as e:
    logger.debug(f"Native acceleration not available: {e}")
    NATIVE_AVAILABLE = False
    _native_lanczos = None

# Check for Real-ESRGAN - with comprehensive error handling
REALESRGAN_AVAILABLE = False
try:
    # Import both required packages
    import basicsr
    import realesrgan
    
    # Import the specific classes we need
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

# Module-level flag: True when at minimum PIL is available (basic upscaling works).
# REALESRGAN_AVAILABLE / NATIVE_AVAILABLE cover the optional faster backends.
UPSCALER_AVAILABLE: bool = HAS_PIL


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
        self.model_manager = model_manager
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
    
    def ensure_model_available(self, model_name: str = 'RealESRGAN_x4plus') -> bool:
        """
        Check if model is available, prompt to download if not
        
        Returns:
            True if model is available or successfully downloaded
        """
        if not self.model_manager:
            logger.warning("Model manager not available")
            return False
        
        status = self.model_manager.get_model_status(model_name)
        
        if status == ModelStatus.INSTALLED:
            return True
        elif status == ModelStatus.MISSING:
            logger.warning(f"Model {model_name} not installed")
            return False
        else:
            logger.error(f"Error checking model status")
            return False
    
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
            logger.warning("Real-ESRGAN libraries not available, falling back to bicubic")
            return self._upscale_bicubic(image, scale_factor)
        
        # Check if model is available
        model_name = 'RealESRGAN_x2plus' if scale_factor == 2 else 'RealESRGAN_x4plus'
        if not self.ensure_model_available(model_name):
            logger.warning(f"Model {model_name} not available, falling back to bicubic")
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
            elif scale_factor == 2:
                model_name = 'RealESRGAN_x2plus'
            else:
                # Default to x4
                model_name = 'RealESRGAN_x4plus'
            
            # Get model path from model manager
            if self.model_manager:
                model_path = str(self.model_manager.models_dir / f"{model_name}.pth")
            else:
                # Fallback to old location
                model_path = f'weights/{model_name}.pth'

            # Verify the model file exists before trying to load it
            if not os.path.isfile(model_path):
                logger.warning(
                    f"Real-ESRGAN model file not found at '{model_path}'. "
                    "Download it or run the model manager. Falling back to PIL upscaling."
                )
                self._realesrgan_loaded = False
                return
            
            # Create model
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=scale_factor
            )
            
            # Use model from model manager
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
