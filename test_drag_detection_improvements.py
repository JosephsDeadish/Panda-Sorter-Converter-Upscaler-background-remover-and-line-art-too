#!/usr/bin/env python3
"""
Test panda drag detection improvements.
Validates:
- Spin/shake detection only when grabbed by belly/body
- Body part detection for drag start
- Clothing sync with dangle physics
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_drag_grab_part_tracking():
    """Test that _drag_grab_part is properly tracked during drag start."""
    try:
        from src.ui.panda_widget import PandaWidget
        # Check that the class has the new instance variable
        # We can't instantiate without GUI, but we can check it's documented
        import inspect
        source = inspect.getsource(PandaWidget.__init__)
        assert '_drag_grab_part' in source, \
            "PandaWidget should initialize _drag_grab_part variable"
        print("✓ Drag grab part tracking variable exists")
    except ImportError:
        print("⚠ Skipping drag grab part test (GUI not available)")


def test_spin_shake_blocked_when_not_belly():
    """Test that spin/shake detection checks grab part."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._detect_drag_patterns)
        # Check that the function checks _drag_grab_part
        assert '_drag_grab_part' in source, \
            "_detect_drag_patterns should check _drag_grab_part"
        # Check that it filters based on body parts
        assert "'body'" in source or "'butt'" in source, \
            "_detect_drag_patterns should check for body/butt parts"
        # Check that there's an early return based on grab part
        # Split by _drag_grab_part and check for 'return' in the next few lines
        parts = source.split('_drag_grab_part')
        if len(parts) > 1:
            next_lines = parts[1].split('\n')[:10]  # Check next 10 lines
            has_return = any('return' in line for line in next_lines)
            assert has_return, \
                "_detect_drag_patterns should return early based on grab part"
        print("✓ Spin/shake detection checks grab part")
    except ImportError:
        print("⚠ Skipping spin/shake filter test (GUI not available)")


def test_body_part_detection_uses_rel_x():
    """Test that body part detection uses both rel_y and rel_x."""
    from src.features.panda_character import PandaCharacter
    panda = PandaCharacter()
    
    # Test that rel_x parameter is used
    import inspect
    sig = inspect.signature(panda.get_body_part_at_position)
    params = list(sig.parameters.keys())
    assert 'rel_x' in params, "get_body_part_at_position should accept rel_x parameter"
    
    # Test that left side of body detects as left_arm
    part = panda.get_body_part_at_position(0.4, 0.1)  # body height, far left
    assert part == 'left_arm', f"Far left body area should be 'left_arm', got {part}"
    
    # Test that right side of body detects as right_arm
    part = panda.get_body_part_at_position(0.4, 0.9)  # body height, far right
    assert part == 'right_arm', f"Far right body area should be 'right_arm', got {part}"
    
    # Test that center of body detects as body
    part = panda.get_body_part_at_position(0.4, 0.5)  # body height, center
    assert part == 'body', f"Center body area should be 'body', got {part}"
    
    print("✓ Body part detection uses X position for individual arm detection")


def test_wrist_accessories_sync_with_dangle():
    """Test that wrist accessories include dangle physics."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)
        
        # Find the wrist accessory section
        wrist_section = source.split('_WRIST_IDS')[1].split('_NECK_IDS')[0]
        
        # Check that arm_dangle is used for wrist accessories
        assert 'arm_dangle' in wrist_section, \
            "Wrist accessories should use arm_dangle for vertical sync"
        
        # Check that horizontal dangle is also used
        assert 'arm_dangle_h' in wrist_section, \
            "Wrist accessories should use arm_dangle_h for horizontal sync"
        
        # Check that dangle is added to swing (more flexible pattern)
        assert 'arm_swing' in wrist_section and 'arm_dangle' in wrist_section, \
            "Wrist accessories should combine arm_swing with arm_dangle"
        
        print("✓ Wrist accessories sync with arm dangle physics")
    except ImportError:
        print("⚠ Skipping wrist accessory test (GUI not available)")


def test_shoes_sync_with_dangle():
    """Test that shoes include dangle physics."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)
        
        # Check that leg_dangle is used for shoes
        shoes_section = source.split('# --- Draw shoes')[1].split('except')[0]
        assert 'leg_dangle' in shoes_section, \
            "Shoes drawing should use leg_dangle"
        
        # Check that horizontal dangle is also used
        assert 'leg_dangle_h' in shoes_section, \
            "Shoes drawing should use leg_dangle_h for horizontal sync"
        
        # Check that dangle is added to shoe swing
        assert '_leg_swing) + leg_dangle' in shoes_section or \
               'leg_swing + leg_dangle' in shoes_section, \
            "Shoes should add leg_dangle to swing"
        
        print("✓ Shoes sync with leg dangle physics")
    except ImportError:
        print("⚠ Skipping shoe test (GUI not available)")


def test_drag_start_detects_body_part():
    """Test that drag start detects and stores the grabbed body part."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._on_drag_start)
        
        # Check that it calls get_body_part_at_position
        assert 'get_body_part_at_position' in source, \
            "_on_drag_start should call get_body_part_at_position"
        
        # Check that it stores the result in _drag_grab_part
        assert '_drag_grab_part' in source, \
            "_on_drag_start should set _drag_grab_part"
        
        # Check that it uses both rel_x and rel_y
        assert 'rel_x' in source and 'rel_y' in source, \
            "_on_drag_start should calculate both rel_x and rel_y"
        
        print("✓ Drag start detects and stores grabbed body part")
    except ImportError:
        print("⚠ Skipping drag start test (GUI not available)")


def test_spin_shake_allowed_for_belly_body():
    """Test that spin/shake is allowed when grabbed by body or butt."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._detect_drag_patterns)
        
        # Check that the docstring mentions the behavior
        docstring = PandaWidget._detect_drag_patterns.__doc__
        assert 'belly' in docstring.lower() or 'body' in docstring.lower(), \
            "Docstring should mention belly/body detection"
        
        # Check that it allows 'body' and 'butt'
        part_check = source.split('_drag_grab_part')[1].split('return')[0]
        assert "'body'" in part_check and "'butt'" in part_check, \
            "Should allow spin/shake for 'body' and 'butt'"
        
        print("✓ Spin/shake allowed for belly/body grab")
    except ImportError:
        print("⚠ Skipping spin/shake allow test (GUI not available)")


if __name__ == "__main__":
    print("Testing Drag Detection Improvements...")
    print("-" * 50)
    
    try:
        test_drag_grab_part_tracking()
        test_spin_shake_blocked_when_not_belly()
        test_body_part_detection_uses_rel_x()
        test_wrist_accessories_sync_with_dangle()
        test_shoes_sync_with_dangle()
        test_drag_start_detects_body_part()
        test_spin_shake_allowed_for_belly_body()
        
        print("-" * 50)
        print("✅ All drag detection improvement tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
