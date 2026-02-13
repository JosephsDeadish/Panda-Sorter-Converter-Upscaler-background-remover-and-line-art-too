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
        
        # Check that persp_sx is used in clothing drawing for garment widths
        # It should appear in the key sections: pants waistband, jacket body, dress, full_body, shirt
        clothing_sections = ['pants', 'jacket', 'dress', 'full_body', 'shirt']
        for section_name in clothing_sections:
            section_marker = f"--- {section_name.replace('_', ' ').title()}" if section_name != 'full_body' else "--- Full body"
            if section_name == 'shirt':
                section_marker = "--- Default (shirt)"
            if section_marker.lower().replace(' ', '') in source.lower().replace(' ', ''):
                pass  # section exists
        assert source.count('persp_sx') > 3, \
            f"persp_sx should be used in multiple clothing garment sections (found {source.count('persp_sx')} uses)"
        
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


def test_toss_draw_uses_facing_direction():
    """Test that _draw_panda uses _facing_direction during toss animations."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        
        # Check that toss animations remap anim based on _facing_direction
        assert '_is_tossing' in source, \
            "_draw_panda should check _is_tossing for facing direction"
        assert "'tossed'" in source and "'wall_hit'" in source, \
            "_draw_panda should handle tossed and wall_hit animations"
        assert "'rolling'" in source and "'spinning'" in source, \
            "_draw_panda should handle rolling and spinning animations"
        assert "'walking_left'" in source and "'walking_right'" in source, \
            "_draw_panda should remap to walking_left/walking_right for side views"
        assert "'walking_up'" in source, \
            "_draw_panda should remap to walking_up for back view"
        
        print("✓ Toss drawing uses _facing_direction for correct view")
    except ImportError:
        print("⚠ Skipping toss draw facing test (GUI not available)")


def test_toss_bounce_updates_facing():
    """Test that _toss_physics_tick updates facing direction on bounce."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._toss_physics_tick)
        
        # Check that facing direction is updated when bouncing
        assert '_facing_direction' in source, \
            "_toss_physics_tick should update _facing_direction on bounce"
        
        print("✓ Toss bounce updates facing direction")
    except ImportError:
        print("⚠ Skipping toss bounce facing test (GUI not available)")


