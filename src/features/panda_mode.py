"""
Panda Mode - Fun animations and quotes during processing
Random panda facts, progress celebrations, and Easter eggs
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time

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


class PandaMode:
    """Manages panda animations, facts, and Easter eggs."""
    
    # Comprehensive tooltip system
    TOOLTIPS = {
        'sort_button': {
            'normal': [
                "Click to sort your textures into organized folders",
                "Begin the texture organization process",
                "Start sorting textures by category and LOD level",
                "Organize your textures with intelligent sorting",
                "Sort textures into their proper directories",
                "Initiate the automated texture sorting workflow"
            ],
            'vulgar': [
                "Click this to sort your damn textures. It's not rocket science, Karen.",
                "Organize these bad boys into folders. Like Marie Kondo but with more profanity.",
                "Sort this sh*t out. Literally. That's what the button does.",
                "Time to unfuck your texture directory structure.",
                "Click here unless you enjoy chaos and madness.",
                "Make your textures less of a clusterfuck with one click."
            ]
        },
        'convert_button': {
            'normal': [
                "Convert textures to different formats",
                "Transform your textures into the desired format",
                "Begin batch texture format conversion",
                "Convert texture files to supported formats",
                "Process and convert texture formats efficiently",
                "Start the texture conversion process"
            ],
            'vulgar': [
                "Turn your textures into whatever the hell format you need.",
                "Convert this sh*t. PNG, DDS, whatever floats your boat.",
                "Magic button that transforms textures. No rabbits or hats required.",
                "Because apparently your textures are in the wrong goddamn format.",
                "Click to unfuck your texture formats.",
                "Convert or die. Well, not die. But your project might."
            ]
        },
        'settings_button': {
            'normal': [
                "Open settings and preferences",
                "Configure application options",
                "Adjust your preferences and settings",
                "Access configuration options",
                "Customize your application settings",
                "Modify application behavior and appearance"
            ],
            'vulgar': [
                "Tweak sh*t. Make it yours. Go nuts.",
                "Settings, preferences, all that boring but necessary crap.",
                "Click here if you're picky about how things work. We don't judge.",
                "Configure this bad boy to your heart's content.",
                "Mess with settings until something breaks. Then undo.",
                "For control freaks and perfectionists. You know who you are."
            ]
        },
        'file_selection': {
            'normal': [
                "Select files to process",
                "Choose input or output file locations",
                "Browse for files and directories",
                "Pick your source or destination files",
                "Select the files you want to work with",
                "Choose your file path"
            ],
            'vulgar': [
                "Point me to your damn files already.",
                "Show me where you hid your textures, you sneaky bastard.",
                "Pick a file. Any file. I don't have all day.",
                "File picker. Because apparently you can't just type the path.",
                "Navigate this hellscape of directories and find your files.",
                "Choose wisely. Or don't. I'm not your mother."
            ]
        },
        'category_selection': {
            'normal': [
                "Select texture categories to process",
                "Choose which categories to include",
                "Filter by texture category",
                "Pick specific texture types",
                "Select categories for organization",
                "Choose texture classification groups"
            ],
            'vulgar': [
                "Pick your texture flavor. Diffuse? Normal? Whatever the f*ck?",
                "Choose categories or process everything. Your funeral.",
                "Category picker. For when you're too good for all textures.",
                "Filter this sh*t by category. Be selective.",
                "What kind of textures are we destroying today?",
                "Pick a category. Or don't. Chaos is always an option."
            ]
        },
        'lod_detection': {
            'normal': [
                "Toggle automatic LOD level detection",
                "Enable or disable LOD detection",
                "Automatically identify texture LOD levels",
                "Detect Level of Detail in texture names",
                "Turn LOD detection on or off",
                "Configure automatic LOD identification"
            ],
            'vulgar': [
                "Let the panda figure out your LOD levels. He's smart like that.",
                "Auto-detect LODs because manually sorting is for masochists.",
                "Toggle LOD magic. On or off. Your choice.",
                "Enable this unless you hate yourself and your free time.",
                "LOD detection. Like facial recognition but for textures.",
                "Turn this on and let the algorithm do the heavy lifting."
            ]
        },
        'batch_operations': {
            'normal': [
                "Perform operations on multiple files",
                "Process files in batches",
                "Execute batch operations",
                "Run operations on selected files",
                "Process multiple files simultaneously",
                "Perform bulk file operations"
            ],
            'vulgar': [
                "Process a sh*tload of files at once. Because efficiency.",
                "Batch operations for people with actual work to do.",
                "Do many things to many files. It's beautiful.",
                "Because processing one file at a time is for chumps.",
                "Bulk operations. Like Costco but for file processing.",
                "Handle multiple files like a goddamn professional."
            ]
        },
        'export_button': {
            'normal': [
                "Export processed results",
                "Save your organized textures",
                "Export to destination folder",
                "Complete and export the operation",
                "Save the processed files",
                "Finalize and export your work"
            ],
            'vulgar': [
                "Export this sh*t before you lose it.",
                "Save your work unless you enjoy starting over.",
                "Click to yeet your textures to their new home.",
                "Export or suffer the consequences of lost work.",
                "Finalize this motherf*cker and export.",
                "Save button. Use it. Don't be a hero."
            ]
        },
        'preview_button': {
            'normal': [
                "Preview changes before applying",
                "See what will happen before committing",
                "Preview the results",
                "Check before you wreck",
                "Preview your changes",
                "Look before you leap"
            ],
            'vulgar': [
                "Preview this sh*t before you commit. Trust nobody.",
                "Look at what's about to happen. Prevent disasters.",
                "Preview mode. For the paranoid. And the smart.",
                "See the future. Well, the preview. Same difference.",
                "Check your work before the universe does.",
                "Preview because CTRL+Z only goes so far."
            ]
        },
        'search_button': {
            'normal': [
                "Search for specific textures",
                "Find files by name or pattern",
                "Search through your textures",
                "Locate specific files",
                "Search and filter files",
                "Find what you're looking for"
            ],
            'vulgar': [
                "Find your sh*t. It's in here somewhere.",
                "Search function. Because you lost your damn files again.",
                "Where the f*ck is that texture? Let's find out.",
                "Search bar. Type stuff. Get results. Revolutionary.",
                "Find your needle in this texture haystack.",
                "Lost something? Course you did. That's why this exists."
            ]
        },
        'analysis_button': {
            'normal': [
                "Analyze texture properties",
                "Run detailed file analysis",
                "Examine texture characteristics",
                "Perform deep analysis",
                "Get detailed texture information",
                "Analyze file structure and metadata"
            ],
            'vulgar': [
                "Analyze the hell out of these textures.",
                "Deep dive into texture properties. Get nerdy with it.",
                "Analysis mode. For when you need ALL the information.",
                "Let's get technical. Really f*cking technical.",
                "Examine these textures like a CSI investigator.",
                "Analysis button. Nerd mode activated."
            ]
        },
        'favorites_button': {
            'normal': [
                "Access your favorite presets",
                "Quick access to saved favorites",
                "View bookmarked items",
                "Open favorite configurations",
                "Access frequently used settings",
                "View saved favorites"
            ],
            'vulgar': [
                "Your favorites. The sh*t you actually use.",
                "Quick access to your go-to stuff.",
                "Favorites list. The VIP section.",
                "The greatest hits of your workflow.",
                "Your favorite settings because you're a creature of habit.",
                "Bookmarks for the modern age. Still useful."
            ]
        },
        'recent_files': {
            'normal': [
                "View recently accessed files",
                "See your recent work",
                "Access recent projects",
                "Quick access to recent files",
                "View file history",
                "Open recently used files"
            ],
            'vulgar': [
                "Recent files. Because your memory is sh*t.",
                "The stuff you worked on recently. Remember?",
                "Recent history. NSA would be proud.",
                "Your greatest hits from this week.",
                "Recent files list. Memory lane but useful.",
                "Quick access to what you were just f*cking with."
            ]
        },
        'theme_selector': {
            'normal': [
                "Change application theme",
                "Select color scheme",
                "Customize appearance",
                "Choose your preferred theme",
                "Switch between light and dark modes",
                "Personalize the interface"
            ],
            'vulgar': [
                "Make it pretty. Or dark. Whatever helps you see.",
                "Theme selector. Because aesthetics matter, damn it.",
                "Change colors until your eyes don't hurt.",
                "Pick a theme. Light mode users are psychopaths, btw.",
                "Customize this bitch to match your vibe.",
                "Make it yours. Paint that interface."
            ]
        },
        'cursor_selector': {
            'normal': [
                "Choose cursor style",
                "Select custom cursor",
                "Change pointer appearance",
                "Pick your cursor preference",
                "Customize mouse pointer",
                "Select cursor theme"
            ],
            'vulgar': [
                "Cursor styles. Because why the hell not?",
                "Change your pointer. Make it fancy.",
                "Cursor customization. We went there.",
                "Pick a cursor. It's the little things.",
                "Customize your pointy thing.",
                "Make your cursor less boring than default."
            ]
        },
        'sound_settings': {
            'normal': [
                "Configure audio preferences",
                "Adjust sound settings",
                "Control notification sounds",
                "Set audio options",
                "Manage sound effects",
                "Configure audio feedback"
            ],
            'vulgar': [
                "Sound settings. Make it loud. Or mute. Your call.",
                "Audio controls for when you want beeps and boops.",
                "Turn sounds on or off. We won't judge.",
                "Sound effects. For that authentic computer experience.",
                "Audio settings. Beep boop motherf*cker.",
                "Configure your audio. Or silence everything. Both valid."
            ]
        },
        'tutorial_button': {
            'normal': [
                "View tutorial and guides",
                "Learn how to use the application",
                "Access help documentation",
                "Get started with tutorials",
                "View step-by-step guides",
                "Learn the basics"
            ],
            'vulgar': [
                "Tutorial. Because reading docs is apparently hard.",
                "Learn how to use this thing. RTFM made easy.",
                "Help for the helpless. No shame.",
                "Tutorial button. For when you're lost AF.",
                "Learn sh*t here. It's actually helpful.",
                "Education time. Get learned."
            ]
        },
        'help_button': {
            'normal': [
                "Get help and support",
                "Access help resources",
                "Find answers to questions",
                "View help documentation",
                "Get assistance",
                "Access support materials"
            ],
            'vulgar': [
                "Help! I've fallen and I can't use software!",
                "Cry for help button. We're here for you.",
                "Get help before you break something.",
                "Help docs. Read them. Please.",
                "Assistance for the confused.",
                "Help button. Use it. Don't be a hero."
            ]
        },
        'about_button': {
            'normal': [
                "About this application",
                "View version information",
                "See application details",
                "Learn about the software",
                "View credits and information",
                "Application information"
            ],
            'vulgar': [
                "About page. Who made this? Why? Find out here.",
                "Version info and other boring but important sh*t.",
                "Credits to the poor bastards who coded this.",
                "About section. Meet your digital overlords.",
                "Who made this? Why? All answered here.",
                "Application info. For the curious."
            ]
        },
        'undo_button': {
            'normal': [
                "Undo last action",
                "Reverse previous operation",
                "Go back one step",
                "Undo recent changes",
                "Revert last action",
                "Step backward"
            ],
            'vulgar': [
                "CTRL+Z. The panic button. The savior.",
                "Unfuck what you just f*cked up.",
                "Undo. Because mistakes happen. A lot.",
                "Reverse that disaster you just created.",
                "Time travel button. Go back. Fix sh*t.",
                "Undo. Your second chance at not screwing up."
            ]
        },
        'redo_button': {
            'normal': [
                "Redo undone action",
                "Reapply last undone change",
                "Step forward",
                "Redo operation",
                "Restore undone action",
                "Move forward"
            ],
            'vulgar': [
                "Redo. Because you undid too much, idiot.",
                "CTRL+Y. Forward time travel.",
                "Redo what you just undid. Make up your mind.",
                "Go forward. Stop going backward.",
                "Redo button. For the indecisive.",
                "F*ck it, put it back the way it was."
            ]
        },
        'input_browse': {
            'normal': [
                "Browse for the folder containing your texture files",
                "Select the input directory with your textures",
                "Choose the source folder for texture processing",
                "Pick the directory to read textures from",
                "Navigate to your texture input folder"
            ],
            'vulgar': [
                "Find your damn texture folder. It's somewhere on that hard drive.",
                "Browse for input. Like Tinder but for file directories.",
                "Point me to your textures, you beautiful disaster.",
                "Navigate the digital jungle to find your texture stash.",
                "Show me where the goods are. The texture goods.",
                "Pick a folder. It's not that deep. Well, maybe it is.",
                "File browsing: the Windows Explorer safari adventure.",
                "Where'd you put those textures? Let's go find out."
            ]
        },
        'output_browse': {
            'normal': [
                "Choose where to save the organized textures",
                "Select the destination folder for sorted textures",
                "Pick an output directory for your results",
                "Set the target folder for organized files",
                "Choose the output location for sorted textures"
            ],
            'vulgar': [
                "Where do you want this organized mess dumped?",
                "Pick a destination. The textures need a new home.",
                "Choose wisely. This is where the magic ends up.",
                "Output folder. Where dreams of organization become reality.",
                "Select where to yeet your sorted textures.",
                "Destination please! Like an Uber but for files.",
                "Where should I put this sh*t? Literally your call.",
                "Pick an output or I'll choose your desktop. Don't test me."
            ]
        },
        'detect_duplicates': {
            'normal': [
                "Find and handle duplicate texture files",
                "Detect identical textures using file hashing",
                "Identify copies and duplicates in your collection",
                "Scan for redundant duplicate texture files",
                "Check for duplicate textures to save disk space"
            ],
            'vulgar': [
                "Find duplicate textures. Trust issues? Same.",
                "Duplicate detection. Because copying is only flattering sometimes.",
                "Spot the clones. Like a texture witness protection program.",
                "Find duplicates before your hard drive files a complaint.",
                "Duplicate finder. CTRL+C CTRL+V consequences detector.",
                "Because apparently copy-paste got out of hand.",
                "Hunt down those sneaky identical textures.",
                "Duplicate detection: the 'who wore it better' for textures."
            ]
        },
        'group_lods': {
            'normal': [
                "Keep LOD variants together in the same folder",
                "Group Level of Detail textures by their base name",
                "Organize LOD levels into unified groups",
                "Bundle related LOD textures together",
                "Group LOD variants for easy management"
            ],
            'vulgar': [
                "Group LODs together. They're like a dysfunctional family.",
                "Keep LOD buddies together. Separation anxiety is real.",
                "LOD grouping. Because nobody puts LOD-baby in a corner.",
                "Bundle those LODs like a cozy texture family reunion.",
                "Keep the LOD crew together. Squad goals.",
                "Group LODs. Like organizing your sock drawer but nerdier.",
                "LOD family reunion time. Get them all in one folder.",
                "No LOD left behind. We group them ALL."
            ]
        },
        'achievements_tab': {
            'normal': [
                "View your achievements and progress milestones",
                "Track your accomplishments and earned badges",
                "See which achievements you've unlocked"
            ],
            'vulgar': [
                "Check your trophies, you overachiever.",
                "Achievement log. Proof you actually did something.",
                "Your bragging rights live here.",
                "Look at all the sh*t you've accomplished. Proud?",
                "Achievements. For people who need validation.",
                "Gold stars and participation trophies. Knock yourself out."
            ]
        },
        'shop_tab': {
            'normal': [
                "Opens the reward store where earned points can be spent",
                "Browse and purchase items with your earned currency",
                "Spend your points on cosmetics and upgrades"
            ],
            'vulgar': [
                "This is the loot cave. Spend your shiny points, idiot.",
                "You did work. Now buy dumb cosmetic crap.",
                "Click here to exchange grind for dopamine.",
                "The shop. Where your hard-earned money goes to die.",
                "Buy stuff. Waste points. Live your best life.",
                "Shopping spree time. Your wallet (points) won't survive."
            ]
        },
        'shop_buy_button': {
            'normal': [
                "Purchase this item with your currency",
                "Buy this item from the shop",
                "Complete the purchase"
            ],
            'vulgar': [
                "Yeet your money at this item. Do it.",
                "Buy it before someone else doesn't.",
                "Take my money! Except it's points. Whatever.",
                "Purchase this bad boy. You deserve it. Maybe.",
                "Click buy. Instant regret or joy. 50/50.",
                "Add to cart? Nah. Just buy the damn thing."
            ]
        },
        'shop_category_button': {
            'normal': [
                "Filter shop items by this category",
                "View items in this category",
                "Browse this section of the shop"
            ],
            'vulgar': [
                "Filter the shop. Because scrolling is for peasants.",
                "Category filter. Find your poison faster.",
                "Browse this section. There's good sh*t in here.",
                "Click to see what's in this category of nonsense."
            ]
        },
        'rewards_tab': {
            'normal': [
                "View all unlockable rewards and their requirements",
                "See what rewards you can earn by completing goals",
                "Track your progress toward unlocking rewards"
            ],
            'vulgar': [
                "Your loot table. See what you can unlock.",
                "Rewards page. Dangle carrots in front of yourself.",
                "All the shiny things you haven't earned yet.",
                "Check what's locked and cry about it.",
                "Reward tracker. Motivation through materialism.",
                "See the prizes. Want them. Work for them. Simple."
            ]
        },
        'closet_tab': {
            'normal': [
                "Customize your panda's appearance with outfits and accessories",
                "Dress up your panda companion with unlocked items",
                "Change your panda's look and style"
            ],
            'vulgar': [
                "Dress up your panda. Fashion show time.",
                "Panda wardrobe. Because even pandas need style.",
                "Outfit your furry friend. Don't make it weird.",
                "Panda closet. It's like The Sims but with bamboo.",
                "Fashion crimes against pandas start here.",
                "Makeover time! Make your panda look fabulous or ridiculous."
            ]
        },
        'browser_browse_button': {
            'normal': [
                "Select a directory to browse for texture files",
                "Open folder picker to navigate to your files",
                "Choose a folder to browse its contents"
            ],
            'vulgar': [
                "Pick a folder. Any folder. Let's see what's inside.",
                "Browse button. Because typing paths is for masochists.",
                "Point me to your files. I'll judge them.",
                "Folder picker. Navigate your digital hoarding."
            ]
        },
        'browser_refresh_button': {
            'normal': [
                "Refresh the file list to show current directory contents",
                "Reload the current directory listing",
                "Update the file browser display"
            ],
            'vulgar': [
                "Refresh. In case something magically changed.",
                "Hit refresh like you're checking your ex's profile.",
                "Reload. Because maybe it's different this time. (It's not.)",
                "F5 energy in button form."
            ]
        },
        'browser_search': {
            'normal': [
                "Search for files by name in the current directory",
                "Filter displayed files by search term",
                "Type to find specific files"
            ],
            'vulgar': [
                "Find your damn files. Type something.",
                "Search bar. For when you can't find sh*t.",
                "Like Google but for your messy folder.",
                "Ctrl+F vibes. Find that needle in the haystack."
            ]
        },
        'browser_show_all': {
            'normal': [
                "Toggle between showing only textures or all file types",
                "Show all files, not just supported texture formats",
                "Include non-texture files in the listing"
            ],
            'vulgar': [
                "Show EVERYTHING. Even the weird files.",
                "All files mode. Including your shame.",
                "Toggle this to see non-texture files too.",
                "Show all. Because you're nosy like that."
            ]
        }
    }
    
    # Panda drawn animation frames
    PANDA_FRAMES = {
        'idle': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　●　　● |
  |　　　( _●_) ミ
 彡､　　　|∪| ､｀＼
/　＿＿ ヽノ /´>　)
(＿＿＿）　　/ (_／
 |　　　　　　　|
 | ／＼　　　　|
 | /　　　)　　　|
 ∪　　（　　　＼
　　　　　＼＿＿)
            """,
        ],
        'working': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　●　　● |  💻
  |　　　( _●_) ミ
 彡､　　　|∪| ､｀＼
