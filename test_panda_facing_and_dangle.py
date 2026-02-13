#!/usr/bin/env python3
"""
Test panda facing direction, horizontal dangle, weapon positioning,
clothing perspective, and toss direction.
Validates:
- Dangle multiplier is applied based on grab part (head vs body)
- Horizontal dangle offsets are used in drawing code
- Weapon position adjusts for walking direction
- Clothing uses perspective scale for side/back views
- Toss sets facing direction
- Head dragging allows full dangly physics
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_dangle_multiplier_constants():
    """Test that dangle multiplier constants exist and have correct values."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'DANGLE_HEAD_MULTIPLIER'), \
            "PandaWidget should have DANGLE_HEAD_MULTIPLIER"
        assert hasattr(PandaWidget, 'DANGLE_BODY_MULTIPLIER'), \
            "PandaWidget should have DANGLE_BODY_MULTIPLIER"
        assert PandaWidget.DANGLE_HEAD_MULTIPLIER >= 0.8, \
            f"DANGLE_HEAD_MULTIPLIER should be >= 0.8 for full dangle (got {PandaWidget.DANGLE_HEAD_MULTIPLIER})"
        assert PandaWidget.DANGLE_BODY_MULTIPLIER <= 0.5, \
            f"DANGLE_BODY_MULTIPLIER should be <= 0.5 for minimal dangle (got {PandaWidget.DANGLE_BODY_MULTIPLIER})"
        assert PandaWidget.DANGLE_HEAD_MULTIPLIER > PandaWidget.DANGLE_BODY_MULTIPLIER, \
            "Head multiplier should be greater than body multiplier"
        print("✓ Dangle multiplier constants have correct values")
    except ImportError:
        print("⚠ Skipping dangle multiplier test (GUI not available)")


def test_dangle_multiplier_applied_in_physics():
    """Test that dangle multiplier is actually used in limb physics."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        
        # Check that dangle_mult is computed based on grabbed_part
        assert 'dangle_mult' in source, \
            "Dangle multiplier variable should be used in _draw_panda"
        assert 'DANGLE_HEAD_MULTIPLIER' in source, \
            "DANGLE_HEAD_MULTIPLIER should be referenced in physics"
        assert 'DANGLE_BODY_MULTIPLIER' in source, \
            "DANGLE_BODY_MULTIPLIER should be referenced in physics"
        
        # Check that multiplier is applied to dangle velocity calculations
        assert 'dangle_mult' in source and 'DANGLE_ARM_FACTOR' in source, \
            "Dangle multiplier should be applied to arm dangle factor"
        
        print("✓ Dangle multiplier is applied in limb physics")
    except ImportError:
        print("⚠ Skipping dangle multiplier physics test (GUI not available)")


def test_horizontal_dangle_applied_in_drawing():
    """Test that horizontal dangle offsets are applied to limb X positions."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        
        # Find the FRONT VIEW section
        front_view_start = source.find('# --- FRONT VIEW (default)')
        assert front_view_start > 0, "Should have FRONT VIEW section"
        front_view_section = source[front_view_start:]
        
        # Check that horizontal dangle is applied to leg X positions
        assert 'left_leg_dangle_h' in front_view_section, \
            "Left leg horizontal dangle should be computed"
        assert 'right_leg_dangle_h' in front_view_section, \
            "Right leg horizontal dangle should be computed"
        
        # Check that horizontal dangle is applied to arm X positions
        assert 'left_arm_dangle_h' in front_view_section, \
            "Left arm horizontal dangle should be computed"
        assert 'right_arm_dangle_h' in front_view_section, \
            "Right arm horizontal dangle should be computed"
        
        # Verify that leg_dangle_h modifies the X position
        assert '+ left_leg_dangle_h' in front_view_section or \
               '+left_leg_dangle_h' in front_view_section or \
               'left_leg_dangle_h' in front_view_section.split('left_leg_x')[1][:100], \
            "Left leg horizontal dangle should modify leg X position"
        
        print("✓ Horizontal dangle offsets are applied in drawing code")
    except ImportError:
        print("⚠ Skipping horizontal dangle drawing test (GUI not available)")


def test_weapon_facing_direction():
    """Test that weapon position adjusts based on walking direction."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)
        
        # Check that weapon drawing considers facing direction
        assert 'walking_left' in source or '_facing_direction' in source, \
            "Weapon drawing should consider walking/facing direction"
        assert 'walking_right' in source, \
            "Weapon drawing should handle walking_right"
        assert 'walking_up' in source, \
            "Weapon drawing should handle walking_up (back view)"
        
        print("✓ Weapon position adjusts for walking direction")
    except ImportError:
        print("⚠ Skipping weapon facing test (GUI not available)")


def test_clothing_perspective_scale():
    """Test that clothing uses perspective scale for side/back views."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)
        
        # Check that perspective scale is computed
        assert 'persp_sx' in source, \
            "Clothing should compute persp_sx for perspective scaling"
        
        # Check that side view uses compressed width
        assert 'walking_left' in source and 'walking_right' in source, \
            "Clothing should handle side views"
        
        # Check that persp_sx is used in clothing drawing
        assert source.count('persp_sx') > 5, \
            f"persp_sx should be used extensively in clothing drawing (found {source.count('persp_sx')} uses)"
        
        # Check that back view hides front-only details
        assert 'walking_up' in source, \
            "Clothing should handle back view"
        
        print("✓ Clothing uses perspective scale for different views")
    except ImportError:
        print("⚠ Skipping clothing perspective test (GUI not available)")


