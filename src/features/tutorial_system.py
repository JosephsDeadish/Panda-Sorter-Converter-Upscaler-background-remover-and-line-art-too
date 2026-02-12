"""
Tutorial System - Phase 3
Provides first-run tutorial, tooltip verbosity management, and context-sensitive help
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import tkinter as tk
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import random

logger = logging.getLogger(__name__)

# Try to import GUI libraries
try:
    import customtkinter as ctk
    from tkinter import messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Tooltip definitions with normal and vulgar variants per widget
# (Previously stored in panda_mode.py – inlined here so the file can be removed)
_PANDA_TOOLTIPS = {
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
    },
    'sound_enabled': {
        'normal': [
            "Enable or disable all sound effects",
            "Toggle sound effects on or off globally",
            "Control whether the application plays sounds",
            "Turn all audio feedback on or off"
        ],
        'vulgar': [
            "Mute everything. Enjoy the silence, you hermit.",
            "Sound toggle. On or off. Binary. Like your social skills.",
            "Kill all sounds. Peace and quiet at last.",
            "Enable sounds or pretend you're in a library. Your call.",
            "Toggle audio. Because not everyone appreciates art."
        ]
    },
    'master_volume': {
        'normal': [
            "Adjust the overall volume level for all sounds",
            "Control the master audio volume",
            "Set the global volume for all sound effects",
            "Change how loud the application is overall"
        ],
        'vulgar': [
            "Master volume. Crank it up or shut it down.",
            "The big volume knob. Turn it up to 11 if you're brave.",
            "Overall loudness control. Your neighbors might care.",
            "Volume slider. Slide to the right for chaos, left for stealth mode.",
            "How loud do you want this sh*t? Slide and find out."
        ]
    },
    'effects_volume': {
        'normal': [
            "Control the volume of sound effects",
            "Adjust how loud action sounds are",
            "Set the volume for click and completion sounds",
            "Fine-tune the effects audio level"
        ],
        'vulgar': [
            "Effects volume. Make the clicks louder or stfu.",
            "Sound effects loudness. For those satisfying click sounds.",
            "Turn up the effects or turn them down. Nobody's watching.",
            "How loud should the bleep-bloops be? You decide.",
            "Effects slider. Slide it around like you know what you're doing."
        ]
    },
    'notifications_volume': {
        'normal': [
            "Control the volume of notification sounds",
            "Adjust how loud alert sounds are",
            "Set the volume for notification audio",
            "Fine-tune the notification audio level"
        ],
        'vulgar': [
            "Notification volume. Ding ding or nothing. Pick one.",
            "How loud do you want to be bothered? Slide accordingly.",
            "Notification sounds. Adjust before your coworkers complain.",
            "Alert volume. From 'barely a whisper' to 'everyone heard that'.",
            "Notification loudness. Subtle or obnoxious. Both valid."
        ]
    },
    'sound_pack': {
        'normal': [
            "Choose a sound pack style for audio feedback",
            "Select between different sets of sound effects",
            "Pick a sound theme for the application",
            "Change the overall audio style"
        ],
        'vulgar': [
            "Sound packs. Default is boring, vulgar is... interesting.",
            "Choose your audio aesthetic. Classy or trashy.",
            "Pick a sound theme. Each one has its own personality. Like you.",
            "Sound pack selector. Default, minimal, or WTF mode.",
            "Audio vibes. Pick the one that matches your energy."
        ]
    },
    'sound_test_button': {
        'normal': [
            "Play a preview of this event's sound",
            "Test what this sound effect sounds like",
            "Preview the audio for this event",
            "Click to hear a sample of this sound"
        ],
        'vulgar': [
            "Test the sound. Preview before you commit. Smart.",
            "Click to hear a preview. Try before you buy... wait, it's free.",
            "Sound test. Because surprises aren't always fun.",
            "Preview this noise. Your eardrums will thank you. Or not.",
            "Hit test to hear what this sounds like. Science!"
        ]
    },
    'cursor_type': {
        'normal': [
            "Select the style of your mouse cursor",
            "Choose a cursor appearance from the available options",
            "Change what your mouse pointer looks like",
            "Pick a cursor design for the application"
        ],
        'vulgar': [
            "Cursor style. Default is boring. Live a little.",
            "Change your cursor. Skull cursor? Hell yeah.",
            "Pointer picker. Because the default arrow is basic AF.",
            "Cursor options. From professional to 'what is that?'",
            "Pick a cursor. Crosshair makes you feel like a pro gamer."
        ]
    },
    'cursor_size': {
        'normal': [
            "Change the size of your mouse cursor",
            "Make your cursor larger or smaller",
            "Adjust cursor size for visibility",
            "Select a cursor size that works for you"
        ],
        'vulgar': [
            "Cursor size. Compensating for something? Go huge.",
            "Make your cursor tiny or massive. No judgment.",
            "Size matters. At least for cursors. Pick your preference.",
            "Cursor size slider. From 'where the hell is it' to 'can't miss it'.",
            "Resize your pointer. Because accessibility is important, damn it."
        ]
    },
    'cursor_trail': {
        'normal': [
            "Enable or disable cursor trail effects",
            "Add a decorative trail behind your cursor",
            "Toggle the cursor sparkle trail on or off",
            "Turn cursor trail effects on or off"
        ],
        'vulgar': [
            "Cursor trail. Leave sparkles wherever you go. Majestic.",
            "Enable trails. Your cursor will look fabulous. Trust me.",
            "Sparkle trail toggle. For the extra in all of us.",
            "Cursor trail. Because your mouse movements deserve to be celebrated.",
            "Turn on trails and watch your productivity drop. Worth it."
        ]
    },
    'trail_style': {
        'normal': [
            "Choose the visual style for your cursor trail",
            "Select a trail color scheme",
            "Pick a trail appearance from available styles",
            "Change the look of your cursor trail effect"
        ],
        'vulgar': [
            "Trail style. Rainbow? Fire? Galaxy? Go nuts.",
            "Pick a trail flavor. Each one is more extra than the last.",
            "Trail aesthetic picker. Match your energy level.",
            "Choose your sparkle style. No wrong answers here.",
            "Trail options. From 'subtle nature' to 'galactic overkill'."
        ]
    },
    'hotkey_edit': {
        'normal': [
            "Click to change the key binding for this shortcut",
            "Edit this keyboard shortcut assignment",
            "Remap this hotkey to a different key combination",
            "Modify the key binding for this action"
        ],
        'vulgar': [
            "Edit this hotkey. Remap it to something useful. Or chaotic.",
            "Change the keybinding. Make it whatever the hell you want.",
            "Remap this shortcut. Ctrl+Alt+Delete? Go for it.",
            "Edit hotkey. Because the default key was stupid.",
            "Rebind this action. Your keyboard, your rules."
        ]
    },
    'hotkey_toggle': {
        'normal': [
            "Enable or disable this keyboard shortcut",
            "Toggle this hotkey on or off",
            "Control whether this shortcut is active",
            "Turn this keyboard binding on or off"
        ],
        'vulgar': [
            "Enable or disable this shortcut. Some keys deserve a break.",
            "Toggle hotkey. On or off. Revolutionary, I know.",
            "Disable this shortcut if it keeps interrupting your flow.",
            "Turn this keybinding on or off. It's like a light switch but nerdier.",
            "Enable/disable toggle. For when shortcuts start sh*t."
        ]
    },
    'cursor_tint': {
        'normal': [
            "Set a color tint for your cursor",
            "Add a custom color to your cursor",
            "Change the cursor color using a hex code",
            "Tint your cursor a different color"
        ],
        'vulgar': [
            "Color your cursor. Make it match your personality.",
            "Cursor tint. Paint that pointer whatever color you want.",
            "Hex color input. #FF0000 if you're feeling dangerous.",
            "Tint your cursor. Because plain white is so last year.",
            "Color picker for your cursor. Go full rainbow if you dare."
        ]
    },
    'hotkey_reset': {
        'normal': [
            "Reset all keyboard shortcuts to their defaults",
            "Restore default key bindings for all shortcuts",
            "Undo all custom hotkey changes",
            "Return all shortcuts to factory settings"
        ],
        'vulgar': [
            "Reset all hotkeys to defaults. Panic button for keybinds.",
            "Factory reset your shortcuts. Undo all your 'improvements'.",
            "Reset everything. Start fresh. Embrace the defaults.",
            "Nuclear option for hotkeys. Resets EVERYTHING.",
            "Defaults button. For when your custom bindings are a disaster."
        ]
    },
    'sound_choice': {
        'normal': [
            "Choose which sound to play for this event",
            "Select a sound style for this event",
            "Pick a different audio tone for this action",
            "Change the sound effect for this event"
        ],
        'vulgar': [
            "Pick a sound style. Chime, beep, whatever tickles your fancy.",
            "Sound selector. Mix and match your audio nightmare.",
            "Choose your weapon. I mean sound. Same energy.",
            "What noise do you want for this event? Go wild.",
            "Sound picker. The DJ booth of settings panels."
        ]
    },
    'per_event_sound': {
        'normal': [
            "Toggle individual sounds on or off for specific events",
            "Control which events play sound effects",
            "Enable or disable sounds for each event type",
            "Manage individual sound event toggles"
        ],
        'vulgar': [
            "Micromanage your sounds. Mute what annoys you.",
            "Individual sound toggles for control freaks.",
            "Pick and choose which sounds you tolerate. Fair enough.",
            "Per-event audio control. Because one size doesn't fit all.",
            "Cherry-pick your sounds like the picky bastard you are."
        ]
    },
}


class TooltipMode(Enum):
    """Tooltip verbosity modes"""
    NORMAL = "normal"
    DUMBED_DOWN = "dumbed-down"
    VULGAR_PANDA = "vulgar_panda"


@dataclass
class TutorialStep:
    """Represents a single tutorial step"""
    title: str
    message: str
    target_widget: Optional[Any] = None  # Widget to highlight
    highlight_mode: str = "border"  # "border", "overlay", "arrow"
    button_text: str = "Next"
    show_back: bool = True
    show_skip: bool = True
    arrow_direction: str = "down"  # "up", "down", "left", "right"
    celebration: bool = False  # Show celebration effect on this step


class TutorialManager:
    """Manages the tutorial flow and UI overlays"""
    
    def __init__(self, master_window, config):
        self.master = master_window
        self.config = config
        self.current_step = 0
        self.tutorial_window = None
        self.overlay = None
        self.tutorial_active = False
        self.steps = []
        self.on_complete_callback = None
        
    def is_first_run(self) -> bool:
        """Check if this is the first run of the application"""
        # Check both 'completed' and 'seen' flags for consistency
        completed = self.config.get('tutorial', 'completed', default=False)
        seen = self.config.get('tutorial', 'seen', default=False)
        return not (completed or seen)
    
    def should_show_tutorial(self) -> bool:
        """Determine if tutorial should be shown"""
        show_on_startup = self.config.get('tutorial', 'show_on_startup', default=True)
        return show_on_startup and self.is_first_run() and GUI_AVAILABLE
    
    def start_tutorial(self, on_complete: Optional[Callable] = None):
        """Start the first-run tutorial"""
        if not GUI_AVAILABLE:
            logger.warning("GUI not available, skipping tutorial")
            return
        
        try:
            self.on_complete_callback = on_complete
            self.tutorial_active = True
            self.current_step = 0
            self.steps = self._create_tutorial_steps()
            
            # Create semi-transparent overlay
            self._create_overlay()
            
            # Show first step
            self._show_step(0)
        except Exception as e:
            logger.error(f"Failed to start tutorial: {e}", exc_info=True)
            self.tutorial_active = False
            if self.overlay:
                try:
                    self.overlay.destroy()
                except Exception:
                    pass
                self.overlay = None
    
    def _create_tutorial_steps(self) -> List[TutorialStep]:
        """Create the 7-step tutorial sequence"""
        steps = [
            TutorialStep(
                title="Welcome to PS2 Texture Sorter! 🐼",
                message=(
                    "Welcome! This quick tutorial will show you how to use the application.\n\n"
                    "PS2 Texture Sorter helps you organize and manage texture files from "
                    "PS2 game dumps with intelligent classification and LOD detection.\n\n"
                    "Let's get started!"
                ),
                target_widget=None,
                show_back=False,
                show_skip=True,
                celebration=False
            ),
            TutorialStep(
                title="Step 1: Select Input Directory",
                message=(
                    "First, you need to select the folder containing your texture files.\n\n"
                    "Click the 'Browse' button next to 'Input Directory' to choose "
                    "the folder with your unsorted textures.\n\n"
                    "Supported formats: DDS, PNG, JPG, BMP, TGA"
                ),
                target_widget="input_browse",
                highlight_mode="border",
                arrow_direction="down"
            ),
            TutorialStep(
                title="Step 2: Organization Style",
                message=(
                    "Choose how you want your textures organized:\n\n"
                    "• By Category: Groups by type (UI, Characters, etc.)\n"
                    "• By Size: Organizes by texture dimensions\n"
                    "• Flat: Keeps everything in one folder\n"
                    "• Hierarchical: Creates nested category folders\n\n"
                    "The default 'By Category' works great for most users!"
                ),
                target_widget="style_dropdown",
                highlight_mode="border",
                arrow_direction="left"
            ),
            TutorialStep(
                title="Step 3: Categories & LOD Detection",
                message=(
                    "The app automatically detects texture types:\n\n"
                    "• UI Elements (buttons, icons)\n"
                    "• Characters (player models, NPCs)\n"
                    "• Environment (terrain, buildings)\n"
                    "• Effects (particles, lighting)\n\n"
                    "LOD Detection groups textures by detail level:\n"
                    "LOD0 (highest detail) → LOD1 → LOD2 → LOD3 (lowest detail)"
                ),
                target_widget="detect_lods",
                highlight_mode="border",
                arrow_direction="up"
            ),
            TutorialStep(
                title="Step 4: Meet Your Panda Companion! 🐼",
                message=(
                    "Your panda companion is always here!\n\n"
                    "Your panda features:\n"
                    "• Animated panda companion on your screen\n"
                    "• Fun (and sometimes vulgar) tooltips\n"
                    "• Easter eggs and achievements\n"
                    "• Mood-based reactions\n\n"
                    "Customize your panda in Settings → Customization"
                ),
                target_widget=None,
                celebration=False
            ),
            TutorialStep(
                title="Step 5: Start Sorting!",
                message=(
                    "Ready to organize your textures?\n\n"
                    "1. Make sure input and output directories are set\n"
                    "2. Choose your preferred organization style\n"
                    "3. Click 'Start Sorting' to begin!\n\n"
                    "The app will:\n"
                    "• Scan all texture files\n"
                    "• Classify them automatically\n"
                    "• Organize them into folders\n"
                    "• Show progress in real-time"
                ),
                target_widget="start_button",
                highlight_mode="border",
                arrow_direction="down"
            ),
            TutorialStep(
                title="You're All Set! 🎉",
                message=(
                    "Congratulations! You're ready to start sorting textures!\n\n"
                    "Quick Tips:\n"
                    "• Press F1 anytime for context-sensitive help\n"
                    "• Check the Achievements tab for fun challenges\n"
                    "• Use the Notepad tab for project notes\n"
                    "• Explore Settings for customization options\n\n"
                    "Need help? Click the ❓ button in the menu bar!\n\n"
                    "Happy sorting! 🐼"
                ),
                target_widget=None,
                show_back=True,
                show_skip=False,
                button_text="Finish",
                celebration=True
            )
        ]
        return steps
    
    def _create_overlay(self):
        """Create semi-transparent dark overlay"""
        if not GUI_AVAILABLE:
            return
        
        try:
            # Create toplevel window for overlay
            self.overlay = ctk.CTkToplevel(self.master)
            self.overlay.title("")
            
            # Make it cover the entire main window
            self.overlay.attributes('-alpha', 0.7)  # Semi-transparent
            self.overlay.attributes('-topmost', True)
            
            # Get main window position and size
            self.master.update_idletasks()
            x = self.master.winfo_x()
            y = self.master.winfo_y()
            width = self.master.winfo_width()
            height = self.master.winfo_height()
            
            self.overlay.geometry(f"{width}x{height}+{x}+{y}")
            self.overlay.overrideredirect(True)
            
            # Dark background
            overlay_frame = ctk.CTkFrame(self.overlay, fg_color="#000000")
            overlay_frame.pack(fill="both", expand=True)
            
            # Add click handler to overlay to prevent getting stuck
            # Clicking the overlay will bring tutorial window to front or close tutorial if window is gone
            overlay_frame.bind("<Button-1>", self._on_overlay_click)
        except Exception as e:
            logger.error(f"Failed to create tutorial overlay: {e}", exc_info=True)
            self.overlay = None
    
    def _on_overlay_click(self, event=None):
        """Handle clicks on the overlay - bring tutorial to front or close if missing"""
        if self.tutorial_window and self.tutorial_window.winfo_exists():
            # Tutorial window exists, bring it to front
            # Ensure overlay stays below tutorial window
            if self.overlay:
                self.overlay.attributes('-topmost', False)
            self.tutorial_window.attributes('-topmost', True)
            self.tutorial_window.lift()
            self.tutorial_window.focus_force()
        else:
            # Tutorial window is gone but overlay remains - clean up
            self._complete_tutorial()
    
    def _show_step(self, step_index: int):
        """Display a tutorial step"""
        if step_index < 0 or step_index >= len(self.steps):
            self._complete_tutorial()
            return
            
        step = self.steps[step_index]
        self.current_step = step_index
        
        logger.debug(f"Showing tutorial step {step_index + 1}/{len(self.steps)}: {step.title}")
        
        # Create tutorial dialog
        if self.tutorial_window:
            self.tutorial_window.destroy()
        
        self.tutorial_window = ctk.CTkToplevel(self.master)
        self.tutorial_window.title(step.title)
        
        # Set protocol handler for window close button (X)
        # This ensures overlay is properly destroyed when user closes the window
        self.tutorial_window.protocol("WM_DELETE_WINDOW", self._complete_tutorial)
        
        # Center the window
        window_width = 500
        window_height = 350 if not step.celebration else 400
        screen_width = self.tutorial_window.winfo_screenwidth()
        screen_height = self.tutorial_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.tutorial_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # CRITICAL: Ensure tutorial window is above overlay in z-order
        # Lower overlay topmost temporarily so tutorial window can be on top
        if self.overlay:
            self.overlay.attributes('-topmost', False)
            logger.debug("Lowered overlay topmost to ensure tutorial window is clickable")
        
        # Make tutorial window topmost and lift it above everything
        self.tutorial_window.attributes('-topmost', True)
        self.tutorial_window.lift()
        self.tutorial_window.focus_force()
        logger.debug("Tutorial window raised above overlay and focused")
        
        # Content frame
        content = ctk.CTkFrame(self.tutorial_window)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content,
            text=step.title,
            font=("Arial Bold", 18)
        )
        title_label.pack(pady=(0, 15))
        
        # Message
        message_label = ctk.CTkLabel(
            content,
            text=step.message,
            font=("Arial", 12),
            wraplength=450,
            justify="left"
        )
        message_label.pack(pady=10, fill="both", expand=True)
        
        # Celebration effect for last step
        if step.celebration:
            celebration_label = ctk.CTkLabel(
                content,
                text="🎉 🐼 🎊 ✨ 🎈",
                font=("Arial", 24)
            )
            celebration_label.pack(pady=10)
        
        # Progress indicator
        progress_text = f"Step {step_index + 1} of {len(self.steps)}"
        progress_label = ctk.CTkLabel(
            content,
            text=progress_text,
            font=("Arial", 10),
            text_color="gray"
        )
        progress_label.pack(pady=5)
        
        # Buttons frame
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(pady=15)
        
        if step.show_skip and step_index < len(self.steps) - 1:
            skip_btn = ctk.CTkButton(
                button_frame,
                text="Skip Tutorial",
                width=120,
                command=self._skip_tutorial,
                fg_color="gray"
            )
            skip_btn.pack(side="left", padx=5)
        
        if step.show_back and step_index > 0:
            back_btn = ctk.CTkButton(
                button_frame,
                text="Back",
                width=100,
                command=lambda: self._show_step(step_index - 1)
            )
            back_btn.pack(side="left", padx=5)
        
        next_btn = ctk.CTkButton(
            button_frame,
            text=step.button_text,
            width=120,
            command=lambda: self._show_step(step_index + 1)
        )
        next_btn.pack(side="left", padx=5)
        
        # Don't show again checkbox on last step
        if step_index == len(self.steps) - 1:
            self.dont_show_var = ctk.BooleanVar(value=True)
            dont_show_check = ctk.CTkCheckBox(
                content,
                text="Don't show this tutorial again",
                variable=self.dont_show_var
            )
            dont_show_check.pack(pady=5)
    
    def _skip_tutorial(self):
        """Skip the tutorial"""
        # Temporarily lower overlay so messagebox is visible
        if self.overlay:
            self.overlay.attributes('-topmost', False)
        
        # Also ensure tutorial window is above overlay
        if self.tutorial_window:
            self.tutorial_window.lift()
        
        result = messagebox.askyesno(
            "Skip Tutorial", 
            "Are you sure you want to skip the tutorial? You can restart it later from Settings."
        )
        if result:
            self._complete_tutorial()
        else:
            # User chose not to skip, ensure tutorial window is on top
            if self.tutorial_window:
                self.tutorial_window.lift()
                self.tutorial_window.focus_force()
    
    def _complete_tutorial(self):
        """Complete and close the tutorial"""
        try:
            logger.info("Completing tutorial - starting cleanup process")
            
            # Check if user wants to skip tutorial in future
            try:
                if hasattr(self, 'dont_show_var') and self.dont_show_var.get():
                    logger.debug("User opted to skip tutorial in future")
                    self.config.set('tutorial', 'completed', value=True)
                else:
                    # User may want to see tutorial again, just mark as seen
                    logger.debug("Tutorial marked as seen but not completed")
                    self.config.set('tutorial', 'seen', value=True)
                
                # Save config changes
                self.config.save()
                logger.debug("Tutorial preferences saved to config")
            except Exception as e:
                logger.error(f"Failed to save tutorial preferences: {e}", exc_info=True)
                # Continue cleanup even if config save fails
            
            # Close tutorial windows
            try:
                if self.tutorial_window and self.tutorial_window.winfo_exists():
                    logger.debug("Destroying tutorial window")
                    self.tutorial_window.destroy()
                    self.tutorial_window = None
                    logger.info("Tutorial window destroyed successfully")
                elif self.tutorial_window:
                    logger.warning("Tutorial window exists but winfo_exists() returned False")
                    self.tutorial_window = None
            except Exception as e:
                logger.error(f"Error destroying tutorial window: {e}", exc_info=True)
                self.tutorial_window = None
            
            try:
                if self.overlay and self.overlay.winfo_exists():
                    logger.debug("Destroying overlay")
                    self.overlay.destroy()
                    self.overlay = None
                    logger.info("Overlay destroyed successfully")
                elif self.overlay:
                    logger.warning("Overlay exists but winfo_exists() returned False")
                    self.overlay = None
            except Exception as e:
                logger.error(f"Error destroying overlay: {e}", exc_info=True)
                self.overlay = None
            
            self.tutorial_active = False
            logger.info("Tutorial marked as inactive")
            
            # Call completion callback
            try:
                if self.on_complete_callback:
                    logger.debug("Calling completion callback")
                    self.on_complete_callback()
                    logger.debug("Completion callback executed successfully")
            except Exception as e:
                logger.error(f"Error in completion callback: {e}", exc_info=True)
                
        except Exception as e:
            logger.error(f"Unexpected error in _complete_tutorial: {e}", exc_info=True)
            # Ensure cleanup happens even on error
            self.tutorial_active = False
            self.tutorial_window = None
            self.overlay = None
    
    def reset_tutorial(self):
        """Reset tutorial completion flags so it can be shown again"""
        self.config.set('tutorial', 'completed', value=False)
        self.config.set('tutorial', 'seen', value=False)
        self.config.save()  # Make sure changes are persisted
        logger.info("Tutorial reset - will show on next start or manual trigger")


class TooltipVerbosityManager:
    """Manages tooltip verbosity levels across the application"""
    
    def __init__(self, config):
        self.config = config
        self.current_mode = self._load_mode()
        self._last_tooltip = {}  # Track last tooltip per widget_id to avoid repeats
        
        # Tooltip collections for each mode
        self.tooltips = {
            TooltipMode.NORMAL: self._get_normal_tooltips(),
            TooltipMode.DUMBED_DOWN: self._get_dumbed_down_tooltips(),
            TooltipMode.VULGAR_PANDA: self._get_vulgar_panda_tooltips()
        }
    
    def _load_mode(self) -> TooltipMode:
        """Load tooltip mode from config"""
        mode_str = self.config.get('ui', 'tooltip_mode', default='normal')
        try:
            return TooltipMode(mode_str)
        except ValueError:
            return TooltipMode.NORMAL
    
    def set_mode(self, mode: TooltipMode):
        """Change tooltip verbosity mode"""
        self.current_mode = mode
        self.config.set('ui', 'tooltip_mode', value=mode.value)
        self.config.save()
    
    def get_tooltip(self, widget_id: str) -> str:
        """Get tooltip text for a widget based on current mode.
        
        For list-based tooltips (e.g. vulgar mode), picks a random variant
        with cooldown to avoid repeating the same line back-to-back.
        Falls back to normal mode if widget_id not found in current mode.
        """
        tooltips = self.tooltips.get(self.current_mode, {})
        tooltip = tooltips.get(widget_id, "")
        
        # Fall back to normal mode if current mode doesn't have this widget
        if not tooltip and self.current_mode != TooltipMode.NORMAL:
            normal_tooltips = self.tooltips.get(TooltipMode.NORMAL, {})
            tooltip = normal_tooltips.get(widget_id, "")
        
        # If tooltip is a list, pick a random one with cooldown
        if isinstance(tooltip, list):
            if not tooltip:
                return ""
            if len(tooltip) == 1:
                return tooltip[0]
            # Avoid repeating last shown tooltip for this widget
            last = self._last_tooltip.get(widget_id)
            choices = [t for t in tooltip if t != last]
            if not choices:
                choices = tooltip
            selected = random.choice(choices)
            self._last_tooltip[widget_id] = selected
            return selected
        
        return tooltip
    
    def _get_normal_tooltips(self) -> Dict[str, Any]:
        """Standard helpful tooltips"""
        base_tooltips = {
            'sort_button': "Click to sort your textures into organized folders",
            'convert_button': "Convert textures to different formats",
            'input_browse': "Browse for the folder containing your texture files",
            'output_browse': "Choose where to save the organized textures",
            'detect_lods': "Automatically detect and group LOD levels (Level of Detail)",
            'group_lods': "Keep LOD variants together in the same folder",
            'detect_duplicates': "Find and handle duplicate texture files",
            'style_dropdown': "Choose how to organize your textures",
            'settings_button': "Open settings and preferences",
            'theme_button': "Switch between dark and light themes",
            'help_button': "Get help and documentation",
            'achievements_tab': "View your achievements and progress milestones",
            'shop_tab': "Opens the reward store where earned points can be spent",
            'shop_buy_button': "Purchase this item with your currency",
            'shop_category_button': "Filter shop items by this category",
            'rewards_tab': "View all unlockable rewards and their requirements",
            'closet_tab': "Customize your panda's appearance with outfits and accessories",
            'browser_browse_button': "Select a directory to browse for texture files",
            'browser_refresh_button': "Refresh the file list to show current directory contents",
            'browser_search': "Search for files by name in the current directory",
            'browser_show_all': "Toggle between showing only textures or all file types",
            # Tab tooltips
            'sort_tab': "Sort and organize PS2 texture dumps into categories",
            'convert_tab': "Batch convert texture files between formats (DDS, PNG, JPG, etc.)",
            'browser_tab': "Browse and preview texture files in a directory",
            'notepad_tab': "Jot down notes and project information",
            'about_tab': "View application info, credits, and keyboard shortcuts",
            # Category tooltips
            'tools_category': "Access sorting, conversion, and file browsing tools",
            'features_category': "Interact with your panda, shop, achievements, and more",
            # Feature tab tooltips
            'inventory_tab': "View and use your collected toys and food items",
            'panda_stats_tab': "Check your panda's mood, stats, and interaction history",
            'minigames_tab': "Play mini-games to earn rewards and have fun",
            # Settings tooltips
            'keyboard_controls': "View and customize keyboard shortcuts",
            'tooltip_mode': "Choose how tooltips are displayed: normal, beginner, or vulgar",
            'theme_selector': "Choose a visual theme for the application",
            # Sound settings tooltips
            'sound_enabled': "Enable or disable all sound effects",
            'master_volume': "Adjust the overall volume level for all sounds",
            'effects_volume': "Control the volume of sound effects",
            'notifications_volume': "Control the volume of notification sounds",
            'sound_pack': "Choose a sound pack style for audio feedback",
            'per_event_sound': "Toggle individual sounds on or off for specific events",
            'sound_test_button': "Play a preview of this event's sound",
            'sound_choice': "Choose which sound to play for this event",
            # Cursor settings tooltips
            'cursor_type': "Select the style of your mouse cursor",
            'cursor_size': "Change the size of your mouse cursor",
            'cursor_tint': "Set a color tint for your cursor",
            'cursor_trail': "Enable or disable cursor trail effects",
            'trail_style': "Choose the visual style for your cursor trail",
            # Hotkey settings tooltips
            'hotkey_edit': "Click to change the key binding for this shortcut",
            'hotkey_toggle': "Enable or disable this keyboard shortcut",
            'hotkey_reset': "Reset all keyboard shortcuts to their defaults",
            # Inventory tooltips
            'inventory_purchased': "Items purchased from the shop",
            'inventory_give_button': "Give this item to your panda for interaction",
            'inventory_toy': "Your toy collection — use toys to play with your panda",
            'inventory_food': "Your food collection — feed your panda to increase happiness",
            'inventory_accessory': "Your accessory collection — equip via the closet",
            'inventory_unlocked': "Summary of rewards you have unlocked so far",
            # Closet tooltips
            'closet_header': "Dress up your panda with outfits and accessories you own",
            'closet_equip': "Equip this item on your panda",
            'closet_unequip': "Remove this item from your panda",
            'closet_appearance': "Your panda's current outfit summary",
            # Achievement tooltips
            'achievement_claim': "Claim the reward for this completed achievement",
            'achievement_claim_all': "Claim all available achievement rewards at once",
            'achievement_progress': "Track your progress toward completing this achievement",
            # Shop-specific tooltips
            'shop_price': "The cost in Bamboo Bucks to purchase this item",
            'shop_level_req': "The user level required to unlock this item for purchase",
            'shop_item_name': "Click for more details about this item",
        }
        
        # Merge tooltip variants from the inlined tooltip definitions
        try:
            for widget_id, tooltip_dict in _PANDA_TOOLTIPS.items():
                if 'normal' in tooltip_dict:
                    base_tooltips[widget_id] = tooltip_dict['normal']
        except Exception as e:
            logger.warning(f"Error loading normal tooltips: {e}")
        
        return base_tooltips
    
    def _get_dumbed_down_tooltips(self) -> Dict[str, str]:
        """Detailed explanations for beginners with random variants"""
        return {
            'sort_button': [
                "This button will look at all your texture files, figure out what type "
                "each one is (UI, character, environment, etc.), and move them into "
                "neat, organized folders. Just click it to start!",
                "Press this to automatically organize your textures! The app scans each "
                "file and sorts it into the right category folder for you.",
                "Ready to organize? Click here and the app will sort all your texture "
                "files into tidy folders based on what they are.",
            ],
            'convert_button': [
                "Use this to change your texture files from one format to another. "
                "For example, you can convert DDS files to PNG, or PNG to DDS. "
                "This is useful when different programs need different file formats.",
                "Need your textures in a different format? This converts them! "
                "Great for switching between DDS (game format) and PNG (editing format).",
            ],
            'input_browse': [
                "Click this button to find and select the folder on your computer "
                "that has all your texture files in it. This is where the app will "
                "look for textures to organize.",
                "Pick the folder that contains your texture files. The app will "
                "scan everything inside this folder.",
            ],
            'output_browse': [
                "Click here to choose where you want your organized textures to be saved. "
                "The app will create new folders here and put your sorted textures inside them.",
                "Choose a destination folder where the sorted textures will go. "
                "New category folders will be created inside automatically.",
            ],
            'detect_lods': [
                "LOD means 'Level of Detail'. Many games use multiple versions of the same "
                "texture at different quality levels. Enable this to automatically find and "
                "group these different versions together.",
                "Games often have high-quality and low-quality versions of the same texture. "
                "Turn this on to find and group those versions together.",
            ],
            'lod_detection': [
                "LOD means 'Level of Detail'. Many games use multiple versions of the same "
                "texture at different quality levels. Enable this to automatically find and "
                "group these different versions together.",
                "This finds different quality versions of the same texture (high, medium, low) "
                "and groups them so you can easily compare them.",
            ],
            'group_lods': [
                "When enabled, this keeps all the different quality versions of the same "
                "texture in one folder, making it easier to find related files.",
                "Keeps related LOD textures together in one folder instead of "
                "spreading them across different category folders.",
            ],
            'detect_duplicates': [
                "This feature will scan your textures and find any files that are exact "
                "copies of each other, helping you save disk space and keep things clean.",
                "Find duplicate files that are taking up extra space. The app will "
                "identify exact copies so you can decide what to keep.",
            ],
            'style_dropdown': [
                "This dropdown menu lets you choose different ways to organize your files. "
                "'Simple Flat' puts files in category folders. 'By Game Area' sorts by "
                "level, 'By Module' sorts by character/vehicle/UI, and more.",
                "Pick an organization style! Each one arranges your files differently. "
                "Try 'Simple Flat' if you're not sure which to choose.",
            ],
            'settings_button': [
                "Click here to open the settings window where you can customize how the "
                "app looks and behaves. You can change themes, adjust performance, and more!",
                "Open settings to personalize the app. Change colors, themes, "
                "performance options, and lots more!",
            ],
            'theme_button': [
                "Switch between a dark theme (easier on the eyes) and a light theme (better "
                "for bright environments). Just click to toggle!",
                "Toggle dark/light mode. Dark mode is great for working at night!",
            ],
            'theme_selector': [
                "Switch between a dark theme (easier on the eyes) and a light theme (better "
                "for bright environments). Or try a fun custom theme!",
                "Pick a visual theme for the app. There are several presets to choose from!",
            ],
            'help_button': [
                "Need help? Click this button to open the help panel with guides, FAQs, "
                "and troubleshooting tips.",
                "Stuck? Click here for help, FAQs, and step-by-step guides!",
            ],
            'tutorial_button': [
                "Click here to start or restart the interactive tutorial. It will walk "
                "you through all the features step by step!",
                "New here? Start the tutorial to learn how everything works!",
            ],
            'file_selection': [
                "Click here to open a file picker and navigate to the folder "
                "that contains your texture files.",
            ],
            'search_button': [
                "Type in here to search for specific texture files by their name. "
                "It will filter the file list as you type!",
                "Search for files by typing part of their name. Results update as you type!",
            ],
            'batch_operations': [
                "This lets you work with multiple files at the same time instead "
                "of one at a time, saving you lots of effort!",
            ],
            'achievements_tab': [
                "This tab shows all the achievements you can earn by using the app. "
                "Each achievement tracks your progress and unlocks rewards when completed!",
                "View your achievements! Complete challenges to earn rewards and "
                "unlock new features.",
            ],
            'shop_tab': [
                "This is where you trade points for cool stuff. You earn points by "
                "sorting textures and completing achievements, then spend them here!",
                "The shop! Spend your earned Bamboo Bucks on themes, cursors, "
                "outfits, and other fun items.",
            ],
            'shop_buy_button': [
                "Click this button to buy the item. Make sure you have enough points "
                "first! The price is shown next to the item.",
            ],
            'shop_category_button': [
                "Click one of these buttons to show only items from that category. "
                "This helps you find what you're looking for faster.",
            ],
            'rewards_tab': [
                "This tab shows all the things you can unlock, like custom cursors, "
                "themes, and panda outfits. Each item shows what you need to do to get it!",
            ],
            'closet_tab': [
                "This is where you dress up your panda companion! Choose from outfits "
                "and accessories you've unlocked to make your panda look unique.",
                "Dress up your panda! Pick outfits, hats, and accessories "
                "from your unlocked collection.",
            ],
            'browser_browse_button': [
                "Click this button to open a folder picker. Navigate to the folder "
                "where your texture files are stored to browse them.",
            ],
            'browser_refresh_button': [
                "Click this to reload the list of files. Use it if you've added or "
                "removed files while the browser is open.",
            ],
            'browser_search': [
                "Type a file name (or part of one) here to filter the file list. "
                "Only files matching what you type will be shown.",
            ],
            'browser_show_all': [
                "By default, only texture files are shown. Check this box to see "
                "ALL files in the folder, including non-texture files.",
            ],
            # Tab tooltips
            'sort_tab': [
                "This is where you sort your texture files! Select an input folder "
                "with your textures, an output folder, and click Sort to organize them.",
            ],
            'convert_tab': [
                "This tab lets you change your texture files from one format to another. "
                "For example, DDS to PNG or PNG to DDS.",
            ],
            'browser_tab': [
                "Use this tab to look through your texture files. You can preview them "
                "and search for specific files.",
            ],
            'notepad_tab': [
                "A handy notepad where you can write down notes about your project, "
                "keep track of what you've done, or plan your next steps.",
            ],
            'about_tab': [
                "Information about the app, who made it, and a handy list of "
                "all the keyboard shortcuts you can use.",
            ],
            # Category tooltips
            'tools_category': [
                "This section has all the main tools: sorting textures, converting "
                "file formats, and browsing your texture files.",
            ],
            'features_category': [
                "This section has fun extras: your panda companion, the shop where "
                "you spend points, achievements, and your inventory.",
            ],
            # Feature tab tooltips
            'inventory_tab': [
                "Your collection of toys and food items! Use them to interact with "
                "your panda and make it happy.",
                "Everything you own is here — toys, food, and accessories. "
                "Click 'Give to Panda' to use any unlocked item.",
                "Your item collection! Organized by category and rarity. "
                "Locked items need to be purchased from the Shop first.",
                "All your stuff in one place. Use toys to play, food to feed, "
                "and accessories to decorate your panda!",
                "The inventory shows everything you've collected. Items are sorted "
                "by type and rarity for easy browsing.",
            ],
            'inventory_purchased': [
                "These are items you've bought from the shop. They're yours to keep!",
                "Your purchased items from the shop are listed here.",
                "Everything you've spent Bamboo Bucks on shows up here.",
                "Shop purchases appear in this section. One-time items stay forever!",
                "Your shopping history — all purchased items are shown here.",
            ],
            'inventory_give_button': [
                "Give this item to your panda! They'll react with an animation.",
                "Click to use this item with your panda companion.",
                "Share this with your panda — watch them play or eat!",
                "Hand this over to your panda and see what happens!",
                "Your panda would love this! Click to give it to them.",
                "Use this item on your panda for a fun interaction.",
            ],
            'panda_stats_tab': [
                "See how your panda is doing! Check its mood, how many times "
                "you've petted or fed it, and other fun stats.",
                "Your panda's dashboard — mood, interaction history, level, "
                "and a live preview all in one place.",
                "Everything about your panda at a glance. Stats update "
                "automatically every few seconds!",
                "Check on your panda friend — see their mood, stats, level, "
                "and even discovered easter eggs.",
                "The panda stats page shows live data about your companion. "
                "No refresh needed — it updates on its own!",
            ],
            # Closet tooltips
            'closet_tab': [
                "This is where you dress up your panda companion! Choose from outfits "
                "and accessories you've unlocked to make your panda look unique.",
                "Dress up your panda! Pick outfits, hats, and accessories "
                "from your unlocked collection.",
                "Your panda's wardrobe — equip or unequip items you own. "
                "Buy new items in the Shop to expand your collection!",
                "Mix and match fur styles, clothes, hats, shoes, and accessories "
                "to create your perfect panda look!",
                "The closet only shows items you own. Visit the Shop to "
                "buy new outfits and accessories!",
            ],
            'closet_equip': [
                "Click to put this item on your panda.",
                "Equip this item — your panda will wear it right away!",
                "Dress your panda with this item. Click to equip!",
                "Add this to your panda's outfit. Click to equip.",
                "Your panda would look great in this! Click to try it on.",
            ],
            'closet_unequip': [
                "Click to take this item off your panda.",
                "Remove this item from your panda's outfit.",
                "Unequip this item — it'll go back to your collection.",
                "Take this off your panda. You can re-equip it anytime!",
                "Remove from outfit. The item stays in your closet.",
            ],
            # Achievement tooltips
            'achievements_tab': [
                "This tab shows all the achievements you can earn by using the app. "
                "Each achievement tracks your progress and unlocks rewards when completed!",
                "View your achievements! Complete challenges to earn rewards and "
                "unlock new features.",
                "Track your progress across different challenges. Completed achievements "
                "can be claimed for Bamboo Bucks and exclusive items!",
                "Your achievement collection — from beginner tasks to legendary challenges. "
                "Each one rewards you with points, currency, or exclusive items.",
                "Achievements are earned automatically as you use the app. "
                "Check back often to see your progress and claim rewards!",
            ],
            'achievement_claim': [
                "Click to collect your reward for completing this achievement!",
                "You've earned this! Click Claim to get your reward.",
                "Reward ready! Click to add it to your collection.",
                "Congratulations! Claim your well-deserved reward here.",
                "This achievement is complete — click to claim your prize!",
            ],
            'achievement_claim_all': [
                "Claim all available rewards at once — quick and easy!",
                "Got multiple completed achievements? Claim everything in one click!",
                "Batch claim all your pending rewards. No reward left behind!",
                "Collect all your achievement rewards with a single click.",
                "Why claim one at a time? Get all your rewards here!",
            ],
            # Shop tooltips
            'shop_tab': [
                "This is where you trade points for cool stuff. You earn points by "
                "sorting textures and completing achievements, then spend them here!",
                "The shop! Spend your earned Bamboo Bucks on themes, cursors, "
                "outfits, and other fun items.",
                "Browse items for sale — outfits, themes, cursors, food, and more! "
                "Earn Bamboo Bucks through achievements and interactions.",
                "Your one-stop shop for panda accessories, app themes, cursors, "
                "and special upgrades. New items unlock as you level up!",
                "Spend your hard-earned Bamboo Bucks here. Higher-level items "
                "become available as you gain experience.",
            ],
            'shop_buy_button': [
                "Click this button to buy the item. Make sure you have enough points "
                "first! The price is shown next to the item.",
                "Purchase this item with your Bamboo Bucks. The price is deducted "
                "from your balance immediately.",
                "Buy this item! You'll be asked to confirm before the purchase "
                "goes through.",
                "Ready to buy? Click here! You'll get a confirmation dialog first.",
                "Add this to your collection! Requires enough Bamboo Bucks.",
            ],
            'shop_category_button': [
                "Click one of these buttons to show only items from that category. "
                "This helps you find what you're looking for faster.",
                "Filter the shop by category to find items faster.",
                "Browse a specific type of item. Click any category to filter.",
                "Narrow down the shop to just this category of items.",
                "Show only items in this category. Click another to switch.",
            ],
            'shop_price': [
                "The cost in Bamboo Bucks. Earn more by sorting textures and "
                "completing achievements!",
                "This is how many Bamboo Bucks you need. Check your balance "
                "in the top-right corner.",
                "Item price in Bamboo Bucks. You earn currency by using "
                "the app and completing challenges.",
                "Cost of this item. Not enough? Sort more textures or "
                "complete achievements to earn Bamboo Bucks!",
                "The price tag! Bamboo Bucks are earned through app usage, "
                "achievements, and panda interactions.",
            ],
            'shop_level_req': [
                "Some items require a higher user level. Keep using the app "
                "to level up and unlock more items!",
                "This item has a level requirement. Gain XP by sorting "
                "textures to reach the needed level.",
                "Level locked! Use the app more to gain experience and "
                "unlock this item.",
                "Your level isn't high enough yet. Keep sorting and "
                "interacting to level up!",
                "Reach the required level to purchase this. XP is earned "
                "through sorting and achievements.",
            ],
            'keyboard_controls': [
                "View all keyboard shortcuts and change them to whatever keys "
                "you prefer. Click Edit next to any shortcut to change it.",
                "This panel lists every keyboard shortcut in the app. "
                "You can change any of them by clicking the Edit button!",
            ],
            'tooltip_mode': [
                "Choose how tooltips are shown: Normal gives standard info, "
                "Dumbed Down gives extra detail, Vulgar adds humor.",
                "Control tooltip style: Normal, Beginner-friendly, or Vulgar "
                "with sarcastic commentary!",
                "This controls the style of the little pop-up hints that appear "
                "when you hover over buttons. Pick the one you like!",
            ],
            'theme_selector': [
                "Pick a color theme for the application. Try dark mode for "
                "late-night sessions or light mode for daytime use.",
                "This changes all the colors of the app at once. "
                "There are several presets — just pick one and see!",
            ],
            # Sound settings tooltips
            'sound_enabled': [
                "This checkbox turns all sounds on or off. When unchecked, "
                "the app will be completely silent — no beeps, chimes, or effects.",
                "Toggle sound effects globally. When off, nothing will make noise.",
            ],
            'master_volume': [
                "This slider controls how loud everything is overall. Drag it "
                "left for quieter, right for louder. Affects all sound types.",
                "The master volume slider — controls the loudness of all sounds "
                "in the application at once.",
            ],
            'effects_volume': [
                "This slider controls just the sound effects (like clicks and "
                "completion sounds). Separate from notification volume.",
                "Adjust how loud the action sound effects are. These play when "
                "you click buttons or complete tasks.",
            ],
            'notifications_volume': [
                "This slider controls how loud notification sounds are. These "
                "are the sounds that play for alerts and status updates.",
                "Notification sounds volume — the sounds that tell you about "
                "achievements, errors, and other events.",
            ],
            'sound_pack': [
                "Choose a sound pack to change what all the sounds in the app "
                "sound like. Default is standard, Minimal is subtle, and "
                "Vulgar is... well, fun.",
                "Sound packs change the overall style of every sound effect. "
                "Try different ones to find your favorite!",
            ],
            'per_event_sound': [
                "Turn individual sounds on or off. For example, you can mute "
                "the button click sound but keep the achievement sound.",
                "Each event (like clicking, completing, error) has its own "
                "sound. Toggle them individually here!",
            ],
            'sound_test_button': [
                "Click this to hear what this sound sounds like with your "
                "current settings. Great for previewing before committing!",
                "Preview button! Plays the sound for this event so you can "
                "hear it before deciding to keep it or change it.",
            ],
            'sound_choice': [
                "Pick a different sound style for this event. Each option "
                "plays a unique tone — try them out with the Test button!",
                "Choose which sound plays for this event. Options include "
                "chimes, beeps, melodies, bells, and more.",
            ],
            # Cursor settings tooltips
            'cursor_type': [
                "This lets you change what your mouse pointer looks like. "
                "There are lots of fun options like crosshairs, hearts, and skulls!",
                "Pick a cursor style! The default arrow works great, but "
                "you can also try crosshairs, stars, or even a pirate skull.",
            ],
            'cursor_size': [
                "Make your cursor bigger or smaller. If you have trouble "
                "seeing the cursor, try a larger size.",
                "Cursor size options range from tiny to huge. Pick whatever "
                "is most comfortable for you to see and use.",
            ],
            'cursor_tint': [
                "Add a color tint to your cursor. Type a hex color code "
                "(like #FF0000 for red) or use the Pick button.",
                "This lets you color your cursor. Use the color picker "
                "or type a hex code directly.",
            ],
            'cursor_trail': [
                "Enable this to add a sparkly trail that follows your cursor. "
                "It's purely decorative and can be turned off anytime.",
                "Cursor trails leave a colorful effect behind your mouse "
                "as you move it. Fun but optional!",
            ],
            'trail_style': [
                "Choose the style of your cursor trail — rainbow, fire, "
                "ice, nature, galaxy, or gold. Each has unique colors!",
                "Different trail styles have different color patterns. "
                "Try them all to see which one you like best!",
            ],
            # Hotkey settings tooltips
            'hotkey_edit': [
                "Click this to change which key triggers this shortcut. "
                "Press the new key combination when prompted.",
                "Edit the keyboard shortcut for this action. A dialog "
                "will pop up where you press your new key combination.",
            ],
            'hotkey_toggle': [
                "Check or uncheck this to enable or disable this keyboard "
                "shortcut. Disabled shortcuts won't respond to key presses.",
                "Toggle this shortcut on or off. When off, pressing the key "
                "won't do anything for this action.",
            ],
            'hotkey_reset': [
                "Reset all keyboard shortcuts back to their original default "
                "settings. This undoes any custom key bindings you've made.",
                "Click to restore all hotkeys to factory defaults. "
                "Useful if you've messed up your shortcuts!",
            ],
        }
    
    def _get_vulgar_panda_tooltips(self) -> Dict[str, Any]:
        """Fun/sarcastic tooltips (vulgar mode)"""
        base_tooltips = {
            'sort_button': [
                "Click this to sort your damn textures. It's not rocket science, Karen.",
                "Hit this button and watch your textures get organized. Magic, right?",
            ],
            'convert_button': [
                "Turn your textures into whatever the hell format you need.",
                "Format conversion. Because one format is never enough for you people.",
            ],
            'input_browse': [
                "Find your texture folder. Come on, you can do this.",
                "Navigate to your texture folder. I believe in you. Maybe.",
            ],
            'output_browse': [
                "Where do you want this beautiful organized mess?",
                "Pick where the sorted stuff goes. Any folder. Your call.",
            ],
            'detect_lods': [
                "LOD detection. Fancy words for 'find the quality variants'.",
                "Find the blurry and sharp versions of the same texture. Science!",
            ],
            'group_lods': [
                "Keep LOD buddies together. They get lonely apart.",
                "Group quality variants together. Like a texture family reunion.",
            ],
            'detect_duplicates': [
                "Find duplicate textures. Because apparently you have trust issues.",
                "Spot the copycats. Your hard drive will thank you.",
            ],
            'style_dropdown': [
                "How do you want your stuff organized? Pick one, any one.",
                "Organization style. Because everyone's a control freak about something.",
            ],
            'settings_button': [
                "Tweak sh*t. Make it yours. Go nuts.",
                "Settings. Where the magic happens. Or where things break.",
            ],
            'theme_button': [
                "Dark mode = hacker vibes. Light mode = boomer energy.",
                "Toggle the dark side. Or the light side. No judgment.",
            ],
            'help_button': [
                "Lost? Confused? Click here, we'll hold your hand.",
                "Need help? That's what this button is for, genius.",
            ],
            'achievements_tab': [
                "Check your trophies, you overachiever.",
                "See how many fake awards you've collected. Congrats, I guess.",
            ],
            'shop_tab': [
                "This is the loot cave. Spend your shiny points, idiot.",
                "The shop. Where your hard-earned points go to die.",
            ],
            'shop_buy_button': [
                "Yeet your money at this item. Do it.",
                "Buy it. You know you want to. Impulse control is overrated.",
            ],
            'shop_category_button': [
                "Filter the shop. Because scrolling is for peasants.",
                "Narrow it down. Too many choices hurting your brain?",
            ],
            'rewards_tab': [
                "Your loot table. See what you can unlock.",
                "All the shiny things you haven't earned yet. Motivating, right?",
            ],
            'closet_tab': [
                "Dress up your panda. Fashion show time.",
                "Panda makeover! Because even virtual bears need style.",
            ],
            'browser_browse_button': [
                "Pick a folder. Any folder. Let's see what's inside.",
                "Open a folder. I promise we won't judge your file organization. Much.",
            ],
            'browser_refresh_button': [
                "Refresh. In case something magically changed.",
                "Reload the file list. For the paranoid types.",
            ],
            'browser_search': [
                "Find your damn files. Type something.",
                "Search for files. Use your keyboard. That's the thing with letters on it.",
            ],
            'browser_show_all': [
                "Show EVERYTHING. Even the weird files.",
                "Toggle this to see ALL files. Prepare yourself.",
            ],
            # Tab tooltips
            'sort_tab': [
                "The main event. Sort your textures or go home.",
                "Sorting tab. Where the real work happens.",
            ],
            'convert_tab': [
                "Format conversion. Because one format is never enough.",
                "Convert stuff. DDS, PNG, whatever floats your boat.",
            ],
            'browser_tab': [
                "Snoop through your texture files like a pro.",
                "Browse your files. Digital window shopping.",
            ],
            'notepad_tab': [
                "Scribble your thoughts. No one's judging. Maybe.",
                "Write notes. Or a novel. We don't care.",
            ],
            'about_tab': [
                "Credits and keyboard shortcuts. Riveting stuff.",
                "Who made this thing and how to use it. Thrilling.",
            ],
            # Category tooltips
            'tools_category': [
                "The useful stuff. Sorting, converting, browsing.",
                "Work tools. The boring but necessary section.",
            ],
            'features_category': [
                "The fun stuff. Panda, shop, achievements, bling.",
                "The cool extras. Panda time!",
            ],
            # Feature tab tooltips
            'inventory_tab': [
                "Your hoard of toys and snacks. Use 'em or lose 'em.",
                "All your stuff. Feed the panda or play with toys.",
                "Your loot stash. Every item you've hoarded is here.",
                "The toybox and snack drawer. Go wild.",
                "Your collection of random crap. Some of it's useful!",
                "Items galore. Give stuff to the panda or just admire it.",
            ],
            'inventory_purchased': [
                "Your shopping spree results. No refunds.",
                "Everything you blew your Bamboo Bucks on. Worth it? Maybe.",
                "Purchased goods. Your wallet cried, but here they are.",
                "All your impulse purchases in one convenient place.",
                "The evidence of your spending habits. No judgment. Much.",
            ],
            'inventory_give_button': [
                "Yeet this at the panda. They'll love it. Probably.",
                "Share with the panda. They're always hungry anyway.",
                "Give it to the bear. What's the worst that could happen?",
                "Hand it over to your fluffy roommate.",
                "Panda wants it. Panda gets it. Click the button.",
                "Bribe the panda with gifts. Classic strategy.",
            ],
            'panda_stats_tab': [
                "Stalk your panda's mood and life choices.",
                "Check on your panda. Is it happy? Who cares. Check anyway.",
                "Your panda's FBI file. All the stats, all the time.",
                "Mood check! See if your panda still likes you.",
                "Stats nerd paradise. Every click, pet, and feed tracked.",
                "The panda dashboard. Everything updates live. Fancy, right?",
            ],
            # Closet tooltips
            'closet_tab': [
                "Dress up your panda. Fashion show time.",
                "Panda makeover! Because even virtual bears need style.",
                "The panda wardrobe. Project Runway: Panda Edition.",
                "Fashion police? Never heard of 'em. Dress your panda however you want.",
                "Outfit central. Make your panda look fabulous. Or ridiculous.",
                "Closet raid! Equip outfits, hats, and accessories.",
            ],
            'closet_equip': [
                "Slap this on your panda. Fashion awaits.",
                "Dress up time! Put this on the bear.",
                "Equip it. Your panda's been waiting for this look.",
                "Add this to the outfit. Style points incoming.",
                "Your panda would rock this. Equip it already!",
            ],
            'closet_unequip': [
                "Strip it off. The panda doesn't mind. Probably.",
                "Remove this item. Back to the closet it goes.",
                "Take it off. Minimalism is a valid aesthetic.",
                "Unequip. Sometimes less is more. Or just more naked.",
                "Remove from outfit. Don't worry, it's still yours.",
            ],
            # Achievement tooltips
            'achievements_tab': [
                "Check your trophies, you overachiever.",
                "See how many fake awards you've collected. Congrats, I guess.",
                "Achievement unlocked: Opening the achievements tab. Just kidding.",
                "Your trophy case. Some earned, some... not so much.",
                "All your bragging rights in one place. You're welcome.",
                "Achievements! Because validation through virtual badges is totally normal.",
            ],
            'achievement_claim': [
                "Gimme gimme! Claim your reward, you earned it.",
                "Click to cash in. Cha-ching!",
                "Reward time! Claim it before the panda does.",
                "You did the thing! Now get the stuff!",
                "Free loot! Well, you did earn it. Technically.",
            ],
            'achievement_claim_all': [
                "CLAIM EVERYTHING. Maximum efficiency!",
                "Bulk claim. Because who has time for one-by-one?",
                "All the rewards. All at once. Living the dream.",
                "Speed run: Claim all rewards edition.",
                "One click to rule them all. Claim everything!",
            ],
            # Shop tooltips
            'shop_tab': [
                "This is the loot cave. Spend your shiny points, idiot.",
                "The shop. Where your hard-earned points go to die.",
                "Retail therapy, but make it virtual. And with a panda.",
                "Your Bamboo Bucks burning a hole in your pocket? Spend 'em here.",
                "The marketplace. Window shopping is free, buying costs bucks.",
                "Shop 'til you drop. Or until you're broke. Same thing.",
            ],
            'shop_buy_button': [
                "Yeet your money at this item. Do it.",
                "Buy it. You know you want to. Impulse control is overrated.",
                "Click buy. Regret later. That's the spirit!",
                "Purchase! Your wallet says no, but your heart says yes.",
                "Money is temporary. This item is... also temporary. But fun!",
            ],
            'shop_category_button': [
                "Filter the shop. Because scrolling is for peasants.",
                "Narrow it down. Too many choices hurting your brain?",
                "Category filter. For the organized shopper in you.",
                "Browse by type. Window shopping just got easier.",
                "Pick a lane. What are you shopping for today?",
            ],
            'shop_price': [
                "That's the price tag. No haggling allowed.",
                "The damage. Can you afford it? Only one way to find out.",
                "Cost in Bamboo Bucks. Earn more by actually using the app.",
                "The price. Not negotiable. I don't make the rules.",
                "How much this costs. Start sorting more textures if you're broke.",
            ],
            'shop_level_req': [
                "Level locked, noob. Keep grinding.",
                "Your level isn't high enough. Git gud.",
                "Need more XP to unlock this. Back to the texture mines!",
                "Level requirement. AKA 'you need to use the app more.'",
                "Locked behind a level gate. Time to grind, baby!",
            ],
            'keyboard_controls': [
                "Keyboard shortcuts. Customize 'em if you dare.",
                "Hotkeys. For when clicking is too much effort.",
                "Key bindings. Ctrl+Z your way out of problems.",
                "Shortcuts for the lazy and the efficient. Same thing.",
                "Remap keys. Because defaults are for normies.",
            ],
            'tooltip_mode': [
                "Control the sass level. You've been warned.",
                "Switch tooltip modes. You're in vulgar mode. Obviously.",
                "Tooltip flavor picker. You chose chaos. Good for you.",
                "Normal is boring. Dumbed down is hand-holding. Vulgar is *chef's kiss*.",
                "Change how mouthy the tooltips are. You picked the spicy option.",
            ],
            'theme_selector': [
                "Pick a vibe. Dark mode or boomer mode.",
                "Choose your aesthetic. Make it pretty. Or ugly. Your call.",
                "Theme picker. Dark mode supremacy or die trying.",
                "Color scheme selector. Make it match your personality disorder.",
                "Pick colors. We won't judge. Much.",
            ],
            # Sound settings tooltips
            'sound_enabled': [
                "Mute everything. Enjoy the silence, you hermit.",
                "Sound toggle. On or off. Binary. Like your social skills.",
                "Kill all sounds. Peace and quiet at last.",
                "Enable sounds or pretend you're in a library. Your call.",
                "Toggle audio. Because not everyone appreciates art.",
            ],
            'master_volume': [
                "Master volume. Crank it up or shut it down.",
                "The big volume knob. Turn it up to 11 if you're brave.",
                "Overall loudness control. Your neighbors might care.",
                "Volume slider. Slide to the right for chaos, left for stealth mode.",
                "How loud do you want this sh*t? Slide and find out.",
            ],
            'effects_volume': [
                "Effects volume. Make the clicks louder or stfu.",
                "Sound effects loudness. For those satisfying click sounds.",
                "Turn up the effects or turn them down. Nobody's watching.",
                "Effects volume slider. Customize your auditory experience. Fancy.",
                "How loud should the bleep-bloops be? You decide.",
            ],
            'notifications_volume': [
                "Notification volume. Ding ding or nothing. Pick one.",
                "How loud do you want to be bothered? Slide accordingly.",
                "Notification sounds. Adjust before your coworkers complain.",
                "Alert volume. From 'barely a whisper' to 'everyone heard that'.",
                "Notification loudness. Subtle or obnoxious. Both valid.",
            ],
            'sound_pack': [
                "Sound packs. Default is boring, vulgar is... interesting.",
                "Choose your audio aesthetic. Classy or trashy.",
                "Pick a sound theme. Each one has its own personality. Like you.",
                "Sound pack selector. Default, minimal, or WTF mode.",
                "Audio vibes. Pick the one that matches your energy.",
            ],
            'per_event_sound': [
                "Micromanage your sounds. Mute what annoys you.",
                "Individual sound toggles for control freaks.",
                "Pick and choose which sounds you tolerate. Fair enough.",
                "Per-event audio control. Because one size doesn't fit all.",
                "Cherry-pick your sounds like the picky bastard you are.",
            ],
            'sound_test_button': [
                "Test the sound. Preview before you commit. Smart.",
                "Click to hear a preview. Try before you buy... wait, it's free.",
                "Sound test. Because surprises aren't always fun.",
                "Preview this noise. Your eardrums will thank you. Or not.",
                "Hit test to hear what this sounds like. Science!",
            ],
            'sound_choice': [
                "Pick a sound style. Chime, beep, whatever tickles your fancy.",
                "Sound selector. Mix and match your audio nightmare.",
                "Choose your weapon. I mean sound. Same energy.",
                "What noise do you want for this event? Go wild.",
                "Sound picker. The DJ booth of settings panels.",
            ],
            # Cursor settings tooltips
            'cursor_type': [
                "Cursor style. Default is boring. Live a little.",
                "Change your cursor. Skull cursor? Hell yeah.",
                "Pointer picker. Because the default arrow is basic AF.",
                "Cursor options. From professional to 'what is that?'",
                "Pick a cursor. Crosshair makes you feel like a pro gamer.",
            ],
            'cursor_size': [
                "Cursor size. Compensating for something? Go huge.",
                "Make your cursor tiny or massive. No judgment.",
                "Size matters. At least for cursors. Pick your preference.",
                "Cursor size slider. From 'where the hell is it' to 'can't miss it'.",
                "Resize your pointer. Because accessibility is important, damn it.",
            ],
            'cursor_tint': [
                "Color your cursor. Make it match your personality.",
                "Cursor tint. Paint that pointer whatever color you want.",
                "Hex color input. #FF0000 if you're feeling dangerous.",
                "Tint your cursor. Because plain white is so last year.",
                "Color picker for your cursor. Go full rainbow if you dare.",
            ],
            'cursor_trail': [
                "Cursor trail. Leave sparkles wherever you go. Majestic.",
                "Enable trails. Your cursor will look fabulous. Trust me.",
                "Sparkle trail toggle. For the extra in all of us.",
                "Cursor trail. Because your mouse movements deserve to be celebrated.",
                "Turn on trails and watch your productivity drop. Worth it.",
            ],
            'trail_style': [
                "Trail style. Rainbow? Fire? Galaxy? Go nuts.",
                "Pick a trail flavor. Each one is more extra than the last.",
                "Trail aesthetic picker. Match your energy level.",
                "Choose your sparkle style. No wrong answers here.",
                "Trail options. From 'subtle nature' to 'galactic overkill'.",
            ],
            # Hotkey settings tooltips
            'hotkey_edit': [
                "Edit this hotkey. Remap it to something useful. Or chaotic.",
                "Change the keybinding. Make it whatever the hell you want.",
                "Remap this shortcut. Ctrl+Alt+Delete? Go for it.",
                "Edit hotkey. Because the default key was stupid.",
                "Rebind this action. Your keyboard, your rules.",
            ],
            'hotkey_toggle': [
                "Enable or disable this shortcut. Some keys deserve a break.",
                "Toggle hotkey. On or off. Revolutionary, I know.",
                "Disable this shortcut if it keeps interrupting your flow.",
                "Turn this keybinding on or off. It's like a light switch but nerdier.",
                "Enable/disable toggle. For when shortcuts start sh*t.",
            ],
            'hotkey_reset': [
                "Reset all hotkeys to defaults. Panic button for keybinds.",
                "Factory reset your shortcuts. Undo all your 'improvements'.",
                "Reset everything. Start fresh. Embrace the defaults.",
                "Nuclear option for hotkeys. Resets EVERYTHING.",
                "Defaults button. For when your custom bindings are a disaster.",
            ],
        }
        
        # Merge tooltip variants from the inlined tooltip definitions
        try:
            for widget_id, tooltip_dict in _PANDA_TOOLTIPS.items():
                if 'vulgar' in tooltip_dict:
                    base_tooltips[widget_id] = tooltip_dict['vulgar']
        except Exception as e:
            logger.warning(f"Error loading vulgar tooltips: {e}")
        
        return base_tooltips


class WidgetTooltip:
    """Simple hover tooltip for widgets.
    
    When ``widget_id`` and ``tooltip_manager`` are provided, the displayed
    text is resolved dynamically each time the tooltip is shown so that
    tooltip-mode changes take effect immediately without a restart.
    """
    
    def __init__(self, widget, text, delay=500, widget_id=None, tooltip_manager=None):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self._after_id = None
        self._auto_hide_id = None
        # Dynamic tooltip support
        self.widget_id = widget_id
        self.tooltip_manager = tooltip_manager
        
        # Bind to the widget using add="+" to avoid overriding existing bindings
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        # Also hide on mouse motion outside widget as a safety measure
        widget.bind("<Motion>", self._on_motion, add="+")
        
        # Bind to internal components for CustomTkinter widgets
        # CTK widgets use internal canvas and label that receive mouse events
        for attr in ('_canvas', '_text_label', '_image_label'):
            try:
                child = getattr(widget, attr, None)
                if child is not None:
                    child.bind("<Enter>", self._on_enter, add="+")
                    child.bind("<Leave>", self._on_leave, add="+")
            except (AttributeError, tk.TclError):
                pass
    
    def _get_display_text(self):
        """Get the text to display, resolving dynamically if possible."""
        if self.widget_id and self.tooltip_manager:
            try:
                dynamic = self.tooltip_manager.get_tooltip(self.widget_id)
                if dynamic:
                    return dynamic
            except (AttributeError, KeyError, TypeError) as e:
                logger.debug(f"Dynamic tooltip resolution failed for {self.widget_id}: {e}")
        return self.text
    
    def _on_enter(self, event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
        self._after_id = self.widget.after(self.delay, self._show_tip)
    
    def _on_motion(self, event=None):
        """Track that mouse is still over the widget (no action needed,
        auto-hide timer set in _show_tip handles cleanup)."""
        pass
    
    def _on_leave(self, event=None):
        # Always cancel pending tooltip display
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        # Always hide the tooltip on leave - don't try to second-guess
        # whether the cursor is still inside. The _on_enter on child widgets
        # will re-trigger display if needed.
        self._hide_tip()
    
    def _show_tip(self):
        display_text = self._get_display_text()
        if not display_text:
            return
        
        # Check if widget is still visible and mapped
        try:
            if not self.widget.winfo_ismapped():
                return
        except Exception:
            return
            
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            
            # Use regular tkinter Toplevel for lighter-weight tooltip
            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tw.attributes('-topmost', True)
            
            # Create label with larger styling for better visibility
            label = tk.Label(tw, text=display_text, wraplength=400,
                           font=("Arial", 13),
                           bg="#2b2b2b",
                           fg="#ffffff",
                           relief="solid",
                           borderwidth=1,
                           padx=12, pady=8)
            label.pack()
            
            # Auto-hide tooltip after 5 seconds as a safety measure
            self._auto_hide_id = self.widget.after(5000, self._hide_tip)
        except Exception as e:
            # Log but don't crash
            logger.debug(f"Tooltip error: {e}")
    
    def _hide_tip(self):
        if self._auto_hide_id:
            try:
                self.widget.after_cancel(self._auto_hide_id)
            except Exception:
                pass
            self._auto_hide_id = None
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None
    
    def update_text(self, text):
        self.text = text


class ContextHelp:
    """Provides context-sensitive help with F1 key"""
    
    def __init__(self, master_window, config):
        self.master = master_window
        self.config = config
        self.help_window = None
        
        # Bind F1 key globally
        if GUI_AVAILABLE:
            self.master.bind('<F1>', self._show_context_help)
    
    def _show_context_help(self, event=None):
        """Show help based on current context"""
        if not GUI_AVAILABLE:
            return
            
        # Get current focused widget or active tab
        context = self._determine_context()
        
        # Create or update help window
        if self.help_window and self.help_window.winfo_exists():
            self._update_help_content(context)
            # Ensure existing help window is brought to front
            self._lift_help_window()
        else:
            self._create_help_window(context)
    
    def _determine_context(self) -> str:
        """Determine what context the user is currently in"""
        # Try to get the current tab
        try:
            focused = self.master.focus_get()
            if focused:
                # Analyze the widget hierarchy to determine context
                widget_name = str(focused)
                if 'sort' in widget_name.lower():
                    return 'sort'
                elif 'convert' in widget_name.lower():
                    return 'convert'
                elif 'browser' in widget_name.lower():
                    return 'browser'
                elif 'settings' in widget_name.lower():
                    return 'settings'
                elif 'notepad' in widget_name.lower():
                    return 'notepad'
        except Exception:
            pass
        
        return 'general'
    
    def _create_help_window(self, context: str):
        """Create the help window"""
        self.help_window = ctk.CTkToplevel(self.master)
        self.help_window.title("❓ Help & Documentation")
        self.help_window.geometry("700x600")
        
        # Bring window to front without forcing it to stay permanently on top
        self.help_window.after(100, lambda: self._lift_help_window())
        
        # Create content
        self._update_help_content(context)
    
    def _lift_help_window(self):
        """Ensure help window is visible above the main application"""
        try:
            if self.help_window and self.help_window.winfo_exists():
                self.help_window.lift()
                self.help_window.focus_force()
        except Exception:
            pass
    
    def _update_help_content(self, context: str):
        """Update help content based on context"""
        # Clear existing content
        for widget in self.help_window.winfo_children():
            widget.destroy()
        
        # Main frame
        main_frame = ctk.CTkFrame(self.help_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text=f"Help: {context.capitalize()}",
            font=("Arial Bold", 20)
        )
        title.pack(pady=(0, 20))
        
        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(main_frame)
        scroll_frame.pack(fill="both", expand=True)
        
        # Get help content for context
        help_text = self._get_help_text(context)
        
        help_label = ctk.CTkLabel(
            scroll_frame,
            text=help_text,
            font=("Arial", 12),
            wraplength=600,
            justify="left"
        )
        help_label.pack(pady=10, padx=10)
        
        # Quick links
        links_frame = ctk.CTkFrame(main_frame)
        links_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(
            links_frame,
            text="Quick Start",
            width=120,
            command=lambda: self._update_help_content('quickstart')
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            links_frame,
            text="FAQ",
            width=120,
            command=lambda: self._update_help_content('faq')
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            links_frame,
            text="Close",
            width=120,
            command=self.help_window.destroy
        ).pack(side="right", padx=5)
    
    def _get_help_text(self, context: str) -> str:
        """Get help text for a specific context"""
        help_texts = {
            'general': """
