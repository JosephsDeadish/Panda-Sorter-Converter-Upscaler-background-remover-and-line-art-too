#!/usr/bin/env python3
"""
Test visual effects renderer structure.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.features.damage_system import DamageTracker, DamageCategory, LimbType


def test_visual_effects_file_exists():
    """Test that visual effects renderer file exists."""
    vfx_path = Path(__file__).parent / "src/ui/visual_effects_renderer.py"
    assert vfx_path.exists(), "Visual effects renderer file should exist"
    
    # Check it has the right content
    content = vfx_path.read_text()
    assert "VisualEffectsRenderer" in content
    assert "render_wounds" in content
    assert "render_projectile" in content
    assert "render_stuck_projectiles" in content
    
    print("✓ Visual effects renderer file exists with correct structure")


def test_damage_tracker_wounds_for_rendering():
    """Test that damage tracker provides wounds for rendering."""
    tracker = DamageTracker()
    
    # Apply various damage
    tracker.apply_damage(LimbType.TORSO, DamageCategory.SHARP, 30)
    tracker.apply_damage(LimbType.LEFT_ARM, DamageCategory.BLUNT, 25)
    tracker.apply_damage(LimbType.RIGHT_LEG, DamageCategory.FIRE, 20)
    
    # Get wounds
    wounds = tracker.get_all_wounds()
    
    assert len(wounds) > 0, "Should have wounds to render"
    
    for wound in wounds:
        assert hasattr(wound, 'wound_type')
        assert hasattr(wound, 'position')
        assert hasattr(wound, 'size')
        assert hasattr(wound, 'color')
        assert hasattr(wound, 'limb')
    
    print("✓ Damage tracker provides renderable wound data")


def test_stuck_projectiles_for_rendering():
    """Test that stuck projectiles can be retrieved for rendering."""
    tracker = DamageTracker()
    
    # Add stuck projectiles
    tracker.add_stuck_projectile("arrow", (10, 20), LimbType.TORSO)
    tracker.add_stuck_projectile("bolt", (15, 25), LimbType.LEFT_ARM)
    
    # Get stuck projectiles
    projectiles = tracker.get_stuck_projectiles()
    
    assert len(projectiles) == 2, "Should have 2 stuck projectiles"
    
    for proj in projectiles:
        assert hasattr(proj, 'projectile_type')
        assert hasattr(proj, 'position')
        assert hasattr(proj, 'limb')
    
    print("✓ Stuck projectiles are accessible for rendering")


def test_bleeding_effect_data():
    """Test bleeding rate data for rendering."""
    tracker = DamageTracker()
    
    # Initial bleeding
    assert tracker.total_bleeding_rate == 0.0
    
    # Apply sharp damage
    tracker.apply_damage(LimbType.TORSO, DamageCategory.SHARP, 50)
    
    # Should have bleeding now
    assert tracker.total_bleeding_rate > 0, "Should have bleeding from sharp damage"
    
    print("✓ Bleeding rate data available for rendering")


def test_visual_integration_ready():
    """Test that all data structures are ready for visual integration."""
    tracker = DamageTracker()
    
    # Apply comprehensive damage
    tracker.apply_damage(LimbType.HEAD, DamageCategory.SHARP, 30)
    tracker.apply_damage(LimbType.TORSO, DamageCategory.BLUNT, 40)
    tracker.apply_damage(LimbType.LEFT_ARM, DamageCategory.FIRE, 25)
    tracker.add_stuck_projectile("arrow", (5, 10), LimbType.TORSO)
    
    # Get all rendering data
    wounds = tracker.get_all_wounds()
    projectiles = tracker.get_stuck_projectiles()
    bleeding_rate = tracker.total_bleeding_rate
    move_penalty = tracker.get_movement_penalty()
    attack_penalty = tracker.get_attack_penalty()
    
    # Verify data is available
    assert len(wounds) > 0
    assert len(projectiles) > 0
    assert bleeding_rate > 0
    assert move_penalty >= 0
    assert attack_penalty >= 0
    
    print("✓ All visual integration data structures ready")


def test_demo_file_exists():
    """Test that demo file exists."""
    demo_path = Path(__file__).parent / "demo_combat_visual.py"
    assert demo_path.exists(), "Combat visual demo should exist"
    
    content = demo_path.read_text()
    assert "CombatDemo" in content
    assert "VisualEffectsRenderer" in content
    
    print("✓ Combat visual demo exists")


if __name__ == "__main__":
    print("Testing Visual Effects Integration...")
    print("-" * 50)
    
    try:
        test_visual_effects_file_exists()
        test_damage_tracker_wounds_for_rendering()
        test_stuck_projectiles_for_rendering()
        test_bleeding_effect_data()
        test_visual_integration_ready()
        test_demo_file_exists()
        
        print("-" * 50)
        print("✅ All visual effects integration tests passed!")
        print("\nNote: Full rendering tests require tkinter GUI environment.")
        print("Run demo_combat_visual.py in a GUI environment to see effects.")
        sys.exit(0)
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
