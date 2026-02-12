"""
Travel System - Navigate between locations including procedural dungeons
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LocationType(Enum):
    """Types of locations."""
    HOME = "home"
    DUNGEON = "dungeon"
    TOWN = "town"
    WILDERNESS = "wilderness"
    BOSS_ROOM = "boss_room"


class DungeonDifficulty(Enum):
    """Dungeon difficulty levels."""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXTREME = "extreme"


@dataclass
class Location:
    """Represents a location the panda can travel to."""
    id: str
    name: str
    description: str
    location_type: LocationType
    icon: str
    level_required: int = 1
    unlocked: bool = True
    
    # For dungeons
    difficulty: Optional[DungeonDifficulty] = None
    room_count: int = 5
    enemy_level_range: Tuple[int, int] = (1, 5)


class DungeonRoom:
    """Represents a room in a dungeon."""
    
    def __init__(self, room_id: int, room_type: str):
        """
        Initialize dungeon room.
        
        Args:
            room_id: Unique room identifier
            room_type: Type of room (combat, treasure, rest, boss)
        """
        self.room_id = room_id
        self.room_type = room_type
        self.enemies: List[str] = []  # Enemy type IDs
        self.treasures: List[str] = []  # Loot item IDs
        self.is_cleared = False
        self.is_current = False
        
    def add_enemy(self, enemy_type: str, level: int):
        """Add an enemy to the room."""
        self.enemies.append(f"{enemy_type}:{level}")
    
    def add_treasure(self, item_id: str):
        """Add treasure to the room."""
        self.treasures.append(item_id)
    
    def clear(self):
        """Mark room as cleared."""
        self.is_cleared = True


class ProceduralDungeon:
    """Generates and manages procedural dungeons."""
    
    def __init__(self, difficulty: DungeonDifficulty, player_level: int):
        """
        Generate a procedural dungeon.
        
        Args:
            difficulty: Dungeon difficulty
            player_level: Player's adventure level (for scaling)
        """
        self.difficulty = difficulty
        self.player_level = player_level
        self.rooms: List[DungeonRoom] = []
        self.current_room_index = 0
        
        # Difficulty settings
        self.settings = self._get_difficulty_settings(difficulty)
        
        # Generate dungeon
        self._generate_dungeon()
    
    def _get_difficulty_settings(self, difficulty: DungeonDifficulty) -> dict:
        """Get settings for difficulty level."""
        settings = {
            DungeonDifficulty.EASY: {
                'room_count': random.randint(3, 5),
                'enemy_count_range': (1, 2),
                'level_offset': -1,  # Enemies 1 level below player
                'treasure_chance': 0.6
            },
            DungeonDifficulty.NORMAL: {
                'room_count': random.randint(5, 8),
                'enemy_count_range': (1, 3),
                'level_offset': 0,  # Enemies same level as player
                'treasure_chance': 0.4
            },
            DungeonDifficulty.HARD: {
                'room_count': random.randint(8, 12),
                'enemy_count_range': (2, 4),
                'level_offset': 1,  # Enemies 1 level above player
                'treasure_chance': 0.5
            },
            DungeonDifficulty.EXTREME: {
                'room_count': random.randint(12, 15),
                'enemy_count_range': (3, 5),
                'level_offset': 2,  # Enemies 2 levels above player
                'treasure_chance': 0.7
            }
        }
        
        return settings.get(difficulty, settings[DungeonDifficulty.NORMAL])
    
    def _generate_dungeon(self):
        """Generate dungeon rooms."""
        room_count = self.settings['room_count']
        
        for i in range(room_count):
            # Determine room type
            if i == 0:
                room_type = 'entrance'
            elif i == room_count - 1:
                room_type = 'boss'
            else:
                # Random room type
                roll = random.random()
                if roll < 0.6:
                    room_type = 'combat'
                elif roll < 0.8:
                    room_type = 'treasure'
                else:
                    room_type = 'rest'
            
            room = DungeonRoom(i, room_type)
            
            # Populate room based on type
            if room_type == 'combat':
                self._populate_combat_room(room)
            elif room_type == 'treasure':
                self._populate_treasure_room(room)
            elif room_type == 'boss':
                self._populate_boss_room(room)
            
            self.rooms.append(room)
        
        # Set first room as current
        if self.rooms:
            self.rooms[0].is_current = True
    
    def _populate_combat_room(self, room: DungeonRoom):
        """Populate a combat room with enemies."""
        enemy_count = random.randint(*self.settings['enemy_count_range'])
        
        # Available enemy types
        enemy_types = ['slime', 'goblin', 'skeleton', 'wolf']
        
        for _ in range(enemy_count):
            enemy_type = random.choice(enemy_types)
            enemy_level = max(1, self.player_level + self.settings['level_offset'])
            room.add_enemy(enemy_type, enemy_level)
        
        # Chance for treasure
        if random.random() < self.settings['treasure_chance']:
            self._add_random_treasure(room)
    
    def _populate_treasure_room(self, room: DungeonRoom):
        """Populate a treasure room."""
        # Treasure rooms have guaranteed loot
        treasure_count = random.randint(2, 4)
        for _ in range(treasure_count):
            self._add_random_treasure(room)
    
    def _populate_boss_room(self, room: DungeonRoom):
        """Populate boss room."""
        # Boss enemy
        boss_types = ['orc', 'dragon']
        boss_type = random.choice(boss_types)
        boss_level = self.player_level + self.settings['level_offset'] + 2
        
        room.add_enemy(boss_type, boss_level)
        
        # Boss always has good loot
        for _ in range(3):
            self._add_random_treasure(room)
    
    def _add_random_treasure(self, room: DungeonRoom):
        """Add random treasure to room."""
        treasures = [
            'gold_coin', 'health_potion', 'magic_potion',
            'iron_ore', 'leather', 'gemstone'
        ]
        room.add_treasure(random.choice(treasures))
    
    def get_current_room(self) -> Optional[DungeonRoom]:
        """Get current room."""
        if 0 <= self.current_room_index < len(self.rooms):
            return self.rooms[self.current_room_index]
        return None
    
    def advance_room(self) -> bool:
        """Move to next room."""
        current = self.get_current_room()
        if current:
            current.is_current = False
            current.clear()
        
        self.current_room_index += 1
        
        if self.current_room_index < len(self.rooms):
            self.rooms[self.current_room_index].is_current = True
            return True
        
        return False  # Dungeon completed
    
    def is_complete(self) -> bool:
        """Check if dungeon is complete."""
        return self.current_room_index >= len(self.rooms)
    
    def get_progress(self) -> Tuple[int, int]:
        """Get dungeon progress (current_room, total_rooms)."""
        return (self.current_room_index + 1, len(self.rooms))


class TravelSystem:
    """Manages travel between locations."""
    
    def __init__(self):
        """Initialize travel system."""
        self.locations: Dict[str, Location] = {}
        self.current_location: Optional[Location] = None
        self.current_dungeon: Optional[ProceduralDungeon] = None
        
        self._initialize_locations()
    
    def _initialize_locations(self):
        """Initialize available locations."""
        # Home
        self.locations['home'] = Location(
            id='home',
            name='Panda Home',
            description='A cozy bamboo house where the panda rests',
            location_type=LocationType.HOME,
            icon='🏠',
            level_required=1,
            unlocked=True
        )
        
        # Dungeons
        self.locations['easy_dungeon'] = Location(
            id='easy_dungeon',
            name='Bamboo Forest',
            description='A peaceful forest filled with slimes and goblins',
            location_type=LocationType.DUNGEON,
            icon='🌳',
            level_required=1,
            unlocked=True,
            difficulty=DungeonDifficulty.EASY,
            room_count=5,
            enemy_level_range=(1, 3)
        )
        
        self.locations['normal_dungeon'] = Location(
            id='normal_dungeon',
            name='Dark Cave',
            description='A mysterious cave inhabited by skeletons',
            location_type=LocationType.DUNGEON,
            icon='🕳️',
            level_required=5,
            unlocked=False,
            difficulty=DungeonDifficulty.NORMAL,
            room_count=8,
            enemy_level_range=(5, 10)
        )
        
        self.locations['hard_dungeon'] = Location(
            id='hard_dungeon',
            name='Orc Stronghold',
            description='A fortified keep controlled by orc warriors',
            location_type=LocationType.DUNGEON,
            icon='🏰',
            level_required=10,
            unlocked=False,
            difficulty=DungeonDifficulty.HARD,
            room_count=12,
            enemy_level_range=(10, 15)
        )
        
        self.locations['extreme_dungeon'] = Location(
            id='extreme_dungeon',
            name="Dragon's Lair",
            description='The legendary lair of an ancient dragon',
            location_type=LocationType.DUNGEON,
            icon='🐉',
            level_required=20,
            unlocked=False,
            difficulty=DungeonDifficulty.EXTREME,
            room_count=15,
            enemy_level_range=(20, 25)
        )
        
        # Start at home
        self.current_location = self.locations['home']
    
    def travel_to(self, location_id: str, player_level: int = 1) -> Tuple[bool, str]:
        """
        Travel to a location.
        
        Args:
            location_id: ID of location to travel to
            player_level: Player's adventure level
        
        Returns:
            (success, message)
        """
        location = self.locations.get(location_id)
        
        if not location:
            return (False, "Location not found")
        
        if not location.unlocked:
            return (False, f"{location.name} is locked. Reach level {location.level_required} to unlock.")
        
        if player_level < location.level_required:
            return (False, f"You need to be level {location.level_required} to enter {location.name}")
        
        # Travel to location
        self.current_location = location
        
        # If dungeon, generate it
        if location.location_type == LocationType.DUNGEON and location.difficulty:
            self.current_dungeon = ProceduralDungeon(location.difficulty, player_level)
            return (True, f"Entered {location.name}! Dungeon generated with {len(self.current_dungeon.rooms)} rooms.")
        else:
            self.current_dungeon = None
            return (True, f"Traveled to {location.name}")
    
    def get_available_locations(self) -> List[Location]:
        """Get all unlocked locations."""
        return [loc for loc in self.locations.values() if loc.unlocked]
    
    def unlock_location(self, location_id: str) -> bool:
        """Unlock a location."""
        location = self.locations.get(location_id)
        if location:
            location.unlocked = True
            logger.info(f"Unlocked location: {location_id}")
            return True
        return False
    
    def get_current_dungeon_info(self) -> Optional[Dict]:
        """Get current dungeon information."""
        if not self.current_dungeon:
            return None
        
        current_room = self.current_dungeon.get_current_room()
        progress = self.current_dungeon.get_progress()
        
        return {
            'difficulty': self.current_dungeon.difficulty.value,
            'current_room': progress[0],
            'total_rooms': progress[1],
            'room_type': current_room.room_type if current_room else 'unknown',
            'is_complete': self.current_dungeon.is_complete()
        }
