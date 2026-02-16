"""
FAISS-based Similarity Search System
Vector database for fast similarity search and clustering
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pickle

logger = logging.getLogger(__name__)

# Check for FAISS availability
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Similarity search disabled.")


class SimilaritySearch:
    """
    Fast similarity search using FAISS vector database.
    
    Features:
    - Generate and store image embeddings
    - Cosine similarity search
    - Detect duplicates and variants
    - Auto-group similar textures
    - Find reused UI elements
    """
    
    def __init__(
        self,
        embedding_dim: int = 512,
        index_type: str = 'flat',  # 'flat', 'ivf', 'hnsw'
        metric: str = 'cosine',  # 'cosine', 'l2', 'inner_product'
        use_gpu: bool = False
    ):
        """
        Initialize similarity search system.
        
        Args:
            embedding_dim: Dimension of embedding vectors
            index_type: FAISS index type
            metric: Distance metric
            use_gpu: Use GPU acceleration if available
        """
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS is required for similarity search")
        
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.metric = metric
        self.use_gpu = use_gpu
        
        # Create index
        self.index = self._create_index()
        
        # Storage for metadata
        self.texture_paths: List[Path] = []
        self.texture_metadata: List[Dict[str, Any]] = []
        
        logger.info(f"SimilaritySearch initialized: dim={embedding_dim}, "
                   f"index={index_type}, metric={metric}")
    
    def _create_index(self) -> faiss.Index:
        """Create FAISS index based on configuration."""
        if self.metric == 'cosine':
            # For cosine similarity, normalize vectors and use inner product
            if self.index_type == 'flat':
                index = faiss.IndexFlatIP(self.embedding_dim)
            elif self.index_type == 'ivf':
                # IVF (Inverted File) index for large datasets
                quantizer = faiss.IndexFlatIP(self.embedding_dim)
                index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, 100)
            elif self.index_type == 'hnsw':
                # HNSW (Hierarchical Navigable Small World) for fast search
                index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
            else:
                logger.warning(f"Unknown index type '{self.index_type}', using flat")
                index = faiss.IndexFlatIP(self.embedding_dim)
        elif self.metric == 'l2':
            if self.index_type == 'flat':
                index = faiss.IndexFlatL2(self.embedding_dim)
            elif self.index_type == 'ivf':
                quantizer = faiss.IndexFlatL2(self.embedding_dim)
                index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, 100)
            elif self.index_type == 'hnsw':
                index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
            else:
                index = faiss.IndexFlatL2(self.embedding_dim)
        else:
            # Default to inner product
            index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Move to GPU if requested
        if self.use_gpu and faiss.get_num_gpus() > 0:
            res = faiss.StandardGpuResources()
            index = faiss.index_cpu_to_gpu(res, 0, index)
            logger.info("Using GPU for FAISS index")
        
        return index
    
    def add_embedding(
        self,
        embedding: np.ndarray,
        texture_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add an embedding to the index.
        
        Args:
            embedding: Embedding vector (embedding_dim,)
            texture_path: Path to texture file
            metadata: Optional metadata dictionary
        """
        # Normalize embedding if using cosine similarity
        if self.metric == 'cosine':
            embedding = self._normalize(embedding)
        
        # Add to index
        embedding = embedding.reshape(1, -1).astype(np.float32)
        self.index.add(embedding)
        
        # Store metadata
        self.texture_paths.append(texture_path)
        self.texture_metadata.append(metadata or {})
    
    def add_embeddings_batch(
        self,
        embeddings: np.ndarray,
        texture_paths: List[Path],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Add multiple embeddings at once.
        
        Args:
            embeddings: Array of embeddings (N, embedding_dim)
            texture_paths: List of texture paths
            metadata_list: Optional list of metadata dicts
        """
        # Normalize if using cosine similarity
        if self.metric == 'cosine':
            embeddings = self._normalize_batch(embeddings)
        
        # Add to index
        embeddings = embeddings.astype(np.float32)
        self.index.add(embeddings)
        
        # Store metadata
        self.texture_paths.extend(texture_paths)
        if metadata_list:
            self.texture_metadata.extend(metadata_list)
        else:
            self.texture_metadata.extend([{} for _ in texture_paths])
        
        logger.info(f"Added {len(texture_paths)} embeddings to index")
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar textures.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Optional similarity threshold
            
        Returns:
            List of results with path, distance, and metadata
        """
        # Normalize if using cosine similarity
        if self.metric == 'cosine':
            query_embedding = self._normalize(query_embedding)
        
        # Search
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        distances, indices = self.index.search(query_embedding, k)
        
        # Build results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # No result found
                continue
            
            # Apply threshold if specified
            if threshold is not None and dist < threshold:
                continue
            
            result = {
                'texture_path': self.texture_paths[idx],
                'distance': float(dist),
                'similarity': float(dist) if self.metric == 'cosine' else 1.0 / (1.0 + float(dist)),
                'metadata': self.texture_metadata[idx]
            }
            results.append(result)
        
        return results
    
    def find_duplicates(
        self,
        similarity_threshold: float = 0.99
    ) -> List[List[Dict[str, Any]]]:
        """
        Find duplicate or near-duplicate textures.
        
        Args:
            similarity_threshold: Minimum similarity to consider as duplicate
            
        Returns:
            List of duplicate groups
        """
        duplicate_groups = []
        processed = set()
        
        # Search for each texture
        for i in range(len(self.texture_paths)):
            if i in processed:
                continue
            
            # Get embedding
            embedding = self.index.reconstruct(i)
            
            # Search for similar textures
            results = self.search(embedding, k=10, threshold=similarity_threshold)
            
            # Filter out self and create group
            group = []
            for result in results:
                # Find index of this result
                try:
                    idx = self.texture_paths.index(result['texture_path'])
                    if idx != i and idx not in processed:
                        group.append(result)
                        processed.add(idx)
                except ValueError:
                    pass
            
            if group:
                # Add original texture to group
                group.insert(0, {
                    'texture_path': self.texture_paths[i],
                    'distance': 1.0,
                    'similarity': 1.0,
                    'metadata': self.texture_metadata[i]
                })
                processed.add(i)
                duplicate_groups.append(group)
        
        logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups
    
    def find_variants(
        self,
        query_path: Path,
        similarity_range: Tuple[float, float] = (0.85, 0.99)
    ) -> List[Dict[str, Any]]:
        """
        Find variants of a texture (color swaps, brightness changes, etc.).
        
        Args:
            query_path: Path to query texture
            similarity_range: Min and max similarity for variants
            
        Returns:
            List of variant textures
        """
        # Find index of query texture
        try:
            idx = self.texture_paths.index(query_path)
        except ValueError:
            logger.error(f"Texture not found in index: {query_path}")
            return []
        
        # Get embedding
        embedding = self.index.reconstruct(idx)
        
        # Search for similar textures
        results = self.search(embedding, k=50)
        
        # Filter by similarity range
        variants = [
            r for r in results
            if similarity_range[0] <= r['similarity'] < similarity_range[1]
        ]
        
        return variants
    
    def cluster_similar(
        self,
        similarity_threshold: float = 0.9,
        max_cluster_size: int = 50
    ) -> List[List[Dict[str, Any]]]:
        """
        Auto-group similar textures into clusters.
        
        Args:
            similarity_threshold: Minimum similarity for same cluster
            max_cluster_size: Maximum number of textures per cluster
            
        Returns:
            List of clusters
        """
        clusters = []
        processed = set()
        
        for i in range(len(self.texture_paths)):
            if i in processed:
                continue
            
            # Get embedding
            embedding = self.index.reconstruct(i)
            
            # Search for similar textures
            results = self.search(embedding, k=max_cluster_size + 1, threshold=similarity_threshold)
            
            # Create cluster
            cluster = []
            for result in results:
                try:
                    idx = self.texture_paths.index(result['texture_path'])
                    if idx not in processed:
                        cluster.append(result)
                        processed.add(idx)
                except ValueError:
                    pass
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        logger.info(f"Created {len(clusters)} clusters")
        return clusters
    
    def search_by_text(
        self,
        text_embedding: np.ndarray,
        k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for textures matching a text description using CLIP embeddings.
        
        This method enables keyword-based texture search like "gun", "character face",
        "environmental texture", etc. The text_embedding should come from a CLIP 
        text encoder.
        
        Args:
            text_embedding: Text embedding from CLIP or similar model
            k: Number of results to return
            threshold: Optional similarity threshold
            
        Returns:
            List of matching textures sorted by relevance
            
        Example:
            # Using with CLIP model:
            from vision_models.clip_model import CLIPModel
            clip = CLIPModel()
            text_emb = clip.encode_text("gun texture")
            results = similarity_search.search_by_text(text_emb, k=20)
        """
        # Use the standard search method with text embedding
        return self.search(text_embedding, k=k, threshold=threshold)
    
    def save(self, path: Path):
        """Save index and metadata to disk."""
        # Save FAISS index
        index_path = path.with_suffix('.index')
        faiss.write_index(self.index, str(index_path))
        
        # Save metadata
        metadata_path = path.with_suffix('.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'texture_paths': self.texture_paths,
                'texture_metadata': self.texture_metadata,
                'embedding_dim': self.embedding_dim,
                'index_type': self.index_type,
                'metric': self.metric
            }, f)
        
        logger.info(f"Saved similarity search to {path}")
    
    def load(self, path: Path):
        """Load index and metadata from disk."""
        # Load FAISS index
        index_path = path.with_suffix('.index')
        self.index = faiss.read_index(str(index_path))
        
        # Move to GPU if requested
        if self.use_gpu and faiss.get_num_gpus() > 0:
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
        
        # Load metadata
        metadata_path = path.with_suffix('.pkl')
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
            self.texture_paths = data['texture_paths']
            self.texture_metadata = data['texture_metadata']
            self.embedding_dim = data['embedding_dim']
            self.index_type = data['index_type']
            self.metric = data['metric']
        
        logger.info(f"Loaded similarity search from {path}")
    
    @staticmethod
    def _normalize(embedding: np.ndarray) -> np.ndarray:
        """Normalize embedding to unit length."""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding
    
    @staticmethod
    def _normalize_batch(embeddings: np.ndarray) -> np.ndarray:
        """Normalize batch of embeddings."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms > 0, norms, 1.0)
        return embeddings / norms
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        return {
            'total_embeddings': len(self.texture_paths),
            'embedding_dim': self.embedding_dim,
            'index_type': self.index_type,
            'metric': self.metric,
            'is_trained': self.index.is_trained if hasattr(self.index, 'is_trained') else True
        }
