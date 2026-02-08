"""
LOD (Level of Detail) Detection System
Automatically detects and groups LOD textures
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class LODDetector:
    """Detects and groups Level of Detail (LOD) textures"""
    
    # Common LOD patterns
    LOD_PATTERNS = [
        r'(.+)_lod(\d+)',           # texture_lod0, texture_lod1
        r'(.+)_l(\d+)',              # texture_l0, texture_l1
        r'(.+)_(high|med|medium|low)', # texture_high, texture_med, texture_low
        r'(.+)_(\d+)$',              # texture_0, texture_1, texture_2
        r'(.+)_(hi|md|lo)',          # texture_hi, texture_md, texture_lo
        r'(.+)_([0-9]+)x([0-9]+)',   # texture_1024x1024, texture_512x512
    ]
    
    # Resolution-based LOD detection
    LOD_RESOLUTIONS = {
        'high': [(2048, 4096), (4096, 8192), (8192, 16384)],
        'medium': [(512, 1024), (1024, 2048)],
        'low': [(64, 256), (256, 512)]
    }
    
    def __init__(self):
        self.lod_groups = defaultdict(list)
    
    def detect_lod_pattern(self, filename: str) -> Tuple[str, Optional[str]]:
        """
        Detect if filename follows a LOD pattern
        
        Args:
            filename: The filename to check
        
        Returns:
            Tuple of (base_name, lod_level) or (filename, None) if no pattern found
        """
        for pattern in self.LOD_PATTERNS:
            match = re.match(pattern, filename, re.IGNORECASE)
            if match:
                groups = match.groups()
                base_name = groups[0]
                lod_level = groups[1] if len(groups) > 1 else "0"
                return base_name, lod_level
        
        return filename, None
    
    def group_lods(self, file_paths: List[Path]) -> Dict[str, List[Path]]:
        """
        Group files by their base name (LOD sets)
        
        Args:
            file_paths: List of file paths to group
        
        Returns:
            Dictionary mapping base names to lists of LOD files
        """
        groups = defaultdict(list)
        
        for file_path in file_paths:
            filename = file_path.stem
            base_name, lod_level = self.detect_lod_pattern(filename)
            
            # Use base name as group key
            groups[base_name].append({
                'path': file_path,
                'lod_level': lod_level,
                'filename': filename
            })
        
        # Sort each group by LOD level
        for base_name, files in groups.items():
            groups[base_name] = sorted(files, key=lambda x: self._lod_sort_key(x['lod_level']))
        
        return groups
    
    def detect_lods(self, file_paths: List[Path]) -> Dict[str, List[Path]]:
        """
        Alias for group_lods() for backward compatibility.
        
        Args:
            file_paths: List of file paths to group
        
        Returns:
            Dictionary mapping base names to lists of LOD files
        """
        return self.group_lods(file_paths)
    
    def _lod_sort_key(self, lod_level: Optional[str]) -> int:
        """Generate sort key for LOD level"""
        if lod_level is None:
            return 999
        
        # Try to extract numeric value
        try:
            return int(re.search(r'\d+', str(lod_level)).group())
        except:
            pass
        
        # Handle text-based levels
        level_map = {
            'high': 0, 'hi': 0,
            'med': 1, 'medium': 1, 'md': 1,
            'low': 2, 'lo': 2
        }
        return level_map.get(str(lod_level).lower(), 999)
    
    def find_incomplete_lod_sets(self, groups: Dict[str, List[Path]]) -> List[str]:
        """
        Find LOD sets that might be incomplete
        
        Args:
            groups: Dictionary of grouped LOD files
        
        Returns:
            List of base names with potentially incomplete LOD sets
        """
        incomplete = []
        
        for base_name, files in groups.items():
            # If it has LOD patterns but only one file, might be incomplete
            if len(files) == 1 and files[0]['lod_level'] is not None:
                incomplete.append(base_name)
            
            # Check for gaps in numeric LOD sequences
            lod_levels = [f['lod_level'] for f in files if f['lod_level'] is not None]
            if lod_levels:
                try:
                    numeric_levels = sorted([int(re.search(r'\d+', str(l)).group()) for l in lod_levels])
                    expected = list(range(numeric_levels[0], numeric_levels[-1] + 1))
                    if len(numeric_levels) != len(expected):
                        incomplete.append(base_name)
                except:
                    pass
        
        return incomplete
    
    def are_visually_similar(self, file1: Path, file2: Path, threshold=0.85) -> bool:
        """
        Check if two textures are visually similar (potential LOD pair)
        
        Args:
            file1: First texture file
            file2: Second texture file  
            threshold: Similarity threshold (0-1)
        
        Returns:
            True if textures are similar enough to be LODs
        """
        try:
            from PIL import Image
            import numpy as np
            
            # Load and resize both images to same size for comparison
            img1 = Image.open(file1).convert('RGB').resize((64, 64))
            img2 = Image.open(file2).convert('RGB').resize((64, 64))
            
            # Convert to arrays
            arr1 = np.array(img1, dtype=np.float32)
            arr2 = np.array(img2, dtype=np.float32)
            
            # Calculate similarity (normalized cross-correlation)
            similarity = np.corrcoef(arr1.flatten(), arr2.flatten())[0, 1]
            
            return similarity >= threshold
            
        except Exception as e:
            print(f"Error comparing images: {e}")
            return False
    
    def detect_unnumbered_lods(self, file_paths: List[Path], similarity_threshold=0.85) -> Dict[str, List[Path]]:
        """
        Detect LODs without explicit numbering using visual similarity
        
        Args:
            file_paths: List of file paths to check
            similarity_threshold: Minimum similarity to consider as LOD pair
        
        Returns:
            Dictionary of grouped similar textures
        """
        # This is computationally expensive, so only use on small sets
        if len(file_paths) > 100:
            print("Warning: Visual similarity detection is slow for large sets")
        
        groups = defaultdict(list)
        processed = set()
        
        for i, file1 in enumerate(file_paths):
            if str(file1) in processed:
                continue
            
            group_key = file1.stem
            groups[group_key].append(file1)
            processed.add(str(file1))
            
            # Compare with remaining files
            for file2 in file_paths[i+1:]:
                if str(file2) not in processed:
                    if self.are_visually_similar(file1, file2, similarity_threshold):
                        groups[group_key].append(file2)
                        processed.add(str(file2))
        
        # Filter out single-file groups
        return {k: v for k, v in groups.items() if len(v) > 1}
