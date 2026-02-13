#!/usr/bin/env python3
"""
Test pants equip slot, body-contoured rendering, equipment alignment, and limb detection.
Validates:
- PandaAppearance has a separate 'pants' slot
- Pants can be equipped alongside shirts (not replace them)
- Full-body/dress items clear the pants slot
- Pants rendering uses body-contoured shapes (hip area, tapered legs)
- Shoes use per-leg dangle values
- Weapons use horizontal dangle tracking
- Limb detection boundaries are widened for head and arms
- Side/back view rendering uses view-specific positioning
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_appearance_has_pants_slot():
    """PandaAppearance should have a separate 'pants' field."""
    from src.features.panda_closet import PandaAppearance
    appearance = PandaAppearance()
    assert hasattr(appearance, 'pants'), "PandaAppearance should have 'pants' field"
    assert appearance.pants is None, "pants should default to None"
    print("✓ PandaAppearance has separate pants slot")


def test_appearance_pants_serialization():
    """Pants slot should be included in to_dict/from_dict."""
    from src.features.panda_closet import PandaAppearance
    appearance = PandaAppearance()
    appearance.pants = 'blue_jeans'
    appearance.clothing = 'red_shirt'
    d = appearance.to_dict()
    assert 'pants' in d, "to_dict should include pants"
    assert d['pants'] == 'blue_jeans'
    assert d['clothing'] == 'red_shirt'

    loaded = PandaAppearance()
    loaded.from_dict(d)
    assert loaded.pants == 'blue_jeans', "from_dict should restore pants"
    assert loaded.clothing == 'red_shirt', "from_dict should restore clothing"
    print("✓ Pants slot serialises/deserialises correctly")


def test_equip_pants_separate_from_shirt():
    """Equipping pants should NOT unequip the current shirt."""
    from src.features.panda_closet import PandaCloset
    pc = PandaCloset()
    # Unlock test items
    for item in pc.items.values():
        item.unlocked = True

    # Equip a shirt first
    assert pc.equip_item('red_shirt'), "Should equip red_shirt"
    assert pc.appearance.clothing == 'red_shirt'

    # Now equip pants — shirt should remain
    assert pc.equip_item('blue_jeans'), "Should equip blue_jeans"
    assert pc.appearance.pants == 'blue_jeans', \
        f"pants should be blue_jeans, got {pc.appearance.pants}"
    assert pc.appearance.clothing == 'red_shirt', \
        f"clothing should still be red_shirt, got {pc.appearance.clothing}"
    print("✓ Pants equip separately from shirts")


def test_equip_shirt_does_not_remove_pants():
    """Equipping a new shirt should keep pants equipped."""
    from src.features.panda_closet import PandaCloset
    pc = PandaCloset()
    for item in pc.items.values():
        item.unlocked = True

    pc.equip_item('blue_jeans')
    pc.equip_item('red_shirt')
    assert pc.appearance.pants == 'blue_jeans'

    # Swap shirt — pants should remain
    pc.equip_item('blue_shirt')
    assert pc.appearance.clothing == 'blue_shirt'
    assert pc.appearance.pants == 'blue_jeans', \
        "Changing shirt should not remove pants"
    print("✓ Shirt swap keeps pants")


def test_full_body_clears_pants():
    """Equipping a full-body outfit should clear the pants slot."""
    from src.features.panda_closet import PandaCloset
    pc = PandaCloset()
    for item in pc.items.values():
        item.unlocked = True

    pc.equip_item('blue_jeans')
    pc.equip_item('red_shirt')
    assert pc.appearance.pants == 'blue_jeans'

    pc.equip_item('tuxedo')  # full_body
    assert pc.appearance.clothing == 'tuxedo'
    assert pc.appearance.pants is None, \
        "Full-body should clear pants slot"
    print("✓ Full-body outfit clears pants slot")


def test_dress_clears_pants():
    """Equipping a dress should clear the pants slot."""
    from src.features.panda_closet import PandaCloset
    pc = PandaCloset()
    for item in pc.items.values():
        item.unlocked = True

    pc.equip_item('blue_jeans')
    pc.equip_item('dress')  # dress type
    assert pc.appearance.pants is None, \
        "Dress should clear pants slot"
    print("✓ Dress clears pants slot")


def test_equip_pants_over_full_body():
    """Equipping pants when wearing full-body should clear the full-body item."""
    from src.features.panda_closet import PandaCloset
    pc = PandaCloset()
    for item in pc.items.values():
        item.unlocked = True

    pc.equip_item('tuxedo')  # full_body
    assert pc.appearance.clothing == 'tuxedo'

    pc.equip_item('blue_jeans')
    assert pc.appearance.pants == 'blue_jeans'
    assert pc.appearance.clothing is None, \
        "Full-body should be removed when pants equipped"
    print("✓ Pants over full-body clears full-body")


def test_unequip_pants():
    """Unequipping pants should clear the pants slot only."""
    from src.features.panda_closet import PandaCloset
    pc = PandaCloset()
    for item in pc.items.values():
        item.unlocked = True

    pc.equip_item('red_shirt')
    pc.equip_item('blue_jeans')
    pc.unequip_item('blue_jeans')
    assert pc.appearance.pants is None, "Pants slot should be None"
    assert pc.appearance.clothing == 'red_shirt', "Shirt should remain"
    print("✓ Unequip pants keeps shirt")


def test_pants_rendering_body_contoured():
    """Pants drawing should include body-contoured shapes (hip area, tapered legs)."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)

        # Should draw from appearance.pants
        assert 'appearance.pants' in source or "appearance, 'pants'" in source, \
            "Should read pants from appearance.pants"

        # Should have hip / crotch connection area
        assert 'hip_y' in source, "Pants should use a hip_y anchor for shaping"

        # Should have tapered leg polygon points (thigh wider than calf)
        assert 'leg_bottom' in source, "Should compute leg_bottom"

        # Should have waistband
        assert 'waist_y' in source or 'Waistband' in source, \
            "Should draw a waistband"

        print("✓ Pants rendering is body-contoured")
    except ImportError:
        print("⚠ Skipping pants rendering test (GUI not available)")


