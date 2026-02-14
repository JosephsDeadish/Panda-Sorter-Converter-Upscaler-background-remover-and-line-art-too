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
    """Test that panda widget sensitivity thresholds are properly tuned.
    
    Spin detection should be strict (hard to trigger accidentally).
    Shake detection should require very fast motion but fewer direction changes.
    """
    # Import cannot instantiate PandaWidget without GUI, so check class constants
    try:
        from src.ui.panda_widget import PandaWidget
        # Shake: lowered direction changes but high velocity requirement
        assert PandaWidget.SHAKE_DIRECTION_CHANGES >= 4, \
            f"SHAKE_DIRECTION_CHANGES should be >= 4 (got {PandaWidget.SHAKE_DIRECTION_CHANGES})"
        assert PandaWidget.MIN_SHAKE_VELOCITY >= 500, \
            f"MIN_SHAKE_VELOCITY should be >= 500 for fast shakes (got {PandaWidget.MIN_SHAKE_VELOCITY})"
        # Spin: stricter thresholds to avoid false triggers
        assert PandaWidget.MIN_ROTATION_ANGLE >= 0.7, \
            f"MIN_ROTATION_ANGLE should be >= 0.7 (got {PandaWidget.MIN_ROTATION_ANGLE})"
        assert PandaWidget.SPIN_CONSISTENCY_THRESHOLD >= 0.95, \
            f"SPIN_CONSISTENCY_THRESHOLD should be >= 0.95 (got {PandaWidget.SPIN_CONSISTENCY_THRESHOLD})"
        assert PandaWidget.MIN_SPIN_POSITIONS >= 24, \
            f"MIN_SPIN_POSITIONS should be >= 24 (got {PandaWidget.MIN_SPIN_POSITIONS})"
        assert PandaWidget.MIN_SPIN_TOTAL_ANGLE >= 4.71239, \
            f"MIN_SPIN_TOTAL_ANGLE should be >= 4.71239 (~1.5*pi) (got {PandaWidget.MIN_SPIN_TOTAL_ANGLE})"
        assert PandaWidget.MIN_SPIN_VELOCITY >= 600, \
            f"MIN_SPIN_VELOCITY should be >= 600 for fast-only spin (got {PandaWidget.MIN_SPIN_VELOCITY})"
        print("✓ Sensitivity thresholds correctly tuned")
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


def test_belly_rub_animation_state():
    """Test that belly_rub replaced tail_wag as a valid animation state."""
    panda = PandaCharacter()
    assert 'belly_rub' in panda.ANIMATION_STATES, \
        "belly_rub should be in ANIMATION_STATES"
    assert 'tail_wag' not in panda.ANIMATION_STATES, \
        "tail_wag should have been renamed to belly_rub"
    state = panda.get_animation_state('belly_rub')
    assert state == 'belly_rub', "get_animation_state should return belly_rub"
    print("✓ belly_rub animation state is valid (replaced tail_wag)")


def test_belly_rub_in_click_animations():
    """Test that belly_rub is used as a click animation variant."""
    try:
        import src.ui.panda_widget as pw
        # Check ANIMATION_EMOJIS has belly_rub
        assert 'belly_rub' in pw.PandaWidget.ANIMATION_EMOJIS, \
            "belly_rub should have animation emojis"
        print("✓ belly_rub is configured as a click animation variant")
    except ImportError:
        print("⚠ Skipping belly_rub click animation test (GUI not available)")


