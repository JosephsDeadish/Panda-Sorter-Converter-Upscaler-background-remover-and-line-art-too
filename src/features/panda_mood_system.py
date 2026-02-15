"""
Panda Mood System

Internal mood state management for the interactive panda.
Moods affect animations, behaviors, and interactions.

Mood States:
    - Happy: Playful, energetic, frequent interactions
    - Sleepy: Slow, lies down, infrequent interactions
    - Mischievous: Bites more, playful pranks, high interaction
    - Annoyed: Grumpy reactions, less cooperative, moderate interaction

Features:
    - Mood transitions based on events
    - Time-based mood changes
    - Mood-based behavior modifiers
    - Visual mood indicators
"""

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QObject = object

import random
import time
from enum import Enum


class PandaMood(Enum):
    """Panda mood states."""
    HAPPY = "happy"
    SLEEPY = "sleepy"
    MISCHIEVOUS = "mischievous"
    ANNOYED = "annoyed"


class MoodTransitionReason(Enum):
    """Reasons for mood transitions."""
    TIME_DECAY = "time_decay"
    USER_INTERACTION = "user_interaction"
    ENVIRONMENTAL_EVENT = "environmental_event"
    QUEST_COMPLETION = "quest_completion"
    WIDGET_INTERACTION = "widget_interaction"
    IDLE_TOO_LONG = "idle_too_long"
    TOO_MANY_INTERACTIONS = "too_many_interactions"