/　＿＿ ヽノ /´>　)
            """,
            """
    ∩＿＿∩
    |ノ　　　　ヽ  💻
   /　●　　● |
  |　　　( _●_) ミ
 彡､　　　|∪| ､｀＼
/　＿＿ ヽノ /´>　)
            """,
        ],
        'celebrating': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　◕　　◕ |  🎉
  |　　　( _●_) ミ
 彡､　　　|∪| ､｀＼  ✨
/　＿＿ ヽノ /´>　)
            """,
        ],
        'sleeping': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　－　　－ |  💤
  |　　　( _●_) ミ
 彡､　　　|∪| ､｀＼
/　＿＿ ヽノ /´>　)
            """,
        ],
        'rage': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　✖　　✖ |  💢
  |　　　( _●_) ミ  🔥
 彡､　　　|∪| ､｀＼
/　＿＿ ヽノ /´>　)
            """,
        ],
        'drunk': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　⊙　　⊙ |  🍺
  |　　　( _●_) ミ
 彡､　　　|∪| ､｀＼
/　＿＿ ヽノ /´>　)  🥴
            """,
        ],
        'sarcastic': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　◔　　◔ |  🙄
  |　　　( _●_) ミ
 彡､　　　|∪| ､｀＼
/　＿＿ ヽノ /´>　)
            """,
        ],
        'existential': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　○　　○ |  🌌
  |　　　( _●_) ミ  ✨
 彡､　　　|∪| ､｀＼
