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
except (ImportError, OSError, RuntimeError):
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False
try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, OSError, RuntimeError):
    HAS_PIL = False

try:
    import cv2
    HAS_CV2 = True
except (ImportError, OSError, RuntimeError):
    HAS_CV2 = False
    cv2 = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

# Import model manager for smart model downloads
# Try direct import first (frozen EXE / src/ on sys.path), then src-prefixed fallback
try:
    from upscaler.model_manager import AIModelManager, ModelStatus
    model_manager = AIModelManager()
except (ImportError, OSError, RuntimeError):
    try:
        from src.upscaler.model_manager import AIModelManager, ModelStatus
        model_manager = AIModelManager()
    except (ImportError, OSError, RuntimeError):
        logger.warning("Model manager not available - model downloads disabled")
        model_manager = None
        ModelStatus = None

# Check for native Rust acceleration
# native_ops.py is a wrapper that tries to import 'texture_ops' (the compiled Rust
# extension) and falls back to pure-Python/PIL implementations automatically.
try:
    from native_ops import lanczos_upscale as _native_lanczos, NATIVE_AVAILABLE
except (ImportError, OSError, RuntimeError):
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

# ---------------------------------------------------------------------------
# torchvision compatibility shim for basicsr / realesrgan
# ---------------------------------------------------------------------------
# torchvision removed ``torchvision.transforms.functional_tensor`` in 0.16+.
# basicsr ≤ 1.4.2 imports it directly.  We inject a thin compat module so
# that ``import basicsr`` succeeds on any modern torchvision version.
try:
    import torchvision.transforms.functional_tensor as _tvft_check  # noqa: F401
except (ImportError, ModuleNotFoundError):
    try:
        import sys as _sys
        import types as _types
        import torchvision.transforms.functional as _tvtf  # noqa: F401
        _compat_mod = _types.ModuleType('torchvision.transforms.functional_tensor')
        # Mirror functions that basicsr actually calls
        for _attr in (
            'rgb_to_grayscale', 'adjust_brightness', 'adjust_contrast',
            'adjust_saturation', 'adjust_hue', 'normalize',
            'pad', 'crop', 'center_crop', 'resize',
            'to_tensor', 'to_pil_image',
        ):
            if hasattr(_tvtf, _attr):
                setattr(_compat_mod, _attr, getattr(_tvtf, _attr))
        _sys.modules['torchvision.transforms.functional_tensor'] = _compat_mod
    except Exception:
        pass  # best effort — if basicsr still fails the except below handles it
# ---------------------------------------------------------------------------

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

except (ImportError, OSError, RuntimeError) as e:
    logger.warning(f"⚠️  Real-ESRGAN not available (optional): {e}")
    REALESRGAN_AVAILABLE = False
except Exception as e:
    logger.warning(f"⚠️  Error loading Real-ESRGAN: {type(e).__name__}: {e}")
    REALESRGAN_AVAILABLE = False

# Check for GFPGAN face restoration
GFPGAN_AVAILABLE = False
try:
    from gfpgan import GFPGANer  # noqa: F401
    GFPGAN_AVAILABLE = True
    logger.info("✅ GFPGAN face restoration available")
