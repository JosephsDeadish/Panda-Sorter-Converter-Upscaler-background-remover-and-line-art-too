"""
Panda Character - Always-present animated panda companion
Manages panda moods, animations, interactions, and easter eggs
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
from typing import List, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class PandaMood(Enum):
    """Panda mood states."""
    HAPPY = "happy"
    EXCITED = "excited"
    WORKING = "working"
    TIRED = "tired"
    CELEBRATING = "celebrating"
    SLEEPING = "sleeping"
    SARCASTIC = "sarcastic"
    RAGE = "rage"
    DRUNK = "drunk"
    EXISTENTIAL = "existential"
    MOTIVATING = "motivating"
    TECH_SUPPORT = "tech_support"
    SLEEPY = "sleepy"


@dataclass
class PandaAnimation:
    """Represents a panda animation frame sequence."""
    name: str
    frames: List[str]
    duration_ms: int = 200
    loop: bool = False


class PandaCharacter:
    """Manages the panda companion character - always present."""
    
    # Configuration constants
    RAGE_CLICK_THRESHOLD = 10  # Number of clicks to trigger rage mode
    
    # ASCII art animations for different states
    ANIMATIONS = {
        'idle': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　●　　● |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'working': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  💼
   /　●　　● |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'celebrating': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  🎉
   /　^　　^ |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'rage': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  💢
   /　►　　► |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'sarcastic': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  🙄
   /　-　　- |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'drunk': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  🍺
   /　x　　x |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'playing': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  🎾
   /　◕　　◕ |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'eating': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  🎋
   /　●　　● |
  |　  ( _🍃_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'customizing': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  ✨
   /　★　　★ |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'sleeping': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  💤
   /　-　　- |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'gaming': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  🎮
   /　●　　● |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
        'thinking': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ  💭
   /　●　　● |
  |　　　( _●_) ミ
  彡､　　　|∪| ､｀＼
 /　＿＿ ヽノ /´>　)
            """,
        ],
    }
    
    # Panda click responses
    CLICK_RESPONSES = [
        "🐼 Hi there!",
        "🐼 Need something?",
        "🐼 *happy panda noises*",
        "🐼 Ready to work!",
        "🐼 At your service!",
        "🐼 Panda reporting for duty!",
        "🐼 What's up?",
        "🐼 How can I help?",
        "🐼 *munches bamboo*",
        "🐼 Still here, still awesome!",
    ]
    
    # Panda hover thoughts
    HOVER_THOUGHTS = [
        "💭 Thinking about bamboo...",
        "💭 Processing textures is fun!",
        "💭 Wonder what's for lunch...",
        "💭 Is it nap time yet?",
        "💭 These textures look organized!",
        "💭 Should I learn Python?",
        "💭 Life is good.",
        "💭 Texture sorting: 10/10 would recommend",
    ]
    
    # Petting responses
    PETTING_RESPONSES = [
        "🐼 *purrs* (Wait, pandas don't purr...)",
        "🐼 That feels nice!",
        "🐼 More pets please!",
        "🐼 You're the best!",
        "🐼 *happy panda sounds*",
        "🐼 I could get used to this!",
    ]
    
    # Easter egg triggers
    EASTER_EGGS = {
        'konami': '🎮 Up, Up, Down, Down, Left, Right, Left, Right, B, A, Start!',
        'bamboo': '🎋 Unlimited bamboo mode activated!',
        'ninja': '🥷 Stealth sorting engaged!',
        'panda_rage': '💢 PANDA RAGE MODE ACTIVATED! CLICK COUNT: 10!',
        'thousand_files': '🏆 HOLY SH*T! 1000 FILES SORTED! LEGENDARY!',
        'midnight_madness': '🌙 WHY ARE YOU AWAKE AT 3 AM? GO TO SLEEP!',
    }
    
    # Mood-specific messages
    MOOD_MESSAGES = {
        PandaMood.SARCASTIC: [
            "Oh wow, took you long enough. 🙄",
            "Sure, I'll just wait here. Not like I have bamboo to eat.",
            "Faster? Nah, take your time. I'm immortal apparently.",
        ],
        PandaMood.RAGE: [
            "THAT'S IT! I'VE HAD ENOUGH! 💢",
            "WHY DO YOU KEEP FAILING?! 🔥",
            "ANOTHER ERROR?! ARE YOU KIDDING ME?! 😤",
        ],
        PandaMood.DRUNK: [
            "Heyyy... you're pretty cool, you know that? 🍺",
            "*hiccup* Let's sort some... whatever those things are... 🥴",
            "Everything's... spinning... but in a good way! 🍻",
        ],
        PandaMood.EXISTENTIAL: [
            "What is the meaning of sorting textures? 🌌",
            "Are we just... organizing pixels in an infinite void? ✨",
            "10,000 files... and for what? What does it all mean? 💭",
        ],
    }
    
    def __init__(self):
        """Initialize the panda character."""
        self.current_mood = PandaMood.HAPPY
        self.click_count = 0
        self.pet_count = 0
        self.feed_count = 0
        self.hover_count = 0
        self.easter_eggs_triggered: Set[str] = set()
        self.start_time = time.time()
        self.files_processed_count = 0
        self.failed_operations = 0
        
        self._lock = threading.RLock()
    
    def set_mood(self, mood: PandaMood):
        """Set panda's current mood."""
        with self._lock:
            self.current_mood = mood
            logger.debug(f"Panda mood changed to: {mood.value}")
    
    def get_mood_indicator(self) -> str:
        """Get emoji indicator for current mood."""
        mood_emojis = {
            PandaMood.HAPPY: "😊",
            PandaMood.EXCITED: "🤩",
            PandaMood.WORKING: "💼",
            PandaMood.TIRED: "😮‍💨",
            PandaMood.CELEBRATING: "🎉",
            PandaMood.SLEEPING: "😴",
            PandaMood.SARCASTIC: "🙄",
            PandaMood.RAGE: "😡",
            PandaMood.DRUNK: "🥴",
            PandaMood.EXISTENTIAL: "🤔",
            PandaMood.MOTIVATING: "💪",
            PandaMood.TECH_SUPPORT: "🤓",
            PandaMood.SLEEPY: "🥱",
        }
        return mood_emojis.get(self.current_mood, "🐼")
    
    def get_animation_frame(self, animation_name: str = 'idle') -> str:
        """Get animation frame for current state."""
        frames = self.ANIMATIONS.get(animation_name, self.ANIMATIONS['idle'])
        return random.choice(frames)
    
    def on_click(self) -> str:
        """Handle panda being clicked."""
        with self._lock:
            self.click_count += 1
            
            # Easter egg: clicks trigger rage
            if self.click_count == self.RAGE_CLICK_THRESHOLD:
                self.easter_eggs_triggered.add('panda_rage')
                self.set_mood(PandaMood.RAGE)
                return self.EASTER_EGGS['panda_rage']
            
            return random.choice(self.CLICK_RESPONSES)
    
    def on_hover(self) -> str:
        """Handle mouse hovering over panda."""
        with self._lock:
            self.hover_count += 1
            return random.choice(self.HOVER_THOUGHTS)
    
    def on_pet(self) -> str:
        """Handle panda being petted."""
        with self._lock:
            self.pet_count += 1
            return random.choice(self.PETTING_RESPONSES)
    
    def on_feed(self) -> str:
        """Handle panda being fed bamboo."""
        with self._lock:
            self.feed_count += 1
            return "🎋 *nom nom nom* Delicious bamboo!"
    
    def get_context_menu(self) -> Dict[str, str]:
        """Get right-click context menu options."""
        return {
            'pet_panda': '🐼 Pet the panda',
            'feed_bamboo': '🎋 Feed bamboo',
            'check_mood': f'{self.get_mood_indicator()} Check mood',
        }
    
    def track_file_processed(self):
        """Track that a file was processed."""
        with self._lock:
            self.files_processed_count += 1
            
            # Easter egg: 1000 files
            if self.files_processed_count == 1000:
                self.easter_eggs_triggered.add('thousand_files')
            
            # Existential crisis after 10k files
            if self.files_processed_count >= 10000:
                self.set_mood(PandaMood.EXISTENTIAL)
    
    def track_operation_failure(self):
        """Track a failed operation."""
        with self._lock:
            self.failed_operations += 1
            
            # Enter rage mode after 5 failures
            if self.failed_operations >= 5:
                self.set_mood(PandaMood.RAGE)
    
    def check_time_for_3am(self) -> bool:
        """Check if it's 3 AM and trigger easter egg."""
        now = datetime.now()
        if now.hour == 3:
            if 'midnight_madness' not in self.easter_eggs_triggered:
                self.easter_eggs_triggered.add('midnight_madness')
                return True
        return False
    
    def handle_text_input(self, text: str) -> bool:
        """
        Handle text input for easter eggs.
        
        Returns:
            True if easter egg triggered
        """
        text_lower = text.lower()
        
        for trigger in ['bamboo', 'ninja', 'konami']:
            if trigger in text_lower and trigger not in self.easter_eggs_triggered:
                self.easter_eggs_triggered.add(trigger)
                return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """Get panda statistics."""
        return {
            'current_mood': self.current_mood.value,
            'click_count': self.click_count,
            'pet_count': self.pet_count,
            'feed_count': self.feed_count,
            'hover_count': self.hover_count,
            'files_processed': self.files_processed_count,
            'failed_operations': self.failed_operations,
            'easter_eggs_found': len(self.easter_eggs_triggered),
            'easter_eggs': list(self.easter_eggs_triggered),
            'uptime_seconds': time.time() - self.start_time,
        }
