"""
Weapon System - Equip and use weapons with the panda
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class WeaponType(Enum):
    """Types of weapons."""
    MELEE = "melee"
    RANGED = "ranged"
    MAGIC = "magic"


class WeaponRarity(Enum):
    """Weapon rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class WeaponStats:
    """Combat statistics for a weapon."""
    damage: int = 10
    attack_speed: float = 1.0  # Attacks per second
    range: int = 1  # Range in units (1 for melee, higher for ranged)
    critical_chance: float = 0.05  # 5% base crit chance
    critical_multiplier: float = 2.0  # 2x damage on crit
    durability: int = 100  # Weapon health (infinite if -1)
    magic_cost: int = 0  # Mana/magic cost per attack


@dataclass
class Weapon:
    """Represents a weapon that can be equipped by the panda."""
    id: str
    name: str
    description: str
    weapon_type: WeaponType
    rarity: WeaponRarity
    stats: WeaponStats
    icon: str = "⚔️"
    level_required: int = 1
    unlocked: bool = False
    equipped: bool = False
    animation_swing: str = "swing"  # Animation name for attacking
    animation_idle: str = "idle_armed"  # Animation when weapon equipped but not attacking
    unlock_condition: Optional[str] = None  # Achievement or quest requirement
    
    def to_dict(self) -> dict:
        """Convert weapon to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'weapon_type': self.weapon_type.value,
            'rarity': self.rarity.value,
            'stats': asdict(self.stats),
            'icon': self.icon,
            'level_required': self.level_required,
            'unlocked': self.unlocked,
            'equipped': self.equipped,
            'animation_swing': self.animation_swing,
            'animation_idle': self.animation_idle,
            'unlock_condition': self.unlock_condition
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Weapon':
        """Create weapon from dictionary."""
        stats_data = data.get('stats', {})
        stats = WeaponStats(**stats_data)
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            weapon_type=WeaponType(data['weapon_type']),
            rarity=WeaponRarity(data['rarity']),
            stats=stats,
            icon=data.get('icon', '⚔️'),
            level_required=data.get('level_required', 1),
            unlocked=data.get('unlocked', False),
            equipped=data.get('equipped', False),
            animation_swing=data.get('animation_swing', 'swing'),
            animation_idle=data.get('animation_idle', 'idle_armed'),
            unlock_condition=data.get('unlock_condition')
        )


class WeaponCollection:
    """Manages all weapons available to the panda."""
    
    def __init__(self, save_path: Optional[Path] = None):
        """
        Initialize weapon collection.
        
        Args:
            save_path: Path to save weapon states
        """
        self.save_path = save_path
        self.weapons: Dict[str, Weapon] = {}
        self.equipped_weapon: Optional[Weapon] = None
        
        self._initialize_default_weapons()
        
        if save_path and save_path.exists():
            self.load_from_file(save_path)
    
    def _initialize_default_weapons(self):
        """Initialize default weapon collection."""
        # Melee weapons
        self.weapons['wooden_sword'] = Weapon(
            id='wooden_sword',
            name='Wooden Sword',
            description='A basic training sword made of wood',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=10, attack_speed=1.2, range=1),
            icon='🗡️',
            level_required=1,
            unlocked=True
        )
        
        self.weapons['bamboo_staff'] = Weapon(
            id='bamboo_staff',
            name='Bamboo Staff',
            description='A sturdy staff made from ancient bamboo',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=15, attack_speed=1.0, range=2),
            icon='🎋',
            level_required=1,
            unlocked=True
        )
        
        self.weapons['iron_sword'] = Weapon(
            id='iron_sword',
            name='Iron Sword',
            description='A reliable blade forged from iron',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=25, attack_speed=1.0, range=1),
            icon='⚔️',
            level_required=5,
            unlocked=False
        )
        
        self.weapons['katana'] = Weapon(
            id='katana',
            name='Panda Katana',
            description='A legendary blade passed down through generations',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=40, attack_speed=1.5, range=1, critical_chance=0.15),
            icon='🗡️',
            level_required=10,
            unlocked=False
        )
        
        # Ranged weapons
        self.weapons['slingshot'] = Weapon(
            id='slingshot',
            name='Bamboo Slingshot',
            description='A simple slingshot for launching bamboo shoots',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=8, attack_speed=1.5, range=5),
            icon='🏹',
            level_required=1,
            unlocked=True,
            animation_swing='shoot'
        )
        
        self.weapons['bow'] = Weapon(
            id='bow',
            name='Hunting Bow',
            description='A well-crafted bow for ranged combat',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=20, attack_speed=0.8, range=8),
            icon='🏹',
            level_required=5,
            unlocked=False,
            animation_swing='shoot'
        )
        
        # Magic weapons
        self.weapons['magic_wand'] = Weapon(
            id='magic_wand',
            name='Bamboo Wand',
            description='A wand imbued with natural magic',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=30, attack_speed=0.5, range=6, magic_cost=10),
            icon='🪄',
            level_required=5,
            unlocked=False,
            animation_swing='cast_spell'
        )

        # =====================================================================
        # Additional Melee Weapons (~40)
        # =====================================================================

        # COMMON melee (levels 1-3, damage 5-15)
        self.weapons['rusty_dagger'] = Weapon(
            id='rusty_dagger',
            name='Rusty Dagger',
            description='A corroded dagger found in a forgotten dungeon',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=7, attack_speed=1.5, range=1),
            icon='🔪',
            level_required=1,
            unlocked=False
        )
        self.weapons['stone_club'] = Weapon(
            id='stone_club',
            name='Stone Club',
            description='A heavy club carved from solid stone',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=12, attack_speed=0.8, range=1),
            icon='🪨',
            level_required=1,
            unlocked=False
        )
        self.weapons['bronze_shortsword'] = Weapon(
            id='bronze_shortsword',
            name='Bronze Shortsword',
            description='A small but reliable bronze blade',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=11, attack_speed=1.3, range=1),
            icon='🗡️',
            level_required=2,
            unlocked=False
        )
        self.weapons['wooden_mallet'] = Weapon(
            id='wooden_mallet',
            name='Wooden Mallet',
            description='A sturdy mallet used by carpenters and warriors alike',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=14, attack_speed=0.7, range=1),
            icon='🔨',
            level_required=2,
            unlocked=False
        )
        self.weapons['bone_knife'] = Weapon(
            id='bone_knife',
            name='Bone Knife',
            description='A jagged knife fashioned from animal bone',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=9, attack_speed=1.6, range=1),
            icon='🦴',
            level_required=1,
            unlocked=False
        )
        self.weapons['copper_axe'] = Weapon(
            id='copper_axe',
            name='Copper Axe',
            description='A simple axe with a dull copper head',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=13, attack_speed=0.9, range=1),
            icon='🪓',
            level_required=2,
            unlocked=False
        )
        self.weapons['training_spear'] = Weapon(
            id='training_spear',
            name='Training Spear',
            description='A blunted spear for sparring practice',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=10, attack_speed=1.1, range=2),
            icon='🔱',
            level_required=3,
            unlocked=False
        )
        self.weapons['flint_hatchet'] = Weapon(
            id='flint_hatchet',
            name='Flint Hatchet',
            description='A primitive hatchet with a sharp flint edge',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=8, attack_speed=1.4, range=1),
            icon='🪓',
            level_required=1,
            unlocked=False
        )

        # UNCOMMON melee (levels 3-7, damage 15-30)
        self.weapons['steel_longsword'] = Weapon(
            id='steel_longsword',
            name='Steel Longsword',
            description='A well-forged longsword of tempered steel',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=20, attack_speed=1.1, range=1, critical_chance=0.08),
            icon='⚔️',
            level_required=4,
            unlocked=False
        )
        self.weapons['iron_battleaxe'] = Weapon(
            id='iron_battleaxe',
            name='Iron Battleaxe',
            description='A heavy two-handed battleaxe that cleaves through armor',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=25, attack_speed=0.7, range=1, critical_chance=0.07),
            icon='🪓',
            level_required=5,
            unlocked=False
        )
        self.weapons['barbed_flail'] = Weapon(
            id='barbed_flail',
            name='Barbed Flail',
            description='A spiked ball on a chain that tears through defenses',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=22, attack_speed=0.8, range=2, critical_chance=0.09),
            icon='⛓️',
            level_required=5,
            unlocked=False
        )
        self.weapons['silver_rapier'] = Weapon(
            id='silver_rapier',
            name='Silver Rapier',
            description='An elegant thrusting sword with a silver blade',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=17, attack_speed=1.5, range=1, critical_chance=0.12),
            icon='🗡️',
            level_required=4,
            unlocked=False
        )
        self.weapons['war_hammer'] = Weapon(
            id='war_hammer',
            name='War Hammer',
            description='A massive hammer that crushes bones on impact',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=28, attack_speed=0.6, range=1, critical_chance=0.06),
            icon='🔨',
            level_required=6,
            unlocked=False
        )
        self.weapons['poison_dagger'] = Weapon(
            id='poison_dagger',
            name='Poison Dagger',
            description='A dagger coated with a venomous toxin',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=16, attack_speed=1.6, range=1, critical_chance=0.10),
            icon='🔪',
            level_required=4,
            unlocked=False
        )
        self.weapons['oak_quarterstaff'] = Weapon(
            id='oak_quarterstaff',
            name='Oak Quarterstaff',
            description='A reinforced quarterstaff of ancient oak',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=18, attack_speed=1.2, range=2, critical_chance=0.07),
            icon='🥢',
            level_required=3,
            unlocked=False
        )
        self.weapons['spiked_mace'] = Weapon(
            id='spiked_mace',
            name='Spiked Mace',
            description='A heavy mace covered in iron spikes',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=24, attack_speed=0.9, range=1, critical_chance=0.08),
            icon='🔨',
            level_required=6,
            unlocked=False
        )
        self.weapons['steel_halberd'] = Weapon(
            id='steel_halberd',
            name='Steel Halberd',
            description='A polearm combining an axe blade with a spear tip',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=23, attack_speed=0.8, range=2, critical_chance=0.07),
            icon='⚔️',
            level_required=7,
            unlocked=False
        )

        # RARE melee (levels 7-12, damage 30-50, higher crit)
        self.weapons['flamebrand_sword'] = Weapon(
            id='flamebrand_sword',
            name='Flamebrand Sword',
            description='A blade wreathed in eternal flames',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=38, attack_speed=1.2, range=1, critical_chance=0.15),
            icon='🔥',
            level_required=8,
            unlocked=False
        )
        self.weapons['frostbite_axe'] = Weapon(
            id='frostbite_axe',
            name='Frostbite Axe',
            description='An axe forged from enchanted ice that never melts',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=42, attack_speed=0.8, range=1, critical_chance=0.12),
            icon='❄️',
            level_required=9,
            unlocked=False
        )
        self.weapons['moonlit_scimitar'] = Weapon(
            id='moonlit_scimitar',
            name='Moonlit Scimitar',
            description='A curved blade that glows under moonlight',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=35, attack_speed=1.3, range=1, critical_chance=0.18),
            icon='🌙',
            level_required=8,
            unlocked=False
        )
        self.weapons['thunder_maul'] = Weapon(
            id='thunder_maul',
            name='Thunder Maul',
            description='A massive maul that crackles with lightning',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=48, attack_speed=0.6, range=1, critical_chance=0.10),
            icon='⚡',
            level_required=10,
            unlocked=False
        )
        self.weapons['venomfang_spear'] = Weapon(
            id='venomfang_spear',
            name='Venomfang Spear',
            description='A spear tipped with a deadly serpent fang',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=36, attack_speed=1.0, range=2, critical_chance=0.16),
            icon='🐍',
            level_required=9,
            unlocked=False
        )
        self.weapons['shadowsteel_dagger'] = Weapon(
            id='shadowsteel_dagger',
            name='Shadowsteel Dagger',
            description='A dagger forged from ore found only in the deepest shadows',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=32, attack_speed=1.7, range=1, critical_chance=0.20),
            icon='🔪',
            level_required=7,
            unlocked=False
        )
        self.weapons['coral_trident'] = Weapon(
            id='coral_trident',
            name='Coral Trident',
            description='A trident grown from living coral, blessed by the sea',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=40, attack_speed=0.9, range=2, critical_chance=0.14),
            icon='🔱',
            level_required=10,
            unlocked=False
        )
        self.weapons['windcutter_blade'] = Weapon(
            id='windcutter_blade',
            name='Windcutter Blade',
            description='A razor-thin blade that cuts through the air itself',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=34, attack_speed=1.5, range=1, critical_chance=0.17),
            icon='🌬️',
            level_required=11,
            unlocked=False
        )

        # EPIC melee (levels 12-18, damage 50-80, higher crit/speed)
        self.weapons['dragons_fang'] = Weapon(
            id='dragons_fang',
            name="Dragon's Fang",
            description='A legendary blade forged from a dragon tooth',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=65, attack_speed=1.3, range=1, critical_chance=0.20, critical_multiplier=2.5),
            icon='🐉',
            level_required=14,
            unlocked=False
        )
        self.weapons['abyssal_cleaver'] = Weapon(
            id='abyssal_cleaver',
            name='Abyssal Cleaver',
            description='A massive blade pulled from the ocean abyss',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=75, attack_speed=0.7, range=1, critical_chance=0.15, critical_multiplier=2.5),
            icon='🌊',
            level_required=16,
            unlocked=False
        )
        self.weapons['phoenix_glaive'] = Weapon(
            id='phoenix_glaive',
            name='Phoenix Glaive',
            description='A glaive reborn in phoenix fire, blazing with power',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=60, attack_speed=1.1, range=2, critical_chance=0.22, critical_multiplier=2.5),
            icon='🔥',
            level_required=13,
            unlocked=False
        )
        self.weapons['titans_hammer'] = Weapon(
            id='titans_hammer',
            name="Titan's Hammer",
            description='An enormous hammer once wielded by ancient titans',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=78, attack_speed=0.5, range=1, critical_chance=0.12, critical_multiplier=3.0),
            icon='🔨',
            level_required=17,
            unlocked=False
        )
        self.weapons['void_scythe'] = Weapon(
            id='void_scythe',
            name='Void Scythe',
            description='A scythe that rends the fabric of reality',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=68, attack_speed=0.9, range=2, critical_chance=0.18, critical_multiplier=2.5),
            icon='💀',
            level_required=15,
            unlocked=False
        )
        self.weapons['stormbreaker_axe'] = Weapon(
            id='stormbreaker_axe',
            name='Stormbreaker Axe',
            description='An axe infused with the fury of a thousand storms',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=72, attack_speed=0.8, range=1, critical_chance=0.16, critical_multiplier=2.5),
            icon='⚡',
            level_required=16,
            unlocked=False
        )
        self.weapons['emerald_falchion'] = Weapon(
            id='emerald_falchion',
            name='Emerald Falchion',
            description='A curved blade set with emeralds that pulse with nature magic',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=58, attack_speed=1.4, range=1, critical_chance=0.22, critical_multiplier=2.5),
            icon='🌿',
            level_required=12,
            unlocked=False
        )
        self.weapons['obsidian_warblade'] = Weapon(
            id='obsidian_warblade',
            name='Obsidian Warblade',
            description='A jet-black blade of volcanic glass, impossibly sharp',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=70, attack_speed=1.0, range=1, critical_chance=0.20, critical_multiplier=2.5),
            icon='🖤',
            level_required=15,
            unlocked=False
        )

        # LEGENDARY melee (levels 18-25, damage 80-120, best stats)
        self.weapons['excalibur'] = Weapon(
            id='excalibur',
            name='Excalibur',
            description='The legendary sword of kings, pulled from the stone',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=110, attack_speed=1.3, range=1, critical_chance=0.25, critical_multiplier=3.0),
            icon='👑',
            level_required=22,
            unlocked=False
        )
        self.weapons['ragnarok_blade'] = Weapon(
            id='ragnarok_blade',
            name='Ragnarok Blade',
            description='A world-ending sword forged at the end of days',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=120, attack_speed=1.0, range=2, critical_chance=0.22, critical_multiplier=3.5),
            icon='⭐',
            level_required=25,
            unlocked=False
        )
        self.weapons['celestial_halberd'] = Weapon(
            id='celestial_halberd',
            name='Celestial Halberd',
            description='A halberd blessed by the stars themselves',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=100, attack_speed=0.9, range=2, critical_chance=0.20, critical_multiplier=3.0),
            icon='🌟',
            level_required=20,
            unlocked=False
        )
        self.weapons['soul_reaper'] = Weapon(
            id='soul_reaper',
            name='Soul Reaper',
            description='A scythe that harvests the very essence of fallen foes',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=95, attack_speed=1.1, range=2, critical_chance=0.28, critical_multiplier=3.0),
            icon='💀',
            level_required=20,
            unlocked=False
        )
        self.weapons['suns_fury_mace'] = Weapon(
            id='suns_fury_mace',
            name="Sun's Fury Mace",
            description='A radiant mace burning with the power of the sun',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=105, attack_speed=0.8, range=1, critical_chance=0.18, critical_multiplier=3.5),
            icon='☀️',
            level_required=23,
            unlocked=False
        )
        self.weapons['eternal_katana'] = Weapon(
            id='eternal_katana',
            name='Eternal Katana',
            description='A katana folded ten thousand times, never dulled',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=90, attack_speed=1.6, range=1, critical_chance=0.30, critical_multiplier=3.0),
            icon='⚔️',
            level_required=19,
            unlocked=False
        )
        self.weapons['worldsplitter_axe'] = Weapon(
            id='worldsplitter_axe',
            name='Worldsplitter Axe',
            description='An axe so powerful it can split the earth in two',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=115, attack_speed=0.6, range=1, critical_chance=0.15, critical_multiplier=4.0),
            icon='🪓',
            level_required=24,
            unlocked=False
        )

        # =====================================================================
        # Additional Ranged Weapons (~30)
        # =====================================================================

        # COMMON ranged (levels 1-3, damage 5-15)
        self.weapons['short_bow'] = Weapon(
            id='short_bow',
            name='Short Bow',
            description='A small bow suited for beginners',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=8, attack_speed=1.2, range=5),
            icon='🏹',
            level_required=1,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['pebble_sling'] = Weapon(
            id='pebble_sling',
            name='Pebble Sling',
            description='A crude sling that hurls small pebbles',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=6, attack_speed=1.4, range=4),
            icon='🪨',
            level_required=1,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['wooden_crossbow'] = Weapon(
            id='wooden_crossbow',
            name='Wooden Crossbow',
            description='A simple crossbow made from planks and rope',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=12, attack_speed=0.8, range=6),
            icon='🏹',
            level_required=2,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['throwing_rocks'] = Weapon(
            id='throwing_rocks',
            name='Throwing Rocks',
            description='A pouch of smooth rocks, perfect for throwing',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=7, attack_speed=1.5, range=3),
            icon='🪨',
            level_required=1,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['reed_blowgun'] = Weapon(
            id='reed_blowgun',
            name='Reed Blowgun',
            description='A hollow reed used to fire tiny darts',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=5, attack_speed=1.8, range=4),
            icon='🎯',
            level_required=2,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['bamboo_dart_shooter'] = Weapon(
            id='bamboo_dart_shooter',
            name='Bamboo Dart Shooter',
            description='A bamboo tube that launches feathered darts',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=9, attack_speed=1.3, range=5),
            icon='🎋',
            level_required=3,
            unlocked=False,
            animation_swing='shoot'
        )

        # UNCOMMON ranged (levels 3-7, damage 15-30)
        self.weapons['hunters_longbow'] = Weapon(
            id='hunters_longbow',
            name="Hunter's Longbow",
            description='A powerful longbow favored by wilderness hunters',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=20, attack_speed=0.9, range=7, critical_chance=0.10),
            icon='🏹',
            level_required=4,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['iron_crossbow'] = Weapon(
            id='iron_crossbow',
            name='Iron Crossbow',
            description='A sturdy crossbow with an iron frame and strong draw',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=24, attack_speed=0.7, range=8, critical_chance=0.08),
            icon='🏹',
            level_required=5,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['throwing_knives'] = Weapon(
            id='throwing_knives',
            name='Throwing Knives',
            description='A set of balanced knives designed for precise throws',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=16, attack_speed=1.5, range=4, critical_chance=0.12),
            icon='🔪',
            level_required=4,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['steel_javelin'] = Weapon(
            id='steel_javelin',
            name='Steel Javelin',
            description='A javelin with a hardened steel tip for piercing armor',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=22, attack_speed=0.8, range=5, critical_chance=0.09),
            icon='🎯',
            level_required=5,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['shuriken_set'] = Weapon(
            id='shuriken_set',
            name='Shuriken Set',
            description='A collection of razor-sharp throwing stars',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=15, attack_speed=1.8, range=4, critical_chance=0.14),
            icon='⭐',
            level_required=3,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['poison_blowgun'] = Weapon(
            id='poison_blowgun',
            name='Poison Blowgun',
            description='A blowgun loaded with poison-tipped darts',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=18, attack_speed=1.3, range=5, critical_chance=0.11),
            icon='🐍',
            level_required=6,
            unlocked=False,
            animation_swing='shoot'
        )

        # RARE ranged (levels 7-12, damage 30-50)
        self.weapons['gale_force_bow'] = Weapon(
            id='gale_force_bow',
            name='Gale Force Bow',
            description='A bow that harnesses the wind to accelerate arrows',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=38, attack_speed=1.1, range=9, critical_chance=0.15),
            icon='🌬️',
            level_required=8,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['repeating_crossbow'] = Weapon(
            id='repeating_crossbow',
            name='Repeating Crossbow',
            description='A mechanical crossbow that fires bolts in rapid succession',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=30, attack_speed=1.6, range=7, critical_chance=0.12),
            icon='🏹',
            level_required=9,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['lightning_javelin'] = Weapon(
            id='lightning_javelin',
            name='Lightning Javelin',
            description='A javelin that crackles with electric energy',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=42, attack_speed=0.8, range=6, critical_chance=0.14),
            icon='⚡',
            level_required=10,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['ice_shard_stars'] = Weapon(
            id='ice_shard_stars',
            name='Ice Shard Stars',
            description='Throwing stars carved from enchanted ice crystals',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=35, attack_speed=1.4, range=5, critical_chance=0.18),
            icon='❄️',
            level_required=8,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['flame_arrow_bow'] = Weapon(
            id='flame_arrow_bow',
            name='Flame Arrow Bow',
            description='A bow that ignites arrows as they are drawn',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=40, attack_speed=1.0, range=8, critical_chance=0.13),
            icon='🔥',
            level_required=11,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['boomerang_blade'] = Weapon(
            id='boomerang_blade',
            name='Boomerang Blade',
            description='A bladed boomerang that returns after striking',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=33, attack_speed=1.2, range=6, critical_chance=0.16),
            icon='🪃',
            level_required=7,
            unlocked=False,
            animation_swing='shoot'
        )

        # EPIC ranged (levels 12-18, damage 50-80)
        self.weapons['dragons_breath_bow'] = Weapon(
            id='dragons_breath_bow',
            name="Dragon's Breath Bow",
            description='A bow that shoots arrows wreathed in dragonfire',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=62, attack_speed=1.0, range=10, critical_chance=0.20, critical_multiplier=2.5),
            icon='🐉',
            level_required=14,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['phantom_crossbow'] = Weapon(
            id='phantom_crossbow',
            name='Phantom Crossbow',
            description='A ghostly crossbow that fires spectral bolts',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=55, attack_speed=1.3, range=9, critical_chance=0.22, critical_multiplier=2.5),
            icon='👻',
            level_required=13,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['tempest_shurikens'] = Weapon(
            id='tempest_shurikens',
            name='Tempest Shurikens',
            description='Storm-infused throwing stars that leave lightning trails',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=52, attack_speed=1.7, range=5, critical_chance=0.25, critical_multiplier=2.5),
            icon='🌪️',
            level_required=12,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['voidstrike_javelin'] = Weapon(
            id='voidstrike_javelin',
            name='Voidstrike Javelin',
            description='A javelin that pierces through dimensions',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=70, attack_speed=0.7, range=8, critical_chance=0.18, critical_multiplier=3.0),
            icon='🌀',
            level_required=16,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['solar_flare_bow'] = Weapon(
            id='solar_flare_bow',
            name='Solar Flare Bow',
            description='A bow that channels the raw energy of solar flares',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=66, attack_speed=0.9, range=10, critical_chance=0.20, critical_multiplier=2.5),
            icon='☀️',
            level_required=17,
            unlocked=False,
            animation_swing='shoot'
        )

        # LEGENDARY ranged (levels 18-25, damage 80-120)
        self.weapons['starfall_bow'] = Weapon(
            id='starfall_bow',
            name='Starfall Bow',
            description='A divine bow that rains down stars upon enemies',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=100, attack_speed=1.1, range=12, critical_chance=0.25, critical_multiplier=3.0),
            icon='🌟',
            level_required=21,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['oblivion_crossbow'] = Weapon(
            id='oblivion_crossbow',
            name='Oblivion Crossbow',
            description='A crossbow that fires bolts of pure annihilation',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=110, attack_speed=0.8, range=11, critical_chance=0.20, critical_multiplier=3.5),
            icon='💀',
            level_required=23,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['heavens_javelin'] = Weapon(
            id='heavens_javelin',
            name="Heaven's Javelin",
            description='A holy javelin forged in celestial light',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=95, attack_speed=0.9, range=9, critical_chance=0.22, critical_multiplier=3.0),
            icon='✨',
            level_required=20,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['galaxys_edge_bow'] = Weapon(
            id='galaxys_edge_bow',
            name="Galaxy's Edge Bow",
            description='A bow strung with cosmic energy from the edge of the galaxy',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=115, attack_speed=1.0, range=14, critical_chance=0.28, critical_multiplier=3.5),
            icon='🌌',
            level_required=25,
            unlocked=False,
            animation_swing='shoot'
        )

        # =====================================================================
        # Additional Magic Weapons (~30)
        # =====================================================================

        # COMMON magic (levels 1-3, damage 5-15)
        self.weapons['apprentice_wand'] = Weapon(
            id='apprentice_wand',
            name='Apprentice Wand',
            description='A simple wand given to magic students',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=8, attack_speed=1.0, range=5, magic_cost=5),
            icon='🪄',
            level_required=1,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['spark_stone'] = Weapon(
            id='spark_stone',
            name='Spark Stone',
            description='A small stone that emits faint magical sparks',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=6, attack_speed=1.2, range=4, magic_cost=5),
            icon='💎',
            level_required=1,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['herb_charm'] = Weapon(
            id='herb_charm',
            name='Herb Charm',
            description='A bundle of enchanted herbs that channels nature magic',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=7, attack_speed=1.1, range=4, magic_cost=5),
            icon='🌿',
            level_required=1,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['wooden_tome'] = Weapon(
            id='wooden_tome',
            name='Wooden Tome',
            description='A beginner spellbook bound in simple wood',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=10, attack_speed=0.9, range=5, magic_cost=6),
            icon='📖',
            level_required=2,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['glowing_pebble'] = Weapon(
            id='glowing_pebble',
            name='Glowing Pebble',
            description='A luminous pebble pulsing with minor enchantment',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=5, attack_speed=1.3, range=3, magic_cost=5),
            icon='✨',
            level_required=1,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['runic_twig'] = Weapon(
            id='runic_twig',
            name='Runic Twig',
            description='A twig carved with faintly glowing runes',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.COMMON,
            stats=WeaponStats(damage=9, attack_speed=1.1, range=4, magic_cost=5),
            icon='🪄',
            level_required=2,
            unlocked=False,
            animation_swing='cast_spell'
        )

        # UNCOMMON magic (levels 3-7, damage 15-30)
        self.weapons['flame_staff'] = Weapon(
            id='flame_staff',
            name='Flame Staff',
            description='A staff crowned with an ever-burning flame',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=22, attack_speed=0.8, range=6, magic_cost=10, critical_chance=0.08),
            icon='🔥',
            level_required=4,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['frost_orb'] = Weapon(
            id='frost_orb',
            name='Frost Orb',
            description='A frozen sphere that channels blizzard magic',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=20, attack_speed=0.9, range=6, magic_cost=10, critical_chance=0.09),
            icon='❄️',
            level_required=4,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['enchanted_tome'] = Weapon(
            id='enchanted_tome',
            name='Enchanted Tome',
            description='A spellbook filled with intermediate incantations',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=25, attack_speed=0.7, range=7, magic_cost=12, critical_chance=0.07),
            icon='📖',
            level_required=5,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['amethyst_crystal'] = Weapon(
            id='amethyst_crystal',
            name='Amethyst Crystal',
            description='A purple crystal that amplifies magical energy',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=18, attack_speed=1.1, range=5, magic_cost=8, critical_chance=0.10),
            icon='💎',
            level_required=3,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['serpent_amulet'] = Weapon(
            id='serpent_amulet',
            name='Serpent Amulet',
            description='An amulet shaped like a coiled serpent that spits venom magic',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=19, attack_speed=1.0, range=5, magic_cost=9, critical_chance=0.11),
            icon='🐍',
            level_required=5,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['moonstone_wand'] = Weapon(
            id='moonstone_wand',
            name='Moonstone Wand',
            description='A wand tipped with a lustrous moonstone',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=21, attack_speed=1.0, range=6, magic_cost=10, critical_chance=0.09),
            icon='🌙',
            level_required=6,
            unlocked=False,
            animation_swing='cast_spell'
        )

        # RARE magic (levels 7-12, damage 30-50)
        self.weapons['stormcaller_staff'] = Weapon(
            id='stormcaller_staff',
            name='Stormcaller Staff',
            description='A staff that summons bolts of lightning from storm clouds',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=40, attack_speed=0.9, range=8, magic_cost=15, critical_chance=0.15),
            icon='⚡',
            level_required=9,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['shadow_grimoire'] = Weapon(
            id='shadow_grimoire',
            name='Shadow Grimoire',
            description='A dark tome containing forbidden shadow spells',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=45, attack_speed=0.7, range=7, magic_cost=18, critical_chance=0.14),
            icon='📖',
            level_required=10,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['crystal_prism'] = Weapon(
            id='crystal_prism',
            name='Crystal Prism',
            description='A prism that refracts magical energy into devastating beams',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=38, attack_speed=1.0, range=7, magic_cost=14, critical_chance=0.16),
            icon='💎',
            level_required=8,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['tidal_scepter'] = Weapon(
            id='tidal_scepter',
            name='Tidal Scepter',
            description='A scepter that commands the power of ocean tides',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=42, attack_speed=0.8, range=8, magic_cost=16, critical_chance=0.13),
            icon='🌊',
            level_required=10,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['verdant_totem'] = Weapon(
            id='verdant_totem',
            name='Verdant Totem',
            description='A totem carved from a living tree, pulsing with nature magic',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=35, attack_speed=0.9, range=6, magic_cost=13, critical_chance=0.15),
            icon='🌿',
            level_required=7,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['inferno_orb'] = Weapon(
            id='inferno_orb',
            name='Inferno Orb',
            description='A blazing orb of concentrated fire magic',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=48, attack_speed=0.8, range=7, magic_cost=17, critical_chance=0.12),
            icon='🔥',
            level_required=11,
            unlocked=False,
            animation_swing='cast_spell'
        )

        # EPIC magic (levels 12-18, damage 50-80)
        self.weapons['arcane_codex'] = Weapon(
            id='arcane_codex',
            name='Arcane Codex',
            description='An ancient codex containing the secrets of arcane mastery',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=65, attack_speed=0.8, range=9, magic_cost=22, critical_chance=0.20, critical_multiplier=2.5),
            icon='📖',
            level_required=14,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['void_crystal'] = Weapon(
            id='void_crystal',
            name='Void Crystal',
            description='A crystal of pure void energy that warps reality',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=70, attack_speed=0.7, range=8, magic_cost=25, critical_chance=0.18, critical_multiplier=2.5),
            icon='🔮',
            level_required=16,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['phoenix_feather_wand'] = Weapon(
            id='phoenix_feather_wand',
            name='Phoenix Feather Wand',
            description='A wand crafted around a genuine phoenix feather',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=58, attack_speed=1.1, range=8, magic_cost=20, critical_chance=0.22, critical_multiplier=2.5),
            icon='🪶',
            level_required=13,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['eclipse_amulet'] = Weapon(
            id='eclipse_amulet',
            name='Eclipse Amulet',
            description='An amulet that draws power from solar eclipses',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=62, attack_speed=0.9, range=7, magic_cost=22, critical_chance=0.20, critical_multiplier=2.5),
            icon='🌑',
            level_required=15,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['necromancers_skull'] = Weapon(
            id='necromancers_skull',
            name="Necromancer's Skull",
            description='A skull that channels dark necromantic energy',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=75, attack_speed=0.6, range=7, magic_cost=28, critical_chance=0.16, critical_multiplier=3.0),
            icon='💀',
            level_required=17,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['aurora_staff'] = Weapon(
            id='aurora_staff',
            name='Aurora Staff',
            description='A staff that channels the shimmering energy of the northern lights',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=60, attack_speed=1.0, range=9, magic_cost=20, critical_chance=0.22, critical_multiplier=2.5),
            icon='🌈',
            level_required=14,
            unlocked=False,
            animation_swing='cast_spell'
        )

        # LEGENDARY magic (levels 18-25, damage 80-120)
        self.weapons['cosmic_scepter'] = Weapon(
            id='cosmic_scepter',
            name='Cosmic Scepter',
            description='A scepter that commands the forces of the cosmos',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=105, attack_speed=0.9, range=12, magic_cost=28, critical_chance=0.25, critical_multiplier=3.0),
            icon='🌌',
            level_required=22,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['book_of_eternity'] = Weapon(
            id='book_of_eternity',
            name='Book of Eternity',
            description='A tome containing every spell ever written across all time',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=115, attack_speed=0.7, range=11, magic_cost=30, critical_chance=0.22, critical_multiplier=3.5),
            icon='📖',
            level_required=24,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['philosophers_stone'] = Weapon(
            id='philosophers_stone',
            name="Philosopher's Stone",
            description='The mythical stone of ultimate transmutation and power',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=100, attack_speed=1.0, range=10, magic_cost=25, critical_chance=0.28, critical_multiplier=3.0),
            icon='💎',
            level_required=21,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['astral_orb'] = Weapon(
            id='astral_orb',
            name='Astral Orb',
            description='An orb containing a miniature galaxy of pure magical energy',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=120, attack_speed=0.8, range=13, magic_cost=30, critical_chance=0.25, critical_multiplier=3.5),
            icon='🔮',
            level_required=25,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['divinity_staff'] = Weapon(
            id='divinity_staff',
            name='Divinity Staff',
            description='A staff said to have been wielded by the gods themselves',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=110, attack_speed=0.9, range=12, magic_cost=28, critical_chance=0.26, critical_multiplier=3.0),
            icon='👑',
            level_required=23,
            unlocked=False,
            animation_swing='cast_spell'
        )
        self.weapons['chrono_amulet'] = Weapon(
            id='chrono_amulet',
            name='Chrono Amulet',
            description='An amulet that bends time to devastate enemies',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.LEGENDARY,
            stats=WeaponStats(damage=95, attack_speed=1.2, range=10, magic_cost=26, critical_chance=0.30, critical_multiplier=3.0),
            icon='⏳',
            level_required=19,
            unlocked=False,
            animation_swing='cast_spell'
        )

        # Additional weapons to complete the set
        self.weapons['granite_warhammer'] = Weapon(
            id='granite_warhammer',
            name='Granite Warhammer',
            description='A warhammer hewn from solid granite, devastatingly heavy',
            weapon_type=WeaponType.MELEE,
            rarity=WeaponRarity.UNCOMMON,
            stats=WeaponStats(damage=26, attack_speed=0.6, range=1, critical_chance=0.07),
            icon='🔨',
            level_required=6,
            unlocked=False
        )
        self.weapons['serpent_fang_bow'] = Weapon(
            id='serpent_fang_bow',
            name='Serpent Fang Bow',
            description='A bow strung with enchanted serpent sinew',
            weapon_type=WeaponType.RANGED,
            rarity=WeaponRarity.RARE,
            stats=WeaponStats(damage=37, attack_speed=1.1, range=8, critical_chance=0.15),
            icon='🐍',
            level_required=9,
            unlocked=False,
            animation_swing='shoot'
        )
        self.weapons['ethereal_lantern'] = Weapon(
            id='ethereal_lantern',
            name='Ethereal Lantern',
            description='A ghostly lantern that channels spirits into destructive magic',
            weapon_type=WeaponType.MAGIC,
            rarity=WeaponRarity.EPIC,
            stats=WeaponStats(damage=64, attack_speed=0.9, range=8, magic_cost=22, critical_chance=0.20, critical_multiplier=2.5),
            icon='🏮',
            level_required=15,
            unlocked=False,
            animation_swing='cast_spell'
        )
    
    def get_weapon(self, weapon_id: str) -> Optional[Weapon]:
        """Get a weapon by ID."""
        return self.weapons.get(weapon_id)
    
    def unlock_weapon(self, weapon_id: str) -> bool:
        """Unlock a weapon."""
        weapon = self.weapons.get(weapon_id)
        if weapon:
            weapon.unlocked = True
            logger.info(f"Unlocked weapon: {weapon_id}")
            if self.save_path:
                self.save_to_file(self.save_path)
            return True
        return False
    
    def equip_weapon(self, weapon_id: str) -> bool:
        """Equip a weapon."""
        weapon = self.weapons.get(weapon_id)
        if weapon and weapon.unlocked:
            # Unequip current weapon
            if self.equipped_weapon:
                self.equipped_weapon.equipped = False
            
            # Equip new weapon
            weapon.equipped = True
            self.equipped_weapon = weapon
            logger.info(f"Equipped weapon: {weapon_id}")
            
            if self.save_path:
                self.save_to_file(self.save_path)
            return True
        return False
    
    def unequip_weapon(self) -> bool:
        """Unequip current weapon."""
        if self.equipped_weapon:
            self.equipped_weapon.equipped = False
            weapon_id = self.equipped_weapon.id
            self.equipped_weapon = None
            logger.info(f"Unequipped weapon: {weapon_id}")
            
            if self.save_path:
                self.save_to_file(self.save_path)
            return True
        return False
    
    def get_all_weapons(self, unlocked_only: bool = False) -> List[Weapon]:
        """Get all weapons, optionally filtered by unlocked status."""
        weapons = list(self.weapons.values())
        if unlocked_only:
            weapons = [w for w in weapons if w.unlocked]
        return weapons
    
    def get_weapons_by_type(self, weapon_type: WeaponType, unlocked_only: bool = False) -> List[Weapon]:
        """Get weapons of a specific type."""
        weapons = [w for w in self.weapons.values() if w.weapon_type == weapon_type]
        if unlocked_only:
            weapons = [w for w in weapons if w.unlocked]
        return weapons
    
    def save_to_file(self, path: Path):
        """Save weapon states to file."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'weapons': {wid: w.to_dict() for wid, w in self.weapons.items()},
                'equipped_weapon_id': self.equipped_weapon.id if self.equipped_weapon else None,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved weapons to {path}")
        except Exception as e:
            logger.error(f"Failed to save weapons: {e}")
    
    def load_from_file(self, path: Path):
        """Load weapon states from file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Load weapons
            for wid, wdata in data.get('weapons', {}).items():
                if wid in self.weapons:
                    # Update existing weapon with saved state
                    weapon = Weapon.from_dict(wdata)
                    self.weapons[wid] = weapon
            
            # Restore equipped weapon
            equipped_id = data.get('equipped_weapon_id')
            if equipped_id and equipped_id in self.weapons:
                self.equipped_weapon = self.weapons[equipped_id]
            
            logger.info(f"Loaded weapons from {path}")
        except Exception as e:
            logger.error(f"Failed to load weapons: {e}")
