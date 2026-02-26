"""
LOD (Level of Detail) Replacement System
Identify and replace lower quality LOD textures with highest quality versions
Author: Dead On The Inside / JosephsDeadish
"""

import re
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, OSError, RuntimeError):
    HAS_PIL = False
    Image = None  # type: ignore[assignment]
    logger.warning("Pillow not available — LOD resolution detection disabled. "
                   "Install with: pip install Pillow")


@dataclass
class LODTexture:
    """Represents a texture with LOD information."""
    path: Path
    base_name: str
    lod_level: int
    width: int
    height: int
    file_size: int
    format: str
    
    @property
    def resolution(self) -> int:
        """Get total resolution (width * height)."""
        return self.width * self.height
    
    @property
    def quality_score(self) -> float:
        """
        Calculate quality score for LOD comparison.
        Higher score = better quality.
        """
        # Weight resolution heavily, but also consider file size
        resolution_score = self.resolution / 1000000.0  # Normalize to megapixels
        size_score = self.file_size / 1000000.0  # Normalize to MB
        
        # Resolution is more important than file size
        return (resolution_score * 0.7) + (size_score * 0.3)


@dataclass
class LODGroup:
    """Group of LOD textures for the same base texture."""
    base_name: str
    textures: List[LODTexture]
    best_lod: Optional[LODTexture] = None
    
    def __post_init__(self):
        """Identify the best quality LOD."""
        if self.textures:
            self.best_lod = max(self.textures, key=lambda t: t.quality_score)