def test_animation_interval_smooth():
    """Test that animation interval is fast enough for smooth animations."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert PandaWidget.ANIMATION_INTERVAL <= 50, \
            f"ANIMATION_INTERVAL should be <= 50ms for smooth animations (got {PandaWidget.ANIMATION_INTERVAL})"
        print("✓ Animation interval is smooth ({0}ms)".format(PandaWidget.ANIMATION_INTERVAL))
    except ImportError:
        print("⚠ Skipping animation interval test (GUI not available)")


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


def test_auto_walk_state_variables():
    """Test that PandaWidget has auto-walk state variables."""
    try:
        from src.ui.panda_widget import PandaWidget
        # Check class has the auto-walk methods
        assert hasattr(PandaWidget, '_schedule_auto_walk'), \
            "PandaWidget should have _schedule_auto_walk method"
        assert hasattr(PandaWidget, '_start_auto_walk'), \
            "PandaWidget should have _start_auto_walk method"
        assert hasattr(PandaWidget, '_auto_walk_tick'), \
            "PandaWidget should have _auto_walk_tick method"
        assert hasattr(PandaWidget, 'AUTO_WALK_COMMENTS'), \
            "PandaWidget should have AUTO_WALK_COMMENTS"
        print("✓ Auto-walk state variables and methods exist")
    except ImportError:
        print("⚠ Skipping auto-walk test (GUI not available)")


def test_accessories_routed_to_closet():
    """Test that shop accessories are in SHOP_TO_CLOSET_CATEGORY mapping."""
    from src.features.shop_system import ShopCategory, SHOP_TO_CLOSET_CATEGORY
    assert ShopCategory.ACCESSORIES in SHOP_TO_CLOSET_CATEGORY, \
        "ACCESSORIES should map to closet"
    assert SHOP_TO_CLOSET_CATEGORY[ShopCategory.ACCESSORIES] == "accessory", \
        "ACCESSORIES should map to 'accessory' closet category"
    print("✓ Accessories properly routed to closet via SHOP_TO_CLOSET_CATEGORY")


def test_drag_blocks_non_drag_animations():
    """Test that drag-allowed animations are defined and block non-drag ones."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'DRAG_ALLOWED_ANIMATIONS'), \
            "PandaWidget should have DRAG_ALLOWED_ANIMATIONS"
        allowed = PandaWidget.DRAG_ALLOWED_ANIMATIONS
        assert 'dragging' in allowed, "dragging should be allowed during drag"
        assert 'wall_hit' in allowed, "wall_hit should be allowed during drag"
        assert 'shaking' in allowed, "shaking should be allowed during drag"
        assert 'spinning' in allowed, "spinning should be allowed during drag"
        # Non-drag animations should NOT be in the set
        assert 'dancing' not in allowed, "dancing should not be allowed during drag"
        assert 'celebrating' not in allowed, "celebrating should not be allowed during drag"
        assert 'idle' not in allowed, "idle should not be allowed during drag"
        print("✓ Drag-allowed animations correctly defined")
    except ImportError:
        print("⚠ Skipping drag animation guard test (GUI not available)")


def test_head_drag_responses():
    """Test that head-drag specific responses exist and are used."""
    panda = PandaCharacter()
    assert hasattr(panda, 'HEAD_DRAG_RESPONSES'), \
        "PandaCharacter should have HEAD_DRAG_RESPONSES"
    assert len(panda.HEAD_DRAG_RESPONSES) > 0, \
        "HEAD_DRAG_RESPONSES should not be empty"
    # Test that on_drag with grabbed_head=True uses head responses
    responses = set()
    for _ in range(30):
        responses.add(panda.on_drag(grabbed_head=True))
    head_set = set(panda.HEAD_DRAG_RESPONSES)
    assert responses & head_set, "on_drag(grabbed_head=True) should use HEAD_DRAG_RESPONSES"
    print("✓ Head drag responses work correctly")


def test_body_drag_responses():
    """Test that body-drag responses are used when not grabbed by head."""
    panda = PandaCharacter()
    assert hasattr(panda, 'BODY_DRAG_RESPONSES'), \
        "PandaCharacter should have BODY_DRAG_RESPONSES"
    # Default (non-head) drag should use DRAG_RESPONSES
    responses = set()
    for _ in range(30):
        responses.add(panda.on_drag(grabbed_head=False))
    drag_set = set(panda.DRAG_RESPONSES)
    assert responses & drag_set, "on_drag(grabbed_head=False) should use DRAG_RESPONSES"
    print("✓ Body drag responses work correctly")


