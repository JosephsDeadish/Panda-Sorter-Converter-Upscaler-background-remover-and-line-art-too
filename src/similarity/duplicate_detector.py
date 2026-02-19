"""
Duplicate Detector
Detect duplicates and variants using embeddings
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.error("numpy not available - limited functionality")
    logger.error("Install with: pip install numpy")

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
        Uses color histogram analysis: a true color swap will have a
        significantly different hue distribution while the structural
        (grayscale) similarity stays high.
        
        Args:
            texture_path: Path to reference texture
            threshold: Similarity threshold
            
        Returns:
            List of color-swapped textures
        """
        # Find structurally similar variants first
        variants = self.find_variants(texture_path, min_similarity=threshold, max_similarity=0.99)

        # Filter to true color swaps via histogram comparison
        try:
            from PIL import Image as PILImage
            ref_img = PILImage.open(texture_path).convert("RGB")
            ref_hist = self._color_histogram(ref_img)
        except Exception:
            logger.debug("Could not load reference image for histogram analysis")
            return variants

        color_swaps = []
        for variant in variants:
            try:
                v_path = variant.get("texture_path") or variant.get("path")
                if v_path is None:
                    color_swaps.append(variant)
                    continue
                v_img = PILImage.open(v_path).convert("RGB")
                v_hist = self._color_histogram(v_img)
                hist_diff = self._histogram_distance(ref_hist, v_hist)
                # A large histogram distance means very different colours
                # but the structural similarity is already high (>threshold)
                if hist_diff > 0.15:
                    variant["histogram_distance"] = round(hist_diff, 4)
                    color_swaps.append(variant)
            except Exception:
                color_swaps.append(variant)

        logger.info(f"Found {len(color_swaps)} color swaps (from {len(variants)} variants) for {texture_path.name}")
        return color_swaps

    @staticmethod
    def _color_histogram(image, bins: int = 32) -> np.ndarray:
        """Compute a normalized per-channel colour histogram."""
        arr = np.asarray(image)
        hists = []
        for ch in range(min(arr.shape[2], 3)):
            h, _ = np.histogram(arr[:, :, ch], bins=bins, range=(0, 256))
            h = h.astype(np.float64)
            total = h.sum()
            if total > 0:
                h /= total
            hists.append(h)
        return np.concatenate(hists)

    @staticmethod
    def _histogram_distance(h1: np.ndarray, h2: np.ndarray) -> float:
        """Chi-squared distance between two histograms (0 = identical)."""
        denom = h1 + h2
        nonzero = denom > 0
        if not nonzero.any():
            return 0.0
        return float(0.5 * np.sum(((h1[nonzero] - h2[nonzero]) ** 2) / denom[nonzero]))
    
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
