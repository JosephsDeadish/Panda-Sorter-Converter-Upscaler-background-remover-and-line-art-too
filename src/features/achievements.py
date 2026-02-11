"""
Achievement System - Gamification and progress tracking
Track user milestones and unlock achievements
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class AchievementTier(Enum):
    """Achievement difficulty tiers."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    LEGENDARY = "legendary"


@dataclass
class Achievement:
    """Represents an achievement."""
    id: str
    name: str
    description: str
    tier: AchievementTier
    points: int
    icon: str = "🏆"
    hidden: bool = False
    unlocked: bool = False
    unlock_date: Optional[str] = None
    progress: float = 0.0
    progress_max: float = 100.0
    category: str = "general"
    reward: Optional[Dict] = None  # Direct reward on unlock, e.g. {'type': 'currency', 'amount': 100}
    
    def is_complete(self) -> bool:
        """Check if achievement is complete."""
        return self.progress >= self.progress_max
    
    def get_progress_percent(self) -> float:
        """Get progress as percentage."""
        if self.progress_max <= 0:
            return 0.0
        return (self.progress / self.progress_max) * 100.0


class AchievementSystem:
    """Manages achievement tracking and unlocking."""
    
    # Achievement definitions
    ACHIEVEMENTS = {
        # Beginner achievements
        'first_sort': Achievement(
            id='first_sort',
            name='First Steps',
            description='Complete your first texture sort',
            tier=AchievementTier.BRONZE,
            points=10,
            icon='🎯',
            category='beginner',
            progress_max=1,
            reward={'type': 'currency', 'amount': 50, 'description': '50 Bamboo Bucks'}
        ),
        'rookie_sorter': Achievement(
            id='rookie_sorter',
            name='Rookie Sorter',
            description='Sort 100 textures',
            tier=AchievementTier.BRONZE,
            points=25,
            icon='📦',
            category='progress',
            progress_max=100,
            reward={'type': 'currency', 'amount': 100, 'description': '100 Bamboo Bucks'}
        ),
        
        # Progress achievements
        'apprentice': Achievement(
            id='apprentice',
            name='Apprentice Sorter',
            description='Sort 1,000 textures',
            tier=AchievementTier.SILVER,
            points=50,
            icon='📊',
            category='progress',
            progress_max=1000,
            reward={'type': 'currency', 'amount': 250, 'description': '250 Bamboo Bucks'}
        ),
        'journeyman': Achievement(
            id='journeyman',
            name='Journeyman Sorter',
            description='Sort 10,000 textures',
            tier=AchievementTier.GOLD,
            points=100,
            icon='⚡',
            category='progress',
            progress_max=10000,
            reward={'type': 'currency', 'amount': 500, 'description': '500 Bamboo Bucks'}
        ),
        'master': Achievement(
            id='master',
            name='Master Sorter',
            description='Sort 50,000 textures',
            tier=AchievementTier.PLATINUM,
            points=250,
            icon='👑',
            category='progress',
            progress_max=50000,
            reward={'type': 'exclusive_title', 'title': 'Master Sorter', 'description': 'Exclusive "Master Sorter" title'}
        ),
        'legend': Achievement(
            id='legend',
            name='Legendary Sorter',
            description='Sort 200,000 textures',
            tier=AchievementTier.LEGENDARY,
            points=500,
            icon='⭐',
            category='progress',
            progress_max=200000,
            reward={'type': 'exclusive_title', 'title': 'Legendary Sorter', 'description': 'Exclusive "Legendary Sorter" title'}
        ),
        
        # Speed achievements
        'speed_demon': Achievement(
            id='speed_demon',
            name='Speed Demon',
            description='Sort 1,000 textures in under 5 minutes',
            tier=AchievementTier.GOLD,
            points=100,
            icon='⚡',
            category='speed',
            progress_max=1,
            reward={'type': 'currency', 'amount': 300, 'description': '300 Bamboo Bucks'}
        ),
        'lightning_fast': Achievement(
            id='lightning_fast',
            name='Lightning Fast',
            description='Sort 10,000 textures in under 30 minutes',
            tier=AchievementTier.PLATINUM,
            points=200,
            icon='⚡',
            category='speed',
            progress_max=1
        ),
        
        # Session achievements
        'marathon': Achievement(
            id='marathon',
            name='Marathon Runner',
            description='Run the sorter for 4 hours straight',
            tier=AchievementTier.SILVER,
            points=75,
            icon='🏃',
            category='session',
            progress_max=240  # minutes
        ),
        'dedicated': Achievement(
            id='dedicated',
            name='Dedicated User',
            description='Use the sorter for 10 days',
            tier=AchievementTier.GOLD,
            points=100,
            icon='📅',
            category='session',
            progress_max=10
        ),
        
        # Feature usage
        'profile_master': Achievement(
            id='profile_master',
            name='Profile Master',
            description='Create 5 custom organization profiles',
            tier=AchievementTier.SILVER,
            points=50,
            icon='📝',
            category='features',
            progress_max=5
        ),
        'backup_hero': Achievement(
            id='backup_hero',
            name='Backup Hero',
            description='Create 10 backups',
            tier=AchievementTier.BRONZE,
            points=30,
            icon='💾',
            category='features',
            progress_max=10
        ),
        'search_master': Achievement(
            id='search_master',
            name='Search Master',
            description='Use search feature 50 times',
            tier=AchievementTier.BRONZE,
            points=25,
            icon='🔍',
            category='features',
            progress_max=50
        ),
        
        # Quality achievements
        'perfectionist': Achievement(
            id='perfectionist',
            name='Perfectionist',
            description='Complete 10 sorts with 100% success rate',
            tier=AchievementTier.GOLD,
            points=150,
            icon='💯',
            category='quality',
            progress_max=10,
            reward={'type': 'currency', 'amount': 500, 'description': '500 Bamboo Bucks'}
        ),
        
        # Special/Hidden achievements
        'panda_lover': Achievement(
            id='panda_lover',
            name='Panda Lover',
            description='Interact with your panda companion',
            tier=AchievementTier.BRONZE,
            points=20,
            icon='🐼',
            category='special',
            hidden=True,
            progress_max=1,
            reward={'type': 'exclusive_item', 'item': 'panda_badge', 'description': 'Exclusive Panda Lover badge'}
        ),
        'achievement_hunter': Achievement(
            id='achievement_hunter',
            name='Achievement Hunter',
            description='Unlock 50% of all achievements',
            tier=AchievementTier.PLATINUM,
            points=300,
            icon='🏆',
            category='meta',
            progress_max=50  # percentage
        ),
        'completionist': Achievement(
            id='completionist',
            name='Completionist',
            description='Unlock ALL achievements',
            tier=AchievementTier.LEGENDARY,
            points=1000,
            icon='🌟',
            category='meta',
            hidden=True,
            progress_max=100,  # percentage
            reward={'type': 'exclusive_title', 'title': 'Completionist', 'description': 'Exclusive "Completionist" title + 5000 Bamboo Bucks'}
        ),
        
        # Easter eggs
        'konami_code': Achievement(
            id='konami_code',
            name='Old School Gamer',
            description='Enter the Konami Code',
            tier=AchievementTier.SILVER,
            points=50,
            icon='🎮',
            category='easter_egg',
            hidden=True,
            progress_max=1,
            reward={'type': 'currency', 'amount': 200, 'description': '200 Bamboo Bucks'}
        ),
        'night_owl': Achievement(
            id='night_owl',
            name='Night Owl',
            description='Sort textures between 2 AM and 4 AM',
            tier=AchievementTier.BRONZE,
            points=30,
            icon='🦉',
            category='easter_egg',
            hidden=True,
            progress_max=1
        ),
    }
    
    def __init__(self, save_file: Optional[str] = None):
        """
        Initialize achievement system.
        
        Args:
            save_file: Path to achievement save file
        """
        self.achievements: Dict[str, Achievement] = {}
        self.save_file = save_file
        self.lock = threading.RLock()
        
        # Event callbacks
        self.unlock_callbacks: List[Callable[[Achievement], None]] = []
        self.progress_callbacks: List[Callable[[Achievement], None]] = []
        
        # Statistics
        self.total_textures_sorted = 0
        self.total_sessions = 0
        self.total_time_minutes = 0
        
        # Initialize achievements
        self._initialize_achievements()
        
        # Load saved progress
        if save_file:
            self.load_progress(save_file)
    
    def _initialize_achievements(self) -> None:
        """Initialize achievements from definitions."""
        for achievement_id, achievement in self.ACHIEVEMENTS.items():
            # Create a copy so we don't modify the template
            self.achievements[achievement_id] = Achievement(
                id=achievement.id,
                name=achievement.name,
                description=achievement.description,
                tier=achievement.tier,
                points=achievement.points,
                icon=achievement.icon,
                hidden=achievement.hidden,
                category=achievement.category,
                progress_max=achievement.progress_max,
                reward=achievement.reward
            )
    
    def update_progress(
        self,
        achievement_id: str,
        progress: float,
        increment: bool = False
    ) -> bool:
        """
        Update achievement progress.
        
        Args:
            achievement_id: Achievement ID
            progress: Progress value
            increment: Whether to increment or set progress
            
        Returns:
            True if achievement was unlocked
        """
        with self.lock:
            if achievement_id not in self.achievements:
                logger.warning(f"Unknown achievement: {achievement_id}")
                return False
            
            achievement = self.achievements[achievement_id]
            
            # Don't update already unlocked achievements
            if achievement.unlocked:
                return False
            
            # Update progress
            if increment:
                achievement.progress += progress
            else:
                achievement.progress = progress
            
            # Ensure progress doesn't exceed max
            achievement.progress = min(achievement.progress, achievement.progress_max)
            
            # Check if achievement is now unlocked
            if achievement.is_complete() and not achievement.unlocked:
                self._unlock_achievement(achievement_id)
                return True
            
            # Notify progress callbacks
            self._notify_progress(achievement)
            
            return False
    
    def _unlock_achievement(self, achievement_id: str) -> None:
        """
        Unlock an achievement.
        
        Args:
            achievement_id: Achievement ID to unlock
        """
        if achievement_id not in self.achievements:
            return
        
        achievement = self.achievements[achievement_id]
        
        if achievement.unlocked:
            return
        
        achievement.unlocked = True
        achievement.unlock_date = datetime.now().isoformat()
        achievement.progress = achievement.progress_max
        
        logger.info(f"🏆 Achievement unlocked: {achievement.name}")
        
        # Notify callbacks
        self._notify_unlock(achievement)
        
        # Check meta achievements
        self._check_meta_achievements()
        
        # Auto-save progress
        if self.save_file:
            self.save_progress(self.save_file)
    
    def unlock_achievement(self, achievement_id: str) -> bool:
        """
        Manually unlock an achievement.
        
        Args:
            achievement_id: Achievement ID
            
        Returns:
            True if unlocked successfully
        """
        with self.lock:
            if achievement_id not in self.achievements:
                logger.warning(f"Unknown achievement: {achievement_id}")
                return False
            
            achievement = self.achievements[achievement_id]
            
            if achievement.unlocked:
                logger.debug(f"Achievement already unlocked: {achievement_id}")
                return False
            
            self._unlock_achievement(achievement_id)
            return True
    
    def _check_meta_achievements(self) -> None:
        """Check and update meta achievements (achievement hunter, completionist)."""
        unlocked_count = self.get_unlocked_count()
        total_count = len(self.achievements)
        
        if total_count == 0:
            return
        
        unlock_percent = (unlocked_count / total_count) * 100
        
        # Update achievement hunter progress
        if 'achievement_hunter' in self.achievements:
            self.update_progress('achievement_hunter', unlock_percent)
        
        # Update completionist progress
        if 'completionist' in self.achievements:
            self.update_progress('completionist', unlock_percent)
    
    def increment_textures_sorted(self, count: int = 1) -> None:
        """
        Increment total textures sorted and update related achievements.
        
        Args:
            count: Number of textures to add
        """
        self.total_textures_sorted += count
        
        # Update progress achievements
        progress_achievements = [
            'first_sort', 'rookie_sorter', 'apprentice',
            'journeyman', 'master', 'legend'
        ]
        
        for ach_id in progress_achievements:
            if ach_id in self.achievements:
                self.update_progress(ach_id, self.total_textures_sorted)
    
    def increment_session_time(self, minutes: float) -> None:
        """
        Increment total session time.
        
        Args:
            minutes: Minutes to add
        """
        self.total_time_minutes += minutes
        
        # Update marathon achievement with current session time
        if 'marathon' in self.achievements:
            self.update_progress('marathon', minutes, increment=True)
    
    def increment_sessions(self) -> None:
        """Increment total sessions and update related achievements."""
        self.total_sessions += 1
        
        # Update dedicated user achievement
        if 'dedicated' in self.achievements:
            self.update_progress('dedicated', self.total_sessions)
    
    def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """
        Get achievement by ID.
        
        Args:
            achievement_id: Achievement ID
            
        Returns:
            Achievement or None
        """
        return self.achievements.get(achievement_id)
    
    def get_reward(self, achievement_id: str) -> Optional[Dict]:
        """
        Get the reward for an achievement.
        
        Args:
            achievement_id: Achievement ID
            
        Returns:
            Reward dict or None
        """
        achievement = self.achievements.get(achievement_id)
        if achievement and achievement.reward:
            return achievement.reward
        return None
    
    def get_all_achievements(self, include_hidden: bool = False) -> List[Achievement]:
        """
        Get all achievements.
        
        Args:
            include_hidden: Whether to include hidden achievements
            
        Returns:
            List of achievements
        """
        achievements = list(self.achievements.values())
        
        if not include_hidden:
            achievements = [a for a in achievements if not a.hidden or a.unlocked]
        
        return achievements
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """
        Get all unlocked achievements.
        
        Returns:
            List of unlocked achievements
        """
        return [a for a in self.achievements.values() if a.unlocked]
    
    def get_locked_achievements(self) -> List[Achievement]:
        """
        Get all locked achievements.
        
        Returns:
            List of locked achievements
        """
        return [a for a in self.achievements.values() if not a.unlocked]
    
    def get_achievements_by_category(self, category: str) -> List[Achievement]:
        """
        Get achievements in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of achievements
        """
        return [a for a in self.achievements.values() if a.category == category]
    
    def get_achievements_by_tier(self, tier: AchievementTier) -> List[Achievement]:
        """
        Get achievements of a specific tier.
        
        Args:
            tier: Achievement tier
            
        Returns:
            List of achievements
        """
        return [a for a in self.achievements.values() if a.tier == tier]
    
    def get_unlocked_count(self) -> int:
        """Get number of unlocked achievements."""
        return sum(1 for a in self.achievements.values() if a.unlocked)
    
    def get_total_count(self) -> int:
        """Get total number of achievements."""
        return len(self.achievements)
    
    def get_total_points(self) -> int:
        """Get total points earned from unlocked achievements."""
        return sum(a.points for a in self.achievements.values() if a.unlocked)
    
    def get_completion_percent(self) -> float:
        """Get overall achievement completion percentage."""
        total = self.get_total_count()
        if total == 0:
            return 0.0
        return (self.get_unlocked_count() / total) * 100.0
    
    def get_categories(self) -> Set[str]:
        """Get all achievement categories."""
        return {a.category for a in self.achievements.values()}
    
    def register_unlock_callback(self, callback: Callable[[Achievement], None]) -> None:
        """
        Register callback for achievement unlocks.
        
        Args:
            callback: Function to call when achievement is unlocked
        """
        self.unlock_callbacks.append(callback)
    
    def register_progress_callback(self, callback: Callable[[Achievement], None]) -> None:
        """
        Register callback for achievement progress updates.
        
        Args:
            callback: Function to call when achievement progress updates
        """
        self.progress_callbacks.append(callback)
    
    def _notify_unlock(self, achievement: Achievement) -> None:
        """Notify unlock callbacks."""
        for callback in self.unlock_callbacks:
            try:
                callback(achievement)
            except Exception as e:
                logger.error(f"Error in unlock callback: {e}")
    
    def _notify_progress(self, achievement: Achievement) -> None:
        """Notify progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(achievement)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def save_progress(self, save_file: str) -> bool:
        """
        Save achievement progress to file.
        
        Args:
            save_file: Path to save file
            
        Returns:
            True if saved successfully
        """
        try:
            save_data = {
                'version': '1.0',
                'last_saved': datetime.now().isoformat(),
                'statistics': {
                    'total_textures_sorted': self.total_textures_sorted,
                    'total_sessions': self.total_sessions,
                    'total_time_minutes': self.total_time_minutes
                },
                'achievements': {}
            }
            
            # Save achievement data
            for achievement_id, achievement in self.achievements.items():
                save_data['achievements'][achievement_id] = {
                    'unlocked': achievement.unlocked,
                    'unlock_date': achievement.unlock_date,
                    'progress': achievement.progress
                }
            
            # Write to file
            path = Path(save_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2)
            
            logger.info(f"Saved achievement progress to {save_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save achievement progress: {e}")
            return False
    
    def load_progress(self, save_file: str) -> bool:
        """
        Load achievement progress from file.
        
        Args:
            save_file: Path to save file
            
        Returns:
            True if loaded successfully
        """
        try:
            path = Path(save_file)
            
            if not path.exists():
                logger.info(f"No existing save file: {save_file}")
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Load statistics
            stats = save_data.get('statistics', {})
            self.total_textures_sorted = stats.get('total_textures_sorted', 0)
            self.total_sessions = stats.get('total_sessions', 0)
            self.total_time_minutes = stats.get('total_time_minutes', 0)
            
            # Load achievement data
            achievements_data = save_data.get('achievements', {})
            
            for achievement_id, data in achievements_data.items():
                if achievement_id in self.achievements:
                    achievement = self.achievements[achievement_id]
                    achievement.unlocked = data.get('unlocked', False)
                    achievement.unlock_date = data.get('unlock_date')
                    achievement.progress = data.get('progress', 0.0)
            
            logger.info(f"Loaded achievement progress from {save_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load achievement progress: {e}")
            return False
    
    def reset_progress(self) -> None:
        """Reset all achievement progress."""
        with self.lock:
            for achievement in self.achievements.values():
                achievement.unlocked = False
                achievement.unlock_date = None
                achievement.progress = 0.0
            
            self.total_textures_sorted = 0
            self.total_sessions = 0
            self.total_time_minutes = 0
            
            logger.info("Reset all achievement progress")
    
    def get_summary(self) -> Dict:
        """
        Get achievement system summary.
        
        Returns:
            Summary dictionary
        """
        return {
            'total_achievements': self.get_total_count(),
            'unlocked': self.get_unlocked_count(),
            'locked': self.get_total_count() - self.get_unlocked_count(),
            'completion_percent': self.get_completion_percent(),
            'total_points': self.get_total_points(),
            'statistics': {
                'textures_sorted': self.total_textures_sorted,
                'sessions': self.total_sessions,
                'time_minutes': self.total_time_minutes
            }
        }