PS2 Texture Sorter - Quick Help

This application helps you organize and manage texture files from PS2 game dumps.

Key Features:
• Automatic texture classification with 50+ categories
• LOD (Level of Detail) detection and grouping
• Format conversion (DDS ↔ PNG ↔ JPG ↔ BMP ↔ TGA)
• Duplicate detection
• File browser with thumbnail previews
• Interactive panda companion (drag, toss, pet, feed!)
• Achievement system with Bamboo Bucks currency
• Customizable themes, cursors, and tooltips
• Undo/redo with 50-level history
• Pop-out tabs for multi-monitor setups

Press F1 anytime for context-sensitive help based on what you're doing.

Need more help? Check the Quick Start guide or FAQ!
            """,
            'sort': """
Sorting Textures

1. Select Input Directory: Choose the folder with your unsorted textures
2. Select Output Directory: Choose where to save organized textures
3. Choose Organization Style: By Category, By Size, Flat, or Hierarchical
4. Enable Options: LOD Detection, Group LODs, Detect Duplicates
5. Click "Start Sorting" to begin!

The app will:
• Scan all texture files
• Classify them by type (UI, Character, Environment, etc.)
• Organize them into folders
• Show progress in real-time

Tip: The default "By Category" style works great for most projects!
            """,
            'convert': """
