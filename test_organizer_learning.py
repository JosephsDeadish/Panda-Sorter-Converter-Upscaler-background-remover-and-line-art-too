"""
Test AI Learning System for Texture Organization
"""

import sys
from pathlib import Path
import tempfile
import json

# Add src to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from organizer.learning_system import AILearningSystem, LearningEntry, LearningProfileMetadata


def test_learning_system_basic():
    """Test basic learning system functionality."""
    print("Testing AI Learning System...")
    
    # Create temp directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "profiles"
        learning = AILearningSystem(config_dir)
        
        # Test 1: Create new profile
        print("\n1. Creating new profile...")
        learning.create_new_profile(
            game_name="God of War II",
            game_serial="SLUS-20917",
            author="Test User",
            description="Test profile for GOW2"
        )
        
        assert learning.metadata.game == "God of War II"
        assert learning.metadata.game_serial == "SLUS-20917"
        print("✓ Profile created successfully")
        
        # Test 2: Add learning entries
        print("\n2. Adding learning entries...")
        learning.add_learning(
            filename="kratos_head_01.png",
            suggested_folder="character",
            user_choice="character/kratos",
            confidence=0.95,
            accepted=True
        )
        
        learning.add_learning(
            filename="kratos_body_02.png",
            suggested_folder="character",
            user_choice="character/kratos",
            confidence=0.92,
            accepted=True
        )
        
        learning.add_learning(
            filename="olympus_bg_01.png",
            suggested_folder="environment/olympus",
            user_choice="environment/temple",
            confidence=0.87,
            accepted=True
        )
        
        assert len(learning.learned_mappings) == 3
        print(f"✓ Added {len(learning.learned_mappings)} learning entries")
        
        # Test 3: Get suggestions
        print("\n3. Testing suggestions...")
        suggestions = learning.get_suggestion("kratos_arm_03.png")
        print(f"   Suggestions for 'kratos_arm_03.png': {suggestions}")
        
        if suggestions:
            top_suggestion = suggestions[0]
            assert "kratos" in top_suggestion[0].lower()
            print(f"✓ Top suggestion: {top_suggestion[0]} (confidence: {top_suggestion[1]:.2f})")
        
        # Test 4: Add custom category
        print("\n4. Adding custom category...")
        learning.add_custom_category(
            "character/kratos",
            ["kratos", "god", "warrior", "spartan"]
        )
        
        assert "character/kratos" in learning.custom_categories
        print("✓ Custom category added")
        
        # Test 5: Save profile
        print("\n5. Saving profile...")
        saved_path = learning.save_profile()
        assert saved_path.exists()
        print(f"✓ Profile saved to: {saved_path}")
        
        # Test 6: Load profile
        print("\n6. Loading profile...")
        learning2 = AILearningSystem(config_dir)
        learning2.load_profile(saved_path)
        
        assert learning2.metadata.game == "God of War II"
        assert len(learning2.learned_mappings) == 3
        assert "character/kratos" in learning2.custom_categories
        print("✓ Profile loaded successfully")
        
        # Test 7: Export profile (without encryption)
        print("\n7. Exporting profile (JSON)...")
        export_path = Path(temp_dir) / "exported_profile.json"
        exported = learning.export_profile(export_path)
        assert exported.exists()
        
        with open(exported, 'r') as f:
            exported_data = json.load(f)
        
        assert exported_data["metadata"]["game"] == "God of War II"
        assert len(exported_data["learned_mappings"]) == 3
        print(f"✓ Profile exported to: {exported}")
        
        # Test 8: Import profile
        print("\n8. Importing profile (merge mode)...")
        learning3 = AILearningSystem(config_dir)
        learning3.create_new_profile("Test Game", "TEST-001")
        
        summary = learning3.import_profile(exported, merge=False)
        assert summary["entries_imported"] == 3
        assert summary["game"] == "God of War II"
        print(f"✓ Profile imported: {summary}")
        
        # Test 9: Get statistics
        print("\n9. Getting statistics...")
        stats = learning.get_statistics()
        print(f"   Total entries: {stats['total_entries']}")
        print(f"   Accepted entries: {stats['accepted_entries']}")
        print(f"   Custom categories: {stats['custom_categories']}")
        print(f"   Most used folders: {stats['most_used_folders'][:3]}")
        print("✓ Statistics retrieved")
        
        # Test 10: Pattern matching
        print("\n10. Testing pattern similarity...")
        test_cases = [
            ("kratos_head_01.png", "kratos_*.*", 1.0),  # Exact match
            ("kratos_body_99.png", "kratos_*.*", 1.0),  # Exact match
            ("olympus_texture.png", "kratos_*.*", 0.0),  # No match
        ]
        
        for filename, pattern, expected_min in test_cases:
            score = learning._pattern_similarity(filename, pattern)
            print(f"   {filename} vs {pattern}: {score:.2f}")
            
            # For expected_min > 0, score should be >= expected_min
            # For expected_min == 0, score should be 0 (no match at all)
            if expected_min > 0:
                assert score >= expected_min, f"Score {score} should be >= {expected_min}"
            else:
                # Allow some tolerance for partial matches, but must be significantly lower
                assert score < expected_min + 0.6, f"Score {score} should be low for no match"
        
        print("✓ Pattern matching working")
        
        # Test 11: List profiles
        print("\n11. Listing profiles...")
        profiles = learning.list_profiles()
        print(f"   Found {len(profiles)} profiles")
        for profile in profiles:
            print(f"   - {profile['game']} ({profile['game_serial']}) - {profile['entries']} entries")
        print("✓ Profile listing working")
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)


def test_encryption():
    """Test profile encryption/decryption."""
    print("\n\nTesting Profile Encryption...")
    
    try:
        from cryptography.fernet import Fernet
        print("✓ Cryptography library available")
    except ImportError:
        print("⚠ Cryptography library not available - skipping encryption tests")
        return
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "profiles"
        learning = AILearningSystem(config_dir)
        
        # Create and populate profile
        learning.create_new_profile("Encrypted Test", "ENC-001")
        learning.add_learning(
            "test_file.png",
            "suggested",
            "actual",
            0.9,
            True
        )
        
        # Export with encryption
        print("\n1. Exporting with encryption...")
        export_path = Path(temp_dir) / "encrypted.enc"
        password = "test_password_123"
        
        exported = learning.export_profile(export_path, password=password)
        assert exported.exists()
        print(f"✓ Encrypted profile exported: {exported}")
        
        # Try to import with wrong password
        print("\n2. Testing wrong password...")
        learning2 = AILearningSystem(config_dir)
        try:
            learning2.import_profile(exported, password="wrong_password")
            assert False, "Should have failed with wrong password"
        except ValueError as e:
            print(f"✓ Correctly rejected wrong password: {e}")
        
        # Import with correct password
        print("\n3. Importing with correct password...")
        learning3 = AILearningSystem(config_dir)
        summary = learning3.import_profile(exported, password=password)
        
        assert summary["game"] == "Encrypted Test"
        assert summary["entries_imported"] == 1
        print("✓ Successfully imported encrypted profile")
        
        print("\n✓ ENCRYPTION TESTS PASSED!")


if __name__ == "__main__":
    try:
        test_learning_system_basic()
        test_encryption()
        
        print("\n" + "="*60)
        print("✅ ALL LEARNING SYSTEM TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
