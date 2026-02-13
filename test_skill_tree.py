"""
Tests for the Skill Tree system.
"""

import unittest
import os
import tempfile
from src.features.skill_tree import SkillTree, SkillNode


class TestSkillTree(unittest.TestCase):
    """Test cases for SkillTree class."""
    
    def setUp(self):
        """Create a fresh skill tree for each test."""
        self.tree = SkillTree()
    
    def test_initialization(self):
        """Test that skill tree initializes with all skills."""
        self.assertGreater(len(self.tree.skills), 0)
        
        # Check that all three branches exist
        combat_skills = self.tree.get_skills_by_branch("combat")
        magic_skills = self.tree.get_skills_by_branch("magic")
        utility_skills = self.tree.get_skills_by_branch("utility")
        
        self.assertGreater(len(combat_skills), 0)
        self.assertGreater(len(magic_skills), 0)
        self.assertGreater(len(utility_skills), 0)
    
    def test_skill_tiers(self):
        """Test that skills are organized in tiers 1-5."""
        for tier in range(1, 6):
            tier_skills = self.tree.get_skills_by_tier(tier)
            self.assertGreater(len(tier_skills), 0, f"Tier {tier} should have skills")
    
    def test_unlock_basic_skill(self):
        """Test unlocking a tier 1 skill."""
        player_level = 1
        skill_points = 10
        
        # Basic combat skill should be unlockable
        skill_id = "combat_basic_strike"
        
        self.assertTrue(self.tree.can_unlock_skill(skill_id, player_level, skill_points))
        success = self.tree.unlock_skill(skill_id, player_level, skill_points)
        self.assertTrue(success)
        self.assertTrue(self.tree.is_skill_unlocked(skill_id))
    
    def test_unlock_with_requirements(self):
        """Test that skills with requirements need prerequisites."""
        player_level = 10
        skill_points = 10
        
        # Try to unlock tier 2 skill without prerequisite
        skill_id = "combat_power_attack"
        self.assertFalse(self.tree.can_unlock_skill(skill_id, player_level, skill_points))
        
        # Unlock prerequisite
        self.tree.unlock_skill("combat_basic_strike", player_level, skill_points)
        
        # Now tier 2 skill should be unlockable
        self.assertTrue(self.tree.can_unlock_skill(skill_id, player_level, skill_points))
    
    def test_level_requirement(self):
        """Test that skills require minimum level."""
        player_level = 1
        skill_points = 10
        
        # Tier 2 skill requires level 5
        skill_id = "combat_power_attack"
        self.tree.unlock_skill("combat_basic_strike", player_level, skill_points)
        self.assertFalse(self.tree.can_unlock_skill(skill_id, player_level, skill_points))
        
        # With enough level, should be unlockable
        player_level = 5
        self.assertTrue(self.tree.can_unlock_skill(skill_id, player_level, skill_points))
    
    def test_skill_point_cost(self):
        """Test that skills cost skill points."""
        player_level = 10
        skill_points = 0  # Not enough points
        
        skill_id = "combat_basic_strike"
        self.assertFalse(self.tree.can_unlock_skill(skill_id, player_level, skill_points))
        
        # With enough points
        skill_points = 1
        self.assertTrue(self.tree.can_unlock_skill(skill_id, player_level, skill_points))
    
    def test_calculate_bonuses(self):
        """Test calculating total bonuses from unlocked skills."""
        player_level = 10
        skill_points = 10
        
        # Unlock a few skills
        self.tree.unlock_skill("combat_basic_strike", player_level, skill_points)
        self.tree.unlock_skill("combat_basic_defense", player_level, skill_points)
        
        bonuses = self.tree.calculate_total_bonuses()
        
        # Should have strength and defense bonuses
        self.assertGreater(bonuses["strength_bonus"], 0)
        self.assertGreater(bonuses["defense_bonus"], 0)
    
    def test_get_available_skills(self):
        """Test getting list of currently available skills."""
        player_level = 1
        skill_points = 10
        
        available = self.tree.get_available_skills(player_level, skill_points)
        
        # At level 1, only tier 1 skills should be available
        for skill in available:
            self.assertEqual(skill.tier, 1)
    
    def test_skill_points_spent(self):
        """Test tracking total skill points spent."""
        player_level = 10
        skill_points = 10
        
        self.tree.unlock_skill("combat_basic_strike", player_level, skill_points)
        self.tree.unlock_skill("magic_basic_spell", player_level, skill_points)
        
        spent = self.tree.get_total_skill_points_spent()
        self.assertEqual(spent, 2)  # Each tier 1 skill costs 1 point
    
    def test_reset_skills(self):
        """Test resetting all skills."""
        player_level = 10
        skill_points = 10
        
        # Unlock some skills
        self.tree.unlock_skill("combat_basic_strike", player_level, skill_points)
        self.tree.unlock_skill("magic_basic_spell", player_level, skill_points)
        
        self.assertGreater(len(self.tree.get_unlocked_skills()), 0)
        
        # Reset
        self.tree.reset_skills()
        self.assertEqual(len(self.tree.get_unlocked_skills()), 0)
    
    def test_save_and_load(self):
        """Test saving and loading skill tree state."""
        player_level = 10
        skill_points = 10
        
        # Unlock some skills
        self.tree.unlock_skill("combat_basic_strike", player_level, skill_points)
        self.tree.unlock_skill("magic_basic_spell", player_level, skill_points)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            self.tree.save_to_file(temp_path)
            
            # Load into new tree
            loaded_tree = SkillTree.load_from_file(temp_path)
            
            self.assertTrue(loaded_tree.is_skill_unlocked("combat_basic_strike"))
            self.assertTrue(loaded_tree.is_skill_unlocked("magic_basic_spell"))
        finally:
            os.unlink(temp_path)
    
    def test_ultimate_skills(self):
        """Test that ultimate skills exist and have high requirements."""
        # Check combat ultimate
        ultimate = self.tree.get_skill("combat_ultimate_warrior")
        self.assertIsNotNone(ultimate)
        self.assertEqual(ultimate.tier, 5)
        self.assertEqual(ultimate.level_required, 50)
        self.assertGreater(len(ultimate.requirements), 0)
        
        # Check magic ultimate
        ultimate = self.tree.get_skill("magic_ultimate_sorcerer")
        self.assertIsNotNone(ultimate)
        self.assertEqual(ultimate.tier, 5)
        
        # Check utility ultimate
        ultimate = self.tree.get_skill("utility_ultimate_survivor")
        self.assertIsNotNone(ultimate)
        self.assertEqual(ultimate.tier, 5)
    
    def test_skill_branches_complete(self):
        """Test that each branch has skills in all tiers."""
        for branch in ["combat", "magic", "utility"]:
            branch_skills = self.tree.get_skills_by_branch(branch)
            
            # Check that branch has skills in multiple tiers
            tiers_present = set(skill.tier for skill in branch_skills)
            self.assertGreaterEqual(len(tiers_present), 3, 
                                  f"{branch} should have skills in multiple tiers")


if __name__ == '__main__':
    unittest.main()
