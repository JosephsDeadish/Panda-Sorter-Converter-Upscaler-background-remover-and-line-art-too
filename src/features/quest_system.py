"""
Mini Quest and Achievement System for Interactive Panda

Provides quests, achievements, and rewards for the panda companion.
Adds engagement, replayability, and Easter eggs to the experience.

Quest Types:
    - Find items (food, toys) in workspace
    - Interact with specific widgets
    - Complete certain actions
    - Time-based challenges

Features:
    - Quest definitions and tracking
    - Progress monitoring
    - Achievement system
    - Reward tooltips
    - Easter eggs
    - Persistent progress (optional)
"""

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QPoint
    from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect
    from PyQt6.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QObject = object

import random
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any


class QuestType(Enum):
    """Types of quests."""
    FIND_ITEM = "find_item"
    INTERACT_WIDGET = "interact_widget"
    INTERACT_COUNT = "interact_count"
    TIME_BASED = "time_based"
    EXPLORATION = "exploration"
    EASTER_EGG = "easter_egg"


class QuestStatus(Enum):
    """Quest status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Quest:
    """Quest definition."""
    id: str
    name: str
    description: str
    quest_type: QuestType
    goal_value: int
    current_progress: int = 0
    status: QuestStatus = QuestStatus.NOT_STARTED
    reward_message: str = "Quest complete!"
    easter_egg_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Achievement:
    """Achievement definition."""
    id: str
    name: str
    description: str
    unlocked: bool = False
    unlock_time: float = 0.0
    icon_emoji: str = "🏆"


class QuestSystem(QObject if PYQT_AVAILABLE else object):
    """
    Quest and achievement system for panda companion.
    
    This system:
    - Defines and tracks quests
    - Monitors achievement progress
    - Provides rewards and Easter eggs
    - Shows tooltips for completions
    - Adds engagement and replayability
    """
    
    # Signals
    quest_started = pyqtSignal(str) if PYQT_AVAILABLE else None
    quest_progress = pyqtSignal(str, int, int) if PYQT_AVAILABLE else None  # quest_id, current, goal
    quest_completed = pyqtSignal(str, str) if PYQT_AVAILABLE else None  # quest_id, reward
    achievement_unlocked = pyqtSignal(str) if PYQT_AVAILABLE else None
    easter_egg_found = pyqtSignal(str) if PYQT_AVAILABLE else None
    
    def __init__(self, main_window=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 required for QuestSystem")
        
        super().__init__()
        
        self.main_window = main_window
        
        # Quest and achievement storage
        self.quests: Dict[str, Quest] = {}
        self.achievements: Dict[str, Achievement] = {}
        self.active_quests: List[str] = []
        
        # Easter eggs
        self.easter_eggs_found: List[str] = []
        
        # Statistics
        self.total_interactions = 0
        self.widgets_interacted = set()
        self.time_played = 0.0
        self.start_time = time.time()
        
        # Initialize default quests
        self._create_default_quests()
        
        # Initialize default achievements
        self._create_default_achievements()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_quests)
        self.update_timer.start(1000)  # Update every second
    
    def _create_default_quests(self):
        """Create default quest definitions."""
        quests = [
            Quest(
                id="first_interaction",
                name="First Friend",
                description="Interact with panda for the first time",
                quest_type=QuestType.INTERACT_COUNT,
                goal_value=1,
                reward_message="Panda is now your friend! 🐼",
            ),
            Quest(
                id="button_biter",
                name="Button Biter",
                description="Watch panda bite 5 buttons",
                quest_type=QuestType.INTERACT_COUNT,
                goal_value=5,
                reward_message="Panda loves buttons! 🔘",
            ),
            Quest(
                id="tab_switcher",
                name="Tab Switcher",
                description="Let panda switch tabs 3 times",
                quest_type=QuestType.INTERACT_COUNT,
                goal_value=3,
                reward_message="Panda is a navigation expert! 📑",
            ),
            Quest(
                id="slider_tapper",
                name="Slider Tapper",
                description="Watch panda tap sliders 10 times",
                quest_type=QuestType.INTERACT_COUNT,
                goal_value=10,
                reward_message="Panda loves playing with sliders! 🎚️",
            ),
            Quest(
                id="explorer",
                name="Explorer",
                description="Let panda explore for 5 minutes",
                quest_type=QuestType.TIME_BASED,
                goal_value=300,  # 5 minutes in seconds
                reward_message="Panda knows the workspace now! 🗺️",
            ),
            Quest(
                id="food_finder",
                name="Food Finder",
                description="Find 3 hidden food items",
                quest_type=QuestType.FIND_ITEM,
                goal_value=3,
                reward_message="Panda found all the snacks! 🍜",
                metadata={'item_type': 'food'}
            ),
            Quest(
                id="toy_collector",
                name="Toy Collector",
                description="Collect 5 toys for panda",
                quest_type=QuestType.FIND_ITEM,
                goal_value=5,
                reward_message="Panda has a toy collection! 🧸",
                metadata={'item_type': 'toy'}
            ),
            Quest(
                id="easter_egg_hunter",
                name="Easter Egg Hunter",
                description="Find the hidden Easter egg",
                quest_type=QuestType.EASTER_EGG,
                goal_value=1,
                reward_message="You found the secret! 🥚",
                easter_egg_message="Konami Code activated! Up, Up, Down, Down, Left, Right, Left, Right, B, A"
            ),
            Quest(
                id="persistent_friend",
                name="Persistent Friend",
                description="Use the app for 30 minutes total",
                quest_type=QuestType.TIME_BASED,
                goal_value=1800,  # 30 minutes
                reward_message="Panda really enjoys your company! ❤️",
            ),
            Quest(
                id="widget_master",
                name="Widget Master",
                description="Interact with 10 different widget types",
                quest_type=QuestType.EXPLORATION,
                goal_value=10,
                reward_message="You've mastered the UI with panda! 🎯",
            ),
        ]
        
        for quest in quests:
            self.quests[quest.id] = quest
    
    def _create_default_achievements(self):
        """Create default achievement definitions."""
        achievements = [
            Achievement(
                id="panda_friend",
                name="Panda's Friend",
                description="Complete your first quest",
                icon_emoji="🤝"
            ),
            Achievement(
                id="quest_master",
                name="Quest Master",
                description="Complete 5 quests",
                icon_emoji="🏆"
            ),
            Achievement(
                id="completionist",
                name="Completionist",
                description="Complete all quests",
                icon_emoji="⭐"
            ),
            Achievement(
                id="secret_finder",
                name="Secret Finder",
                description="Find an Easter egg",
                icon_emoji="🥚"
            ),
            Achievement(
                id="dedicated_user",
                name="Dedicated User",
                description="Use app for 1 hour total",
                icon_emoji="⏰"
            ),
        ]
        
        for achievement in achievements:
            self.achievements[achievement.id] = achievement
    
    def start_quest(self, quest_id):
        """
        Start a quest.
        
        Args:
            quest_id: Quest ID to start
        """
        if quest_id in self.quests:
            quest = self.quests[quest_id]
            if quest.status == QuestStatus.NOT_STARTED:
                quest.status = QuestStatus.IN_PROGRESS
                self.active_quests.append(quest_id)
                
                if self.quest_started:
                    self.quest_started.emit(quest_id)
                
                print(f"Quest started: {quest.name}")
    
    def update_quest_progress(self, quest_id, amount=1):
        """
        Update quest progress.
        
        Args:
            quest_id: Quest ID to update
            amount: Amount to increment progress
        """
        if quest_id in self.quests:
            quest = self.quests[quest_id]
            
            if quest.status != QuestStatus.IN_PROGRESS:
                return
            
            quest.current_progress += amount
            
            if self.quest_progress:
                self.quest_progress.emit(quest_id, quest.current_progress, quest.goal_value)
            
            # Check if quest completed
            if quest.current_progress >= quest.goal_value:
                self._complete_quest(quest_id)
    
    def _complete_quest(self, quest_id):
        """Complete a quest."""
        if quest_id in self.quests:
            quest = self.quests[quest_id]
            quest.status = QuestStatus.COMPLETED
            
            if quest_id in self.active_quests:
                self.active_quests.remove(quest_id)
            
            # Emit completion signal
            if self.quest_completed:
                self.quest_completed.emit(quest_id, quest.reward_message)
            
            # Show reward tooltip
            self._show_reward_tooltip(quest.reward_message)
            
            # Check for Easter egg
            if quest.easter_egg_message:
                self._show_easter_egg(quest.easter_egg_message)
            
            # Check achievements
            self._check_achievements()
            
            print(f"Quest completed: {quest.name} - {quest.reward_message}")
    
    def on_widget_interaction(self, widget_type, widget_name):
        """
        Handle widget interaction for quest tracking.
        
        Args:
            widget_type: Type of widget (button, slider, etc.)
            widget_name: Name/text of widget
        """
        self.total_interactions += 1
        self.widgets_interacted.add(widget_type)
        
        # Update quest progress
        if widget_type == 'button':
            self.update_quest_progress('button_biter')
        elif widget_type == 'tab':
            self.update_quest_progress('tab_switcher')
        elif widget_type == 'slider':
            self.update_quest_progress('slider_tapper')
        
        # First interaction quest
        if self.total_interactions == 1:
            self.start_quest('first_interaction')
            self.update_quest_progress('first_interaction')
        
        # Widget master quest
        if len(self.widgets_interacted) > 0:
            quest = self.quests.get('widget_master')
            if quest and quest.status == QuestStatus.NOT_STARTED:
                self.start_quest('widget_master')
            self.update_quest_progress('widget_master', 0)  # Update to current count
            quest.current_progress = len(self.widgets_interacted)
    
    def find_item(self, item_type, item_name):
        """
        Handle item found.
        
        Args:
            item_type: Type of item (food, toy, etc.)
            item_name: Name of item
        """
        print(f"Panda found: {item_name} ({item_type})")
        
        # Update relevant quests
        if item_type == 'food':
            quest = self.quests.get('food_finder')
            if quest and quest.status == QuestStatus.NOT_STARTED:
                self.start_quest('food_finder')
            self.update_quest_progress('food_finder')
        
        elif item_type == 'toy':
            quest = self.quests.get('toy_collector')
            if quest and quest.status == QuestStatus.NOT_STARTED:
                self.start_quest('toy_collector')
            self.update_quest_progress('toy_collector')
    
    def trigger_easter_egg(self, egg_id):
        """
        Trigger an Easter egg.
        
        Args:
            egg_id: Easter egg identifier
        """
        if egg_id not in self.easter_eggs_found:
            self.easter_eggs_found.append(egg_id)
            
            quest = self.quests.get('easter_egg_hunter')
            if quest:
                if quest.status == QuestStatus.NOT_STARTED:
                    self.start_quest('easter_egg_hunter')
                self._complete_quest('easter_egg_hunter')
            
            if self.easter_egg_found:
                self.easter_egg_found.emit(egg_id)
    
    def _update_quests(self):
        """Periodic quest update (for time-based quests)."""
        self.time_played = time.time() - self.start_time
        
        # Update explorer quest
        explorer = self.quests.get('explorer')
        if explorer and explorer.status == QuestStatus.NOT_STARTED and self.time_played > 10:
            self.start_quest('explorer')
        if explorer and explorer.status == QuestStatus.IN_PROGRESS:
            explorer.current_progress = int(self.time_played)
            if explorer.current_progress >= explorer.goal_value:
                self._complete_quest('explorer')
        
        # Update persistent friend quest
        persistent = self.quests.get('persistent_friend')
        if persistent and persistent.status == QuestStatus.NOT_STARTED and self.time_played > 60:
            self.start_quest('persistent_friend')
        if persistent and persistent.status == QuestStatus.IN_PROGRESS:
            persistent.current_progress = int(self.time_played)
            if persistent.current_progress >= persistent.goal_value:
                self._complete_quest('persistent_friend')
    
    def _check_achievements(self):
        """Check and unlock achievements."""
        # Count completed quests
        completed_count = sum(1 for q in self.quests.values() if q.status == QuestStatus.COMPLETED)
        
        # First quest achievement
        if completed_count >= 1:
            self._unlock_achievement('panda_friend')
        
        # Quest master
        if completed_count >= 5:
            self._unlock_achievement('quest_master')
        
        # Completionist
        if completed_count == len(self.quests):
            self._unlock_achievement('completionist')
        
        # Secret finder
        if len(self.easter_eggs_found) > 0:
            self._unlock_achievement('secret_finder')
        
        # Dedicated user
        if self.time_played >= 3600:  # 1 hour
            self._unlock_achievement('dedicated_user')
    
    def _unlock_achievement(self, achievement_id):
        """Unlock an achievement."""
        if achievement_id in self.achievements:
            achievement = self.achievements[achievement_id]
            
            if not achievement.unlocked:
                achievement.unlocked = True
                achievement.unlock_time = time.time()
                
                if self.achievement_unlocked:
                    self.achievement_unlocked.emit(achievement_id)
                
                # Show achievement tooltip
                message = f"{achievement.icon_emoji} {achievement.name}\n{achievement.description}"
                self._show_reward_tooltip(message)
                
                print(f"Achievement unlocked: {achievement.name}")
    
    def _show_reward_tooltip(self, message):
        """Show reward tooltip on screen."""
        if not self.main_window:
            return
        
        # Create tooltip label
        tooltip = QLabel(message, self.main_window)
        tooltip.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 2px solid gold;
                border-radius: 10px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        tooltip.setFont(QFont("Arial", 14))
        tooltip.adjustSize()
        
        # Position at top center
        x = (self.main_window.width() - tooltip.width()) // 2
        y = 50
        tooltip.move(x, y)
        
        # Fade effect
        effect = QGraphicsOpacityEffect()
        tooltip.setGraphicsEffect(effect)
        tooltip.show()
        
        # Auto-hide after 3 seconds
        QTimer.singleShot(3000, tooltip.deleteLater)
    
    def _show_easter_egg(self, message):
        """Show Easter egg message."""
        if self.main_window:
            self._show_reward_tooltip(f"🥚 Easter Egg!\n{message}")
    
    def get_active_quests(self):
        """Get list of active quests."""
        return [self.quests[qid] for qid in self.active_quests]
    
    def get_completed_quests(self):
        """Get list of completed quests."""
        return [q for q in self.quests.values() if q.status == QuestStatus.COMPLETED]
    
    def get_achievements(self):
        """Get all achievements."""
        return list(self.achievements.values())
    
    def get_unlocked_achievements(self):
        """Get unlocked achievements."""
        return [a for a in self.achievements.values() if a.unlocked]
    
    def get_statistics(self):
        """Get quest system statistics."""
        return {
            'total_interactions': self.total_interactions,
            'unique_widgets': len(self.widgets_interacted),
            'time_played': self.time_played,
            'completed_quests': len(self.get_completed_quests()),
            'total_quests': len(self.quests),
            'unlocked_achievements': len(self.get_unlocked_achievements()),
            'total_achievements': len(self.achievements),
            'easter_eggs_found': len(self.easter_eggs_found),
        }


# Convenience function
def create_quest_system(main_window=None):
    """
    Create a quest system.
    
    Args:
        main_window: Optional main window for tooltips
        
    Returns:
        QuestSystem instance or None
    """
    if not PYQT_AVAILABLE:
        print("Warning: PyQt6 not available, cannot create quest system")
        return None
    
    return QuestSystem(main_window)
