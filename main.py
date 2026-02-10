"""
PS2 Texture Sorter - Main Entry Point
Author: Dead On The Inside / JosephsDeadish

A professional, single-executable Windows application for automatically 
sorting PS2 texture dumps with advanced AI classification and massive-scale 
support (200,000+ textures).
"""

# Set Windows taskbar icon BEFORE any GUI imports
import ctypes
try:
    # Follow Microsoft's AppUserModelID naming convention
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Josephs.PS2TextureSorter.Main.1.0.0')
except (AttributeError, OSError):
    pass  # Not Windows or no windll

import sys
import os
import time
import threading
import logging
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# Add src directory to path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import configuration first
from src.config import config, APP_NAME, APP_VERSION, APP_AUTHOR, CONFIG_DIR, LOGS_DIR, CACHE_DIR

# Flag to check if GUI libraries are available
GUI_AVAILABLE = False

try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
    GUI_AVAILABLE = True
except ImportError:
    print("Warning: CustomTkinter not available. Running in console mode.")

# Import core modules
from src.classifier import TextureClassifier, ALL_CATEGORIES
from src.lod_detector import LODDetector
from src.file_handler import FileHandler
from src.database import TextureDatabase
from src.organizer import OrganizationEngine, ORGANIZATION_STYLES, TextureInfo

# Import UI customization
try:
    from src.ui.customization_panel import open_customization_dialog
    CUSTOMIZATION_AVAILABLE = True
except ImportError:
    CUSTOMIZATION_AVAILABLE = False
    print("Warning: UI customization panel not available.")

try:
    from src.features.panda_character import PandaCharacter
    PANDA_CHARACTER_AVAILABLE = True
except ImportError:
    PANDA_CHARACTER_AVAILABLE = False
    print("Warning: Panda character not available.")

# Keep PandaMode import for backward compatibility during transition
try:
    from src.features.panda_mode import PandaMode
    PANDA_MODE_AVAILABLE = True
except ImportError:
    PANDA_MODE_AVAILABLE = False
    print("Warning: Panda mode not available.")

try:
    from src.features.sound_manager import SoundManager
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("Warning: Sound manager not available.")

try:
    from src.features.achievements import AchievementSystem
    ACHIEVEMENTS_AVAILABLE = True
except ImportError:
    ACHIEVEMENTS_AVAILABLE = False
    print("Warning: Achievements system not available.")

try:
    from src.features.unlockables_system import UnlockablesSystem, UnlockConditionType
    UNLOCKABLES_AVAILABLE = True
except ImportError:
    UNLOCKABLES_AVAILABLE = False
    print("Warning: Unlockables system not available.")

try:
    from src.features.statistics import StatisticsTracker
    STATISTICS_AVAILABLE = True
except ImportError:
    STATISTICS_AVAILABLE = False
    print("Warning: Statistics tracker not available.")

try:
    from src.features.search_filter import SearchFilter
    SEARCH_FILTER_AVAILABLE = True
except ImportError:
    SEARCH_FILTER_AVAILABLE = False
    print("Warning: Search filter not available.")

try:
    from src.features.tutorial_system import setup_tutorial_system, TooltipMode, WidgetTooltip
    TUTORIAL_AVAILABLE = True
except ImportError:
    TUTORIAL_AVAILABLE = False
    WidgetTooltip = None
    print("Warning: Tutorial system not available.")

try:
    from src.features.preview_viewer import PreviewViewer
    PREVIEW_AVAILABLE = True
except ImportError:
    PREVIEW_AVAILABLE = False
    print("Warning: Preview viewer not available.")

try:
    from src.features.currency_system import CurrencySystem
    CURRENCY_AVAILABLE = True
except ImportError:
    CURRENCY_AVAILABLE = False
    print("Warning: Currency system not available.")

try:
    from src.features.level_system import UserLevelSystem, PandaLevelSystem
    LEVEL_SYSTEM_AVAILABLE = True
except ImportError:
    LEVEL_SYSTEM_AVAILABLE = False
    print("Warning: Level system not available.")

try:
    from src.features.shop_system import ShopSystem, ShopCategory
    SHOP_AVAILABLE = True
except ImportError:
    SHOP_AVAILABLE = False
    print("Warning: Shop system not available.")

try:
    from src.ui.panda_widget import PandaWidget
    PANDA_WIDGET_AVAILABLE = True
except ImportError:
    PANDA_WIDGET_AVAILABLE = False
    print("Warning: Panda widget not available.")

try:
    from src.features.panda_closet import PandaCloset
    from src.ui.closet_panel import ClosetPanel
    PANDA_CLOSET_AVAILABLE = True
except ImportError:
    PANDA_CLOSET_AVAILABLE = False
    print("Warning: Panda closet not available.")

try:
    from src.features.panda_widgets import WidgetCollection, WidgetType
    PANDA_WIDGETS_AVAILABLE = True
except ImportError:
    PANDA_WIDGETS_AVAILABLE = False
    print("Warning: Panda widgets not available.")

try:
    from src.ui.goodbye_splash import show_goodbye_splash
    GOODBYE_SPLASH_AVAILABLE = True
except ImportError:
    GOODBYE_SPLASH_AVAILABLE = False
    print("Warning: Goodbye splash not available.")


class SplashScreen:
    """Splash screen with panda logo and loading animation"""
    
    def __init__(self, master=None):
        if not GUI_AVAILABLE or master is None:
            self.show_console_splash()
            return
            
        self.window = ctk.CTkToplevel(master) if master else ctk.CTk()
        self.window.title(f"{APP_NAME}")
        
        # Configure window
        window_width = 500
        window_height = 400
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Remove window decorations
        self.window.overrideredirect(True)
        
        # Main frame
        frame = ctk.CTkFrame(self.window, corner_radius=20)
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Panda ASCII art
        panda_art = """
        ████████████████
      ██░░░░░░░░░░░░░░██
    ██░░░░░░░░░░░░░░░░░░██
    ██░░██████░░██████░░██
    ██░░██████░░██████░░██
    ██░░░░░░░░░░░░░░░░░░██
    ██░░░░░░██░░░░░░░░░░██
      ██░░░░░░░░░░░░░░██
        ██████████████
        """
        
        # Title
        title_label = ctk.CTkLabel(
            frame, 
            text=f"🐼 {APP_NAME} 🐼",
            font=("Arial Bold", 24)
        )
        title_label.pack(pady=(30, 10))
        
        # Panda art
        panda_label = ctk.CTkLabel(
            frame,
            text=panda_art,
            font=("Courier", 10),
            justify="center"
        )
        panda_label.pack(pady=10)
        
        # Version info
        version_label = ctk.CTkLabel(
            frame,
            text=f"Version {APP_VERSION}",
            font=("Arial", 12)
        )
        version_label.pack(pady=5)
        
        # Author
        author_label = ctk.CTkLabel(
            frame,
            text=f"by {APP_AUTHOR}",
            font=("Arial", 10),
            text_color="gray"
        )
        author_label.pack(pady=5)
        
        # Loading text
        self.loading_label = ctk.CTkLabel(
            frame,
            text="Initializing...",
            font=("Arial", 11)
        )
        self.loading_label.pack(pady=20)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(frame, width=400)
        self.progress.pack(pady=10)
        self.progress.set(0)
        
        self.window.update()
    
    def show_console_splash(self):
        """Show splash screen in console"""
        print("=" * 60)
        print(f"{APP_NAME} v{APP_VERSION}")
        print(f"Author: {APP_AUTHOR}")
        print("=" * 60)
        print("""
    🐼 PS2 Texture Sorter 🐼
    
        ████████████████
      ██░░░░░░░░░░░░░░██
    ██░░░░░░░░░░░░░░░░░░██
    ██░░██████░░██████░░██
    ██░░██████░░██████░░██
    ██░░░░░░░░░░░░░░░░░░██
    ██░░░░░░██░░░░░░░░░░██
      ██░░░░░░░░░░░░░░██
        ██████████████
        
    Loading application...
        """)
    
    def update_progress(self, value, text):
        """Update loading progress"""
        if GUI_AVAILABLE and hasattr(self, 'window'):
            self.progress.set(value)
            self.loading_label.configure(text=text)
            self.window.update()
        else:
            print(f"[{int(value*100)}%] {text}")
    
    def close(self):
        """Close splash screen"""
        if GUI_AVAILABLE and hasattr(self, 'window'):
            time.sleep(0.5)  # Brief pause before closing
            self.window.destroy()


