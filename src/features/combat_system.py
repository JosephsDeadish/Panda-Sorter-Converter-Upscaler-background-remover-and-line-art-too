"""
Combat System - Fighting mechanics for panda adventures
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DamageType(Enum):
    """Types of damage."""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    TRUE = "true"  # Ignores defense


@dataclass
class CombatStats:
    """Combat statistics for fighters (panda or enemies)."""
    # Core stats
    max_health: int = 100
    current_health: int = 100
    max_magic: int = 50
    current_magic: int = 50
    max_stamina: int = 100
    current_stamina: int = 100
    
    # Offensive stats
    attack_power: int = 10
    magic_power: int = 10
    critical_chance: float = 0.05
    critical_damage: float = 2.0
    
    # Defensive stats
    physical_defense: int = 5
    magical_defense: int = 5
    evasion: float = 0.05  # 5% chance to dodge
    
    # Regeneration (per second in combat)
    health_regen: float = 0.0
    magic_regen: float = 1.0
    stamina_regen: float = 5.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CombatStats':
        """Create from dictionary."""
        return cls(**data)
    
    def is_alive(self) -> bool:
        """Check if entity is alive."""
        return self.current_health > 0
    
    def take_damage(self, damage: int, damage_type: DamageType = DamageType.PHYSICAL) -> int:
        """
        Take damage and apply defense.
        
        Args:
            damage: Raw damage amount
            damage_type: Type of damage
        
        Returns:
            Actual damage taken after defense
        """
        if damage_type == DamageType.TRUE:
            actual_damage = damage
        elif damage_type == DamageType.PHYSICAL:
            actual_damage = max(1, damage - self.physical_defense)
        elif damage_type == DamageType.MAGICAL:
            actual_damage = max(1, damage - self.magical_defense)
        else:
            actual_damage = damage
        
        self.current_health = max(0, self.current_health - actual_damage)
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Heal health.
        
        Args:
            amount: Amount to heal
        
        Returns:
            Actual amount healed
        """
        old_health = self.current_health
        self.current_health = min(self.max_health, self.current_health + amount)
        return self.current_health - old_health
    
    def restore_magic(self, amount: int) -> int:
        """Restore magic/mana."""
        old_magic = self.current_magic
        self.current_magic = min(self.max_magic, self.current_magic + amount)
        return self.current_magic - old_magic
    
    def restore_stamina(self, amount: int) -> int:
        """Restore stamina."""
        old_stamina = self.current_stamina
        self.current_stamina = min(self.max_stamina, self.current_stamina + amount)
        return self.current_stamina - old_stamina
    
    def use_stamina(self, amount: int) -> bool:
        """
        Use stamina for an action.
        
        Returns:
            True if enough stamina, False otherwise
        """
        if self.current_stamina >= amount:
            self.current_stamina -= amount
            return True
        return False
    
    def use_magic(self, amount: int) -> bool:
        """
        Use magic for a spell.
        
        Returns:
            True if enough magic, False otherwise
        """
        if self.current_magic >= amount:
            self.current_magic -= amount
            return True
        return False


class AdventureLevel:
    """Separate leveling system for combat/adventure."""
    
    def __init__(self, save_path: Optional[Path] = None):
        """Initialize adventure level system."""
        self.save_path = save_path
        self.level = 1
        self.xp = 0
        self.skill_points = 0
        
        # XP curve: XP needed for each level
        self.xp_curve = [0]  # Level 1 starts at 0
        for i in range(1, 100):
            # Each level requires more XP (exponential growth)
            xp_needed = int(100 * (1.5 ** (i - 1)))
            self.xp_curve.append(xp_needed)
        
        if save_path and save_path.exists():
            self.load_from_file(save_path)
    
    def add_xp(self, amount: int, source: str = "combat") -> Tuple[bool, int]:
        """
        Add XP and check for level up.
        
        Args:
            amount: XP to add
            source: Source of XP
        
        Returns:
            (leveled_up, new_level)
        """
        self.xp += amount
        logger.info(f"Gained {amount} adventure XP from {source} (total: {self.xp})")
        
        # Check for level up
        old_level = self.level
        while self.level < len(self.xp_curve) and self.xp >= self.get_xp_for_next_level():
            self.level += 1
            self.skill_points += 1
            logger.info(f"Adventure level up! Now level {self.level}")
        
        if self.save_path:
            self.save_to_file(self.save_path)
        
        return (self.level > old_level, self.level)
    
    def get_xp_for_next_level(self) -> int:
        """Get XP required for next level."""
        if self.level < len(self.xp_curve):
            return self.xp_curve[self.level]
        return self.xp_curve[-1] * 2  # Beyond max level
    
    def get_xp_progress(self) -> Tuple[int, int]:
        """
        Get XP progress for current level.
        
        Returns:
            (current_xp_in_level, xp_needed_for_level)
        """
        if self.level == 1:
            current_in_level = self.xp
        else:
            current_in_level = self.xp - self.xp_curve[self.level - 1]
        
        if self.level < len(self.xp_curve):
            needed = self.xp_curve[self.level] - (self.xp_curve[self.level - 1] if self.level > 1 else 0)
        else:
            needed = self.xp_curve[-1]
        
        return (current_in_level, needed)
    
    def spend_skill_point(self) -> bool:
        """Spend a skill point."""
        if self.skill_points > 0:
            self.skill_points -= 1
            if self.save_path:
                self.save_to_file(self.save_path)
            return True
        return False
    
    def save_to_file(self, path: Path):
        """Save adventure level to file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'level': self.level,
                'xp': self.xp,
                'skill_points': self.skill_points,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved adventure level to {path}")
        except Exception as e:
            logger.error(f"Failed to save adventure level: {e}")
    
    def load_from_file(self, path: Path):
        """Load adventure level from file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            self.level = data.get('level', 1)
            self.xp = data.get('xp', 0)
            self.skill_points = data.get('skill_points', 0)
            
            logger.info(f"Loaded adventure level from {path}")
        except Exception as e:
            logger.error(f"Failed to load adventure level: {e}")


