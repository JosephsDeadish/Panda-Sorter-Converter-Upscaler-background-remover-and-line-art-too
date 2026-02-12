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
    # Closet subcategory tooltips
    'closet_all_clothing': {
        'normal': [
            "Browse all owned clothing items",
            "View every clothing item in your collection",
            "See shirts, pants, jackets, and more — all in one view",
        ],
        'vulgar': [
            "Every piece of clothing. Fashion overload incoming.",
            "All the clothes. Browse 'em all, you fashionista.",
            "Your panda's entire wardrobe in one scrollable nightmare.",
            "All clothing. Because subcategories are for quitters.",
        ]
    },
    'closet_shirts': {
        'normal': [
            "Browse shirts and tops for your panda",
            "View your collection of tops and tees",
            "Shirts that fit perfectly on your panda's torso",
        ],
        'vulgar': [
            "Shirts. The torso region. Chest coverage.",
            "Tops and tees. Basic but essential bear fashion.",
            "Shirt shopping for a panda. What a world.",
            "Browse tops. Your panda's chest needs some love.",
        ]
    },
    'closet_pants': {
        'normal': [
            "Browse pants and bottoms for your panda",
            "View your collection of pants and trousers",
            "Pants that follow your panda's leg movements",
        ],
        'vulgar': [
            "Pants! Give your panda some dignity.",
            "Leg coverings. Because naked panda legs are weird.",
            "Trousers that move with the bear's legs. Science!",
            "Pants shopping. Your panda's been exposed long enough.",
        ]
    },
    'closet_jackets': {
        'normal': [
            "Browse jackets, hoodies, and coats",
            "View your collection of outerwear",
            "Jackets with sleeves that move with arm animations",
        ],
        'vulgar': [
            "Jackets. Because pandas get cold. Probably.",
            "Outerwear for your bear. Hoodies, coats, the works.",
            "Layer up! Sleeves move with the arms. Fancy, right?",
            "Jacket section. Cool panda vibes incoming.",
        ]
    },
    'closet_dresses': {
        'normal': [
            "Browse dresses, robes, and gowns",
            "View your collection of dresses and robes",
            "Elegant garments that flow from neck to below the body",
        ],
        'vulgar': [
            "Dresses and robes. Fancy bear time!",
            "Flowing garments for the classy panda.",
            "Dress-up time. Your panda is red-carpet ready.",
            "Gowns and robes. Panda couture at its finest.",
        ]
    },
    'closet_full_outfits': {
        'normal': [
            "Browse full-body outfits and costumes",
            "View complete outfit sets that cover the entire body",
            "Full costumes with torso, legs, and sleeve coverage",
        ],
        'vulgar': [
            "Full body costumes. Total panda transformation.",
            "Complete outfits. One-stop shopping for bear fashion.",
            "Full suit mode. Torso, legs, sleeves — the whole deal.",
            "Costume shop. Your panda becomes someone else entirely.",
        ]
    },
    # UI settings tooltips
    'ui_language': {
        'normal': [
            "Choose the display language for the application",
            "Switch between available language translations",
            "Set your preferred interface language",
        ],
        'vulgar': [
            "Language picker. Sprechen sie panda?",
            "Change language. Won't fix your grammar though.",
            "International mode. Pick a language, any language.",
            "Language selector. For the worldly panda enthusiast.",
        ]
    },
    'ui_font_size': {
        'normal': [
            "Adjust the size of text throughout the application",
            "Make text larger or smaller for better readability",
            "Change the font size for all UI elements",
        ],
        'vulgar': [
            "Font size. For people who refuse to wear glasses.",
            "Make text bigger or smaller. We won't judge your eyes.",
            "Text size slider. From 'ant writing' to 'billboard'.",
            "Font size. Squint less, enjoy more.",
        ]
    },
    'ui_animations': {
        'normal': [
            "Enable or disable UI animations and transitions",
            "Toggle smooth animation effects in the interface",
            "Control whether the UI uses animated transitions",
        ],
        'vulgar': [
            "Toggle animations. Smooth or instant. Your call.",
            "UI animations on or off. Performance vs. pretty.",
            "Animation switch. For the impatient.",
            "Smooth transitions toggle. Fancy or fast?",
        ]
    },
    'ui_transparency': {
        'normal': [
            "Adjust the window transparency level",
            "Make the application window more or less transparent",
            "Control the opacity of the application window",
        ],
        'vulgar': [
            "Window transparency. See-through panda time.",
            "Opacity slider. From solid to ghost mode.",
            "Make the window transparent. Stealth sorting.",
            "Transparency control. X-ray vision for your desktop.",
        ]
    },
    'ui_compact_mode': {
        'normal': [
            "Switch to a compact layout with smaller panels",
            "Use a condensed view to save screen space",
            "Enable compact mode for a more efficient layout",
        ],
        'vulgar': [
            "Compact mode. Squeeze everything smaller.",
            "Small layout for tiny screens and big dreams.",
            "Compact view. More room for activities!",
            "Efficiency mode. Less padding, more action.",
        ]
    },
    'ui_auto_save': {
        'normal': [
            "Automatically save settings when changes are made",
            "Enable automatic saving of preferences",
            "Settings are saved without manual intervention",
        ],
        'vulgar': [
            "Auto-save. Because you'll forget to save. We know.",
            "Automatic saving. One less thing to worry about.",
            "Set it and forget it. Settings save themselves.",
            "Auto-save toggle. Manual saving is for cavemen.",
        ]
    },
    'ui_confirm_exit': {
        'normal': [
            "Ask for confirmation before closing the application",
            "Show a dialog when you try to exit the app",
            "Prevent accidental exits with a confirmation prompt",
        ],
        'vulgar': [
            "Exit confirmation. The app clings to you like a needy ex.",
            "'Are you sure?' dialog. For the indecisive among us.",
            "Prevent rage-quitting by accident. You're welcome.",
            "Exit safety net. Because misclicks are embarrassing.",
        ]
    },
    'ui_startup_tab': {
        'normal': [
            "Choose which tab opens when the app starts",
            "Set your preferred starting tab",
            "Select the default tab shown on application launch",
        ],
        'vulgar': [
            "Startup tab. Skip the intro, go straight to work.",
            "Pick which tab loads first. First impressions matter.",
            "Default tab selector. Speed-run your workflow.",
            "Launch tab. Because clicking twice is unacceptable.",
        ]
    },
    'panda_name': {
        'normal': [
            "Set a custom name for your panda companion",
            "Give your panda a personalized name",
            "Type a name for your panda — it appears in messages",
        ],
        'vulgar': [
            "Name your panda. 'Sir Chomps-a-Lot' is taken.",
            "Panda naming ceremony. Choose wisely. Or not.",
            "Type a name. Your bear deserves an identity.",
            "Name your virtual bear. This is peak entertainment.",
        ]
    },
    'panda_gender': {
        'normal': [
            "Choose your panda's gender identity",
            "Set the gender for your panda companion",
            "Select a gender — affects pronouns in speech bubbles",
        ],
        'vulgar': [
            "Panda gender. They/them is valid for bears too.",
            "Gender selection. Progressive pandas unite!",
            "Pick your bear's identity. We don't judge.",
            "Gender picker. It's 2024, even bears get to choose.",
        ]
    },
    'panda_auto_walk': {
        'normal': [
            "Enable or disable automatic panda walking",
            "Let your panda wander around on its own",
            "Toggle autonomous panda movement",
        ],
        'vulgar': [
            "Auto-walk. Your panda is a free spirit.",
            "Let the bear roam. Free-range panda mode.",
            "Walking toggle. Restless bear syndrome.",
            "Your panda walks on its own. Deal with it.",
        ]
    },
    'panda_speech_bubbles': {
        'normal': [
            "Show or hide speech bubbles above the panda",
            "Toggle text bubbles for panda commentary",
            "Enable speech bubbles for panda messages",
        ],
        'vulgar': [
            "Speech bubbles. Your panda never shuts up.",
            "Toggle commentary. The bear has opinions.",
            "Text bubbles on or off. Silence is golden.",
            "Show/hide the panda's hot takes.",
        ]
    },
    'panda_idle_animations': {
        'normal': [
            "Enable or disable idle animations",
            "Toggle small animations when the panda is idle",
            "Your panda stretches and yawns when not interacting",
        ],
        'vulgar': [
            "Idle animations. Your panda does cute stuff when bored.",
            "Watch your bear yawn and stretch. Riveting content.",
            "Idle mode animations. Because pandas need hobbies.",
            "Toggle idle animations. Less movement, less distraction.",
        ]
    },
    'panda_drag_enabled': {
        'normal': [
            "Allow dragging the panda around the screen",
            "Enable click-and-drag panda movement",
            "Toggle the ability to pick up and move your panda",
        ],
        'vulgar': [
            "Drag mode. Yeet the panda across the screen.",
            "Pick up and fling your bear. Totally ethical.",
            "Drag toggle. Grab, move, release. Repeat.",
            "Enable dragging. Your panda is now a cursor toy.",
        ]
    },
    'perf_thread_count': {
        'normal': [
            "Number of threads used for texture processing",
            "Control how many parallel threads are used",
            "Adjust thread count for processing performance",
        ],
        'vulgar': [
            "Thread count. More threads = faster. Maybe hotter CPU.",
            "How many threads to throw at the problem.",
            "Processing threads. Don't go nuclear.",
            "Thread slider. Your CPU's workout intensity.",
        ]
    },
    'perf_cache_size': {
        'normal': [
            "Maximum memory used for caching processed textures",
            "Larger cache means faster repeated operations",
            "Control memory allocation for texture caching",
        ],
        'vulgar': [
            "Cache size. Feed the RAM monster.",
            "Memory cache slider. More RAM, more speed, more heat.",
            "Cache allocation. Greedy or conservative. Pick one.",
            "How much memory to hoard. Digital dragon vibes.",
        ]
    },
    'profile_save': {
        'normal': [
            "Save your current settings as a profile",
            "Create a named settings snapshot",
            "Store your configuration for later use",
        ],
        'vulgar': [
            "Save profile. Insurance against future stupidity.",
            "Create a settings backup. You'll need it.",
            "Save now. You know you'll mess something up later.",
            "Profile snapshot. Future you will thank present you.",
        ]
    },
    'profile_load': {
        'normal': [
            "Load a previously saved settings profile",
            "Restore settings from a saved profile",
            "Switch to a different saved configuration",
        ],
        'vulgar': [
            "Load profile. Time travel for settings.",
            "Restore a saved config. Undo your disasters.",
            "Load a profile. Instant settings swap!",
            "Switch configs. For the indecisive.",
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
                title="Welcome to Game Texture Sorter! 🐼",
                message=(
                    "Welcome! This quick tutorial will show you how to use the application.\n\n"
                    "Game Texture Sorter helps you organize and manage texture files from "
                    "game texture dumps with intelligent classification and LOD detection.\n\n"
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
            'sort_button': [
                "Click to sort your textures into organized folders",
                "Start the sorting process to categorize your texture files",
                "Organize your texture dump into neat, labeled folders",
                "Run the texture sorter on the selected input directory",
                "Begin sorting textures by type, use-case, and category",
            ],
            'convert_button': [
                "Convert textures to different formats",
                "Transform texture files between supported image formats",
                "Batch convert your textures (e.g., DDS to PNG)",
                "Change the file format of selected textures",
                "Convert textures for compatibility with other tools",
            ],
            'input_browse': [
                "Browse for the folder containing your texture files",
                "Select the source directory where your raw textures are stored",
                "Pick the input folder to read textures from",
                "Choose a directory of textures to process",
                "Open a folder picker to set the input path",
            ],
            'output_browse': [
                "Choose where to save the organized textures",
                "Select the destination folder for sorted output",
                "Pick an output directory for your processed textures",
                "Set the folder where sorted textures will be written",
                "Browse for a location to store the results",
            ],
            'detect_lods': [
                "Automatically detect and group LOD levels (Level of Detail)",
                "Identify LOD variants so they can be grouped together",
                "Scan textures for LOD suffixes and resolution patterns",
                "Enable detection of Level of Detail texture variants",
                "Find LOD chains across your texture files automatically",
            ],
            'group_lods': [
                "Keep LOD variants together in the same folder",
                "Group Level of Detail textures into shared directories",
                "Ensure LOD levels stay organized alongside their base textures",
                "Place all LOD variants of a texture in one folder",
                "Maintain LOD grouping during the sorting process",
            ],
            'detect_duplicates': [
                "Find and handle duplicate texture files",
                "Scan for duplicate textures based on content hashing",
                "Identify identical textures even if file names differ",
                "Detect duplicates to avoid redundant copies in the output",
                "Check for repeated texture data across your input files",
            ],
            'style_dropdown': [
                "Choose how to organize your textures",
                "Select an organizational style for the sorting output",
                "Pick a folder structure template for sorted textures",
                "Decide how textures are grouped in the output directory",
                "Change the sorting strategy used for file organization",
            ],
            'settings_button': [
                "Open settings and preferences",
                "Configure application options and preferences",
                "Access the settings panel to customize behavior",
                "Adjust application settings to suit your workflow",
                "Open the preferences dialog for fine-tuning",
            ],
            'theme_button': [
                "Switch between dark and light themes",
                "Toggle the application's visual theme",
                "Change the color scheme of the interface",
                "Cycle through available appearance themes",
                "Switch to a different look and feel for the UI",
            ],
            'help_button': [
                "Get help and documentation",
                "Open the help guide and reference documentation",
                "Access tutorials and usage instructions",
                "View helpful tips and feature explanations",
                "Find answers to common questions about the application",
            ],
            'achievements_tab': [
                "View your achievements and progress milestones",
                "Check which achievements you have unlocked",
                "See your accomplishments and remaining goals",
                "Browse the full list of available achievements",
                "Track your milestone progress and claim rewards",
            ],
            'shop_tab': [
                "Opens the reward store where earned points can be spent",
                "Browse the shop to purchase items with Bamboo Bucks",
                "Visit the store to spend your earned currency",
                "Shop for outfits, accessories, and upgrades",
                "Explore purchasable items and cosmetics",
            ],
            'shop_buy_button': [
                "Purchase this item with your currency",
                "Buy this item using your Bamboo Bucks balance",
                "Complete the purchase of the selected item",
                "Spend currency to add this item to your inventory",
                "Confirm your purchase and receive the item",
            ],
            'shop_category_button': [
                "Filter shop items by this category",
                "Show only items belonging to this category",
                "Narrow the shop view to this item type",
                "Browse shop items within this specific category",
                "Select this category to filter displayed products",
            ],
            'rewards_tab': [
                "View all unlockable rewards and their requirements",
                "See which rewards are available and how to earn them",
                "Browse the rewards catalog and unlock conditions",
                "Check what you can unlock through achievements and progress",
                "Explore all earnable rewards and their criteria",
            ],
            'closet_tab': [
                "Customize your panda's appearance with outfits and accessories",
                "Dress up your panda using items from your inventory",
                "Equip clothing and accessories on your panda",
                "Open the closet to change your panda's look",
                "Mix and match outfits for your panda companion",
            ],
            'browser_browse_button': [
                "Select a directory to browse for texture files",
                "Open a folder picker to choose a browsing directory",
                "Pick a folder to view its texture contents",
                "Choose a directory to explore its files",
                "Browse your file system for a texture folder",
            ],
            'browser_refresh_button': [
                "Refresh the file list to show current directory contents",
                "Reload the directory listing to reflect recent changes",
                "Update the file browser with the latest folder contents",
                "Re-scan the current directory for new or removed files",
                "Refresh to see any files added since the last scan",
            ],
            'browser_search': [
                "Search for files by name in the current directory",
                "Filter the file list using a search query",
                "Type to find specific files in the current folder",
                "Quickly locate files by entering part of their name",
                "Use search to narrow down the displayed file list",
            ],
            'browser_show_all': [
                "Toggle between showing only textures or all file types",
                "Switch between texture-only and all-file display modes",
                "Show every file type or limit the view to textures",
                "Filter the browser to display all files or just textures",
                "Control whether non-texture files are visible in the list",
            ],
            # Tab tooltips
            'sort_tab': [
                "Sort and organize game texture dumps into categories",
                "Open the sorting tool to categorize texture files",
                "Use this tab to sort textures into structured folders",
                "Access the texture sorting and organization features",
                "Navigate to the tab for sorting game texture dumps",
            ],
            'convert_tab': [
                "Batch convert texture files between formats (DDS, PNG, JPG, etc.)",
                "Open the conversion tool for changing texture file formats",
                "Use this tab to convert textures to different image formats",
                "Access batch conversion for textures across supported formats",
                "Navigate to the format conversion tab",
            ],
            'browser_tab': [
                "Browse and preview texture files in a directory",
                "Open the file browser to explore and preview textures",
                "Use this tab to navigate folders and view texture thumbnails",
                "Access the texture browser for visual file exploration",
                "Navigate to the directory browsing and preview tab",
            ],
            'notepad_tab': [
                "Jot down notes and project information",
                "Open the notepad to record project notes and reminders",
                "Use this tab to keep text notes alongside your work",
                "Write and save notes related to your texture projects",
                "Access the built-in notepad for quick note-taking",
            ],
            'about_tab': [
                "View application info, credits, and keyboard shortcuts",
                "See version information and application credits",
                "Check the about page for app details and shortcuts",
                "Open the about section for credits and version info",
                "View build information and developer acknowledgments",
            ],
            # Category tooltips
            'tools_category': [
                "Access sorting, conversion, and file browsing tools",
                "Navigate to the tools section for texture processing",
                "Open the tools category with sorting and conversion features",
                "Find texture sorting, format conversion, and browser tools here",
                "Switch to the tools category for core functionality",
            ],
            'features_category': [
                "Interact with your panda, shop, achievements, and more",
                "Explore fun features like the panda companion and rewards",
                "Access the features section for panda, shop, and achievements",
                "Navigate to interactive features beyond texture processing",
                "Switch to the features category for panda and reward content",
            ],
            # Feature tab tooltips
            'inventory_tab': [
                "View and use your collected toys and food items",
                "Open your inventory to see all owned items",
                "Check your collection of toys, food, and accessories",
                "Browse items you have purchased or earned",
                "Access your inventory to manage and use items",
            ],
            'panda_stats_tab': [
                "Check your panda's mood, stats, and interaction history",
                "View detailed statistics about your panda companion",
                "See your panda's happiness, hunger, and activity log",
                "Open the stats panel for your panda's current state",
                "Monitor your panda's well-being and interaction metrics",
            ],
            'minigames_tab': [
                "Play mini-games to earn rewards and have fun",
                "Access available mini-games for extra rewards",
                "Open the mini-games section to play and earn currency",
                "Choose from a selection of mini-games to enjoy",
                "Play games to earn Bamboo Bucks and boost your panda's mood",
            ],
            # Settings tooltips
            'keyboard_controls': [
                "View and customize keyboard shortcuts",
                "See all available hotkeys and reassign them",
                "Open the keyboard shortcut configuration panel",
                "Manage keyboard bindings for quick actions",
                "Customize key bindings to match your preferred workflow",
            ],
            'tooltip_mode': [
                "Choose how tooltips are displayed: normal, beginner, or vulgar",
                "Switch the tooltip style between available verbosity modes",
                "Select the tone and detail level of tooltip messages",
                "Change tooltip verbosity to match your preference",
                "Pick a tooltip mode that suits your experience level",
            ],
            'theme_selector': [
                "Choose a visual theme for the application",
                "Select from available themes to change the app appearance",
                "Switch the color scheme and visual style of the interface",
                "Pick a theme that matches your aesthetic preference",
                "Browse and apply different visual themes",
            ],
            # Sound settings tooltips
            'sound_enabled': [
                "Enable or disable all sound effects",
                "Toggle sound on or off globally",
                "Control whether the application plays any audio",
                "Mute or unmute all application sounds",
                "Turn all sound effects on or off",
            ],
            'master_volume': [
                "Adjust the overall volume level for all sounds",
                "Set the master volume that controls all audio output",
                "Raise or lower the global volume level",
                "Control the overall loudness of all sound effects",
                "Fine-tune the master audio level",
            ],
            'effects_volume': [
                "Control the volume of sound effects",
                "Adjust how loud UI and interaction sound effects are",
                "Set the volume level for action-triggered sounds",
                "Raise or lower the sound effects volume independently",
                "Fine-tune the loudness of in-app sound effects",
            ],
            'notifications_volume': [
                "Control the volume of notification sounds",
                "Adjust how loud notification alerts are",
                "Set the volume for achievement and alert notifications",
                "Raise or lower notification sound levels",
                "Fine-tune the loudness of notification audio cues",
            ],
            'sound_pack': [
                "Choose a sound pack style for audio feedback",
                "Select from different sound packs to change audio style",
                "Switch the set of sounds used throughout the app",
                "Pick a sound theme that matches your preference",
                "Change the audio feedback style with a different pack",
            ],
            'per_event_sound': [
                "Toggle individual sounds on or off for specific events",
                "Enable or disable sounds for each event separately",
                "Control which events trigger audio feedback",
                "Customize sound playback on a per-event basis",
                "Fine-tune which actions produce sound effects",
            ],
            'sound_test_button': [
                "Play a preview of this event's sound",
                "Test the sound assigned to this event",
                "Listen to a sample of the selected sound effect",
                "Preview how this event will sound when triggered",
                "Click to hear the current sound for this event",
            ],
            'sound_choice': [
                "Choose which sound to play for this event",
                "Select a specific sound effect for this event",
                "Pick the audio clip that plays when this event fires",
                "Assign a different sound to this event trigger",
                "Browse available sounds for this particular event",
            ],
            # Cursor settings tooltips
            'cursor_type': [
                "Select the style of your mouse cursor",
                "Choose a custom cursor design for the application",
                "Pick from available cursor styles",
                "Change the appearance of your mouse pointer",
                "Switch to a different cursor look and feel",
            ],
            'cursor_size': [
                "Change the size of your mouse cursor",
                "Make the cursor larger or smaller",
                "Adjust cursor dimensions to your preference",
                "Scale the custom cursor up or down",
                "Set a comfortable cursor size for your display",
            ],
            'cursor_tint': [
                "Set a color tint for your cursor",
                "Apply a custom color overlay to your cursor",
                "Tint the cursor to match your theme or preference",
                "Choose a color to apply to the cursor graphic",
                "Adjust the hue of your custom cursor",
            ],
            'cursor_trail': [
                "Enable or disable cursor trail effects",
                "Toggle the visual trail that follows your cursor",
                "Turn cursor trail particles on or off",
                "Control whether a trail appears behind your cursor",
                "Activate or deactivate the cursor trail effect",
            ],
            'trail_style': [
                "Choose the visual style for your cursor trail",
                "Select a trail effect from the available styles",
                "Pick how the cursor trail looks as it follows your mouse",
                "Change the particle or visual style of the trail",
                "Switch between different cursor trail animations",
            ],
            # Hotkey settings tooltips
            'hotkey_edit': [
                "Click to change the key binding for this shortcut",
                "Reassign the keyboard shortcut for this action",
                "Press to record a new key combination for this hotkey",
                "Edit the key binding associated with this command",
                "Click and then press your desired key combination",
            ],
            'hotkey_toggle': [
                "Enable or disable this keyboard shortcut",
                "Turn this hotkey on or off without removing the binding",
                "Toggle whether this shortcut is active",
                "Control if this key binding responds to input",
                "Activate or deactivate this particular shortcut",
            ],
            'hotkey_reset': [
                "Reset all keyboard shortcuts to their defaults",
                "Restore the original key bindings for every shortcut",
                "Revert all hotkeys back to factory defaults",
                "Clear custom bindings and reset to default shortcuts",
                "Undo all hotkey customizations at once",
            ],
            # Inventory tooltips
            'inventory_purchased': [
                "Items purchased from the shop",
                "View the items you have bought with Bamboo Bucks",
                "Browse your purchased item collection",
                "See everything you have acquired from the store",
                "Check your shop purchase history and owned items",
            ],
            'inventory_give_button': [
                "Give this item to your panda for interaction",
                "Hand the selected item to your panda companion",
                "Use this item by giving it to your panda",
                "Offer this item to your panda to see their reaction",
                "Let your panda interact with this item",
            ],
            'inventory_toy': [
                "Your toy collection — use toys to play with your panda",
                "Browse toys you own and give them to your panda",
                "View your toy inventory for panda play sessions",
                "Select a toy to entertain your panda companion",
                "Check your available toys for panda interaction",
            ],
            'inventory_food': [
                "Your food collection — feed your panda to increase happiness",
                "Browse food items available to feed your panda",
                "View your food inventory and nourish your panda",
                "Select a food item to boost your panda's mood",
                "Check your available food items for your panda",
            ],
            'inventory_accessory': [
                "Your accessory collection — equip via the closet",
                "Browse accessories you own for your panda",
                "View your accessory inventory and equip items in the closet",
                "Check available accessories to dress up your panda",
                "See all accessories ready to be equipped on your panda",
            ],
            'inventory_unlocked': [
                "Summary of rewards you have unlocked so far",
                "View a breakdown of all unlocked reward items",
                "See how many rewards you have collected in total",
                "Check your reward unlock progress at a glance",
                "Browse the list of rewards you have earned",
            ],
            # Closet tooltips
            'closet_header': [
                "Dress up your panda with outfits and accessories you own",
                "Customize your panda's look using your wardrobe",
                "Manage your panda's clothing and equipped items here",
                "Open the closet to style your panda companion",
                "Equip outfits and accessories from your collection",
            ],
            'closet_equip': [
                "Equip this item on your panda",
                "Put this clothing or accessory on your panda",
                "Dress your panda with this item",
                "Apply this item to your panda's outfit",
                "Add this item to your panda's current look",
            ],
            'closet_unequip': [
                "Remove this item from your panda",
                "Take this clothing or accessory off your panda",
                "Undress this item from your panda's outfit",
                "Unequip this item and return it to your inventory",
                "Remove this piece from your panda's current look",
            ],
            'closet_appearance': [
                "Your panda's current outfit summary",
                "See what your panda is currently wearing",
                "View the full list of equipped items on your panda",
                "Check your panda's current clothing and accessories",
                "Overview of your panda's active outfit selections",
            ],
            # Closet subcategory tooltips
            'closet_all_clothing': [
                "Browse all owned clothing items",
                "View your complete clothing collection in one list",
                "See every piece of clothing available to equip",
                "Show all categories of clothing at once",
                "Display your full wardrobe of clothing items",
            ],
            'closet_shirts': [
                "Browse shirts and tops for your panda",
                "View available shirts to equip on your panda",
                "Pick a shirt or top for your panda to wear",
                "See your collection of upper-body clothing",
                "Choose from your selection of panda shirts",
            ],
            'closet_pants': [
                "Browse pants and bottoms for your panda",
                "View available pants to equip on your panda",
                "Pick pants or shorts for your panda to wear",
                "See your collection of lower-body clothing",
                "Choose from your selection of panda bottoms",
            ],
            'closet_jackets': [
                "Browse jackets, hoodies, and coats",
                "View available outerwear for your panda",
                "Pick a jacket or hoodie for your panda to wear",
                "See your collection of coats and layered tops",
                "Choose from your panda's outerwear options",
            ],
            'closet_dresses': [
                "Browse dresses, robes, and gowns",
                "View available dresses to equip on your panda",
                "Pick a dress or robe for your panda to wear",
                "See your collection of full-length garments",
                "Choose from your panda's dress options",
            ],
            'closet_full_outfits': [
                "Browse full-body outfits and costumes",
                "View complete outfit sets for your panda",
                "Pick a full costume to dress your panda in",
                "See your collection of head-to-toe outfits",
                "Choose from full-body costumes and themed sets",
            ],
            'closet_fur_style': [
                "Change your panda's fur pattern and style",
                "Select a fur pattern for your panda's coat",
                "Switch between available fur styles and markings",
                "Customize the look of your panda's fur",
                "Pick a unique fur pattern for your companion",
            ],
            'closet_fur_color': [
                "Pick a fur color for your panda",
                "Choose a custom color for your panda's fur",
                "Change your panda's fur to a different color",
                "Select from available fur color options",
                "Set a new fur color for your panda companion",
            ],
            'closet_hats': [
                "Try on hats — equip or unequip from here",
                "Browse hats and headwear for your panda",
                "Pick a hat to put on your panda's head",
                "View your collection of hats and helmets",
                "Choose headwear from your panda's wardrobe",
            ],
            'closet_shoes': [
                "Choose shoes for your panda to wear",
                "Browse footwear options for your panda",
                "Pick boots, sneakers, or sandals for your panda",
                "View your collection of panda shoes",
                "Select footwear from your panda's closet",
            ],
            'closet_accessories': [
                "Accessorize your panda with fun items",
                "Browse accessories to add flair to your panda",
                "Pick an accessory for your panda to wear",
                "View your collection of panda accessories",
                "Choose from watches, glasses, scarves, and more",
            ],
            # Achievement tooltips
            'achievement_claim': [
                "Claim the reward for this completed achievement",
                "Collect your reward from this finished achievement",
                "Press to receive the prize for this achievement",
                "Redeem the reward earned by completing this goal",
                "Claim your well-earned achievement reward now",
            ],
            'achievement_claim_all': [
                "Claim all available achievement rewards at once",
                "Collect every pending achievement reward in one click",
                "Redeem all completed achievement prizes simultaneously",
                "Batch-claim all the rewards you have earned so far",
                "Press to receive all unclaimed achievement rewards",
            ],
            'achievement_progress': [
                "Track your progress toward completing this achievement",
                "See how close you are to finishing this achievement",
                "View the completion percentage for this goal",
                "Check how much remains before this achievement unlocks",
                "Monitor your advancement toward this milestone",
            ],
            # Shop-specific tooltips
            'shop_price': [
                "The cost in Bamboo Bucks to purchase this item",
                "Shows how many Bamboo Bucks this item costs",
                "The price you need to pay for this shop item",
                "Amount of currency required to buy this item",
                "Displays the Bamboo Bucks price tag for this item",
            ],
            'shop_level_req': [
                "The user level required to unlock this item for purchase",
                "Shows the minimum level needed to buy this item",
                "You must reach this level before purchasing",
                "Indicates the level requirement for this shop item",
                "Displays the level you need to access this product",
            ],
            'shop_item_name': [
                "Click for more details about this item",
                "Select this item to view its full description",
                "Tap to see additional information about this product",
                "View details, preview, and purchase options for this item",
                "Click to expand the item details panel",
            ],
            'shop_outfits_cat': [
                "Browse panda outfits available for purchase",
                "View full-body outfits and costumes in the shop",
                "Shop for complete outfit sets for your panda",
                "Explore purchasable outfits to dress your panda",
                "See all available outfit options for sale",
            ],
            'shop_clothes_cat': [
                "Browse clothing items available for purchase",
                "View individual clothing pieces in the shop",
                "Shop for shirts, pants, and other apparel",
                "Explore purchasable clothing for your panda",
                "See all available clothing items for sale",
            ],
            'shop_hats_cat': [
                "Browse hats, helmets, and headwear for purchase",
                "View available hats and headgear in the shop",
                "Shop for headwear to accessorize your panda",
                "Explore purchasable hats and helmets",
                "See all available headwear options for sale",
            ],
            'shop_shoes_cat': [
                "Browse shoes, boots, and footwear for purchase",
                "View available footwear options in the shop",
                "Shop for shoes and boots for your panda",
                "Explore purchasable footwear items",
                "See all available shoe options for sale",
            ],
            'shop_accessories_cat': [
                "Browse accessories like watches, bracelets, and ties",
                "View available accessories in the shop",
                "Shop for accessories to personalize your panda",
                "Explore purchasable accessory items",
                "See all available accessories for sale",
            ],
            'shop_cursors_cat': [
                "Browse custom cursors available for purchase",
                "View cursor styles available in the shop",
                "Shop for unique cursor designs",
                "Explore purchasable cursor appearances",
                "See all available custom cursors for sale",
            ],
            'shop_cursor_trails_cat': [
                "Browse cursor trail effects for purchase",
                "View cursor trail styles available in the shop",
                "Shop for trail effects that follow your cursor",
                "Explore purchasable cursor trail animations",
                "See all available trail effects for sale",
            ],
            'shop_themes_cat': [
                "Browse application themes for purchase",
                "View visual themes available in the shop",
                "Shop for color schemes and UI themes",
                "Explore purchasable application appearances",
                "See all available theme options for sale",
            ],
            'shop_food_cat': [
                "Browse food items to feed your panda",
                "View available food products in the shop",
                "Shop for snacks and meals for your panda",
                "Explore purchasable food to keep your panda happy",
                "See all available food items for sale",
            ],
            'shop_toys_cat': [
                "Browse toys and play items for your panda",
                "View available toys in the shop",
                "Shop for toys to entertain your panda",
                "Explore purchasable play items for interaction",
                "See all available toy options for sale",
            ],
            'shop_upgrades_cat': [
                "Browse upgrades to enhance your experience",
                "View available upgrades in the shop",
                "Shop for functional improvements and boosts",
                "Explore purchasable upgrades and enhancements",
                "See all available upgrade options for sale",
            ],
            'shop_special_cat': [
                "Browse special limited items",
                "View exclusive and limited-edition shop items",
                "Shop for rare and special items while they last",
                "Explore time-limited and unique purchasable items",
                "See all available special items currently in the shop",
            ],
            # UI settings tooltips
            'ui_language': [
                "Choose the display language for the application",
                "Select which language the interface is shown in",
                "Change the UI language to your preferred locale",
                "Pick from available language translations",
                "Set the language used throughout the application",
            ],
            'ui_font_size': [
                "Adjust the size of text throughout the application",
                "Make text larger or smaller across the entire UI",
                "Set a comfortable font size for readability",
                "Scale the text displayed in the interface",
                "Change the default font size for all UI elements",
            ],
            'ui_animations': [
                "Enable or disable UI animations and transitions",
                "Toggle smooth transitions and visual animations",
                "Control whether the interface uses animated effects",
                "Turn UI motion effects on or off",
                "Disable animations for a snappier interface experience",
            ],
            'ui_transparency': [
                "Adjust the window transparency level",
                "Make the application window more or less transparent",
                "Set the opacity of the main application window",
                "Control how see-through the window appears",
                "Fine-tune the window transparency to your liking",
            ],
            'ui_compact_mode': [
                "Switch to a compact layout with smaller panels",
                "Use a condensed UI layout to save screen space",
                "Toggle compact mode for a more space-efficient view",
                "Reduce padding and margins for a tighter layout",
                "Enable compact mode on smaller displays",
            ],
            'ui_auto_save': [
                "Automatically save settings when changes are made",
                "Enable auto-save so your preferences persist immediately",
                "Toggle automatic saving of configuration changes",
                "Save settings automatically without manual confirmation",
                "Keep your settings up to date without pressing save",
            ],
            'ui_confirm_exit': [
                "Ask for confirmation before closing the application",
                "Show a prompt when you attempt to close the app",
                "Prevent accidental closure with an exit confirmation dialog",
                "Enable a confirmation step before quitting",
                "Toggle the exit confirmation dialog on or off",
            ],
            'ui_startup_tab': [
                "Choose which tab opens when the app starts",
                "Set the default tab displayed on application launch",
                "Pick the initial view shown after startup",
                "Control which section appears first when you open the app",
                "Select your preferred starting tab",
            ],
            'ui_sidebar_position': [
                "Choose whether the sidebar appears on the left or right",
                "Move the sidebar to the opposite side of the window",
                "Set the sidebar position to left or right",
                "Control the placement of the navigation sidebar",
                "Switch the sidebar between left-aligned and right-aligned",
            ],
            'ui_show_statusbar': [
                "Show or hide the status bar at the bottom",
                "Toggle the bottom status bar visibility",
                "Control whether the status bar is displayed",
                "Hide the status bar for a cleaner look",
                "Enable the status bar to see real-time info",
            ],
            # Panda settings tooltips
            'panda_name': [
                "Set a custom name for your panda companion",
                "Give your panda a unique name of your choice",
                "Rename your panda to something personal",
                "Enter a new name for your panda friend",
                "Customize what your panda companion is called",
            ],
            'panda_gender': [
                "Choose your panda's gender identity",
                "Set the gender for your panda companion",
                "Select how your panda is referred to",
                "Pick your panda's gender from the available options",
                "Define the gender identity of your panda",
            ],
            'panda_mood_display': [
                "Shows your panda's current mood state",
                "View how your panda is feeling right now",
                "Check the current emotional state of your panda",
                "See whether your panda is happy, sad, or hungry",
                "Monitor your panda's mood at a glance",
            ],
            'panda_auto_walk': [
                "Enable or disable automatic panda walking",
                "Toggle whether your panda wanders on its own",
                "Control automatic movement of your panda companion",
                "Let your panda walk around freely or stay still",
                "Turn on auto-walk so your panda roams the screen",
            ],
            'panda_speech_bubbles': [
                "Show or hide speech bubbles above the panda",
                "Toggle the display of panda speech bubbles",
                "Control whether your panda shows dialogue bubbles",
                "Enable or disable text bubbles from your panda",
                "Choose if your panda displays speech messages",
            ],
            'panda_interaction_sounds': [
                "Enable sounds when interacting with the panda",
                "Toggle audio feedback for panda interactions",
                "Control whether panda actions produce sound effects",
                "Turn on or off sounds when you pet, feed, or play",
                "Manage sound effects triggered by panda activities",
            ],
            'panda_idle_animations': [
                "Enable or disable idle animations",
                "Toggle animations that play when the panda is idle",
                "Control whether your panda animates while waiting",
                "Turn on idle movements so your panda stays lively",
                "Disable idle animations for a calmer panda",
            ],
            'panda_drag_enabled': [
                "Allow dragging the panda around the screen",
                "Enable or disable click-and-drag for your panda",
                "Control whether you can reposition the panda by dragging",
                "Toggle the ability to move your panda with the mouse",
                "Let your panda be dragged to different screen positions",
            ],
            # Performance settings tooltips
            'perf_thread_count': [
                "Number of threads used for texture processing",
                "Set how many CPU threads to use for sorting tasks",
                "Adjust thread count to balance speed and system load",
                "Control parallel processing capacity for textures",
                "More threads can speed up processing on multi-core CPUs",
            ],
            'perf_cache_size': [
                "Maximum memory used for caching processed textures",
                "Set the upper limit for the texture processing cache",
                "Control how much RAM is reserved for caching",
                "Adjust cache size to optimize performance vs. memory usage",
                "Larger cache sizes can improve repeated-operation speed",
            ],
            'perf_batch_size': [
                "Number of textures processed at once during sorting",
                "Set how many textures are handled in each processing batch",
                "Adjust the batch size to control processing throughput",
                "Larger batches may speed up sorting on powerful hardware",
                "Control the number of files processed simultaneously",
            ],
            'perf_preview_quality': [
                "Quality level for texture preview thumbnails",
                "Set the rendering quality of texture previews",
                "Adjust thumbnail quality to balance clarity and performance",
                "Higher quality previews use more resources but look sharper",
                "Control the detail level of generated texture thumbnails",
            ],
            # Profile tooltips
            'profile_save': [
                "Save your current settings as a profile",
                "Store your preferences in a reusable profile",
                "Create a named profile from your current configuration",
                "Save all current settings for later use",
                "Preserve your setup by saving it as a profile",
            ],
            'profile_load': [
                "Load a previously saved settings profile",
                "Restore settings from one of your saved profiles",
                "Apply a saved profile to update your current configuration",
                "Switch to a different settings profile",
                "Load and activate a previously saved set of preferences",
            ],
            'profile_delete': [
                "Delete a saved settings profile",
                "Remove a profile you no longer need",
                "Permanently delete the selected settings profile",
                "Clean up unused profiles from your saved list",
                "Erase a settings profile from storage",
            ],
            'profile_export': [
                "Export your profile settings to a file",
                "Save your profile to a file for backup or sharing",
                "Write your settings profile to an external file",
                "Create a portable copy of your profile settings",
                "Export your configuration for use on another machine",
            ],
            'profile_import': [
                "Import profile settings from a file",
                "Load a profile from an external settings file",
                "Bring in settings exported from another installation",
                "Restore a profile from a previously exported file",
                "Import shared or backed-up profile configurations",
            ],
            # Statistics tooltips
            'stats_textures_sorted': [
                "Total number of textures you have sorted",
                "See your cumulative texture sorting count",
                "Track how many textures have been processed overall",
                "View the lifetime total of textures you have organized",
                "Check your all-time texture sorting statistics",
            ],
            'stats_time_spent': [
                "Total time spent using the application",
                "See how long you have used the app across all sessions",
                "Track your cumulative usage time",
                "View total hours and minutes spent in the application",
                "Check your all-time usage duration",
            ],
            'stats_panda_interactions': [
                "Total number of panda interactions",
                "See how many times you have interacted with your panda",
                "Track your cumulative panda interaction count",
                "View the total of all panda play, feed, and pet actions",
                "Check your all-time panda interaction statistics",
            ],
            'stats_achievements_earned': [
                "Number of achievements you have earned",
                "See your total achievement completion count",
                "Track how many achievements you have unlocked",
                "View your overall achievement progress tally",
                "Check how many milestones you have reached so far",
            ],
            'stats_currency_earned': [
                "Total Bamboo Bucks earned across all time",
                "See your cumulative Bamboo Bucks earnings",
                "Track the total currency you have earned from all sources",
                "View your lifetime Bamboo Bucks income",
                "Check your all-time earnings from sorting, games, and achievements",
            ],
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
            # Closet subcategory tooltips
            'closet_all_clothing': [
                "See every clothing item you own — shirts, pants, jackets, and more!",
                "All clothing in one place. Use the subcategory buttons to narrow down.",
            ],
            'closet_shirts': [
                "Tops, tees, and sweaters — browse your shirt collection here!",
                "Shirts and tops. Pick one to dress up your panda's torso.",
            ],
            'closet_pants': [
                "Pants, trousers, and bottoms — keep those panda legs covered!",
                "Browse bottom-wear. Your panda deserves proper pants.",
            ],
            'closet_jackets': [
                "Jackets, hoodies, and coats — perfect for chilly panda days!",
                "Outerwear for your panda. Stylish AND warm.",
            ],
            'closet_dresses': [
                "Dresses, robes, and flowing garments — elegant panda fashion!",
                "Browse dresses and robes. Fancy panda time!",
            ],
            'closet_full_outfits': [
                "Full-body outfits and costumes — one piece covers everything!",
                "Complete outfits. Put your panda in a full costume!",
            ],
            'closet_fur_style': [
                "Your panda's fur pattern and texture. Pick a look!",
                "Different fur styles change how your panda's body looks.",
            ],
            'closet_fur_color': [
                "Choose a color for your panda's fur. Lots of options!",
                "Fur colors range from classic black & white to galaxy patterns.",
            ],
            'closet_hats': [
                "Hats sit on top of your panda's head. Try them on!",
                "Browse your hat collection — from beanies to crowns.",
            ],
            'closet_shoes': [
                "Shoes go on your panda's feet and follow their steps!",
                "Footwear that moves with your panda during animations.",
            ],
            'closet_accessories': [
                "Accessories like scarves, bracelets, and pendants!",
                "Extra items to decorate your panda companion.",
            ],
            # Shop subcategory tooltips
            'shop_outfits_cat': [
                "Panda outfits available for purchase. Dress to impress!",
                "Buy full outfits for your panda companion here.",
            ],
            'shop_clothes_cat': [
                "Individual clothing pieces — shirts, pants, jackets, and more!",
                "Browse and buy clothing items for your panda's closet.",
            ],
            'shop_hats_cat': [
                "Hats, helmets, and headwear for your panda!",
                "Browse and buy headwear items for your panda.",
            ],
            'shop_shoes_cat': [
                "Shoes, boots, and footwear for your panda!",
                "Browse and buy footwear items for your panda.",
            ],
            'shop_accessories_cat': [
                "Watches, bracelets, ties, bows, and jewelry for sale!",
                "Buy accessories to add flair to your panda.",
            ],
            'shop_cursors_cat': [
                "Custom mouse cursors to personalize your experience!",
                "Replace the default cursor with fun alternatives.",
            ],
            'shop_cursor_trails_cat': [
                "Cursor trail effects that follow your mouse!",
                "Add sparkly trails to your cursor movements.",
            ],
            'shop_themes_cat': [
                "Application color themes — change the entire look!",
                "Buy new themes to customize the app's appearance.",
            ],
            'shop_food_cat': [
                "Food items to feed your panda and boost happiness!",
                "Buy snacks and meals to keep your panda fed.",
            ],
            'shop_toys_cat': [
                "Toys for your panda to play with!",
                "Buy fun toys and watch your panda interact with them.",
            ],
            'shop_upgrades_cat': [
                "Upgrades to enhance your sorting and app experience!",
                "Buy improvements that make the app even better.",
            ],
            'shop_special_cat': [
                "Special limited items — rare finds and exclusives!",
                "Unique items that may not be available forever.",
            ],
            # UI settings tooltips
            'ui_language': [
                "Pick a language for all menus and text in the app.",
                "Change the display language. Choose from available translations.",
            ],
            'ui_font_size': [
                "Make text bigger or smaller throughout the application.",
                "Adjust font size for better readability.",
            ],
            'ui_animations': [
                "Turn UI animations on or off. Off may improve performance.",
                "Enable or disable smooth transitions and animation effects.",
            ],
            'ui_transparency': [
                "Make the window more or less see-through.",
                "Adjust how transparent the application window is.",
            ],
            'ui_compact_mode': [
                "Switch to a smaller, more condensed layout.",
                "Compact mode saves screen space by shrinking panels.",
            ],
            'ui_auto_save': [
                "Your settings will be saved automatically when changed.",
                "No need to click Save — changes apply instantly.",
            ],
            'ui_confirm_exit': [
                "When enabled, the app asks 'Are you sure?' before closing.",
                "Prevent accidental exits with a confirmation dialog.",
            ],
            'ui_startup_tab': [
                "Choose which tab opens first when you start the app.",
                "Set your preferred starting tab — Sort, Browse, etc.",
            ],
            'ui_sidebar_position': [
                "Move the sidebar to the left or right side of the window.",
                "Customize which side the navigation sidebar appears on.",
            ],
            'ui_show_statusbar': [
                "Show or hide the bar at the bottom of the window.",
                "The status bar shows progress and system information.",
            ],
            # Panda settings tooltips
            'panda_name': [
                "Give your panda a custom name! It appears in speech bubbles.",
                "Type a name for your panda companion.",
            ],
            'panda_gender': [
                "Choose your panda's gender — affects pronouns in messages.",
                "Set your panda's gender identity.",
            ],
            'panda_mood_display': [
                "Shows whether your panda is happy, tired, excited, etc.",
                "Your panda's mood changes based on your interactions!",
            ],
            'panda_auto_walk': [
                "Your panda will occasionally walk around on its own.",
                "Enable automatic panda movement across the screen.",
            ],
            'panda_speech_bubbles': [
                "Speech bubbles appear when your panda has something to say.",
                "Show or hide the text bubbles above your panda.",
            ],
            'panda_interaction_sounds': [
                "Play sounds when you pet, click, or interact with the panda.",
                "Audio feedback for panda interactions.",
            ],
            'panda_idle_animations': [
                "Your panda plays small animations when idle — stretching, yawning.",
                "Enable cute idle animations for when you're not interacting.",
            ],
            'panda_drag_enabled': [
                "Click and drag to move your panda around the screen.",
                "When enabled, you can pick up and move your panda.",
            ],
            # Performance settings tooltips
            'perf_thread_count': [
                "More threads = faster processing, but uses more CPU.",
                "Set how many parallel threads are used for sorting.",
            ],
            'perf_cache_size': [
                "Larger cache = faster repeated operations, more memory used.",
                "Controls how much memory is used for texture caching.",
            ],
            'perf_batch_size': [
                "How many textures are processed in each batch.",
                "Larger batches are faster but use more memory.",
            ],
            'perf_preview_quality': [
                "Higher quality previews look better but load slower.",
                "Adjust thumbnail quality for texture previews.",
            ],
            # Profile tooltips
            'profile_save': [
                "Save all your current settings as a named profile.",
                "Create a profile to quickly switch between configurations.",
            ],
            'profile_load': [
                "Load a saved profile to restore its settings.",
                "Switch to a different saved configuration.",
            ],
            'profile_delete': [
                "Permanently remove a saved profile.",
                "Delete a profile you no longer need.",
            ],
            'profile_export': [
                "Save your profile to a file to share or back up.",
                "Export settings to a portable file.",
            ],
            'profile_import': [
                "Load settings from an exported profile file.",
                "Import a profile from someone else or a backup.",
            ],
            # Statistics tooltips
            'stats_textures_sorted': [
                "The total number of texture files you've organized.",
                "Your lifetime sorting count across all sessions.",
            ],
            'stats_time_spent': [
                "How long you've used the app in total.",
                "Your cumulative time spent in the application.",
            ],
            'stats_panda_interactions': [
                "Every click, pet, feed, and poke counted!",
                "Total times you've interacted with your panda.",
            ],
            'stats_achievements_earned': [
                "How many achievements you've completed so far.",
                "Your achievement completion count.",
            ],
            'stats_currency_earned': [
                "All the Bamboo Bucks you've ever earned.",
                "Your lifetime earnings in the app's currency.",
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
            # Closet subcategory tooltips
            'closet_all_clothing': [
                "Everything your panda can wear. Fashion overload incoming.",
                "All the clothes. Every. Single. One. You're welcome.",
                "Browse the entire wardrobe. Decision paralysis in 3… 2… 1…",
                "All clothing items. Because scrolling is your cardio.",
            ],
            'closet_shirts': [
                "Shirts. Tops. The things that go on the chest area.",
                "Browse tees and tops. Your panda's torso deserves love too.",
                "T-shirts, sweaters, and more. Basic but essential.",
                "Shirt shopping for a cartoon bear. What a time to be alive.",
            ],
            'closet_pants': [
                "Pants! Because nobody wants a pantsless panda. Or do they?",
                "Bottoms. Trousers. Leg coverings. You know what pants are.",
                "Browse pants for your panda. Decency is optional but encouraged.",
                "Leg fashion. Your panda's gams deserve some coverage.",
            ],
            'closet_jackets': [
                "Jackets. Hoodies. The cool outerwear section.",
                "Layer up! Jackets make your panda look extra badass.",
                "Outerwear for the fashionable panda. Stay warm, look cool.",
                "Coats and hoodies. Because pandas get cold too. Probably.",
            ],
            'closet_dresses': [
                "Dresses and robes. Fancy panda time, baby!",
                "Flowing garments for the classy panda in your life.",
                "Dress your bear in a dress. Poetry in motion.",
                "Elegant wear. Your panda is ready for the red carpet.",
            ],
            'closet_full_outfits': [
                "Full body costumes. Transform your panda entirely!",
                "One-piece wonders. Suits, spacesuits, costumes — the works.",
                "Complete outfits. No mixing and matching required.",
                "Full costume mode. Your panda becomes someone else entirely.",
            ],
            'closet_fur_style': [
                "Fur patterns. Make your panda's coat unique AF.",
                "Change the fur style. Fluffy, sleek, or completely wild.",
                "Fur customization. Because plain old panda fur is boring.",
                "Pattern picker. Your panda's fashion starts with the fur.",
            ],
            'closet_fur_color': [
                "Fur colors. Galaxy panda? Shadow panda? Go crazy.",
                "Paint your panda a new color. Rules don't apply here.",
                "Color picker for fur. Normal colors are overrated.",
                "Recolor your panda. Because nature's palette was too limiting.",
            ],
            'closet_hats': [
                "Hats. For when your panda's bald spot needs covering.",
                "Head accessories. Crowns, caps, and chaotic headgear.",
                "Hat rack. Put something on that head!",
                "Browse hats. Your panda is one hat away from perfection.",
            ],
            'closet_shoes': [
                "Shoes. Your panda's been walking barefoot this whole time.",
                "Footwear that moves with your panda's steps. Technology!",
                "Shoe shopping. For a bear. In a texture sorter. Normal.",
                "Pick some kicks. Your panda's feet will thank you.",
            ],
            'closet_accessories': [
                "Bling, baubles, and miscellaneous flair.",
                "Accessories. The cherry on top of your panda's look.",
                "Extra bits and bobs. Because more is more.",
                "Accessory aisle. Scarves, bracelets, pendants — go nuts.",
            ],
            # Shop subcategory tooltips
            'shop_outfits_cat': [
                "Outfits for sale. Dress your panda or regret not doing so.",
                "Buy outfits. Your panda's wardrobe expansion starts here.",
                "Outfit shopping. Retail therapy but with Bamboo Bucks.",
                "Panda outfits. Because naked pandas are so last season.",
            ],
            'shop_clothes_cat': [
                "Individual clothing pieces. Mix and match, baby!",
                "Shirts, pants, jackets — à la carte panda fashion.",
                "Buy clothes piece by piece. Build the perfect outfit.",
                "Clothing aisle. Your panda's dream wardrobe awaits.",
            ],
            'shop_hats_cat': [
                "Hats and helmets. Top off your panda's look!",
                "Headwear shop. From berets to space helmets.",
                "Hat aisle. Because bald pandas need love too.",
                "Buy hats. Crown your panda with style.",
            ],
            'shop_shoes_cat': [
                "Shoes and boots. Walk in style, panda!",
                "Footwear shop. From slippers to rocket boots.",
                "Shoe aisle. Put your best paw forward.",
                "Buy kicks. Your panda's feet deserve the best.",
            ],
            'shop_accessories_cat': [
                "Watches, bracelets, ties — the fancy extras.",
                "Buy bling for your bear. Jewelry and accessories galore.",
                "Accessory shop. Small items, big impact.",
                "Decorative bits. Make your panda sparkle.",
            ],
            'shop_cursors_cat': [
                "Custom cursors. Because the default arrow is basic.",
                "Cursor shop. Point at things with style.",
                "Buy new cursors. Your mouse deserves better.",
                "Cursor skins. Yes, that's a thing. And it's awesome.",
            ],
            'shop_cursor_trails_cat': [
                "Cursor trails. Leave sparkles wherever you go!",
                "Trail effects. Make every mouse movement magical.",
                "Buy trails. Your cursor will be fabulous.",
                "Sparkle shop. Trail effects for the extra in you.",
            ],
            'shop_themes_cat': [
                "Themes. Reskin the entire damn app.",
                "Color schemes for sale. Make everything pretty. Or ugly.",
                "Theme shop. Dark mode not enough? Buy more options.",
                "Visual makeover section. Change all the colors at once.",
            ],
            'shop_food_cat': [
                "Food for the panda. They're always hungry. Always.",
                "Buy snacks. Feed the bear. Simple concept.",
                "Panda food. Because a hungry panda is a grumpy panda.",
                "Snack shop. Your panda's stomach is a bottomless pit.",
            ],
            'shop_toys_cat': [
                "Toys! Buy stuff for your panda to play with.",
                "Toy aisle. Balls, plushies, and other distractions.",
                "Entertainment section. Keep your panda amused.",
                "Buy toys. Watch your panda lose its tiny mind with joy.",
            ],
            'shop_upgrades_cat': [
                "Upgrades. Make the app even better. If that's possible.",
                "Buy improvements. Level up your experience.",
                "Enhancement shop. Boost your sorting game.",
                "Upgrade aisle. For the power users and optimization nerds.",
            ],
            'shop_special_cat': [
                "Special items. Rare, limited, and probably overpriced.",
                "Exclusive stuff. Get it before it's gone!",
                "Limited edition section. FOMO fuel.",
                "Special items for special people. That's you. Probably.",
            ],
            # UI settings tooltips
            'ui_language': [
                "Language picker. Parlez-vous sorting?",
                "Change the language. This won't fix your grammar though.",
                "International mode. Pick your tongue.",
                "Language selector. For the cosmopolitan panda enthusiast.",
            ],
            'ui_font_size': [
                "Font size. Big letters or squint mode. Your choice.",
                "Make text bigger or smaller. We don't judge your eyesight.",
                "Resize the text. Accessibility meets vanity.",
                "Font size slider. From 'ant writing' to 'billboard mode'.",
            ],
            'ui_animations': [
                "Toggle animations. Smooth or snappy, pick your vibe.",
                "Animations on or off. Performance vs. pretty.",
                "UI motion toggle. Less movement = more productivity. Maybe.",
                "Animation switch. For the 'I want it now' crowd.",
            ],
            'ui_transparency': [
                "Window transparency. See-through mode for multitaskers.",
                "Ghost mode. Make the window partially transparent.",
                "Transparency slider. From solid to 'where did my app go?'",
                "Adjust opacity. X-ray vision for your desktop.",
            ],
            'ui_compact_mode': [
                "Compact mode. More screen space, less visual noise.",
                "Squeeze everything smaller. Claustrophobia simulator.",
                "Compact layout for efficiency nerds.",
                "Small mode. Big results. Hopefully.",
            ],
            'ui_auto_save': [
                "Auto-save. Because manually saving is so 2005.",
                "Settings save themselves. You're welcome, lazy person.",
                "Automatic saving. One less button to click.",
                "Set it and forget it. Auto-save handles the rest.",
            ],
            'ui_confirm_exit': [
                "Exit confirmation. The app doesn't want you to leave.",
                "'Are you sure?' dialog. For the indecisive.",
                "Prevents rage-quitting by accident. You're welcome.",
                "Exit safety net. Because misclicks happen to everyone.",
            ],
            'ui_startup_tab': [
                "Pick which tab greets you on launch. First impressions matter.",
                "Startup tab. Skip the boring intro and go straight to work.",
                "Default tab selector. Load your favorite section first.",
                "Launch directly into your preferred tab. Efficiency!",
            ],
            'ui_sidebar_position': [
                "Left or right sidebar. Choose your orientation.",
                "Sidebar position. Left-handers unite! Or don't. Whatever.",
                "Put the sidebar where you want it. Freedom!",
                "Move the navigation panel. Left, right, dealer's choice.",
            ],
            'ui_show_statusbar': [
                "Show or hide the bottom bar. It has info. Sometimes useful.",
                "Status bar toggle. That strip at the bottom with numbers.",
                "The status bar. You probably forgot it existed.",
                "Bottom bar visibility. Hide it for maximum zen.",
            ],
            # Panda settings tooltips
            'panda_name': [
                "Name your panda. 'Sir Fluffington III' is taken though.",
                "Give your bear an identity. Choose wisely. Or don't.",
                "Panda naming ceremony. Make it count!",
                "Type a name. Your panda's been going by 'Hey You' too long.",
            ],
            'panda_gender': [
                "Panda gender picker. They/them is valid, even for bears.",
                "Gender selection. Affects nothing except pronouns. Chill.",
                "Pick your panda's identity. We're progressive here.",
                "Gender choice. For when your panda needs proper pronouns.",
            ],
            'panda_mood_display': [
                "Current mood: probably judging you. Check for yourself.",
                "Mood indicator. Spoiler: it's usually hungry.",
                "Is your panda happy? Check this to find out. Or not.",
                "Mood display. Emotional state of your virtual bear. Deep.",
            ],
            'panda_auto_walk': [
                "Auto-walk. Your panda wanders around like it owns the place.",
                "Let the panda roam. Free-range bear, baby!",
                "Walking toggle. Your panda has places to go. Apparently.",
                "Auto-walk mode. Sometimes the panda just needs a stroll.",
            ],
            'panda_speech_bubbles': [
                "Speech bubbles. Your panda has opinions. Brace yourself.",
                "Toggle panda commentary. Some of it's actually funny.",
                "Show/hide speech bubbles. The panda never shuts up otherwise.",
                "Text bubbles. Your panda is chatty and you can't stop it.",
            ],
            'panda_interaction_sounds': [
                "Interaction sounds. Boop, squish, and other noises.",
                "Sound effects when you touch the panda. It's not weird.",
                "Audio feedback for panda poking. Totally normal behavior.",
                "Toggle panda sounds. Silence is an option. But why?",
            ],
            'panda_idle_animations': [
                "Idle animations. Your panda does cute things when bored.",
                "Little animations play when you're not paying attention.",
                "Idle mode animations. Yawning, stretching, existing.",
                "Your panda has a life too. Watch it live its best life.",
            ],
            'panda_drag_enabled': [
                "Drag mode. Yeet your panda around the screen.",
                "Pick up and move the panda. It's surprisingly fun.",
                "Drag toggle. Grab your bear and put it wherever.",
                "Enable dragging. Your panda is a paperweight you can move.",
            ],
            # Performance settings tooltips
            'perf_thread_count': [
                "Thread count. More threads = faster, but your CPU might sweat.",
                "How many CPU threads to use. Don't go nuclear unless needed.",
                "Processing threads. Turn it up for speed, down for stability.",
                "Thread slider. Your CPU's workout routine.",
            ],
            'perf_cache_size': [
                "Cache size. More cache = faster repeats, more RAM usage.",
                "Memory cache. Feed it RAM and it'll work faster.",
                "Cache allocation. Balance speed vs. memory like a pro.",
                "How much memory to hoard. More cache, fewer reloads.",
            ],
            'perf_batch_size': [
                "Batch size. Process more at once or take it slow.",
                "How many textures to chew through per batch.",
                "Batch processing size. Bigger = faster but hungrier.",
                "Texture batch slider. Efficiency vs. memory, round 47.",
            ],
            'perf_preview_quality': [
                "Preview quality. Pretty thumbnails or fast loading. Pick one.",
                "Thumbnail quality slider. High = pretty, low = fast.",
                "Preview resolution. Your GPU's opinion on aesthetics.",
                "How good should previews look? Slide and find out.",
            ],
            # Profile tooltips
            'profile_save': [
                "Save settings as a profile. For when perfection needs a backup.",
                "Create a settings snapshot. Insurance against future you.",
                "Save profile. Because you'll change everything and regret it.",
                "Backup your settings. You know you'll need this later.",
            ],
            'profile_load': [
                "Load a saved profile. Instant settings swap!",
                "Switch to a saved configuration. Time travel, sort of.",
                "Restore a profile. Undo your bad decisions.",
                "Load profile. Like fast travel but for settings.",
            ],
            'profile_delete': [
                "Delete a profile. Yeet it into the void.",
                "Remove a saved profile. No going back!",
                "Profile deletion. For the profiles that didn't spark joy.",
                "Nuke a saved configuration. Therapeutic, honestly.",
            ],
            'profile_export': [
                "Export your profile. Share your genius with the world.",
                "Save to file. Portable settings for the nomadic user.",
                "Export settings. Great for backups or flexing.",
                "Profile export. Take your setup on the road.",
            ],
            'profile_import': [
                "Import a profile. Use someone else's settings. Genius.",
                "Load from file. Steal someone's configuration. Legally.",
                "Import settings. For when someone else did it better.",
                "Profile import. Skip the setup and use a preset.",
            ],
            # Statistics tooltips
            'stats_textures_sorted': [
                "How many textures you've sorted. Your life's work. In a number.",
                "Total sorted textures. Are you impressed yet? You should be.",
                "Sorting score. The higher the number, the nerdier you are.",
                "Your texture sorting count. We're keeping track. Always.",
            ],
            'stats_time_spent': [
                "Time spent in the app. Don't do the math, it's depressing.",
                "Total time. Proof that you have priorities. Questionable ones.",
                "How long you've been here. Time flies when you're sorting.",
                "App usage time. No, you can't get those hours back.",
            ],
            'stats_panda_interactions': [
                "Panda interaction count. You touch that bear a LOT.",
                "Every click, pet, and poke, tracked. Big panda is watching.",
                "How many times you've bothered the panda. It's a lot.",
                "Interaction counter. Your panda relationship in numbers.",
            ],
            'stats_achievements_earned': [
                "Achievements unlocked. Your virtual trophy collection.",
                "Badge count. How many achievements you've earned.",
                "Achievement score. Are you overachieving? Let's see.",
                "Your achievement collection. Proof you've been productive.",
            ],
            'stats_currency_earned': [
                "Total Bamboo Bucks earned. Your lifetime earnings.",
                "All-time currency. You're basically a panda billionaire.",
                "Money earned. Virtual money, but money nonetheless.",
                "Bamboo Buck lifetime total. You've been busy!",
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
Game Texture Sorter - Quick Help

This application helps you organize and manage texture files from game texture dumps.

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
A: No! Game Texture Sorter is 100% offline. No network calls, complete privacy.

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