Converting Texture Formats

This feature allows you to batch convert texture files between formats.

Supported Formats:
• DDS (DirectDraw Surface)
• PNG (Portable Network Graphics)
• JPG/JPEG (Joint Photographic Experts Group)
• BMP (Bitmap)
• TGA (Targa)

How to Use:
1. Select input folder with textures to convert
2. Choose output folder for converted files
3. Select source and target formats
4. Configure quality settings if needed
5. Click "Start Conversion"

Tip: DDS is commonly used in games, PNG is great for editing!
            """,
            'quickstart': """
Quick Start Guide

Step 1: Prepare Your Files
• Gather all texture files in one folder
• Supported formats: DDS, PNG, JPG, BMP, TGA

Step 2: Sort Your Textures
• Open the "Sort Textures" tab
• Select input directory (where your textures are)
• Select output directory (where to save organized files)
• Choose organization style
• Click "Start Sorting"

Step 3: Review Results
• Check the output folder for organized textures
• Review the log for any issues
• Browse sorted textures in the File Browser tab

Tips:
• Enable LOD Detection for better organization
• Use Detect Duplicates to save space
• Check Achievements for fun challenges!
            """,
            'faq': """
Frequently Asked Questions

Q: What texture formats are supported?
A: DDS, PNG, JPG/JPEG, BMP, and TGA formats are fully supported.