def test_body_part_detection_with_x():
    """Test that body part detection uses X position for arm detection."""
    panda = PandaCharacter()
    # Body region (0.48-0.72), center → should return 'body'
    part = panda.get_body_part_at_position(0.55, 0.5)
    assert part == 'body', f"Center body should be 'body', got {part}"
    # Body region, far left → should return 'left_arm'
    part = panda.get_body_part_at_position(0.55, 0.1)
    assert part == 'left_arm', f"Left side body should be 'left_arm', got {part}"
    # Body region, far right → should return 'right_arm'
    part = panda.get_body_part_at_position(0.55, 0.9)
    assert part == 'right_arm', f"Right side body should be 'right_arm', got {part}"
    # Head is always head regardless of X (except for ears)
    part = panda.get_body_part_at_position(0.30, 0.5)
    assert part == 'head', f"Top center should be 'head', got {part}"
    # Legs - left and right
    part = panda.get_body_part_at_position(0.9, 0.3)
    assert part == 'left_leg', f"Bottom left should be 'left_leg', got {part}"
    part = panda.get_body_part_at_position(0.9, 0.7)
    assert part == 'right_leg', f"Bottom right should be 'right_leg', got {part}"
    # Ears
    part = panda.get_body_part_at_position(0.1, 0.1)
    assert part == 'left_ear', f"Top left should be 'left_ear', got {part}"
    part = panda.get_body_part_at_position(0.1, 0.9)
    assert part == 'right_ear', f"Top right should be 'right_ear', got {part}"
    print("✓ Body part detection with X-axis works correctly")


def test_food_pickup_response():
    """Test that on_food_pickup returns a pickup response."""
    panda = PandaCharacter()
    assert hasattr(panda, 'on_food_pickup'), \
        "PandaCharacter should have on_food_pickup method"
    response = panda.on_food_pickup('Fresh Bamboo')
    assert isinstance(response, str) and len(response) > 0, \
        "on_food_pickup should return a non-empty string"
    print("✓ Food pickup response works")


def test_eating_response_per_item():
    """Test that on_eating returns item-specific responses."""
    panda = PandaCharacter()
    assert hasattr(panda, 'on_eating'), \
        "PandaCharacter should have on_eating method"
    # Known item key should give specific response
    response = panda.on_eating('Fresh Bamboo', 'bamboo')
    assert isinstance(response, str) and len(response) > 0
    # Unknown key should give default response
    response = panda.on_eating('Mystery Food', 'unknown_food')
    assert isinstance(response, str) and len(response) > 0
    print("✓ Per-item eating responses work correctly")


def test_kick_toy_response():
    """Test that on_kick_toy returns a kick response."""
    panda = PandaCharacter()
    assert hasattr(panda, 'on_kick_toy'), \
        "PandaCharacter should have on_kick_toy method"
    response = panda.on_kick_toy('Bamboo Ball')
    assert isinstance(response, str) and len(response) > 0, \
        "on_kick_toy should return a non-empty string"
    print("✓ Kick toy response works")


def test_walk_to_food_responses():
    """Test that on_item_interact for food uses walk-to-food responses."""
    panda = PandaCharacter()
    responses = set()
    for _ in range(30):
        responses.add(panda.on_item_interact('Fresh Bamboo', 'food'))
    walk_set = set(panda.WALK_TO_FOOD_RESPONSES)
    assert responses & walk_set, "Food on_item_interact should use WALK_TO_FOOD_RESPONSES"
    print("✓ Walk-to-food responses work correctly")


