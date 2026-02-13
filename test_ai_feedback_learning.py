"""Tests for AI feedback learning system integration."""
import json
import os
import tempfile
from pathlib import Path
import pytest


class TestTrainingDataStore:
    """Test the training data store."""
    
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = Path(self.tmp) / "test_training.db"
    
    def teardown_method(self):
        if self.db_path.exists():
            os.unlink(self.db_path)
        os.rmdir(self.tmp)
    
    def test_add_correction_records_data(self):
        from src.ai.training import TrainingDataStore
        store = TrainingDataStore(db_path=self.db_path)
        cid = store.add_correction(
            texture_path="/test/texture.png",
            corrected_category="characters",
            original_category="environments",
            confidence=0.85
        )
        assert cid > 0
        corrections = store.get_corrections()
        assert len(corrections) == 1
        assert corrections[0]['corrected_category'] == "characters"
        assert corrections[0]['original_category'] == "environments"
    
    def test_category_stats_updated(self):
        from src.ai.training import TrainingDataStore
        store = TrainingDataStore(db_path=self.db_path)
        store.add_correction("/t1.png", "characters")
        store.add_correction("/t2.png", "characters")
        store.add_correction("/t3.png", "environments")
        stats = store.get_category_stats()
        assert stats["characters"]["correction_count"] == 2
        assert stats["environments"]["correction_count"] == 1
    
    def test_export_import_roundtrip(self):
        from src.ai.training import TrainingDataStore
        store = TrainingDataStore(db_path=self.db_path)
        store.add_correction("/t1.png", "characters", "environments", 0.7)
        store.add_correction("/t2.png", "ui_elements", "characters", 0.5)
        
        export_path = Path(self.tmp) / "export.json"
        assert store.export_to_json(export_path)
        
        with open(export_path) as f:
            data = json.load(f)
        assert data['total_corrections'] == 2
        assert len(data['corrections']) == 2
        
        # Import into new store
        db2_path = Path(self.tmp) / "test_training2.db"
        store2 = TrainingDataStore(db_path=db2_path)
        assert store2.import_from_json(export_path)
        corrections = store2.get_corrections()
        assert len(corrections) == 2
        os.unlink(db2_path)
        os.unlink(export_path)


class TestIncrementalLearner:
    """Test the incremental learner."""
    
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = Path(self.tmp) / "test_learning.db"
    
    def teardown_method(self):
        if self.db_path.exists():
            os.unlink(self.db_path)
        os.rmdir(self.tmp)
    
    def test_record_correction_updates_weights(self):
        from src.ai.training import TrainingDataStore, IncrementalLearner
        store = TrainingDataStore(db_path=self.db_path)
        learner = IncrementalLearner(data_store=store)
        
        learner.record_correction(
            texture_path="/test.png",
            corrected_category="characters",
            original_predictions=[{'category': 'environments', 'confidence': 0.9}]
        )
        
        stats = learner.get_learning_stats()
        assert stats['total_corrections'] == 1
        assert 'characters' in stats['learned_weights']
    
    def test_adjust_predictions_boosts_corrected(self):
        from src.ai.training import TrainingDataStore, IncrementalLearner
        store = TrainingDataStore(db_path=self.db_path)
        learner = IncrementalLearner(data_store=store)
        
        # Record many corrections for "characters" to build strong weight
        for i in range(50):
            learner.record_correction(
                texture_path=f"/test{i}.png",
                corrected_category="characters",
                original_predictions=[{'category': 'environments', 'confidence': 0.8}]
            )
        
        predictions = [
            {'category': 'environments', 'confidence': 0.6},
            {'category': 'characters', 'confidence': 0.5}
        ]
        adjusted = learner.adjust_predictions(predictions)
        # characters confidence should be increased due to corrections
        char_pred = next(p for p in adjusted if p['category'] == 'characters')
        assert char_pred['confidence'] > 0.5  # Should be boosted above original
    
    def test_export_import_preserves_learning(self):
        from src.ai.training import TrainingDataStore, IncrementalLearner
        store = TrainingDataStore(db_path=self.db_path)
        learner = IncrementalLearner(data_store=store)
        
        learner.record_correction("/t.png", "characters",
                                  [{'category': 'env', 'confidence': 0.5}])
        
        export_path = Path(self.tmp) / "learn_export.json"
        assert learner.export_training_data(export_path)
        
        db2 = Path(self.tmp) / "learn2.db"
        store2 = TrainingDataStore(db_path=db2)
        learner2 = IncrementalLearner(data_store=store2)
        assert learner2.import_training_data(export_path)
        
        stats = learner2.get_learning_stats()
        assert stats['total_corrections'] == 1
        assert 'characters' in stats['learned_weights']
        
        os.unlink(db2)
        os.unlink(export_path)
    
    def test_rejected_feedback_records(self):
        """Test that __rejected__ feedback is stored correctly."""
        from src.ai.training import TrainingDataStore, IncrementalLearner
        store = TrainingDataStore(db_path=self.db_path)
        learner = IncrementalLearner(data_store=store)
        
        learner.record_correction(
            texture_path="/test.png",
            corrected_category="__rejected__",
            original_predictions=[{'category': 'environments', 'confidence': 0.9}]
        )
        
        corrections = store.get_corrections()
        assert len(corrections) == 1
        assert corrections[0]['corrected_category'] == '__rejected__'
        assert corrections[0]['original_category'] == 'environments'


class TestImplicitLearning:
    """Test that implicit learning happens when user changes category."""
    
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = Path(self.tmp) / "test_implicit.db"
    
    def teardown_method(self):
        if self.db_path.exists():
            os.unlink(self.db_path)
        os.rmdir(self.tmp)
    
    def test_user_override_recorded_as_correction(self):
        """Simulate what happens in on_confirm when user changes category."""
        from src.ai.training import TrainingDataStore, IncrementalLearner
        store = TrainingDataStore(db_path=self.db_path)
        learner = IncrementalLearner(data_store=store)
        
        # Simulate: AI suggested "environments" but user chose "characters"
        ai_category = "environments"
        ai_confidence = 0.85
        user_chosen = "characters"
        
        if user_chosen != ai_category:
            learner.record_correction(
                texture_path="/some/texture.png",
                corrected_category=user_chosen,
                original_predictions=[{'category': ai_category,
                                       'confidence': ai_confidence}]
            )
        
        corrections = store.get_corrections()
        assert len(corrections) == 1
        assert corrections[0]['original_category'] == "environments"
        assert corrections[0]['corrected_category'] == "characters"
    
    def test_same_category_not_recorded(self):
        """If user confirms AI suggestion, no correction needed."""
        from src.ai.training import TrainingDataStore, IncrementalLearner
        store = TrainingDataStore(db_path=self.db_path)
        learner = IncrementalLearner(data_store=store)
        
        ai_category = "characters"
        user_chosen = "characters"
        
        if user_chosen != ai_category:
            learner.record_correction(
                texture_path="/some/texture.png",
                corrected_category=user_chosen,
                original_predictions=[{'category': ai_category, 'confidence': 0.9}]
            )
        
        corrections = store.get_corrections()
        assert len(corrections) == 0
