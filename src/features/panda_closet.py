"""
Panda Closet - Customization system for panda appearance
Allows changing fur style, color, clothing, hats, shoes, and accessories
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class CustomizationCategory(Enum):
    """Categories of customization options."""
    FUR_STYLE = "fur_style"
    FUR_COLOR = "fur_color"
    CLOTHING = "clothing"
    HAT = "hat"
    SHOES = "shoes"
    ACCESSORY = "accessory"


class ItemRarity(Enum):
    """Rarity levels for customization items."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class CustomizationItem:
    """Represents a single customization item."""
    id: str
    name: str
    category: CustomizationCategory
    emoji: str
    description: str
    rarity: ItemRarity
    cost: int = 0
    unlocked: bool = False
    equipped: bool = False


class PandaAppearance:
    """Stores the current panda appearance configuration."""
    
    def __init__(self):
        """Initialize with default appearance."""
        self.fur_style = "classic"
        self.fur_color = "black_white"
        self.clothing = None
        self.hat = None
        self.shoes = None
        self.accessories = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'fur_style': self.fur_style,
            'fur_color': self.fur_color,
            'clothing': self.clothing,
            'hat': self.hat,
            'shoes': self.shoes,
            'accessories': self.accessories
        }
    
    def from_dict(self, data: Dict) -> None:
        """Load from dictionary."""
        self.fur_style = data.get('fur_style', 'classic')
        self.fur_color = data.get('fur_color', 'black_white')
        self.clothing = data.get('clothing')
        self.hat = data.get('hat')
        self.shoes = data.get('shoes')
        self.accessories = data.get('accessories', [])
    
    def get_display_string(self) -> str:
        """Get a string representation of the appearance."""
        parts = [
            f"Fur: {self.fur_style} ({self.fur_color})"
        ]
        
        if self.hat:
            parts.append(f"Hat: {self.hat}")
        if self.clothing:
            parts.append(f"Clothing: {self.clothing}")
        if self.shoes:
            parts.append(f"Shoes: {self.shoes}")
        if self.accessories:
            parts.append(f"Accessories: {', '.join(self.accessories)}")
        
        return " | ".join(parts)


