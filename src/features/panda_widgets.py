"""
Panda Widget System - Interactive toys and food for the panda
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
import time
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class WidgetType(Enum):
    """Types of interactive widgets."""
    TOY = "toy"
    FOOD = "food"
    ACCESSORY = "accessory"


class WidgetRarity(Enum):
    """Widget rarity levels."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class WidgetStats:
    """Statistics for widget usage."""
    times_used: int = 0
    total_happiness_gained: int = 0
    last_used: Optional[float] = None
    favorite: bool = False


class PandaWidget:
    """Base class for panda interactive widgets."""
    
    def __init__(self, name: str, emoji: str, widget_type: WidgetType,
                 rarity: WidgetRarity = WidgetRarity.COMMON):
        """
        Initialize panda widget.
        
        Args:
            name: Widget name
            emoji: Emoji representation
            widget_type: Type of widget
            rarity: Rarity level
        """
        self.name = name
        self.emoji = emoji
        self.widget_type = widget_type
        self.rarity = rarity
        self.stats = WidgetStats()
        self.unlocked = False
    
    def use(self) -> Dict:
        """
        Use the widget with the panda.
        
        Returns:
            Dictionary with results (happiness, message, animation)
        """
        self.stats.times_used += 1
        self.stats.last_used = time.time()
        
        happiness = self._calculate_happiness()
        message = self._get_interaction_message()
        animation = self._get_animation()
        
        self.stats.total_happiness_gained += happiness
        
        logger.debug(f"Used widget {self.name}: +{happiness} happiness")
        
        return {
            'happiness': happiness,
            'message': message,
            'animation': animation,
            'widget': self.name
        }
    
    def _calculate_happiness(self) -> int:
        """Calculate happiness gained from using widget."""
        # Base happiness by rarity
        base_happiness = {
            WidgetRarity.COMMON: 5,
            WidgetRarity.UNCOMMON: 10,
            WidgetRarity.RARE: 20,
            WidgetRarity.EPIC: 35,
            WidgetRarity.LEGENDARY: 50
        }
        
        happiness = base_happiness[self.rarity]
        
        # Bonus for favorite items
        if self.stats.favorite:
            happiness = int(happiness * 1.5)
        
        # Random variation
        variation = random.randint(-2, 5)
        happiness += variation
        
        return max(1, happiness)
    
    def _get_interaction_message(self) -> str:
        """Get message for interaction."""
        return f"Panda plays with {self.name}! 🐼"
    
    def _get_animation(self) -> str:
        """Get animation name for interaction."""
        return "playing"
    
    def set_favorite(self, favorite: bool = True) -> None:
        """Mark widget as favorite."""
        self.stats.favorite = favorite
    
    def unlock(self) -> None:
        """Unlock the widget."""
        self.unlocked = True
        logger.info(f"Unlocked widget: {self.name}")
    
    def get_info(self) -> Dict:
        """Get widget information."""
        return {
            'name': self.name,
            'emoji': self.emoji,
            'type': self.widget_type.value,
            'rarity': self.rarity.value,
            'unlocked': self.unlocked,
            'times_used': self.stats.times_used,
            'total_happiness': self.stats.total_happiness_gained,
            'favorite': self.stats.favorite
        }


class ToyWidget(PandaWidget):
    """Toy widget for panda to play with."""
    
    TOY_MESSAGES = [
        "Panda loves playing with the {name}! 🎾",
        "Panda is having so much fun with the {name}! 🎉",
        "The panda can't get enough of the {name}! ⭐",
        "Panda bounces around with the {name}! 🐾",
        "Best toy ever! Panda says. 🐼💚"
    ]
    
    def __init__(self, name: str, emoji: str, rarity: WidgetRarity = WidgetRarity.COMMON):
        super().__init__(name, emoji, WidgetType.TOY, rarity)
    
    def _get_interaction_message(self) -> str:
        template = random.choice(self.TOY_MESSAGES)
        return template.format(name=self.name)
    
    def _get_animation(self) -> str:
        return "playing"


class FoodWidget(PandaWidget):
    """Food widget for panda to eat."""
    
    FOOD_MESSAGES = [
        "Nom nom nom! Panda devours the {name}! 🍽️",
        "Panda munches happily on {name}! 😋",
        "Delicious! Panda loves {name}! 💚",
        "Panda's favorite snack: {name}! 🎋",
        "*munch* *munch* Panda is satisfied! 🐼"
    ]
    
    def __init__(self, name: str, emoji: str, rarity: WidgetRarity = WidgetRarity.COMMON,
                 energy_boost: int = 0):
        super().__init__(name, emoji, WidgetType.FOOD, rarity)
        self.energy_boost = energy_boost
    
    def use(self) -> Dict:
        """Use food - provides extra energy boost."""
        result = super().use()
        result['energy'] = self.energy_boost
        return result
    
    def _get_interaction_message(self) -> str:
        template = random.choice(self.FOOD_MESSAGES)
        return template.format(name=self.name)
    
    def _get_animation(self) -> str:
        return "eating"