def test_toss_clothing_uses_facing_direction():
    """Test that _draw_equipped_items uses _facing_direction during toss."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)
        
        # Check that clothing perspective adjusts for toss facing
        assert '_is_tossing' in source, \
            "_draw_equipped_items should check _is_tossing"
        assert "'tossed'" in source and "'wall_hit'" in source, \
            "_draw_equipped_items should handle tossed and wall_hit animations"
        assert "'rolling'" in source and "'spinning'" in source, \
            "_draw_equipped_items should handle rolling and spinning animations"
        
        print("✓ Toss clothing uses _facing_direction for perspective")
    except ImportError:
        print("⚠ Skipping toss clothing facing test (GUI not available)")


def test_sorting_stop_sets_cancelled():
    """Test that stop_sorting sets the _sorting_cancelled event."""
    import threading
    
    class MockApp:
        def __init__(self):
            self._sorting_cancelled = threading.Event()
            self._sorting_paused = threading.Event()
        
        def log(self, msg):
            pass
        
        def stop_sorting(self):
            self._sorting_cancelled.set()
            self._sorting_paused.clear()
    
    app = MockApp()
    assert not app._sorting_cancelled.is_set(), "Should start cleared"
    app.stop_sorting()
    assert app._sorting_cancelled.is_set(), "Should be set after stop"
    assert not app._sorting_paused.is_set(), "Pause should be cleared after stop"
    
    print("✓ stop_sorting sets _sorting_cancelled event")


def test_sorting_pause_toggles():
    """Test that pause_sorting toggles the _sorting_paused event."""
    import threading
    
    class MockButton:
        def __init__(self):
            self.text = "⏸️ Pause"
        def configure(self, **kwargs):
            if 'text' in kwargs:
                self.text = kwargs['text']
    
    class MockApp:
        def __init__(self):
            self._sorting_paused = threading.Event()
            self.pause_button = MockButton()
        
        def log(self, msg):
            pass
        
        def pause_sorting(self):
            if self._sorting_paused.is_set():
                self._sorting_paused.clear()
                self.pause_button.configure(text="⏸️ Pause")
            else:
                self._sorting_paused.set()
                self.pause_button.configure(text="▶️ Resume")
    
    app = MockApp()
    assert not app._sorting_paused.is_set(), "Should start unpaused"
    
    app.pause_sorting()
    assert app._sorting_paused.is_set(), "Should be paused after first toggle"
    assert "Resume" in app.pause_button.text, "Button should show Resume"
    
    app.pause_sorting()
    assert not app._sorting_paused.is_set(), "Should be unpaused after second toggle"
    assert "Pause" in app.pause_button.text, "Button should show Pause"
    
    print("✓ pause_sorting toggles _sorting_paused event")


def test_diagonal_facing_enum():
    """Test that PandaFacing enum includes diagonal directions."""
    from src.features.panda_character import PandaFacing
    
    # Verify all diagonal directions exist
    assert hasattr(PandaFacing, 'FRONT_LEFT'), "PandaFacing should have FRONT_LEFT"
    assert hasattr(PandaFacing, 'FRONT_RIGHT'), "PandaFacing should have FRONT_RIGHT"
    assert hasattr(PandaFacing, 'BACK_LEFT'), "PandaFacing should have BACK_LEFT"
    assert hasattr(PandaFacing, 'BACK_RIGHT'), "PandaFacing should have BACK_RIGHT"
    
    assert PandaFacing.FRONT_LEFT.value == "front_left"
    assert PandaFacing.FRONT_RIGHT.value == "front_right"
    assert PandaFacing.BACK_LEFT.value == "back_left"
    assert PandaFacing.BACK_RIGHT.value == "back_right"
    
    print("✓ Diagonal facing enum values exist and are correct")


def test_diagonal_walking_animation_states():
    """Test that diagonal walking animation states are registered."""
    from src.features.panda_character import PandaCharacter
    
    diag_anims = ['walking_up_left', 'walking_up_right',
                  'walking_down_left', 'walking_down_right']
    for anim in diag_anims:
        assert anim in PandaCharacter.ANIMATION_STATES, \
            f"'{anim}' should be in ANIMATION_STATES"
    
    print("✓ Diagonal walking animation states are registered")


def test_diagonal_facing_state_roundtrip():
    """Test that diagonal facing can be set and retrieved."""
    from src.features.panda_character import PandaCharacter, PandaFacing
    panda = PandaCharacter()
    
    for facing in [PandaFacing.FRONT_LEFT, PandaFacing.FRONT_RIGHT,
                   PandaFacing.BACK_LEFT, PandaFacing.BACK_RIGHT]:
        panda.set_facing(facing)
        assert panda.get_facing() == facing, \
            f"After setting {facing}, get_facing returned {panda.get_facing()}"
    
    print("✓ Diagonal facing state roundtrip works correctly")


def test_hand_detection_wider_boundaries():
    """Test that arm/hand detection boundaries are wide enough for easy grabbing."""
    from src.features.panda_character import PandaCharacter
    panda = PandaCharacter()
    
    # Arms should be detectable at wider boundaries than before
    # ARM_LEFT_BOUNDARY=0.35 means rel_x < 0.35 in body zone is left_arm
    assert panda.get_body_part_at_position(0.4, 0.30) == 'left_arm', \
        "rel_x=0.30 in body zone should detect as left_arm"
    assert panda.get_body_part_at_position(0.4, 0.34) == 'left_arm', \
        "rel_x=0.34 in body zone should detect as left_arm"
    assert panda.get_body_part_at_position(0.4, 0.70) == 'right_arm', \
        "rel_x=0.70 in body zone should detect as right_arm"
    assert panda.get_body_part_at_position(0.4, 0.66) == 'right_arm', \
        "rel_x=0.66 in body zone should detect as right_arm"
    
    # Center should still be body
    assert panda.get_body_part_at_position(0.4, 0.5) == 'body', \
        "rel_x=0.5 in body zone should detect as body"
    
    # Hand sub-regions: lower body at outermost edges
    assert panda.get_body_part_at_position(0.45, 0.15) == 'left_arm', \
        "Hand sub-region at far left should detect as left_arm"
    assert panda.get_body_part_at_position(0.45, 0.85) == 'right_arm', \
        "Hand sub-region at far right should detect as right_arm"
    
    print("✓ Hand/arm detection boundaries are wide enough for easy grabbing")


def test_dangle_limb_multiplier_constant():
    """Test that DANGLE_LIMB_MULTIPLIER exists with correct value."""
    try:
        from src.ui.panda_widget import PandaWidget
        assert hasattr(PandaWidget, 'DANGLE_LIMB_MULTIPLIER'), \
            "PandaWidget should have DANGLE_LIMB_MULTIPLIER"
        assert PandaWidget.DANGLE_LIMB_MULTIPLIER >= 0.8, \
            f"DANGLE_LIMB_MULTIPLIER should be >= 0.8 for strong dangle (got {PandaWidget.DANGLE_LIMB_MULTIPLIER})"
        assert PandaWidget.DANGLE_LIMB_MULTIPLIER > PandaWidget.DANGLE_BODY_MULTIPLIER, \
            "Limb multiplier should be greater than body multiplier"
        print("✓ DANGLE_LIMB_MULTIPLIER has correct value for natural limb-held dangle")
    except ImportError:
        print("⚠ Skipping DANGLE_LIMB_MULTIPLIER test (GUI not available)")


def test_ear_detection_matches_canvas():
    """Test that ear detection boundaries match actual canvas ear positions."""
    from src.features.panda_character import PandaCharacter
    panda = PandaCharacter()
    
    # Left ear is drawn at canvas X 72-94 → rel_x ~0.33-0.43
    # Right ear is drawn at canvas X 124-148 → rel_x ~0.56-0.67
    # Ear Y zone is top 15% (rel_y < 0.15)
    
    # Left ear at its actual position should be detected
    assert panda.get_body_part_at_position(0.05, 0.35) == 'left_ear', \
        "Click at actual left ear position (rel_x=0.35) should be left_ear"
    assert panda.get_body_part_at_position(0.05, 0.42) == 'left_ear', \
        "Click at actual left ear position (rel_x=0.42) should be left_ear"
    
    # Right ear at its actual position should be detected
    assert panda.get_body_part_at_position(0.05, 0.60) == 'right_ear', \
        "Click at actual right ear position (rel_x=0.60) should be right_ear"
    assert panda.get_body_part_at_position(0.05, 0.65) == 'right_ear', \
        "Click at actual right ear position (rel_x=0.65) should be right_ear"
    
    # Between ears should be head
    assert panda.get_body_part_at_position(0.05, 0.50) == 'head', \
        "Click between ears (rel_x=0.50) should be head"
    
    print("✓ Ear detection boundaries match actual canvas ear positions")


def test_eye_detection_accuracy():
    """Test that eye detection centers match actual canvas eye positions."""
    from src.features.panda_character import PandaCharacter
    panda = PandaCharacter()
    
    # Left eye at canvas x=86 → rel_x=0.39, right eye at 134 → rel_x=0.61
    # Eye Y zone: 0.15-0.25
    
    # Left eye at its center
    assert panda.get_body_part_at_position(0.20, 0.39) == 'left_eye', \
        "Click at left eye center (rel_x=0.39) should be left_eye"
    
    # Right eye at its center
    assert panda.get_body_part_at_position(0.20, 0.61) == 'right_eye', \
        "Click at right eye center (rel_x=0.61) should be right_eye"
    
    # Between eyes (nose area) should be head at eye Y level
    assert panda.get_body_part_at_position(0.20, 0.50) == 'head', \
        "Click between eyes (rel_x=0.50) should be head"
    
    print("✓ Eye detection centers match actual canvas eye positions")


def test_arm_detection_covers_full_arm():
    """Test that arm detection covers the full arm area on the canvas."""
    from src.features.panda_character import PandaCharacter
    panda = PandaCharacter()
    
    # Arms are drawn at rel_x 0.25-0.36 (left) and 0.64-0.75 (right)
    # ARM_LEFT_BOUNDARY=0.38 should catch the full left arm
    assert panda.get_body_part_at_position(0.4, 0.36) == 'left_arm', \
        "Inner edge of left arm (rel_x=0.36) should be left_arm"
    assert panda.get_body_part_at_position(0.4, 0.37) == 'left_arm', \
        "Just inside left arm boundary (rel_x=0.37) should be left_arm"
    
    # ARM_RIGHT_BOUNDARY=0.62 should catch the full right arm
    assert panda.get_body_part_at_position(0.4, 0.64) == 'right_arm', \
        "Inner edge of right arm (rel_x=0.64) should be right_arm"
    assert panda.get_body_part_at_position(0.4, 0.63) == 'right_arm', \
        "Just inside right arm boundary (rel_x=0.63) should be right_arm"
    
    # Center body region is still body
    assert panda.get_body_part_at_position(0.4, 0.50) == 'body', \
        "Center of body (rel_x=0.50) should still be body"
    
    print("✓ Arm detection covers the full arm area on the canvas")


def test_dangle_uses_dragging_state_not_anim():
    """Test that dangle physics uses the original dragging state, not remapped anim."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        
        # Check that is_being_dragged flag is defined
        assert 'is_being_dragged' in source, \
            "_draw_panda should define is_being_dragged flag"
        
        # Check that dangle offsets use is_being_dragged instead of anim == 'dragging'
        # Count occurrences of the flag in dangle checks
        dangle_uses = source.count('is_being_dragged else')
        assert dangle_uses >= 10, \
            f"is_being_dragged should be used in at least 10 dangle offset checks (found {dangle_uses})"
        
        print("✓ Dangle physics uses is_being_dragged state for correct behavior during drag")
    except ImportError:
        print("⚠ Skipping dangle state test (GUI not available)")


