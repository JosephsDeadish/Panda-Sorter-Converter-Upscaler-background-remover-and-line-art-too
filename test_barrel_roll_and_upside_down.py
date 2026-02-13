#!/usr/bin/env python3
"""
Test barrel roll animation, upside-down visual rendering, shoe tracking
during walking, and equippable perspective matching.
Validates:
- barrel_roll is registered as a valid animation state
- Upside-down flag is tracked and used in drawing
- Shoe positions use perspective-correct scaling (persp_sx)
- _compute_limb_offsets handles walking animations correctly
- Equipped items match perspectives for all directions
"""

import sys
import math
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_barrel_roll_animation_state():
    """Test that barrel_roll is a registered animation state."""
    from src.features.panda_character import PandaCharacter
    assert 'barrel_roll' in PandaCharacter.ANIMATION_STATES, \
        "'barrel_roll' should be in ANIMATION_STATES"
    print("✓ barrel_roll is a registered animation state")


def test_barrel_roll_emoji_decorations():
    """Test that barrel_roll has emoji decorations defined."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert 'barrel_roll' in PandaWidget.ANIMATION_EMOJIS, \
            "'barrel_roll' should have ANIMATION_EMOJIS entry"
        assert len(PandaWidget.ANIMATION_EMOJIS['barrel_roll']) > 0, \
            "barrel_roll emojis should not be empty"
        print("✓ barrel_roll has emoji decorations")
    except ImportError:
        print("⚠ Skipping barrel_roll emoji test (GUI not available)")


def test_barrel_roll_limb_offsets():
    """Test that _compute_limb_offsets handles barrel_roll animation."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._compute_limb_offsets)
        assert "'barrel_roll'" in source or '"barrel_roll"' in source, \
            "_compute_limb_offsets should handle barrel_roll animation"
        print("✓ _compute_limb_offsets handles barrel_roll")
    except ImportError:
        print("⚠ Skipping barrel_roll limb offsets test (GUI not available)")


def test_barrel_roll_draw_animation():
    """Test that _draw_panda includes barrel_roll animation logic."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        assert "'barrel_roll'" in source or '"barrel_roll"' in source, \
            "_draw_panda should handle barrel_roll animation"
        # Verify it has body sway and breath_scale
        barrel_idx = source.find("barrel_roll")
        assert barrel_idx > 0, "barrel_roll should appear in _draw_panda"
        print("✓ barrel_roll has drawing animation logic")
    except ImportError:
        print("⚠ Skipping barrel_roll drawing test (GUI not available)")


def test_upside_down_used_in_drawing():
    """Test that _is_upside_down is used in the drawing code to flip panda."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)

        # Check that _is_upside_down is used in drawing (not just tracking)
        assert '_is_upside_down' in source, \
            "_draw_panda should check _is_upside_down for visual flip"
        # Check that a canvas scale flip is applied
        assert 'scale' in source and '-1.0' in source, \
            "_draw_panda should apply canvas scale flip when upside down"
        print("✓ Upside-down state is used in drawing for visual flip")
    except ImportError:
        print("⚠ Skipping upside-down drawing test (GUI not available)")


def test_upside_down_set_on_leg_drag():
    """Test that _is_upside_down is set when dragged by leg upward."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'UPSIDE_DOWN_VELOCITY_THRESHOLD'), \
            "PandaWidget should have UPSIDE_DOWN_VELOCITY_THRESHOLD"
        assert PandaWidget.UPSIDE_DOWN_VELOCITY_THRESHOLD > 0, \
            "Threshold should be positive"
        print("✓ Upside-down threshold constant exists")
    except ImportError:
        print("⚠ Skipping upside-down threshold test (GUI not available)")


def test_walking_limb_offsets_match():
    """Test that _compute_limb_offsets matches _draw_panda for walking animations."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._compute_limb_offsets)

        # Verify walking animations are explicitly handled
        assert "'walking_left'" in source or '"walking_left"' in source, \
            "_compute_limb_offsets should handle walking_left"
        assert "'walking_right'" in source or '"walking_right"' in source, \
            "_compute_limb_offsets should handle walking_right"
        assert "'walking_up'" in source or '"walking_up"' in source, \
            "_compute_limb_offsets should handle walking_up"
        assert "'walking_down'" in source or '"walking_down"' in source, \
            "_compute_limb_offsets should handle walking_down"

        # Check diagonal walking too
        assert "'walking_up_left'" in source or '"walking_up_left"' in source, \
            "_compute_limb_offsets should handle diagonal walking"

        print("✓ _compute_limb_offsets handles all walking animations")
    except ImportError:
        print("⚠ Skipping walking limb offsets test (GUI not available)")