/　＿＿ ヽノ /´>　)  💭
            """,
        ],
        'tech_support': [
            """
    ∩＿＿∩
    |ノ　　　　ヽ
   /　●　　● |  📞
  |　　　( _●_) ミ  💼
 彡､　　　|∪| ､｀＼
/　＿＿ ヽノ /´>　)
            """,
        ],
    }
    
    # Panda facts
    PANDA_FACTS = [
        "Pandas eat for about 12 hours a day! 🎋",
        "A panda's paw has six digits—five fingers and a thumb!",
        "Giant pandas are excellent tree climbers. 🌲",
        "Pandas communicate through various vocalizations and scent marking.",
        "Baby pandas are about the size of a stick of butter when born!",
        "Pandas have been on Earth for 2-3 million years.",
        "An adult panda can eat 12-38kg of bamboo per day!",
        "Pandas spend 14-16 hours a day eating.",
        "The black patches on a panda's eyes may help them recognize each other.",
        "Pandas are solitary animals by nature. 🐼",
        "A panda's digestive system is actually designed for meat, not bamboo!",
        "Pandas can swim and have been known to enjoy water.",
        "The red panda is not actually related to the giant panda!",
        "Pandas have lived on Earth for about 8 million years.",
        "A panda's bite is almost as strong as a jaguar's!",
    ]
    
    # Regular motivational quotes
    REGULAR_QUOTES = [
        "Great progress! Keep going! 🚀",
        "You're doing amazing! ⭐",
        "Texture sorting like a pro! 💪",
        "Smooth as bamboo! 🎋",
        "Outstanding work! 🌟",
        "Almost there, keep it up! 💯",
        "Fantastic job! 🎉",
        "You're on fire! 🔥",
        "Incredible progress! 👏",
        "Master sorter in action! 👑",
        "Crushing it! 💥",
        "Stellar performance! ⭐",
        "Keep up the great work! 💪",
        "You're unstoppable! 🚀",
        "Excellent sorting! ✨",
    ]
    
    # Vulgar mode quotes (opt-in, funny but edgy)
    VULGAR_QUOTES = [
        "Holy sh*t, you're fast! 🔥",
        "Damn, you're good at this! 💯",
        "F*ck yeah, great progress! 🎉",
        "Badass sorting skills! 💪",
        "Hell yeah, keep crushing it! 💥",
        "That's f*cking impressive! ⭐",
        "Damn son, slow down! 🚀",
        "You're a f*cking legend! 👑",
        "Holy crap, almost done! 🎯",
        "Sh*t yeah, excellent work! ✨",
        "Damn right, you're killing it! 💀",
        "F*ck me, that's fast! ⚡",
        "Badass texture ninja! 🥷",
        "Goddamn professional! 💼",
        "Beast mode activated! 🦁",
    ]
    
    # Milestone messages
    MILESTONE_MESSAGES = {
        10: "10 textures sorted! You're getting started! 🌱",
        50: "50 textures! You're getting the hang of it! 💚",
        100: "100 textures! Century mark! 💯",
        500: "500 textures! Half a thousand! 🎯",
        1000: "1,000 textures! That's a milestone! 🏆",
        5000: "5,000 textures! You're unstoppable! 🚀",
        10000: "10,000 textures! TEN THOUSAND! 🌟",
        25000: "25,000 textures! Quarter way to 100K! ⭐",
        50000: "50,000 textures! FIFTY THOUSAND! 👑",
        100000: "100,000 textures! ONE HUNDRED THOUSAND! 💎",
        200000: "200,000 textures! LEGENDARY STATUS! 🏆✨",
    }
    
    # Easter egg triggers
    EASTER_EGGS = {
        'konami': '🎮 Up, Up, Down, Down, Left, Right, Left, Right, B, A, Start!',
        'bamboo': '🎋 Unlimited bamboo mode activated!',
        'ninja': '🥷 Stealth sorting engaged!',
        'turbo': '⚡ TURBO MODE ENGAGED!',
        'disco': '🕺 Disco panda mode!',
        'panda_rage': '💢 PANDA RAGE MODE ACTIVATED! CLICK COUNT: 10!',
        'thousand_files': '🏆 HOLY SH*T! 1000 FILES SORTED! LEGENDARY!',
        'midnight_madness': '🌙 WHY ARE YOU AWAKE AT 3 AM? GO TO SLEEP!',
        'indecisive': '😤 MAKE UP YOUR DAMN MIND ALREADY! (5 cancellations)',
        'deja_vu': '👻 Wait... have we done this before? DÉJÀ VU!',
        'tab_dancer': '💃 TAB SWITCHING CHAMPION! PANDA DANCE MODE!',
        'zero_bytes': '🤨 Are you serious? A 0 byte file? REALLY?',
        'same_folder': '🔄 SAME FOLDER TWICE? Groundhog Day vibes...',
        'hover_stalker': '😒 Been hovering for 30 seconds. Need something?',
        'achievement_unlocked': '🎮 ACHIEVEMENT UNLOCKED!',
        'speed_demon': '⚡ SPEED DEMON! Processing faster than the speed of light!',
        'night_owl': '🦉 NIGHT OWL MODE! Coffee count: Infinite',
        'perfectionist': '💯 PERFECTIONIST DETECTED! Redoing the same file...',
        'chaos_mode': '🌀 CHAOS MODE! Everything is fine. Probably.',
        'zen_master': '☯️ ZEN MASTER: 10,000 files organized. Inner peace achieved.',
        'coffee_break': '☕ TIME FOR A COFFEE BREAK! You earned it.',
        'rubber_duck': '🦆 Rubber duck debugging mode activated!',
        'matrix': '💚 THERE IS NO SPOON. Only textures.',
        'developer': '👨‍💻 DEVELOPER MODE: Now you see the Matrix.',
    }
    
    # Panda click responses
    PANDA_CLICK_RESPONSES = {
        'normal': [
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
        ],
        'vulgar': [
            "🐼 What? I'm busy eating bamboo here.",
            "🐼 Stop poking me, dammit.",
            "🐼 Yes? Make it quick.",
            "🐼 I'm a panda, not a button. Chill.",
            "🐼 *annoyed panda noises*",
            "🐼 Click me one more time, I dare you.",
            "🐼 Personal space? Ever heard of it?",
            "🐼 This better be important.",
            "🐼 What now?!",
            "🐼 I'm working here! Sort of.",
        ],
    }
    
    # Panda hover thoughts
    PANDA_HOVER_THOUGHTS = {
        'normal': [
            "💭 Thinking about bamboo...",
            "💭 Processing textures is fun!",
            "💭 Wonder what's for lunch...",
            "💭 Is it nap time yet?",
            "💭 These textures look organized!",
            "💭 Should I learn Python?",
            "💭 Life is good.",
            "💭 Texture sorting: 10/10 would recommend",
        ],
        'vulgar': [
            "💭 Why am I sorting textures at 3 AM?",
            "💭 This job doesn't pay enough bamboo.",
            "💭 Should've been a red panda...",
            "💭 These textures better appreciate me.",
            "💭 Coffee. Need coffee. Lots of it.",
            "💭 Living the dream. Sort of.",
            "💭 Is this what success looks like?",
            "💭 Could be worse. Could be parsing CSS.",
        ],
    }
    
    # Mood-specific messages
    MOOD_MESSAGES = {
        PandaMood.SARCASTIC: [
            "Oh wow, took you long enough. 🙄",
            "Sure, I'll just wait here. Not like I have bamboo to eat.",
            "Faster? Nah, take your time. I'm immortal apparently.",
            "Great job! If by great you mean slow as molasses.",
        ],
        PandaMood.RAGE: [
            "THAT'S IT! I'VE HAD ENOUGH! 💢",
            "WHY DO YOU KEEP FAILING?! 🔥",
            "ANOTHER ERROR?! ARE YOU KIDDING ME?! 😤",
            "RAGE MODE: ACTIVATED! FIX YOUR SH*T! 💥",
        ],
        PandaMood.DRUNK: [
            "Heyyy... you're pretty cool, you know that? 🍺",
            "*hiccup* Let's sort some... whatever those things are... 🥴",
            "Everything's... spinning... but in a good way! 🍻",
            "I love you, man. I love textures. I love everything! 🍺",
        ],
        PandaMood.EXISTENTIAL: [
            "What is the meaning of sorting textures? 🌌",
            "Are we just... organizing pixels in an infinite void? ✨",
            "10,000 files... and for what? What does it all mean? 💭",
            "We're all just stardust sorting other stardust... 🌠",
        ],
        PandaMood.MOTIVATING: [
            "YOU GOT THIS! NOW GET BACK TO WORK! 💪",
            "NO EXCUSES! SORT THOSE TEXTURES! 🔥",
            "BELIEVE IN YOURSELF, DAMMIT! 💯",
            "YOU'RE A GODDAMN CHAMPION! ACT LIKE IT! 👑",
        ],
        PandaMood.TECH_SUPPORT: [
            "Have you tried turning it off and on again? 📞",
            "Did you check if it's plugged in? 🔌",
            "Is your computer actually on? Just checking. 💻",
            "Error code: ID-10-T. Look it up. 🤓",
        ],
        PandaMood.SLEEPY: [
            "*yawn* Is it nap time yet? 😴",
            "Can't... keep... eyes... open... 💤",
            "Just five more minutes... zzz... 😪",
            "Need... caffeine... or bamboo... or sleep... 🥱",
        ],
    }
    
    # Easter egg triggers
    
    def __init__(self, vulgar_mode: bool = False):
        """
        Initialize panda mode.
        
        Args:
            vulgar_mode: Enable vulgar/funny quotes (opt-in)
        """
        self.enabled = True
        self.vulgar_mode = vulgar_mode
        self.current_mood = PandaMood.HAPPY
        self.animation_thread: Optional[threading.Thread] = None
        self.stop_animation = threading.Event()
        
        # Callbacks for animation updates
        self.animation_callbacks: List[Callable[[str], None]] = []
        self.message_callbacks: List[Callable[[str], None]] = []
        
        # Statistics
        self.facts_shown = 0
        self.quotes_shown = 0
        self.easter_eggs_triggered: set = set()
        
        # Easter egg tracking
        self.click_count = 0
        self.operation_cancellations = 0
        self.failed_operations = 0
        self.start_time = time.time()
        self.files_processed = 0
        self.tab_switch_times: List[float] = []
        self.hover_start_time: Optional[float] = None
        self.last_file_path: Optional[str] = None
        self.last_folder_path: Optional[str] = None
        self.konami_sequence: List[str] = []
        self.panda_pet_count = 0
        
        logger.info("🐼 Panda Mode initialized" + (" [VULGAR]" if vulgar_mode else ""))
    
    def enable(self) -> None:
        """Enable panda mode."""
        self.enabled = True
        logger.info("🐼 Panda Mode enabled")
    
    def disable(self) -> None:
        """Disable panda mode."""
        self.enabled = False
        self.stop_animation.set()
        logger.info("Panda Mode disabled")
    
    def toggle(self) -> bool:
        """
        Toggle panda mode.
        
        Returns:
            New enabled state
        """
        if self.enabled:
            self.disable()
        else:
            self.enable()
        return self.enabled
    
    def set_vulgar_mode(self, enabled: bool) -> None:
        """
        Enable or disable vulgar mode.
        
        Args:
            enabled: Whether to enable vulgar mode
        """
        self.vulgar_mode = enabled
        logger.info(f"Vulgar mode {'enabled' if enabled else 'disabled'}")
    
    def set_mood(self, mood: PandaMood) -> None:
        """
        Set panda mood.
        
        Args:
            mood: Panda mood state
        """
        self.current_mood = mood
        logger.debug(f"Panda mood: {mood.value}")
    
    def get_tooltip(self, action: str, mode: str = None) -> str:
        """
        Get a random tooltip for the specified action.
        
        Args:
            action: The UI element/action (e.g., 'sort_button', 'convert_button')
            mode: Override mode ('normal', 'vulgar')
                  If None, uses self.vulgar_mode
        
        Returns:
            Random tooltip string from the appropriate set
        """
        if not self.enabled:
            return ""
        
        # Determine which mode to use
        tooltip_mode = mode if mode is not None else ('vulgar' if self.vulgar_mode else 'normal')
        
        # Get tooltip set for action
        tooltip_set = self.TOOLTIPS.get(action, None)
        if not tooltip_set:
            return "Click to perform action"
        
        # Get tooltips for the mode
        tooltips = tooltip_set.get(tooltip_mode, tooltip_set.get('normal', []))
        
        if not tooltips:
            return "Click to perform action"
        
        return random.choice(tooltips)
    
    def trigger_rage_mode(self) -> None:
        """
        Activate rage mode after repeated failures.
        """
        if not self.enabled:
            return
        
        self.set_mood(PandaMood.RAGE)
        self.start_animation('rage', duration_seconds=5.0)
        
        rage_msg = random.choice(self.MOOD_MESSAGES[PandaMood.RAGE])
        self._notify_message(rage_msg)
        
        logger.info("🐼 RAGE MODE ACTIVATED!")
    
    def check_time_for_drunk_panda(self) -> bool:
        """
        Check if it's after midnight and potentially trigger drunk mode.
        
        Returns:
            True if drunk mode was triggered
        """
        if not self.enabled:
            return False
        
        from datetime import datetime
        current_hour = datetime.now().hour
        
        # Between midnight and 5 AM
        if 0 <= current_hour < 5 and random.random() < 0.3:  # 30% chance
            self.set_mood(PandaMood.DRUNK)
            self.start_animation('drunk', duration_seconds=10.0)
            
            drunk_msg = random.choice(self.MOOD_MESSAGES[PandaMood.DRUNK])
            self._notify_message(drunk_msg)
            self.trigger_easter_egg('night_owl')
            
            logger.info("🐼 Drunk panda mode activated!")
            return True
        
        return False
    
    def existential_crisis(self) -> None:
        """
        Trigger existential crisis mode after 10,000+ files.
        """
        if not self.enabled:
            return
        
        self.set_mood(PandaMood.EXISTENTIAL)
        self.start_animation('existential', duration_seconds=8.0)
        
        crisis_msg = random.choice(self.MOOD_MESSAGES[PandaMood.EXISTENTIAL])
        self._notify_message(crisis_msg)
        self.trigger_easter_egg('zen_master')
        
        logger.info("🐼 Existential crisis mode activated!")
    
    def become_sleepy(self) -> None:
        """
        Trigger sleepy mode after 2 hours of usage.
        """
        if not self.enabled:
            return
        
        elapsed_hours = (time.time() - self.start_time) / 3600
        
        if elapsed_hours >= 2.0:
            self.set_mood(PandaMood.SLEEPY)
            self.start_animation('sleeping', duration_seconds=5.0)
            
            sleepy_msg = random.choice(self.MOOD_MESSAGES[PandaMood.SLEEPY])
            self._notify_message(sleepy_msg)
            self.trigger_easter_egg('coffee_break')
            
            logger.info("🐼 Sleepy panda mode activated!")
    
    def on_panda_click(self) -> str:
        """
        React to panda clicks with different responses.
        
        Returns:
            Response message
        """
        if not self.enabled:
            return ""
        
        self.click_count += 1
        self.panda_pet_count += 1
        
        # Easter egg: 10 clicks = rage mode
        if self.click_count == 10:
            self.trigger_rage_mode()
            self.trigger_easter_egg('panda_rage')
            self.click_count = 0  # Reset
            return "💢 STOP CLICKING ME!"
        
        # Get response based on mode
        mode = 'vulgar' if self.vulgar_mode else 'normal'
        responses = self.PANDA_CLICK_RESPONSES.get(mode, self.PANDA_CLICK_RESPONSES['normal'])
        
        response = random.choice(responses)
        self._notify_message(response)
        
        return response
    
    def on_panda_hover(self) -> str:
        """
        Show panda thoughts when hovering.
        
        Returns:
            Panda thought bubble
        """
        if not self.enabled:
            return ""
        
        # Track hover start time
        if self.hover_start_time is None:
            self.hover_start_time = time.time()
        
        # Easter egg: hover for 30 seconds
        hover_duration = time.time() - self.hover_start_time
        if hover_duration >= 30.0:
            self.trigger_easter_egg('hover_stalker')
            self.hover_start_time = None  # Reset
            return "😒 Okay seriously, what do you want?"
        
        mode = 'vulgar' if self.vulgar_mode else 'normal'
        thoughts = self.PANDA_HOVER_THOUGHTS.get(mode, self.PANDA_HOVER_THOUGHTS['normal'])
        
        return random.choice(thoughts)
    
    def on_panda_hover_end(self) -> None:
        """Reset hover tracking when hover ends."""
        self.hover_start_time = None
    
    def on_panda_right_click(self) -> dict:
        """
        Show panda context menu on right-click.
        
        Returns:
            Dictionary of menu options
        """
        if not self.enabled:
            return {}
        
        menu = {
            'pet_panda': '🐼 Pet the panda',
            'feed_bamboo': '🎋 Feed bamboo',
            'panda_stats': '📊 View panda stats',
            'change_mood': '😊 Change mood',
            'tell_joke': '😂 Tell a joke',
            'panda_fact': '📚 Random panda fact',
        }
        
        return menu
    
    def get_panda_mood_indicator(self) -> str:
        """
        Get mood emoji/status indicator.
        
        Returns:
            Emoji representing current mood
        """
        mood_emoji = {
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
        
        return mood_emoji.get(self.current_mood, "🐼")
    
    def pet_panda_minigame(self) -> str:
        """
        Simple panda petting interaction.
        
        Returns:
            Panda reaction to petting
        """
        if not self.enabled:
            return ""
        
        self.panda_pet_count += 1
        
        reactions = [
            "🐼 *purrs like a cat* Wait, pandas don't purr...",
            "🐼 *happy panda noises* 💚",
            "🐼 More please! This is nice!",
            "🐼 You're pretty good at this!",
            "🐼 *munches bamboo contentedly*",
            "🐼 Best. Human. Ever.",
            "🐼 *falls asleep from relaxation*",
            "🐼 Could get used to this...",
        ]
        
        if self.vulgar_mode:
            reactions.extend([
                "🐼 Okay fine, that's actually nice.",
                "🐼 Don't stop, this is the best part of my day.",
                "🐼 You're alright, human.",
                "🐼 *begrudgingly enjoys this*",
            ])
        
        reaction = random.choice(reactions)
        self._notify_message(reaction)
        
        # Easter egg: Pet 50 times
        if self.panda_pet_count >= 50:
            self.trigger_easter_egg('achievement_unlocked')
            self._notify_message("🏆 ACHIEVEMENT: PANDA WHISPERER!")
            self.panda_pet_count = 0  # Reset
        
        return reaction
    
    def track_operation_failure(self) -> None:
        """
        Track failed operations and trigger rage mode if needed.
        """
        self.failed_operations += 1
        
        # Trigger rage after 5 failures
        if self.failed_operations >= 5:
            self.trigger_rage_mode()
            self.failed_operations = 0  # Reset
    
    def track_operation_cancel(self) -> None:
        """
        Track cancelled operations and trigger easter egg if needed.
        """
        self.operation_cancellations += 1
        
        # Easter egg: Cancel 5 times
        if self.operation_cancellations >= 5:
            self.trigger_easter_egg('indecisive')
            if self.vulgar_mode:
                self._notify_message("😤 MAKE UP YOUR DAMN MIND ALREADY!")
            else:
                self._notify_message("🤔 Having trouble deciding?")
            self.operation_cancellations = 0  # Reset
    
    def track_file_processed(self, file_path: str, file_size: int) -> None:
        """
        Track processed files and trigger easter eggs.
        
        Args:
            file_path: Path to processed file
            file_size: Size of file in bytes
        """
        self.files_processed += 1
        
        # Easter egg: Same file twice
        if file_path == self.last_file_path:
            self.trigger_easter_egg('perfectionist')
            if self.vulgar_mode:
                self._notify_message("🤨 Really? Converting the same file AGAIN?")
            else:
                self._notify_message("🔄 Processing this file again?")
        
        self.last_file_path = file_path
        
        # Easter egg: 0 byte file
        if file_size == 0:
            self.trigger_easter_egg('zero_bytes')
            if self.vulgar_mode:
                self._notify_message("🤨 Are you serious? A 0 byte file? REALLY?")
            else:
                self._notify_message("⚠️ This file appears to be empty!")
        
        # Easter egg: 1000 files milestone
        if self.files_processed == 1000:
            self.trigger_easter_egg('thousand_files')
            if self.vulgar_mode:
                self.celebrate("🏆 HOLY SH*T! 1000 FILES SORTED!")
            else:
                self.celebrate("🏆 Amazing! 1000 files sorted!")
        
        # Existential crisis at 10,000 files
        if self.files_processed >= 10000 and self.files_processed % 10000 == 0:
            self.existential_crisis()
        
        # Check for sleepy mode
        self.become_sleepy()
    
    def track_folder_selection(self, folder_path: str) -> None:
        """
        Track folder selections and trigger easter eggs.
        
        Args:
            folder_path: Path to selected folder
        """
        # Easter egg: Same folder twice
        if folder_path == self.last_folder_path:
            self.trigger_easter_egg('same_folder')
            if self.vulgar_mode:
                self._notify_message("👻 Wait... DÉJÀ VU! Same folder twice?")
            else:
                self._notify_message("🔄 Selecting the same folder again?")
        
        self.last_folder_path = folder_path
    
    def track_tab_switch(self) -> None:
        """
        Track tab switches and trigger easter egg for rapid switching.
        """
        current_time = time.time()
        self.tab_switch_times.append(current_time)
        
        # Keep only last 10 switches
        self.tab_switch_times = self.tab_switch_times[-10:]
        
        # Easter egg: 10 tab switches in 5 seconds
        if len(self.tab_switch_times) >= 10:
            time_range = self.tab_switch_times[-1] - self.tab_switch_times[0]
            if time_range <= 5.0:
                self.trigger_easter_egg('tab_dancer')
                self._notify_message("💃 TAB SWITCHING CHAMPION! PANDA DANCE!")
                self.celebrate("🕺 You're quick with those tabs!")
                self.tab_switch_times.clear()
    
    def check_3am_processing(self) -> None:
        """
        Check if user is processing at 3 AM and trigger easter egg.
        """
        from datetime import datetime
        current_hour = datetime.now().hour
        
        if current_hour == 3:
            self.trigger_easter_egg('midnight_madness')
            if self.vulgar_mode:
                self._notify_message("🌙 WHY ARE YOU AWAKE AT 3 AM?! GO TO SLEEP!")
            else:
                self._notify_message("🌙 Working late? Don't forget to rest!")
            
            # Maybe drunk panda too
            self.check_time_for_drunk_panda()
    
    def handle_text_input(self, text: str) -> bool:
        """
        Handle text input for easter egg triggers.
        
        Args:
            text: Input text to check
        
        Returns:
            True if easter egg was triggered
        """
        text_lower = text.lower().strip()
        
        # Check for text-based easter eggs
        easter_egg_map = {
            'bamboo': 'bamboo',
            'ninja': 'ninja',
            'turbo': 'turbo',
            'disco': 'disco',
            'matrix': 'matrix',
            'developer': 'developer',
        }
        
        if text_lower in easter_egg_map:
            return self.trigger_easter_egg(easter_egg_map[text_lower])
        
        return False
    
    def track_konami_input(self, key: str) -> bool:
        """
        Track konami code input sequence.
        
        Args:
            key: Key pressed
        
        Returns:
            True if konami code completed
        """
        self.konami_sequence.append(key.lower())
        
        # Keep only last 10 keys
        self.konami_sequence = self.konami_sequence[-10:]
        
        return self.check_konami_code(self.konami_sequence)
    
    def get_random_tech_support_quote(self) -> str:
        """
        Get a random tech support quote.
        
        Returns:
            Tech support style message
        """
        if not self.enabled:
            return ""
        
        self.set_mood(PandaMood.TECH_SUPPORT)
        self.start_animation('tech_support', duration_seconds=3.0)
        
        return random.choice(self.MOOD_MESSAGES[PandaMood.TECH_SUPPORT])
    
    def motivate_user(self) -> str:
        """
        Get a motivating (and possibly vulgar) message.
        
        Returns:
            Motivational message
        """
        if not self.enabled:
            return ""
        
        self.set_mood(PandaMood.MOTIVATING)
        
        return random.choice(self.MOOD_MESSAGES[PandaMood.MOTIVATING])
    
    def become_sarcastic(self) -> str:
        """
        Trigger sarcastic mode for slow progress.
        
        Returns:
            Sarcastic message
        """
        if not self.enabled:
            return ""
        
        self.set_mood(PandaMood.SARCASTIC)
        self.start_animation('sarcastic', duration_seconds=4.0)
        
        return random.choice(self.MOOD_MESSAGES[PandaMood.SARCASTIC])
    
    
    def get_random_fact(self) -> str:
        """
        Get a random panda fact.
        
        Returns:
            Random panda fact
        """
        if not self.enabled:
            return ""
        
        fact = random.choice(self.PANDA_FACTS)
        self.facts_shown += 1
        logger.debug("Showing panda fact")
        return fact
    
    def get_random_quote(self) -> str:
        """
        Get a random motivational quote.
        
        Returns:
            Random quote (vulgar or regular based on mode)
        """
        if not self.enabled:
            return ""
        
        if self.vulgar_mode:
            quote = random.choice(self.VULGAR_QUOTES)
        else:
            quote = random.choice(self.REGULAR_QUOTES)
        
        self.quotes_shown += 1
        return quote
    
    def get_milestone_message(self, count: int) -> Optional[str]:
        """
        Get milestone message for texture count.
        
        Args:
            count: Number of textures processed
            
        Returns:
            Milestone message or None
        """
        if not self.enabled:
            return None
        
        # Check if this count hits a milestone
        if count in self.MILESTONE_MESSAGES:
            return self.MILESTONE_MESSAGES[count]
        
        return None
    
    def get_animation_frame(self, animation_name: str = 'idle') -> str:
        """
        Get current animation frame.
        
        Args:
            animation_name: Name of animation to get
            
        Returns:
            Animation frame as string
        """
        if not self.enabled:
            return ""
        
        frames = self.PANDA_FRAMES.get(animation_name, self.PANDA_FRAMES['idle'])
        
        # For multi-frame animations, rotate through frames
        # In a real implementation, this would track frame index
        return random.choice(frames)
    
    def start_animation(
        self,
        animation_name: str = 'working',
        duration_seconds: Optional[float] = None
    ) -> None:
        """
        Start animated panda display.
        
        Args:
            animation_name: Name of animation to play
            duration_seconds: How long to animate (None for indefinite)
        """
        if not self.enabled:
            return
        
        # Stop any existing animation
        self.stop_current_animation()
        
        self.stop_animation.clear()
        
        def animate():
            frames = self.PANDA_FRAMES.get(animation_name, self.PANDA_FRAMES['idle'])
            frame_idx = 0
            start_time = time.time()
            
            while not self.stop_animation.is_set():
                # Check duration
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    break
                
                # Get current frame
                frame = frames[frame_idx % len(frames)]
                
                # Notify callbacks
                self._notify_animation_update(frame)
                
                # Next frame
                frame_idx += 1
                
                # Sleep between frames
                time.sleep(0.2)  # 200ms per frame
        
        self.animation_thread = threading.Thread(target=animate, daemon=True)
        self.animation_thread.start()
    
    def stop_current_animation(self) -> None:
        """Stop current animation."""
        if self.animation_thread and self.animation_thread.is_alive():
            self.stop_animation.set()
            self.animation_thread.join(timeout=1.0)
    
    def celebrate(self, message: Optional[str] = None) -> None:
        """
        Trigger celebration animation.
        
        Args:
            message: Optional celebration message
        """
        if not self.enabled:
            return
        
        self.set_mood(PandaMood.CELEBRATING)
        self.start_animation('celebrating', duration_seconds=3.0)
        
        if not message:
            message = self.get_random_quote()
        
        self._notify_message(f"🎉 {message}")
        logger.info(f"🐼 Celebration: {message}")
    
    def show_progress_update(self, processed: int, total: int) -> None:
        """
        Show progress update with panda.
        
        Args:
            processed: Number of textures processed
            total: Total textures to process
        """
        if not self.enabled:
            return
        
        # Check for milestones
        milestone_msg = self.get_milestone_message(processed)
        if milestone_msg:
            self.celebrate(milestone_msg)
            return
        
        # Random facts/quotes at intervals
        if processed % 100 == 0 and processed > 0:
            if random.random() < 0.3:  # 30% chance
                self._notify_message(self.get_random_fact())
            elif random.random() < 0.5:  # 50% of remaining
                self._notify_message(self.get_random_quote())
    
    def trigger_easter_egg(self, egg_name: str) -> bool:
        """
        Trigger an Easter egg.
        
        Args:
            egg_name: Name of Easter egg to trigger
            
        Returns:
            True if triggered successfully
        """
        if not self.enabled:
            return False
        
        if egg_name not in self.EASTER_EGGS:
            return False
        
        self.easter_eggs_triggered.add(egg_name)
        message = self.EASTER_EGGS[egg_name]
        
        self.celebrate(message)
        logger.info(f"🥚 Easter egg triggered: {egg_name}")
        
        return True
    
    def check_konami_code(self, input_sequence: List[str]) -> bool:
        """
        Check if input matches Konami code.
        
        Args:
            input_sequence: List of key inputs
            
        Returns:
            True if Konami code matched
        """
        konami = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right', 'b', 'a']
        
        if input_sequence[-len(konami):] == konami:
            return self.trigger_easter_egg('konami')
        
        return False
    
    def get_panda_status(self) -> str:
        """
        Get current panda status message.
        
        Returns:
            Status message with panda mood
        """
        if not self.enabled:
            return "Panda Mode: Disabled"
        
        mood_messages = {
            PandaMood.HAPPY: "🐼 Panda is happy and ready!",
            PandaMood.EXCITED: "🐼 Panda is excited to help!",
            PandaMood.WORKING: "🐼 Panda is hard at work!",
            PandaMood.TIRED: "🐼 Panda is getting tired...",
            PandaMood.CELEBRATING: "🐼 Panda is celebrating! 🎉",
            PandaMood.SLEEPING: "🐼 Panda is taking a nap... 💤",
        }
        
        return mood_messages.get(self.current_mood, "🐼 Panda is here!")
    
    def register_animation_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register callback for animation frame updates.
        
        Args:
            callback: Function to call with animation frame
        """
        self.animation_callbacks.append(callback)
    
    def register_message_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register callback for panda messages.
        
        Args:
            callback: Function to call with messages
        """
        self.message_callbacks.append(callback)
    
    def _notify_animation_update(self, frame: str) -> None:
        """Notify animation callbacks."""
        for callback in self.animation_callbacks:
            try:
                callback(frame)
            except Exception as e:
                logger.error(f"Error in animation callback: {e}")
    
    def _notify_message(self, message: str) -> None:
        """Notify message callbacks."""
        for callback in self.message_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
    
    def get_statistics(self) -> dict:
        """
        Get panda mode statistics.
        
        Returns:
            Statistics dictionary
        """
        elapsed_time = time.time() - self.start_time
        return {
            'enabled': self.enabled,
            'vulgar_mode': self.vulgar_mode,
            'current_mood': self.current_mood.value,
            'facts_shown': self.facts_shown,
            'quotes_shown': self.quotes_shown,
            'easter_eggs_triggered': len(self.easter_eggs_triggered),
            'easter_eggs_list': list(self.easter_eggs_triggered),
            'files_processed': self.files_processed,
            'click_count': self.click_count,
            'failed_operations': self.failed_operations,
            'operation_cancellations': self.operation_cancellations,
            'panda_pet_count': self.panda_pet_count,
            'elapsed_time_seconds': elapsed_time,
            'elapsed_time_hours': elapsed_time / 3600,
        }
    
    def reset_statistics(self) -> None:
        """Reset panda mode statistics."""
        self.facts_shown = 0
        self.quotes_shown = 0
        self.easter_eggs_triggered.clear()
        self.click_count = 0
        self.operation_cancellations = 0
        self.failed_operations = 0
        self.start_time = time.time()
        self.files_processed = 0
        self.tab_switch_times.clear()
        self.panda_pet_count = 0
        logger.info("Panda mode statistics reset")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop_current_animation()


# Panda Feeding System
@dataclass
class FoodItem:
    """Items you can feed to the panda."""
    name: str
    description: str
    happiness_bonus: int
    unlock_condition: str
    icon: str = "🎋"


class PandaFeedingSystem:
    """Manages panda feeding and hunger mechanics."""
    
    FOOD_ITEMS = {
        'bamboo': FoodItem(
            name="Bamboo",
            description="Classic panda food",
            happiness_bonus=5,
            unlock_condition="always_available",
            icon="🎋"
        ),
        'bamboo_shoots': FoodItem(
            name="Bamboo Shoots",
            description="Fresh tender shoots",
            happiness_bonus=8,
            unlock_condition="always_available",
            icon="🌱"
        ),
        'bamboo_cake': FoodItem(
            name="Bamboo Cake",
            description="Birthday special",
            happiness_bonus=20,
            unlock_condition="use_on_birthday",
            icon="🎂"
        ),
        'golden_bamboo': FoodItem(
            name="Golden Bamboo",
            description="Legendary food",
            happiness_bonus=50,
            unlock_condition="process_100k_files",
            icon="✨"
        ),
        'dumplings': FoodItem(
            name="Dumplings",
            description="Delicious Chinese dumplings",
            happiness_bonus=12,
            unlock_condition="process_1k_files",
            icon="🥟"
        ),
        'ramen': FoodItem(
            name="Ramen",
            description="Hot steaming ramen",
            happiness_bonus=10,
            unlock_condition="process_500_files",
            icon="🍜"
        ),
        'sushi': FoodItem(
            name="Sushi",
            description="Fresh sushi platter",
            happiness_bonus=15,
            unlock_condition="process_5k_files",
            icon="🍣"
        ),
        'ice_cream': FoodItem(
            name="Ice Cream",
            description="Cool and refreshing",
            happiness_bonus=18,
            unlock_condition="work_2_hours",
            icon="🍨"
        ),
        'pizza': FoodItem(
            name="Pizza",
            description="Everyone loves pizza!",
            happiness_bonus=14,
            unlock_condition="work_1_hour",
            icon="🍕"
        ),
        'cookies': FoodItem(
            name="Cookies",
            description="Chocolate chip cookies",
            happiness_bonus=10,
            unlock_condition="always_available",
            icon="🍪"
        ),
        'tea': FoodItem(
            name="Green Tea",
            description="Relaxing green tea",
            happiness_bonus=7,
            unlock_condition="always_available",
            icon="🍵"
        ),
        'rice_ball': FoodItem(
            name="Rice Ball",
            description="Traditional onigiri",
            happiness_bonus=9,
            unlock_condition="process_100_files",
            icon="🍙"
        ),
        'fruit_basket': FoodItem(
            name="Fruit Basket",
            description="Assorted fresh fruits",
            happiness_bonus=11,
            unlock_condition="use_for_7_days",
            icon="🧺"
        ),
        'honey': FoodItem(
            name="Honey",
            description="Sweet golden honey",
            happiness_bonus=13,
            unlock_condition="pet_panda_50_times",
            icon="🍯"
        ),
    }
    
    HUNGER_REACTIONS = [
        "🐼 Panda's tummy is rumbling...",
        "🐼 Panda looks at you with hungry eyes...",
        "🐼 *stomach growls* Feed me maybe?",
        "🐼 Panda points at the food menu hopefully",
        "🐼 Is it snack time yet? Asking for a friend...",
        "🐼 Panda dreams of bamboo...",
        "🐼 *sniff sniff* Do I smell food?",
    ]
    
    FEEDING_REACTIONS = {
        'love': [
            "🐼 ❤️ Nom nom nom! Panda loves this!",
            "🐼 💕 This is amazing! Thank you!",
            "🐼 ✨ Best food ever! You're the best!",
            "🐼 🌟 *happy panda noises*",
        ],
        'like': [
            "🐼 😊 Mmm, tasty!",
            "🐼 Thanks for the snack!",
            "🐼 Yum! Just what I needed!",
            "🐼 Delicious!",
        ],
        'neutral': [
            "🐼 Thanks, I guess...",
            "🐼 Food is food.",
            "🐼 Appreciate it!",
        ],
        'full': [
            "🐼 💤 Too full... can't move...",
            "🐼 I'm stuffed! Maybe later?",
            "🐼 No more food please! *burp*",
        ]
    }
    
    def __init__(self):
        """Initialize feeding system."""
        self.hunger_level = 50
        self.last_fed_time = time.time()
        self.feed_count = 0
        self.favorite_foods = []
    
    def get_hunger_level(self) -> str:
        """Returns panda's current hunger status."""
        elapsed = time.time() - self.last_fed_time
        self.hunger_level = min(100, self.hunger_level + (elapsed / 60))
        
        if self.hunger_level < 20:
            return "🐼 Panda is well-fed and happy!"
        elif self.hunger_level < 40:
            return "🐼 Panda is satisfied"
        elif self.hunger_level < 60:
            return "🐼 Panda is getting peckish"
        elif self.hunger_level < 80:
            return "🐼 Panda is hungry!"
        else:
            return "🐼 Panda is VERY hungry! 🍴"
    
    def feed_panda(self, food_id: str, stats: dict) -> str:
        """Feed the panda and get a reaction."""
        if food_id not in self.FOOD_ITEMS:
            return "🐼 ❓ Panda doesn't recognize this food..."
        
        food = self.FOOD_ITEMS[food_id]
        
        # Check if too full
        if self.hunger_level < 10:
            return random.choice(self.FEEDING_REACTIONS['full'])
        
        # Update hunger
        self.hunger_level = max(0, self.hunger_level - food.happiness_bonus * 2)
        self.last_fed_time = time.time()
        self.feed_count += 1
        
        # Choose reaction based on hunger level and food quality
        if food.happiness_bonus >= 15:
            reaction = random.choice(self.FEEDING_REACTIONS['love'])
        elif food.happiness_bonus >= 10:
            reaction = random.choice(self.FEEDING_REACTIONS['like'])
        else:
            reaction = random.choice(self.FEEDING_REACTIONS['neutral'])
        
        logger.info(f"Fed panda {food.name} (count: {self.feed_count})")
        return f"{reaction}\n{food.icon} Fed panda {food.name}!"
    
    def get_available_foods(self, stats: dict) -> List[str]:
        """Get list of available food items based on unlock conditions."""
        available = []
        for food_id, food in self.FOOD_ITEMS.items():
            if self._check_unlock_condition(food.unlock_condition, stats):
                available.append(food_id)
        return available
    
    def _check_unlock_condition(self, condition: str, stats: dict) -> bool:
        """Check if food unlock condition is met."""
        if condition == "always_available":
            return True
        elif condition == "process_100_files":
            return stats.get('files_processed', 0) >= 100
        elif condition == "process_500_files":
            return stats.get('files_processed', 0) >= 500
        elif condition == "process_1k_files":
            return stats.get('files_processed', 0) >= 1000
        elif condition == "process_5k_files":
            return stats.get('files_processed', 0) >= 5000
        elif condition == "process_100k_files":
            return stats.get('files_processed', 0) >= 100000
        elif condition == "work_1_hour":
            return stats.get('elapsed_time_hours', 0) >= 1
        elif condition == "work_2_hours":
            return stats.get('elapsed_time_hours', 0) >= 2
        elif condition == "use_for_7_days":
            return stats.get('days_used', 0) >= 7
        elif condition == "pet_panda_50_times":
            return stats.get('panda_pet_count', 0) >= 50
        return False


