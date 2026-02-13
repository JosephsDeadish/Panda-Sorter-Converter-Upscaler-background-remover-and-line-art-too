"""
Extensive skill tree system for the panda character.
Includes combat, magic, and utility skill branches with dependencies.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import json


@dataclass
class SkillNode:
    """Represents a single skill in the skill tree."""
    
    id: str
    name: str
    description: str
    branch: str  # "combat", "magic", "utility"
    tier: int  # 1-5 (tier 1 = basic, tier 5 = ultimate)
    cost: int  # Skill points required
    requirements: List[str] = field(default_factory=list)  # Required skill IDs
    level_required: int = 1  # Minimum level needed
    unlocked: bool = False
    
    # Skill effects (stat bonuses/abilities)
    effects: Dict = field(default_factory=dict)
    
    def can_unlock(self, skill_tree: 'SkillTree', player_level: int, skill_points: int) -> bool:
        """Check if this skill can be unlocked."""
        if self.unlocked:
            return False
        
        if player_level < self.level_required:
            return False
        
        if skill_points < self.cost:
            return False
        
        # Check if all required skills are unlocked
        for req_id in self.requirements:
            if not skill_tree.is_skill_unlocked(req_id):
                return False
        
        return True


class SkillTree:
    """
    Extensive skill tree system with three branches:
    - Combat: Physical combat, weapons, defense
    - Magic: Spells, elemental attacks, magic power
    - Utility: Movement, healing, survivability
    """
    
    def __init__(self):
        """Initialize the skill tree with all nodes."""
        self.skills: Dict[str, SkillNode] = {}
        self._initialize_skill_tree()
    
    def _initialize_skill_tree(self):
        """Create all skill nodes in the tree."""
        # Combat Branch
        self._add_combat_skills()
        
        # Magic Branch
        self._add_magic_skills()
        
        # Utility Branch
        self._add_utility_skills()
    
    def _add_combat_skills(self):
        """Add combat branch skills."""
        # Tier 1 - Basic Combat
        self.add_skill(SkillNode(
            id="combat_basic_strike",
            name="Basic Strike",
            description="Increases physical damage by 10%",
            branch="combat",
            tier=1,
            cost=1,
            level_required=1,
            effects={"strength_bonus": 5}
        ))
        
        self.add_skill(SkillNode(
            id="combat_basic_defense",
            name="Basic Defense",
            description="Increases defense by 5",
            branch="combat",
            tier=1,
            cost=1,
            level_required=1,
            effects={"defense_bonus": 5}
        ))
        
        # Tier 2 - Advanced Combat
        self.add_skill(SkillNode(
            id="combat_power_attack",
            name="Power Attack",
            description="Increases physical damage by 20%",
            branch="combat",
            tier=2,
            cost=2,
            requirements=["combat_basic_strike"],
            level_required=5,
            effects={"strength_bonus": 10}
        ))
        
        self.add_skill(SkillNode(
            id="combat_iron_skin",
            name="Iron Skin",
            description="Increases defense by 10",
            branch="combat",
            tier=2,
            cost=2,
            requirements=["combat_basic_defense"],
            level_required=5,
            effects={"defense_bonus": 10}
        ))
        
        self.add_skill(SkillNode(
            id="combat_critical_strikes",
            name="Critical Strikes",
            description="Increases critical hit chance by 5%",
            branch="combat",
            tier=2,
            cost=2,
            requirements=["combat_basic_strike"],
            level_required=5,
            effects={"agility_bonus": 10}
        ))
        
        # Tier 3 - Expert Combat
        self.add_skill(SkillNode(
            id="combat_berserker",
            name="Berserker",
            description="Increases damage by 30%, reduces defense by 5",
            branch="combat",
            tier=3,
            cost=3,
            requirements=["combat_power_attack"],
            level_required=15,
            effects={"strength_bonus": 20, "defense_bonus": -5}
        ))
        
        self.add_skill(SkillNode(
            id="combat_tank",
            name="Tank",
            description="Increases defense by 20, max health by 50",
            branch="combat",
            tier=3,
            cost=3,
            requirements=["combat_iron_skin"],
            level_required=15,
            effects={"defense_bonus": 20, "max_health_bonus": 50}
        ))
        
        self.add_skill(SkillNode(
            id="combat_deadly_precision",
            name="Deadly Precision",
            description="Critical hits deal 50% more damage",
            branch="combat",
            tier=3,
            cost=3,
            requirements=["combat_critical_strikes"],
            level_required=15,
            effects={"crit_damage_bonus": 50}
        ))
        
        # Tier 4 - Master Combat
        self.add_skill(SkillNode(
            id="combat_weapon_master",
            name="Weapon Master",
            description="Increases all weapon damage by 40%",
            branch="combat",
            tier=4,
            cost=4,
            requirements=["combat_berserker", "combat_deadly_precision"],
            level_required=30,
            effects={"strength_bonus": 30, "agility_bonus": 15}
        ))
        
        self.add_skill(SkillNode(
            id="combat_fortress",
            name="Fortress",
            description="Become nearly invulnerable: +40 defense, +100 HP",
            branch="combat",
            tier=4,
            cost=4,
            requirements=["combat_tank"],
            level_required=30,
            effects={"defense_bonus": 40, "max_health_bonus": 100}
        ))
        
        # Tier 5 - Ultimate Combat
        self.add_skill(SkillNode(
            id="combat_ultimate_warrior",
            name="Ultimate Warrior",
            description="The peak of combat mastery: +50 STR, +30 DEF, +20 AGI",
            branch="combat",
            tier=5,
            cost=5,
            requirements=["combat_weapon_master", "combat_fortress"],
            level_required=50,
            effects={"strength_bonus": 50, "defense_bonus": 30, "agility_bonus": 20}
        ))
    
    def _add_magic_skills(self):
        """Add magic branch skills."""
        # Tier 1 - Basic Magic
        self.add_skill(SkillNode(
            id="magic_basic_spell",
            name="Basic Spellcasting",
            description="Increases magic power by 5",
            branch="magic",
            tier=1,
            cost=1,
            level_required=1,
            effects={"magic_bonus": 5}
        ))
        
        self.add_skill(SkillNode(
            id="magic_mana_pool",
            name="Expanded Mana Pool",
            description="Increases intelligence by 5",
            branch="magic",
            tier=1,
            cost=1,
            level_required=1,
            effects={"intelligence_bonus": 5}
        ))
        
        # Tier 2 - Elemental Magic
        self.add_skill(SkillNode(
            id="magic_fire",
            name="Fire Magic",
            description="Unlock fire spells, +10 magic damage",
            branch="magic",
            tier=2,
            cost=2,
            requirements=["magic_basic_spell"],
            level_required=5,
            effects={"magic_bonus": 10, "unlock_fire": True}
        ))
        
        self.add_skill(SkillNode(
            id="magic_ice",
            name="Ice Magic",
            description="Unlock ice spells, +10 magic damage",
            branch="magic",
            tier=2,
            cost=2,
            requirements=["magic_basic_spell"],
            level_required=5,
            effects={"magic_bonus": 10, "unlock_ice": True}
        ))
        
        self.add_skill(SkillNode(
            id="magic_lightning",
            name="Lightning Magic",
            description="Unlock lightning spells, +10 magic damage",
            branch="magic",
            tier=2,
            cost=2,
            requirements=["magic_basic_spell"],
            level_required=5,
            effects={"magic_bonus": 10, "unlock_lightning": True}
        ))
        
        self.add_skill(SkillNode(
            id="magic_scholar",
            name="Scholar",
            description="Increases intelligence by 15",
            branch="magic",
            tier=2,
            cost=2,
            requirements=["magic_mana_pool"],
            level_required=5,
            effects={"intelligence_bonus": 15}
        ))
        
        # Tier 3 - Advanced Magic
        self.add_skill(SkillNode(
            id="magic_elemental_master",
            name="Elemental Master",
            description="Master all elements, +20 magic power",
            branch="magic",
            tier=3,
            cost=3,
            requirements=["magic_fire", "magic_ice", "magic_lightning"],
            level_required=15,
            effects={"magic_bonus": 20, "intelligence_bonus": 10}
        ))
        
        self.add_skill(SkillNode(
            id="magic_arcane_power",
            name="Arcane Power",
            description="Increases magic and intelligence by 20",
            branch="magic",
            tier=3,
            cost=3,
            requirements=["magic_scholar"],
            level_required=15,
            effects={"magic_bonus": 20, "intelligence_bonus": 20}
        ))
        
        # Tier 4 - Master Magic
        self.add_skill(SkillNode(
            id="magic_archmage",
            name="Archmage",
            description="Become a master of magic: +40 MAG, +30 INT",
            branch="magic",
            tier=4,
            cost=4,
            requirements=["magic_elemental_master", "magic_arcane_power"],
            level_required=30,
            effects={"magic_bonus": 40, "intelligence_bonus": 30}
        ))
        
        # Tier 5 - Ultimate Magic
        self.add_skill(SkillNode(
            id="magic_ultimate_sorcerer",
            name="Ultimate Sorcerer",
            description="The peak of magical mastery: +60 MAG, +50 INT",
            branch="magic",
            tier=5,
            cost=5,
            requirements=["magic_archmage"],
            level_required=50,
            effects={"magic_bonus": 60, "intelligence_bonus": 50}
        ))
    
    def _add_utility_skills(self):
        """Add utility branch skills."""
        # Tier 1 - Basic Utility
        self.add_skill(SkillNode(
            id="utility_healing",
            name="Basic Healing",
            description="Increases healing effectiveness by 20%",
            branch="utility",
            tier=1,
            cost=1,
            level_required=1,
            effects={"healing_bonus": 20}
        ))
        
        self.add_skill(SkillNode(
            id="utility_speed",
            name="Fleet Footed",
            description="Increases movement speed by 10%",
            branch="utility",
            tier=1,
            cost=1,
            level_required=1,
            effects={"agility_bonus": 5}
        ))
        
        self.add_skill(SkillNode(
            id="utility_vitality",
            name="Hardy",
            description="Increases max health by 30",
            branch="utility",
            tier=1,
            cost=1,
            level_required=1,
            effects={"vitality_bonus": 3}
        ))
        
        # Tier 2 - Advanced Utility
        self.add_skill(SkillNode(
            id="utility_regeneration",
            name="Regeneration",
            description="Slowly regenerate health over time",
            branch="utility",
            tier=2,
            cost=2,
            requirements=["utility_healing"],
            level_required=5,
            effects={"health_regen": 2, "healing_bonus": 30}
        ))
        
        self.add_skill(SkillNode(
            id="utility_dodge",
            name="Evasion",
            description="Increases dodge chance by 10%",
            branch="utility",
            tier=2,
            cost=2,
            requirements=["utility_speed"],
            level_required=5,
            effects={"agility_bonus": 20}
        ))
        
        self.add_skill(SkillNode(
            id="utility_toughness",
            name="Toughness",
            description="Increases max health by 80",
            branch="utility",
            tier=2,
            cost=2,
            requirements=["utility_vitality"],
            level_required=5,
            effects={"vitality_bonus": 8}
        ))
        
        # Tier 3 - Expert Utility
        self.add_skill(SkillNode(
            id="utility_life_drain",
            name="Life Drain",
            description="Heal for 20% of damage dealt",
            branch="utility",
            tier=3,
            cost=3,
            requirements=["utility_regeneration"],
            level_required=15,
            effects={"life_steal": 20, "healing_bonus": 50}
        ))
        
        self.add_skill(SkillNode(
            id="utility_untouchable",
            name="Untouchable",
            description="Dramatically increases dodge chance",
            branch="utility",
            tier=3,
            cost=3,
            requirements=["utility_dodge"],
            level_required=15,
            effects={"agility_bonus": 40}
        ))
        
        self.add_skill(SkillNode(
            id="utility_iron_will",
            name="Iron Will",
            description="Increases max health by 150",
            branch="utility",
            tier=3,
            cost=3,
            requirements=["utility_toughness"],
            level_required=15,
            effects={"vitality_bonus": 15, "max_health_bonus": 50}
        ))
        
        # Tier 4 - Master Utility
        self.add_skill(SkillNode(
            id="utility_survivor",
            name="Survivor",
            description="Massive health and regen: +200 HP, heal 5/sec",
            branch="utility",
            tier=4,
            cost=4,
            requirements=["utility_life_drain", "utility_iron_will"],
            level_required=30,
            effects={"max_health_bonus": 200, "health_regen": 5, "vitality_bonus": 20}
        ))
        
        self.add_skill(SkillNode(
            id="utility_perfect_dodge",
            name="Perfect Dodge",
            description="Master evasion: +50 AGI, +20% dodge",
            branch="utility",
            tier=4,
            cost=4,
            requirements=["utility_untouchable"],
            level_required=30,
            effects={"agility_bonus": 50, "dodge_bonus": 20}
        ))
        
        # Tier 5 - Ultimate Utility
        self.add_skill(SkillNode(
            id="utility_ultimate_survivor",
            name="Ultimate Survivor",
            description="The peak of survival: +300 HP, +60 VIT, +50 AGI, heal 10/sec",
            branch="utility",
            tier=5,
            cost=5,
            requirements=["utility_survivor", "utility_perfect_dodge"],
            level_required=50,
            effects={"max_health_bonus": 300, "vitality_bonus": 60, "agility_bonus": 50, "health_regen": 10}
        ))
    
    def add_skill(self, skill: SkillNode):
        """Add a skill node to the tree."""
        self.skills[skill.id] = skill
    
    def get_skill(self, skill_id: str) -> Optional[SkillNode]:
        """Get a skill by ID."""
        return self.skills.get(skill_id)
    
    def is_skill_unlocked(self, skill_id: str) -> bool:
        """Check if a skill is unlocked."""
        skill = self.get_skill(skill_id)
        return skill.unlocked if skill else False
    
    def can_unlock_skill(self, skill_id: str, player_level: int, skill_points: int) -> bool:
        """Check if a skill can be unlocked."""
        skill = self.get_skill(skill_id)
        if not skill:
            return False
        return skill.can_unlock(self, player_level, skill_points)
    
    def unlock_skill(self, skill_id: str, player_level: int, skill_points: int) -> bool:
        """
        Attempt to unlock a skill.
        Returns True if successful, False otherwise.
        """
        skill = self.get_skill(skill_id)
        if not skill:
            return False
        
        if not skill.can_unlock(self, player_level, skill_points):
            return False
        
        skill.unlocked = True
        return True
    
    def get_unlocked_skills(self) -> List[SkillNode]:
        """Get all unlocked skills."""
        return [skill for skill in self.skills.values() if skill.unlocked]
    
    def get_skills_by_branch(self, branch: str) -> List[SkillNode]:
        """Get all skills in a specific branch."""
        return [skill for skill in self.skills.values() if skill.branch == branch]
    
    def get_skills_by_tier(self, tier: int) -> List[SkillNode]:
        """Get all skills in a specific tier."""
        return [skill for skill in self.skills.values() if skill.tier == tier]
    
    def get_available_skills(self, player_level: int, skill_points: int) -> List[SkillNode]:
        """Get all skills that can currently be unlocked."""
        return [
            skill for skill in self.skills.values()
            if skill.can_unlock(self, player_level, skill_points)
        ]
    
    def calculate_total_bonuses(self) -> Dict:
        """Calculate total bonuses from all unlocked skills."""
        bonuses = {
            "strength_bonus": 0,
            "defense_bonus": 0,
            "magic_bonus": 0,
            "intelligence_bonus": 0,
            "agility_bonus": 0,
            "vitality_bonus": 0,
            "max_health_bonus": 0,
            "healing_bonus": 0,
            "health_regen": 0,
            "life_steal": 0,
            "crit_damage_bonus": 0,
            "dodge_bonus": 0,
        }
        
        for skill in self.get_unlocked_skills():
            for effect_key, effect_value in skill.effects.items():
                if effect_key in bonuses:
                    bonuses[effect_key] += effect_value
        
        return bonuses
    
    def get_total_skill_points_spent(self) -> int:
        """Calculate total skill points spent."""
        return sum(skill.cost for skill in self.get_unlocked_skills())
    
    def reset_skills(self):
        """Reset all unlocked skills."""
        for skill in self.skills.values():
            skill.unlocked = False
    
    def to_dict(self) -> Dict:
        """Convert skill tree to dictionary (for saving)."""
        return {
            skill_id: skill.unlocked
            for skill_id, skill in self.skills.items()
        }
    
    def load_from_dict(self, data: Dict):
        """Load skill unlocked states from dictionary."""
        for skill_id, unlocked in data.items():
            if skill_id in self.skills:
                self.skills[skill_id].unlocked = unlocked
    
    def save_to_file(self, filepath: str):
        """Save skill tree state to file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'SkillTree':
        """Load skill tree state from file."""
        tree = cls()
        with open(filepath, 'r') as f:
            data = json.load(f)
        tree.load_from_dict(data)
        return tree
