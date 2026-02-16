"""
Integration test for AI Organizer Panel
Tests that all components work together correctly
"""

import sys
from pathlib import Path
import tempfile

# Add src to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from organizer.learning_system import AILearningSystem
        print("✓ AILearningSystem imported")
    except ImportError as e:
        print(f"✗ AILearningSystem import failed: {e}")
        return False
    
    try:
        from organizer import OrganizationEngine, ORGANIZATION_STYLES
        print("✓ OrganizationEngine imported")
    except ImportError as e:
        print(f"✗ OrganizationEngine import failed: {e}")
        return False
    
    try:
        from features.game_identifier import GameIdentifier
        print("✓ GameIdentifier imported")
    except ImportError as e:
        print(f"✗ GameIdentifier import failed: {e}")
        return False
    
    try:
        from features.profile_manager import ProfileManager
        print("✓ ProfileManager imported")
    except ImportError as e:
        print(f"✗ ProfileManager import failed: {e}")
        return False
    
    # Vision models (optional, may not be available)
    try:
        from vision_models.clip_model import CLIPModel
        print("✓ CLIPModel imported (optional)")
    except ImportError:
        print("⚠ CLIPModel not available (optional dependency)")
    
    try:
        from vision_models.dinov2_model import DINOv2Model
        print("✓ DINOv2Model imported (optional)")
    except ImportError:
        print("⚠ DINOv2Model not available (optional dependency)")
    
    return True


def test_game_identifier_integration():
    """Test GameIdentifier with learning system."""
    print("\nTesting GameIdentifier integration...")
    
    from features.game_identifier import GameIdentifier
    from organizer.learning_system import AILearningSystem
    
    game_id = GameIdentifier()
    
    # Test with various path formats
    test_paths = [
        "/textures/SLUS-20917/character",  # God of War II
        "/PCSX2/SCUS-97268/ui",  # GTA San Andreas
        "/roms/SLUS-21122.iso",  # Final Fantasy XII
        "/games/no_serial_here/textures",  # No serial
    ]
    
    for path in test_paths:
        result = game_id.identify_game(Path(path))
        if result and result.confidence > 0.5:
            print(f"✓ Detected: {path}")
            print(f"  Game: {result.title} ({result.serial})")
            print(f"  Confidence: {result.confidence:.0%}")
            
            # Test creating profile for detected game
            with tempfile.TemporaryDirectory() as temp_dir:
                learning = AILearningSystem(Path(temp_dir))
                learning.create_new_profile(
                    game_name=result.title,
                    game_serial=result.serial
                )
                print(f"  ✓ Created learning profile for {result.title}")
        else:
            print(f"⚠ No game detected: {path}")
    
    return True


def test_organization_styles():
    """Test that organization styles are available."""
    print("\nTesting organization styles...")
    
    from organizer import ORGANIZATION_STYLES
    
    expected_styles = [
        'minimalist', 'flat', 'neopets', 'sims', 'game_area',
        'asset_pipeline', 'modular', 'maximum_detail', 'custom'
    ]
    
    for style_id in expected_styles:
        if style_id in ORGANIZATION_STYLES:
            style_class = ORGANIZATION_STYLES[style_id]
            style = style_class()
            print(f"✓ {style_id}: {style.get_name()}")
        else:
            print(f"✗ Missing style: {style_id}")
            return False
    
    return True


def test_learning_with_game_context():
    """Test learning system with game-specific context."""
    print("\nTesting learning with game context...")
    
    from organizer.learning_system import AILearningSystem
    
    with tempfile.TemporaryDirectory() as temp_dir:
        learning = AILearningSystem(Path(temp_dir))
        
        # Create profile for God of War II
        learning.create_new_profile(
            game_name="God of War II",
            game_serial="SLUS-20917",
            author="Test Suite"
        )
        
        # Add GOW-specific learning
        gow_textures = [
            ("kratos_head.png", "character/kratos"),
            ("kratos_body.png", "character/kratos"),
            ("zeus_face.png", "character/gods"),
            ("olympus_bg.png", "environment/olympus"),
            ("blade_chaos.png", "weapon/blades"),
        ]
        
        for filename, folder in gow_textures:
            learning.add_learning(
                filename=filename,
                suggested_folder=folder.split('/')[0],
                user_choice=folder,
                confidence=0.9,
                accepted=True
            )
        
        print(f"✓ Added {len(gow_textures)} GOW-specific patterns")
        
        # Test suggestions
        test_files = [
            ("kratos_arm.png", "character/kratos"),
            ("zeus_lightning.png", "character/gods"),
            ("olympus_temple.png", "environment/olympus"),
        ]
        
        for filename, expected_folder in test_files:
            suggestions = learning.get_suggestion(filename)
            if suggestions:
                top_suggestion = suggestions[0][0]
                print(f"✓ {filename} → {top_suggestion}")
                
                # Check if suggestion is reasonable
                if any(part in top_suggestion.lower() for part in expected_folder.lower().split('/')):
                    print(f"  ✓ Suggestion matches expected category")
                else:
                    print(f"  ⚠ Suggestion differs from expected: {expected_folder}")
            else:
                print(f"⚠ No suggestions for {filename}")
        
        # Save and reload
        profile_path = learning.save_profile()
        print(f"✓ Saved profile: {profile_path}")
        
        learning2 = AILearningSystem(Path(temp_dir))
        learning2.load_profile(profile_path)
        
        assert learning2.metadata.game == "God of War II"
        assert len(learning2.learned_mappings) == len(gow_textures)
        print("✓ Profile successfully saved and loaded")
    
    return True


def test_profile_manager_integration():
    """Test ProfileManager with learning system."""
    print("\nTesting ProfileManager integration...")
    
    from features.profile_manager import ProfileManager
    from organizer.learning_system import AILearningSystem
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create profile manager
        pm = ProfileManager(Path(temp_dir))
        
        # Create organization profile
        profile_data = pm.create_profile(
            name="Test GOW Profile",
            game_name="God of War II",
            game_serial="SLUS-20917"
        )
        
        print(f"✓ Created profile: {profile_data.name}")
        
        # Create learning system with same game
        learning_dir = Path(temp_dir) / "learning"
        learning = AILearningSystem(learning_dir)
        learning.create_new_profile(
            game_name="God of War II",
            game_serial="SLUS-20917"
        )
        
        # Verify they can work together
        assert profile_data.game_serial == learning.metadata.game_serial
        print("✓ ProfileManager and LearningSystem compatible")
    
    return True


def main():
    """Run all integration tests."""
    print("="*60)
    print("AI ORGANIZER INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        ("Module Imports", test_imports),
        ("GameIdentifier Integration", test_game_identifier_integration),
        ("Organization Styles", test_organization_styles),
        ("Learning with Game Context", test_learning_with_game_context),
        ("ProfileManager Integration", test_profile_manager_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"{'='*60}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"\n✓ {test_name} PASSED")
            else:
                print(f"\n✗ {test_name} FAILED")
        except Exception as e:
            print(f"\n✗ {test_name} FAILED WITH EXCEPTION:")
            print(f"   {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
