"""
Enemy Manager - Manages multiple enemy widgets and their interactions
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
from typing import List, Optional, Dict, Callable
import time

logger = logging.getLogger(__name__)


class EnemyManager:
    """Manages spawning and updating multiple enemy widgets."""
    
    def __init__(self, parent, panda_widget, enemy_collection, 
                 on_panda_attacked: Optional[Callable] = None):
        """
        Initialize enemy manager.
        
        Args:
            parent: Parent widget for enemy widgets
            panda_widget: PandaWidget that enemies will target
            enemy_collection: EnemyCollection for creating enemies
            on_panda_attacked: Callback when panda is attacked (receives enemy)
        """
        self.parent = parent
        self.panda_widget = panda_widget
        self.enemy_collection = enemy_collection
        self.on_panda_attacked = on_panda_attacked
        
        # Track active enemies
        self.active_enemies: List = []  # List of (enemy_widget, enemy_data)
        self.max_enemies = 5
        
        # Spawn timing
        self.last_spawn_time = 0
        self.spawn_cooldown = 5.0  # seconds between spawns
        self.auto_spawn = False
        
        # Stats
        self.total_enemies_spawned = 0
        self.total_enemies_defeated = 0
    
    def enable_auto_spawn(self, enabled: bool = True):
        """Enable or disable automatic enemy spawning."""
        self.auto_spawn = enabled
        logger.info(f"Auto-spawn {'enabled' if enabled else 'disabled'}")
    
    def set_spawn_cooldown(self, seconds: float):
        """Set time between auto-spawns."""
        self.spawn_cooldown = max(1.0, seconds)
    
    def set_max_enemies(self, max_count: int):
        """Set maximum number of simultaneous enemies."""
        self.max_enemies = max(1, max_count)
    
    def spawn_enemy(self, enemy_type: str = None, level: int = 1) -> bool:
        """
        Spawn a new enemy.
        
        Args:
            enemy_type: Type of enemy to spawn (random if None)
            level: Enemy level
            
        Returns:
            True if enemy was spawned successfully
        """
        # Check if we can spawn more enemies
        if len(self.active_enemies) >= self.max_enemies:
            logger.debug("Max enemies reached, cannot spawn more")
            return False
        
        try:
            # Import here to avoid circular imports
            from src.ui.enemy_widget import EnemyWidget
            
            # Choose random enemy type if not specified
            if enemy_type is None:
                enemy_types = self.enemy_collection.get_all_types()
                enemy_type = random.choice(enemy_types)
            
            # Create enemy instance
            enemy = self.enemy_collection.create_enemy(enemy_type, level)
            if not enemy:
                logger.error(f"Failed to create enemy: {enemy_type}")
                return False
            
            # Create enemy widget
            enemy_widget = EnemyWidget(
                self.parent,
                enemy,
                self.panda_widget,
                on_attack=self._on_enemy_attack,
                on_death=self._on_enemy_death
            )
            
            # Track the enemy
            self.active_enemies.append((enemy_widget, enemy))
            self.total_enemies_spawned += 1
            
            logger.info(f"Spawned {enemy.name} at level {level}")
            return True
            
        except Exception as e:
            logger.error(f"Error spawning enemy: {e}")
            return False
    
    def spawn_wave(self, count: int, enemy_type: str = None, level: int = 1):
        """
        Spawn multiple enemies at once.
        
        Args:
            count: Number of enemies to spawn
            enemy_type: Type (random if None)
            level: Enemy level
        """
        spawned = 0
        for _ in range(count):
            if self.spawn_enemy(enemy_type, level):
                spawned += 1
            else:
                break
        
        logger.info(f"Spawned wave of {spawned}/{count} enemies")
    
    def _on_enemy_attack(self, enemy):
        """Called when an enemy attacks."""
        logger.info(f"{enemy.name} attacks the panda!")
        
        # Notify callback if provided
        if self.on_panda_attacked:
            self.on_panda_attacked(enemy)
    
    def _on_enemy_death(self, enemy):
        """Called when an enemy dies."""
        logger.info(f"{enemy.name} has been defeated!")
        self.total_enemies_defeated += 1
        
        # Remove from active enemies list
        self.active_enemies = [
            (ew, e) for ew, e in self.active_enemies 
            if e is not enemy
        ]
    
    def update(self):
        """
        Update enemy manager (call periodically).
        Handles auto-spawning and cleanup.
        """
        current_time = time.time()
        
        # Auto-spawn if enabled
        if self.auto_spawn:
            if current_time - self.last_spawn_time >= self.spawn_cooldown:
                if self.spawn_enemy():
                    self.last_spawn_time = current_time
        
        # Clean up dead enemies
        self.active_enemies = [
            (ew, e) for ew, e in self.active_enemies 
            if e.is_alive() and not ew._destroyed
        ]
    
    def get_active_count(self) -> int:
        """Get number of active enemies."""
        return len(self.active_enemies)
    
    def get_enemies(self) -> List:
        """Get list of active enemy instances."""
        return [enemy for _, enemy in self.active_enemies]
    
    def clear_all(self):
        """Remove all active enemies."""
        for enemy_widget, _ in self.active_enemies:
            try:
                enemy_widget.destroy()
            except Exception as e:
                logger.debug(f"Error destroying enemy widget: {e}")
        
        self.active_enemies.clear()
        logger.info("Cleared all enemies")
    
    def get_stats(self) -> Dict:
        """Get enemy manager statistics."""
        return {
            'active_enemies': len(self.active_enemies),
            'max_enemies': self.max_enemies,
            'total_spawned': self.total_enemies_spawned,
            'total_defeated': self.total_enemies_defeated,
            'auto_spawn_enabled': self.auto_spawn,
            'spawn_cooldown': self.spawn_cooldown
        }
    
    def damage_all_enemies(self, damage: int):
        """Damage all active enemies (for testing/AOE attacks)."""
        for enemy_widget, enemy in self.active_enemies:
            try:
                enemy_widget.take_damage(damage)
            except Exception as e:
                logger.debug(f"Error damaging enemy: {e}")
    
    def get_nearest_enemy(self, x: int, y: int):
        """
        Get the nearest enemy to a position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Tuple of (enemy_widget, enemy, distance) or None
        """
        nearest = None
        nearest_dist = float('inf')
        
        for enemy_widget, enemy in self.active_enemies:
            try:
                ex, ey = enemy_widget.get_position()
                dist = ((ex - x) ** 2 + (ey - y) ** 2) ** 0.5
                
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest = (enemy_widget, enemy, dist)
            except Exception:
                continue
        
        return nearest