# Panda Travel System
@dataclass
class PandaLocation:
    """Represents a location panda can visit."""
    id: str
    name: str
    description: str
    postcard_messages: List[str]
    unlock_condition: str
    icon: str = "📍"


class PandaTravelSystem:
    """Manages panda travel and location visits."""
    
    LOCATIONS = {
        'home': PandaLocation(
            id='home',
            name='Home',
            description='Panda is chilling at home',
            postcard_messages=[
                "🏠 There's no place like home!",
                "🏠 Just relaxing and eating bamboo",
                "🏠 Home sweet home 💕",
            ],
            unlock_condition='always_available',
            icon='🏠'
        ),
        'bamboo_forest': PandaLocation(
            id='bamboo_forest',
            name='Bamboo Forest',
            description='Panda is munching bamboo in the forest',
            postcard_messages=[
                "🎋 Found the best bamboo grove ever!",
                "🎋 Living the dream in endless bamboo",
                "🎋 This place is bamboo-tiful!",
            ],
            unlock_condition='always_available',
            icon='🎋'
        ),
        'beach': PandaLocation(
            id='beach',
            name='Beach',
            description='Panda is building sandcastles',
            postcard_messages=[
                "🏖️ Building the most epic sandcastle!",
                "🏖️ Sand, sun, and bamboo smoothies!",
                "🏖️ Beach life is the best life!",
            ],
            unlock_condition='process_100_files',
            icon='🏖️'
        ),
        'mountains': PandaLocation(
            id='mountains',
            name='Mountains',
            description='Panda is climbing mountains',
            postcard_messages=[
                "⛰️ The view from up here is incredible!",
                "⛰️ Conquering peaks one paw at a time!",
                "⛰️ Mountain air and bamboo everywhere!",
            ],
            unlock_condition='process_500_files',
            icon='⛰️'
        ),
        'space': PandaLocation(
            id='space',
            name='Space',
            description='Panda is floating in space',
            postcard_messages=[
                "🚀 Houston, we have no problems!",
                "🚀 Space bamboo tastes different...",
                "🚀 One small step for panda, one giant leap for texture sorting!",
            ],
            unlock_condition='process_10k_files',
            icon='🚀'
        ),
        'underwater': PandaLocation(
            id='underwater',
            name='Underwater',
            description='Panda is diving with fish',
            postcard_messages=[
                "🐠 Made friends with a school of fish!",
                "🐠 Underwater bamboo is surprisingly good!",
                "🐠 Living that mermaid panda life!",
            ],
            unlock_condition='process_1k_files',
            icon='🐠'
        ),
        'tokyo': PandaLocation(
            id='tokyo',
            name='Tokyo',
            description='Panda is visiting Tokyo',
            postcard_messages=[
                "🗼 Tokyo Tower is amazing!",
                "🗼 Trying all the Japanese snacks!",
                "🗼 Kawaii culture everywhere!",
            ],
            unlock_condition='process_5k_files',
            icon='🗼'
        ),
        'cafe': PandaLocation(
            id='cafe',
            name='Café',
            description='Panda is having coffee',
            postcard_messages=[
                "☕ Best cappuccino ever!",
                "☕ Coffee and bamboo biscotti!",
                "☕ Café life is my life!",
            ],
            unlock_condition='work_1_hour',
            icon='☕'
        ),
        'gym': PandaLocation(
            id='gym',
            name='Gym',
            description='Panda is lifting weights',
            postcard_messages=[
                "💪 Getting swole!",
                "💪 Bamboo protein shake time!",
                "💪 Do you even lift, bro?",
            ],
            unlock_condition='work_2_hours',
            icon='💪'
        ),
        'library': PandaLocation(
            id='library',
            name='Library',
            description='Panda is reading books',
            postcard_messages=[
                "📚 Found a great book on texture sorting!",
                "📚 Knowledge is power!",
                "📚 Reading all the classics!",
            ],
            unlock_condition='process_100_files',
            icon='📚'
        ),
        'concert': PandaLocation(
            id='concert',
            name='Concert',
            description='Panda is rocking out',
            postcard_messages=[
                "🎸 Best concert ever!",
                "🎸 Front row seats!",
                "🎸 Rock and roll all night!",
            ],
            unlock_condition='use_for_3_days',
            icon='🎸'
        ),
        'arcade': PandaLocation(
            id='arcade',
            name='Arcade',
            description='Panda is gaming',
            postcard_messages=[
                "🎮 High score achieved!",
                "🎮 Retro games are the best!",
                "🎮 One more game... or ten...",
            ],
            unlock_condition='process_200_files',
            icon='🎮'
        ),
        'museum': PandaLocation(
            id='museum',
            name='Museum',
            description='Panda is appreciating art',
            postcard_messages=[
                "🎨 This art is incredible!",
                "🎨 Feeling very cultured!",
                "🎨 Found a painting of bamboo!",
            ],
            unlock_condition='process_300_files',
            icon='🎨'
        ),
        'zoo': PandaLocation(
            id='zoo',
            name='Zoo',
            description='Panda is visiting relatives',
            postcard_messages=[
                "🦁 Family reunion!",
                "🦁 Showing off my texture sorting skills!",
                "🦁 The other pandas are impressed!",
            ],
            unlock_condition='pet_panda_20_times',
            icon='🦁'
        ),
        'park': PandaLocation(
            id='park',
            name='Park',
            description='Panda is picnicking',
            postcard_messages=[
                "🌳 Perfect picnic weather!",
                "🌳 Bamboo sandwiches for lunch!",
                "🌳 Nature is beautiful!",
            ],
            unlock_condition='always_available',
            icon='🌳'
        ),
        'antarctica': PandaLocation(
            id='antarctica',
            name='Antarctica',
            description='Panda is with penguins',
            postcard_messages=[
                "🐧 Penguins are my new best friends!",
                "🐧 It's cold but beautiful!",
                "🐧 Ice skating with penguins!",
            ],
            unlock_condition='work_3_hours',
            icon='🐧'
        ),
    }
    
    def __init__(self):
        """Initialize travel system."""
        self.current_location = 'home'
        self.visited_locations = {'home'}
        self.travel_count = 0
    
    def send_panda_to(self, location_id: str, stats: dict) -> str:
        """Send panda to a location."""
        if location_id not in self.LOCATIONS:
            return "🐼 ❓ Panda doesn't know how to get there..."
        
        location = self.LOCATIONS[location_id]
        
        # Check unlock condition
        if not self._check_unlock_condition(location.unlock_condition, stats):
            return f"🔒 {location.name} is locked! Keep sorting textures to unlock it!"
        
        # Travel to location
        self.current_location = location_id
        self.visited_locations.add(location_id)
        self.travel_count += 1
        
        logger.info(f"Panda traveled to {location.name}")
        return f"✈️ Panda is traveling to {location.name}!\n{location.icon} {location.description}"
    
    def get_panda_location(self) -> str:
        """Get current panda location."""
        if self.current_location in self.LOCATIONS:
            location = self.LOCATIONS[self.current_location]
            return f"{location.icon} {location.description}"
        return "🐼 Panda is... somewhere?"
    
    def get_panda_postcard(self) -> str:
        """Get a postcard from panda's travels."""
        if self.current_location in self.LOCATIONS:
            location = self.LOCATIONS[self.current_location]
            message = random.choice(location.postcard_messages)
            return f"📮 Postcard from {location.name}:\n{message}"
        return "📮 No postcard available"
    
    def get_available_locations(self, stats: dict) -> List[str]:
        """Get list of available locations based on unlock conditions."""
        available = []
        for loc_id, location in self.LOCATIONS.items():
            if self._check_unlock_condition(location.unlock_condition, stats):
                available.append(loc_id)
        return available
    
    def _check_unlock_condition(self, condition: str, stats: dict) -> bool:
        """Check if location unlock condition is met."""
        if condition == 'always_available':
            return True
        elif condition == 'process_100_files':
            return stats.get('files_processed', 0) >= 100
        elif condition == 'process_200_files':
            return stats.get('files_processed', 0) >= 200
        elif condition == 'process_300_files':
            return stats.get('files_processed', 0) >= 300
        elif condition == 'process_500_files':
            return stats.get('files_processed', 0) >= 500
        elif condition == 'process_1k_files':
            return stats.get('files_processed', 0) >= 1000
        elif condition == 'process_5k_files':
            return stats.get('files_processed', 0) >= 5000
        elif condition == 'process_10k_files':
            return stats.get('files_processed', 0) >= 10000
        elif condition == 'work_1_hour':
            return stats.get('elapsed_time_hours', 0) >= 1
        elif condition == 'work_2_hours':
            return stats.get('elapsed_time_hours', 0) >= 2
        elif condition == 'work_3_hours':
            return stats.get('elapsed_time_hours', 0) >= 3
        elif condition == 'use_for_3_days':
            return stats.get('days_used', 0) >= 3
        elif condition == 'pet_panda_20_times':
            return stats.get('panda_pet_count', 0) >= 20
        return False


# Convenience functions
def create_panda_mode(vulgar: bool = False) -> PandaMode:
    """
    Create a PandaMode instance.
    
    Args:
        vulgar: Enable vulgar mode
        
    Returns:
        PandaMode instance
    """
    return PandaMode(vulgar_mode=vulgar)


def get_random_panda_fact() -> str:
    """
    Get a random panda fact (convenience function).
    
    Returns:
        Random panda fact
    """
    return random.choice(PandaMode.PANDA_FACTS)