class PandaMoodSystem(QObject if PYQT_AVAILABLE else object):
    """
    Manages panda's internal mood state and transitions.
    
    This system:
    - Tracks current mood
    - Handles mood transitions
    - Provides mood-based behavior modifiers
    - Triggers visual mood indicators
    - Reacts to events with mood changes
    """
    
    # Signals
    mood_changed = pyqtSignal(str, str, str) if PYQT_AVAILABLE else None  # old_mood, new_mood, reason
    mood_intensity_changed = pyqtSignal(float) if PYQT_AVAILABLE else None
    
    def __init__(self, panda_overlay=None):
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt6 required for PandaMoodSystem")
        
        super().__init__()
        
        self.panda_overlay = panda_overlay
        
        # Current mood state
        self.current_mood = PandaMood.HAPPY
        self.mood_intensity = 0.7  # 0.0-1.0, how strongly mood is expressed
        self.mood_start_time = time.time()
        
        # Mood durations (in seconds)
        self.mood_durations = {
            PandaMood.HAPPY: (120, 300),  # 2-5 minutes
            PandaMood.SLEEPY: (60, 180),   # 1-3 minutes
            PandaMood.MISCHIEVOUS: (90, 240),  # 1.5-4 minutes
            PandaMood.ANNOYED: (30, 120),  # 0.5-2 minutes
        }
        
        # Interaction tracking
        self.interactions_last_minute = 0
        self.last_interaction_time = time.time()
        self.idle_time = 0
        
        # Mood transition probabilities
        self.transition_matrix = {
            PandaMood.HAPPY: {
                PandaMood.SLEEPY: 0.3,
                PandaMood.MISCHIEVOUS: 0.4,
                PandaMood.ANNOYED: 0.1,
                PandaMood.HAPPY: 0.2,
            },
            PandaMood.SLEEPY: {
                PandaMood.HAPPY: 0.4,
                PandaMood.MISCHIEVOUS: 0.2,
                PandaMood.ANNOYED: 0.1,
                PandaMood.SLEEPY: 0.3,
            },
            PandaMood.MISCHIEVOUS: {
                PandaMood.HAPPY: 0.3,
                PandaMood.SLEEPY: 0.2,
                PandaMood.ANNOYED: 0.2,
                PandaMood.MISCHIEVOUS: 0.3,
            },
            PandaMood.ANNOYED: {
                PandaMood.HAPPY: 0.3,
                PandaMood.SLEEPY: 0.3,
                PandaMood.MISCHIEVOUS: 0.2,
                PandaMood.ANNOYED: 0.2,
            },
        }
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_mood)
        self.update_timer.start(10000)  # Check every 10 seconds
    
    def _update_mood(self):
        """Periodic mood update check."""
        current_time = time.time()
        time_in_mood = current_time - self.mood_start_time
        
        # Update idle time
        time_since_interaction = current_time - self.last_interaction_time
        if time_since_interaction > 60:
            self.idle_time += 10
        else:
            self.idle_time = 0
        
        # Check if mood should change based on time
        min_duration, max_duration = self.mood_durations[self.current_mood]
        
        if time_in_mood > min_duration:
            # Probability increases with time
            change_probability = min((time_in_mood - min_duration) / (max_duration - min_duration), 0.8)
            
            if random.random() < change_probability:
                self._choose_new_mood(MoodTransitionReason.TIME_DECAY)
        
        # Check for idle-based mood changes
        if self.idle_time > 120:  # 2 minutes idle
            self._transition_to_mood(PandaMood.SLEEPY, MoodTransitionReason.IDLE_TOO_LONG)
        
        # Check for over-interaction
        if self.interactions_last_minute > 10:
            self._transition_to_mood(PandaMood.ANNOYED, MoodTransitionReason.TOO_MANY_INTERACTIONS)
    
    def _choose_new_mood(self, reason):
        """Choose a new mood based on transition matrix."""
        # Get transition probabilities from current mood
        transitions = self.transition_matrix[self.current_mood]
        
        # Random choice weighted by probabilities
        moods = list(transitions.keys())
        probabilities = list(transitions.values())
        
        new_mood = random.choices(moods, weights=probabilities, k=1)[0]
        
        if new_mood != self.current_mood:
            self._transition_to_mood(new_mood, reason)
    
    def _transition_to_mood(self, new_mood, reason):
        """Transition to a new mood."""
        old_mood = self.current_mood
        self.current_mood = new_mood
        self.mood_start_time = time.time()
        
        # Reset intensity
        self.mood_intensity = 0.7 + random.random() * 0.3
        
        # Emit signal
        if self.mood_changed:
            self.mood_changed.emit(old_mood.value, new_mood.value, reason.value)
        
        print(f"Panda mood changed: {old_mood.value} → {new_mood.value} (reason: {reason.value})")
        
        # Update overlay animation if available
        if self.panda_overlay:
            self._apply_mood_to_overlay()
    
    def _apply_mood_to_overlay(self):
        """Apply current mood to panda overlay."""
        mood_animations = {
            PandaMood.HAPPY: 'happy_bounce',
            PandaMood.SLEEPY: 'sleepy_slow',
            PandaMood.MISCHIEVOUS: 'mischievous_grin',
            PandaMood.ANNOYED: 'annoyed_grumpy',
        }
        
        animation = mood_animations.get(self.current_mood, 'idle')
        if hasattr(self.panda_overlay, 'set_animation_state'):
            self.panda_overlay.set_animation_state(animation)
    
    def on_user_interaction(self, interaction_type):
        """
        Handle user interaction event.
        
        Args:
            interaction_type: Type of interaction
        """
        self.last_interaction_time = time.time()
        self.idle_time = 0
        self.interactions_last_minute += 1
        
        # Reset interaction counter after a minute
        QTimer.singleShot(60000, self._decrement_interaction_count)
        
        # Mood reactions to interactions
        if self.current_mood == PandaMood.SLEEPY:
            # Interaction wakes panda up
            if random.random() < 0.3:
                self._transition_to_mood(PandaMood.HAPPY, MoodTransitionReason.USER_INTERACTION)
        
        elif self.current_mood == PandaMood.ANNOYED:
            # Might get more annoyed with too many interactions
            if self.interactions_last_minute > 5:
                self.mood_intensity = min(1.0, self.mood_intensity + 0.1)
                if self.mood_intensity_changed:
                    self.mood_intensity_changed.emit(self.mood_intensity)
    
    def _decrement_interaction_count(self):
        """Decrement interaction counter."""
        if self.interactions_last_minute > 0:
            self.interactions_last_minute -= 1
    
    def on_environmental_event(self, event_type):
        """
        Handle environmental event.
        
        Args:
            event_type: Type of environmental event
        """
        # Certain events affect mood
        if event_type == 'focus_lost':
            # User left, panda gets sleepy
            if random.random() < 0.4:
                self._transition_to_mood(PandaMood.SLEEPY, MoodTransitionReason.ENVIRONMENTAL_EVENT)
        
        elif event_type == 'focus_gained':
            # User returned, panda perks up
            if self.current_mood == PandaMood.SLEEPY:
                if random.random() < 0.6:
                    self._transition_to_mood(PandaMood.HAPPY, MoodTransitionReason.ENVIRONMENTAL_EVENT)
        
        elif event_type == 'scroll_start':
            # Scrolling can make mischievous panda more mischievous
            if self.current_mood == PandaMood.MISCHIEVOUS:
                self.mood_intensity = min(1.0, self.mood_intensity + 0.05)
    
    def on_quest_completed(self):
        """Handle quest completion."""
        # Quest completion makes panda happy
        self._transition_to_mood(PandaMood.HAPPY, MoodTransitionReason.QUEST_COMPLETION)
        self.mood_intensity = 0.9
    
    def get_behavior_modifiers(self):
        """
        Get behavior modifiers based on current mood.
        
        Returns:
            Dict with modifier values
        """
        base_modifiers = {
            'interaction_frequency': 1.0,
            'animation_speed': 1.0,
            'bite_probability': 0.5,
            'movement_speed': 1.0,
            'rest_probability': 0.1,
        }
        
        if self.current_mood == PandaMood.HAPPY:
            return {
                'interaction_frequency': 1.3 * self.mood_intensity,
                'animation_speed': 1.2,
                'bite_probability': 0.4,
                'movement_speed': 1.3,
                'rest_probability': 0.05,
            }
        
        elif self.current_mood == PandaMood.SLEEPY:
            return {
                'interaction_frequency': 0.3 * self.mood_intensity,
                'animation_speed': 0.6,
                'bite_probability': 0.1,
                'movement_speed': 0.5,
                'rest_probability': 0.7,
            }
        
        elif self.current_mood == PandaMood.MISCHIEVOUS:
            return {
                'interaction_frequency': 1.5 * self.mood_intensity,
                'animation_speed': 1.1,
                'bite_probability': 0.8,  # More biting!
                'movement_speed': 1.2,
                'rest_probability': 0.03,
            }
        
        elif self.current_mood == PandaMood.ANNOYED:
            return {
                'interaction_frequency': 0.7,
                'animation_speed': 0.9,
                'bite_probability': 0.6,
                'movement_speed': 0.8,
                'rest_probability': 0.3,
            }
        
        return base_modifiers
    
    def get_mood_description(self):
        """Get human-readable mood description."""
        descriptions = {
            PandaMood.HAPPY: "Feeling playful and energetic!",
            PandaMood.SLEEPY: "Getting a bit drowsy...",
            PandaMood.MISCHIEVOUS: "In a mischievous mood!",
            PandaMood.ANNOYED: "Feeling a bit grumpy...",
        }
        return descriptions.get(self.current_mood, "Feeling neutral")
    
    def get_mood_color(self):
        """Get color associated with current mood (for aura/effects)."""
        colors = {
            PandaMood.HAPPY: (1.0, 0.9, 0.2),  # Yellow
            PandaMood.SLEEPY: (0.5, 0.5, 0.8),  # Blue
            PandaMood.MISCHIEVOUS: (1.0, 0.5, 0.0),  # Orange
            PandaMood.ANNOYED: (0.8, 0.2, 0.2),  # Red
        }
        return colors.get(self.current_mood, (1.0, 1.0, 1.0))
    
    def force_mood(self, mood):
        """
        Force a specific mood (for testing or special events).
        
        Args:
            mood: PandaMood to set
        """
        self._transition_to_mood(mood, MoodTransitionReason.USER_INTERACTION)
    
    def get_state(self):
        """
        Get current mood system state.
        
        Returns:
            Dict with state information
        """
        return {
            'mood': self.current_mood.value,
            'intensity': self.mood_intensity,
            'time_in_mood': time.time() - self.mood_start_time,
            'idle_time': self.idle_time,
            'interactions_last_minute': self.interactions_last_minute,
            'description': self.get_mood_description(),
            'color': self.get_mood_color(),
        }


# Convenience function
def create_mood_system(panda_overlay=None):
    """
    Create a panda mood system.
    
    Args:
        panda_overlay: Optional TransparentPandaOverlay instance
        
    Returns:
        PandaMoodSystem instance or None
    """
    if not PYQT_AVAILABLE:
        print("Warning: PyQt6 not available, cannot create mood system")
        return None
    
    return PandaMoodSystem(panda_overlay)
