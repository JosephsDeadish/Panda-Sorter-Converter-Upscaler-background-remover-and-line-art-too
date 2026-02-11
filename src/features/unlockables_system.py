"""
Unlockables System - Hidden content, achievements, and progression
Manage unlockable cursors, panda outfits, themes, animations, and tooltips
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, time as dt_time
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)


class UnlockConditionType(Enum):
    """Types of unlock conditions."""
    ALWAYS_AVAILABLE = "always_available"
    FILES_PROCESSED = "files_processed"
    PET_COUNT = "pet_count"
    FEED_COUNT = "feed_count"
    TIME_BASED = "time_based"
    DATE_BASED = "date_based"
    SESSION_TIME = "session_time"
    ACHIEVEMENT = "achievement"
    EASTER_EGG = "easter_egg"
    THEME_USAGE = "theme_usage"
    SEARCH_USAGE = "search_usage"
    MILESTONE = "milestone"
    SPECIAL_EVENT = "special_event"
    UNLOCK_COUNT = "unlock_count"


@dataclass
class UnlockCondition:
    """Represents an unlock condition."""
    condition_type: UnlockConditionType
    value: Any
    description: str
    
    def check(self, stats: Dict) -> bool:
        """Check if condition is met."""
        if self.condition_type == UnlockConditionType.ALWAYS_AVAILABLE:
            return True
        elif self.condition_type == UnlockConditionType.FILES_PROCESSED:
            return stats.get('total_files_processed', 0) >= self.value
        elif self.condition_type == UnlockConditionType.PET_COUNT:
            return stats.get('panda_pet_count', 0) >= self.value
        elif self.condition_type == UnlockConditionType.FEED_COUNT:
            return stats.get('panda_feed_count', 0) >= self.value
        elif self.condition_type == UnlockConditionType.TIME_BASED:
            now = datetime.now()
            target_hour = self.value
            return now.hour == target_hour
        elif self.condition_type == UnlockConditionType.DATE_BASED:
            now = datetime.now()
            month, day = self.value
            return now.month == month and now.day == day
        elif self.condition_type == UnlockConditionType.SESSION_TIME:
            return stats.get('session_time_minutes', 0) >= self.value
        elif self.condition_type == UnlockConditionType.ACHIEVEMENT:
            return stats.get('easter_eggs', {}).get(self.value, False)
        elif self.condition_type == UnlockConditionType.THEME_USAGE:
            return stats.get('unique_themes_used', 0) >= self.value
        elif self.condition_type == UnlockConditionType.SEARCH_USAGE:
            return stats.get('search_count', 0) >= self.value
        elif self.condition_type == UnlockConditionType.UNLOCK_COUNT:
            return stats.get('total_unlocks', 0) >= self.value
        elif self.condition_type == UnlockConditionType.EASTER_EGG:
            return stats.get('easter_eggs', {}).get(self.value, False)
        elif self.condition_type == UnlockConditionType.MILESTONE:
            return stats.get('milestones', {}).get(self.value, False)
        return False


@dataclass
class UnlockableCursor:
    """Represents an unlockable cursor."""
    id: str
    name: str
    cursor_type: str  # "standard", "special", "animated"
    description: str
    unlock_condition: UnlockCondition
    unlocked: bool = False
    unlock_date: Optional[str] = None


@dataclass
class PandaOutfit:
    """Represents an unlockable panda outfit."""
    id: str
    name: str
    art: str
    description: str
    unlock_condition: UnlockCondition
    unlocked: bool = False
    unlock_date: Optional[str] = None


@dataclass
class UnlockableTheme:
    """Represents an unlockable UI theme."""
    id: str
    name: str
    colors: Dict[str, str]
    description: str
    unlock_condition: UnlockCondition
    unlocked: bool = False
    unlock_date: Optional[str] = None


@dataclass
class WaveAnimation:
    """Represents a wave/pulse animation pattern."""
    id: str
    name: str
    pattern: str
    description: str
    unlock_condition: UnlockCondition
    unlocked: bool = False
    unlock_date: Optional[str] = None


@dataclass
class TooltipCollection:
    """Represents a collection of tooltips."""
    id: str
    name: str
    tooltips: List[str]
    description: str
    unlock_condition: UnlockCondition
    unlocked: bool = False
    unlock_date: Optional[str] = None


class UnlockablesSystem:
    """
    Manages all unlockable content including cursors, outfits, themes, animations, and tooltips.
    Tracks player stats and automatically unlocks content when conditions are met.
    """
    
    # Default cursors available from the start
    CURSORS: Dict[str, Dict] = {
        # Default cursors (always available)
        "arrow": {
            "name": "Classic Arrow",
            "cursor_type": "standard",
            "description": "The classic arrow cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "hand": {
            "name": "Pointing Hand",
            "cursor_type": "standard",
            "description": "A friendly pointing hand",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "crosshair": {
            "name": "Crosshair",
            "cursor_type": "standard",
            "description": "Precise crosshair cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "text": {
            "name": "Text Cursor",
            "cursor_type": "standard",
            "description": "I-beam text selection cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "wait": {
            "name": "Hourglass",
            "cursor_type": "animated",
            "description": "Patient waiting cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        
        # Unlockable cursors
        "bamboo_stick": {
            "name": "Bamboo Stick",
            "cursor_type": "special",
            "description": "A delicious bamboo stick cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.FEED_COUNT, 10, "Feed the panda 10 times"),
        },
        "golden_paw": {
            "name": "Golden Paw",
            "cursor_type": "special",
            "description": "A prestigious golden paw print",
            "unlock_condition": UnlockCondition(UnlockConditionType.PET_COUNT, 100, "Pet the panda 100 times"),
        },
        "ninja_star": {
            "name": "Ninja Star",
            "cursor_type": "special",
            "description": "Swift and precise ninja star",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 500, "Process 500 files"),
        },
        "laser_pointer": {
            "name": "Laser Pointer",
            "cursor_type": "animated",
            "description": "Red dot that pandas can't resist",
            "unlock_condition": UnlockCondition(UnlockConditionType.PET_COUNT, 50, "Pet the panda 50 times"),
        },
        "magic_wand": {
            "name": "Magic Wand",
            "cursor_type": "animated",
            "description": "Sparkly magical wand cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.EASTER_EGG, "konami_code", "Enter the Konami Code"),
        },
        "dragon": {
            "name": "Dragon",
            "cursor_type": "special",
            "description": "Fierce dragon cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 1000, "Process 1000 files"),
        },
        "rainbow": {
            "name": "Rainbow Trail",
            "cursor_type": "animated",
            "description": "Leaves a colorful rainbow trail",
            "unlock_condition": UnlockCondition(UnlockConditionType.THEME_USAGE, 5, "Use 5 different themes"),
        },
        "fire": {
            "name": "Flame",
            "cursor_type": "animated",
            "description": "Blazing fire cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.SESSION_TIME, 60, "Use app for 60 minutes"),
        },
        "ice": {
            "name": "Ice Crystal",
            "cursor_type": "animated",
            "description": "Frozen crystal cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.TIME_BASED, 0, "Use at midnight"),
        },
        "lightning": {
            "name": "Lightning Bolt",
            "cursor_type": "animated",
            "description": "Electric lightning cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 250, "Process 250 files quickly"),
        },
        "crown": {
            "name": "Royal Crown",
            "cursor_type": "special",
            "description": "Fit for texture royalty",
            "unlock_condition": UnlockCondition(UnlockConditionType.UNLOCK_COUNT, 20, "Unlock 20 items"),
        },
        "ghost": {
            "name": "Spooky Ghost",
            "cursor_type": "animated",
            "description": "Friendly spooky ghost",
            "unlock_condition": UnlockCondition(UnlockConditionType.DATE_BASED, (10, 31), "Use on Halloween"),
        },
        "santa_hat": {
            "name": "Santa Hat",
            "cursor_type": "special",
            "description": "Festive holiday cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.DATE_BASED, (12, 25), "Use on Christmas"),
        },
        "heart": {
            "name": "Love Heart",
            "cursor_type": "animated",
            "description": "Spread the love",
            "unlock_condition": UnlockCondition(UnlockConditionType.PET_COUNT, 200, "Pet the panda 200 times"),
        },
        "diamond": {
            "name": "Diamond",
            "cursor_type": "special",
            "description": "Precious diamond cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 2000, "Process 2000 files"),
        },
        "rocket": {
            "name": "Rocket",
            "cursor_type": "animated",
            "description": "Blast off to texture space",
            "unlock_condition": UnlockCondition(UnlockConditionType.SESSION_TIME, 120, "Use app for 2 hours"),
        },
        "alien": {
            "name": "Alien",
            "cursor_type": "special",
            "description": "Out of this world cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.TIME_BASED, 3, "Use at 3 AM"),
        },
        "cake": {
            "name": "Birthday Cake",
            "cursor_type": "special",
            "description": "Celebrate with cake!",
            "unlock_condition": UnlockCondition(UnlockConditionType.MILESTONE, "first_launch", "Launch the app"),
        },
        "trophy": {
            "name": "Trophy",
            "cursor_type": "special",
            "description": "Champion texture sorter",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 5000, "Process 5000 files"),
        },
        "atom": {
            "name": "Atom",
            "cursor_type": "animated",
            "description": "Atomic precision cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.SEARCH_USAGE, 100, "Perform 100 searches"),
        },
        "butterfly": {
            "name": "Butterfly",
            "cursor_type": "animated",
            "description": "Graceful butterfly cursor",
            "unlock_condition": UnlockCondition(UnlockConditionType.FEED_COUNT, 50, "Feed the panda 50 times"),
        },
        "compass": {
            "name": "Compass",
            "cursor_type": "special",
            "description": "Always points true north",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 100, "Process 100 files"),
        },
        "origami": {
            "name": "Origami Crane",
            "cursor_type": "special",
            "description": "Delicate paper crane",
            "unlock_condition": UnlockCondition(UnlockConditionType.EASTER_EGG, "secret_clicks", "Find the secret"),
        },
    }
    
    OUTFITS: Dict[str, Dict] = {
        "classic": {
            "name": "Classic Panda",
            "art": """
    ʕ•ᴥ•ʔ
  ⊂(◕‿◕)つ
    """,
            "description": "The original adorable panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "business": {
            "name": "Business Panda",
            "art": """
    ʕ•̀ω•́ʔ✧
   ⊂(▀̿Ĺ̯▀̿)つ
    👔
    """,
            "description": "Professional panda with a tie",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 100, "Process 100 files"),
        },
        "ninja": {
            "name": "Ninja Panda",
            "art": """
    ʕ•̫͡•ʔ
   ⊂(▀¯▀)つ刀
    """,
            "description": "Stealthy ninja panda warrior",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 500, "Process 500 files"),
        },
        "wizard": {
            "name": "Wizard Panda",
            "art": """
    🎩ʕ•ᴥ•ʔ
   ⊂(◕‿◕)つ🪄
    """,
            "description": "Magical wizard panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.EASTER_EGG, "konami_code", "Enter the Konami Code"),
        },
        "pirate": {
            "name": "Pirate Panda",
            "art": """
    ʕ•̀ω•́ʔ☠️
   ⊂(◉Д◕)つ🗡️
    """,
            "description": "Arrr! Pirate panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.PET_COUNT, 150, "Pet the panda 150 times"),
        },
        "astronaut": {
            "name": "Astronaut Panda",
            "art": """
   🚀ʕ•ᴥ•ʔ
   ⊂(◕‿◕)つ🌟
    """,
            "description": "Space-exploring panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.SESSION_TIME, 120, "Use app for 2 hours"),
        },
        "chef": {
            "name": "Chef Panda",
            "art": """
   👨‍🍳ʕ•ᴥ•ʔ
   ⊂(◕‿◕)つ🍳
    """,
            "description": "Master chef panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.FEED_COUNT, 75, "Feed the panda 75 times"),
        },
        "superhero": {
            "name": "Super Panda",
            "art": """
   🦸ʕ•̀ω•́ʔ✧
   ⊂(▀̿Ĺ̯▀̿)つ💪
    """,
            "description": "Heroic super panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 1000, "Process 1000 files"),
        },
        "detective": {
            "name": "Detective Panda",
            "art": """
   🕵️ʕ•ᴥ•ʔ
   ⊂(◕‿◕)つ🔍
    """,
            "description": "Investigative detective panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.SEARCH_USAGE, 50, "Perform 50 searches"),
        },
        "rockstar": {
            "name": "Rockstar Panda",
            "art": """
   🎸ʕ•̀ω•́ʔ✧
   ⊂(▀̿Ĺ̯▀̿)つ🎤
    """,
            "description": "Rock and roll panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.THEME_USAGE, 7, "Use 7 different themes"),
        },
        "samurai": {
            "name": "Samurai Panda",
            "art": """
   ⚔️ʕ•̫͡•ʔ
   ⊂(ಠ_ಠ)つ🗡️
    """,
            "description": "Honorable samurai panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 750, "Process 750 files"),
        },
        "king": {
            "name": "King Panda",
            "art": """
   👑ʕ•ᴥ•ʔ
   ⊂(◕‿◕)つ👑
    """,
            "description": "Royal king panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.UNLOCK_COUNT, 15, "Unlock 15 items"),
        },
        "scuba": {
            "name": "Scuba Panda",
            "art": """
   🤿ʕ•ᴥ•ʔ
   ⊂(◕‿◕)つ🐠
    """,
            "description": "Deep diving panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.PET_COUNT, 250, "Pet the panda 250 times"),
        },
        "painter": {
            "name": "Artist Panda",
            "art": """
   🎨ʕ•ᴥ•ʔ
   ⊂(◕‿◕)つ🖌️
    """,
            "description": "Creative artist panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 300, "Process 300 files"),
        },
        "santa": {
            "name": "Santa Panda",
            "art": """
   🎅ʕ•ᴥ•ʔ
   ⊂(◕‿◕)つ🎁
    """,
            "description": "Jolly Santa panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.DATE_BASED, (12, 25), "Use on Christmas"),
        },
        "vampire": {
            "name": "Vampire Panda",
            "art": """
   🧛ʕ•̀ω•́ʔ
   ⊂(▀̿Ĺ̯▀̿)つ🦇
    """,
            "description": "Spooky vampire panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.DATE_BASED, (10, 31), "Use on Halloween"),
        },
        "robot": {
            "name": "Robot Panda",
            "art": """
   🤖ʕ•ᴥ•ʔ
   ⊂(▀̿Ĺ̯▀̿)つ⚙️
    """,
            "description": "Mechanical robot panda",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 2000, "Process 2000 files"),
        },
    }
    
    THEMES: Dict[str, Dict] = {
        "default": {
            "name": "Classic",
            "colors": {
                "primary": "#3498db",
                "secondary": "#2ecc71",
                "background": "#ecf0f1",
                "text": "#2c3e50",
            },
            "description": "The classic theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "dark": {
            "name": "Dark Mode",
            "colors": {
                "primary": "#9b59b6",
                "secondary": "#3498db",
                "background": "#2c3e50",
                "text": "#ecf0f1",
            },
            "description": "Easy on the eyes dark theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "bamboo": {
            "name": "Bamboo Forest",
            "colors": {
                "primary": "#27ae60",
                "secondary": "#16a085",
                "background": "#e8f5e9",
                "text": "#1b5e20",
            },
            "description": "Peaceful bamboo forest theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "sunset": {
            "name": "Sunset",
            "colors": {
                "primary": "#e74c3c",
                "secondary": "#f39c12",
                "background": "#ffe0b2",
                "text": "#bf360c",
            },
            "description": "Beautiful sunset colors",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "ocean": {
            "name": "Ocean Blue",
            "colors": {
                "primary": "#3498db",
                "secondary": "#16a085",
                "background": "#e0f7fa",
                "text": "#006064",
            },
            "description": "Deep ocean theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "cherry_blossom": {
            "name": "Cherry Blossom",
            "colors": {
                "primary": "#e91e63",
                "secondary": "#f06292",
                "background": "#fce4ec",
                "text": "#880e4f",
            },
            "description": "Delicate cherry blossom theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.PET_COUNT, 100, "Pet the panda 100 times"),
        },
        "midnight": {
            "name": "Midnight",
            "colors": {
                "primary": "#673ab7",
                "secondary": "#9c27b0",
                "background": "#1a1a2e",
                "text": "#eee",
            },
            "description": "Dark midnight theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.TIME_BASED, 0, "Use at midnight"),
        },
        "fire": {
            "name": "Fire",
            "colors": {
                "primary": "#ff5722",
                "secondary": "#ff9800",
                "background": "#fff3e0",
                "text": "#bf360c",
            },
            "description": "Hot fire theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 500, "Process 500 files"),
        },
        "ice": {
            "name": "Ice",
            "colors": {
                "primary": "#00bcd4",
                "secondary": "#b2ebf2",
                "background": "#e0f7fa",
                "text": "#006064",
            },
            "description": "Cool ice theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 500, "Process 500 files"),
        },
        "neon": {
            "name": "Neon",
            "colors": {
                "primary": "#ff00ff",
                "secondary": "#00ffff",
                "background": "#0a0a0a",
                "text": "#00ff00",
            },
            "description": "Vibrant neon theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.TIME_BASED, 3, "Use at 3 AM"),
        },
        "gold": {
            "name": "Golden",
            "colors": {
                "primary": "#ffd700",
                "secondary": "#ffeb3b",
                "background": "#fffde7",
                "text": "#f57f17",
            },
            "description": "Luxurious golden theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.UNLOCK_COUNT, 25, "Unlock 25 items"),
        },
        "retro": {
            "name": "Retro",
            "colors": {
                "primary": "#8bc34a",
                "secondary": "#ff9800",
                "background": "#f5f5dc",
                "text": "#5d4037",
            },
            "description": "Nostalgic retro theme",
            "unlock_condition": UnlockCondition(UnlockConditionType.EASTER_EGG, "konami_code", "Enter the Konami Code"),
        },
    }
    
    WAVE_ANIMATIONS: Dict[str, Dict] = {
        "classic": {
            "name": "Classic Wave",
            "pattern": "sine",
            "description": "Smooth sine wave animation",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "bounce": {
            "name": "Bounce",
            "pattern": "bounce",
            "description": "Bouncy animation",
            "unlock_condition": UnlockCondition(UnlockConditionType.PET_COUNT, 25, "Pet the panda 25 times"),
        },
        "pulse": {
            "name": "Pulse",
            "pattern": "pulse",
            "description": "Pulsing animation",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 50, "Process 50 files"),
        },
        "spiral": {
            "name": "Spiral",
            "pattern": "spiral",
            "description": "Spiraling wave animation",
            "unlock_condition": UnlockCondition(UnlockConditionType.SESSION_TIME, 15, "Use app for 15 minutes"),
        },
        "zigzag": {
            "name": "Zigzag",
            "pattern": "zigzag",
            "description": "Sharp zigzag animation",
            "unlock_condition": UnlockCondition(UnlockConditionType.SEARCH_USAGE, 20, "Perform 20 searches"),
        },
        "rainbow": {
            "name": "Rainbow Wave",
            "pattern": "rainbow",
            "description": "Colorful rainbow wave",
            "unlock_condition": UnlockCondition(UnlockConditionType.THEME_USAGE, 3, "Use 3 different themes"),
        },
    }
    
    TOOLTIP_COLLECTIONS: Dict[str, Dict] = {
        "default": {
            "name": "Classic Tips",
            "tooltips": [
                "Click to select a texture",
                "Drag and drop files to import",
                "Use Ctrl+F to search",
                "Double-click to open",
                "Right-click for options",
            ],
            "description": "Standard helpful tooltips",
            "unlock_condition": UnlockCondition(UnlockConditionType.ALWAYS_AVAILABLE, None, "Default"),
        },
        "panda_facts": {
            "name": "Panda Facts",
            "tooltips": [
                "🐼 Pandas spend 12-16 hours a day eating bamboo!",
                "🐼 A baby panda is called a cub and weighs only 100g at birth",
                "🐼 Pandas have a 'thumb' that helps them grip bamboo",
                "🐼 Giant pandas can eat up to 40kg of bamboo daily",
                "🐼 Pandas are excellent climbers and swimmers",
                "🐼 A panda's scientific name is Ailuropoda melanoleuca",
                "🐼 Pandas have been on Earth for 2-3 million years",
                "🐼 A panda's favorite snack is bamboo shoots",
                "🐼 Pandas can live up to 20 years in the wild",
                "🐼 Baby pandas are born pink and blind",
                "🐼 Pandas communicate through vocalizations and scent marking",
                "🐼 A panda's day consists of eating, sleeping, and eating more",
                "🐼 Pandas have a special bone in their wrist that acts like a thumb",
                "🐼 In Chinese, the word for panda means 'bear cat'",
                "🐼 Pandas have a very low metabolism for mammals",
            ],
            "description": "Learn about pandas!",
            "unlock_condition": UnlockCondition(UnlockConditionType.FEED_COUNT, 5, "Feed the panda 5 times"),
        },
        "motivational": {
            "name": "Motivational Quotes",
            "tooltips": [
                "✨ You're doing great!",
                "💪 Keep up the excellent work!",
                "🌟 Texture sorting champion!",
                "🚀 You're on fire!",
                "⭐ Amazing progress!",
                "🎯 Perfect organization!",
                "🏆 You're a texture master!",
                "💫 Incredible job!",
                "🎨 Your textures look fantastic!",
                "👏 Outstanding work!",
                "🌈 Bringing order to chaos!",
                "🔥 Unstoppable sorting power!",
                "💎 Quality work right here!",
                "🎪 The show must go on!",
                "🌻 Beautiful organization!",
            ],
            "description": "Stay motivated!",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 50, "Process 50 files"),
        },
        "gaming": {
            "name": "Gaming References",
            "tooltips": [
                "🎮 Press F to pay respects",
                "🎮 It's dangerous to go alone!",
                "🎮 Would you kindly... sort these textures?",
                "🎮 The cake is a lie, but these textures are real",
                "🎮 War. War never changes. But textures do.",
                "🎮 All your textures are belong to us",
                "🎮 Do a barrel roll!",
                "🎮 Get over here! (to this texture folder)",
                "🎮 FINISH HIM! ...I mean, the sorting",
                "🎮 It's super effective!",
                "🎮 A wild texture appeared!",
                "🎮 Achievement Unlocked: Texture Guru",
                "🎮 +100 Sorting XP",
                "🎮 Level up! You're now a Texture Master",
                "🎮 Save point reached",
                "🎮 Quest Complete: Organize Textures",
                "🎮 Legendary texture found!",
                "🎮 Critical hit on that texture!",
                "🎮 Combo x10! Keep sorting!",
                "🎮 New skill unlocked: Speed Sorting",
            ],
            "description": "For the gamers",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 100, "Process 100 files"),
        },
        "memes": {
            "name": "Meme Culture",
            "tooltips": [
                "😂 This is fine. Everything is fine.",
                "😂 Stonks! Your texture organization is going up!",
                "😂 I can haz texture?",
                "😂 One does not simply... sort all textures in one day",
                "😂 Such wow. Much organize. Very texture.",
                "😂 Y u no sort textures?",
                "😂 Not sure if texture... or just noise",
                "😂 Nobody: ... You: *sorts textures*",
                "😂 Is this a texture?",
                "😂 Textures, textures everywhere",
                "😂 Mom can we have textures? We have textures at home",
                "😂 Always has been 🔫 (a texture sorter)",
                "😂 Reject modernity, embrace texture sorting",
                "😂 I see this as an absolute win!",
                "😂 You get a texture! You get a texture! Everyone gets textures!",
                "😂 Task failed successfully",
                "😂 Suffering from success (too many textures)",
                "😂 Outstanding move!",
                "😂 He's too dangerous to be left alive! (this sorting speed)",
                "😂 This does put a smile on my face",
            ],
            "description": "Dank memes",
            "unlock_condition": UnlockCondition(UnlockConditionType.PET_COUNT, 75, "Pet the panda 75 times"),
        },
        "technical": {
            "name": "Technical Info",
            "tooltips": [
                "💻 PS2 textures use TIM2 format",
                "💻 Texture resolution affects memory usage",
                "💻 Mipmaps improve texture rendering",
                "💻 PS2 GPU supports up to 4096x4096 textures",
                "💻 Texture compression saves VRAM",
                "💻 Alpha channels enable transparency",
                "💻 UV mapping defines texture coordinates",
                "💻 Bilinear filtering smooths textures",
                "💻 Texture atlases reduce draw calls",
                "💻 Normal maps add surface detail",
                "💻 DXT compression is GPU-friendly",
                "💻 Texture streaming optimizes loading",
                "💻 LOD textures improve performance",
                "💻 Anisotropic filtering sharpens textures",
                "💻 Color palettes reduce texture size",
            ],
            "description": "Learn the tech",
            "unlock_condition": UnlockCondition(UnlockConditionType.FILES_PROCESSED, 200, "Process 200 files"),
        },
        "jokes": {
            "name": "Dad Jokes",
            "tooltips": [
                "😄 Why don't textures ever get lost? They always follow the map!",
                "😄 What's a texture's favorite music? Heavy metal... oxide!",
                "😄 Why did the texture go to school? To get more resolution!",
                "😄 What do you call a texture that tells jokes? A comic relief map!",
                "😄 Why was the texture tired? Too many render passes!",
                "😄 What's a texture's favorite drink? Filtered water!",
                "😄 How do textures stay in shape? They do UV mapping exercises!",
                "😄 Why did the texture blush? It saw the shader code!",
                "😄 What's a texture's favorite sport? Wrapping!",
                "😄 Why don't textures make good comedians? Their jokes are too flat!",
                "😄 What do you call a fancy texture? High-resolution!",
                "😄 Why did the texture go to therapy? It had too many issues!",
                "😄 What's a texture's favorite movie? The Matrix (transformations)!",
                "😄 Why was the texture cold? It lost its warm colors!",
                "😄 What do textures eat for breakfast? Pixel flakes!",
            ],
            "description": "Groan-worthy jokes",
            "unlock_condition": UnlockCondition(UnlockConditionType.SESSION_TIME, 45, "Use app for 45 minutes"),
        },
        "wisdom": {
            "name": "Ancient Wisdom",
            "tooltips": [
                "🎎 A journey of a thousand textures begins with a single sort",
                "🎎 The texture that burns twice as bright lasts half as long",
                "🎎 When the student is ready, the texture appears",
                "🎎 The texture is mightier than the sword",
                "🎎 Fortune favors the organized",
                "🎎 A sorted texture is worth two in the cache",
                "🎎 Patience, young texture sorter",
                "🎎 With great textures comes great responsibility",
                "🎎 The best time to sort textures was yesterday. The second best is now.",
                "🎎 A wise person once said: 'Sort your textures'",
                "🎎 In texture sorting, balance must be found",
                "🎎 The path to mastery is paved with organized folders",
                "🎎 He who sorts textures with joy finds enlightenment",
                "🎎 A cluttered folder is a cluttered mind",
                "🎎 The texture finds those who seek it",
            ],
            "description": "Words of wisdom",
            "unlock_condition": UnlockCondition(UnlockConditionType.UNLOCK_COUNT, 10, "Unlock 10 items"),
        },
    }
    
    def __init__(self, save_dir: Optional[Path] = None):
        """
        Initialize the unlockables system.
        
        Args:
            save_dir: Directory to save/load progress from
        """
        self.save_dir = save_dir or Path.home() / ".ps2_texture_sorter"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.save_file = self.save_dir / "unlockables.json"
        
        # Initialize collections
        self.cursors: Dict[str, UnlockableCursor] = {}
        self.outfits: Dict[str, PandaOutfit] = {}
        self.themes: Dict[str, UnlockableTheme] = {}
        self.animations: Dict[str, WaveAnimation] = {}
        self.tooltip_collections: Dict[str, TooltipCollection] = {}
        
        # Stats tracking
        self.stats: Dict = {
            'total_files_processed': 0,
            'panda_pet_count': 0,
            'panda_feed_count': 0,
            'session_time_minutes': 0,
            'unique_themes_used': 0,
            'search_count': 0,
            'total_unlocks': 0,
            'easter_eggs': {},
            'milestones': {},
        }
        
        # Callbacks for when items unlock
        self.unlock_callbacks: List[Callable] = []
        
        # Session tracking
        self.session_start_time = time.time()
        self._session_timer_running = False
        
        # Initialize all unlockables
        self._initialize_unlockables()
        
        # Load saved progress
        self.load_progress()
        
        logger.info("Unlockables system initialized")
    
    def _initialize_unlockables(self):
        """Initialize all unlockable items from class definitions."""
        # Initialize cursors
        for cursor_id, data in self.CURSORS.items():
            self.cursors[cursor_id] = UnlockableCursor(
                id=cursor_id,
                name=data["name"],
                cursor_type=data["cursor_type"],
                description=data["description"],
                unlock_condition=data["unlock_condition"],
            )
        
        # Initialize outfits
        for outfit_id, data in self.OUTFITS.items():
            self.outfits[outfit_id] = PandaOutfit(
                id=outfit_id,
                name=data["name"],
                art=data["art"],
                description=data["description"],
                unlock_condition=data["unlock_condition"],
            )
        
        # Initialize themes
        for theme_id, data in self.THEMES.items():
            self.themes[theme_id] = UnlockableTheme(
                id=theme_id,
                name=data["name"],
                colors=data["colors"],
                description=data["description"],
                unlock_condition=data["unlock_condition"],
            )
        
        # Initialize animations
        for anim_id, data in self.WAVE_ANIMATIONS.items():
            self.animations[anim_id] = WaveAnimation(
                id=anim_id,
                name=data["name"],
                pattern=data["pattern"],
                description=data["description"],
                unlock_condition=data["unlock_condition"],
            )
        
        # Initialize tooltip collections
        for coll_id, data in self.TOOLTIP_COLLECTIONS.items():
            self.tooltip_collections[coll_id] = TooltipCollection(
                id=coll_id,
                name=data["name"],
                tooltips=data["tooltips"],
                description=data["description"],
                unlock_condition=data["unlock_condition"],
            )
        
        logger.info(f"Initialized {len(self.cursors)} cursors, {len(self.outfits)} outfits, "
                   f"{len(self.themes)} themes, {len(self.animations)} animations, "
                   f"{len(self.tooltip_collections)} tooltip collections")
    
    def update_stat(self, stat_name: str, increment: int = 1):
        """
        Update a stat and check for unlocks.
        
        Args:
            stat_name: Name of the stat to update
            increment: Amount to increment by (default 1)
        """
        if stat_name in self.stats:
            self.stats[stat_name] += increment
        else:
            self.stats[stat_name] = increment
        
        self._check_all_unlocks()
        logger.debug(f"Updated stat '{stat_name}' to {self.stats.get(stat_name)}")
    
    def set_easter_egg(self, egg_name: str, found: bool = True):
        """
        Mark an easter egg as found.
        
        Args:
            egg_name: Name of the easter egg
            found: Whether it was found (default True)
        """
        self.stats['easter_eggs'][egg_name] = found
        self._check_all_unlocks()
        logger.info(f"Easter egg '{egg_name}' marked as found")
    
    def set_milestone(self, milestone_name: str, achieved: bool = True):
        """
        Mark a milestone as achieved.
        
        Args:
            milestone_name: Name of the milestone
            achieved: Whether it was achieved (default True)
        """
        self.stats['milestones'][milestone_name] = achieved
        self._check_all_unlocks()
        logger.info(f"Milestone '{milestone_name}' achieved")
    
    def _check_all_unlocks(self):
        """Check all unlock conditions and unlock eligible items."""
        newly_unlocked = []
        
        # Check cursors
        for cursor in self.cursors.values():
            if not cursor.unlocked and cursor.unlock_condition.check(self.stats):
                cursor.unlocked = True
                cursor.unlock_date = datetime.now().isoformat()
                self.stats['total_unlocks'] += 1
                newly_unlocked.append(('cursor', cursor.name))
                logger.info(f"Unlocked cursor: {cursor.name}")
        
        # Check outfits
        for outfit in self.outfits.values():
            if not outfit.unlocked and outfit.unlock_condition.check(self.stats):
                outfit.unlocked = True
                outfit.unlock_date = datetime.now().isoformat()
                self.stats['total_unlocks'] += 1
                newly_unlocked.append(('outfit', outfit.name))
                logger.info(f"Unlocked outfit: {outfit.name}")
        
        # Check themes
        for theme in self.themes.values():
            if not theme.unlocked and theme.unlock_condition.check(self.stats):
                theme.unlocked = True
                theme.unlock_date = datetime.now().isoformat()
                self.stats['total_unlocks'] += 1
                newly_unlocked.append(('theme', theme.name))
                logger.info(f"Unlocked theme: {theme.name}")
        
        # Check animations
        for animation in self.animations.values():
            if not animation.unlocked and animation.unlock_condition.check(self.stats):
                animation.unlocked = True
                animation.unlock_date = datetime.now().isoformat()
                self.stats['total_unlocks'] += 1
                newly_unlocked.append(('animation', animation.name))
                logger.info(f"Unlocked animation: {animation.name}")
        
        # Check tooltip collections
        for collection in self.tooltip_collections.values():
            if not collection.unlocked and collection.unlock_condition.check(self.stats):
                collection.unlocked = True
                collection.unlock_date = datetime.now().isoformat()
                self.stats['total_unlocks'] += 1
                newly_unlocked.append(('tooltip_collection', collection.name))
                logger.info(f"Unlocked tooltip collection: {collection.name}")
        
        # Notify about new unlocks
        for unlock_type, unlock_name in newly_unlocked:
            self._notify_unlock(unlock_type, unlock_name)
    
    def register_unlock_callback(self, callback: Callable):
        """
        Register a callback to be called when items are unlocked.
        
        Args:
            callback: Function to call with (unlock_type, unlock_name) args
        """
        self.unlock_callbacks.append(callback)
        logger.debug(f"Registered unlock callback: {callback.__name__}")
    
    def _notify_unlock(self, unlock_type: str, unlock_name: str):
        """
        Notify all registered callbacks about an unlock.
        
        Args:
            unlock_type: Type of item unlocked
            unlock_name: Name of item unlocked
        """
        for callback in self.unlock_callbacks:
            try:
                callback(unlock_type, unlock_name)
            except Exception as e:
                logger.error(f"Error in unlock callback: {e}")
    
    def get_unlocked_cursors(self) -> List[UnlockableCursor]:
        """Get list of unlocked cursors."""
        return [c for c in self.cursors.values() if c.unlocked]
    
    def get_unlocked_outfits(self) -> List[PandaOutfit]:
        """Get list of unlocked outfits."""
        return [o for o in self.outfits.values() if o.unlocked]
    
    def get_unlocked_themes(self) -> List[UnlockableTheme]:
        """Get list of unlocked themes."""
        return [t for t in self.themes.values() if t.unlocked]
    
    def get_unlocked_animations(self) -> List[WaveAnimation]:
        """Get list of unlocked animations."""
        return [a for a in self.animations.values() if a.unlocked]
    
    def get_unlocked_tooltip_collections(self) -> List[TooltipCollection]:
        """Get list of unlocked tooltip collections."""
        return [tc for tc in self.tooltip_collections.values() if tc.unlocked]
    
    def get_random_tooltip(self) -> str:
        """
        Get a random tooltip from unlocked collections.
        
        Returns:
            Random tooltip string
        """
        unlocked_collections = self.get_unlocked_tooltip_collections()
        if not unlocked_collections:
            return "Sort textures like a pro!"
        
        collection = random.choice(unlocked_collections)
        return random.choice(collection.tooltips)
    
    def get_completion_percentage(self) -> Dict[str, float]:
        """
        Calculate completion percentage for each category.
        
        Returns:
            Dict with completion percentages
        """
        def calc_percentage(unlocked_count: int, total_count: int) -> float:
            return (unlocked_count / total_count * 100) if total_count > 0 else 0
        
        unlocked_cursors = len([c for c in self.cursors.values() if c.unlocked])
        unlocked_outfits = len([o for o in self.outfits.values() if o.unlocked])
        unlocked_themes = len([t for t in self.themes.values() if t.unlocked])
        unlocked_animations = len([a for a in self.animations.values() if a.unlocked])
        unlocked_tooltips = len([tc for tc in self.tooltip_collections.values() if tc.unlocked])
        
        total_unlocked = (unlocked_cursors + unlocked_outfits + unlocked_themes + 
                         unlocked_animations + unlocked_tooltips)
        total_items = (len(self.cursors) + len(self.outfits) + len(self.themes) + 
                      len(self.animations) + len(self.tooltip_collections))
        
        return {
            'cursors': calc_percentage(unlocked_cursors, len(self.cursors)),
            'outfits': calc_percentage(unlocked_outfits, len(self.outfits)),
            'themes': calc_percentage(unlocked_themes, len(self.themes)),
            'animations': calc_percentage(unlocked_animations, len(self.animations)),
            'tooltip_collections': calc_percentage(unlocked_tooltips, len(self.tooltip_collections)),
            'overall': calc_percentage(total_unlocked, total_items),
        }
    
    def save_progress(self):
        """Save unlockables progress to disk."""
        try:
            # Only save unlock state, not full objects
            data = {
                'stats': self.stats,
                'cursors': {k: {'unlocked': v.unlocked, 'unlock_date': v.unlock_date} 
                           for k, v in self.cursors.items()},
                'outfits': {k: {'unlocked': v.unlocked, 'unlock_date': v.unlock_date}
                           for k, v in self.outfits.items()},
                'themes': {k: {'unlocked': v.unlocked, 'unlock_date': v.unlock_date}
                          for k, v in self.themes.items()},
                'animations': {k: {'unlocked': v.unlocked, 'unlock_date': v.unlock_date}
                              for k, v in self.animations.items()},
                'tooltip_collections': {k: {'unlocked': v.unlocked, 'unlock_date': v.unlock_date}
                                       for k, v in self.tooltip_collections.items()},
            }
            
            with open(self.save_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved unlockables progress to {self.save_file}")
        except Exception as e:
            logger.error(f"Failed to save unlockables progress: {e}")
    
    def load_progress(self):
        """Load unlockables progress from disk."""
        if not self.save_file.exists():
            logger.info("No saved progress found, starting fresh")
            return
        
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
            
            # Load stats
            self.stats.update(data.get('stats', {}))
            
            # Load cursor unlock states
            for cursor_id, cursor_data in data.get('cursors', {}).items():
                if cursor_id in self.cursors:
                    self.cursors[cursor_id].unlocked = cursor_data.get('unlocked', False)
                    self.cursors[cursor_id].unlock_date = cursor_data.get('unlock_date')
            
            # Load outfit unlock states
            for outfit_id, outfit_data in data.get('outfits', {}).items():
                if outfit_id in self.outfits:
                    self.outfits[outfit_id].unlocked = outfit_data.get('unlocked', False)
                    self.outfits[outfit_id].unlock_date = outfit_data.get('unlock_date')
            
            # Load theme unlock states
            for theme_id, theme_data in data.get('themes', {}).items():
                if theme_id in self.themes:
                    self.themes[theme_id].unlocked = theme_data.get('unlocked', False)
                    self.themes[theme_id].unlock_date = theme_data.get('unlock_date')
            
            # Load animation unlock states
            for anim_id, anim_data in data.get('animations', {}).items():
                if anim_id in self.animations:
                    self.animations[anim_id].unlocked = anim_data.get('unlocked', False)
                    self.animations[anim_id].unlock_date = anim_data.get('unlock_date')
            
            # Load tooltip collection unlock states
            for coll_id, coll_data in data.get('tooltip_collections', {}).items():
                if coll_id in self.tooltip_collections:
                    self.tooltip_collections[coll_id].unlocked = coll_data.get('unlocked', False)
                    self.tooltip_collections[coll_id].unlock_date = coll_data.get('unlock_date')
            
            logger.info(f"Loaded unlockables progress from {self.save_file}")
        except Exception as e:
            logger.error(f"Failed to load unlockables progress: {e}")
    
    def get_summary(self) -> Dict:
        """
        Get a summary of current unlockables status.
        
        Returns:
            Dict with summary information
        """
        completion = self.get_completion_percentage()
        
        return {
            'total_unlocks': self.stats.get('total_unlocks', 0),
            'completion_percentage': completion,
            'stats': self.stats.copy(),
            'unlocked_counts': {
                'cursors': len(self.get_unlocked_cursors()),
                'outfits': len(self.get_unlocked_outfits()),
                'themes': len(self.get_unlocked_themes()),
                'animations': len(self.get_unlocked_animations()),
                'tooltip_collections': len(self.get_unlocked_tooltip_collections()),
            },
            'total_counts': {
                'cursors': len(self.cursors),
                'outfits': len(self.outfits),
                'themes': len(self.themes),
                'animations': len(self.animations),
                'tooltip_collections': len(self.tooltip_collections),
            },
        }