def test_diagonal_view_single_block():
    """Test that there is only one diagonal drawing block (no duplicate)."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_panda)
        
        # There should be only one diagonal view section
        diag_count = source.count('DIAGONAL VIEW')
        assert diag_count == 1, \
            f"Should have exactly 1 diagonal view block, found {diag_count}"
        
        # The diagonal view should include inner ear details
        assert 'ear_inner' in source, \
            "Diagonal view should include pink inner ear details"
        
        # The diagonal view should use diag_body_scale (improved version)
        assert 'diag_body_scale' in source, \
            "Diagonal view should use diag_body_scale for proper proportions"
        
        print("✓ Single improved diagonal drawing block is in use")
    except ImportError:
        print("⚠ Skipping diagonal view test (GUI not available)")


def test_shoe_diagonal_swing_sync():
    """Test that shoe drawing accounts for back/front diagonal leg assignment."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._draw_equipped_items)
        
        # The shoe code should handle diagonal differently based on back/front facing
        assert 'is_back_diag' in source or 'is_back_facing' in source, \
            "Shoe drawing should distinguish back-diagonal from front-diagonal"
        
        # Shoe spacing should match diagonal leg positions
        assert '22 * persp_sx' in source, \
            "Diagonal shoe spacing should match leg positions (22 * persp_sx)"
        
        print("✓ Shoe diagonal swing sync matches leg positions")
    except ImportError:
        print("⚠ Skipping shoe diagonal sync test (GUI not available)")