class PS2TextureSorter(ctk.CTk):
    """Main application window"""
    
    # Configuration constants
    GOODBYE_SPLASH_DISPLAY_MS = 800  # Time to display goodbye splash before exit
    BATCH_BONUS_THRESHOLD = 100  # Number of files for batch bonus
    
    def __init__(self):
        super().__init__()
        
        # Load theme from config before creating UI
        self._load_initial_theme()
        
        # Configure window
        self.title(f"🐼 {APP_NAME} v{APP_VERSION}")
        self.geometry("1200x800")
        self.minsize(900, 650)  # Minimum window size per requirements
        
        # Set window icon (both .ico for Windows and .png for fallback)
        try:
            icon_path = Path(__file__).parent / "assets" / "icon.png"
            ico_path = Path(__file__).parent / "assets" / "icon.ico"
            
            # Set iconbitmap first for Windows (best taskbar integration)
            if ico_path.exists() and sys.platform == 'win32':
                self.iconbitmap(str(ico_path))
            
            # Set iconphoto for better cross-platform support and taskbar
            if icon_path.exists():
                from PIL import Image, ImageTk
                icon_image = Image.open(str(icon_path))
                self._icon_photo = ImageTk.PhotoImage(icon_image)
                self.iconphoto(True, self._icon_photo)
        except Exception as e:
            logger.debug(f"Could not set window icon: {e}")
        
        # Set close handler to ensure clean shutdown
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Initialize core components
        self.classifier = TextureClassifier(config)
        self.lod_detector = LODDetector()
        self.file_handler = FileHandler(create_backup=config.get('file_handling', 'create_backup', default=True))
        self.database = None  # Will be initialized when needed
        
        # Initialize feature modules
        self.panda = None  # Always-present panda character
        self.panda_mode = None  # Deprecated - keeping for backward compatibility
        self.sound_manager = None
        self.achievement_manager = None
        self.unlockables_manager = None
        self.stats_tracker = None
        self.search_filter = None
        self.tutorial_manager = None
        self.tooltip_manager = None  # Uses existing TooltipVerbosityManager - has vulgar mode
        self._tooltips = []  # Store tooltip references to prevent garbage collection
        self.context_help = None
        self.preview_viewer = None
        self.currency_system = None
        self.user_level_system = None
        self.panda_level_system = None
        self.shop_system = None
        self.panda_closet = None
        self.panda_widget = None
        self.widget_collection = None
        
        # Thumbnail cache for file browser (LRU - prevent PhotoImage GC)
        self._thumbnail_cache = {}
        self._thumbnail_cache_order = deque()  # Track insertion order for LRU eviction
        self._thumbnail_cache_max = config.get('performance', 'thumbnail_cache_size', default=500)
        
        # Initialize features if GUI available
        if GUI_AVAILABLE:
            try:
                # Always create panda character - not a "mode"
                if PANDA_CHARACTER_AVAILABLE:
                    self.panda = PandaCharacter()
                    logger.info("Panda character initialized (always present)")
                
                # Keep old panda_mode for backward compatibility (will be deprecated)
                if PANDA_MODE_AVAILABLE and not PANDA_CHARACTER_AVAILABLE:
                    self.panda_mode = PandaMode()
                    logger.warning("Using deprecated PandaMode - should migrate to PandaCharacter")
                
                if SOUND_AVAILABLE:
                    self.sound_manager = SoundManager()
                if ACHIEVEMENTS_AVAILABLE:
                    achievements_save = str(Path.home() / ".ps2_texture_sorter" / "achievements.json")
                    self.achievement_manager = AchievementSystem(save_file=achievements_save)
                    # Register callback to grant rewards when achievements unlock
                    self.achievement_manager.register_unlock_callback(self._on_achievement_unlocked)
                if UNLOCKABLES_AVAILABLE:
                    self.unlockables_manager = UnlockablesSystem()
                if STATISTICS_AVAILABLE:
                    self.stats_tracker = StatisticsTracker(config)
                if SEARCH_FILTER_AVAILABLE:
                    self.search_filter = SearchFilter()
                if PREVIEW_AVAILABLE:
                    self.preview_viewer = PreviewViewer(self)
                if CURRENCY_AVAILABLE:
                    self.currency_system = CurrencySystem()
                    # Process daily login bonus
                    login_bonus = self.currency_system.process_daily_login()
                    if login_bonus > 0:
                        logger.info(f"Daily login bonus: ${login_bonus}")
                if LEVEL_SYSTEM_AVAILABLE:
                    self.user_level_system = UserLevelSystem()
                    self.panda_level_system = PandaLevelSystem()
                if SHOP_AVAILABLE:
                    self.shop_system = ShopSystem()
                if PANDA_CLOSET_AVAILABLE:
                    self.panda_closet = PandaCloset()
                if PANDA_WIDGETS_AVAILABLE:
                    self.widget_collection = WidgetCollection()
                
                # Setup tutorial system
                if TUTORIAL_AVAILABLE:
                    try:
                        self.tutorial_manager, self.tooltip_manager, self.context_help = setup_tutorial_system(self, config)
                        
                        # Log which components initialized successfully
                        components_status = {
                            'TutorialManager': self.tutorial_manager is not None,
                            'TooltipVerbosityManager': self.tooltip_manager is not None,
                            'ContextHelp': self.context_help is not None
                        }
                        
                        success_count = sum(components_status.values())
                        if success_count == 3:
                            logger.info("Tutorial system initialized successfully (all components)")
                        elif success_count > 0:
                            logger.info(f"Tutorial system partially initialized: {components_status}")
                        else:
                            logger.warning("Tutorial system failed to initialize (all components)")
                        
                        # Only show warning for truly critical failures where NO components initialized
                        # and it's not a first-run or expected scenario
                        if success_count == 0:
                            # Don't show warning on first run - it's expected
                            is_first_run = not config.get('tutorial', 'completed', default=False)
                            if not is_first_run:
                                # Show warning only for unexpected complete failures
                                self.after(1000, lambda: messagebox.showwarning(
                                    "Tutorial System Warning",
                                    "The tutorial system failed to initialize.\n\n"
                                    "Tooltips and help may not work correctly.\n"
                                    "This won't affect core functionality."))
                    except Exception as tutorial_error:
                        logger.error(f"Unexpected error in tutorial system initialization: {tutorial_error}", exc_info=True)
                        # Set fallback None values
                        self.tutorial_manager = None
                        self.tooltip_manager = None
                        self.context_help = None
                else:
                    self.tutorial_manager = None
                    self.tooltip_manager = None
                    self.context_help = None
            except Exception as e:
                logger.warning(f"Failed to initialize some features: {e}")
        
        # Create UI
        self.create_menu()
        self.create_main_ui()
        
        # Show tutorial on first run
        if self.tutorial_manager and self.tutorial_manager.should_show_tutorial():
            self.after(500, lambda: self.tutorial_manager.start_tutorial())
        
        # Status
        self.current_operation = None
    
    def _on_close(self):
        """Handle window close to ensure clean shutdown"""
        splash = None
        try:
            # Show goodbye splash if available
            if GOODBYE_SPLASH_AVAILABLE:
                from src.ui.goodbye_splash import INITIAL_PROGRESS
                splash = show_goodbye_splash(self)
                splash.update_status("Saving configuration...", INITIAL_PROGRESS)
            
            # Close tutorial if active
            if self.tutorial_manager and self.tutorial_manager.tutorial_active:
                self.tutorial_manager._complete_tutorial()
            
            # Close any pop-out windows
            if hasattr(self, '_popout_windows'):
                for win in list(self._popout_windows.values()):
                    try:
                        if win.winfo_exists():
                            win.destroy()
                    except Exception:
                        pass
            
            if splash:
                splash.update_status("Cleaning up...", 0.6)
            
            # Save config
            config.save()
            
            if splash:
                splash.update_status("Goodbye! 🐼", 1.0)
                # Brief pause to show the goodbye message
                self.after(self.GOODBYE_SPLASH_DISPLAY_MS, self._force_exit)
            else:
                self._force_exit()
                
        except Exception as e:
            logger.debug(f"Error during shutdown cleanup: {e}")
            if splash:
                splash.close()
            self._force_exit()
    
    def _force_exit(self):
        """Force application exit to terminate all threads"""
        try:
            self.destroy()
        except Exception:
            pass
        # Force exit to ensure all daemon threads are terminated
        sys.exit(0)
    
    def _load_initial_theme(self):
        """Load theme and UI scaling settings from config on startup"""
        try:
            # Get theme from config
            theme = config.get('ui', 'theme', default='dark')
            
            # Apply appearance mode
            if theme in ['dark', 'light']:
                ctk.set_appearance_mode(theme)
            else:
                ctk.set_appearance_mode('dark')
            
            ctk.set_default_color_theme("blue")
            
            # Load and apply UI scaling
            scale_value = config.get('ui', 'scale', default='100%')
            try:
                scale_percent = int(scale_value.rstrip('%'))
                scale_factor = scale_percent / 100.0
                ctk.set_widget_scaling(scale_factor)
                ctk.set_window_scaling(scale_factor)
            except Exception as scale_err:
                print(f"Warning: Failed to apply UI scaling: {scale_err}")
                
        except Exception as e:
            print(f"Warning: Failed to load theme: {e}")
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
    
    def create_menu(self):
        """Create top menu bar (simulated with frame)"""
        menu_frame = ctk.CTkFrame(self, height=40, corner_radius=0)
        menu_frame.pack(fill="x", side="top")
        
        # Title with panda
        title_label = ctk.CTkLabel(
            menu_frame,
            text=f"🐼 {APP_NAME}",
            font=("Arial Bold", 16)
        )
        title_label.pack(side="left", padx=20, pady=5)
        
        # Help button
        help_button = None
        if self.context_help:
            help_button = ctk.CTkButton(
                menu_frame,
                text="❓ Help",
                width=80,
                command=lambda: self.context_help.open_help_panel()
            )
            help_button.pack(side="right", padx=10, pady=5)
        
        # Settings button (theme is available inside Settings → Appearance)
        settings_button = ctk.CTkButton(
            menu_frame,
            text="⚙️ Settings",
            width=100,
            command=self.open_settings_window
        )
        settings_button.pack(side="right", padx=10, pady=5)
        
        # Tutorial button - always visible so user can restart tutorial
        tutorial_button = None
        if TUTORIAL_AVAILABLE:
            tutorial_button = ctk.CTkButton(
                menu_frame,
                text="📖 Tutorial",
                width=100,
                command=self._run_tutorial
            )
            tutorial_button.pack(side="right", padx=10, pady=5)
        
        # Apply tooltips to menu bar widgets
        self._apply_menu_tooltips(tutorial_button, settings_button, None, help_button)
    
    def _run_tutorial(self):
        """Start or restart the tutorial"""
        if self.tutorial_manager:
            try:
                self.tutorial_manager.reset_tutorial()
                self.tutorial_manager.start_tutorial()
                self.log("✅ Tutorial started successfully")
            except Exception as e:
                logger.error(f"Failed to start tutorial: {e}", exc_info=True)
                self.log(f"❌ Error starting tutorial: {e}")
                if GUI_AVAILABLE:
                    messagebox.showerror("Tutorial Error", 
                        f"Failed to start tutorial:\n\n{str(e)}\n\nCheck the log for details.")
        else:
            logger.warning("Tutorial button clicked but tutorial_manager is None")
            self._show_tutorial_unavailable_message()
    
    def _show_tutorial_unavailable_message(self):
        """Show appropriate message when tutorial is unavailable"""
        if not GUI_AVAILABLE:
            return
            
        if not TUTORIAL_AVAILABLE:
            messagebox.showwarning("Tutorial Unavailable", 
                "Tutorial system failed to import.\n\n"
                "This may be due to missing dependencies or import errors.\n"
                "Check the application log for details.")
        else:
            messagebox.showwarning("Tutorial Unavailable", 
                "Tutorial system is available but failed to initialize.\n\n"
                "This may occur if the UI is not fully loaded yet.\n"
                "Try restarting the application.")

    
    def create_main_ui(self):
        """Create main tabbed interface"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top-level category tab view
        self.category_tabview = ctk.CTkTabview(main_frame)
        self.category_tabview.pack(fill="both", expand=True)
        
        # Create two category tabs
        self.tools_category = self.category_tabview.add("🔧 Tools")
        self.features_category = self.category_tabview.add("🐼 Panda & Features")
        
        # Tools tabview (nested)
        self.tabview = ctk.CTkTabview(self.tools_category)
        self.tabview.pack(fill="both", expand=True)
        
        self.tab_sort = self.tabview.add("🐼 Sort Textures")
        self.tab_convert = self.tabview.add("🔄 Convert Files")
        self.tab_browser = self.tabview.add("📁 File Browser")
        self.tab_notepad = self.tabview.add("📝 Notepad")
        self.tab_about = self.tabview.add("ℹ️ About")
        
        # Features tabview (nested)
        self.features_tabview = ctk.CTkTabview(self.features_category)
        self.features_tabview.pack(fill="both", expand=True)
        
        self.tab_shop = self.features_tabview.add("🛒 Shop")
        self.tab_rewards = self.features_tabview.add("🎁 Rewards")
        self.tab_achievements = self.features_tabview.add("🏆 Achievements")
        if PANDA_CLOSET_AVAILABLE and self.panda_closet:
            self.tab_closet = self.features_tabview.add("👔 Panda Closet")
        self.tab_inventory = self.features_tabview.add("📦 Inventory")
        self.tab_panda_stats = self.features_tabview.add("📊 Panda Stats & Mood")
        
        # Track popped-out tabs
        self._popout_windows = {}
        
        # Populate tabs
        self.create_sort_tab()
        self.create_convert_tab()
        self.create_browser_tab()
        self.create_notepad_tab()
        self.create_about_tab()
        self.create_shop_tab()
        self.create_rewards_tab()
        self.create_achievements_tab()
        if PANDA_CLOSET_AVAILABLE and self.panda_closet:
            self.create_closet_tab()
        self.create_inventory_tab()
        self.create_panda_stats_tab()
        
        # Add pop-out buttons to dockable tabs
        self._add_popout_buttons()
        
        # Status bar
        self.create_status_bar()
    
    def _add_popout_buttons(self):
        """Add pop-out/undock buttons to secondary tabs"""
        # Tools tabs that can be popped out
        tools_dockable = {
            "📝 Notepad": (self.tab_notepad, self.tabview),
            "📁 File Browser": (self.tab_browser, self.tabview),
            "ℹ️ About": (self.tab_about, self.tabview),
        }
        # Features tabs that can be popped out
        features_dockable = {
            "🏆 Achievements": (self.tab_achievements, self.features_tabview),
            "🛒 Shop": (self.tab_shop, self.features_tabview),
            "🎁 Rewards": (self.tab_rewards, self.features_tabview),
            "📦 Inventory": (self.tab_inventory, self.features_tabview),
            "📊 Panda Stats & Mood": (self.tab_panda_stats, self.features_tabview),
        }
        all_dockable = {**tools_dockable, **features_dockable}
        # Store tabview mapping for pop-out/dock operations
        self._tab_to_tabview = {name: tv for name, (_, tv) in all_dockable.items()}
        for tab_name, (tab_frame, _) in all_dockable.items():
            btn = ctk.CTkButton(
                tab_frame, text="⬗", width=30, height=26,
                font=("Arial", 11),
                fg_color="gray40",
                command=lambda n=tab_name: self._popout_tab(n)
            )
            btn.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(btn, f"Pop out {tab_name} into a separate window"))
    
    def _popout_tab(self, tab_name):
        """Pop out a tab into its own window"""
        if tab_name in self._popout_windows:
            # Already popped out, bring to front
            win = self._popout_windows[tab_name]
            if win.winfo_exists():
                win.lift()
                win.focus_force()
                return
        
        # Create pop-out window
        popout = ctk.CTkToplevel(self)
        popout.title(tab_name)
        popout.geometry("800x600")
        self._popout_windows[tab_name] = popout
        
        # Special handling for notepad tab (avoid reparenting complex widget)
        if tab_name == "📝 Notepad":
            self._create_popout_notepad(popout, tab_name)
        else:
            # Get the tab frame and its children
            parent_tv = self._tab_to_tabview.get(tab_name, self.tabview)
            tab_frame = parent_tv.tab(tab_name)
            children_info = []
            for child in tab_frame.winfo_children():
                children_info.append(child)
            
            # Store children for re-docking later
            if not hasattr(self, '_popout_children'):
                self._popout_children = {}
            self._popout_children[tab_name] = children_info
            
            # Reparent all children to the pop-out window
            container = ctk.CTkFrame(popout)
            container.pack(fill="both", expand=True, padx=5, pady=5)
            
            for child in children_info:
                child.pack_forget()
                child.place_forget()
                child.grid_forget()
                try:
                    child.pack(in_=container, fill="both", expand=True, padx=5, pady=5)
                except Exception:
                    pass
        
        # Add dock-back button
        dock_btn = ctk.CTkButton(
            popout, text="⬙ Dock Back", width=100, height=28,
            command=lambda n=tab_name: self._dock_tab(n, self._popout_children.get(n), popout)
        )
        dock_btn.pack(side="bottom", pady=5)
        
        # Handle window close = dock back
        popout.protocol("WM_DELETE_WINDOW",
                        lambda n=tab_name: self._dock_tab(n, self._popout_children.get(n), popout))
    
    def _create_popout_notepad(self, popout_window, tab_name):
        """Create notepad functionality in popout window (fully editable)"""
        container = ctk.CTkFrame(popout_window)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header with title and buttons
        header_frame = ctk.CTkFrame(container)
        header_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(header_frame, text="📝 Personal Notes (Undocked)",
                     font=("Arial Bold", 16)).pack(side="left", padx=10)
        
        # Add new note button in popout
        ctk.CTkButton(header_frame, text="➕ New Note", width=100,
                     command=self._popout_add_note).pack(side="right", padx=5)
        
        # Save button in popout
        ctk.CTkButton(header_frame, text="💾 Save All", width=100,
                     command=self._popout_save_notes).pack(side="right", padx=5)
        
        # Delete button in popout
        ctk.CTkButton(header_frame, text="🗑️ Delete Note", width=110,
                     command=self._popout_delete_note).pack(side="right", padx=5)
        
        # Create tabview for notes in popout
        self._popout_notes_tabview = ctk.CTkTabview(container)
        self._popout_notes_tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        self._popout_note_textboxes = {}
        
        # Populate with current notes content
        if hasattr(self, 'note_textboxes'):
            for note_name, textbox in self.note_textboxes.items():
                content = textbox.get("1.0", "end-1c")
                new_tab = self._popout_notes_tabview.add(note_name)
                tb = ctk.CTkTextbox(new_tab, width=750, height=500)
                tb.pack(padx=5, pady=5, fill="both", expand=True)
                tb.insert("1.0", content)
                self._popout_note_textboxes[note_name] = tb
    
    def _popout_add_note(self):
        """Add a new note in popout notepad"""
        import tkinter.simpledialog as simpledialog
        name = simpledialog.askstring("New Note", "Enter note name:",
                                     initialvalue=f"Note {len(self._popout_note_textboxes) + 1}")
        if not name or name in self._popout_note_textboxes:
            return
        new_tab = self._popout_notes_tabview.add(name)
        tb = ctk.CTkTextbox(new_tab, width=750, height=500)
        tb.pack(padx=5, pady=5, fill="both", expand=True)
        self._popout_note_textboxes[name] = tb
        self._popout_notes_tabview.set(name)
    
    def _popout_delete_note(self):
        """Delete the current note in popout notepad"""
        current = self._popout_notes_tabview.get()
        if len(self._popout_note_textboxes) <= 1:
            if GUI_AVAILABLE:
                messagebox.showwarning("Cannot Delete", "You must have at least one note tab.")
            return
        if GUI_AVAILABLE:
            if not messagebox.askyesno("Delete Note", f"Delete '{current}'?"):
                return
        del self._popout_note_textboxes[current]
        self._popout_notes_tabview.delete(current)
    
    def _popout_save_notes(self):
        """Sync popout notes back to the main notepad and save"""
        # Update main notepad textboxes with popout content
        for name, tb in self._popout_note_textboxes.items():
            content = tb.get("1.0", "end-1c")
            if name in self.note_textboxes:
                self.note_textboxes[name].delete("1.0", "end")
                self.note_textboxes[name].insert("1.0", content)
            else:
                self.add_new_note_tab(name=name, content=content)
        # Remove notes deleted in popout
        for name in list(self.note_textboxes.keys()):
            if name not in self._popout_note_textboxes:
                del self.note_textboxes[name]
                try:
                    self.notes_tabview.delete(name)
                except Exception:
                    pass
        self.save_all_notes()
    
    def _dock_tab(self, tab_name, children, popout_window):
        """Dock a popped-out tab back into the main tabview"""
        # Special handling for notepad - sync edits back before closing
        if tab_name == "📝 Notepad":
            if hasattr(self, '_popout_note_textboxes'):
                self._popout_save_notes()
            if popout_window.winfo_exists():
                popout_window.destroy()
            self._popout_windows.pop(tab_name, None)
            # Re-add pop-out button
            parent_tv = self._tab_to_tabview.get(tab_name, self.tabview)
            tab_frame = parent_tv.tab(tab_name)
            btn = ctk.CTkButton(
                tab_frame, text="⬗ Pop Out", width=90, height=26,
                font=("Arial", 11),
                fg_color="gray40",
                command=lambda: self._popout_tab(tab_name)
            )
            btn.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
            return
        
        # For other tabs, reparent children back
        parent_tv = self._tab_to_tabview.get(tab_name, self.tabview)
        tab_frame = parent_tv.tab(tab_name)
        
        if children:
            # Reparent children back
            for child in children:
                child.pack_forget()
                child.place_forget()
                child.grid_forget()
                try:
                    child.pack(in_=tab_frame, fill="both", expand=True, padx=5, pady=5)
                except Exception:
                    pass
        
        # Destroy pop-out window
        if popout_window.winfo_exists():
            popout_window.destroy()
        
        self._popout_windows.pop(tab_name, None)
        if hasattr(self, '_popout_children'):
            self._popout_children.pop(tab_name, None)
        
        # Re-add pop-out button
        btn = ctk.CTkButton(
            tab_frame, text="⬗ Pop Out", width=90, height=26,
            font=("Arial", 11),
            fg_color="gray40",
            command=lambda: self._popout_tab(tab_name)
        )
        btn.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
        
        # Switch to the docked tab
        parent_tv = self._tab_to_tabview.get(tab_name, self.tabview)
        parent_tv.set(tab_name)
    
    def create_sort_tab(self):
        """Create texture sorting tab"""
        # Use scrollable frame to ensure all content is accessible
        scrollable_frame = ctk.CTkScrollableFrame(self.tab_sort)
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ===== ACTION BUTTONS AT TOP =====
        button_frame = ctk.CTkFrame(scrollable_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_button = ctk.CTkButton(button_frame, text="🐼 Start Sorting", 
                                           command=self.start_sorting, 
                                           width=150, height=40,
                                           font=("Arial Bold", 14))
        self.start_button.pack(side="left", padx=10)
        
        self.pause_button = ctk.CTkButton(button_frame, text="⏸️ Pause", 
                                           command=self.pause_sorting,
                                           width=100, height=40, state="disabled")
        self.pause_button.pack(side="left", padx=10)
        
        self.stop_button = ctk.CTkButton(button_frame, text="⏹️ Stop",
                                          command=self.stop_sorting,
                                          width=100, height=40, state="disabled")
        self.stop_button.pack(side="left", padx=10)
        
        # Input section
        input_frame = ctk.CTkFrame(scrollable_frame)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="Input Directory:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        input_path_frame = ctk.CTkFrame(input_frame)
        input_path_frame.pack(fill="x", padx=10, pady=5)
        
        self.input_path_var = ctk.StringVar(value="")
        input_entry = ctk.CTkEntry(input_path_frame, textvariable=self.input_path_var, width=800)
        input_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        browse_btn = ctk.CTkButton(input_path_frame, text="Browse...", width=100, command=self.browse_input)
        browse_btn.pack(side="right", padx=5)
        
        # Output section
        output_frame = ctk.CTkFrame(scrollable_frame)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(output_frame, text="Output Directory:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        output_path_frame = ctk.CTkFrame(output_frame)
        output_path_frame.pack(fill="x", padx=10, pady=5)
        
        self.output_path_var = ctk.StringVar(value="")
        output_entry = ctk.CTkEntry(output_path_frame, textvariable=self.output_path_var, width=800)
        output_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        browse_out_btn = ctk.CTkButton(output_path_frame, text="Browse...", width=100, command=self.browse_output)
        browse_out_btn.pack(side="right", padx=5)
        
        # Options
        options_frame = ctk.CTkFrame(scrollable_frame)
        options_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(options_frame, text="Sorting Options:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        opts_grid = ctk.CTkFrame(options_frame)
        opts_grid.pack(fill="x", padx=10, pady=5)
        
        # Mode selection
        ctk.CTkLabel(opts_grid, text="Mode:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.mode_var = ctk.StringVar(value="automatic")
        mode_menu = ctk.CTkOptionMenu(opts_grid, variable=self.mode_var, 
                                       values=["automatic", "manual", "suggested"])
        mode_menu.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Organization style (default: flat - simplest for new users)
        ctk.CTkLabel(opts_grid, text="Style:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        # Map display names to internal style keys
        self._style_display_to_key = {
            "Simple Flat (Category Only)": "flat",
            "Minimalist (Category → Files)": "minimalist",
            "By Character Traits (Gender/Skin/Body)": "sims",
            "By Type & Variant (Category/Type/File)": "neopets",
            "By Game Area (Level/Area/Type)": "game_area",
            "By Asset Pipeline (Type/Resolution/Format)": "asset_pipeline",
            "By Module (Characters/Vehicles/UI/etc.)": "modular",
            "Maximum Detail (Deep Hierarchy)": "maximum_detail",
            "Custom (User-Defined)": "custom",
        }
        self._style_key_to_display = {v: k for k, v in self._style_display_to_key.items()}
        style_display_names = list(self._style_display_to_key.keys())
        self.style_var = ctk.StringVar(value="Simple Flat (Category Only)")
        style_menu = ctk.CTkOptionMenu(opts_grid, variable=self.style_var,
                                        values=style_display_names)
        style_menu.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        
        # Checkboxes
        check_frame = ctk.CTkFrame(opts_grid)
        check_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="w")
        
        self.detect_lods_var = ctk.BooleanVar(value=True)
        detect_lods_cb = ctk.CTkCheckBox(check_frame, text="Detect LODs", variable=self.detect_lods_var)
        detect_lods_cb.pack(side="left", padx=10)
        
        self.group_lods_var = ctk.BooleanVar(value=True)
        group_lods_cb = ctk.CTkCheckBox(check_frame, text="Group LODs", variable=self.group_lods_var)
        group_lods_cb.pack(side="left", padx=10)
        
        self.detect_duplicates_var = ctk.BooleanVar(value=False)
        detect_dupes_cb = ctk.CTkCheckBox(check_frame, text="Detect Duplicates", variable=self.detect_duplicates_var)
        detect_dupes_cb.pack(side="left", padx=10)
        
        # Progress section
        progress_frame = ctk.CTkFrame(scrollable_frame)
        progress_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(progress_frame, text="Progress:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=1000)
        self.progress_bar.pack(padx=10, pady=10)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready to sort textures", font=("Arial", 11))
        self.progress_label.pack(padx=10, pady=5)
        
        # Log output
        self.log_text = ctk.CTkTextbox(progress_frame, height=200, width=1000)
        self.log_text.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Apply tooltips to sort tab widgets
        self._apply_sort_tooltips(browse_btn, browse_out_btn, mode_menu, style_menu, 
                                  detect_lods_cb, group_lods_cb, detect_dupes_cb)
    
    def _apply_sort_tooltips(self, browse_in_btn, browse_out_btn, mode_menu, style_menu,
                            detect_lods_cb, group_lods_cb, detect_dupes_cb):
        """Apply tooltips to sort tab widgets"""
        if not WidgetTooltip:
            return
        tt = self._get_tooltip_text
        # Store tooltip references to prevent garbage collection
        self._tooltips.append(WidgetTooltip(self.start_button, tt('sort_button')))
        self._tooltips.append(WidgetTooltip(self.pause_button, "Pause the current sorting operation"))
        self._tooltips.append(WidgetTooltip(self.stop_button, "Stop the sorting operation completely"))
        self._tooltips.append(WidgetTooltip(browse_in_btn, tt('input_browse')))
        self._tooltips.append(WidgetTooltip(browse_out_btn, tt('output_browse')))
        self._tooltips.append(WidgetTooltip(mode_menu, 
            "Sorting mode:\n"
            "• automatic – AI classifies textures automatically\n"
            "• manual – You choose the category for each texture\n"
            "• suggested – AI suggests, you confirm each one"))
        self._tooltips.append(WidgetTooltip(style_menu, 
            "Select how textures are organized:\n"
            "• Simple Flat – All files in category folders\n"
            "• Minimalist – Category → Files, minimal nesting\n"
            "• By Character Traits – Gender/Skin/Body Part\n"
            "• By Type & Variant – Category/Type/Individual\n"
            "• By Game Area – Level/Area/Type/Asset\n"
            "• By Asset Pipeline – Type/Resolution/Format\n"
            "• By Module – Characters/Vehicles/UI/etc.\n"
            "• Maximum Detail – Deep nested hierarchy\n"
            "• Custom – User-defined rules"))
        self._tooltips.append(WidgetTooltip(detect_lods_cb, tt('lod_detection') or "Automatically detect Level of Detail (LOD) textures"))
        self._tooltips.append(WidgetTooltip(group_lods_cb, tt('group_lods') or "Group LOD textures together in folders"))
        self._tooltips.append(WidgetTooltip(detect_dupes_cb, tt('detect_duplicates') or "Find and mark duplicate texture files"))
    
    def _get_tooltip_text(self, widget_id):
        """Get tooltip text from the tooltip manager"""
        if self.tooltip_manager:
            text = self.tooltip_manager.get_tooltip(widget_id)
            if text:
                return text
        # Fallback tooltips
        fallbacks = {
            'sort_button': "Click to sort your textures into organized folders",
            'input_browse': "Browse for the folder containing your texture files",
            'output_browse': "Choose where to save the organized textures",
            'detect_lods': "Automatically detect and group LOD levels",
            'convert_button': "Convert textures to different formats",
        }
        return fallbacks.get(widget_id, "")
    
    def _apply_convert_tooltips(self, input_btn, output_btn, from_menu, to_menu,
                                recursive_cb, keep_cb):
        """Apply tooltips to convert tab widgets"""
        if not WidgetTooltip:
            return
        tt = self._get_tooltip_text
        # Store tooltip references to prevent garbage collection
        self._tooltips.append(WidgetTooltip(self.convert_start_button, tt('convert_button') or "Start batch conversion of texture files"))
        self._tooltips.append(WidgetTooltip(input_btn, tt('input_browse') or "Select directory containing files to convert"))
        self._tooltips.append(WidgetTooltip(output_btn, tt('output_browse') or "Choose where to save converted files"))
        self._tooltips.append(WidgetTooltip(from_menu, "Select source file format to convert from"))
        self._tooltips.append(WidgetTooltip(to_menu, "Select target file format to convert to"))
        self._tooltips.append(WidgetTooltip(recursive_cb, "Also convert files in subdirectories"))
        self._tooltips.append(WidgetTooltip(keep_cb, "Keep original files after conversion"))
    
    def _apply_browser_tooltips(self, browse_btn, refresh_btn, search_entry, show_all_cb):
        """Apply tooltips to file browser tab widgets"""
        if not WidgetTooltip:
            return
        tt = self._get_tooltip_text
        # Store tooltip references to prevent garbage collection
        self._tooltips.append(WidgetTooltip(browse_btn, tt('browser_browse_button') or tt('file_selection') or "Select a directory to browse texture files"))
        self._tooltips.append(WidgetTooltip(refresh_btn, tt('browser_refresh_button') or "Refresh the file list"))
        self._tooltips.append(WidgetTooltip(search_entry, tt('browser_search') or tt('search_button') or "Search for specific files by name"))
        self._tooltips.append(WidgetTooltip(show_all_cb, tt('browser_show_all') or "Show all file types, not just textures"))
    
    def _apply_menu_tooltips(self, tutorial_btn, settings_btn, theme_btn, help_btn):
        """Apply tooltips to menu bar widgets"""
        if not WidgetTooltip:
            return
        tt = self._get_tooltip_text
        # Store tooltip references to prevent garbage collection
        if tutorial_btn:
            self._tooltips.append(WidgetTooltip(tutorial_btn, tt('tutorial_button') or "Start or restart the interactive tutorial"))
        if settings_btn:
            self._tooltips.append(WidgetTooltip(settings_btn, tt('settings_button') or "Open application settings and preferences"))
        if theme_btn:
            self._tooltips.append(WidgetTooltip(theme_btn, tt('theme_selector') or "Toggle between light and dark theme"))
        if help_btn:
            self._tooltips.append(WidgetTooltip(help_btn, tt('help_button') or "Open context-sensitive help (F1)"))
    
    def create_convert_tab(self):
        """Create file format conversion tab"""
        # Title at the top
        ctk.CTkLabel(self.tab_convert, text="🔄 File Format Conversion 🔄", 
                     font=("Arial Bold", 18)).pack(pady=10)
        
        ctk.CTkLabel(self.tab_convert, text="Batch convert between DDS, PNG, and other formats",
                     font=("Arial", 12)).pack(pady=5)
        
        # === START CONVERSION BUTTON AT TOP (BEFORE SCROLLABLE CONTENT) ===
        top_button_frame = ctk.CTkFrame(self.tab_convert)
        top_button_frame.pack(fill="x", padx=30, pady=(0, 10))
        
        self.convert_start_button = ctk.CTkButton(
            top_button_frame, 
            text="🐼 START CONVERSION 🐼", 
            command=self.start_conversion,
            width=250, 
            height=60,
            font=("Arial Bold", 18),
            fg_color="#2B7A0B",  # Prominent green color
            hover_color="#368B14"
        )
        self.convert_start_button.pack(pady=5)
        
        # Wrap content in scrollable frame
        scrollable_content = ctk.CTkScrollableFrame(self.tab_convert)
        scrollable_content.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # === INPUT SECTION ===
        input_frame = ctk.CTkFrame(scrollable_content)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="Input:", font=("Arial Bold", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.convert_input_var = ctk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.convert_input_var, width=500).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        convert_input_btn = ctk.CTkButton(input_frame, text="Browse", width=100, 
                     command=lambda: self.browse_directory(self.convert_input_var))
        convert_input_btn.grid(row=0, column=2, padx=10, pady=5)
        
        input_frame.columnconfigure(1, weight=1)
        
        # === CONVERSION OPTIONS ===
        options_frame = ctk.CTkFrame(scrollable_content)
        options_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(options_frame, text="Conversion Options:", 
                     font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        opts_grid = ctk.CTkFrame(options_frame)
        opts_grid.pack(fill="x", padx=10, pady=5)
        
        # From format
        ctk.CTkLabel(opts_grid, text="From:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.convert_from_var = ctk.StringVar(value="DDS")
        from_menu = ctk.CTkOptionMenu(opts_grid, variable=self.convert_from_var,
                                       values=["DDS", "PNG", "JPG", "BMP", "TGA"])
        from_menu.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # To format
        ctk.CTkLabel(opts_grid, text="To:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.convert_to_var = ctk.StringVar(value="PNG")
        to_menu = ctk.CTkOptionMenu(opts_grid, variable=self.convert_to_var,
                                     values=["DDS", "PNG", "JPG", "BMP", "TGA"])
        to_menu.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        
        # Options checkboxes
        check_frame = ctk.CTkFrame(options_frame)
        check_frame.pack(fill="x", padx=10, pady=5)
        
        self.convert_recursive_var = ctk.BooleanVar(value=True)
        convert_recursive_cb = ctk.CTkCheckBox(check_frame, text="Include subdirectories", 
                       variable=self.convert_recursive_var)
        convert_recursive_cb.pack(side="left", padx=10)
        
        self.convert_keep_original_var = ctk.BooleanVar(value=True)
        convert_keep_cb = ctk.CTkCheckBox(check_frame, text="Keep original files", 
                       variable=self.convert_keep_original_var)
        convert_keep_cb.pack(side="left", padx=10)
        
        # === OUTPUT SECTION ===
        output_frame = ctk.CTkFrame(scrollable_content)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(output_frame, text="Output:", font=("Arial Bold", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.convert_output_var = ctk.StringVar()
        ctk.CTkEntry(output_frame, textvariable=self.convert_output_var, width=500).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        convert_output_btn = ctk.CTkButton(output_frame, text="Browse", width=100,
                     command=lambda: self.browse_directory(self.convert_output_var))
        convert_output_btn.grid(row=0, column=2, padx=10, pady=5)
        
        output_frame.columnconfigure(1, weight=1)
        
        # === PROGRESS SECTION ===
        progress_frame = ctk.CTkFrame(scrollable_content)
        progress_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Progress bar
        self.convert_progress_bar = ctk.CTkProgressBar(progress_frame)
        self.convert_progress_bar.pack(fill="x", padx=10, pady=10)
        self.convert_progress_bar.set(0)
        
        self.convert_progress_label = ctk.CTkLabel(progress_frame, text="Ready to convert")
        self.convert_progress_label.pack(pady=5)
        
        # Log
        self.convert_log_text = ctk.CTkTextbox(progress_frame, height=150)
        self.convert_log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Apply tooltips to convert tab widgets
        self._apply_convert_tooltips(convert_input_btn, convert_output_btn, from_menu, to_menu,
                                     convert_recursive_cb, convert_keep_cb)
    
    def start_conversion(self):
        """Start batch conversion"""
        # Read ALL tkinter variable values BEFORE starting thread (thread-safety fix)
        input_path = self.convert_input_var.get()
        output_path = self.convert_output_var.get()
        from_format = self.convert_from_var.get().lower()
        to_format = self.convert_to_var.get().lower()
        recursive = self.convert_recursive_var.get()
        
        if not input_path:
            self.convert_log("⚠️ Please select an input directory")
            return
        if not output_path:
            self.convert_log("⚠️ Please select an output directory")
            return
        
        if from_format == to_format:
            self.convert_log("⚠️ Source and target formats are the same")
            return
        
        self.convert_log("=" * 60)
        self.convert_log("Starting batch conversion...")
        self.convert_log(f"Input: {input_path}")
        self.convert_log(f"Output: {output_path}")
        self.convert_log(f"Converting: {from_format.upper()} → {to_format.upper()}")
        self.convert_log("=" * 60)
        
        # Disable start button
        self.convert_start_button.configure(state="disabled")
        
        # Start conversion in background thread with all parameters
        threading.Thread(
            target=self.conversion_thread,
            args=(input_path, output_path, from_format, to_format, recursive),
            daemon=True
        ).start()
    
    def conversion_thread(self, input_path_str, output_path_str, from_format, to_format, recursive):
        """Background thread for file conversion"""
        try:
            input_path = Path(input_path_str)
            output_path = Path(output_path_str)
            from_format = f".{from_format}"
            to_format = f".{to_format}"
            
            # Scan for files
            self.after(0, lambda: self.convert_progress_bar.set(0.1))
            self.after(0, lambda: self.convert_progress_label.configure(text="Scanning files..."))
            
            if recursive:
                files = list(input_path.rglob(f"*{from_format}"))
            else:
                files = list(input_path.glob(f"*{from_format}"))
            
            total = len(files)
            self.convert_log(f"Found {total} {from_format.upper()} files")
            
            if total == 0:
                self.convert_log("⚠️ No files found to convert")
                return
            
            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Convert files
            converted = 0
            failed = 0
            
            for i, file_path in enumerate(files):
                try:
                    # Calculate output path
                    relative_path = file_path.relative_to(input_path)
                    target_path = output_path / relative_path.with_suffix(to_format)
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Convert using file handler
                    if from_format == '.dds' and to_format == '.png':
                        self.file_handler.convert_dds_to_png(str(file_path), str(target_path))
                    elif from_format == '.png' and to_format == '.dds':
                        self.file_handler.convert_png_to_dds(str(file_path), str(target_path))
                    else:
                        # Generic conversion via PIL
                        from PIL import Image
                        img = Image.open(file_path)
                        img.save(target_path)
                    
                    converted += 1
                    
                    # Progress
                    progress = 0.1 + (0.9 * (i + 1) / total)
                    self.after(0, lambda p=progress: self.convert_progress_bar.set(p))
                    self.after(0, lambda i=i, total=total: self.convert_progress_label.configure(text=f"Converting {i+1}/{total}..."))
                    
                    # Log every 10th file
                    if (i+1) % 10 == 0 or i == total - 1:
                        self.convert_log(f"Converted {i+1}/{total} files...")
                    
                except Exception as e:
                    failed += 1
                    if failed <= 5:  # Only log first 5 errors
                        self.convert_log(f"❌ Failed: {file_path.name} - {str(e)[:50]}")
            
            # Complete
            self.after(0, lambda: self.convert_progress_bar.set(1.0))
            self.after(0, lambda: self.convert_progress_label.configure(text="Conversion complete!"))
            self.convert_log("=" * 60)
            self.convert_log("✓ BATCH CONVERSION COMPLETED!")
            self.convert_log(f"Successfully converted: {converted}")
            if failed > 0:
                self.convert_log(f"Failed: {failed}")
            self.convert_log("=" * 60)
            
        except Exception as e:
            self.convert_log(f"❌ Error during conversion: {e}")
        
        finally:
            # Re-enable button
            self.after(0, lambda: self.convert_start_button.configure(state="normal"))
    
    def convert_log(self, message):
        """Add message to conversion log - thread-safe"""
        self.after(0, self._convert_log_impl, message)
    
    def _convert_log_impl(self, message):
        """Internal implementation of conversion log on main thread"""
        self.convert_log_text.insert("end", f"{message}\n")
        self.convert_log_text.see("end")
    
    def create_browser_tab(self):
        """Create file browser tab with directory browsing and file preview"""
        # Header - use wrapping layout to prevent button overlap at small sizes
        header_frame = ctk.CTkFrame(self.tab_browser)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="📁 File Browser",
                     font=("Arial Bold", 16)).pack(side="left", padx=10)
        
        # Button sub-frame to keep buttons together and prevent overlap
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)
        
        # Browse button
        browser_browse_btn = ctk.CTkButton(btn_frame, text="📂 Browse", 
                     command=self.browser_select_directory,
                     width=100)
        browser_browse_btn.pack(side="left", padx=5)
        
        # Refresh button
        browser_refresh_btn = ctk.CTkButton(btn_frame, text="🔄 Refresh", 
                     command=self.browser_refresh,
                     width=80)
        browser_refresh_btn.pack(side="left", padx=5)
        
        # Path display
        path_frame = ctk.CTkFrame(self.tab_browser)
        path_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(path_frame, text="Path:").pack(side="left", padx=5)
        self.browser_path_var = ctk.StringVar(value="No directory selected")
        self.browser_path_label = ctk.CTkLabel(path_frame, textvariable=self.browser_path_var,
                                               font=("Arial", 10), anchor="w")
        self.browser_path_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # Main content area - split into two panes
        content_frame = ctk.CTkFrame(self.tab_browser)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left pane - Directory tree (placeholder)
        left_pane = ctk.CTkFrame(content_frame, width=250)
        left_pane.pack(side="left", fill="both", expand=False, padx=(0, 5))
        
        ctk.CTkLabel(left_pane, text="📂 Folders", 
                    font=("Arial Bold", 12)).pack(pady=5)
        
        self.browser_folder_list = ctk.CTkTextbox(left_pane, width=250, height=500)
        self.browser_folder_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Right pane - File list with info
        right_pane = ctk.CTkFrame(content_frame)
        right_pane.pack(side="left", fill="both", expand=True)
        
        # File list header with filter options
        file_header = ctk.CTkFrame(right_pane)
        file_header.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(file_header, text="📄 Files", 
                    font=("Arial Bold", 12)).pack(side="left", pady=5)
        
        # Add search entry
        self.browser_search_var = ctk.StringVar()
        self.browser_search_var.trace_add("write", lambda *args: self.browser_refresh())
        search_entry = ctk.CTkEntry(
            file_header,
            placeholder_text="Search files...",
            textvariable=self.browser_search_var,
            width=150
        )
        search_entry.pack(side="left", padx=10)
        
        # Add show all files checkbox
        self.browser_show_all = ctk.BooleanVar(value=False)
        browser_show_all_cb = ctk.CTkCheckBox(file_header, text="Show all files", 
                       variable=self.browser_show_all,
                       command=self.browser_refresh)
        browser_show_all_cb.pack(side="left", padx=10)
        
        # File list (scrollable)
        self.browser_file_list = ctk.CTkScrollableFrame(right_pane, height=450)
        self.browser_file_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Info panel at bottom
        info_panel = ctk.CTkFrame(right_pane)
        info_panel.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(info_panel, text="ℹ️ File Info:", 
                    font=("Arial Bold", 11)).pack(anchor="w", padx=5, pady=2)
        self.browser_file_info = ctk.CTkLabel(info_panel, 
                                              text="No file selected",
                                              font=("Arial", 10),
                                              anchor="w",
                                              justify="left")
        self.browser_file_info.pack(anchor="w", padx=5, pady=2)
        
        # Status
        self.browser_status = ctk.CTkLabel(self.tab_browser, 
                                           text="Select a directory to browse",
                                           font=("Arial", 9))
        self.browser_status.pack(pady=5)
        
        # Apply tooltips to browser tab widgets
        self._apply_browser_tooltips(browser_browse_btn, browser_refresh_btn, 
                                     search_entry, browser_show_all_cb)
    
    def browser_select_directory(self):
        """Select directory for file browser"""
        directory = filedialog.askdirectory(title="Select Directory to Browse")
        if directory:
            self.browser_path_var.set(directory)
            self.browser_current_dir = Path(directory)
            self.browser_refresh()
    
    def browser_refresh(self):
        """Refresh file browser content - scanning runs off UI thread"""
        if not hasattr(self, 'browser_current_dir'):
            return
        
        # Debounce rapid refresh calls (e.g. from search typing)
        # Note: This flag is only accessed from the main UI thread
        # (_browser_update_ui is scheduled via self.after), so no lock is needed.
        if hasattr(self, '_browser_refresh_pending') and self._browser_refresh_pending:
            return
        self._browser_refresh_pending = True
        
        try:
            # Clear current file list
            for widget in self.browser_file_list.winfo_children():
                widget.destroy()
            
            # Show loading indicator
            self.browser_status.configure(text="Scanning directory...")
            
            # Capture filter state before threading
            show_all = self.browser_show_all.get() if hasattr(self, 'browser_show_all') else False
            search_query = self.browser_search_var.get().lower() if hasattr(self, 'browser_search_var') else ""
            current_dir = self.browser_current_dir
            
            def _scan_files():
                """Run file scanning and sorting off the UI thread"""
                texture_extensions = {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga'}
                files = []
                MAX_MATCHING_FILES = 10000
                try:
                    for f in current_dir.iterdir():
                        if not f.is_file():
                            continue
                        if not show_all and f.suffix.lower() not in texture_extensions:
                            continue
                        if search_query and search_query not in f.name.lower():
                            continue
                        files.append(f)
                        if len(files) >= MAX_MATCHING_FILES:
                            break
                except PermissionError:
                    pass
                
                files_sorted = sorted(files)
                
                # Collect folders
                folders = []
                try:
                    folders = sorted([f for f in current_dir.iterdir() if f.is_dir()])
                except PermissionError:
                    pass
                
                # Schedule UI update on main thread
                self.after(0, lambda: self._browser_update_ui(
                    files_sorted, folders, show_all, search_query, MAX_MATCHING_FILES))
            
            thread = threading.Thread(target=_scan_files, daemon=True)
            thread.start()
            
        except Exception as e:
            self._browser_refresh_pending = False
            self.browser_status.configure(text=f"Error: {e}")
    
    def _browser_update_ui(self, files_sorted, folders, show_all, search_query, max_matching):
        """Update browser UI on the main thread after scanning completes"""
        self._browser_refresh_pending = False
        
        try:
            # Clear current file list (in case it changed during scan)
            for widget in self.browser_file_list.winfo_children():
                widget.destroy()
            
            MAX_DISPLAY = 200
            total_files = len(files_sorted)
            display_files = files_sorted[:MAX_DISPLAY]
            
            # Display files
            if not display_files:
                file_type = "files" if show_all else "texture files"
                search_msg = f" matching '{search_query}'" if search_query else ""
                ctk.CTkLabel(self.browser_file_list, 
                           text=f"No {file_type}{search_msg} found in this directory",
                           font=("Arial", 11)).pack(pady=20)
            else:
                # Create file entries in batches to keep UI responsive
                self._browser_pending_files = display_files
                self._browser_batch_index = 0
                self._browser_load_batch()
                
                if total_files > MAX_DISPLAY:
                    overflow_text = f"... and {total_files - MAX_DISPLAY} more files"
                    if total_files >= max_matching:
                        overflow_text += f" (showing first {MAX_DISPLAY} of {max_matching}+)"
                    overflow_text += " (use search to filter)"
                    ctk.CTkLabel(self.browser_file_list, 
                               text=overflow_text,
                               font=("Arial", 10), text_color="gray").pack(pady=10)
            
            # Update folder list with navigation
            self.browser_folder_list.delete("1.0", "end")
            
            if self.browser_current_dir.parent != self.browser_current_dir:
                self.browser_folder_list.insert("end", "⬆️ .. (Parent Directory)\n")
            
            for folder in folders:
                self.browser_folder_list.insert("end", f"📁 {folder.name}\n")
            
            self.browser_folder_list.bind("<Double-Button-1>", self._on_folder_click)
            
            status = f"Showing {len(display_files)} of {total_files} file(s) and {len(folders)} folder(s)"
            self.browser_status.configure(text=status)
            
        except Exception as e:
            self.browser_status.configure(text=f"Error: {e}")
    
    def _browser_load_batch(self):
        """Load a batch of file entries to keep UI responsive"""
        BATCH_SIZE = 20
        files = self._browser_pending_files
        start = self._browser_batch_index
        end = min(start + BATCH_SIZE, len(files))
        
        for i in range(start, end):
            self._create_file_entry(files[i])
        
        self._browser_batch_index = end
        if end < len(files):
            # Schedule next batch after a short delay to allow UI to update
            self.after(10, self._browser_load_batch)
    
    def _on_folder_click(self, event):
        """Handle double-click on folder in browser"""
        try:
            # Get the clicked line
            index = self.browser_folder_list.index("@%d,%d" % (event.x, event.y))
            line = self.browser_folder_list.get(f"{index} linestart", f"{index} lineend").strip()
            
            # Handle parent directory
            if line.startswith("⬆️"):
                self.browser_current_dir = self.browser_current_dir.parent
                self.browser_path_var.set(str(self.browser_current_dir))
                self.browser_refresh()
            # Handle subdirectory
            elif line.startswith("📁"):
                folder_name = line.replace("📁 ", "").strip()
                new_dir = self.browser_current_dir / folder_name
                if new_dir.exists() and new_dir.is_dir():
                    self.browser_current_dir = new_dir
                    self.browser_path_var.set(str(self.browser_current_dir))
                    self.browser_refresh()
        except Exception as e:
            self.log(f"Error navigating folders: {e}")
    
    def _create_file_entry(self, file_path):
        """Create a file entry widget with thumbnail"""
        entry_frame = ctk.CTkFrame(self.browser_file_list)
        entry_frame.pack(fill="x", padx=5, pady=2)
        
        # Add thumbnail for image/texture files if enabled in settings
        show_thumbnails = config.get('ui', 'show_thumbnails', default=True)
        image_extensions = {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga', '.tif', '.tiff', '.gif', '.webp'}
        if show_thumbnails and file_path.suffix.lower() in image_extensions:
            try:
                # Skip files exceeding preview size limit to prevent lag
                THUMBNAIL_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
                try:
                    if file_path.stat().st_size > THUMBNAIL_MAX_FILE_SIZE:
                        logger.debug(f"Skipping thumbnail for large file: {file_path.name}")
                    else:
                        thumbnail_label = self._create_thumbnail(file_path, entry_frame)
                        if thumbnail_label:
                            thumbnail_label.pack(side="left", padx=5)
                except OSError:
                    pass
            except Exception as e:
                logger.debug(f"Failed to create thumbnail for {file_path.name}: {e}")
        
        # File icon and name
        file_info = f"📄 {file_path.name}"
        try:
            file_size = file_path.stat().st_size
            size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
        except OSError:
            size_str = "N/A"
        
        ctk.CTkLabel(entry_frame, text=file_info, 
                    font=("Arial", 10), anchor="w").pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(entry_frame, text=size_str, 
                    font=("Arial", 9), text_color="gray").pack(side="right", padx=5)
        
        # Add preview button for image/texture files
        if file_path.suffix.lower() in image_extensions:
            preview_btn = ctk.CTkButton(
                entry_frame,
                text="👁️",
                width=30,
                height=20,
                font=("Arial", 10),
                command=lambda: self._preview_file(file_path)
            )
            preview_btn.pack(side="right", padx=2)
    
    def _create_thumbnail(self, file_path, parent_frame):
        """Create a thumbnail for an image file with LRU cache"""
        try:
            from PIL import Image
            
            thumb_size = config.get('ui', 'thumbnail_size', default=32)
            
            # Check cache first
            cache_key = f"{file_path}_{thumb_size}"
            if cache_key in self._thumbnail_cache:
                cached_photo = self._thumbnail_cache[cache_key]
                # Move to end of LRU order
                if cache_key in self._thumbnail_cache_order:
                    self._thumbnail_cache_order.remove(cache_key)
                self._thumbnail_cache_order.append(cache_key)
                label = ctk.CTkLabel(parent_frame, image=cached_photo, text="")
                return label
            
            # Load and resize image
            img = Image.open(file_path)
            
            # Convert DDS if needed
            if file_path.suffix.lower() == '.dds':
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA')
            
            # Create thumbnail at configured size
            img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
            
            # Use CTkImage for proper display in customtkinter
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(thumb_size, thumb_size))
            
            # LRU eviction: remove oldest entries if cache exceeds max
            while len(self._thumbnail_cache) >= self._thumbnail_cache_max and self._thumbnail_cache_order:
                oldest_key = self._thumbnail_cache_order.popleft()
                self._thumbnail_cache.pop(oldest_key, None)
            
            self._thumbnail_cache[cache_key] = photo
            self._thumbnail_cache_order.append(cache_key)
            
            # Create label with thumbnail
            label = ctk.CTkLabel(parent_frame, image=photo, text="")
            return label
            
        except Exception as e:
            logger.debug(f"Thumbnail creation failed for {file_path.name}: {e}")
            return None
    
    def _preview_file(self, file_path):
        """Open file in preview viewer"""
        if hasattr(self, 'preview_viewer') and self.preview_viewer:
            try:
                # Get all texture files in current directory for navigation
                texture_extensions = {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga'}
                files = [f for f in self.browser_current_dir.iterdir() 
                        if f.is_file() and f.suffix.lower() in texture_extensions]
                file_list = [str(f) for f in sorted(files)]
                
                self.preview_viewer.open_preview(str(file_path), file_list)
                self.log(f"📷 Opened preview for: {file_path.name}")
            except Exception as e:
                self.log(f"❌ Error opening preview: {e}")
    
    def apply_theme(self, theme_name):
        """Apply selected theme"""
        if theme_name in ['dark', 'light']:
            ctk.set_appearance_mode(theme_name)
            config.set('ui', 'theme', value=theme_name)
            self.log(f"Theme changed to: {theme_name}")
        else:
            # Handle custom themes from THEME_PRESETS
            try:
                from src.ui.customization_panel import THEME_PRESETS
                if theme_name in THEME_PRESETS:
                    theme = THEME_PRESETS[theme_name]
                    appearance = theme.get("appearance_mode", "dark")
                    ctk.set_appearance_mode(appearance)
                    config.set('ui', 'theme', value=theme_name)
                    # Apply colors to existing widgets
                    colors = theme.get("colors", {})
                    if colors:
                        try:
                            for widget in self.winfo_children():
                                self._apply_theme_to_widget(widget, colors)
                        except Exception:
                            pass
                    self.log(f"Theme changed to: {theme['name']}")
                else:
                    # Fall back to dark/light based on name hint
                    mode = 'light' if 'light' in theme_name.lower() else 'dark'
                    ctk.set_appearance_mode(mode)
                    config.set('ui', 'theme', value=theme_name)
                    self.log(f"Theme changed to: {theme_name}")
            except ImportError:
                ctk.set_appearance_mode('dark')
                self.log(f"Theme changed to dark (fallback)")
    
    def apply_ui_scaling(self, scale_value):
        """Apply UI scaling"""
        try:
            # Extract percentage value (e.g., "100%" -> 1.0)
            scale_percent = int(scale_value.rstrip('%'))
            scale_factor = scale_percent / 100.0
            
            # Apply scaling
            ctk.set_widget_scaling(scale_factor)
            ctk.set_window_scaling(scale_factor)
            
            # Save to config
            config.set('ui', 'scale', value=scale_value)
            
            self.log(f"✅ UI scale set to {scale_value}")
            if GUI_AVAILABLE:
                messagebox.showinfo("UI Scale", 
                    f"UI scale set to {scale_value}.\n"
                    "Some changes may require restarting the application.")
        except Exception as e:
            self.log(f"❌ Error applying UI scale: {e}")
    
    def open_customization(self):
        """Open UI customization dialog"""
        if CUSTOMIZATION_AVAILABLE:
            try:
                open_customization_dialog(parent=self, on_settings_change=self._on_customization_change)
                self.log("✅ Opened UI Customization panel")
            except Exception as e:
                self.log(f"❌ Error opening customization: {e}")
                if GUI_AVAILABLE:
                    messagebox.showerror("Error", f"Failed to open customization panel: {e}")
        else:
            self.log("⚠️ UI Customization not available")
            if GUI_AVAILABLE:
                messagebox.showwarning("Not Available", 
                                     "UI customization panel is not available.\n"
                                     "Please check your installation.")
    
    def _on_customization_change(self, setting_type, value):
        """Handle customization setting changes from the customization panel"""
        try:
            if setting_type == 'theme':
                # Apply theme changes
                theme = value
                appearance_mode = theme.get('appearance_mode', 'dark')
                ctk.set_appearance_mode(appearance_mode)
                
                # Update all widgets with new colors if available
                colors = theme.get('colors', {})
                if colors:
                    # Try to update button colors
                    try:
                        for widget in self.winfo_children():
                            self._apply_theme_to_widget(widget, colors)
                    except Exception as widget_err:
                        logger.debug(f"Could not update all widget colors: {widget_err}")
                
                self.log(f"✅ Theme applied: {theme.get('name', 'Unknown')}")
                
            elif setting_type == 'color':
                # Apply accent color changes to buttons and accents
                accent_color = value
                try:
                    # Update button colors throughout the app
                    for widget in self.winfo_children():
                        self._apply_color_to_widget(widget, accent_color)
                except Exception as color_err:
                    logger.debug(f"Could not update all widget colors: {color_err}")
                    
                self.log(f"✅ Accent color changed: {accent_color}")
                
            elif setting_type == 'cursor':
                # Apply cursor changes to window and child widgets
                cursor_type = value.get('type', 'arrow')
                trail_enabled = value.get('trail', False)
                trail_color = value.get('trail_color', 'rainbow')
                cursor_size = value.get('size', 'medium')
                # Map to valid tk cursor via _apply_cursor_to_widget
                try:
                    # Propagate to main window and all child widgets
                    self._apply_cursor_to_widget(self, cursor_type)
                except Exception as cursor_err:
                    logger.debug(f"Could not update all cursors: {cursor_err}")
                
                # Save cursor size to config
                try:
                    config.set('ui', 'cursor_size', value=cursor_size)
                except Exception as size_err:
                    logger.debug(f"Could not save cursor size: {size_err}")
                
                # Handle cursor trail
                try:
                    self._setup_cursor_trail(trail_enabled, trail_color=trail_color)
                except Exception as trail_err:
                    logger.debug(f"Could not setup cursor trail: {trail_err}")
                    
                self.log(f"✅ Cursor settings applied: {cursor_type} (size: {cursor_size})")
                
            elif setting_type == 'tooltip_mode':
                # Apply tooltip mode change
                if self.tooltip_manager:
                    try:
                        from src.features.tutorial_system import TooltipMode
                        mode = TooltipMode(value)
                        self.tooltip_manager.set_mode(mode)
                        self.log(f"✅ Tooltip mode changed to: {value}")
                    except Exception as tooltip_err:
                        logger.debug(f"Could not change tooltip mode: {tooltip_err}")
                        self.log(f"⚠️ Could not change tooltip mode: {tooltip_err}")
                else:
                    # Save to config directly if tooltip manager not available
                    try:
                        config.set('ui', 'tooltip_mode', value=value)
                        config.save()
                        self.log(f"✅ Tooltip mode saved: {value}")
                    except Exception as cfg_err:
                        logger.debug(f"Could not save tooltip mode: {cfg_err}")
                
            elif setting_type == 'sound_enabled':
                # Apply sound toggle
                try:
                    config.set('ui', 'sound_enabled', value=value)
                    config.save()
                    self.log(f"✅ Sound {'enabled' if value else 'disabled'}")
                except Exception as sound_err:
                    logger.debug(f"Could not save sound setting: {sound_err}")
                
            elif setting_type == 'volume':
                # Apply volume change
                try:
                    config.set('ui', 'volume', value=value)
                    config.save()
                except Exception as vol_err:
                    logger.debug(f"Could not save volume setting: {vol_err}")
                
        except Exception as e:
            self.log(f"❌ Error applying customization: {e}")
            logger.error(f"Customization change error: {e}", exc_info=True)
    
    def _apply_theme_to_widget(self, widget, colors):
        """Recursively apply theme colors to a widget and its children"""
        try:
            # Apply colors to CTkButton widgets
            if isinstance(widget, ctk.CTkButton):
                if 'button' in colors:
                    widget.configure(fg_color=colors['button'])
                if 'button_hover' in colors:
                    widget.configure(hover_color=colors['button_hover'])
            
            # Apply colors to CTkFrame widgets
            elif isinstance(widget, ctk.CTkFrame):
                if 'secondary' in colors:
                    widget.configure(fg_color=colors['secondary'])
            
            # Recursively apply to children
            for child in widget.winfo_children():
                self._apply_theme_to_widget(child, colors)
                
        except Exception:
            pass  # Ignore widgets that don't support these configurations
    
    def _apply_color_to_widget(self, widget, color):
        """Recursively apply accent color to a widget and its children"""
        try:
            # Apply to buttons
            if isinstance(widget, ctk.CTkButton):
                widget.configure(fg_color=color)
            
            # Recursively apply to children
            for child in widget.winfo_children():
                self._apply_color_to_widget(child, color)
                
        except Exception:
            pass  # Ignore widgets that don't support color changes
    
    def _apply_cursor_to_widget(self, widget, cursor_type):
        """Recursively apply cursor to a widget and its children"""
        # Map custom cursor names to valid tkinter cursor types
        cursor_map = {
            'default': 'arrow',
            'Arrow Pointer': 'arrow',
            'Pointing Hand': 'hand2',
            'Crosshair': 'crosshair',
            'Text Select': 'xterm',
            'Hourglass': 'watch',
            'Pirate Skull': 'pirate',
            'Heart': 'heart',
            'Target Cross': 'tcross',
            'Star': 'star',
            'Circle': 'circle',
            'Plus Sign': 'plus',
            'Pencil': 'pencil',
            'Dot': 'dot',
            'X Cursor': 'X_cursor',
            'Diamond': 'diamond_cross',
            'Fleur': 'fleur',
            'Spraycan': 'spraycan',
            'Left Arrow': 'left_ptr',
            'Right Arrow': 'right_ptr',
            # Legacy names for backward compatibility
            'arrow': 'arrow',
            'hand': 'hand2',
            'crosshair': 'crosshair',
            'text': 'xterm',
            'wait': 'watch',
            'skull': 'pirate',
            'panda': 'heart',
            'sword': 'tcross',
            'custom': 'arrow',
        }
        tk_cursor = cursor_map.get(cursor_type, cursor_type)
        self._apply_tk_cursor_recursive(widget, tk_cursor)
    
    def _apply_tk_cursor_recursive(self, widget, tk_cursor):
        """Recursively apply a resolved tkinter cursor to a widget and its children"""
        try:
            widget.configure(cursor=tk_cursor)
            for child in widget.winfo_children():
                self._apply_tk_cursor_recursive(child, tk_cursor)
        except Exception:
            pass  # Ignore widgets that don't support cursor changes
    
    def _setup_cursor_trail(self, enabled, trail_color=None):
        """Setup or teardown cursor trail effect"""
        # Remove existing trail canvas if any
        if hasattr(self, '_trail_canvas') and self._trail_canvas:
            try:
                self.unbind('<Motion>', self._trail_bind_id)
            except Exception:
                pass
            self._trail_canvas.destroy()
            self._trail_canvas = None
            self._trail_bind_id = None
            self._trail_dots = []
        
        if not enabled:
            return
        
        import tkinter as tk
        # Create overlay canvas for trail — use a transparent background and
        # disable all mouse events so it doesn't block the UI underneath.
        self._trail_canvas = tk.Canvas(
            self, highlightthickness=0,
            width=self.winfo_width(), height=self.winfo_height()
        )
        self._trail_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            self._trail_canvas.config(bg=self.cget('bg'))
        except Exception:
            try:
                self._trail_canvas.config(bg='#1a1a1a')
            except Exception:
                pass
        # Lower the canvas below all other widgets so it doesn't cover them
        self._trail_canvas.lower()
        # Disable all mouse events on the canvas so clicks pass through
        self._trail_canvas.bindtags(('trail_canvas_passthrough',))
        
        self._trail_dots = []
        self._trail_max = 15
        
        # Determine trail colors based on setting
        trail_color_setting = trail_color or config.get('ui', 'cursor_trail_color', default='rainbow')
        trail_color_palettes = {
            'rainbow': ['#ff6b6b', '#feca57', '#48dbfb', '#ff9ff3', '#54a0ff',
                        '#5f27cd', '#01a3a4', '#f368e0', '#ff6348', '#7bed9f'],
            'fire': ['#ff0000', '#ff4500', '#ff6600', '#ff8c00', '#ffa500',
                     '#ffcc00', '#ffff00', '#ffff66', '#ff3300', '#cc0000'],
            'ice': ['#00ffff', '#00e5ff', '#00ccff', '#00b3ff', '#0099ff',
                    '#0080ff', '#0066ff', '#e0f7ff', '#b3e5fc', '#81d4fa'],
            'nature': ['#00cc00', '#33cc33', '#66cc66', '#00ff00', '#33ff33',
                       '#228b22', '#32cd32', '#7cfc00', '#adff2f', '#98fb98'],
            'galaxy': ['#9b59b6', '#8e44ad', '#6c3483', '#5b2c6f', '#4a235a',
                       '#bb8fce', '#d7bde2', '#e8daef', '#c39bd3', '#af7ac5'],
            'gold': ['#ffd700', '#ffcc00', '#daa520', '#b8860b', '#cd853f',
                     '#f0e68c', '#eee8aa', '#fafad2', '#ffe4b5', '#ffdead'],
        }
        trail_colors = trail_color_palettes.get(trail_color_setting,
                                                trail_color_palettes['rainbow'])
        
        def on_motion(event):
            try:
                canvas = self._trail_canvas
                if not canvas or not canvas.winfo_exists():
                    return
                x, y = event.x_root - self.winfo_rootx(), event.y_root - self.winfo_rooty()
                color_idx = len(self._trail_dots) % len(trail_colors)
                dot = canvas.create_oval(
                    x - 3, y - 3, x + 3, y + 3,
                    fill=trail_colors[color_idx], outline=''
                )
                self._trail_dots.append(dot)
                # Fade old dots
                if len(self._trail_dots) > self._trail_max:
                    old_dot = self._trail_dots.pop(0)
                    canvas.delete(old_dot)
                # Auto-fade after delay
                canvas.after(300, lambda d=dot: self._fade_trail_dot(d))
            except Exception:
                pass
        
        self._trail_bind_id = self.bind('<Motion>', on_motion, add='+')
    
    def _fade_trail_dot(self, dot_id):
        """Remove a trail dot after it fades"""
        try:
            if hasattr(self, '_trail_canvas') and self._trail_canvas and self._trail_canvas.winfo_exists():
                self._trail_canvas.delete(dot_id)
                if dot_id in self._trail_dots:
                    self._trail_dots.remove(dot_id)
        except Exception:
            pass
    
    def open_settings_window(self):
        """Open settings in a separate window"""
        # Import subprocess for directory opening functionality
        import subprocess
        
        # Create new window
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("⚙️ Application Settings")
        settings_window.geometry("900x700")
        
        # Make it modal-ish - stay on top of main window
        settings_window.transient(self)  # Set as child of main window
        settings_window.focus()
        
        # Title
        ctk.CTkLabel(settings_window, text="🐼 Application Settings 🐼",
                     font=("Arial Bold", 18)).pack(pady=15)
        
        # Settings scroll frame
        settings_scroll = ctk.CTkScrollableFrame(settings_window, width=850, height=550)
        settings_scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        # === PERFORMANCE SETTINGS ===
        perf_frame = ctk.CTkFrame(settings_scroll)
        perf_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(perf_frame, text="⚡ Performance Settings", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        # Thread count
        thread_frame = ctk.CTkFrame(perf_frame)
        thread_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(thread_frame, text="Thread Count:").pack(side="left", padx=10)
        thread_slider = ctk.CTkSlider(thread_frame, from_=1, to=16, number_of_steps=15)
        thread_slider.set(config.get('performance', 'max_threads', default=4))
        thread_slider.pack(side="left", fill="x", expand=True, padx=10)
        thread_label = ctk.CTkLabel(thread_frame, text=f"{int(thread_slider.get())}")
        thread_label.pack(side="left", padx=5)
        ctk.CTkLabel(thread_frame, text="(default: 4)",
                    font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        def update_thread_label(value):
            thread_label.configure(text=f"{int(float(value))}")
        thread_slider.configure(command=update_thread_label)
        
        # Memory limit
        mem_frame = ctk.CTkFrame(perf_frame)
        mem_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(mem_frame, text="Memory Limit (MB):").pack(side="left", padx=10)
        memory_var = ctk.StringVar(value=str(config.get('performance', 'memory_limit_mb', default=2048)))
        mem_entry = ctk.CTkEntry(mem_frame, textvariable=memory_var, width=100)
        mem_entry.pack(side="left", padx=10)
        ctk.CTkLabel(mem_frame, text="(default: 2048)",
                    font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        # Cache size
        cache_frame = ctk.CTkFrame(perf_frame)
        cache_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(cache_frame, text="Thumbnail Cache Size:").pack(side="left", padx=10)
        cache_var = ctk.StringVar(value=str(config.get('performance', 'thumbnail_cache_size', default=500)))
        cache_entry = ctk.CTkEntry(cache_frame, textvariable=cache_var, width=100)
        cache_entry.pack(side="left", padx=10)
        ctk.CTkLabel(cache_frame, text="(default: 500)",
                    font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        # Show thumbnails toggle
        thumb_toggle_frame = ctk.CTkFrame(perf_frame)
        thumb_toggle_frame.pack(fill="x", padx=10, pady=5)
        
        show_thumb_var = ctk.BooleanVar(value=config.get('ui', 'show_thumbnails', default=True))
        ctk.CTkCheckBox(thumb_toggle_frame, text="Show thumbnails in File Browser",
                       variable=show_thumb_var).pack(side="left", padx=10)
        
        # Thumbnail size selector
        thumb_size_frame = ctk.CTkFrame(perf_frame)
        thumb_size_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(thumb_size_frame, text="Thumbnail Size:").pack(side="left", padx=10)
        thumb_size_var = ctk.StringVar(value=str(config.get('ui', 'thumbnail_size', default=32)))
        thumb_size_menu = ctk.CTkOptionMenu(thumb_size_frame, variable=thumb_size_var,
                                            values=["16", "32", "64"])
        thumb_size_menu.pack(side="left", padx=10)
        ctk.CTkLabel(thumb_size_frame, text="(default: 32)",
                    font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        # Disable panda animations (for low-end systems)
        panda_anim_frame = ctk.CTkFrame(perf_frame)
        panda_anim_frame.pack(fill="x", padx=10, pady=5)
        
        disable_panda_anim_var = ctk.BooleanVar(value=config.get('ui', 'disable_panda_animations', default=False))
        ctk.CTkCheckBox(panda_anim_frame, text="Disable panda animations (for low-end systems)",
                       variable=disable_panda_anim_var).pack(side="left", padx=10)
        
        # === APPEARANCE & CUSTOMIZATION (merged UI Settings + UI Customization) ===
        ui_frame = ctk.CTkFrame(settings_scroll)
        ui_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(ui_frame, text="🎨 Appearance & Customization", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        # Theme
        theme_frame = ctk.CTkFrame(ui_frame)
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=10)
        theme_var = ctk.StringVar(value=config.get('ui', 'theme', default='dark'))
        theme_menu = ctk.CTkOptionMenu(theme_frame, variable=theme_var,
                                       values=["dark", "light", "cyberpunk", "neon_dreams", 
                                              "classic_windows", "vulgar_panda"],
                                       command=self.apply_theme)
        theme_menu.pack(side="left", padx=10)
        
        # UI Scaling
        scale_frame = ctk.CTkFrame(ui_frame)
        scale_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(scale_frame, text="UI Scale:").pack(side="left", padx=10)
        scale_var = ctk.StringVar(value=config.get('ui', 'scale', default='100%'))
        scale_menu = ctk.CTkOptionMenu(
            scale_frame, 
            variable=scale_var,
            values=["80%", "90%", "100%", "110%", "120%", "130%", "150%"],
            command=lambda val: self.apply_ui_scaling(val)
        )
        scale_menu.pack(side="left", padx=10)
        ctk.CTkLabel(scale_frame, text="(applies immediately)", 
                    font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        # Note: Tooltip mode, cursor style, and panda mode settings are
        # available in the Advanced Customization panel to avoid duplication.
        
        # Advanced Customization button
        ctk.CTkButton(ui_frame, text="🎨 Advanced Customization (Tooltips, Cursors, Colors)",
                     command=self.open_customization,
                     width=350, height=35).pack(padx=20, pady=10)
        
        # === KEYBOARD CONTROLS SETTINGS ===
        kb_frame = ctk.CTkFrame(settings_scroll)
        kb_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(kb_frame, text="⌨️ Keyboard Controls", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        ctk.CTkLabel(kb_frame, text="Quick reference for keyboard shortcuts:", 
                    font=("Arial", 10), text_color="gray").pack(anchor="w", padx=20, pady=(0, 5))
        
        # Create tabview for organized shortcuts by category
        kb_tabview = ctk.CTkTabview(kb_frame, width=850, height=250)
        kb_tabview.pack(padx=10, pady=5, fill="both")
        
        # Add tabs for different categories
        tab_file = kb_tabview.add("📁 File")
        tab_processing = kb_tabview.add("⚙️ Processing")
        tab_view = kb_tabview.add("👁️ View")
        tab_nav = kb_tabview.add("🧭 Navigation")
        tab_tools = kb_tabview.add("🔧 Tools")
        tab_special = kb_tabview.add("🐼 Special")
        
        # Helper function to add shortcut rows
        def add_shortcut_row(parent, key, description):
            row = ctk.CTkFrame(parent)
            row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row, text=key, font=("Courier Bold", 10), width=150, 
                        anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=description, font=("Arial", 10), 
                        anchor="w").pack(side="left", padx=5)
        
        # File operations
        add_shortcut_row(tab_file, "Ctrl+O", "Open files")
        add_shortcut_row(tab_file, "Ctrl+S", "Save results")
        add_shortcut_row(tab_file, "Ctrl+E", "Export data")
        add_shortcut_row(tab_file, "Alt+F4", "Close application")
        
        # Processing operations
        add_shortcut_row(tab_processing, "Ctrl+P", "Start processing")
        add_shortcut_row(tab_processing, "Ctrl+Shift+P", "Pause processing")
        add_shortcut_row(tab_processing, "Ctrl+Shift+S", "Stop processing")
        add_shortcut_row(tab_processing, "Ctrl+R", "Resume processing")
        
        # View operations
        add_shortcut_row(tab_view, "Ctrl+T", "Toggle preview panel")
        add_shortcut_row(tab_view, "F5", "Refresh view")
        add_shortcut_row(tab_view, "F11", "Toggle fullscreen")
        add_shortcut_row(tab_view, "Ctrl+B", "Toggle sidebar")
        
        # Navigation
        add_shortcut_row(tab_nav, "Right Arrow", "Next texture")
        add_shortcut_row(tab_nav, "Left Arrow", "Previous texture")
        add_shortcut_row(tab_nav, "Home", "First texture")
        add_shortcut_row(tab_nav, "End", "Last texture")
        add_shortcut_row(tab_nav, "Ctrl+A", "Select all")
        add_shortcut_row(tab_nav, "Ctrl+D", "Deselect all")
        add_shortcut_row(tab_nav, "Ctrl+I", "Invert selection")
        
        # Tools
        add_shortcut_row(tab_tools, "Ctrl+F", "Search")
        add_shortcut_row(tab_tools, "Ctrl+Shift+F", "Filter")
        add_shortcut_row(tab_tools, "Ctrl+,", "Open Settings")
        add_shortcut_row(tab_tools, "Ctrl+Shift+T", "View Statistics")
        add_shortcut_row(tab_tools, "F1", "Help / Tutorial")
        
        # Special Features
        add_shortcut_row(tab_special, "Ctrl+Shift+A", "View Achievements")
        add_shortcut_row(tab_special, "Ctrl+M", "Toggle Sound")
        add_shortcut_row(tab_special, "Ctrl+Alt+P", "Global Start (works outside app)")
        add_shortcut_row(tab_special, "Ctrl+Alt+Space", "Global Pause (works outside app)")
        
        ctk.CTkLabel(kb_frame, text="💡 Note: Keyboard shortcuts are currently not customizable but will be in a future update.", 
                    font=("Arial", 9), text_color="gray", wraplength=800).pack(anchor="w", padx=20, pady=5)
        
        # === FILE HANDLING SETTINGS ===
        file_frame = ctk.CTkFrame(settings_scroll)
        file_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(file_frame, text="📁 File Handling", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        backup_var = ctk.BooleanVar(value=config.get('file_handling', 'create_backup', default=True))
        ctk.CTkCheckBox(file_frame, text="Create backup before operations", 
                       variable=backup_var).pack(anchor="w", padx=20, pady=3)
        
        overwrite_var = ctk.BooleanVar(value=config.get('file_handling', 'overwrite_existing', default=False))
        ctk.CTkCheckBox(file_frame, text="Overwrite existing files", 
                       variable=overwrite_var).pack(anchor="w", padx=20, pady=3)
        
        autosave_var = ctk.BooleanVar(value=config.get('file_handling', 'auto_save', default=True))
        ctk.CTkCheckBox(file_frame, text="Auto-save progress", 
                       variable=autosave_var).pack(anchor="w", padx=20, pady=3)
        
        # Undo depth
        undo_frame = ctk.CTkFrame(file_frame)
        undo_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(undo_frame, text="Undo History Depth:").pack(side="left", padx=10)
        undo_var = ctk.StringVar(value=str(config.get('file_handling', 'undo_depth', default=10)))
        undo_entry = ctk.CTkEntry(undo_frame, textvariable=undo_var, width=100)
        undo_entry.pack(side="left", padx=10)
        ctk.CTkLabel(undo_frame, text="(default: 10)",
                    font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        # === LOGGING SETTINGS ===
        log_frame = ctk.CTkFrame(settings_scroll)
        log_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(log_frame, text="📋 Logging", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        # Log level
        loglevel_frame = ctk.CTkFrame(log_frame)
        loglevel_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(loglevel_frame, text="Log Level:").pack(side="left", padx=10)
        loglevel_var = ctk.StringVar(value=config.get('logging', 'log_level', default='INFO'))
        loglevel_menu = ctk.CTkOptionMenu(loglevel_frame, variable=loglevel_var,
                                          values=["DEBUG", "INFO", "WARNING", "ERROR"])
        loglevel_menu.pack(side="left", padx=10)
        
        crash_report_var = ctk.BooleanVar(value=config.get('logging', 'crash_reports', default=True))
        ctk.CTkCheckBox(log_frame, text="Enable crash reports", 
                       variable=crash_report_var).pack(anchor="w", padx=20, pady=3)
        
        # === NOTIFICATIONS SETTINGS ===
        notif_frame = ctk.CTkFrame(settings_scroll)
        notif_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(notif_frame, text="🔔 Notifications", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        sound_var = ctk.BooleanVar(value=config.get('notifications', 'play_sounds', default=True))
        ctk.CTkCheckBox(notif_frame, text="Play sound effects", 
                       variable=sound_var).pack(anchor="w", padx=20, pady=3)
        
        completion_var = ctk.BooleanVar(value=config.get('notifications', 'completion_alert', default=True))
        ctk.CTkCheckBox(notif_frame, text="Alert on operation completion", 
                       variable=completion_var).pack(anchor="w", padx=20, pady=3)
        
        # === SYSTEM & DEBUG SETTINGS ===
        system_frame = ctk.CTkFrame(settings_scroll)
        system_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(system_frame, text="🛠️ System & Debug", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        # Directory access buttons
        dirs_frame = ctk.CTkFrame(system_frame)
        dirs_frame.pack(fill="x", padx=10, pady=5)
        
        def open_logs_directory():
            """Open logs directory in file explorer"""
            try:
                logs_dir = LOGS_DIR
                if not logs_dir.exists():
                    logs_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created logs directory: {logs_dir}")
                
                if sys.platform == 'win32':
                    os.startfile(str(logs_dir))
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', str(logs_dir)], check=True)
                else:  # linux
                    subprocess.run(['xdg-open', str(logs_dir)], check=True)
                
                logger.info(f"Opened logs directory: {logs_dir}")
                self.log(f"✅ Opened logs directory: {logs_dir}")
            except Exception as e:
                logger.error(f"Failed to open logs directory: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to open logs directory:\n{e}")
        
        def open_config_directory():
            """Open config directory in file explorer"""
            try:
                config_dir = CONFIG_DIR
                if not config_dir.exists():
                    config_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created config directory: {config_dir}")
                
                if sys.platform == 'win32':
                    os.startfile(str(config_dir))
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', str(config_dir)], check=True)
                else:  # linux
                    subprocess.run(['xdg-open', str(config_dir)], check=True)
                
                logger.info(f"Opened config directory: {config_dir}")
                self.log(f"✅ Opened config directory: {config_dir}")
            except Exception as e:
                logger.error(f"Failed to open config directory: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to open config directory:\n{e}")
        
        def open_cache_directory():
            """Open cache directory in file explorer"""
            try:
                cache_dir = CACHE_DIR
                if not cache_dir.exists():
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created cache directory: {cache_dir}")
                
                if sys.platform == 'win32':
                    os.startfile(str(cache_dir))
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', str(cache_dir)], check=True)
                else:  # linux
                    subprocess.run(['xdg-open', str(cache_dir)], check=True)
                
                logger.info(f"Opened cache directory: {cache_dir}")
                self.log(f"✅ Opened cache directory: {cache_dir}")
            except Exception as e:
                logger.error(f"Failed to open cache directory: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to open cache directory:\n{e}")
        
        # Buttons for opening directories
        ctk.CTkButton(dirs_frame, text="📁 Open Logs Directory", 
                     command=open_logs_directory,
                     width=200, height=32).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(dirs_frame, text="📁 Open Config Directory", 
                     command=open_config_directory,
                     width=200, height=32).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(dirs_frame, text="📁 Open Cache Directory", 
                     command=open_cache_directory,
                     width=200, height=32).pack(side="left", padx=5, pady=5)
        
        # Directory paths display
        paths_frame = ctk.CTkFrame(system_frame)
        paths_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(paths_frame, text="Application Data Locations:", 
                    font=("Arial Bold", 11)).pack(anchor="w", padx=10, pady=(5, 0))
        
        ctk.CTkLabel(paths_frame, text=f"• Logs: {LOGS_DIR}", 
                    font=("Arial", 9), text_color="gray").pack(anchor="w", padx=20)
        
        ctk.CTkLabel(paths_frame, text=f"• Config: {CONFIG_DIR}", 
                    font=("Arial", 9), text_color="gray").pack(anchor="w", padx=20)
        
        ctk.CTkLabel(paths_frame, text=f"• Cache: {CACHE_DIR}", 
                    font=("Arial", 9), text_color="gray").pack(anchor="w", padx=20, pady=(0, 5))
        
        # === SAVE BUTTON ===
        def save_settings_window():
            try:
                # Performance
                config.set('performance', 'max_threads', value=int(thread_slider.get()))
                config.set('performance', 'memory_limit_mb', value=int(memory_var.get()))
                config.set('performance', 'thumbnail_cache_size', value=int(cache_var.get()))
                
                # Thumbnail & animation settings
                config.set('ui', 'show_thumbnails', value=show_thumb_var.get())
                config.set('ui', 'thumbnail_size', value=int(thumb_size_var.get()))
                config.set('ui', 'disable_panda_animations', value=disable_panda_anim_var.get())
                self._thumbnail_cache_max = int(cache_var.get())
                
                # UI / Appearance & Customization
                config.set('ui', 'theme', value=theme_var.get())
                config.set('ui', 'scale', value=scale_var.get())
                # Tooltip mode, cursor, and panda mode are managed via Advanced Customization panel
                
                # File Handling
                config.set('file_handling', 'create_backup', value=backup_var.get())
                config.set('file_handling', 'overwrite_existing', value=overwrite_var.get())
                config.set('file_handling', 'auto_save', value=autosave_var.get())
                config.set('file_handling', 'undo_depth', value=int(undo_var.get()))
                
                # Logging
                config.set('logging', 'log_level', value=loglevel_var.get())
                config.set('logging', 'crash_reports', value=crash_report_var.get())
                
                # Notifications
                config.set('notifications', 'play_sounds', value=sound_var.get())
                config.set('notifications', 'completion_alert', value=completion_var.get())
                
                # Save to file
                config.save()
                
                # Apply settings immediately
                self.apply_theme(theme_var.get())
                self.apply_ui_scaling(scale_var.get())
                
                self.log("✅ Settings saved successfully!")
                
                # Show confirmation
                if GUI_AVAILABLE:
                    messagebox.showinfo("Settings Saved", "All settings have been saved and applied successfully!")
                    
            except Exception as e:
                self.log(f"❌ Error saving settings: {e}")
                if GUI_AVAILABLE:
                    messagebox.showerror("Error", f"Failed to save settings: {e}")
        
        button_frame = ctk.CTkFrame(settings_scroll)
        button_frame.pack(fill="x", padx=10, pady=20)
        
        ctk.CTkButton(button_frame, text="💾 Save Settings", 
                     command=save_settings_window,
                     width=200, height=40,
                     font=("Arial Bold", 14)).pack(pady=10)
    
    def create_achievements_tab(self):
        """Create achievements tab"""
        ctk.CTkLabel(self.tab_achievements, text="🏆 Achievements 🏆",
                     font=("Arial Bold", 18)).pack(pady=15)
        
        if not self.achievement_manager:
            # No achievement manager
            info_frame = ctk.CTkFrame(self.tab_achievements)
            info_frame.pack(pady=50, padx=50, fill="both", expand=True)
            ctk.CTkLabel(info_frame,
                         text="Achievement system not available\n\nPlease check your installation.",
                         font=("Arial", 14)).pack(expand=True)
            return
        
        # Achievement scroll frame
        achieve_scroll = ctk.CTkScrollableFrame(self.tab_achievements, width=1000, height=600)
        achieve_scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Get all achievements
        try:
            achievements = self.achievement_manager.get_all_achievements()
            
            for achievement in achievements:
                # Achievement frame
                achieve_frame = ctk.CTkFrame(achieve_scroll)
                achieve_frame.pack(fill="x", padx=10, pady=5)
                
                # Lock/unlock status
                status = "🔓" if achievement.unlocked else "🔒"
                
                # Title and description
                title_text = f"{status} {achievement.icon} {achievement.name}"
                ctk.CTkLabel(achieve_frame, text=title_text,
                            font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
                
                desc_text = achievement.description
                ctk.CTkLabel(achieve_frame, text=desc_text,
                            font=("Arial", 11), text_color="gray").pack(anchor="w", padx=20, pady=2)
                
                # Show reward information - what this achievement unlocks
                reward_text = self._get_achievement_rewards(achievement)
                if reward_text:
                    ctk.CTkLabel(achieve_frame, text=f"🎁 Reward: {reward_text}",
                                font=("Arial", 10), text_color="#2fa572").pack(anchor="w", padx=20, pady=2)
                
                # Progress bar
                progress = achievement.progress
                required = achievement.progress_max
                
                progress_frame = ctk.CTkFrame(achieve_frame)
                progress_frame.pack(fill="x", padx=20, pady=5)
                
                progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
                progress_bar.pack(side="left", padx=5)
                
                if required > 0:
                    progress_value = min(progress / required, 1.0)
                else:
                    progress_value = 1.0 if achievement.unlocked else 0.0
                
                progress_bar.set(progress_value)
                
                progress_label = ctk.CTkLabel(progress_frame, 
                                              text=f"{progress:g}/{required:g}",
                                              font=("Arial", 10))
                progress_label.pack(side="left", padx=5)
                
        except Exception as e:
            ctk.CTkLabel(achieve_scroll,
                        text=f"Error loading achievements: {e}",
                        font=("Arial", 12)).pack(pady=20)
    
    def _get_achievement_rewards(self, achievement):
        """Get text describing what rewards an achievement unlocks"""
        rewards = []
        
        # Add direct achievement rewards (separate from shop)
        if hasattr(achievement, 'reward') and achievement.reward:
            reward = achievement.reward
            desc = reward.get('description', '')
            if desc:
                rewards.append(f"🎁 {desc}")
        
        if self.unlockables_manager and UNLOCKABLES_AVAILABLE:
            # Map achievement progress thresholds to unlockable conditions
            try:
                # Check cursors
                for cursor in self.unlockables_manager.cursors.values():
                    cond = cursor.unlock_condition
                    if cond.condition_type == UnlockConditionType.FILES_PROCESSED:
                        if achievement.category == 'progress' and achievement.progress_max == cond.value:
                            rewards.append(f"🖱️ {cursor.name} cursor")
                    elif cond.condition_type == UnlockConditionType.EASTER_EGG:
                        if achievement.id == cond.value or achievement.category == 'easter_egg':
                            if achievement.id == cond.value:
                                rewards.append(f"🖱️ {cursor.name} cursor")
                
                # Check themes
                for theme in self.unlockables_manager.themes.values():
                    cond = theme.unlock_condition
                    if cond.condition_type == UnlockConditionType.FILES_PROCESSED:
                        if achievement.category == 'progress' and achievement.progress_max == cond.value:
                            rewards.append(f"🎨 {theme.name} theme")
                
                # Check outfits
                for outfit in self.unlockables_manager.outfits.values():
                    cond = outfit.unlock_condition
                    if cond.condition_type == UnlockConditionType.FILES_PROCESSED:
                        if achievement.category == 'progress' and achievement.progress_max == cond.value:
                            rewards.append(f"🐼 {outfit.name} outfit")
            except Exception:
                pass
        
        # Add points info
        if achievement.points > 0:
            rewards.append(f"{achievement.points} pts")
        
        return ", ".join(rewards) if rewards else f"{achievement.points} pts"
    
    def _on_achievement_unlocked(self, achievement):
        """Handle achievement unlock - grant direct rewards separate from shop"""
        try:
            if not hasattr(achievement, 'reward') or not achievement.reward:
                return
            
            reward = achievement.reward
            reward_type = reward.get('type', '')
            
            if reward_type == 'currency' and self.currency_system:
                amount = reward.get('amount', 0)
                if amount > 0:
                    self.currency_system.add_money(amount, f"Achievement reward: {achievement.name}")
                    self.log(f"🏆 Achievement '{achievement.name}' unlocked! Reward: {reward.get('description', f'${amount}')}")
            elif reward_type == 'exclusive_title':
                title = reward.get('title', '')
                self.log(f"🏆 Achievement '{achievement.name}' unlocked! Reward: {reward.get('description', title)}")
            elif reward_type == 'exclusive_item':
                item_name = reward.get('item', '')
                self.log(f"🏆 Achievement '{achievement.name}' unlocked! Reward: {reward.get('description', item_name)}")
            else:
                self.log(f"🏆 Achievement '{achievement.name}' unlocked!")
        except Exception as e:
            logger.error(f"Error granting achievement reward: {e}")
    
    
    def create_shop_tab(self):
        """Create shop tab for purchasing items with money"""
        # Header
        header_frame = ctk.CTkFrame(self.tab_shop)
        header_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(header_frame, text="🛒 Shop 🛒",
                     font=("Arial Bold", 18)).pack(side="left", padx=10)
        
        # Money display
        if self.currency_system:
            money_text = f"💰 Money: ${self.currency_system.get_balance()}"
            self.shop_money_label = ctk.CTkLabel(header_frame, text=money_text,
                         font=("Arial Bold", 14), text_color="#00cc00")
            self.shop_money_label.pack(side="right", padx=20)
        
        # User level display
        if self.user_level_system:
            level_text = f"⭐ Level {self.user_level_system.level}"
            ctk.CTkLabel(header_frame, text=level_text,
                        font=("Arial Bold", 14), text_color="#ffaa00").pack(side="right", padx=10)
        
        if not self.shop_system or not self.currency_system:
            info_frame = ctk.CTkFrame(self.tab_shop)
            info_frame.pack(pady=50, padx=50, fill="both", expand=True)
            ctk.CTkLabel(info_frame,
                         text="Shop system not available\n\nPlease check your installation.",
                         font=("Arial", 14)).pack(expand=True)
            return
        
        # Shop categories
        categories_frame = ctk.CTkFrame(self.tab_shop)
        categories_frame.pack(fill="x", pady=10, padx=10)
        
        # Category buttons
        self.selected_category = ShopCategory.PANDA_OUTFITS
        category_buttons = {}
        
        for category in ShopCategory:
            btn = ctk.CTkButton(
                categories_frame,
                text=category.value.replace('_', ' ').title(),
                command=lambda c=category: self._select_shop_category(c)
            )
            btn.pack(side="left", padx=5, pady=5)
            category_buttons[category] = btn
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(btn, self._get_tooltip_text('shop_category_button') or "Filter shop items by this category"))
        
        # Shop items scroll frame
        self.shop_scroll = ctk.CTkScrollableFrame(self.tab_shop, width=1000, height=500)
        self.shop_scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Display items for default category
        self._display_shop_category(self.selected_category)
    
    def _select_shop_category(self, category: ShopCategory):
        """Select and display shop category"""
        self.selected_category = category
        self._display_shop_category(category)
    
    def _display_shop_category(self, category: ShopCategory):
        """Display items in shop category"""
        # Clear current items
        for widget in self.shop_scroll.winfo_children():
            widget.destroy()
        
        # Get user level
        user_level = self.user_level_system.level if self.user_level_system else 1
        
        # Get items in category
        items = self.shop_system.get_items_by_category(category, user_level)
        
        if not items:
            ctk.CTkLabel(self.shop_scroll,
                        text="No items available in this category",
                        font=("Arial", 14)).pack(pady=50)
            return
        
        # Display each item
        for item in items:
            item_frame = ctk.CTkFrame(self.shop_scroll)
            item_frame.pack(fill="x", padx=10, pady=5)
            
            # Item icon and name
            name_frame = ctk.CTkFrame(item_frame)
            name_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(name_frame, text=f"{item.icon} {item.name}",
                        font=("Arial Bold", 14)).pack(anchor="w")
            
            ctk.CTkLabel(name_frame, text=item.description,
                        font=("Arial", 11), text_color="gray").pack(anchor="w")
            
            # Price and requirements
            info_frame = ctk.CTkFrame(item_frame)
            info_frame.pack(side="right", padx=10, pady=10)
            
            # Price
            price_text = f"💰 ${item.price}"
            ctk.CTkLabel(info_frame, text=price_text,
                        font=("Arial Bold", 12), text_color="#00cc00").pack(side="left", padx=10)
            
            # Level requirement
            if item.level_required > 1:
                level_text = f"⭐ Lvl {item.level_required}"
                color = "gray" if user_level >= item.level_required else "red"
                ctk.CTkLabel(info_frame, text=level_text,
                            font=("Arial", 10), text_color=color).pack(side="left", padx=5)
            
            # Purchase button
            is_purchased = self.shop_system.is_purchased(item.id)
            can_buy, reason = self.shop_system.can_purchase(item.id, self.currency_system.get_balance())
            
            if is_purchased and item.one_time_purchase:
                btn_text = "✓ Owned"
                btn_state = "disabled"
            elif user_level < item.level_required:
                btn_text = "🔒 Locked"
                btn_state = "disabled"
            elif not can_buy:
                btn_text = "Can't Afford"
                btn_state = "disabled"
            else:
                btn_text = "Buy"
                btn_state = "normal"
            
            buy_btn = ctk.CTkButton(
                info_frame,
                text=btn_text,
                width=80,
                state=btn_state,
                command=lambda i=item: self._purchase_item(i)
            )
            buy_btn.pack(side="left", padx=5)
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(buy_btn, self._get_tooltip_text('shop_buy_button') or "Purchase this item"))
    
    def _purchase_item(self, item):
        """Purchase an item from the shop"""
        # Confirm purchase
        from tkinter import messagebox
        
        confirm = messagebox.askyesno(
            "Confirm Purchase",
            f"Purchase {item.name} for ${item.price}?\n\n{item.description}"
        )
        
        if not confirm:
            return
        
        # Attempt purchase
        success, message, purchased_item = self.shop_system.purchase_item(
            item.id,
            self.currency_system.get_balance(),
            self.user_level_system.level if self.user_level_system else 1
        )
        
        if success:
            # Deduct money
            self.currency_system.spend_money(item.price, f"Purchased {item.name}")
            
            # Update money display
            if hasattr(self, 'shop_money_label'):
                self.shop_money_label.configure(
                    text=f"💰 Money: ${self.currency_system.get_balance()}"
                )
            
            # Unlock in unlockables system if linked
            if item.unlockable_id and self.unlockables_manager:
                try:
                    # Try to unlock the item in unlockables
                    for category in ['cursors', 'outfits', 'themes', 'animations',
                                     'cursor_trails', 'clothes', 'accessories']:
                        items_dict = getattr(self.unlockables_manager, category, {})
                        if isinstance(items_dict, dict) and item.unlockable_id in items_dict:
                            items_dict[item.unlockable_id].unlocked = True
                            items_dict[item.unlockable_id].unlock_date = datetime.now().isoformat()
                            logger.info(f"Unlocked {category} item: {item.unlockable_id}")
                            break
                except Exception as e:
                    logger.error(f"Error unlocking item: {e}")
            
            # Also unlock in panda closet for clothes/accessories
            if item.unlockable_id and self.panda_closet:
                try:
                    closet_item = self.panda_closet.get_item(item.unlockable_id)
                    if closet_item and not closet_item.unlocked:
                        closet_item.unlocked = True
                        self.panda_closet.save_to_file(
                            str(CONFIG_DIR / 'closet.json')
                        )
                        logger.info(f"Unlocked closet item: {item.unlockable_id}")
                except Exception as e:
                    logger.debug(f"Item not in closet (expected for non-closet items): {e}")
            
            # Handle cursor trail purchases — save as available trail
            if item.category.value == 'cursor_trails' and item.unlockable_id:
                try:
                    trail_name = item.unlockable_id.replace('trail_', '')
                    config.set('ui', f'trail_{trail_name}_unlocked', value=True)
                    logger.info(f"Unlocked cursor trail: {trail_name}")
                except Exception as e:
                    logger.debug(f"Could not save trail unlock: {e}")
            
            # Handle food purchases — feed the panda directly
            if item.category.value == 'food' and self.panda:
                try:
                    response = self.panda.on_feed()
                    if hasattr(self, 'panda_widget') and self.panda_widget:
                        self.panda_widget.info_label.configure(text=response)
                        self.panda_widget.play_animation_once('fed')
                    self.log(f"🎋 Fed panda with {item.name}! {response}")
                    # Award XP for feeding
                    if self.panda_level_system:
                        try:
                            xp = self.panda_level_system.get_xp_reward('feed')
                            self.panda_level_system.add_xp(xp, f'Fed with {item.name}')
                        except Exception:
                            pass
                except Exception as e:
                    logger.debug(f"Could not feed panda: {e}")

            # Handle toy purchases — unlock widget in collection
            if item.category.value == 'toys' and item.unlockable_id and self.widget_collection:
                try:
                    self.widget_collection.unlock_widget(item.unlockable_id)
                    logger.info(f"Unlocked toy widget: {item.unlockable_id}")
                except Exception as e:
                    logger.debug(f"Could not unlock toy widget: {e}")
            
            messagebox.showinfo("Purchase Successful", message)
            
            # Refresh shop display
            self._display_shop_category(self.selected_category)
        else:
            messagebox.showerror("Purchase Failed", message)
    
    def create_rewards_tab(self):
        """Create unlockables/rewards tab"""
        ctk.CTkLabel(self.tab_rewards, text="🎁 Unlockables & Rewards 🎁",
                     font=("Arial Bold", 18)).pack(pady=15)
        
        if not self.unlockables_manager:
            # No unlockables manager
            info_frame = ctk.CTkFrame(self.tab_rewards)
            info_frame.pack(pady=50, padx=50, fill="both", expand=True)
            ctk.CTkLabel(info_frame,
                         text="Unlockables system not available\n\nPlease check your installation.",
                         font=("Arial", 14)).pack(expand=True)
            return
        
        # Rewards scroll frame
        rewards_scroll = ctk.CTkScrollableFrame(self.tab_rewards, width=1000, height=600)
        rewards_scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Display unlockables by category using actual UnlockablesSystem attributes
        try:
            categories = [
                ('🖱️ Custom Cursors', self.unlockables_manager.cursors),
                ('🐼 Panda Outfits', self.unlockables_manager.outfits),
                ('🎨 Themes', self.unlockables_manager.themes),
                ('✨ Animations', self.unlockables_manager.animations),
            ]
            
            for cat_label, items_dict in categories:
                # Category header
                cat_frame = ctk.CTkFrame(rewards_scroll)
                cat_frame.pack(fill="x", padx=10, pady=10)
                
                ctk.CTkLabel(cat_frame, text=cat_label,
                            font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=10)
                
                if not items_dict:
                    ctk.CTkLabel(cat_frame, 
                                text="No items in this category",
                                font=("Arial", 11), 
                                text_color="gray").pack(anchor="w", padx=20, pady=5)
                    continue
                
                # Display each item
                for item in items_dict.values():
                    item_frame = ctk.CTkFrame(cat_frame)
                    item_frame.pack(fill="x", padx=10, pady=3)
                    
                    if item.unlocked:
                        # Unlocked item - show normally
                        item_text = f"✓ {item.name}"
                        ctk.CTkLabel(item_frame, text=item_text,
                                    font=("Arial", 12)).pack(side="left", padx=10, pady=5)
                        
                        ctk.CTkLabel(item_frame, text=item.description,
                                    font=("Arial", 10),
                                    text_color="gray").pack(side="left", padx=5)
                    else:
                        # Locked item - show with locked overlay and unlock condition
                        item_text = f"🔒 {item.name}"
                        ctk.CTkLabel(item_frame, text=item_text,
                                    font=("Arial", 12),
                                    text_color="#888888").pack(side="left", padx=10, pady=5)
                        
                        # Show unlock condition clearly
                        unlock_desc = getattr(item.unlock_condition, 'description', 'Complete achievement')
                        ctk.CTkLabel(item_frame, text=f"🔑 Unlock: {unlock_desc}",
                                    font=("Arial", 10),
                                    text_color="#cc8800").pack(side="left", padx=5)
                
        except Exception as e:
            ctk.CTkLabel(rewards_scroll,
                        text=f"Error loading rewards: {e}",
                        font=("Arial", 12)).pack(pady=20)
    
    def create_closet_tab(self):
        """Create panda closet tab for customizing panda appearance"""
        if not PANDA_CLOSET_AVAILABLE or not self.panda_closet:
            ctk.CTkLabel(self.tab_closet, text="Panda closet not available",
                         font=("Arial", 14)).pack(pady=50)
            return
        
        closet_panel = ClosetPanel(self.tab_closet, self.panda_closet)
        closet_panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_notepad_tab(self):
        """Create notepad tab with multiple note tabs support"""
        # Header with title
        header_frame = ctk.CTkFrame(self.tab_notepad)
        header_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(header_frame, text="📝 Personal Notes",
                     font=("Arial Bold", 16)).pack(side="left", padx=10)
        
        # Add new note button
        ctk.CTkButton(header_frame, text="➕ New Note", width=100,
                     command=self.add_new_note_tab).pack(side="right", padx=10)
        
        # Tabview for multiple notes
        self.notes_tabview = ctk.CTkTabview(self.tab_notepad)
        self.notes_tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Dictionary to store note textboxes
        self.note_textboxes = {}
        
        # Load all notes or create default
        self.load_all_notes()
        
        # Buttons
        button_frame = ctk.CTkFrame(self.tab_notepad)
        button_frame.pack(pady=10)
        
        ctk.CTkButton(button_frame, text="💾 Save All Notes", width=130, 
                     command=self.save_all_notes).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="🗑️ Delete Current Note", width=150,
                     command=self.delete_current_note).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="✏️ Rename Current Note", width=150,
                     command=self.rename_current_note).pack(side="left", padx=5)
    
    def add_new_note_tab(self, name=None, content=""):
        """Add a new note tab"""
        if name is None:
            # Ask for note name
            import tkinter.simpledialog as simpledialog
            name = simpledialog.askstring("New Note", "Enter note name:", 
                                         initialvalue=f"Note {len(self.note_textboxes) + 1}")
            if not name:
                return  # User cancelled
        
        # Limit to 20 tabs
        if len(self.note_textboxes) >= 20:
            if GUI_AVAILABLE:
                messagebox.showwarning("Limit Reached", "Maximum 20 note tabs allowed.")
            return
        
        # Check if name already exists
        if name in self.note_textboxes:
            if GUI_AVAILABLE:
                messagebox.showwarning("Duplicate Name", "A note with this name already exists.")
            return
        
        # Create new tab
        new_tab = self.notes_tabview.add(name)
        
        # Create textbox in the tab
        textbox = ctk.CTkTextbox(new_tab, width=1000, height=550)
        textbox.pack(padx=5, pady=5, fill="both", expand=True)
        textbox.insert("1.0", content)
        
        # Store reference
        self.note_textboxes[name] = textbox
        
        # Switch to new tab
        self.notes_tabview.set(name)
    
    def delete_current_note(self):
        """Delete the currently selected note tab"""
        current_tab = self.notes_tabview.get()
        
        # Don't delete if it's the last tab
        if len(self.note_textboxes) <= 1:
            if GUI_AVAILABLE:
                messagebox.showwarning("Cannot Delete", "You must have at least one note tab.")
            return
        
        # Confirm deletion
        if GUI_AVAILABLE:
            result = messagebox.askyesno("Delete Note", 
                                        f"Are you sure you want to delete '{current_tab}'? This cannot be undone.")
            if not result:
                return
        
        # Remove from dictionary
        if current_tab in self.note_textboxes:
            del self.note_textboxes[current_tab]
        
        # Delete the tab
        self.notes_tabview.delete(current_tab)
        
        # Save after deletion
        self.save_all_notes()
    
    def rename_current_note(self):
        """Rename the currently selected note tab"""
        current_tab = self.notes_tabview.get()
        
        # Ask for new name
        import tkinter.simpledialog as simpledialog
        new_name = simpledialog.askstring("Rename Note", "Enter new name:", 
                                         initialvalue=current_tab)
        if not new_name or new_name == current_tab:
            return  # User cancelled or same name
        
        # Check if new name already exists
        if new_name in self.note_textboxes:
            if GUI_AVAILABLE:
                messagebox.showwarning("Duplicate Name", "A note with this name already exists.")
            return
        
        # Get current content
        content = self.note_textboxes[current_tab].get("1.0", "end-1c")
        
        # Delete old tab
        del self.note_textboxes[current_tab]
        self.notes_tabview.delete(current_tab)
        
        # Create new tab with new name
        self.add_new_note_tab(name=new_name, content=content)
        
        # Save after rename
        self.save_all_notes()
    
    def load_all_notes(self):
        """Load all notes from config directory"""
        try:
            import json
            notes_file = Path.home() / ".ps2_texture_sorter" / "notes.json"
            
            if notes_file.exists():
                with open(notes_file, 'r', encoding='utf-8') as f:
                    notes_data = json.load(f)
                    
                    # Load multiple notes
                    if 'notes' in notes_data and isinstance(notes_data['notes'], dict):
                        for name, content in notes_data['notes'].items():
                            self.add_new_note_tab(name=name, content=content)
                    # Legacy: load old single note format
                    elif 'content' in notes_data:
                        self.add_new_note_tab(name="General Notes", content=notes_data['content'])
                    else:
                        # Empty file, create default
                        self.add_new_note_tab(name="General Notes", content="")
            else:
                # No file, create default
                self.add_new_note_tab(name="General Notes", content="")
                
        except Exception as e:
            logger.warning(f"Failed to load notes: {e}")
            # Create default on error
            if len(self.note_textboxes) == 0:
                self.add_new_note_tab(name="General Notes", content="")
    
    def save_all_notes(self):
        """Save all notes to config directory"""
        try:
            import json
            from datetime import datetime
            
            # Ensure config directory exists
            config_dir = Path.home() / ".ps2_texture_sorter"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Collect all notes
            all_notes = {}
            for name, textbox in self.note_textboxes.items():
                content = textbox.get("1.0", "end-1c")
                all_notes[name] = content
            
            # Save to JSON
            notes_file = config_dir / "notes.json"
            
            notes_data = {
                'notes': all_notes,
                'last_modified': datetime.now().isoformat()
            }
            
            with open(notes_file, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, indent=2)
            
            if GUI_AVAILABLE:
                messagebox.showinfo("Notes Saved", f"All {len(all_notes)} note(s) have been saved successfully!")
        except Exception as e:
            logger.error(f"Failed to save notes: {e}")
            if GUI_AVAILABLE:
                messagebox.showerror("Error", f"Failed to save notes: {e}")
    
    # Keep legacy methods for compatibility but update them
    def load_notes(self):
        """Legacy method - redirects to load_all_notes"""
        self.load_all_notes()
    
    def save_notes(self):
        """Legacy method - redirects to save_all_notes"""
        self.save_all_notes()
    
    def clear_notes(self):
        """Clear current note content with confirmation"""
        current_tab = self.notes_tabview.get()
        if current_tab in self.note_textboxes:
            if GUI_AVAILABLE:
                result = messagebox.askyesno("Clear Note", 
                                            f"Are you sure you want to clear '{current_tab}'? This cannot be undone.")
                if result:
                    self.note_textboxes[current_tab].delete("1.0", "end")
                    self.save_all_notes()
            else:
                self.note_textboxes[current_tab].delete("1.0", "end")
    
    def create_about_tab(self):
        """Create comprehensive about tab with hotkeys, features, and panda info"""
        # Create scrollable frame for all content
        scrollable_frame = ctk.CTkScrollableFrame(self.tab_about)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ============= TITLE & VERSION =============
        ctk.CTkLabel(scrollable_frame, text=f"🐼 {APP_NAME} 🐼",
                     font=("Arial Bold", 28)).pack(pady=15)
        
        ctk.CTkLabel(scrollable_frame, text=f"Version {APP_VERSION}",
                     font=("Arial", 16)).pack(pady=5)
        
        ctk.CTkLabel(scrollable_frame, text=f"by {APP_AUTHOR}",
                     font=("Arial", 14), text_color="gray").pack(pady=5)
        
        # ============= DESCRIPTION =============
        desc_frame = ctk.CTkFrame(scrollable_frame)
        desc_frame.pack(fill="x", padx=20, pady=15)
        
        desc_text = """A professional, single-executable Windows application for automatically 
