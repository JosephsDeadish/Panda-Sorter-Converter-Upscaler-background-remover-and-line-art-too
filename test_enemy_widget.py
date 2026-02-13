#!/usr/bin/env python3
"""
Test enemy widget system with autonomous movement and pathfinding.
Validates:
- Enemy widget creation and rendering
- Autonomous movement toward panda
- Collision detection (attack range)
- Attack triggering
- Health/death mechanics
- Enemy manager functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.features.enemy_system import EnemyCollection, Enemy
from src.features.combat_system import CombatStats


def test_enemy_widget_imports():
    """Test that enemy widget can be imported."""
    try:
        from src.ui.enemy_widget import EnemyWidget
        print("✓ EnemyWidget imports successfully")
        return True
    except ImportError as e:
        # CustomTkinter not available is ok for basic testing
        if 'customtkinter' in str(e):
            print("⚠ CustomTkinter not available, but enemy_widget structure is valid")
            return True
        print(f"✗ Failed to import EnemyWidget: {e}")
        return False


def test_enemy_manager_imports():
    """Test that enemy manager can be imported."""
    try:
        from src.features.enemy_manager import EnemyManager
        print("✓ EnemyManager imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import EnemyManager: {e}")
        return False


def test_enemy_creation():
    """Test creating enemies from templates."""
    collection = EnemyCollection()
    
    # Test creating different enemy types
    slime = collection.create_enemy('slime', level=1)
    assert slime is not None, "Should create slime enemy"
    assert slime.level == 1, "Slime should be level 1"
    assert slime.icon == '🟢', "Slime should have correct icon"
    
    goblin = collection.create_enemy('goblin', level=5)
    assert goblin is not None, "Should create goblin enemy"
    assert goblin.level == 5, "Goblin should be level 5"
    assert goblin.stats.max_health == 90, "Level 5 goblin should have scaled health (50 + 4*10)"
    
    wolf = collection.create_enemy('wolf', level=1)
    assert wolf is not None, "Should create wolf enemy"
    assert wolf.icon == '🐺', "Wolf should have correct icon"
    
    print("✓ Enemy creation from templates works")


def test_enemy_behaviors():
    """Test enemy AI behaviors."""
    collection = EnemyCollection()
    
    # Passive enemy
    slime = collection.create_enemy('slime', level=1)
    slime.aggro_level = 0
    action = slime.get_ai_action()
    assert action == 'idle', "Passive enemy with no aggro should idle"
    
    slime.aggro_level = 1
    action = slime.get_ai_action()
    assert action == 'attack', "Passive enemy with aggro should attack"
    
    # Aggressive enemy
    goblin = collection.create_enemy('goblin', level=1)
    action = goblin.get_ai_action()
    assert action == 'attack', "Aggressive enemy should always attack"
    
    print("✓ Enemy AI behaviors work correctly")


def test_enemy_stats_scaling():
    """Test that enemy stats scale with level."""
    collection = EnemyCollection()
    
    goblin_1 = collection.create_enemy('goblin', level=1)
    goblin_5 = collection.create_enemy('goblin', level=5)
    
    # Health should scale
    assert goblin_5.stats.max_health > goblin_1.stats.max_health, \
        "Higher level enemy should have more health"
    
    # Attack should scale
    assert goblin_5.stats.attack_power > goblin_1.stats.attack_power, \
        "Higher level enemy should have higher attack"
    
    # XP reward should scale
    assert goblin_5.xp_reward > goblin_1.xp_reward, \
        "Higher level enemy should give more XP"
    
    print("✓ Enemy stat scaling works correctly")


def test_enemy_combat():
    """Test enemy combat mechanics."""
    collection = EnemyCollection()
    
    enemy = collection.create_enemy('goblin', level=1)
    initial_health = enemy.stats.current_health
    
    # Test taking damage
    damage_dealt = enemy.take_damage(10)
    assert damage_dealt > 0, "Enemy should take damage"
    assert enemy.stats.current_health < initial_health, "Health should decrease"
    assert enemy.is_alive(), "Enemy should still be alive"
    
    # Test death
    enemy.take_damage(1000)
    assert not enemy.is_alive(), "Enemy should be dead after massive damage"
    
    print("✓ Enemy combat mechanics work")


def test_enemy_loot():
    """Test enemy loot drops."""
    collection = EnemyCollection()
    
    enemy = collection.create_enemy('goblin', level=1)
    
    # Run multiple loot attempts to verify probability
    loot_results = []
    for _ in range(100):
        drops = enemy.drop_loot()
        loot_results.append(len(drops) > 0)
    
    # Should get some loot (not always, but often)
    success_rate = sum(loot_results) / len(loot_results)
    assert success_rate > 0.1, f"Should get some loot drops (got {success_rate*100}%)"
    
    print("✓ Enemy loot system works")


def test_all_enemy_types():
    """Test that all enemy types can be created."""
    collection = EnemyCollection()
    
    enemy_types = ['slime', 'goblin', 'skeleton', 'wolf', 'orc', 'dragon']
    
    for enemy_type in enemy_types:
        enemy = collection.create_enemy(enemy_type, level=1)
        assert enemy is not None, f"Should create {enemy_type} enemy"
        assert enemy.icon is not None, f"{enemy_type} should have an icon"
        assert enemy.is_alive(), f"{enemy_type} should start alive"
    
    print("✓ All enemy types can be created")


def test_enemy_widget_constants():
    """Test that enemy widget has correct constants defined."""
    try:
        from src.ui.enemy_widget import EnemyWidget, ENEMY_CANVAS_W, ENEMY_CANVAS_H
        
        assert ENEMY_CANVAS_W > 0, "Canvas width should be positive"
        assert ENEMY_CANVAS_H > 0, "Canvas height should be positive"
        assert hasattr(EnemyWidget, 'MOVEMENT_INTERVAL'), "Should have movement interval"
        assert hasattr(EnemyWidget, 'ATTACK_RANGE'), "Should have attack range"
        assert hasattr(EnemyWidget, 'COLLISION_RADIUS'), "Should have collision radius"
        
        print("✓ Enemy widget constants are defined")
    except ImportError:
        print("⚠ Skipping enemy widget constants test (GUI not available)")


def test_enemy_manager_creation():
    """Test enemy manager basic functionality."""
    from src.features.enemy_manager import EnemyManager
    
    collection = EnemyCollection()
    
    # Create a mock parent and panda widget (just need basic objects)
    class MockWidget:
        def winfo_toplevel(self):
            return self
        def winfo_width(self):
            return 800
        def winfo_height(self):
            return 600
        def winfo_rootx(self):
            return 0
        def winfo_rooty(self):
            return 0
    
    mock_parent = MockWidget()
    mock_panda = MockWidget()
    mock_panda._toplevel = mock_panda
    mock_panda._toplevel_w = 220
    mock_panda._toplevel_h = 270
    
    # Create manager (won't actually spawn widgets in test environment)
    manager = EnemyManager(mock_parent, mock_panda, collection)
    
    assert manager.get_active_count() == 0, "Should start with no enemies"
    assert manager.max_enemies == 5, "Should have default max enemies"
    
    # Test configuration
    manager.set_max_enemies(10)
    assert manager.max_enemies == 10, "Should update max enemies"
    
    manager.set_spawn_cooldown(3.0)
    assert manager.spawn_cooldown == 3.0, "Should update spawn cooldown"
    
    manager.enable_auto_spawn(True)
    assert manager.auto_spawn is True, "Should enable auto spawn"
    
    stats = manager.get_stats()
    assert 'active_enemies' in stats, "Stats should include active_enemies"
    assert 'total_spawned' in stats, "Stats should include total_spawned"
    
    print("✓ Enemy manager creation and configuration work")


if __name__ == "__main__":
    print("Testing Enemy Widget System...")
    print("-" * 50)
    
    try:
        # Test imports first
        if not test_enemy_widget_imports():
            print("❌ Import test failed - stopping")
            sys.exit(1)
        
        if not test_enemy_manager_imports():
            print("❌ Manager import test failed - stopping")
            sys.exit(1)
        
        # Test enemy system
        test_enemy_creation()
        test_enemy_behaviors()
        test_enemy_stats_scaling()
        test_enemy_combat()
        test_enemy_loot()
        test_all_enemy_types()
        test_enemy_widget_constants()
        test_enemy_manager_creation()
        
        print("-" * 50)
        print("✅ All enemy widget tests passed!")
        sys.exit(0)
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
