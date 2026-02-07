"""
Image Processing Utilities
Efficient image operations including thumbnails, conversions, and validation
Author: Dead On The Inside / JosephsDeadish
"""

import io
import logging
from pathlib import Path
from typing import Optional, Tuple, Union, BinaryIO
from PIL import Image, ImageOps, ImageFile
import numpy as np
import cv2

# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)


# Supported image formats
SUPPORTED_FORMATS = {
    '.png', '.jpg', '.jpeg', '.bmp', '.tga', '.dds',
    '.tif', '.tiff', '.webp', '.gif', '.pcx'
}

# PS2 optimal dimensions
PS2_MAX_DIMENSION = 1024
PS2_COMMON_SIZES = [16, 32, 64, 128, 256, 512, 1024]


def validate_image(image_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate if file is a valid image.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not image_path.exists():
            return False, "File does not exist"
        
        if not image_path.is_file():
            return False, "Path is not a file"
        
        if image_path.suffix.lower() not in SUPPORTED_FORMATS:
            return False, f"Unsupported format: {image_path.suffix}"
        
        # Try to open and verify
        with Image.open(image_path) as img:
            img.verify()
        
        # Reopen for actual check (verify() closes the file)
        with Image.open(image_path) as img:
            # Check basic properties
            if img.width <= 0 or img.height <= 0:
                return False, "Invalid dimensions"
            
            if img.width > 16384 or img.height > 16384:
                return False, "Dimensions too large"
        
        return True, None
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def get_image_info(image_path: Path) -> Optional[dict]:
    """
    Get basic image information without loading full image.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with image info or None if error
    """
    try:
        with Image.open(image_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'width': img.width,
                'height': img.height,
                'size_bytes': image_path.stat().st_size,
                'has_alpha': img.mode in ('RGBA', 'LA', 'PA', 'P')
            }
    except Exception as e:
        logger.error(f"Failed to get image info for {image_path}: {e}")
        return None


def create_thumbnail(
    image_path: Path,
    size: Tuple[int, int] = (256, 256),
    maintain_aspect: bool = True,
    quality: int = 85
) -> Optional[Image.Image]:
    """
    Create thumbnail from image with efficient memory usage.
    
    Args:
        image_path: Path to source image
        size: Target thumbnail size (width, height)
        maintain_aspect: Maintain aspect ratio
        quality: JPEG quality for compression (1-100)
        
    Returns:
        PIL Image object or None if error
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Create thumbnail
            if maintain_aspect:
                img.thumbnail(size, Image.Resampling.LANCZOS)
            else:
                img = img.resize(size, Image.Resampling.LANCZOS)
            
            return img.copy()
            
    except Exception as e:
        logger.error(f"Failed to create thumbnail for {image_path}: {e}")
        return None


def save_thumbnail(
    image_path: Path,
    output_path: Path,
    size: Tuple[int, int] = (256, 256),
    format: str = 'JPEG',
    quality: int = 85
) -> bool:
    """
    Create and save thumbnail to disk.
    
    Args:
        image_path: Path to source image
        output_path: Path to save thumbnail
        size: Target thumbnail size
        format: Output format (JPEG, PNG, etc.)
        quality: Compression quality
        
    Returns:
        True if successful, False otherwise
    """
    try:
        thumbnail = create_thumbnail(image_path, size, quality=quality)
        if thumbnail:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            thumbnail.save(output_path, format=format, quality=quality, optimize=True)
            logger.debug(f"Thumbnail saved: {output_path}")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Failed to save thumbnail: {e}")
        return False


def convert_image_format(
    source_path: Path,
    target_path: Path,
    target_format: str,
    quality: int = 95,
    optimize: bool = True
) -> bool:
    """
    Convert image to different format.
    
    Args:
        source_path: Source image path
        target_path: Target image path
        target_format: Target format (PNG, JPEG, BMP, etc.)
        quality: Compression quality for lossy formats
        optimize: Enable optimization
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with Image.open(source_path) as img:
            # Handle format-specific conversions
            if target_format.upper() == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                # JPEG doesn't support transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif target_format.upper() == 'PNG' and img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA')
            
            # Create target directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with format-specific options
            save_kwargs = {'format': target_format, 'optimize': optimize}
            
            if target_format.upper() in ('JPEG', 'JPG'):
                save_kwargs['quality'] = quality
                save_kwargs['progressive'] = True
            elif target_format.upper() == 'PNG':
                save_kwargs['compress_level'] = 9 if optimize else 6
            
            img.save(target_path, **save_kwargs)
            logger.info(f"Converted {source_path} to {target_format}: {target_path}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to convert image: {e}")
        return False


def resize_image(
    image_path: Path,
    output_path: Path,
    target_size: Tuple[int, int],
    maintain_aspect: bool = True,
    resample_method: Image.Resampling = Image.Resampling.LANCZOS
) -> bool:
    """
    Resize image to target dimensions.
    
    Args:
        image_path: Source image path
        output_path: Output path
        target_size: Target (width, height)
        maintain_aspect: Maintain aspect ratio
        resample_method: Resampling algorithm
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            if maintain_aspect:
                img.thumbnail(target_size, resample_method)
            else:
                img = img.resize(target_size, resample_method)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path)
            logger.info(f"Resized image saved: {output_path}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to resize image: {e}")
        return False


def normalize_for_ps2(
    image_path: Path,
    output_path: Path,
    max_dimension: int = PS2_MAX_DIMENSION,
    force_power_of_2: bool = True
) -> bool:
    """
    Normalize image for PS2 compatibility.
    
    - Ensures dimensions are power of 2
    - Respects PS2 size limits
    - Maintains quality
    
    Args:
        image_path: Source image path
        output_path: Output path
        max_dimension: Maximum allowed dimension
        force_power_of_2: Force dimensions to power of 2
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Calculate target dimensions
            if force_power_of_2:
                target_width = _nearest_power_of_2(width, max_dimension)
                target_height = _nearest_power_of_2(height, max_dimension)
            else:
                target_width = min(width, max_dimension)
                target_height = min(height, max_dimension)
            
            # Resize if needed
            if (target_width, target_height) != (width, height):
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                logger.info(f"Normalized from {width}x{height} to {target_width}x{target_height}")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path)
            return True
            
    except Exception as e:
        logger.error(f"Failed to normalize image: {e}")
        return False