def test_toss_sets_facing_direction():
    """Test that toss physics sets the panda's facing direction."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._start_toss_physics)
        
        # Check that facing direction is set based on toss velocity
        assert '_facing_direction' in source, \
            "Toss should set _facing_direction"
        assert 'toss_velocity_x' in source or '_toss_velocity_x' in source, \
            "Toss should use velocity to determine facing"
        assert 'set_facing' in source, \
            "Toss should call set_facing on the panda character"
        
        print("✓ Toss sets facing direction based on velocity")
    except ImportError:
        print("⚠ Skipping toss facing test (GUI not available)")


def test_head_drag_full_dangle():
    """Test that head dragging gives full dangly effect to all limbs."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        
        # Find the dangle_mult assignment section
        mult_section_start = source.find('dangle_mult')
        assert mult_section_start > 0, "Should have dangle_mult variable"
        mult_section = source[mult_section_start:mult_section_start + 500]
        
        # Check head grab gives full multiplier
        assert "'head'" in mult_section, \
            "Head grab should be checked for dangle multiplier"
        assert 'DANGLE_HEAD_MULTIPLIER' in mult_section, \
            "Head grab should use DANGLE_HEAD_MULTIPLIER"
        
        # Check ear grabs also get full dangle
        assert "'left_ear'" in mult_section or 'ear' in mult_section, \
            "Ear grabs should also get full dangle multiplier"
        
        print("✓ Head/ear dragging gives full dangly effect")
    except ImportError:
        print("⚠ Skipping head drag dangle test (GUI not available)")


def test_facing_direction_state():
    """Test that facing direction state is properly initialized and used."""
    from src.features.panda_character import PandaCharacter, PandaFacing
    panda = PandaCharacter()
    
    # Test default facing
    assert panda.get_facing() == PandaFacing.FRONT, \
        f"Default facing should be FRONT, got {panda.get_facing()}"
    
    # Test setting facing
    panda.set_facing(PandaFacing.LEFT)
    assert panda.get_facing() == PandaFacing.LEFT, \
        f"Facing should be LEFT after setting, got {panda.get_facing()}"
    
    panda.set_facing(PandaFacing.BACK)
    assert panda.get_facing() == PandaFacing.BACK, \
        f"Facing should be BACK after setting, got {panda.get_facing()}"
    
    panda.set_facing(PandaFacing.RIGHT)
    assert panda.get_facing() == PandaFacing.RIGHT, \
        f"Facing should be RIGHT after setting, got {panda.get_facing()}"
    
    print("✓ Facing direction state works correctly")


def test_individual_limb_detection():
    """Test that all individual body parts are detected correctly."""
    from src.features.panda_character import PandaCharacter
    panda = PandaCharacter()
    
    # Test all specific body parts can be detected
    expected_parts = {
        (0.05, 0.05): 'left_ear',
        (0.05, 0.95): 'right_ear',
        (0.20, 0.35): 'left_eye',
        (0.20, 0.65): 'right_eye',
        (0.28, 0.5): 'nose',
        (0.10, 0.5): 'head',
        (0.4, 0.1): 'left_arm',
        (0.4, 0.9): 'right_arm',
        (0.4, 0.5): 'body',
        (0.65, 0.5): 'butt',
        (0.9, 0.3): 'left_leg',
        (0.9, 0.7): 'right_leg',
    }
    
    for (rel_y, rel_x), expected in expected_parts.items():
        actual = panda.get_body_part_at_position(rel_y, rel_x)
        assert actual == expected, \
            f"Position ({rel_y}, {rel_x}) expected '{expected}' got '{actual}'"
    
    print("✓ All individual body parts detected correctly")


def test_drag_response_per_body_part():
    """Test that each body part gives correct drag responses."""
    from src.features.panda_character import PandaCharacter
    panda = PandaCharacter()
    
    # Test that each body part has specific responses
    part_response_lists = {
        'head': panda.HEAD_DRAG_RESPONSES,
        'body': panda.BODY_DRAG_RESPONSES,
        'left_arm': panda.LEFT_ARM_DRAG_RESPONSES,
        'right_arm': panda.RIGHT_ARM_DRAG_RESPONSES,
        'left_leg': panda.LEFT_LEG_DRAG_RESPONSES,
        'right_leg': panda.RIGHT_LEG_DRAG_RESPONSES,
        'left_ear': panda.LEFT_EAR_DRAG_RESPONSES,
        'right_ear': panda.RIGHT_EAR_DRAG_RESPONSES,
    }
    
    for part, expected_list in part_response_lists.items():
        response = panda.on_drag(grabbed_part=part)
        assert response in expected_list, \
            f"Drag response for '{part}' should be from its specific list"
    
    print("✓ Each body part gives correct drag responses")


if __name__ == "__main__":
    print("\nTesting Panda Facing Direction, Dangle & Perspective...")
    print("-" * 50)
    
    tests = [
        test_dangle_multiplier_constants,
        test_dangle_multiplier_applied_in_physics,
        test_horizontal_dangle_applied_in_drawing,
        test_weapon_facing_direction,
        test_clothing_perspective_scale,
        test_toss_sets_facing_direction,
        test_head_drag_full_dangle,
        test_facing_direction_state,
        test_individual_limb_detection,
        test_drag_response_per_body_part,
    ]
    
    failed = False
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed = True
    
    print("-" * 50)
    if failed:
        print("❌ Some tests failed!")
        sys.exit(1)
    else:
        print("✅ All panda facing/dangle/perspective tests passed!")