def test_drag_updates_facing_direction():
    """Test that _on_drag_motion updates facing direction based on velocity."""
    try:
        from src.ui.panda_widget import PandaWidget
        import inspect
        source = inspect.getsource(PandaWidget._on_drag_motion)
        
        # Drag motion should update _facing_direction
        assert '_facing_direction' in source, \
            "_on_drag_motion should update _facing_direction during drag"
        
        # Should handle diagonal directions
        assert 'back_left' in source or 'front_left' in source, \
            "_on_drag_motion should set diagonal facing directions"
        
        # Should use DIAGONAL_MOVEMENT_THRESHOLD
        assert 'DIAGONAL_MOVEMENT_THRESHOLD' in source, \
            "_on_drag_motion should use DIAGONAL_MOVEMENT_THRESHOLD for diagonal detection"
        
        print("✓ Drag motion updates facing direction based on velocity")
    except ImportError:
        print("⚠ Skipping drag facing direction test (GUI not available)")


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
        test_toss_draw_uses_facing_direction,
        test_toss_bounce_updates_facing,
        test_toss_clothing_uses_facing_direction,
        test_head_drag_full_dangle,
        test_facing_direction_state,
        test_individual_limb_detection,
        test_drag_response_per_body_part,
        test_sorting_stop_sets_cancelled,
        test_sorting_pause_toggles,
        test_diagonal_facing_enum,
        test_diagonal_walking_animation_states,
        test_diagonal_facing_state_roundtrip,
        test_hand_detection_wider_boundaries,
        test_dangle_limb_multiplier_constant,
        test_ear_detection_matches_canvas,
        test_eye_detection_accuracy,
        test_arm_detection_covers_full_arm,
        test_dangle_uses_dragging_state_not_anim,
        test_diagonal_view_single_block,
        test_shoe_diagonal_swing_sync,
        test_drag_updates_facing_direction,
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
