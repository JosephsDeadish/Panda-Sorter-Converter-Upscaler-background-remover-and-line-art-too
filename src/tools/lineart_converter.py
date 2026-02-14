"""
Line Art / Stencil Converter Tool
Convert images to pure black line work, 1-bit stencils, and clean line art
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Callable
from dataclasses import dataclass
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("opencv-python not available - advanced line detection disabled")


class ConversionMode(Enum):
    """Line art conversion modes."""
    PURE_BLACK = "pure_black"  # Pure black lines on transparent/white
    THRESHOLD = "threshold"  # Simple threshold
    STENCIL_1BIT = "stencil_1bit"  # 1-bit black and white
    EDGE_DETECT = "edge_detect"  # Edge detection
    ADAPTIVE = "adaptive"  # Adaptive thresholding
    SKETCH = "sketch"  # Sketch-like effect


class BackgroundMode(Enum):
    """Background options for line art."""
    TRANSPARENT = "transparent"
    WHITE = "white"
    BLACK = "black"


class MorphologyOperation(Enum):
    """Morphology operations for line modification."""
    NONE = "none"
    DILATE = "dilate"  # Expand/thicken lines
    ERODE = "erode"  # Contract/thin lines
    CLOSE = "close"  # Close small gaps
    OPEN = "open"  # Remove small details


@dataclass
class LineArtSettings:
    """Settings for line art conversion."""
    mode: ConversionMode = ConversionMode.PURE_BLACK
    threshold: int = 128
    invert: bool = False
    background_mode: BackgroundMode = BackgroundMode.TRANSPARENT
    remove_midtones: bool = True
    midtone_threshold: int = 200
    morphology_operation: MorphologyOperation = MorphologyOperation.NONE
    morphology_iterations: int = 1
    morphology_kernel_size: int = 3
    denoise: bool = True
    denoise_size: int = 2
    sharpen: bool = False
    sharpen_amount: float = 1.0
    contrast_boost: float = 1.0
    auto_threshold: bool = False


@dataclass
class ConversionResult:
    """Result of a line art conversion."""
    input_path: str
    output_path: str
    success: bool
    error_message: str = ""
    original_size: Tuple[int, int] = (0, 0)
    output_size: Tuple[int, int] = (0, 0)
    mode_used: str = ""
    threshold_used: int = 0


class LineArtConverter:
    """
    Comprehensive line art converter that can:
    - Convert to pure black linework
    - Create 1-bit stencils
    - Detect and extract edges
    - Adjust line thickness with morphology
    - Remove noise and speckles
    - Remove midtones automatically
    """
    
    def __init__(self):
        """Initialize the converter."""
        self.has_cv2 = HAS_CV2
    
    def convert_image(self,
                     input_path: str,
                     output_path: str,
                     settings: LineArtSettings) -> ConversionResult:
        """
        Convert a single image to line art.
        
        Args:
            input_path: Path to input image
            output_path: Path to save output image
            settings: Conversion settings
            
        Returns:
            ConversionResult object
        """
        try:
            # Load image
            img = Image.open(input_path)
            original_size = img.size
            
            # Convert to grayscale for processing
            if img.mode != 'L':
                gray = img.convert('L')
            else:
                gray = img
            
            # Apply contrast boost if needed
            if settings.contrast_boost != 1.0:
                enhancer = ImageEnhance.Contrast(gray)
                gray = enhancer.enhance(settings.contrast_boost)
            
            # Sharpen if requested
            if settings.sharpen:
                gray = self._sharpen_image(gray, settings.sharpen_amount)
            
            # Auto-threshold if requested
            if settings.auto_threshold:
                threshold = self._calculate_auto_threshold(gray)
            else:
                threshold = settings.threshold
            
            # Apply conversion mode
            result_img = self._apply_conversion_mode(gray, settings, threshold)
            
            # Remove midtones if requested
            if settings.remove_midtones:
                result_img = self._remove_midtones(result_img, settings.midtone_threshold)
            
            # Apply morphology operations
            if settings.morphology_operation != MorphologyOperation.NONE:
                result_img = self._apply_morphology(result_img, settings)
            
            # Denoise if requested
            if settings.denoise:
                result_img = self._denoise(result_img, settings.denoise_size)
            
            # Invert if requested
            if settings.invert:
                result_img = ImageOps.invert(result_img)
            
            # Apply background mode
            final_img = self._apply_background(result_img, settings.background_mode)
            
            # Save
            final_img.save(output_path, format='PNG', optimize=True)
            
            return ConversionResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                original_size=original_size,
                output_size=final_img.size,
                mode_used=settings.mode.value,
                threshold_used=threshold
            )
            
        except Exception as e:
            logger.error(f"Error converting {input_path}: {e}")
            return ConversionResult(
                input_path=input_path,
                output_path=output_path,
                success=False,
                error_message=str(e)
            )
    
    def convert_batch(self,
                     input_paths: List[str],
                     output_directory: str,
                     settings: LineArtSettings,
                     progress_callback: Optional[Callable] = None) -> List[ConversionResult]:
        """
        Convert multiple images to line art.
        
        Args:
            input_paths: List of input image paths
            output_directory: Directory to save output images
            settings: Conversion settings
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            List of ConversionResult objects
        """
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        total = len(input_paths)
        
        for i, input_path in enumerate(input_paths):
            try:
                # Generate output path
                input_file = Path(input_path)
                output_path = output_dir / f"{input_file.stem}_lineart.png"
                
                # Ensure unique filename
                counter = 1
                while output_path.exists():
                    output_path = output_dir / f"{input_file.stem}_lineart_{counter}.png"
                    counter += 1
                
                # Convert image
                result = self.convert_image(input_path, str(output_path), settings)
                results.append(result)
                
                if progress_callback:
                    progress_callback(i + 1, total, input_file.name)
                    
            except Exception as e:
                logger.error(f"Error processing {input_path}: {e}")
                results.append(ConversionResult(
                    input_path=input_path,
                    output_path="",
                    success=False,
                    error_message=str(e)
                ))
                
                if progress_callback:
                    progress_callback(i + 1, total, Path(input_path).name)
        
        return results
    
    def _sharpen_image(self, img: Image.Image, amount: float) -> Image.Image:
        """Sharpen image for better line detection."""
        from PIL import ImageFilter
        
        # Apply unsharp mask
        blurred = img.filter(ImageFilter.GaussianBlur(radius=1))
        arr = np.array(img).astype(float)
        blurred_arr = np.array(blurred).astype(float)
        
        # Sharpen formula: original + amount * (original - blurred)
        sharpened = arr + amount * (arr - blurred_arr)
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        
        return Image.fromarray(sharpened, mode='L')
    
    def _calculate_auto_threshold(self, img: Image.Image) -> int:
        """
        Calculate optimal threshold using Otsu's method.
        
        Returns threshold value (0-255).
        """
        if self.has_cv2:
            arr = np.array(img)
            threshold, _ = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return int(threshold)
        else:
            # Fallback: use histogram to find optimal threshold
            histogram = img.histogram()
            total_pixels = sum(histogram)
            
            # Calculate weighted sum
            sum_total = sum(i * histogram[i] for i in range(256))
            sum_background = 0
            weight_background = 0
            max_variance = 0
            threshold = 0
            
            for i in range(256):
                weight_background += histogram[i]
                if weight_background == 0:
                    continue
                
                weight_foreground = total_pixels - weight_background
                if weight_foreground == 0:
                    break
                
                sum_background += i * histogram[i]
                mean_background = sum_background / weight_background
                mean_foreground = (sum_total - sum_background) / weight_foreground
                
                # Calculate between-class variance
                variance = weight_background * weight_foreground * (mean_background - mean_foreground) ** 2
                
                if variance > max_variance:
                    max_variance = variance
                    threshold = i
            
            return threshold
    
    def _apply_conversion_mode(self,
                              img: Image.Image,
                              settings: LineArtSettings,
                              threshold: int) -> Image.Image:
        """Apply the selected conversion mode."""
        if settings.mode == ConversionMode.PURE_BLACK:
            # Pure black lines on white
            arr = np.array(img)
            binary = (arr < threshold).astype(np.uint8) * 255
            return Image.fromarray(binary, mode='L')
        
        elif settings.mode == ConversionMode.THRESHOLD:
            # Simple threshold
            arr = np.array(img)
            binary = (arr >= threshold).astype(np.uint8) * 255
            return Image.fromarray(binary, mode='L')
        
        elif settings.mode == ConversionMode.STENCIL_1BIT:
            # 1-bit stencil (pure black and white)
            return img.point(lambda p: 255 if p >= threshold else 0, mode='1').convert('L')
        
        elif settings.mode == ConversionMode.EDGE_DETECT:
            # Edge detection
            return self._detect_edges(img)
        
        elif settings.mode == ConversionMode.ADAPTIVE:
            # Adaptive thresholding
            return self._adaptive_threshold(img)
        
        elif settings.mode == ConversionMode.SKETCH:
            # Sketch effect
            return self._sketch_effect(img)
        
        else:
            # Default to pure black
            arr = np.array(img)
            binary = (arr < threshold).astype(np.uint8) * 255
            return Image.fromarray(binary, mode='L')
    
    def _detect_edges(self, img: Image.Image) -> Image.Image:
        """Detect edges in image."""
        if self.has_cv2:
            arr = np.array(img)
            
            # Use Canny edge detection
            edges = cv2.Canny(arr, 50, 150)
            
            # Invert (white lines on black)
            edges = 255 - edges
            
            return Image.fromarray(edges, mode='L')
        else:
            # Fallback: use PIL's FIND_EDGES filter
            edges = img.filter(ImageFilter.FIND_EDGES)
            # Invert
            edges = ImageOps.invert(edges)
            return edges
    
    def _adaptive_threshold(self, img: Image.Image) -> Image.Image:
        """Apply adaptive thresholding."""
        if self.has_cv2:
            arr = np.array(img)
            
            # Apply adaptive threshold
            binary = cv2.adaptiveThreshold(
                arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            return Image.fromarray(binary, mode='L')
        else:
            # Fallback: simple local threshold
            arr = np.array(img)
            window_size = 11
            pad = window_size // 2
            
            # Pad array
            padded = np.pad(arr, pad, mode='edge')
            
            # Calculate local mean
            result = np.zeros_like(arr)
            for i in range(arr.shape[0]):
                for j in range(arr.shape[1]):
                    window = padded[i:i+window_size, j:j+window_size]
                    local_mean = window.mean()
                    result[i, j] = 255 if arr[i, j] >= local_mean - 2 else 0
            
            return Image.fromarray(result, mode='L')
    
    def _sketch_effect(self, img: Image.Image) -> Image.Image:
        """Apply sketch effect."""
        if self.has_cv2:
            arr = np.array(img)
            
            # Invert
            inverted = 255 - arr
            
            # Blur inverted image
            blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
            
            # Blend using color dodge
            sketch = cv2.divide(arr, 255 - blurred, scale=256)
            
            return Image.fromarray(sketch, mode='L')
        else:
            # Fallback: simple edge enhancement
            edges = img.filter(ImageFilter.FIND_EDGES)
            edges = ImageOps.invert(edges)
            return edges
    
    def _remove_midtones(self, img: Image.Image, threshold: int) -> Image.Image:
        """
        Remove midtones, keeping only pure black and white.
        
        Args:
            img: Input grayscale image
            threshold: Threshold for white (0-255). Values above this become white.
        """
        arr = np.array(img)
        
        # Everything above threshold becomes white (255)
        # Everything below becomes black (0)
        binary = np.where(arr >= threshold, 255, 0).astype(np.uint8)
        
        return Image.fromarray(binary, mode='L')
    
    def _apply_morphology(self, img: Image.Image, settings: LineArtSettings) -> Image.Image:
        """Apply morphology operations to modify lines."""
        if not self.has_cv2:
            return img
        
        arr = np.array(img)
        kernel_size = settings.morphology_kernel_size
        iterations = settings.morphology_iterations
        
        # Create kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        # Apply operation
        if settings.morphology_operation == MorphologyOperation.DILATE:
            # Expand/thicken lines (on black pixels)
            result = cv2.dilate(arr, kernel, iterations=iterations)
        
        elif settings.morphology_operation == MorphologyOperation.ERODE:
            # Contract/thin lines (on black pixels)
            result = cv2.erode(arr, kernel, iterations=iterations)
        
        elif settings.morphology_operation == MorphologyOperation.CLOSE:
            # Close small gaps (dilate then erode)
            result = cv2.morphologyEx(arr, cv2.MORPH_CLOSE, kernel, iterations=iterations)
        
        elif settings.morphology_operation == MorphologyOperation.OPEN:
            # Remove small details (erode then dilate)
            result = cv2.morphologyEx(arr, cv2.MORPH_OPEN, kernel, iterations=iterations)
        
        else:
            result = arr
        
        return Image.fromarray(result, mode='L')
    
    def _denoise(self, img: Image.Image, size: int) -> Image.Image:
        """
        Remove noise and speckles.
        
        Args:
            img: Input image
            size: Minimum size of features to keep (in pixels)
        """
        if not self.has_cv2:
            # Fallback: simple median filter
            from PIL import ImageFilter
            return img.filter(ImageFilter.MedianFilter(size=3))
        
        arr = np.array(img)
        
        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            255 - arr, connectivity=8
        )
        
        # Create output array
        result = np.ones_like(arr) * 255
        
        # Keep only components larger than threshold
        min_size = size * size
        for i in range(1, num_labels):  # Skip background (label 0)
            if stats[i, cv2.CC_STAT_AREA] >= min_size:
                result[labels == i] = 0
        
        return Image.fromarray(result, mode='L')
    
    def _apply_background(self, img: Image.Image, mode: BackgroundMode) -> Image.Image:
        """Apply background mode to result."""
        if mode == BackgroundMode.TRANSPARENT:
            # Convert to RGBA with transparent background
            arr = np.array(img)
            
            # Create RGBA array
            rgba = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
            
            # Black pixels become opaque black
            # White pixels become transparent
            rgba[:, :, 0] = arr  # R
            rgba[:, :, 1] = arr  # G
            rgba[:, :, 2] = arr  # B
            rgba[:, :, 3] = 255 - arr  # Alpha (inverted)
            
            return Image.fromarray(rgba, mode='RGBA')
        
        elif mode == BackgroundMode.WHITE:
            # Keep as grayscale with white background
            return img
        
        elif mode == BackgroundMode.BLACK:
            # Invert to get black background
            return ImageOps.invert(img)
        
        return img
    
    def preview_settings(self,
                        sample_image_path: str,
                        settings: LineArtSettings) -> Image.Image:
        """
        Generate preview of how settings will affect an image.
        
        Args:
            sample_image_path: Path to sample image
            settings: Conversion settings to preview
            
        Returns:
            Processed PIL Image
        """
        img = Image.open(sample_image_path)
        
        # Convert to grayscale
        if img.mode != 'L':
            gray = img.convert('L')
        else:
            gray = img
        
        # Apply contrast boost
        if settings.contrast_boost != 1.0:
            enhancer = ImageEnhance.Contrast(gray)
            gray = enhancer.enhance(settings.contrast_boost)
        
        # Sharpen if requested
        if settings.sharpen:
            gray = self._sharpen_image(gray, settings.sharpen_amount)
        
        # Auto-threshold if requested
        if settings.auto_threshold:
            threshold = self._calculate_auto_threshold(gray)
        else:
            threshold = settings.threshold
        
        # Apply conversion mode
        result_img = self._apply_conversion_mode(gray, settings, threshold)
        
        # Remove midtones if requested
        if settings.remove_midtones:
            result_img = self._remove_midtones(result_img, settings.midtone_threshold)
        
        # Apply morphology operations
        if settings.morphology_operation != MorphologyOperation.NONE:
            result_img = self._apply_morphology(result_img, settings)
        
        # Denoise if requested
        if settings.denoise:
            result_img = self._denoise(result_img, settings.denoise_size)
        
        # Invert if requested
        if settings.invert:
            result_img = ImageOps.invert(result_img)
        
        # Apply background mode
        final_img = self._apply_background(result_img, settings.background_mode)
        
        return final_img
