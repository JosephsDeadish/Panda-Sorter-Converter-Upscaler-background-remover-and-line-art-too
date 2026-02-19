"""
Batch Rename Tool
-----------------
Rename files in batch using various patterns and metadata injection.

Features:
- Date-based naming (creation, modification, EXIF)
- Resolution-based naming (WIDTHxHEIGHT)
- Custom template naming with variables
- Sequential numbering
- Metadata injection (copyright, author, description)
- Preview before rename
- Undo/rollback support
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Callable
from PIL import Image
import piexif

logger = logging.getLogger(__name__)


class RenamePattern:
    """Available rename patterns"""
    DATE_CREATED = "date_created"
    DATE_MODIFIED = "date_modified"
    DATE_EXIF = "date_exif"
    RESOLUTION = "resolution"
    SEQUENTIAL = "sequential"
    CUSTOM = "custom"
    PRIVACY = "privacy"  # Random anonymization


class BatchRenamer:
    """
    Batch rename files with various naming patterns and metadata injection.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rename_history = []  # For undo functionality
        
    def generate_preview(
        self,
        files: List[str],
        pattern: str,
        template: str = None,
        start_index: int = 1,
        add_metadata: bool = False
    ) -> List[Tuple[str, str]]:
        """
        Generate preview of renamed files without actually renaming.
        
        Args:
            files: List of file paths to rename
            pattern: Rename pattern (from RenamePattern)
            template: Custom template string (for CUSTOM pattern)
            start_index: Starting index for sequential numbering
            add_metadata: Whether metadata will be added
            
        Returns:
            List of (original_path, new_name) tuples
        """
        previews = []
        
        for idx, filepath in enumerate(files):
            try:
                new_name = self._generate_name(
                    filepath, pattern, template, start_index + idx
                )
                previews.append((filepath, new_name))
            except Exception as e:
                self.logger.error(f"Error generating preview for {filepath}: {e}")
                previews.append((filepath, f"ERROR: {str(e)}"))
                
        return previews
    
    def _generate_name(
        self,
        filepath: str,
        pattern: str,
        template: str = None,
        index: int = 1
    ) -> str:
        """Generate new filename based on pattern"""
        path = Path(filepath)
        ext = path.suffix
        
        if pattern == RenamePattern.DATE_CREATED:
            timestamp = os.path.getctime(filepath)
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
            return f"{date_str}{ext}"
            
        elif pattern == RenamePattern.DATE_MODIFIED:
            timestamp = os.path.getmtime(filepath)
            date_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
            return f"{date_str}{ext}"
            
        elif pattern == RenamePattern.DATE_EXIF:
            try:
                img = Image.open(filepath)
                exif_dict = piexif.load(img.info.get('exif', b''))
                if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                    date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode()
                    # Convert "YYYY:MM:DD HH:MM:SS" to "YYYYMMDD_HHMMSS"
                    date_str = date_str.replace(':', '').replace(' ', '_')
                    return f"{date_str}{ext}"
                else:
                    # Fallback to modified date
                    return self._generate_name(filepath, RenamePattern.DATE_MODIFIED, template, index)
            except Exception as e:
                self.logger.warning(f"Could not read EXIF for {filepath}: {e}")
                return self._generate_name(filepath, RenamePattern.DATE_MODIFIED, template, index)
                
        elif pattern == RenamePattern.RESOLUTION:
            try:
                img = Image.open(filepath)
                width, height = img.size
                return f"{width}x{height}_{index:04d}{ext}"
            except Exception as e:
                self.logger.error(f"Could not read image dimensions: {e}")
                return f"unknown_res_{index:04d}{ext}"
                
        elif pattern == RenamePattern.SEQUENTIAL:
            return f"image_{index:04d}{ext}"
            
        elif pattern == RenamePattern.CUSTOM:
            if not template:
                template = "{name}_{index}"
            return self._apply_template(filepath, template, index) + ext
            
        elif pattern == RenamePattern.PRIVACY:
            # Generate random anonymized name
            import random
            import string
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
            return f"anon_{random_str}{ext}"
            
        else:
            # Default: keep original name with index
            return f"{path.stem}_{index:04d}{ext}"
    
    def _apply_template(self, filepath: str, template: str, index: int) -> str:
        """
        Apply custom template with variable substitution.
        
        Supported variables:
        - {name}: Original filename (without extension)
        - {index}: Sequential index
        - {date}: Current date (YYYYMMDD)
        - {time}: Current time (HHMMSS)
        - {width}: Image width
        - {height}: Image height
        - {res}: Resolution (WIDTHxHEIGHT)
        """
        path = Path(filepath)
        result = template
        
        # Basic variables
        result = result.replace('{name}', path.stem)
        result = result.replace('{index}', f"{index:04d}")
        result = result.replace('{date}', datetime.now().strftime("%Y%m%d"))
        result = result.replace('{time}', datetime.now().strftime("%H%M%S"))
        
        # Image dimension variables
        try:
            img = Image.open(filepath)
            width, height = img.size
            result = result.replace('{width}', str(width))
            result = result.replace('{height}', str(height))
            result = result.replace('{res}', f"{width}x{height}")
        except Exception as e:
            self.logger.warning(f"Could not read image dimensions for template: {e}")
            result = result.replace('{width}', 'unknown')
            result = result.replace('{height}', 'unknown')
            result = result.replace('{res}', 'unknown')
        
        return result
    
    def batch_rename(
        self,
        files: List[str],
        pattern: str,
        template: str = None,
        start_index: int = 1,
        metadata: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Perform batch rename operation.
        
        Args:
            files: List of file paths to rename
            pattern: Rename pattern
            template: Custom template (for CUSTOM pattern)
            start_index: Starting index for sequential numbering
            metadata: Optional metadata to inject (copyright, author, description)
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            Tuple of (success_list, error_list)
        """
        successes = []
        errors = []
        rename_ops = []  # For undo
        
        for idx, filepath in enumerate(files):
            try:
                if progress_callback:
                    progress_callback(idx + 1, len(files), filepath)
                
                # Generate new name
                new_name = self._generate_name(
                    filepath, pattern, template, start_index + idx
                )
                
                # Build new path
                directory = os.path.dirname(filepath)
                new_path = os.path.join(directory, new_name)
                
                # Check for collision
                if os.path.exists(new_path) and new_path != filepath:
                    # Add suffix to avoid collision
                    base, ext = os.path.splitext(new_name)
                    collision_idx = 1
                    while os.path.exists(os.path.join(directory, f"{base}_{collision_idx}{ext}")):
                        collision_idx += 1
                    new_name = f"{base}_{collision_idx}{ext}"
                    new_path = os.path.join(directory, new_name)
                
                # Rename file
                if new_path != filepath:
                    os.rename(filepath, new_path)
                    rename_ops.append((new_path, filepath))  # Store for undo
                    
                    # Inject metadata if requested
                    if metadata and self._is_image(new_path):
                        self._inject_metadata(new_path, metadata)
                    
                    successes.append(new_path)
                    self.logger.info(f"Renamed: {filepath} -> {new_name}")
                else:
                    successes.append(filepath)  # No change needed
                    
            except Exception as e:
                self.logger.error(f"Error renaming {filepath}: {e}")
                errors.append(f"{filepath}: {str(e)}")
        
        # Store rename operations for undo
        if rename_ops:
            self.rename_history.append(rename_ops)
            # Keep history limited to last 10 operations
            if len(self.rename_history) > 10:
                self.rename_history.pop(0)
        
        return successes, errors
    
    def _is_image(self, filepath: str) -> bool:
        """Check if file is an image"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    def _inject_metadata(self, filepath: str, metadata: Dict[str, str]):
        """
        Inject metadata into image file.
        
        Args:
            filepath: Path to image file
            metadata: Dict with 'copyright', 'author', 'description' keys
        """
        try:
            img = Image.open(filepath)
            
            # Handle PNG
            if filepath.lower().endswith('.png'):
                from PIL import PngImagePlugin
                meta = PngImagePlugin.PngInfo()
                
                if 'copyright' in metadata:
                    meta.add_text("Copyright", metadata['copyright'])
                if 'author' in metadata:
                    meta.add_text("Author", metadata['author'])
                if 'description' in metadata:
                    meta.add_text("Description", metadata['description'])
                
                img.save(filepath, "PNG", pnginfo=meta)
                
            # Handle JPEG
            elif filepath.lower().endswith(('.jpg', '.jpeg')):
                # Load existing EXIF or create new
                try:
                    exif_dict = piexif.load(filepath)
                except Exception as e:
                    logger.warning(f"Could not load EXIF data from {filepath}: {e}")
                    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
                
                if 'copyright' in metadata:
                    exif_dict['0th'][piexif.ImageIFD.Copyright] = metadata['copyright'].encode()
                if 'author' in metadata:
                    exif_dict['0th'][piexif.ImageIFD.Artist] = metadata['author'].encode()
                if 'description' in metadata:
                    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = metadata['description'].encode()
                
                exif_bytes = piexif.dump(exif_dict)
                img.save(filepath, "JPEG", exif=exif_bytes, quality=95)
            
            self.logger.info(f"Injected metadata into {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error injecting metadata into {filepath}: {e}")
    
    def undo_last_rename(self) -> bool:
        """
        Undo the last batch rename operation.
        
        Returns:
            True if undo successful, False otherwise
        """
        if not self.rename_history:
            self.logger.warning("No rename operations to undo")
            return False
        
        try:
            rename_ops = self.rename_history.pop()
            
            # Reverse the rename operations
            for new_path, old_path in reversed(rename_ops):
                if os.path.exists(new_path):
                    os.rename(new_path, old_path)
                    self.logger.info(f"Undone: {new_path} -> {old_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error undoing rename: {e}")
            return False
    
    def get_metadata_from_file(self, filepath: str) -> Dict[str, str]:
        """
        Extract existing metadata from image file.
        
        Returns:
            Dict with 'copyright', 'author', 'description' keys
        """
        metadata = {
            'copyright': '',
            'author': '',
            'description': ''
        }
        
        try:
            if filepath.lower().endswith('.png'):
                img = Image.open(filepath)
                info = img.info
                metadata['copyright'] = info.get('Copyright', '')
                metadata['author'] = info.get('Author', '')
                metadata['description'] = info.get('Description', '')
                
            elif filepath.lower().endswith(('.jpg', '.jpeg')):
                exif_dict = piexif.load(filepath)
                if piexif.ImageIFD.Copyright in exif_dict['0th']:
                    metadata['copyright'] = exif_dict['0th'][piexif.ImageIFD.Copyright].decode()
                if piexif.ImageIFD.Artist in exif_dict['0th']:
                    metadata['author'] = exif_dict['0th'][piexif.ImageIFD.Artist].decode()
                if piexif.ImageIFD.ImageDescription in exif_dict['0th']:
                    metadata['description'] = exif_dict['0th'][piexif.ImageIFD.ImageDescription].decode()
        
        except Exception as e:
            self.logger.warning(f"Could not read metadata from {filepath}: {e}")
        
        return metadata
