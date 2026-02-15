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
            "Click this to sort your damn textures. It's not rocket science, Karen. Hell, it's barely regular science.",
            "Organize these bad boys into folders. Like Marie Kondo but with way more profanity and way less bullshit about sparking joy.",
            "Sort this shit out. Literally. That's what the fucking button does. I'd explain more but you'd probably fall asleep.",
            "Time to unfuck your texture directory structure. You're welcome, you disorganized bastard.",
            "Click here unless you actually enjoy chaos, madness, and disappointing your team. And your mother. She knows what you did.",
            "Make your textures less of a clusterfuck with one goddamn click. It's like Photoshop's undo but for your entire life choices.",
            "SORT BUTTON. Big green button. Does sorting. Why the fuck are you still reading this? Go press the damn thing already!",
            "Press this and watch the panda do all the work while you sit on your ass eating Cheetos. Living the dream, aren't you?",
            "One click and your textures go from dumpster fire to organized perfection. Magic! Just kidding, it's algorithms. Way cooler than magic.",
            "Sort textures faster than you can say 'why the hell didn't I do this sooner.' Seriously, time yourself. I dare you.",
            "The magic 'make my mess disappear' button. You're basically a wizard now, Harry. Except your superpower is file management. Not impressive at parties.",
            "Hit sort and go grab a coffee. The panda's got this shit handled. Unlike your love life, this one's automated and actually works."
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
            "Turn your textures into whatever the hell format you fucking need. PNG, DDS, TGA - I don't judge your poor life choices.",
            "Convert this shit. PNG, DDS, whatever floats your goddamn boat. Or sinks it. I'm not your Coast Guard.",
            "Magic button that transforms textures. No rabbits, hats, or bullshit required. Unlike your last meeting, this actually does something useful.",
            "Because apparently your textures are in the wrong fucking format. Again. Did you learn nothing from last time? Rhetorical question.",
            "Click to unfuck your texture formats. You know you need to. The entire dev team knows you need to. Your mom probably knows too.",
            "Convert or die. Well, not die. But your project might crash and burn like the Hindenburg. Too soon?",
            "Format conversion: because game engines are picky little bastards with commitment issues. Just like your ex.",
            "Press convert and let the panda handle the rest. Go touch grass, seriously. When's the last time you saw actual sunlight?",
            "Convert button. Turns format A into format B. It's not rocket surgery. It's barely regular surgery. Hell, it's barely a band-aid.",
            "Batch conversion go brrr. All your textures, all at once, zero fucks given. Like Thanos but for file formats.",
            "This button converts formats. Not feelings. We don't do therapy here, pal. Try a licensed professional. Or beer.",
            "File conversion: making your textures speak the right language for once. Rosetta Stone for pixels. You're welcome."
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
            "Tweak shit. Make it yours. Unfuck everything to your liking. It's like Pimp My Ride but for software. RIP Xzibit.",
            "Settings, preferences, all that boring-ass but necessary crap. Like taxes but with RGB sliders. Slightly more fun.",
            "Click here if you're anal about how things work. No judgment... okay, maybe some. Definitely some. Who are we kidding, a lot.",
            "Configure this bad boy. Go fucking nuts with options. Channel your inner control freak. Embrace the OCD.",
            "Mess with settings until something breaks. Then blame the developer. It's tradition. Like Thanksgiving but with more finger-pointing.",
            "For control freaks and perfectionists. Yes, you. Don't lie. We see you organizing your desktop icons by color.",
            "Open settings. Where the magic happens. Or at least the obsessive tweaking. Same difference really.",
            "⚙️ Settings panel. Tweak every goddamn knob. Go absolutely ham. Make this interface your bitch.",
            "Configure app behavior. The panda's got options for days, you picky bastard. More settings than a spaceship. Less useful though.",
            "Settings: because your unique snowflake ass needs everything customized. Just like your coffee order that takes 5 minutes to explain.",
            "Open preferences. Customize this motherfucker into oblivion if you want. Make it look like a unicorn vomited on your screen. We won't judge.",
            "Click here to access settings you'll change once and never touch again, you liar. Just like that gym membership. We all know."
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
            "Point me to your damn files already. I haven't got all fucking day. Unlike you, I have shit to process.",
            "Show me where you hid your textures, you sneaky little shit. Are they in 'New Folder (17)'? They're in there, aren't they?",
            "Pick a file. Any goddamn file. Let's get this show on the road. This isn't the fucking Oscars, we don't need suspense.",
            "File picker. Because apparently typing a path is too hard for your lazy ass. It's okay, we invented GUIs for a reason.",
            "Navigate this hellscape of directories and find your shit. Good luck in that nested folder hell you created. Abandon hope, ye who enter.",
            "Choose wisely. Or don't. I'm not your mother and she's disappointed anyway. Probably about other things too, but let's focus.",
            "Browse button. Because drag-drop is apparently too fucking complicated. Baby steps. We'll get there eventually. Maybe.",
            "Select your files. The ones you definitely organized properly. Right? RIGHT? Who am I kidding, it's chaos in there.",
            "File browser for the directionally challenged. It's okay, we've all been there. Some of us are still there. Living there. It's home now.",
            "Pick files. The computer can't read your mind. Yet. Give it another year, AI's getting scary good."
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
            "Pick your texture flavor. Diffuse? Normal? Specular? What-the-fuck-ever floats your shader boat?",
            "Choose categories or process everything. YOLO, am I right? Actually no, backup your shit first. Then YOLO.",
            "Category picker. For when you're too fucking special for 'all textures'. We get it, you're sophisticated. Have a medal. 🏅",
            "Filter this shit by category. Be selective, your majesty. I'll just be here waiting while you make your royal decree.",
            "What kind of textures are we unfucking today? Diffuse? Normal maps? The weird ones you found on that sketchy site?",
            "Pick a category. Or don't. Chaos is always a valid life choice. Some say it builds character. Those people are idiots.",
            "Select what texture types to process. Because apparently 'all' is too simple. God forbid we make your life easy.",
            "Category filter. For the texture snobs among us. Oh, you only work with hand-crafted artisanal normal maps? How pretentious.",
            "Choose your poison: diffuse, normal, specular, or just fuck it and do everything. When in doubt, nuke it from orbit.",
            "Texture categories. Because your anal-retentive ass needs organization. It's okay, I need therapy too."
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
            "Let the panda figure out your LOD levels. He's fucking brilliant like that. Smarter than you at least. No offense. Okay, some offense.",
            "Auto-detect LODs because manually sorting is for masochists and idiots. Which category are you in? Don't answer, it's rhetorical.",
            "Toggle LOD magic. On or off. Your fucking choice. But spoiler: one choice is stupid. Guess which one?",
            "Enable this unless you hate yourself and enjoy wasting your precious life. Like watching paint dry but worse. And boring.",
            "Auto LOD detection. Because apparently counting from LOD0 to LOD3 is fucking rocket science for some people.",
            "Turn this on. Seriously. Don't be a hero. Let the code do the work. Save the heroics for when Taco Bell runs out of hot sauce.",
            "LOD detection: teaching computers to read LOD0, LOD1, etc. Revolutionary shit. Like the printing press but for lazy developers.",
            "Enable LOD auto-detect or spend hours doing it yourself. Your call, genius. I've got popcorn ready for whatever stupid decision you make.",
            "LOD finder. Because apparently '_LOD0' is too cryptic without AI help. It's literally in the fucking filename. Right there. See it?",
            "Auto-detect Level of Detail. Or waste time doing it by hand like a chump. Manual labor in 2024. Bold strategy, Cotton."
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
            "Process a shitload of files at once. Because efficiency. And because clicking 1000 times is how you get carpal tunnel, dumbass.",
            "Batch operations for people with actual work to do. You know, productive people. Not you browsing Reddit. Yeah, I see you.",
            "Do many things to many files. It's beautiful. Like watching dominoes fall but with more practical value and less virginity.",
            "Because processing one file at a time is for chumps and people with way too much fucking time. Get a hobby. Or a life.",
            "Bulk operations. Like Costco but for file processing. Same concept: buy in bulk, save time, question your life choices.",
            "Handle multiple files like a goddamn professional. Not like an amateur. Professionals use batch operations. Be professional, for fuck's sake."
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
            "Export this shit before you lose it. Because Murphy's Law is real and it's out to fuck you specifically.",
            "Save your work unless you enjoy starting over. Some people like pain. BDSM is a thing. But this is just masochism.",
            "Click to yeet your textures to their new home. YEET! Maximum velocity achieved. Your files are now in orbit. Mission accomplished.",
            "Export or suffer the consequences of lost work. Consequences include crying, drinking, and questioning your career choices. Save yourself.",
            "Finalize this motherfucker and export. Ship it. Done. Finished. Finito. Stop tweaking shit, it's good enough. Perfection is the enemy of done.",
            "Save button. Use it. Don't be a hero. Heroes in movies? Cool. Heroes who don't save their work? Fucking idiots."
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
            "Preview this shit before you commit. Trust nobody. Not even yourself. Especially not yourself at 3 AM.",
            "Look at what's about to happen. Prevent disasters. Learn from the Titanic. They should've previewed that iceberg situation.",
            "Preview mode. For the paranoid. And the smart. Being paranoid doesn't mean they're not out to get you. Or that your code won't break.",
            "See the future. Well, the preview. Same difference. It's like a crystal ball but actually useful and less likely to get you burned as a witch.",
            "Check your work before the universe does. The universe is a harsh critic. Zero stars on Yelp. Would not recommend.",
            "Preview because CTRL+Z only goes so far. And by 'so far' I mean 'not far enough when you really fuck up.' Trust me on this."
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
            "Find your shit. It's in here somewhere. Probably in that folder you named 'temp' six months ago.",
            "Search function. Because you lost your damn files again. This is becoming a pattern. Maybe see a doctor? Or a file management course?",
            "Where the fuck is that texture? Let's find out. It's like Where's Waldo but more frustrating and with higher stakes.",
            "Search bar. Type stuff. Get results. Revolutionary. Like Google but local and with lower expectations.",
            "Find your needle in this texture haystack. Except the haystack is on fire and the needle is probably corrupted. Good luck!",
            "Lost something? Course you did. That's why this exists. We planned for your incompetence. You're welcome."
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
            "Analyze the hell out of these textures. Go full Sherlock Holmes on these pixels. Except less cocaine and more metadata.",
            "Deep dive into texture properties. Get nerdy with it. Channel your inner neckbeard. Embrace the technical details. This is your moment.",
            "Analysis mode. For when you need ALL the information. Every. Single. Byte. You magnificent data hoarder.",
            "Let's get technical. Really fucking technical. Break out the pocket protector and thick-rimmed glasses. This is peak nerd shit.",
            "Examine these textures like a CSI investigator. ENHANCE! ENHANCE! Except this actually works unlike that TV bullshit.",
            "Analysis button. Nerd mode activated. Power level over 9000. Your mom is still disappointed though."
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
            "Your favorites. The shit you actually use. Unlike that gym membership. This one gets action.",
            "Quick access to your go-to stuff. Your workflow's greatest hits. The Beatles but for file management.",
            "Favorites list. The VIP section. You're on the list. The bouncer will let you in. Feel special yet?",
            "The greatest hits of your workflow. More useful than a 'Now That's What I Call Music' compilation. Barely.",
            "Your favorite settings because you're a creature of habit. Like a cat but with less grace and more poor life choices.",
            "Bookmarks for the modern age. Still useful. Unlike your college degree. Too harsh? Sorry. Not sorry."
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
            "Recent files. Because your memory is shit. Goldfish have better recall. And they're dead in two weeks.",
            "The stuff you worked on recently. Remember? No? That's why this fucking feature exists. You're welcome.",
            "Recent history. NSA would be proud. Big Brother is watching. Just kidding, it's just tracking your files. Probably.",
            "Your greatest hits from this week. Like a highlight reel but less impressive and more 'oh god what was I doing?'",
            "Recent files list. Memory lane but useful. Unlike actual memory lane which is just regret and embarrassment.",
            "Quick access to what you were just fucking with. Your digital breadcrumb trail. Hansel and Gretel style but with less witch danger."
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
            "Make it pretty. Or dark. Whatever helps your weak-ass eyes not burn from retina-searing brightness.",
            "Theme selector. Because aesthetics matter, damn it. This isn't the 90s. We have standards now. Low standards, but standards.",
            "Change colors until your eyes don't hurt. Or until you realize you're colorblind. That's a fun discovery.",
            "Pick a theme. Light mode users are psychopaths, btw. Fight me. Actually don't, I'm fragile. But you're still wrong.",
            "Customize this bitch to match your vibe. Dark mode, light mode, whatever-the-fuck mode. Live your truth.",
            "Make it yours. Paint that interface. Bob Ross this motherfucker. Happy little UI elements everywhere."
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
            "Cursor styles. Because why the hell not? We coded this at 3 AM fueled by Red Bull and poor decisions.",
            "Change your pointer. Make it fancy. Sparkles optional. But recommended. Everything's better with sparkles.",
            "Cursor customization. We went there. Is it necessary? No. Is it fucking cool? Also no. But it exists.",
            "Pick a cursor. It's the little things. That separate us from the animals. Well, that and opposable thumbs.",
            "Customize your pointy thing. That sounded better in my head. The cursor. I mean the cursor. Moving on.",
            "Make your cursor less boring than default. Unlike your personality. Zing! Just kidding. You're fine."
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
            "Sound settings. Make it loud. Or mute. Your call. Neighbors' sanity not included.",
            "Audio controls for when you want beeps and boops. Like R2-D2 but less useful and more annoying.",
            "Turn sounds on or off. We won't judge. Okay we'll judge a little. Muting is basically admitting defeat.",
            "Sound effects. For that authentic computer experience. Because silence is too peaceful. Add some DING DING motherfucker.",
            "Audio settings. Beep boop motherfucker. I'm a computer. This is what we sound like. Deal with it.",
            "Configure your audio. Or silence everything. Both valid. Some people meditate. Others enable notification sounds. Choose your chaos."
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
            "Tutorial. Because reading docs is apparently hard. I get it. Words are difficult. Pictures help. We have pictures.",
            "Learn how to use this thing. RTFM made easy. That's 'Read The Fucking Manual' for the innocent among us.",
            "Help for the helpless. No shame. We've all been there. Some of us live there. It's our permanent address.",
            "Tutorial button. For when you're lost AF. Like that time you used Apple Maps. We remember. Everyone remembers.",
            "Learn shit here. It's actually helpful. Unlike your college lectures. This one won't put you to sleep. Probably.",
            "Education time. Get learned. Knowledge is power. Power is pizza. Therefore, tutorials equal pizza. Math checks out."
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
            "Help! I've fallen and I can't use software! And I can't get up! Someone call Life Alert!",
            "Cry for help button. We're here for you. Like a digital hug. But less awkward and more informative.",
            "Get help before you break something. Too late? Well fuck. Try asking anyway, maybe we can unfuck it.",
            "Help docs. Read them. Please. We spent hours writing this shit. Show some goddamn respect.",
            "Assistance for the confused. That's you. You're confused. It's okay. Confusion is the first step to enlightenment. Or madness.",
            "Help button. Use it. Don't be a hero. Heroes die in movies. Smart people read documentation."
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
            "About page. Who made this? Why? Find out here. Spoiler: sleep deprivation and caffeine were heavily involved.",
            "Version info and other boring but important shit. Like terms and conditions. But people actually read this one.",
            "Credits to the poor bastards who coded this. They deserve medals. Or therapy. Probably therapy.",
            "About section. Meet your digital overlords. We're just programmers who sold our souls for syntax highlighting.",
            "Who made this? Why? All answered here. Warning: the 'why' answer is just 'seemed like a good idea at 2 AM.'",
            "Application info. For the curious. And the people looking for someone to blame. We accept both."
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
            "CTRL+Z. The panic button. The savior. The reason humanity can function. More important than oxygen.",
            "Unfuck what you just fucked up. Time travel for the terminally clumsy. You're welcome.",
            "Undo. Because mistakes happen. A lot. Constantly. With you specifically. We've been keeping track.",
            "Reverse that disaster you just created. Like Ctrl+Z is your personal time machine. Flux capacitor sold separately.",
            "Time travel button. Go back. Fix shit. Prevent the apocalypse. Or at least prevent that accidental delete.",
            "Undo. Your second chance at not screwing up. Third chance. Fourth. We've lost count. Just use it."
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
            "Redo. Because you undid too much, you indecisive fuck. Make up your goddamn mind already.",
            "CTRL+Y. Forward time travel. Like Back to the Future 2 but less hoverboards and more file restoration.",
            "Redo what you just undid. Make up your mind. This isn't a democracy. Well it is. But stop flip-flopping.",
            "Go forward. Stop going backward. You're not a car. You don't have a reverse gear. Wait, yes you do. But still.",
            "Redo button. For the indecisive. Hamlet wishes he had this button. To redo or not to redo, that is the question.",
            "Fuck it, put it back the way it was. I knew the undo was a mistake. We all knew. But did you listen?"
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
            "Find your damn INPUT texture folder. It's somewhere on that hard drive. Probably buried under 47 folders named 'New Folder'.",
            "Browse for the INPUT folder. Like Tinder but for file directories. Swipe right on the one with your textures.",
            "Point me to your source textures, you beautiful disaster. The INPUT. Where the magic begins. Or the chaos. Usually chaos.",
            "Navigate the digital jungle to find your INPUT texture stash. It's like Indiana Jones but with less Nazis and more clicking.",
            "Show me where the source goods are. The texture goods. The INPUT folder. Not the output. Jesus, read the label.",
            "Pick an INPUT folder. It's not that deep. Well, maybe it is. How many subdirectories did you nest? Sweet Christ.",
            "Source folder browsing: the Windows Explorer safari adventure. Watch out for wild subdirectories and hidden files.",
            "Where'd you put those source textures? Let's go find out. Time for a treasure hunt. X marks the INPUT folder.",
            "INPUT folder selector. That's the folder WITH the textures, genius. The source. The origin. The beginning. Follow along.",
            "Browse for source textures. The ones you want to sort. Obviously. Not rocket science. Barely regular science.",
            "Find your input directory. The panda believes in you. Barely. Like one percent belief. Prove me wrong.",
            "Pick the folder you want processed. Not the output. The INPUT. The source. The motherfucking starting point. Got it?"
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
            "Where do you want this organized mess dumped? Pick an OUTPUT folder. A destination. A final resting place for sorted textures.",
            "Pick an OUTPUT destination. The textures need a new home. Like witness relocation but for files.",
            "Choose wisely. This is where the sorted OUTPUT ends up. Forever. Or until you delete it. Your choice.",
            "OUTPUT folder. Where dreams of organization become reality. And by dreams I mean 'basic file management.' But still.",
            "Select where to yeet your sorted textures. Maximum velocity. Into the OUTPUT folder. YEET!",
            "OUTPUT destination please! Like an Uber but for files. Destination: organized bliss. ETA: whenever you finish clicking.",
            "Where should I put this sorted shit? Literally your call. Your responsibility. Your burden. Welcome to adulthood.",
            "Pick an OUTPUT folder or I'll choose your desktop. Don't test me. I will do it. I've done it before. It was chaos.",
            "OUTPUT directory. Where your beautifully sorted textures will live. Their forever home. Until the next reorganization.",
            "Choose the OUTPUT folder. Not the input. OUTPUT. The result goes here. The finished product. The final destination.",
            "Browse for an output destination. The panda needs an address. GPS coordinates optional but appreciated.",
            "Pick where the sorted results go. This is the OUTPUT selector. O-U-T-P-U-T. The end point. Capisce?"
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
            "Find duplicate textures. Trust issues? Same. This tool validates your paranoia. You were right to be suspicious.",
            "Duplicate detection. Because copying is only flattering sometimes. Other times it's just wasting disk space like an asshole.",
            "Spot the clones. Like a texture witness protection program. Find the imposters. Sus as fuck.",
            "Find duplicates before your hard drive files a complaint. Space is precious. Unlike your time apparently.",
            "Duplicate finder. CTRL+C CTRL+V consequences detector. Your copy-paste addiction has a price. This finds it.",
            "Because apparently copy-paste got out of hand. Like rabbits. But less cute and more storage-consuming.",
            "Hunt down those sneaky identical textures. They're hiding. Playing hide and seek. Time to end the game.",
            "Duplicate detection: the 'who wore it better' for textures. Spoiler alert: they're exactly the same. Both can go."
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
            "Group LODs together. They're like a dysfunctional family. LOD0 is the favorite child. LOD3 is the disappointment.",
            "Keep LOD buddies together. Separation anxiety is real. They need each other. It's codependent but functional.",
            "LOD grouping. Because nobody puts LOD-baby in a corner. Dirty Dancing reference. You're welcome. Google it, zoomer.",
            "Bundle those LODs like a cozy texture family reunion. Awkward small talk optional. Potato salad mandatory.",
            "Keep the LOD crew together. Squad goals. Friendship is magic. File organization is more magic.",
            "Group LODs. Like organizing your sock drawer but nerdier. And actually useful. Unlike your sock drawer.",
            "LOD family reunion time. Get them all in one folder. Group photo! Everyone say 'optimization!'",
            "No LOD left behind. We group them ALL. LOD0 through LOD-whatever-the-fuck. Everyone gets a home."
        ]
    },
    'achievements_tab': {
        'normal': [
            "View your achievements and progress milestones",
            "Track your accomplishments and earned badges",
            "See which achievements you've unlocked"
        ],
        'vulgar': [
            "Check your trophies, you overachiever. Look at you being all productive and shit. Your mother would be proud. Probably.",
            "Achievement log. Proof you actually did something. Unlike that time you said you'd go to the gym.",
            "Your bragging rights live here. Screenshot this. Post on Twitter. Nobody cares. Do it anyway.",
            "Look at all the shit you've accomplished. Proud? You should be. Or at least mildly satisfied. That's close enough.",
            "Achievements. For people who need validation. It's okay. We all do. Digital gold stars for everyone!",
            "Gold stars and participation trophies. Knock yourself out. You earned them. Or the system took pity. Either way, congrats!"
        ]
    },
    'shop_tab': {
        'normal': [
            "Opens the reward store where earned points can be spent",
            "Browse and purchase items with your earned currency",
            "Spend your points on cosmetics and upgrades"
        ],
        'vulgar': [
            "This is the loot cave. Spend your shiny points, you filthy casual. Capitalism simulator right here.",
            "You did work. Now buy dumb cosmetic crap. It's the circle of life. Hakuna Matata, bitch.",
            "Click here to exchange grind for dopamine. It's like a slot machine but with guaranteed purchases. Still addictive though.",
            "The shop. Where your hard-earned points go to die. RIP your savings. They served you well. For like five minutes.",
            "Buy stuff. Waste points. Live your best life. YOLO but make it consumerism. Adam Smith is smiling somewhere.",
            "Shopping spree time. Your wallet (points) won't survive. Economic responsibility? Never heard of her."
        ]
    },
    'shop_buy_button': {
        'normal': [
            "Purchase this item with your currency",
            "Buy this item from the shop",
            "Complete the purchase"
        ],
        'vulgar': [
            "Yeet your money at this item. Do it. No regrets. Okay, some regrets. But that's tomorrow's problem.",
            "Buy it before someone else doesn't. Because you're the only user. But urgency sells! Marketing 101.",
            "Take my money! Except it's points. Whatever. Close enough. The emotion is real even if the currency isn't.",
            "Purchase this bad boy. You deserve it. Maybe. Probably not. But treat yourself anyway. Self-care!",
            "Click buy. Instant regret or joy. 50/50. Life is a gamble. This purchase? Also a gamble. Roll the dice.",
            "Add to cart? Nah. Just buy the damn thing. We don't have a cart system. One-click purchase baby. Amazon would be proud."
        ]
    },
    'shop_category_button': {
        'normal': [
            "Filter shop items by this category",
            "View items in this category",
            "Browse this section of the shop"
        ],
        'vulgar': [
            "Filter the shop. Because scrolling is for peasants. And people with time. You have neither.",
            "Category filter. Find your poison faster. Life's too short to browse every goddamn item.",
            "Browse this section. There's good shit in here. Trust me. Or don't. I'm a tooltip, not a financial advisor.",
            "Click to see what's in this category of nonsense. Organized nonsense. The best kind of nonsense."
        ]
    },
    'rewards_tab': {
        'normal': [
            "View all unlockable rewards and their requirements",
            "See what rewards you can earn by completing goals",
            "Track your progress toward unlocking rewards"
        ],
        'vulgar': [
            "Your loot table. See what you can unlock. Like a video game but the reward is slightly better file management.",
            "Rewards page. Dangle carrots in front of yourself. Self-motivation through materialism. It works though.",
            "All the shiny things you haven't earned yet. Look at them. Want them. Feel the desire. Now go earn them.",
            "Check what's locked and cry about it. Or get motivated. Your choice. I recommend motivation but crying is valid too.",
            "Reward tracker. Motivation through materialism. Late-stage capitalism in tooltip form. You're welcome.",
            "See the prizes. Want them. Work for them. Simple. Pavlov would be proud. You're the dog. The treats are digital."
        ]
    },
    'closet_tab': {
        'normal': [
            "Customize your panda's appearance with outfits and accessories",
            "Dress up your panda companion with unlocked items",
            "Change your panda's look and style"
        ],
        'vulgar': [
            "Dress up your panda. Fashion show time. Runway walk optional. Fierce attitude mandatory.",
            "Panda wardrobe. Because even pandas need style. Fashion is pain. Digital fashion is painless. Much better.",
            "Outfit your furry friend. Don't make it weird. Keep it PG. This is a family-friendly texture sorter. Mostly.",
            "Panda closet. It's like The Sims but with bamboo. And less house fires. And more file management. Actually nothing like The Sims.",
            "Fashion crimes against pandas start here. Go wild. Tutus? Sure. Top hat? Why not. Regret? Inevitable.",
            "Makeover time! Make your panda look fabulous or ridiculous. There's a fine line. We crossed it. No regrets."
        ]
    },
    'browser_browse_button': {
        'normal': [
            "Select a directory to browse for texture files",
            "Open folder picker to navigate to your files",
            "Choose a folder to browse its contents"
        ],
        'vulgar': [
            "Pick a folder to browse. Any folder. Let's see what's inside. Your organizational skills? Or lack thereof?",
            "Browse folder button. Because typing paths is for masochists. And people who remember where they put things. Not you.",
            "Point me to your files. I'll judge them. Silently. Very silently. With so much judgment.",
            "Folder picker. Navigate your digital hoarding. It's okay. We're all pack rats here. No shame. Okay, some shame.",
            "Open the folder browser. The panda wants to snoop through your textures. Privacy is dead. Accept it.",
            "Browse for a directory. The panda is a professional folder-opener. Years of experience. Degrees in browsing. Very qualified.",
            "Select a directory to browse. Like window shopping but for files. Less expensive. Same disappointment.",
            "Folder browsing: for when you need to see ALL the textures. Every. Single. One. Including the bad ones."
        ]
    },
    'browser_refresh_button': {
        'normal': [
            "Refresh the file browser list to show current directory contents",
            "Reload the current directory listing",
            "Update the file browser display"
        ],
        'vulgar': [
            "Refresh file list. In case something magically changed. Spoiler: it didn't. But hope is free.",
            "Hit refresh like you're checking your ex's profile. Obsessively. Repeatedly. With false hope.",
            "Reload the file browser. Because maybe it's different this time. (It's not.) But you'll try anyway.",
            "F5 energy in button form. Refresh the file listing. Compulsively. Like you do with your email. Expecting different results.",
            "Refresh the browser. New files? Updated files? Only one way to find out. Spoiler: probably nothing changed.",
            "Smash refresh. The panda loves watching the file list reload. It's therapeutic. Very zen. ASMR for file systems.",
            "Refresh button. For the impatient and the hopeful. Mostly the impatient. But hey, dream big.",
            "Reload file listing. Trust no cache. Cache is a liar. A dirty, filthy liar. Refresh for truth."
        ]
    },
    'browser_search': {
        'normal': [
            "Search for files by name in the current directory",
            "Filter displayed files by search term",
            "Type to find specific files in the file browser"
        ],
        'vulgar': [
            "Find your damn files. Type something in the search box. Anything. A name. A letter. Your hopes and dreams.",
            "Search bar. For when you can't find shit in the file browser. Because organization is theoretical. Chaos is real.",
            "Like Google but for your messy texture folder. Except less ads. And no tracking. Probably.",
            "Ctrl+F vibes. Find that needle in the texture haystack. The haystack is massive. The needle is tiny. Good luck.",
            "Type to filter files. The panda pre-filters the results for you. Like a good assistant. Unlike Karen from HR.",
            "Search files by name. Or by content if smart search is on. Technology is magic. Arthur C. Clarke was right.",
            "File search. Because scrolling through 20,000 files is not a hobby. It's a cry for help. Use the search.",
            "Find files faster. The search box is your friend. Your only friend. It won't judge you. Much."
        ]
    },
    'browser_show_all': {
        'normal': [
            "Toggle between showing only textures or all file types",
            "Show all files, not just supported texture formats",
            "Include non-texture files in the listing"
        ],
        'vulgar': [
            "Show EVERYTHING. Even the weird files. The ones you thought you deleted. They're still here. Always watching.",
            "All files mode. Including your shame. That embarrassing test file. Yeah, we see it. Everyone sees it.",
            "Toggle this to see non-texture files too. CONFIG files. README files. That file named 'djkfhdsjkfh'. Very descriptive.",
            "Show all. Because you're nosy like that. Embrace it. Privacy is dead anyway.",
            "All file types visible. Textures, configs, your secret diary. We don't discriminate. We judge equally.",
            "Show every file. The panda doesn't discriminate by extension. .txt, .exe, .wtf - all welcome here.",
            "Unfiltered file listing. See ALL the things. The good, the bad, the 'why does this exist?'",
            "Show all files checkbox. Remove the texture-only filter. Unleash the chaos. Regret optional."
        ]
    },
    'browser_show_archives': {
        'normal': [
            "Show archive files (ZIP, 7Z, RAR) in the file listing",
            "Toggle display of archive files alongside textures",
            "Include archive files in the browser view",
            "Show compressed archive files in the directory listing"
        ],
        'vulgar': [
            "Show those zipped-up files too. Unzip them mentally. Use your imagination. The power of visualization.",
            "Archives in the list. Because why not complicate things. Life was too simple. Add more file types.",
            "Toggle this to see ZIP/RAR/7Z files. You hoarder. Digital pack rat. Compress all the things!",
            "Show archives. For when regular files aren't enough chaos. Need more entropy? Here you go.",
            "Show archive files in the browser. ZIP, RAR, 7Z, the whole gang. The Avengers of compression formats.",
            "Toggle archives on. Because you need to see those compressed files too. All files matter. Even compressed ones.",
            "Show archive checkbox. The panda sees your compressed secrets. Nothing is hidden. Compression is futile.",
            "Display archives alongside textures. The more files, the merrier. Chaos is a ladder. Climb it."
        ]
    },
    'alpha_fix_button': {
        'normal': [
            "Start fixing alpha channels on selected textures",
            "Begin alpha correction process with chosen preset",
            "Fix transparency issues in PS2 texture files",
            "Apply alpha correction to remove halos and artifacts"
        ],
        'vulgar': [
            "Fix that alpha. No more white boxes ruining your day. Or your textures. Or your life.",
            "Click to unfuck your transparency. You're welcome. The panda's got your back. Unlike that one friend.",
            "Alpha fixer go brrrr. Say goodbye to those ugly halos. And that transparency nightmare. Brrrrr indeed.",
            "Fix the alpha or keep living with broken transparency. Your call. But we both know which is the right choice."
        ]
    },
    'alpha_fix_input': {
        'normal': [
            "Select a file or folder containing textures with alpha issues",
            "Browse for a single image or directory with textures to fix",
            "Choose a source file or folder for alpha correction",
            "Pick an image file or folder with broken-alpha textures",
            "Drag and drop a file or folder to process",
            "Input can be a single texture or an entire directory"
        ],
        'dumbed-down': [
            "Pick ONE file or a WHOLE folder to fix!",
            "Choose a single image or a bunch of them in a folder!",
            "You can select just one picture OR a folder full of them!",
            "Drag a file here, or drag a whole folder!",
            "Works with one image or many images in a folder!",
            "Single file or folder — both work!"
        ],
        'vulgar': [
            "Point me to ONE file or a folder with your broken textures. The panda doesn't discriminate. All files are equal in their brokenness.",
            "File or folder. Pick one. Both work. The panda doesn't judge. Okay, judges a little. But processes both.",
            "Single image? Sure. Whole folder? Also fine. Your call. This isn't a dictatorship. It's a benevolent file-fixing autocracy.",
            "Drag a file. Drag a folder. Whatever. I'll fix it. I'm not picky. Unlike you with your coffee order.",
            "One texture or a thousand. Just point me to the disaster zone. Hurricane Texture has made landfall. Time for cleanup.",
            "File or folder input. Because flexibility is key. Like yoga but for file selection. Way less sweating.",
            "Select input. File, folder, doesn't matter. I got you. Like a digital security blanket. But useful.",
            "Browse for one file or an entire folder. Alpha fixer handles both. It's bisexual for file types. Very progressive."
        ]
    },
    'alpha_fix_output': {
        'normal': [
            "Choose where to save fixed textures (leave empty for in-place)",
            "Select output folder for corrected textures",
            "Pick a destination for alpha-corrected files",
            "Set output directory (blank = modify originals)"
        ],
        'vulgar': [
            "Where do you want the fixed files? Or just leave it empty, you lazy beautiful bastard. In-place edits are fine.",
            "Output folder. Or don't set one and live dangerously. Edge optional. Danger mandatory.",
            "Pick where the fixed textures go. Or gamble with in-place edits. Life's a casino. This is just files.",
            "Choose output. Empty = overwrite originals. No pressure. Okay, some pressure. Actually a lot. But it's fine."
        ]
    },
    'alpha_fix_preset': {
        'normal': [
            "Select alpha correction preset for different texture types",
            "Choose a correction mode optimized for specific PS2 alpha styles",
            "Pick preset: binary (UI), three-level, smooth, or clean edges",
            "Select how alpha channels should be corrected"
        ],
        'vulgar': [
            "Pick a preset. Each one fixes alpha differently. Choose wisely, Indy. The wrong grail melts faces. Wrong preset just looks bad.",
            "Alpha presets. Like difficulty modes but for transparency. Easy, medium, hard, fuck-it-we'll-do-it-live.",
            "Select your flavor of alpha correction. They're all good. Some are better. But all are good. Trust me. I'm a tooltip.",
            "Choose preset or just pick binary and pray. Prayer optional. Binary recommended. Your mileage may vary."
        ]
    },
    'alpha_fix_recursive': {
        'normal': [
            "Process textures in subdirectories as well",
            "Include files from nested folders in the correction",
            "Scan all subdirectories for textures to fix",
            "Enable recursive processing of directory tree"
        ],
        'vulgar': [
            "Dig through ALL the subfolders. Leave no texture behind. No soldier left behind. But textures. Saving Private Texture.",
            "Go deep. Process everything in every subfolder too. Deep like philosophy. Or deep like folder nesting. Both work.",
            "Recursive mode. Because your files are nested like Russian dolls. Matryoshka folder structure. Very cultural.",
            "Check subfolders too. Or just the top level if you're lazy. No judgment. Okay, some judgment. Fine, a lot."
        ]
    },
    'alpha_fix_backup': {
        'normal': [
            "Create backup copies before modifying files",
            "Save original files as backups before applying changes",
            "Keep a safety copy of unmodified textures",
            "Backup originals in case correction needs reverting"
        ],
        'vulgar': [
            "Backups. Because you WILL want to undo this someday. Murphy's Law is real. Backups are sacred.",
            "Save copies first. Trust me, future you will thank present you. Hell, future you might buy present you a beer.",
            "Create backups. Unless you like living on the edge. Tom Cruise in that motorcycle scene. But with files. Less cool.",
            "Backup your files or regret it later. Classic choice. Like 'turn back' signs in horror movies. Nobody listens."
        ]
    },
    'alpha_fix_overwrite': {
        'normal': [
            "Overwrite original files with corrected versions",
            "Replace source files with alpha-fixed output",
            "Save corrected textures over the originals",
            "Modify files in-place without creating copies"
        ],
        'vulgar': [
            "Overwrite originals. Point of no return. Hope you have backups. This is the Rubicon. Caesar is crossing. Good luck.",
            "Replace the originals. Bold move, Cotton. Let's see if it pays off. Spoiler: probably will. But maybe won't.",
            "Overwrite mode. The 'YOLO' of file operations. Drake would approve. Your IT department would not.",
            "Write over originals. No take-backs unless you backed up. This is commitment. Like marriage but for files."
        ]
    },
    'alpha_fix_extract_archive': {
        'normal': [
            "Extract textures from archive files before fixing alpha",
            "Unpack ZIP/7Z/RAR archives and process contained textures",
            "Automatically extract archived textures for correction",
            "Support archive input for alpha correction"
        ],
        'vulgar': [
            "Extract from archives first. Unzip then fix. Simple. Like a two-step process. But actually two steps.",
            "Pull files out of archives before fixing. Multitasking! The panda can chew bamboo AND extract files. Talented.",
            "Unpack those zipped textures and fix 'em. Two birds, one click. Efficient. PETA might disagree but they're not here.",
            "Extract from archive. Because fixing zipped files is hard. Actually impossible. Physics won't allow it. Trust me."
        ]
    },
    'alpha_fix_compress_archive': {
        'normal': [
            "Compress fixed textures into a ZIP archive",
            "Create a ZIP file containing all corrected textures",
            "Package alpha-corrected output into an archive",
            "Bundle fixed textures into a compressed archive"
        ],
        'vulgar': [
            "Zip it all up when done. Neat and tidy. Unlike your desktop. Which is a war zone. We've all seen it.",
            "Compress output. Because loose files are so last century. This is 2024. We compress. We organize. We function.",
            "Pack everything into a ZIP. Marie Kondo would be proud. This sparks joy. Compressed, organized, beautiful joy.",
            "Archive the output. For the organizationally obsessed. You know who you are. We see you. It's okay."
        ]
    },
    'alpha_fix_preview': {
        'normal': [
            "Preview a single image with the current alpha correction preset",
            "Load and preview one file to see before/after alpha correction",
            "Test alpha correction on a single image before batch processing",
            "Browse for an image to preview with the selected preset",
            "See how alpha correction affects one texture before processing all",
            "Preview individual file with live preset comparison"
        ],
        'dumbed-down': [
            "Click to see how ONE image will look after fixing!",
            "Preview a single file before fixing a whole bunch!",
            "Test the alpha fix on just one image first!",
            "See before and after for one picture!",
            "Try fixing one file to make sure it looks good!",
            "Load one image and see the fix preview!"
        ],
        'vulgar': [
            "Preview one file. See what the fuck you're getting into before committing.",
            "Test drive the alpha fix on a single image. Smart fucking move, actually.",
            "Load a file and see the before/after. It's like a makeover show but for textures.",
            "Preview single file. Because YOLO batch processing is for the brave and/or stupid.",
            "Check what the preset does to one image. Don't fly blind, dipshit.",
            "See the fix on one file first. The panda respects your paranoid ass.",
            "Test alpha correction on one image. Then decide if you trust this shit.",
            "Single file preview. For when you want to be absolutely goddamn sure.",
            "Try before you buy. Or in this case, preview before you batch-process your entire library.",
            "One file test run. Because mistakes are expensive and you're already broke."
        ]
    },
    'alpha_fix_export': {
        'normal': [
            "Export the currently previewed alpha-corrected image",
            "Save the fixed image shown in the preview",
            "Export this single corrected texture to a file",
            "Save the alpha-fixed preview to your chosen location",
            "Export the processed image from the preview",
            "Save this single fixed texture without batch processing"
        ],
        'dumbed-down': [
            "Save the fixed image you're looking at!",
            "Export this ONE fixed picture to a file!",
            "Save the preview image after it's been fixed!",
            "Click to save this corrected image!",
            "Export the single image you just previewed!",
            "Save this fixed picture somewhere!"
        ],
        'vulgar': [
            "Export this fixed image. One and fucking done. Efficient as hell.",
            "Save the preview. Because sometimes you only need ONE fixed texture, not a thousand.",
            "Export this single texture. No batch bullshit required.",
            "Save what you see. The preview, now permanent. Revolutionary, I know.",
            "Export single file. For when batch processing is complete overkill.",
            "Grab that fixed image and save it. Mission accomplished, you beautiful bastard.",
            "Export preview result. Sometimes less is more, you overachiever.",
            "Save this bad boy. One perfect texture, ready to fucking go.",
            "Export button. Takes the preview and saves it. Rocket science it ain't.",
            "Single file export. Because not everything needs to be a batch operation, Karen."
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
            "Mute everything. Enjoy the silence, you hermit. Deafening silence. Beautiful. Like a library. Or a tomb.",
            "Sound toggle. On or off. Binary. Like your social skills. On: functional. Off: hermit mode activated.",
            "Kill all sounds. Peace and quiet at last. Serenity now. Inner peace achieved. Neighbors pleased.",
            "Enable sounds or pretend you're in a library. Your call. Shh. Quiet hours. No fun allowed.",
            "Toggle audio. Because not everyone appreciates art. Some people are uncultured swine. Present company excluded."
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
            "Master volume. Crank it up or shut it down. This is the power knob. The god slider. The volume supreme.",
            "The big volume knob. Turn it up to 11 if you're brave. Spinal Tap reference. Classic. Google it if you're uncultured.",
            "Overall loudness control. Your neighbors might care. Hell, they probably will care. Fuck 'em. Live your truth.",
            "Volume slider. Slide to the right for chaos, left for stealth mode. Stealth is boring. Chaos is fun. Choose wisely.",
            "How loud do you want this shit? Slide and find out. Science experiment. Except your ears are the lab rats."
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
            "Effects volume. Make the clicks louder or stfu. Click satisfaction is important. ASMR for productivity nerds.",
            "Sound effects loudness. For those satisfying click sounds. The dopamine hits. The auditory rewards. The good stuff.",
            "Turn up the effects or turn them down. Nobody's watching. Except me. I'm watching. Judging your volume choices.",
            "How loud should the bleep-bloops be? You decide. Democracy in action. Freedom rings. At whatever volume you choose.",
            "Effects slider. Slide it around like you know what you're doing. Fake it till you make it. Confidence is key."
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
            "Notification volume. Ding ding or nothing. Pick one. The bell tolls. For thee. At whatever volume you set.",
            "How loud do you want to be bothered? Slide accordingly. Interruptions are customizable. Modern problems, modern solutions.",
            "Notification sounds. Adjust before your coworkers complain. Or don't. Chaos in the workplace. Anarchy!",
            "Alert volume. From 'barely a whisper' to 'everyone heard that'. Full spectrum. Choose your embarrassment level.",
            "Notification loudness. Subtle or obnoxious. Both valid. Both have their place. Usually not in meetings though."
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
            "Sound packs. Default is boring, vulgar is... interesting. Spicy. Like hot sauce but for your ears.",
            "Choose your audio aesthetic. Classy or trashy. Professional or profane. Corporate or chaotic.",
            "Pick a sound theme. Each one has its own personality. Like you. But hopefully less annoying.",
            "Sound pack selector. Default, minimal, or WTF mode. WTF mode is our specialty. It's in the name.",
            "Audio vibes. Pick the one that matches your energy. Calm? Chaotic? Catastrophic? We got you covered."
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
            "Test the sound. Preview before you commit. Smart. Unlike that impulse purchase. Or that tattoo.",
            "Click to hear a preview. Try before you buy... wait, it's free. Test anyway. Science demands it.",
            "Sound test. Because surprises aren't always fun. Sometimes they're annoying. Avoid auditory regret.",
            "Preview this noise. Your eardrums will thank you. Or not. They might hate it. Only one way to find out.",
            "Hit test to hear what this sounds like. Science! Experimentation! Discovery! Or just curiosity. That works too."
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
            "Cursor style. Default is boring. Live a little. Take risks. Choose the skull. Be that person.",
            "Change your cursor. Skull cursor? Hell yeah. Edgy. Mysterious. Possibly problematic. Definitely cool.",
            "Pointer picker. Because the default arrow is basic AF. Basic bitch arrow. Upgrade that shit.",
            "Cursor options. From professional to 'what is that?' Full spectrum. Office appropriate to nightmare fuel.",
            "Pick a cursor. Crosshair makes you feel like a pro gamer. Even if you're just clicking buttons. Fake it."
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
            "Cursor size. Compensating for something? Go huge. No shame. Big cursor energy. Own it.",
            "Make your cursor tiny or massive. No judgment. Okay, some judgment. But mostly support.",
            "Size matters. At least for cursors. Pick your preference. Small and nimble or THICC and visible.",
            "Cursor size slider. From 'where the hell is it' to 'can't miss it'. Lost your cursor? Make it bigger, genius.",
            "Resize your pointer. Because accessibility is important, damn it. Vision problems are real. Big cursor gang rise up."
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
            "Cursor trail. Leave sparkles wherever you go. Majestic. Like a unicorn. Or a glitter bomb. Beautiful chaos.",
            "Enable trails. Your cursor will look fabulous. Trust me. I'm a professional. Okay not really. But it looks good.",
            "Sparkle trail toggle. For the extra in all of us. Extra is a lifestyle. Embrace it. Sparkle on, you magnificent bastard.",
            "Cursor trail. Because your mouse movements deserve to be celebrated. Every click. Every hover. Art in motion.",
            "Turn on trails and watch your productivity drop. Worth it. Beauty requires sacrifice. In this case, focus."
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
            "Trail style. Rainbow? Fire? Galaxy? Go nuts. Cosmic cursor energy. Interstellar pointing device.",
            "Pick a trail flavor. Each one is more extra than the last. Maximum extraness. Peak aesthetic overload.",
            "Trail aesthetic picker. Match your energy level. Calm: stars. Chaotic: rainbow vomit. Choose your fighter.",
            "Choose your sparkle style. No wrong answers here. Except maybe that one. Yeah, that one's wrong. Kidding. Maybe.",
            "Trail options. From 'subtle nature' to 'galactic overkill'. Subtle is boring. Overkill is living. Choose life."
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
            "Edit this hotkey. Remap it to something useful. Or chaotic. Useful is boring. Chaos is memorable.",
            "Change the keybinding. Make it whatever the hell you want. Your keyboard. Your rules. Your inevitable carpal tunnel.",
            "Remap this shortcut. Ctrl+Alt+Delete? Go for it. Live dangerously. Break conventions. Piss off other users.",
            "Edit hotkey. Because the default key was stupid. Some developer at 3 AM made that choice. Fix their mistakes.",
            "Rebind this action. Your keyboard, your rules. Democracy in action. Or anarchy. Probably anarchy."
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
            "Enable or disable this shortcut. Some keys deserve a break. Keyboard rest day. Recovery is important.",
            "Toggle hotkey. On or off. Revolutionary, I know. Binary choices. The foundation of computing. And this toggle.",
            "Disable this shortcut if it keeps interrupting your flow. Flow state is sacred. Protect it. Kill the interruptions.",
            "Turn this keybinding on or off. It's like a light switch but nerdier. And less likely to electrocute you.",
            "Enable/disable toggle. For when shortcuts start shit. Keyboard drama. Digital beef. Toggle it off. Problem solved."
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
            "Color your cursor. Make it match your personality. Vibrant? Use red. Dead inside? Gray works.",
            "Cursor tint. Paint that pointer whatever color you want. RGB everything. Gaming culture approved.",
            "Hex color input. #FF0000 if you're feeling dangerous. Red is passion. Or anger. Or both. Spicy.",
            "Tint your cursor. Because plain white is so last year. This year? Neon pink. Next year? Who knows. Fashion.",
            "Color picker for your cursor. Go full rainbow if you dare. Pride cursor. Every click a statement. Fabulous."
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
            "Reset all hotkeys to defaults. Panic button for keybinds. The nuclear option. Format C: for shortcuts.",
            "Factory reset your shortcuts. Undo all your 'improvements'. Return to sender. Admit defeat gracefully.",
            "Reset everything. Start fresh. Embrace the defaults. Sometimes vanilla is the best flavor. Controversial take.",
            "Nuclear option for hotkeys. Resets EVERYTHING. Scorched earth policy. Burn it all down. Start over.",
            "Defaults button. For when your custom bindings are a disaster. It happens. No shame. We've all been there. Reset and move on."
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
            "Pick a sound style. Chime, beep, whatever tickles your fancy. Auditory customization. Sound sommelier. You decide.",
            "Sound selector. Mix and match your audio nightmare. Or symphony. Depends on your choices. And taste.",
            "Choose your weapon. I mean sound. Same energy. Every notification is a battle. Arm yourself accordingly.",
            "What noise do you want for this event? Go wild. The world is your oyster. This is your audio canvas.",
            "Sound picker. The DJ booth of settings panels. Drop that beat. Mix those sounds. DJ Panda in the house."
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
            "Micromanage your sounds. Mute what annoys you. Custom silence. Tactical audio disabling. Surgical precision.",
            "Individual sound toggles for control freaks. That's you. You're the control freak. Own it. Excel at it.",
            "Pick and choose which sounds you tolerate. Fair enough. Not all sounds are created equal. Democracy in action.",
            "Per-event audio control. Because one size doesn't fit all. Customization is king. Or queen. Or non-binary monarch.",
            "Cherry-pick your sounds like the picky bastard you are. Selective hearing. But intentional. And helpful."
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
            "Every piece of clothing. Fashion overload incoming. Brace yourself. The fashion show is about to begin.",
            "All the clothes. Browse 'em all, you fashionista. Every shirt, pant, hat. The whole fucking wardrobe.",
            "Your panda's entire wardrobe in one scrollable nightmare. Or dream. Depends on your relationship with fashion.",
            "All clothing. Because subcategories are for quitters. And organized people. But mostly quitters."
        ]
    },
    'closet_shirts': {
        'normal': [
            "Browse shirts and tops for your panda",
            "View your collection of tops and tees",
            "Shirts that fit perfectly on your panda's torso",
        ],
        'vulgar': [
            "Shirts. The torso region. Chest coverage. Basic fashion. Essential protection. Nipple concealment.",
            "Tops and tees. Basic but essential bear fashion. Every panda needs a good shirt. It's just facts.",
            "Shirt shopping for a panda. What a world. This is the timeline we're in. Welcome to the future.",
            "Browse tops. Your panda's chest needs some love. Fashion love. Fabric love. Dignified coverage love."
        ]
    },
    'closet_pants': {
        'normal': [
            "Browse pants and bottoms for your panda",
            "View your collection of pants and trousers",
            "Pants that follow your panda's leg movements",
        ],
        'vulgar': [
            "Pants! Give your panda some dignity. Lower body coverage. Leg fashion. Modest and necessary.",
            "Leg coverings. Because naked panda legs are weird. Uncomfortable. Unprofessional. Cover that shit.",
            "Trousers that move with the bear's legs. Science! Physics! Animation magic! Technology is amazing!",
            "Pants shopping. Your panda's been exposed long enough. Time for some goddamn trousers. Dignity restored."
        ]
    },
    'closet_jackets': {
        'normal': [
            "Browse jackets, hoodies, and coats",
            "View your collection of outerwear",
            "Jackets with sleeves that move with arm animations",
        ],
        'vulgar': [
            "Jackets. Because pandas get cold. Probably. Maybe. I don't know panda biology. But they look cool in jackets.",
            "Outerwear for your bear. Hoodies, coats, the works. Layer up. Fashion layers. Warmth layers. Style layers.",
            "Layer up! Sleeves move with the arms. Fancy, right? Animation technology. Physics simulation. Expensive shit.",
            "Jacket section. Cool panda vibes incoming. Leather jacket? Yes. Bomber jacket? Hell yes. Denim? Always."
        ]
    },
    'closet_dresses': {
        'normal': [
            "Browse dresses, robes, and gowns",
            "View your collection of dresses and robes",
            "Elegant garments that flow from neck to below the body",
        ],
        'vulgar': [
            "Dresses and robes. Fancy bear time! Elegance. Class. Sophistication. Your panda at the Met Gala.",
            "Flowing garments for the classy panda. Majestic. Regal. Probably uncomfortable but beautiful.",
            "Dress-up time. Your panda is red-carpet ready. Paparazzi optional. Glamour mandatory.",
            "Gowns and robes. Panda couture at its finest. High fashion. Low function. Maximum style."
        ]
    },
    'closet_full_outfits': {
        'normal': [
            "Browse full-body outfits and costumes",
            "View complete outfit sets that cover the entire body",
            "Full costumes with torso, legs, and sleeve coverage",
        ],
        'vulgar': [
            "Full body costumes. Total panda transformation. Halloween every day. Cosplay central. Identity crisis optional.",
            "Complete outfits. One-stop shopping for bear fashion. Everything matched. Coordinated. Professional level lazy.",
            "Full suit mode. Torso, legs, sleeves — the whole deal. Complete package. No mix-and-match. All or nothing.",
            "Costume shop. Your panda becomes someone else entirely. Identity theft but fashionable. And legal."
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
            "Language picker. Sprechen sie panda? Parlez-vous ours? ¿Hablas oso? Universal panda. Multilingual magic.",
            "Change language. Won't fix your grammar though. Or spelling. Or life choices. Just the interface language.",
            "International mode. Pick a language, any language. Global panda. Worldwide texture sorting. No borders.",
            "Language selector. For the worldly panda enthusiast. Cultured. Sophisticated. Probably studied abroad."
        ]
    },
    'ui_font_size': {
        'normal': [
            "Adjust the size of text throughout the application",
            "Make text larger or smaller for better readability",
            "Change the font size for all UI elements",
        ],
        'vulgar': [
            "Font size. For people who refuse to wear glasses. Stubborn and squinting. Make it bigger. Your eyes will thank you.",
            "Make text bigger or smaller. We won't judge your eyes. Okay we'll judge a little. But mostly support.",
            "Text size slider. From 'ant writing' to 'billboard'. Full spectrum. Microscopic to macroscopic.",
            "Font size. Squint less, enjoy more. Life's too short for eye strain. Make that text thicc."
        ]
    },
    'ui_animations': {
        'normal': [
            "Enable or disable UI animations and transitions",
            "Toggle smooth animation effects in the interface",
            "Control whether the UI uses animated transitions",
        ],
        'vulgar': [
            "Toggle animations. Smooth or instant. Your call. Butter smooth or lightning fast. Performance vs. aesthetics.",
            "UI animations on or off. Performance vs. pretty. Choose your priority. Speed or beauty. Both valid.",
            "Animation switch. For the impatient. And people with potato computers. No judgment. We understand.",
            "Smooth transitions toggle. Fancy or fast? Can't have both. Well, you can. But sometimes you can't. It's complicated."
        ]
    },
    'ui_transparency': {
        'normal': [
            "Adjust the window transparency level",
            "Make the application window more or less transparent",
            "Control the opacity of the application window",
        ],
        'vulgar': [
            "Window transparency. See-through panda time. Ghost mode. Spectral sorting. Ethereal file management.",
            "Opacity slider. From solid to ghost mode. Visible to invisible. Matter to spirit. Physics optional.",
            "Make the window transparent. Stealth sorting. Ninja mode. Covert operations. Mission Impossible theme plays.",
            "Transparency control. X-ray vision for your desktop. See through the window. Literally. Not metaphorically."
        ]
    },
    'ui_compact_mode': {
        'normal': [
            "Switch to a compact layout with smaller panels",
            "Use a condensed view to save screen space",
            "Enable compact mode for a more efficient layout",
        ],
        'vulgar': [
            "Compact mode. Squeeze everything smaller. Tetris but for UI elements. Efficiency maximized.",
            "Small layout for tiny screens and big dreams. Your laptop is small. Your ambitions are not. Balance achieved.",
            "Compact view. More room for activities! Step Brothers reference. Classic. Tight spaces. Maximum utility.",
            "Efficiency mode. Less padding, more action. Dense information. Compressed UI. Maximum productivity per pixel."
        ]
    },
    'ui_auto_save': {
        'normal': [
            "Automatically save settings when changes are made",
            "Enable automatic saving of preferences",
            "Settings are saved without manual intervention",
        ],
        'vulgar': [
            "Auto-save. Because you'll forget to save. We know. We've tracked your behavior. The data doesn't lie.",
            "Automatic saving. One less thing to worry about. Mental load reduced. Cognitive burden lightened. Brain thanked.",
            "Set it and forget it. Settings save themselves. Ron Popeil would be proud. Infomercial energy.",
            "Auto-save toggle. Manual saving is for cavemen. And people who like losing work. Progress is automatic now."
        ]
    },
    'ui_confirm_exit': {
        'normal': [
            "Ask for confirmation before closing the application",
            "Show a dialog when you try to exit the app",
            "Prevent accidental exits with a confirmation prompt",
        ],
        'vulgar': [
            "Exit confirmation. The app clings to you like a needy ex. 'Are you sure you want to leave?' Yes. No. Maybe. Complicated.",
            "'Are you sure?' dialog. For the indecisive among us. Second-guessing is a lifestyle. Embrace it.",
            "Prevent rage-quitting by accident. You're welcome. Your 'X' key is dangerous. We're protecting you from yourself.",
            "Exit safety net. Because misclicks are embarrassing. And permanent. And regrettable. Triple-check everything."
        ]
    },
    'ui_startup_tab': {
        'normal': [
            "Choose which tab opens when the app starts",
            "Set your preferred starting tab",
            "Select the default tab shown on application launch",
        ],
        'vulgar': [
            "Startup tab. Skip the intro, go straight to work. Efficiency! No time for pleasantries. Business mode activated.",
            "Pick which tab loads first. First impressions matter. Set the tone. Start strong. End stronger. Middle is whatever.",
            "Default tab selector. Speed-run your workflow. Any% no tutorial glitch. Gotta go fast. Sonic approved.",
            "Launch tab. Because clicking twice is unacceptable. Time is money. Money is power. Power is pizza. Save clicks."
        ]
    },
    'panda_name': {
        'normal': [
            "Set a custom name for your panda companion",
            "Give your panda a personalized name",
            "Type a name for your panda — it appears in messages",
        ],
        'vulgar': [
            "Name your panda. 'Sir Chomps-a-Lot' is taken. So is 'Bamboo Bandit'. And 'Fuzzy McFuzzface'. Be original, damn it.",
            "Panda naming ceremony. Choose wisely. Or not. Names are permanent. Like tattoos but less painful and more digital.",
            "Type a name. Your bear deserves an identity. Something better than 'Panda_001'. Show some creativity. Or don't. Whatever.",
            "Name your virtual bear. This is peak entertainment. This is what we've come to. This is modern life. Accept it."
        ]
    },
    'panda_gender': {
        'normal': [
            "Choose your panda's gender identity",
            "Set the gender for your panda companion",
            "Select a gender — affects pronouns in speech bubbles",
        ],
        'vulgar': [
            "Panda gender. They/them is valid for bears too. Inclusive pandas. Progressive wildlife. 21st century ursine representation.",
            "Gender selection. Progressive pandas unite! LGBTQ+ friendly bears. Rainbow pandas. Love is love. Bamboo is bamboo.",
            "Pick your bear's identity. We don't judge. Okay we judge the outfit choices. But not the gender. That's sacred.",
            "Gender picker. It's 2024, even bears get to choose. Gender is a construct. Pandas transcend constructs. Be free, bear."
        ]
    },
    'panda_auto_walk': {
        'normal': [
            "Enable or disable automatic panda walking",
            "Let your panda wander around on its own",
            "Toggle autonomous panda movement",
        ],
        'vulgar': [
            "Auto-walk. Your panda is a free spirit. Can't be caged. Won't be tamed. Wanderlust incarnate. Jack Kerouac but fuzzy.",
            "Let the bear roam. Free-range panda mode. Organic. Grass-fed. Ethically wandering. Farm-to-table file sorting.",
            "Walking toggle. Restless bear syndrome. Can't sit still. ADHD panda. Gotta move. Always moving. Motion is life.",
            "Your panda walks on its own. Deal with it. Independent. Autonomous. Free-thinking. You can't control everything. Learn to let go."
        ]
    },
    'panda_speech_bubbles': {
        'normal': [
            "Show or hide speech bubbles above the panda",
            "Toggle text bubbles for panda commentary",
            "Enable speech bubbles for panda messages",
        ],
        'vulgar': [
            "Speech bubbles. Your panda never shuts up. Constant commentary. Endless opinions. Like Twitter but furrier.",
            "Toggle commentary. The bear has opinions. Strong opinions. Wrong opinions. But opinions nonetheless.",
            "Text bubbles on or off. Silence is golden. Sometimes. Other times it's just awkward. Your call.",
            "Show/hide the panda's hot takes. Unpopular opinions. Controversial statements. Panda punditry. Bear broadcast."
        ]
    },
    'panda_idle_animations': {
        'normal': [
            "Enable or disable idle animations",
            "Toggle small animations when the panda is idle",
            "Your panda stretches and yawns when not interacting",
        ],
        'vulgar': [
            "Idle animations. Your panda does cute stuff when bored. Stretches. Yawns. Exists adorably. Peak performance.",
            "Watch your bear yawn and stretch. Riveting content. Better than cable. Cheaper than Netflix. Free entertainment.",
            "Idle mode animations. Because pandas need hobbies. Can't just stand there. Must move. Must exist cutely.",
            "Toggle idle animations. Less movement, less distraction. More productivity. Less adorable bear stretching. Your loss."
        ]
    },
    'panda_drag_enabled': {
        'normal': [
            "Allow dragging the panda around the screen",
            "Enable click-and-drag panda movement",
            "Toggle the ability to pick up and move your panda",
        ],
        'vulgar': [
            "Drag mode. Yeet the panda across the screen. Physics optional. Ethics questionable. Fun guaranteed.",
            "Pick up and fling your bear. Totally ethical. PETA won't find out. Probably. It's digital anyway. No real pandas harmed.",
            "Drag toggle. Grab, move, release. Repeat. It's therapeutic. Like bubble wrap but with endangered species. Wait no—",
            "Enable dragging. Your panda is now a cursor toy. Interactive. Moveable. Slightly resentful but cooperative."
        ]
    },
    'perf_thread_count': {
        'normal': [
            "Number of threads used for texture processing",
            "Control how many parallel threads are used",
            "Adjust thread count for processing performance",
        ],
        'vulgar': [
            "Thread count. More threads = faster. Maybe hotter CPU. Trade speed for heat. Your cooling system's final boss.",
            "How many threads to throw at the problem. Brute force approach. Computational bludgeoning. Science!",
            "Processing threads. Don't go nuclear. Your CPU has limits. Respect them. Or don't. Fire extinguisher recommended.",
            "Thread slider. Your CPU's workout intensity. Gym for processors. Gains for performance. Sweat is thermal paste."
        ]
    },
    'perf_cache_size': {
        'normal': [
            "Maximum memory used for caching processed textures",
            "Larger cache means faster repeated operations",
            "Control memory allocation for texture caching",
        ],
        'vulgar': [
            "Cache size. Feed the RAM monster. More memory nom nom. Hungry for bytes. Thirsty for performance.",
            "Memory cache slider. More RAM, more speed, more heat. The eternal triangle. Pick two. Can't have all three.",
            "Cache allocation. Greedy or conservative. Pick one. Maximize performance or minimize risk. Gambler or coward?",
            "How much memory to hoard. Digital dragon vibes. Smaug but for RAM. Sitting on a pile of cached data. Majestic."
        ]
    },
    'profile_save': {
        'normal': [
            "Save your current settings as a profile",
            "Create a named settings snapshot",
            "Store your configuration for later use",
        ],
        'vulgar': [
            "Save profile. Insurance against future stupidity. And present stupidity. And past stupidity that might repeat.",
            "Create a settings backup. You'll need it. Trust me. Future you is clumsy. Present you knows this. Plan accordingly.",
            "Save now. You know you'll mess something up later. It's inevitable. Like death and taxes. But more annoying.",
            "Profile snapshot. Future you will thank present you. Possibly with tears of joy. Or relief. Probably relief."
        ]
    },
    'profile_load': {
        'normal': [
            "Load a previously saved settings profile",
            "Restore settings from a saved profile",
            "Switch to a different saved configuration",
        ],
        'vulgar': [
            "Load profile. Time travel for settings. Back to the Future but for configuration. Doc Brown would approve.",
            "Restore a saved config. Undo your disasters. Reset the timeline. Butterfly effect but less dramatic and more practical.",
            "Load a profile. Instant settings swap! Configuration shapeshifting. Transformer settings. Settings in disguise.",
            "Switch configs. For the indecisive. Multiple personality disorder but for preferences. No therapy required."
        ]
    },
    'pause_button': {
        'normal': [
            "Pause the sorting operation temporarily",
            "Temporarily halt the current sorting process",
            "Freeze the sorting progress to resume later",
            "Put the sorting operation on hold",
        ],
        'vulgar': [
            "Hit pause, you indecisive bastard. Second thoughts? Valid. Cold feet? Understandable. Pause button? Right here.",
            "Take a damn breather. Sorting can wait. Your anxiety can't. Deep breaths. In through the nose. Out through the mouth.",
            "Pause this shit. Go grab a coffee or something. Bathroom break. Snack break. Existential crisis break. Your choice.",
            "Hold the hell up. We're pausing. Freeze frame. Record scratch. 'You're probably wondering how I got here.'",
            "Freeze! Not you, the sorting process, you idiot. The computer. Not your body. Don't actually freeze. That'd be weird."
        ]
    },
    'stop_button': {
        'normal': [
            "Stop the sorting operation completely",
            "Cancel the current sorting process",
            "Terminate the sorting operation in progress",
            "Halt all sorting activity immediately",
        ],
        'vulgar': [
            "ABORT! ABORT! Kill the sorting process! Red alert! All hands on deck! Abandon ship! This is not a drill!",
            "Stop this shit right now. Full stop. Period. End of sentence. No more sorting. Done. Finished. Kaput.",
            "Pull the damn emergency brake on sorting. Screeching halt. Rubber burning. Dramatic stop. Michael Bay explosion optional.",
            "Nuke the sorting operation from orbit. It's the only way to be sure. Aliens reference. Classic. Ripley approved.",
            "Stop everything. Panic button activated, you disaster. Chaos mode. Emergency protocols. DEFCON 1. Your fault."
        ]
    },
    'sort_mode_menu': {
        'normal': [
            "Select the sorting mode: automatic, manual, or suggested",
            "Choose how textures are sorted and categorized",
            "Pick the sorting approach that suits your workflow",
            "Switch between different sorting strategies",
        ],
        'vulgar': [
            "Pick a sort mode. Auto if you're lazy, manual if you're a control freak. No judgment. Okay, some judgment. Mostly about manual.",
            "Sorting strategy selector. Choose your damn destiny. Your path. Your journey. Your organizational philosophy.",
            "Auto, manual, or suggested. Like dating preferences but for textures. Swipe right on auto. Left on manual. Super like on suggested.",
            "How do you want your shit sorted? Pick one already. Decision paralysis is real. But this isn't that important. Just pick.",
            "Sort mode menu. Because apparently 'just sort it' wasn't specific enough. You need options. Fine. Here's your damn options."
        ]
    },
    'extract_archives': {
        'normal': [
            "Extract textures from archive files (ZIP, 7Z, RAR, TAR.GZ)",
            "Unpack compressed archives to access textures inside",
            "Automatically detect and extract archived texture files",
            "Enable extraction of textures from compressed containers",
        ],
        'vulgar': [
            "Unzip that shit. ZIP, 7Z, RAR, whatever you've compressed. All archives accepted. No discrimination.",
            "Extract from archives. Because your textures are trapped in zip jail. Free them. Liberation time. Texture freedom.",
            "Free your damn textures from their compressed prison cells. Break the chains. Smash the ZIP walls. Revolution!",
            "Archive extraction. Liberating files since forever, you lazy ass. Digital freedom fighter. Texture emancipator.",
            "Dig through compressed crap and find the textures. Automatically. Like a truffle pig but for files. And automated."
        ]
    },
    'compress_output': {
        'normal': [
            "Compress the sorted output into a ZIP file",
            "Create a ZIP archive of the organized textures",
            "Bundle the sorted results into a compressed file",
            "Package output into a compressed archive for sharing",
        ],
        'vulgar': [
            "Squish everything into a ZIP. Compression magic, baby. Make it smaller. Physics? Don't know her. Just works.",
            "Zip it up. Not your mouth, the output folder. Though zipper your mouth might not be bad advice either.",
            "Compress output. Because disk space isn't free, you hoarder. Storage costs money. Compression saves money. Math!",
            "Make a ZIP file. Perfect for sharing your sorted shit. Email-friendly. Upload-ready. Shareable.",
            "Pack it all up into a tidy little compressed ball of textures. Neat. Organized. Compressed. Beautiful."
        ]
    },
    'convert_from_format': {
        'normal': [
            "Select the source format for texture conversion",
            "Choose which texture format to convert from",
            "Set the input format for the conversion process",
            "Pick the original format of your texture files",
        ],
        'vulgar': [
            "What format are your textures in? Pick the source, genius. This isn't guessing time. Tell me what you've got.",
            "Source format. Tell me what format your crap is currently in. PNG? DDS? Ancient hieroglyphics? Specify.",
            "Input format selector. What the hell am I converting FROM? The before. The origin. The starting point.",
            "From-format. Step one of unfucking your texture formats. Every journey starts somewhere. This is somewhere.",
            "Original format. The 'before' in this before-and-after makeover. The ugly duckling stage. Pre-transformation."
        ]
    },
    'convert_to_format': {
        'normal': [
            "Select the target format for texture conversion",
            "Choose which format to convert textures to",
            "Set the desired output format for conversion",
            "Pick the format you want your textures converted to",
        ],
        'vulgar': [
            "What format do you want? Pick the target, smartass. The destination. The goal. The promised land of formats.",
            "Target format. What should your textures become? Choose wisely. This determines their entire future.",
            "Output format selector. What the hell am I converting TO? The after. The destination. The end result.",
            "To-format. Step two of unfucking your texture formats. Almost there. One more choice. Make it count.",
            "Destination format. The 'after' in this glow-up. The swan stage. The final form. Peak texture evolution."
        ]
    },
    'convert_recursive': {
        'normal': [
            "Convert files in subdirectories recursively",
            "Include textures in all subfolders for conversion",
            "Process nested directory structures during conversion",
            "Enable recursive conversion through folder hierarchies",
        ],
        'vulgar': [
            "Go deep. Convert files in ALL subfolders, you thorough bastard. No stone unturned. No folder unsearched.",
            "Recursive mode. Dig through every damn subdirectory. Folders within folders. Inception style. Dream deeper.",
            "Search every nook and cranny. No folder left behind! Every subfolder. Every nested directory. Everything.",
            "Recursion! Folders within folders within folders. We'll find 'em all. Matryoshka folder searching. Russian doll directories.",
            "Like a mole digging through directories. Every subfolder gets hit. Tunnel vision. Directory spelunking. Cave exploration but files."
        ]
    },
    'convert_keep_original': {
        'normal': [
            "Keep original files after conversion",
            "Preserve source files alongside converted output",
            "Don't delete originals when converting textures",
            "Maintain original texture files as backup",
        ],
        'vulgar': [
            "Keep the originals. Because you don't trust anything, do you? Trust issues. Valid. Backups save lives. And files.",
            "Don't delete the source files. Safety first, you paranoid genius. Paranoia is self-preservation. Smart move.",
            "Backup mode: keep your old crap AND the new crap. Double the crap! Twice the storage. Zero regrets.",
            "Preserve originals. Hoarding tendencies enabled. No judgment. Okay, some judgment. But mostly respect. Digital pack rat life.",
            "Keep both versions. Your disk space is crying but whatever. Hard drives are cheap. Data loss is expensive. Math works out."
        ]
    },
    'profile_new': {
        'normal': [
            "Create a new game organization profile",
            "Set up a fresh profile for a different game",
            "Start a new configuration profile from scratch",
            "Add a new profile to your collection",
        ],
        'vulgar': [
            "New profile! Start fresh, you beautiful disaster. Clean slate. Fresh beginning. New mistakes incoming!",
            "Create another profile. As if the 50 you have aren't enough. Profile collector. Configuration hoarder. We see you.",
            "Fresh profile. Clean slate. New mistakes to make! Exciting! The circle of life. The wheel of configuration.",
            "Brand new profile. Because starting over is always an option. Phoenix rising. From the ashes of your last config.",
            "Make a new profile. Your collection of configs grows ever larger. Like Pokemon but for settings. Gotta configure 'em all."
        ]
    },
    'settings_perf_tab': {
        'normal': [
            "Performance settings: threads, cache, and batch size",
            "Adjust performance-related configuration options",
            "Fine-tune processing speed and resource usage",
            "Configure performance parameters for optimal speed",
        ],
        'vulgar': [
            "Performance settings. Make it go brrr or save your CPU from meltdown. Speed or safety. Pick your priority.",
            "Speed tweaks. For when 'fast enough' just isn't fast enough. Need for speed. Gotta go fast. Sonic energy.",
            "Performance tab. Overclock your texture sorting, you nerd. Push the limits. Break the sound barrier. Ludicrous speed!",
            "CPU settings. Thread counts and cache sizes. Nerd shit. Technical specifications. The good stuff. For nerds. By nerds.",
            "Perf settings. Because you want everything yesterday. Impatient bastard. Instant gratification culture. We get it."
        ]
    },
    'settings_appearance_tab': {
        'normal': [
            "Appearance settings: themes, fonts, and visual options",
            "Customize the look and feel of the application",
            "Adjust visual preferences like themes and font sizes",
            "Configure UI appearance and display settings",
        ],
        'vulgar': [
            "Make it pretty. Or ugly. Your call, interior decorator. Feng shui for software. Digital aesthetics. Pixel perfection.",
            "Appearance tab. Because functionality alone is too boring for you. Form AND function. Why not both? Greedy but fair.",
            "Visual settings. Theme it, font it, fancy it up. Customize everything. Every pixel. Every color. Your canvas awaits.",
            "Look and feel settings. Lipstick on a pig? Maybe. But a FABULOUS pig. Confidence is key. Rock that pink.",
            "UI beautification zone. Make those pixels dance, you vain bastard. Visual flair. Style points. Aesthetic excellence."
        ]
    },
    'settings_controls_tab': {
        'normal': [
            "Controls settings: keyboard shortcuts and input options",
            "Configure keyboard bindings and control preferences",
            "Customize hotkeys and control schemes",
            "Set up your preferred keyboard shortcuts",
        ],
        'vulgar': [
            "Keyboard shortcuts. For people who think mice are for peasants. Elite input methods. Keyboard master race.",
            "Controls tab. Rebind keys like the power user you pretend to be. Fake it till you make it. Eventually you'll be good.",
            "Hotkey heaven. Ctrl+everything. Go wild, keyboard warrior. Every key combination. Maximum efficiency. Zero mouse touching.",
            "Key bindings. Because clicking is SO last century. This is 2024. We use keyboards like civilized people.",
            "Controls setup. Map every damn key to something. Even Caps Lock. Especially Caps Lock. That key needs a job."
        ]
    },
    'settings_files_tab': {
        'normal': [
            "File settings: default paths, formats, and file handling",
            "Configure file-related preferences and defaults",
            "Set default directories and file processing options",
            "Adjust how files are handled and organized",
        ],
        'vulgar': [
            "File settings. Tell the app where your crap lives. Directory coordinates. File addresses. Digital GPS.",
            "File handling prefs. Paths, formats, all that boring file shit. Necessary evil. Important but tedious.",
            "Where do files go? Where do they come from? Configure it here. Cotton-Eye Joe but for files. Ancient meme. Google it.",
            "File settings tab. For those who care about directory structures. Folder fetishists. Path purists. Organization enthusiasts.",
            "Path configurations. Because typing paths manually is for masochists. And people with too much time. And perfect memory. Not you."
        ]
    },
    'settings_ai_tab': {
        'normal': [
            "AI settings: vision models and automatic categorization",
            "Configure AI-powered texture analysis options",
            "Set up machine learning features for smart sorting",
            "Adjust AI model preferences for texture recognition",
        ],
        'vulgar': [
            "AI settings. Teaching a computer to look at textures. Welcome to the future. Skynet starts here. Just kidding. Mostly.",
            "Robot brain configuration. Make the AI smarter. Or dumber. Your call. Play god. Tweak the neural networks.",
            "AI tab. Skynet for texture sorting. Totally not concerning. Nothing could possibly go wrong. Famous last words.",
            "Machine learning settings. It's like training a dog, but nerdier. And with more math. And less poop. Usually.",
            "AI config. Let the robots handle it while you eat snacks. Automation nation. Robot workforce. Human laziness. Perfect synergy."
        ],
        'dumbed-down': [
            "This is where you tell the robot brain how to work!",
            "AI settings = robot helper settings. Change how the computer guesses stuff!",
            "The computer tries to be smart here. You pick HOW smart!",
        ]
    },
    'settings_system_tab': {
        'normal': [
            "System settings: updates, logging, and diagnostics",
            "Configure system-level application options",
            "Adjust system behavior, updates, and debug settings",
            "Manage system preferences and maintenance options",
        ],
        'vulgar': [
            "System settings. The 'under the hood' stuff for tech nerds. Engine room. Boiler room. The technical bowels.",
            "System tab. Logs, updates, diagnostics. Boring but important, dammit. Like vegetables. Hate them but need them.",
            "The engine room. Touch things carefully or everything explodes. Metaphorically. Probably. No guarantees.",
            "System config. For people who read error logs for fun. Nerds. Masochists. People with too much free time.",
            "Under-the-hood settings. Careful, there be dragons here. And segmentation faults. And mysterious crashes. Adventure!"
        ]
    },
    'tooltip_mode_normal': {
        'normal': [
            "Standard tooltips with clear, helpful descriptions",
            "Professional tooltip mode with informative text",
            "Regular tooltip style for everyday use",
            "Normal tooltips providing useful guidance",
        ],
        'vulgar': [
            "Boring normal mode. For the straights who can't handle spice. Vanilla. Plain. Safe. Corporate-approved.",
            "Normal tooltips. Vanilla. Plain. Like unseasoned chicken. Edible but forgettable. Functional but bland.",
            "Standard mode. Snooze fest but technically helpful. Information without personality. Facts without flair.",
            "Normal mode. For when you want help without the attitude. Professional. Polite. Personality-free zone.",
            "The boring option. Professional and dull as hell. Like a PowerPoint presentation. But helpful. Technically."
        ]
    },
    'tooltip_mode_dumbed_down': {
        'normal': [
            "Simplified tooltips for beginners and new users",
            "Easy-to-understand explanations for every feature",
            "Beginner-friendly tooltips with extra detail",
            "Tooltips written in simple, accessible language",
        ],
        'vulgar': [
            "Baby mode. Explains everything like you're five. No shame. Everyone starts somewhere. Learning is good. Growth is beautiful.",
            "Dumbed down mode. We don't judge your intelligence. Much. Okay maybe a little. But we support your journey. Mostly.",
            "ELI5 tooltips. Big words scary? This mode's for you. Small words. Simple concepts. Easy understanding. Brain happy.",
            "Beginner mode. Hand-holding included. Training wheels on. Stabilizers activated. You'll get there. Eventually.",
            "Simple mode. Because reading is hard sometimes. We get it. Comprehension takes energy. Your brain is tired. Rest mode engaged."
        ]
    },
    'tooltip_mode_vulgar': {
        'normal': [
            "Unhinged Panda mode: sarcastic, funny, and explicit tooltips",
            "Adult-only tooltip mode with colorful language",
            "Humorous and irreverent tooltip style with profanity",
            "The unfiltered, no-holds-barred tooltip experience",
        ],
        'vulgar': [
            "You're already here, you beautiful degenerate. Welcome home. This is your natural habitat. Embrace it.",
            "Unhinged mode. The ONLY mode. Why would you pick anything else? Everything else is a lie. This is truth.",
            "This mode. The best mode. Fuck the other options. They're weak. This is strong. Choose strength.",
            "Welcome to the party, asshole. Best tooltips in the game. The others can't compete. We're the champions.",
            "The correct choice. Everything else is a waste of screen space. And time. And potential. You chose well."
        ]
    },
    'shop_balance': {
        'normal': [
            "Your current Bamboo Bucks balance",
            "Shows how many Bamboo Bucks you have to spend",
            "Displays your available currency for shop purchases",
            "Your wallet balance in Bamboo Bucks",
        ],
        'vulgar': [
            "Your broke-ass balance. Time to grind more, cheapskate. Poverty is temporary. Bamboo Bucks are forever. Well, digital.",
            "Bamboo Bucks. Your virtual wallet. Probably empty. Like your real wallet. But more depressing because pixels.",
            "How much cash you got? Spoiler: never enough. The eternal struggle. More money, more problems. No money, more problems.",
            "Your balance. Try not to cry at the number. It's okay. We've all been there. Financial judgment-free zone.",
            "Bamboo Bucks count. Jeff Bezos you are not. Space travel not included. Just texture sorting. And crushing debt."
        ]
    },
    'shop_level': {
        'normal': [
            "Your current user level",
            "Shows your level and experience progress",
            "Displays your current rank and leveling status",
            "Your user level determines shop item availability",
        ],
        'vulgar': [
            "Your level. Higher = more stuff to buy. Grind harder. No pain, no gain. Level up or shut up.",
            "Level indicator. Flex on the newbies with your big number. Size matters. In levels. Definitely in levels.",
            "Your rank. Still a noob? Keep sorting, peasant. Git gud. Level up. Become legendary. Or stay mediocre. Your call.",
            "Level display. Size doesn't matter... except here it does. Big level energy. Flex those digits.",
            "Your XP level. Level up or forever be locked out of cool shit. The game is rigged. Play anyway."
        ]
    },
    'inventory_animations': {
        'normal': [
            "Play animations on your panda companion",
            "Use animation items to trigger panda actions",
            "Activate collected animations for your panda",
            "Browse and play panda animation items",
        ],
        'vulgar': [
            "Make the panda dance. Or wave. Or whatever these animations do. Entertainment value questionable. Cute factor maximum.",
            "Play animations. Watch your bear do stupid tricks. Like a circus but smaller. And digital. And free.",
            "Animation items. Because your panda needs to show off. Talent show time. America's Got Panda Talent.",
            "Trigger panda animations. Free entertainment for the easily amused. You're easily amused. We know. No judgment.",
            "Panda tricks! Teach your virtual bear to do things. Badly. With enthusiasm. Participation trophy guaranteed."
        ]
    },
    'popout_button': {
        'normal': [
            "Pop this tab out into a separate window",
            "Detach this tab into its own floating window",
            "Open this tab in an independent window",
            "Undock this tab for multi-monitor use",
        ],
        'vulgar': [
            "Pop it out! Like a damn zit but for UI tabs. Gross analogy. Functional result. Success.",
            "Detach this tab. Freedom for windows! Viva la revolución! Liberty, equality, fraternity, separate windows!",
            "Separate window. For multi-monitor flex lords. Look at you with your multiple screens. Living the dream.",
            "Pop out this tab. Because one window is never enough for you. Window collector. Screen hoarder. Power user.",
            "Undock it. Let this tab spread its wings and fly, dammit. Free bird. Lynyrd Skynyrd plays in distance."
        ]
    },
    'minigames_tab': {
        'normal': [
            "Play mini-games to earn rewards and have fun",
            "Access available mini-games for extra rewards",
            "Open the mini-games section to play and earn currency",
            "Choose from a selection of mini-games to enjoy",
        ],
        'vulgar': [
            "Mini-games! Because sorting textures alone is boring as hell. Variety is the spice of life. Add some fucking spice.",
            "Play games. Win prizes. Waste time. The holy trinity. The trifecta of productivity loss. Worth it.",
            "Game time, baby! Earn Bamboo Bucks while procrastinating. Productive procrastination. The best kind.",
            "Mini-games tab. The 'I should be working' section. But you're not. You're here. Playing games. No regrets.",
            "Games! Because you'd rather play than sort textures, you slacker. Priorities. You have them. They're questionable."
        ]
    },
    'closet_appearance': {
        'normal': [
            "Your panda's current outfit summary",
            "See what your panda is currently wearing",
            "View the full list of equipped items on your panda",
            "Check your panda's current clothing and accessories",
        ],
        'vulgar': [
            "Your panda's look. Rate it out of 10. I dare you. Double dare you. Be honest. The panda can take it.",
            "Current outfit. Is it fashion? Is it a disaster? You decide. Fashion is subjective. Taste is personal. Yours is questionable.",
            "What your bear is wearing. Hopefully not a crime against fashion. Fashion police have been notified. Awaiting backup.",
            "Panda's current drip. Or lack thereof. Drip check failed. Try again. Better luck next outfit.",
            "Outfit check! Looking good? Looking terrible? Who cares, it's a panda. Pandas are always cute. Even in that."
        ]
    },
    'closet_header': {
        'normal': [
            "Dress up your panda with outfits and accessories",
            "Customize your panda's look using your wardrobe",
            "Manage your panda's clothing and equipped items",
            "Open the closet to style your panda companion",
        ],
        'vulgar': [
            "The closet. Where fashion dreams come true. Or die horribly. Usually both. In that order. Welcome.",
            "Wardrobe management. Your panda has more clothes than you. And probably better taste. Sad but true.",
            "Dress-up time! Your panda's about to look fabulous. Maybe. Possibly. Hopefully. No guarantees.",
            "Closet header. Welcome to Panda's Next Top Model. Tyra Banks not included. Sass definitely included.",
            "Fashion central. Make your bear look less naked. Or don't. Nudist panda colony also valid. Live your truth."
        ]
    },
    'achievement_progress': {
        'normal': [
            "Track your progress toward completing this achievement",
            "See how close you are to finishing this achievement",
            "View the completion percentage for this goal",
            "Check how much remains before this achievement unlocks",
        ],
        'vulgar': [
            "Progress bar. Watch it fill up. Riveting entertainment. Better than cable. Cheaper than Netflix. More boring than both.",
            "How close you are. Spoiler: probably not close enough. Keep grinding. The struggle is real. The progress is slow.",
            "Achievement progress. Almost there... or not even close. Schrodinger's achievement. Both complete and incomplete.",
            "Progress tracker. For the impatient obsessive types. That's you. You're checking this constantly. We know.",
            "Completion percentage. Like a loading screen but for achievements. Watching. Waiting. Hoping. Living."
        ]
    },
    'upscale_button': {
        'normal': [
            "Start batch upscaling all images in the input folder",
            "Begin the upscaling process for your selected textures",
            "Click to upscale all queued images at the chosen scale factor",
            "Launch the batch upscale operation on your texture files",
            "Process all images in the input folder using current upscale settings",
            "Run the upscaler on every texture in the selected directory",
        ],
        'dumbed-down': [
            "Press this big button to make all your small pictures bigger!",
            "This starts making your textures larger — just click and wait!",
            "Click here to begin! It'll make all your images bigger automatically.",
            "The GO button! It takes your tiny images and makes them big.",
            "Hit this to start processing. Your pictures will get bigger!",
            "Ready to upscale? This button kicks everything off for you.",
        ],
        'vulgar': [
            "SMASH this button to make your tiny textures less embarrassingly small.",
            "Hit it! Time to blow up those pixels like a panda sitting on bubblewrap.",
            "Upscale button: because your textures called and they want more pixels.",
            "Click to embiggen. Yes, embiggen. The panda said it, deal with it.",
            "Big green UPSCALE button. You know what it does. Just press it.",
            "Start batch upscaling. Your GPU is about to earn its keep.",
            "Make textures bigger. That's the whole job description of this button.",
            "Click to start the pixel multiplication party. Confetti not included.",
            "Upscale everything! The panda believes in your texture enhancement journey.",
            "Enlarge those bad boys. The panda supports all forms of pixel growth.",
            "🔍 UPSCALE 🔍 — It says it right on the button, what more do you need?",
            "Time to make those textures thicc. Click upscale. Now."
        ]
    },
    'upscale_input': {
        'normal': [
            "Select the input folder containing images to upscale",
            "Browse for the upscaler input directory with your source textures",
            "Choose which folder of source textures to upscale",
            "Pick the input directory with images you want to enlarge",
            "Set the source folder where your original textures are stored",
            "Point to the folder containing the images you want upscaled",
        ],
        'dumbed-down': [
            "Click to pick the folder where your pictures are stored.",
            "Choose the folder with the images you want to make bigger.",
            "This lets you find and select the folder with your textures.",
            "Browse your computer to find where your images live.",
            "Pick the folder! The one with the pictures you want upscaled.",
            "Find the folder on your computer that has the images inside it.",
        ],
        'vulgar': [
            "Point me to the sad little textures that need a growth spurt.",
            "Select the folder of shame — er, I mean 'source images.'",
            "Where are the tiny textures? Show the panda the folder where they hide.",
            "Pick an input folder. Any folder. As long as it has pictures in it, genius.",
            "Input folder for upscaling. The panda needs to see the before pics.",
            "Browse for the source folder. These textures about to get SWOLE.",
            "Select your input directory. The pixelated victims — I mean, textures.",
            "Show me the INPUT folder. The panda promises to make them bigger. And better.",
        ]
    },
    'upscale_zip_input': {
        'normal': [
            "Select a ZIP archive containing images to upscale",
            "Browse for a compressed archive of source textures",
            "Choose a ZIP file with textures to enlarge",
            "Pick a ZIP archive to extract and upscale its images",
            "Load a compressed file of textures for batch upscaling",
            "Open a ZIP containing the textures you want to process",
        ],
        'dumbed-down': [
            "Got a ZIP file with pictures inside? Click here to pick it!",
            "If your images are stored in a .zip file, use this button.",
            "Click to select a ZIP archive — it'll unpack and upscale everything inside.",
            "Have a compressed file of textures? This button opens it for you.",
            "Pick a .zip file and the tool will find all the images inside it.",
            "Use this if your textures are zipped up in one file.",
        ],
        'vulgar': [
            "Got a ZIP? Unzip it with your mind. Just kidding, click the damn button.",
            "Compressed textures? The panda will UNZIP them and make them HUGE.",
            "ZIP file full of sad small textures? Let's liberate those pixels!",
            "Select a ZIP. We'll rip it open like a panda with a Christmas present.",
            "Upload your ZIP of shame. The panda won't judge. Much.",
            "ZIP archive? The panda will extract those textures faster than you can say 'decompression.'",
            "Got a ZIP? Hand it over. The panda's got magic unzipping paws.",
            "Select your ZIP file. These compressed textures are about to get the VIP treatment.",
        ]
    },
    'upscale_output': {
        'normal': [
            "Choose the destination folder for upscaled images",
            "Select where to save the processed upscaled textures",
            "Pick an output directory for the enlarged images",
            "Set the folder where upscaled results will be saved",
            "Browse for the output location to store finished textures",
            "Specify the target directory for all upscaled output files",
        ],
        'dumbed-down': [
            "Pick where you want the bigger images to be saved on your computer.",
            "Choose a folder to save the upscaled results into.",
            "Click to select the destination — where the finished images go!",
            "This sets where on your computer the new bigger images get stored.",
            "Select the save location. Your upscaled pictures will end up there.",
            "Pick an output folder — that's where your enlarged images will be.",
        ],
        'vulgar': [
            "Where do you want these MAGNIFICENT upscaled textures deposited?",
            "Pick an output folder. The panda needs to know where to dump the goods.",
            "Select the output. Where should we put these absolute units of textures?",
            "Choose a folder for the results. Preferably not your Desktop. AGAIN.",
            "Output directory. Where the magic happens. Well, where it LANDS anyway.",
            "Browse for output folder. These upscaled textures need a home!",
            "Where to save? Pick wisely. The panda only delivers once.",
            "Select output directory. Your newly THICC textures await their destination.",
        ]
    },
    'upscale_factor': {
        'normal': [
            "Choose the upscale multiplier (2x, 4x, 8x, etc.)",
            "Select how much to enlarge each texture",
            "Pick the scale factor for output resolution",
            "Set the magnification level for upscaling",
            "Choose the resolution multiplier applied to each image",
            "Specify how many times larger the output should be",
        ],
        'dumbed-down': [
            "Pick how much bigger to make your images — 2x means twice as big!",
            "This number says how much to enlarge. 4x = four times bigger!",
            "Choose the zoom level: 2x doubles it, 4x quadruples it, and so on.",
            "How big do you want them? 2x is double, 8x is EIGHT times larger!",
            "Select the multiplier. Higher number = bigger output image.",
            "This controls the size increase. Start with 2x or 4x if unsure!",
        ],
        'vulgar': [
            "How THICC do you want these textures? 2x? 4x? GO BIG OR GO HOME!",
            "Scale factor! 2x is baby mode. 8x is where the real chaos begins.",
            "Pick a multiplier. 4x is the sweet spot. 16x is pure madness.",
            "How much bigger? The panda recommends 4x. The panda also eats bamboo for breakfast.",
            "Choose your upscale power level. 8x? Over 9000 pixels? Go wild.",
            "Scale factor selection. The bigger the number, the longer you wait. Choose wisely.",
            "2x? Boring. 4x? Reasonable. 16x? You absolute madlad.",
            "Select magnification. The panda dares you to try 16x. Do it. DO IT.",
        ]
    },
    'upscale_style': {
        'normal': [
            "Choose the resampling algorithm used for upscaling",
            "Select the interpolation method that determines output quality",
            "Pick the upscale filter — each produces different visual results",
            "Set the resampling style: Lanczos for sharpness, Bicubic for smoothness",
            "Choose how pixels are interpolated: affects sharpness, smoothness, and speed",
            "Select the upscaling method — determines the quality-speed tradeoff",
        ],
        'dumbed-down': [
            "This picks HOW the image gets made bigger. Lanczos = sharpest, Bilinear = fastest!",
            "Choose the method for enlarging. Each one looks a bit different — try them with preview!",
            "Pick a style! Lanczos is best for most things, Bicubic is smooth, Box is for pixel art.",
            "This controls quality vs speed. Lanczos = best quality, Bilinear = fastest.",
            "Select the magic recipe for upscaling. Preview to see which one you like!",
            "Different methods for making images bigger. Lanczos is usually the best bet!",
        ],
        'vulgar': [
            "Pick your poison: Lanczos is the fancy one. Nearest is the lazy one.",
            "Resampling filter! Lanczos: sharp. Bicubic: smooth. Box: pixel art vibes. Real-ESRGAN: AI flex.",
            "Choose your upscale style like you're choosing a weapon. Lanczos is the katana.",
            "Lanczos for sharpness, Bicubic for that buttery smooth look. The panda recommends Lanczos.",
            "Style selection: how do you want your pixels interpolated today, sir/madam?",
            "Pick the filter! Each one makes your textures look different. Try preview first, genius.",
            "Lanczos: chef's kiss. Bilinear: fast food. Box: retro vibes. Real-ESRGAN: BOUGIE.",
            "Select your resampling algorithm. Yeah, it's a big word. Just pick Lanczos.",
        ]
    },
    'upscale_format': {
        'normal': [
            "Choose the output file format for upscaled images",
            "Select which image format to save the upscaled textures in",
            "Pick the file type for output (PNG, BMP, TGA, JPEG, etc.)",
            "Set the export format — PNG for lossless, JPEG for smaller files",
            "Choose the output format: affects quality, file size, and compatibility",
            "Select the image format for saving processed textures",
        ],
        'dumbed-down': [
            "Pick what type of file to save as — PNG keeps quality, JPEG is smaller.",
            "Choose the file format. PNG is best for game textures!",
            "Select the save format. PNG = best quality, JPEG = small but lossy.",
            "What file type? TGA and PNG are great for games. JPEG loses some quality.",
            "Pick the output format. If unsure, PNG is always a safe choice!",
            "Choose how to save your images. PNG is recommended for most uses.",
        ],
        'vulgar': [
            "Pick your format. PNG is lossless and beautiful. JPEG is a war crime on textures.",
            "Output format! PNG = pristine. JPEG = pixel massacre. Choose wisely.",
            "File format time! The panda judges you if you pick JPEG for game textures.",
            "PNG, BMP, TGA, JPEG, WEBP... so many choices, so little time to screw up.",
            "Format selection: PNG for quality snobs, JPEG for file size misers.",
            "Choose format. The panda strongly suggests PNG. The panda always suggests PNG.",
            "Pick output format. JPEG for photos, PNG for everything else. Fight me.",
            "Select format. TGA is classic for games. PNG is chef's kiss. JPEG is... a choice.",
        ]
    },
    'upscale_alpha': {
        'normal': [
            "Keep the alpha channel (transparency) intact during upscaling",
            "Preserve transparent areas when enlarging RGBA images",
            "Maintain alpha transparency in the upscaled output",
            "Process alpha channel separately to prevent edge artifacts",
            "Ensure transparency data survives the upscaling process",
            "Keep RGBA mode with proper alpha handling during resize",
        ],
        'dumbed-down': [
            "Keep the see-through parts see-through! Don't lose your transparency.",
            "This keeps transparent areas transparent when making images bigger.",
            "If your image has see-through parts, check this to keep them!",
            "Preserve transparency! Without this, transparent parts might turn white.",
            "Check this box if your textures use transparency (most game textures do).",
            "Keeps the invisible parts invisible. Very important for game textures!",
        ],
        'vulgar': [
            "Keep alpha or your transparent textures become opaque nightmares. Your call.",
            "Preserve transparency. Unless you WANT white boxes around your sprites. Weirdo.",
            "Alpha preservation: ON. Because the panda refuses to let you ruin your textures.",
            "Check this unless you enjoy destroying perfectly good transparency data.",
            "Keep the alpha channel. The panda doesn't trust you to remember this on your own.",
            "Transparency preservation. Uncheck if you hate yourself and your game textures.",
            "RGBA alpha handling. Check this. Always. The panda is not asking.",
            "Preserve alpha or face the consequences of white-boxed sprites. You've been warned.",
        ]
    },
    'upscale_recursive': {
        'normal': [
            "Process images in subdirectories as well as the main folder",
            "Include all nested folders when scanning for images to upscale",
            "Recursively search subfolders for additional textures to process",
            "Upscale images found in all child directories of the input folder",
            "Enable deep directory scanning to find all images in nested folders",
            "Process the entire folder tree, not just the top-level directory",
        ],
        'dumbed-down': [
            "Check this to also process images inside folders-within-folders.",
            "This looks inside ALL subfolders too, not just the main folder.",
            "Got folders inside your folder? Check this to process everything!",
            "Makes the tool dig into ALL subfolders to find more images.",
            "Enable this to upscale images in nested directories too!",
            "Searches deep inside your folder structure for all images.",
        ],
        'vulgar': [
            "Check this to raid all subfolders. Leave no texture behind!",
            "Recursive mode: digs through EVERY subfolder like a panda looking for bamboo.",
            "Process subfolders too. Because one folder is never enough, is it?",
            "Go DEEP into the folder tree. The panda leaves no directory unturned.",
            "Recursive scanning. Finds textures hiding in subfolders. Nowhere to run!",
            "Check this to process ALL the folders. ALL of them. Every. Single. One.",
            "Subdirectory mode: ON. The panda will find every last hidden texture.",
            "Dig through the entire folder tree like a caffeinated archaeologist.",
        ]
    },
    'upscale_zip_output': {
        'normal': [
            "Save all upscaled images into a single ZIP archive",
            "Compress output files into a ZIP for easy sharing",
            "Package the upscaled results into a compressed archive",
            "Create a ZIP file containing all processed textures",
            "Bundle the output into a single compressed ZIP file",
            "Archive upscaled textures into a portable ZIP package",
        ],
        'dumbed-down': [
            "Check this to get all your upscaled images packed into one ZIP file!",
            "Want everything in one file? This zips up all the results for you.",
            "Creates a ZIP with all your finished images — easy to share or move!",
            "Packages everything into a single .zip file when done.",
            "Check this to compress all results into one tidy ZIP archive.",
            "Bundles your upscaled images into a ZIP for convenience.",
        ],
        'vulgar': [
            "ZIP it all up! One tidy package of upscaled glory.",
            "Compress the output into a ZIP. Because loose files are SO last century.",
            "ZIP output: for when you want everything in one neat little package. How organized of you.",
            "Bundle those upscaled textures into a ZIP. The panda approves of tidiness.",
            "Create a ZIP! Because having 500 loose files on your desktop is a lifestyle choice.",
            "Pack it up, pack it in. ZIP that output before things get messy.",
            "Compress to ZIP. Keeps things tidy. The panda respects organization.",
            "ZIP mode: ON. Your upscaled textures, vacuum-sealed for freshness.",
        ]
    },
    'upscale_send_organizer': {
        'normal': [
            "Send upscaled results to the Sort Textures tab for AI organization",
            "After upscaling, forward output to the texture organizer",
            "Automatically route processed textures to the sorting system",
            "Chain upscaling with AI-powered texture categorization",
            "Pass upscaled files directly to the organizer for sorting",
            "Enable pipeline from upscaler to the AI texture sorter",
        ],
        'dumbed-down': [
            "After upscaling, send the images to be automatically sorted and organized!",
            "Check this to auto-sort your upscaled textures by type afterward.",
            "Chains upscaling + sorting together — upscale first, organize second!",
            "Sends finished images to the organizer tab for automatic categorization.",
            "Want to sort your textures after upscaling? This does it automatically!",
            "Routes your upscaled images to the AI sorter when done.",
        ],
        'vulgar': [
            "Auto-send to organizer! The panda does ALL the work for you. As usual.",
            "Chain upscale → sort. Because you're too lazy to click another tab. The panda gets it.",
            "Send to organizer after upscaling. Two birds, one panda.",
            "Automatic pipeline! Upscale AND sort. The panda is a one-bear assembly line.",
            "Route to organizer. The panda will sort your stuff. You just sit there and look pretty.",
            "Enable the upscale-to-sort pipeline. Maximum automation, minimum effort.",
            "Send upscaled textures straight to the sorter. The panda loves efficiency.",
            "Auto-organize after upscale. Because who has TIME to do things manually?",
        ]
    },
    'upscale_preview': {
        'normal': [
            "Select a single image to see a before/after preview",
            "Preview how the current settings affect one texture",
            "Open a file to compare original vs upscaled side-by-side",
            "Test your settings on one image before batch processing",
            "See a live preview of the upscale result for one file",
            "Check quality by previewing a single texture first",
        ],
        'dumbed-down': [
            "Click to pick ONE image and see what it looks like after upscaling!",
            "Try it on a single picture first to see if you like the result.",
            "Test your settings! Pick one image and see before vs after.",
            "Preview mode — see how your settings change an image before doing them all.",
            "Check the result on one image first. Better safe than sorry!",
            "Pick a single image to preview. Shows you original and upscaled side-by-side!",
        ],
        'vulgar': [
            "Preview one image first. Because batch-processing 500 textures and THEN checking is DUMB.",
            "Test drive! Pick an image and see if your settings don't make it look like abstract art.",
            "Preview before you commit. Smart move. The panda approves of this level of caution.",
            "See before/after for one image. Try to contain your excitement.",
            "Single file preview. The panda recommends trying before buying... I mean, batch processing.",
            "Click to see what your settings actually DO. Revolutionary concept, I know.",
            "Preview first, regret never. Pick a texture and see the magic happen.",
            "Test your settings on one image. The panda believes in quality control.",
        ]
    },
    'upscale_fb_good': {
        'normal': [
            "Rate this upscale result as good quality",
            "Give positive feedback on the upscaling output",
            "Mark this texture as a successful upscale",
            "Thumbs up — the upscale result meets your expectations",
            "Positive rating for the current upscale quality",
            "Indicate that this upscale result looks good",
        ],
        'dumbed-down': [
            "Click if the result looks good to you! Thumbs up!",
            "Like what you see? Give it a thumbs up!",
            "Hit this if the upscaled image looks nice!",
            "Good result? Let the app know with a positive rating!",
            "Click the thumbs up if you're happy with how it turned out.",
            "Rate it positively — this helps improve future results!",
        ],
        'vulgar': [
            "👍 NICE! The upscale looks good? Smash that like button!",
            "Good quality? The panda is PLEASED. Click to validate the panda's hard work.",
            "Looks good? Hit the thumbs up. The panda lives for your approval.",
            "Rate as good! Positive feedback fuels the panda's self-esteem.",
            "Thumbs up! The panda will remember your kindness. Probably.",
            "Good result? The panda does a little happy dance. Click it!",
            "👍 Quality approved! The panda's ego needed this today.",
            "Smash that good button. The panda needs validation to function.",
        ]
    },
    'upscale_fb_bad': {
        'normal': [
            "Rate this upscale result as poor quality",
            "Give negative feedback on the upscaling output",
            "Mark this texture as an unsatisfactory upscale",
            "Thumbs down — the upscale result needs improvement",
            "Negative rating for the current upscale quality",
            "Indicate that this result doesn't meet quality standards",
        ],
        'dumbed-down': [
            "Click if the result doesn't look right to you.",
            "Not happy with it? Click thumbs down and try different settings!",
            "If the upscale looks bad, rate it so you can try something else.",
            "Doesn't look good? That's okay — give it a thumbs down and adjust.",
            "Rate it poorly if the quality isn't what you wanted.",
            "Bad result? Click here and consider changing the style or scale.",
        ],
        'vulgar': [
            "Boo! Thumbs down! The panda shares your disappointment.",
            "Bad upscale? Let us know so we can cry about it together.",
            "Click if the result looks worse than a panda's fingerpainting.",
            "Results look like garbage? Hit the sad button. We'll try harder.",
            "Negative feedback. The panda hangs its head in shame.",
            "Bad quality? Ouch. Try a different filter, maybe?",
            "Thumbs down. The panda will consider this a learning experience.",
            "Looks terrible? Rate it. The panda uses this data to improve. Allegedly.",
        ]
    },
    'upscale_sharpen': {
        'normal': [
            "Apply sharpening filter after upscaling to enhance edges",
            "Post-process with an unsharp mask to restore crispness",
            "Sharpen output to counteract blur from interpolation",
            "Enhance edge detail and fine textures with sharpening",
            "Add a sharpening pass to make the upscaled result crisper",
            "Apply edge enhancement to improve visual clarity after resize",
        ],
        'dumbed-down': [
            "Makes the upscaled image look crisper and less blurry!",
            "Check this to sharpen edges — it makes things look clearer.",
            "Sharpening makes details pop! Great if the result looks too soft.",
            "Adds crispness to the image. Like focusing a camera!",
            "Enable to make edges cleaner and details sharper in the output.",
            "If the upscale looks blurry, this helps make it clearer!",
        ],
        'vulgar': [
            "Make it CRISPY. Like a well-done pizza crust but for pixels.",
            "Sharpen those blurry-ass edges. Your textures deserve better.",
            "Click to make the upscale look less like it was smeared in vaseline.",
            "ENHANCE! *slams table* — actually works unlike CSI zoom-enhance.",
            "Sharpening: because nobody asked for blurry textures. Nobody.",
            "Turn on the edge enhancer. Preview updates right away so you can see the magic.",
            "Make your pixels ANGRY and DEFINED. Soft is for pillows, not textures.",
            "Crispify those edges! The panda demands HD-quality sharpness.",
        ]
    },
    'upscale_denoise': {
        'normal': [
            "Apply noise reduction to remove compression artifacts",
            "Smooth out grainy noise from the upscaled result",
            "Reduce visual noise — useful for JPEG source images",
            "Clean up artifacts left by lossy compression in source files",
            "Apply smoothing filter to reduce grain and noise",
            "Remove high-frequency noise while preserving detail",
        ],
        'dumbed-down': [
            "Removes graininess and speckles from the image!",
            "If your image looks grainy or noisy, this cleans it up.",
            "Smooths out ugly dots and noise — especially good for JPEGs.",
            "Check this to make the image less speckly and more smooth.",
            "Reduces that fuzzy/grainy look some images get after upscaling.",
            "Cleans up visual noise. Think of it as a spa treatment for pixels!",
        ],
        'vulgar': [
            "Remove that grainy bullshit from your textures. You're welcome.",
            "Denoise! Because your source images look like they were photographed during an earthquake.",
            "Smooth out the pixel vomit. The panda hates noisy textures.",
            "Click to remove artifacts. Turns 'crusty JPEG' into 'slightly less crusty.'",
            "Noise reduction ON. Your textures were screaming, now they whisper.",
            "Clean up those compression artifacts. Whoever saved as JPEG should be ashamed.",
            "Shhh... quiet those noisy pixels. The panda needs its beauty sleep.",
            "De-crustify your images. Preview updates live so you can watch the magic happen.",
        ]
    },
    'upscale_face_enhance': {
        'normal': [
            "Enhance facial features in character textures",
            "Apply face-specific processing for better portrait results",
            "Optimize upscaling for face and character textures",
            "Use specialized face enhancement during upscale",
            "Improve facial detail and clarity in character images",
            "Apply portrait-optimized processing to face textures",
        ],
        'dumbed-down': [
            "Makes faces in your images look better and clearer!",
            "If your texture has a face on it, this makes it look nicer.",
            "Check this for character face textures — it's optimized for faces!",
            "Special face mode! Makes eyes, mouths, and features look better.",
            "Good for character portraits — enhances facial features specifically.",
            "Turns blurry faces into recognizable faces. Magic!",
        ],
        'vulgar': [
            "Give those low-res faces a glow-up. Botox for pixels, basically.",
            "Face enhancer: because your characters shouldn't look like potatoes.",
            "Click to make faces look like FACES and not abstract art.",
            "Enhance faces! Your NPCs deserve to not look like melted wax figures.",
            "Turn on face mode. The panda promises better cheekbones for everyone.",
            "Fix those fugly faces. Every pixel deserves jawline definition.",
            "Character faces looking rough? This'll make them look merely 'meh.'",
            "Face enhancement: turning pixel blobs into something resembling human features.",
        ]
    },
    'upscale_gpu': {
        'normal': [
            "Use GPU acceleration for faster upscaling",
            "Enable CUDA/OpenCL processing for improved speed",
            "Leverage your graphics card for faster processing",
            "Offload computation to the GPU for acceleration",
            "Use hardware acceleration to speed up the upscale process",
            "Enable graphics card processing for faster results",
        ],
        'dumbed-down': [
            "Uses your graphics card to make things faster! (Needs a good GPU.)",
            "Speed boost! Makes your graphics card do the heavy lifting.",
            "Check this if you have a good graphics card — it'll be much faster!",
            "Uses your GPU (graphics card) instead of just the CPU. Way faster!",
            "Enable hardware acceleration. Your graphics card will help with processing.",
            "Turbo mode! Uses your GPU for speed. Works best with NVIDIA cards.",
        ],
        'vulgar': [
            "Make your GPU earn its keep. It's been slacking playing games all day.",
            "GPU go BRRRRR. Uses your graphics card for SPEED.",
            "Engage turbo mode! Your GPU didn't cost $500 to sit there idle.",
            "Click to wake up your graphics card from its gaming-only retirement.",
            "GPU acceleration: because your CPU was crying and your GPU was bored.",
            "Put that overpriced graphics card to work! COMPUTE, damn you!",
            "Turn on the rocket engines! Requires an actual GPU, not hopes and dreams.",
            "GPU mode: make that expensive graphics card justify its existence.",
        ]
    },
    'upscale_tile_seamless': {
        'normal': [
            "Ensure texture tiles seamlessly after upscaling",
            "Edge-wrap processing for repeating/tiling textures",
            "Prevent visible seams at tile boundaries after upscale",
            "Maintain seamless tiling for repeating textures like floors and walls",
            "Apply edge blending to preserve tileable texture properties",
            "Process tile edges to avoid seam artifacts in repeating textures",
        ],
        'dumbed-down': [
            "For textures that repeat (like floors/walls) — keeps them seamless!",
            "Check this if your texture needs to tile without visible seams.",
            "Repeating textures stay smooth at the edges. No ugly lines!",
            "Use this for floor, wall, or fabric textures that need to tile perfectly.",
            "Keeps repeating textures looking seamless after upscaling. Very important!",
            "If your texture repeats in a pattern, this prevents visible edges.",
        ],
        'vulgar': [
            "Make your tiles actually TILE. Revolutionary concept, we know.",
            "Seamless mode: because visible seams are the worst thing since dial-up.",
            "Click so your floor textures don't look like a bad wallpaper job.",
            "Tiling mode ON. Your walls won't have that 'I clearly repeat' look.",
            "Remove seams! Nobody wants to see where your texture goes 'copy paste copy paste.'",
            "Seamless tiling for the OCD perfectionist in all of us.",
            "For tiling textures. If you use this on a character face, the panda judges you.",
            "Make repeating textures actually seamless. Groundbreaking, honestly.",
        ]
    },
    'upscale_normal_map': {
        'normal': [
            "Process image as a normal map to preserve directional data",
            "Normal map mode keeps RGB channel data physically accurate",
            "Optimize upscaling for normal/bump map textures",
            "Preserve surface normal direction vectors during upscale",
            "Use specialized handling for normal map lighting data",
            "Maintain correct normal map encoding through the upscale process",
        ],
        'dumbed-down': [
            "For those blue-purple bumpy textures used for lighting in 3D!",
            "Check this if your texture is a normal map (used for fake depth/bumps).",
            "Normal maps need special treatment — this keeps the lighting data correct.",
            "If your texture looks blue/purple and makes surfaces look bumpy, use this!",
            "Special mode for normal maps — preserves the lighting direction data.",
            "For bump/normal maps only. Keeps the RGB channels accurate for 3D rendering.",
        ],
        'vulgar': [
            "Normal map mode. For those blue-purple textures that make surfaces bumpy.",
            "Treat this as a NORMAL MAP. The panda knows what normals are. Allegedly.",
            "Click if this is one of those weird blue textures. Trust the process.",
            "Normal map processing! Preserves those precious XYZ vectors or whatever.",
            "For normal maps ONLY. If you click this on a regular texture, chaos ensues.",
            "Blue-purple bumpy texture? Click this. Regular photo? Don't.",
            "Preserve lighting data during upscale. The 3D nerds will thank you.",
            "Normal map mode: treating your blue blobs with the respect they deserve.",
        ]
    },
    'upscale_auto_level': {
        'normal': [
            "Auto-level colors by stretching the histogram to full 0-255 range",
            "Automatically improve contrast for better tonal range",
            "Enhance washed-out textures with automatic brightness adjustment",
            "Apply auto-contrast to maximize dynamic range in the output",
            "Stretch color values to utilize the full brightness spectrum",
            "Normalize brightness levels for improved visual clarity",
        ],
        'dumbed-down': [
            "Makes colors more vivid by adjusting brightness and contrast automatically!",
            "If your image looks washed out or faded, this fixes the colors.",
            "Auto-adjusts brightness so dark parts are darker and light parts are lighter.",
            "Fixes dull-looking images by stretching the color range. Very helpful!",
            "Makes colors pop! Great for textures that look flat or low-contrast.",
            "Automatically improves contrast. Like putting on glasses for your textures.",
        ],
        'vulgar': [
            "Auto-level: makes your washed-out textures less... washed out. Shocker.",
            "ENHANCE THE CONTRAST! Your textures look like they've been left in the sun.",
            "Click to un-fade your textures. The panda disapproves of low contrast.",
            "Stretch those histograms! (That sounded dirtier than intended.)",
            "Auto-level colors because your textures have the contrast of a foggy day.",
            "Fix that flat, lifeless look. Preview updates live so you can gasp in real time.",
            "Contrast boost! Go from 'meh gray blob' to 'ooh, actual colors!'",
            "The 'make it not look like crap' button. Uses histogram stretching. Very fancy.",
        ]
    },
    'upscale_overwrite': {
        'normal': [
            "Overwrite existing output files instead of skipping them",
            "Replace previously processed files in the output directory",
            "Re-process files that already exist in the output folder",
            "Enable file replacement for already-upscaled textures",
            "When enabled, existing files are overwritten with new results",
            "Skip nothing — reprocess and replace all output files",
        ],
        'dumbed-down': [
            "Check this to replace old files. Uncheck to skip images already done.",
            "If you want to redo files that already exist, turn this on.",
            "Overwrites files that are already in the output folder.",
            "When ON, it replaces old results. When OFF, it skips files that exist.",
            "Re-do everything? Check this. Keep old results? Leave it unchecked.",
            "Controls whether to replace existing files or skip them.",
        ],
        'vulgar': [
            "Overwrite mode: DESTROY the old files. No mercy. No backup.",
            "Click to enable file destruction. Old outputs get REPLACED.",
            "Replace existing files? Living dangerously, I see.",
            "Overwrite: because you want the NEW version, not that old garbage.",
            "Enable to re-do everything. The panda respects your commitment to perfection.",
            "Skip nothing! Overwrite EVERYTHING! ...hope you have backups.",
            "Bulldoze existing files. The panda takes no prisoners.",
            "Overwrite mode. For when yesterday's upscale just wasn't good enough.",
        ]
    },
    'upscale_zoom_out': {
        'normal': [
            "Zoom out to shrink the preview thumbnails",
            "Decrease preview zoom level to see more of the image",
            "Make preview smaller to see the full texture at a glance",
            "Reduce preview magnification by one step",
            "Zoom out the preview display for a wider view",
            "Decrease the preview zoom to show more of the texture",
        ],
        'dumbed-down': [
            "Makes the preview pictures smaller so you can see more!",
            "Click to zoom out — see more of the image at once.",
            "Shrinks the preview. Good for seeing the whole picture.",
            "Zoom out! Makes the preview thumbnails smaller.",
            "See the bigger picture (literally) by zooming out.",
            "Makes the preview images smaller to show more detail at once.",
        ],
        'vulgar': [
            "Zoom OUT. See more, squint harder. The panda has tiny eyes too.",
            "Make the preview smaller. For when you want the big picture. Literally.",
            "Shrink! The preview, not your expectations.",
            "Zoom out so you can pretend the artifacts aren't visible.",
            "ENHANCE — wait no, the opposite of that.",
            "Step back from the pixels. Sometimes you need the eagle-eye view.",
            "Zoom out. For when the zoomed-in view is too honest about quality.",
            "Make it smaller! The panda believes in perspective. Literally.",
        ]
    },
    'upscale_zoom_in': {
        'normal': [
            "Zoom in to enlarge the preview thumbnails",
            "Increase preview zoom level for a closer look at details",
            "Magnify the preview to inspect fine texture details",
            "Increase preview magnification by one step",
            "Zoom in on the preview display for pixel-level inspection",
            "Get a closer look at the upscaled result details",
        ],
        'dumbed-down': [
            "Makes the preview pictures bigger so you can see details!",
            "Click to zoom in — get a closer look at the texture.",
            "Enlarges the preview. Great for checking small details!",
            "Zoom in! Makes the preview thumbnails bigger.",
            "Get up close and personal with your texture details.",
            "Makes preview images larger to show fine detail better.",
        ],
        'vulgar': [
            "Zoom IN. Get uncomfortably close to those pixels.",
            "ENHANCE! Finally, a zoom that actually works.",
            "Get closer! Inspect every single damn pixel if you want.",
            "Zoom in to either admire or be horrified by the details.",
            "Magnify! The panda wants to see those pores... er, pixels.",
            "Closer! CLOSER! The panda demands pixel-level scrutiny!",
            "Zoom in and witness the beautiful (or horrifying) details up close.",
            "Get your face right up in those pixels. Quality inspection time!",
        ]
    },
    'upscale_zoom_fit': {
        'normal': [
            "Reset preview zoom to 100% (default fit)",
            "Return to the standard preview zoom level",
            "Fit the preview back to its default display size",
            "Reset zoom to show the preview at standard magnification",
            "Restore the default preview size and zoom level",
            "Snap back to 100% zoom for normal preview viewing",
        ],
        'dumbed-down': [
            "Reset the zoom back to normal! Shows images at regular size.",
            "Click to go back to the default zoom level.",
            "Back to normal! Resets the preview to its default size.",
            "Return to standard view — not too big, not too small.",
            "Reset everything to the default zoom. Nice and simple!",
            "Go back to regular size. Like hitting a reset button for zoom.",
        ],
        'vulgar': [
            "Back to normal! Reset zoom to 100%. The boring default.",
            "Fit to size. Like finding the right pair of pants but for previews.",
            "Reset zoom. The panda prefers the Goldilocks view — juuust right.",
            "Undo your zoom rampage. Return to sensible preview size.",
            "100% zoom. Not too big, not too small. The panda approves.",
            "Reset! For when you've zoomed yourself into pixel-level existential crisis.",
            "Back to default. The panda recommends this zoom for daily use.",
            "Fit mode: the 'I've zoomed too much and need to go back' button.",
        ]
    },
    'upscale_export_single': {
        'normal': [
            "Export the previewed texture with all current settings applied",
            "Save this single upscaled image to a file on disk",
            "Export the currently displayed upscaled result",
            "Save the upscaled texture with the chosen scale, style, and post-processing",
            "Write the previewed upscale result to your chosen file location",
            "Export one texture with all active settings (scale, style, filters)",
        ],
        'dumbed-down': [
            "Save the upscaled image to a file! Click to pick where to save it.",
            "Export your result! This saves the bigger version to your computer.",
            "Click to save the upscaled texture as a file on your computer.",
            "Download your upscaled image! Pick a location and format to save.",
            "Save it! This exports the processed texture with all your settings.",
            "Export the result to a file. You get to pick where it goes!",
        ],
        'vulgar': [
            "SAVE IT! Export this beautiful upscaled masterpiece to a file.",
            "Export this one texture with ALL your fancy settings applied. Chef's kiss.",
            "Save the result before you forget what settings you used.",
            "Export button! The panda packed your upscaled texture for takeout.",
            "Download your creation! It's like hitting 'Save As' but fancier.",
            "Save this upscale to disk. The panda will guard it with its life.",
            "Export with all filters applied. One-click gourmet texture export.",
            "Yoink! Save that upscaled texture before the preview disappears.",
        ]
    },
    'upscale_custom_res': {
        'normal': [
            "Enter a custom output resolution (e.g. 1024x1024)",
            "Specify exact pixel dimensions for the upscaled output",
            "Override the scale factor with a specific target resolution",
            "Set a custom width x height for the output image",
            "Type a resolution like '2048x2048' to set an exact output size",
            "Custom resolution overrides the scale factor when a value is entered",
        ],
        'dumbed-down': [
            "Type a size like '1024x1024' to set an exact output size!",
            "Want a specific size? Type it here! Example: 512x512",
            "Enter your own dimensions. This overrides the scale multiplier!",
            "Type width x height (like 2048x2048) for a specific output size.",
            "Custom size! If you know exactly how big you want the image, type it here.",
            "Enter exact pixel dimensions. Leave blank to use the scale factor instead.",
        ],
        'vulgar': [
            "Type your custom resolution. 1024x1024? 4096x4096? Go nuts!",
            "Custom size! For control freaks who need EXACT pixel counts.",
            "Enter dimensions manually. Because the scale factor isn't good enough for you, apparently.",
            "Type a resolution. The panda trusts you know what you're doing. Probably.",
            "Custom res: for when 'make it 4x bigger' isn't specific enough for your needs.",
            "Hand-type your target resolution like the power user you clearly are.",
            "Enter exact pixels. Leave blank if you trust the scale factor. (Do you, though?)",
            "Custom dimensions! Because sometimes you need EXACTLY 1337x420 pixels. No judgment.",
        ]
    },
    'upscale_preserve_metadata': {
        'normal': [
            "Preserve original image metadata (EXIF) when upscaling",
            "Keep EXIF data from source images in the upscaled output",
            "Maintain camera info, timestamps, and other metadata during upscaling",
            "Copy metadata from original images to processed files",
            "Preserve image properties like creation date and camera settings",
            "Transfer EXIF data to upscaled images (best for JPEG files)",
        ],
        'dumbed-down': [
            "Keep the extra info from your photos (like when it was taken)!",
            "This saves photo details like date and camera info when upscaling.",
            "Check this to keep the 'behind-the-scenes' info from your images!",
            "Works best with JPEG photos — keeps all the camera details!",
            "Copies the photo's 'birth certificate' to the bigger version.",
            "Preserves info like when and where the photo was taken!",
        ],
        'vulgar': [
            "Keep that EXIF shit. Date, camera model, all that nerdy-ass metadata.",
            "Preserve metadata? Sure, if you actually give a fuck about timestamps and camera info.",
            "EXIF preservation: for when you give a damn about photo metadata for some reason.",
            "Copy all that technical crap from the original. JPEG nerds will love you forever.",
            "Metadata mode: because apparently you need to know WHEN a texture was created. Whatever floats your boat.",
            "Keep the photo's metadata. Date, camera, GPS... wait, why the fuck do your textures have GPS?",
            "EXIF copying go brrr. All your precious metadata stays intact, you perfectionist.",
            "For photographers who upscale. The panda judges your metadata obsession. But only a little.",
            "Checkbox for metadata nerds. You know who you are. Don't be ashamed.",
            "Preserve EXIF or don't. The panda doesn't care about your camera settings, but you might."
        ]
    },
    'panda_sound_eat': {
        'normal': [
            "Choose the sound played when your panda eats bamboo",
            "Select an audio clip for panda eating moments",
            "Pick the munching sound for your panda companion",
        ],
        'vulgar': [
            "Pick the nom-nom sound. The panda is a very loud eater.",
            "Eating sounds: CHOMP CHOMP MUNCH. You're welcome.",
            "Select your panda's dining soundtrack. Manners not included.",
        ]
    },
    'panda_sound_happy': {
        'normal': [
            "Choose the sound played when your panda is happy",
            "Select the audio for joyful panda moments",
            "Pick a cheerful sound for your panda's happy mood",
        ],
        'vulgar': [
            "Happy panda noises! Like a tiny bear having the best day ever.",
            "Joy sounds. The panda is basically vibrating with happiness.",
            "Pick the happy sound. Warning: may cause involuntary smiling.",
        ]
    },
    'panda_sound_sad': {
        'normal': [
            "Choose the sound played when your panda is sad",
            "Select the audio for panda sadness moments",
            "Pick a melancholy sound for your panda's sad mood",
        ],
        'vulgar': [
            "Sad panda sounds. You monster, what did you do to it?",
            "The saddest sound in the world: a disappointed panda.",
            "Sad noises. If you hear this, give the panda some bamboo ASAP.",
        ]
    },
    'panda_sound_drag': {
        'normal': [
            "Choose the sound played when dragging the panda",
            "Select audio for when the panda is being moved around",
            "Pick the sound for dragging your panda companion",
        ],
        'vulgar': [
            "Drag sound: the noise of an unwilling panda being relocated.",
            "WHEEE—wait, no. The panda did NOT consent to being dragged.",
            "Pick the 'I'm being kidnapped' sound. The panda is not amused.",
        ]
    },
    'panda_sound_drop': {
        'normal': [
            "Choose the sound played when the panda is dropped",
            "Select audio for when you release the panda after dragging",
            "Pick the landing sound for your panda companion",
        ],
        'vulgar': [
            "THUD. That's the sound of dropping a panda. Feel bad yet?",
            "Drop sound: the gentle 'plop' of an undignified panda landing.",
            "Select the 'you let go of me, you animal' sound effect.",
        ]
    },
    'panda_sound_sleep': {
        'normal': [
            "Choose the sound played when your panda falls asleep",
            "Select the snoozing audio for your panda companion",
            "Pick the sleeping sound for nap time",
        ],
        'vulgar': [
            "Zzzzz... Pick the snoring sound. The panda sleeps like a log.",
            "Sleep sounds: choose between gentle snore and chainsaw snore.",
            "Nap time audio. The panda is OUT. Do not disturb.",
        ]
    },
    'panda_sound_wake': {
        'normal': [
            "Choose the sound played when your panda wakes up",
            "Select the wake-up audio for your panda companion",
            "Pick the morning greeting sound for your panda",
        ],
        'vulgar': [
            "Wake up sound! The panda rises like a grumpy fuzzy phoenix.",
            "Morning sounds: the panda is NOT a morning bear. Choose wisely.",
            "Wake-up audio. Consider something gentle. The panda bites.",
        ]
    },
    'panda_sound_click': {
        'normal': [
            "Choose the sound played when you click on the panda",
            "Select the audio response for clicking your panda",
            "Pick the reaction sound when tapping your panda companion",
        ],
        'vulgar': [
            "Click sound: what happens when you poke a panda. Repeatedly.",
            "Boop! You clicked the panda. It has opinions about that.",
            "Click reaction noise. The panda tolerates your poking. Barely.",
        ]
    },
    'panda_sound_pet': {
        'normal': [
            "Choose the sound played when petting the panda",
            "Select the audio for gentle panda petting moments",
            "Pick the purring sound for when you pet your panda",
        ],
        'vulgar': [
            "Pet sounds: the panda purrs like a furry little motorboat.",
            "Aww, you're petting it! Pick a sound worthy of this tender moment.",
            "Petting audio. The panda is melting into a puddle of fluff.",
        ]
    },
    'panda_sound_play': {
        'normal': [
            "Choose the sound played when your panda is playing",
            "Select the audio for panda playtime activities",
            "Pick the playful sound for your active panda companion",
        ],
        'vulgar': [
            "Play sounds! The panda is rolling around like a fluffy bowling ball.",
            "Playtime audio: chaos in sound form. The panda has the zoomies.",
            "Pick the play sound. The panda is HYPER and there's no stopping it.",
        ]
    },
    'panda_sound_walk': {
        'normal': [
            "Choose the sound played when the panda walks around",
            "Select the footstep audio for your wandering panda",
            "Pick the walking sound for panda movement",
        ],
        'vulgar': [
            "Waddle waddle waddle. Pick the panda's walking soundtrack.",
            "Footstep sounds: pitter-patter of chunky panda feet.",
            "Walking audio. The panda struts. It doesn't walk, it STRUTS.",
        ]
    },
    'panda_sound_jump': {
        'normal': [
            "Choose the sound played when your panda jumps",
            "Select the audio for panda jumping moments",
            "Pick the bounce sound for your leaping panda",
        ],
        'vulgar': [
            "BOING! The panda defies gravity! Pick the launch sound.",
            "Jump audio: proof that round bears can achieve liftoff.",
            "Pick the jump sound. Physics weeps. The panda soars.",
        ]
    },
    'panda_sound_dance': {
        'normal': [
            "Choose the sound played when your panda dances",
            "Select the music for panda dance moves",
            "Pick the groove sound for your dancing panda companion",
        ],
        'vulgar': [
            "Dance music! The panda's got moves you wouldn't believe.",
            "Boogie time audio. The panda dances like nobody's watching.",
            "Pick the dance sound. Warning: may cause spontaneous panda twerking.",
        ]
    },
    'panda_sound_sneeze': {
        'normal': [
            "Choose the sound played when your panda sneezes",
            "Select the sneeze audio for your panda companion",
            "Pick the achoo sound for sneezing moments",
        ],
        'vulgar': [
            "ACHOO! The cutest, most violent sneeze in nature. Pick one.",
            "Sneeze sound: the panda just blew itself backwards. Classic.",
            "Pick the sneeze audio. Baby panda sneezes break the internet.",
        ]
    },
    'panda_sound_yawn': {
        'normal': [
            "Choose the sound played when your panda yawns",
            "Select the yawning audio for your sleepy panda",
            "Pick the yawn sound for tired panda moments",
        ],
        'vulgar': [
            "YAAAWN. The panda is bored of your texture sorting. Just kidding.",
            "Yawn sound: the panda's way of saying 'I need a nap, human.'",
            "Pick the yawn audio. It's contagious. You're yawning now, aren't you?",
        ]
    },
    'sound_selection_system': {
        'normal': [
            "Configure system-wide sound effects for UI interactions",
            "Manage audio settings for application events like clicks and alerts",
            "Customize the sounds used for system notifications and actions",
        ],
        'vulgar': [
            "System sounds: beeps, boops, and dings. Customize the cacophony.",
            "Pick your system sounds. Make every click a tiny celebration.",
            "Audio settings for the app itself. Make it sound like a spaceship if you want.",
        ]
    },
    'sound_selection_panda': {
        'normal': [
            "Configure sounds for all panda companion actions",
            "Manage audio settings for your panda's various behaviors",
            "Customize the sounds your panda makes during interactions",
        ],
        'vulgar': [
            "Panda sound central: where you decide what noises your bear makes.",
            "All the panda sounds in one place. It's a furry symphony.",
            "Customize your panda's entire vocal repertoire. Go nuts.",
        ]
    },
    'ai_feedback_bad': {
        'normal': [
            "Mark this AI suggestion as incorrect to improve future accuracy",
            "Give negative feedback on the AI's category classification",
            "Tell the AI this sorting suggestion was wrong",
            "Flag this classification as a bad result for AI learning",
        ],
        'vulgar': [
            "Slap the AI with a thumbs down. It can take it. Probably.",
            "Bad AI! No biscuit! Click to teach it a lesson.",
            "The AI got it wrong? Shocking. Click to add to its shame file.",
            "Negative feedback: because even AI needs to know when it's being dumb.",
        ],
        'dumbed-down': [
            "Click this if the computer guessed WRONG!",
            "The robot made a mistake? Tell it by clicking here!",
            "This tells the computer 'No, that's not right!'",
        ]
    },
    'ai_feedback_retry': {
        'normal': [
            "Ask the AI to try classifying this texture again",
            "Retry the AI classification with a fresh attempt",
            "Re-run the AI sorting suggestion for this item",
        ],
        'vulgar': [
            "Try again, robot! The panda believes in second chances.",
            "Retry: because the AI's first attempt was... creative, let's say.",
            "Give the AI another shot. Maybe it was having an off day.",
        ],
        'dumbed-down': [
            "Make the computer try again! Maybe it'll get it right this time!",
            "Click to let the robot have another guess!",
            "Try again button — gives the AI a do-over!",
        ]
    },
    'ai_export_training': {
        'normal': [
            "Export your AI training data to share with others",
            "Save your accumulated AI feedback corrections to a file",
            "Download the training data the AI has learned from your usage",
        ],
        'vulgar': [
            "Export your AI's brain to a file. It's less creepy than it sounds.",
            "Save the AI training data. Share your panda's wisdom with the world.",
            "Download the AI's learned corrections. It's like a report card, but for robots.",
        ],
        'dumbed-down': [
            "Save what the robot learned to a file you can share!",
            "Download the AI's homework so your friend's AI can copy it!",
            "Export = save the robot's brain to a file!",
        ]
    },
    'ai_import_training': {
        'normal': [
            "Import AI training data from another user or backup",
            "Load previously exported AI feedback corrections",
            "Restore AI learning data from a shared training file",
        ],
        'vulgar': [
            "Import someone else's AI training. Steal their panda's homework!",
            "Load training data. Give your AI a brain transplant.",
            "Import AI corrections. It's like downloading experience points for your robot.",
        ],
        'dumbed-down': [
            "Load someone else's robot brain file to make YOUR robot smarter!",
            "Import = give the AI a cheat sheet from another user!",
            "Plug in training data so the computer already knows stuff!",
        ]
    },
    # ── Per-Tool AI Settings Tooltips ──
    'ai_cls_model': {
        'normal': [
            "Select the vision model used for classifying image content into categories",
            "CLIP ViT-B/32 is the default general-purpose classifier; DinoV2 excels at self-supervised features",
            "EfficientNet is lightweight and fast; ViT-Base offers strong accuracy for larger datasets",
        ],
        'vulgar': [
            "Pick which robot eyeball to use for sorting your damn textures. CLIP is the reliable one, DinoV2 is the fancy one.",
            "Vision model selector: it's like picking which pair of glasses the AI wears. Some see better than others, obviously.",
            "Choose your AI's brain type. CLIP = generalist nerd, DinoV2 = hipster with self-taught skills, EfficientNet = the speedy little bastard.",
        ],
        'dumbed-down': [
            "Pick which robot eye the computer uses to look at your pictures!",
            "Different models = different ways the computer 'sees' your images!",
            "The default one (CLIP) works great — only change if you know what you're doing!",
        ]
    },
    'ai_cls_custom_api': {
        'normal': [
            "Enable to use your own hosted classification API instead of the built-in model",
            "When checked, classification requests are sent to your custom endpoint",
        ],
        'vulgar': [
            "Check this if you're running your own classifier because you're too cool for built-in AI. Look at you, Mr. Self-Hosted.",
            "Enable custom API: for people who don't trust our AI and rolled their own. Fair enough, honestly.",
        ],
        'dumbed-down': [
            "Turn this ON if you have your own classification server running somewhere!",
            "Leave this OFF unless you set up your own AI service!",
        ]
    },
    'ai_cls_api_url': {
        'normal': [
            "The URL endpoint for your custom classification API (e.g., https://your-server.com/v1/classify)",
            "Enter the full HTTP/HTTPS address of your hosted classifier",
        ],
        'vulgar': [
            "Paste your custom API URL here. You know, the one you spent 3 hours setting up. We won't judge the domain name.",
            "API URL field: type in where your fancy self-hosted classifier lives. Don't forget the https, genius.",
        ],
        'dumbed-down': [
            "Type the web address of your custom AI server here!",
            "This is like a website link, but for your AI!",
        ]
    },
    'ai_cls_api_key': {
        'normal': [
            "Authentication key for your custom classification API",
            "This key is stored locally and sent as a Bearer token with each request",
        ],
        'vulgar': [
            "Your API secret key. Guard it like a dragon guards gold. Or at least don't paste it on Twitter, you absolute walnut.",
            "API key: the password to your AI's soul. Keep it secret, keep it safe. Gandalf voice.",
        ],
        'dumbed-down': [
            "This is like a password for your custom AI — keep it secret!",
            "Put your special access code here so the AI lets you in!",
        ]
    },
    'ai_bgr_model': {
        'normal': [
            "Select the AI model for background removal: u2net is general-purpose, isnet-anime is optimized for 2D art",
            "u2netp is a lightweight/fast variant; sam (Segment Anything) works on complex scenes",
            "u2net_human_seg specializes in isolating people; u2net_cloth_seg isolates clothing",
        ],
        'vulgar': [
            "Pick which AI model nukes your backgrounds. u2net = old reliable, isnet-anime = weeb mode, sam = 'I'll segment ANY damn thing'.",
            "Background removal model: u2net for normies, anime model for weebs, sam for when you need to segment literally everything in the goddamn image.",
            "Choose your background assassin. u2netp is fast but sloppy, u2net is balanced, sam is the overachieving tryhard.",
        ],
        'dumbed-down': [
            "Pick which robot removes backgrounds! 'u2net' works for most things!",
            "For cartoon/anime pictures, pick 'isnet-anime' — it works better on drawings!",
            "Just leave it on 'u2net' unless something looks weird!",
        ]
    },
    'ai_bgr_custom_api': {
        'normal': [
            "Enable to route background removal through your own hosted API",
            "When checked, removal requests go to your custom endpoint instead of the local model",
        ],
        'vulgar': [
            "Check this to use your own bg removal API. Because apparently the built-in one isn't fancy enough for your royal highness.",
            "Self-hosted bg removal? Look at this absolute chad running their own infrastructure.",
        ],
        'dumbed-down': [
            "Turn this ON only if you have your own background removal server!",
            "Leave OFF to use the built-in background remover!",
        ]
    },
    'ai_bgr_api_url': {
        'normal': [
            "URL endpoint for your custom background removal API",
            "Enter the full address where your bg removal service accepts requests",
        ],
        'vulgar': [
            "Paste your self-hosted background removal URL. Make sure it actually works before blaming us, please.",
            "API URL for your bg remover. Triple-check for typos — the AI can't read your mind. Yet.",
        ],
        'dumbed-down': [
            "Type the web address of your background removal server here!",
            "This is the link to where your custom bg remover lives on the internet!",
        ]
    },
    'ai_bgr_api_key': {
        'normal': [
            "Authentication key for your custom background removal API",
            "Stored locally and sent with each removal request",
        ],
        'vulgar': [
            "API key for your bg remover. Don't share it or some random will be removing backgrounds on your dime.",
            "Secret key. Emphasis on SECRET. Don't screenshot this and post it on Reddit.",
        ],
        'dumbed-down': [
            "The password for your custom background removal service!",
            "Keep this secret — it's like a key to your AI's house!",
        ]
    },
    'ai_ups_model': {
        'normal': [
            "Select the AI upscaling model: realesrgan-x4plus is best for general photos and textures",
            "anime variant is optimized for 2D artwork; remacri and ultrasharp preserve fine details",
            "ultramix_balanced offers a good middle ground; 'bicubic (no AI)' uses traditional interpolation",
        ],
        'vulgar': [
            "Pick your upscale engine. realesrgan = the OG, anime = for your 'totally not hentai' textures, ultrasharp = for pixel-peeping psychopaths.",
            "Upscale model: realesrgan-x4plus is the safe bet. anime is for weebs. ultrasharp is for maniacs who zoom to 4000%. bicubic is for quitters.",
            "Choose wisely: this determines whether your upscaled textures look godly or like they were smeared with Vaseline.",
        ],
        'dumbed-down': [
            "Pick which robot makes your pictures bigger! The first one works for most things!",
            "For cartoons/anime, pick the 'anime' one! For photos, pick 'ultrasharp'!",
            "'bicubic' means NO AI — just normal stretching. It's fine but not as good!",
        ]
    },
    'ai_ups_gpu': {
        'normal': [
            "Enable GPU acceleration for significantly faster upscaling (requires compatible NVIDIA GPU)",
            "When disabled, upscaling runs on CPU which is slower but always available",
        ],
        'vulgar': [
            "GPU go BRRRRR. Turn this on if you have an NVIDIA card. If you don't, cry into your CPU-only peasant hands.",
            "GPU acceleration: makes upscaling fast as hell. Without it, you'll be waiting long enough to question your life choices.",
        ],
        'dumbed-down': [
            "Turn ON to make upscaling FAST if you have a gaming graphics card!",
            "If this causes errors, turn it OFF — your computer will just be slower!",
        ]
    },
    'ai_ups_tile': {
        'normal': [
            "Tile size for processing large images: 0 = automatic, higher values use less GPU memory",
            "Try 256 or 512 if you get out-of-memory errors; 0 processes the whole image at once",
        ],
        'vulgar': [
            "Tile size: 0 = YOLO mode, let the AI figure it out. Getting crashes? Set to 256, ya cheapskate with your 2GB VRAM.",
            "How big of a chunk to process at once. 0 = full send. Getting memory errors? Lower this, your GPU is weeping.",
        ],
        'dumbed-down': [
            "Leave this at 0 unless your computer runs out of memory!",
            "If you get errors, try putting 256 or 512 here!",
            "Smaller number = less memory needed, but slower!",
        ]
    },
    'ai_ups_custom_api': {
        'normal': [
            "Enable to use your own hosted upscaling API instead of the local model",
            "When checked, images are sent to your custom endpoint for upscaling",
        ],
        'vulgar': [
            "Running your own upscale server? Check this. God knows why you'd want to, but hey, it's your electricity bill.",
            "Custom API for upscaling: for the special snowflakes who can't use anything out of the box.",
        ],
        'dumbed-down': [
            "Turn ON only if you have your own upscaling server set up!",
            "Leave this OFF to use the built-in upscaler!",
        ]
    },
    'ai_ups_api_url': {
        'normal': [
            "URL endpoint for your custom upscaling API",
            "Enter the full address where your upscale service accepts image requests",
        ],
        'vulgar': [
            "Paste your upscale API URL here. And pray it doesn't have a typo that sends your textures into the void.",
            "Custom upscale endpoint URL. Double-check this or your images are going to some random server in Kazakhstan.",
        ],
        'dumbed-down': [
            "Type the web address of your custom upscaling server here!",
            "It should look like a website URL starting with https://",
        ]
    },
    'ai_ups_api_key': {
        'normal': [
            "Authentication key for your custom upscaling API",
            "Stored locally and included with each upscale request for authentication",
        ],
        'vulgar': [
            "API key for upscaling. This is basically the password to your wallet if you're using a paid service. Don't be stupid with it.",
            "Your upscaler API key. Treat it like your credit card number. Actually, treat it BETTER than your credit card number.",
        ],
        'dumbed-down': [
            "The secret password for your custom upscaling service!",
            "Keep this safe — don't share it with anyone!",
        ]
    },
    'travel_hub': {
        'normal': [
            "Access the Travel Hub to explore different game worlds",
            "Open the hub for traveling between themed environments",
            "Visit the Travel Hub to discover new locations",
        ],
        'vulgar': [
            "Travel Hub: where the panda goes on vacation. Pack your bamboo.",
            "Explore new worlds! The panda is ready for adventure. Are you?",
            "Open the Travel Hub. The panda has wanderlust and zero chill.",
        ]
    },
    'armory_tab': {
        'normal': [
            "View and manage your collected equipment and gear",
            "Open the Armory to browse your inventory items",
            "Access your collection of unlocked armory items",
        ],
        'vulgar': [
            "The Armory: where the panda suits up for battle. Or nap time.",
            "Check your gear! The panda has been hoarding equipment like a dragon.",
            "Open the Armory. The panda needs to accessorize.",
        ]
    },
    'battle_arena': {
        'normal': [
            "Enter the Battle Arena for panda combat challenges",
            "Open the arena to participate in battles and earn rewards",
            "Access the Battle Arena for competitive panda encounters",
        ],
        'vulgar': [
            "BATTLE ARENA! The panda is ready to throw paws! Let's GO!",
            "Enter the arena. Two pandas enter, one panda leaves... with more bamboo.",
            "Battle time! The panda has been training. Mostly by eating, but still.",
        ]
    },
    # ═══════════════════ STATS SYSTEM TOOLTIPS ═══════════════════
    'stat_level': {
        'normal': [
            "Your panda's current experience level",
            "Level indicates overall progression and unlocks new abilities",
            "Gain experience through interactions and combat to level up",
            "Higher levels grant stat boosts and skill points",
            "Character level - increases with experience points",
        ],
        'dumbed-down': [
            "This number goes up when you do stuff. Bigger number = better panda!",
            "Level is like... how strong your panda is. Do things, get XP, level goes brrr.",
            "The bigger this number, the more awesome your panda becomes!",
            "Think of this like... your panda's power level. It's over 9000... eventually.",
            "This is your panda's 'I'm better than I was yesterday' number.",
        ],
        'vulgar': [
            "Your panda's badass level. Higher = more badass. The badass-ometer. Maximum badassery achieved at level 100.",
            "This shit shows how much of a beast your panda has become. Spoiler: pretty beastly. Getting beastlier.",
            "Level up, get stronger, kick more ass. Simple as that. The circle of life. Except with more violence.",
            "The 'how much of a legend is this panda' metric. Currently: working on it. Legendary status pending.",
            "Your panda's power level. Make it bigger, goddammit. Numbers go up. Power increases. Math works."
        ]
    },
    'stat_experience': {
        'normal': [
            "Experience points toward next level",
            "Earn XP through activities, combat, and achievements",
            "Reach the required XP to level up and gain rewards",
            "Experience accumulates from all panda activities",
            "Progress bar showing XP needed for next level",
        ],
        'dumbed-down': [
            "Do stuff, get points. Get enough points, level goes up!",
            "This bar fills up when you make your panda do things. Full bar = DING!",
            "XP is like... participation points but actually useful.",
            "Every time your panda does something cool, this number goes up a little.",
            "Fill this bar by playing. It's basically a 'you're doing great sweetie' meter.",
        ],
        'vulgar': [
            "XP points. Get 'em, level up, become a god. No pressure. Just become divine. Easy.",
            "Fill this fucking bar already! Do stuff! Kill things! Whatever! Action required. Immediately.",
            "Experience points. AKA 'proof you're not just sitting there'. Get off your ass. Move. Do things.",
            "This bar needs to fill up. Go adventure or some shit. Quest. Fight. Exist productively.",
            "Earn XP by not being lazy. The panda demands progress! Forward momentum. No stagnation. Growth only."
        ]
    },
    'stat_health': {
        'normal': [
            "Current and maximum health points",
            "Health represents vitality and determines survival in combat",
            "Restore health through healing items and rest",
            "Low health increases danger - manage it carefully",
            "HP determines how much damage you can take",
        ],
        'dumbed-down': [
            "This is your panda's life juice. Don't let it hit zero!",
            "Health = how alive your panda is. Keep this number up!",
            "The 'please don't die' meter. Red = bad, green = good.",
            "HP means health points. More is better. Zero is game over.",
            "How much ouchie your panda can take before naptime.",
        ],
        'vulgar': [
            "HP. Don't let this hit zero or your panda's taking a dirt nap. Permanent sleep. The long goodbye.",
            "Health points. Lose 'em all and it's game fucking over. Death screen. Respawn button. Shame.",
            "This is your 'am I dead yet' meter. Keep it high, genius. Self-preservation 101. Don't die.",
            "The life bar. When it empties, you're fucked. Stay alive! Survival mandatory. Death optional. Choose wisely.",
            "Your panda's 'still kicking' gauge. Zero = not kicking anymore. Corpse status. Avoid this."
        ]
    },
    'stat_defense': {
        'normal': [
            "Damage reduction from incoming attacks",
            "Higher defense means less damage taken in combat",
            "Defense reduces physical damage by a percentage",
            "Improve defense through equipment and skills",
            "Defensive stat that mitigates incoming damage",
        ],
        'dumbed-down': [
            "This makes your panda harder to hurt. Like armor but... statsier.",
            "Defense = how tough your panda is. More = good!",
            "This number makes attacks hurt less. It's like a safety cushion!",
            "Think of it as your panda's toughness level. Bigger is better!",
            "How well your panda can take a hit without crying.",
        ],
        'vulgar': [
            "Defense. Makes you harder to kill. Pretty fucking important. Survival stat. Tank mode. Become invincible.",
            "How much of a tank your panda is. More = less ouchie. Pain reduction. Damage mitigation. Science.",
            "Your damage resistance stat. High = laugh at enemy attacks. Mocking enabled. Taunts optional.",
            "This shit reduces how much you get hurt. Stack it! More defense. Less pain. Simple math.",
            "Defense means you can take a beating. Level this up, fool. Become bulletproof. Metaphorically. Mostly."
        ]
    },
    'stat_strength': {
        'normal': [
            "Physical power and melee damage multiplier",
            "Strength increases damage dealt with physical attacks",
            "Higher strength = more devastating attacks",
            "Primary stat for physical combat effectiveness",
            "Boosts all melee and physical damage output",
        ],
        'dumbed-down': [
            "This is your panda's muscles! Big muscles = big damage!",
            "Strength makes you hit harder. Like, way harder. SMASH!",
            "How strong your panda is. More strength = enemies go bye-bye faster.",
            "The 'how hard can this panda punch' stat. Make it BIG!",
            "This number decides if you tickle enemies or obliterate them.",
        ],
        'vulgar': [
            "Strength. Hit harder, kill faster. It's that fucking simple. Violence efficiency. Murder mathematics. Basic calculus.",
            "Your panda's ability to absolutely wreck shit. Pump this up! Destruction capacity. Chaos potential. Maximize it.",
            "How much pain your panda can dish out. More = more carnage. Pain delivery system. Optimized.",
            "The 'crush your enemies' stat. Max this bad boy out. Conan the Barbarian energy. Flex those muscles.",
            "Strength means you hit like a goddamn truck. Stack it! Impact force. Bone-crushing power. Unstoppable."
        ]
    },
    'stat_magic': {
        'normal': [
            "Magical power and spell effectiveness",
            "Increases damage and potency of magical abilities",
            "Higher magic stat unlocks more powerful spells",
            "Determines success rate of magical effects",
            "Core stat for spellcasting and magic damage",
        ],
        'dumbed-down': [
            "Magic power! Makes your spells go BOOM instead of poof.",
            "This is how magical your panda is. More magic = cooler spells!",
            "The 'can this panda do magic tricks' stat. Spoiler: yes!",
            "Makes your magic spells actually do something instead of fizzle.",
            "How much wizard energy your panda has. Make it sparkly!",
        ],
        'vulgar': [
            "Magic stat. Makes you a fucking wizard. Abracadabra, bitches! Spell-slinging champion. Arcane badass.",
            "Your panda's 'turning enemies into toast' power. Magic! Bread-based violence. Delicious destruction.",
            "This shit makes spells hurt. More magic = more pain. Magical murder. Enchanted agony. Spell damage.",
            "The sorcery stat. High enough and you're basically Gandalf. Staff optional. Wisdom mandatory. Fireworks guaranteed.",
            "Magic power. Shoot fireballs and watch shit burn! Pyromania sanctioned. Arson justified. Flames everywhere."
        ]
    },
    'stat_intelligence': {
        'normal': [
            "Mental acuity and magical damage bonus",
            "Intelligence amplifies spell damage and magic effects",
            "Higher INT increases magic critical chance",
            "Governs learning speed and ability effectiveness",
            "Determines maximum mana and magic regeneration",
        ],
        'dumbed-down': [
            "How smart your panda is! Smart pandas cast better spells!",
            "Intelligence = brain power. More brains = stronger magic!",
            "The 'is this panda a genius' stat. Make it brainy!",
            "Think of it like... how much your panda studied at wizard school.",
            "Smart pandas do more magic damage. Be a smart panda!",
        ],
        'vulgar': [
            "Intelligence. Be smart, cast better spells, fuck shit up. Big brain energy. Nerd power. Knowledge is destruction.",
            "Your panda's IQ basically. Higher = better magic damage. Smart equals deadly. Einstein with fireballs.",
            "The 'how big brain is this panda' stat. Make it huge! Cranial capacity. Mental magnitude. Brain big.",
            "Intelligence means your magic actually works. Don't be dumb! Study. Learn. Dominate. Graduate.",
            "Brain power stat. More brain = more magical destruction. Scholarly violence. Academic ass-kicking. PhD in pain."
        ]
    },
    'stat_agility': {
        'normal': [
            "Speed, evasion, and critical hit chance",
            "Higher agility increases dodge probability",
            "Determines attack speed and movement",
            "Affects critical strike chance in combat",
            "Core stat for evasive and precision-based builds",
        ],
        'dumbed-down': [
            "How fast and nimble your panda is! Zoom zoom, dodge dodge!",
            "Agility = not getting hit. Also hitting enemies in their face more often!",
            "This makes your panda quick like... a quick panda!",
            "The 'can this panda dodge stuff' stat. Make it swooshy!",
            "Fast pandas dodge better and crit more. Be speedy!",
        ],
        'vulgar': [
            "Agility. Be fast, dodge shit, land crits. It's clutch. Speed is life. Fast pandas don't die.",
            "Your panda's 'try to hit me, I dare you' stat. Pump this! Dodge master. Untouchable. Neo mode.",
            "Speed and dodge chance. High agility = untouchable badass. Matrix-style bullet dodging. Effortless.",
            "This shit lets you dodge like Neo and crit like a boss. Bend spoons. Dodge bullets. Win fights.",
            "Agility means you're fast as fuck and hard to hit. Stack it! Speed demon. Lightning panda. Zoom."
        ]
    },
    'stat_vitality': {
        'normal': [
            "Constitution and health pool modifier",
            "Each point of vitality increases maximum health",
            "Determines survivability and endurance",
            "Affects health regeneration rate",
            "Essential stat for tanks and survival builds",
        ],
        'dumbed-down': [
            "This makes your health bar bigger! More health = live longer!",
            "Vitality = how much health your panda has. Big health = good!",
            "The 'don't die easily' stat. More vitality = more life!",
            "Think of it as your panda's toughness juice. Get more!",
            "Vitality gives you more HP so you don't die as fast. Useful!",
        ],
        'vulgar': [
            "Vitality. More HP, harder to kill. Don't be a glass cannon. Be a tank. Survival first.",
            "This shit increases your health pool. More = survive longer. Health is wealth. Stack it high.",
            "Your panda's 'I ain't dying today' stat. Max this bitch! Immortality pending. Death delayed.",
            "Vitality means you can take more beatings. Very fucking important. Pain tolerance. Maximum endurance.",
            "Health modifier stat. Stack this if you like being alive. Survival instinct. Self-preservation. Smart."
        ]
    },
    'stat_skill_points': {
        'normal': [
            "Available points for skill tree progression",
            "Earned through leveling up and achievements",
            "Spend on unlocking and upgrading abilities",
            "Plan carefully - some skills require prerequisites",
            "Skill points enable character customization",
        ],
        'dumbed-down': [
            "These are your 'buy cool abilities' points! Spend them wisely!",
            "Skill points = unlock new powers. Get them, spend them, be awesome!",
            "This is how many new abilities you can unlock right now!",
            "Think of these like... tokens at an arcade but for superpowers!",
            "You get these when you level up. Use them to get stronger!",
        ],
        'vulgar': [
            "Skill points. Spend 'em on abilities or hoard like a dragon. Your call. Decisions matter. Choose wisely.",
            "These let you unlock shit in the skill tree. Don't waste them! Precious resources. Invest carefully.",
            "Skill points = new abilities. More abilities = more ass-kicking. Power scaling. Growth potential.",
            "Use these to unlock skills and become a fucking powerhouse. Dominate. Conquer. Win everything.",
            "Points for buying cool powers. Spend wisely or you'll regret it. No refunds. Plan ahead. Think."
        ]
    },
    'stat_total_attacks': {
        'normal': [
            "Total number of attacks performed in combat",
            "Tracks all offensive actions taken",
            "Includes melee, ranged, and magical attacks",
            "Historical combat activity metric",
            "Cumulative attack count across all battles",
        ],
        'dumbed-down': [
            "How many times your panda has tried to hit something. A lot, probably!",
            "This counts every single time you pressed the attack button. Every. Single. Time.",
            "Attack counter! Goes up every time your panda goes 'HI-YAH!'",
            "The 'how aggressive is this panda' tracker. Spoiler: very!",
            "Total attacks ever. This number just keeps going up and up!",
        ],
        'vulgar': [
            "How many times your panda has thrown hands. The answer: a shit ton. Violence counter. Aggression metrics.",
            "Attack counter. Basically tracks how violent your panda is. Fury quantified. Rage measured.",
            "Total attacks launched. This number = your dedication to violence. Commitment issues? Not here.",
            "Every swing, every spell, every 'fuck you' attack. All counted here. Comprehensive. Detailed. Accurate.",
            "How many times you've tried to murder something. No judgment. Combat statistics. Death attempts."
        ]
    },
    'stat_monsters_slain': {
        'normal': [
            "Total enemies defeated in combat",
            "Tracks successful kills and takedowns",
            "Measure of combat prowess and experience",
            "Each victory contributes to this count",
            "Monster elimination statistics",
        ],
        'dumbed-down': [
            "How many bad guys your panda has defeated! Victory counter!",
            "This counts every monster you've beaten. You're a hero!",
            "Monster kill count! Higher = you're winning at life!",
            "The 'how many enemies did I destroy' tracker. Celebrate each one!",
            "Every monster defeated adds to this number. You did that!",
        ],
        'vulgar': [
            "Kill count. How many fuckers you've sent to the shadow realm. One-way tickets. No returns.",
            "Body count tracker. Your panda is a certified monster murderer. Professional killer. Licensed.",
            "Enemies slain. This number = your combat resume. Impressive! Hire-worthy. Deadly.",
            "How many things you've killed. Badge of honor, really. Achievement unlocked. Massacre master.",
            "Monster slayer stat. Higher = more badass. Keep killing! Slay button operational. Continue."
        ]
    },
    'stat_damage_dealt': {
        'normal': [
            "Total damage output across all combat encounters",
            "Cumulative offensive damage delivered",
            "Tracks effectiveness of your attacks",
            "Includes all damage types and sources",
            "Overall damage metrics for combat analysis",
        ],
        'dumbed-down': [
            "All the ouchies your panda has given to enemies. Big number = good panda!",
            "This is how much hurt you've delivered. The more the merrier!",
            "Total damage! Every hit adds up. You're doing great!",
            "The 'how much pain have I caused' counter. Lots, apparently!",
            "All your damage combined into one big impressive number!",
        ],
        'vulgar': [
            "Total pain delivered. How much fucking hurt you've dished out. Agony export. Suffering distribution.",
            "Damage dealt counter. Your legacy of destruction, quantified. Numbers don't lie. Violence verified.",
            "This is how much shit you've wrecked. Make it bigger! Destruction goals. Chaos metrics.",
            "Total damage output. Higher = you're a force of nature. Hurricane energy. Earthquake power.",
            "How much hurt you've put on enemies. Rack up those numbers! Pain provider. Hurt merchant."
        ]
    },
    'stat_damage_taken': {
        'normal': [
            "Total damage received from all sources",
            "Cumulative damage absorbed during combat",
            "Tracks how much punishment you've endured",
            "Includes all damage types received",
            "Durability and survival metrics",
        ],
        'dumbed-down': [
            "How many ouchies your panda has received. Lower is better!",
            "This is how much you've been hurt. Try to keep it down!",
            "Damage taken counter. Your panda is tough for surviving this much!",
            "The 'ouch counter' - every hit you've taken is tracked here.",
            "Total damage received. You've been through a lot, brave panda!",
        ],
        'vulgar': [
            "How much shit you've taken. Your survival badge of honor. Pain endured. Warrior scars.",
            "Damage received tracker. You've been through hell and lived! Survivor status. Tough bastard.",
            "This is your 'got my ass kicked but survived' stat. Proud of you. Resilience exemplified.",
            "Total beatings endured. You're still here so... winning? Alive equals victory. Math checks out.",
            "How much hurt you've tanked. Lower is better but hey, you're alive! Breathing = success."
        ]
    },
    'stat_critical_hits': {
        'normal': [
            "Number of critical strikes landed",
            "Critical hits deal amplified damage",
            "Tracks devastating blows and lucky strikes",
            "Critical strikes are marked by bonus damage",
            "Measure of combat effectiveness and luck",
        ],
        'dumbed-down': [
            "Super strong hits that do extra damage! These are the GOOD hits!",
            "Critical hits = when you hit REALLY hard. Like, BOOM hard!",
            "The 'extra awesome attack' counter. More crits = more fun!",
            "Sometimes you hit so good it's critical. This counts those!",
            "Special powerful hits that hurt way more. You love to see it!",
        ],
        'vulgar': [
            "Crit count. Those beautiful bastard hits that just DELETE enemies. One-shot potential. Instant death.",
            "Critical strikes. When your attack says 'fuck you' extra hard. Bonus damage. Maximum pain.",
            "How many times you've hit like a goddamn truck. Beautiful. Devastating. Perfect.",
            "Crits = bonus damage. The game saying 'nice fucking hit, dude!' Congratulations. Excellence.",
            "Critical hit tracker. Each one is a moment of pure destruction. Perfection achieved. Repeatedly."
        ]
    },
    'dungeon_enter_button': {
        'normal': [
            "Enter a procedurally generated dungeon with multiple floors",
            "Explore dungeons, fight monsters, and collect treasure",
            "Begin your dungeon crawling adventure",
            "Challenge yourself in randomly generated dungeons",
            "Start a new dungeon exploration session",
        ],
        'dumbed-down': [
            "Click this to go into a dungeon! It's like a video game inside a video game!",
            "Dungeon time! Fight monsters, get loot, have fun! Simple!",
            "This button starts an adventure! Press it and see what happens!",
            "Enter the dungeon! There's monsters and treasure and stuff!",
            "Click here to go on an adventure! Your panda is ready!",
        ],
        'vulgar': [
            "Enter the fucking dungeon! Fight shit, get loot, be a legend! Adventure awaits. Glory calls.",
            "Dungeon button. Click it if you've got the balls to explore! Courage required. Bravery essential.",
            "Ready to crawl some dungeons? This button says 'let's go!' Adventure time. Hero hour.",
            "Enter here to kick ass and take names in randomly generated hell! Chaos guaranteed. Fun promised.",
            "Dungeon time, baby! Click this and prepare for chaos! Mayhem mode. Violence vacation."
        ]
    },
    'dungeon_wasd_controls': {
        'normal': [
            "Use WASD or arrow keys to navigate the dungeon",
            "Move your character through the dungeon corridors",
            "Standard movement controls for dungeon exploration",
            "Navigate using keyboard directional controls",
            "Control your panda's movement with WASD keys",
        ],
        'dumbed-down': [
            "WASD makes your panda walk! W=up, A=left, S=down, D=right! Easy!",
            "These keys move your panda around. Like walking but with buttons!",
            "Press W-A-S-D to go places! It's like a tiny joystick!",
            "Movement keys! Press them and your panda walks that way!",
            "WASD = walking controls. Simple as that!",
        ],
        'vulgar': [
            "WASD to move your ass around. Not rocket science, people. Basic controls. Standard operation.",
            "Movement keys. W-A-S-D. You've played games before, right? RIGHT? Common knowledge. Universal.",
            "Use WASD to navigate. Pretty fucking standard controls here. Gaming 101. Elementary shit.",
            "Move with WASD. If you can't figure this out, I can't help you. Self-explanatory. Intuitive. Easy.",
            "Walking controls. WASD. That's it. Don't overcomplicate this. Simple. Direct. Functional."
        ]
    },
    'dungeon_attack_control': {
        'normal': [
            "Press Space to attack nearby enemies",
            "Attack enemies within melee range",
            "Combat action key for engaging monsters",
            "Deal damage to adjacent enemies",
            "Primary attack button for dungeon combat",
        ],
        'dumbed-down': [
            "Space bar = punch! Press it near bad guys to hit them!",
            "This makes your panda attack! Press it to fight monsters!",
            "The fight button! Press Space when near enemies to KAPOW them!",
            "Attack key! Get close to monsters and press this to bonk them!",
            "Press Space to make your panda go HI-YAH! at enemies!",
        ],
        'vulgar': [
            "Space bar = violence. Press it near enemies to fuck them up. Combat engaged. Damage delivered.",
            "Attack button. Get in range and press Space to wreck shit. Destruction initiated. Pain incoming.",
            "Space = beatdown time. Press it to introduce enemies to pain. Meet. Greet. Delete.",
            "Combat button. Press Space to remind monsters who's boss. Dominance asserted. Hierarchy established.",
            "Attack key. Space bar. Use it to murder things. Got it? Clear? Understood? Good."
        ]
    },
    'dungeon_stairs_control': {
        'normal': [
            "Press E when standing on stairs to change floors",
            "Use stairs to navigate between dungeon levels",
            "Floor transition key for multi-level exploration",
            "Move up or down floors using the E key",
            "Interact with stairs to access different levels",
        ],
        'dumbed-down': [
            "E key = use stairs! Stand on stairs and press E to go up or down!",
            "This makes you use stairs! Find stairs, stand on them, press E!",
            "Stairs button! E makes you climb up or go down levels!",
            "Press E on stairs to change floors! Like an elevator but stairs!",
            "The 'use stairs' key! E when on stairs = go to new floor!",
        ],
        'vulgar': [
            "E = use fucking stairs. Stand on them, press E, change floors. Easy.",
            "Stairs key. Find stairs, press E, go to next floor. Not complicated.",
            "E button uses stairs. Up or down, doesn't matter. Just press it.",
            "Stair navigation. Press E when on stairs. Boom. New floor. Done.",
            "E key = level transition. Stand on stairs and press E. That's it.",
            "Press E on stairs. What are you, new here? It's called a staircase.",
            "Going up? Going down? Don't care. Just press E on the stairs.",
            "Stairs + E = new floor. I swear this ain't calculus.",
        ]
    },
    # --- Missing button tooltips ---
    'notepad_new': {
        'normal': [
            "Create a new note in the notepad",
            "Add a fresh note to your collection",
            "Start a brand new note",
        ],
        'vulgar': [
            "New note. Because your brain can't remember shit on its own.",
            "Create a note. Revolutionary concept, writing things down.",
            "Click here to pretend you're organized by taking notes.",
            "New note. The digital equivalent of a Post-it on your monitor.",
            "Start a note. Maybe this time you'll actually read it later.",
            "Brain full? Dump it in a note. The panda won't judge.",
            "Jot something down before your goldfish memory kicks in.",
            "Another note. Your notepad is becoming a novel at this point.",
        ]
    },
    'notepad_save': {
        'normal': [
            "Save all notes to disk",
            "Persist your notes so they survive app restarts",
            "Write all notes to the save file",
        ],
        'vulgar': [
            "Save your notes. Unless you want them to vanish into the void.",
            "Hit save before the universe conspires to crash your app.",
            "Save all notes. Because trusting RAM is like trusting a fart.",
            "Click save or cry later. Your choice, champ.",
            "Persist those beautiful thoughts. Or whatever gibberish you wrote.",
            "CTRL+S energy in button form. You know you need it.",
            "Save notes. The panda's seen too many lost masterpieces.",
            "Don't be that person who loses everything. Just save it.",
        ]
    },
    'notepad_delete': {
        'normal': [
            "Delete the currently selected note",
            "Remove this note permanently",
            "Discard the selected note",
        ],
        'vulgar': [
            "Delete this note. It served its purpose. Or didn't. Whatever.",
            "Yeet this note into oblivion. No take-backsies.",
            "Kill this note dead. Rest in pixels.",
            "Delete. Gone. Poof. Like it never existed.",
            "Nuke this note from orbit. It's the only way to be sure.",
            "Permanently erase this note. Hope it wasn't important!",
            "Trash this note. The recycle bin won't save you here.",
            "Say goodbye to this note. *plays taps on tiny trumpet*",
        ]
    },
    'open_sound_settings': {
        'normal': [
            "Open the sound settings panel",
            "Configure audio and sound effects",
            "Adjust volume and sound preferences",
        ],
        'vulgar': [
            "Open sound settings. Turn stuff up, turn stuff down, go wild.",
            "Audio tweaking time. Make the panda louder or shut him up.",
            "Sound settings. For when the panda's noises are too much. Or not enough.",
            "Configure your audio. Volume knobs for everything, basically.",
            "Sound settings. Because not everyone wants to hear the panda fart.",
            "Tweak the audio. DJ Panda in the house.",
            "Adjust sounds. The panda's got opinions about volume levels.",
            "Open sounds panel. Warning: the panda may judge your music taste.",
        ]
    },
    'open_customization': {
        'normal': [
            "Open the advanced UI customization panel",
            "Access themes, colors, cursors, and sound settings",
            "Customize the look and feel of the application",
        ],
        'vulgar': [
            "Open customization. Make this app look like YOUR garbage, not ours.",
            "Advanced customization. For the aesthetically obsessed.",
            "Themes, colors, cursors — the whole cosmetic surgery toolkit.",
            "Customize everything. The panda supports your artistic vision.",
            "Make it pretty. Or ugly. We don't kink-shame UI preferences.",
            "Open the beauty salon for your app. Makeover time.",
            "Advanced settings for advanced nerds. No offense. Okay, some offense.",
            "Pimp your UI. The panda's seen worse taste, probably.",
        ]
    },
    'save_settings': {
        'normal': [
            "Save all current settings and preferences",
            "Persist your configuration changes to disk",
            "Write settings to the configuration file",
        ],
        'vulgar': [
            "Save settings. Unless you enjoy reconfiguring everything. Every. Single. Time.",
            "Hit save or lose your precious settings. The choice is stupidly obvious.",
            "Save your settings before something catastrophic happens.",
            "Persist that config. Your future self will thank your current self.",
            "Save it. SAVE IT. The panda is begging you.",
            "Click save or enjoy the default experience next time. Your funeral.",
            "Save settings to disk. Not to the cloud. We're not that fancy.",
            "Settings saved = peace of mind. Settings not saved = chaos.",
        ]
    },
    'open_logs_dir': {
        'normal': [
            "Open the application logs directory in your file manager",
            "Browse to the folder containing log files",
            "Navigate to where log files are stored",
        ],
        'vulgar': [
            "Open logs folder. For when you need to prove the app isn't lying.",
            "Browse logs directory. CSI: Texture Edition.",
            "Find the log files. Because debugging is just fancy detective work.",
            "Open logs. Warning: may contain more info than you wanted.",
            "Logs directory. Where the app confesses all its sins.",
            "View log files. The app's diary, essentially.",
            "Open the logs folder. Spoiler: it's mostly stack traces.",
            "Dig through logs. The digital equivalent of dumpster diving.",
        ]
    },
    'open_config_dir': {
        'normal': [
            "Open the configuration directory in your file manager",
            "Browse to the folder containing config files",
            "Navigate to the application configuration location",
        ],
        'vulgar': [
            "Open config folder. Where all your preferences live rent-free.",
            "Browse to the config directory. Touch nothing unless you know what you're doing.",
            "Config files directory. Modify at your own risk, cowboy.",
            "Open the config folder. Here be dragons (and JSON files).",
            "Find your config. For when the UI settings aren't enough chaos.",
            "Config directory. One wrong edit and boom, factory reset time.",
            "Browse config files. The app's DNA, basically. Don't mutate it.",
            "Open config folder. The panda takes no responsibility for manual edits.",
        ]
    },
    'open_cache_dir': {
        'normal': [
            "Open the application cache directory in your file manager",
            "Browse to the folder containing cached data",
            "Navigate to where temporary cache files are stored",
        ],
        'vulgar': [
            "Open cache folder. It's like the app's junk drawer.",
            "Browse the cache. Spoiler: it's mostly thumbnails and regret.",
            "Cache directory. Where old data goes to die... slowly.",
            "Open cache. The app's version of shoving things under the bed.",
            "Find the cache folder. Delete it if you're feeling dangerous.",
            "Cache files. Temporary in theory, permanent in practice.",
            "Browse cache. The digital equivalent of your browser history.",
            "Open cache directory. Warning: it's bigger than you think.",
        ]
    },
    'browser_smart_search': {
        'normal': [
            "Enable smart search to find textures by content type, not just filename",
            "Smart search uses AI categories to match textures by what they depict",
            "Search by content: type 'gun' to find weapon textures even if filenames differ",
        ],
        'vulgar': [
            "Smart search ON. Now finding textures by what they actually are. Revolutionary.",
            "Turn on the big brain search. It knows what a gun texture looks like.",
            "Smart search: because filenames lie but pixels don't.",
            "Enable AI-powered search. The panda went to college for this.",
            "Smart search. Like Google, but for your messy texture folder.",
            "Turn this on and type 'gun' — boom, weapon textures appear. Magic.",
            "Big brain search mode. Matches by content, not some random filename.",
            "Smart search: for when whoever named these textures was drunk.",
        ]
    },

    # ── Batch Rename Panel ─────────────────────────────────────────
    'rename_date': {
        'normal': [
            "Rename files using their creation date as the new filename",
            "Use file creation dates for automatic chronological naming",
            "Date-based renaming organizes files by when they were created",
            "Assign filenames derived from creation timestamps",
        ],
        'vulgar': [
            "Rename by date. Because 'IMG_20231217_final_FINAL_v3' is not a naming convention, it's a cry for help.",
            "Date-based naming. Finally, your files will know what fucking day they were born.",
            "Let the dates do the talking. At least SOMETHING in your workflow has a sense of time.",
            "Chronological naming. Revolutionary concept for someone who names files 'asdfasdf.png'.",
            "Sort by date because you clearly can't be trusted to name things yourself.",
            "Date stamps: the only honest thing about your file management system.",
        ],
        'dumbed-down': [
            "This renames your files using the date they were created. So instead of 'texture1.png' you might get '2024-01-15_texture.png'.",
            "Pick this to name files by when they were made. Great for keeping things in order!",
        ],
    },
    'rename_template': {
        'normal': [
            "Enter a custom naming pattern using placeholders like {name}, {num}, {date}, {ext}",
            "Define a template pattern for batch renaming with variable substitution",
            "Create naming rules with placeholders that get replaced during rename",
            "Build custom filename patterns using template variables",
        ],
        'vulgar': [
            "Write your naming template. Use {name}, {num}, {date}. It's like Mad Libs but for files and less fun.",
            "Template time! {name}_{num}.{ext} or whatever unholy naming scheme your brain conjures up.",
            "Custom patterns. Because you're a unique snowflake who can't use the damn presets like everyone else.",
            "Build your own filename format. With great power comes great responsibility. Try not to fuck it up.",
            "Template editor. {name} = original name, {num} = number. Not that complicated. I believe in you. Barely.",
            "Placeholder madness! Mix and match like a DJ, but instead of sick beats you get... filenames. Living the dream.",
        ],
        'dumbed-down': [
            "Type a naming pattern here. Use {name} for the original name, {num} for a number, {date} for date, {ext} for file type.",
            "This is where you write your own naming rule. Placeholders like {name} get replaced with real info.",
        ],
    },
    'rename_copyright': {
        'normal': [
            "Set copyright metadata to embed in renamed files",
            "Add copyright information to file metadata during rename",
            "Embed ownership details in the renamed files' metadata",
            "Include copyright text in file properties",
        ],
        'vulgar': [
            "Slap your copyright on these files like a dog marking territory. It's YOUR art now, dammit.",
            "Copyright metadata. Because someone will steal your textures and you'll want legal ammunition.",
            "Mark your damn territory. Add copyright info so everyone knows who made this masterpiece. Or disaster.",
            "Embed copyright. In case some asshole tries to claim your textures as their own. We've all been there.",
            "Copyright protection: cheaper than a lawyer, almost as effective, and way less annoying.",
        ],
        'dumbed-down': [
            "Type your name or copyright notice here. It gets saved inside the file's hidden info so people know who made it.",
            "This adds an invisible tag to your files saying who owns them. Like writing your name on your lunchbox.",
        ],
    },
    'rename_preview': {
        'normal': [
            "Preview of how files will be renamed before applying changes",
            "See the new filenames before committing to the rename operation",
            "Review rename results without modifying any files yet",
            "Check the before/after comparison of filenames",
        ],
        'vulgar': [
            "Preview before you commit. Unlike that tattoo you got in Cancun, this is reversible.",
            "Look before you leap. See what your files WILL look like. No surprises, no regrets, no therapy bills.",
            "Preview mode. Because 'undo' exists but prevention is better than crying over corrupted filenames.",
            "Check the preview unless you enjoy living dangerously. And by dangerously I mean stupidly.",
            "See the future! Your files' future, that is. Less exciting than a crystal ball but more accurate.",
        ],
        'dumbed-down': [
            "This area shows you what the new filenames will look like BEFORE anything actually changes. Safe to look!",
            "A preview of the rename. Nothing has changed yet — this just shows you what WILL happen when you click apply.",
        ],
    },
    'rename_undo': {
        'normal': [
            "Undo the last rename operation and restore original filenames",
            "Revert files back to their original names",
            "Reverse the most recent batch rename",
            "Restore previous filenames if the rename didn't work out",
        ],
        'vulgar': [
            "UNDO. The most beautiful word in any language. Unfuck what you just fucked.",
            "Ctrl+Z's cooler, buffer older brother. Restores your original filenames like nothing happened.",
            "Made a mistake? Of course you did. Hit undo and pretend it never happened. We won't tell anyone.",
            "Undo button: because nobody gets it right the first time. NOBODY. Not even you, perfectionist.",
            "Reverse! Go back! Abort! Whatever you want to call it, this button fixes your oopsie.",
            "Time travel for filenames. Takes them right back to before you messed everything up. Again.",
        ],
        'dumbed-down': [
            "Oops button! Click this to put all the filenames back to what they were before the rename.",
            "Changed your mind? This undoes the last rename and restores the original filenames.",
        ],
    },

    # ── Color Correction Panel ─────────────────────────────────────
    'cc_white_balance': {
        'normal': [
            "Adjust the color temperature — left for cooler (blue), right for warmer (yellow)",
            "Correct the white balance to make colors look natural",
            "Shift color temperature between cool and warm tones",
            "Fine-tune the overall color cast of the image",
        ],
        'vulgar': [
            "White balance. Make your textures less 'filmed in a gas station bathroom' and more 'professional studio'.",
            "Color temperature slider. Left = ice cold blue, Right = warm golden. Like a mood ring for your images.",
            "Fix that ugly yellow cast. Or blue cast. Whatever crime against color your camera committed.",
            "Slide left for 'Arctic tundra vibes', slide right for 'my GPU is literally on fire'. Find the sweet spot.",
            "White balance: because your monitor lied to you about what these colors actually look like.",
            "Temperature control. Not for your thermostat — for your textures. Though both need adjusting, clearly.",
        ],
        'dumbed-down': [
            "Slide this to fix colors that look too blue (cold) or too yellow (warm). The middle is usually natural-looking.",
            "If your image looks tinted blue or orange, this slider fixes it. Move it until the colors look right.",
        ],
    },
    'cc_exposure': {
        'normal': [
            "Adjust the overall brightness/exposure of the image",
            "Increase exposure to brighten or decrease to darken",
            "Control the lightness and darkness of the entire image",
            "Fine-tune image brightness for optimal visibility",
        ],
        'vulgar': [
            "Exposure slider. Too dark? Crank it up. Too bright? Turn it down. Rocket science, I know.",
            "Make it brighter or darker. Like the emotional spectrum of your last code review.",
            "Brightness control. Because 'I can't see shit' and 'MY EYES' are both valid complaints.",
            "Exposure adjustment: the difference between 'moody atmospheric' and 'did you forget the lights?'",
            "Slide right to blind yourself, slide left to enter the void. Somewhere in the middle is perfection.",
            "Fix the brightness because apparently your camera and the sun had a disagreement about exposure.",
        ],
        'dumbed-down': [
            "Makes the image brighter or darker. Slide right = brighter, slide left = darker.",
            "If your image is too dark to see or too bright and washed out, this slider fixes it.",
        ],
    },
    'cc_vibrance': {
        'normal': [
            "Boost color intensity without over-saturating vivid colors",
            "Enhance muted colors while preserving already-vivid tones",
            "Intelligently increase color saturation across the image",
            "Add punch to dull colors without destroying bright ones",
        ],
        'vulgar': [
            "Vibrance: makes dull colors pop without turning everything into a damn clown painting.",
            "Smart saturation. Unlike regular saturation, this one has taste. Unlike you. I'm kidding. Maybe.",
            "Add color punch without the neon nightmare. Subtle. Refined. Not like your Photoshop crimes.",
            "Boost those sad, desaturated colors back to life. It's like CPR but for pixels.",
            "Vibrance slider: the difference between 'stylistic choice' and 'did a toddler do this?'",
            "Make colors pop. Tastefully. We're going for 'wow' not 'dear god my retinas'.",
        ],
        'dumbed-down': [
            "Makes dull colors more vivid without making already-bright colors go crazy. A gentler version of saturation.",
            "Slide right to make colors pop more. Unlike saturation, this won't make things look neon.",
        ],
    },
    'cc_clarity': {
        'normal': [
            "Enhance midtone contrast to add crispness and detail",
            "Increase local contrast for sharper-looking textures",
            "Add definition and punch to image details",
            "Fine-tune midtone sharpness without affecting highlights or shadows",
        ],
        'vulgar': [
            "Clarity slider. Makes everything look crispy and detailed. Like upgrading from potato cam to actual camera.",
            "Add crispness. Your textures will look sharper than your wit. And that's saying something.",
            "Midtone contrast magic. Makes textures look professional AF without actually being professional.",
            "Clarity: because 'slightly blurry but whatever' is not an acceptable quality standard. Allegedly.",
            "Sharpen those midtones. Go from 'was this rendered on a calculator?' to 'damn that's clean.'",
            "Crank up the clarity and watch your textures go from 'meh' to 'MAGNIFICENT.' Or at least 'decent.'",
        ],
        'dumbed-down': [
            "Makes details in the image look sharper and crisper. Higher = more detail visible.",
            "Adds crispness to the image. Think of it like turning up the 'sharpness' specifically for the medium-bright parts.",
        ],
    },
    'cc_lut': {
        'normal': [
            "Load a LUT (Look-Up Table) file for color grading — supports .cube and .3dl",
            "Apply cinematic color grading presets via LUT files",
            "Import a color lookup table for professional color treatment",
            "Use industry-standard LUT files for consistent color grading",
        ],
        'vulgar': [
            "Load a LUT file. It's like an Instagram filter but for people who actually know what they're doing.",
            "LUT files: .cube and .3dl. Professional color grading without the professional price tag. Or skill.",
            "Import a LUT and instantly look like you spent 6 hours color grading. Our little secret.",
            "Color LUTs: because 'I just cranked the saturation to 11' is not a color grading strategy.",
            "Load a look-up table. Fancy name for 'make everything look cinematic with zero effort.' You're welcome.",
            "LUT loading. Turn your game textures into Christopher Nolan's wet dream. Or at least a dry one.",
        ],
        'dumbed-down': [
            "Load a .cube or .3dl file that changes all the colors at once — like a fancy filter for your images.",
            "A LUT is basically a color recipe file. Load one and it recolors your image in a specific style.",
        ],
    },

    # ── Image Repair Panel ─────────────────────────────────────────
    'repair_diagnose': {
        'normal': [
            "Analyze images for corruption, truncation, and header errors",
            "Scan selected files to detect any damage or formatting issues",
            "Run diagnostic checks on images to find repairable problems",
            "Identify corrupted headers, truncated data, and checksum mismatches",
        ],
        'vulgar': [
            "Diagnose what's wrong with your broken-ass images. Like a doctor but for pixels. And cheaper.",
            "Scan for corruption. Someone's gotta look at the damage after you played 'what if I close without saving.'",
            "Let the panda play detective. Who murdered these pixels? Headers corrupted, data truncated, dreams shattered.",
            "Image autopsy time. Let's figure out how these files died and if CPR is even an option.",
            "Run diagnostics. Find out if your images are slightly sick or completely fucked. Fingers crossed.",
            "Corruption scan. Like antivirus but for your texture files. Less dramatic, equally necessary.",
        ],
        'dumbed-down': [
            "Click this to check your images for problems — like missing data, broken headers, or incomplete files.",
            "This scans your selected files and tells you if anything is wrong with them, like a doctor's checkup.",
        ],
    },
    'repair_fix': {
        'normal': [
            "Attempt to repair detected issues in selected images",
            "Fix corrupted headers, rebuild truncated data, correct checksums",
            "Apply automatic repairs to damaged image files",
            "Restore broken images using header reconstruction and data recovery",
        ],
        'vulgar': [
            "REPAIR. Unfuck these images. Fix headers, rebuild data, perform pixel surgery. No anesthesia needed.",
            "Hit repair and pray. Just kidding, the panda's actually good at this shit. Usually. Probably.",
            "Fix button. Like duct tape for corrupted images but actually works and doesn't leave residue.",
            "Attempt repairs. Key word: attempt. We're optimistic but realistic. Like a therapist for files.",
            "Restore your broken images from the dead. Necromancy for PNG files. Totally legal, I checked.",
            "Repair time. Headers get fixed, checksums get corrected, and your files stop being digital corpses.",
        ],
        'dumbed-down': [
            "Click to try fixing the problems that were found. It'll patch up corrupted data and fix broken file info.",
            "This tries to fix broken images automatically. Not everything can be saved, but it does its best!",
        ],
    },
    'repair_results': {
        'normal': [
            "Diagnostic and repair results with details of issues found",
            "Review the report showing what was detected and what was fixed",
            "View detailed results of the analysis and repair operations",
            "Check the outcome of diagnostic scans and repair attempts",
        ],
        'vulgar': [
            "Results panel. See what's broken, what got fixed, and what's beyond saving. Like a relationship status update.",
            "The damage report. Read it and weep. Or celebrate. Depends on how badly you fucked up your files.",
            "Detailed results. Every issue found, every fix attempted. It's like reading your file's medical records.",
            "Check results. Good news and bad news. The bad news: your files were corrupted. The good news: we probably fixed them.",
            "Results area. Where dreams are confirmed or crushed. No pressure or anything.",
        ],
        'dumbed-down': [
            "This area shows what was found and what was fixed. Green = good, red = still broken.",
            "The report of what the scan found and what the repair did. Read through it to see what happened.",
        ],
    },

    # ── Performance Dashboard ──────────────────────────────────────
    'perf_speed': {
        'normal': [
            "Current processing speed measured in files per second",
            "Shows how fast files are being processed right now",
            "Real-time throughput indicator for the current operation",
            "Monitor the processing rate of the active task",
        ],
        'vulgar': [
            "Processing speed. Files per second. Like a speedometer but for boring office work. Vroom vroom.",
            "Speed indicator. How fast the panda's chewing through your files. Spoiler: faster than you could do it manually.",
            "Files per second. Higher is better. Lower means your computer is having an existential crisis.",
            "Throughput meter. Watch the numbers go up and pretend you understand what they mean.",
            "Speed stat. Like checking your car's mph except you're measuring file-crunching velocity. Less fun, equally nerdy.",
        ],
        'dumbed-down': [
            "Shows how many files are being processed every second. Higher number = faster!",
            "A speedometer for file processing. The bigger the number, the faster things are going.",
        ],
    },
    'perf_memory': {
        'normal': [
            "Current memory (RAM) used by the application",
            "Shows how much system memory is being consumed",
            "Monitor RAM usage to avoid out-of-memory issues",
            "Track application memory footprint in real-time",
        ],
        'vulgar': [
            "RAM usage. How much memory we're hogging. If this gets too high, close some of your 47 Chrome tabs.",
            "Memory consumption. Like watching your bank account after Steam sales. It only goes in one direction.",
            "RAM meter. If it turns red, blame Chrome, not us. We're practically anorexic compared to that memory glutton.",
            "How much memory we're eating. Don't worry, we're on a diet. Unlike your browser with 200 tabs open.",
            "Memory usage: the silent killer of performance. Keep an eye on it or your PC will remind you the hard way.",
        ],
        'dumbed-down': [
            "Shows how much of your computer's memory (RAM) this app is using. If it gets really high, things might slow down.",
            "This is like checking how full a bucket is — it shows how much memory the app is using right now.",
        ],
    },
    'perf_cpu': {
        'normal': [
            "Current CPU utilization percentage for the application",
            "Shows processor load from active operations",
            "Monitor how much processing power is being used",
            "Track CPU usage to balance performance and responsiveness",
        ],
        'vulgar': [
            "CPU usage. How hard your processor is sweating right now. If it's at 100%, pour one out for your fan.",
            "Processor load. Higher means we're working harder. Or your CPU is having a panic attack. Same thing, really.",
            "CPU meter. Watch your processor earn its keep instead of sitting there mining crypto. Wait, you're not... right?",
            "How much brain power your CPU is burning. If it hits 100%, congratulations, you found its limit. Or a bug.",
            "CPU percentage. Fun fact: your processor right now is doing more work than your entire team combined. Probably.",
        ],
        'dumbed-down': [
            "Shows how hard your computer's brain (CPU) is working. 100% means it's maxed out.",
            "Think of this as a 'how busy is my computer' meter. Lower is more relaxed.",
        ],
    },
    'perf_queue': {
        'normal': [
            "Number of files waiting in the processing queue",
            "Shows how many items are pending in the task queue",
            "Monitor remaining work in the processing pipeline",
            "Track the backlog of files awaiting processing",
        ],
        'vulgar': [
            "Queue depth. How many files are standing in line like it's Black Friday at Best Buy.",
            "Files waiting. Like a DMV queue but these actually move. And nobody's arguing about expired IDs.",
            "Pending items. The digital equivalent of 'your call is important to us, please hold.' But faster.",
            "Queue counter. Watch it go down and feel that sweet, sweet dopamine of progress. Better than social media.",
            "Files in line. They're patient, unlike you refreshing this panel every 2 seconds. Relax. Grab a coffee.",
        ],
        'dumbed-down': [
            "How many files are still waiting to be processed. This number goes down as work gets done.",
            "Think of it like a line at a store — this shows how many files are still waiting their turn.",
        ],
    },
    'perf_workers': {
        'normal': [
            "Number of parallel worker threads for processing — more workers use more CPU/memory",
            "Configure how many simultaneous processing threads to use",
            "Adjust parallelism: higher values process faster but use more resources",
            "Set the number of concurrent workers for batch operations",
        ],
        'vulgar': [
            "Worker threads. More pandas on the job = faster results. But also more RAM eaten. Balance, young grasshopper.",
            "Thread count. Crank it up for speed, dial it down if your PC starts sounding like a jet engine.",
            "Parallel workers. Like hiring more employees except they don't need coffee breaks or health insurance.",
            "How many threads to throw at the problem. The answer is usually 'as many as your RAM can handle before crying.'",
            "Worker slider. More threads = faster. Until your CPU melts. Then it's slower. And expensive. And on fire.",
            "Concurrency control. Sounds fancy. It means 'how many things happen at once.' You're welcome for the explanation.",
        ],
        'dumbed-down': [
            "How many tasks run at the same time. More = faster, but uses more computer power. Start low if unsure.",
            "Like hiring more helpers — more workers means faster results, but your computer works harder too.",
        ],
    },

    # ── Quality Checker Panel ──────────────────────────────────────
    'qc_analyze': {
        'normal': [
            "Run quality analysis on selected texture files",
            "Check textures for common issues like incorrect dimensions or compression artifacts",
            "Scan images for quality problems and potential optimizations",
            "Analyze texture quality metrics including resolution, format, and compression",
        ],
        'vulgar': [
            "Quality check. Let the panda judge your textures like a drunk art critic at a gallery opening.",
            "Analyze button. Time to find out if your textures are 'professional quality' or 'made in MS Paint.'",
            "Run quality scan. Spoiler alert: there's always something wrong. ALWAYS. Don't shoot the messenger.",
            "Check your textures for problems you didn't know existed. Ignorance was bliss, knowledge is power.",
            "Quality analysis: because 'it looks fine on MY monitor' is not a valid QA process, Kevin.",
        ],
        'dumbed-down': [
            "Click this to check if your images have any quality problems like wrong sizes or bad compression.",
            "Runs a quality check on your selected files and tells you if anything could be improved.",
        ],
    },
    'qc_results': {
        'normal': [
            "View quality analysis results and recommendations",
            "Review detected issues with suggested fixes",
            "Check the quality report for each analyzed texture",
            "See detailed metrics and improvement suggestions",
        ],
        'vulgar': [
            "Results. The moment of truth. Let's see how many textures passed and how many need to repeat the grade.",
            "Quality report card. Some A's, some F's, and a lot of 'see me after class.' Just like high school.",
            "Detailed results. Read them and weep. Or celebrate. Mostly weep, in my experience.",
            "Analysis results. Everything the panda found wrong with your textures. It's a long list. Get comfortable.",
            "Report time. Find out which textures are worthy and which ones belong in the recycling bin. Harsh but fair.",
        ],
        'dumbed-down': [
            "Shows what the quality check found. It lists any problems and suggests how to fix them.",
            "The results of the quality scan. Look here to see what's good and what needs fixing.",
        ],
    },
    'qc_export': {
        'normal': [
            "Export the quality analysis report to a text file",
            "Save the quality check results for review or sharing",
            "Download quality metrics as a formatted report",
            "Write the analysis results to a file on disk",
        ],
        'vulgar': [
            "Export report. Because showing proof of your texture crimes is sometimes necessary. Evidence!",
            "Save the report. Print it out, frame it, hang it on your wall of shame. Or fix the problems. Your call.",
            "Export results. Share with your team so everyone knows whose textures suck the most. Accountability!",
            "Save the report. Keep receipts of which textures are garbage. Digital forensics for pixel detectives.",
            "Export button. Because 'the panda said my textures are bad' isn't convincing without documentation.",
        ],
        'dumbed-down': [
            "Saves the quality report to a text file so you can read it later or share with others.",
            "Click to export — it creates a file with all the results from the quality check.",
        ],
    },
    'qc_dpi': {
        'normal': [
            "Set the target DPI for quality analysis (72=screen, 300=print)",
            "Choose the DPI standard to check textures against",
            "Select the resolution threshold for quality evaluation",
            "Configure the DPI baseline for the quality checker",
        ],
        'vulgar': [
            "DPI setting. 72 for screens, 300 for print, 600 for absolute overkill. Pick your poison.",
            "Dots per inch. The number that tells you if your textures are HD or potato quality. No middle ground.",
            "Target DPI. Set it high and watch everything fail. Set it low and feel great about mediocrity. Balance!",
            "DPI picker. Like choosing between a microscope and binoculars for judging your pixel density.",
            "Resolution standard. 72 DPI is 'meh' for print but fine for screens. 300 is 'chef's kiss' for everything.",
        ],
        'dumbed-down': [
            "Pick the DPI to check against. 72 is normal for screens, 300 is for printing. Higher = stricter checks.",
            "DPI is like detail density. 72 is standard for digital, 300 is needed for sharp prints.",
        ],
    },

    # ── Batch Normalizer Panel ─────────────────────────────────────
    'bn_normalize': {
        'normal': [
            "Normalize textures to a consistent format, resolution, and color space",
            "Standardize all selected textures to match your target specifications",
            "Batch process images to uniform dimensions and format settings",
            "Apply normalization rules across all selected texture files",
        ],
        'vulgar': [
            "Normalize. Make all your textures match like a uniform. Conformity! Structure! Not anarchy!",
            "Batch normalize. Because having 47 different formats and resolutions is not 'creative diversity,' it's chaos.",
            "Standardize everything. Like a dictator but for pixel dimensions. A benevolent one, though. Mostly.",
            "Hit normalize and watch the panda whip your textures into shape. Boot camp for pixels.",
            "Make everything consistent. Same format, same size, same quality. OCD paradise. You're welcome.",
        ],
        'dumbed-down': [
            "Click to make all your images the same size, format, and quality. Great for consistency!",
            "Standardizes your files so they all match the settings you picked above.",
        ],
    },
    'bn_format': {
        'normal': [
            "Select the target format for normalized output files",
            "Choose which image format all textures will be converted to",
            "Set the output format for the normalization process",
            "Pick the standard format for your normalized textures",
        ],
        'vulgar': [
            "Pick your format. PNG, DDS, TGA — choose your fighter. They all have strengths and weaknesses. Like Pokémon.",
            "Output format selector. Choose wisely. Or don't. You can always normalize again. We're patient.",
            "Target format. The 'what do I want these files to be when they grow up' dropdown.",
            "Format selection. PNG for quality snobs, DDS for game devs, TGA for people stuck in 2005.",
            "Choose a format. Any format. Just PICK ONE and stop overthinking it. Analysis paralysis is real.",
        ],
        'dumbed-down': [
            "Pick what file type you want your images saved as. PNG is great for quality, DDS is common in games.",
            "Choose the output format — all your files will be converted to this type.",
        ],
    },
    'bn_resolution': {
        'normal': [
            "Set the target resolution for normalized textures",
            "Choose the output dimensions for batch normalization",
            "Define width and height for the standardized output",
            "Configure the target texture resolution",
        ],
        'vulgar': [
            "Resolution picker. 512x512? 1024x1024? 4K? How much VRAM do you want to MURDER today?",
            "Set the size. Bigger isn't always better. That's what she— I mean, that's what the GPU said.",
            "Target resolution. Where you decide if your game runs at 60fps or 6fps. Choose wisely.",
            "Dimensions. The eternal struggle between 'it looks beautiful' and 'my GPU is literally on fire.'",
            "Pick a resolution. Pro tip: if your laptop sounds like a helicopter, maybe go smaller.",
        ],
        'dumbed-down': [
            "Set the width and height for your output images. Common game sizes are 512, 1024, or 2048 pixels.",
            "Choose how big or small the final images should be. Bigger = more detail but larger file size.",
        ],
    },
    'bn_resize_mode': {
        'normal': [
            "Choose how images are resized: fit, fill, stretch, or none",
            "Select the resize method for batch normalization",
            "Configure resize behavior when target dimensions differ from source",
            "Set the strategy for scaling images to the target size",
        ],
        'vulgar': [
            "Resize mode. Fit = polite cropping. Fill = aggressive cropping. Stretch = war crimes against aspect ratios.",
            "How to resize. 'Fit' keeps proportions. 'Stretch' does not. 'None' is for commitment-phobes.",
            "Scaling strategy. Fit, fill, stretch, or none. Like dating options but for pixels.",
            "Resize method. Stretch makes everything look drunk. Fit is classy. Fill is somewhere in between.",
            "Pick how resizing works. 'Fit' preserves sanity. 'Stretch' preserves nothing. Choose wisely.",
        ],
        'dumbed-down': [
            "How images get resized. 'Fit' keeps proportions, 'Fill' crops to fill, 'Stretch' forces the size, 'None' skips resizing.",
            "Choose the resize method. 'Fit' is usually best — it scales without distortion.",
        ],
    },
    'bn_output_format': {
        'normal': [
            "Select the output image format (PNG, JPEG, WEBP, TIFF)",
            "Choose which file format to save normalized images as",
            "Set the target format for batch output files",
            "Pick the output file type for normalized textures",
        ],
        'vulgar': [
            "Output format. PNG for lossless perfection, JPEG for 'good enough,' WEBP for hipsters, TIFF for dinosaurs.",
            "File format picker. PNG = safe. JPEG = lossy but small. WEBP = cool and modern. TIFF = why though?",
            "Choose a format. PNG is king. JPEG is acceptable. WEBP is the cool new kid. TIFF is… still here somehow.",
            "Export format. Like choosing your weapon: PNG (sword), JPEG (dagger), WEBP (laser), TIFF (trebuchet).",
            "Pick the output format. All roads lead to pixels, but some roads are lossier than others.",
        ],
        'dumbed-down': [
            "Pick the file type to save as. PNG keeps all quality, JPEG is smaller but loses some, WEBP is a good balance.",
            "Choose your output format. PNG is best for quality, JPEG for smaller files.",
        ],
    },
    'bn_quality': {
        'normal': [
            "Set output quality for JPEG/WebP formats (50-100)",
            "Adjust compression quality for lossy formats",
            "Control the quality-to-filesize tradeoff",
            "Configure the compression level for output files",
        ],
        'vulgar': [
            "Quality slider. 100 = pixel perfection. 50 = JPEG artifact hellscape. Find your comfort zone.",
            "Compression quality. Crank it up for beauty, dial it down for tiny files. The eternal tradeoff.",
            "Quality setting. Higher = prettier. Lower = smaller. It's like the attractiveness vs. rent analogy.",
            "JPEG/WebP quality. 95+ is chef's kiss. Below 70 is a cry for help. You've been warned.",
            "Quality control. This slider determines if your textures look professional or like they were faxed.",
        ],
        'dumbed-down': [
            "Controls how much quality is kept when saving as JPEG or WEBP. Higher is better looking but bigger files.",
            "Slide right for better quality, left for smaller files. Only affects JPEG and WEBP formats.",
        ],
    },
    'bn_padding': {
        'normal': [
            "Choose padding fill method when resizing with 'fit' mode",
            "Select what fills the empty space when image doesn't fill target dimensions",
            "Configure the padding type for resized images",
            "Set the border fill strategy for padded areas",
        ],
        'vulgar': [
            "Padding mode. What fills the gaps when your image doesn't fit. Transparent, black, white, blur, or edge magic.",
            "Fill the void! When images don't fit the target size, this picks what goes in the empty space. Existential padding.",
            "Padding type. Transparent = honest. Black = dramatic. White = clean. Blur = artistic. Edge extend = sneaky.",
            "What goes in the borders? Transparent for layering, black for drama, blur for 'I meant to do that' vibes.",
            "Padding selector. Because empty space needs filling. Like your schedule. And your fridge. But for pixels.",
        ],
        'dumbed-down': [
            "When an image is resized smaller than the target, this fills the remaining space. Transparent is usually best.",
            "Picks what color or effect fills empty borders. Try 'transparent' for layering or 'blur' for a smooth look.",
        ],
    },

    # ── Line Art Converter Panel ───────────────────────────────────
    'la_convert': {
        'normal': [
            "Convert images to clean line art renditions",
            "Extract line work from textures and photographs",
            "Generate line art versions of your images",
            "Process images through the line art extraction algorithm",
        ],
        'vulgar': [
            "Hit convert and watch your ugly-ass textures turn into actual art. You're welcome.",
            "Line art extraction. Strip away the colors like ripping off a band-aid — what's left is the good shit.",
            "Generate line art. Because your raw images look like ass and need a serious damn makeover.",
            "Convert to lines. Make any image look like it was drawn by someone who isn't a talentless hack.",
            "Line art button. Turns your garbage into gallery-worthy sketches. Don't thank me, thank the algorithm.",
            "Click this and your images go from 'what the hell is that' to 'oh damn, that's clean.'",
        ],
        'dumbed-down': [
            "Click to turn your images into black-and-white line drawings, like a coloring book version.",
            "Converts your pictures into clean line art — just the outlines, no colors.",
        ],
    },
    'la_threshold': {
        'normal': [
            "Adjust the line detection sensitivity threshold",
            "Control how much detail is captured in the line art output",
            "Fine-tune the boundary between lines and background",
            "Set the sensitivity for edge detection in line extraction",
        ],
        'vulgar': [
            "Threshold slider. Too low and every damn pixel thinks it's a line. Too high and your image vanishes. Find the sweet spot, dipshit.",
            "Edge sensitivity. Crank it wrong and you'll either get a shitty Jackson Pollock or a blank-ass page.",
            "Line detection threshold. The fine line between 'holy shit that's detailed' and 'where the fuck did my image go?'",
            "Sensitivity control. It's a volume knob for line detail. Don't crank it to 11 unless you want pixel diarrhea.",
            "Threshold: decides if you get 'elegant sketch' or 'my printer shit the bed.' Adjust carefully.",
        ],
        'dumbed-down': [
            "Controls how sensitive the line detection is. Low = lots of detail, High = only strong edges. Try different values!",
            "Adjusts which edges get drawn as lines. Move it around until the output looks good to you.",
        ],
    },
    'la_style': {
        'normal': [
            "Select the line art style preset to use",
            "Choose between different line art rendering styles",
            "Pick a visual style for the line art output",
            "Configure the artistic style of the extracted lines",
        ],
        'vulgar': [
            "Style picker. Manga, sketch, blueprint, whatever floats your artsy little boat.",
            "Line art style. Are we going 'detailed comic book' or 'minimalist hipster nonsense'? You decide.",
            "Choose a style. Each one makes your images look like a different kind of pretentious.",
            "Art style dropdown. Pick one and pretend you made a deeply artistic decision. We won't judge. Much.",
            "Style presets. Because 'I want it to look cool but I don't know how' is a valid starting point.",
        ],
        'dumbed-down': [
            "Pick a style for the line art. Each one gives a different look — try them to see which you like!",
            "Choose what kind of line art you want. Options include sketch, manga, blueprint, and more.",
        ],
    },
    'la_preset': {
        'normal': [
            "Pick a ready-made preset to instantly configure all settings for a common line art style",
            "Quick-start presets: Clean Inks, Pencil Sketch, Bold Outlines, Comic Book, and more",
            "Select a preset to auto-fill all conversion settings — tweak afterwards if needed",
        ],
        'vulgar': [
            "Preset picker. Because manually tweaking 15 goddamn sliders is for masochists with too much free time.",
            "Pre-built recipes for line art. Ink for pros, Pencil for artsy dipshits, Coloring Book for your inner toddler.",
            "Too lazy to configure everything yourself? Same here, asshole. Pick a preset and pretend you know what you're doing.",
            "Presets: like fast food for line art — quick, satisfying, and you don't have to think. Perfect for your smooth brain.",
            "One-click magic. Pick a style, all the sliders move by themselves. Even you can't fuck this up.",
        ],
        'dumbed-down': [
            "Choose a pre-made style and all settings fill in automatically! Pick the closest one to what you want.",
            "Ready-made presets for common line art styles. Just pick one and go!",
        ],
    },
    'la_mode': {
        'normal': [
            "Select the line art conversion algorithm",
            "Choose between different conversion methods: pure black, threshold, edge detect, etc.",
            "Pick the conversion mode that best suits your input images",
            "Configure the core algorithm for line extraction",
        ],
        'vulgar': [
            "Conversion mode. Pure black, threshold, edge detect — pick your damn weapon of line extraction.",
            "Algorithm picker. Each mode converts differently. 'Pure black' is aggressive as hell. 'Sketch' is artsy bullshit. Both work.",
            "Mode dropdown. It's choosing between a scalpel and a goddamn chainsaw for extracting lines. Both get the job done.",
            "Pick your flavor. 'Edge detect' for nerds. 'Sketch' for pretentious fucks. No judgment. Okay, maybe a little.",
            "Conversion mode. Try them all, you coward. What's the worst that could happen? Bad line art? Already there.",
        ],
        'dumbed-down': [
            "Choose how the image gets converted to lines. 'Pure black' is simple, 'Edge detect' finds outlines, 'Sketch' is artistic.",
            "Pick a conversion mode — each one produces a different kind of line art. Try a few to see what you like!",
        ],
    },
    'la_contrast': {
        'normal': [
            "Boost contrast before conversion to strengthen line edges",
            "Increase image contrast to improve line art quality",
            "Enhance contrast for cleaner, more defined lines",
            "Pre-process contrast adjustment for better edge detection",
        ],
        'vulgar': [
            "Contrast boost. Crank it up to make lines POP like a motherfucker. 1.0 if you're boring. 3.0 if you've got balls.",
            "Pre-conversion contrast. Like espresso for your pixels — makes everything intense as shit. Too much? Prepare for chaos.",
            "Contrast slider. Higher = bolder lines. Lower = subtler. 1.0 = 'I'm too chickenshit to commit to anything.'",
            "Boost that contrast. Make your lines thicc and defined. Or don't, pussy. The panda supports all lifestyles.",
            "Contrast adjuster. Difference between 'elegant line art' and 'bold-ass graphic novel.' Both cool, different damn vibes.",
        ],
        'dumbed-down': [
            "Makes lines stronger or weaker. 1.0 is normal, higher makes bolder lines, lower makes softer ones.",
            "Adjusts contrast before converting. Slide right for stronger, more visible lines.",
        ],
    },
    'la_morphology': {
        'normal': [
            "Apply morphology operations to thicken or thin lines",
            "Use dilate/erode to adjust line thickness after conversion",
            "Post-process lines with morphological transformations",
            "Fine-tune line weight using mathematical morphology",
        ],
        'vulgar': [
            "Morphology. Dilate = fatten those lines like Thanksgiving dinner. Erode = slim 'em down. Gym membership for your damn pixels.",
            "Line thickness via math magic. Dilate adds bulk. Erode trims fat. Close fills gaps. It's plastic surgery for line art, bitch.",
            "Morphology ops. Sounds fancy as fuck. It's just making lines thicker or thinner. Don't overthink it, Einstein.",
            "Post-processing for line weight. 'Dilate' for chunky-ass lines. 'Erode' for delicate ones. 'None' for lazy bastards.",
            "Morphological operations. Big-ass words for simple shit: make lines fatter, thinner, or fill in gaps. Not rocket science.",
        ],
        'dumbed-down': [
            "Changes line thickness after conversion. 'Dilate' makes lines thicker, 'Erode' makes them thinner, 'None' leaves them as-is.",
            "Adjusts the weight of the lines. Try 'dilate' if lines are too thin, or 'erode' if they're too thick.",
        ],
    },

    'la_save_preset': {
        'normal': [
            "Save your current settings as a custom preset you can reuse later",
            "Create a named preset from the current slider and menu values",
            "Store these exact settings so you can apply them again with one click",
        ],
        'vulgar': [
            "Save this shit as a preset so you don't have to fuck around with 16 sliders again.",
            "Custom preset saver. Because your lazy ass shouldn't have to redo this every damn time.",
            "Bookmark these settings. You finally got it looking right — don't lose it, dumbass.",
            "Save preset: for when you accidentally nail the perfect settings and don't wanna lose 'em like an idiot.",
            "Click to immortalize your settings. The panda's sick of watching you tweak the same goddamn sliders.",
        ],
        'dumbed-down': [
            "Saves your current settings so you can use them again later without re-doing everything!",
            "Creates a custom preset — give it a name and it'll remember all your settings.",
        ],
    },
    'la_export': {
        'normal': [
            "Export the previewed line art result to a file on your computer",
            "Save the current preview as a PNG, JPEG, or BMP file",
            "Download the line art preview to your chosen location",
        ],
        'vulgar': [
            "Export this masterpiece before you accidentally close the damn window.",
            "Save the preview to a file. You know, so your work isn't completely pointless.",
            "Export button. Because staring at the preview forever doesn't actually save it, genius.",
            "Click to save the line art to disk. The panda ain't holding onto it for your lazy ass.",
            "Export the preview. Congrats, you made line art. Now save the damn thing.",
        ],
        'dumbed-down': [
            "Saves the line art preview to a file on your computer so you can use it!",
            "Click to export — pick where to save it and what format you want.",
        ],
    },

    # ── Line Art – file / preview buttons ─────────────────────────
    'la_select_files': {
        'normal': [
            "Pick individual image files to convert to line art",
            "Browse and select one or more images for conversion",
        ],
        'vulgar': [
            "Open the file picker and choose your damn images already.",
            "Click this to actually select files. They don't magically appear, smartass.",
        ],
        'dumbed-down': [
            "Opens a window so you can pick images to convert!",
        ],
    },
    'la_select_folder': {
        'normal': [
            "Select a folder — all supported images inside will be queued for conversion",
            "Batch-select an entire directory of images at once",
        ],
        'vulgar': [
            "Point at a folder and every image in there gets dragged into the line art grinder.",
            "Select a whole folder. Because picking files one-by-one is for masochists.",
        ],
        'dumbed-down': [
            "Pick a folder and every picture inside it gets added automatically!",
        ],
    },
    'la_browse_output': {
        'normal': [
            "Choose the directory where converted line art files are saved",
            "Set the output folder for your converted images",
        ],
        'vulgar': [
            "Pick where you want the converted files dumped. Not my problem if you lose them.",
            "Set the output folder. Or don't. Enjoy hunting for files on your cluttered desktop.",
        ],
        'dumbed-down': [
            "Pick the folder where your finished line art gets saved!",
        ],
    },
    'la_update_preview': {
        'normal': [
            "Re-render the preview with your current settings",
            "Refresh the before/after comparison with the latest settings",
        ],
        'vulgar': [
            "Hit this to actually SEE what your settings do. Revolutionary concept, right?",
            "Refresh the preview. Because staring at stale results helps absolutely nobody.",
        ],
        'dumbed-down': [
            "Click to update the preview so you can see how it looks now!",
        ],
    },
    'la_select_preview': {
        'normal': [
            "Choose a single image to preview before running the full batch",
            "Pick one image to test your settings on before converting everything",
        ],
        'vulgar': [
            "Pick ONE image to preview. Don't convert the whole batch just to realise you f***ed it up.",
            "Select a preview image. It's called 'testing your settings' — try it sometime.",
        ],
        'dumbed-down': [
            "Pick a picture to try your settings on before converting the whole batch!",
        ],
    },

    # ── Line Art – conversion controls ────────────────────────────
    'la_auto_threshold': {
        'normal': [
            "Let Otsu's method automatically pick the best threshold for each image",
            "Enable auto-threshold to skip manual threshold tuning",
        ],
        'vulgar': [
            "Let the computer figure out the threshold. It's literally smarter than you at this.",
            "Turn on Otsu's method and stop pretending you know the perfect threshold value.",
        ],
        'dumbed-down': [
            "Lets the app pick the best cutoff point automatically — just check the box!",
        ],
    },
    'la_background': {
        'normal': [
            "Set the background of the line art output: transparent, white, or black",
            "Choose what goes behind the lines — transparency, white, or black",
        ],
        'vulgar': [
            "Pick a damn background colour. Transparent if you're layering, white if you're basic, black if you're edgy.",
            "Background mode. Transparent keeps it classy, white is boring, black is dramatic.",
        ],
        'dumbed-down': [
            "Pick what colour goes behind the lines — clear, white, or black!",
        ],
    },
    'la_invert': {
        'normal': [
            "Swap black and white — lines become white on a dark background",
            "Invert the colour output for a negative effect",
        ],
        'vulgar': [
            "Flip the colours so everything's backwards. White lines on black — very artsy, very pretentious.",
            "Invert colours. Now your lines are white. Congratulations, you're an artist.",
        ],
        'dumbed-down': [
            "Flips the colours! Lines go white and background goes dark.",
        ],
    },
    'la_remove_midtones': {
        'normal': [
            "Crush gray values to pure black or white for crisp stencil-ready output",
            "Remove all in-between grays for a sharp two-tone result",
        ],
        'vulgar': [
            "Kill the grays. No mercy. Pure black and white or nothing.",
            "Obliterate every shade of gray. This isn't a gradient party, it's a STENCIL.",
        ],
        'dumbed-down': [
            "Gets rid of gray areas so everything is either black or white — nice and clean!",
        ],
    },
    'la_midtone_threshold': {
        'normal': [
            "Gray values above this are pushed to white (range: 128–255)",
            "Control where the midtone cutoff sits between gray and white",
        ],
        'vulgar': [
            "The midtone guillotine. Everything above this number becomes white. Chop chop.",
            "Set where gray dies and becomes white. Higher = more survives. Lower = brutal.",
        ],
        'dumbed-down': [
            "Slide to decide how much gray stays — higher means more grays become white!",
        ],
    },

    # ── Line Art – line modification ──────────────────────────────
    'la_sharpen': {
        'normal': [
            "Pre-sharpen the source image before conversion for crisper line edges",
            "Apply sharpening to the original image to improve line clarity",
        ],
        'vulgar': [
            "Sharpen the image first so your lines aren't a blurry mess. You're welcome.",
            "Enable pre-sharpening. Because blurry input makes blurry output. Shocking, I know.",
        ],
        'dumbed-down': [
            "Makes the picture sharper before converting — gives you cleaner lines!",
        ],
    },
    'la_sharpen_amount': {
        'normal': [
            "How aggressively to sharpen — 0.5 is subtle, 3.0 is extreme",
            "Controls the strength of the sharpening pass",
        ],
        'vulgar': [
            "Crank this up and your edges could cut steel. Or just set it to 1.2 like a normal person.",
            "Sharpen intensity. Low = gently nudging pixels. High = stabbing them into clarity.",
        ],
        'dumbed-down': [
            "Slide right for stronger sharpening, left for softer. Around 1.2 is usually good!",
        ],
    },
    'la_morph_iterations': {
        'normal': [
            "Number of times to apply the morphology operation (more = stronger effect)",
            "Increase to thicken or thin lines more aggressively",
        ],
        'vulgar': [
            "How many times to run morphology. Once is polite. Ten is 'I have no f***ing chill'.",
            "Iterations slider. Each pass makes the effect stronger. Don't come crying at 10.",
        ],
        'dumbed-down': [
            "More passes = stronger effect! Start at 1 or 2 and see how it looks.",
        ],
    },
    'la_kernel_size': {
        'normal': [
            "Size of the morphology brush in pixels (3, 5, 7, or 9)",
            "Bigger kernel = broader morphology effect on lines",
        ],
        'vulgar': [
            "Kernel size — basically how fat the morphology brush is. 3 is delicate, 9 is a sledgehammer.",
            "Pick the kernel size. Smaller = precise. Bigger = everything bleeds together. Choose wisely.",
        ],
        'dumbed-down': [
            "How big the brush is for thickening or thinning lines. 3 is small, 9 is big!",
        ],
    },

    # ── Line Art – cleanup ────────────────────────────────────────
    'la_denoise': {
        'normal': [
            "Remove small noise speckles and stray dots from the line art result",
            "Clean up tiny artifacts that aren't part of the actual line work",
        ],
        'vulgar': [
            "Kill the speckles. Every stray pixel gets obliterated. No survivors.",
            "Enable denoising to nuke those annoying little dots. Scorched-earth pixel policy.",
        ],
        'dumbed-down': [
            "Gets rid of tiny dots and specks that aren't part of the real lines!",
        ],
    },
    'la_denoise_size': {
        'normal': [
            "Minimum feature size to keep — smaller features below this are removed as noise",
            "Set how small a detail must be to be treated as noise and deleted",
        ],
        'vulgar': [
            "Anything smaller than this gets vaporised. Set it too high and your fine detail dies too. Balance, b*tch.",
            "Min feature size. Tiny = gentle cleanup. Big = 'everything under 10px can go f*** itself'.",
        ],
        'dumbed-down': [
            "Slide to set how small a speck has to be before it gets cleaned up. Start at 2!",
        ],
    },

    # ── Background Remover Panel ───────────────────────────────────
    'bg_mode': {
        'normal': [
            "Switch between background removal and object removal modes",
            "Toggle the removal mode: remove backgrounds or specific objects",
            "Select whether to remove the background or isolate objects",
            "Choose the removal operation type",
        ],
        'vulgar': [
            "Mode toggle. Background removal or object removal. Choose your destruction method.",
            "Remove the background or remove objects. Either way, something's getting erased from existence.",
            "Pick your mode. Background begone! Or object obliteration! Decisions, decisions.",
            "Toggle between 'nuke the background' and 'surgically remove that one thing.'",
            "Mode switch: full background annihilation or precision object deletion. Both satisfying.",
        ],
        'dumbed-down': [
            "Choose whether to remove the background (leaving your subject) or remove a specific object.",
            "This switches between two modes: one removes backgrounds, the other removes objects you select.",
        ],
    },
    'bg_preset': {
        'normal': [
            "Choose a preset optimized for your image type",
            "Select a preconfigured profile for optimal removal quality",
            "Pick a preset tuned for specific content types",
            "Use preset settings tailored for different image categories",
        ],
        'vulgar': [
            "Presets! Because manually tuning settings is for people with infinite time and patience. You have neither.",
            "Pick a preset. General, portrait, product — we did the thinking so you don't have to.",
            "Preset selector. Like fast food: quick, easy, and usually good enough.",
            "Choose a preset or spend an hour tweaking sliders. We both know which one you'll pick.",
        ],
        'dumbed-down': [
            "Pick a preset that matches your image type. 'General' works for most things, 'Portrait' is for people photos.",
            "Presets are pre-made settings that work well for different kinds of images. Just pick the closest match!",
        ],
    },
    'bg_edge': {
        'normal': [
            "Adjust edge feathering and refinement for smoother cutouts",
            "Control how smooth or sharp the edges of the cutout are",
            "Fine-tune the edge quality of the background removal",
            "Set the feathering amount for natural-looking edges",
        ],
        'vulgar': [
            "Edge slider. Make edges smooth or sharp. Smooth = professional. Sharp = 'I used scissors in MS Paint.'",
            "Feathering control. The difference between 'clean cutout' and 'my 5-year-old did this with safety scissors.'",
            "Edge refinement. Because jaggy edges are a war crime in the design world.",
            "Smooth those edges. Nobody likes a cutout that looks like it was torn out of a magazine. By a cat.",
        ],
        'dumbed-down': [
            "Makes the edges of the cutout smoother or sharper. Higher = softer/more blended edges.",
            "Controls how smooth the border is after removing the background. Try different values until it looks clean.",
        ],
    },
    'bg_model': {
        'normal': [
            "Select the AI model for background removal",
            "Choose which neural network model performs the removal",
            "Pick an AI model optimized for your use case",
            "Select the processing model for best results",
        ],
        'vulgar': [
            "AI model selector. Pick which robot brain processes your images. They're all good. Some are just more good.",
            "Choose your AI model. u2net for general, isnet for people, silueta for everything else. Easy peasy.",
            "Model picker. Like choosing a Pokémon starter but the stakes are lower and nobody judges your choice. Probably.",
            "Select the AI. Different brains for different tasks. None of them will become Skynet. Probably.",
        ],
        'dumbed-down': [
            "Pick which AI model removes the background. The default works for most images, but others may be better for specific types.",
            "Different models are good at different things. Try 'u2net' for general use or 'isnet' for people.",
        ],
    },
    'bg_alpha_matting': {
        'normal': [
            "Enable alpha matting for semi-transparent objects like hair or glass",
            "Use alpha matting for more precise edge handling on transparent areas",
            "Turn on advanced edge detection for translucent materials",
            "Enable fine-grained transparency handling at edges",
        ],
        'vulgar': [
            "Alpha matting. For when your subject has wispy hair and the AI needs to not butcher it.",
            "Turn this on for glass, hair, smoke, or anything see-through. Off = faster but choppier edges.",
            "Alpha matting: the 'please don't destroy my hair edges' checkbox. You're welcome.",
            "Enable this for translucent stuff. The AI tries harder. Emphasis on 'tries.'",
        ],
        'dumbed-down': [
            "Turn this on if your image has see-through parts like glass or wispy hair. It makes the edges better.",
            "Alpha matting helps with tricky edges on transparent or semi-transparent things. Takes longer but looks better.",
        ],
    },
}


