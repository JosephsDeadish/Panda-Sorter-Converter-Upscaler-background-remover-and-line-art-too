#!/usr/bin/env python3
"""
Test panda character improvements.
Validates:
- Reduced sensitivity thresholds
- New stat tracking (drag, toss, shake, spin, toy_interact, clothing_change)
- Toy interaction uses correct counter (toy_interact_count, not click_count)
- Clothing change tracking
- Statistics include all new fields
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.features.panda_character import PandaCharacter


def test_sensitivity_thresholds():
    """Test that panda widget sensitivity thresholds are properly increased."""
    # Import cannot instantiate PandaWidget without GUI, so check class constants
    try:
        from src.ui.panda_widget import PandaWidget
        assert PandaWidget.SHAKE_DIRECTION_CHANGES >= 40, \
            f"SHAKE_DIRECTION_CHANGES should be >= 40 (got {PandaWidget.SHAKE_DIRECTION_CHANGES})"
        assert PandaWidget.MIN_SHAKE_MOVEMENT >= 12, \
            f"MIN_SHAKE_MOVEMENT should be >= 12 (got {PandaWidget.MIN_SHAKE_MOVEMENT})"
        assert PandaWidget.MIN_ROTATION_ANGLE >= 0.55, \
            f"MIN_ROTATION_ANGLE should be >= 0.55 (got {PandaWidget.MIN_ROTATION_ANGLE})"
        assert PandaWidget.SPIN_CONSISTENCY_THRESHOLD >= 0.92, \
            f"SPIN_CONSISTENCY_THRESHOLD should be >= 0.92 (got {PandaWidget.SPIN_CONSISTENCY_THRESHOLD})"
        print("✓ Sensitivity thresholds correctly increased")
    except ImportError:
        print("⚠ Skipping sensitivity test (GUI not available)")


def test_new_stats_initialized():
    """Test that new stats are initialized on PandaCharacter."""
    panda = PandaCharacter()
    assert panda.drag_count == 0, "drag_count should start at 0"
    assert panda.toss_count == 0, "toss_count should start at 0"
    assert panda.shake_count == 0, "shake_count should start at 0"
    assert panda.spin_count == 0, "spin_count should start at 0"
    assert panda.toy_interact_count == 0, "toy_interact_count should start at 0"
    assert panda.clothing_change_count == 0, "clothing_change_count should start at 0"
    print("✓ New stats initialized correctly")


def test_drag_tracks_stat():
    """Test that on_drag increments drag_count."""
    panda = PandaCharacter()
    panda.on_drag()
    assert panda.drag_count == 1, "on_drag should increment drag_count"
    panda.on_drag()
    assert panda.drag_count == 2, "drag_count should be 2 after two drags"
    print("✓ Drag stat tracking works")


def test_toss_tracks_stat():
    """Test that on_toss increments toss_count."""
    panda = PandaCharacter()
    panda.on_toss()
    assert panda.toss_count == 1, "on_toss should increment toss_count"
    print("✓ Toss stat tracking works")


def test_shake_tracks_stat():
    """Test that on_shake increments shake_count."""
    panda = PandaCharacter()
    panda.on_shake()
    assert panda.shake_count == 1, "on_shake should increment shake_count"
    print("✓ Shake stat tracking works")


def test_spin_tracks_stat():
    """Test that on_spin increments spin_count."""
    panda = PandaCharacter()
    panda.on_spin()
    assert panda.spin_count == 1, "on_spin should increment spin_count"
    print("✓ Spin stat tracking works")


def test_toy_interact_uses_correct_counter():
    """Test that toy interactions use toy_interact_count, not click_count."""
    panda = PandaCharacter()
    panda.on_item_interact('Ball', 'toy')
    assert panda.toy_interact_count == 1, "Toy interact should increment toy_interact_count"
    assert panda.click_count == 0, "Toy interact should NOT increment click_count"
    print("✓ Toy interaction uses correct counter")


def test_clothing_change_tracks_stat():
    """Test that clothing changes are tracked."""
    panda = PandaCharacter()
    panda.on_clothing_change()
    assert panda.clothing_change_count == 1, "on_clothing_change should increment clothing_change_count"
    print("✓ Clothing change stat tracking works")


def test_statistics_include_new_fields():
    """Test that get_statistics returns all new stat fields."""
    panda = PandaCharacter()
    panda.on_drag()
    panda.on_toss()
    panda.on_shake()
    panda.on_spin()
    panda.on_item_interact('Ball', 'toy')
    panda.on_clothing_change()

    stats = panda.get_statistics()
    assert 'drag_count' in stats, "Statistics should include drag_count"
    assert 'toss_count' in stats, "Statistics should include toss_count"
    assert 'shake_count' in stats, "Statistics should include shake_count"
    assert 'spin_count' in stats, "Statistics should include spin_count"
    assert 'toy_interact_count' in stats, "Statistics should include toy_interact_count"
    assert 'clothing_change_count' in stats, "Statistics should include clothing_change_count"
    assert stats['drag_count'] == 1
    assert stats['toss_count'] == 1
    assert stats['shake_count'] == 1
    assert stats['spin_count'] == 1
    assert stats['toy_interact_count'] == 1
    assert stats['clothing_change_count'] == 1
    print("✓ Statistics include all new fields")


def test_food_interact_still_tracks_feed_count():
    """Test that food interactions still correctly track feed_count."""
    panda = PandaCharacter()
    panda.on_item_interact('Bamboo', 'food')
    assert panda.feed_count == 1, "Food interact should increment feed_count"
    print("✓ Food interaction still tracks feed_count correctly")


def test_speech_bubble_font_constants():
    """Test that speech bubble constants are updated for bigger/bolder text."""
    try:
        from src.ui.panda_widget import (
            BUBBLE_CHAR_WIDTH, BUBBLE_LINE_HEIGHT, BUBBLE_MAX_WIDTH
        )
        assert BUBBLE_CHAR_WIDTH >= 10, \
            f"BUBBLE_CHAR_WIDTH should be >= 10 for larger font (got {BUBBLE_CHAR_WIDTH})"
        assert BUBBLE_LINE_HEIGHT >= 24, \
            f"BUBBLE_LINE_HEIGHT should be >= 24 for larger font (got {BUBBLE_LINE_HEIGHT})"
        assert BUBBLE_MAX_WIDTH >= 300, \
            f"BUBBLE_MAX_WIDTH should be >= 300 for larger text (got {BUBBLE_MAX_WIDTH})"
        print("✓ Speech bubble constants updated for bigger/bolder text")
    except ImportError:
        print("⚠ Skipping speech bubble test (GUI not available)")


def test_item_thrown_at_panda():
    """Test that items can be thrown at panda with body-part-specific reactions."""
    panda = PandaCharacter()

    # Head hit
    response = panda.on_item_thrown_at('Ball', 'head')
    assert panda.items_thrown_at_count == 1, "items_thrown_at_count should be 1"
    assert 'head' in response.lower() or 'bonk' in response.lower() or 'ow' in response.lower() \
        or 'stars' in response.lower() or 'hurt' in response.lower(), \
        f"Head hit should mention head/pain: {response}"

    # Belly hit
    response = panda.on_item_thrown_at('Squishy Ball', 'belly')
    assert panda.items_thrown_at_count == 2, "items_thrown_at_count should be 2"
    assert 'belly' in response.lower() or 'tummy' in response.lower() or 'wobble' in response.lower() \
        or 'jiggle' in response.lower() or 'bounce' in response.lower(), \
        f"Belly hit should mention belly/wobble: {response}"

    # Legs hit
    response = panda.on_item_thrown_at('Stick', 'legs')
    assert panda.items_thrown_at_count == 3, "items_thrown_at_count should be 3"
    print("✓ Item thrown at panda works correctly")


def test_item_physics_wobble_elasticity():
    """Test that items have wobble and elasticity physics properties."""
    from src.features.panda_widgets import WidgetCollection
    wc = WidgetCollection()

    squishy = wc.get_widget('squishy_ball')
    assert squishy.physics.wobble > 0, "Squishy ball should have wobble"
    assert squishy.physics.elasticity > 0, "Squishy ball should have elasticity"

    plushie = wc.get_widget('plushie')
    assert plushie.physics.wobble > 0, "Plushie should be wobbly"

    stick = wc.get_widget('stick')
    assert stick.physics.elasticity > 0, "Stick should be bendy"
    print("✓ Item physics wobble/elasticity properties correct")


def test_statistics_include_items_thrown():
    """Test that statistics include items_thrown_at_count."""
    panda = PandaCharacter()
    panda.on_item_thrown_at('Ball', 'head')
    stats = panda.get_statistics()
    assert 'items_thrown_at_count' in stats, "Stats should include items_thrown_at_count"
    assert stats['items_thrown_at_count'] == 1
    print("✓ Statistics include items_thrown_at_count")


def test_belly_poke_tracks_stat():
    """Test that on_belly_poke increments belly_poke_count."""
    panda = PandaCharacter()
    assert panda.belly_poke_count == 0, "belly_poke_count should start at 0"
    response = panda.on_belly_poke()
    assert panda.belly_poke_count == 1, "on_belly_poke should increment belly_poke_count"
    assert isinstance(response, str), "on_belly_poke should return a string"
    assert len(response) > 0, "on_belly_poke should return a non-empty string"
    panda.on_belly_poke()
    assert panda.belly_poke_count == 2, "belly_poke_count should be 2 after two pokes"
    print("✓ Belly poke stat tracking works")


def test_belly_poke_responses():
    """Test that belly poke returns jiggle-themed responses."""
    panda = PandaCharacter()
    # Collect several responses
    responses = set()
    for _ in range(20):
        responses.add(panda.on_belly_poke())
    # Should have at least a few different responses
    assert len(responses) > 1, "Belly poke should have variety in responses"
    print("✓ Belly poke responses have variety")


def test_statistics_include_belly_poke():
    """Test that statistics include belly_poke_count."""
    panda = PandaCharacter()
    panda.on_belly_poke()
    stats = panda.get_statistics()
    assert 'belly_poke_count' in stats, "Stats should include belly_poke_count"
    assert stats['belly_poke_count'] == 1
    print("✓ Statistics include belly_poke_count")


def test_belly_jiggle_animation_state():
    """Test that belly_jiggle is a valid animation state."""
    panda = PandaCharacter()
    assert 'belly_jiggle' in panda.ANIMATION_STATES, \
        "belly_jiggle should be in ANIMATION_STATES"
    state = panda.get_animation_state('belly_jiggle')
    assert state == 'belly_jiggle', "get_animation_state should return belly_jiggle"
    print("✓ belly_jiggle animation state is valid")

def test_body_part_click_vs_rub_responses():
    """Test that click and rub have separate response sets for body parts."""
    panda = PandaCharacter()
    # Click responses should use BODY_PART_CLICK_RESPONSES
    assert hasattr(panda, 'BODY_PART_CLICK_RESPONSES'), \
        "PandaCharacter should have BODY_PART_CLICK_RESPONSES"
    assert hasattr(panda, 'BODY_PART_RESPONSES'), \
        "PandaCharacter should have BODY_PART_RESPONSES"
    # They should be separate dicts
    assert panda.BODY_PART_CLICK_RESPONSES is not panda.BODY_PART_RESPONSES, \
        "Click and rub responses should be separate dicts"
    # Click response for head should differ from rub response
    click_head = set(panda.BODY_PART_CLICK_RESPONSES.get('head', []))
    rub_head = set(panda.BODY_PART_RESPONSES.get('head', []))
    assert click_head != rub_head, \
        "Head click and rub responses should be different"
    print("✓ Body part click vs rub responses are separate")


def test_body_part_click_returns_click_responses():
    """Test that on_body_part_click uses click-specific responses."""
    panda = PandaCharacter()
    click_responses = panda.BODY_PART_CLICK_RESPONSES.get('head', [])
    responses = set()
    for _ in range(40):
        responses.add(panda.on_body_part_click('head'))
    # At least one response should be from the click-specific set
    assert responses & set(click_responses), \
        "on_body_part_click should use BODY_PART_CLICK_RESPONSES"
    print("✓ on_body_part_click uses click-specific responses")


def test_on_rub_returns_rub_responses():
    """Test that on_rub uses rub/pet-specific responses."""
    panda = PandaCharacter()
    rub_responses = panda.BODY_PART_RESPONSES.get('head', [])
    responses = set()
    for _ in range(40):
        responses.add(panda.on_rub('head'))
    assert responses & set(rub_responses), \
        "on_rub should use BODY_PART_RESPONSES"
    print("✓ on_rub uses rub-specific responses")


def test_dangle_physics_constants():
    """Test that dangle physics constants exist for directional dangle."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'DANGLE_ARM_H_FACTOR'), \
            "PandaWidget should have DANGLE_ARM_H_FACTOR for horizontal dangle"
        assert hasattr(PandaWidget, 'DANGLE_LEG_H_FACTOR'), \
            "PandaWidget should have DANGLE_LEG_H_FACTOR for horizontal dangle"
        assert hasattr(PandaWidget, 'DANGLE_HEAD_MULTIPLIER'), \
            "PandaWidget should have DANGLE_HEAD_MULTIPLIER"
        assert hasattr(PandaWidget, 'DANGLE_BODY_MULTIPLIER'), \
            "PandaWidget should have DANGLE_BODY_MULTIPLIER"
        assert PandaWidget.DANGLE_HEAD_MULTIPLIER > PandaWidget.DANGLE_BODY_MULTIPLIER, \
            "Head dangle should be stronger than body dangle"
        print("✓ Dangle physics constants correctly defined")
    except ImportError:
        print("⚠ Skipping dangle physics test (GUI not available)")