except (ImportError, OSError, RuntimeError) as _e:
    logger.debug(f"GFPGAN not available (optional): {_e}")

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
    - GFPGAN face restoration (enhance faces/characters before upscaling)
    """
    
    def __init__(self):
        """Initialize upscaler."""
        self.realesrgan_model = None
        self._realesrgan_loaded = False
        self._loaded_model_name: str = ''
        self._gfpgan_model = None
        self._gfpgan_loaded = False
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
            return self._upscale_realesrgan(image, scale_factor, model_name='RealESRGAN_x4plus')
        elif method == 'realesrgan_anime' and REALESRGAN_AVAILABLE:
            return self._upscale_realesrgan(image, scale_factor, model_name='RealESRGAN_x4plus_anime_6B')
        elif method == 'realesrgan_x2' and REALESRGAN_AVAILABLE:
            return self._upscale_realesrgan(image, 2, model_name='RealESRGAN_x2plus')
        elif method in ('swinir', 'swinir_anime') and REALESRGAN_AVAILABLE:
            # SwinIR is loaded via basicsr — delegate to realesrgan path with correct model
            _mname = 'SwinIR_x4_realworld' if method == 'swinir' else 'SwinIR_x4_anime'
            return self._upscale_realesrgan(image, scale_factor, model_name=_mname)
        elif method == 'esrgan':
            # Fallback to bicubic if ESRGAN not available
            logger.warning("ESRGAN not fully implemented, using bicubic")
            return self._upscale_bicubic(image, scale_factor)
        else:
            if method not in ('bicubic', 'lanczos'):
                logger.warning(f"Method '{method}' unavailable (missing deps or unknown), using bicubic")
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
        scale_factor: int,
        model_name: str = 'RealESRGAN_x4plus',
    ) -> np.ndarray:
        """
        Upscale using Real-ESRGAN (or a compatible model like SwinIR via basicsr).

        Selects model by *model_name*.  Falls back to bicubic when the required
        model file or library is unavailable.
        """
        if not REALESRGAN_AVAILABLE:
            logger.warning("Real-ESRGAN libraries not available, falling back to bicubic")
            return self._upscale_bicubic(image, scale_factor)

        # For x2 variants always use 2x scale
        if model_name == 'RealESRGAN_x2plus':
            scale_factor = 2

        if not self.ensure_model_available(model_name):
            logger.warning(f"Model {model_name} not available, falling back to bicubic")
            return self._upscale_bicubic(image, scale_factor)

        try:
            # Reload if model name changed
            if not self._realesrgan_loaded or getattr(self, '_loaded_model_name', None) != model_name:
                self._load_realesrgan_model(scale_factor, model_name=model_name)

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

            logger.debug(f"Real-ESRGAN ({model_name}) upscale: {image.shape[:2]} -> {output.shape[:2]}")
            return output

        except Exception as e:
            logger.error(f"Real-ESRGAN upscaling failed ({model_name}): {e}")
            return self._upscale_bicubic(image, scale_factor)
    
    def _load_realesrgan_model(self, scale_factor: int, model_name: str = None):
        """Load Real-ESRGAN model (or a compatible SwinIR model via basicsr)."""
        try:
            # Choose model name if not explicitly given
            if model_name is None:
                model_name = 'RealESRGAN_x2plus' if scale_factor == 2 else 'RealESRGAN_x4plus'

            # SwinIR models use long filenames that differ from their dict key
            _SWINIR_FILES = {
                'SwinIR_x4_realworld': '003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth',
                'SwinIR_x4_anime':     '001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth',
            }

            # Get model path from model manager (uses dest_filename for SwinIR too)
            if self.model_manager:
                if model_name in _SWINIR_FILES:
                    model_path = str(self.model_manager.models_dir / _SWINIR_FILES[model_name])
                else:
                    model_path = str(self.model_manager.models_dir / f"{model_name}.pth")
                    # Fallback: check anime_6B variant filename
                    if model_name == 'RealESRGAN_x4plus_anime_6B' and not os.path.isfile(model_path):
                        model_path = str(self.model_manager.models_dir / 'RealESRGAN_x4plus_anime_6B.pth')
            else:
                pth = _SWINIR_FILES.get(model_name, f"{model_name}.pth")
                model_path = os.path.join('weights', pth)

            # Verify the model file exists before trying to load it
            if not os.path.isfile(model_path):
                logger.warning(
                    f"Model file not found at '{model_path}'. "
                    "Download it via Settings → AI Models. Falling back to bicubic."
                )
                self._realesrgan_loaded = False
                return

            # Anime 6B uses fewer RRDB blocks
            if 'anime_6B' in model_name:
                model = RRDBNet(
                    num_in_ch=3, num_out_ch=3, num_feat=64,
                    num_block=6, num_grow_ch=32, scale=4
                )
                _scale = 4
            elif model_name == 'RealESRGAN_x2plus':
                model = RRDBNet(
                    num_in_ch=3, num_out_ch=3, num_feat=64,
                    num_block=23, num_grow_ch=32, scale=2
                )
                _scale = 2
            elif model_name in _SWINIR_FILES:
                # SwinIR models are loaded by RealESRGANer with model=None
                model = None
                _scale = scale_factor
            else:
                model = RRDBNet(
                    num_in_ch=3, num_out_ch=3, num_feat=64,
                    num_block=23, num_grow_ch=32, scale=scale_factor
                )
                _scale = scale_factor

            self.realesrgan_model = RealESRGANer(
                scale=_scale,
                model_path=model_path,
                model=model,
                tile=0,
                tile_pad=10,
                pre_pad=0,
                half=False,  # FP32 for better compatibility
            )

            self._realesrgan_loaded = True
            self._loaded_model_name = model_name
            logger.info(f"Upscaler model loaded: {model_name}")

        except Exception as e:
            logger.error(f"Failed to load upscaler model '{model_name}': {e}")
            self._realesrgan_loaded = False

    # ── GFPGAN face / character restoration ─────────────────────────────────

    def enhance_faces(self, image: np.ndarray, upscale: int = 2) -> np.ndarray:
        """Apply GFPGAN face / character restoration to *image*.

        Falls back to the original image on any error (safe to call unconditionally).

        Args:
            image: BGR or RGB numpy array (uint8).
            upscale: Output scale factor (1 or 2 recommended).

        Returns:
            Restored image as numpy array (same colour order as input).
        """
        if not GFPGAN_AVAILABLE:
            logger.debug("GFPGAN not available — skipping face enhancement")
            return image

        try:
            if not self._gfpgan_loaded:
                self._load_gfpgan_model(upscale)
            if self._gfpgan_model is None:
                return image

            # GFPGAN expects BGR uint8; guard against 2D grayscale or single-channel arrays
            if image.ndim < 3 or image.shape[2] != 3:
                bgr = image
            else:
                bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            _, _, restored = self._gfpgan_model.enhance(
                bgr,
                has_aligned=False,
                only_center_face=False,
                paste_back=True,
            )
            out = cv2.cvtColor(restored, cv2.COLOR_BGR2RGB)
            logger.debug("GFPGAN face restoration applied")
            return out
        except Exception as exc:
            logger.warning(f"GFPGAN enhance failed ({exc}); returning original")
            return image

    def _load_gfpgan_model(self, upscale: int = 2) -> None:
        """Load GFPGANer once and cache in *self._gfpgan_model*."""
        try:
            from gfpgan import GFPGANer  # late import — optional dep

            # Build candidate list — check model_manager first, then common paths
            model_path: str | None = None
            if self.model_manager:
                mp = self.model_manager.get_model_path('GFPGANv1.4')
                if mp and mp.exists():
                    model_path = str(mp)
            if not model_path:
                import sys as _sys
                exe_dir = os.path.dirname(_sys.executable)
                candidates = [
                    # PyInstaller bundle: app_data/models/ next to EXE
                    os.path.join(exe_dir, 'app_data', 'models', 'GFPGANv1.4.pth'),
                    # Dev / source-tree run
                    os.path.join('app_data', 'models', 'GFPGANv1.4.pth'),
                    # User's home cache (gfpgan default download location)
                    os.path.join(os.path.expanduser('~'), '.cache', 'gfpgan', 'GFPGANv1.4.pth'),
                    os.path.join(os.path.expanduser('~'), 'gfpgan', 'weights', 'GFPGANv1.4.pth'),
                ]
                for c in candidates:
                    if os.path.isfile(c):
                        model_path = c
                        break

            if not model_path:
                logger.warning("GFPGANv1.4.pth not found — face enhancement skipped. "
                               "Run setup_models.py or download from Settings → AI Models.")
                self._gfpgan_loaded = True   # avoid repeated attempts
                return

            self._gfpgan_model = GFPGANer(
                model_path=model_path,
                upscale=upscale,
                arch='clean',
                channel_multiplier=2,
                bg_upsampler=None,   # set externally if Real-ESRGAN bg desired
            )
            self._gfpgan_loaded = True
            logger.info(f"GFPGANer loaded from {model_path}")
        except Exception as exc:
            logger.error(f"Failed to load GFPGAN model: {exc}")
            self._gfpgan_loaded = True  # avoid repeated attempts
