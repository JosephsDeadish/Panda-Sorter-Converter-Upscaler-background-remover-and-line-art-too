"""
Image Metadata Handler
Handles EXIF and other metadata preservation for image processing operations.
Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations


import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, OSError, RuntimeError):
    HAS_PIL = False


logger = logging.getLogger(__name__)


class MetadataHandler:
    """
    Handler for image metadata operations.
    
    Supports:
    - EXIF data extraction and copying
    - Metadata validation
    - Format-specific warnings
    """
    
    # Formats that commonly support EXIF data
    EXIF_SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.tiff', '.tif'}
    
    # Formats that may have limited EXIF support
    LIMITED_EXIF_FORMATS = {'.png', '.webp'}
    
    def __init__(self):
        """Initialize metadata handler."""
        self.last_warning = None
    
    def extract_metadata(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing metadata, or None if no metadata found
        """
        try:
            with Image.open(image_path) as img:
                metadata = {}
                
                # Extract EXIF data
                exif = img.getexif()
                if exif:
                    metadata['exif'] = exif
                    logger.debug(f"Extracted EXIF data from {image_path.name}: {len(exif)} tags")
                
                # Extract info dict (PNG metadata, etc.)
                if img.info:
                    metadata['info'] = img.info.copy()
                    logger.debug(f"Extracted info data from {image_path.name}: {len(img.info)} keys")
                
                # Store image format
                metadata['format'] = img.format
                
                return metadata if metadata else None
                
        except Exception as e:
            logger.warning(f"Failed to extract metadata from {image_path}: {e}")
            return None
    
    def apply_metadata(self, image: Image.Image, metadata: Optional[Dict[str, Any]], 
                      target_format: str) -> Tuple[Image.Image, bool]:
        """
        Apply metadata to an image.
        
        Args:
            image: PIL Image object
            metadata: Metadata dictionary from extract_metadata()
            target_format: Target format (e.g., 'JPEG', 'PNG')
            
        Returns:
            Tuple of (image, success_flag)
        """
        if not metadata:
            return image, False
        
        try:
            # Apply EXIF data if present and format supports it
            if 'exif' in metadata:
                target_ext = self._format_to_extension(target_format)
                if target_ext in self.EXIF_SUPPORTED_FORMATS:
                    # EXIF is directly supported
                    logger.debug(f"EXIF will be preserved for {target_format}")
                elif target_ext in self.LIMITED_EXIF_FORMATS:
                    # Limited support - may work but warn user
                    logger.debug(f"EXIF support limited for {target_format}")
                else:
                    # Format doesn't support EXIF
                    logger.debug(f"EXIF not supported for {target_format}")
                    return image, False
            
            return image, True
            
        except Exception as e:
            logger.error(f"Failed to apply metadata: {e}")
            return image, False
    
    def save_with_metadata(self, image: Image.Image, output_path: Path,
                          metadata: Optional[Dict[str, Any]], **save_kwargs) -> bool:
        """
        Save an image with metadata preservation.
        
        Args:
            image: PIL Image object to save
            output_path: Output file path
            metadata: Metadata to preserve
            **save_kwargs: Additional arguments for Image.save()
            
        Returns:
            True if metadata was successfully preserved, False otherwise
        """
        try:
            # Prepare save kwargs with metadata
            final_kwargs = save_kwargs.copy()
            metadata_preserved = False
            
            if metadata:
                # Add EXIF data if present
                if 'exif' in metadata:
                    final_kwargs['exif'] = metadata['exif']
                    metadata_preserved = True
                    logger.debug(f"Preserving EXIF data in {output_path.name}")
                
                # Add info dict for formats that support it (like PNG)
                if 'info' in metadata and output_path.suffix.lower() in {'.png', '.webp'}:
                    # PNG metadata
                    from PIL import PngImagePlugin
                    pnginfo = PngImagePlugin.PngInfo()
                    for key, value in metadata['info'].items():
                        if isinstance(key, str) and isinstance(value, (str, bytes)):
                            try:
                                pnginfo.add_text(key, value if isinstance(value, str) else value.decode('utf-8', errors='ignore'))
                            except Exception:
                                pass
                    final_kwargs['pnginfo'] = pnginfo
                    metadata_preserved = True
            
            # Save the image
            image.save(output_path, **final_kwargs)
            
            return metadata_preserved
            
        except Exception as e:
            logger.error(f"Failed to save image with metadata to {output_path}: {e}")
            # Try to save without metadata as fallback
            try:
                image.save(output_path, **save_kwargs)
                logger.warning(f"Saved {output_path.name} without metadata")
                return False
            except Exception as e2:
                logger.error(f"Failed to save image even without metadata: {e2}")
                raise
    
    def check_format_support(self, file_extension: str) -> Tuple[bool, str]:
        """
        Check if a format supports EXIF metadata.
        
        Args:
            file_extension: File extension (e.g., '.jpg', '.png')
            
        Returns:
            Tuple of (supports_exif, warning_message)
        """
        ext = file_extension.lower()
        
        if ext in self.EXIF_SUPPORTED_FORMATS:
            return True, ""
        elif ext in self.LIMITED_EXIF_FORMATS:
            warning = f"Metadata support for {ext.upper()} is limited. Some EXIF data may not be visible in all viewers."
            return True, warning
        else:
            warning = f"Format {ext.upper()} does not support EXIF metadata. Metadata will not be preserved."
            return False, warning
    
    def _format_to_extension(self, format_str: str) -> str:
        """
        Convert PIL format string to file extension.
        
        Args:
            format_str: PIL format string (e.g., 'JPEG', 'PNG')
            
        Returns:
            File extension (e.g., '.jpg', '.png')
        """
        format_map = {
            'JPEG': '.jpg',
            'PNG': '.png',
            'TIFF': '.tiff',
            'BMP': '.bmp',
            'WEBP': '.webp',
            'TGA': '.tga',
            'DDS': '.dds'
        }
        return format_map.get(format_str.upper(), f'.{format_str.lower()}')
    
    def copy_metadata(self, source_path: Path, target_path: Path) -> bool:
        """
        Copy metadata from source image to target image (post-save).
        
        This is a convenience method for copying metadata after an image
        has already been saved.
        
        Args:
            source_path: Source image path
            target_path: Target image path
            
        Returns:
            True if metadata was copied successfully
        """
        try:
            metadata = self.extract_metadata(source_path)
            if not metadata:
                logger.debug(f"No metadata to copy from {source_path.name}")
                return False
            
            # Re-open and re-save with metadata
            with Image.open(target_path) as img:
                # Get current save format
                save_format = img.format or target_path.suffix[1:].upper()
                
                # Prepare save kwargs based on format
                save_kwargs = {}
                if save_format == 'JPEG':
                    save_kwargs['quality'] = 95
                    save_kwargs['optimize'] = True
                elif save_format == 'PNG':
                    save_kwargs['optimize'] = True
                elif save_format == 'WEBP':
                    save_kwargs['quality'] = 95
                
                # Save with metadata
                return self.save_with_metadata(img, target_path, metadata, **save_kwargs)
                
        except Exception as e:
            logger.error(f"Failed to copy metadata from {source_path} to {target_path}: {e}")
            return False


# Global instance for easy access
metadata_handler = MetadataHandler()
