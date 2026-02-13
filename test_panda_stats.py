"""
Tests for the PandaStats system.
"""

import unittest
import os
import tempfile
from src.features.panda_stats import PandaStats


class TestPandaStats(unittest.TestCase):
    """Test cases for PandaStats class."""
    
    def setUp(self):
        """Create a fresh stats instance for each test."""
        self.stats = PandaStats()
    
    def test_initialization(self):
        """Test that stats initialize with correct defaults."""
        self.assertEqual(self.stats.level, 1)
        self.assertEqual(self.stats.experience, 0)
        self.assertEqual(self.stats.health, 100)
        self.assertEqual(self.stats.max_health, 100)
        self.assertEqual(self.stats.defense, 10)
        self.assertEqual(self.stats.strength, 10)
    
    def test_experience_calculation(self):
        """Test experience requirement calculations."""
        self.assertEqual(self.stats.get_experience_for_level(1), 0)   # Level 1 requires 0 XP
        self.assertEqual(self.stats.get_experience_for_level(2), 100)  # Level 2 requires 100 XP
        self.assertEqual(self.stats.get_experience_for_level(3), 300)  # Level 3 requires 300 XP total
    
    def test_level_up(self):
        """Test leveling up mechanic."""
        initial_level = self.stats.level
        initial_health = self.stats.max_health
        initial_strength = self.stats.strength
        
        # Add enough XP to level up
        self.stats.add_experience(100)
        
        self.assertEqual(self.stats.level, initial_level + 1)
        self.assertEqual(self.stats.max_health, initial_health + 20)
        self.assertEqual(self.stats.strength, initial_strength + 2)
        self.assertEqual(self.stats.skill_points, 3)
    
    def test_multiple_level_ups(self):
        """Test multiple level ups at once."""
        self.stats.add_experience(1000)  # Enough for multiple levels
        self.assertGreater(self.stats.level, 1)
        self.assertGreater(self.stats.skill_points, 3)
    
    def test_damage_reduction(self):
        """Test defense-based damage reduction."""
        damage = 100
        reduced = self.stats.calculate_damage_reduction(damage)
        
        # With 10 defense, should reduce damage
        self.assertLess(reduced, damage)
        self.assertGreater(reduced, 0)
    
    def test_physical_damage_calculation(self):
        """Test strength-based damage bonus."""
        base_damage = 10
        boosted = self.stats.calculate_physical_damage(base_damage)
        
        # With 10 strength (20% bonus), damage should be higher
        self.assertGreater(boosted, base_damage)
    
    def test_magic_damage_calculation(self):
        """Test intelligence/magic damage bonus."""
        base_damage = 10
        boosted = self.stats.calculate_magic_damage(base_damage)
        
        # Should have intelligence and magic bonuses
        self.assertGreater(boosted, base_damage)
    
    def test_combat_stat_tracking(self):
        """Test combat stat increments."""
        self.stats.increment_attack()
        self.stats.add_monster_kill()
        self.stats.add_damage_dealt(50)
        self.stats.add_critical_hit()
        
        self.assertEqual(self.stats.total_attacks, 1)
        self.assertEqual(self.stats.monsters_slain, 1)
        self.assertEqual(self.stats.damage_dealt, 50)
        self.assertEqual(self.stats.critical_hits, 1)
    
    def test_system_stat_tracking(self):
        """Test system stat tracking."""
        self.stats.add_playtime(3600)  # 1 hour
        self.stats.add_item_collected()
        self.stats.increment_dungeons()
        self.stats.increment_floors()
        
        self.assertEqual(self.stats.playtime, 3600)
        self.assertEqual(self.stats.items_collected, 1)
        self.assertEqual(self.stats.dungeons_cleared, 1)
        self.assertEqual(self.stats.floors_explored, 1)
    
    def test_save_and_load(self):
        """Test saving and loading stats."""
        # Modify stats
        self.stats.level = 5
        self.stats.experience = 500
        self.stats.monsters_slain = 10
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            self.stats.save_to_file(temp_path)
            
            # Load back
            loaded_stats = PandaStats.load_from_file(temp_path)
            
            self.assertEqual(loaded_stats.level, 5)
            self.assertEqual(loaded_stats.experience, 500)
            self.assertEqual(loaded_stats.monsters_slain, 10)
        finally:
            os.unlink(temp_path)
    
    def test_to_dict_and_from_dict(self):
        """Test dictionary conversion."""
        self.stats.level = 3
        self.stats.monsters_slain = 5
        
        data = self.stats.to_dict()
        new_stats = PandaStats.from_dict(data)
        
        self.assertEqual(new_stats.level, 3)
        self.assertEqual(new_stats.monsters_slain, 5)
    
    def test_stat_category_getters(self):
        """Test getting stats by category."""
        base_stats = self.stats.get_base_stats()
        combat_stats = self.stats.get_combat_stats()
        system_stats = self.stats.get_system_stats()
        
        self.assertIn('Level', base_stats)
        self.assertIn('Monsters Slain', combat_stats)
        self.assertIn('Playtime', system_stats)
    
    def test_dodge_and_crit_chances(self):
        """Test derived stat calculations."""
        self.stats.agility = 100  # Should give 10% dodge, 5% crit
        
        dodge_chance = self.stats.get_dodge_chance()
        crit_chance = self.stats.get_critical_chance()
        
        self.assertEqual(dodge_chance, 10.0)
        self.assertEqual(crit_chance, 5.0)
    
    def test_take_damage_and_heal(self):
        """Test health management."""
        initial_health = self.stats.health
        
        self.stats.take_damage(30)
        self.assertLess(self.stats.health, initial_health)
        
        damaged_health = self.stats.health
        self.stats.heal(20)
        self.assertGreater(self.stats.health, damaged_health)
        self.assertLessEqual(self.stats.health, self.stats.max_health)
    
    def test_death_tracking(self):
        """Test death counter."""
        initial_deaths = self.stats.times_died
        
        # Take fatal damage
        self.stats.take_damage(1000)
        self.assertEqual(self.stats.health, 0)
        self.assertEqual(self.stats.times_died, initial_deaths + 1)
    
    def test_interaction_stats(self):
        """Test interaction stat tracking."""
        # Test clicks
        self.stats.increment_clicks()
        self.assertEqual(self.stats.click_count, 1)
        
        # Test pets
        self.stats.increment_pets()
        self.stats.increment_pets()
        self.assertEqual(self.stats.pet_count, 2)
        
        # Test feeds
        self.stats.increment_feeds()
        self.assertEqual(self.stats.feed_count, 1)
        
        # Test other interactions
        self.stats.increment_drags()
        self.stats.increment_tosses()
        self.stats.increment_shakes()
        self.assertEqual(self.stats.drag_count, 1)
        self.assertEqual(self.stats.toss_count, 1)
        self.assertEqual(self.stats.shake_count, 1)
    
    def test_interaction_stats_getter(self):
        """Test getting interaction stats as dictionary."""
        self.stats.increment_clicks()
        self.stats.increment_pets()
        self.stats.increment_belly_pokes()
        
        interaction_stats = self.stats.get_interaction_stats()
        self.assertIn('Clicks', interaction_stats)
        self.assertIn('Pets', interaction_stats)
        self.assertIn('Belly Pokes', interaction_stats)
        self.assertEqual(interaction_stats['Clicks'], 1)
        self.assertEqual(interaction_stats['Pets'], 1)
        self.assertEqual(interaction_stats['Belly Pokes'], 1)
    
    def test_system_stats_with_files(self):
        """Test system stats including file processing."""
        self.stats.track_file_processed()
        self.stats.track_file_processed()
        self.stats.track_operation_failure()
        self.stats.add_easter_egg()
        
        system_stats = self.stats.get_system_stats()
        self.assertIn('Files Processed', system_stats)
        self.assertIn('Failed Operations', system_stats)
        self.assertIn('Easter Eggs Found', system_stats)
        self.assertEqual(system_stats['Files Processed'], 2)
        self.assertEqual(system_stats['Failed Operations'], 1)
        self.assertEqual(system_stats['Easter Eggs Found'], 1)


if __name__ == '__main__':
    unittest.main()