def test_shop_to_closet_category_mapping():
    """Test that shop categories map to closet categories."""
    from src.features.shop_system import ShopCategory, SHOP_TO_CLOSET_CATEGORY
    assert ShopCategory.CLOTHES in SHOP_TO_CLOSET_CATEGORY, \
        "CLOTHES should map to a closet category"
    assert ShopCategory.ACCESSORIES in SHOP_TO_CLOSET_CATEGORY, \
        "ACCESSORIES should map to a closet category"
    assert SHOP_TO_CLOSET_CATEGORY[ShopCategory.CLOTHES] == "clothing", \
        "CLOTHES should map to 'clothing'"
    assert SHOP_TO_CLOSET_CATEGORY[ShopCategory.ACCESSORIES] == "accessory", \
        "ACCESSORIES should map to 'accessory'"
    print("✓ Shop-to-closet category mapping is correct")


def test_widgets_panel_has_animations():
    """Test that WidgetsPanel has animation entries."""
    try:
        from src.ui.widgets_panel import WidgetsPanel
        assert hasattr(WidgetsPanel, 'ANIMATION_ENTRIES'), \
            "WidgetsPanel should have ANIMATION_ENTRIES"
        assert len(WidgetsPanel.ANIMATION_ENTRIES) > 0, \
            "ANIMATION_ENTRIES should not be empty"
        # Each entry should be (emoji, name, anim_state)
        for entry in WidgetsPanel.ANIMATION_ENTRIES:
            assert len(entry) == 3, f"Animation entry should have 3 elements: {entry}"
            emoji, name, anim_state = entry
            assert isinstance(emoji, str) and isinstance(name, str) and isinstance(anim_state, str), \
                f"All animation entry fields should be strings: {entry}"
        print("✓ WidgetsPanel has valid animation entries")
    except ImportError:
        print("⚠ Skipping WidgetsPanel test (GUI not available)")


