"""
Similarity Search Module
FAISS-based vector database for texture similarity search
Author: Dead On The Inside / JosephsDeadish
"""

from .similarity_search import SimilaritySearch
from .embedding_store import EmbeddingStore
from .duplicate_detector import DuplicateDetector

__all__ = [
    'SimilaritySearch',
    'EmbeddingStore',
    'DuplicateDetector'
]