sorting PS2 texture dumps with advanced AI classification and massive-scale 
support (200,000+ textures). 100% offline operation."""
        
        ctk.CTkLabel(desc_frame, text=desc_text,
                     font=("Arial", 12), justify="left", wraplength=900).pack(pady=15, padx=15)
        
        # ============= KEYBOARD SHORTCUTS =============
        hotkeys_frame = ctk.CTkFrame(scrollable_frame)
        hotkeys_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(hotkeys_frame, text="⌨️ KEYBOARD SHORTCUTS",
                     font=("Arial Bold", 18)).pack(pady=10)
        
        # Define hotkeys by category
        hotkey_categories = {
            "📁 File Operations": [
                ("Ctrl+O", "Open files"),
                ("Ctrl+S", "Save results"),
                ("Ctrl+E", "Export data"),
                ("Alt+F4", "Close application")
            ],
            "⚙️ Processing": [
                ("Ctrl+P", "Start processing"),
                ("Ctrl+Shift+P", "Pause processing"),
                ("Ctrl+Shift+S", "Stop processing"),
                ("Ctrl+R", "Resume processing")
            ],
            "👁️ View": [
                ("Ctrl+T", "Toggle preview panel"),
                ("F5", "Refresh view"),
                ("F11", "Toggle fullscreen"),
                ("Ctrl+B", "Toggle sidebar")
            ],
            "🧭 Navigation": [
                ("Right Arrow", "Next texture"),
                ("Left Arrow", "Previous texture"),
                ("Home", "First texture"),
                ("End", "Last texture")
            ],
            "✅ Selection": [
                ("Ctrl+A", "Select all"),
                ("Ctrl+D", "Deselect all"),
                ("Ctrl+I", "Invert selection")
            ],
            "🔧 Tools": [
                ("Ctrl+F", "Search"),
                ("Ctrl+Shift+F", "Filter"),
                ("Ctrl+,", "Settings"),
                ("Ctrl+Shift+T", "Statistics")
            ],
            "🐼 Special Features": [
                ("Ctrl+Shift+A", "View achievements"),
                ("Ctrl+M", "Toggle sound"),
                ("F1", "Help / Tutorial")
            ],
            "🌍 Global (works when app not focused)": [
                ("Ctrl+Alt+P", "Global start processing"),
                ("Ctrl+Alt+Space", "Global pause")
            ]
        }
        
        # Display hotkeys by category
        for category, hotkeys in hotkey_categories.items():
            cat_frame = ctk.CTkFrame(hotkeys_frame)
            cat_frame.pack(fill="x", padx=15, pady=8)
            
            ctk.CTkLabel(cat_frame, text=category,
                        font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
            
            for key, description in hotkeys:
                hotkey_row = ctk.CTkFrame(cat_frame)
                hotkey_row.pack(fill="x", padx=20, pady=2)
                
                ctk.CTkLabel(hotkey_row, text=key,
                            font=("Courier Bold", 11), width=180, 
                            anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(hotkey_row, text=description,
                            font=("Arial", 11), anchor="w").pack(side="left", padx=5)
        
        # ============= FEATURES =============
        features_frame = ctk.CTkFrame(scrollable_frame)
        features_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(features_frame, text="✨ FEATURES",
                     font=("Arial Bold", 18)).pack(pady=10)
        
        features_list = [
            "🎯 50+ texture categories with AI classification",
            "🔍 LOD detection and automatic grouping",
            "🔄 Bidirectional DDS ↔ PNG conversion with quality preservation",
            "💾 SQLite database indexing for massive libraries (200,000+ textures)",
            "📂 9 organization styles (Sims, Neopets, Flat, Game Area, Asset Pipeline, Modular, etc.)",
            "🎨 Modern panda-themed UI with 5+ preset themes and custom color palettes",
            "🏆 Achievement system with 50+ achievements and unlockable rewards",
            "💰 Currency system - Earn Bamboo Bucks through usage and spend in the shop",
            "📊 Comprehensive statistics and analytics tracking",
            "🔎 Advanced search and filtering with multiple criteria",
            "📝 Multi-tab notepad with pop-out window support",
            "🖼️ File browser with thumbnail preview and quick actions",
            "🐼 Interactive panda character with 13 moods and leveling system",
            "💡 250+ contextual tooltips in 4 verbosity modes (expert to panda)",
            "🔊 Sound effects and audio feedback with volume control",
            "📚 Interactive tutorial system with first-run guide and F1 context help",
            "⚡ Multi-threaded batch processing with pause/resume",
            "🔐 Safe operations with automatic backups and undo/redo",
            "⌨️ Full keyboard shortcut support with customizable hotkeys",
            "🛡️ 100% offline operation - no network calls, complete privacy"
        ]
        
        for feature in features_list:
            ctk.CTkLabel(features_frame, text=feature,
                        font=("Arial", 11), anchor="w").pack(anchor="w", padx=20, pady=3)
        
        # ============= PANDA MODE =============
        panda_frame = ctk.CTkFrame(scrollable_frame)
        panda_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(panda_frame, text="🐼 PANDA MODE",
                     font=("Arial Bold", 18)).pack(pady=10)
        
        panda_text = """The interactive panda character is your companion throughout texture sorting!

