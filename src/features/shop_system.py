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
    ACCESSORIES = "accessories"
    UPGRADES = "upgrades"
    SPECIAL = "special"
    FOOD = "food"
    TOYS = "toys"


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
            category=ShopCategory.ACCESSORIES,
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
