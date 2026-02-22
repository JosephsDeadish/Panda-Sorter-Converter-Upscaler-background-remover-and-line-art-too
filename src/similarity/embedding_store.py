"""
Embedding Store
Persistent storage for texture embeddings
Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Dict, Any, List, Optional
try:
    import numpy as np
    HAS_NUMPY = True
except (ImportError, OSError):
    HAS_NUMPY = False
    logger.error("numpy not available - limited functionality")
    logger.error("Install with: pip install numpy")
import sqlite3
import pickle



class EmbeddingStore:
    """
    Persistent storage for texture embeddings using SQLite.
    
    Features:
    - Store embeddings with metadata
    - Query by texture path
    - Batch operations
    - Efficient serialization
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize embedding store.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self._create_tables()
        logger.info(f"EmbeddingStore initialized: {db_path}")
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texture_path TEXT UNIQUE NOT NULL,
                embedding BLOB NOT NULL,
                embedding_dim INTEGER NOT NULL,
                model_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                texture_path TEXT PRIMARY KEY,
                metadata BLOB,
                FOREIGN KEY (texture_path) REFERENCES embeddings(texture_path)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_texture_path ON embeddings(texture_path)')
        self.conn.commit()
    
    def store(
        self,
        texture_path: Path,
        embedding: np.ndarray,
        model_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store an embedding."""
        cursor = self.conn.cursor()
        embedding_blob = pickle.dumps(embedding)
        
        cursor.execute('''
            INSERT OR REPLACE INTO embeddings (texture_path, embedding, embedding_dim, model_name)
            VALUES (?, ?, ?, ?)
        ''', (str(texture_path), embedding_blob, embedding.shape[0], model_name))
        
        if metadata:
            metadata_blob = pickle.dumps(metadata)
            cursor.execute('''
                INSERT OR REPLACE INTO metadata (texture_path, metadata)
                VALUES (?, ?)
            ''', (str(texture_path), metadata_blob))
        
        self.conn.commit()
    
    def get(self, texture_path: Path) -> Optional[Dict[str, Any]]:
        """Retrieve an embedding."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT embedding, embedding_dim, model_name, created_at
            FROM embeddings WHERE texture_path = ?
        ''', (str(texture_path),))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        embedding = pickle.loads(row[0])
        
        # Get metadata
        cursor.execute('SELECT metadata FROM metadata WHERE texture_path = ?', (str(texture_path),))
        metadata_row = cursor.fetchone()
        metadata = pickle.loads(metadata_row[0]) if metadata_row else None
        
        return {
            'embedding': embedding,
            'embedding_dim': row[1],
            'model_name': row[2],
            'created_at': row[3],
            'metadata': metadata
        }
    
    def get_all(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all embeddings, optionally filtered by model."""
        cursor = self.conn.cursor()
        
        if model_name:
            cursor.execute('''
                SELECT texture_path, embedding, embedding_dim, model_name
                FROM embeddings WHERE model_name = ?
            ''', (model_name,))
        else:
            cursor.execute('''
                SELECT texture_path, embedding, embedding_dim, model_name
                FROM embeddings
            ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'texture_path': Path(row[0]),
                'embedding': pickle.loads(row[1]),
                'embedding_dim': row[2],
                'model_name': row[3]
            })
        
        return results
    
    def close(self):
        """Close database connection."""
        self.conn.close()