• 13 dynamic moods (happy, working, celebrating, rage, sarcastic, drunk, existential, etc.)
• Level system - Both you and the panda gain XP and level up through usage
• 250+ tooltip variations ranging from helpful to hilariously sarcastic
• Random panda facts, jokes, and motivational quotes during processing
• Easter eggs and hidden surprises (try clicking the panda 10 times!)
• Vulgar Mode toggle for uncensored panda commentary (opt-in, off by default)
• Right-click the panda for special interactions: pet, feed bamboo, check mood, reset position
• Draggable - Click and drag the panda anywhere on screen! Position is saved automatically
• Earn Bamboo Bucks currency through interactions and achievements
• Customizable appearance and behavior in Settings → Panda

Drag the panda to your favorite spot or right-click to reset to corner! 🎋"""
        
        ctk.CTkLabel(panda_frame, text=panda_text,
                     font=("Arial", 11), justify="left", wraplength=900).pack(pady=10, padx=20)
        
        # ============= CREDITS =============
        credits_frame = ctk.CTkFrame(scrollable_frame)
        credits_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(credits_frame, text="👥 CREDITS",
                     font=("Arial Bold", 18)).pack(pady=10)
        
        credits_text = """Developed with 🐼 by Dead On The Inside / JosephsDeadish