def test_eating_sequence_constants():
    """Test that eating sequence phase constants exist."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'EATING_PICKUP_FRAMES'), \
            "PandaWidget should have EATING_PICKUP_FRAMES"
        assert hasattr(PandaWidget, 'EATING_INSPECT_FRAMES'), \
            "PandaWidget should have EATING_INSPECT_FRAMES"
        assert hasattr(PandaWidget, 'EATING_CHEW_FRAMES'), \
            "PandaWidget should have EATING_CHEW_FRAMES"
        assert hasattr(PandaWidget, 'EATING_SATISFIED_FRAMES'), \
            "PandaWidget should have EATING_SATISFIED_FRAMES"
        total = (PandaWidget.EATING_PICKUP_FRAMES +
                 PandaWidget.EATING_INSPECT_FRAMES +
                 PandaWidget.EATING_CHEW_FRAMES +
                 PandaWidget.EATING_SATISFIED_FRAMES)
        assert total >= 60, f"Total eating frames should be >= 60, got {total}"
        print("✓ Eating sequence constants correctly defined")
    except ImportError:
        print("⚠ Skipping eating sequence test (GUI not available)")


def test_individual_limb_drag_responses():
    """Test that individual limbs have specific drag responses."""
    panda = PandaCharacter()
    
    # Test left arm drag
    response = panda.on_drag(grabbed_part='left_arm')
    assert response in panda.LEFT_ARM_DRAG_RESPONSES, \
        f"Left arm drag should use LEFT_ARM_DRAG_RESPONSES, got {response}"
    
    # Test right arm drag
    response = panda.on_drag(grabbed_part='right_arm')
    assert response in panda.RIGHT_ARM_DRAG_RESPONSES, \
        f"Right arm drag should use RIGHT_ARM_DRAG_RESPONSES"
    
    # Test left leg drag
    response = panda.on_drag(grabbed_part='left_leg')
    assert response in panda.LEFT_LEG_DRAG_RESPONSES, \
        f"Left leg drag should use LEFT_LEG_DRAG_RESPONSES"
    
    # Test right leg drag
    response = panda.on_drag(grabbed_part='right_leg')
    assert response in panda.RIGHT_LEG_DRAG_RESPONSES, \
        f"Right leg drag should use RIGHT_LEG_DRAG_RESPONSES"
    
    # Test left ear drag
    response = panda.on_drag(grabbed_part='left_ear')
    assert response in panda.LEFT_EAR_DRAG_RESPONSES, \
        f"Left ear drag should use LEFT_EAR_DRAG_RESPONSES"
    
    # Test right ear drag
    response = panda.on_drag(grabbed_part='right_ear')
    assert response in panda.RIGHT_EAR_DRAG_RESPONSES, \
        f"Right ear drag should use RIGHT_EAR_DRAG_RESPONSES"
    
    print("✓ Individual limb drag responses work correctly")


def test_nose_and_eye_click_responses():
    """Test that nose and eyes have specific click responses."""
    panda = PandaCharacter()
    
    # Test nose click
    response = panda.on_body_part_click('nose')
    assert response in panda.BODY_PART_CLICK_RESPONSES['nose'], \
        f"Nose click should use nose-specific responses"
    
    # Test left eye click
    response = panda.on_body_part_click('left_eye')
    assert response in panda.BODY_PART_CLICK_RESPONSES['left_eye'], \
        f"Left eye click should use left_eye-specific responses"
    
    # Test right eye click
    response = panda.on_body_part_click('right_eye')
    assert response in panda.BODY_PART_CLICK_RESPONSES['right_eye'], \
        f"Right eye click should use right_eye-specific responses"
    
    print("✓ Nose and eye click responses work correctly")


def test_individual_ear_detection():
    """Test that individual ears can be detected."""
    panda = PandaCharacter()
    
    # Top left corner should be left ear
    part = panda.get_body_part_at_position(0.05, 0.05)
    assert part == 'left_ear', f"Top left corner should be 'left_ear', got {part}"
    
    # Top right corner should be right ear
    part = panda.get_body_part_at_position(0.05, 0.95)
    assert part == 'right_ear', f"Top right corner should be 'right_ear', got {part}"
    
    print("✓ Individual ear detection works correctly")


def test_facing_direction():
    """Test that panda has facing direction support."""
    from src.features.panda_character import PandaFacing
    panda = PandaCharacter()
    assert panda.facing == PandaFacing.FRONT, "Panda should face front by default"
    panda.set_facing(PandaFacing.LEFT)
    assert panda.get_facing() == PandaFacing.LEFT, "Panda should face left after set_facing"
    panda.set_facing(PandaFacing.RIGHT)
    assert panda.get_facing() == PandaFacing.RIGHT, "Panda should face right after set_facing"
    panda.set_facing(PandaFacing.BACK)
    assert panda.get_facing() == PandaFacing.BACK, "Panda should face back after set_facing"
    print("✓ Facing direction works correctly")


def test_directional_walking_animations():
    """Test that directional walking animation states exist."""
    panda = PandaCharacter()
    for direction in ('walking_left', 'walking_right', 'walking_up', 'walking_down'):
        assert direction in panda.ANIMATION_STATES, \
            f"{direction} should be in ANIMATION_STATES"
        state = panda.get_animation_state(direction)
        assert state == direction, f"get_animation_state should return {direction}"
    print("✓ Directional walking animation states exist")


def test_fall_on_face_animation():
    """Test fall_on_face animation state and response."""
    panda = PandaCharacter()
    assert 'fall_on_face' in panda.ANIMATION_STATES, \
        "fall_on_face should be in ANIMATION_STATES"
    assert panda.fall_count == 0, "fall_count should start at 0"
    response = panda.on_fall_on_face()
    assert panda.fall_count == 1, "on_fall_on_face should increment fall_count"
    assert isinstance(response, str) and len(response) > 0, \
        "on_fall_on_face should return a non-empty string"
    print("✓ Fall on face animation and response works")


def test_tip_over_animation():
    """Test tip_over_side animation state and response."""
    panda = PandaCharacter()
    assert 'tip_over_side' in panda.ANIMATION_STATES, \
        "tip_over_side should be in ANIMATION_STATES"
    assert panda.tip_over_count == 0, "tip_over_count should start at 0"
    response = panda.on_tip_over()
    assert panda.tip_over_count == 1, "on_tip_over should increment tip_over_count"
    assert isinstance(response, str) and len(response) > 0, \
        "on_tip_over should return a non-empty string"
    print("✓ Tip over animation and response works")


def test_statistics_include_facing_and_falls():
    """Test that statistics include facing, fall_count, and tip_over_count."""
    panda = PandaCharacter()
    panda.on_fall_on_face()
    panda.on_tip_over()
    stats = panda.get_statistics()
    assert 'facing' in stats, "Statistics should include facing"
    assert stats['facing'] == 'front', "facing should be 'front'"
    assert 'fall_count' in stats, "Statistics should include fall_count"
    assert stats['fall_count'] == 1
    assert 'tip_over_count' in stats, "Statistics should include tip_over_count"
    assert stats['tip_over_count'] == 1
    print("✓ Statistics include facing and fall/tip counts")


def test_spin_requires_high_velocity():
    """Test that spin detection requires MIN_SPIN_VELOCITY threshold."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'MIN_SPIN_VELOCITY'), \
            "PandaWidget should have MIN_SPIN_VELOCITY constant"
        assert PandaWidget.MIN_SPIN_VELOCITY >= 600, \
            f"MIN_SPIN_VELOCITY should be >= 600 (got {PandaWidget.MIN_SPIN_VELOCITY})"
        assert PandaWidget.MIN_SPIN_POSITIONS >= 30, \
            f"MIN_SPIN_POSITIONS should be >= 30 (got {PandaWidget.MIN_SPIN_POSITIONS})"
        assert PandaWidget.MIN_SPIN_TOTAL_ANGLE >= 6.28, \
            f"MIN_SPIN_TOTAL_ANGLE should be >= 6.28 (~2*pi) (got {PandaWidget.MIN_SPIN_TOTAL_ANGLE})"
        print("✓ Spin detection requires high velocity")
    except ImportError:
        print("⚠ Skipping spin velocity test (GUI not available)")