class LODReplacer:
    """
    LOD (Level of Detail) replacement system.
    
    Features:
    - Identify LOD textures by common naming patterns
    - Detect best quality LOD in each group
    - Replace lower quality LODs with highest quality
    - Batch process LOD groups
    - Preview changes before applying
    - Create backups before replacement
    - NEVER rename original files (only creates copies)
    - Thread-safe operations
    
    Common LOD patterns:
    - texture_lod0, texture_lod1, texture_lod2
    - texture_0, texture_1, texture_2
    - texture_hi, texture_med, texture_low
    - texture_mip0, texture_mip1, texture_mip2
    """
    
    # LOD naming patterns (regex patterns)
    LOD_PATTERNS = [
        r'(.+)_lod(\d+)',           # texture_lod0, texture_lod1
        r'(.+)_mip(\d+)',           # texture_mip0, texture_mip1
        r'(.+)_(\d+)$',             # texture_0, texture_1 (end of name)
        r'(.+)_(hi|med|medium|low|lowest)',  # texture_hi, texture_med
        r'(.+)_(high|normal|small)',         # texture_high, texture_normal
    ]
    
    # Quality level mappings for text-based LOD levels
    QUALITY_LEVELS = {
        'hi': 0, 'high': 0, 'highest': 0,
        'med': 1, 'medium': 1, 'normal': 1,
        'low': 2, 'small': 2,
        'lowest': 3, 'tiny': 3
    }
    
    def __init__(self, backup_enabled: bool = True):
        """
        Initialize LOD replacer.
        
        Args:
            backup_enabled: Whether to create backups before replacement
        """
        self.backup_enabled = backup_enabled
        self.lod_groups: Dict[str, LODGroup] = {}
        self._lock = Lock()
        
        logger.debug(f"LODReplacer initialized with backup_enabled={backup_enabled}")
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> Dict[str, LODGroup]:
        """
        Scan directory for LOD textures and group them.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            Dictionary of LOD groups by base name
        """
        try:
            logger.info(f"Scanning directory for LOD textures: {directory}")
            
            # Supported image formats
            image_extensions = {'.dds', '.png', '.jpg', '.jpeg', '.tga', '.bmp'}
            
            # Find all texture files
            if recursive:
                files = [f for f in directory.rglob('*') if f.suffix.lower() in image_extensions]
            else:
                files = [f for f in directory.glob('*') if f.suffix.lower() in image_extensions]
            
            logger.debug(f"Found {len(files)} texture files")
            
            # Group by base name
            grouped_textures = defaultdict(list)
            
            for file_path in files:
                lod_info = self._parse_lod_info(file_path)
                if lod_info:
                    base_name, lod_level = lod_info
                    
                    # Get texture properties
                    texture = self._create_lod_texture(file_path, base_name, lod_level)
                    if texture:
                        grouped_textures[base_name].append(texture)
            
            # Create LOD groups
            with self._lock:
                self.lod_groups = {}
                for base_name, textures in grouped_textures.items():
                    if len(textures) > 1:  # Only consider groups with multiple LODs
                        group = LODGroup(base_name=base_name, textures=textures)
                        self.lod_groups[base_name] = group
            
            logger.info(f"Found {len(self.lod_groups)} LOD groups")
            return self.lod_groups
            
        except Exception as e:
            logger.error(f"Error scanning directory for LODs: {e}", exc_info=True)
            return {}
    
    def _parse_lod_info(self, file_path: Path) -> Optional[Tuple[str, int]]:
        """
        Parse LOD information from filename.
        
        Args:
            file_path: Path to texture file
            
        Returns:
            Tuple of (base_name, lod_level) or None if not an LOD texture
        """
        filename = file_path.stem
        
        for pattern in self.LOD_PATTERNS:
            match = re.match(pattern, filename, re.IGNORECASE)
            if match:
                base_name = match.group(1)
                lod_indicator = match.group(2)
                
                # Convert LOD indicator to numeric level
                if lod_indicator.isdigit():
                    lod_level = int(lod_indicator)
                else:
                    lod_level = self.QUALITY_LEVELS.get(lod_indicator.lower(), 999)
                
                return (base_name, lod_level)
        
        return None
    
    def _create_lod_texture(
        self,
        file_path: Path,
        base_name: str,
        lod_level: int
    ) -> Optional[LODTexture]:
        """
        Create LODTexture object with metadata.
        
        Args:
            file_path: Path to texture file
            base_name: Base name without LOD suffix
            lod_level: LOD level number
            
        Returns:
            LODTexture object or None on error
        """
        try:
            # Get file size
            file_size = file_path.stat().st_size
            
            # Get image dimensions
            try:
                if not HAS_PIL:
                    logger.warning(f"Pillow not available, cannot read dimensions for {file_path}")
                    return None
                with Image.open(file_path) as img:
                    width, height = img.size
                    format_name = img.format or file_path.suffix[1:].upper()
            except Exception as e:
                logger.warning(f"Could not read image {file_path}: {e}")
                return None
            
            return LODTexture(
                path=file_path,
                base_name=base_name,
                lod_level=lod_level,
                width=width,
                height=height,
                file_size=file_size,
                format=format_name
            )
            
        except Exception as e:
            logger.error(f"Error creating LODTexture for {file_path}: {e}")
            return None
    
    def get_replacement_plan(self) -> List[Dict[str, any]]:
        """
        Generate preview of replacement operations.
        
        Returns:
            List of replacement plans with source and target info
        """
        plans = []
        
        with self._lock:
            for group in self.lod_groups.values():
                if not group.best_lod:
                    continue
                
                for texture in group.textures:
                    if texture.path != group.best_lod.path:
                        plans.append({
                            'base_name': group.base_name,
                            'source': {
                                'path': str(group.best_lod.path),
                                'resolution': f"{group.best_lod.width}x{group.best_lod.height}",
                                'size': group.best_lod.file_size,
                                'quality_score': group.best_lod.quality_score
                            },
                            'target': {
                                'path': str(texture.path),
                                'resolution': f"{texture.width}x{texture.height}",
                                'size': texture.file_size,
                                'quality_score': texture.quality_score
                            },
                            'improvement': {
                                'resolution': group.best_lod.resolution - texture.resolution,
                                'size': group.best_lod.file_size - texture.file_size
                            }
                        })
        
        return plans
    
    def replace_lods(
        self,
        base_names: Optional[List[str]] = None,
        backup_dir: Optional[Path] = None
    ) -> Dict[str, any]:
        """
        Replace lower quality LODs with highest quality versions.
        
        Args:
            base_names: Optional list of base names to process (None = all)
            backup_dir: Optional custom backup directory
            
        Returns:
            Dictionary with replacement results
        """
        try:
            logger.info("Starting LOD replacement")
            
            replaced = []
            failed = []
            backed_up = []
            
            with self._lock:
                groups_to_process = self.lod_groups.values()
                
                if base_names:
                    groups_to_process = [
                        self.lod_groups[name]
                        for name in base_names
                        if name in self.lod_groups
                    ]
            
            for group in groups_to_process:
                if not group.best_lod:
                    logger.warning(f"No best LOD found for group: {group.base_name}")
                    continue
                
                for texture in group.textures:
                    # Skip the best quality texture itself
                    if texture.path == group.best_lod.path:
                        continue
                    
                    try:
                        # Create backup if enabled
                        if self.backup_enabled:
                            backup_path = self._create_backup(texture.path, backup_dir)
                            if backup_path:
                                backed_up.append(backup_path)
                        
                        # Copy best LOD to replace lower quality version
                        # NOTE: We do NOT rename the original, only replace with a copy
                        shutil.copy2(group.best_lod.path, texture.path)
                        
                        replaced.append({
                            'base_name': group.base_name,
                            'source': str(group.best_lod.path),
                            'target': str(texture.path)
                        })
                        
                        logger.info(
                            f"Replaced {texture.path.name} with best LOD "
                            f"from {group.best_lod.path.name}"
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to replace {texture.path}: {e}")
                        failed.append({
                            'path': str(texture.path),
                            'error': str(e)
                        })
            
            result = {
                'replaced': len(replaced),
                'failed': len(failed),
                'backed_up': len(backed_up),
                'replaced_files': replaced,
                'failed_files': failed
            }
            
            logger.info(
                f"LOD replacement complete: "
                f"{len(replaced)} replaced, {len(failed)} failed"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during LOD replacement: {e}", exc_info=True)
            return {
                'replaced': 0,
                'failed': 0,
                'backed_up': 0,
                'error': str(e)
            }
    
    def _create_backup(
        self,
        file_path: Path,
        backup_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Create backup of a file before replacement.
        
        Args:
            file_path: File to backup
            backup_dir: Optional custom backup directory
            
        Returns:
            Path to backup file or None on error
        """
        try:
            if backup_dir is None:
                backup_dir = file_path.parent / '.lod_backups'
            
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create unique backup name with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            return None
    
    def get_lod_groups(self) -> List[Dict[str, any]]:
        """
        Get information about all LOD groups.
        
        Returns:
            List of LOD group information dictionaries
        """
        with self._lock:
            return [
                {
                    'base_name': group.base_name,
                    'texture_count': len(group.textures),
                    'best_lod': {
                        'path': str(group.best_lod.path),
                        'resolution': f"{group.best_lod.width}x{group.best_lod.height}",
                        'size': group.best_lod.file_size,
                        'lod_level': group.best_lod.lod_level
                    } if group.best_lod else None,
                    'textures': [
                        {
                            'path': str(tex.path),
                            'lod_level': tex.lod_level,
                            'resolution': f"{tex.width}x{tex.height}",
                            'size': tex.file_size,
                            'quality_score': tex.quality_score
                        }
                        for tex in sorted(group.textures, key=lambda t: t.lod_level)
                    ]
                }
                for group in self.lod_groups.values()
            ]
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about LOD groups.
        
        Returns:
            Dictionary with LOD statistics
        """
        with self._lock:
            if not self.lod_groups:
                return {
                    'total_groups': 0,
                    'total_textures': 0,
                    'replaceable_textures': 0,
                    'potential_space_saved': 0
                }
            
            total_textures = sum(len(g.textures) for g in self.lod_groups.values())
            replaceable_textures = sum(
                len(g.textures) - 1
                for g in self.lod_groups.values()
                if g.best_lod
            )
            
            # Calculate potential space change (could be positive or negative)
            space_delta = 0
            for group in self.lod_groups.values():
                if group.best_lod:
                    for texture in group.textures:
                        if texture.path != group.best_lod.path:
                            space_delta += group.best_lod.file_size - texture.file_size
            
            return {
                'total_groups': len(self.lod_groups),
                'total_textures': total_textures,
                'replaceable_textures': replaceable_textures,
                'potential_space_delta': space_delta,
                'avg_textures_per_group': total_textures / len(self.lod_groups)
            }
    
    def clear(self):
        """Clear all LOD groups."""
        with self._lock:
            self.lod_groups.clear()
            logger.debug("Cleared all LOD groups")
