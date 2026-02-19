"""
Training System - User Feedback Learning
Learns from user corrections and enables incremental learning
Author: Dead On The Inside / JosephsDeadish
"""

import json
import logging

logger = logging.getLogger(__name__)
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.error("numpy not available - limited functionality")
    logger.error("Install with: pip install numpy")




class TrainingDataStore:
    """
    Persistent storage for training data and user corrections.
    
    Uses SQLite for efficient storage and querying.
    Thread-safe operations.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize training data store.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = Path.home() / ".ps2_texture_sorter" / "training_data.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.RLock()
        self._init_database()
        
        logger.info(f"Training data store initialized: {db_path}")
    
    def _init_database(self):
        """Initialize database schema."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # User corrections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    texture_path TEXT NOT NULL,
                    texture_hash TEXT,
                    original_category TEXT,
                    corrected_category TEXT NOT NULL,
                    confidence REAL,
                    timestamp TEXT NOT NULL,
                    image_width INTEGER,
                    image_height INTEGER,
                    image_channels INTEGER,
                    metadata TEXT
                )
            """)
            
            # Training history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_version TEXT,
                    training_date TEXT NOT NULL,
                    num_samples INTEGER,
                    accuracy REAL,
                    loss REAL,
                    notes TEXT
                )
            """)
            
            # Category statistics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS category_stats (
                    category TEXT PRIMARY KEY,
                    correction_count INTEGER DEFAULT 0,
                    last_updated TEXT
                )
            """)
            
            # Indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_texture_hash 
                ON user_corrections(texture_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_corrected_category 
                ON user_corrections(corrected_category)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON user_corrections(timestamp)
            """)
            
            conn.commit()
            conn.close()
    
    def add_correction(
        self,
        texture_path: str,
        corrected_category: str,
        original_category: Optional[str] = None,
        confidence: Optional[float] = None,
        texture_hash: Optional[str] = None,
        image_shape: Optional[Tuple[int, int, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Record a user correction.
        
        Args:
            texture_path: Path to texture file
            corrected_category: User's corrected category
            original_category: Original AI prediction
            confidence: Original prediction confidence
            texture_hash: Hash of texture for deduplication
            image_shape: (height, width, channels)
            metadata: Additional metadata
            
        Returns:
            Correction ID
        """
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            width, height, channels = None, None, None
            if image_shape:
                height, width, channels = image_shape
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO user_corrections 
                (texture_path, texture_hash, original_category, corrected_category,
                 confidence, timestamp, image_width, image_height, image_channels, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                texture_path, texture_hash, original_category, corrected_category,
                confidence, timestamp, width, height, channels, metadata_json
            ))
            
            correction_id = cursor.lastrowid
            
            # Update category statistics
            cursor.execute("""
                INSERT INTO category_stats (category, correction_count, last_updated)
                VALUES (?, 1, ?)
                ON CONFLICT(category) DO UPDATE SET
                    correction_count = correction_count + 1,
                    last_updated = ?
            """, (corrected_category, timestamp, timestamp))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded correction: {corrected_category} (ID: {correction_id})")
            return correction_id
    
    def get_corrections(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user corrections.
        
        Args:
            category: Filter by category (None for all)
            limit: Maximum number of records
            offset: Offset for pagination
            
        Returns:
            List of correction records
        """
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            query = "SELECT * FROM user_corrections"
            params = []
            
            if category:
                query += " WHERE corrected_category = ?"
                params.append(category)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                if record['metadata']:
                    record['metadata'] = json.loads(record['metadata'])
                results.append(record)
            
            conn.close()
            return results
    
    def get_category_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all categories.
        
        Returns:
            Dictionary mapping category to stats
        """
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM category_stats ORDER BY correction_count DESC")
            
            stats = {}
            for row in cursor.fetchall():
                category, count, last_updated = row
                stats[category] = {
                    'correction_count': count,
                    'last_updated': last_updated
                }
            
            conn.close()
            return stats
    
    def get_training_dataset(
        self,
        min_samples_per_category: int = 5
    ) -> Dict[str, List[str]]:
        """
        Build training dataset from corrections.
        
        Args:
            min_samples_per_category: Minimum samples needed per category
            
        Returns:
            Dictionary mapping category to list of texture paths
        """
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT corrected_category, COUNT(*) as count
                FROM user_corrections
                GROUP BY corrected_category
                HAVING count >= ?
            """, (min_samples_per_category,))
            
            valid_categories = [row[0] for row in cursor.fetchall()]
            
            dataset = {}
            for category in valid_categories:
                cursor.execute("""
                    SELECT texture_path FROM user_corrections
                    WHERE corrected_category = ?
                    ORDER BY timestamp DESC
                """, (category,))
                
                dataset[category] = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            logger.info(f"Training dataset: {len(dataset)} categories, "
                       f"{sum(len(v) for v in dataset.values())} samples")
            
            return dataset
    
    def export_to_json(self, output_path: Path) -> bool:
        """
        Export training data to JSON.
        
        Args:
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            corrections = self.get_corrections()
            stats = self.get_category_stats()
            
            data = {
                'export_date': datetime.now().isoformat(),
                'total_corrections': len(corrections),
                'corrections': corrections,
                'category_stats': stats
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported training data to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            return False
    
    def import_from_json(self, input_path: Path) -> bool:
        """
        Import training data from JSON.
        
        Args:
            input_path: Input file path
            
        Returns:
            True if successful
        """
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            corrections = data.get('corrections', [])
            
            for correction in corrections:
                self.add_correction(
                    texture_path=correction['texture_path'],
                    corrected_category=correction['corrected_category'],
                    original_category=correction.get('original_category'),
                    confidence=correction.get('confidence'),
                    texture_hash=correction.get('texture_hash'),
                    metadata=correction.get('metadata')
                )
            
            logger.info(f"Imported {len(corrections)} corrections from {input_path}")
            return True
        
        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            return False


class IncrementalLearner:
    """
    Incremental learning system that adapts from user corrections.
    
    Features:
    - Learn from user feedback
    - Update prediction weights
    - Category frequency tracking
    - Confidence adjustment
    """
    
    def __init__(self, data_store: Optional[TrainingDataStore] = None):
        """
        Initialize incremental learner.
        
        Args:
            data_store: Training data store instance
        """
        self.data_store = data_store or TrainingDataStore()
        self._lock = threading.RLock()
        
        # Category weights (learned from corrections)
        self.category_weights: Dict[str, float] = {}
        
        # Confidence adjustments per category
        self.confidence_adjustments: Dict[str, float] = {}
        
        self._update_weights()
        
        logger.info("IncrementalLearner initialized")
    
    def _update_weights(self):
        """Update category weights from correction history."""
        with self._lock:
            stats = self.data_store.get_category_stats()
            
            if not stats:
                return
            
            # Calculate weights based on correction frequency
            total_corrections = sum(s['correction_count'] for s in stats.values())
            
            for category, stat in stats.items():
                # Weight = sqrt(count) / sqrt(total) for balanced representation
                weight = np.sqrt(stat['correction_count']) / np.sqrt(total_corrections)
                self.category_weights[category] = weight
                
                # Higher correction count = more confident in this category
                self.confidence_adjustments[category] = min(0.2, stat['correction_count'] / 100)
            
            logger.debug(f"Updated weights for {len(self.category_weights)} categories")
    
    def record_correction(
        self,
        texture_path: str,
        corrected_category: str,
        original_predictions: List[Dict[str, float]],
        texture_hash: Optional[str] = None,
        image_shape: Optional[Tuple[int, int, int]] = None
    ) -> int:
        """
        Record user correction and update learning.
        
        Args:
            texture_path: Path to texture
            corrected_category: User's correct category
            original_predictions: Original AI predictions
            texture_hash: Texture hash
            image_shape: Image dimensions
            
        Returns:
            Correction ID
        """
        # Get original top prediction
        original_category = None
        confidence = None
        
        if original_predictions:
            original_category = original_predictions[0]['category']
            confidence = original_predictions[0]['confidence']
        
        # Store correction
        correction_id = self.data_store.add_correction(
            texture_path=texture_path,
            corrected_category=corrected_category,
            original_category=original_category,
            confidence=confidence,
            texture_hash=texture_hash,
            image_shape=image_shape
        )
        
        # Update weights
        self._update_weights()
        
        logger.info(f"Learned from correction: {original_category} → {corrected_category}")
        return correction_id
    
    def adjust_predictions(
        self,
        predictions: List[Dict[str, float]]
    ) -> List[Dict[str, float]]:
        """
        Adjust predictions based on learned weights.
        
        Args:
            predictions: Raw predictions from model
            
        Returns:
            Adjusted predictions
        """
        if not predictions:
            return predictions
        
        with self._lock:
            adjusted = []
            
            for pred in predictions:
                category = pred['category']
                confidence = pred['confidence']
                
                # Apply weight boost
                weight = self.category_weights.get(category, 1.0)
                confidence_adj = self.confidence_adjustments.get(category, 0.0)
                
                new_confidence = min(1.0, confidence * weight + confidence_adj)
                
                adjusted.append({
                    'category': category,
                    'confidence': new_confidence
                })
            
            # Re-sort by adjusted confidence
            adjusted.sort(key=lambda x: x['confidence'], reverse=True)
            
            return adjusted
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get learning statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = self.data_store.get_category_stats()
        
        return {
            'total_categories': len(stats),
            'total_corrections': sum(s['correction_count'] for s in stats.values()),
            'category_stats': stats,
            'learned_weights': self.category_weights,
            'confidence_adjustments': self.confidence_adjustments
        }
    
    def export_training_data(self, output_path: Path) -> bool:
        """
        Export training data for sharing or backup.
        
        Args:
            output_path: Output file path
            
        Returns:
            True if successful
        """
        return self.data_store.export_to_json(output_path)
    
    def import_training_data(self, input_path: Path) -> bool:
        """
        Import training data from another user or backup.
        
        Args:
            input_path: Input file path
            
        Returns:
            True if successful
        """
        success = self.data_store.import_from_json(input_path)
        if success:
            self._update_weights()
        return success