def test_panda_widget_facing_state():
    """Test that PandaWidget tracks facing direction."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'ANIMATION_EMOJIS'), \
            "PandaWidget should have ANIMATION_EMOJIS"
        for anim in ('walking_left', 'walking_right', 'walking_up', 'walking_down',
                      'fall_on_face', 'tip_over_side'):
            assert anim in PandaWidget.ANIMATION_EMOJIS, \
                f"{anim} should have ANIMATION_EMOJIS entry"
        print("✓ PandaWidget has animation emojis for new states")
    except ImportError:
        print("⚠ Skipping PandaWidget facing state test (GUI not available)")


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
        test_auto_walk_state_variables()
        test_accessories_routed_to_closet()
        test_belly_rub_animation_state()
        test_belly_rub_in_click_animations()
        test_animation_interval_smooth()
        # New tests for drag/touch/eat improvements
        test_drag_blocks_non_drag_animations()
        test_head_drag_responses()
        test_body_drag_responses()
        test_body_part_detection_with_x()
        test_food_pickup_response()
        test_eating_response_per_item()
        test_kick_toy_response()
        test_walk_to_food_responses()
        test_eating_sequence_constants()
        # New tests for individual limb dragging
        test_individual_limb_drag_responses()
        test_nose_and_eye_click_responses()
        test_individual_ear_detection()
        # New tests for facing direction, perspectives, and fall/tip
        test_facing_direction()
        test_directional_walking_animations()
        test_fall_on_face_animation()
        test_tip_over_animation()
        test_statistics_include_facing_and_falls()
        test_spin_requires_high_velocity()
        test_panda_widget_facing_state()

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