def test_shoes_use_per_leg_dangle():
    """Shoes should use per-leg dangle values, not generic whole-body dangle."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)

        # Find the shoes section
        shoes_section = source.split('# --- Draw shoes')[1].split('except')[0]

        # Should reference per-leg dangle variables
        assert '_left_leg_dangle' in shoes_section or 'left_shoe_swing' in shoes_section, \
            "Shoes should use per-leg dangle values"
        assert '_right_leg_dangle' in shoes_section or 'right_shoe_swing' in shoes_section, \
            "Shoes should use per-leg dangle values"

        print("✓ Shoes use per-leg dangle values")
    except ImportError:
        print("⚠ Skipping shoe dangle test (GUI not available)")


def test_weapon_uses_horizontal_dangle():
    """Weapon positioning should include horizontal arm dangle tracking."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)

        weapon_section = source.split('# Draw equipped weapon')[1].split('except')[0]

        # Weapon should track right arm horizontal dangle
        assert 'ra_swing_h' in weapon_section or '_right_arm_dangle_h' in weapon_section, \
            "Weapon should use horizontal arm dangle"

        print("✓ Weapon uses horizontal arm dangle tracking")
    except ImportError:
        print("⚠ Skipping weapon test (GUI not available)")


def test_side_view_clothing_positioning():
    """Clothing should use view-specific arm positioning for side views."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)

        # Should detect side view
        assert 'is_side' in source, "Should detect side view animations"
        assert 'is_back' in source, "Should detect back view animation"

        # Side view should use side_dir for arm/sleeve positioning
        assert 'side_dir' in source, "Should use side_dir for directional positioning"

        print("✓ Clothing has view-specific positioning")
    except ImportError:
        print("⚠ Skipping side view test (GUI not available)")


def test_limb_detection_boundaries_improved():
    """Arm and head detection boundaries should be wider for accurate grabbing."""
    from src.features.panda_character import PandaCharacter

    # Head boundary should be extended
    assert PandaCharacter.HEAD_BOUNDARY >= 0.33, \
        f"HEAD_BOUNDARY should be >= 0.33 (got {PandaCharacter.HEAD_BOUNDARY})"

    # Arm boundaries should be wider (inward) for better arm grabbing
    assert PandaCharacter.ARM_LEFT_BOUNDARY >= 0.28, \
        f"ARM_LEFT_BOUNDARY should be >= 0.28 (got {PandaCharacter.ARM_LEFT_BOUNDARY})"
    assert PandaCharacter.ARM_RIGHT_BOUNDARY <= 0.72, \
        f"ARM_RIGHT_BOUNDARY should be <= 0.72 (got {PandaCharacter.ARM_RIGHT_BOUNDARY})"

    # Ear boundaries should be wider for easier ear detection
    assert PandaCharacter.EAR_LEFT_BOUNDARY >= 0.18, \
        f"EAR_LEFT_BOUNDARY should be >= 0.18 (got {PandaCharacter.EAR_LEFT_BOUNDARY})"
    assert PandaCharacter.EAR_RIGHT_BOUNDARY <= 0.82, \
        f"EAR_RIGHT_BOUNDARY should be <= 0.82 (got {PandaCharacter.EAR_RIGHT_BOUNDARY})"

    print("✓ Limb detection boundaries are improved")


def test_body_part_detection_accuracy():
    """Body part detection should correctly identify arms at their actual positions."""
    from src.features.panda_character import PandaCharacter
    panda = PandaCharacter()

    # Arms should be detected at their actual canvas positions
    # Left arm rel_x < ARM_LEFT_BOUNDARY (0.30), Right arm rel_x > ARM_RIGHT_BOUNDARY (0.70)
    assert panda.get_body_part_at_position(0.45, 0.15) == 'left_arm', \
        "Should detect left arm at rel_x=0.15, rel_y=0.45"
    assert panda.get_body_part_at_position(0.45, 0.85) == 'right_arm', \
        "Should detect right arm at rel_x=0.85, rel_y=0.45"

    # Centre of body should be body
    assert panda.get_body_part_at_position(0.45, 0.5) == 'body', \
        "Should detect body at centre"

    # Head should be detected with expanded boundary
    assert panda.get_body_part_at_position(0.33, 0.3) == 'head', \
        "Should detect head at rel_y=0.33, rel_x=0.3 (off-centre, not nose)"
    # Nose detected in centre of lower head
    assert panda.get_body_part_at_position(0.30, 0.5) == 'nose', \
        "Should detect nose at rel_y=0.30, rel_x=0.5"

    # Ears should be detected at wider positions
    assert panda.get_body_part_at_position(0.10, 0.15) == 'left_ear', \
        "Should detect left ear at rel_x=0.15"
    assert panda.get_body_part_at_position(0.10, 0.85) == 'right_ear', \
        "Should detect right ear at rel_x=0.85"

    print("✓ Body part detection is accurate")


if __name__ == '__main__':
    test_appearance_has_pants_slot()
    test_appearance_pants_serialization()
    test_equip_pants_separate_from_shirt()
    test_equip_shirt_does_not_remove_pants()
    test_full_body_clears_pants()
    test_dress_clears_pants()
    test_equip_pants_over_full_body()
    test_unequip_pants()
    test_pants_rendering_body_contoured()
    test_shoes_use_per_leg_dangle()
    test_weapon_uses_horizontal_dangle()
    test_side_view_clothing_positioning()
    test_limb_detection_boundaries_improved()
    test_body_part_detection_accuracy()
    print("\n✅ All tests passed!")
