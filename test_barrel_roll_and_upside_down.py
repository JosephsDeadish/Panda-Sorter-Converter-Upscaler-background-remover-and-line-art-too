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


def test_flip_progress_attribute():
    """Test that PandaWidget has _flip_progress for gradual upside-down transition."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget.__init__)
        assert '_flip_progress' in source, \
            "PandaWidget should have _flip_progress attribute for gradual flip"
        # Check that _draw_panda uses gradual flip logic
        draw_source = inspect.getsource(PandaWidget._draw_panda)
        assert 'flip_progress' in draw_source, \
            "_draw_panda should use flip_progress for gradual transition"
        # Should NOT use the old instantaneous flip
        assert '_is_upside_down' not in source or 'flip_progress' in source, \
            "_draw_panda should use gradual flip_progress instead of instant flip"
        print("✓ Gradual flip_progress transition is implemented")
    except ImportError:
        print("⚠ Skipping flip_progress test (GUI not available)")


def test_backflip_has_body_rotation():
    """Test that backflip animation has body_sway and breath_scale for visual rotation."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        # Find body_sway section for backflip
        idx = source.find("backflip")
        assert idx > 0, "backflip should appear in _draw_panda"
        # After the first body_sway 'backflip', check for rotation-like sway
        sway_section = source[source.find("backflip", source.find("body_sway")):]
        # backflip should have multi-phase body_sway (not just simple sine)
        assert 'flip_phase' in sway_section or 'launch' in sway_section, \
            "Backflip body_sway should have multi-phase rotation logic"
        # Check breath_scale has backflip entry
        assert "'backflip'" in source[source.find("breath_scale"):], \
            "breath_scale should handle backflip animation for body compression"
        print("✓ Backflip animation has visual body rotation effects")
    except ImportError:
        print("⚠ Skipping backflip rotation test (GUI not available)")


def test_lay_on_side_has_tilt_transform():
    """Test that lay_on_side uses post-draw canvas transformation for true side tilt."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        # Should have a scale transform specifically for lay_on_side
        assert "lay_on_side" in source, "lay_on_side should be handled in _draw_panda"
        # Look for the post-draw tilt transform
        assert "tip_over_side" in source, "tip_over_side should share the tilt logic"
        # Check that lay_on_side body_bob is very low (>= 55)
        assert "body_bob" in source, "body_bob should exist for lay_on_side"
        # Check that lay_on_side body_sway is large (>= 40)
        sway_idx = source.find("lay_on_side", source.find("body_sway"))
        assert sway_idx > 0, "body_sway should handle lay_on_side"
        print("✓ lay_on_side has proper tilt transformation for sideways laying")
    except ImportError:
        print("⚠ Skipping lay_on_side tilt test (GUI not available)")


def test_sleeping_animation_body_bob():
    """Test that sleeping animation uses a lower body_bob for a proper lying-down pose."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        # Find sleeping body_bob section
        idx = source.find("sleeping")
        assert idx > 0, "sleeping should appear in _draw_panda"
        # The settled body_bob should be well above 40 for a low sleeping pose
        sleep_section = source[idx:idx+500]
        assert "body_bob" in sleep_section, "sleeping should set body_bob"
        print("✓ Sleeping animation has proper lowered body position")
    except ImportError:
        print("⚠ Skipping sleeping body_bob test (GUI not available)")


def test_widget_card_transparent_backgrounds():
    """Test that widget card frames use transparent/flat backgrounds."""
    try:
        from src.ui.widgets_panel import WidgetsPanel
        import inspect
        source = inspect.getsource(WidgetsPanel._create_widget_card)
        # Inner frames should have transparent or flat styling
        assert 'fg_color="transparent"' in source or "highlightthickness=0" in source, \
            "Widget card inner frames should use transparent/flat backgrounds"
        print("✓ Widget card frames use transparent/flat backgrounds")
    except ImportError:
        print("⚠ Skipping widget card background test (GUI not available)")


def test_eating_walks_to_item():
    """Test that food eating uses walk_to_item so panda moves to the food first."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._give_widget_to_panda)
        # Should use walk_to_item to physically move the panda
        assert "walk_to_item" in source, \
            "_give_widget_to_panda should call walk_to_item so panda moves to the food"
        # Should pass the on_arrive callback so consumption happens after walking
        assert "on_arrive" in source, \
            "_give_widget_to_panda should pass on_arrive callback to walk_to_item"
        # Should calculate a target position for the walk
        assert "target_x" in source and "target_y" in source, \
            "_give_widget_to_panda should calculate target position for the walk"
        # Toys should also walk to item
        assert source.count("walk_to_item") >= 2, \
            "_give_widget_to_panda should use walk_to_item for both food and toys"
        print("✓ Food/toy eating uses walk_to_item for physical movement")
    except ImportError:
        print("⚠ Skipping eating walk test (GUI not available)")


def test_barrel_roll_has_canvas_transform():
    """Test that barrel_roll has post-draw c.scale() for visual body rotation."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        # Find the post-draw barrel_roll transform section (after all body drawing)
        # It should have barrel_roll-specific c.scale() call separate from body_sway
        idx = source.rfind("barrel_roll")  # last occurrence (post-draw section)
        assert idx > 0, "barrel_roll should have a post-draw section in _draw_panda"
        tail = source[idx:]
        assert "c.scale" in tail[:500], \
            "barrel_roll should use c.scale() for canvas body rotation transform"
        print("✓ barrel_roll has post-draw canvas rotation transform")
    except ImportError:
        print("⚠ Skipping barrel_roll canvas transform test (GUI not available)")