Q: Will my original files be modified?
A: No! Files are copied to the output directory. Originals remain unchanged. You can enable automatic backups in Settings for extra safety.

Q: What is LOD Detection?
A: LOD (Level of Detail) detection finds different quality versions of the same texture (LOD0, LOD1, LOD2, etc.) and can group them together.

Q: Can I undo sorting operations?
A: Yes! The app supports undo/redo with configurable history depth (default 50 operations). Check Settings -> File Handling.

Q: What is the Panda Character?
A: An interactive companion that reacts to your actions! The panda has 13 moods, levels up, provides helpful tips, and makes sorting fun. Click, hover, drag, toss, pet, or right-click the panda to interact! You can throw it and watch it bounce off walls.

Q: Can I toss the panda?
A: Yes! Drag the panda and release with some speed. It will bounce off walls and the floor with physics, playing different animations as it goes.

Q: How do I change tooltip modes?
A: Go to Settings -> UI & Appearance and change the tooltip mode. Changes take effect immediately - no restart needed. Choose Normal, Beginner, or Vulgar.

Q: How do keyboard shortcuts work?
A: Press F1 for help, Ctrl+P to start processing, Ctrl+S to save, and more. Check the About tab for a complete list of shortcuts.

Q: How do I customize the UI theme?
A: Click Settings button -> UI & Appearance to change colors, cursors, themes, and tooltip verbosity. Open Advanced Customization for full control over colors, cursors, and sounds.

