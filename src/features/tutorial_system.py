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

# Try to import panda mode tooltips
try:
    from src.features.panda_mode import PandaMode
    PANDA_MODE_AVAILABLE = True
except ImportError:
    PANDA_MODE_AVAILABLE = False
    logger.warning("PandaMode not available - vulgar tooltips will be limited")


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
        return self.is_first_run() and GUI_AVAILABLE
    
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
                except:
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
                    "Want some fun while you work?\n\n"
                    "Enable Panda Mode for:\n"
                    "• Animated panda companion\n"
                    "• Fun (and sometimes vulgar) tooltips\n"
                    "• Easter eggs and achievements\n"
                    "• Mood-based reactions\n\n"
                    "You can enable it in Settings → Customization\n"
                    "(Don't worry, it's optional and off by default!)"
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
        """Standard helpful tooltips from PandaMode"""
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
            'tooltip_mode': "Choose how tooltips are displayed: normal, beginner, or panda mode",
            'theme_selector': "Choose a visual theme for the application",
        }
        
        # Pull from PandaMode TOOLTIPS if available
        if PANDA_MODE_AVAILABLE:
            try:
                for widget_id, tooltip_dict in PandaMode.TOOLTIPS.items():
                    if 'normal' in tooltip_dict:
                        base_tooltips[widget_id] = tooltip_dict['normal']
            except Exception as e:
                logger.warning(f"Error loading normal tooltips from PandaMode: {e}")
        
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
            ],
            'panda_stats_tab': [
                "See how your panda is doing! Check its mood, how many times "
                "you've petted or fed it, and other fun stats.",
            ],
            'keyboard_controls': [
                "View all keyboard shortcuts and change them to whatever keys "
                "you prefer. Click Edit next to any shortcut to change it.",
            ],
            'tooltip_mode': [
                "Choose how tooltips are shown: Normal gives standard info, "
                "Dumbed Down gives extra detail, Vulgar Panda adds humor.",
                "Control tooltip style: Normal, Beginner-friendly, or Panda mode "
                "with sarcastic commentary!",
            ],
            'theme_selector': [
                "Pick a color theme for the application. Try dark mode for "
                "late-night sessions or light mode for daytime use.",
            ],
        }
    
    def _get_vulgar_panda_tooltips(self) -> Dict[str, Any]:
        """Fun/sarcastic tooltips from PandaMode (vulgar mode)"""
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
            ],
            'panda_stats_tab': [
                "Stalk your panda's mood and life choices.",
                "Check on your panda. Is it happy? Who cares. Check anyway.",
            ],
            'keyboard_controls': [
                "Keyboard shortcuts. Customize 'em if you dare.",
                "Hotkeys. For when clicking is too much effort.",
            ],
            'tooltip_mode': [
                "Control the sass level. You've been warned.",
                "Switch tooltip modes. You're in vulgar mode. Obviously.",
            ],
            'theme_selector': [
                "Pick a vibe. Dark mode or boomer mode.",
                "Choose your aesthetic. Make it pretty. Or ugly. Your call.",
            ],
        }
        
        # Pull from PandaMode TOOLTIPS if available
        if PANDA_MODE_AVAILABLE:
            try:
                for widget_id, tooltip_dict in PandaMode.TOOLTIPS.items():
                    if 'vulgar' in tooltip_dict:
                        base_tooltips[widget_id] = tooltip_dict['vulgar']
            except Exception as e:
                logger.warning(f"Error loading vulgar tooltips from PandaMode: {e}")
        
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
        except:
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
A: Go to Settings -> UI & Appearance and change the tooltip mode. Changes take effect immediately - no restart needed. Choose Normal, Beginner, or Vulgar Panda mode.

Q: How do keyboard shortcuts work?
A: Press F1 for help, Ctrl+P to start processing, Ctrl+S to save, and more. Check the About tab for a complete list of shortcuts.

Q: How do I customize the UI theme?
A: Click Settings button -> UI & Appearance to change colors, cursors (default/skull/panda/sword), themes, and tooltip verbosity. The Vulgar Panda theme uses a red color scheme.

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

Still need help? Check the documentation files in the repository!
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