def test_sound_settings_persistence():
    """Test that sound settings include all volume and choice fields."""
    # Test the structure of settings without needing GUI
    from src.features.sound_manager import SoundManager, SoundPack
    sm = SoundManager()
    sm.set_effects_volume(0.7)
    sm.set_notifications_volume(0.5)
    sm.set_sound_pack(SoundPack.MINIMAL)
    config = sm.get_config()
    assert 'effects_volume' in config, "Config should include effects_volume"
    assert 'notifications_volume' in config, "Config should include notifications_volume"
    assert config['effects_volume'] == 0.7, "effects_volume should be 0.7"
    assert config['notifications_volume'] == 0.5, "notifications_volume should be 0.5"
    assert config['sound_pack'] == 'minimal', "sound_pack should be 'minimal'"
    print("✓ Sound settings include all volume fields")


if __name__ == "__main__":
    print("Testing Panda Character Improvements...")
    print("-" * 50)

    try:
        test_sensitivity_thresholds()
        test_new_stats_initialized()
        test_drag_tracks_stat()
        test_toss_tracks_stat()
        test_shake_tracks_stat()
        test_spin_tracks_stat()
        test_toy_interact_uses_correct_counter()
        test_clothing_change_tracks_stat()
        test_statistics_include_new_fields()
        test_food_interact_still_tracks_feed_count()
        test_speech_bubble_font_constants()
        test_item_thrown_at_panda()
        test_item_physics_wobble_elasticity()
        test_statistics_include_items_thrown()
        test_belly_poke_tracks_stat()
        test_belly_poke_responses()
        test_statistics_include_belly_poke()
        test_belly_jiggle_animation_state()
        test_body_part_click_vs_rub_responses()
        test_body_part_click_returns_click_responses()
        test_on_rub_returns_rub_responses()
        test_dangle_physics_constants()
        test_shop_to_closet_category_mapping()
        test_widgets_panel_has_animations()
        test_sound_settings_persistence()

        print("-" * 50)
        print("✅ All panda improvement tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
