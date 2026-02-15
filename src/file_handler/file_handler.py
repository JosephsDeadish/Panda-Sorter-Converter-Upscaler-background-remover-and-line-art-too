"""
File Handler Module
Handles file operations, conversions, and integrity checks
Extended format support for SVG, JPEG, WEBP, and more
"""

import shutil
import hashlib
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import send2trash

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("PIL/Pillow not available. Image operations disabled.")

# Check for SVG support (dual mode)
try:
    import cairosvg
    HAS_SVG_CAIRO = True
except (ImportError, OSError):
    HAS_SVG_CAIRO = False
    logger.debug("cairosvg not available. Cairo SVG conversion disabled.")

# Check for native Rust vector tracing and/or Python fallback
try:
    from ..native_ops import bitmap_to_svg as native_bitmap_to_svg, NATIVE_AVAILABLE
    HAS_SVG_NATIVE = NATIVE_AVAILABLE
    # bitmap_to_svg works even without Rust via OpenCV fallback
    HAS_BITMAP_TO_SVG = True
except ImportError:
    HAS_SVG_NATIVE = False
    HAS_BITMAP_TO_SVG = False
    logger.debug("Native vector tracing not available.")

# Overall SVG support (either native, bitmap_to_svg fallback, or cairo)
HAS_SVG = HAS_SVG_CAIRO or HAS_BITMAP_TO_SVG

try:
    from io import BytesIO
    HAS_BYTESIO = True
except ImportError:
    HAS_BYTESIO = False

# Import archive handler
try:
    from ..utils.archive_handler import ArchiveHandler
    HAS_ARCHIVE_SUPPORT = True
except ImportError:
    HAS_ARCHIVE_SUPPORT = False
    logger.debug("Archive handler not available.")