class TooltipMode(Enum):
    """Tooltip verbosity modes"""
    NORMAL = "normal"
    DUMBED_DOWN = "dumbed-down"
    UNHINGED_PANDA = "vulgar_panda"  # Legacy value for backwards compatibility


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
        """Create tutorial sequence from categorized tutorials"""
        try:
            # Import categorized tutorials
            from src.features.tutorial_categories import get_tutorial_sequence
            
            # Get categorized steps
            categorized_steps = get_tutorial_sequence()
            
            # Convert to TutorialStep objects
            steps = []
            for cat_step in categorized_steps:
                step = TutorialStep(
                    title=cat_step.title,
                    message=cat_step.message,
                    target_widget=cat_step.target_widget,
                    highlight_mode=cat_step.highlight_mode,
                    arrow_direction=cat_step.arrow_direction,
                    show_back=cat_step.show_back,
                    show_skip=cat_step.show_skip,
                    button_text=cat_step.button_text,
                    celebration=cat_step.celebration
                )
                steps.append(step)
            
            logger.info(f"Created {len(steps)} tutorial steps from categorized system")
            return steps
            
        except Exception as e:
            logger.error(f"Failed to load categorized tutorials: {e}", exc_info=True)
            # Fallback to basic tutorial if categorized system fails
            return self._create_fallback_tutorial_steps()
    
    def _create_fallback_tutorial_steps(self) -> List[TutorialStep]:
        """Fallback tutorial if categorized system fails"""
        logger.warning("Using fallback tutorial steps")
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
                title="You're All Set! 🎉",
                message=(
                    "Congratulations! You're ready to start sorting textures!\n\n"
                    "Quick Tips:\n"
                    "• Press F1 anytime for context-sensitive help\n"
                    "• Check the Achievements tab for fun challenges\n"
                    "• Explore the Tools menu for advanced features\n\n"
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
            TooltipMode.UNHINGED_PANDA: self._get_unhinged_panda_tooltips()
        }
    
    def _load_mode(self) -> TooltipMode:
        """Load tooltip mode from config"""
        mode_str = self.config.get('ui', 'tooltip_mode', default='vulgar_panda')
        try:
            return TooltipMode(mode_str)
        except ValueError:
            return TooltipMode.UNHINGED_PANDA
    
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
            'pause_button': [
                "Pause the current sorting operation",
                "Temporarily halt sorting to review progress",
                "Freeze the sorting process; resume anytime",
                "Put sorting on hold without losing progress",
                "Suspend the current sorting task temporarily",
            ],
            'stop_button': [
                "Stop the sorting operation completely",
                "Cancel and terminate the current sort process",
                "End the sorting operation immediately",
                "Abort the current sorting task entirely",
                "Halt all sorting and discard remaining work",
            ],
            'sort_mode_menu': [
                "Choose the sorting mode: automatic, manual, or suggested",
                "Select how textures are categorized during sorting",
                "Switch between automatic and manual sorting strategies",
                "Pick a sorting approach that fits your workflow",
                "Configure the sorting method for texture organization",
            ],
            'extract_archives': [
                "Extract textures from compressed archives (ZIP, 7Z, RAR, TAR.GZ)",
                "Automatically unpack archive files to access textures",
                "Enable extraction of textures from compressed containers",
                "Detect and decompress archived texture files before sorting",
                "Support for extracting textures from common archive formats",
            ],
            'compress_output': [
                "Compress sorted output into a ZIP archive",
                "Bundle the organized textures into a compressed file",
                "Create a ZIP file from the sorted output directory",
                "Package results into a compressed archive for sharing",
                "Generate a ZIP archive of all sorted textures",
            ],
            'convert_from_format': [
                "Select the source format for texture conversion",
                "Choose which file format to convert textures from",
                "Set the input format for the conversion pipeline",
                "Pick the original format of your texture files",
                "Specify the current format of textures to convert",
            ],
            'convert_to_format': [
                "Select the target format for texture conversion",
                "Choose which file format to convert textures into",
                "Set the desired output format for converted files",
                "Pick the format your textures should be converted to",
                "Specify the destination format for texture conversion",
            ],
            'convert_recursive': [
                "Convert textures in all subdirectories recursively",
                "Include files from nested folders in conversion",
                "Process entire folder hierarchies during conversion",
                "Enable recursive scanning for texture conversion",
                "Traverse subdirectories to find and convert textures",
            ],
            'convert_keep_original': [
                "Keep original files after conversion completes",
                "Preserve source textures alongside converted files",
                "Don't delete originals during the conversion process",
                "Maintain a backup of original textures automatically",
                "Retain the original files when converting to a new format",
            ],
            'profile_new': [
                "Create a new game organization profile",
                "Set up a fresh profile with default settings",
                "Add a new configuration profile to your collection",
                "Start a new profile for a different game or project",
                "Initialize a blank profile for custom configuration",
            ],
            'settings_perf_tab': [
                "Open performance settings for threads, cache, and batch size",
                "Adjust processing performance and resource allocation",
                "Fine-tune speed settings for texture operations",
                "Configure CPU and memory usage for optimal performance",
                "Access performance tuning options for sorting and conversion",
            ],
            'settings_appearance_tab': [
                "Open appearance settings for themes, fonts, and visuals",
                "Customize the look and feel of the application",
                "Adjust theme, font size, and display preferences",
                "Configure visual options and UI style settings",
                "Personalize the application's appearance to your liking",
            ],
            'settings_controls_tab': [
                "Open controls settings for keyboard shortcuts",
                "Configure hotkeys and keyboard bindings",
                "Customize keyboard shortcuts for quick actions",
                "Set up control preferences and key mappings",
                "Manage keyboard input settings and shortcut assignments",
            ],
            'settings_files_tab': [
                "Open file settings for paths, formats, and handling",
                "Configure default directories and file preferences",
                "Set default input and output paths for convenience",
                "Adjust file processing and naming conventions",
                "Manage file-related configuration options",
            ],
            'settings_ai_tab': [
                "Open AI settings for vision models and categorization",
                "Configure AI-powered texture recognition options",
                "Set up machine learning models for smart sorting",
                "Adjust AI parameters for automatic categorization",
                "Manage AI model selection and analysis preferences",
            ],
            'settings_system_tab': [
                "Open system settings for updates, logging, and diagnostics",
                "Configure system-level preferences and maintenance",
                "Adjust update frequency, logging, and debug options",
                "Manage system behavior and diagnostic settings",
                "Access advanced system configuration and troubleshooting",
            ],
            'tooltip_mode_normal': [
                "Switch to normal tooltip mode with standard descriptions",
                "Use professional, clear tooltips for everyday use",
                "Select the default tooltip style with helpful text",
                "Enable standard tooltips with informative descriptions",
                "Choose the regular tooltip mode for balanced guidance",
            ],
            'tooltip_mode_dumbed_down': [
                "Switch to simplified tooltips for beginners",
                "Use easy-to-understand explanations for all features",
                "Select the beginner-friendly tooltip style",
                "Enable detailed, accessible tooltips for new users",
                "Choose simplified tooltips with extra guidance",
            ],
            'tooltip_mode_vulgar': [
                "Switch to Unhinged Panda mode for sarcastic tooltips",
                "Enable humorous, explicit tooltip language",
                "Select the irreverent adult-only tooltip style",
                "Activate Unhinged Panda mode for colorful commentary",
                "Choose the unfiltered, no-holds-barred tooltip experience",
            ],
            'shop_balance': [
                "View your current Bamboo Bucks balance",
                "Check how many Bamboo Bucks you have available",
                "See your spendable currency in the shop",
                "Display your current wallet balance",
                "Shows the Bamboo Bucks you can spend on items",
            ],
            'shop_level': [
                "View your current user level and rank",
                "Check your level to see what items you can unlock",
                "Your level determines which shop items are available",
                "See your experience level and progression status",
                "Display your current rank in the leveling system",
            ],
            'inventory_animations': [
                "Browse and play animation items for your panda",
                "Use collected animations to trigger panda actions",
                "Activate animation items from your inventory",
                "View available animation items and play them",
                "Select animations to entertain your panda companion",
            ],
            'popout_button': [
                "Pop this tab out into a separate window",
                "Detach the current tab into its own floating window",
                "Open this tab in an independent resizable window",
                "Undock this tab for use on another monitor",
                "Create a standalone window from this tab",
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
        base_tooltips = {
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
            'browser_show_archives': [
                "Check this box to also show archive files like ZIP, 7Z, and RAR "
                "in the file list. You can then click on them to browse inside!",
            ],
            'alpha_fix_button': [
                "Click this button to fix transparency problems in your textures. "
                "It removes white boxes, dark halos, and other alpha artifacts "
                "that happen with PS2 textures.",
            ],
            'alpha_fix_input': [
                "Click Browse to pick the folder that has your textures with "
                "transparency problems. The app will scan this folder for images.",
            ],
            'alpha_fix_output': [
                "Choose where to save the fixed textures. If you leave this empty, "
                "the app will fix them right where they are (in-place).",
            ],
            'alpha_fix_preset': [
                "Pick a fixing mode! 'ps2_binary' is best for UI icons and fonts. "
                "'ps2_smooth' keeps gradients. 'clean_edges' removes fringing around edges.",
            ],
            'alpha_fix_recursive': [
                "When checked, the app also looks inside subfolders for textures "
                "to fix, not just the main folder you selected.",
            ],
            'alpha_fix_backup': [
                "When checked, the app saves a copy of your original files before "
                "changing them, just in case you want to go back.",
            ],
            'alpha_fix_overwrite': [
                "When checked, the fixed version replaces your original file. "
                "Make sure you have backups enabled if you use this!",
            ],
            'alpha_fix_extract_archive': [
                "If your textures are inside a ZIP or other archive file, check "
                "this to automatically unpack them before fixing.",
            ],
            'alpha_fix_compress_archive': [
                "After fixing, this packs all the corrected textures into a "
                "ZIP file for easy sharing or storage.",
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
                "Dumbed Down gives extra detail, Unhinged adds humor.",
                "Control tooltip style: Normal, Beginner-friendly, or Unhinged "
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
                "Unhinged is... well, fun.",
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
            'pause_button': [
                "Click this to pause the sorting. It will stop but remember where it was, so you can continue later.",
                "This button pauses sorting. Nothing is lost — just click again to keep going.",
            ],
            'stop_button': [
                "Click this to completely stop sorting. You'll need to start over if you want to sort again.",
                "This button cancels the sorting process entirely. Use it if you want to stop and start fresh.",
            ],
            'sort_mode_menu': [
                "This lets you choose how sorting works. 'Automatic' does it all for you, 'Manual' lets you decide, and 'Suggested' gives recommendations.",
                "Pick a sorting mode here. If you're not sure, 'Automatic' is the easiest choice.",
                "This dropdown changes the sorting method. Try 'Automatic' first — it's the simplest.",
            ],
            'extract_archives': [
                "If your textures are inside ZIP or other compressed files, this will unpack them first so they can be sorted.",
                "This option opens compressed files (like ZIP) to get the textures out before sorting them.",
            ],
            'compress_output': [
                "After sorting, this packs everything into one ZIP file so it's easy to share or move.",
                "This creates a compressed ZIP file from your sorted textures.",
            ],
            'convert_from_format': [
                "Choose what format your textures are in right now (like PNG or DDS). This is the 'from' part of the conversion.",
                "Pick the current format of your texture files here.",
            ],
            'convert_to_format': [
                "Choose what format you want your textures to become (like PNG or DDS). This is the 'to' part of the conversion.",
                "Pick the format you want to convert your textures into.",
            ],
            'convert_recursive': [
                "When this is on, the converter looks inside all subfolders too, not just the main folder.",
                "Turn this on to convert textures in subfolders as well as the main folder.",
            ],
            'convert_keep_original': [
                "When this is on, your original files are kept safe. The converted files are saved alongside them.",
                "This keeps your original texture files instead of replacing them with the converted versions.",
            ],
            'profile_new': [
                "Click this to make a brand new profile. A profile saves all your settings so you can switch between different setups.",
                "This creates a new profile. Think of it like a save slot for your settings.",
            ],
            'settings_perf_tab': [
                "This tab has settings that affect speed — like how many processor threads to use and how much memory to allow.",
                "Performance settings control how fast things run. If the app feels slow, check here.",
            ],
            'settings_appearance_tab': [
                "This tab lets you change how the app looks — themes, font sizes, and other visual things.",
                "Change the app's appearance here. Pick a theme or adjust the font size.",
            ],
            'settings_controls_tab': [
                "This tab lets you set up keyboard shortcuts so you can do things faster with key presses.",
                "Configure your keyboard shortcuts here. Handy if you use the app a lot.",
            ],
            'settings_files_tab': [
                "This tab has settings about files — like default folder locations and file naming options.",
                "Set up where files go by default and how they're handled.",
            ],
            'settings_ai_tab': [
                "This tab controls the AI features that help automatically identify and sort textures.",
                "AI settings for smart texture sorting. The app can use AI to figure out what textures are.",
            ],
            'settings_system_tab': [
                "This tab has system-level settings like updates, error logs, and diagnostic options.",
                "System settings for updates and troubleshooting. You usually won't need to change these.",
            ],
            'tooltip_mode_normal': [
                "This sets tooltips to normal mode — clear and helpful descriptions of what things do.",
                "Normal tooltips give you straightforward, professional descriptions.",
            ],
            'tooltip_mode_dumbed_down': [
                "This sets tooltips to beginner mode — everything is explained in very simple language (like this!).",
                "Beginner tooltips explain things in the simplest way possible. Perfect if you're new!",
            ],
            'tooltip_mode_vulgar': [
                "This sets tooltips to vulgar mode — the descriptions are funny and use adult language, but still helpful.",
                "Unhinged Panda mode makes tooltips funny and sarcastic with some bad words. Still tells you what things do!",
            ],
            'shop_balance': [
                "This shows how many Bamboo Bucks you have. That's the currency you use to buy things in the shop.",
                "Your Bamboo Bucks balance — the money you earn from sorting and playing games.",
            ],
            'shop_level': [
                "This shows your current level. As you level up, you can buy more items in the shop.",
                "Your level number. Higher levels unlock more items to purchase.",
            ],
            'inventory_animations': [
                "This section shows animation items you own. Click one to make your panda do a fun action!",
                "Play animations on your panda! These are special items that trigger cute actions.",
            ],
            'popout_button': [
                "Click this to open the current tab in its own separate window. Useful if you have multiple monitors.",
                "This pops the tab out into a floating window you can move around independently.",
            ],
            'minigames_tab': [
                "Click here to play fun mini-games! You can earn Bamboo Bucks and other rewards while playing.",
                "This tab has mini-games you can play for fun and to earn rewards.",
            ],
            'closet_appearance': [
                "This shows what your panda is currently wearing. You can see all equipped clothing and accessories here.",
                "View your panda's current outfit — all the clothes and accessories they have on right now.",
            ],
            'closet_header': [
                "This is the closet where you dress up your panda! Pick outfits, hats, and accessories from items you own.",
                "The panda closet — use it to change what your panda wears.",
            ],
            'achievement_progress': [
                "This shows how far along you are in completing an achievement. The bar fills up as you make progress.",
                "A progress bar showing how close you are to finishing this achievement.",
            ],
            'about_button': [
                "Click here to see information about this app — the version, who made it, and credits.",
                "Shows app info like version number and developer credits.",
            ],
            'analysis_button': [
                "Click this to analyze your textures. It looks at each file and tells you about its size, format, and quality.",
                "Runs an analysis on your texture files to give you useful stats.",
            ],
            'armory_tab': [
                "This is where your panda's weapons and equipment are kept. Equip items for dungeon adventures!",
                "The armory stores all your panda's gear for battles and adventures.",
            ],
            'battle_arena': [
                "Enter the battle arena to fight enemies and earn rewards! Your panda uses equipped gear in combat.",
                "Fight stuff, earn rewards. It's a mini combat game for your panda.",
            ],
            'browser_smart_search': [
                "Smart search looks through your files using AI to find textures that match what you describe, even if the filename doesn't match.",
                "AI-powered search that finds files by what they look like, not just their name.",
            ],
            'category_selection': [
                "Pick which texture categories you want to sort into. You can check or uncheck types like UI, Characters, Environment, etc.",
                "Choose which categories to include when sorting your textures.",
            ],
            'cursor_selector': [
                "Pick a custom cursor style for the app. There are fun options like panda paws and bamboo!",
                "Change what your mouse cursor looks like inside the app.",
            ],
            'export_button': [
                "Click this to save/export your sorted textures to the output folder you selected.",
                "Exports your organized textures to the destination folder.",
            ],
            'favorites_button': [
                "Mark textures as favorites so you can quickly find them later. Like a bookmark for your files!",
                "Save textures to your favorites list for quick access.",
            ],
            'inventory_accessory': [
                "These are accessories you own for your panda — things like glasses, scarves, or jewelry. Equip them in the closet!",
                "Your panda's accessory collection. Go to the closet to put them on.",
            ],
            'inventory_food': [
                "Food items you have! Feed them to your panda to make them happy and restore energy.",
                "Your food stash. Feed your panda to boost their mood.",
            ],
            'inventory_toy': [
                "Toys you own! Give one to your panda and watch them play. It increases happiness!",
                "Your toy collection. Give toys to your panda for fun playtime.",
            ],
            'inventory_unlocked': [
                "A summary of all the special rewards you've earned so far by completing achievements and playing.",
                "Shows everything you've unlocked through playing and achievements.",
            ],
            'notepad_delete': [
                "Delete the current note. Be careful — this can't be undone!",
                "Removes the selected note permanently.",
            ],
            'notepad_new': [
                "Create a brand new empty note to write in.",
                "Start a fresh note from scratch.",
            ],
            'notepad_save': [
                "Save whatever you've written in the notepad so it's there when you come back.",
                "Saves your note so you don't lose it.",
            ],
            'open_cache_dir': [
                "Opens the folder where the app stores temporary files (cache). Useful for clearing space.",
                "Shows the cache folder on your computer.",
            ],
            'open_config_dir': [
                "Opens the folder where your settings and preferences are saved.",
                "Shows the config folder with your app settings.",
            ],
            'open_customization': [
                "Opens the customization panel where you can change how the app looks and feels.",
                "Go to customization options to personalize the app.",
            ],
            'open_logs_dir': [
                "Opens the folder where the app saves log files. Helpful for troubleshooting problems.",
                "Shows the logs folder for debugging.",
            ],
            'open_sound_settings': [
                "Opens sound settings where you can change volumes, pick sound packs, and adjust audio.",
                "Go to sound settings to change audio options.",
            ],
            'panda_sound_click': [
                "The sound your panda makes when you click on them.",
                "Click sound effect for the panda.",
            ],
            'panda_sound_dance': [
                "The sound that plays when your panda dances.",
                "Dancing sound effect.",
            ],
            'panda_sound_drag': [
                "The sound when you start dragging your panda around.",
                "Drag sound effect.",
            ],
            'panda_sound_drop': [
                "The sound when you let go and drop your panda.",
                "Drop/release sound effect.",
            ],
            'panda_sound_eat': [
                "The munching sound when your panda eats food.",
                "Eating sound effect.",
            ],
            'panda_sound_happy': [
                "A cheerful sound when your panda is happy!",
                "Happy emotion sound effect.",
            ],
            'panda_sound_jump': [
                "The sound when your panda jumps up.",
                "Jump sound effect.",
            ],
            'panda_sound_pet': [
                "A content purr-like sound when you pet your panda.",
                "Petting sound effect.",
            ],
            'panda_sound_play': [
                "A fun playful sound when your panda is playing.",
                "Play sound effect.",
            ],
            'panda_sound_sad': [
                "A sad whimper sound when your panda is unhappy.",
                "Sad emotion sound effect.",
            ],
            'panda_sound_sleep': [
                "Gentle snoring sounds when your panda sleeps.",
                "Sleep/snoring sound effect.",
            ],
            'panda_sound_sneeze': [
                "An adorable little sneeze sound!",
                "Sneeze sound effect.",
            ],
            'panda_sound_wake': [
                "A yawning wake-up sound when your panda wakes from sleep.",
                "Wake-up sound effect.",
            ],
            'panda_sound_walk': [
                "Soft footstep sounds when your panda walks around.",
                "Walking footstep sounds.",
            ],
            'panda_sound_yawn': [
                "A big sleepy yawn sound.",
                "Yawn sound effect.",
            ],
            'preview_button': [
                "Click this to see a preview of what the texture looks like before you process it.",
                "Shows a preview of the selected texture.",
            ],
            'recent_files': [
                "A list of files and folders you've worked with recently. Click one to open it again quickly.",
                "Quick access to your recently used files and folders.",
            ],
            'redo_button': [
                "Redo something you just undid. Like pressing Ctrl+Z backwards!",
                "Redo the last action you undid.",
            ],
            'rename_template': [
                "Type a naming pattern here. Use {name} for the original name, {num} for a number, {date} for today's date.",
                "Write your own naming rule using placeholders like {name} and {num}.",
            ],
            'save_settings': [
                "Save all your current settings so they stay the same next time you open the app.",
                "Saves your preferences so they persist between sessions.",
            ],
            'shop_item_name': [
                "Click on an item to see more details about it — what it looks like, how much it costs, etc.",
                "Select an item to view its description and price.",
            ],
            'sound_selection_panda': [
                "Choose which sounds your panda makes for different actions like clicking, dragging, eating, etc.",
                "Pick individual sounds for each panda action.",
            ],
            'sound_selection_system': [
                "Choose sounds for app actions like sorting, completing tasks, and notifications.",
                "Pick sounds for system events and notifications.",
            ],
            'sound_settings': [
                "Adjust all the sound options — volume levels, sound packs, and individual sound effects.",
                "Main sound settings panel for all audio options.",
            ],
            'travel_hub': [
                "The travel hub lets your panda visit different locations and discover new areas!",
                "Send your panda on trips to different places.",
            ],
            'undo_button': [
                "Undo the last thing you did. Works like Ctrl+Z in most programs.",
                "Takes back your last action.",
            ],
        }

        # Merge dumbed-down tooltip variants from the inlined definitions
        try:
            for widget_id, tooltip_dict in _PANDA_TOOLTIPS.items():
                if 'dumbed-down' in tooltip_dict:
                    base_tooltips[widget_id] = tooltip_dict['dumbed-down']
        except Exception as e:
            logger.warning(f"Error loading dumbed-down tooltips: {e}")

        return base_tooltips
    
    def _get_unhinged_panda_tooltips(self) -> Dict[str, Any]:
        """Fun/sarcastic tooltips (vulgar mode)"""
        base_tooltips = {
            'sort_button': [
                "Click this to sort your damn textures. It's not rocket science, Karen.",
                "Hit this button and watch your textures get organized. Magic, right?",
                "Sort your textures or live in chaos forever. Your damn choice.",
                "Organizing textures. Because your folder is a fucking war zone.",
                "Click to sort. Even a monkey could do it. Probably faster than you.",
            ],
            'convert_button': [
                "Turn your textures into whatever the hell format you need.",
                "Format conversion. Because one format is never enough for you people.",
                "Convert those textures. Abracadabra, format-change-a, motherfucker.",
                "Format alchemy. Turn PNG lead into DDS gold. Or whatever.",
                "File format conversion. It's not brain surgery, but it's close enough.",
            ],
            'input_browse': [
                "Find your texture folder. Come on, you can do this.",
                "Navigate to your texture folder. I believe in you. Maybe.",
                "Browse for your damn input folder. It's not gonna find itself.",
                "Pick the source folder. Where's your texture stash, you hoarder?",
                "Input directory selection. Point me to the goods, genius.",
            ],
            'output_browse': [
                "Where do you want this beautiful organized mess?",
                "Pick where the sorted stuff goes. Any folder. Your call.",
                "Choose the output destination. Where should this organized shit go?",
                "Output folder picker. Select a place for your sorted masterpiece.",
                "Destination directory. Where do you want your beautiful sorted textures?",
            ],
            'detect_lods': [
                "LOD detection. Fancy words for 'find the quality variants'.",
                "Find the blurry and sharp versions of the same texture. Science!",
                "LOD finder. Hunting down quality variants like a texture detective.",
                "Detect level-of-detail versions. Big textures, small textures, we find 'em all.",
                "LOD detection enabled. Your blurry thumbnails won't escape us.",
            ],
            'group_lods': [
                "Keep LOD buddies together. They get lonely apart.",
                "Group quality variants together. Like a texture family reunion.",
                "Group LODs together. Texture family therapy, basically.",
                "LOD grouping. Keeping related textures together so they don't get lonely.",
                "Buddy system for textures. No LOD left behind, dammit.",
            ],
            'detect_duplicates': [
                "Find duplicate textures. Because apparently you have trust issues.",
                "Spot the copycats. Your hard drive will thank you.",
                "Find the clones! Duplicate detection for paranoid perfectionists.",
                "Duplicate finder. Your hard drive is full of identical crap and you know it.",
                "Spot the copies. Cleaning up your mess one duplicate at a time.",
            ],
            'style_dropdown': [
                "How do you want your stuff organized? Pick one, any one.",
                "Organization style. Because everyone's a control freak about something.",
                "Sorting style selector. Pick your organizational poison.",
                "Choose your style. Flat, nested, by type — whatever makes your OCD happy.",
                "Style picker. How anal-retentive are you about folder structure?",
            ],
            'settings_button': [
                "Tweak shit. Make it yours. Go nuts.",
                "Settings. Where the magic happens. Or where things break.",
                "Configuration paradise. Or hell. Depends on how deep you go.",
                "Preferences! Tweak every little thing until it's perfect. Or broken.",
                "Settings menu. Enter at your own risk, you compulsive tweaker.",
            ],
            'theme_button': [
                "Dark mode = hacker vibes. Light mode = boomer energy.",
                "Toggle the dark side. Or the light side. No judgment.",
                "Theme toggle. Dark mode for vampires, light mode for psychopaths.",
                "Switch themes. Make it dark. Make it light. Make it whatever the hell you want.",
                "Theme button. Your eyes will either thank you or curse you.",
            ],
            'help_button': [
                "Lost? Confused? Click here, we'll hold your hand.",
                "Need help? That's what this button is for, genius.",
                "HELP! I need somebody! HELP! Not just anybody! Click this button.",
                "Assistance mode. For when you're too proud to Google it.",
                "Help button. We've all been there. No shame. Okay, a little shame.",
            ],
            'achievements_tab': [
                "Check your trophies, you overachiever.",
                "See how many fake awards you've collected. Congrats, I guess.",
                "Achievement gallery. Your digital trophy case of awesomeness.",
                "Check your achievements. Feel validated. Then chase the next one, addict.",
                "Virtual trophies for virtual accomplishments. Living the dream, champ.",
            ],
            'shop_tab': [
                "This is the loot cave. Spend your shiny points, idiot.",
                "The shop. Where your hard-earned points go to die.",
                "Shop time! Open your wallet and cry at the prices.",
                "The store. Where dreams are purchased and Bamboo Bucks go to die.",
                "Shopping spree! Everything's affordable if you sort enough textures.",
            ],
            'shop_buy_button': [
                "Yeet your money at this item. Do it.",
                "Buy it. You know you want to. Impulse control is overrated.",
                "BUY IT. Your virtual wallet can handle it. Probably.",
                "Purchase button. Money go bye-bye, item go hello!",
                "Spend those Bamboo Bucks. You can't take 'em with you.",
            ],
            'shop_category_button': [
                "Filter the shop. Because scrolling is for peasants.",
                "Narrow it down. Too many choices hurting your brain?",
                "Filter categories. Because the shop has more crap than Walmart.",
                "Category filter. Focus your shopping addiction on one section at a time.",
                "Sort the store items. Ironic, using a sorter to sort the sorter's shop.",
            ],
            'rewards_tab': [
                "Your loot table. See what you can unlock.",
                "All the shiny things you haven't earned yet. Motivating, right?",
                "Rewards! The carrot on the stick that keeps you sorting, you sucker.",
                "Unlockable goodies. Motivation to keep grinding, you beautiful fool.",
                "Reward list. See what you're missing out on. Feel the FOMO.",
            ],
            'closet_tab': [
                "Dress up your panda. Fashion show time.",
                "Panda makeover! Because even virtual bears need style.",
                "Panda fashion show! Outfits, accessories, the whole shebang.",
                "The closet! Where your panda gets dressed. Or undressed. We don't judge.",
                "Wardrobe section. Your panda has more style options than you do.",
            ],
            'browser_browse_button': [
                "Pick a folder. Any folder. Let's see what's inside.",
                "Open a folder. I promise we won't judge your file organization. Much.",
                "Browse folders. Navigate the digital wilderness of your file system.",
                "Folder picker. Point and click your way to texture discovery.",
                "Open a directory. Adventure awaits in your file system! ...maybe.",
            ],
            'browser_refresh_button': [
                "Refresh. In case something magically changed.",
                "Reload the file list. For the paranoid types.",
                "Refresh! Did something change? Probably not, but check anyway, paranoid.",
                "Reload the list. Insanity is doing this repeatedly expecting different results.",
                "Hit refresh. The digital equivalent of shaking a vending machine.",
            ],
            'browser_search': [
                "Find your damn files. Type something.",
                "Search for files. Use your keyboard. That's the thing with letters on it.",
                "Search box. Type what you want. Pray it exists.",
                "File search. Like Google but way more disappointing.",
                "Find files. Lost something? This is your only hope, padawan.",
            ],
            'browser_show_all': [
                "Show EVERYTHING. Even the weird files.",
                "Toggle this to see ALL files. Prepare yourself.",
                "Show all files. Even the ones you forgot existed. Especially those.",
                "Toggle full visibility. See EVERYTHING. Brace your eyeballs.",
                "All files mode. Warning: you might find things you wish you hadn't.",
            ],
            # Tab tooltips
            'sort_tab': [
                "The main event. Sort your textures or go home.",
                "Sorting tab. Where the real work happens.",
                "Sorting headquarters. Where the actual work gets done, slacker.",
                "The sorting tab. Your textures won't organize themselves, dumbass.",
                "Sort tab. AKA the reason this app exists. Try using it.",
            ],
            'convert_tab': [
                "Format conversion. Because one format is never enough.",
                "Convert stuff. DDS, PNG, whatever floats your boat.",
                "Conversion station. Transform textures like a format wizard.",
                "Convert tab. Format alchemy for the modern texture artist.",
                "Format conversion central. Turn your crap into slightly different crap.",
            ],
            'browser_tab': [
                "Snoop through your texture files like a pro.",
                "Browse your files. Digital window shopping.",
                "File browser. Your textures, all laid out for your viewing pleasure.",
                "Browse your files. It's like window shopping but for texture nerds.",
                "Browser tab. See what you've got before you wreck what you've got.",
            ],
            'notepad_tab': [
                "Scribble your thoughts. No one's judging. Maybe.",
                "Write notes. Or a novel. We don't care.",
                "Notepad. Write down important shit. Or doodle. I'm not your mother.",
                "Text editor. For the organized people who take notes. Show-offs.",
                "Notes tab. Jot something down before your goldfish memory forgets it.",
            ],
            'about_tab': [
                "Credits and keyboard shortcuts. Riveting stuff.",
                "Who made this thing and how to use it. Thrilling.",
                "About section. See who built this masterpiece and how to control it.",
                "Credits and shortcuts. The boring stuff nobody reads. Except you, apparently.",
                "About tab. Legal stuff, credits, and the secrets of keyboard shortcuts.",
            ],
            # Category tooltips
            'tools_category': [
                "The useful stuff. Sorting, converting, browsing.",
                "Work tools. The boring but necessary section.",
                "Tool belt. Sorting, converting, browsing — all the productive stuff.",
                "Work tools category. The stuff you SHOULD be using instead of playing games.",
                "The business section. No fun allowed. Just kidding. But seriously, work.",
            ],
            'features_category': [
                "The fun stuff. Panda, shop, achievements, bling.",
                "The cool extras. Panda time!",
                "Feature land! Where pandas roam and achievements are meaninglessly rewarding.",
                "The fun zone. Panda, shop, games — everything EXCEPT actual work.",
                "Extra features. AKA the reason you spend more time here than sorting.",
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
                "Normal is boring. Dumbed down is hand-holding. Unhinged is *chef's kiss*.",
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
                "How loud do you want this shit? Slide and find out.",
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
                "Enable/disable toggle. For when shortcuts start shit.",
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
            'pause_button': [
                "Pause this shit. Take a breather, you workaholic.",
                "Hit pause. Even texture sorting needs a damn intermission.",
                "PAUSE. Like a VCR. Google it, you young bastard.",
                "Time out! The sorting can wait while you question your life choices.",
                "Freeze frame! Everything stops. Dramatic, ain't it?",
            ],
            'stop_button': [
                "STOP. Full stop. Done. Finito. Kaput.",
                "Kill the process! MURDER IT! ...I mean, stop sorting.",
                "Emergency stop! Slam the brakes! Everything DIES!",
                "Abort mission! Pull the plug! Yeet the sorting into the void!",
                "Stop button. For when you realize you fucked up and need to bail.",
            ],
            'sort_mode_menu': [
                "Pick your sorting style. Auto for lazy asses, manual for control freaks.",
                "Sort mode selector. Choose your own damn adventure.",
                "Auto, manual, or suggested. Like a transmission but for textures, dumbass.",
                "How do you want your shit sorted? Make a decision for once in your life.",
                "Sorting approach menu. Spoiler: you'll pick auto because you're lazy.",
            ],
            'extract_archives': [
                "Unzip those compressed bastards. ZIP, 7Z, RAR — we crack 'em all open.",
                "Archive extraction. Free your textures from their zippered prison!",
                "Bust open those archives like a piñata full of textures!",
                "Extract from compressed files. Like performing surgery on a ZIP file.",
                "Archive support. We'll rip those textures out of whatever you stuffed them in.",
            ],
            'compress_output': [
                "Zip it all up. Not your mouth — the output folder, smartass.",
                "Compress output. Because sending 10,000 loose files is psychotic.",
                "Make a ZIP. Package your shit. Be a civilized human being.",
                "Compression mode. Squish those textures into a tidy little package.",
                "ZIP the output. Your disk space and your sanity will thank you.",
            ],
            'convert_from_format': [
                "What format is your crap in? Tell me so I can fix it.",
                "Source format. The 'before' picture of this texture makeover.",
                "FROM format. Step one: admit what format your textures are stuck in.",
                "Input format. What the hell am I working with here?",
                "Original format selector. What mess are we starting with today?",
            ],
            'convert_to_format': [
                "What format do you want? Choose your destiny, format warrior.",
                "Target format. The 'after' picture. Hopefully an improvement.",
                "TO format. Step two: pick where this format journey ends.",
                "Output format. What should your textures become? Choose wisely, grasshopper.",
                "Destination format. The promised land for your converted textures.",
            ],
            'convert_recursive': [
                "Go recursive! Dig through EVERY damn subdirectory like a mole on caffeine.",
                "Check subfolders too. Leave no directory un-converted, you thoroughbred.",
                "Recursive mode. Because your folder structure is deeper than the Mariana Trench.",
                "All subfolders included. We're going DEEP. That's what she said.",
                "Recursion activated. Folders within folders within folders. We'll find every last texture.",
            ],
            'convert_keep_original': [
                "Keep the originals. Because you trust NOTHING and NO ONE. Smart.",
                "Don't delete source files. Paranoia is a survival skill, honestly.",
                "Preserve originals. Double the files, double the fun, double the disk space.",
                "Keep both versions. You hoarding bastard. I respect it though.",
                "Safety mode ON. Original files stay. Your data anxiety is valid.",
            ],
            'profile_new': [
                "New profile. Because your current one is apparently not good enough.",
                "Create a fresh profile. Starting over is always an option, you disaster.",
                "Another profile?! How many configurations does one person NEED?!",
                "New profile button. For the serial restarter in all of us.",
                "Fresh start. New profile. New you. Same mess, probably.",
            ],
            'settings_perf_tab': [
                "Performance settings. Make it ZOOM or make it gentle. Your CPU, your rules.",
                "Speed tweaks for nerds. Threads, cache, batch size. Go nuts.",
                "Perf tab. Where you overclock your texture sorting like a damn madman.",
                "Performance tuning. Because 'it works' isn't good enough for you, is it?",
                "CPU and memory settings. Don't melt your computer, genius.",
            ],
            'settings_appearance_tab': [
                "Pretty settings. Make the app match your aesthetic, you vain creature.",
                "Appearance tab. Because functionality isn't enough — it has to LOOK good too.",
                "Theme and font settings. Interior decorating for software, basically.",
                "Visual config. Dark mode? Light mode? Clown mode? It's all here.",
                "Beautify the UI. Make those pixels dance to YOUR tune, drama queen.",
            ],
            'settings_controls_tab': [
                "Keyboard shortcuts. For people too elite to use a mouse.",
                "Controls. Rebind everything. Make Ctrl+Alt+Delete sort textures if you want.",
                "Hotkey city. Every button gets a keyboard shortcut. Go crazy, keyboard warrior.",
                "Key bindings tab. Because clicking is for PEASANTS.",
                "Controls config. Map keys, break things, blame the software.",
            ],
            'settings_files_tab': [
                "File settings. Tell the app where all your crap lives.",
                "Paths and formats. The boring-but-necessary file configuration shit.",
                "File handling prefs. Where do things go? How do they get there? Configure it.",
                "Default paths and naming. For organized people. So probably not you.",
                "File config. Because 'just put it wherever' isn't a valid strategy, Karen.",
            ],
            'settings_ai_tab': [
                "AI settings. Welcome to the future, where robots sort your textures.",
                "Machine learning config. Teach the computer brain. What could go wrong?",
                "AI tab. Skynet for texture organization. I for one welcome our robot overlords.",
                "Robot settings. Make the AI smarter so YOU can be lazier.",
                "AI configuration. The singularity starts with texture sorting, apparently.",
            ],
            'settings_system_tab': [
                "System settings. The 'don't touch unless you know what you're doing' section.",
                "Under the hood. Logs, updates, debug mode. Nerd central.",
                "System config. For tech masochists who enjoy reading log files.",
                "The engine room. Proceed with caution, you curious bastard.",
                "System tab. Where IT professionals feel at home and everyone else panics.",
            ],
            'tooltip_mode_normal': [
                "Normal mode. Boring. Professional. Adequate. Like plain oatmeal.",
                "Standard tooltips. For people who don't appreciate creative profanity.",
                "Vanilla mode. Zero spice. Zero fun. Maximum helpfulness, I guess.",
                "Normal tooltips. The safe option. The BORING option.",
                "Switch to normal. If you hate fun and joy, this is your mode.",
            ],
            'tooltip_mode_dumbed_down': [
                "Baby mode. Everything explained like you've never seen a computer before.",
                "ELI5 tooltips. No shame in needing extra help. Okay, maybe a little shame.",
                "Beginner mode. We'll hold your hand so gently. So, so gently.",
                "Dumbed down. For when regular tooltips have too many big words.",
                "Simple mode. Training wheels for your eyeballs. Adorable.",
            ],
            'tooltip_mode_vulgar': [
                "THIS MODE. THE BEST MODE. You're goddamn right.",
                "Unhinged Panda mode. Where the magic and the profanity happen.",
                "Welcome to the good shit. Why would you ever use another mode?",
                "The superior tooltip mode. Fight me if you disagree, coward.",
                "You want this one. Trust me. The other modes are for wimps.",
            ],
            'shop_balance': [
                "Your Bamboo Bucks. Probably not enough for anything good, you broke bastard.",
                "Balance check. Prepare for disappointment, window shopper.",
                "How much money you got? Not enough. Never enough. Grind harder.",
                "Your virtual wallet. Almost certainly emptier than your real one.",
                "Bamboo Bucks balance. You're not rich. Face it.",
            ],
            'shop_level': [
                "Your level. Higher number = bigger e-peen. Congrats.",
                "Level display. Are you high level yet? No? Sort more textures, scrub.",
                "Your rank. Flex it. Or don't. Nobody's impressed anyway.",
                "Level indicator. The number that determines if you're worthy of cool items.",
                "XP level. Grind your way up or stay a peasant. Your call.",
            ],
            'inventory_animations': [
                "Animation items. Make your panda do tricks like a trained circus bear.",
                "Play animations! Watch your panda be an idiot. It's hilarious.",
                "Panda tricks section. Dance, wave, whatever. They'll do anything for attention.",
                "Animations! Because watching a panda just sit there is boring as shit.",
                "Trigger panda animations. Free entertainment for your easily amused brain.",
            ],
            'popout_button': [
                "Pop this tab out! Like busting out of prison but for UI elements.",
                "Detach the tab. Let it be free! FREEDOM for windows!",
                "Separate window time. Multi-monitor flex incoming.",
                "Undock this bad boy. Spread your workspace across every screen you own.",
                "Pop it out. Because cramming everything in one window is for savages.",
            ],
            'minigames_tab': [
                "Mini-games! Because sorting textures is boring as HELL sometimes.",
                "Game time, you procrastinating bastard. Earn bucks while slacking off.",
                "Play games! Win prizes! Pretend you're being productive!",
                "Mini-games tab. The 'I'm definitely still working' section.",
                "Games! Because you'd rather play Snake than organize textures, admit it.",
            ],
            'closet_appearance': [
                "Your panda's current look. Fashion disaster or style icon? You decide.",
                "Outfit summary. See what crimes against fashion your panda is committing.",
                "Current drip check. Is your panda stylish or looking like a damn fool?",
                "What your bear's wearing right now. Probably something ridiculous.",
                "Panda outfit overview. Rate it 1-10. Spoiler: it's always a 10 to me.",
            ],
            'closet_header': [
                "The closet! Where your panda becomes a fashion ICON. Or a fashion DISASTER.",
                "Wardrobe central. Your panda has more outfits than you do, probably.",
                "Dress-up headquarters. Project Runway: Panda Edition starts NOW.",
                "Closet time! Make your bear look absolutely fabulous or utterly ridiculous.",
                "Fashion central for your fluffy friend. No judgment. Okay, SOME judgment.",
            ],
            'achievement_progress': [
                "Progress bar. Watch it slowly fill up while you question your hobbies.",
                "How close you are to that achievement. Spoiler: not close enough, probably.",
                "Achievement progress. The world's slowest loading bar, basically.",
                "Progress tracker. For obsessive completionists who need to see the NUMBERS.",
                "How far along you are. Keep going, you beautiful overachiever. Or don't.",
            ],
            'inventory_accessory': [
                "Your accessory hoard. Because your panda needs bling more than you need therapy.",
                "Accessories for your panda. Yes, a virtual bear needs jewelry. We don't judge.",
                "The accessory pile. Equip these or let them gather digital dust. Your call.",
            ],
            'inventory_food': [
                "Food stash. Feed your panda or watch it give you the saddest damn eyes ever.",
                "Your panda's snack drawer. Feed the beast or suffer the guilt trip.",
                "Food items. Because apparently your virtual panda can't find its own damn food.",
            ],
            'inventory_toy': [
                "Toys! Give one to your panda and watch it lose its tiny mind with joy.",
                "Your toy collection. Making a virtual bear happy is peak adult behavior.",
                "Toys for your panda. More entertaining than most Netflix shows, honestly.",
            ],
            'inventory_unlocked': [
                "Everything you've unlocked. Look at all this shit you earned by clicking buttons. Proud of you.",
                "Your unlocked rewards summary. Proof that your obsessive playing paid off.",
                "Achievement loot. All the stuff you earned by being a completionist psycho.",
            ],
            'shop_item_name': [
                "Click for details. Read the damn description before buying like an informed consumer for once.",
                "Item details. Read before purchasing, you impulsive little shopper.",
                "Tap this to see what the hell you're about to waste your Bamboo Bucks on.",
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
A: Go to Settings -> UI & Appearance and change the tooltip mode. Changes take effect immediately - no restart needed. Choose Normal, Beginner, or Unhinged.

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