def extract_alpha_channel(
    image_path: Path,
    output_path: Path,
    as_grayscale: bool = True
) -> bool:
    """
    Extract alpha channel from image.
    
    Args:
        image_path: Source image path
        output_path: Output path for alpha channel
        as_grayscale: Save as grayscale image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            if img.mode not in ('RGBA', 'LA'):
                logger.warning(f"Image has no alpha channel: {image_path}")
                return False
            
            alpha = img.getchannel('A')
            
            if as_grayscale:
                alpha = alpha.convert('L')
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            alpha.save(output_path)
            logger.info(f"Alpha channel extracted: {output_path}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to extract alpha channel: {e}")
        return False


def merge_alpha_channel(
    rgb_path: Path,
    alpha_path: Path,
    output_path: Path
) -> bool:
    """
    Merge RGB image with separate alpha channel.
    
    Args:
        rgb_path: Path to RGB image
        alpha_path: Path to alpha channel image
        output_path: Output path for merged RGBA
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with Image.open(rgb_path) as rgb_img:
            with Image.open(alpha_path) as alpha_img:
                # Ensure RGB mode
                if rgb_img.mode != 'RGB':
                    rgb_img = rgb_img.convert('RGB')
                
                # Ensure alpha is grayscale and same size
                if alpha_img.mode != 'L':
                    alpha_img = alpha_img.convert('L')
                
                if rgb_img.size != alpha_img.size:
                    alpha_img = alpha_img.resize(rgb_img.size, Image.Resampling.LANCZOS)
                
                # Merge channels
                rgba = Image.merge('RGBA', (*rgb_img.split(), alpha_img))
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                rgba.save(output_path)
                logger.info(f"Alpha channel merged: {output_path}")
                return True
                
    except Exception as e:
        logger.error(f"Failed to merge alpha channel: {e}")
        return False


