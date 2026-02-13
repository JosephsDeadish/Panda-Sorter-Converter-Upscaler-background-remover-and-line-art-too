"""
Tests for the integrated dungeon system.
"""

import unittest
from src.features.integrated_dungeon import IntegratedDungeon, LootItem, SpawnedEnemy


class TestIntegratedDungeon(unittest.TestCase):
    """Test cases for integrated dungeon system."""
    
    def setUp(self):
        """Set up test dungeon."""
        self.dungeon = IntegratedDungeon(width=50, height=50, num_floors=3, seed=12345)
    
    def test_dungeon_creation(self):
        """Test that integrated dungeon is created properly."""
        self.assertIsNotNone(self.dungeon.dungeon)
        self.assertEqual(len(self.dungeon.dungeon.floors), 3)
    
    def test_enemy_spawning(self):
        """Test that enemies are spawned on floors."""
        # Check that enemies exist on each floor
        for floor_num in range(3):
            self.assertIn(floor_num, self.dungeon.enemies_by_floor)
            enemies = self.dungeon.enemies_by_floor[floor_num]
            self.assertGreater(len(enemies), 0, f"Floor {floor_num} should have enemies")
    
    def test_loot_spawning(self):
        """Test that loot is spawned on floors."""
        # Check that loot exists
        total_loot = sum(len(loot_list) for loot_list in self.dungeon.loot_by_floor.values())
        self.assertGreater(total_loot, 0, "Dungeon should have loot")
    
    def test_player_movement(self):
        """Test player movement."""
        self.dungeon.teleport_to_spawn()
        initial_x = self.dungeon.player_x
        initial_y = self.dungeon.player_y
        
        # Try to move
        moved = self.dungeon.move_player(1, 0)
        
        # Movement might be blocked by wall, but function should work
        self.assertIsInstance(moved, bool)
    
    def test_player_state(self):
        """Test player state retrieval."""
        state = self.dungeon.get_player_state()
        
        self.assertIn('floor', state)
        self.assertIn('x', state)
        self.assertIn('y', state)
        self.assertIn('health', state)
        self.assertIn('max_health', state)
        self.assertEqual(state['health'], 100)
        self.assertEqual(state['max_health'], 100)
    
    def test_get_enemies_on_floor(self):
        """Test getting enemies on current floor."""
        self.dungeon.player_floor = 0
        enemies = self.dungeon.get_enemies_on_current_floor()
        
        self.assertIsInstance(enemies, list)
        if len(enemies) > 0:
            self.assertIsInstance(enemies[0], SpawnedEnemy)
            self.assertTrue(enemies[0].is_alive)
    
    def test_get_loot_on_floor(self):
        """Test getting loot on current floor."""
        self.dungeon.player_floor = 0
        loot = self.dungeon.get_loot_on_current_floor()
        
        self.assertIsInstance(loot, list)
        if len(loot) > 0:
            self.assertIsInstance(loot[0], LootItem)
            self.assertFalse(loot[0].collected)
    
    def test_enemy_difficulty_scaling(self):
        """Test that enemies get harder on lower floors."""
        # Get enemies from first and last floor
        floor_0_enemies = [e for e in self.dungeon.enemies_by_floor.get(0, []) if e.is_alive]
        floor_2_enemies = [e for e in self.dungeon.enemies_by_floor.get(2, []) if e.is_alive]
        
        if floor_0_enemies and floor_2_enemies:
            avg_hp_0 = sum(e.enemy.stats.max_health for e in floor_0_enemies) / len(floor_0_enemies)
            avg_hp_2 = sum(e.enemy.stats.max_health for e in floor_2_enemies) / len(floor_2_enemies)
            
            # Lower floors should have higher HP enemies (indicating difficulty)
            self.assertGreater(avg_hp_2, avg_hp_0)
    
    def test_player_attack(self):
        """Test player attack functionality."""
        initial_kills = self.dungeon.enemies_killed
        
        # Attack (might not hit anything)
        self.dungeon.player_attack_nearby_enemies(weapon_damage=25)
        
        # Kills should not decrease
        self.assertGreaterEqual(self.dungeon.enemies_killed, initial_kills)
    
    def test_spawn_point_exists(self):
        """Test that spawn points exist on all floors."""
        for floor_num in range(len(self.dungeon.dungeon.floors)):
            floor = self.dungeon.dungeon.get_floor(floor_num)
            self.assertIsNotNone(floor.spawn_point, f"Floor {floor_num} should have spawn point")
    
    def test_random_generation_without_seed(self):
        """Test that dungeon generation works without fixed seed."""
        # Create dungeon without seed
        dungeon1 = IntegratedDungeon(width=50, height=50, num_floors=3)
        dungeon2 = IntegratedDungeon(width=50, height=50, num_floors=3)
        
        # Both should be valid
        self.assertEqual(len(dungeon1.dungeon.floors), 3)
        self.assertEqual(len(dungeon2.dungeon.floors), 3)
        
        # Should have enemies and loot
        self.assertGreater(sum(len(e) for e in dungeon1.enemies_by_floor.values()), 0)
        self.assertGreater(sum(len(l) for l in dungeon1.loot_by_floor.values()), 0)


if __name__ == '__main__':
    unittest.main()