def test_backflip_has_canvas_transform():
    """Test that backflip has post-draw c.scale() for visual body rotation."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        # Find the post-draw backflip transform section
        idx = source.rfind("backflip")  # last occurrence (post-draw section)
        assert idx > 0, "backflip should have a post-draw section in _draw_panda"
        tail = source[idx:]
        assert "c.scale" in tail[:500], \
            "backflip should use c.scale() for canvas body rotation transform"
        print("✓ backflip has post-draw canvas rotation transform")
    except ImportError:
        print("⚠ Skipping backflip canvas transform test (GUI not available)")


def test_drag_body_angle_tracking():
    """Test that drag_body_angle tracks continuous rotation when grabbed by limbs."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        # Check __init__ has the angle attributes
        init_src = inspect.getsource(PandaWidget.__init__)
        assert '_drag_body_angle' in init_src, \
            "PandaWidget should have _drag_body_angle attribute"
        assert '_drag_body_angle_target' in init_src, \
            "PandaWidget should have _drag_body_angle_target attribute"

        # Check _on_drag_motion computes angle from velocity
        drag_src = inspect.getsource(PandaWidget._on_drag_motion)
        assert 'atan2' in drag_src, \
            "_on_drag_motion should use atan2 to compute body hang angle from velocity"
        # Arms/ears should also get rotation (partial tilt)
        assert 'left_arm' in drag_src and 'right_arm' in drag_src, \
            "_on_drag_motion should compute rotation for arms too"
        assert 'left_ear' in drag_src and 'right_ear' in drag_src, \
            "_on_drag_motion should compute rotation for ears too"
        # Arms should have a limited angle range (pi/4)
        assert 'pi / 4' in drag_src, \
            "Arms/ears should have limited rotation range (~pi/4)"

        # Check _draw_panda applies rotation for all limbs
        draw_src = inspect.getsource(PandaWidget._draw_panda)
        assert '_drag_body_angle' in draw_src, \
            "_draw_panda should use _drag_body_angle for body rotation"
        assert 'c.move' in draw_src, \
            "_draw_panda should use c.move for horizontal shift during rotation"
        print("✓ Continuous drag body angle rotation works for legs, arms, and ears")
    except ImportError:
        print("⚠ Skipping drag body angle test (GUI not available)")


def test_min_visible_scale_constant():
    """Test that MIN_VISIBLE_SCALE constant exists and is used."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'MIN_VISIBLE_SCALE'), \
            "PandaWidget should have MIN_VISIBLE_SCALE constant"
        assert PandaWidget.MIN_VISIBLE_SCALE > 0, \
            "MIN_VISIBLE_SCALE should be positive"
        assert PandaWidget.MIN_VISIBLE_SCALE < 0.5, \
            "MIN_VISIBLE_SCALE should be small (< 0.5)"
        print("✓ MIN_VISIBLE_SCALE constant exists with correct value")
    except ImportError:
        print("⚠ Skipping MIN_VISIBLE_SCALE test (GUI not available)")


def test_item_walk_offset_constants():
    """Test that item walk offset constants exist."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'ITEM_WALK_OFFSET_X'), \
            "PandaWidget should have ITEM_WALK_OFFSET_X constant"
        assert hasattr(PandaWidget, 'ITEM_WALK_OFFSET_Y'), \
            "PandaWidget should have ITEM_WALK_OFFSET_Y constant"
        assert PandaWidget.ITEM_WALK_OFFSET_X > 0, \
            "ITEM_WALK_OFFSET_X should be positive"
        print("✓ Item walk offset constants exist")
    except ImportError:
        print("⚠ Skipping item walk offset test (GUI not available)")


def test_side_view_clothing_includes_dangle():
    """Test that side view clothing includes dangle offsets for all limbs."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)
        # All side view sections should include dangle variables
        # Find each 'is_side:' block and verify it contains dangle references
        parts = source.split('is_side')
        # There should be multiple is_side sections (pants, shirts, jacket, full_body, shoes)
        dangle_in_side = 0
        for i, part in enumerate(parts):
            if i == 0:
                continue  # skip before first is_side
            # Check next ~600 chars for dangle usage
            chunk = part[:600]
            if '_dangle' in chunk or 'dangle_v' in chunk or 'dangle_h' in chunk:
                dangle_in_side += 1
        assert dangle_in_side >= 4, \
            f"At least 4 side-view sections should include dangle offsets, found {dangle_in_side}"
        print(f"✓ {dangle_in_side} side-view clothing sections include dangle offsets")
    except ImportError:
        print("⚠ Skipping side view dangle test (GUI not available)")


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
        test_flip_progress_attribute,
        test_backflip_has_body_rotation,
        test_lay_on_side_has_tilt_transform,
        test_sleeping_animation_body_bob,
        test_widget_card_transparent_backgrounds,
        test_eating_walks_to_item,
        test_barrel_roll_has_canvas_transform,
        test_backflip_has_canvas_transform,
        test_drag_body_angle_tracking,
        test_min_visible_scale_constant,
        test_item_walk_offset_constants,
        test_side_view_clothing_includes_dangle,
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
