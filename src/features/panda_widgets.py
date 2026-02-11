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
class ItemPhysics:
    """Physics properties for draggable items."""
    friction: float = 0.92
    gravity: float = 1.5
    bounce_damping: float = 0.6
    weight: float = 1.0  # Affects throw distance (higher = shorter throw)
    bounciness: float = 1.0  # Multiplier for bounce height


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
                 rarity: WidgetRarity = WidgetRarity.COMMON,
                 consumable: bool = False,
                 physics: Optional['ItemPhysics'] = None):
        """
        Initialize panda widget.
        
        Args:
            name: Widget name
            emoji: Emoji representation
            widget_type: Type of widget
            rarity: Rarity level
            consumable: Whether item is consumed on use (food) vs infinite (toys)
            physics: Custom physics properties for draggable item behavior
        """
        self.name = name
        self.emoji = emoji
        self.widget_type = widget_type
        self.rarity = rarity
        self.stats = WidgetStats()
        self.unlocked = False
        self.consumable = consumable
        self.quantity = 0  # For consumable items, tracks how many the user owns
        self.physics = physics or ItemPhysics()
    
    def use(self) -> Dict:
        """
        Use the widget with the panda.
        
        Returns:
            Dictionary with results (happiness, message, animation)
        """
        # Consumable items require quantity > 0
        if self.consumable and self.quantity <= 0:
            return {
                'happiness': 0,
                'message': f"No {self.name} left! Buy more from the shop.",
                'animation': 'idle',
                'widget': self.name,
                'consumed': False
            }
        
        self.stats.times_used += 1
        self.stats.last_used = time.time()
        
        happiness = self._calculate_happiness()
        message = self._get_interaction_message()
        animation = self._get_animation()
        
        self.stats.total_happiness_gained += happiness
        
        consumed = False
        if self.consumable:
            self.quantity -= 1
            consumed = True
        
        logger.debug(f"Used widget {self.name}: +{happiness} happiness")
        
        return {
            'happiness': happiness,
            'message': message,
            'animation': animation,
            'widget': self.name,
            'consumed': consumed
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
        info = {
            'name': self.name,
            'emoji': self.emoji,
            'type': self.widget_type.value,
            'rarity': self.rarity.value,
            'unlocked': self.unlocked,
            'times_used': self.stats.times_used,
            'total_happiness': self.stats.total_happiness_gained,
            'favorite': self.stats.favorite,
            'consumable': self.consumable,
        }
        if self.consumable:
            info['quantity'] = self.quantity
        return info


class ToyWidget(PandaWidget):
    """Toy widget for panda to play with. Toys have infinite uses."""
    
    TOY_MESSAGES = [
        "Panda loves playing with the {name}! 🎾",
        "Panda is having so much fun with the {name}! 🎉",
        "The panda can't get enough of the {name}! ⭐",
        "Panda bounces around with the {name}! 🐾",
        "Best toy ever! Panda says. 🐼💚"
    ]
    
    def __init__(self, name: str, emoji: str, rarity: WidgetRarity = WidgetRarity.COMMON,
                 physics: Optional[ItemPhysics] = None):
        super().__init__(name, emoji, WidgetType.TOY, rarity,
                         consumable=False, physics=physics)
    
    def _get_interaction_message(self) -> str:
        template = random.choice(self.TOY_MESSAGES)
        return template.format(name=self.name)
    
    def _get_animation(self) -> str:
        return "playing"


class FoodWidget(PandaWidget):
    """Food widget for panda to eat. Food is consumed on use."""
    
    FOOD_MESSAGES = [
        "Nom nom nom! Panda devours the {name}! 🍽️",
        "Panda munches happily on {name}! 😋",
        "Delicious! Panda loves {name}! 💚",
        "Panda's favorite snack: {name}! 🎋",
        "*munch* *munch* Panda is satisfied! 🐼"
    ]
    
    def __init__(self, name: str, emoji: str, rarity: WidgetRarity = WidgetRarity.COMMON,
                 energy_boost: int = 0):
        super().__init__(name, emoji, WidgetType.FOOD, rarity, consumable=True)
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
    
    # Prefixes to strip when mapping shop unlockable_ids to widget keys
    SHOP_ID_PREFIXES = ['food_', 'toy_']
    
    # Predefined widgets
    DEFAULT_WIDGETS = {
        # Toys - infinite use, different physics behaviors
        'ball': ToyWidget('Bamboo Ball', '🎾', WidgetRarity.COMMON,
                          physics=ItemPhysics(bounciness=1.8, weight=0.5, bounce_damping=0.75)),
        'stick': ToyWidget('Bamboo Stick', '🎍', WidgetRarity.COMMON,
                           physics=ItemPhysics(bounciness=0.3, weight=0.8)),
        'plushie': ToyWidget('Mini Panda Plushie', '🧸', WidgetRarity.UNCOMMON,
                             physics=ItemPhysics(bounciness=0.5, weight=0.4, friction=0.85)),
        'frisbee': ToyWidget('Bamboo Frisbee', '🥏', WidgetRarity.UNCOMMON,
                             physics=ItemPhysics(friction=0.97, gravity=0.5, weight=0.3)),
        'yo-yo': ToyWidget('Panda Yo-Yo', '🪀', WidgetRarity.RARE,
                           physics=ItemPhysics(bounciness=1.5, weight=0.6)),
        'puzzle': ToyWidget('Bamboo Puzzle', '🧩', WidgetRarity.RARE),
        'kite': ToyWidget('Panda Kite', '🪁', WidgetRarity.EPIC,
                          physics=ItemPhysics(gravity=0.3, friction=0.98, weight=0.2)),
        'robot': ToyWidget('Robot Panda Friend', '🤖', WidgetRarity.LEGENDARY,
                           physics=ItemPhysics(weight=1.5, bounciness=0.8)),
        'skateboard': ToyWidget('Panda Skateboard', '🛹', WidgetRarity.RARE,
                                physics=ItemPhysics(friction=0.96, weight=1.0, bounciness=0.4)),
        'drum': ToyWidget('Mini Drum Set', '🥁', WidgetRarity.EPIC,
                          physics=ItemPhysics(weight=2.0, bounciness=0.3, gravity=2.5)),
        'telescope': ToyWidget('Stargazing Telescope', '🔭', WidgetRarity.LEGENDARY,
                               physics=ItemPhysics(weight=1.8, bounciness=0.2)),
        'bouncy_carrot': ToyWidget('Bouncy Carrot', '🥕', WidgetRarity.UNCOMMON,
                                   physics=ItemPhysics(bounciness=2.5, weight=0.3, bounce_damping=0.85)),
        'squishy_ball': ToyWidget('Big Red Squishy Ball', '🔴', WidgetRarity.RARE,
                                  physics=ItemPhysics(bounciness=2.0, weight=0.4, bounce_damping=0.8, friction=0.88)),
        'dumbbell': ToyWidget('Super Heavy Dumbbell', '🏋️', WidgetRarity.EPIC,
                              physics=ItemPhysics(weight=3.0, gravity=3.0, bounciness=0.15, bounce_damping=0.3)),
        
        # Food - consumed on use
        'bamboo': FoodWidget('Fresh Bamboo', '🎋', WidgetRarity.COMMON, energy_boost=10),
        'bamboo_shoots': FoodWidget('Bamboo Shoots', '🌱', WidgetRarity.COMMON, energy_boost=5),
        'apple': FoodWidget('Juicy Apple', '🍎', WidgetRarity.UNCOMMON, energy_boost=15),
        'cake': FoodWidget('Bamboo Cake', '🍰', WidgetRarity.RARE, energy_boost=30),
        'honey': FoodWidget('Sweet Honey', '🍯', WidgetRarity.RARE, energy_boost=25),
        'bento': FoodWidget('Panda Bento Box', '🍱', WidgetRarity.EPIC, energy_boost=50),
        'tea': FoodWidget('Bamboo Tea', '🍵', WidgetRarity.UNCOMMON, energy_boost=20),
        'dumplings': FoodWidget('Lucky Dumplings', '🥟', WidgetRarity.LEGENDARY, energy_boost=100),
        'cookies': FoodWidget('Panda Cookies', '🍪', WidgetRarity.COMMON, energy_boost=8),
        'ramen': FoodWidget('Ramen Bowl', '🍜', WidgetRarity.UNCOMMON, energy_boost=20),
        'sushi': FoodWidget('Panda Sushi Roll', '🍣', WidgetRarity.RARE, energy_boost=28),
        'rice_ball': FoodWidget('Rice Ball', '🍙', WidgetRarity.COMMON, energy_boost=8),
        'boba_tea': FoodWidget('Boba Tea', '🧋', WidgetRarity.UNCOMMON, energy_boost=18),
        'ice_cream': FoodWidget('Ice Cream Cone', '🍦', WidgetRarity.UNCOMMON, energy_boost=15),
        'birthday_cake': FoodWidget('Birthday Cake', '🎂', WidgetRarity.EPIC, energy_boost=60),
        'golden_bamboo': FoodWidget('Golden Bamboo', '✨', WidgetRarity.LEGENDARY, energy_boost=80),
        
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
    
    def add_food_quantity(self, widget_id: str, amount: int = 1) -> bool:
        """
        Add quantity to a consumable food widget (from shop purchase).
        
        Args:
            widget_id: Widget identifier
            amount: Number of items to add
            
        Returns:
            True if successful
        """
        widget = self.widgets.get(widget_id)
        if not widget:
            logger.warning(f"Widget not found: {widget_id}")
            return False
        
        if not widget.consumable:
            logger.debug(f"Widget {widget_id} is not consumable, skipping quantity add")
            return False
        
        if not widget.unlocked:
            widget.unlock()
        
        widget.quantity += amount
        logger.info(f"Added {amount}x {widget.name} (now has {widget.quantity})")
        return True
    
    def resolve_shop_widget_id(self, shop_unlockable_id: str) -> Optional[str]:
        """
        Resolve a shop item's unlockable_id to a widget collection key.
        Handles prefix stripping (e.g. 'food_bamboo' -> 'bamboo').
        
        Args:
            shop_unlockable_id: The unlockable_id from the shop item
            
        Returns:
            Widget collection key or None
        """
        # Direct match first
        if shop_unlockable_id in self.widgets:
            return shop_unlockable_id
        
        # Strip common prefixes
        for prefix in self.SHOP_ID_PREFIXES:
            if shop_unlockable_id.startswith(prefix):
                stripped = shop_unlockable_id[len(prefix):]
                if stripped in self.widgets:
                    return stripped
        
        return None
    
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