class AccessoryWidget(PandaWidget):
    """Accessory widget for panda customization."""
    
    def __init__(self, name: str, emoji: str, rarity: WidgetRarity = WidgetRarity.COMMON):
        super().__init__(name, emoji, WidgetType.ACCESSORY, rarity)
    
    def _get_interaction_message(self) -> str:
        return f"Panda tries on {self.name}! Looking good! ✨"
    
    def _get_animation(self) -> str:
        return "customizing"


class WidgetCollection:
    """Manages the collection of all panda widgets."""
    
    # Predefined widgets
    DEFAULT_WIDGETS = {
        # Toys
        'ball': ToyWidget('Bamboo Ball', '🎾', WidgetRarity.COMMON),
        'stick': ToyWidget('Bamboo Stick', '🎍', WidgetRarity.COMMON),
        'plushie': ToyWidget('Mini Panda Plushie', '🧸', WidgetRarity.UNCOMMON),
        'frisbee': ToyWidget('Bamboo Frisbee', '🥏', WidgetRarity.UNCOMMON),
        'yo-yo': ToyWidget('Panda Yo-Yo', '🪀', WidgetRarity.RARE),
        'puzzle': ToyWidget('Bamboo Puzzle', '🧩', WidgetRarity.RARE),
        'kite': ToyWidget('Panda Kite', '🪁', WidgetRarity.EPIC),
        'robot': ToyWidget('Robot Panda Friend', '🤖', WidgetRarity.LEGENDARY),
        
        # Food
        'bamboo': FoodWidget('Fresh Bamboo', '🎋', WidgetRarity.COMMON, energy_boost=10),
        'bamboo_shoots': FoodWidget('Bamboo Shoots', '🌱', WidgetRarity.COMMON, energy_boost=5),
        'apple': FoodWidget('Juicy Apple', '🍎', WidgetRarity.UNCOMMON, energy_boost=15),
        'cake': FoodWidget('Bamboo Cake', '🍰', WidgetRarity.RARE, energy_boost=30),
        'honey': FoodWidget('Sweet Honey', '🍯', WidgetRarity.RARE, energy_boost=25),
        'bento': FoodWidget('Panda Bento Box', '🍱', WidgetRarity.EPIC, energy_boost=50),
        'tea': FoodWidget('Bamboo Tea', '🍵', WidgetRarity.UNCOMMON, energy_boost=20),
        'dumplings': FoodWidget('Lucky Dumplings', '🥟', WidgetRarity.LEGENDARY, energy_boost=100),
        
        # Accessories
        'bowtie': AccessoryWidget('Fancy Bow Tie', '🎀', WidgetRarity.COMMON),
        'hat': AccessoryWidget('Bamboo Hat', '🎩', WidgetRarity.UNCOMMON),
        'sunglasses': AccessoryWidget('Cool Sunglasses', '🕶️', WidgetRarity.RARE),
        'crown': AccessoryWidget('Panda Crown', '👑', WidgetRarity.EPIC),
        'cape': AccessoryWidget('Superhero Cape', '🦸', WidgetRarity.LEGENDARY),
    }
    
    def __init__(self):
        """Initialize widget collection."""
        self.widgets: Dict[str, PandaWidget] = {}
        self.active_widgets: List[str] = []
        self._initialize_defaults()
    
    def _initialize_defaults(self) -> None:
        """Initialize with default widgets."""
        for widget_id, widget in self.DEFAULT_WIDGETS.items():
            self.widgets[widget_id] = widget
        
        # Unlock common items by default
        for widget_id, widget in self.widgets.items():
            if widget.rarity == WidgetRarity.COMMON:
                widget.unlock()
    
    def get_widget(self, widget_id: str) -> Optional[PandaWidget]:
        """Get widget by ID."""
        return self.widgets.get(widget_id)
    
    def get_all_widgets(self, widget_type: Optional[WidgetType] = None,
                       unlocked_only: bool = False) -> List[PandaWidget]:
        """
        Get all widgets, optionally filtered.
        
        Args:
            widget_type: Filter by widget type
            unlocked_only: Only return unlocked widgets
            
        Returns:
            List of widgets
        """
        widgets = list(self.widgets.values())
        
        if widget_type:
            widgets = [w for w in widgets if w.widget_type == widget_type]
        
        if unlocked_only:
            widgets = [w for w in widgets if w.unlocked]
        
        return widgets
    
    def get_toys(self, unlocked_only: bool = False) -> List[ToyWidget]:
        """Get all toy widgets."""
        return self.get_all_widgets(WidgetType.TOY, unlocked_only)
    
    def get_food(self, unlocked_only: bool = False) -> List[FoodWidget]:
        """Get all food widgets."""
        return self.get_all_widgets(WidgetType.FOOD, unlocked_only)
    
    def get_accessories(self, unlocked_only: bool = False) -> List[AccessoryWidget]:
        """Get all accessory widgets."""
        return self.get_all_widgets(WidgetType.ACCESSORY, unlocked_only)
    
    def unlock_widget(self, widget_id: str) -> bool:
        """
        Unlock a widget.
        
        Args:
            widget_id: Widget identifier
            
        Returns:
            True if unlocked successfully
        """
        widget = self.widgets.get(widget_id)
        if not widget:
            logger.warning(f"Widget not found: {widget_id}")
            return False
        
        if widget.unlocked:
            logger.debug(f"Widget already unlocked: {widget_id}")
            return False
        
        widget.unlock()
        return True
    
    def use_widget(self, widget_id: str) -> Optional[Dict]:
        """
        Use a widget with the panda.
        
        Args:
            widget_id: Widget identifier
            
        Returns:
            Result dictionary or None if failed
        """
        widget = self.widgets.get(widget_id)
        if not widget:
            logger.warning(f"Widget not found: {widget_id}")
            return None
        
        if not widget.unlocked:
            logger.warning(f"Widget not unlocked: {widget_id}")
            return None
        
        return widget.use()
    
    def set_favorite(self, widget_id: str, favorite: bool = True) -> bool:
        """
        Mark a widget as favorite.
        
        Args:
            widget_id: Widget identifier
            favorite: Whether to mark as favorite
            
        Returns:
            True if successful
        """
        widget = self.widgets.get(widget_id)
        if not widget:
            return False
        
        widget.set_favorite(favorite)
        return True
    
    def get_favorites(self) -> List[PandaWidget]:
        """Get all favorite widgets."""
        return [w for w in self.widgets.values() if w.stats.favorite]
    
    def get_statistics(self) -> Dict:
        """
        Get widget collection statistics.
        
        Returns:
            Statistics dictionary
        """
        total_widgets = len(self.widgets)
        unlocked_widgets = sum(1 for w in self.widgets.values() if w.unlocked)
        total_uses = sum(w.stats.times_used for w in self.widgets.values())
        total_happiness = sum(w.stats.total_happiness_gained for w in self.widgets.values())
        
        return {
            'total_widgets': total_widgets,
            'unlocked_widgets': unlocked_widgets,
            'total_uses': total_uses,
            'total_happiness_gained': total_happiness,
            'by_type': self._count_by_type(),
            'by_rarity': self._count_by_rarity(),
            'most_used': self._get_most_used()
        }
    
    def _count_by_type(self) -> Dict[str, Dict[str, int]]:
        """Count widgets by type."""
        counts = {}
        for widget_type in WidgetType:
            total = sum(1 for w in self.widgets.values() if w.widget_type == widget_type)
            unlocked = sum(1 for w in self.widgets.values() 
                          if w.widget_type == widget_type and w.unlocked)
            counts[widget_type.value] = {
                'total': total,
                'unlocked': unlocked
            }
        return counts
    
    def _count_by_rarity(self) -> Dict[str, Dict[str, int]]:
        """Count widgets by rarity."""
        counts = {}
        for rarity in WidgetRarity:
            total = sum(1 for w in self.widgets.values() if w.rarity == rarity)
            unlocked = sum(1 for w in self.widgets.values() 
                          if w.rarity == rarity and w.unlocked)
            counts[rarity.value] = {
                'total': total,
                'unlocked': unlocked
            }
        return counts
    
    def _get_most_used(self, limit: int = 5) -> List[Dict]:
        """Get most used widgets."""
        sorted_widgets = sorted(
            self.widgets.values(),
            key=lambda w: w.stats.times_used,
            reverse=True
        )
        
        return [
            {
                'name': w.name,
                'emoji': w.emoji,
                'times_used': w.stats.times_used
            }
            for w in sorted_widgets[:limit]
        ]