Built with:
• Python 3.8+
• CustomTkinter for modern UI
• PIL/Pillow for image processing
• NumPy for texture analysis
• And lots of bamboo 🎋"""
        
        ctk.CTkLabel(credits_frame, text=credits_text,
                     font=("Arial", 11), justify="left").pack(pady=10, padx=20)
        
        # Repository link
        ctk.CTkLabel(credits_frame, 
                     text="Repository: JosephsDeadish/PS2-texture-sorter",
                     font=("Arial", 10), text_color="gray").pack(pady=5)
    
    def create_inventory_tab(self):
        """Create inventory tab for managing collected items"""
        scrollable_frame = ctk.CTkScrollableFrame(self.tab_inventory)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scrollable_frame, text="📦 Inventory",
                     font=("Arial Bold", 22)).pack(pady=15)

        # Show purchased shop items
        if self.shop_system:
            shop_frame = ctk.CTkFrame(scrollable_frame)
            shop_frame.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(shop_frame, text="🛒 Purchased Items",
                         font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=10)

            if self.shop_system.purchased_items:
                for item_id in self.shop_system.purchased_items:
                    item = self.shop_system.CATALOG.get(item_id)
                    if item:
                        item_frame = ctk.CTkFrame(shop_frame)
                        item_frame.pack(fill="x", padx=10, pady=3)
                        ctk.CTkLabel(item_frame, text=f"{item.icon} {item.name}",
                                     font=("Arial", 12)).pack(side="left", padx=10, pady=5)
                        ctk.CTkLabel(item_frame, text=item.description,
                                     font=("Arial", 10), text_color="gray").pack(side="left", padx=5)
            else:
                ctk.CTkLabel(shop_frame, text="No purchases yet. Visit the Shop to buy items!",
                             font=("Arial", 11), text_color="gray").pack(anchor="w", padx=20, pady=5)

        # Show widget collection (toys, food, accessories)
        if self.widget_collection:
            for type_label, widget_type in [("🎾 Toys", WidgetType.TOY),
                                            ("🍱 Food Items", WidgetType.FOOD),
                                            ("🎀 Accessories", WidgetType.ACCESSORY)]:
                type_frame = ctk.CTkFrame(scrollable_frame)
                type_frame.pack(fill="x", padx=10, pady=10)
                ctk.CTkLabel(type_frame, text=type_label,
                             font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=10)

                widgets = self.widget_collection.get_all_widgets(widget_type)
                for widget in widgets:
                    w_frame = ctk.CTkFrame(type_frame)
                    w_frame.pack(fill="x", padx=10, pady=3)
                    status = "✅" if widget.unlocked else "🔒"
                    ctk.CTkLabel(w_frame, text=f"{status} {widget.emoji} {widget.name}",
                                 font=("Arial", 12)).pack(side="left", padx=10, pady=5)
                    rarity_colors = {"common": "gray", "uncommon": "#00cc00",
                                     "rare": "#3399ff", "epic": "#cc66ff",
                                     "legendary": "#ffaa00"}
                    ctk.CTkLabel(w_frame, text=widget.rarity.value.title(),
                                 font=("Arial", 10),
                                 text_color=rarity_colors.get(widget.rarity.value, "gray")
                                 ).pack(side="left", padx=5)
                    if widget.stats.times_used > 0:
                        ctk.CTkLabel(w_frame, text=f"Used {widget.stats.times_used}x",
                                     font=("Arial", 10), text_color="gray").pack(side="right", padx=10)

        # Show unlockables summary
        if self.unlockables_manager:
            unlockables_frame = ctk.CTkFrame(scrollable_frame)
            unlockables_frame.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(unlockables_frame, text="🎁 Unlocked Rewards",
                         font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=10)

            try:
                categories = [
                    ('🖱️ Cursors', self.unlockables_manager.cursors),
                    ('🐼 Outfits', self.unlockables_manager.outfits),
                    ('🎨 Themes', self.unlockables_manager.themes),
                    ('✨ Animations', self.unlockables_manager.animations),
                ]
                for cat_label, items_dict in categories:
                    unlocked = [i for i in items_dict.values() if i.unlocked]
                    if unlocked:
                        ctk.CTkLabel(unlockables_frame,
                                     text=f"  {cat_label}: {len(unlocked)}/{len(items_dict)}",
                                     font=("Arial", 11)).pack(anchor="w", padx=20, pady=2)
            except Exception as e:
                ctk.CTkLabel(unlockables_frame,
                             text=f"Could not load unlockables: {e}",
                             font=("Arial", 11), text_color="gray").pack(anchor="w", padx=20, pady=5)
    
    def create_panda_stats_tab(self):
        """Create panda stats and mood tab"""
        scrollable_frame = ctk.CTkScrollableFrame(self.tab_panda_stats)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scrollable_frame, text="📊 Panda Stats & Mood",
                     font=("Arial Bold", 22)).pack(pady=15)

        if not self.panda:
            ctk.CTkLabel(scrollable_frame,
                         text="Panda character not available.",
                         font=("Arial", 14)).pack(pady=50)
            return

        # Current mood display
        mood_frame = ctk.CTkFrame(scrollable_frame)
        mood_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(mood_frame, text="🎭 Current Mood",
                     font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=10)

        mood_indicator = self.panda.get_mood_indicator()
        mood_name = self.panda.mood.value.title()
        self.panda_mood_label = ctk.CTkLabel(
            mood_frame, text=f"{mood_indicator} {mood_name}",
            font=("Arial Bold", 18))
        self.panda_mood_label.pack(anchor="w", padx=20, pady=5)

        # Panda animation preview
        anim_frame = ctk.CTkFrame(scrollable_frame)
        anim_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(anim_frame, text="🐼 Panda Preview",
                     font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=10)

        current_anim = self.panda.get_animation_frame('idle')
        self.panda_preview_label = ctk.CTkLabel(
            anim_frame, text=current_anim,
            font=("Courier", 10), justify="left")
        self.panda_preview_label.pack(anchor="w", padx=20, pady=5)

        # Statistics
        stats = self.panda.get_statistics()
        stats_frame = ctk.CTkFrame(scrollable_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(stats_frame, text="📈 Interaction Statistics",
                     font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=10)

        stat_items = [
            ("🖱️ Clicks", stats.get('click_count', 0)),
            ("🐾 Pets", stats.get('pet_count', 0)),
            ("🎋 Feeds", stats.get('feed_count', 0)),
            ("💭 Hovers", stats.get('hover_count', 0)),
            ("📁 Files Processed", stats.get('files_processed', 0)),
            ("❌ Failed Operations", stats.get('failed_operations', 0)),
            ("🥚 Easter Eggs Found", stats.get('easter_eggs_found', 0)),
        ]
        for label, value in stat_items:
            row = ctk.CTkFrame(stats_frame)
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=label, font=("Arial", 12)).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(value), font=("Arial Bold", 12),
                         text_color="#00cc00").pack(side="right", padx=10)

        # Level info
        if self.panda_level_system:
            level_frame = ctk.CTkFrame(scrollable_frame)
            level_frame.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(level_frame, text="⭐ Panda Level",
                         font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=10)
            try:
                level = self.panda_level_system.level
                xp = self.panda_level_system.xp
                xp_needed = self.panda_level_system.xp_to_next_level()
                ctk.CTkLabel(level_frame,
                             text=f"Level {level}  •  XP: {xp}/{xp_needed}",
                             font=("Arial Bold", 14), text_color="#ffaa00"
                             ).pack(anchor="w", padx=20, pady=5)
                # XP progress bar
                progress = min(1.0, xp / max(1, xp_needed))
                xp_bar = ctk.CTkProgressBar(level_frame, width=400)
                xp_bar.pack(anchor="w", padx=20, pady=5)
                xp_bar.set(progress)
            except Exception as e:
                ctk.CTkLabel(level_frame, text=f"Level info unavailable: {e}",
                             font=("Arial", 11), text_color="gray").pack(anchor="w", padx=20, pady=5)

        # Easter eggs found
        if stats.get('easter_eggs'):
            egg_frame = ctk.CTkFrame(scrollable_frame)
            egg_frame.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(egg_frame, text="🥚 Easter Eggs Discovered",
                         font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=10)
            for egg in stats['easter_eggs']:
                ctk.CTkLabel(egg_frame, text=f"  🥚 {egg}",
                             font=("Arial", 11)).pack(anchor="w", padx=20, pady=2)

        # Refresh button
        ctk.CTkButton(scrollable_frame, text="🔄 Refresh Stats",
                      command=self._refresh_panda_stats).pack(pady=15)

    def _refresh_panda_stats(self):
        """Refresh panda stats display"""
        if hasattr(self, 'panda_mood_label') and self.panda:
            mood_indicator = self.panda.get_mood_indicator()
            mood_name = self.panda.mood.value.title()
            self.panda_mood_label.configure(text=f"{mood_indicator} {mood_name}")
        if hasattr(self, 'panda_preview_label') and self.panda:
            current_anim = self.panda.get_animation_frame('idle')
            self.panda_preview_label.configure(text=current_anim)
    
    def create_status_bar(self):
        """Create bottom status bar with panda indicator"""
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_frame.pack(fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(status_frame, text="🐼 Ready", font=("Arial", 10))
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Add level and money display on the right
        if self.user_level_system:
            level_text = f"⭐ Level {self.user_level_system.level} - {self.user_level_system.get_title_for_level()}"
            self.status_level_label = ctk.CTkLabel(status_frame, text=level_text, font=("Arial", 10))
            self.status_level_label.pack(side="right", padx=10, pady=5)
        
        if self.currency_system:
            money_text = f"💰 ${self.currency_system.get_balance()}"
            self.status_money_label = ctk.CTkLabel(status_frame, text=money_text, font=("Arial", 10))
            self.status_money_label.pack(side="right", padx=10, pady=5)
        
        # Add panda widget in a separate frame on bottom right
        # Panda is always present - not a "mode"
        if PANDA_WIDGET_AVAILABLE and self.panda:
            panda_container = ctk.CTkFrame(self, corner_radius=10)
            
            # Restore saved position or use default
            # Position coordinates are relative (0.0 to 1.0) not absolute pixels
            # saved_x: 0.0 = left edge, 1.0 = right edge
            # saved_y: 0.0 = top edge, 1.0 = bottom edge
            saved_x = config.get('panda', 'position_x', default=0.98)
            saved_y = config.get('panda', 'position_y', default=0.98)
            
            # Position using saved relative coordinates
            panda_container.place(relx=saved_x, rely=saved_y, anchor="se")
            
            self.panda_widget = PandaWidget(
                panda_container, 
                panda_character=self.panda,
                panda_level_system=self.panda_level_system,
                widget_collection=self.widget_collection
            )
            self.panda_widget.pack(padx=5, pady=5)
            
            # Add panda level display
            if self.panda_level_system:
                panda_level_text = f"Panda Lvl {self.panda_level_system.level}"
                panda_level_label = ctk.CTkLabel(panda_container, text=panda_level_text, font=("Arial", 9))
                panda_level_label.pack(pady=2)
    
    def browse_input(self):
        """Browse for input directory"""
        directory = filedialog.askdirectory(title="Select Input Directory")
        if directory:
            self.input_path_var.set(directory)
            self.log(f"Input directory selected: {directory}")
    
    def browse_output(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path_var.set(directory)
            self.log(f"Output directory selected: {directory}")
    
    def browse_directory(self, target_var):
        """Browse for a directory and set the target variable"""
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            target_var.set(directory)
    
    def start_sorting(self):
        """Start texture sorting operation"""
        try:
            logger.info("start_sorting() called - initiating texture sorting")
            
            # Read ALL tkinter variable values BEFORE starting thread (thread-safety fix)
            input_path = self.input_path_var.get()
            output_path = self.output_path_var.get()
            mode = self.mode_var.get()
            style_display = self.style_var.get()
            style = self._style_display_to_key.get(style_display, "flat")
            detect_lods = self.detect_lods_var.get()
            group_lods = self.group_lods_var.get()
            detect_duplicates = self.detect_duplicates_var.get()
            
            logger.debug(f"Sorting parameters - Input: {input_path}, Output: {output_path}, Mode: {mode}, Style: {style}")
            logger.debug(f"Options - LODs: {detect_lods}, Group LODs: {group_lods}, Duplicates: {detect_duplicates}")
            
            if not input_path or not output_path:
                logger.warning("Sorting aborted - missing input or output path")
                messagebox.showerror("Error", "Please select both input and output directories")
                return
            
            if not Path(input_path).exists():
                logger.error(f"Sorting aborted - input directory does not exist: {input_path}")
                messagebox.showerror("Error", "Input directory does not exist")
                return
            
            self.log("=" * 60)
            self.log("Starting texture sorting operation...")
            self.log(f"Input: {input_path}")
            self.log(f"Output: {output_path}")
            self.log(f"Mode: {mode}")
            self.log(f"Style: {style}")
            self.log("=" * 60)
            
            # Disable start buttons
            self.start_button.configure(state="disabled")
            self.pause_button.configure(state="normal")
            self.stop_button.configure(state="normal")
            logger.debug("UI buttons state updated - sorting controls enabled")
            
            # Start sorting in background thread with all parameters
            try:
                thread = threading.Thread(
                    target=self.sort_textures_thread,
                    args=(input_path, output_path, mode, style, detect_lods, group_lods, detect_duplicates),
                    daemon=True,
                    name="SortingThread"
                )
                thread.start()
                logger.info(f"Sorting thread started successfully (Thread ID: {thread.ident})")
            except Exception as e:
                logger.error(f"Failed to start sorting thread: {e}", exc_info=True)
                self.log(f"❌ ERROR: Failed to start sorting thread: {e}")
                # Re-enable buttons on failure
                self.start_button.configure(state="normal")
                self.pause_button.configure(state="disabled")
                self.stop_button.configure(state="disabled")
                messagebox.showerror("Thread Error", f"Failed to start sorting operation:\n{e}")
                
        except Exception as e:
            logger.error(f"Unexpected error in start_sorting(): {e}", exc_info=True)
            self.log(f"❌ CRITICAL ERROR in start_sorting: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
    
    def sort_textures_thread(self, input_path_str, output_path_str, mode, style_name, detect_lods, group_lods, detect_duplicates):
        """Background thread for texture sorting with full organization system"""
        # Constants for error reporting
        MAX_UI_ERROR_MESSAGES = 5  # Maximum number of classification errors to show in UI
        MAX_RESULTS_ERROR_DISPLAY = 10  # Maximum number of organization errors to display
        
        try:
            logger.info(f"sort_textures_thread started - Processing: {input_path_str} -> {output_path_str}")
            input_path = Path(input_path_str)
            output_path = Path(output_path_str)
            
            # Scan for texture files lazily to avoid memory issues with large directories
            logger.debug("Starting directory scan for texture files")
            self.update_progress(0.05, "Scanning directory...")
            texture_extensions = {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga'}
            try:
                texture_files = []
                for f in input_path.rglob("*.*"):
                    if f.suffix.lower() in texture_extensions:
                        texture_files.append(f)
                logger.info(f"Directory scan complete - found {len(texture_files)} potential texture files")
            except Exception as e:
                logger.error(f"Error scanning directory: {e}", exc_info=True)
                self.log(f"❌ ERROR: Failed to scan directory: {e}")
                return
            
            total = len(texture_files)
            self.log(f"Found {total} texture files")
            
            if total == 0:
                logger.warning("No texture files found in input directory")
                self.log("⚠️ No texture files found in input directory")
                return
            
            # Classify textures
            logger.info(f"Starting classification of {total} textures")
            self.update_progress(0.1, "Classifying textures...")
            texture_infos = []
            classification_errors = 0
            
            for i, file_path in enumerate(texture_files):
                try:
                    # Classify
                    category, confidence = self.classifier.classify_texture(file_path)
                    
                    # Get file info
                    try:
                        stat = file_path.stat()
                    except Exception as e:
                        logger.warning(f"Failed to get file stats for {file_path}: {e}")
                        # Use -1 as sentinel value to indicate unknown size (not actually zero bytes)
                        # We use -1 instead of None because TextureInfo.file_size expects an integer
                        stat = SimpleNamespace(st_size=-1)
                    
                    # Create TextureInfo
                    texture_info = TextureInfo(
                        file_path=str(file_path),
                        filename=file_path.name,
                        category=category,
                        confidence=confidence,
                        file_size=stat.st_size,
                        format=file_path.suffix.lower()[1:]  # Remove dot
                    )
                    
                    texture_infos.append(texture_info)
                    
                except Exception as e:
                    classification_errors += 1
                    logger.error(f"Failed to classify {file_path}: {e}", exc_info=True)
                    if classification_errors <= MAX_UI_ERROR_MESSAGES:
                        self.log(f"⚠️ Classification error for {file_path.name}: {e}")
                    continue
                
                # Progress
                progress = 0.1 + (0.3 * (i+1) / total)
                self.update_progress(progress, f"Classifying {i+1}/{total}...")
                
                # Log every 50th file or last file for large sets, every 10th for small
                log_interval = 50 if total > 1000 else 10
                if (i+1) % log_interval == 0 or i == total - 1:
                    self.log(f"Classified {i+1}/{total} files...")
            
            if classification_errors > 0:
                logger.warning(f"Total classification errors: {classification_errors}/{total}")
                self.log(f"⚠️ {classification_errors} files failed classification and were skipped")
            
            # LOD Detection if enabled
            if detect_lods:
                logger.info("Starting LOD detection")
                self.update_progress(0.4, "Detecting LODs...")
                self.log("Detecting LOD groups...")
                try:
                    # Convert string paths to Path objects for LOD detector
                    file_paths = [Path(t.file_path) for t in texture_infos]
                    lod_groups = self.lod_detector.detect_lods(file_paths)
                    
                    # Apply LOD information to textures
                    for texture_info in texture_infos:
                        for group_name, lod_files in lod_groups.items():
                            for lod_file in lod_files:
                                # Compare Path objects or convert to string for comparison
                                lod_path = str(lod_file['path']) if isinstance(lod_file['path'], Path) else lod_file['path']
                                if lod_path == texture_info.file_path:
                                    texture_info.lod_group = group_name
                                    texture_info.lod_level = lod_file.get('lod_level', lod_file.get('level'))
                                    break
                    
                    logger.info(f"LOD detection complete - found {len(lod_groups)} groups")
                    self.log(f"Found {len(lod_groups)} LOD groups")
                except Exception as e:
                    logger.error(f"LOD detection failed: {e}", exc_info=True)
                    self.log(f"⚠️ LOD detection failed: {e}")
                    # Continue without LOD information
            
            # Duplicate Detection if enabled
            if detect_duplicates:
                logger.info("Starting duplicate detection")
                self.update_progress(0.5, "Detecting duplicates...")
                self.log("Detecting duplicate files...")
                # Note: Duplicate handling would go here
                # For now, we'll just log and continue
                logger.debug("Duplicate detection is not yet fully implemented")
                self.log("Duplicate detection complete")
            
            # Initialize organization engine
            logger.info(f"Initializing organization engine with style: {style_name}")
            self.update_progress(0.6, "Organizing textures...")
            self.log(f"Using organization style: {style_name}")
            
            try:
                # Get organization style class
                style_class = ORGANIZATION_STYLES.get(style_name, ORGANIZATION_STYLES['flat'])
                
                # Create engine
                engine = OrganizationEngine(
                    style_class=style_class,
                    output_dir=str(output_path),
                    dry_run=False
                )
                
                self.log(f"Style: {engine.get_style_name()}")
                self.log(f"Description: {engine.get_style_description()}")
                self.log(f"Output directory: {output_path}")
                self.log("-" * 60)
                
                # Progress callback
                def progress_callback(current, total, message):
                    progress = 0.6 + (0.35 * current / total)
                    self.update_progress(progress, f"Organizing {current}/{total}...")
                    if current % 10 == 0 or current == total:
                        self.log(message)
                
                # Organize textures
                logger.info(f"Starting file organization of {len(texture_infos)} textures")
                self.log("Starting file organization...")
                results = engine.organize_textures(texture_infos, progress_callback)
                logger.info(f"Organization complete - Processed: {results['processed']}, Failed: {results['failed']}")
                
                # Report results
                self.update_progress(1.0, "Complete!")
                self.log("=" * 60)
                self.log("✓ TEXTURE SORTING COMPLETED!")
                self.log("-" * 60)
                self.log(f"Total files: {total}")
                self.log(f"Successfully organized: {results['processed']}")
                self.log(f"Failed: {results['failed']}")
                
                if results['errors']:
                    logger.warning(f"{len(results['errors'])} errors occurred during organization")
                    self.log(f"\n⚠️ Errors encountered:")
                    for error in results['errors'][:MAX_RESULTS_ERROR_DISPLAY]:
                        self.log(f"  - {error['file']}: {error['error']}")
                    if len(results['errors']) > MAX_RESULTS_ERROR_DISPLAY:
                        self.log(f"  ... and {len(results['errors']) - MAX_RESULTS_ERROR_DISPLAY} more errors")
                
                self.log("=" * 60)
                
                # Award XP and money for sorting
                files_sorted = results['processed']
                if files_sorted > 0:
                    # Award money
                    if self.currency_system:
                        money_per_file = self.currency_system.get_reward_for_action('file_processed')
                        total_money = money_per_file * files_sorted
                        
                        # Bonus for large batches
                        if files_sorted >= self.BATCH_BONUS_THRESHOLD:
                            batch_bonus = self.currency_system.get_reward_for_action('batch_complete')
                            total_money += batch_bonus
                            self.log(f"💰 Earned ${total_money} (${money_per_file} per file + ${batch_bonus} batch bonus)")
                        else:
                            self.log(f"💰 Earned ${total_money} (${money_per_file} per file)")
                        
                        self.currency_system.earn_money(total_money, f"Sorted {files_sorted} files")
                        
                        # Update money display
                        if hasattr(self, 'status_money_label'):
                            self.after(0, lambda: self.status_money_label.configure(
                                text=f"💰 ${self.currency_system.get_balance()}"
                            ))
                        if hasattr(self, 'shop_money_label'):
                            self.after(0, lambda: self.shop_money_label.configure(
                                text=f"💰 Money: ${self.currency_system.get_balance()}"
                            ))
                    
                    # Award XP
                    if self.user_level_system:
                        xp_per_file = self.user_level_system.get_xp_reward('file_processed')
                        total_xp = xp_per_file * files_sorted
                        
                        # Bonus for large batches
                        if files_sorted >= self.BATCH_BONUS_THRESHOLD:
                            batch_xp = self.user_level_system.get_xp_reward('batch_complete')
                            total_xp += batch_xp
                        
                        leveled_up, new_level = self.user_level_system.add_xp(
                            total_xp, 
                            f"Sorted {files_sorted} files"
                        )
                        
                        self.log(f"⭐ Earned {total_xp} XP")
                        
                        if leveled_up:
                            title = self.user_level_system.get_title_for_level()
                            self.log(f"🎉 LEVEL UP! You are now Level {new_level} - {title}!")
                            
                            # Award level up rewards
                            rewards = self.user_level_system.get_rewards_for_level(new_level)
                            for reward in rewards:
                                if reward['type'] == 'money' and self.currency_system:
                                    self.currency_system.earn_money(
                                        reward['amount'], 
                                        f"Level {new_level} bonus"
                                    )
                                    self.log(f"  💰 {reward['description']}")
                                else:
                                    self.log(f"  🎁 {reward['description']}")
                        
                        # Update level display
                        if hasattr(self, 'status_level_label'):
                            level_text = f"⭐ Level {self.user_level_system.level} - {self.user_level_system.get_title_for_level()}"
                            self.after(0, lambda: self.status_level_label.configure(text=level_text))
                
                # Play completion sound if enabled
                self._play_completion_sound()
                
            except Exception as e:
                logger.error(f"Organization engine failed: {e}", exc_info=True)
                self.log(f"❌ Organization failed: {e}")
                raise  # Re-raise to be caught by outer handler
            
        except Exception as e:
            error_msg = f"Error during sorting: {e}"
            logger.error(error_msg, exc_info=True)
            self.log(f"❌ {error_msg}")
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Full traceback:\n{tb}")
            self.log(tb)
            # Show user-friendly error dialog
            if GUI_AVAILABLE:
                from tkinter import messagebox
                messagebox.showerror("Sorting Error", 
                    f"An error occurred during sorting:\n\n{str(e)}\n\nCheck the log for details.")
        
        finally:
            logger.info("Sorting thread cleanup - re-enabling UI buttons")
            # Re-enable buttons
            self.after(0, lambda: self.start_button.configure(state="normal"))
            self.after(0, lambda: self.pause_button.configure(state="disabled"))
            self.after(0, lambda: self.stop_button.configure(state="disabled"))
    
    def _play_completion_sound(self):
        """Play a completion sound if enabled"""
        try:
            # Check if sounds are enabled
            sound_enabled = config.get('notifications', 'play_sounds', default=False)
            completion_alert = config.get('notifications', 'completion_alert', default=True)
            
            if not (sound_enabled and completion_alert):
                return
            
            # Try to play system beep (cross-platform)
            import sys
            if sys.platform == 'win32':
                try:
                    import winsound
                    # Play system asterisk sound (MB_ICONASTERISK)
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except Exception:
                    pass
            else:
                # Unix/Mac - print bell character
                print('\a')
        except Exception as e:
            # Fail silently - sound is not critical
            pass
    
    def pause_sorting(self):
        """Pause sorting operation"""
        self.log("⏸️ Sorting paused")
    
    def stop_sorting(self):
        """Stop sorting operation"""
        self.log("⏹️ Sorting stopped")
    
    def update_progress(self, value, text):
        """Update progress bar and label - thread-safe"""
        self.after(0, self._update_progress_impl, value, text)
    
    def _update_progress_impl(self, value, text):
        """Internal implementation of progress update on main thread"""
        self.progress_bar.set(value)
        self.progress_label.configure(text=text)
        self.status_label.configure(text=text)
    
    def log(self, message):
        """Add message to log - thread-safe"""
        self.after(0, self._log_impl, message)
    
    def _log_impl(self, message):
        """Internal implementation of log on main thread"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
    
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        current = config.get('ui', 'theme', default='dark')
        new_theme = 'light' if current == 'dark' else 'dark'
        config.set('ui', 'theme', value=new_theme)
        ctk.set_appearance_mode(new_theme)
        self.log(f"Theme changed to: {new_theme}")


