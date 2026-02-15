"""
Test Suite for Interactive Panda Overlay System

Tests for:
- TransparentPandaOverlay
- WidgetDetector
- PandaInteractionBehavior
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from src.ui.transparent_panda_overlay import TransparentPandaOverlay
        print("✅ TransparentPandaOverlay imported")
    except Exception as e:
        print(f"❌ TransparentPandaOverlay import failed: {e}")
        return False
    
    try:
        from src.features.widget_detector import WidgetDetector
        print("✅ WidgetDetector imported")
    except Exception as e:
        print(f"❌ WidgetDetector import failed: {e}")
        return False
    
    try:
        from src.features.panda_interaction_behavior import PandaInteractionBehavior, InteractionBehavior
        print("✅ PandaInteractionBehavior imported")
    except Exception as e:
        print(f"❌ PandaInteractionBehavior import failed: {e}")
        return False
    
    return True


def test_pyqt_available():
    """Test if PyQt6 and OpenGL are available."""
    print("\nTesting PyQt6 and OpenGL availability...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QPushButton
        from PyQt6.QtCore import Qt
        from OpenGL.GL import glClear
        print("✅ PyQt6 and OpenGL available")
        return True
    except ImportError as e:
        print(f"❌ PyQt6 or OpenGL not available: {e}")
        print("Install with: pip install PyQt6 PyOpenGL PyOpenGL-accelerate")
        return False


def test_interaction_behaviors():
    """Test interaction behavior enum."""
    print("\nTesting interaction behaviors...")
    
    from src.features.panda_interaction_behavior import InteractionBehavior
    
    behaviors = [
        InteractionBehavior.BITE_BUTTON,
        InteractionBehavior.JUMP_ON_BUTTON,
        InteractionBehavior.TAP_SLIDER,
        InteractionBehavior.BITE_TAB,
        InteractionBehavior.PUSH_CHECKBOX,
        InteractionBehavior.SPIN_COMBOBOX,
        InteractionBehavior.MISCHIEVOUS_LOOK,
        InteractionBehavior.WALK_AROUND,
    ]
    
    print(f"✅ All {len(behaviors)} interaction behaviors defined:")
    for behavior in behaviors:
        print(f"   - {behavior.value}")
    
    return True


def test_widget_detector_class():
    """Test WidgetDetector class structure."""
    print("\nTesting WidgetDetector class...")
    
    from src.features.widget_detector import WidgetDetector
    
    # Check methods exist
    methods = [
        'get_widget_at_position',
        'get_all_widgets',
        'build_collision_map',
        'is_position_blocked',
        'get_widget_center',
        'get_widget_rect',
        'get_widgets_in_area',
        'get_nearest_widget',
        'get_widget_type_name',
        'get_widget_info',
    ]
    
    for method in methods:
        if hasattr(WidgetDetector, method):
            print(f"✅ WidgetDetector.{method} exists")
        else:
            print(f"❌ WidgetDetector.{method} missing")
            return False
    
    return True


def test_overlay_class():
    """Test TransparentPandaOverlay class structure."""
    print("\nTesting TransparentPandaOverlay class...")
    
    from src.ui.transparent_panda_overlay import TransparentPandaOverlay
    
    # Check methods exist
    methods = [
        'set_panda_position',
        'set_animation_state',
        'apply_squash_effect',
        'set_widget_below',
        'get_head_position',
        'get_mouth_position',
        'get_feet_positions',
    ]
    
    for method in methods:
        if hasattr(TransparentPandaOverlay, method):
            print(f"✅ TransparentPandaOverlay.{method} exists")
        else:
            print(f"❌ TransparentPandaOverlay.{method} missing")
            return False
    
    return True


def test_behavior_class():
    """Test PandaInteractionBehavior class structure."""
    print("\nTesting PandaInteractionBehavior class...")
    
    from src.features.panda_interaction_behavior import PandaInteractionBehavior
    
    # Check methods exist
    methods = [
        'update',
        'force_interact_with_widget',
        'set_mischievousness',
        'set_playfulness',
    ]
    
    for method in methods:
        if hasattr(PandaInteractionBehavior, method):
            print(f"✅ PandaInteractionBehavior.{method} exists")
        else:
            print(f"❌ PandaInteractionBehavior.{method} missing")
            return False
    
    return True


def test_convenience_functions():
    """Test convenience functions exist."""
    print("\nTesting convenience functions...")
    
    from src.ui.transparent_panda_overlay import create_transparent_overlay
    from src.features.widget_detector import create_widget_detector
    from src.features.panda_interaction_behavior import create_interaction_behavior
    
    print("✅ create_transparent_overlay exists")
    print("✅ create_widget_detector exists")
    print("✅ create_interaction_behavior exists")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("INTERACTIVE PANDA OVERLAY SYSTEM - TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("PyQt6/OpenGL Availability", test_pyqt_available),
        ("Interaction Behaviors", test_interaction_behaviors),
        ("WidgetDetector Class", test_widget_detector_class),
        ("TransparentPandaOverlay Class", test_overlay_class),
        ("PandaInteractionBehavior Class", test_behavior_class),
        ("Convenience Functions", test_convenience_functions),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print("✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Run integration example: python test_integration_example.py")
        print("2. Test with real Qt application")
        print("3. Adjust behavior parameters as needed")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        print("\nPlease check:")
        print("1. PyQt6 installed: pip install PyQt6")
        print("2. OpenGL installed: pip install PyOpenGL PyOpenGL-accelerate")
        print("3. All modules in correct locations")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
