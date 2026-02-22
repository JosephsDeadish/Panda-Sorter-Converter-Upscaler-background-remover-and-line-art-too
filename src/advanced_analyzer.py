"""
Advanced Texture Analyzer
Integration of preprocessing, vision models, and similarity search
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
try:
    import numpy as np
    HAS_NUMPY = True
except (ImportError, OSError):
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False
try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, OSError):
    HAS_PIL = False


logger = logging.getLogger(__name__)


class AdvancedTextureAnalyzer:
    """
    Complete texture analysis system integrating all advanced features.
    
    Combines:
    - Preprocessing pipeline (upscaling, filtering, normalization)
    - Vision models (CLIP, DINOv2, ViT, EfficientNet)
    - Similarity search (FAISS-based)
    - Duplicate detection
    """
    
    def __init__(
        self,
        use_preprocessing: bool = True,
        use_clip: bool = True,
        use_dinov2: bool = False,
        use_faiss: bool = True,
        device: Optional[str] = None
    ):
        """
        Initialize advanced texture analyzer.
        
        Args:
            use_preprocessing: Enable preprocessing pipeline
            use_clip: Enable CLIP model
            use_dinov2: Enable DINOv2 model
            use_faiss: Enable FAISS similarity search
            device: Device for models ('cuda', 'cpu', or None for auto)
        """
        self.device = device
        
        # Initialize preprocessing
        self.preprocessing = None
        if use_preprocessing:
            try:
                from preprocessing import PreprocessingPipeline
                self.preprocessing = PreprocessingPipeline()
                logger.info("Preprocessing pipeline initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize preprocessing: {e}")
        
        # Initialize CLIP
        self.clip_model = None
        if use_clip:
            try:
                from vision_models import CLIPModel
                self.clip_model = CLIPModel(device=device)
                logger.info("CLIP model initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize CLIP: {e}")
        
        # Initialize DINOv2
        self.dinov2_model = None
        if use_dinov2:
            try:
                from vision_models import DINOv2Model
                self.dinov2_model = DINOv2Model(device=device)
                logger.info("DINOv2 model initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize DINOv2: {e}")
        
        # Initialize similarity search
        self.similarity_search = None
        if use_faiss and self.clip_model:
            try:
                from similarity import SimilaritySearch
                # Use CLIP embedding dimension (512 for base model)
                self.similarity_search = SimilaritySearch(embedding_dim=512)
                logger.info("Similarity search initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize similarity search: {e}")
        
        logger.info("AdvancedTextureAnalyzer initialized")
    
    def analyze_texture(
        self,
        texture_path: Path,
        preprocess: bool = True,
        generate_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        Perform complete analysis on a texture.
        
        Args:
            texture_path: Path to texture file
            preprocess: Apply preprocessing
            generate_embedding: Generate embedding with vision model
            
        Returns:
            Dictionary with all analysis results
        """
        result = {
            'texture_path': texture_path,
            'preprocessed': False,
            'embedding': None,
            'preprocessing_info': None
        }
        
        try:
            if not texture_path.exists():
                logger.error(f"Texture file not found: {texture_path}")
                result['error'] = f"File not found: {texture_path}"
                return result
            
            # Load image
            with Image.open(texture_path) as _img:
                img_array = np.array(_img.convert('RGB'))
            
            # Preprocess if enabled
            if preprocess and self.preprocessing:
                preprocess_result = self.preprocessing.process(img_array)
                img_array = preprocess_result['image']
                result['preprocessed'] = True
                result['preprocessing_info'] = preprocess_result
                logger.debug(f"Preprocessed {texture_path.name}")
            
            # Generate embedding
            if generate_embedding and self.clip_model:
                embedding = self.clip_model.encode_image(img_array)
                result['embedding'] = embedding
                logger.debug(f"Generated embedding for {texture_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to analyze texture {texture_path}: {e}")
            result['error'] = str(e)
        
        return result
    
    def batch_analyze(
        self,
        texture_paths: List[Path],
        preprocess: bool = True,
        add_to_index: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple textures in batch.
        
        Args:
            texture_paths: List of texture paths
            preprocess: Apply preprocessing
            add_to_index: Add embeddings to similarity search index
            
        Returns:
            List of analysis results
        """
        results = []
        
        for path in texture_paths:
            result = self.analyze_texture(path, preprocess=preprocess)
            results.append(result)
            
            # Add to similarity index
            if add_to_index and self.similarity_search and result.get('embedding') is not None:
                self.similarity_search.add_embedding(
                    result['embedding'],
                    path,
                    metadata={'preprocessed': result['preprocessed']}
                )
        
        logger.info(f"Batch analyzed {len(texture_paths)} textures")
        return results
    
    def classify_texture(
        self,
        texture_path: Path,
        categories: List[str],
        preprocess: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Classify texture into categories using CLIP.
        
        Args:
            texture_path: Path to texture
            categories: List of category names
            preprocess: Apply preprocessing
            
        Returns:
            List of predictions with categories and confidences
        """
        if not self.clip_model:
            raise RuntimeError("CLIP model not initialized")
        
        # Load and optionally preprocess
        image = Image.open(texture_path).convert('RGB')
        img_array = np.array(image)
        
        if preprocess and self.preprocessing:
            preprocess_result = self.preprocessing.process(img_array)
            img_array = preprocess_result['image']
        
        # Classify
        predictions = self.clip_model.classify_texture(img_array, categories)
        
        return predictions
    
    def find_similar_textures(
        self,
        texture_path: Path,
        k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar textures using similarity search.
        
        Args:
            texture_path: Path to query texture
            k: Number of results
            threshold: Optional similarity threshold
            
        Returns:
            List of similar textures
        """
        if not self.similarity_search:
            raise RuntimeError("Similarity search not initialized")
        
        # Get embedding
        result = self.analyze_texture(texture_path, generate_embedding=True)
        if result.get('embedding') is None:
            raise RuntimeError("Failed to generate embedding")
        
        # Search
        similar = self.similarity_search.search(
            result['embedding'],
            k=k,
            threshold=threshold
        )
        
        return similar
    
    def detect_duplicates(
        self,
        threshold: float = 0.99
    ) -> List[List[Path]]:
        """
        Detect duplicate textures.
        
        Args:
            threshold: Similarity threshold
            
        Returns:
            List of duplicate groups
        """
        if not self.similarity_search:
            raise RuntimeError("Similarity search not initialized")
        
        from similarity import DuplicateDetector
        detector = DuplicateDetector(self.similarity_search)
        
        return detector.find_exact_duplicates(threshold)
    
    def save_index(self, path: Path):
        """Save similarity search index."""
        if self.similarity_search:
            self.similarity_search.save(path)
            logger.info(f"Saved index to {path}")
    
    def load_index(self, path: Path):
        """Load similarity search index."""
        if self.similarity_search:
            self.similarity_search.load(path)
            logger.info(f"Loaded index from {path}")
