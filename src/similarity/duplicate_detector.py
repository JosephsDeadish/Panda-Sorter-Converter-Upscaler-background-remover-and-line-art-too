"""
Duplicate Detector
Detect duplicates and variants using embeddings
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Detect duplicate and variant textures.
    
    Features:
    - Exact duplicates (high similarity)
    - Color variants
    - Brightness variants
    - Slight modifications
    """
    
    def __init__(self, similarity_search):
        """
        Initialize duplicate detector.
        
        Args:
            similarity_search: SimilaritySearch instance
        """
        self.similarity_search = similarity_search
        logger.info("DuplicateDetector initialized")
    
    def find_exact_duplicates(
        self,
        threshold: float = 0.99
    ) -> List[List[Path]]:
        """
        Find exact duplicate textures.
        
        Args:
            threshold: Similarity threshold for exact duplicates
            
        Returns:
            List of duplicate groups (list of paths)
        """
        duplicate_groups = self.similarity_search.find_duplicates(threshold)
        
        # Convert to list of paths
        result = []
        for group in duplicate_groups:
            paths = [item['texture_path'] for item in group]
            result.append(paths)
        
        logger.info(f"Found {len(result)} exact duplicate groups")
        return result
    
    def find_variants(
        self,
        texture_path: Path,
        min_similarity: float = 0.85,
        max_similarity: float = 0.99
    ) -> List[Dict[str, Any]]:
        """
        Find variants of a specific texture.
        
        Args:
            texture_path: Path to reference texture
            min_similarity: Minimum similarity for variants
            max_similarity: Maximum similarity for variants
            
        Returns:
            List of variant textures with similarity scores
        """
        variants = self.similarity_search.find_variants(
            texture_path,
            similarity_range=(min_similarity, max_similarity)
        )
        
        logger.info(f"Found {len(variants)} variants for {texture_path.name}")
        return variants
    
    def detect_color_swaps(
        self,
        texture_path: Path,
        threshold: float = 0.90
    ) -> List[Dict[str, Any]]:
        """
        Detect textures that are color swaps of the original.
        
        Color swaps have similar structure but different colors.
        
        Args:
            texture_path: Path to reference texture
            threshold: Similarity threshold
            
        Returns:
            List of color-swapped textures
        """
        # Find variants
        variants = self.find_variants(texture_path, min_similarity=threshold, max_similarity=0.99)
        
        # TODO: Add additional color histogram analysis to filter true color swaps
        # For now, variants in the specified range are likely color swaps
        
        logger.info(f"Found {len(variants)} potential color swaps for {texture_path.name}")
        return variants
    
    def group_by_similarity(
        self,
        similarity_threshold: float = 0.90,
        max_group_size: int = 50
    ) -> List[List[Dict[str, Any]]]:
        """
        Group all textures by similarity.
        
        Args:
            similarity_threshold: Minimum similarity for same group
            max_group_size: Maximum textures per group
            
        Returns:
            List of texture groups
        """
        groups = self.similarity_search.cluster_similar(
            similarity_threshold=similarity_threshold,
            max_cluster_size=max_group_size
        )
        
        logger.info(f"Grouped textures into {len(groups)} similarity groups")
        return groups