class FileHandler:
    """Handles file operations for texture sorting"""
    
    # Extended format support for PS2, HD, and 4K textures
    SUPPORTED_FORMATS = {
        '.dds', '.png', '.jpg', '.jpeg', '.jpe', '.jfif',  # Common formats
        '.tga', '.bmp', '.tif', '.tiff',  # Standard formats
        '.webp', '.gif', '.pcx',  # Additional formats
        '.svg', '.svgz'  # Vector formats (require special handling)
    }
    
    # Raster formats that can be directly loaded with PIL
    RASTER_FORMATS = {
        '.dds', '.png', '.jpg', '.jpeg', '.jpe', '.jfif',
        '.tga', '.bmp', '.tif', '.tiff', '.webp', '.gif', '.pcx'
    }
    
    # Vector formats that need conversion
    VECTOR_FORMATS = {'.svg', '.svgz'}
    
    # Format name mapping for PIL
    FORMAT_MAP = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'jpe': 'JPEG',
        'jfif': 'JPEG',
        'tif': 'TIFF',
        'tiff': 'TIFF'
    }
    
    # Formats that don't support transparency
    NO_ALPHA_FORMATS = {'jpeg', 'jpg', 'jpe', 'jfif', 'bmp'}
    
    def __init__(self, create_backup=True):
        self.create_backup = create_backup
        self.operations_log = []
        
        # Initialize archive handler if available
        self.archive_handler = None
        if HAS_ARCHIVE_SUPPORT:
            self.archive_handler = ArchiveHandler()
            logger.debug("Archive handler initialized")
    
    def convert_dds_to_png(self, dds_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Convert DDS file to PNG
        
        Args:
            dds_path: Path to DDS file
            output_path: Optional output path, defaults to same location with .png extension
        
        Returns:
            Path to converted PNG file or None if conversion failed
        """
        if not HAS_PIL:
            print("PIL/Pillow not available. Cannot convert images.")
            return None
        
        try:
            # Set output path
            if output_path is None:
                output_path = dds_path.with_suffix('.png')
            
            if not dds_path.exists():
                logger.error(f"Source file not found: {dds_path}")
                return None
            
            # Open and convert
            with Image.open(dds_path) as img:
                img.save(output_path, 'PNG')
            
            self.operations_log.append(f"Converted {dds_path} to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting {dds_path} to PNG: {e}")
            return None
    
    def convert_png_to_dds(self, png_path: Path, output_path: Optional[Path] = None, 
                          format='DXT5') -> Optional[Path]:
        """
        Convert PNG file to DDS
        
        Args:
            png_path: Path to PNG file
            output_path: Optional output path, defaults to same location with .dds extension
            format: DDS compression format (DXT1, DXT5, etc.)
        
        Returns:
            Path to converted DDS file or None if conversion failed
        """
        if not HAS_PIL:
            print("PIL/Pillow not available. Cannot convert images.")
            return None
        
        try:
            # Set output path
            if output_path is None:
                output_path = png_path.with_suffix('.dds')
            
            if not png_path.exists():
                logger.error(f"Source file not found: {png_path}")
                return None
            
            # Open and convert
            with Image.open(png_path) as img:
                # Note: Basic PIL/Pillow has limited DDS write support
                # For full DDS support, would need additional libraries
                img.save(output_path, 'DDS')
            
            self.operations_log.append(f"Converted {png_path} to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting {png_path} to DDS: {e}")
            return None
    
    def convert_svg_to_png(self, svg_path: Path, output_path: Optional[Path] = None, 
                          width: Optional[int] = None, height: Optional[int] = None) -> Optional[Path]:
        """
        Convert SVG file to PNG.
        
        Args:
            svg_path: Path to SVG file
            output_path: Optional output path, defaults to same location with .png extension
            width: Optional target width (maintains aspect ratio if height not given)
            height: Optional target height (maintains aspect ratio if width not given)
        
        Returns:
            Path to converted PNG file or None if conversion failed
        """
        if not HAS_SVG_CAIRO:
            logger.warning("cairosvg not available. Cannot convert SVG files.")
            return None
        
        if not HAS_PIL or not HAS_BYTESIO:
            logger.warning("PIL or BytesIO not available. Cannot convert SVG files.")
            return None
        
        try:
            # Set output path
            if output_path is None:
                output_path = svg_path.with_suffix('.png')
            
            if not svg_path.exists():
                logger.error(f"Source file not found: {svg_path}")
                return None
            
            # Convert SVG to PNG bytes
            png_bytes = cairosvg.svg2png(
                url=str(svg_path),
                output_width=width,
                output_height=height
            )
            
            # Load PNG from bytes and save
            with Image.open(BytesIO(png_bytes)) as img:
                img.save(output_path, 'PNG')
            
            self.operations_log.append(f"Converted {svg_path} to {output_path}")
            logger.info(f"Successfully converted SVG: {svg_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting {svg_path} to PNG: {e}")
            return None
    
    def convert_raster_to_svg_native(
        self, 
        image_path: Path, 
        output_path: Optional[Path] = None,
        threshold: int = 25,
        mode: str = "color"
    ) -> Optional[Path]:
        """
        Convert raster image to SVG using native Rust vector tracing (offline mode).
        
        This method uses the native Rust vtracer library for bitmap-to-vector
        conversion. It works completely offline without external dependencies.
        
        Args:
            image_path: Path to raster image file (PNG, JPEG, etc.)
            output_path: Optional output path, defaults to same location with .svg extension
            threshold: Color difference threshold (0-255), lower = more detail
            mode: Tracing mode ("color", "binary", or "spline")
        
        Returns:
            Path to converted SVG file or None if conversion failed
        """
        if not HAS_BITMAP_TO_SVG:
            logger.warning("Vector tracing not available. Install OpenCV or build the Rust extension.")
            return None
        
        if not HAS_PIL:
            logger.warning("PIL not available. Cannot load images.")
            return None
        
        try:
            if output_path is None:
                output_path = image_path.with_suffix('.svg')
            
            if not image_path.exists():
                logger.error(f"Source file not found: {image_path}")
                return None
            
            # Load image as RGB numpy array
            import numpy as np
            img = Image.open(image_path).convert('RGB')
            img_array = np.array(img)
            
            # Convert to SVG using native tracing (or OpenCV fallback)
            svg_content = native_bitmap_to_svg(img_array, threshold=threshold, mode=mode)
            
            if svg_content is None:
                logger.error(f"Vector tracing failed for {image_path}")
                return None
            
            # Save SVG to file
            output_path.write_text(svg_content, encoding='utf-8')
            
            method = "native" if HAS_SVG_NATIVE else "opencv-fallback"
            self.operations_log.append(f"Converted {image_path} to {output_path} ({method})")
            logger.info(f"Successfully converted to SVG ({method}): {image_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting {image_path} to SVG (native): {e}")
            return None
    
    def convert_raster_to_svg_cairo(
        self,
        image_path: Path,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Convert raster image to SVG using cairosvg (online mode).
        
        This method uses cairosvg for conversion, which provides better quality
        for complex images but requires external system dependencies.
        
        Note: This is a placeholder - cairosvg primarily converts SVG to raster,
        not raster to SVG. For actual raster-to-vector, use the native method.
        
        Args:
            image_path: Path to raster image file
            output_path: Optional output path
        
        Returns:
            Path to converted SVG file or None if not supported
        """
        logger.warning(
            "cairosvg converts SVG to raster, not raster to SVG. "
            "Use convert_raster_to_svg_native() for raster-to-vector conversion."
        )
        return None
    
    def convert_raster_to_svg(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        threshold: int = 25,
        mode: str = "color"
    ) -> Optional[Path]:
        """
        Convert raster image to SVG using automatic mode selection.
        
        This method automatically tries the best available conversion method:
        1. Native Rust tracing (offline, fast, good quality)
        2. Falls back to error if native unavailable
        
        Args:
            image_path: Path to raster image file
            output_path: Optional output path, defaults to same location with .svg extension
            threshold: Color difference threshold (0-255), lower = more detail
            mode: Tracing mode ("color", "binary", or "spline")
        
        Returns:
            Path to converted SVG file or None if conversion failed
        """
        # Try bitmap_to_svg (native Rust or OpenCV fallback)
        if HAS_BITMAP_TO_SVG:
            result = self.convert_raster_to_svg_native(
                image_path, output_path, threshold, mode
            )
            if result:
                return result
            logger.warning("Vector tracing failed")
        else:
            logger.warning(
                "No raster-to-SVG conversion method available. "
                "Install OpenCV (pip install opencv-python) or build the Rust extension."
            )
        
        return None
    
    def load_image(self, image_path: Path) -> Optional[Image.Image]:
        """
        Load an image file, handling special formats like SVG.
        
        Args:
            image_path: Path to image file
            
        Returns:
            PIL Image object or None if loading failed
        """
        if not HAS_PIL:
            logger.warning("PIL not available. Cannot load images.")
            return None
        
        try:
            suffix = image_path.suffix.lower()
            
            if not image_path.exists():
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Handle SVG files
            if suffix in self.VECTOR_FORMATS:
                if not HAS_SVG:
                    logger.warning(f"Cannot load SVG file {image_path}: no SVG support available")
                    return None
                
                # Try cairosvg first if available (better quality for existing SVG files)
                if HAS_SVG_CAIRO:
                    try:
                        import cairosvg
                        png_bytes = cairosvg.svg2png(url=str(image_path))
                        return Image.open(BytesIO(png_bytes))
                    except Exception as e:
                        logger.warning(f"Cairo SVG loading failed: {e}")
                
                logger.error(f"Cannot load SVG file {image_path}: cairosvg required for SVG-to-raster")
                return None
            
            # Handle raster formats
            elif suffix in self.RASTER_FORMATS:
                return Image.open(image_path)
            
            else:
                logger.warning(f"Unsupported image format: {suffix}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def batch_convert(self, file_paths: List[Path], target_format: str, 
                     output_dir: Optional[Path] = None, progress_callback=None) -> List[Path]:
        """
        Batch convert multiple files with extended format support.
        
        Args:
            file_paths: List of files to convert
            target_format: Target format ('png', 'dds', 'jpg', 'webp', etc.)
            output_dir: Optional output directory
            progress_callback: Callback for progress updates
        
        Returns:
            List of successfully converted file paths
        """
        converted = []
        total = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            output_path = None
            if output_dir:
                output_path = output_dir / file_path.with_suffix(f'.{target_format}').name
            
            suffix = file_path.suffix.lower()
            result = None
            
            # DDS to PNG conversion
            if target_format.lower() == 'png' and suffix == '.dds':
                result = self.convert_dds_to_png(file_path, output_path)
            
            # PNG/JPG to DDS conversion
            elif target_format.lower() == 'dds' and suffix in {'.png', '.jpg', '.jpeg'}:
                result = self.convert_png_to_dds(file_path, output_path)
            
            # SVG to PNG conversion
            elif target_format.lower() == 'png' and suffix in self.VECTOR_FORMATS:
                result = self.convert_svg_to_png(file_path, output_path)
            
            # Generic format conversion using PIL
            elif HAS_PIL and suffix in self.SUPPORTED_FORMATS:
                try:
                    img = self.load_image(file_path)
                    if img:
                        if output_path is None:
                            output_path = file_path.with_suffix(f'.{target_format}')
                        
                        # Get proper format name for PIL
                        pil_format = self.FORMAT_MAP.get(target_format.lower(), target_format.upper())
                        
                        # Handle transparency for formats that don't support it
                        if target_format.lower() in self.NO_ALPHA_FORMATS and img.mode in ('RGBA', 'LA'):
                            logger.info(f"Converting {img.mode} to RGB for {target_format} (no transparency support)")
                            # Create white background
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'RGBA':
                                background.paste(img, mask=img.split()[3])  # Use alpha as mask
                            else:
                                background.paste(img, mask=img.split()[1])  # LA mode
                            img = background
                        
                        # Save in target format
                        img.save(output_path, format=pil_format)
                        result = output_path
                        self.operations_log.append(f"Converted {file_path} to {output_path}")
                except Exception as e:
                    logger.error(f"Error converting {file_path}: {e}")
                    result = None
            
            if result:
                converted.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return converted
    
    def check_file_integrity(self, file_path: Path) -> Tuple[bool, str]:
        """
        Check if file is valid and not corrupted
        
        Args:
            file_path: Path to file to check
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file exists
        if not file_path.exists():
            return False, "File does not exist"
        
        # Check file size
        if file_path.stat().st_size == 0:
            return False, "File is empty"
        
        # Try to open as image
        if HAS_PIL and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
            try:
                img = Image.open(file_path)
                img.verify()  # Verify it's a valid image
                return True, "OK"
            except Exception as e:
                return False, f"Image corrupted: {str(e)}"
        
        return True, "OK"
    
    def calculate_file_hash(self, file_path: Path, algorithm='md5') -> str:
        """
        Calculate hash of file for duplicate detection
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha256')
        
        Returns:
            Hex string of file hash
        """
        hash_obj = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        
        # Read file in chunks for memory efficiency
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def find_duplicates(self, file_paths: List[Path], by_hash=True) -> dict:
        """
        Find duplicate files
        
        Args:
            file_paths: List of file paths to check
            by_hash: Use hash comparison (slower but accurate) vs name+size (faster)
        
        Returns:
            Dictionary mapping original files to lists of duplicates
        """
        if by_hash:
            hash_map = {}
            duplicates = {}
            
            for file_path in file_paths:
                file_hash = self.calculate_file_hash(file_path)
                
                if file_hash in hash_map:
                    # Found duplicate
                    original = hash_map[file_hash]
                    if original not in duplicates:
                        duplicates[original] = []
                    duplicates[original].append(file_path)
                else:
                    hash_map[file_hash] = file_path
            
            return duplicates
        else:
            # Compare by name and size (faster)
            size_name_map = {}
            duplicates = {}
            
            for file_path in file_paths:
                key = (file_path.name, file_path.stat().st_size)
                
                if key in size_name_map:
                    original = size_name_map[key]
                    if original not in duplicates:
                        duplicates[original] = []
                    duplicates[original].append(file_path)
                else:
                    size_name_map[key] = file_path
            
            return duplicates
    
    def safe_copy(self, source: Path, destination: Path, overwrite=False) -> bool:
        """
        Safely copy file with backup
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if destination exists
            if destination.exists() and not overwrite:
                print(f"Destination {destination} already exists. Skipping.")
                return False
            
            # Create backup if enabled
            if self.create_backup and destination.exists():
                backup_path = destination.with_suffix(destination.suffix + '.backup')
                shutil.copy2(destination, backup_path)
            
            # Copy file
            shutil.copy2(source, destination)
            self.operations_log.append(f"Copied {source} to {destination}")
            return True
            
        except Exception as e:
            print(f"Error copying {source} to {destination}: {e}")
            return False
    
    def safe_move(self, source: Path, destination: Path, overwrite=False) -> bool:
        """
        Safely move file
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if destination exists
            if destination.exists() and not overwrite:
                print(f"Destination {destination} already exists. Skipping.")
                return False
            
            # Move file
            shutil.move(str(source), str(destination))
            self.operations_log.append(f"Moved {source} to {destination}")
            return True
            
        except Exception as e:
            print(f"Error moving {source} to {destination}: {e}")
            return False
    
    def safe_delete(self, file_path: Path, use_trash=True) -> bool:
        """
        Safely delete file (optionally to trash)
        
        Args:
            file_path: File to delete
            use_trash: Send to trash instead of permanent delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if use_trash:
                send2trash.send2trash(str(file_path))
            else:
                file_path.unlink()
            
            self.operations_log.append(f"Deleted {file_path}")
            return True
            
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
            return False
    
    def get_operations_log(self) -> List[str]:
        """Get log of all operations performed"""
        return self.operations_log.copy()
    
    def clear_operations_log(self):
        """Clear the operations log"""
        self.operations_log.clear()
    
    # ==================== Archive Support Methods ====================
    
    def is_archive(self, file_path: Path) -> bool:
        """
        Check if a file is a supported archive format.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file is a supported archive
        """
        if not self.archive_handler:
            return False
        return self.archive_handler.is_archive(file_path)
    
    def extract_archive(self, archive_path: Path, extract_to: Optional[Path] = None) -> Optional[Path]:
        """
        Extract archive to a directory.
        
        Args:
            archive_path: Path to archive file
            extract_to: Target directory (creates temp dir if None)
            
        Returns:
            Path to extraction directory or None on failure
        """
        if not self.archive_handler:
            logger.error("Archive handler not available")
            return None
        
        return self.archive_handler.extract_archive(archive_path, extract_to)
    
    def create_archive(self, source_path: Path, archive_path: Path) -> bool:
        """
        Create an archive from a directory or files.
        
        Args:
            source_path: Directory or file to archive
            archive_path: Target archive file path
            
        Returns:
            True if successful, False otherwise
        """
        if not self.archive_handler:
            logger.error("Archive handler not available")
            return False
        
        return self.archive_handler.create_archive(source_path, archive_path)
    
    def list_archive_contents(self, archive_path: Path) -> List[str]:
        """
        List all files in an archive.
        
        Args:
            archive_path: Path to archive file
            
        Returns:
            List of file paths inside archive
        """
        if not self.archive_handler:
            logger.error("Archive handler not available")
            return []
        
        return self.archive_handler.list_archive_contents(archive_path)
    
    def cleanup_temp_archives(self):
        """Clean up temporary archive extraction directories."""
        if self.archive_handler:
            self.archive_handler.cleanup_temp_dirs()
    
    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, 'archive_handler') and self.archive_handler:
            self.archive_handler.cleanup_temp_dirs()
