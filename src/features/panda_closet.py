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


class ClothingSubCategory(Enum):
    """Subcategories for clothing items for better closet/shop organization."""
    SHIRT = "shirt"
    PANTS = "pants"
    JACKET = "jacket"
    DRESS = "dress"
    FULL_BODY = "full_body"
    OTHER = "other"


class AccessorySubCategory(Enum):
    """Subcategories for accessory items."""
    WATCH = "watch"
    BRACELET = "bracelet"
    TIE = "tie"
    BOW = "bow"
    NECKLACE = "necklace"
    SCARF = "scarf"
    GLASSES = "glasses"
    OTHER = "other"


# Mapping from clothing item IDs to their subcategory
CLOTHING_SUBCATEGORIES: Dict[str, 'ClothingSubCategory'] = {}


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
    clothing_type: str = ""  # One of: shirt, pants, jacket, dress, full_body, other


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

        # Fur Styles - Free (closet)
        'curly': CustomizationItem(
            'curly', 'Curly Panda', CustomizationCategory.FUR_STYLE,
            '🐼🌀', 'Playful curly fur', ItemRarity.COMMON, 0, True, False
        ),
        'wispy': CustomizationItem(
            'wispy', 'Wispy Panda', CustomizationCategory.FUR_STYLE,
            '🐼🌬️', 'Light and airy wispy fur', ItemRarity.COMMON, 0, True, False
        ),

        # Fur Styles - Shop
        'spiky': CustomizationItem(
            'spiky', 'Spiky Panda', CustomizationCategory.FUR_STYLE,
            '🐼⚡', 'Wild spiky fur', ItemRarity.UNCOMMON, 120, False, False
        ),
        'wavy': CustomizationItem(
            'wavy', 'Wavy Panda', CustomizationCategory.FUR_STYLE,
            '🐼🌊', 'Flowing wavy fur', ItemRarity.UNCOMMON, 130, False, False
        ),
        'shaggy': CustomizationItem(
            'shaggy', 'Shaggy Panda', CustomizationCategory.FUR_STYLE,
            '🐼🍃', 'Relaxed shaggy look', ItemRarity.COMMON, 80, False, False
        ),
        'velvet': CustomizationItem(
            'velvet', 'Velvet Panda', CustomizationCategory.FUR_STYLE,
            '🐼💎', 'Ultra smooth velvet fur', ItemRarity.RARE, 300, False, False
        ),
        'mohawk': CustomizationItem(
            'mohawk', 'Mohawk Panda', CustomizationCategory.FUR_STYLE,
            '🐼🤘', 'Punk rock mohawk style', ItemRarity.RARE, 350, False, False
        ),
        'braided': CustomizationItem(
            'braided', 'Braided Panda', CustomizationCategory.FUR_STYLE,
            '🐼🎀', 'Intricate braided fur', ItemRarity.RARE, 280, False, False
        ),
        'frosted': CustomizationItem(
            'frosted', 'Frosted Panda', CustomizationCategory.FUR_STYLE,
            '🐼❄️', 'Frost-tipped fur', ItemRarity.RARE, 320, False, False
        ),
        'crystalline': CustomizationItem(
            'crystalline', 'Crystalline Panda', CustomizationCategory.FUR_STYLE,
            '🐼💠', 'Crystal-like sparkling fur', ItemRarity.EPIC, 500, False, False
        ),
        'feathered': CustomizationItem(
            'feathered', 'Feathered Panda', CustomizationCategory.FUR_STYLE,
            '🐼🪶', 'Soft feathered texture', ItemRarity.UNCOMMON, 150, False, False
        ),
        'metallic': CustomizationItem(
            'metallic', 'Metallic Panda', CustomizationCategory.FUR_STYLE,
            '🐼🔩', 'Shiny metallic sheen', ItemRarity.RARE, 400, False, False
        ),
        'woolly': CustomizationItem(
            'woolly', 'Woolly Panda', CustomizationCategory.FUR_STYLE,
            '🐼🧶', 'Thick woolly fur', ItemRarity.UNCOMMON, 140, False, False
        ),
        'spotted': CustomizationItem(
            'spotted', 'Spotted Panda', CustomizationCategory.FUR_STYLE,
            '🐼🐆', 'Exotic spotted pattern', ItemRarity.RARE, 380, False, False
        ),
        'striped': CustomizationItem(
            'striped', 'Striped Panda', CustomizationCategory.FUR_STYLE,
            '🐼🦓', 'Bold striped pattern', ItemRarity.RARE, 360, False, False
        ),
        'tufted': CustomizationItem(
            'tufted', 'Tufted Panda', CustomizationCategory.FUR_STYLE,
            '🐼🌿', 'Charming fur tufts', ItemRarity.UNCOMMON, 160, False, False
        ),
        'silky': CustomizationItem(
            'silky', 'Silky Panda', CustomizationCategory.FUR_STYLE,
            '🐼🎗️', 'Silky smooth perfection', ItemRarity.RARE, 290, False, False
        ),
        'pixelated': CustomizationItem(
            'pixelated', 'Pixelated Panda', CustomizationCategory.FUR_STYLE,
            '🐼🎮', 'Retro pixel art style', ItemRarity.EPIC, 600, False, False
        ),
        'cosmic': CustomizationItem(
            'cosmic', 'Cosmic Panda', CustomizationCategory.FUR_STYLE,
            '🐼🌌', 'Swirling cosmic energy fur', ItemRarity.LEGENDARY, 1200, False, False
        ),
        'ember': CustomizationItem(
            'ember', 'Ember Panda', CustomizationCategory.FUR_STYLE,
            '🐼🔥', 'Glowing ember-like fur', ItemRarity.EPIC, 550, False, False
        ),
        'glacial': CustomizationItem(
            'glacial', 'Glacial Panda', CustomizationCategory.FUR_STYLE,
            '🐼🧊', 'Frozen glacial fur texture', ItemRarity.EPIC, 520, False, False
        ),
        'holographic': CustomizationItem(
            'holographic', 'Holographic Panda', CustomizationCategory.FUR_STYLE,
            '🐼✨', 'Color-shifting holographic', ItemRarity.LEGENDARY, 1500, False, False
        ),
        'plush': CustomizationItem(
            'plush', 'Plush Panda', CustomizationCategory.FUR_STYLE,
            '🐼🧸', 'Stuffed animal soft fur', ItemRarity.UNCOMMON, 110, False, False
        ),
        'windswept': CustomizationItem(
            'windswept', 'Windswept Panda', CustomizationCategory.FUR_STYLE,
            '🐼💨', 'Dramatically windblown look', ItemRarity.UNCOMMON, 170, False, False
        ),
        'mossy': CustomizationItem(
            'mossy', 'Mossy Panda', CustomizationCategory.FUR_STYLE,
            '🐼🌱', 'Nature-covered mossy fur', ItemRarity.RARE, 270, False, False
        ),
        'electric': CustomizationItem(
            'electric', 'Electric Panda', CustomizationCategory.FUR_STYLE,
            '🐼⚡', 'Crackling electric fur', ItemRarity.EPIC, 700, False, False
        ),

        # Fur Styles - Achievement Rewards
        'phoenix': CustomizationItem(
            'phoenix', 'Phoenix Panda', CustomizationCategory.FUR_STYLE,
            '🐼🔥', 'Reborn in fire phoenix fur', ItemRarity.LEGENDARY, 0, False, False
        ),
        'diamond': CustomizationItem(
            'diamond', 'Diamond Panda', CustomizationCategory.FUR_STYLE,
            '🐼💎', 'Rare diamond-encrusted fur', ItemRarity.LEGENDARY, 0, False, False
        ),
        'aurora': CustomizationItem(
            'aurora', 'Aurora Panda', CustomizationCategory.FUR_STYLE,
            '🐼🌌', 'Northern lights aurora fur', ItemRarity.EPIC, 0, False, False
        ),
        'sakura': CustomizationItem(
            'sakura', 'Sakura Panda', CustomizationCategory.FUR_STYLE,
            '🐼🌸', 'Cherry blossom petal fur', ItemRarity.RARE, 0, False, False
        ),
        'thunder': CustomizationItem(
            'thunder', 'Thunder Panda', CustomizationCategory.FUR_STYLE,
            '🐼⛈️', 'Storm-charged thunder fur', ItemRarity.EPIC, 0, False, False
        ),
        'starweave': CustomizationItem(
            'starweave', 'Starweave Panda', CustomizationCategory.FUR_STYLE,
            '🐼🌟', 'Woven from starlight', ItemRarity.LEGENDARY, 0, False, False
        ),
        'bamboo_spirit': CustomizationItem(
            'bamboo_spirit', 'Bamboo Spirit Panda', CustomizationCategory.FUR_STYLE,
            '🐼🎋', 'Ancient bamboo spirit fur', ItemRarity.EPIC, 0, False, False
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
        
        # Clothing — Shirts
        'tshirt': CustomizationItem(
            'tshirt', 'Bamboo T-Shirt', CustomizationCategory.CLOTHING,
            '👕', 'Casual bamboo tee', ItemRarity.COMMON, 25, False, False,
            clothing_type='shirt'
        ),
        # Clothing — Jackets
        'hoodie': CustomizationItem(
            'hoodie', 'Cozy Hoodie', CustomizationCategory.CLOTHING,
            '🧥', 'Warm and comfy', ItemRarity.UNCOMMON, 75, False, False,
            clothing_type='jacket'
        ),
        # Clothing — Full Body
        'suit': CustomizationItem(
            'suit', 'Business Suit', CustomizationCategory.CLOTHING,
            '🤵', 'Professional attire', ItemRarity.RARE, 300, False, False,
            clothing_type='full_body'
        ),
        'kimono': CustomizationItem(
            'kimono', 'Traditional Kimono', CustomizationCategory.CLOTHING,
            '👘', 'Elegant traditional wear', ItemRarity.EPIC, 600, False, False,
            clothing_type='dress'
        ),
        'superhero': CustomizationItem(
            'superhero', 'Superhero Costume', CustomizationCategory.CLOTHING,
            '🦸', 'Save the world in style', ItemRarity.LEGENDARY, 2000, False, False,
            clothing_type='full_body'
        ),

        # Panda Outfits (shop costumes) — Full Body
        'casual': CustomizationItem(
            'casual', 'Casual Panda', CustomizationCategory.CLOTHING,
            '👕', 'Comfy hoodie for your panda pal', ItemRarity.COMMON, 100, False, False,
            clothing_type='full_body'
        ),
        'ninja': CustomizationItem(
            'ninja', 'Ninja Panda', CustomizationCategory.CLOTHING,
            '🥷', 'Stealth mode activated!', ItemRarity.UNCOMMON, 250, False, False,
            clothing_type='full_body'
        ),
        'wizard': CustomizationItem(
            'wizard', 'Wizard Panda', CustomizationCategory.CLOTHING,
            '🧙', 'Magical texture sorting powers', ItemRarity.RARE, 500, False, False,
            clothing_type='full_body'
        ),
        'pirate': CustomizationItem(
            'pirate', 'Pirate Panda', CustomizationCategory.CLOTHING,
            '🏴‍☠️', 'Arr, matey!', ItemRarity.UNCOMMON, 300, False, False,
            clothing_type='full_body'
        ),
        'astronaut': CustomizationItem(
            'astronaut', 'Astronaut Panda', CustomizationCategory.CLOTHING,
            '🚀', 'To infinity and beyond!', ItemRarity.EPIC, 1000, False, False,
            clothing_type='full_body'
        ),
        'chef': CustomizationItem(
            'chef', 'Chef Panda', CustomizationCategory.CLOTHING,
            '👨‍🍳', 'Cooking up some sorted textures!', ItemRarity.UNCOMMON, 200, False, False,
            clothing_type='full_body'
        ),
        'detective': CustomizationItem(
            'detective', 'Detective Panda', CustomizationCategory.CLOTHING,
            '🕵️', 'Investigating texture mysteries', ItemRarity.RARE, 400, False, False,
            clothing_type='full_body'
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
        'flower_crown': CustomizationItem(
            'flower_crown', 'Flower Crown', CustomizationCategory.HAT,
            '🌸', 'Spring vibes all year round', ItemRarity.COMMON, 100, False, False
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

        # Additional Hats
        'chef_hat': CustomizationItem(
            'chef_hat', 'Chef Hat', CustomizationCategory.HAT,
            '👨‍🍳', 'Ready to cook up sorted textures', ItemRarity.UNCOMMON, 120, False, False
        ),
        'cowboy_hat': CustomizationItem(
            'cowboy_hat', 'Cowboy Hat', CustomizationCategory.HAT,
            '🤠', 'Yeehaw partner!', ItemRarity.RARE, 200, False, False
        ),
        'beanie': CustomizationItem(
            'beanie', 'Cozy Beanie', CustomizationCategory.HAT,
            '🧢', 'Warm and casual', ItemRarity.COMMON, 40, False, False
        ),

        # Additional Clothing — Jackets
        'raincoat': CustomizationItem(
            'raincoat', 'Raincoat', CustomizationCategory.CLOTHING,
            '🧥', 'Stay dry and sorted', ItemRarity.UNCOMMON, 100, False, False,
            clothing_type='jacket'
        ),
        # Additional Clothing — Pants
        'overalls': CustomizationItem(
            'overalls', 'Denim Overalls', CustomizationCategory.CLOTHING,
            '👖', 'Working panda attire', ItemRarity.COMMON, 50, False, False,
            clothing_type='pants'
        ),
        # Additional Clothing — Shirts
        'sweater': CustomizationItem(
            'sweater', 'Knit Sweater', CustomizationCategory.CLOTHING,
            '👕', 'Cozy and warm', ItemRarity.COMMON, 60, False, False,
            clothing_type='shirt'
        ),
        # Additional Clothing — Dresses
        'toga': CustomizationItem(
            'toga', 'Greek Toga', CustomizationCategory.CLOTHING,
            '👘', 'Ancient Greek wrap', ItemRarity.RARE, 250, False, False,
            clothing_type='dress'
        ),
        # Additional Clothing — Full Body
        'spacesuit': CustomizationItem(
            'spacesuit', 'Space Suit', CustomizationCategory.CLOTHING,
            '🚀', 'Ready for launch', ItemRarity.EPIC, 700, False, False,
            clothing_type='full_body'
        ),
        # Additional Clothing — Shirts
        'jersey': CustomizationItem(
            'jersey', 'Sports Jersey', CustomizationCategory.CLOTHING,
            '👕', 'Go team panda!', ItemRarity.UNCOMMON, 150, False, False,
            clothing_type='shirt'
        ),

        # Additional Accessories
        'scarf': CustomizationItem(
            'scarf', 'Bamboo Scarf', CustomizationCategory.ACCESSORY,
            '🧣', 'Stay warm and stylish', ItemRarity.COMMON, 45, False, False
        ),
        'headphones': CustomizationItem(
            'headphones', 'DJ Headphones', CustomizationCategory.ACCESSORY,
            '🎧', 'Sorting to the beat', ItemRarity.UNCOMMON, 100, False, False
        ),
        'monocle': CustomizationItem(
            'monocle', 'Distinguished Monocle', CustomizationCategory.ACCESSORY,
            '🧐', 'Inspect textures with class', ItemRarity.RARE, 180, False, False
        ),
        'flower': CustomizationItem(
            'flower', 'Bamboo Flower', CustomizationCategory.ACCESSORY,
            '🌸', 'Nature-loving panda', ItemRarity.COMMON, 30, False, False
        ),

        # Additional Shoes
        'sandals': CustomizationItem(
            'sandals', 'Beach Sandals', CustomizationCategory.SHOES,
            '🩴', 'Casual beach vibes', ItemRarity.COMMON, 35, False, False
        ),
        'high_heels': CustomizationItem(
            'high_heels', 'Fancy Heels', CustomizationCategory.SHOES,
            '👠', 'Glamorous panda', ItemRarity.RARE, 200, False, False
        ),
        'rain_boots': CustomizationItem(
            'rain_boots', 'Rain Boots', CustomizationCategory.SHOES,
            '🥾', 'Splash through puddles', ItemRarity.UNCOMMON, 70, False, False
        ),

        # Shop-synced Accessories
        'bow_tie': CustomizationItem(
            'bow_tie', 'Bow Tie', CustomizationCategory.ACCESSORY,
            '🎀', 'A classic bow tie', ItemRarity.COMMON, 35, False, False
        ),
        'cape': CustomizationItem(
            'cape', 'Cape', CustomizationCategory.ACCESSORY,
            '🦸', 'Swish and swoosh', ItemRarity.UNCOMMON, 100, False, False
        ),
        'watch': CustomizationItem(
            'watch', 'Wrist Watch', CustomizationCategory.ACCESSORY,
            '⌚', 'Always on time', ItemRarity.UNCOMMON, 90, False, False
        ),

        # Shop-synced Clothing
        'dress': CustomizationItem(
            'dress', 'Elegant Dress', CustomizationCategory.CLOTHING,
            '👗', 'Dressed to impress', ItemRarity.RARE, 200, False, False,
            clothing_type='dress'
        ),
        'lab_coat': CustomizationItem(
            'lab_coat', 'Lab Coat', CustomizationCategory.CLOTHING,
            '🥼', 'Science panda reporting', ItemRarity.UNCOMMON, 120, False, False,
            clothing_type='jacket'
        ),
        'leather_jacket': CustomizationItem(
            'leather_jacket', 'Leather Jacket', CustomizationCategory.CLOTHING,
            '🧥', 'Cool and rebellious', ItemRarity.RARE, 250, False, False,
            clothing_type='jacket'
        ),
        'pajamas': CustomizationItem(
            'pajamas', 'Cozy Pajamas', CustomizationCategory.CLOTHING,
            '👔', 'Sleepy panda vibes', ItemRarity.COMMON, 50, False, False,
            clothing_type='full_body'
        ),
        'sports_jersey': CustomizationItem(
            'sports_jersey', 'Basketball Jersey', CustomizationCategory.CLOTHING,
            '🏀', 'Game day ready', ItemRarity.UNCOMMON, 150, False, False,
            clothing_type='shirt'
        ),
        'superhero_cape': CustomizationItem(
            'superhero_cape', 'Superhero Cape', CustomizationCategory.CLOTHING,
            '🦸‍♂️', 'Up, up, and away!', ItemRarity.EPIC, 500, False, False,
            clothing_type='jacket'
        ),
        'tuxedo': CustomizationItem(
            'tuxedo', 'Tuxedo', CustomizationCategory.CLOTHING,
            '🤵', 'Black tie affair', ItemRarity.RARE, 300, False, False,
            clothing_type='full_body'
        ),
        'vest': CustomizationItem(
            'vest', 'Stylish Vest', CustomizationCategory.CLOTHING,
            '🦺', 'Layered look', ItemRarity.COMMON, 60, False, False,
            clothing_type='shirt'
        ),

        # Additional Clothing — Color Shirts
        'red_shirt': CustomizationItem(
            'red_shirt', 'Red T-Shirt', CustomizationCategory.CLOTHING,
            '👕', 'A bright red casual tee', ItemRarity.COMMON, 30, False, False,
            clothing_type='shirt'
        ),
        'blue_shirt': CustomizationItem(
            'blue_shirt', 'Blue T-Shirt', CustomizationCategory.CLOTHING,
            '👕', 'A cool blue casual tee', ItemRarity.COMMON, 30, False, False,
            clothing_type='shirt'
        ),
        'green_shirt': CustomizationItem(
            'green_shirt', 'Green T-Shirt', CustomizationCategory.CLOTHING,
            '👕', 'A fresh green casual tee', ItemRarity.COMMON, 30, False, False,
            clothing_type='shirt'
        ),
        'yellow_polo': CustomizationItem(
            'yellow_polo', 'Yellow Polo Shirt', CustomizationCategory.CLOTHING,
            '👕', 'A sunny yellow collared polo', ItemRarity.UNCOMMON, 55, False, False,
            clothing_type='shirt'
        ),
        'striped_shirt': CustomizationItem(
            'striped_shirt', 'Striped Shirt', CustomizationCategory.CLOTHING,
            '👕', 'A classic striped button-up', ItemRarity.UNCOMMON, 65, False, False,
            clothing_type='shirt'
        ),
        'hawaiian_shirt': CustomizationItem(
            'hawaiian_shirt', 'Hawaiian Shirt', CustomizationCategory.CLOTHING,
            '🌺', 'A tropical floral shirt', ItemRarity.UNCOMMON, 70, False, False,
            clothing_type='shirt'
        ),
        'tank_top': CustomizationItem(
            'tank_top', 'White Tank Top', CustomizationCategory.CLOTHING,
            '👕', 'A sleeveless white tank top', ItemRarity.COMMON, 20, False, False,
            clothing_type='shirt'
        ),

        # Additional Clothing — Pants
        'blue_jeans': CustomizationItem(
            'blue_jeans', 'Blue Jeans', CustomizationCategory.CLOTHING,
            '👖', 'Classic blue denim jeans', ItemRarity.COMMON, 40, False, False,
            clothing_type='pants'
        ),
        'black_pants': CustomizationItem(
            'black_pants', 'Black Pants', CustomizationCategory.CLOTHING,
            '👖', 'Sleek black trousers', ItemRarity.COMMON, 45, False, False,
            clothing_type='pants'
        ),
        'cargo_pants': CustomizationItem(
            'cargo_pants', 'Cargo Pants', CustomizationCategory.CLOTHING,
            '👖', 'Rugged cargo pants with pockets', ItemRarity.UNCOMMON, 55, False, False,
            clothing_type='pants'
        ),
        'shorts': CustomizationItem(
            'shorts', 'Khaki Shorts', CustomizationCategory.CLOTHING,
            '🩳', 'Comfortable khaki shorts', ItemRarity.COMMON, 30, False, False,
            clothing_type='pants'
        ),
        'sweatpants': CustomizationItem(
            'sweatpants', 'Grey Sweatpants', CustomizationCategory.CLOTHING,
            '👖', 'Cozy grey sweatpants', ItemRarity.COMMON, 35, False, False,
            clothing_type='pants'
        ),

        # Additional Clothing — Jackets
        'denim_jacket': CustomizationItem(
            'denim_jacket', 'Denim Jacket', CustomizationCategory.CLOTHING,
            '🧥', 'A classic blue denim jacket', ItemRarity.UNCOMMON, 110, False, False,
            clothing_type='jacket'
        ),
        'bomber_jacket': CustomizationItem(
            'bomber_jacket', 'Bomber Jacket', CustomizationCategory.CLOTHING,
            '🧥', 'A sleek green bomber jacket', ItemRarity.RARE, 180, False, False,
            clothing_type='jacket'
        ),
        'puffer_jacket': CustomizationItem(
            'puffer_jacket', 'Puffer Jacket', CustomizationCategory.CLOTHING,
            '🧥', 'A warm puffy winter jacket', ItemRarity.UNCOMMON, 130, False, False,
            clothing_type='jacket'
        ),
        'varsity_jacket': CustomizationItem(
            'varsity_jacket', 'Varsity Jacket', CustomizationCategory.CLOTHING,
            '🧥', 'A red and white letterman jacket', ItemRarity.RARE, 200, False, False,
            clothing_type='jacket'
        ),
        'windbreaker': CustomizationItem(
            'windbreaker', 'Windbreaker', CustomizationCategory.CLOTHING,
            '🧥', 'A light neon windbreaker', ItemRarity.UNCOMMON, 90, False, False,
            clothing_type='jacket'
        ),

        # Additional Clothing — Dresses
        'summer_dress': CustomizationItem(
            'summer_dress', 'Summer Dress', CustomizationCategory.CLOTHING,
            '👗', 'A flowy floral summer dress', ItemRarity.UNCOMMON, 85, False, False,
            clothing_type='dress'
        ),
        'evening_gown': CustomizationItem(
            'evening_gown', 'Evening Gown', CustomizationCategory.CLOTHING,
            '👗', 'An elegant black evening gown', ItemRarity.EPIC, 400, False, False,
            clothing_type='dress'
        ),

        # Additional Clothing — Full Body
        'tracksuit': CustomizationItem(
            'tracksuit', 'Tracksuit', CustomizationCategory.CLOTHING,
            '🏃', 'A sporty matching tracksuit', ItemRarity.UNCOMMON, 100, False, False,
            clothing_type='full_body'
        ),
        'onesie': CustomizationItem(
            'onesie', 'Panda Onesie', CustomizationCategory.CLOTHING,
            '🐼', 'A cute panda-print onesie', ItemRarity.RARE, 150, False, False,
            clothing_type='full_body'
        ),
        'jumpsuit': CustomizationItem(
            'jumpsuit', 'Orange Jumpsuit', CustomizationCategory.CLOTHING,
            '👷', 'A bright orange utility jumpsuit', ItemRarity.UNCOMMON, 80, False, False,
            clothing_type='full_body'
        ),

        # New Fur Colors - Free
        'silver': CustomizationItem(
            'silver', 'Silver Panda', CustomizationCategory.FUR_COLOR,
            '⬜', 'Shimmering silver fur', ItemRarity.COMMON, 0, True, False
        ),
        'cinnamon': CustomizationItem(
            'cinnamon', 'Cinnamon Panda', CustomizationCategory.FUR_COLOR,
            '🟫', 'Warm cinnamon brown', ItemRarity.COMMON, 0, True, False
        ),
        'midnight': CustomizationItem(
            'midnight', 'Midnight Panda', CustomizationCategory.FUR_COLOR,
            '🌑', 'Deep midnight blue-black', ItemRarity.COMMON, 0, True, False
        ),
        # New Fur Colors - Achievement Rewards
        'rose_gold': CustomizationItem(
            'rose_gold', 'Rose Gold Panda', CustomizationCategory.FUR_COLOR,
            '🌹', 'Elegant rose gold', ItemRarity.RARE, 0, False, False
        ),
        'lavender': CustomizationItem(
            'lavender', 'Lavender Panda', CustomizationCategory.FUR_COLOR,
            '💜', 'Soft lavender fur', ItemRarity.UNCOMMON, 0, False, False
        ),
        'arctic_white': CustomizationItem(
            'arctic_white', 'Arctic White Panda', CustomizationCategory.FUR_COLOR,
            '❄️', 'Pure arctic white', ItemRarity.RARE, 0, False, False
        ),
        'copper': CustomizationItem(
            'copper', 'Copper Panda', CustomizationCategory.FUR_COLOR,
            '🟠', 'Warm copper tones', ItemRarity.UNCOMMON, 0, False, False
        ),
        'emerald': CustomizationItem(
            'emerald', 'Emerald Panda', CustomizationCategory.FUR_COLOR,
            '💚', 'Jewel-toned emerald green', ItemRarity.EPIC, 0, False, False
        ),
        # New Fur Colors - Shop
        'cherry_blossom': CustomizationItem(
            'cherry_blossom', 'Cherry Blossom Panda', CustomizationCategory.FUR_COLOR,
            '🌸', 'Pink cherry blossom fur', ItemRarity.RARE, 300, False, False
        ),
        'ocean_blue': CustomizationItem(
            'ocean_blue', 'Ocean Blue Panda', CustomizationCategory.FUR_COLOR,
            '🌊', 'Deep ocean blue', ItemRarity.RARE, 350, False, False
        ),
        'sunset_orange': CustomizationItem(
            'sunset_orange', 'Sunset Orange Panda', CustomizationCategory.FUR_COLOR,
            '🌅', 'Warm sunset orange', ItemRarity.UNCOMMON, 200, False, False
        ),
        'neon_green': CustomizationItem(
            'neon_green', 'Neon Green Panda', CustomizationCategory.FUR_COLOR,
            '💚', 'Electric neon green', ItemRarity.RARE, 400, False, False
        ),
        'ice_crystal': CustomizationItem(
            'ice_crystal', 'Ice Crystal Panda', CustomizationCategory.FUR_COLOR,
            '🧊', 'Translucent ice blue', ItemRarity.EPIC, 600, False, False
        ),
        'volcanic': CustomizationItem(
            'volcanic', 'Volcanic Panda', CustomizationCategory.FUR_COLOR,
            '🌋', 'Fiery volcanic red-orange', ItemRarity.EPIC, 700, False, False
        ),
        'starlight': CustomizationItem(
            'starlight', 'Starlight Panda', CustomizationCategory.FUR_COLOR,
            '⭐', 'Twinkling starlight white', ItemRarity.LEGENDARY, 1200, False, False
        ),
        'shadow': CustomizationItem(
            'shadow', 'Shadow Panda', CustomizationCategory.FUR_COLOR,
            '🖤', 'Deep shadow black', ItemRarity.RARE, 350, False, False
        ),
        'cotton_candy': CustomizationItem(
            'cotton_candy', 'Cotton Candy Panda', CustomizationCategory.FUR_COLOR,
            '🍬', 'Pastel cotton candy pink and blue', ItemRarity.EPIC, 550, False, False
        ),
        'phantom': CustomizationItem(
            'phantom', 'Phantom Panda', CustomizationCategory.FUR_COLOR,
            '👻', 'Ghostly translucent white', ItemRarity.LEGENDARY, 1800, False, False
        ),

        # New Hats - Free
        'bamboo_hat': CustomizationItem(
            'bamboo_hat', 'Bamboo Hat', CustomizationCategory.HAT,
            '🎍', 'Traditional bamboo hat', ItemRarity.COMMON, 0, True, False
        ),
        'headband': CustomizationItem(
            'headband', 'Sports Headband', CustomizationCategory.HAT,
            '🏋️', 'Athletic headband', ItemRarity.COMMON, 0, True, False
        ),
        'flower_crown_hat': CustomizationItem(
            'flower_crown_hat', 'Flower Crown', CustomizationCategory.HAT,
            '🌺', 'Beautiful flower crown', ItemRarity.COMMON, 0, True, False
        ),
        # New Hats - Achievement Rewards
        'pirate_hat': CustomizationItem(
            'pirate_hat', 'Pirate Hat', CustomizationCategory.HAT,
            '🏴‍☠️', 'Arr! A classic pirate hat', ItemRarity.RARE, 0, False, False
        ),
        'viking_helmet': CustomizationItem(
            'viking_helmet', 'Viking Helmet', CustomizationCategory.HAT,
            '⚔️', 'Nordic warrior helmet', ItemRarity.RARE, 0, False, False
        ),
        'halo': CustomizationItem(
            'halo', 'Angel Halo', CustomizationCategory.HAT,
            '😇', 'Glowing golden halo', ItemRarity.EPIC, 0, False, False
        ),
        'detective_hat': CustomizationItem(
            'detective_hat', 'Detective Hat', CustomizationCategory.HAT,
            '🕵️', 'Sherlock-style deerstalker', ItemRarity.UNCOMMON, 0, False, False
        ),
        'ninja_mask': CustomizationItem(
            'ninja_mask', 'Ninja Mask', CustomizationCategory.HAT,
            '🥷', 'Stealthy ninja mask', ItemRarity.RARE, 0, False, False
        ),
        # New Hats - Shop
        'space_helmet': CustomizationItem(
            'space_helmet', 'Space Helmet', CustomizationCategory.HAT,
            '🪐', 'Astronaut bubble helmet', ItemRarity.EPIC, 500, False, False
        ),
        'samurai_helmet': CustomizationItem(
            'samurai_helmet', 'Samurai Helmet', CustomizationCategory.HAT,
            '⛩️', 'Ancient samurai kabuto', ItemRarity.EPIC, 600, False, False
        ),
        'propeller_hat': CustomizationItem(
            'propeller_hat', 'Propeller Hat', CustomizationCategory.HAT,
            '🌀', 'Fun spinning propeller', ItemRarity.UNCOMMON, 150, False, False
        ),
        'beret': CustomizationItem(
            'beret', 'Artist Beret', CustomizationCategory.HAT,
            '🎨', 'French artist beret', ItemRarity.UNCOMMON, 120, False, False
        ),
        'sombrero': CustomizationItem(
            'sombrero', 'Sombrero', CustomizationCategory.HAT,
            '🌮', 'Festive wide-brim sombrero', ItemRarity.RARE, 250, False, False
        ),
        'firefighter_hat': CustomizationItem(
            'firefighter_hat', 'Firefighter Helmet', CustomizationCategory.HAT,
            '🚒', 'Brave firefighter helmet', ItemRarity.RARE, 300, False, False
        ),
        'graduation_cap': CustomizationItem(
            'graduation_cap', 'Graduation Cap', CustomizationCategory.HAT,
            '🎓', 'Academic mortarboard', ItemRarity.UNCOMMON, 180, False, False
        ),
        'tiara': CustomizationItem(
            'tiara', 'Princess Tiara', CustomizationCategory.HAT,
            '👸', 'Sparkling princess tiara', ItemRarity.EPIC, 450, False, False
        ),
        'straw_hat': CustomizationItem(
            'straw_hat', 'Straw Hat', CustomizationCategory.HAT,
            '🌾', 'Simple straw hat', ItemRarity.COMMON, 50, False, False
        ),
        'ice_crown': CustomizationItem(
            'ice_crown', 'Ice Crown', CustomizationCategory.HAT,
            '❄️', 'Frozen crystal crown', ItemRarity.LEGENDARY, 1500, False, False
        ),

        # New Shoes - Free
        'bamboo_sandals': CustomizationItem(
            'bamboo_sandals', 'Bamboo Sandals', CustomizationCategory.SHOES,
            '🩴', 'Traditional bamboo sandals', ItemRarity.COMMON, 0, True, False
        ),
        'running_shoes': CustomizationItem(
            'running_shoes', 'Running Shoes', CustomizationCategory.SHOES,
            '🏃', 'Lightweight running shoes', ItemRarity.COMMON, 0, True, False
        ),
        'flip_flops': CustomizationItem(
            'flip_flops', 'Panda Flip Flops', CustomizationCategory.SHOES,
            '🐾', 'Comfy panda flip flops', ItemRarity.COMMON, 0, True, False
        ),
        # New Shoes - Achievement Rewards
        'ice_skates': CustomizationItem(
            'ice_skates', 'Ice Skates', CustomizationCategory.SHOES,
            '⛸️', 'Graceful ice skates', ItemRarity.RARE, 0, False, False
        ),
        'roller_skates': CustomizationItem(
            'roller_skates', 'Roller Skates', CustomizationCategory.SHOES,
            '🛼', 'Retro roller skates', ItemRarity.UNCOMMON, 0, False, False
        ),
        'ninja_tabi': CustomizationItem(
            'ninja_tabi', 'Ninja Tabi', CustomizationCategory.SHOES,
            '🥷', 'Silent ninja footwear', ItemRarity.RARE, 0, False, False
        ),
        'hiking_boots_adv': CustomizationItem(
            'hiking_boots_adv', 'Mountain Boots', CustomizationCategory.SHOES,
            '🏔️', 'Rugged mountain hiking boots', ItemRarity.UNCOMMON, 0, False, False
        ),
        'golden_shoes': CustomizationItem(
            'golden_shoes', 'Golden Shoes', CustomizationCategory.SHOES,
            '✨', 'Dazzling golden shoes', ItemRarity.EPIC, 0, False, False
        ),
        # New Shoes - Shop
        'cowboy_boots': CustomizationItem(
            'cowboy_boots', 'Cowboy Boots', CustomizationCategory.SHOES,
            '🤠', 'Western cowboy boots', ItemRarity.UNCOMMON, 120, False, False
        ),
        'ballet_shoes': CustomizationItem(
            'ballet_shoes', 'Ballet Slippers', CustomizationCategory.SHOES,
            '🩰', 'Elegant ballet slippers', ItemRarity.RARE, 250, False, False
        ),
        'moon_boots': CustomizationItem(
            'moon_boots', 'Moon Boots', CustomizationCategory.SHOES,
            '🌙', 'Anti-gravity moon boots', ItemRarity.EPIC, 500, False, False
        ),
        'platform_shoes': CustomizationItem(
            'platform_shoes', 'Platform Shoes', CustomizationCategory.SHOES,
            '📐', 'Groovy platform shoes', ItemRarity.UNCOMMON, 150, False, False
        ),
        'ski_boots': CustomizationItem(
            'ski_boots', 'Ski Boots', CustomizationCategory.SHOES,
            '⛷️', 'Mountain ski boots', ItemRarity.RARE, 280, False, False
        ),
        'glass_slippers': CustomizationItem(
            'glass_slippers', 'Glass Slippers', CustomizationCategory.SHOES,
            '💎', 'Fairy tale glass slippers', ItemRarity.EPIC, 600, False, False
        ),
        'steel_boots': CustomizationItem(
            'steel_boots', 'Steel Boots', CustomizationCategory.SHOES,
            '🛡️', 'Heavy armored steel boots', ItemRarity.RARE, 350, False, False
        ),
        'neon_kicks': CustomizationItem(
            'neon_kicks', 'Neon Kicks', CustomizationCategory.SHOES,
            '💡', 'Light-up neon sneakers', ItemRarity.UNCOMMON, 180, False, False
        ),
        'bunny_slippers_new': CustomizationItem(
            'bunny_slippers_new', 'Bunny Slippers', CustomizationCategory.SHOES,
            '🐰', 'Adorable bunny slippers', ItemRarity.COMMON, 60, False, False
        ),
        'lava_boots': CustomizationItem(
            'lava_boots', 'Lava Boots', CustomizationCategory.SHOES,
            '🔥', 'Fireproof lava walking boots', ItemRarity.LEGENDARY, 1200, False, False
        ),

        # New Accessories - Free
        'bamboo_bracelet': CustomizationItem(
            'bamboo_bracelet', 'Bamboo Bracelet', CustomizationCategory.ACCESSORY,
            '🎋', 'Simple bamboo bracelet', ItemRarity.COMMON, 0, True, False
        ),
        'panda_pin': CustomizationItem(
            'panda_pin', 'Panda Pin', CustomizationCategory.ACCESSORY,
            '🐼', 'Cute panda lapel pin', ItemRarity.COMMON, 0, True, False
        ),
        'friendship_band': CustomizationItem(
            'friendship_band', 'Friendship Band', CustomizationCategory.ACCESSORY,
            '🤝', 'Woven friendship bracelet', ItemRarity.COMMON, 0, True, False
        ),
        # New Accessories - Achievement Rewards
        'medal_of_honor': CustomizationItem(
            'medal_of_honor', 'Medal of Honor', CustomizationCategory.ACCESSORY,
            '🎖️', 'Distinguished service medal', ItemRarity.EPIC, 0, False, False
        ),
        'lucky_charm_acc': CustomizationItem(
            'lucky_charm_acc', 'Lucky Clover', CustomizationCategory.ACCESSORY,
            '🍀', 'Four-leaf clover charm', ItemRarity.UNCOMMON, 0, False, False
        ),
        'crystal_pendant': CustomizationItem(
            'crystal_pendant', 'Crystal Pendant', CustomizationCategory.ACCESSORY,
            '💎', 'Sparkling crystal pendant', ItemRarity.RARE, 0, False, False
        ),
        'ninja_star_acc': CustomizationItem(
            'ninja_star_acc', 'Ninja Star', CustomizationCategory.ACCESSORY,
            '⭐', 'Decorative shuriken pendant', ItemRarity.RARE, 0, False, False
        ),
        'golden_bell': CustomizationItem(
            'golden_bell', 'Golden Bell', CustomizationCategory.ACCESSORY,
            '🔔', 'Jingling golden bell', ItemRarity.UNCOMMON, 0, False, False
        ),
        # New Accessories - Shop
        'diamond_ring': CustomizationItem(
            'diamond_ring', 'Diamond Ring', CustomizationCategory.ACCESSORY,
            '💍', 'Sparkly diamond ring', ItemRarity.EPIC, 500, False, False
        ),
        'feather_boa': CustomizationItem(
            'feather_boa', 'Feather Boa', CustomizationCategory.ACCESSORY,
            '🪶', 'Glamorous feather boa', ItemRarity.RARE, 250, False, False
        ),
        'pocket_watch_acc': CustomizationItem(
            'pocket_watch_acc', 'Pocket Watch', CustomizationCategory.ACCESSORY,
            '🕰️', 'Antique pocket watch', ItemRarity.RARE, 280, False, False
        ),
        'magic_wand': CustomizationItem(
            'magic_wand', 'Magic Wand', CustomizationCategory.ACCESSORY,
            '🪄', 'Sparkly magic wand', ItemRarity.EPIC, 450, False, False
        ),
        'pearl_necklace': CustomizationItem(
            'pearl_necklace', 'Pearl Necklace', CustomizationCategory.ACCESSORY,
            '🦪', 'Elegant pearl necklace', ItemRarity.RARE, 300, False, False
        ),
        'bandana': CustomizationItem(
            'bandana', 'Cool Bandana', CustomizationCategory.ACCESSORY,
            '🏴', 'Stylish bandana', ItemRarity.UNCOMMON, 100, False, False
        ),
        'compass': CustomizationItem(
            'compass', 'Golden Compass', CustomizationCategory.ACCESSORY,
            '🧭', 'Adventure compass', ItemRarity.UNCOMMON, 130, False, False
        ),
        'camera': CustomizationItem(
            'camera', 'Polaroid Camera', CustomizationCategory.ACCESSORY,
            '📸', 'Retro instant camera', ItemRarity.RARE, 220, False, False
        ),
        'telescope_acc': CustomizationItem(
            'telescope_acc', 'Mini Telescope', CustomizationCategory.ACCESSORY,
            '🔭', 'Tiny telescope monocle', ItemRarity.RARE, 350, False, False
        ),
        'phoenix_feather': CustomizationItem(
            'phoenix_feather', 'Phoenix Feather', CustomizationCategory.ACCESSORY,
            '🔥', 'Legendary phoenix tail feather', ItemRarity.LEGENDARY, 1500, False, False
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
                equipped=item.equipped,
                clothing_type=item.clothing_type
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

    def get_clothing_by_subcategory(self, clothing_type: str,
                                     unlocked_only: bool = False) -> List[CustomizationItem]:
        """Get clothing items filtered by subcategory (shirt, pants, jacket, etc.).

        Args:
            clothing_type: One of 'shirt', 'pants', 'jacket', 'dress', 'full_body', 'other'
            unlocked_only: Only return unlocked items

        Returns:
            List of matching clothing items
        """
        items = [
            item for item in self.items.values()
            if item.category == CustomizationCategory.CLOTHING
            and (item.clothing_type or 'other') == clothing_type
        ]
        if unlocked_only:
            items = [item for item in items if item.unlocked]
        return sorted(items, key=lambda x: (x.rarity.value, x.name))
    
    # Prefixes to strip when resolving shop unlockable_ids to closet item keys
    SHOP_ID_PREFIXES = ['closet_', 'clothes_', 'panda_outfit_', 'acc_']

    def resolve_shop_item_id(self, shop_unlockable_id: str) -> Optional[str]:
        """
        Resolve a shop item's unlockable_id to a closet item key.

        Tries direct match first, then strips known prefixes.

        Args:
            shop_unlockable_id: The unlockable_id from the shop item

        Returns:
            Matching closet item key or None
        """
        # Direct match
        if shop_unlockable_id in self.items:
            return shop_unlockable_id

        # Try stripping prefixes
        for prefix in self.SHOP_ID_PREFIXES:
            if shop_unlockable_id.startswith(prefix):
                stripped = shop_unlockable_id[len(prefix):]
                if stripped in self.items:
                    return stripped

        return None

    def unlock_item(self, item_id: str) -> bool:
        """
        Unlock a customization item.
        
        Tries direct ID match first, then resolves shop unlockable_id prefixes.
        
        Args:
            item_id: Item identifier (closet key or shop unlockable_id)
            
        Returns:
            True if unlocked successfully
        """
        resolved = self.resolve_shop_item_id(item_id)
        if not resolved:
            logger.warning(f"Item not found: {item_id}")
            return False
        
        item = self.items[resolved]
        if item.unlocked:
            logger.debug(f"Item already unlocked: {resolved}")
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
        if item.category == CustomizationCategory.FUR_STYLE:
            self.appearance.fur_style = "classic"
        elif item.category == CustomizationCategory.FUR_COLOR:
            self.appearance.fur_color = "black_white"
        elif item.category == CustomizationCategory.CLOTHING:
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


# Populate the module-level CLOTHING_SUBCATEGORIES mapping from DEFAULT_ITEMS
for _item_id, _item in PandaCloset.DEFAULT_ITEMS.items():
    if _item.category == CustomizationCategory.CLOTHING and _item.clothing_type:
        CLOTHING_SUBCATEGORIES[_item_id] = ClothingSubCategory(_item.clothing_type)
