"""
Batch Format Normalizer Tool
Normalize images to consistent format, size, and naming patterns
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Callable
from dataclasses import dataclass
from PIL import Image, ImageOps, ImageDraw
from enum import Enum
import re

logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("opencv-python not available - advanced centering disabled")


class PaddingMode(Enum):
    """Padding modes for making images square."""
    TRANSPARENT = "transparent"
    BLACK = "black"
    WHITE = "white"
    BLUR = "blur"
    EDGE_EXTEND = "edge_extend"


class ResizeMode(Enum):
    """Resize modes for fitting images."""
    FIT = "fit"  # Fit inside target size (letterbox/pillarbox)
    FILL = "fill"  # Fill target size (crop if needed)
    STRETCH = "stretch"  # Stretch to exact size (may distort)
    NONE = "none"  # No resize, only pad


class OutputFormat(Enum):
    """Output format options."""
    PNG = "PNG"
    JPEG = "JPEG"
    WEBP = "WEBP"
    TIFF = "TIFF"


class NamingPattern(Enum):
    """Naming pattern options."""
    ORIGINAL = "original"  # Keep original name
    SEQUENTIAL = "sequential"  # image_001, image_002, etc.
    TIMESTAMP = "timestamp"  # image_20240101_120000
    DESCRIPTIVE = "descriptive"  # prefix_WxH_index


@dataclass
class NormalizationSettings:
    """Settings for batch normalization."""
    target_width: int = 1024
    target_height: int = 1024
    make_square: bool = True
    resize_mode: ResizeMode = ResizeMode.FIT
    padding_mode: PaddingMode = PaddingMode.TRANSPARENT
    center_subject: bool = True
    output_format: OutputFormat = OutputFormat.PNG
    jpeg_quality: int = 95
    webp_quality: int = 95
    naming_pattern: NamingPattern = NamingPattern.ORIGINAL
    naming_prefix: str = "image"
    preserve_alpha: bool = True
    force_rgb: bool = False
    strip_metadata: bool = False  # Strip EXIF and other metadata from output


@dataclass
class NormalizationResult:
    """Result of a normalization operation."""
    input_path: str
    output_path: str
    success: bool
    error_message: str = ""
    original_size: Tuple[int, int] = (0, 0)
    output_size: Tuple[int, int] = (0, 0)
    format_changed: bool = False
    was_resized: bool = False
    was_padded: bool = False


class BatchFormatNormalizer:
    """
    Comprehensive batch format normalizer that can:
    - Resize to target dimensions
    - Pad to square with various modes
    - Center subject automatically
    - Standardize format (PNG/JPEG/WebP)
    - Rename according to patterns
    """
    
    def __init__(self):
        """Initialize the normalizer."""
        self.has_cv2 = HAS_CV2
    
    def normalize_image(self, 
                       input_path: str,
                       output_path: str,
                       settings: NormalizationSettings) -> NormalizationResult:
        """
        Normalize a single image according to settings.
        
        Args:
            input_path: Path to input image
            output_path: Path to save output image
            settings: Normalization settings
            
        Returns:
            NormalizationResult object
        """
        try:
            # Load image
            img = Image.open(input_path)
            original_size = img.size
            original_format = img.format
            
            # Convert mode if needed
            if settings.force_rgb and img.mode in ('RGBA', 'LA', 'PA'):
                # Remove alpha channel
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif settings.preserve_alpha and img.mode == 'RGB':
                img = img.convert('RGBA')
            elif not settings.preserve_alpha and img.mode in ('RGBA', 'LA', 'PA'):
                img = img.convert('RGB')
            
            # Process image
            processed = self._process_image(img, settings)
            
            # Check what changed
            was_resized = processed.size != original_size
            was_padded = settings.make_square and original_size[0] != original_size[1]
            format_changed = settings.output_format.value != original_format
            
            # Save image
            self._save_image(processed, output_path, settings)
            
            return NormalizationResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                original_size=original_size,
                output_size=processed.size,
                format_changed=format_changed,
                was_resized=was_resized,
                was_padded=was_padded
            )
            
        except Exception as e:
            logger.error(f"Error normalizing {input_path}: {e}")
            return NormalizationResult(
                input_path=input_path,
                output_path=output_path,
                success=False,
                error_message=str(e)
            )
    
    def normalize_batch(self,
                       input_paths: List[str],
                       output_directory: str,
                       settings: NormalizationSettings,
                       progress_callback: Optional[Callable] = None) -> List[NormalizationResult]:
        """
        Normalize multiple images.
        
        Args:
            input_paths: List of input image paths
            output_directory: Directory to save output images
            settings: Normalization settings
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            List of NormalizationResult objects
        """
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        total = len(input_paths)
        
        for i, input_path in enumerate(input_paths):
            try:
                # Generate output path
                output_path = self._generate_output_path(
                    input_path, output_dir, i, total, settings
                )
                
                # Normalize image
                result = self.normalize_image(input_path, str(output_path), settings)
                results.append(result)
                
                if progress_callback:
                    progress_callback(i + 1, total, Path(input_path).name)
                    
            except Exception as e:
                logger.error(f"Error processing {input_path}: {e}")
                results.append(NormalizationResult(
                    input_path=input_path,
                    output_path="",
                    success=False,
                    error_message=str(e)
                ))
                
                if progress_callback:
                    progress_callback(i + 1, total, Path(input_path).name)
        
        return results
    
    def _process_image(self, img: Image.Image, settings: NormalizationSettings) -> Image.Image:
        """Process image according to settings."""
        # Step 1: Center subject if requested
        if settings.center_subject:
            img = self._center_subject(img)
        
        # Step 2: Resize if needed
        if settings.resize_mode != ResizeMode.NONE:
            img = self._resize_image(img, settings)
        
        # Step 3: Make square with padding if needed
        if settings.make_square:
            img = self._make_square(img, settings)
        
        return img
    
    def _center_subject(self, img: Image.Image) -> Image.Image:
        """
        Center the main subject in the image.
        
        Uses edge detection and center of mass calculation.
        """
        try:
            if not self.has_cv2:
                return img
            
            # Convert to numpy array
            if img.mode == 'RGBA':
                # Use alpha channel for subject detection
                alpha = np.array(img.split()[-1])
                mask = (alpha > 128).astype(np.uint8) * 255
            else:
                # Use edge detection
                gray = np.array(img.convert('L'))
                edges = cv2.Canny(gray, 50, 150)
                mask = edges
            
            # Find center of mass
            moments = cv2.moments(mask)
            if moments['m00'] != 0:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])
                
                # Calculate shift needed to center
                img_cx = img.width // 2
                img_cy = img.height // 2
                shift_x = img_cx - cx
                shift_y = img_cy - cy
                
                # Only shift if offset is significant (>5% of image size)
                if abs(shift_x) > img.width * 0.05 or abs(shift_y) > img.height * 0.05:
                    # Create new image with shifted content
                    if img.mode == 'RGBA':
                        new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
                    else:
                        new_img = Image.new(img.mode, img.size, (255, 255, 255))
                    
                    # Paste with offset
                    paste_x = max(0, shift_x)
                    paste_y = max(0, shift_y)
                    crop_x = max(0, -shift_x)
                    crop_y = max(0, -shift_y)
                    
                    crop_region = (
                        crop_x,
                        crop_y,
                        min(img.width, img.width - shift_x),
                        min(img.height, img.height - shift_y)
                    )
                    
                    cropped = img.crop(crop_region)
                    new_img.paste(cropped, (paste_x, paste_y))
                    
                    return new_img
            
            return img
            
        except Exception as e:
            logger.debug(f"Error centering subject: {e}")
            return img
    
    def _resize_image(self, img: Image.Image, settings: NormalizationSettings) -> Image.Image:
        """Resize image according to mode."""
        target_w = settings.target_width
        target_h = settings.target_height
        
        if settings.resize_mode == ResizeMode.STRETCH:
            # Simply stretch to target size
            return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        elif settings.resize_mode == ResizeMode.FIT:
            # Fit inside target size (preserve aspect ratio)
            img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
            return img
        
        elif settings.resize_mode == ResizeMode.FILL:
            # Fill target size (crop if needed to preserve aspect ratio)
            img_ratio = img.width / img.height
            target_ratio = target_w / target_h
            
            if img_ratio > target_ratio:
                # Image is wider, fit to height and crop width
                new_height = target_h
                new_width = int(new_height * img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Crop to target width (center crop)
                left = (new_width - target_w) // 2
                img = img.crop((left, 0, left + target_w, target_h))
            else:
                # Image is taller, fit to width and crop height
                new_width = target_w
                new_height = int(new_width / img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Crop to target height (center crop)
                top = (new_height - target_h) // 2
                img = img.crop((0, top, target_w, top + target_h))
            
            return img
        
        return img
    
    def _make_square(self, img: Image.Image, settings: NormalizationSettings) -> Image.Image:
        """Make image square using padding."""
        if img.width == img.height:
            return img
        
        # Determine target size (use max dimension)
        size = max(img.width, img.height)
        if settings.target_width > 0:
            size = max(settings.target_width, settings.target_height)
        
        # Create new image with padding
        if settings.padding_mode == PaddingMode.TRANSPARENT:
            new_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        elif settings.padding_mode == PaddingMode.BLACK:
            mode = 'RGBA' if img.mode == 'RGBA' else 'RGB'
            new_img = Image.new(mode, (size, size), (0, 0, 0))
        elif settings.padding_mode == PaddingMode.WHITE:
            mode = 'RGBA' if img.mode == 'RGBA' else 'RGB'
            new_img = Image.new(mode, (size, size), (255, 255, 255))
        elif settings.padding_mode == PaddingMode.BLUR:
            # Create blurred background
            new_img = self._create_blur_background(img, size)
        elif settings.padding_mode == PaddingMode.EDGE_EXTEND:
            # Extend edges
            new_img = self._create_edge_extend_background(img, size)
        else:
            new_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        
        # Center paste
        x = (size - img.width) // 2
        y = (size - img.height) // 2
        
        if img.mode == 'RGBA' and new_img.mode == 'RGBA':
            new_img.paste(img, (x, y), img)
        else:
            new_img.paste(img, (x, y))
        
        return new_img
    
    def _create_blur_background(self, img: Image.Image, size: int) -> Image.Image:
        """Create blurred background for padding."""
        # Resize image to fill square
        bg = img.copy()
        bg = ImageOps.fit(bg, (size, size), Image.Resampling.LANCZOS)
        
        # Apply heavy blur
        from PIL import ImageFilter
        bg = bg.filter(ImageFilter.GaussianBlur(radius=20))
        
        # Reduce opacity
        if bg.mode == 'RGBA':
            alpha = bg.split()[-1]
            alpha = alpha.point(lambda p: int(p * 0.3))
            bg.putalpha(alpha)
        
        return bg
    
    def _create_edge_extend_background(self, img: Image.Image, size: int) -> Image.Image:
        """Create background by extending edges."""
        if img.mode == 'RGBA':
            new_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        else:
            new_img = Image.new(img.mode, (size, size), (255, 255, 255))
        
        # Extend edges by stretching border pixels
        x = (size - img.width) // 2
        y = (size - img.height) // 2
        
        # Top border
        if y > 0:
            top_strip = img.crop((0, 0, img.width, 1))
            top_strip = top_strip.resize((img.width, y), Image.Resampling.NEAREST)
            new_img.paste(top_strip, (x, 0))
        
        # Bottom border
        if y > 0:
            bottom_strip = img.crop((0, img.height - 1, img.width, img.height))
            bottom_strip = bottom_strip.resize((img.width, y), Image.Resampling.NEAREST)
            new_img.paste(bottom_strip, (x, y + img.height))
        
        # Left border
        if x > 0:
            left_strip = img.crop((0, 0, 1, img.height))
            left_strip = left_strip.resize((x, img.height), Image.Resampling.NEAREST)
            new_img.paste(left_strip, (0, y))
        
        # Right border
        if x > 0:
            right_strip = img.crop((img.width - 1, 0, img.width, img.height))
            right_strip = right_strip.resize((x, img.height), Image.Resampling.NEAREST)
            new_img.paste(right_strip, (x + img.width, y))
        
        # Paste original image on top
        if img.mode == 'RGBA':
            new_img.paste(img, (x, y), img)
        else:
            new_img.paste(img, (x, y))
        
        return new_img
    
    def _save_image(self, img: Image.Image, output_path: str, settings: NormalizationSettings):
        """Save image with appropriate format and quality settings."""
        output_format = settings.output_format.value
        
        # Ensure proper mode for format
        if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'PA'):
            # JPEG doesn't support transparency
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        
        # Prepare save kwargs
        save_kwargs = {}
        
        # Strip metadata if requested
        if settings.strip_metadata:
            # Create clean copy without metadata
            # Don't pass exif or info to save
            logger.debug(f"Stripping metadata from {Path(output_path).name}")
        else:
            # Preserve existing metadata if available
            if hasattr(img, 'info') and img.info:
                exif_data = img.info.get('exif')
                if exif_data:  # Only add if EXIF data actually exists
                    save_kwargs['exif'] = exif_data
        
        # Save with format-specific options
        if output_format == 'JPEG':
            img.save(output_path, format='JPEG', quality=settings.jpeg_quality, optimize=True, **save_kwargs)
        elif output_format == 'WEBP':
            img.save(output_path, format='WEBP', quality=settings.webp_quality, method=6, **save_kwargs)
        elif output_format == 'PNG':
            img.save(output_path, format='PNG', optimize=True, **save_kwargs)
        elif output_format == 'TIFF':
            img.save(output_path, format='TIFF', compression='tiff_lzw', **save_kwargs)
        else:
            img.save(output_path, **save_kwargs)
    
    def _generate_output_path(self,
                            input_path: str,
                            output_dir: Path,
                            index: int,
                            total: int,
                            settings: NormalizationSettings) -> Path:
        """Generate output path according to naming pattern."""
        input_path = Path(input_path)
        
        # Get extension for output format
        ext_map = {
            OutputFormat.PNG: '.png',
            OutputFormat.JPEG: '.jpg',
            OutputFormat.WEBP: '.webp',
            OutputFormat.TIFF: '.tiff'
        }
        ext = ext_map.get(settings.output_format, '.png')
        
        # Generate name according to pattern
        if settings.naming_pattern == NamingPattern.ORIGINAL:
            name = input_path.stem + ext
        
        elif settings.naming_pattern == NamingPattern.SEQUENTIAL:
            # Determine number of digits needed
            digits = len(str(total))
            name = f"{settings.naming_prefix}_{str(index + 1).zfill(digits)}{ext}"
        
        elif settings.naming_pattern == NamingPattern.TIMESTAMP:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"{settings.naming_prefix}_{timestamp}_{index + 1}{ext}"
        
        elif settings.naming_pattern == NamingPattern.DESCRIPTIVE:
            # Get image size from settings
            w = settings.target_width
            h = settings.target_height
            digits = len(str(total))
            name = f"{settings.naming_prefix}_{w}x{h}_{str(index + 1).zfill(digits)}{ext}"
        
        else:
            name = input_path.stem + ext
        
        # Ensure unique filename
        output_path = output_dir / name
        counter = 1
        while output_path.exists():
            stem = output_path.stem
            output_path = output_dir / f"{stem}_{counter}{ext}"
            counter += 1
        
        return output_path
    
    def preview_settings(self, 
                        sample_image_path: str,
                        settings: NormalizationSettings) -> Image.Image:
        """
        Generate preview of how settings will affect an image.
        
        Args:
            sample_image_path: Path to sample image
            settings: Normalization settings to preview
            
        Returns:
            Processed PIL Image
        """
        img = Image.open(sample_image_path)
        return self._process_image(img, settings)
