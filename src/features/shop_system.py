"""
Shop System - Buy items with money
Manage shop inventory, purchases, and categories
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ShopCategory(Enum):
    """Shop item categories."""
    PANDA_OUTFITS = "panda_outfits"
    CURSORS = "cursors"
    CURSOR_TRAILS = "cursor_trails"
    THEMES = "themes"
    ANIMATIONS = "animations"
    CLOTHES = "clothes"
    HATS = "hats"
    SHOES = "shoes"
    ACCESSORIES = "accessories"
    UPGRADES = "upgrades"
    SPECIAL = "special"
    FOOD = "food"
    TOYS = "toys"
    WEAPONS = "weapons"  # New category for weapons


# Mapping from ShopCategory to CustomizationCategory for persistent
# category association across shop and closet panels
SHOP_TO_CLOSET_CATEGORY = {
    ShopCategory.PANDA_OUTFITS: "clothing",
    ShopCategory.CLOTHES: "clothing",
    ShopCategory.HATS: "hat",
    ShopCategory.SHOES: "shoes",
    ShopCategory.ACCESSORIES: "accessory",
}


@dataclass
class ShopItem:
    """Represents an item in the shop."""
    id: str
    name: str
    description: str
    category: ShopCategory
    price: int
    icon: str = "🛒"
    level_required: int = 1
    one_time_purchase: bool = True
    unlockable_id: Optional[str] = None  # Links to unlockables system


class ShopSystem:
    """Manages shop inventory and purchases."""
    
    # Configuration constants
    MAX_PURCHASE_HISTORY = 100  # Number of purchases to keep in history
    
    # Shop catalog
    CATALOG: Dict[str, ShopItem] = {
        # Panda Outfits
        'panda_casual': ShopItem(
            id='panda_casual',
            name='Casual Panda',
            description='Comfy hoodie for your panda pal',
            category=ShopCategory.PANDA_OUTFITS,
            price=100,
            icon='👕',
            level_required=1,
            unlockable_id='panda_outfit_casual'
        ),
        'panda_ninja': ShopItem(
            id='panda_ninja',
            name='Ninja Panda',
            description='Stealth mode activated!',
            category=ShopCategory.PANDA_OUTFITS,
            price=250,
            icon='🥷',
            level_required=5,
            unlockable_id='panda_outfit_ninja'
        ),
        'panda_wizard': ShopItem(
            id='panda_wizard',
            name='Wizard Panda',
            description='Magical texture sorting powers',
            category=ShopCategory.PANDA_OUTFITS,
            price=500,
            icon='🧙',
            level_required=10,
            unlockable_id='panda_outfit_wizard'
        ),
        'panda_pirate': ShopItem(
            id='panda_pirate',
            name='Pirate Panda',
            description='Arr, matey!',
            category=ShopCategory.PANDA_OUTFITS,
            price=350,
            icon='🏴‍☠️',
            level_required=8,
            unlockable_id='panda_outfit_pirate'
        ),
        'panda_astronaut': ShopItem(
            id='panda_astronaut',
            name='Astronaut Panda',
            description='To infinity and beyond!',
            category=ShopCategory.PANDA_OUTFITS,
            price=750,
            icon='🚀',
            level_required=15,
            unlockable_id='panda_outfit_astronaut'
        ),
        
        # Cursors
        'cursor_bamboo': ShopItem(
            id='cursor_bamboo',
            name='Bamboo Cursor',
            description='Cursor shaped like bamboo',
            category=ShopCategory.CURSORS,
            price=50,
            icon='🎋',
            level_required=1,
            unlockable_id='cursor_bamboo'
        ),
        'cursor_paw': ShopItem(
            id='cursor_paw',
            name='Paw Print Cursor',
            description='Leave paw prints everywhere',
            category=ShopCategory.CURSORS,
            price=150,
            icon='🐾',
            level_required=3,
            unlockable_id='cursor_paw'
        ),
        'cursor_rainbow': ShopItem(
            id='cursor_rainbow',
            name='Rainbow Cursor',
            description='Fabulous rainbow trail',
            category=ShopCategory.CURSORS,
            price=300,
            icon='🌈',
            level_required=7,
            unlockable_id='cursor_rainbow'
        ),
        
        # Themes
        'theme_bamboo_forest': ShopItem(
            id='theme_bamboo_forest',
            name='Bamboo Forest Theme',
            description='Serene bamboo forest colors',
            category=ShopCategory.THEMES,
            price=200,
            icon='🎋',
            level_required=5,
            unlockable_id='theme_bamboo_forest'
        ),
        'theme_neon': ShopItem(
            id='theme_neon',
            name='Neon Theme',
            description='Cyberpunk vibes',
            category=ShopCategory.THEMES,
            price=400,
            icon='💫',
            level_required=12,
            unlockable_id='theme_neon'
        ),
        'theme_midnight': ShopItem(
            id='theme_midnight',
            name='Midnight Theme',
            description='Dark and mysterious',
            category=ShopCategory.THEMES,
            price=300,
            icon='🌙',
            level_required=8,
            unlockable_id='theme_midnight'
        ),
        
        # Animations
        'anim_dance': ShopItem(
            id='anim_dance',
            name='Dance Animation',
            description='Panda dance party!',
            category=ShopCategory.ANIMATIONS,
            price=150,
            icon='💃',
            level_required=4,
            unlockable_id='animation_dance'
        ),
        'anim_backflip': ShopItem(
            id='anim_backflip',
            name='Backflip Animation',
            description='Panda acrobatics',
            category=ShopCategory.ANIMATIONS,
            price=250,
            icon='🤸',
            level_required=6,
            unlockable_id='animation_backflip'
        ),
        'anim_magic': ShopItem(
            id='anim_magic',
            name='Magic Animation',
            description='Panda pulls textures from a hat',
            category=ShopCategory.ANIMATIONS,
            price=500,
            icon='🎩',
            level_required=10,
            unlockable_id='animation_magic'
        ),
        
        # Upgrades
        'upgrade_xp_boost': ShopItem(
            id='upgrade_xp_boost',
            name='XP Boost (1 hour)',
            description='Double XP for 1 hour',
            category=ShopCategory.UPGRADES,
            price=100,
            icon='⚡',
            level_required=1,
            one_time_purchase=False
        ),
        'upgrade_money_boost': ShopItem(
            id='upgrade_money_boost',
            name='Money Boost (1 hour)',
            description='Double money earned for 1 hour',
            category=ShopCategory.UPGRADES,
            price=150,
            icon='💰',
            level_required=1,
            one_time_purchase=False
        ),
        'upgrade_auto_sort': ShopItem(
            id='upgrade_auto_sort',
            name='Auto-Sort Helper',
            description='Automatically suggests categories',
            category=ShopCategory.UPGRADES,
            price=1000,
            icon='🤖',
            level_required=20,
            one_time_purchase=True
        ),
        
        # Special
        'special_golden_bamboo': ShopItem(
            id='special_golden_bamboo',
            name='Golden Bamboo',
            description='Legendary item! +10% all rewards permanently',
            category=ShopCategory.SPECIAL,
            price=5000,
            icon='✨',
            level_required=50,
            one_time_purchase=True
        ),
        
        # Additional Panda Outfits
        'panda_chef': ShopItem(
            id='panda_chef',
            name='Chef Panda',
            description='Cooking up some sorted textures!',
            category=ShopCategory.PANDA_OUTFITS,
            price=200,
            icon='👨‍🍳',
            level_required=3,
            unlockable_id='panda_outfit_chef'
        ),
        'panda_detective': ShopItem(
            id='panda_detective',
            name='Detective Panda',
            description='Investigating texture mysteries',
            category=ShopCategory.PANDA_OUTFITS,
            price=400,
            icon='🕵️',
            level_required=12,
            unlockable_id='panda_outfit_detective'
        ),
        'panda_superhero': ShopItem(
            id='panda_superhero',
            name='Superhero Panda',
            description='Saving textures one sort at a time!',
            category=ShopCategory.PANDA_OUTFITS,
            price=600,
            icon='🦸',
            level_required=18,
            unlockable_id='panda_outfit_superhero'
        ),
        
        # Additional Cursors
        'cursor_star': ShopItem(
            id='cursor_star',
            name='Star Cursor',
            description='Sparkle wherever you click',
            category=ShopCategory.CURSORS,
            price=200,
            icon='⭐',
            level_required=5,
            unlockable_id='cursor_star'
        ),
        'cursor_diamond': ShopItem(
            id='cursor_diamond',
            name='Diamond Cursor',
            description='Premium diamond-shaped cursor',
            category=ShopCategory.CURSORS,
            price=500,
            icon='💎',
            level_required=15,
            unlockable_id='cursor_diamond'
        ),
        
        # Additional Themes
        'theme_retro': ShopItem(
            id='theme_retro',
            name='Retro Theme',
            description='Classic retro gaming vibes',
            category=ShopCategory.THEMES,
            price=250,
            icon='🕹️',
            level_required=6,
            unlockable_id='theme_retro'
        ),
        'theme_ocean': ShopItem(
            id='theme_ocean',
            name='Ocean Theme',
            description='Deep blue ocean colors',
            category=ShopCategory.THEMES,
            price=350,
            icon='🌊',
            level_required=10,
            unlockable_id='theme_ocean'
        ),
        
        # Additional Animations
        'anim_spin': ShopItem(
            id='anim_spin',
            name='Spin Animation',
            description='Panda does a dizzy spin!',
            category=ShopCategory.ANIMATIONS,
            price=100,
            icon='🌀',
            level_required=2,
            unlockable_id='animation_spin'
        ),
        'anim_juggle': ShopItem(
            id='anim_juggle',
            name='Juggle Animation',
            description='Panda juggles texture files',
            category=ShopCategory.ANIMATIONS,
            price=350,
            icon='🤹',
            level_required=8,
            unlockable_id='animation_juggle'
        ),
        
        # Additional Upgrades
        'upgrade_lucky_charm': ShopItem(
            id='upgrade_lucky_charm',
            name='Lucky Charm',
            description='5% chance for bonus rewards on any action',
            category=ShopCategory.UPGRADES,
            price=500,
            icon='🍀',
            level_required=10,
            one_time_purchase=True
        ),
        
        # Additional Special Items
        'special_party_hat': ShopItem(
            id='special_party_hat',
            name='Party Hat',
            description='Celebration mode! Confetti on achievements',
            category=ShopCategory.SPECIAL,
            price=1000,
            icon='🎉',
            level_required=20,
            one_time_purchase=True
        ),
        'special_rainbow_aura': ShopItem(
            id='special_rainbow_aura',
            name='Rainbow Aura',
            description='Panda glows with rainbow colors',
            category=ShopCategory.SPECIAL,
            price=2500,
            icon='🌈',
            level_required=30,
            one_time_purchase=True
        ),
        
        # Cursor Trails
        'trail_rainbow': ShopItem(
            id='trail_rainbow',
            name='Rainbow Trail',
            description='Leave a colorful rainbow trail behind your cursor',
            category=ShopCategory.CURSOR_TRAILS,
            price=100,
            icon='🌈',
            level_required=1,
            unlockable_id='trail_rainbow'
        ),
        'trail_fire': ShopItem(
            id='trail_fire',
            name='Fire Trail',
            description='Blazing hot fire trail follows your cursor',
            category=ShopCategory.CURSOR_TRAILS,
            price=200,
            icon='🔥',
            level_required=5,
            unlockable_id='trail_fire'
        ),
        'trail_ice': ShopItem(
            id='trail_ice',
            name='Ice Trail',
            description='Cool icy blue trail behind your cursor',
            category=ShopCategory.CURSOR_TRAILS,
            price=200,
            icon='❄️',
            level_required=5,
            unlockable_id='trail_ice'
        ),
        'trail_nature': ShopItem(
            id='trail_nature',
            name='Nature Trail',
            description='Leaves and green particles follow your cursor',
            category=ShopCategory.CURSOR_TRAILS,
            price=150,
            icon='🌿',
            level_required=3,
            unlockable_id='trail_nature'
        ),
        'trail_galaxy': ShopItem(
            id='trail_galaxy',
            name='Galaxy Trail',
            description='Stardust and cosmic purple trail',
            category=ShopCategory.CURSOR_TRAILS,
            price=400,
            icon='🌌',
            level_required=10,
            unlockable_id='trail_galaxy'
        ),
        'trail_gold': ShopItem(
            id='trail_gold',
            name='Gold Trail',
            description='Shimmering golden sparkle trail',
            category=ShopCategory.CURSOR_TRAILS,
            price=500,
            icon='✨',
            level_required=15,
            unlockable_id='trail_gold'
        ),
        
        # Additional Cursors
        'cursor_crosshair': ShopItem(
            id='cursor_crosshair',
            name='Crosshair Cursor',
            description='Precision targeting crosshair',
            category=ShopCategory.CURSORS,
            price=75,
            icon='🎯',
            level_required=2,
            unlockable_id='cursor_crosshair'
        ),
        'cursor_heart': ShopItem(
            id='cursor_heart',
            name='Heart Cursor',
            description='Spread the love with a heart cursor',
            category=ShopCategory.CURSORS,
            price=100,
            icon='❤️',
            level_required=3,
            unlockable_id='cursor_heart'
        ),
        'cursor_pencil': ShopItem(
            id='cursor_pencil',
            name='Pencil Cursor',
            description='Draw your way through sorting',
            category=ShopCategory.CURSORS,
            price=125,
            icon='✏️',
            level_required=4,
            unlockable_id='cursor_pencil'
        ),
        'cursor_circle': ShopItem(
            id='cursor_circle',
            name='Circle Cursor',
            description='Smooth circular cursor design',
            category=ShopCategory.CURSORS,
            price=100,
            icon='⭕',
            level_required=3,
            unlockable_id='cursor_circle'
        ),
        'cursor_spraycan': ShopItem(
            id='cursor_spraycan',
            name='Spraycan Cursor',
            description='Street art style spray paint cursor',
            category=ShopCategory.CURSORS,
            price=250,
            icon='🎨',
            level_required=8,
            unlockable_id='cursor_spraycan'
        ),
        
        # Clothes
        'clothes_tshirt': ShopItem(
            id='clothes_tshirt',
            name='Classic T-Shirt',
            description='A comfy everyday t-shirt for your panda',
            category=ShopCategory.CLOTHES,
            price=50,
            icon='👕',
            level_required=1,
            unlockable_id='clothes_tshirt'
        ),
        'clothes_hoodie': ShopItem(
            id='clothes_hoodie',
            name='Cozy Hoodie',
            description='Keep your panda warm and stylish',
            category=ShopCategory.CLOTHES,
            price=100,
            icon='🧥',
            level_required=2,
            unlockable_id='clothes_hoodie'
        ),
        'clothes_suit': ShopItem(
            id='clothes_suit',
            name='Business Suit',
            description='Professional panda means business',
            category=ShopCategory.CLOTHES,
            price=300,
            icon='🤵',
            level_required=8,
            unlockable_id='clothes_suit'
        ),
        'clothes_kimono': ShopItem(
            id='clothes_kimono',
            name='Silk Kimono',
            description='Elegant traditional kimono',
            category=ShopCategory.CLOTHES,
            price=400,
            icon='👘',
            level_required=10,
            unlockable_id='clothes_kimono'
        ),
        'clothes_superhero_cape': ShopItem(
            id='clothes_superhero_cape',
            name='Superhero Cape',
            description='Every hero needs a cape!',
            category=ShopCategory.CLOTHES,
            price=500,
            icon='🦸',
            level_required=12,
            unlockable_id='clothes_superhero_cape'
        ),
        'clothes_leather_jacket': ShopItem(
            id='clothes_leather_jacket',
            name='Leather Jacket',
            description='Cool rebel panda vibes',
            category=ShopCategory.CLOTHES,
            price=350,
            icon='🧥',
            level_required=7,
            unlockable_id='clothes_leather_jacket'
        ),
        'clothes_lab_coat': ShopItem(
            id='clothes_lab_coat',
            name='Lab Coat',
            description='Science panda is conducting experiments',
            category=ShopCategory.CLOTHES,
            price=250,
            icon='🥼',
            level_required=6,
            unlockable_id='clothes_lab_coat'
        ),
        'clothes_pajamas': ShopItem(
            id='clothes_pajamas',
            name='Cozy Pajamas',
            description='For those late night sorting sessions',
            category=ShopCategory.CLOTHES,
            price=75,
            icon='🩳',
            level_required=1,
            unlockable_id='clothes_pajamas'
        ),
        'clothes_raincoat': ShopItem(
            id='clothes_raincoat',
            name='Yellow Raincoat',
            description='Stay dry and stylish in the rain',
            category=ShopCategory.CLOTHES,
            price=125,
            icon='🧥',
            level_required=3,
            unlockable_id='clothes_raincoat'
        ),
        'clothes_tuxedo': ShopItem(
            id='clothes_tuxedo',
            name='Fancy Tuxedo',
            description='Black tie panda event ready',
            category=ShopCategory.CLOTHES,
            price=450,
            icon='🤵',
            level_required=12,
            unlockable_id='clothes_tuxedo'
        ),
        'clothes_overalls': ShopItem(
            id='clothes_overalls',
            name='Denim Overalls',
            description='Hardworking farmer panda look',
            category=ShopCategory.CLOTHES,
            price=90,
            icon='👖',
            level_required=2,
            unlockable_id='clothes_overalls'
        ),
        'clothes_vest': ShopItem(
            id='clothes_vest',
            name='Adventure Vest',
            description='Pockets for all your bamboo snacks',
            category=ShopCategory.CLOTHES,
            price=175,
            icon='🦺',
            level_required=5,
            unlockable_id='clothes_vest'
        ),
        'clothes_sweater': ShopItem(
            id='clothes_sweater',
            name='Cozy Sweater',
            description='Warm knit sweater for chilly days',
            category=ShopCategory.CLOTHES,
            price=110,
            icon='🧶',
            level_required=3,
            unlockable_id='clothes_sweater'
        ),
        'clothes_jersey': ShopItem(
            id='clothes_jersey',
            name='Sports Jersey',
            description='Go team panda!',
            category=ShopCategory.CLOTHES,
            price=200,
            icon='🏅',
            level_required=6,
            unlockable_id='clothes_jersey'
        ),
        'clothes_toga': ShopItem(
            id='clothes_toga',
            name='Ancient Toga',
            description='Philosopher panda contemplates textures',
            category=ShopCategory.CLOTHES,
            price=275,
            icon='🏛️',
            level_required=8,
            unlockable_id='clothes_toga'
        ),
        'clothes_spacesuit': ShopItem(
            id='clothes_spacesuit',
            name='Space Suit',
            description='One small step for panda, one giant leap for textures',
            category=ShopCategory.CLOTHES,
            price=600,
            icon='🚀',
            level_required=15,
            unlockable_id='clothes_spacesuit'
        ),
        
        # Accessories
        'acc_sunglasses': ShopItem(
            id='acc_sunglasses',
            name='Cool Sunglasses',
            description='Too cool for school shades',
            category=ShopCategory.ACCESSORIES,
            price=80,
            icon='🕶️',
            level_required=1,
            unlockable_id='acc_sunglasses'
        ),
        'acc_bow_tie': ShopItem(
            id='acc_bow_tie',
            name='Bow Tie',
            description='Dapper and distinguished',
            category=ShopCategory.ACCESSORIES,
            price=60,
            icon='🎀',
            level_required=1,
            unlockable_id='acc_bow_tie'
        ),
        'acc_necklace': ShopItem(
            id='acc_necklace',
            name='Gold Necklace',
            description='Bling bling panda style',
            category=ShopCategory.ACCESSORIES,
            price=200,
            icon='📿',
            level_required=5,
            unlockable_id='acc_necklace'
        ),
        'acc_backpack': ShopItem(
            id='acc_backpack',
            name='Adventure Backpack',
            description='Ready for any sorting adventure',
            category=ShopCategory.ACCESSORIES,
            price=150,
            icon='🎒',
            level_required=4,
            unlockable_id='acc_backpack'
        ),
        'acc_wings': ShopItem(
            id='acc_wings',
            name='Angel Wings',
            description='Heavenly sorting powers',
            category=ShopCategory.ACCESSORIES,
            price=1000,
            icon='🪽',
            level_required=20,
            unlockable_id='acc_wings'
        ),
        'acc_crown': ShopItem(
            id='acc_crown',
            name='Royal Crown',
            description='King or Queen of texture sorting',
            category=ShopCategory.HATS,
            price=750,
            icon='👑',
            level_required=15,
            unlockable_id='acc_crown'
        ),
        'acc_headphones': ShopItem(
            id='acc_headphones',
            name='DJ Headphones',
            description='Sorting to the beat',
            category=ShopCategory.ACCESSORIES,
            price=120,
            icon='🎧',
            level_required=3,
            unlockable_id='acc_headphones'
        ),
        'acc_monocle': ShopItem(
            id='acc_monocle',
            name='Monocle',
            description='Inspecting textures with class',
            category=ShopCategory.ACCESSORIES,
            price=180,
            icon='🧐',
            level_required=5,
            unlockable_id='acc_monocle'
        ),
        
        # Additional Themes
        'theme_sunset': ShopItem(
            id='theme_sunset',
            name='Sunset Theme',
            description='Warm sunset gradient colors',
            category=ShopCategory.THEMES,
            price=300,
            icon='🌅',
            level_required=7,
            unlockable_id='theme_sunset'
        ),
        'theme_cherry_blossom': ShopItem(
            id='theme_cherry_blossom',
            name='Cherry Blossom Theme',
            description='Beautiful pink cherry blossom aesthetic',
            category=ShopCategory.THEMES,
            price=350,
            icon='🌸',
            level_required=9,
            unlockable_id='theme_cherry_blossom'
        ),
        'theme_arctic': ShopItem(
            id='theme_arctic',
            name='Arctic Theme',
            description='Cool icy blue and white colors',
            category=ShopCategory.THEMES,
            price=250,
            icon='🏔️',
            level_required=6,
            unlockable_id='theme_arctic'
        ),
        'theme_hacker': ShopItem(
            id='theme_hacker',
            name='Hacker Theme',
            description='Green on black matrix style',
            category=ShopCategory.THEMES,
            price=400,
            icon='💻',
            level_required=12,
            unlockable_id='theme_hacker'
        ),
        
        # Food items - buy and drag to panda to feed
        'food_bamboo': ShopItem(
            id='food_bamboo',
            name='Fresh Bamboo',
            description='Drag to panda to feed! Their favorite snack',
            category=ShopCategory.FOOD,
            price=10,
            icon='🎋',
            level_required=1,
            one_time_purchase=False,
            unlockable_id='food_bamboo'
        ),
        'food_bamboo_shoots': ShopItem(
            id='food_bamboo_shoots',
            name='Bamboo Shoots',
            description='Drag to panda to feed! Tender young shoots',
            category=ShopCategory.FOOD,
            price=20,
            icon='🌱',
            level_required=2,
            one_time_purchase=False,
            unlockable_id='food_bamboo_shoots'
        ),
        'food_bamboo_cake': ShopItem(
            id='food_bamboo_cake',
            name='Bamboo Cake',
            description='Drag to panda to feed! A delicious treat',
            category=ShopCategory.FOOD,
            price=50,
            icon='🍰',
            level_required=5,
            one_time_purchase=False,
            unlockable_id='food_bamboo_cake'
        ),
        'food_golden_bamboo': ShopItem(
            id='food_golden_bamboo',
            name='Golden Bamboo',
            description='Drag to panda to feed! Legendary delicacy',
            category=ShopCategory.FOOD,
            price=200,
            icon='✨',
            level_required=10,
            one_time_purchase=False,
            unlockable_id='food_golden_bamboo'
        ),
        'food_cookies': ShopItem(
            id='food_cookies',
            name='Panda Cookies',
            description='Drag to panda to feed! Cute panda-shaped cookies',
            category=ShopCategory.FOOD,
            price=15,
            icon='🍪',
            level_required=1,
            one_time_purchase=False,
            unlockable_id='food_cookies'
        ),
        'food_ramen': ShopItem(
            id='food_ramen',
            name='Ramen Bowl',
            description='Drag to panda to feed! Hot and savory',
            category=ShopCategory.FOOD,
            price=30,
            icon='🍜',
            level_required=3,
            one_time_purchase=False,
            unlockable_id='food_ramen'
        ),

        # Toys
        'toy_ball': ShopItem(
            id='toy_ball',
            name='Bamboo Ball',
            description='A bouncy ball for the panda to play with',
            category=ShopCategory.TOYS,
            price=15,
            icon='🎾',
            level_required=1,
            one_time_purchase=True,
            unlockable_id='ball'
        ),
        'toy_plushie': ShopItem(
            id='toy_plushie',
            name='Mini Panda Plushie',
            description='A cuddly mini panda plushie toy',
            category=ShopCategory.TOYS,
            price=50,
            icon='🧸',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='plushie'
        ),
        'toy_frisbee': ShopItem(
            id='toy_frisbee',
            name='Bamboo Frisbee',
            description='A lightweight frisbee for outdoor fun',
            category=ShopCategory.TOYS,
            price=40,
            icon='🥏',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='frisbee'
        ),
        'toy_yoyo': ShopItem(
            id='toy_yoyo',
            name='Panda Yo-Yo',
            description='A tricky yo-yo with panda design',
            category=ShopCategory.TOYS,
            price=100,
            icon='🪀',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='yo-yo'
        ),
        'toy_puzzle': ShopItem(
            id='toy_puzzle',
            name='Bamboo Puzzle',
            description='A challenging bamboo puzzle for smart pandas',
            category=ShopCategory.TOYS,
            price=120,
            icon='🧩',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='puzzle'
        ),
        'toy_kite': ShopItem(
            id='toy_kite',
            name='Panda Kite',
            description='A beautiful kite with panda art',
            category=ShopCategory.TOYS,
            price=250,
            icon='🪁',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='kite'
        ),
        'toy_robot': ShopItem(
            id='toy_robot',
            name='Robot Panda Friend',
            description='A legendary robotic panda companion',
            category=ShopCategory.TOYS,
            price=1000,
            icon='🤖',
            level_required=20,
            one_time_purchase=True,
            unlockable_id='robot'
        ),
        'toy_stick': ShopItem(
            id='toy_stick',
            name='Bamboo Stick',
            description='A simple bamboo stick to play fetch',
            category=ShopCategory.TOYS,
            price=10,
            icon='🎍',
            level_required=1,
            one_time_purchase=True,
            unlockable_id='stick'
        ),

        # More special items
        'special_party_hat': ShopItem(
            id='special_party_hat',
            name='Party Hat',
            description='A festive party hat for celebrations',
            category=ShopCategory.SPECIAL,
            price=200,
            icon='🥳',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='party_hat'
        ),
        'special_fireworks': ShopItem(
            id='special_fireworks',
            name='Fireworks Pack',
            description='Celebrate with a dazzling fireworks display',
            category=ShopCategory.SPECIAL,
            price=300,
            icon='🎆',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='fireworks'
        ),
        'special_confetti': ShopItem(
            id='special_confetti',
            name='Confetti Cannon',
            description='Blast confetti everywhere!',
            category=ShopCategory.SPECIAL,
            price=150,
            icon='🎊',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='confetti'
        ),

        # More upgrades
        'upgrade_lucky_charm': ShopItem(
            id='upgrade_lucky_charm',
            name='Lucky Charm',
            description='Increases rare item drop rates for 1 hour',
            category=ShopCategory.UPGRADES,
            price=200,
            icon='🍀',
            level_required=10,
            one_time_purchase=False,
            unlockable_id=None
        ),
        'upgrade_speed_boost': ShopItem(
            id='upgrade_speed_boost',
            name='Speed Boost',
            description='Sort textures 2x faster for 1 hour',
            category=ShopCategory.UPGRADES,
            price=150,
            icon='⚡',
            level_required=5,
            one_time_purchase=False,
            unlockable_id=None
        ),

        # Additional Clothes
        'clothes_dress': ShopItem(
            id='clothes_dress',
            name='Fancy Dress',
            description='A beautiful dress for special occasions',
            category=ShopCategory.CLOTHES,
            price=350,
            icon='👗',
            level_required=8,
            unlockable_id='clothes_dress'
        ),
        'clothes_sports_jersey': ShopItem(
            id='clothes_sports_jersey',
            name='Sports Jersey',
            description='Game day panda ready to score!',
            category=ShopCategory.CLOTHES,
            price=150,
            icon='🏅',
            level_required=4,
            unlockable_id='clothes_sports_jersey'
        ),

        # Color Shirts
        'clothes_red_shirt': ShopItem(
            id='clothes_red_shirt',
            name='Red T-Shirt',
            description='A bright red casual tee for your panda',
            category=ShopCategory.CLOTHES,
            price=30,
            icon='👕',
            level_required=1,
            unlockable_id='clothes_red_shirt'
        ),
        'clothes_blue_shirt': ShopItem(
            id='clothes_blue_shirt',
            name='Blue T-Shirt',
            description='A cool blue casual tee for your panda',
            category=ShopCategory.CLOTHES,
            price=30,
            icon='👕',
            level_required=1,
            unlockable_id='clothes_blue_shirt'
        ),
        'clothes_green_shirt': ShopItem(
            id='clothes_green_shirt',
            name='Green T-Shirt',
            description='A fresh green casual tee for your panda',
            category=ShopCategory.CLOTHES,
            price=30,
            icon='👕',
            level_required=1,
            unlockable_id='clothes_green_shirt'
        ),
        'clothes_yellow_polo': ShopItem(
            id='clothes_yellow_polo',
            name='Yellow Polo Shirt',
            description='A sunny yellow collared polo',
            category=ShopCategory.CLOTHES,
            price=55,
            icon='👕',
            level_required=2,
            unlockable_id='clothes_yellow_polo'
        ),
        'clothes_striped_shirt': ShopItem(
            id='clothes_striped_shirt',
            name='Striped Shirt',
            description='A classic striped button-up shirt',
            category=ShopCategory.CLOTHES,
            price=65,
            icon='👕',
            level_required=2,
            unlockable_id='clothes_striped_shirt'
        ),
        'clothes_hawaiian_shirt': ShopItem(
            id='clothes_hawaiian_shirt',
            name='Hawaiian Shirt',
            description='A tropical floral shirt for beach vibes',
            category=ShopCategory.CLOTHES,
            price=70,
            icon='🌺',
            level_required=3,
            unlockable_id='clothes_hawaiian_shirt'
        ),
        'clothes_tank_top': ShopItem(
            id='clothes_tank_top',
            name='White Tank Top',
            description='A sleeveless white tank top',
            category=ShopCategory.CLOTHES,
            price=20,
            icon='👕',
            level_required=1,
            unlockable_id='clothes_tank_top'
        ),

        # Pants
        'clothes_blue_jeans': ShopItem(
            id='clothes_blue_jeans',
            name='Blue Jeans',
            description='Classic blue denim jeans',
            category=ShopCategory.CLOTHES,
            price=40,
            icon='👖',
            level_required=1,
            unlockable_id='clothes_blue_jeans'
        ),
        'clothes_black_pants': ShopItem(
            id='clothes_black_pants',
            name='Black Pants',
            description='Sleek black trousers for your panda',
            category=ShopCategory.CLOTHES,
            price=45,
            icon='👖',
            level_required=2,
            unlockable_id='clothes_black_pants'
        ),
        'clothes_cargo_pants': ShopItem(
            id='clothes_cargo_pants',
            name='Cargo Pants',
            description='Rugged cargo pants with extra pockets',
            category=ShopCategory.CLOTHES,
            price=55,
            icon='👖',
            level_required=3,
            unlockable_id='clothes_cargo_pants'
        ),
        'clothes_shorts': ShopItem(
            id='clothes_shorts',
            name='Khaki Shorts',
            description='Comfortable khaki shorts for warm days',
            category=ShopCategory.CLOTHES,
            price=30,
            icon='🩳',
            level_required=1,
            unlockable_id='clothes_shorts'
        ),
        'clothes_sweatpants': ShopItem(
            id='clothes_sweatpants',
            name='Grey Sweatpants',
            description='Cozy grey sweatpants for lounging',
            category=ShopCategory.CLOTHES,
            price=35,
            icon='👖',
            level_required=1,
            unlockable_id='clothes_sweatpants'
        ),

        # Jackets
        'clothes_denim_jacket': ShopItem(
            id='clothes_denim_jacket',
            name='Denim Jacket',
            description='A classic blue denim jacket',
            category=ShopCategory.CLOTHES,
            price=110,
            icon='🧥',
            level_required=3,
            unlockable_id='clothes_denim_jacket'
        ),
        'clothes_bomber_jacket': ShopItem(
            id='clothes_bomber_jacket',
            name='Bomber Jacket',
            description='A sleek green bomber jacket',
            category=ShopCategory.CLOTHES,
            price=180,
            icon='🧥',
            level_required=5,
            unlockable_id='clothes_bomber_jacket'
        ),
        'clothes_puffer_jacket': ShopItem(
            id='clothes_puffer_jacket',
            name='Puffer Jacket',
            description='A warm puffy winter jacket',
            category=ShopCategory.CLOTHES,
            price=130,
            icon='🧥',
            level_required=4,
            unlockable_id='clothes_puffer_jacket'
        ),
        'clothes_varsity_jacket': ShopItem(
            id='clothes_varsity_jacket',
            name='Varsity Jacket',
            description='A red and white letterman jacket',
            category=ShopCategory.CLOTHES,
            price=200,
            icon='🧥',
            level_required=6,
            unlockable_id='clothes_varsity_jacket'
        ),
        'clothes_windbreaker': ShopItem(
            id='clothes_windbreaker',
            name='Windbreaker',
            description='A light neon windbreaker for rainy days',
            category=ShopCategory.CLOTHES,
            price=90,
            icon='🧥',
            level_required=2,
            unlockable_id='clothes_windbreaker'
        ),

        # Dresses
        'clothes_summer_dress': ShopItem(
            id='clothes_summer_dress',
            name='Summer Dress',
            description='A flowy floral summer dress',
            category=ShopCategory.CLOTHES,
            price=85,
            icon='👗',
            level_required=3,
            unlockable_id='clothes_summer_dress'
        ),
        'clothes_evening_gown': ShopItem(
            id='clothes_evening_gown',
            name='Evening Gown',
            description='An elegant black evening gown',
            category=ShopCategory.CLOTHES,
            price=400,
            icon='👗',
            level_required=12,
            unlockable_id='clothes_evening_gown'
        ),

        # Full Body Outfits
        'clothes_tracksuit': ShopItem(
            id='clothes_tracksuit',
            name='Tracksuit',
            description='A sporty matching tracksuit',
            category=ShopCategory.CLOTHES,
            price=100,
            icon='🏃',
            level_required=3,
            unlockable_id='clothes_tracksuit'
        ),
        'clothes_onesie': ShopItem(
            id='clothes_onesie',
            name='Panda Onesie',
            description='A cute panda-print onesie',
            category=ShopCategory.CLOTHES,
            price=150,
            icon='🐼',
            level_required=5,
            unlockable_id='clothes_onesie'
        ),
        'clothes_jumpsuit': ShopItem(
            id='clothes_jumpsuit',
            name='Orange Jumpsuit',
            description='A bright orange utility jumpsuit',
            category=ShopCategory.CLOTHES,
            price=80,
            icon='🟠',
            level_required=3,
            unlockable_id='clothes_jumpsuit'
        ),
        # Additional Accessories
        'acc_scarf': ShopItem(
            id='acc_scarf',
            name='Silk Scarf',
            description='Elegant and breezy',
            category=ShopCategory.ACCESSORIES,
            price=90,
            icon='🧣',
            level_required=2,
            unlockable_id='acc_scarf'
        ),
        'acc_watch': ShopItem(
            id='acc_watch',
            name='Fancy Watch',
            description='Time flies when sorting textures',
            category=ShopCategory.ACCESSORIES,
            price=250,
            icon='⌚',
            level_required=7,
            unlockable_id='acc_watch'
        ),
        'acc_flower': ShopItem(
            id='acc_flower',
            name='Flower Crown',
            description='Spring vibes all year round',
            category=ShopCategory.HATS,
            price=100,
            icon='🌸',
            level_required=3,
            unlockable_id='acc_flower'
        ),
        'acc_cape': ShopItem(
            id='acc_cape',
            name='Mystic Cape',
            description='Flowing cape of mystery',
            category=ShopCategory.ACCESSORIES,
            price=400,
            icon='🦹',
            level_required=10,
            unlockable_id='acc_cape'
        ),

        # Additional Food
        'food_sushi': ShopItem(
            id='food_sushi',
            name='Panda Sushi Roll',
            description='Drag to panda to feed! Cute panda-shaped sushi',
            category=ShopCategory.FOOD,
            price=40,
            icon='🍣',
            level_required=4,
            one_time_purchase=False,
            unlockable_id='food_sushi'
        ),
        'food_dumplings': ShopItem(
            id='food_dumplings',
            name='Steamed Dumplings',
            description='Drag to panda to feed! Hot and juicy',
            category=ShopCategory.FOOD,
            price=35,
            icon='🥟',
            level_required=3,
            one_time_purchase=False,
            unlockable_id='food_dumplings'
        ),
        'food_honey': ShopItem(
            id='food_honey',
            name='Honey Jar',
            description='Drag to panda to feed! Sweet golden honey',
            category=ShopCategory.FOOD,
            price=25,
            icon='🍯',
            level_required=2,
            one_time_purchase=False,
            unlockable_id='food_honey'
        ),
        'food_rice_ball': ShopItem(
            id='food_rice_ball',
            name='Rice Ball',
            description='Drag to panda to feed! Cute onigiri',
            category=ShopCategory.FOOD,
            price=15,
            icon='🍙',
            level_required=1,
            one_time_purchase=False,
            unlockable_id='food_rice_ball'
        ),
        'food_boba_tea': ShopItem(
            id='food_boba_tea',
            name='Boba Tea',
            description='Drag to panda to feed! Refreshing bubble tea',
            category=ShopCategory.FOOD,
            price=30,
            icon='🧋',
            level_required=3,
            one_time_purchase=False,
            unlockable_id='food_boba_tea'
        ),
        'food_ice_cream': ShopItem(
            id='food_ice_cream',
            name='Ice Cream Cone',
            description='Drag to panda to feed! Cool and sweet',
            category=ShopCategory.FOOD,
            price=20,
            icon='🍦',
            level_required=2,
            one_time_purchase=False,
            unlockable_id='food_ice_cream'
        ),
        'food_birthday_cake': ShopItem(
            id='food_birthday_cake',
            name='Birthday Cake',
            description='Drag to panda to feed! Party time treat',
            category=ShopCategory.FOOD,
            price=100,
            icon='🎂',
            level_required=8,
            one_time_purchase=False,
            unlockable_id='food_birthday_cake'
        ),

        # Additional Toys
        'toy_skateboard': ShopItem(
            id='toy_skateboard',
            name='Panda Skateboard',
            description='Shred some gnarly tricks!',
            category=ShopCategory.TOYS,
            price=150,
            icon='🛹',
            level_required=6,
            one_time_purchase=True,
            unlockable_id='skateboard'
        ),
        'toy_drum': ShopItem(
            id='toy_drum',
            name='Mini Drum Set',
            description='Rock out panda style!',
            category=ShopCategory.TOYS,
            price=200,
            icon='🥁',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='drum'
        ),
        'toy_telescope': ShopItem(
            id='toy_telescope',
            name='Stargazing Telescope',
            description='Explore the panda universe!',
            category=ShopCategory.TOYS,
            price=300,
            icon='🔭',
            level_required=12,
            one_time_purchase=True,
            unlockable_id='telescope'
        ),
        'toy_bouncy_carrot': ShopItem(
            id='toy_bouncy_carrot',
            name='Bouncy Carrot',
            description='A super bouncy carrot that bounces everywhere!',
            category=ShopCategory.TOYS,
            price=60,
            icon='🥕',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='bouncy_carrot'
        ),
        'toy_squishy_ball': ShopItem(
            id='toy_squishy_ball',
            name='Big Red Squishy Ball',
            description='A big squishy ball that wobbles and bounces!',
            category=ShopCategory.TOYS,
            price=80,
            icon='🔴',
            level_required=4,
            one_time_purchase=True,
            unlockable_id='squishy_ball'
        ),
        'toy_dumbbell': ShopItem(
            id='toy_dumbbell',
            name='Super Heavy Dumbbell',
            description='A heavy dumbbell — throw it at panda for a funny reaction!',
            category=ShopCategory.TOYS,
            price=200,
            icon='🏋️',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='dumbbell'
        ),

        # New Fur Colors - Shop
        'closet_cherry_blossom': ShopItem(
            id='closet_cherry_blossom',
            name='Cherry Blossom Panda',
            description='Pink cherry blossom fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=300,
            icon='🌸',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_cherry_blossom'
        ),
        'closet_ocean_blue': ShopItem(
            id='closet_ocean_blue',
            name='Ocean Blue Panda',
            description='Deep ocean blue',
            category=ShopCategory.PANDA_OUTFITS,
            price=350,
            icon='🌊',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='closet_ocean_blue'
        ),
        'closet_sunset_orange': ShopItem(
            id='closet_sunset_orange',
            name='Sunset Orange Panda',
            description='Warm sunset orange',
            category=ShopCategory.PANDA_OUTFITS,
            price=200,
            icon='🌅',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='closet_sunset_orange'
        ),
        'closet_neon_green': ShopItem(
            id='closet_neon_green',
            name='Neon Green Panda',
            description='Electric neon green',
            category=ShopCategory.PANDA_OUTFITS,
            price=400,
            icon='💚',
            level_required=12,
            one_time_purchase=True,
            unlockable_id='closet_neon_green'
        ),
        'closet_ice_crystal': ShopItem(
            id='closet_ice_crystal',
            name='Ice Crystal Panda',
            description='Translucent ice blue',
            category=ShopCategory.PANDA_OUTFITS,
            price=600,
            icon='🧊',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_ice_crystal'
        ),
        'closet_volcanic': ShopItem(
            id='closet_volcanic',
            name='Volcanic Panda',
            description='Fiery volcanic red-orange',
            category=ShopCategory.PANDA_OUTFITS,
            price=700,
            icon='🌋',
            level_required=18,
            one_time_purchase=True,
            unlockable_id='closet_volcanic'
        ),
        'closet_starlight': ShopItem(
            id='closet_starlight',
            name='Starlight Panda',
            description='Twinkling starlight white',
            category=ShopCategory.PANDA_OUTFITS,
            price=1200,
            icon='⭐',
            level_required=20,
            one_time_purchase=True,
            unlockable_id='closet_starlight'
        ),
        'closet_shadow': ShopItem(
            id='closet_shadow',
            name='Shadow Panda',
            description='Deep shadow black',
            category=ShopCategory.PANDA_OUTFITS,
            price=350,
            icon='🖤',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='closet_shadow'
        ),
        'closet_cotton_candy': ShopItem(
            id='closet_cotton_candy',
            name='Cotton Candy Panda',
            description='Pastel cotton candy pink and blue',
            category=ShopCategory.PANDA_OUTFITS,
            price=550,
            icon='🍬',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_cotton_candy'
        ),
        'closet_phantom': ShopItem(
            id='closet_phantom',
            name='Phantom Panda',
            description='Ghostly translucent white',
            category=ShopCategory.PANDA_OUTFITS,
            price=1800,
            icon='👻',
            level_required=25,
            one_time_purchase=True,
            unlockable_id='closet_phantom'
        ),

        # New Fur Styles - Shop
        'closet_spiky': ShopItem(
            id='closet_spiky',
            name='Spiky Panda',
            description='Wild spiky fur style',
            category=ShopCategory.PANDA_OUTFITS,
            price=120,
            icon='⚡',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='closet_spiky'
        ),
        'closet_wavy': ShopItem(
            id='closet_wavy',
            name='Wavy Panda',
            description='Flowing wavy fur style',
            category=ShopCategory.PANDA_OUTFITS,
            price=130,
            icon='🌊',
            level_required=4,
            one_time_purchase=True,
            unlockable_id='closet_wavy'
        ),
        'closet_shaggy': ShopItem(
            id='closet_shaggy',
            name='Shaggy Panda',
            description='Relaxed shaggy look',
            category=ShopCategory.PANDA_OUTFITS,
            price=80,
            icon='🍃',
            level_required=2,
            one_time_purchase=True,
            unlockable_id='closet_shaggy'
        ),
        'closet_velvet': ShopItem(
            id='closet_velvet',
            name='Velvet Panda',
            description='Ultra smooth velvet fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=300,
            icon='💎',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='closet_velvet'
        ),
        'closet_mohawk': ShopItem(
            id='closet_mohawk',
            name='Mohawk Panda',
            description='Punk rock mohawk style',
            category=ShopCategory.PANDA_OUTFITS,
            price=350,
            icon='🔥',
            level_required=12,
            one_time_purchase=True,
            unlockable_id='closet_mohawk'
        ),
        'closet_braided': ShopItem(
            id='closet_braided',
            name='Braided Panda',
            description='Intricate braided fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=280,
            icon='🎀',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_braided'
        ),
        'closet_frosted': ShopItem(
            id='closet_frosted',
            name='Frosted Panda',
            description='Frost-tipped fur style',
            category=ShopCategory.PANDA_OUTFITS,
            price=320,
            icon='❄️',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='closet_frosted'
        ),
        'closet_crystalline': ShopItem(
            id='closet_crystalline',
            name='Crystalline Panda',
            description='Crystal-like sparkling fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=500,
            icon='💠',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_crystalline'
        ),
        'closet_feathered': ShopItem(
            id='closet_feathered',
            name='Feathered Panda',
            description='Soft feathered texture',
            category=ShopCategory.PANDA_OUTFITS,
            price=150,
            icon='🪶',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='closet_feathered'
        ),
        'closet_metallic': ShopItem(
            id='closet_metallic',
            name='Metallic Panda',
            description='Shiny metallic sheen fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=400,
            icon='🔩',
            level_required=12,
            one_time_purchase=True,
            unlockable_id='closet_metallic'
        ),
        'closet_woolly': ShopItem(
            id='closet_woolly',
            name='Woolly Panda',
            description='Thick woolly fur style',
            category=ShopCategory.PANDA_OUTFITS,
            price=140,
            icon='🧶',
            level_required=4,
            one_time_purchase=True,
            unlockable_id='closet_woolly'
        ),
        'closet_spotted': ShopItem(
            id='closet_spotted',
            name='Spotted Panda',
            description='Exotic spotted pattern',
            category=ShopCategory.PANDA_OUTFITS,
            price=380,
            icon='🐆',
            level_required=12,
            one_time_purchase=True,
            unlockable_id='closet_spotted'
        ),
        'closet_striped': ShopItem(
            id='closet_striped',
            name='Striped Panda',
            description='Bold striped pattern',
            category=ShopCategory.PANDA_OUTFITS,
            price=360,
            icon='🦓',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='closet_striped'
        ),
        'closet_tufted': ShopItem(
            id='closet_tufted',
            name='Tufted Panda',
            description='Charming fur tufts',
            category=ShopCategory.PANDA_OUTFITS,
            price=160,
            icon='🌿',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='closet_tufted'
        ),
        'closet_silky': ShopItem(
            id='closet_silky',
            name='Silky Panda',
            description='Silky smooth perfection',
            category=ShopCategory.PANDA_OUTFITS,
            price=290,
            icon='🎗️',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_silky'
        ),
        'closet_pixelated': ShopItem(
            id='closet_pixelated',
            name='Pixelated Panda',
            description='Retro pixel art fur style',
            category=ShopCategory.PANDA_OUTFITS,
            price=600,
            icon='🎮',
            level_required=18,
            one_time_purchase=True,
            unlockable_id='closet_pixelated'
        ),
        'closet_cosmic': ShopItem(
            id='closet_cosmic',
            name='Cosmic Panda',
            description='Swirling cosmic energy fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=1200,
            icon='🌌',
            level_required=22,
            one_time_purchase=True,
            unlockable_id='closet_cosmic'
        ),
        'closet_ember': ShopItem(
            id='closet_ember',
            name='Ember Panda',
            description='Glowing ember-like fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=550,
            icon='🔥',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_ember'
        ),
        'closet_glacial': ShopItem(
            id='closet_glacial',
            name='Glacial Panda',
            description='Frozen glacial fur texture',
            category=ShopCategory.PANDA_OUTFITS,
            price=520,
            icon='🧊',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_glacial'
        ),
        'closet_holographic': ShopItem(
            id='closet_holographic',
            name='Holographic Panda',
            description='Color-shifting holographic fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=1500,
            icon='✨',
            level_required=25,
            one_time_purchase=True,
            unlockable_id='closet_holographic'
        ),
        'closet_plush': ShopItem(
            id='closet_plush',
            name='Plush Panda',
            description='Stuffed animal soft fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=110,
            icon='🧸',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='closet_plush'
        ),
        'closet_windswept': ShopItem(
            id='closet_windswept',
            name='Windswept Panda',
            description='Dramatically windblown look',
            category=ShopCategory.PANDA_OUTFITS,
            price=170,
            icon='💨',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='closet_windswept'
        ),
        'closet_mossy': ShopItem(
            id='closet_mossy',
            name='Mossy Panda',
            description='Nature-covered mossy fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=270,
            icon='🌱',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_mossy'
        ),
        'closet_electric': ShopItem(
            id='closet_electric',
            name='Electric Panda',
            description='Crackling electric fur',
            category=ShopCategory.PANDA_OUTFITS,
            price=700,
            icon='⚡',
            level_required=20,
            one_time_purchase=True,
            unlockable_id='closet_electric'
        ),

        # New Hats - Shop
        'closet_space_helmet': ShopItem(
            id='closet_space_helmet',
            name='Space Helmet',
            description='Astronaut bubble helmet',
            category=ShopCategory.HATS,
            price=500,
            icon='🪐',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_space_helmet'
        ),
        'closet_samurai_helmet': ShopItem(
            id='closet_samurai_helmet',
            name='Samurai Helmet',
            description='Ancient samurai kabuto',
            category=ShopCategory.HATS,
            price=600,
            icon='⛩️',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_samurai_helmet'
        ),
        'closet_propeller_hat': ShopItem(
            id='closet_propeller_hat',
            name='Propeller Hat',
            description='Fun spinning propeller',
            category=ShopCategory.HATS,
            price=150,
            icon='🌀',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='closet_propeller_hat'
        ),
        'closet_beret': ShopItem(
            id='closet_beret',
            name='Artist Beret',
            description='French artist beret',
            category=ShopCategory.HATS,
            price=120,
            icon='🎨',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='closet_beret'
        ),
        'closet_sombrero': ShopItem(
            id='closet_sombrero',
            name='Sombrero',
            description='Festive wide-brim sombrero',
            category=ShopCategory.HATS,
            price=250,
            icon='🌮',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_sombrero'
        ),
        'closet_firefighter_hat': ShopItem(
            id='closet_firefighter_hat',
            name='Firefighter Helmet',
            description='Brave firefighter helmet',
            category=ShopCategory.HATS,
            price=300,
            icon='🚒',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_firefighter_hat'
        ),
        'closet_graduation_cap': ShopItem(
            id='closet_graduation_cap',
            name='Graduation Cap',
            description='Academic mortarboard',
            category=ShopCategory.HATS,
            price=180,
            icon='🎓',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='closet_graduation_cap'
        ),
        'closet_tiara': ShopItem(
            id='closet_tiara',
            name='Princess Tiara',
            description='Sparkling princess tiara',
            category=ShopCategory.HATS,
            price=450,
            icon='👸',
            level_required=12,
            one_time_purchase=True,
            unlockable_id='closet_tiara'
        ),
        'closet_straw_hat': ShopItem(
            id='closet_straw_hat',
            name='Straw Hat',
            description='Simple straw hat',
            category=ShopCategory.HATS,
            price=50,
            icon='🌾',
            level_required=1,
            one_time_purchase=True,
            unlockable_id='closet_straw_hat'
        ),
        'closet_ice_crown': ShopItem(
            id='closet_ice_crown',
            name='Ice Crown',
            description='Frozen crystal crown',
            category=ShopCategory.HATS,
            price=1500,
            icon='❄️',
            level_required=25,
            one_time_purchase=True,
            unlockable_id='closet_ice_crown'
        ),

        # New Shoes - Shop
        'closet_cowboy_boots': ShopItem(
            id='closet_cowboy_boots',
            name='Cowboy Boots',
            description='Western cowboy boots',
            category=ShopCategory.SHOES,
            price=120,
            icon='🤠',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='closet_cowboy_boots'
        ),
        'closet_ballet_shoes': ShopItem(
            id='closet_ballet_shoes',
            name='Ballet Slippers',
            description='Elegant ballet slippers',
            category=ShopCategory.SHOES,
            price=250,
            icon='🩰',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_ballet_shoes'
        ),
        'closet_moon_boots': ShopItem(
            id='closet_moon_boots',
            name='Moon Boots',
            description='Anti-gravity moon boots',
            category=ShopCategory.SHOES,
            price=500,
            icon='🌙',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_moon_boots'
        ),
        'closet_platform_shoes': ShopItem(
            id='closet_platform_shoes',
            name='Platform Shoes',
            description='Groovy platform shoes',
            category=ShopCategory.SHOES,
            price=150,
            icon='📐',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='closet_platform_shoes'
        ),
        'closet_ski_boots': ShopItem(
            id='closet_ski_boots',
            name='Ski Boots',
            description='Mountain ski boots',
            category=ShopCategory.SHOES,
            price=280,
            icon='⛷️',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_ski_boots'
        ),
        'closet_glass_slippers': ShopItem(
            id='closet_glass_slippers',
            name='Glass Slippers',
            description='Fairy tale glass slippers',
            category=ShopCategory.SHOES,
            price=600,
            icon='💎',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_glass_slippers'
        ),
        'closet_steel_boots': ShopItem(
            id='closet_steel_boots',
            name='Steel Boots',
            description='Heavy armored steel boots',
            category=ShopCategory.SHOES,
            price=350,
            icon='🛡️',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='closet_steel_boots'
        ),
        'closet_neon_kicks': ShopItem(
            id='closet_neon_kicks',
            name='Neon Kicks',
            description='Light-up neon sneakers',
            category=ShopCategory.SHOES,
            price=180,
            icon='💡',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='closet_neon_kicks'
        ),
        'closet_bunny_slippers_new': ShopItem(
            id='closet_bunny_slippers_new',
            name='Bunny Slippers',
            description='Adorable bunny slippers',
            category=ShopCategory.SHOES,
            price=60,
            icon='🐰',
            level_required=1,
            one_time_purchase=True,
            unlockable_id='closet_bunny_slippers_new'
        ),
        'closet_lava_boots': ShopItem(
            id='closet_lava_boots',
            name='Lava Boots',
            description='Fireproof lava walking boots',
            category=ShopCategory.SHOES,
            price=1200,
            icon='🔥',
            level_required=20,
            one_time_purchase=True,
            unlockable_id='closet_lava_boots'
        ),

        # New Accessories - Shop
        'closet_diamond_ring': ShopItem(
            id='closet_diamond_ring',
            name='Diamond Ring',
            description='Sparkly diamond ring',
            category=ShopCategory.ACCESSORIES,
            price=500,
            icon='💍',
            level_required=15,
            one_time_purchase=True,
            unlockable_id='closet_diamond_ring'
        ),
        'closet_feather_boa': ShopItem(
            id='closet_feather_boa',
            name='Feather Boa',
            description='Glamorous feather boa',
            category=ShopCategory.ACCESSORIES,
            price=250,
            icon='🪶',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_feather_boa'
        ),
        'closet_pocket_watch_acc': ShopItem(
            id='closet_pocket_watch_acc',
            name='Pocket Watch',
            description='Antique pocket watch',
            category=ShopCategory.ACCESSORIES,
            price=280,
            icon='🕰️',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_pocket_watch_acc'
        ),
        'closet_magic_wand': ShopItem(
            id='closet_magic_wand',
            name='Magic Wand',
            description='Sparkly magic wand',
            category=ShopCategory.ACCESSORIES,
            price=450,
            icon='🪄',
            level_required=12,
            one_time_purchase=True,
            unlockable_id='closet_magic_wand'
        ),
        'closet_pearl_necklace': ShopItem(
            id='closet_pearl_necklace',
            name='Pearl Necklace',
            description='Elegant pearl necklace',
            category=ShopCategory.ACCESSORIES,
            price=300,
            icon='🦪',
            level_required=8,
            one_time_purchase=True,
            unlockable_id='closet_pearl_necklace'
        ),
        'closet_bandana': ShopItem(
            id='closet_bandana',
            name='Cool Bandana',
            description='Stylish bandana',
            category=ShopCategory.ACCESSORIES,
            price=100,
            icon='🏴',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='closet_bandana'
        ),
        'closet_compass': ShopItem(
            id='closet_compass',
            name='Golden Compass',
            description='Adventure compass',
            category=ShopCategory.ACCESSORIES,
            price=130,
            icon='🧭',
            level_required=3,
            one_time_purchase=True,
            unlockable_id='closet_compass'
        ),
        'closet_camera': ShopItem(
            id='closet_camera',
            name='Polaroid Camera',
            description='Retro instant camera',
            category=ShopCategory.ACCESSORIES,
            price=220,
            icon='📸',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='closet_camera'
        ),
        'closet_telescope_acc': ShopItem(
            id='closet_telescope_acc',
            name='Mini Telescope',
            description='Tiny telescope monocle',
            category=ShopCategory.ACCESSORIES,
            price=350,
            icon='🔭',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='closet_telescope_acc'
        ),
        'closet_phoenix_feather': ShopItem(
            id='closet_phoenix_feather',
            name='Phoenix Feather',
            description='Legendary phoenix tail feather',
            category=ShopCategory.ACCESSORIES,
            price=1500,
            icon='🔥',
            level_required=25,
            one_time_purchase=True,
            unlockable_id='closet_phoenix_feather'
        ),
        
        # Weapons - Melee
        'weapon_wooden_sword': ShopItem(
            id='weapon_wooden_sword',
            name='Wooden Sword',
            description='A basic training sword made of wood',
            category=ShopCategory.WEAPONS,
            price=100,
            icon='🗡️',
            level_required=1,
            one_time_purchase=True,
            unlockable_id='wooden_sword'
        ),
        'weapon_bamboo_staff': ShopItem(
            id='weapon_bamboo_staff',
            name='Bamboo Staff',
            description='A sturdy staff made from ancient bamboo',
            category=ShopCategory.WEAPONS,
            price=150,
            icon='🎋',
            level_required=1,
            one_time_purchase=True,
            unlockable_id='bamboo_staff'
        ),
        'weapon_iron_sword': ShopItem(
            id='weapon_iron_sword',
            name='Iron Sword',
            description='A reliable blade forged from iron',
            category=ShopCategory.WEAPONS,
            price=300,
            icon='⚔️',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='iron_sword'
        ),
        'weapon_katana': ShopItem(
            id='weapon_katana',
            name='Panda Katana',
            description='A legendary blade passed down through generations',
            category=ShopCategory.WEAPONS,
            price=800,
            icon='🗡️',
            level_required=10,
            one_time_purchase=True,
            unlockable_id='katana'
        ),
        
        # Weapons - Ranged
        'weapon_slingshot': ShopItem(
            id='weapon_slingshot',
            name='Bamboo Slingshot',
            description='A simple slingshot for launching bamboo shoots',
            category=ShopCategory.WEAPONS,
            price=120,
            icon='🏹',
            level_required=1,
            one_time_purchase=True,
            unlockable_id='slingshot'
        ),
        'weapon_bow': ShopItem(
            id='weapon_bow',
            name='Hunting Bow',
            description='A well-crafted bow for ranged combat',
            category=ShopCategory.WEAPONS,
            price=400,
            icon='🏹',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='bow'
        ),
        
        # Weapons - Magic
        'weapon_magic_wand': ShopItem(
            id='weapon_magic_wand',
            name='Bamboo Wand',
            description='A wand imbued with natural magic',
            category=ShopCategory.WEAPONS,
            price=500,
            icon='🪄',
            level_required=5,
            one_time_purchase=True,
            unlockable_id='magic_wand'
        ),
    }
    
    def __init__(self, save_path: Optional[Path] = None):
        """
        Initialize shop system.
        
        Args:
            save_path: Path to save purchase data
        """
        self.save_path = save_path or Path.home() / '.ps2_texture_sorter' / 'shop.json'
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.purchased_items: Set[str] = set()
        self.purchase_history: List[Dict] = []
        
        # Load saved data
        self.load()
    
    def get_items_by_category(self, category: ShopCategory, user_level: Optional[int] = None) -> List[ShopItem]:
        """
        Get items in a category that user can see.
        
        Args:
            category: Shop category
            user_level: User's current level (None means show all items)
            
        Returns:
            List of items in category
        """
        items = [
            item for item in self.CATALOG.values()
            if item.category == category and (user_level is None or item.level_required <= user_level)
        ]
        return sorted(items, key=lambda x: x.price)
    
    def get_all_categories(self) -> List[ShopCategory]:
        """Get all shop categories."""
        return list(ShopCategory)
    
    def can_purchase(self, item_id: str, balance: int) -> Tuple[bool, str]:
        """
        Check if item can be purchased.
        
        Args:
            item_id: Item ID
            balance: User's money balance
            
        Returns:
            Tuple of (can_purchase, reason)
        """
        if item_id not in self.CATALOG:
            return False, "Item not found"
        
        item = self.CATALOG[item_id]
        
        # Check if already purchased
        if item.one_time_purchase and item_id in self.purchased_items:
            return False, "Already purchased"
        
        # Check balance
        if balance < item.price:
            return False, f"Insufficient funds (need ${item.price}, have ${balance})"
        
        return True, "OK"
    
    def purchase_item(self, item_id: str, balance: int, level: int) -> Tuple[bool, str, Optional[ShopItem]]:
        """
        Purchase an item.
        
        Args:
            item_id: Item ID
            balance: User's money balance
            level: User's level
            
        Returns:
            Tuple of (success, message, item)
        """
        if item_id not in self.CATALOG:
            return False, "Item not found", None
        
        item = self.CATALOG[item_id]
        
        # Check level requirement
        if level < item.level_required:
            return False, f"Level {item.level_required} required", None
        
        # Check if can purchase
        can_buy, reason = self.can_purchase(item_id, balance)
        if not can_buy:
            return False, reason, None
        
        # Record purchase
        self.purchased_items.add(item_id)
        self.purchase_history.append({
            'item_id': item_id,
            'item_name': item.name,
            'price': item.price,
            'timestamp': datetime.now().isoformat(),
        })
        
        self.save()
        
        logger.info(f"Purchased {item.name} for ${item.price}")
        return True, f"Purchased {item.name}!", item
    
    def is_purchased(self, item_id: str) -> bool:
        """Check if item has been purchased."""
        return item_id in self.purchased_items
    
    def get_purchase_history(self, count: int = 10) -> List[Dict]:
        """Get recent purchase history."""
        return self.purchase_history[-count:]
    
    def save(self):
        """Save shop data to file."""
        try:
            data = {
                'purchased_items': list(self.purchased_items),
                'purchase_history': self.purchase_history[-self.MAX_PURCHASE_HISTORY:],
            }
            
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved shop data to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save shop data: {e}")
    
    def load(self):
        """Load shop data from file."""
        try:
            if self.save_path.exists():
                with open(self.save_path, 'r') as f:
                    data = json.load(f)
                
                self.purchased_items = set(data.get('purchased_items', []))
                self.purchase_history = data.get('purchase_history', [])
                
                logger.info(f"Loaded shop data. {len(self.purchased_items)} items purchased")
            else:
                logger.info("No saved shop data found. Starting fresh.")
        except Exception as e:
            logger.error(f"Failed to load shop data: {e}")
