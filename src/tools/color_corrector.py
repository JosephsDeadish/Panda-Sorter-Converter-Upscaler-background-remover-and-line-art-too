"""
Color Correction Tool

Provides various color correction and enhancement features:
- Auto white balance
- Exposure correction
- Vibrance enhancement
- Clarity/sharpness
- LUT support (.cube files)
"""

import logging
from PIL import Image
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.error("numpy not available - limited functionality")
    logger.error("Install with: pip install numpy")
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import re

logger = logging.getLogger(__name__)


class ColorCorrector:
    """Main color correction class combining all correction methods."""
    
    def __init__(self):
        """Initialize color corrector."""
        self.lut_cache = {}  # Cache loaded LUTs
        
    def auto_white_balance(self, image: Image.Image, strength: float = 1.0) -> Image.Image:
        """
        Apply auto white balance using gray world algorithm.
        
        Args:
            image: Input PIL Image
            strength: Correction strength (0.0 to 1.0)
            
        Returns:
            Corrected PIL Image
        """
        try:
            # Convert to numpy array
            img_array = np.array(image, dtype=np.float32)
            
            # Calculate average values for each channel
            r_avg = np.mean(img_array[:, :, 0])
            g_avg = np.mean(img_array[:, :, 1])
            b_avg = np.mean(img_array[:, :, 2])
            
            # Calculate gray value (average of all channels)
            gray = (r_avg + g_avg + b_avg) / 3
            
            # Calculate correction factors
            r_gain = gray / r_avg if r_avg > 0 else 1.0
            g_gain = gray / g_avg if g_avg > 0 else 1.0
            b_gain = gray / b_avg if b_avg > 0 else 1.0
            
            # Apply strength factor (blend with original)
            r_gain = 1.0 + (r_gain - 1.0) * strength
            g_gain = 1.0 + (g_gain - 1.0) * strength
            b_gain = 1.0 + (b_gain - 1.0) * strength
            
            # Apply corrections
            img_array[:, :, 0] = np.clip(img_array[:, :, 0] * r_gain, 0, 255)
            img_array[:, :, 1] = np.clip(img_array[:, :, 1] * g_gain, 0, 255)
            img_array[:, :, 2] = np.clip(img_array[:, :, 2] * b_gain, 0, 255)
            
            # Convert back to PIL Image
            return Image.fromarray(img_array.astype(np.uint8), mode=image.mode)
            
        except Exception as e:
            logger.error(f"Auto white balance failed: {e}")
            return image
    
    def adjust_exposure(self, image: Image.Image, ev_stops: float) -> Image.Image:
        """
        Adjust image exposure in EV stops.
        
        Args:
            image: Input PIL Image
            ev_stops: Exposure adjustment in stops (-3.0 to +3.0)
            
        Returns:
            Adjusted PIL Image
        """
        try:
            # Convert to numpy array
            img_array = np.array(image, dtype=np.float32)
            
            # Calculate exposure multiplier (2^ev_stops)
            multiplier = 2.0 ** ev_stops
            
            # Apply exposure adjustment
            img_array = img_array * multiplier
            
            # Clip to valid range
            img_array = np.clip(img_array, 0, 255)
            
            # Convert back to PIL Image
            return Image.fromarray(img_array.astype(np.uint8), mode=image.mode)
            
        except Exception as e:
            logger.error(f"Exposure adjustment failed: {e}")
            return image
    
    def enhance_vibrance(self, image: Image.Image, amount: float) -> Image.Image:
        """
        Enhance vibrance (selective saturation boost).
        
        Args:
            image: Input PIL Image
            amount: Vibrance amount (0.0 to 2.0, 1.0 = no change)
            
        Returns:
            Enhanced PIL Image
        """
        try:
            # Convert to numpy array
            img_array = np.array(image, dtype=np.float32) / 255.0
            
            # Convert RGB to HSV
            r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
            
            max_rgb = np.maximum(np.maximum(r, g), b)
            min_rgb = np.minimum(np.minimum(r, g), b)
            diff = max_rgb - min_rgb
            
            # Calculate saturation
            saturation = np.where(max_rgb > 0, diff / max_rgb, 0)
            
            # Vibrance: boost less saturated colors more
            # (protects already saturated areas like skin tones)
            boost = (1 - saturation) * (amount - 1) + 1
            
            # Apply boost to each channel relative to gray
            gray = (r + g + b) / 3
            r = gray + (r - gray) * boost
            g = gray + (g - gray) * boost
            b = gray + (b - gray) * boost
            
            # Clip and convert back
            img_array[:, :, 0] = np.clip(r, 0, 1)
            img_array[:, :, 1] = np.clip(g, 0, 1)
            img_array[:, :, 2] = np.clip(b, 0, 1)
            
            img_array = (img_array * 255).astype(np.uint8)
            
            return Image.fromarray(img_array, mode=image.mode)
            
        except Exception as e:
            logger.error(f"Vibrance enhancement failed: {e}")
            return image
    
    def enhance_clarity(self, image: Image.Image, amount: float, radius: int = 2) -> Image.Image:
        """
        Enhance clarity (local contrast/mid-tone sharpness).
        
        Args:
            image: Input PIL Image
            amount: Clarity amount (0.0 to 2.0)
            radius: Blur radius for clarity calculation
            
        Returns:
            Enhanced PIL Image
        """
        try:
            from PIL import ImageFilter
            
            # Convert to numpy array
            img_array = np.array(image, dtype=np.float32)
            
            # Create blurred version for high-pass filter
            blurred = image.filter(ImageFilter.GaussianBlur(radius))
            blurred_array = np.array(blurred, dtype=np.float32)
            
            # Calculate high-pass (detail) layer
            detail = img_array - blurred_array
            
            # Apply clarity (add detail back with multiplier)
            img_array = img_array + detail * (amount - 1.0)
            
            # Clip to valid range
            img_array = np.clip(img_array, 0, 255)
            
            return Image.fromarray(img_array.astype(np.uint8), mode=image.mode)
            
        except Exception as e:
            logger.error(f"Clarity enhancement failed: {e}")
            return image
    
    def load_lut(self, lut_path: str) -> Optional[np.ndarray]:
        """
        Load a .cube LUT file.
        
        Args:
            lut_path: Path to .cube file
            
        Returns:
            3D LUT array or None if failed
        """
        try:
            # Check cache first
            if lut_path in self.lut_cache:
                return self.lut_cache[lut_path]
            
            with open(lut_path, 'r') as f:
                lines = f.readlines()
            
            # Parse LUT file
            lut_size = None
            lut_data = []
            
            for line in lines:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Get LUT size
                if line.startswith('LUT_3D_SIZE'):
                    lut_size = int(line.split()[-1])
                    continue
                
                # Get LUT data (RGB triplets)
                parts = line.split()
                if len(parts) == 3:
                    try:
                        r, g, b = map(float, parts)
                        lut_data.append([r, g, b])
                    except ValueError:
                        continue
            
            if not lut_size or not lut_data:
                logger.error(f"Invalid LUT file: {lut_path}")
                return None
            
            # Convert to numpy array and reshape to 3D
            lut_array = np.array(lut_data, dtype=np.float32)
            lut_array = lut_array.reshape((lut_size, lut_size, lut_size, 3))
            
            # Cache the LUT
            self.lut_cache[lut_path] = lut_array
            
            return lut_array
            
        except Exception as e:
            logger.error(f"Failed to load LUT {lut_path}: {e}")
            return None
    
    def apply_lut(self, image: Image.Image, lut: np.ndarray, strength: float = 1.0) -> Image.Image:
        """
        Apply a 3D LUT to an image.
        
        Args:
            image: Input PIL Image
            lut: 3D LUT array
            strength: LUT application strength (0.0 to 1.0)
            
        Returns:
            LUT-applied PIL Image
        """
        try:
            # Convert to numpy array
            img_array = np.array(image, dtype=np.float32) / 255.0
            h, w = img_array.shape[:2]
            
            # Get LUT size
            lut_size = lut.shape[0]
            
            # Map image colors to LUT indices
            r_idx = (img_array[:, :, 0] * (lut_size - 1)).astype(np.float32)
            g_idx = (img_array[:, :, 1] * (lut_size - 1)).astype(np.float32)
            b_idx = (img_array[:, :, 2] * (lut_size - 1)).astype(np.float32)
            
            # Get integer indices and fractional parts for interpolation
            r0 = np.floor(r_idx).astype(np.int32)
            g0 = np.floor(g_idx).astype(np.int32)
            b0 = np.floor(b_idx).astype(np.int32)
            
            r1 = np.minimum(r0 + 1, lut_size - 1)
            g1 = np.minimum(g0 + 1, lut_size - 1)
            b1 = np.minimum(b0 + 1, lut_size - 1)
            
            r_frac = (r_idx - r0).reshape(h, w, 1)
            g_frac = (g_idx - g0).reshape(h, w, 1)
            b_frac = (b_idx - b0).reshape(h, w, 1)
            
            # Trilinear interpolation
            c000 = lut[r0, g0, b0]
            c001 = lut[r0, g0, b1]
            c010 = lut[r0, g1, b0]
            c011 = lut[r0, g1, b1]
            c100 = lut[r1, g0, b0]
            c101 = lut[r1, g0, b1]
            c110 = lut[r1, g1, b0]
            c111 = lut[r1, g1, b1]
            
            c00 = c000 * (1 - b_frac) + c001 * b_frac
            c01 = c010 * (1 - b_frac) + c011 * b_frac
            c10 = c100 * (1 - b_frac) + c101 * b_frac
            c11 = c110 * (1 - b_frac) + c111 * b_frac
            
            c0 = c00 * (1 - g_frac) + c01 * g_frac
            c1 = c10 * (1 - g_frac) + c11 * g_frac
            
            result = c0 * (1 - r_frac) + c1 * r_frac
            
            # Blend with original based on strength
            if strength < 1.0:
                result = img_array * (1 - strength) + result * strength
            
            # Convert back to 0-255 range
            result = np.clip(result * 255, 0, 255).astype(np.uint8)
            
            return Image.fromarray(result, mode=image.mode)
            
        except Exception as e:
            logger.error(f"LUT application failed: {e}")
            return image
    
    def apply_corrections(
        self,
        image: Image.Image,
        white_balance: float = 0.0,
        exposure: float = 0.0,
        vibrance: float = 1.0,
        clarity: float = 0.0,
        lut_path: Optional[str] = None,
        lut_strength: float = 1.0
    ) -> Image.Image:
        """
        Apply multiple corrections to an image.
        
        Args:
            image: Input PIL Image
            white_balance: Auto white balance strength (0.0 to 1.0)
            exposure: Exposure adjustment in EV stops (-3.0 to +3.0)
            vibrance: Vibrance amount (0.0 to 2.0)
            clarity: Clarity amount (0.0 to 2.0)
            lut_path: Optional path to .cube LUT file
            lut_strength: LUT application strength (0.0 to 1.0)
            
        Returns:
            Corrected PIL Image
        """
        result = image.copy()
        
        # Apply in optimal order
        if white_balance > 0:
            result = self.auto_white_balance(result, white_balance)
        
        if exposure != 0:
            result = self.adjust_exposure(result, exposure)
        
        if vibrance != 1.0:
            result = self.enhance_vibrance(result, vibrance)
        
        if clarity > 0:
            result = self.enhance_clarity(result, clarity)
        
        if lut_path:
            lut = self.load_lut(lut_path)
            if lut is not None:
                result = self.apply_lut(result, lut, lut_strength)
        
        return result
    
    def batch_process(
        self,
        input_files: List[str],
        output_dir: str,
        settings: Dict[str, Any],
        progress_callback=None
    ) -> Tuple[int, List[str]]:
        """
        Batch process multiple images with same corrections.
        
        Args:
            input_files: List of input image paths
            output_dir: Output directory
            settings: Dictionary of correction settings
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            Tuple of (success_count, error_messages)
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        errors = []
        
        for idx, input_file in enumerate(input_files):
            try:
                if progress_callback:
                    progress_callback(idx + 1, len(input_files), Path(input_file).name)
                
                # Load image
                image = Image.open(input_file)
                
                # Apply corrections
                result = self.apply_corrections(image, **settings)
                
                # Save result
                output_file = Path(output_dir) / Path(input_file).name
                result.save(output_file, quality=95)
                
                success_count += 1
                logger.info(f"Processed: {input_file} -> {output_file}")
                
            except Exception as e:
                error_msg = f"Failed to process {input_file}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return success_count, errors
