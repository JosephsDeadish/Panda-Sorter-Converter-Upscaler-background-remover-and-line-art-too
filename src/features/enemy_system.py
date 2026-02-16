"""
Enemy System - Animated enemies for combat
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from features.combat_system import CombatStats, DamageType

logger = logging.getLogger(__name__)


class EnemyType(Enum):
    """Types of enemies."""
    SLIME = "slime"
    GOBLIN = "goblin"
    SKELETON = "skeleton"
    WOLF = "wolf"
    ORC = "orc"
    DRAGON = "dragon"
    BOSS = "boss"


class EnemyBehavior(Enum):
    """AI behavior patterns."""
    PASSIVE = "passive"  # Doesn't attack unless attacked
    AGGRESSIVE = "aggressive"  # Attacks on sight
    DEFENSIVE = "defensive"  # Stays in area, attacks if approached
    TACTICAL = "tactical"  # Uses abilities strategically
    BERSERKER = "berserker"  # Becomes more aggressive at low health


@dataclass
class EnemyTemplate:
    """Template for creating enemies."""
    enemy_type: EnemyType
    name: str
    description: str
    icon: str
    base_stats: CombatStats
    behavior: EnemyBehavior
    xp_reward: int
    loot_table: Dict[str, float]  # item_id -> drop_chance
    abilities: List[str] = None
    
    def __post_init__(self):
        if self.abilities is None:
            self.abilities = []


class Enemy:
    """Represents an enemy in combat."""
    
    def __init__(self, template: EnemyTemplate, level: int = 1):
        """
        Create enemy from template.
        
        Args:
            template: Enemy template
            level: Enemy level (scales stats)
        """
        self.template = template
        self.level = level
        self.name = f"Lv.{level} {template.name}"
        self.description = template.description
        self.icon = template.icon
        self.behavior = template.behavior
        self.xp_reward = template.xp_reward * level
        self.loot_table = template.loot_table
        self.abilities = template.abilities.copy()
        
        # Scale stats by level
        self.stats = self._scale_stats(template.base_stats, level)
        
        # AI state
        self.target = None
        self.aggro_level = 0
        self.cooldowns: Dict[str, float] = {}
    
    def _scale_stats(self, base_stats: CombatStats, level: int) -> CombatStats:
        """Scale stats based on level."""
        # Create a copy
        stats = CombatStats(
            max_health=base_stats.max_health + (level - 1) * 10,
            current_health=base_stats.max_health + (level - 1) * 10,
            max_magic=base_stats.max_magic + (level - 1) * 5,
            current_magic=base_stats.max_magic + (level - 1) * 5,
            max_stamina=base_stats.max_stamina,
            current_stamina=base_stats.max_stamina,
            attack_power=base_stats.attack_power + (level - 1) * 2,
            magic_power=base_stats.magic_power + (level - 1) * 2,
            critical_chance=base_stats.critical_chance,
            critical_damage=base_stats.critical_damage,
            physical_defense=base_stats.physical_defense + (level - 1),
            magical_defense=base_stats.magical_defense + (level - 1),
            evasion=base_stats.evasion,
            health_regen=base_stats.health_regen,
            magic_regen=base_stats.magic_regen,
            stamina_regen=base_stats.stamina_regen
        )
        
        return stats
    
    def is_alive(self) -> bool:
        """Check if enemy is alive."""
        return self.stats.is_alive()
    
    def take_damage(self, damage: int, damage_type: DamageType = DamageType.PHYSICAL) -> int:
        """Take damage."""
        actual_damage = self.stats.take_damage(damage, damage_type)
        logger.info(f"{self.name} took {actual_damage} {damage_type.value} damage")
        return actual_damage
    
    def attack(self, target_defense: int) -> Tuple[int, bool]:
        """
        Perform basic attack.
        
        Args:
            target_defense: Target's defense value
        
        Returns:
            (damage_dealt, was_critical)
        """
        # Calculate damage
        base_damage = self.stats.attack_power
        
        # Check for critical hit
        is_crit = random.random() < self.stats.critical_chance
        if is_crit:
            base_damage = int(base_damage * self.stats.critical_damage)
        
        # Apply target defense
        damage = max(1, base_damage - target_defense)
        
        return (damage, is_crit)
    
    def drop_loot(self) -> List[str]:
        """
        Determine loot drops.
        
        Returns:
            List of item IDs dropped
        """
        drops = []
        
        for item_id, chance in self.loot_table.items():
            if random.random() < chance:
                drops.append(item_id)
        
        return drops
    
    def get_ai_action(self) -> str:
        """
        Determine AI action based on behavior.
        
        Returns:
            Action name
        """
        if not self.is_alive():
            return 'dead'
        
        # Simple AI logic
        if self.behavior == EnemyBehavior.PASSIVE:
            return 'idle' if self.aggro_level == 0 else 'attack'
        
        elif self.behavior == EnemyBehavior.AGGRESSIVE:
            return 'attack'
        
        elif self.behavior == EnemyBehavior.DEFENSIVE:
            # Attacks if in range
            return 'attack' if self.aggro_level > 0 else 'idle'
        
        elif self.behavior == EnemyBehavior.BERSERKER:
            # More aggressive at low health
            health_pct = self.stats.current_health / self.stats.max_health
            if health_pct < 0.3:
                return 'rage_attack'
            return 'attack'
        
        elif self.behavior == EnemyBehavior.TACTICAL:
            # Use abilities if available
            if self.abilities and random.random() < 0.3:
                return random.choice(self.abilities)
            return 'attack'
        
        return 'idle'


class EnemyCollection:
    """Collection of enemy templates."""
    
    def __init__(self):
        """Initialize enemy collection."""
        self.templates: Dict[str, EnemyTemplate] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize default enemy templates."""
        # Slime - Easy starter enemy
        self.templates['slime'] = EnemyTemplate(
            enemy_type=EnemyType.SLIME,
            name='Slime',
            description='A gelatinous blob that bounces around',
            icon='🟢',
            base_stats=CombatStats(
                max_health=30,
                current_health=30,
                attack_power=5,
                physical_defense=2,
                magical_defense=1
            ),
            behavior=EnemyBehavior.PASSIVE,
            xp_reward=10,
            loot_table={'slime_gel': 0.5}
        )
        
        # Goblin - Basic aggressive enemy
        self.templates['goblin'] = EnemyTemplate(
            enemy_type=EnemyType.GOBLIN,
            name='Goblin',
            description='A small but fierce creature',
            icon='👺',
            base_stats=CombatStats(
                max_health=50,
                current_health=50,
                attack_power=10,
                physical_defense=5,
                magical_defense=3
            ),
            behavior=EnemyBehavior.AGGRESSIVE,
            xp_reward=25,
            loot_table={'goblin_ear': 0.3, 'gold_coin': 0.8}
        )
        
        # Skeleton - Defensive undead
        self.templates['skeleton'] = EnemyTemplate(
            enemy_type=EnemyType.SKELETON,
            name='Skeleton',
            description='Animated bones driven by dark magic',
            icon='💀',
            base_stats=CombatStats(
                max_health=60,
                current_health=60,
                attack_power=12,
                physical_defense=10,
                magical_defense=5
            ),
            behavior=EnemyBehavior.DEFENSIVE,
            xp_reward=35,
            loot_table={'bone': 0.7, 'rusty_sword': 0.2}
        )
        
        # Wolf - Fast aggressive enemy
        self.templates['wolf'] = EnemyTemplate(
            enemy_type=EnemyType.WOLF,
            name='Wolf',
            description='A fierce predator of the wild',
            icon='🐺',
            base_stats=CombatStats(
                max_health=55,
                current_health=55,
                attack_power=15,
                physical_defense=6,
                magical_defense=4,
                critical_chance=0.15,
                evasion=0.10
            ),
            behavior=EnemyBehavior.AGGRESSIVE,
            xp_reward=30,
            loot_table={'wolf_fur': 0.6, 'wolf_fang': 0.4}
        )
        
        # Orc - Strong tactical enemy
        self.templates['orc'] = EnemyTemplate(
            enemy_type=EnemyType.ORC,
            name='Orc Warrior',
            description='A powerful warrior from the mountains',
            icon='👹',
            base_stats=CombatStats(
                max_health=100,
                current_health=100,
                attack_power=20,
                physical_defense=15,
                magical_defense=8
            ),
            behavior=EnemyBehavior.TACTICAL,
            xp_reward=75,
            loot_table={'orc_tusk': 0.5, 'iron_ore': 0.6, 'health_potion': 0.3},
            abilities=['power_strike', 'war_cry']
        )
        
        # Dragon - Boss enemy
        self.templates['dragon'] = EnemyTemplate(
            enemy_type=EnemyType.DRAGON,
            name='Ancient Dragon',
            description='A legendary beast of immense power',
            icon='🐉',
            base_stats=CombatStats(
                max_health=500,
                current_health=500,
                max_magic=200,
                current_magic=200,
                attack_power=50,
                magic_power=60,
                physical_defense=30,
                magical_defense=25,
                critical_chance=0.15,
                critical_damage=3.0
            ),
            behavior=EnemyBehavior.TACTICAL,
            xp_reward=500,
            loot_table={'dragon_scale': 0.9, 'dragon_claw': 0.7, 'legendary_gem': 0.3},
            abilities=['fire_breath', 'tail_swipe', 'roar']
        )
    
    def get_template(self, enemy_type: str) -> Optional[EnemyTemplate]:
        """Get enemy template by type."""
        return self.templates.get(enemy_type)
    
    def create_enemy(self, enemy_type: str, level: int = 1) -> Optional[Enemy]:
        """Create an enemy instance."""
        template = self.get_template(enemy_type)
        if template:
            return Enemy(template, level)
        return None
    
    def get_all_types(self) -> List[str]:
        """Get all enemy type IDs."""
        return list(self.templates.keys())