class SkillTree:
    """Skill tree for unlocking combat abilities."""
    
    def __init__(self, save_path: Optional[Path] = None):
        """Initialize skill tree."""
        self.save_path = save_path
        self.unlocked_skills: Set[str] = set()
        
        # Define skill tree structure
        self.skills = {
            # Melee tree
            'power_strike': {
                'name': 'Power Strike',
                'description': 'Increase melee damage by 10%',
                'cost': 1,
                'requires': [],
                'stat_bonus': {'attack_power': 10}
            },
            'critical_eye': {
                'name': 'Critical Eye',
                'description': 'Increase critical chance by 5%',
                'cost': 1,
                'requires': ['power_strike'],
                'stat_bonus': {'critical_chance': 0.05}
            },
            'whirlwind': {
                'name': 'Whirlwind',
                'description': 'Unlocks whirlwind attack ability (hits all nearby enemies)',
                'cost': 2,
                'requires': ['power_strike', 'critical_eye'],
                'ability': 'whirlwind_attack'
            },
            
            # Defense tree
            'tough_skin': {
                'name': 'Tough Skin',
                'description': 'Increase physical defense by 5',
                'cost': 1,
                'requires': [],
                'stat_bonus': {'physical_defense': 5}
            },
            'magic_resist': {
                'name': 'Magic Resist',
                'description': 'Increase magical defense by 5',
                'cost': 1,
                'requires': [],
                'stat_bonus': {'magical_defense': 5}
            },
            'iron_will': {
                'name': 'Iron Will',
                'description': 'Increase max health by 25',
                'cost': 2,
                'requires': ['tough_skin', 'magic_resist'],
                'stat_bonus': {'max_health': 25}
            },
            
            # Magic tree
            'magic_mastery': {
                'name': 'Magic Mastery',
                'description': 'Increase magic power by 10',
                'cost': 1,
                'requires': [],
                'stat_bonus': {'magic_power': 10}
            },
            'mana_pool': {
                'name': 'Expanded Mana Pool',
                'description': 'Increase max magic by 25',
                'cost': 1,
                'requires': [],
                'stat_bonus': {'max_magic': 25}
            },
            'fireball': {
                'name': 'Fireball',
                'description': 'Unlocks fireball spell',
                'cost': 2,
                'requires': ['magic_mastery'],
                'ability': 'fireball'
            },
        }
        
        if save_path and save_path.exists():
            self.load_from_file(save_path)
    
    def can_unlock_skill(self, skill_id: str) -> bool:
        """Check if a skill can be unlocked."""
        if skill_id not in self.skills:
            return False
        
        if skill_id in self.unlocked_skills:
            return False  # Already unlocked
        
        skill = self.skills[skill_id]
        
        # Check requirements
        for req in skill.get('requires', []):
            if req not in self.unlocked_skills:
                return False
        
        return True
    
    def unlock_skill(self, skill_id: str) -> bool:
        """Unlock a skill."""
        if self.can_unlock_skill(skill_id):
            self.unlocked_skills.add(skill_id)
            logger.info(f"Unlocked skill: {skill_id}")
            
            if self.save_path:
                self.save_to_file(self.save_path)
            return True
        return False
    
    def get_stat_bonuses(self) -> Dict[str, float]:
        """Calculate total stat bonuses from all unlocked skills."""
        bonuses = {}
        
        for skill_id in self.unlocked_skills:
            skill = self.skills.get(skill_id, {})
            stat_bonus = skill.get('stat_bonus', {})
            
            for stat, value in stat_bonus.items():
                bonuses[stat] = bonuses.get(stat, 0) + value
        
        return bonuses
    
    def get_unlocked_abilities(self) -> List[str]:
        """Get list of unlocked ability names."""
        abilities = []
        
        for skill_id in self.unlocked_skills:
            skill = self.skills.get(skill_id, {})
            ability = skill.get('ability')
            if ability:
                abilities.append(ability)
        
        return abilities
    
    def save_to_file(self, path: Path):
        """Save skill tree to file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'unlocked_skills': list(self.unlocked_skills),
                'last_saved': datetime.now().isoformat()
            }
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved skill tree to {path}")
        except Exception as e:
            logger.error(f"Failed to save skill tree: {e}")
    
    def load_from_file(self, path: Path):
        """Load skill tree from file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            self.unlocked_skills = set(data.get('unlocked_skills', []))
            
            logger.info(f"Loaded skill tree from {path}")
        except Exception as e:
            logger.error(f"Failed to load skill tree: {e}")