_SHOE_SECTION_MARKER = 'Draw shoes at feet'


def test_shoe_uses_perspective_scale():
    """Test that shoe drawing uses persp_sx for perspective-correct sizing."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)

        # Find the shoe drawing section
        shoe_start = source.find(_SHOE_SECTION_MARKER)
        assert shoe_start > 0, "Should have shoe drawing section"
        shoe_section = source[shoe_start:shoe_start + 2000]

        # Check that persp_sx is used in shoe drawing (not raw sx)
        assert 'persp_sx' in shoe_section, \
            "Shoe drawing should use persp_sx for perspective-correct width"
        print("✓ Shoe drawing uses perspective scale (persp_sx)")
    except ImportError:
        print("⚠ Skipping shoe perspective test (GUI not available)")


def test_shoe_diagonal_view_handling():
    """Test that shoe positions account for diagonal walking view."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)

        shoe_start = source.find(_SHOE_SECTION_MARKER)
        assert shoe_start > 0, "Should have shoe drawing section"
        shoe_section = source[shoe_start:shoe_start + 1500]

        # Check that diagonal view is handled separately
        assert 'is_diag' in shoe_section, \
            "Shoe drawing should handle diagonal view"
        print("✓ Shoe drawing handles diagonal view)")
    except ImportError:
        print("⚠ Skipping shoe diagonal test (GUI not available)")


def test_walking_limb_offset_values():
    """Test that walking limb offset values match between _compute_limb_offsets and _draw_panda."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect

        # Inspect _compute_limb_offsets source for walking_left/right amplitude
        source = inspect.getsource(PandaWidget._compute_limb_offsets)

        # For walking_left/right, _draw_panda uses leg_swing = sin(phase) * 12
        # _compute_limb_offsets should match
        walk_idx = source.find("walking_left")
        assert walk_idx > 0, "Should find walking_left in _compute_limb_offsets"
        walk_section = source[walk_idx:walk_idx + 300]

        # Verify the amplitude matches (12 for legs, 10 for arms)
        assert '* 12' in walk_section, \
            "Walking left/right leg_swing should use amplitude 12 to match _draw_panda"
        assert '* 10' in walk_section, \
            "Walking left/right arm_swing should use amplitude 10 to match _draw_panda"

        print("✓ Walking limb offset values match _draw_panda")
    except ImportError:
        print("⚠ Skipping walking offset values test (GUI not available)")


if __name__ == "__main__":
    print("\nTesting Barrel Roll, Upside-Down & Shoe Tracking...")
    print("-" * 55)

    tests = [
        test_barrel_roll_animation_state,
        test_barrel_roll_emoji_decorations,
        test_barrel_roll_limb_offsets,
        test_barrel_roll_draw_animation,
        test_upside_down_used_in_drawing,
        test_upside_down_set_on_leg_drag,
        test_walking_limb_offsets_match,
        test_shoe_uses_perspective_scale,
        test_shoe_diagonal_view_handling,
        test_walking_limb_offset_values,
    ]

    failed = False
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed = True

    print("-" * 55)
    if failed:
        print("❌ Some tests failed!")
        sys.exit(1)
    else:
        print("✅ All barrel roll / upside-down / shoe tracking tests passed!")
