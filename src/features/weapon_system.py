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
