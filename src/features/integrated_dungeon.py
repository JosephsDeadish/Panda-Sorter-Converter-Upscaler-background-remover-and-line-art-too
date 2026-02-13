"""
Integrated Dungeon System - Combines all game systems.
Manages enemies, combat, loot, and navigation in the dungeon.
"""

import random
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from src.features.dungeon_generator import DungeonGenerator, DungeonFloor, Room
from src.features.enemy_system import Enemy, EnemyCollection
from src.features.damage_system import DamageTracker, DamageCategory, LimbType
from src.features.projectile_system import ProjectileManager, ProjectileType


@dataclass
class LootItem:
    """Represents a loot item in the dungeon."""
    x: int
    y: int
    item_type: str  # 'health', 'weapon', 'gold', 'key'
    value: int
    collected: bool = False


@dataclass
class SpawnedEnemy:
    """Represents a spawned enemy in the dungeon."""
    enemy: Enemy
    x: int
    y: int
    damage_tracker: DamageTracker
    is_alive: bool = True
    target_x: Optional[int] = None
    target_y: Optional[int] = None


class IntegratedDungeon:
    """
    Manages the complete dungeon experience with all systems integrated.
    """
    
    # AI Constants
    ATTACK_RANGE = 2  # Distance at which enemies attack
    AGGRO_RANGE = 15  # Distance at which enemies notice player
    MELEE_RANGE = 1   # Distance for player melee attacks
    
    def __init__(self, width: int = 80, height: int = 80, num_floors: int = 5, seed: Optional[int] = None):
        """
        Initialize the integrated dungeon.
        
        Args:
            width: Dungeon width in tiles
            height: Dungeon height in tiles
            num_floors: Number of floors
            seed: Random seed for reproducibility
        """
        # Core dungeon
        self.dungeon = DungeonGenerator(width, height, num_floors, seed)
        
        # Enemy collection
        self.enemy_collection = EnemyCollection()
        
        # Spawned entities per floor
        self.enemies_by_floor: Dict[int, List[SpawnedEnemy]] = {}
        self.loot_by_floor: Dict[int, List[LootItem]] = {}
        
        # Projectile manager
        self.projectile_manager = ProjectileManager()
        
        # Player state
        self.player_floor = 0
        self.player_x = 0
        self.player_y = 0
        self.player_health = 100
        self.player_max_health = 100
        self.player_damage_tracker = DamageTracker()
        
        # Statistics
        self.enemies_killed = 0
        self.loot_collected = 0
        self.exploration_percentage = 0.0
        
        # Initialize all floors
        self._initialize_all_floors()
    
    def _initialize_all_floors(self):
        """Initialize enemies and loot for all floors."""
        for floor_num in range(len(self.dungeon.floors)):
            self._spawn_enemies_on_floor(floor_num)
            self._spawn_loot_on_floor(floor_num)
    
    def _spawn_enemies_on_floor(self, floor_num: int):
        """Spawn enemies on a specific floor."""
        floor = self.dungeon.get_floor(floor_num)
        if not floor:
            return
        
        self.enemies_by_floor[floor_num] = []
        
        # Difficulty scaling by floor
        min_level = 1 + floor_num
        max_level = 3 + floor_num * 2
        
        # Spawn enemies in rooms (except spawn room)
        for room in floor.rooms:
            if room.room_type == 'spawn':
                continue  # No enemies in spawn room
            
            # Determine number of enemies based on room type
            if room.room_type == 'boss':
                num_enemies = 1  # Single boss
                enemy_level = max_level + 5
            elif room.room_type == 'treasure':
                num_enemies = random.randint(2, 4)  # Guarded treasure
                enemy_level = random.randint(min_level, max_level)
            else:
                num_enemies = random.randint(1, 3)  # Normal room
                enemy_level = random.randint(min_level, max_level)
            
            # Spawn enemies
            for _ in range(num_enemies):
                # Choose enemy type based on floor
                if room.room_type == 'boss':
                    enemy_template = 'dragon'
                elif floor_num >= 4:
                    enemy_template = random.choice(['orc', 'dragon', 'skeleton'])
                elif floor_num >= 2:
                    enemy_template = random.choice(['wolf', 'skeleton', 'orc'])
                else:
                    enemy_template = random.choice(['slime', 'goblin', 'wolf'])
                
                # Create enemy
                enemy = self.enemy_collection.create_enemy(enemy_template, enemy_level)
                
                # Random position in room
                spawn_x = random.randint(room.x + 1, room.x + room.width - 2)
                spawn_y = random.randint(room.y + 1, room.y + room.height - 2)
                
                # Add to spawned enemies
                spawned = SpawnedEnemy(
                    enemy=enemy,
                    x=spawn_x,
                    y=spawn_y,
                    damage_tracker=DamageTracker()
                )
                self.enemies_by_floor[floor_num].append(spawned)
    
    def _spawn_loot_on_floor(self, floor_num: int):
        """Spawn loot on a specific floor."""
        floor = self.dungeon.get_floor(floor_num)
        if not floor:
            return
        
        self.loot_by_floor[floor_num] = []
        
        # Spawn loot in treasure rooms
        for room in floor.rooms:
            if room.room_type == 'treasure':
                # Place multiple loot items
                for _ in range(random.randint(3, 6)):
                    loot_x = random.randint(room.x + 1, room.x + room.width - 2)
                    loot_y = random.randint(room.y + 1, room.y + room.height - 2)
                    
                    loot_type = random.choice(['health', 'weapon', 'gold', 'gold', 'gold'])
                    value = random.randint(10, 50) if loot_type == 'gold' else 1
                    
                    loot = LootItem(
                        x=loot_x,
                        y=loot_y,
                        item_type=loot_type,
                        value=value
                    )
                    self.loot_by_floor[floor_num].append(loot)
            
            # Occasionally place loot in normal rooms
            elif room.room_type == 'normal' and random.random() < 0.3:
                loot_x, loot_y = room.center
                loot = LootItem(
                    x=loot_x,
                    y=loot_y,
                    item_type='health',
                    value=1
                )
                self.loot_by_floor[floor_num].append(loot)
    
    def set_player_position(self, floor_num: int, x: int, y: int):
        """Set player position."""
        self.player_floor = floor_num
        self.player_x = x
        self.player_y = y
    
    def teleport_to_spawn(self):
        """Teleport player to spawn point on current floor."""
        floor = self.dungeon.get_floor(self.player_floor)
        if floor and floor.spawn_point:
            self.player_x, self.player_y = floor.spawn_point
    
    def move_player(self, dx: int, dy: int) -> bool:
        """
        Attempt to move player.
        
        Args:
            dx, dy: Direction to move
            
        Returns:
            True if move was successful
        """
        new_x = self.player_x + dx
        new_y = self.player_y + dy
        
        # Check collision
        if self.dungeon.is_walkable(self.player_floor, new_x, new_y):
            self.player_x = new_x
            self.player_y = new_y
            
            # Check for loot pickup
            self._check_loot_pickup()
            
            # Check for stairs
            self._check_stairs()
            
            return True
        
        return False
    
    def _check_loot_pickup(self):
        """Check if player is on loot and pick it up."""
        if self.player_floor not in self.loot_by_floor:
            return
        
        for loot in self.loot_by_floor[self.player_floor]:
            if not loot.collected and loot.x == self.player_x and loot.y == self.player_y:
                loot.collected = True
                self.loot_collected += 1
                
                # Apply loot effect
                if loot.item_type == 'health':
                    self.player_health = min(self.player_max_health, self.player_health + 20)
                elif loot.item_type == 'gold':
                    pass  # Gold tracked separately
    
    def _check_stairs(self) -> Optional[str]:
        """Check if player is on stairs and return the stair type."""
        floor = self.dungeon.get_floor(self.player_floor)
        if not floor:
            return None
        
        # Check stairs down
        if (self.player_x, self.player_y) in floor.stairs_down:
            return 'stairs_down'
        
        # Check stairs up
        if (self.player_x, self.player_y) in floor.stairs_up:
            return 'stairs_up'
        
        return None
    
    def use_stairs(self, going_up: bool) -> bool:
        """
        Use stairs to change floor.
        
        Args:
            going_up: True for up, False for down
            
        Returns:
            True if successful
        """
        floor = self.dungeon.get_floor(self.player_floor)
        if not floor:
            return False
        
        # Check if on stairs
        on_stairs_up = (self.player_x, self.player_y) in floor.stairs_up
        on_stairs_down = (self.player_x, self.player_y) in floor.stairs_down
        
        if going_up and on_stairs_up and self.player_floor > 0:
            # Go up
            self.player_floor -= 1
            new_floor = self.dungeon.get_floor(self.player_floor)
            if new_floor and new_floor.stairs_down:
                self.player_x, self.player_y = new_floor.stairs_down[0]
            return True
        
        elif not going_up and on_stairs_down and self.player_floor < len(self.dungeon.floors) - 1:
            # Go down
            self.player_floor += 1
            new_floor = self.dungeon.get_floor(self.player_floor)
            if new_floor and new_floor.stairs_up:
                self.player_x, self.player_y = new_floor.stairs_up[0]
            return True
        
        return False
    
    def get_enemies_on_current_floor(self) -> List[SpawnedEnemy]:
        """Get all living enemies on current floor."""
        if self.player_floor not in self.enemies_by_floor:
            return []
        
        return [e for e in self.enemies_by_floor[self.player_floor] if e.is_alive]
    
    def get_loot_on_current_floor(self) -> List[LootItem]:
        """Get all uncollected loot on current floor."""
        if self.player_floor not in self.loot_by_floor:
            return []
        
        return [l for l in self.loot_by_floor[self.player_floor] if not l.collected]
    
    def update_enemies(self, delta_time: float):
        """
        Update enemy AI and movement.
        
        Args:
            delta_time: Time since last update
        """
        enemies = self.get_enemies_on_current_floor()
        
        for spawned in enemies:
            # Simple AI: move toward player
            dx = self.player_x - spawned.x
            dy = self.player_y - spawned.y
            distance = (dx * dx + dy * dy) ** 0.5
            
            # If close enough, attack
            if distance < self.ATTACK_RANGE:
                # Enemy attacks player
                damage = spawned.enemy.stats.attack
                self.player_damage_tracker.apply_damage(
                    LimbType.TORSO,
                    DamageCategory.SHARP,
                    damage
                )
                self.player_health -= damage
            
            # Move toward player
            elif distance < self.AGGRO_RANGE:  # Aggro range
                # Determine move direction
                move_x = 1 if dx > 0 else -1 if dx < 0 else 0
                move_y = 1 if dy > 0 else -1 if dy < 0 else 0
                
                # Try to move
                new_x = spawned.x + move_x
                new_y = spawned.y + move_y
                
                if self.dungeon.is_walkable(self.player_floor, new_x, new_y):
                    spawned.x = new_x
                    spawned.y = new_y
    
    def player_attack_nearby_enemies(self, weapon_damage: int = 25):
        """Player attacks enemies in melee range."""
        enemies = self.get_enemies_on_current_floor()
        
        for spawned in enemies:
            dx = abs(self.player_x - spawned.x)
            dy = abs(self.player_y - spawned.y)
            
            # If in melee range
            if dx <= self.MELEE_RANGE and dy <= self.MELEE_RANGE:
                # Apply damage
                result = spawned.damage_tracker.apply_damage(
                    LimbType.TORSO,
                    DamageCategory.SHARP,
                    weapon_damage
                )
                
                # Damage enemy health
                spawned.enemy.take_damage(weapon_damage)
                
                # Check if dead
                if not spawned.enemy.is_alive():
                    spawned.is_alive = False
                    self.enemies_killed += 1
    
    def get_player_state(self) -> Dict:
        """Get player state dictionary."""
        return {
            'floor': self.player_floor,
            'x': self.player_x,
            'y': self.player_y,
            'health': self.player_health,
            'max_health': self.player_max_health,
            'enemies_killed': self.enemies_killed,
            'loot_collected': self.loot_collected,
            'movement_penalty': self.player_damage_tracker.get_movement_penalty(),
            'attack_penalty': self.player_damage_tracker.get_attack_penalty()
        }