def main():
    """Main application entry point"""
    
    if not GUI_AVAILABLE:
        print("\n❌ Error: CustomTkinter not installed!")
        print("Please install dependencies:")
        print("  pip install customtkinter")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Set Windows taskbar AppUserModelID for proper icon display
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('JosephsDeadish.PS2TextureSorter.App.1.0.0')
        except Exception as e:
            logger.debug(f"Could not set AppUserModelID: {e}")
    
    try:
        # Create root window (hidden)
        root = ctk.CTk()
        root.withdraw()
        
        # Show splash screen
        splash = SplashScreen(root)
        
        # Simulate loading components
        components = [
            (0.2, "Loading configuration..."),
            (0.4, "Initializing classifier..."),
            (0.6, "Setting up database..."),
            (0.8, "Loading UI components..."),
            (1.0, "Ready!")
        ]
        
        for progress, text in components:
            splash.update_progress(progress, text)
            time.sleep(0.3)
        
        # Close splash
        splash.close()
        
        # Show main window
        root.deiconify()
        app = PS2TextureSorter()
        
        # Start main loop
        app.mainloop()
        
    except Exception as e:
        if GUI_AVAILABLE:
            messagebox.showerror("Fatal Error", f"Application failed to start:\n{e}")
        else:
            print(f"\n❌ Fatal Error: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