def optimize_image(
    image_path: Path,
    output_path: Optional[Path] = None,
    quality: int = 85,
    reduce_colors: bool = False,
    max_colors: int = 256
) -> bool:
    """
    Optimize image file size while maintaining quality.
    
    Args:
        image_path: Source image path
        output_path: Output path (overwrites source if None)
        quality: Compression quality
        reduce_colors: Reduce color palette
        max_colors: Maximum colors if reducing
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if output_path is None:
            output_path = image_path
        
        with Image.open(image_path) as img:
            # Reduce colors if requested
            if reduce_colors and img.mode in ('RGB', 'RGBA'):
                img = img.convert('P', palette=Image.ADAPTIVE, colors=max_colors)
            
            # Save with optimization
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if img.format == 'PNG' or output_path.suffix.lower() == '.png':
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
            elif img.format in ('JPEG', 'JPG') or output_path.suffix.lower() in ('.jpg', '.jpeg'):
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            else:
                img.save(output_path, optimize=True)
            
            original_size = image_path.stat().st_size
            optimized_size = output_path.stat().st_size
            savings = ((original_size - optimized_size) / original_size) * 100
            
            logger.info(f"Optimized {image_path}: {savings:.1f}% size reduction")
            return True
            
    except Exception as e:
        logger.error(f"Failed to optimize image: {e}")
        return False


def load_image_stream(
    stream: Union[BinaryIO, bytes],
    format: Optional[str] = None
) -> Optional[Image.Image]:
    """
    Load image from memory stream efficiently.
    
    Args:
        stream: Binary stream or bytes
        format: Optional format hint
        
    Returns:
        PIL Image or None if error
    """
    try:
        if isinstance(stream, bytes):
            stream = io.BytesIO(stream)
        
        img = Image.open(stream)
        if format:
            img.format = format
        
        return img
        
    except Exception as e:
        logger.error(f"Failed to load image from stream: {e}")
        return None


def image_to_bytes(
    image: Image.Image,
    format: str = 'PNG',
    quality: int = 95
) -> Optional[bytes]:
    """
    Convert PIL Image to bytes.
    
    Args:
        image: PIL Image object
        format: Output format
        quality: Compression quality
        
    Returns:
        Image as bytes or None if error
    """
    try:
        buffer = io.BytesIO()
        save_kwargs = {'format': format}
        
        if format.upper() in ('JPEG', 'JPG'):
            save_kwargs['quality'] = quality
        
        image.save(buffer, **save_kwargs)
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Failed to convert image to bytes: {e}")
        return None


def compare_images(
    image1_path: Path,
    image2_path: Path,
    method: str = 'mse'
) -> Optional[float]:
    """
    Compare two images and return similarity metric.
    
    Args:
        image1_path: First image path
        image2_path: Second image path
        method: Comparison method ('mse', 'ssim', 'psnr')
        
    Returns:
        Similarity score or None if error
    """
    try:
        img1 = cv2.imread(str(image1_path))
        img2 = cv2.imread(str(image2_path))
        
        if img1 is None or img2 is None:
            logger.error("Failed to load images for comparison")
            return None
        
        # Resize to same dimensions if different
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        if method.lower() == 'mse':
            # Mean Squared Error (lower is better)
            return float(np.mean((img1 - img2) ** 2))
        
        elif method.lower() == 'psnr':
            # Peak Signal-to-Noise Ratio (higher is better)
            mse = np.mean((img1 - img2) ** 2)
            if mse == 0:
                return float('inf')
            max_pixel = 255.0
            return float(20 * np.log10(max_pixel / np.sqrt(mse)))
        
        elif method.lower() == 'ssim':
            # Structural Similarity Index (requires scikit-image)
            try:
                from skimage.metrics import structural_similarity as ssim
                # Convert to grayscale for SSIM
                gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
                return float(ssim(gray1, gray2))
            except ImportError:
                logger.warning("scikit-image not available, using MSE instead")
                return float(np.mean((img1 - img2) ** 2))
        
        else:
            logger.error(f"Unknown comparison method: {method}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to compare images: {e}")
        return None


def batch_process_images(
    input_dir: Path,
    output_dir: Path,
    operation: str,
    **kwargs
) -> dict:
    """
    Batch process images in directory.
    
    Args:
        input_dir: Input directory
        output_dir: Output directory
        operation: Operation to perform ('resize', 'convert', 'optimize', 'normalize')
        **kwargs: Operation-specific arguments
        
    Returns:
        Dictionary with processing results
    """
    results = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        # Get all image files
        image_files = []
        for ext in SUPPORTED_FORMATS:
            image_files.extend(input_dir.glob(f"**/*{ext}"))
        
        results['total'] = len(image_files)
        
        for img_path in image_files:
            try:
                # Create relative output path
                rel_path = img_path.relative_to(input_dir)
                out_path = output_dir / rel_path
                
                # Perform operation
                success = False
                if operation == 'resize':
                    success = resize_image(img_path, out_path, **kwargs)
                elif operation == 'convert':
                    success = convert_image_format(img_path, out_path, **kwargs)
                elif operation == 'optimize':
                    success = optimize_image(img_path, out_path, **kwargs)
                elif operation == 'normalize':
                    success = normalize_for_ps2(img_path, out_path, **kwargs)
                else:
                    logger.error(f"Unknown operation: {operation}")
                    results['errors'].append(f"{img_path}: Unknown operation")
                    continue
                
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"{img_path}: Operation failed")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"{img_path}: {str(e)}")
        
        logger.info(f"Batch processing complete: {results['success']}/{results['total']} successful")
        return results
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        results['errors'].append(str(e))
        return results


def _nearest_power_of_2(value: int, max_value: int) -> int:
    """Find nearest power of 2 within max value."""
    power = 1
    while power < value and power < max_value:
        power *= 2
    
    # Choose between current and previous power based on proximity
    if power > value and power > 1:
        prev_power = power // 2
        if (value - prev_power) < (power - value):
            return prev_power
    
    return min(power, max_value)


def get_supported_formats() -> set:
    """Get set of supported image formats."""
    return SUPPORTED_FORMATS.copy()


def is_supported_format(file_path: Path) -> bool:
    """Check if file format is supported."""
    return file_path.suffix.lower() in SUPPORTED_FORMATS
