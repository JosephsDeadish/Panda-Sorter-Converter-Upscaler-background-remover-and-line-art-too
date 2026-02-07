"""
PS2 Texture Sorter - Organization Engine
Author: Dead On The Inside / JosephsDeadish

Main engine for organizing textures into hierarchical folder structures.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
import re


@dataclass
class TextureInfo:
    """Information about a texture file for organization"""
    file_path: str
    filename: str
    category: str
    confidence: float
    lod_group: Optional[str] = None
    lod_level: Optional[int] = None
    file_size: int = 0
    dimensions: Optional[Tuple[int, int]] = None
    format: str = ""
    variant: Optional[str] = None  # For detecting variants like gender, skin tone


class OrganizationEngine:
    """
    Base engine for organizing textures into folder hierarchies.
    Handles the actual file operations and delegates structure creation to style classes.
    """
    
    def __init__(self, style_class, output_dir: str, dry_run: bool = False):
        """
        Initialize the organization engine.
        
        Args:
            style_class: Organization style class to use
            output_dir: Base output directory for organized files
            dry_run: If True, only simulate operations without moving files
        """
        self.style = style_class()
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.operations_log = []
        
    def organize_textures(
        self, 
        textures: List[TextureInfo],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Organize textures according to the selected style.
        
        Args:
            textures: List of TextureInfo objects to organize
            progress_callback: Optional callback function(current, total, status_msg)
            
        Returns:
            Dict with results: {
                'success': bool,
                'processed': int,
                'failed': int,
                'operations': list,
                'errors': list
            }
        """
        results = {
            'success': True,
            'processed': 0,
            'failed': 0,
            'operations': [],
            'errors': []
        }
        
        # Create base output directory
        if not self.dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        total = len(textures)
        
        for idx, texture in enumerate(textures):
            try:
                # Get target path from style
                relative_path = self.style.get_target_path(texture)
                target_path = self.output_dir / relative_path
                
                # Create directory structure
                if not self.dry_run:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy/move file
                operation = self._perform_file_operation(texture.file_path, target_path)
                
                results['operations'].append(operation)
                results['processed'] += 1
                
                # Progress callback
                if progress_callback:
                    progress_callback(
                        idx + 1,
                        total,
                        f"Organized: {texture.filename}"
                    )
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'file': texture.filename,
                    'error': str(e)
                })
                results['success'] = False
                
                if progress_callback:
                    progress_callback(
                        idx + 1,
                        total,
                        f"Error: {texture.filename} - {str(e)}"
                    )
        
        return results
    
    def _perform_file_operation(self, source: str, target: Path) -> Dict[str, str]:
        """
        Perform the actual file copy/move operation.
        
        Args:
            source: Source file path
            target: Target file path
            
        Returns:
            Dict with operation details
        """
        operation = {
            'source': source,
            'target': str(target),
            'action': 'copy' if self.dry_run else 'copied'
        }
        
        if self.dry_run:
            operation['status'] = 'simulated'
        else:
            # Copy file (preserve original)
            shutil.copy2(source, target)
            operation['status'] = 'success'
        
        self.operations_log.append(operation)
        return operation
    
    def get_style_name(self) -> str:
        """Get the name of the current organization style"""
        return self.style.get_name()
    
    def get_style_description(self) -> str:
        """Get the description of the current organization style"""
        return self.style.get_description()


class OrganizationStyle:
    """Base class for organization styles"""
    
    def get_name(self) -> str:
        """Return the style name"""
        raise NotImplementedError
    
    def get_description(self) -> str:
        """Return the style description"""
        raise NotImplementedError
    
    def get_target_path(self, texture: TextureInfo) -> str:
        """
        Calculate the target path for a texture based on this style.
        
        Args:
            texture: TextureInfo object
            
        Returns:
            Relative path string (e.g., "Character/Male/Skin/variant_01.dds")
        """
        raise NotImplementedError
    
    @staticmethod
    def detect_variant(filename: str) -> Optional[str]:
        """
        Detect variant information from filename.
        Common patterns: _male, _female, _black, _white, _01, _02, etc.
        
        Args:
            filename: File name to analyze
            
        Returns:
            Variant string or None
        """
        # Gender detection
        if re.search(r'[_-]male(?![a-z])', filename, re.IGNORECASE):
            return 'Male'
        if re.search(r'[_-]female(?![a-z])', filename, re.IGNORECASE):
            return 'Female'
        
        # Color/skin tone detection
        color_patterns = {
            'Black': r'[_-]black(?![a-z])',
            'White': r'[_-]white(?![a-z])',
            'Brown': r'[_-]brown(?![a-z])',
            'Tan': r'[_-]tan(?![a-z])',
            'Red': r'[_-]red(?![a-z])',
            'Blue': r'[_-]blue(?![a-z])',
            'Green': r'[_-]green(?![a-z])',
            'Yellow': r'[_-]yellow(?![a-z])',
        }
        
        for color, pattern in color_patterns.items():
            if re.search(pattern, filename, re.IGNORECASE):
                return color
        
        # Numeric variant detection
        numeric_match = re.search(r'[_-](\d{2,})(?=\.|$)', filename)
        if numeric_match:
            return f"Variant_{numeric_match.group(1)}"
        
        return None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove invalid characters from filename"""
        # Remove or replace invalid Windows filename characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
