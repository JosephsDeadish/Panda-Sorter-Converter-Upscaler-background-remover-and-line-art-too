"""
Comprehensive stats system for the panda character.
Tracks base stats, combat stats, and system stats with leveling and persistence.
"""

import json
from typing import Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class PandaStats:
    """
    Comprehensive stats tracking for the panda character.
    
    Stats are organized into four categories:
    1. Base Stats - Character attributes (health, strength, defense, etc.)
    2. Combat Stats - Gameplay tracking (kills, damage, attacks, etc.)
    3. Interaction Stats - User interaction tracking (clicks, pets, feeds, etc.)
    4. System Stats - Meta tracking (playtime, items collected, files processed, etc.)
    """
    
    # Base Stats - Character Attributes
    level: int = 1
    experience: int = 0
    health: int = 100
    max_health: int = 100
    defense: int = 10
    magic: int = 10
    intelligence: int = 10
    strength: int = 10
    agility: int = 10
    vitality: int = 10
    skill_points: int = 0
    
    # Combat Stats - Gameplay Tracking
    total_attacks: int = 0
    monsters_slain: int = 0
    damage_dealt: int = 0
    damage_taken: int = 0
    critical_hits: int = 0
    perfect_dodges: int = 0
    spells_cast: int = 0
    healing_done: int = 0
    
    # Interaction Stats - User Interaction Tracking
    click_count: int = 0
    pet_count: int = 0
    feed_count: int = 0
    hover_count: int = 0
    drag_count: int = 0
    toss_count: int = 0
    shake_count: int = 0
    spin_count: int = 0
    toy_interact_count: int = 0
    clothing_change_count: int = 0
    items_thrown_at_count: int = 0
    belly_poke_count: int = 0
    fall_count: int = 0
    tip_over_count: int = 0
    
    # System Stats - Meta Tracking
    playtime: float = 0.0  # seconds
    items_collected: int = 0
    dungeons_cleared: int = 0
    floors_explored: int = 0
    distance_traveled: float = 0.0
    times_died: int = 0
    times_saved: int = 0
    files_processed: int = 0
    failed_operations: int = 0
    easter_eggs_found: int = 0
    
    def get_experience_for_level(self, level: int) -> int:
        """Calculate experience required to reach a given level (cumulative)."""
        # Level 1 requires 0 XP, level 2 requires 100, level 3 requires 300, etc.
        if level <= 1:
            return 0
        return ((level - 1) * level * 100) // 2
    
    def get_experience_to_next_level(self) -> int:
        """Get experience needed to reach next level."""
        next_level_xp = self.get_experience_for_level(self.level + 1)
        return next_level_xp - self.experience
    
    def can_level_up(self) -> bool:
        """Check if player has enough XP to level up."""
        if self.level >= 100:  # Max level
            return False
        return self.experience >= self.get_experience_for_level(self.level + 1)
    
    def level_up(self) -> bool:
        """
        Level up the character if possible.
        Returns True if level up occurred.
        """
        if not self.can_level_up():
            return False
        
        self.level += 1
        
        # Apply level-up bonuses
        self.max_health += 20
        self.health = self.max_health  # Restore to full health on level up
        self.strength += 2
        self.defense += 2
        self.magic += 2
        self.intelligence += 1
        self.agility += 1
        self.vitality += 1
        self.skill_points += 3
        
        return True
    
    def add_experience(self, amount: int):
        """Add experience and automatically level up if possible."""
        self.experience += amount
        
        # Auto level-up loop
        while self.can_level_up():
            self.level_up()
    
    def take_damage(self, amount: int):
        """Take damage, applying defense reduction."""
        reduced_damage = self.calculate_damage_reduction(amount)
        self.health -= reduced_damage
        
        if self.health < 0:
            self.health = 0
            self.times_died += 1
    
    def heal(self, amount: int):
        """Heal the character, not exceeding max health."""
        old_health = self.health
        self.health = min(self.health + amount, self.max_health)
        actual_healing = self.health - old_health
        self.healing_done += actual_healing
    
    def calculate_damage_reduction(self, damage: int) -> int:
        """
        Calculate damage after defense reduction.
        Formula: actual_damage = damage * (100 / (100 + defense))
        """
        if damage <= 0:
            return 0
        
        reduction_factor = 100 / (100 + self.defense)
        return int(damage * reduction_factor)
    
    def calculate_physical_damage(self, base_damage: int) -> int:
        """
        Calculate physical damage with strength bonus.
        Each point of strength adds 2% damage.
        """
        if base_damage <= 0:
            return 0
        
        strength_multiplier = 1.0 + (self.strength * 0.02)
        return int(base_damage * strength_multiplier)
    
    def calculate_magic_damage(self, base_damage: int) -> int:
        """
        Calculate magic damage with intelligence bonus.
        Each point of intelligence adds 2% magic damage.
        """
        if base_damage <= 0:
            return 0
        
        int_multiplier = 1.0 + (self.intelligence * 0.02)
        magic_multiplier = 1.0 + (self.magic * 0.01)
        return int(base_damage * int_multiplier * magic_multiplier)
    
    def get_dodge_chance(self) -> float:
        """
        Get dodge chance percentage (0-50%).
        Agility / 10 = dodge chance.
        """
        return min(self.agility / 10.0, 50.0)
    
    def get_critical_chance(self) -> float:
        """
        Get critical hit chance percentage (0-25%).
        Agility / 20 = crit chance.
        """
        return min(self.agility / 20.0, 25.0)
    
    def get_vitality_bonus(self) -> int:
        """Get bonus max health from vitality (10 HP per point)."""
        return self.vitality * 10
    
    def should_dodge(self) -> bool:
        """Check if an attack should be dodged (random check)."""
        import random
        return random.random() * 100 < self.get_dodge_chance()
    
    def should_crit(self) -> bool:
        """Check if an attack should crit (random check)."""
        import random
        return random.random() * 100 < self.get_critical_chance()
    
    # Combat stat tracking methods
    def increment_attack(self):
        """Increment total attacks counter."""
        self.total_attacks += 1
    
    def add_monster_kill(self):
        """Add a monster kill."""
        self.monsters_slain += 1
    
    def add_damage_dealt(self, amount: int):
        """Track damage dealt."""
        self.damage_dealt += amount
    
    def add_damage_taken(self, amount: int):
        """Track damage taken."""
        self.damage_taken += amount
    
    def add_critical_hit(self):
        """Increment critical hit counter."""
        self.critical_hits += 1
    
    def add_perfect_dodge(self):
        """Increment perfect dodge counter."""
        self.perfect_dodges += 1
    
    def add_spell_cast(self):
        """Increment spell cast counter."""
        self.spells_cast += 1
    
    # System stat tracking methods
    def add_playtime(self, seconds: float):
        """Add to playtime counter."""
        self.playtime += seconds
    
    def add_item_collected(self):
        """Increment items collected."""
        self.items_collected += 1
    
    def increment_dungeons(self):
        """Increment dungeons cleared."""
        self.dungeons_cleared += 1
    
    def increment_floors(self):
        """Increment floors explored."""
        self.floors_explored += 1
    
    def add_distance(self, distance: float):
        """Add to distance traveled."""
        self.distance_traveled += distance
    
    def increment_saves(self):
        """Increment times saved."""
        self.times_saved += 1
    
    # Interaction stat increment methods
    def increment_clicks(self):
        """Increment click count."""
        self.click_count += 1
    
    def increment_pets(self):
        """Increment pet count."""
        self.pet_count += 1
    
    def increment_feeds(self):
        """Increment feed count."""
        self.feed_count += 1
    
    def increment_hovers(self):
        """Increment hover count."""
        self.hover_count += 1
    
    def increment_drags(self):
        """Increment drag count."""
        self.drag_count += 1
    
    def increment_tosses(self):
        """Increment toss count."""
        self.toss_count += 1
    
    def increment_shakes(self):
        """Increment shake count."""
        self.shake_count += 1
    
    def increment_spins(self):
        """Increment spin count."""
        self.spin_count += 1
    
    def increment_toy_interacts(self):
        """Increment toy interact count."""
        self.toy_interact_count += 1
    
    def increment_clothing_changes(self):
        """Increment clothing change count."""
        self.clothing_change_count += 1
    
    def increment_items_thrown(self):
        """Increment items thrown at count."""
        self.items_thrown_at_count += 1
    
    def increment_belly_pokes(self):
        """Increment belly poke count."""
        self.belly_poke_count += 1
    
    def increment_falls(self):
        """Increment fall count."""
        self.fall_count += 1
    
    def increment_tip_overs(self):
        """Increment tip-over count."""
        self.tip_over_count += 1
    
    def track_file_processed(self):
        """Track a file being processed."""
        self.files_processed += 1
    
    def track_operation_failure(self):
        """Track a failed operation."""
        self.failed_operations += 1
    
    def add_easter_egg(self):
        """Add to easter egg count."""
        self.easter_eggs_found += 1
    
    # Stat category getters
    def get_base_stats(self) -> Dict:
        """Get all base stats as a dictionary."""
        return {
            'Level': self.level,
            'Experience': f"{self.experience}/{self.get_experience_for_level(self.level + 1)}",
            'Health': f"{self.health}/{self.max_health}",
            'Defense': self.defense,
            'Magic': self.magic,
            'Intelligence': self.intelligence,
            'Strength': self.strength,
            'Agility': self.agility,
            'Vitality': self.vitality,
            'Skill Points': self.skill_points,
        }
    
    def get_combat_stats(self) -> Dict:
        """Get all combat stats as a dictionary."""
        return {
            'Total Attacks': self.total_attacks,
            'Monsters Slain': self.monsters_slain,
            'Damage Dealt': self.damage_dealt,
            'Damage Taken': self.damage_taken,
            'Critical Hits': self.critical_hits,
            'Perfect Dodges': self.perfect_dodges,
            'Spells Cast': self.spells_cast,
            'Healing Done': self.healing_done,
        }
    
    def get_interaction_stats(self) -> Dict:
        """Get all interaction stats as a dictionary."""
        return {
            'Clicks': self.click_count,
            'Pets': self.pet_count,
            'Feeds': self.feed_count,
            'Hovers': self.hover_count,
            'Drags': self.drag_count,
            'Tosses': self.toss_count,
            'Shakes': self.shake_count,
            'Spins': self.spin_count,
            'Toy Interactions': self.toy_interact_count,
            'Clothing Changes': self.clothing_change_count,
            'Items Thrown At': self.items_thrown_at_count,
            'Belly Pokes': self.belly_poke_count,
            'Falls': self.fall_count,
            'Tip-overs': self.tip_over_count,
        }
    
    def get_system_stats(self) -> Dict:
        """Get all system stats as a dictionary."""
        hours = int(self.playtime / 3600)
        minutes = int((self.playtime % 3600) / 60)
        
        return {
            'Playtime': f"{hours}h {minutes}m",
            'Items Collected': self.items_collected,
            'Dungeons Cleared': self.dungeons_cleared,
            'Floors Explored': self.floors_explored,
            'Distance Traveled': f"{self.distance_traveled:.1f}",
            'Times Died': self.times_died,
            'Times Saved': self.times_saved,
            'Files Processed': self.files_processed,
            'Failed Operations': self.failed_operations,
            'Easter Eggs Found': self.easter_eggs_found,
        }
    
    # Persistence methods
    def to_dict(self) -> Dict:
        """Convert stats to dictionary for serialization."""
        return asdict(self)
    
    def save_to_file(self, filepath: str):
        """Save stats to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'PandaStats':
        """Load stats from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PandaStats':
        """Create PandaStats from dictionary."""
        return cls(**data)