Q: How do I see thumbnails in the File Browser?
A: Check the "Thumbnails" checkbox in the File Browser tab header. You can also adjust thumbnail size in Settings -> Performance.

Q: Can I pop out tabs into separate windows?
A: Yes! Click the pop-out button on any secondary tab to open it in its own window. Click "Dock Back" or close the window to return it.

Q: The app is slow with many files. What can I do?
A: Settings -> Performance: Increase thread count (use number of CPU cores), increase memory limit, and enable database indexing.

Q: What are Bamboo Bucks?
A: In-app currency earned through usage, achievements, and interactions. Spend it in the Shop tab on themes, customizations, and unlockables!

Q: How do I earn achievements?
A: Process files, explore features, interact with the panda, and discover Easter eggs! Check the Achievements tab to see all available achievements.

Q: Does this require internet?
A: No! PS2 Texture Sorter is 100% offline. No network calls, complete privacy.

Q: Where are my settings and data stored?
A: In your user profile folder: ~/.ps2_texture_sorter/ (or %USERPROFILE%\\.ps2_texture_sorter\\ on Windows)

Q: Can I dress up the panda?
A: Yes! Unlock outfits, hats, shoes, and accessories through achievements and the shop, then customize your panda in the Closet tab.
            """
        }
        
        return help_texts.get(context, help_texts['general'])
    
    def open_help_panel(self):
        """Open the main help panel"""
        self._show_context_help()


# Convenience function for easy integration
def setup_tutorial_system(master_window, config):
    """
    Setup and initialize the tutorial system with resilient error handling.
    Each component is initialized independently, so if one fails, others can still work.
    
    Returns:
        tuple[Optional[TutorialManager], Optional[TooltipVerbosityManager], Optional[ContextHelp]]:
            A tuple of (manager, tooltip_manager, context_help) where None indicates failure.
    """
    manager = None
    tooltip_manager = None
    context_help = None
    
    # Try to initialize TutorialManager
    try:
        manager = TutorialManager(master_window, config)
        logger.info("TutorialManager initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize TutorialManager: {e}", exc_info=True)
    
    # Try to initialize TooltipVerbosityManager independently
    try:
        tooltip_manager = TooltipVerbosityManager(config)
        logger.info("TooltipVerbosityManager initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize TooltipVerbosityManager: {e}", exc_info=True)
    
    # Try to initialize ContextHelp independently
    try:
        context_help = ContextHelp(master_window, config)
        logger.info("ContextHelp initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize ContextHelp: {e}", exc_info=True)
    
    # Return what we successfully initialized (None for failed components)
    return manager, tooltip_manager, context_help