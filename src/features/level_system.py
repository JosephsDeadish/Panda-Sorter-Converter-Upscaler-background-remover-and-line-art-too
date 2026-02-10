"""
Level/XP System - User and Panda progression
Track experience points and levels for both user and panda
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import json
import math
from pathlib import Path
from typing import Dict, Optional, Callable, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class LevelReward(Enum):
    """Types of level rewards."""
    MONEY = "money"
    UNLOCK = "unlock"
    ABILITY = "ability"
    TITLE = "title"


@dataclass
class Level:
    """Represents a level."""
    level: int
    xp_required: int
    rewards: List[Dict]
    title: str = ""


class LevelSystem:
    """Base class for level/XP tracking."""
    
    def __init__(self, name: str, save_path: Optional[Path] = None):
        """
        Initialize level system.
        
        Args:
            name: Name of the system (user/panda)
            save_path: Path to save level data
        """
        self.name = name
        self.save_path = save_path or Path.home() / '.ps2_texture_sorter' / f'{name}_level.json'
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.level = 1
        self.xp = 0
        self.total_xp = 0
        
        # Callbacks for level up events
        self.level_up_callbacks: List[Callable] = []
        
        # Load saved data
        self.load()
    
    def calculate_xp_for_level(self, level: int) -> int:
        """
        Calculate XP required for a level.
        Uses exponential formula: XP = 100 * (level^1.5)
        
        Args:
            level: Target level
            
        Returns:
            XP required for that level
        """
        return int(100 * math.pow(level, 1.5))
    
    def get_xp_to_next_level(self) -> int:
        """Get XP needed for next level."""
        current_level_xp = self.calculate_xp_for_level(self.level)
        next_level_xp = self.calculate_xp_for_level(self.level + 1)
        return next_level_xp - current_level_xp
    
    def get_progress_to_next_level(self) -> float:
        """Get progress percentage to next level (0-100)."""
        xp_needed = self.get_xp_to_next_level()
        if xp_needed <= 0:
            return 100.0
        return (self.xp / xp_needed) * 100.0
    
    def add_xp(self, amount: int, reason: str = "") -> Tuple[bool, int]:
        """
        Add XP and check for level up.
        
        Args:
            amount: XP to add
            reason: Reason for XP gain
            
        Returns:
            Tuple of (leveled_up, new_level)
        """
        self.xp += amount
        self.total_xp += amount
        
        logger.info(f"{self.name} gained {amount} XP for '{reason}'. Total: {self.xp}")
        
        # Check for level up - optimized to handle large XP gains
        leveled_up = False
        old_level = self.level
        
        # Calculate how many levels can be gained
        while self.xp >= self.get_xp_to_next_level():
            xp_needed = self.get_xp_to_next_level()
            if xp_needed <= 0:
                break
            
            self.xp -= xp_needed
            self.level += 1
            leveled_up = True
            logger.info(f"{self.name} leveled up! Now level {self.level}")
            
            # Safety check to prevent infinite loops
            if self.level > 1000:
                logger.error(f"Level cap exceeded, capping at 1000")
                self.level = 1000
                break
        
        if leveled_up:
            # Trigger callbacks
            for callback in self.level_up_callbacks:
                try:
                    callback(old_level, self.level)
                except Exception as e:
                    logger.error(f"Error in level up callback: {e}")
        
        self.save()
        return leveled_up, self.level
    
    def get_xp_reward(self, action: str) -> int:
        """
        Get XP reward for an action (encapsulated access).
        
        Args:
            action: Action name
            
        Returns:
            XP amount for that action
        """
        return self.XP_REWARDS.get(action, 0)
    
    def register_level_up_callback(self, callback: Callable):
        """Register callback for level up events."""
        self.level_up_callbacks.append(callback)
    
    def get_statistics(self) -> Dict:
        """Get level statistics."""
        return {
            'name': self.name,
            'level': self.level,
            'xp': self.xp,
            'total_xp': self.total_xp,
            'xp_to_next': self.get_xp_to_next_level(),
            'progress_percent': self.get_progress_to_next_level(),
        }
    
    def save(self):
        """Save level data to file."""
        try:
            data = {
                'level': self.level,
                'xp': self.xp,
                'total_xp': self.total_xp,
            }
            
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {self.name} level data to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save {self.name} level data: {e}")
    
    def load(self):
        """Load level data from file."""
        try:
            if self.save_path.exists():
                with open(self.save_path, 'r') as f:
                    data = json.load(f)
                
                self.level = data.get('level', 1)
                self.xp = data.get('xp', 0)
                self.total_xp = data.get('total_xp', 0)
                
                logger.info(f"Loaded {self.name} level data. Level: {self.level}, XP: {self.xp}")
            else:
                logger.info(f"No saved {self.name} level data found. Starting fresh.")
        except Exception as e:
            logger.error(f"Failed to load {self.name} level data: {e}")


class UserLevelSystem(LevelSystem):
    """Level system for the user."""
    
    # XP rewards for various actions
    XP_REWARDS = {
        # File operations
        'file_processed': 1,
        'batch_complete': 50,
        'conversion_complete': 2,
        
        # Achievements
        'achievement_bronze': 25,
        'achievement_silver': 50,
        'achievement_gold': 100,
        'achievement_platinum': 250,
        'achievement_legendary': 500,
        
        # Tutorials
        'tutorial_complete': 100,
        
        # Usage
        'session_hour': 25,
        'feature_discovered': 10,
    }
    
    def __init__(self, save_path: Optional[Path] = None):
        """Initialize user level system."""
        super().__init__('user', save_path)
    
    def get_title_for_level(self) -> str:
        """Get title based on level."""
        if self.level >= 100:
            return "Legendary Sorter"
        elif self.level >= 75:
            return "Master Sorter"
        elif self.level >= 50:
            return "Expert Sorter"
        elif self.level >= 25:
            return "Advanced Sorter"
        elif self.level >= 10:
            return "Intermediate Sorter"
        elif self.level >= 5:
            return "Apprentice Sorter"
        else:
            return "Novice Sorter"
    
    def get_rewards_for_level(self, level: int) -> List[Dict]:
        """Get rewards for reaching a level."""
        rewards = []
        
        # Every 5 levels: money bonus
        if level % 5 == 0:
            rewards.append({
                'type': LevelReward.MONEY.value,
                'amount': level * 10,
                'description': f'${level * 10} bonus'
            })
        
        # Every 10 levels: title upgrade
        if level % 10 == 0:
            title = self.get_title_for_level()
            rewards.append({
                'type': LevelReward.TITLE.value,
                'value': title,
                'description': f'New title: {title}'
            })
        
        # Special milestones
        if level == 25:
            rewards.append({
                'type': LevelReward.UNLOCK.value,
                'value': 'pro_theme',
                'description': 'Unlocked Pro Theme'
            })
        
        if level == 50:
            rewards.append({
                'type': LevelReward.UNLOCK.value,
                'value': 'master_cursor',
                'description': 'Unlocked Master Cursor'
            })
        
        return rewards


class PandaLevelSystem(LevelSystem):
    """Level system for the panda companion."""
    
    # XP rewards for panda interactions
    XP_REWARDS = {
        'click': 1,
        'pet': 5,
        'feed': 10,
        'hover': 1,
        'play_game': 20,
        'mood_change': 5,
    }
    
    def __init__(self, save_path: Optional[Path] = None):
        """Initialize panda level system."""
        super().__init__('panda', save_path)
    
    def get_title_for_level(self) -> str:
        """Get panda title based on level."""
        if self.level >= 100:
            return "Legendary Panda"
        elif self.level >= 75:
            return "Master Panda"
        elif self.level >= 50:
            return "Wise Panda"
        elif self.level >= 25:
            return "Happy Panda"
        elif self.level >= 10:
            return "Playful Panda"
        elif self.level >= 5:
            return "Young Panda"
        else:
            return "Baby Panda"
    
    def get_abilities_for_level(self) -> List[str]:
        """Get panda abilities based on level."""
        abilities = []
        
        if self.level >= 5:
            abilities.append("🎋 Bamboo Master: Faster eating animations")
        if self.level >= 10:
            abilities.append("💬 Chatty: More dialogue options")
        if self.level >= 25:
            abilities.append("🎭 Actor: Additional mood states")
        if self.level >= 50:
            abilities.append("🎪 Entertainer: Special animations")
        if self.level >= 75:
            abilities.append("🧙 Sage: Wisdom mode unlocked")
        if self.level >= 100:
            abilities.append("👑 Legend: All abilities mastered")
        
        return abilities
    
    def get_rewards_for_level(self, level: int) -> List[Dict]:
        """Get rewards for panda reaching a level."""
        rewards = []
        
        # Every 5 levels: new outfit
        if level % 5 == 0:
            rewards.append({
                'type': LevelReward.UNLOCK.value,
                'value': f'panda_outfit_lvl{level}',
                'description': f'New panda outfit unlocked!'
            })
        
        # Every 10 levels: ability unlock
        if level % 10 == 0:
            abilities = self.get_abilities_for_level()
            if abilities:
                rewards.append({
                    'type': LevelReward.ABILITY.value,
                    'value': abilities[-1],
                    'description': 'New panda ability!'
                })
        
        # Title upgrades
        if level in [5, 10, 25, 50, 75, 100]:
            title = self.get_title_for_level()
            rewards.append({
                'type': LevelReward.TITLE.value,
                'value': title,
                'description': f'Panda promoted to: {title}'
            })
        
        return rewards