class PandaCloset:
    """Manages panda customization options and appearance."""
    
    # Predefined customization items
    DEFAULT_ITEMS = {
        # Fur Styles
        'classic': CustomizationItem(
            'classic', 'Classic Panda', CustomizationCategory.FUR_STYLE,
            '🐼', 'The traditional panda look', ItemRarity.COMMON, 0, True, True
        ),
        'fluffy': CustomizationItem(
            'fluffy', 'Fluffy Panda', CustomizationCategory.FUR_STYLE,
            '🐼✨', 'Extra fluffy fur', ItemRarity.UNCOMMON, 100, False, False
        ),
        'sleek': CustomizationItem(
            'sleek', 'Sleek Panda', CustomizationCategory.FUR_STYLE,
            '🐼💨', 'Smooth and shiny', ItemRarity.RARE, 250, False, False
        ),
        'rainbow': CustomizationItem(
            'rainbow', 'Rainbow Panda', CustomizationCategory.FUR_STYLE,
            '🌈🐼', 'Magical rainbow fur', ItemRarity.LEGENDARY, 1000, False, False
        ),
        
        # Fur Colors
        'black_white': CustomizationItem(
            'black_white', 'Black & White', CustomizationCategory.FUR_COLOR,
            '⚫⚪', 'Classic panda colors', ItemRarity.COMMON, 0, True, True
        ),
        'brown': CustomizationItem(
            'brown', 'Brown Bear', CustomizationCategory.FUR_COLOR,
            '🟤', 'Brown fur variation', ItemRarity.UNCOMMON, 50, False, False
        ),
        'red_panda': CustomizationItem(
            'red_panda', 'Red Panda', CustomizationCategory.FUR_COLOR,
            '🔴', 'Red panda coloring', ItemRarity.RARE, 200, False, False
        ),
        'golden': CustomizationItem(
            'golden', 'Golden Panda', CustomizationCategory.FUR_COLOR,
            '🟡', 'Shimmering gold', ItemRarity.EPIC, 500, False, False
        ),
        'galaxy': CustomizationItem(
            'galaxy', 'Galaxy Panda', CustomizationCategory.FUR_COLOR,
            '🌌', 'Cosmic space colors', ItemRarity.LEGENDARY, 1500, False, False
        ),
        
        # Clothing
        'tshirt': CustomizationItem(
            'tshirt', 'Bamboo T-Shirt', CustomizationCategory.CLOTHING,
            '👕', 'Casual bamboo tee', ItemRarity.COMMON, 25, False, False
        ),
        'hoodie': CustomizationItem(
            'hoodie', 'Cozy Hoodie', CustomizationCategory.CLOTHING,
            '🧥', 'Warm and comfy', ItemRarity.UNCOMMON, 75, False, False
        ),
        'suit': CustomizationItem(
            'suit', 'Business Suit', CustomizationCategory.CLOTHING,
            '🤵', 'Professional attire', ItemRarity.RARE, 300, False, False
        ),
        'kimono': CustomizationItem(
            'kimono', 'Traditional Kimono', CustomizationCategory.CLOTHING,
            '👘', 'Elegant traditional wear', ItemRarity.EPIC, 600, False, False
        ),
        'superhero': CustomizationItem(
            'superhero', 'Superhero Costume', CustomizationCategory.CLOTHING,
            '🦸', 'Save the world in style', ItemRarity.LEGENDARY, 2000, False, False
        ),
        
        # Hats
        'baseball_cap': CustomizationItem(
            'baseball_cap', 'Baseball Cap', CustomizationCategory.HAT,
            '🧢', 'Sporty cap', ItemRarity.COMMON, 30, False, False
        ),
        'top_hat': CustomizationItem(
            'top_hat', 'Top Hat', CustomizationCategory.HAT,
            '🎩', 'Classy top hat', ItemRarity.UNCOMMON, 100, False, False
        ),
        'party_hat': CustomizationItem(
            'party_hat', 'Party Hat', CustomizationCategory.HAT,
            '🎉', 'It\'s party time!', ItemRarity.RARE, 150, False, False
        ),
        'crown': CustomizationItem(
            'crown', 'Royal Crown', CustomizationCategory.HAT,
            '👑', 'Rule the bamboo forest', ItemRarity.EPIC, 800, False, False
        ),
        'wizard_hat': CustomizationItem(
            'wizard_hat', 'Wizard Hat', CustomizationCategory.HAT,
            '🧙', 'Magical powers included', ItemRarity.LEGENDARY, 1800, False, False
        ),
        
        # Shoes
        'sneakers': CustomizationItem(
            'sneakers', 'Bamboo Sneakers', CustomizationCategory.SHOES,
            '👟', 'Comfortable running shoes', ItemRarity.COMMON, 40, False, False
        ),
        'boots': CustomizationItem(
            'boots', 'Adventure Boots', CustomizationCategory.SHOES,
            '👢', 'Ready for any terrain', ItemRarity.UNCOMMON, 90, False, False
        ),
        'dress_shoes': CustomizationItem(
            'dress_shoes', 'Dress Shoes', CustomizationCategory.SHOES,
            '👞', 'Formal footwear', ItemRarity.RARE, 250, False, False
        ),
        'slippers': CustomizationItem(
            'slippers', 'Fuzzy Slippers', CustomizationCategory.SHOES,
            '🥿', 'Maximum comfort', ItemRarity.UNCOMMON, 60, False, False
        ),
        'rocket_boots': CustomizationItem(
            'rocket_boots', 'Rocket Boots', CustomizationCategory.SHOES,
            '🚀', 'Fly through the sky', ItemRarity.LEGENDARY, 2500, False, False
        ),
        
        # Accessories
        'sunglasses': CustomizationItem(
            'sunglasses', 'Cool Sunglasses', CustomizationCategory.ACCESSORY,
            '🕶️', 'Look cool always', ItemRarity.UNCOMMON, 80, False, False
        ),
        'bowtie': CustomizationItem(
            'bowtie', 'Fancy Bow Tie', CustomizationCategory.ACCESSORY,
            '🎀', 'Dapper accessory', ItemRarity.COMMON, 35, False, False
        ),
        'necklace': CustomizationItem(
            'necklace', 'Bamboo Necklace', CustomizationCategory.ACCESSORY,
            '📿', 'Natural jewelry', ItemRarity.RARE, 200, False, False
        ),
        'backpack': CustomizationItem(
            'backpack', 'Adventure Backpack', CustomizationCategory.ACCESSORY,
            '🎒', 'Carry all your bamboo', ItemRarity.UNCOMMON, 120, False, False
        ),
        'wings': CustomizationItem(
            'wings', 'Angel Wings', CustomizationCategory.ACCESSORY,
            '👼', 'Heavenly accessory', ItemRarity.LEGENDARY, 3000, False, False
        ),
    }
    
    def __init__(self, currency_manager: Optional[object] = None):
        """
        Initialize panda closet.
        
        Args:
            currency_manager: Currency system for purchases
        """
        self.items: Dict[str, CustomizationItem] = {}
        self.appearance = PandaAppearance()
        self.currency_manager = currency_manager
        self._initialize_items()
    
    def _initialize_items(self) -> None:
        """Initialize with default items."""
        for item_id, item in self.DEFAULT_ITEMS.items():
            # Create a copy to avoid shared state
            self.items[item_id] = CustomizationItem(
                id=item.id,
                name=item.name,
                category=item.category,
                emoji=item.emoji,
                description=item.description,
                rarity=item.rarity,
                cost=item.cost,
                unlocked=item.unlocked,
                equipped=item.equipped
            )
    
    def get_item(self, item_id: str) -> Optional[CustomizationItem]:
        """Get customization item by ID."""
        return self.items.get(item_id)
    
    def get_items_by_category(self, category: CustomizationCategory,
                             unlocked_only: bool = False) -> List[CustomizationItem]:
        """
        Get items in a specific category.
        
        Args:
            category: Item category
            unlocked_only: Only return unlocked items
            
        Returns:
            List of items
        """
        items = [item for item in self.items.values() if item.category == category]
        
        if unlocked_only:
            items = [item for item in items if item.unlocked]
        
        return sorted(items, key=lambda x: (x.rarity.value, x.name))
    
    def unlock_item(self, item_id: str) -> bool:
        """
        Unlock a customization item.
        
        Args:
            item_id: Item identifier
            
        Returns:
            True if unlocked successfully
        """
        item = self.items.get(item_id)
        if not item:
            logger.warning(f"Item not found: {item_id}")
            return False
        
        if item.unlocked:
            logger.debug(f"Item already unlocked: {item_id}")
            return False
        
        item.unlocked = True
        logger.info(f"Unlocked customization item: {item.name}")
        return True
    
    def purchase_item(self, item_id: str) -> bool:
        """
        Purchase and unlock a customization item.
        
        Args:
            item_id: Item identifier
            
        Returns:
            True if purchased successfully
        """
        item = self.items.get(item_id)
        if not item:
            logger.warning(f"Item not found: {item_id}")
            return False
        
        if item.unlocked:
            logger.debug(f"Item already unlocked: {item_id}")
            return False
        
        # Check if currency manager is available
        if not self.currency_manager:
            logger.warning("No currency manager available")
            return False
        
        # Check if player can afford it
        if not hasattr(self.currency_manager, 'get_balance'):
            logger.error("Currency manager missing get_balance method")
            return False
        
        current_balance = self.currency_manager.get_balance()
        if current_balance < item.cost:
            logger.warning(f"Insufficient funds: need {item.cost}, have {current_balance}")
            return False
        
        # Deduct cost and unlock
        if hasattr(self.currency_manager, 'spend'):
            if not self.currency_manager.spend(item.cost):
                return False
        
        item.unlocked = True
        logger.info(f"Purchased and unlocked: {item.name} for {item.cost} currency")
        return True
    
    def equip_item(self, item_id: str) -> bool:
        """
        Equip a customization item.
        
        Args:
            item_id: Item identifier
            
        Returns:
            True if equipped successfully
        """
        item = self.items.get(item_id)
        if not item:
            logger.warning(f"Item not found: {item_id}")
            return False
        
        if not item.unlocked:
            logger.warning(f"Item not unlocked: {item_id}")
            return False
        
        # Unequip current item in same category
        for other_item in self.items.values():
            if other_item.category == item.category and other_item.equipped:
                other_item.equipped = False
        
        # Equip new item
        item.equipped = True
        
        # Update appearance
        if item.category == CustomizationCategory.FUR_STYLE:
            self.appearance.fur_style = item_id
        elif item.category == CustomizationCategory.FUR_COLOR:
            self.appearance.fur_color = item_id
        elif item.category == CustomizationCategory.CLOTHING:
            self.appearance.clothing = item_id
        elif item.category == CustomizationCategory.HAT:
            self.appearance.hat = item_id
        elif item.category == CustomizationCategory.SHOES:
            self.appearance.shoes = item_id
        elif item.category == CustomizationCategory.ACCESSORY:
            # Accessories can have multiple
            if item_id not in self.appearance.accessories:
                self.appearance.accessories.append(item_id)
        
        logger.info(f"Equipped: {item.name}")
        return True
    
    def unequip_item(self, item_id: str) -> bool:
        """
        Unequip a customization item.
        
        Args:
            item_id: Item identifier
            
        Returns:
            True if unequipped successfully
        """
        item = self.items.get(item_id)
        if not item:
            return False
        
        if not item.equipped:
            return False
        
        item.equipped = False
        
        # Update appearance
        if item.category == CustomizationCategory.CLOTHING:
            self.appearance.clothing = None
        elif item.category == CustomizationCategory.HAT:
            self.appearance.hat = None
        elif item.category == CustomizationCategory.SHOES:
            self.appearance.shoes = None
        elif item.category == CustomizationCategory.ACCESSORY:
            if item_id in self.appearance.accessories:
                self.appearance.accessories.remove(item_id)
        
        logger.info(f"Unequipped: {item.name}")
        return True
    
    def get_current_appearance(self) -> PandaAppearance:
        """Get current panda appearance."""
        return self.appearance
    
    def get_equipped_items(self) -> List[CustomizationItem]:
        """Get all currently equipped items."""
        return [item for item in self.items.values() if item.equipped]
    
    def save_to_file(self, filepath: str) -> bool:
        """
        Save closet state to file.
        
        Args:
            filepath: Path to save file
            
        Returns:
            True if saved successfully
        """
        try:
            data = {
                'appearance': self.appearance.to_dict(),
                'unlocked_items': [
                    item_id for item_id, item in self.items.items() if item.unlocked
                ],
                'equipped_items': [
                    item_id for item_id, item in self.items.items() if item.equipped
                ]
            }
            
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved closet to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save closet: {e}")
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """
        Load closet state from file.
        
        Args:
            filepath: Path to load file
            
        Returns:
            True if loaded successfully
        """
        try:
            path = Path(filepath)
            if not path.exists():
                logger.warning(f"Closet file not found: {filepath}")
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load appearance
            self.appearance.from_dict(data.get('appearance', {}))
            
            # Unlock items
            for item_id in data.get('unlocked_items', []):
                if item_id in self.items:
                    self.items[item_id].unlocked = True
            
            # Equip items
            for item_id in data.get('equipped_items', []):
                if item_id in self.items:
                    self.items[item_id].equipped = True
            
            logger.info(f"Loaded closet from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load closet: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get closet statistics."""
        total_items = len(self.items)
        unlocked_items = sum(1 for item in self.items.values() if item.unlocked)
        equipped_items = sum(1 for item in self.items.values() if item.equipped)
        
        total_cost = sum(item.cost for item in self.items.values())
        spent = sum(item.cost for item in self.items.values() if item.unlocked)
        
        return {
            'total_items': total_items,
            'unlocked_items': unlocked_items,
            'equipped_items': equipped_items,
            'total_cost': total_cost,
            'spent': spent,
            'remaining_cost': total_cost - spent,
            'by_category': self._count_by_category(),
            'by_rarity': self._count_by_rarity()
        }
    
    def _count_by_category(self) -> Dict[str, Dict[str, int]]:
        """Count items by category."""
        counts = {}
        for category in CustomizationCategory:
            total = sum(1 for item in self.items.values() if item.category == category)
            unlocked = sum(1 for item in self.items.values() 
                          if item.category == category and item.unlocked)
            counts[category.value] = {
                'total': total,
                'unlocked': unlocked
            }
        return counts
    
    def _count_by_rarity(self) -> Dict[str, Dict[str, int]]:
        """Count items by rarity."""
        counts = {}
        for rarity in ItemRarity:
            total = sum(1 for item in self.items.values() if item.rarity == rarity)
            unlocked = sum(1 for item in self.items.values() 
                          if item.rarity == rarity and item.unlocked)
            counts[rarity.value] = {
                'total': total,
                'unlocked': unlocked
            }
        return counts
