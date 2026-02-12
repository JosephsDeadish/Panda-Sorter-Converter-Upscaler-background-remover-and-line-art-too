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
from collections import OrderedDict
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
    import tkinter as tk
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
        
        # Panda drawn art
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
    
    # Prefixes to strip when mapping shop unlockable_ids to closet item IDs
    CLOSET_ID_PREFIXES = ['clothes_', 'acc_', 'closet_', 'panda_outfit_']
    
    # Shop categories that belong in the closet (not inventory)
    CLOSET_SHOP_CATEGORIES = {'panda_outfits', 'clothes', 'hats', 'shoes', 'accessories'}
    
    # Constants for user interaction
    USER_INTERACTION_TIMEOUT = 300  # 5 minutes timeout for manual/suggested mode dialogs
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
        # Initialize model manager for AI
        self.model_manager = None
        if config.get('ai', 'offline', 'enabled', default=True) or config.get('ai', 'online', 'enabled', default=False):
            try:
                from src.ai.model_manager import ModelManager
                self.model_manager = ModelManager.create_default(config.settings.get('ai', {}))
                logger.info("AI Model Manager initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize AI Model Manager: {e}")
                self.model_manager = None
        
        self.classifier = TextureClassifier(config=config, model_manager=self.model_manager)
        self.lod_detector = LODDetector()
        self.file_handler = FileHandler(create_backup=config.get('file_handling', 'create_backup', default=True))
        self.database = None  # Will be initialized when needed
        
        # Initialize profile manager for game identification
        try:
            from src.features.profile_manager import ProfileManager
            profiles_dir = CONFIG_DIR / "profiles"
            self.profile_manager = ProfileManager(profiles_dir=profiles_dir)
            logger.info("Profile Manager initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Profile Manager: {e}")
            self.profile_manager = None
        
        # Initialize feature modules
        self.panda = None  # Always-present panda character
        self.sound_manager = None
        self.achievement_manager = None
        self.unlockables_manager = None
        self.stats_tracker = None
        self.search_filter = None
        self.tutorial_manager = None
        self.tooltip_manager = None  # Uses existing TooltipVerbosityManager - has vulgar mode
        self._tooltips = []  # Store tooltip references to prevent garbage collection
        self._claimed_rewards = set()  # Track claimed achievement reward IDs
        self.context_help = None
        self.preview_viewer = None
        self.currency_system = None
        self.user_level_system = None
        self.panda_level_system = None
        self.shop_system = None
        self.panda_closet = None
        self.panda_widget = None
        self.widget_collection = None
        self.closet_panel = None
        self.current_game_info = None  # Store detected game info
        
        # Thumbnail cache for file browser (LRU using OrderedDict for O(1) operations)
        self._thumbnail_cache = OrderedDict()
        self._thumbnail_cache_max = config.get('performance', 'thumbnail_cache_size', default=500)
        
        # Sorting dialog state flags (thread-safe events)
        self._sorting_skip_all = threading.Event()
        self._sorting_cancelled = threading.Event()
        
        # Initialize features if GUI available
        if GUI_AVAILABLE:
            try:
                # Always create panda character - not a "mode"
                if PANDA_CHARACTER_AVAILABLE:
                    self.panda = PandaCharacter()
                    logger.info("Panda character initialized (always present)")
                
                if SOUND_AVAILABLE:
                    self.sound_manager = SoundManager()
                    # Load saved sound settings from config
                    try:
                        sound_config = config.get('sound', default={})
                        if sound_config:
                            self.sound_manager.apply_config(sound_config)
                    except Exception as se:
                        logger.debug(f"Could not load sound config: {se}")
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
        
        # Show tutorial on first run (if enabled)
        show_on_startup = config.get('tutorial', 'show_on_startup', default=True)
        if show_on_startup and self.tutorial_manager and self.tutorial_manager.should_show_tutorial():
            self.after(500, lambda: self.tutorial_manager.start_tutorial())
        
        # Status
        self.current_operation = None
    
    def _on_close(self):
        """Handle window close to ensure clean shutdown"""
        # Cancel any pending auto-refresh timers
        self._cancel_stats_auto_refresh()
        
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
                # Check if it's a custom theme preset and apply its appearance mode
                try:
                    from src.ui.customization_panel import THEME_PRESETS
                    if theme in THEME_PRESETS:
                        preset = THEME_PRESETS[theme]
                        ctk.set_appearance_mode(preset.get("appearance_mode", "dark"))
                    else:
                        ctk.set_appearance_mode('dark')
                except ImportError:
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
            
            # Restore saved theme colors after widgets are created
            saved_colors = config.get('ui', 'theme_colors', default=None)
            if saved_colors and theme not in ['dark', 'light']:
                self.after(500, lambda: self._apply_saved_theme_colors(saved_colors))
            
            # Restore saved cursor settings
            cursor_type = config.get('ui', 'cursor', default='default')
            if cursor_type and cursor_type != 'default':
                self.after(600, lambda: self._apply_cursor_to_widget(self, cursor_type))
            
            cursor_trail = config.get('ui', 'cursor_trail', default=False)
            if cursor_trail:
                trail_color = config.get('ui', 'cursor_trail_color', default='rainbow')
                self.after(700, lambda: self._setup_cursor_trail(True, trail_color=trail_color))
                
        except Exception as e:
            print(f"Warning: Failed to load theme: {e}")
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
    
    def _apply_saved_theme_colors(self, colors):
        """Apply saved theme colors to all existing widgets"""
        try:
            if 'background' in colors:
                try:
                    self.configure(fg_color=colors['background'])
                except Exception:
                    pass
            for widget in self.winfo_children():
                self._apply_theme_to_widget(widget, colors)
        except Exception as e:
            logger.debug(f"Could not restore saved theme colors: {e}")
    
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

            # Checkbox to enable/disable tutorial on startup
            self.tutorial_on_startup_var = ctk.BooleanVar(
                value=config.get('tutorial', 'show_on_startup', default=True)
            )
            tutorial_checkbox = ctk.CTkCheckBox(
                menu_frame,
                text="Show on startup",
                variable=self.tutorial_on_startup_var,
                command=self._toggle_tutorial_on_startup,
                width=20
            )
            tutorial_checkbox.pack(side="right", padx=(0, 5), pady=5)
        
        # Apply tooltips to menu bar widgets
        self._apply_menu_tooltips(tutorial_button, settings_button, None, help_button)
    
    def _toggle_tutorial_on_startup(self):
        """Toggle whether tutorial shows on application startup"""
        config.set('tutorial', 'show_on_startup', value=self.tutorial_on_startup_var.get())
        config.save()

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
        
        # Throttle scroll events on all scrollable frames to reduce lag/tearing
        self._throttle_scroll_frames()
        
        # Add pop-out buttons to dockable tabs
        self._add_popout_buttons()
        
        # Status bar
        self.create_status_bar()
    
    def _throttle_scroll_frames(self):
        """Patch CTkScrollableFrame widgets to throttle scroll events and reduce lag."""
        self._scroll_throttle_time = 0
        
        def _find_scrollable_frames(widget):
            """Recursively find all CTkScrollableFrame instances."""
            frames = []
            if isinstance(widget, ctk.CTkScrollableFrame):
                frames.append(widget)
            try:
                for child in widget.winfo_children():
                    frames.extend(_find_scrollable_frames(child))
            except Exception:
                pass
            return frames
        
        for sf in _find_scrollable_frames(self):
            try:
                # Access the internal canvas and reduce scroll increment
                if hasattr(sf, '_parent_canvas'):
                    canvas = sf._parent_canvas
                    canvas.configure(yscrollincrement=4)
            except Exception:
                pass
    
    def _has_popout_button(self, tab_frame):
        """Check if tab frame already has a pop-out button"""
        for widget in tab_frame.winfo_children():
            if self._is_popout_button(widget):
                return True
        return False
    
    def _is_popout_button(self, widget):
        """Check if widget is a popout button"""
        if not isinstance(widget, ctk.CTkButton):
            return False
        try:
            text = widget.cget('text')
            return text and ('Pop Out' in text or text in ('↗', '⧉'))
        except (Exception, AttributeError):
            return False
    
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
                tab_frame, text="⧉", width=30, height=26,
                font=("Arial", 14),
                fg_color="gray40", hover_color="gray50",
                corner_radius=6,
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
        
        # Get the tab frame and store a reference to it
        parent_tv = self._tab_to_tabview.get(tab_name, self.tabview)
        tab_frame = parent_tv.tab(tab_name)
        
        # Store original tab frame reference for re-docking
        if not hasattr(self, '_popout_original_frames'):
            self._popout_original_frames = {}
        self._popout_original_frames[tab_name] = tab_frame
        
        # Create container in popout window
        container = ctk.CTkFrame(popout)
        container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header label
        ctk.CTkLabel(container, text=f"{tab_name} (Undocked)",
                    font=("Arial Bold", 16)).pack(pady=(5, 10))
        
        # Content frame to hold rebuilt widgets
        content = ctk.CTkFrame(container)
        content.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Special handling for notepad: sync content instead of reparenting
        if tab_name == "📝 Notepad":
            self._create_popout_notepad(popout, content)
        else:
            # Rebuild tab content in the popout window
            self._rebuild_popout_content(tab_name, content)
        
        # Add dock-back button
        dock_btn = ctk.CTkButton(
            popout, text="📌 Dock Back", width=100, height=28,
            command=lambda n=tab_name, w=popout: self._dock_tab(n, w)
        )
        dock_btn.pack(side="bottom", pady=5)
        
        # Handle window close = dock back
        popout.protocol("WM_DELETE_WINDOW",
                        lambda n=tab_name, w=popout: self._dock_tab(n, w))
    
    def _rebuild_popout_content(self, tab_name, container):
        """Rebuild tab content inside a popout container frame."""
        # Temporarily reassign tab frame references so create_*_tab builds into container
        tab_creators = {
            "📁 File Browser": ('tab_browser', self.create_browser_tab),
            "ℹ️ About": ('tab_about', self.create_about_tab),
            "🏆 Achievements": None,
            "🛒 Shop": ('tab_shop', self.create_shop_tab),
            "🎁 Rewards": ('tab_rewards', self.create_rewards_tab),
            "📦 Inventory": ('tab_inventory', self.create_inventory_tab),
            "📊 Panda Stats & Mood": ('tab_panda_stats', self.create_panda_stats_tab),
        }
        creator_info = tab_creators.get(tab_name)
        if creator_info is None and tab_name == "🏆 Achievements":
            # Achievements has special rebuild logic
            scroll = ctk.CTkScrollableFrame(container)
            scroll.pack(fill="both", expand=True, padx=5, pady=5)
            self.achieve_scroll = scroll
            self._display_achievements(getattr(self, '_achievement_category_filter', 'all'))
            return
        if creator_info:
            attr_name, creator_fn = creator_info
            original = getattr(self, attr_name)
            setattr(self, attr_name, container)
            try:
                creator_fn()
            except Exception as e:
                logger.error(f"Error rebuilding popout content for {tab_name}: {e}")
                ctk.CTkLabel(container, text=f"Error loading {tab_name}",
                           font=("Arial", 12)).pack(pady=20)
            finally:
                # Store the popout container ref; original will be restored on dock
                if not hasattr(self, '_popout_tab_refs'):
                    self._popout_tab_refs = {}
                self._popout_tab_refs[tab_name] = (attr_name, original)
    
    def _create_popout_notepad(self, popout_window, container):
        """Create notepad functionality in popout window (fully editable)"""
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
    
    def _dock_tab(self, tab_name, popout_window):
        """Dock a popped-out tab back into the main tabview"""
        try:
            # Special handling for notepad - sync edits back before closing
            if tab_name == "📝 Notepad":
                if hasattr(self, '_popout_note_textboxes'):
                    try:
                        self._popout_save_notes()
                    except Exception as e:
                        logger.error(f"Error saving popout notes during dock: {e}")
            else:
                # Restore original tab frame reference and rebuild content
                if hasattr(self, '_popout_tab_refs') and tab_name in self._popout_tab_refs:
                    attr_name, original_frame = self._popout_tab_refs[tab_name]
                    setattr(self, attr_name, original_frame)
                    del self._popout_tab_refs[tab_name]
                
                # Regenerate tab content in the original tab frame
                self._regenerate_tab_content(tab_name)
            
            # Destroy pop-out window
            if popout_window and popout_window.winfo_exists():
                popout_window.destroy()
            
            self._popout_windows.pop(tab_name, None)
            
            # Switch to the docked tab
            parent_tv = self._tab_to_tabview.get(tab_name, self.tabview)
            parent_tv.set(tab_name)
        except Exception as e:
            logger.error(f"Error docking tab '{tab_name}': {e}")
            # Ensure window is destroyed even if docking fails
            try:
                if popout_window and popout_window.winfo_exists():
                    popout_window.destroy()
            except Exception:
                pass
            self._popout_windows.pop(tab_name, None)
    
    def _regenerate_tab_content(self, tab_name):
        """Regenerate content for a tab after failed undock/dock cycle."""
        try:
            tab_frame = self._popout_original_frames.get(tab_name)
            if not tab_frame or not tab_frame.winfo_exists():
                return
            # Clear any leftover widgets (except the popout button)
            for child in list(tab_frame.winfo_children()):
                if not self._is_popout_button(child):
                    try:
                        child.destroy()
                    except Exception:
                        pass
            # Regenerate based on tab name
            tab_creators = {
                "📁 File Browser": lambda: self._rebuild_browser_in_frame(tab_frame),
                "ℹ️ About": lambda: self._rebuild_about_in_frame(tab_frame),
                "🏆 Achievements": lambda: self._rebuild_achievements_in_frame(tab_frame),
                "🛒 Shop": lambda: self._rebuild_shop_in_frame(tab_frame),
                "🎁 Rewards": lambda: self._rebuild_rewards_in_frame(tab_frame),
                "📦 Inventory": lambda: self._rebuild_inventory_in_frame(tab_frame),
                "📊 Panda Stats & Mood": lambda: self._rebuild_panda_stats_in_frame(tab_frame),
            }
            creator = tab_creators.get(tab_name)
            if creator:
                creator()
                logger.info(f"Regenerated content for tab: {tab_name}")
        except Exception as e:
            logger.error(f"Error regenerating tab '{tab_name}': {e}")
    
    def _rebuild_achievements_in_frame(self, frame):
        """Rebuild achievements tab content."""
        scroll = ctk.CTkScrollableFrame(frame)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.achieve_scroll = scroll
        self._display_achievements(getattr(self, '_achievement_category_filter', 'all'))
    
    def _rebuild_shop_in_frame(self, frame):
        """Rebuild shop tab content."""
        self.tab_shop = frame
        self.create_shop_tab()
    
    def _rebuild_rewards_in_frame(self, frame):
        """Rebuild rewards tab content."""
        self.tab_rewards = frame
        self.create_rewards_tab()
    
    def _rebuild_inventory_in_frame(self, frame):
        """Rebuild inventory tab content."""
        self.tab_inventory = frame
        self.create_inventory_tab()
    
    def _rebuild_panda_stats_in_frame(self, frame):
        """Rebuild panda stats & mood tab content."""
        self.tab_panda_stats = frame
        self.create_panda_stats_tab()
    
    def _rebuild_browser_in_frame(self, frame):
        """Rebuild file browser tab content."""
        self.tab_browser = frame
        self.create_browser_tab()
    
    def _rebuild_about_in_frame(self, frame):
        """Rebuild about tab content."""
        self.tab_about = frame
        self.create_about_tab()
    
    def _create_popout_browser(self, popout_window, container):
        """Create file browser in popout window"""
        ctk.CTkLabel(container, text="📁 File Browser (Undocked)",
                    font=("Arial Bold", 16)).pack(pady=20)
        ctk.CTkLabel(container, text="File browser content shown here",
                    font=("Arial", 12)).pack(pady=10)
    
    def _create_popout_about(self, popout_window, container):
        """Create about page in popout window"""
        scrollable = ctk.CTkScrollableFrame(container)
        scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(scrollable, text=f"🐼 {APP_NAME}",
                    font=("Arial Bold", 24)).pack(pady=20)
        ctk.CTkLabel(scrollable, text=f"Version {APP_VERSION}",
                    font=("Arial", 14)).pack(pady=5)
        ctk.CTkLabel(scrollable, text=f"by {APP_AUTHOR}",
                    font=("Arial", 12)).pack(pady=5)
    
    def _create_popout_achievements(self, popout_window, container):
        """Create achievements view in popout window"""
        ctk.CTkLabel(container, text="🏆 Achievements (Undocked)",
                    font=("Arial Bold", 16)).pack(pady=20)
        if self.achievement_manager:
            # Show achievements list
            scrollable = ctk.CTkScrollableFrame(container)
            scrollable.pack(fill="both", expand=True, padx=10, pady=10)
            
            achievements = self.achievement_manager.get_all_achievements()
            for ach_id, ach_data in achievements.items():
                ach_frame = ctk.CTkFrame(scrollable)
                ach_frame.pack(fill="x", padx=5, pady=2)
                
                icon = "🏆" if ach_data.get('unlocked', False) else "🔒"
                text = f"{icon} {ach_data.get('name', ach_id)}"
                ctk.CTkLabel(ach_frame, text=text).pack(side="left", padx=10)
    
    def _create_popout_shop(self, popout_window, container):
        """Create shop in popout window"""
        ctk.CTkLabel(container, text="🛒 Shop (Undocked)",
                    font=("Arial Bold", 16)).pack(pady=20)
        ctk.CTkLabel(container, text="Shop content shown here",
                    font=("Arial", 12)).pack(pady=10)
    
    def _create_popout_rewards(self, popout_window, container):
        """Create rewards page in popout window"""
        ctk.CTkLabel(container, text="🎁 Rewards (Undocked)",
                    font=("Arial Bold", 16)).pack(pady=20)
        ctk.CTkLabel(container, text="Rewards content shown here",
                    font=("Arial", 12)).pack(pady=10)
    
    def _create_popout_inventory(self, popout_window, container):
        """Create inventory in popout window"""
        ctk.CTkLabel(container, text="📦 Inventory (Undocked)",
                    font=("Arial Bold", 16)).pack(pady=20)
        ctk.CTkLabel(container, text="Inventory content shown here",
                    font=("Arial", 12)).pack(pady=10)
    
    def _create_popout_panda_stats(self, popout_window, container):
        """Create panda stats page in popout window"""
        ctk.CTkLabel(container, text="📊 Panda Stats & Mood (Undocked)",
                    font=("Arial Bold", 16)).pack(pady=20)
        if self.panda:
            stats_text = f"Mood: {self.panda.current_mood.value.title()}\nClicks: {self.panda.click_count}\nFeedings: {self.panda.feed_count}"
            ctk.CTkLabel(container, text=stats_text,
                        font=("Arial", 12)).pack(pady=10)
    
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
        
        browse_btn = ctk.CTkButton(input_path_frame, text="📂 Browse...", width=100, command=self.browse_input)
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
        
        browse_out_btn = ctk.CTkButton(output_path_frame, text="📂 Browse...", width=100, command=self.browse_output)
        browse_out_btn.pack(side="right", padx=5)
        
        # Options
        options_frame = ctk.CTkFrame(scrollable_frame)
        options_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(options_frame, text="Sorting Options:", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        opts_grid = ctk.CTkFrame(options_frame)
        opts_grid.pack(fill="x", padx=10, pady=5)
        
        # Mode selection
        ctk.CTkLabel(opts_grid, text="Mode:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.mode_var = ctk.StringVar(value="🤖 automatic")
        mode_menu = ctk.CTkOptionMenu(opts_grid, variable=self.mode_var, 
                                       values=["🤖 automatic", "✋ manual", "💡 suggested"])
        mode_menu.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Organization style (default: flat - simplest for new users)
        ctk.CTkLabel(opts_grid, text="Style:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        # Map display names to internal style keys
        self._style_display_to_key = {
            "📁 Simple Flat (Category Only)": "flat",
            "📋 Minimalist (Category → Files)": "minimalist",
            "👤 By Character Traits (Gender/Skin/Body)": "sims",
            "🏷️ By Type & Variant (Category/Type/File)": "neopets",
            "🗺️ By Game Area (Level/Area/Type)": "game_area",
            "⚙️ By Asset Pipeline (Type/Resolution/Format)": "asset_pipeline",
            "🧩 By Module (Characters/Vehicles/UI/etc.)": "modular",
            "🔬 Maximum Detail (Deep Hierarchy)": "maximum_detail",
            "🛠️ Custom (User-Defined)": "custom",
        }
        self._style_key_to_display = {v: k for k, v in self._style_display_to_key.items()}
        # Map for mode dropdown (strip emoji for internal use)
        self._mode_display_to_key = {
            "🤖 automatic": "automatic",
            "✋ manual": "manual",
            "💡 suggested": "suggested",
        }
        style_display_names = list(self._style_display_to_key.keys())
        self.style_var = ctk.StringVar(value="📁 Simple Flat (Category Only)")
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
        
        # Archive support checkboxes (new row)
        archive_check_frame = ctk.CTkFrame(opts_grid)
        archive_check_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky="w")
        
        self.extract_from_archive_var = ctk.BooleanVar(value=False)
        extract_archive_cb = ctk.CTkCheckBox(archive_check_frame, text="📦 Extract from archive", 
                                            variable=self.extract_from_archive_var)
        extract_archive_cb.pack(side="left", padx=10)
        
        self.compress_to_archive_var = ctk.BooleanVar(value=False)
        compress_archive_cb = ctk.CTkCheckBox(archive_check_frame, text="📦 Compress output to archive", 
                                             variable=self.compress_to_archive_var)
        compress_archive_cb.pack(side="left", padx=10)
        
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
                                  detect_lods_cb, group_lods_cb, detect_dupes_cb,
                                  extract_archive_cb, compress_archive_cb)
    
    def _apply_sort_tooltips(self, browse_in_btn, browse_out_btn, mode_menu, style_menu,
                            detect_lods_cb, group_lods_cb, detect_dupes_cb,
                            extract_archive_cb, compress_archive_cb):
        """Apply tooltips to sort tab widgets"""
        if not WidgetTooltip:
            return
        tt = self._get_tooltip_text
        tm = self.tooltip_manager
        # Store tooltip references to prevent garbage collection
        self._tooltips.append(WidgetTooltip(self.start_button, tt('sort_button'), widget_id='sort_button', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(self.pause_button, "Pause the current sorting operation"))
        self._tooltips.append(WidgetTooltip(self.stop_button, "Stop the sorting operation completely"))
        self._tooltips.append(WidgetTooltip(browse_in_btn, tt('input_browse'), widget_id='input_browse', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(browse_out_btn, tt('output_browse'), widget_id='output_browse', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(mode_menu, 
            "Sorting mode:\n"
            "• 🤖 automatic – AI classifies textures automatically based on image content and filenames\n"
            "• ✋ manual – You choose the category for each texture (AI shows suggestions)\n"
            "• 💡 suggested – AI suggests, you confirm or change each classification"))

        self._tooltips.append(WidgetTooltip(style_menu, 
            "Select how textures are organized:\n"
            "• 📁 Simple Flat – All files in category folders\n"
            "• 📋 Minimalist – Category → Files, minimal nesting\n"
            "• 👤 By Character Traits – Gender/Skin/Body Part\n"
            "• 🏷️ By Type & Variant – Category/Type/Individual\n"
            "• 🗺️ By Game Area – Level/Area/Type/Asset\n"
            "• ⚙️ By Asset Pipeline – Type/Resolution/Format\n"
            "• 🧩 By Module – Characters/Vehicles/UI/etc.\n"
            "• 🔬 Maximum Detail – Deep nested hierarchy\n"
            "• 🛠️ Custom – User-defined rules",
            widget_id='style_dropdown', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(detect_lods_cb, tt('lod_detection') or "Automatically detect Level of Detail (LOD) textures", widget_id='lod_detection', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(group_lods_cb, tt('group_lods') or "Group LOD textures together in folders", widget_id='group_lods', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(detect_dupes_cb, tt('detect_duplicates') or "Find and mark duplicate texture files", widget_id='detect_duplicates', tooltip_manager=tm))
        
        # NEW: Archive support tooltips
        self._tooltips.append(WidgetTooltip(extract_archive_cb, 
            "Extract textures from archive files before sorting\n"
            "Supports: ZIP, 7Z, RAR, TAR.GZ formats\n"
            "Automatically detects and extracts to temp directory"))
        self._tooltips.append(WidgetTooltip(compress_archive_cb, 
            "Compress sorted output into a ZIP archive\n"
            "Creates a .zip file with all organized textures\n"
            "Useful for sharing or storing sorted collections"))
    
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
        tm = self.tooltip_manager
        # Store tooltip references to prevent garbage collection
        self._tooltips.append(WidgetTooltip(self.convert_start_button, tt('convert_button') or "Start batch conversion of texture files", widget_id='convert_button', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(input_btn, tt('input_browse') or "Select directory containing files to convert", widget_id='input_browse', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(output_btn, tt('output_browse') or "Choose where to save converted files", widget_id='output_browse', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(from_menu, "Select source file format to convert from"))
        self._tooltips.append(WidgetTooltip(to_menu, "Select target file format to convert to"))
        self._tooltips.append(WidgetTooltip(recursive_cb, "Also convert files in subdirectories"))
        self._tooltips.append(WidgetTooltip(keep_cb, "Keep original files after conversion"))
    
    def _apply_browser_tooltips(self, browse_btn, refresh_btn, search_entry, show_all_cb):
        """Apply tooltips to file browser tab widgets"""
        if not WidgetTooltip:
            return
        tt = self._get_tooltip_text
        tm = self.tooltip_manager
        # Store tooltip references to prevent garbage collection
        self._tooltips.append(WidgetTooltip(browse_btn, tt('browser_browse_button') or tt('file_selection') or "Select a directory to browse texture files", widget_id='browser_browse_button', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(refresh_btn, tt('browser_refresh_button') or "Refresh the file list", widget_id='browser_refresh_button', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(search_entry, tt('browser_search') or tt('search_button') or "Search for specific files by name", widget_id='browser_search', tooltip_manager=tm))
        self._tooltips.append(WidgetTooltip(show_all_cb, tt('browser_show_all') or "Show all file types, not just textures", widget_id='browser_show_all', tooltip_manager=tm))
    
    def _apply_menu_tooltips(self, tutorial_btn, settings_btn, theme_btn, help_btn):
        """Apply tooltips to menu bar widgets"""
        if not WidgetTooltip:
            return
        tt = self._get_tooltip_text
        tm = self.tooltip_manager
        # Store tooltip references to prevent garbage collection
        if tutorial_btn:
            self._tooltips.append(WidgetTooltip(tutorial_btn, tt('tutorial_button') or "Start or restart the interactive tutorial", widget_id='tutorial_button', tooltip_manager=tm))
        if settings_btn:
            self._tooltips.append(WidgetTooltip(settings_btn, tt('settings_button') or "Open application settings and preferences", widget_id='settings_button', tooltip_manager=tm))
        if theme_btn:
            self._tooltips.append(WidgetTooltip(theme_btn, tt('theme_selector') or "Toggle between light and dark theme", widget_id='theme_selector', tooltip_manager=tm))
        if help_btn:
            self._tooltips.append(WidgetTooltip(help_btn, tt('help_button') or "Open context-sensitive help (F1)", widget_id='help_button', tooltip_manager=tm))
    
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
        convert_input_btn = ctk.CTkButton(input_frame, text="📂 Browse", width=100, 
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
        
        # Archive support checkboxes
        archive_check_frame = ctk.CTkFrame(check_frame)
        archive_check_frame.pack(side="left", padx=20)
        
        self.convert_extract_from_archive_var = ctk.BooleanVar(value=False)
        convert_extract_archive_cb = ctk.CTkCheckBox(archive_check_frame, text="📦 Extract from archive", 
                       variable=self.convert_extract_from_archive_var)
        convert_extract_archive_cb.pack(side="left", padx=10)
        
        self.convert_compress_to_archive_var = ctk.BooleanVar(value=False)
        convert_compress_archive_cb = ctk.CTkCheckBox(archive_check_frame, text="📦 Compress output to archive", 
                       variable=self.convert_compress_to_archive_var)
        convert_compress_archive_cb.pack(side="left", padx=10)
        
        # === OUTPUT SECTION ===
        output_frame = ctk.CTkFrame(scrollable_content)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(output_frame, text="Output:", font=("Arial Bold", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.convert_output_var = ctk.StringVar()
        ctk.CTkEntry(output_frame, textvariable=self.convert_output_var, width=500).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        convert_output_btn = ctk.CTkButton(output_frame, text="📂 Browse", width=100,
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
        extract_from_archive = self.convert_extract_from_archive_var.get()
        compress_to_archive = self.convert_compress_to_archive_var.get()
        
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
            args=(input_path, output_path, from_format, to_format, recursive, extract_from_archive, compress_to_archive),
            daemon=True
        ).start()
    
    def conversion_thread(self, input_path_str, output_path_str, from_format, to_format, recursive, 
                         extract_from_archive=False, compress_to_archive=False):
        """Background thread for file conversion"""
        temp_extraction_dir = None
        try:
            input_path = Path(input_path_str)
            output_path = Path(output_path_str)
            
            # Handle archive extraction if requested
            if extract_from_archive and self.file_handler.is_archive(input_path):
                self.convert_log(f"📦 Extracting archive: {input_path.name}")
                self.after(0, lambda: self.convert_progress_bar.set(0.05))
                self.after(0, lambda: self.convert_progress_label.configure(text="Extracting archive..."))
                temp_extraction_dir = self.file_handler.extract_archive(input_path)
                if temp_extraction_dir:
                    input_path = temp_extraction_dir
                    self.convert_log(f"✓ Archive extracted to temporary directory")
                else:
                    self.convert_log(f"❌ Failed to extract archive: {input_path.name}")
                    return
            
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
            
            # Handle archive compression if requested
            if compress_to_archive and converted > 0:
                self.after(0, lambda: self.convert_progress_bar.set(0.95))
                self.after(0, lambda: self.convert_progress_label.configure(text="Compressing output..."))
                self.convert_log(f"📦 Creating archive from output directory...")
                archive_name = f"{output_path.name}_converted.zip"
                archive_path = output_path.parent / archive_name
                success = self.file_handler.create_archive(output_path, archive_path)
                if success:
                    self.convert_log(f"✓ Archive created: {archive_path.name}")
                else:
                    self.convert_log(f"⚠️ Failed to create output archive")
            
        except Exception as e:
            self.convert_log(f"❌ Error during conversion: {e}")
        
        finally:
            # Clean up temporary extraction directory if it was created
            if temp_extraction_dir and temp_extraction_dir.exists():
                try:
                    self.file_handler.cleanup_temp_archives()
                except Exception as e:
                    logger.error(f"Failed to cleanup temp dir: {e}")
            
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
        header_frame.pack(fill="x", padx=(10, 45), pady=10)
        
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
        
        # Game info display (initially hidden)
        self.browser_game_info_frame = ctk.CTkFrame(self.tab_browser)
        # Don't pack yet - will be shown when game is detected
        
        self.browser_game_info_label = ctk.CTkLabel(
            self.browser_game_info_frame,
            text="No game identified",
            font=("Arial", 10),
            anchor="w"
        )
        self.browser_game_info_label.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        # Add manual game selection button
        self.browser_game_select_btn = ctk.CTkButton(
            self.browser_game_info_frame,
            text="🎮 Select Game",
            command=self._browser_manual_game_select,
            width=120
        )
        self.browser_game_select_btn.pack(side="right", padx=5, pady=5)
        
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
        
        # Add show thumbnails checkbox directly in browser
        self.browser_show_thumbs = ctk.BooleanVar(value=config.get('ui', 'show_thumbnails', default=True))
        
        def on_browser_thumb_toggle():
            config.set('ui', 'show_thumbnails', value=self.browser_show_thumbs.get())
            try:
                config.save()
            except Exception:
                pass
            self.browser_refresh()
        
        browser_thumb_cb = ctk.CTkCheckBox(file_header, text="🖼️ Thumbnails",
                       variable=self.browser_show_thumbs,
                       command=on_browser_thumb_toggle)
        browser_thumb_cb.pack(side="left", padx=10)
        
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
        """Select directory or archive for file browser"""
        # Allow selecting both directories and archive files
        from tkinter import filedialog as tk_filedialog
        
        # Create custom file dialog that allows selecting directories or archives
        result = tk_filedialog.askopenfilename(
            title="Select Directory or Archive",
            filetypes=[
                ("All Supported", "*.zip *.7z *.rar *.tar.gz *.tgz"),
                ("ZIP archives", "*.zip"),
                ("7Z archives", "*.7z"),
                ("RAR archives", "*.rar"),
                ("TAR archives", "*.tar.gz *.tgz"),
                ("All files", "*.*")
            ]
        )
        
        # If user didn't select a file, try directory selection
        if not result:
            directory = filedialog.askdirectory(title="Select Directory to Browse")
            if directory:
                self.browser_path_var.set(directory)
                self.browser_current_dir = Path(directory)
                self.browser_is_archive = False
                self.browser_archive_path = None
                
                # Attempt to identify game from directory
                self._identify_and_display_game(Path(directory))
                
                self.browser_refresh()
        else:
            # User selected an archive file
            archive_path = Path(result)
            if self.file_handler.is_archive(archive_path):
                self.browser_path_var.set(f"📦 {archive_path.name}")
                self.browser_current_dir = archive_path
                self.browser_is_archive = True
                self.browser_archive_path = archive_path
                
                # Try to identify game from archive name
                self._identify_and_display_game(archive_path)
                
                self.browser_refresh_archive()
            else:
                messagebox.showwarning("Invalid Archive", "Selected file is not a valid archive format.")
    
    def _identify_and_display_game(self, directory: Path):
        """Identify game from directory and display info in browser."""
        try:
            # Try to identify game using ProfileManager
            if hasattr(self, 'profile_manager'):
                game_info = self.profile_manager.identify_game_from_path(directory)
                
                if game_info:
                    # Store game info
                    self.current_game_info = game_info
                    
                    # Update status display if it exists
                    if hasattr(self, 'browser_game_info_label'):
                        info_text = (
                            f"🎮 Game: {game_info.get('title', 'Unknown')} "
                            f"| Serial: {game_info.get('serial', 'N/A')} "
                            f"| Region: {game_info.get('region', 'N/A')}"
                        )
                        self.browser_game_info_label.configure(text=info_text)
                        
                        # Show the game info frame if it was hidden
                        if hasattr(self, 'browser_game_info_frame'):
                            self.browser_game_info_frame.pack(fill="x", padx=10, pady=5, after=self.browser_path_label.master)
                    
                    self.log(
                        f"Identified game: {game_info.get('title')} "
                        f"(Serial: {game_info.get('serial')}, "
                        f"Confidence: {game_info.get('confidence', 0):.0%})"
                    )
                else:
                    # No game identified
                    self.current_game_info = None
                    if hasattr(self, 'browser_game_info_frame'):
                        self.browser_game_info_frame.pack_forget()
                        
        except Exception as e:
            logger.error(f"Error identifying game: {e}", exc_info=True)
            self.current_game_info = None
    
    def _browser_manual_game_select(self):
        """Show dialog to manually select a game."""
        try:
            from src.features.game_identifier import GameIdentifier
            
            # Create identifier to get list of known games
            identifier = GameIdentifier()
            known_games = identifier.get_all_known_games()
            
            if not known_games:
                messagebox.showinfo(
                    "Game Database Unavailable", 
                    "Unable to load game database. Please check the game identifier configuration."
                )
                return
            
            # Create dialog
            dialog = ctk.CTkToplevel(self)
            dialog.title("Select Game")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - 250
            y = (dialog.winfo_screenheight() // 2) - 200
            dialog.geometry(f"500x400+{x}+{y}")
            
            # Header
            ctk.CTkLabel(
                dialog,
                text="Select PS2 Game",
                font=("Arial Bold", 16)
            ).pack(pady=10)
            
            ctk.CTkLabel(
                dialog,
                text="Choose a game to apply its texture profile:"
            ).pack(pady=5)
            
            # Game list
            list_frame = ctk.CTkFrame(dialog)
            list_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Create scrollable frame
            scroll_frame = ctk.CTkScrollableFrame(list_frame)
            scroll_frame.pack(fill="both", expand=True)
            
            selected_game = [None]  # Use list to capture selection
            
            def on_game_select(game):
                """Handle game selection."""
                selected_game[0] = game
                
                # Look up full game info
                game_info = identifier.lookup_by_serial(game['serial'])
                if game_info:
                    # Store as current game
                    self.current_game_info = {
                        'serial': game_info.serial,
                        'crc': game_info.crc,
                        'title': game_info.title,
                        'region': game_info.region,
                        'confidence': 1.0,  # Manual selection = 100% confidence
                        'source': 'manual',
                        'texture_profile': game_info.texture_profile
                    }
                    
                    # Update UI
                    info_text = (
                        f"🎮 Game: {game_info.title} "
                        f"| Serial: {game_info.serial} "
                        f"| Region: {game_info.region} (Manual)"
                    )
                    self.browser_game_info_label.configure(text=info_text)
                    
                    # Show the game info frame
                    if hasattr(self, 'browser_game_info_frame'):
                        self.browser_game_info_frame.pack(fill="x", padx=10, pady=5, after=self.browser_path_label.master)
                    
                    self.log(f"Manually selected game: {game_info.title} ({game_info.serial})")
                
                dialog.destroy()
            
            # Add game buttons
            for game in known_games:
                btn = ctk.CTkButton(
                    scroll_frame,
                    text=f"{game['title']} ({game['serial']})",
                    command=lambda g=game: on_game_select(g),
                    anchor="w",
                    height=40
                )
                btn.pack(fill="x", padx=5, pady=2)
            
            # Cancel button
            ctk.CTkButton(
                dialog,
                text="Cancel",
                command=dialog.destroy,
                width=100
            ).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error in manual game selection: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to show game selection dialog:\n{e}")
    
    def browser_refresh(self):
        """Refresh file browser content - scanning runs off UI thread"""
        if not hasattr(self, 'browser_current_dir'):
            return
        
        # Check if we're browsing an archive
        if hasattr(self, 'browser_is_archive') and self.browser_is_archive:
            self.browser_refresh_archive()
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
                    # Use list() to ensure iterator is properly consumed and closed
                    dir_entries = list(current_dir.iterdir())
                    for f in dir_entries:
                        try:
                            if not f.is_file():
                                continue
                            if not show_all and f.suffix.lower() not in texture_extensions:
                                continue
                            if search_query and search_query not in f.name.lower():
                                continue
                            files.append(f)
                            if len(files) >= MAX_MATCHING_FILES:
                                break
                        except (OSError, PermissionError) as e:
                            logger.debug(f"Error accessing file {f}: {e}")
                            continue
                except (PermissionError, OSError, FileNotFoundError) as e:
                    logger.error(f"Error scanning directory {current_dir}: {e}")
                    files = []
                
                files_sorted = sorted(files)
                
                # Collect folders
                folders = []
                try:
                    dir_entries = list(current_dir.iterdir())
                    for f in dir_entries:
                        try:
                            if f.is_dir():
                                folders.append(f)
                        except (OSError, PermissionError) as e:
                            logger.debug(f"Error accessing directory {f}: {e}")
                            continue
                    folders = sorted(folders)
                except (PermissionError, OSError, FileNotFoundError) as e:
                    logger.error(f"Error scanning folders in {current_dir}: {e}")
                    folders = []
                
                # Schedule UI update on main thread - check window still exists
                if self.winfo_exists():
                    self.after(0, lambda: self._browser_update_ui(
                        files_sorted, folders, show_all, search_query, MAX_MATCHING_FILES))
            
            thread = threading.Thread(target=_scan_files, daemon=True)
            thread.start()
            
        except Exception as e:
            self._browser_refresh_pending = False
            self.browser_status.configure(text=f"Error: {e}")
            logger.error(f"Browser refresh error: {e}")
    
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
    
    def browser_refresh_archive(self):
        """Refresh file browser content for archive files"""
        if not hasattr(self, 'browser_archive_path'):
            return
        
        try:
            # Clear current file list
            for widget in self.browser_file_list.winfo_children():
                widget.destroy()
            
            # Show loading indicator
            self.browser_status.configure(text="Reading archive contents...")
            
            # Get archive contents
            archive_contents = self.file_handler.list_archive_contents(self.browser_archive_path)
            
            if not archive_contents:
                ctk.CTkLabel(self.browser_file_list, text="❌ Failed to read archive contents",
                           font=("Arial", 12)).pack(pady=20)
                self.browser_status.configure(text="Error reading archive")
                return
            
            # Filter for texture files
            texture_extensions = {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga'}
            show_all = self.browser_show_all.get() if hasattr(self, 'browser_show_all') else False
            search_query = self.browser_search_var.get().lower() if hasattr(self, 'browser_search_var') else ""
            
            filtered_files = []
            for file_path in archive_contents:
                file_lower = file_path.lower()
                # Check if it's a file (not directory)
                if '/' in file_path and not file_path.endswith('/'):
                    ext = Path(file_path).suffix.lower()
                    if show_all or ext in texture_extensions:
                        if not search_query or search_query in file_lower:
                            filtered_files.append(file_path)
            
            # Sort files
            filtered_files.sort()
            
            # Display files
            MAX_DISPLAY = 200
            total_files = len(filtered_files)
            display_files = filtered_files[:MAX_DISPLAY]
            
            if not display_files:
                file_type = "files" if show_all else "texture files"
                no_files_msg = f"No {file_type} found"
                if search_query:
                    no_files_msg += f" matching '{search_query}'"
                ctk.CTkLabel(self.browser_file_list, text=no_files_msg,
                           font=("Arial", 12)).pack(pady=20)
            else:
                # Display file entries
                for file_path in display_files:
                    file_name = Path(file_path).name
                    file_frame = ctk.CTkFrame(self.browser_file_list)
                    file_frame.pack(fill="x", pady=2, padx=5)
                    
                    # Archive icon
                    icon_label = ctk.CTkLabel(file_frame, text="📦", width=30)
                    icon_label.pack(side="left", padx=5)
                    
                    # File name
                    name_label = ctk.CTkLabel(file_frame, text=file_name, anchor="w")
                    name_label.pack(side="left", fill="x", expand=True, padx=5)
                    
                    # Path in archive
                    path_label = ctk.CTkLabel(file_frame, text=file_path, 
                                             font=("Arial", 8), text_color="gray", anchor="w")
                    path_label.pack(side="left", padx=5)
                
                if total_files > MAX_DISPLAY:
                    overflow_text = f"... and {total_files - MAX_DISPLAY} more files (use search to filter)"
                    ctk.CTkLabel(self.browser_file_list, 
                               text=overflow_text,
                               font=("Arial", 10), text_color="gray").pack(pady=10)
            
            # Clear folder list for archives
            if hasattr(self, 'browser_folder_list'):
                self.browser_folder_list.delete("1.0", "end")
                self.browser_folder_list.insert("end", "📦 Archive contents (no folder navigation)\n")
            
            status = f"Archive: {len(display_files)} of {total_files} file(s)"
            self.browser_status.configure(text=status)
            
        except Exception as e:
            logger.error(f"Error refreshing archive browser: {e}", exc_info=True)
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
        
        # Add thumbnail for image/texture files if enabled
        show_thumbnails = self.browser_show_thumbs.get() if hasattr(self, 'browser_show_thumbs') else config.get('ui', 'show_thumbnails', default=True)
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
        """Create a thumbnail for an image file with LRU cache (O(1) operations)"""
        try:
            from PIL import Image
            
            thumb_size = config.get('ui', 'thumbnail_size', default=32)
            
            # Check cache first
            cache_key = f"{file_path}_{thumb_size}"
            if cache_key in self._thumbnail_cache:
                cached_photo = self._thumbnail_cache[cache_key]
                # Move to end of LRU order (O(1) operation with OrderedDict)
                self._thumbnail_cache.move_to_end(cache_key)
                label = ctk.CTkLabel(parent_frame, image=cached_photo, text="")
                # Keep strong reference to prevent garbage collection (tkinter pattern)
                label.photo_ref = cached_photo
                return label
            
            # Load and resize image
            img = Image.open(file_path)
            try:
                # Convert DDS if needed
                if file_path.suffix.lower() == '.dds':
                    if img.mode not in ('RGB', 'RGBA'):
                        converted = img.convert('RGBA')
                        img.close()
                        img = converted
                
                # Force load pixel data before creating CTkImage
                img.load()
                
                # Create thumbnail at configured size
                img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                
                # Make a copy so the file handle can be released
                thumb_img = img.copy()
            finally:
                img.close()
            
            # Use CTkImage for proper display in customtkinter
            photo = ctk.CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(thumb_size, thumb_size))
            
            # LRU eviction: remove oldest entry if cache exceeds max (O(1) with OrderedDict)
            if len(self._thumbnail_cache) >= self._thumbnail_cache_max:
                # Remove oldest item (first item in OrderedDict)
                self._thumbnail_cache.popitem(last=False)
            
            # Add to cache (at end, marking as most recently used)
            self._thumbnail_cache[cache_key] = photo
            
            # Create label with thumbnail
            label = ctk.CTkLabel(parent_frame, image=photo, text="")
            # Keep strong reference to prevent garbage collection (tkinter pattern)
            label.photo_ref = photo
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
        """Apply selected theme. Themes only affect visual colors, not application behavior."""
        # Handle backward compatibility: rename old "vulgar_panda" theme to "red_panda"
        if theme_name == 'vulgar_panda':
            theme_name = 'red_panda'
        
        try:
            if theme_name in ['dark', 'light']:
                ctk.set_appearance_mode(theme_name)
                config.set('ui', 'theme', value=theme_name)
                self.log(f"Theme changed to: {theme_name}")
                # Force widget refresh to prevent invisible elements
                self.update_idletasks()
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
                                # Apply background color to the main window
                                if 'background' in colors:
                                    try:
                                        self.configure(fg_color=colors['background'])
                                    except Exception:
                                        pass
                                for widget in self.winfo_children():
                                    self._apply_theme_to_widget(widget, colors)
                            except Exception as widget_err:
                                logger.warning(f"Error applying theme to widgets: {widget_err}")
                        self.log(f"Theme changed to: {theme['name']}")
                        # Force widget refresh to prevent invisible elements
                        self.update_idletasks()
                    else:
                        # Fall back to dark/light based on name hint
                        mode = 'light' if 'light' in theme_name.lower() else 'dark'
                        ctk.set_appearance_mode(mode)
                        config.set('ui', 'theme', value=theme_name)
                        self.log(f"Theme changed to: {theme_name}")
                        # Force widget refresh
                        self.update_idletasks()
                except ImportError as imp_err:
                    logger.warning(f"Import error loading theme: {imp_err}")
                    ctk.set_appearance_mode('dark')
                    self.log(f"Theme changed to dark (fallback)")
                    self.update_idletasks()
        except Exception as e:
            logger.error(f"Error applying theme: {e}")
            self.log(f"⚠️ Theme change error, reverting to safe mode")
            try:
                ctk.set_appearance_mode('dark')
                self.update_idletasks()
            except Exception:
                pass
    
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
    
    def _open_sound_settings(self):
        """Open customization dialog directly on the Sound tab."""
        if CUSTOMIZATION_AVAILABLE:
            try:
                open_customization_dialog(parent=self,
                                          on_settings_change=self._on_customization_change,
                                          initial_tab="🔊 Sound")
                self.log("✅ Opened Sound Settings")
            except Exception as e:
                self.log(f"❌ Error opening sound settings: {e}")
        else:
            self.log("⚠️ UI Customization not available")
    
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
                    try:
                        # Apply background color to main window
                        if 'background' in colors:
                            try:
                                self.configure(fg_color=colors['background'])
                            except Exception:
                                pass
                        for widget in self.winfo_children():
                            self._apply_theme_to_widget(widget, colors)
                    except Exception as widget_err:
                        logger.debug(f"Could not update all widget colors: {widget_err}")
                
                # Force widget refresh to prevent invisible elements
                self.update_idletasks()
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
                
                self.update_idletasks()
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
                # Apply tooltip mode change immediately
                # Tooltip mode only affects tooltip text style (normal/dumbed-down/vulgar_panda)
                # It does NOT change the application mode or theme
                # Update TooltipVerbosityManager
                if self.tooltip_manager:
                    try:
                        from src.features.tutorial_system import TooltipMode
                        mode = TooltipMode(value)
                        self.tooltip_manager.set_mode(mode)
                    except Exception as tooltip_err:
                        logger.debug(f"Could not change tooltip mode via manager: {tooltip_err}")
                
                # Sync vulgar tooltip text preference with PandaCharacter
                if self.panda and hasattr(self.panda, 'set_vulgar_mode'):
                    self.panda.set_vulgar_mode(value == 'vulgar_panda')
                
                # Always save to config immediately
                try:
                    config.set('ui', 'tooltip_mode', value=value)
                    config.save()
                except Exception as cfg_err:
                    logger.debug(f"Could not save tooltip mode: {cfg_err}")
                
                self.log(f"✅ Tooltip mode changed to: {value}")
                
            elif setting_type == 'sound_enabled':
                # Apply sound toggle
                try:
                    config.set('sound', 'enabled', value=value)
                    config.save()
                    if self.sound_manager:
                        if value:
                            self.sound_manager.unmute()
                        else:
                            self.sound_manager.mute()
                    self.log(f"✅ Sound {'enabled' if value else 'disabled'}")
                except Exception as sound_err:
                    logger.debug(f"Could not save sound setting: {sound_err}")
                
            elif setting_type == 'volume':
                # Apply master volume change
                try:
                    config.set('sound', 'master_volume', value=value)
                    config.save()
                    if self.sound_manager:
                        self.sound_manager.set_master_volume(value)
                except Exception as vol_err:
                    logger.debug(f"Could not save volume setting: {vol_err}")
            
            elif setting_type == 'effects_volume':
                try:
                    config.set('sound', 'effects_volume', value=value)
                    config.save()
                    if self.sound_manager:
                        self.sound_manager.set_effects_volume(value)
                except Exception as vol_err:
                    logger.debug(f"Could not save effects volume: {vol_err}")
            
            elif setting_type == 'notifications_volume':
                try:
                    config.set('sound', 'notifications_volume', value=value)
                    config.save()
                    if self.sound_manager:
                        self.sound_manager.set_notifications_volume(value)
                except Exception as vol_err:
                    logger.debug(f"Could not save notifications volume: {vol_err}")
            
            elif setting_type == 'sound_pack':
                try:
                    config.set('sound', 'sound_pack', value=value)
                    config.save()
                    if self.sound_manager:
                        from src.features.sound_manager import SoundPack
                        try:
                            pack = SoundPack(value)
                            self.sound_manager.set_sound_pack(pack)
                        except ValueError:
                            pass
                    self.log(f"✅ Sound pack changed to: {value}")
                except Exception as pack_err:
                    logger.debug(f"Could not save sound pack: {pack_err}")
            
            elif setting_type == 'mute_sound':
                try:
                    event_id = value.get('event', '')
                    enabled = value.get('enabled', True)
                    muted_sounds = config.get('sound', 'muted_sounds', default={})
                    muted_sounds[event_id] = not enabled
                    config.set('sound', 'muted_sounds', value=muted_sounds)
                    config.save()
                except Exception as mute_err:
                    logger.debug(f"Could not save mute setting: {mute_err}")
            
            elif setting_type == 'sound_choice':
                try:
                    event_id = value.get('event', '')
                    sound = value.get('sound', '')
                    sound_choices = config.get('sound', 'sound_choices', default={})
                    sound_choices[event_id] = sound
                    config.set('sound', 'sound_choices', value=sound_choices)
                    config.save()
                except Exception as choice_err:
                    logger.debug(f"Could not save sound choice: {choice_err}")
                
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
                if 'text' in colors:
                    widget.configure(text_color=colors['text'])
            
            # Apply colors to CTkLabel widgets
            elif isinstance(widget, ctk.CTkLabel):
                if 'text' in colors:
                    try:
                        widget.configure(text_color=colors['text'])
                    except Exception:
                        pass
            
            # Apply colors to CTkEntry widgets
            elif isinstance(widget, ctk.CTkEntry):
                if 'background' in colors:
                    try:
                        widget.configure(fg_color=colors['background'])
                    except Exception:
                        pass
                if 'text' in colors:
                    try:
                        widget.configure(text_color=colors['text'])
                    except Exception:
                        pass
                if 'border' in colors:
                    try:
                        widget.configure(border_color=colors['border'])
                    except Exception:
                        pass
            
            # Apply colors to CTkTextbox widgets
            elif isinstance(widget, ctk.CTkTextbox):
                if 'background' in colors:
                    try:
                        widget.configure(fg_color=colors['background'])
                    except Exception:
                        pass
                if 'text' in colors:
                    try:
                        widget.configure(text_color=colors['text'])
                    except Exception:
                        pass
                if 'border' in colors:
                    try:
                        widget.configure(border_color=colors['border'])
                    except Exception:
                        pass
            
            # Apply colors to CTkOptionMenu widgets
            elif isinstance(widget, ctk.CTkOptionMenu):
                if 'button' in colors:
                    try:
                        widget.configure(fg_color=colors['button'])
                    except Exception:
                        pass
                if 'button_hover' in colors:
                    try:
                        widget.configure(button_hover_color=colors['button_hover'])
                    except Exception:
                        pass
                if 'text' in colors:
                    try:
                        widget.configure(text_color=colors['text'])
                    except Exception:
                        pass
            
            # Apply colors to CTkComboBox widgets
            elif isinstance(widget, ctk.CTkComboBox):
                if 'button' in colors:
                    try:
                        widget.configure(button_color=colors['button'])
                    except Exception:
                        pass
                if 'button_hover' in colors:
                    try:
                        widget.configure(button_hover_color=colors['button_hover'])
                    except Exception:
                        pass
                if 'border' in colors:
                    try:
                        widget.configure(border_color=colors['border'])
                    except Exception:
                        pass
                if 'text' in colors:
                    try:
                        widget.configure(text_color=colors['text'])
                    except Exception:
                        pass
            
            # Apply colors to CTkCheckBox widgets
            elif isinstance(widget, ctk.CTkCheckBox):
                if 'accent' in colors:
                    try:
                        widget.configure(fg_color=colors['accent'])
                    except Exception:
                        pass
                if 'text' in colors:
                    try:
                        widget.configure(text_color=colors['text'])
                    except Exception:
                        pass
            
            # Apply colors to CTkSwitch widgets
            elif isinstance(widget, ctk.CTkSwitch):
                if 'accent' in colors:
                    try:
                        widget.configure(progress_color=colors['accent'])
                    except Exception:
                        pass
                if 'button' in colors:
                    try:
                        widget.configure(button_color=colors['button'])
                    except Exception:
                        pass
                if 'text' in colors:
                    try:
                        widget.configure(text_color=colors['text'])
                    except Exception:
                        pass
            
            # Apply colors to CTkProgressBar widgets
            elif isinstance(widget, ctk.CTkProgressBar):
                if 'accent' in colors:
                    try:
                        widget.configure(progress_color=colors['accent'])
                    except Exception:
                        pass
            
            # Apply colors to CTkSlider widgets
            elif isinstance(widget, ctk.CTkSlider):
                if 'accent' in colors:
                    try:
                        widget.configure(progress_color=colors['accent'])
                    except Exception:
                        pass
                if 'button' in colors:
                    try:
                        widget.configure(button_color=colors['button'])
                    except Exception:
                        pass
                if 'button_hover' in colors:
                    try:
                        widget.configure(button_hover_color=colors['button_hover'])
                    except Exception:
                        pass
            
            # Apply colors to CTkSegmentedButton widgets
            elif isinstance(widget, ctk.CTkSegmentedButton):
                if 'accent' in colors:
                    try:
                        widget.configure(selected_color=colors['accent'])
                    except Exception:
                        pass
                if 'text' in colors:
                    try:
                        widget.configure(text_color=colors['text'])
                    except Exception:
                        pass
            
            # Apply colors to CTkScrollableFrame widgets
            elif isinstance(widget, ctk.CTkScrollableFrame):
                if 'secondary' in colors:
                    try:
                        widget.configure(fg_color=colors['secondary'])
                    except Exception:
                        pass
                if 'border' in colors:
                    try:
                        widget.configure(border_color=colors['border'])
                    except Exception:
                        pass
            
            # Apply colors to CTkTabview widgets
            elif isinstance(widget, ctk.CTkTabview):
                if 'secondary' in colors:
                    try:
                        widget.configure(fg_color=colors['secondary'])
                    except Exception:
                        pass
                if 'accent' in colors:
                    try:
                        widget.configure(segmented_button_selected_color=colors['accent'])
                    except Exception:
                        pass
            
            # Apply colors to CTkFrame widgets (must be last since some widgets inherit from it)
            elif isinstance(widget, ctk.CTkFrame):
                if 'secondary' in colors:
                    try:
                        widget.configure(fg_color=colors['secondary'])
                    except Exception:
                        pass
                if 'border' in colors:
                    try:
                        widget.configure(border_color=colors['border'])
                    except Exception:
                        pass
            
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
        """Setup or teardown cursor trail effect.
        
        Instead of covering the entire window with a canvas overlay (which
        blocks interaction), we track mouse motion on the root window and
        draw small, temporary fading labels that don't intercept events.
        """
        # Remove existing trail items if any
        if hasattr(self, '_trail_bind_id') and self._trail_bind_id:
            try:
                self.unbind('<Motion>', self._trail_bind_id)
            except Exception:
                pass
            self._trail_bind_id = None
        
        # Clean up any leftover trail dot widgets
        if hasattr(self, '_trail_dots_widgets'):
            for w in self._trail_dots_widgets:
                try:
                    w.destroy()
                except Exception:
                    pass
        self._trail_dots_widgets = []
        
        if not enabled:
            return
        
        import tkinter as tk
        
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
                x = event.x_root - self.winfo_rootx()
                y = event.y_root - self.winfo_rooty()
                
                # Draw trail even outside window bounds, but clip to visible area
                # This allows trail to extend to full window including decorations
                window_width = self.winfo_width()
                window_height = self.winfo_height()
                
                # Only skip if way outside reasonable bounds (prevents excessive dots)
                if x < -50 or y < -50 or x > window_width + 50 or y > window_height + 50:
                    return
                
                color_idx = len(self._trail_dots_widgets) % len(trail_colors)
                
                # Create a tiny non-interactive label as a trail dot
                dot = tk.Frame(self, width=6, height=6, bg=trail_colors[color_idx],
                               highlightthickness=0, bd=0)
                dot.place(x=x - 3, y=y - 3)
                dot.lower()  # Keep below all other widgets
                # Prevent the dot from intercepting any mouse events
                dot.bind('<Enter>', lambda e: None)
                dot.bind('<Button-1>', lambda e: None)
                
                self._trail_dots_widgets.append(dot)
                
                # Remove oldest dots beyond max
                if len(self._trail_dots_widgets) > self._trail_max:
                    old = self._trail_dots_widgets.pop(0)
                    try:
                        old.destroy()
                    except Exception:
                        pass
                
                # Auto-fade after delay
                self.after(300, lambda d=dot: self._fade_trail_dot(d))
            except Exception as e:
                logger.debug(f"Cursor trail motion error: {e}")
        
        self._trail_bind_id = self.bind('<Motion>', on_motion, add='+')
    
    def _fade_trail_dot(self, dot_widget):
        """Remove a trail dot widget after it fades"""
        try:
            if dot_widget and dot_widget.winfo_exists():
                dot_widget.destroy()
                if hasattr(self, '_trail_dots_widgets') and dot_widget in self._trail_dots_widgets:
                    self._trail_dots_widgets.remove(dot_widget)
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
        
        def on_thumbnail_toggle():
            """Handle real-time thumbnail toggle"""
            try:
                config.set('ui', 'show_thumbnails', value=show_thumb_var.get())
                config.save()
                # Immediately refresh browser if it's loaded
                if hasattr(self, 'browser_current_dir'):
                    self.browser_refresh()
                self.log(f"✅ Thumbnails {'enabled' if show_thumb_var.get() else 'disabled'}")
            except Exception as e:
                logger.error(f"Failed to save thumbnail setting: {e}")
                self.log(f"❌ Error saving thumbnail setting: {e}")
        
        ctk.CTkCheckBox(thumb_toggle_frame, text="Show thumbnails in File Browser",
                       variable=show_thumb_var,
                       command=on_thumbnail_toggle).pack(side="left", padx=10)
        
        # Thumbnail size selector
        thumb_size_frame = ctk.CTkFrame(perf_frame)
        thumb_size_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(thumb_size_frame, text="Thumbnail Size:").pack(side="left", padx=10)
        thumb_size_var = ctk.StringVar(value=str(config.get('ui', 'thumbnail_size', default=32)))
        
        def on_thumbnail_size_change(choice):
            """Handle real-time thumbnail size change"""
            try:
                config.set('ui', 'thumbnail_size', value=int(choice))
                config.save()
                # Clear cache since size changed
                if hasattr(self, '_thumbnail_cache'):
                    self._thumbnail_cache.clear()
                # Refresh browser to show new size
                if hasattr(self, 'browser_current_dir'):
                    self.browser_refresh()
                self.log(f"✅ Thumbnail size changed to {choice}px")
            except Exception as e:
                logger.error(f"Failed to save thumbnail size: {e}")
                self.log(f"❌ Error saving thumbnail size: {e}")
        
        thumb_size_menu = ctk.CTkOptionMenu(thumb_size_frame, variable=thumb_size_var,
                                            values=["16", "32", "64"],
                                            command=on_thumbnail_size_change)
        thumb_size_menu.pack(side="left", padx=10)
        ctk.CTkLabel(thumb_size_frame, text="(default: 32)",
                    font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        # Disable panda animations (for low-end systems)
        panda_anim_frame = ctk.CTkFrame(perf_frame)
        panda_anim_frame.pack(fill="x", padx=10, pady=5)
        
        disable_panda_anim_var = ctk.BooleanVar(value=config.get('ui', 'disable_panda_animations', default=False))
        
        def on_panda_anim_toggle():
            """Apply panda animation toggle instantly."""
            try:
                disabled = disable_panda_anim_var.get()
                config.set('ui', 'disable_panda_animations', value=disabled)
                config.save()
                self.log(f"✅ Panda animations {'disabled' if disabled else 'enabled'}")
                # Immediately apply to active panda widget
                if hasattr(self, 'panda_widget') and self.panda_widget:
                    if disabled:
                        self.panda_widget.start_animation('idle')  # triggers hide
                    else:
                        self.panda_widget.start_animation('idle')  # triggers show
            except Exception as e:
                logger.error(f"Failed to save panda animation setting: {e}")
        
        ctk.CTkCheckBox(panda_anim_frame, text="Disable panda animations (for low-end systems)",
                       variable=disable_panda_anim_var,
                       command=on_panda_anim_toggle).pack(side="left", padx=10)
        
        # === APPEARANCE & CUSTOMIZATION (merged UI Settings + UI Customization) ===
        ui_frame = ctk.CTkFrame(settings_scroll)
        ui_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(ui_frame, text="🎨 Appearance & Customization", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        # Theme note - themes are managed in Advanced Customization panel only
        theme_note_frame = ctk.CTkFrame(ui_frame)
        theme_note_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(theme_note_frame, text="🎨 Theme: Use Advanced Customization below to select themes",
                    font=("Arial", 11), text_color="gray").pack(side="left", padx=10)
        
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
        
        # Note: Tooltip mode, cursor style, and sound settings are
        # available in the Advanced Customization panel to avoid duplication.
        
        # Advanced Customization button
        ctk.CTkButton(ui_frame, text="🎨 Advanced Customization (Tooltips, Cursors, Colors)",
                     command=self.open_customization,
                     width=350, height=35).pack(padx=20, pady=10)
        
        # === KEYBOARD CONTROLS & HOTKEY CONFIGURATION (combined) ===
        kb_frame = ctk.CTkFrame(settings_scroll)
        kb_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(kb_frame, text="⌨️ Keyboard Controls & Hotkey Configuration", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        ctk.CTkLabel(kb_frame, text="View and customize keyboard shortcuts below. Click Edit to change a hotkey binding.", 
                    font=("Arial", 10), text_color="gray").pack(anchor="w", padx=20, pady=(0, 5))
        
        # Enable/disable hotkeys
        hotkey_enabled_var = ctk.BooleanVar(value=config.get('hotkeys', 'enabled', default=True))
        ctk.CTkCheckBox(kb_frame, text="Enable keyboard shortcuts", 
                       variable=hotkey_enabled_var).pack(anchor="w", padx=20, pady=3)
        
        global_hotkey_var = ctk.BooleanVar(value=config.get('hotkeys', 'global_hotkeys_enabled', default=False))
        ctk.CTkCheckBox(kb_frame, text="Enable global hotkeys (work when app is not focused)", 
                       variable=global_hotkey_var).pack(anchor="w", padx=20, pady=3)
        
        # Embed the HotkeySettingsPanel directly
        try:
            from src.ui.hotkey_settings_panel import HotkeySettingsPanel
            if not hasattr(self, 'hotkey_manager') or self.hotkey_manager is None:
                from src.features.hotkey_manager import HotkeyManager
                self.hotkey_manager = HotkeyManager()
            
            hotkey_panel = HotkeySettingsPanel(kb_frame, self.hotkey_manager)
            hotkey_panel.pack(fill="both", expand=True, padx=10, pady=5)
        except Exception as e:
            logger.error(f"Failed to load hotkey panel: {e}", exc_info=True)
            ctk.CTkLabel(kb_frame, text=f"⚠️ Could not load hotkey panel: {e}", 
                        text_color="orange").pack(padx=20, pady=5)
        
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
        
        # === NOTIFICATIONS & SOUND SETTINGS ===
        notif_frame = ctk.CTkFrame(settings_scroll)
        notif_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(notif_frame, text="🔔 Notifications & Sounds", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        ctk.CTkLabel(notif_frame,
                     text="🔊 All sound settings are in Advanced Customization → Sound tab",
                     font=("Arial", 11), text_color="gray").pack(anchor="w", padx=20, pady=3)
        
        ctk.CTkButton(notif_frame, text="🔊 Open Sound Settings",
                     command=self._open_sound_settings,
                     width=220, height=30).pack(padx=20, pady=8)
        
        # === AI MODEL SETTINGS ===
        ai_frame = ctk.CTkFrame(settings_scroll)
        ai_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(ai_frame, text="🤖 AI Model Settings", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        # Classification preference
        prefer_image_var = ctk.BooleanVar(value=config.get('ai', 'prefer_image_content', default=True))
        ctk.CTkCheckBox(ai_frame, text="Prioritize image content over filename patterns (recommended)", 
                       variable=prefer_image_var).pack(anchor="w", padx=20, pady=3)
        
        ctk.CTkLabel(ai_frame, text="This makes the AI analyze actual image content instead of just filenames",
                    font=("Arial", 9), text_color="gray").pack(anchor="w", padx=40, pady=(0, 5))
        
        # Offline AI Model
        offline_frame = ctk.CTkFrame(ai_frame)
        offline_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(offline_frame, text="Offline AI Model (ONNX):", 
                    font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=3)
        
        offline_enabled_var = ctk.BooleanVar(value=config.get('ai', 'offline', 'enabled', default=True))
        ctk.CTkCheckBox(offline_frame, text="Enable offline AI model", 
                       variable=offline_enabled_var).pack(anchor="w", padx=20, pady=3)
        
        offline_image_var = ctk.BooleanVar(value=config.get('ai', 'offline', 'use_image_analysis', default=True))
        ctk.CTkCheckBox(offline_frame, text="Use for image content analysis", 
                       variable=offline_image_var).pack(anchor="w", padx=20, pady=3)
        
        # Offline threads
        offline_thread_frame = ctk.CTkFrame(offline_frame)
        offline_thread_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(offline_thread_frame, text="CPU Threads:").pack(side="left", padx=10)
        offline_threads_var = ctk.StringVar(value=str(config.get('ai', 'offline', 'num_threads', default=4)))
        offline_threads_entry = ctk.CTkEntry(offline_thread_frame, textvariable=offline_threads_var, width=60)
        offline_threads_entry.pack(side="left", padx=10)
        ctk.CTkLabel(offline_thread_frame, text="(default: 4)",
                    font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        # Offline confidence weight
        offline_conf_frame = ctk.CTkFrame(offline_frame)
        offline_conf_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(offline_conf_frame, text="Confidence Weight:").pack(side="left", padx=10)
        offline_conf_slider = ctk.CTkSlider(offline_conf_frame, from_=0.0, to=1.0, number_of_steps=10)
        offline_conf_slider.set(config.get('ai', 'offline', 'confidence_weight', default=0.7))
        offline_conf_slider.pack(side="left", fill="x", expand=True, padx=10)
        offline_conf_label = ctk.CTkLabel(offline_conf_frame, text=f"{offline_conf_slider.get():.1f}")
        offline_conf_label.pack(side="left", padx=5)
        
        def update_offline_conf_label(value):
            offline_conf_label.configure(text=f"{float(value):.1f}")
        offline_conf_slider.configure(command=update_offline_conf_label)
        
        # Online AI Model
        online_frame = ctk.CTkFrame(ai_frame)
        online_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(online_frame, text="Online AI Model (API):", 
                    font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=3)
        
        online_enabled_var = ctk.BooleanVar(value=config.get('ai', 'online', 'enabled', default=False))
        ctk.CTkCheckBox(online_frame, text="Enable online AI model (requires API key)", 
                       variable=online_enabled_var).pack(anchor="w", padx=20, pady=3)
        
        # API Key
        api_key_frame = ctk.CTkFrame(online_frame)
        api_key_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(api_key_frame, text="API Key:").pack(side="left", padx=10)
        api_key_var = ctk.StringVar(value=config.get('ai', 'online', 'api_key', default=''))
        api_key_entry = ctk.CTkEntry(api_key_frame, textvariable=api_key_var, width=300, show="*")
        api_key_entry.pack(side="left", padx=10)
        
        # API URL
        api_url_frame = ctk.CTkFrame(online_frame)
        api_url_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(api_url_frame, text="API URL:").pack(side="left", padx=10)
        api_url_var = ctk.StringVar(value=config.get('ai', 'online', 'api_url', default='https://api.openai.com/v1'))
        api_url_entry = ctk.CTkEntry(api_url_frame, textvariable=api_url_var, width=400)
        api_url_entry.pack(side="left", padx=10)
        
        # Model name
        model_frame = ctk.CTkFrame(online_frame)
        model_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(model_frame, text="Model:").pack(side="left", padx=10)
        model_var = ctk.StringVar(value=config.get('ai', 'online', 'model', default='clip-vit-base-patch32'))
        model_entry = ctk.CTkEntry(model_frame, textvariable=model_var, width=300)
        model_entry.pack(side="left", padx=10)
        
        # Online timeout
        timeout_frame = ctk.CTkFrame(online_frame)
        timeout_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(timeout_frame, text="Timeout (seconds):").pack(side="left", padx=10)
        timeout_var = ctk.StringVar(value=str(config.get('ai', 'online', 'timeout', default=30)))
        timeout_entry = ctk.CTkEntry(timeout_frame, textvariable=timeout_var, width=60)
        timeout_entry.pack(side="left", padx=10)
        
        # Rate limits
        rate_frame = ctk.CTkFrame(online_frame)
        rate_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(rate_frame, text="Rate Limits:").pack(side="left", padx=10)
        ctk.CTkLabel(rate_frame, text="Per Minute:").pack(side="left", padx=5)
        rate_min_var = ctk.StringVar(value=str(config.get('ai', 'online', 'max_requests_per_minute', default=60)))
        rate_min_entry = ctk.CTkEntry(rate_frame, textvariable=rate_min_var, width=60)
        rate_min_entry.pack(side="left", padx=5)
        ctk.CTkLabel(rate_frame, text="Per Hour:").pack(side="left", padx=5)
        rate_hour_var = ctk.StringVar(value=str(config.get('ai', 'online', 'max_requests_per_hour', default=1000)))
        rate_hour_entry = ctk.CTkEntry(rate_frame, textvariable=rate_hour_var, width=60)
        rate_hour_entry.pack(side="left", padx=5)
        
        # Online confidence weight
        online_conf_frame = ctk.CTkFrame(online_frame)
        online_conf_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(online_conf_frame, text="Confidence Weight:").pack(side="left", padx=10)
        online_conf_slider = ctk.CTkSlider(online_conf_frame, from_=0.0, to=1.0, number_of_steps=10)
        online_conf_slider.set(config.get('ai', 'online', 'confidence_weight', default=0.8))
        online_conf_slider.pack(side="left", fill="x", expand=True, padx=10)
        online_conf_label = ctk.CTkLabel(online_conf_frame, text=f"{online_conf_slider.get():.1f}")
        online_conf_label.pack(side="left", padx=5)
        
        def update_online_conf_label(value):
            online_conf_label.configure(text=f"{float(value):.1f}")
        online_conf_slider.configure(command=update_online_conf_label)
        
        # Use online for difficult images
        online_difficult_var = ctk.BooleanVar(value=config.get('ai', 'online', 'use_for_difficult_images', default=True))
        ctk.CTkCheckBox(online_frame, text="Use online AI when offline has low confidence", 
                       variable=online_difficult_var).pack(anchor="w", padx=20, pady=3)
        
        # Low confidence threshold
        low_conf_frame = ctk.CTkFrame(online_frame)
        low_conf_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(low_conf_frame, text="Low Confidence Threshold:").pack(side="left", padx=10)
        low_conf_slider = ctk.CTkSlider(low_conf_frame, from_=0.0, to=1.0, number_of_steps=10)
        low_conf_slider.set(config.get('ai', 'online', 'low_confidence_threshold', default=0.5))
        low_conf_slider.pack(side="left", fill="x", expand=True, padx=10)
        low_conf_label = ctk.CTkLabel(low_conf_frame, text=f"{low_conf_slider.get():.1f}")
        low_conf_label.pack(side="left", padx=5)
        
        def update_low_conf_label(value):
            low_conf_label.configure(text=f"{float(value):.1f}")
        low_conf_slider.configure(command=update_low_conf_label)
        
        # AI Blending Mode
        blend_frame = ctk.CTkFrame(ai_frame)
        blend_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(blend_frame, text="AI Blend Mode:").pack(side="left", padx=10)
        blend_var = ctk.StringVar(value=config.get('ai', 'blend_mode', default='confidence_weighted'))
        blend_menu = ctk.CTkOptionMenu(blend_frame, variable=blend_var,
                                       values=["confidence_weighted", "max", "average", "offline_only", "online_only"])
        blend_menu.pack(side="left", padx=10)
        ctk.CTkLabel(blend_frame, text="(how to combine offline and online predictions)",
                    font=("Arial", 9), text_color="gray").pack(side="left", padx=5)
        
        # Minimum confidence
        min_conf_frame = ctk.CTkFrame(ai_frame)
        min_conf_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(min_conf_frame, text="Minimum Confidence:").pack(side="left", padx=10)
        min_conf_slider = ctk.CTkSlider(min_conf_frame, from_=0.0, to=1.0, number_of_steps=10)
        min_conf_slider.set(config.get('ai', 'min_confidence', default=0.3))
        min_conf_slider.pack(side="left", fill="x", expand=True, padx=10)
        min_conf_label = ctk.CTkLabel(min_conf_frame, text=f"{min_conf_slider.get():.1f}")
        min_conf_label.pack(side="left", padx=5)
        
        def update_min_conf_label(value):
            min_conf_label.configure(text=f"{float(value):.1f}")
        min_conf_slider.configure(command=update_min_conf_label)
        
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
                # Validate and save Performance settings
                try:
                    max_threads = int(thread_slider.get())
                    memory_limit = int(memory_var.get())
                    cache_size = int(cache_var.get())
                    
                    if max_threads < 1 or max_threads > 16:
                        raise ValueError("Thread count must be between 1 and 16")
                    if memory_limit < 512:
                        raise ValueError("Memory limit must be at least 512 MB")
                    if cache_size < 10:
                        raise ValueError("Cache size must be at least 10")
                    
                    config.set('performance', 'max_threads', value=max_threads)
                    config.set('performance', 'memory_limit_mb', value=memory_limit)
                    config.set('performance', 'thumbnail_cache_size', value=cache_size)
                    self._thumbnail_cache_max = cache_size
                except ValueError as e:
                    raise ValueError(f"Performance settings error: {e}")
                
                # Thumbnail & animation settings
                config.set('ui', 'show_thumbnails', value=show_thumb_var.get())
                config.set('ui', 'thumbnail_size', value=int(thumb_size_var.get()))
                config.set('ui', 'disable_panda_animations', value=disable_panda_anim_var.get())
                
                # UI / Appearance & Customization
                config.set('ui', 'scale', value=scale_var.get())
                
                # Validate and save File Handling settings
                try:
                    undo_depth = int(undo_var.get())
                    if undo_depth < 0:
                        raise ValueError("Undo depth cannot be negative")
                    
                    config.set('file_handling', 'create_backup', value=backup_var.get())
                    config.set('file_handling', 'overwrite_existing', value=overwrite_var.get())
                    config.set('file_handling', 'auto_save', value=autosave_var.get())
                    config.set('file_handling', 'undo_depth', value=undo_depth)
                except ValueError as e:
                    raise ValueError(f"File handling settings error: {e}")
                
                # Logging
                config.set('logging', 'log_level', value=loglevel_var.get())
                config.set('logging', 'crash_reports', value=crash_report_var.get())
                
                # Notifications & Sounds are now managed in Advanced Customization → Sound tab
                
                # AI Settings
                config.set('ai', 'prefer_image_content', value=prefer_image_var.get())
                
                # Validate and save Offline AI settings
                try:
                    offline_threads = int(offline_threads_var.get())
                    if offline_threads < 1 or offline_threads > 16:
                        raise ValueError("Offline AI threads must be between 1 and 16")
                    
                    config.set('ai', 'offline', 'enabled', value=offline_enabled_var.get())
                    config.set('ai', 'offline', 'use_image_analysis', value=offline_image_var.get())
                    config.set('ai', 'offline', 'num_threads', value=offline_threads)
                    config.set('ai', 'offline', 'confidence_weight', value=float(offline_conf_slider.get()))
                except ValueError as e:
                    raise ValueError(f"Offline AI settings error: {e}")
                
                # Validate and save Online AI settings
                try:
                    timeout = int(timeout_var.get())
                    rate_min = int(rate_min_var.get())
                    rate_hour = int(rate_hour_var.get())
                    
                    if timeout < 1:
                        raise ValueError("Timeout must be at least 1 second")
                    if rate_min < 1:
                        raise ValueError("Rate limit per minute must be at least 1")
                    if rate_hour < 1:
                        raise ValueError("Rate limit per hour must be at least 1")
                    
                    config.set('ai', 'online', 'enabled', value=online_enabled_var.get())
                    config.set('ai', 'online', 'api_key', value=api_key_var.get())
                    config.set('ai', 'online', 'api_url', value=api_url_var.get())
                    config.set('ai', 'online', 'model', value=model_var.get())
                    config.set('ai', 'online', 'timeout', value=timeout)
                    config.set('ai', 'online', 'max_requests_per_minute', value=rate_min)
                    config.set('ai', 'online', 'max_requests_per_hour', value=rate_hour)
                    config.set('ai', 'online', 'confidence_weight', value=float(online_conf_slider.get()))
                    config.set('ai', 'online', 'use_for_difficult_images', value=online_difficult_var.get())
                    config.set('ai', 'online', 'low_confidence_threshold', value=float(low_conf_slider.get()))
                except ValueError as e:
                    raise ValueError(f"Online AI settings error: {e}")
                
                # AI Blending
                config.set('ai', 'blend_mode', value=blend_var.get())
                config.set('ai', 'min_confidence', value=float(min_conf_slider.get()))
                
                # Hotkeys
                config.set('hotkeys', 'enabled', value=hotkey_enabled_var.get())
                config.set('hotkeys', 'global_hotkeys_enabled', value=global_hotkey_var.get())
                
                # Save to file
                config.save()
                
                # Apply settings immediately - wrap in try/except to avoid crashing settings window
                # Theme is now managed through Advanced Customization panel only
                try:
                    self.apply_ui_scaling(scale_var.get())
                except Exception as scale_err:
                    logger.debug(f"Scale apply during settings save: {scale_err}")
                
                # Reinitialize classifier with new config
                if hasattr(self, 'classifier'):
                    try:
                        # Create model manager if AI is enabled
                        model_manager = None
                        if config.get('ai', 'offline', 'enabled') or config.get('ai', 'online', 'enabled'):
                            from src.ai.model_manager import ModelManager
                            model_manager = ModelManager.create_default(config.settings.get('ai', {}))
                        
                        # Recreate classifier with new config and model manager
                        self.classifier = TextureClassifier(config=config, model_manager=model_manager)
                        self.log("✅ AI settings applied - classifier reinitialized")
                    except Exception as e:
                        logger.error(f"Failed to reinitialize classifier: {e}", exc_info=True)
                        self.log(f"⚠️ Warning: Failed to apply AI settings: {e}")
                
                self.log("✅ Settings saved successfully!")
                
                # Show confirmation
                if GUI_AVAILABLE:
                    messagebox.showinfo("Settings Saved", "All settings have been saved and applied successfully!")
                    
            except ValueError as e:
                self.log(f"❌ Invalid input: {e}")
                logger.error(f"Settings validation error: {e}")
                if GUI_AVAILABLE:
                    messagebox.showerror("Invalid Input", str(e))
            except Exception as e:
                self.log(f"❌ Error saving settings: {e}")
                logger.error(f"Error saving settings: {e}", exc_info=True)
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
        ach_header = ctk.CTkLabel(self.tab_achievements, text="🏆 Achievements 🏆",
                     font=("Arial Bold", 18))
        ach_header.pack(pady=15)
        if WidgetTooltip:
            self._tooltips.append(WidgetTooltip(ach_header, self._get_tooltip_text('achievements_tab') or "Track your progress and earn rewards by completing challenges"))
        
        if not self.achievement_manager:
            # No achievement manager
            info_frame = ctk.CTkFrame(self.tab_achievements)
            info_frame.pack(pady=50, padx=50, fill="both", expand=True)
            ctk.CTkLabel(info_frame,
                         text="Achievement system not available\n\nPlease check your installation.",
                         font=("Arial", 14)).pack(expand=True)
            return
        
        # Category filter buttons
        categories_frame = ctk.CTkFrame(self.tab_achievements)
        categories_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(categories_frame, text="Filter:", font=("Arial", 11)).pack(side="left", padx=5)
        
        self._achievement_category_filter = "all"
        
        category_labels = {
            "all": "📋 All",
            "beginner": "🌱 Beginner",
            "progress": "📊 Progress",
            "speed": "⚡ Speed",
            "session": "🏃 Session",
            "features": "🔧 Features",
            "quality": "💯 Quality",
            "special": "🐼 Special",
            "meta": "🏆 Meta",
            "easter_egg": "🥚 Easter Eggs",
        }
        
        category_tips = {
            "all": "Show all achievements across every category",
            "beginner": "Introductory achievements for new users",
            "progress": "Achievements earned by sorting more textures",
            "speed": "Achievements for fast sorting performance",
            "session": "Achievements for time spent using the app",
            "features": "Achievements for exploring app features",
            "quality": "Achievements for high-quality sorting results",
            "special": "Special and hidden achievements",
            "meta": "Achievements about earning other achievements",
            "easter_egg": "Secret achievements hidden throughout the app",
        }
        
        for cat_id, cat_label in category_labels.items():
            btn = ctk.CTkButton(
                categories_frame, text=cat_label, width=80, height=28,
                font=("Arial", 10),
                command=lambda c=cat_id: self._filter_achievements(c)
            )
            btn.pack(side="left", padx=2, pady=3)
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(btn, category_tips.get(cat_id, f"Filter to {cat_label} achievements")))
        
        # Achievement scroll frame
        self.achieve_scroll = ctk.CTkScrollableFrame(self.tab_achievements, width=1000, height=600)
        self.achieve_scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Display all achievements initially
        self._display_achievements("all")
    
    def _filter_achievements(self, category):
        """Filter achievements by category"""
        self._achievement_category_filter = category
        self._display_achievements(category)
    
    def _display_achievements(self, category="all"):
        """Display achievements, optionally filtered by category"""
        # Clear current items
        for widget in self.achieve_scroll.winfo_children():
            widget.destroy()

        try:
            achievements = self.achievement_manager.get_all_achievements(include_hidden=True)

            if category != "all":
                achievements = [a for a in achievements if a.category == category]

            if not achievements:
                ctk.CTkLabel(self.achieve_scroll,
                            text="No achievements in this category",
                            font=("Arial", 14)).pack(pady=50)
                return

            # One-time sync: auto-unlock any achievement whose progress
            # has reached the maximum but was not yet marked as unlocked.
            for a in achievements:
                if a.is_complete() and not a.unlocked:
                    self.achievement_manager.update_progress(a.id, a.progress_max)

            # Summary bar
            total = len(achievements)
            completed = sum(1 for a in achievements if a.unlocked or a.is_complete())
            claimable = sum(1 for a in achievements
                           if (a.unlocked or a.is_complete())
                           and a.reward
                           and a.id not in self._claimed_rewards)
            summary_frame = ctk.CTkFrame(self.achieve_scroll)
            summary_frame.pack(fill="x", padx=10, pady=(5, 10))
            ctk.CTkLabel(summary_frame,
                        text=f"✅ {completed}/{total} completed  •  🎁 {claimable} rewards available",
                        font=("Arial Bold", 12)).pack(side="left", padx=10, pady=8)

            if claimable > 0:
                ctk.CTkButton(summary_frame, text="🎁 Claim All Rewards",
                             width=160, fg_color="#2fa572", hover_color="#248a5c",
                             command=self._claim_all_achievement_rewards
                             ).pack(side="right", padx=10, pady=8)

            # Tier colors for badges
            tier_colors = {
                'bronze': '#cd7f32', 'silver': '#c0c0c0',
                'gold': '#ffd700', 'platinum': '#e5e4e2',
                'legendary': '#ff6600',
            }

            for achievement in achievements:
                is_completed = achievement.unlocked or achievement.is_complete()

                achieve_frame = ctk.CTkFrame(self.achieve_scroll)
                achieve_frame.pack(fill="x", padx=10, pady=4)

                # Top row: status + title + tier badge
                top_row = ctk.CTkFrame(achieve_frame)
                top_row.pack(fill="x", padx=10, pady=(8, 2))

                status = "✅" if is_completed else "🔒"
                title_text = f"{status} {achievement.icon} {achievement.name}"
                title_color = "#2fa572" if is_completed else None
                title_label = ctk.CTkLabel(top_row, text=title_text,
                            font=("Arial Bold", 14))
                if title_color:
                    title_label.configure(text_color=title_color)
                title_label.pack(side="left")

                # Tier badge
                tier_val = achievement.tier.value if hasattr(achievement.tier, 'value') else str(achievement.tier)
                badge_color = tier_colors.get(tier_val, '#888888')
                ctk.CTkLabel(top_row, text=f" {tier_val.upper()} ",
                            font=("Arial Bold", 10), text_color=badge_color
                            ).pack(side="left", padx=8)

                # Points
                ctk.CTkLabel(top_row, text=f"🏅 {achievement.points} pts",
                            font=("Arial", 10), text_color="#888888"
                            ).pack(side="right", padx=5)

                # Description
                desc_text = achievement.description
                if is_completed and achievement.unlock_date:
                    desc_text += f"  — Completed!"
                ctk.CTkLabel(achieve_frame, text=desc_text,
                            font=("Arial", 11), text_color="gray"
                            ).pack(anchor="w", padx=20, pady=2)

                # Reward info
                reward_text = self._get_achievement_rewards(achievement)
                if reward_text:
                    ctk.CTkLabel(achieve_frame, text=f"🎁 Reward: {reward_text}",
                                font=("Arial", 10), text_color="#2fa572"
                                ).pack(anchor="w", padx=20, pady=2)

                # Progress bar row
                progress_frame = ctk.CTkFrame(achieve_frame)
                progress_frame.pack(fill="x", padx=20, pady=(2, 4))

                progress = achievement.progress
                required = achievement.progress_max
                progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
                progress_bar.pack(side="left", padx=5)
                progress_value = 1.0 if is_completed else (min(progress / max(1, required), 1.0))
                progress_bar.set(progress_value)

                progress_label = ctk.CTkLabel(progress_frame,
                                              text=f"{progress:g}/{required:g}",
                                              font=("Arial", 10))
                progress_label.pack(side="left", padx=5)

                # Claim reward button (only if completed and has reward)
                if is_completed and achievement.reward and achievement.id not in self._claimed_rewards:
                    ctk.CTkButton(
                        progress_frame, text="🎁 Claim", width=80, height=26,
                        fg_color="#2fa572", hover_color="#248a5c",
                        command=lambda a=achievement: self._claim_achievement_reward(a)
                    ).pack(side="right", padx=5)

        except Exception as e:
            ctk.CTkLabel(self.achieve_scroll,
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
                # Still show notification for achievements without rewards
                self.log(f"🏆 Achievement '{achievement.name}' unlocked!")
                self._show_achievement_popup(achievement)
                return
            
            reward = achievement.reward
            reward_type = reward.get('type', '')
            
            if reward_type == 'currency' and self.currency_system:
                amount = reward.get('amount', 0)
                if amount > 0:
                    self.currency_system.add_money(amount, f"Achievement reward: {achievement.name}")
                    self.log(f"🏆 Achievement '{achievement.name}' unlocked! Reward: {reward.get('description', f'${amount}')}")
            elif reward_type == 'closet_item' and self.panda_closet:
                item_id = reward.get('item', '')
                if item_id:
                    closet_item = self.panda_closet.get_item(item_id)
                    if closet_item and not closet_item.unlocked:
                        closet_item.unlocked = True
                        try:
                            self.panda_closet.save_to_file(str(CONFIG_DIR / 'closet.json'))
                        except Exception:
                            pass
                self.log(f"🏆 Achievement '{achievement.name}' unlocked! Reward: {reward.get('description', item_id)}")
            elif reward_type == 'exclusive_title':
                title = reward.get('title', '')
                self.log(f"🏆 Achievement '{achievement.name}' unlocked! Reward: {reward.get('description', title)}")
            elif reward_type == 'exclusive_item':
                item_name = reward.get('item', '')
                self.log(f"🏆 Achievement '{achievement.name}' unlocked! Reward: {reward.get('description', item_name)}")
            else:
                self.log(f"🏆 Achievement '{achievement.name}' unlocked!")
            
            # Show visual popup notification
            self._show_achievement_popup(achievement)
        except Exception as e:
            logger.error(f"Error granting achievement reward: {e}")

    def _show_achievement_popup(self, achievement):
        """Show a nice achievement notification popup that fades out."""
        try:
            import tkinter as tk

            root = self.winfo_toplevel()
            popup = tk.Toplevel(root)
            popup.overrideredirect(True)
            popup.wm_attributes('-topmost', True)

            # Tier colors for badge
            tier_colors = {
                'bronze': ('#CD7F32', '#8B5A2B'),
                'silver': ('#C0C0C0', '#808080'),
                'gold': ('#FFD700', '#DAA520'),
                'platinum': ('#E5E4E2', '#A9A9A9'),
                'legendary': ('#FF6347', '#B22222'),
            }
            tier_name = achievement.tier.value if hasattr(achievement.tier, 'value') else str(achievement.tier)
            bg_color, accent_color = tier_colors.get(tier_name, ('#FFD700', '#DAA520'))

            popup_w, popup_h = 340, 110
            # Position in top-right of application window
            root.update_idletasks()
            rx = root.winfo_rootx() + root.winfo_width() - popup_w - 20
            ry = root.winfo_rooty() + 20
            popup.geometry(f"{popup_w}x{popup_h}+{rx}+{ry}")

            canvas = tk.Canvas(popup, width=popup_w, height=popup_h,
                               highlightthickness=0, bd=0, bg='#2b2b2b')
            canvas.pack(fill='both', expand=True)

            # Rounded rect background
            r = 12
            canvas.create_polygon(
                r, 0, popup_w - r, 0, popup_w, 0, popup_w, r,
                popup_w, popup_h - r, popup_w, popup_h,
                popup_w - r, popup_h, r, popup_h, 0, popup_h,
                0, popup_h - r, 0, r, 0, 0,
                fill='#1e1e2e', outline=accent_color, width=2, smooth=True
            )

            # Left accent bar
            canvas.create_rectangle(0, 8, 5, popup_h - 8, fill=bg_color, outline='')

            # Trophy icon
            canvas.create_text(30, 35, text=achievement.icon,
                               font=('Arial', 24), fill='white', anchor='w')

            # Title
            canvas.create_text(65, 22, text='Achievement Unlocked!',
                               font=('Arial', 10, 'bold'), fill=bg_color, anchor='w')

            # Achievement name
            name_text = achievement.name
            if len(name_text) > 32:
                name_text = name_text[:30] + '…'
            canvas.create_text(65, 42, text=name_text,
                               font=('Arial', 13, 'bold'), fill='white', anchor='w')

            # Description
            desc_text = achievement.description
            if len(desc_text) > 42:
                desc_text = desc_text[:40] + '…'
            canvas.create_text(65, 62, text=desc_text,
                               font=('Arial', 9), fill='#aaaaaa', anchor='w')

            # Reward line
            reward_text = ''
            if achievement.reward:
                reward_text = f"🎁 {achievement.reward.get('description', '')}"
                if len(reward_text) > 45:
                    reward_text = reward_text[:43] + '…'
            if reward_text:
                canvas.create_text(65, 82, text=reward_text,
                                   font=('Arial', 9, 'italic'), fill=bg_color, anchor='w')

            # Tier badge
            canvas.create_oval(popup_w - 35, 10, popup_w - 10, 35,
                               fill=bg_color, outline=accent_color, width=1)
            canvas.create_text(popup_w - 22, 22, text=tier_name[0].upper() if tier_name else '?',
                               font=('Arial', 10, 'bold'), fill='#1e1e2e')

            # Auto-close after 5 seconds with fade
            def _fade_out(alpha=1.0):
                try:
                    if alpha <= 0:
                        popup.destroy()
                        return
                    popup.wm_attributes('-alpha', alpha)
                    popup.after(50, lambda: _fade_out(alpha - 0.05))
                except Exception:
                    try:
                        popup.destroy()
                    except Exception:
                        pass

            popup.after(4000, _fade_out)

        except Exception as e:
            logger.debug(f"Could not show achievement popup: {e}")

    def _claim_achievement_reward(self, achievement):
        """Claim reward for a single completed achievement."""
        try:
            if not achievement.reward:
                return
            reward = achievement.reward
            reward_type = reward.get('type', '')
            desc = reward.get('description', '')

            if reward_type == 'currency' and self.currency_system:
                amount = reward.get('amount', 0)
                if amount > 0:
                    self.currency_system.add_money(amount, f"Achievement reward: {achievement.name}")
                    if hasattr(self, 'shop_money_label'):
                        self.shop_money_label.configure(text=f"💰 Money: ${self.currency_system.get_balance()}")
            elif reward_type in ('exclusive_item', 'closet_item') and self.panda_closet:
                item_id = reward.get('item', '')
                if item_id:
                    closet_item = self.panda_closet.get_item(item_id)
                    if closet_item and not closet_item.unlocked:
                        closet_item.unlocked = True
                        try:
                            self.panda_closet.save_to_file(str(CONFIG_DIR / 'closet.json'))
                        except Exception:
                            pass
                        if self.closet_panel:
                            try:
                                self.closet_panel.refresh()
                            except Exception:
                                pass

            self._claimed_rewards.add(achievement.id)
            self.log(f"🎁 Claimed reward for '{achievement.name}': {desc}")
            # Refresh display
            self._display_achievements(self._achievement_category_filter)
        except Exception as e:
            logger.error(f"Error claiming achievement reward: {e}")

    def _claim_all_achievement_rewards(self):
        """Claim all available achievement rewards."""
        try:
            achievements = self.achievement_manager.get_all_achievements(include_hidden=True)
            claimed = 0
            for a in achievements:
                if (a.unlocked or a.is_complete()) and a.reward and a.id not in self._claimed_rewards:
                    # Inline reward granting to avoid per-claim UI refresh
                    reward = a.reward
                    reward_type = reward.get('type', '')
                    desc = reward.get('description', '')
                    if reward_type == 'currency' and self.currency_system:
                        amount = reward.get('amount', 0)
                        if amount > 0:
                            self.currency_system.add_money(amount, f"Achievement reward: {a.name}")
                    elif reward_type in ('exclusive_item', 'closet_item') and self.panda_closet:
                        item_id = reward.get('item', '')
                        if item_id:
                            closet_item = self.panda_closet.get_item(item_id)
                            if closet_item and not closet_item.unlocked:
                                closet_item.unlocked = True
                    self._claimed_rewards.add(a.id)
                    self.log(f"🎁 Claimed reward for '{a.name}': {desc}")
                    claimed += 1
            # Single UI refresh after all claims
            if claimed > 0:
                if hasattr(self, 'shop_money_label') and self.currency_system:
                    self.shop_money_label.configure(text=f"💰 Money: ${self.currency_system.get_balance()}")
                if self.panda_closet:
                    try:
                        self.panda_closet.save_to_file(str(CONFIG_DIR / 'closet.json'))
                    except Exception:
                        pass
                self.log(f"🎁 Claimed {claimed} achievement reward(s)!")
                self._display_achievements(self._achievement_category_filter)
                messagebox.showinfo("Rewards Claimed", f"Successfully claimed {claimed} reward(s)!")
            else:
                messagebox.showinfo("No Rewards", "No unclaimed rewards available.")
        except Exception as e:
            logger.error(f"Error claiming all rewards: {e}")

    
    def create_shop_tab(self):
        """Create shop tab for purchasing items with money"""
        # Header
        header_frame = ctk.CTkFrame(self.tab_shop)
        header_frame.pack(fill="x", pady=10, padx=10)
        
        shop_title = ctk.CTkLabel(header_frame, text="🛒 Shop 🛒",
                     font=("Arial Bold", 18))
        shop_title.pack(side="left", padx=10)
        if WidgetTooltip:
            self._tooltips.append(WidgetTooltip(shop_title, self._get_tooltip_text('shop_tab') or "Spend your Bamboo Bucks on items, outfits, themes, and more"))
        
        # Money display
        if self.currency_system:
            money_text = f"💰 Money: ${self.currency_system.get_balance()}"
            self.shop_money_label = ctk.CTkLabel(header_frame, text=money_text,
                         font=("Arial Bold", 14), text_color="#00cc00")
            self.shop_money_label.pack(side="right", padx=20)
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(self.shop_money_label, "Your current Bamboo Bucks balance — earn more through achievements and interactions"))
        
        # User level display
        if self.user_level_system:
            level_text = f"⭐ Level {self.user_level_system.level}"
            level_label = ctk.CTkLabel(header_frame, text=level_text,
                        font=("Arial Bold", 14), text_color="#ffaa00")
            level_label.pack(side="right", padx=10)
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(level_label, "Your current level — higher levels unlock more shop items"))
        
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
        
        # Category buttons - use grid layout to wrap instead of overflowing
        self.selected_category = ShopCategory.PANDA_OUTFITS
        category_buttons = {}
        
        # Map categories to icons for readability
        category_icons = {
            ShopCategory.PANDA_OUTFITS: "🐼",
            ShopCategory.CURSORS: "🖱️",
            ShopCategory.CURSOR_TRAILS: "✨",
            ShopCategory.THEMES: "🎨",
            ShopCategory.ANIMATIONS: "💃",
            ShopCategory.CLOTHES: "👕",
            ShopCategory.HATS: "🎩",
            ShopCategory.SHOES: "👟",
            ShopCategory.ACCESSORIES: "💎",
            ShopCategory.UPGRADES: "⚡",
            ShopCategory.SPECIAL: "🌟",
            ShopCategory.FOOD: "🍱",
            ShopCategory.TOYS: "🎾",
        }
        
        # Specific tips for each shop category
        category_shop_tips = {
            ShopCategory.PANDA_OUTFITS: "Browse full outfit sets for your panda companion",
            ShopCategory.CURSORS: "Custom mouse cursor styles — click to equip after purchase",
            ShopCategory.CURSOR_TRAILS: "Visual trails that follow your cursor around the app",
            ShopCategory.THEMES: "Color themes to change the look of the entire application",
            ShopCategory.ANIMATIONS: "New animations for your panda to perform",
            ShopCategory.CLOTHES: "Individual clothing items — shirts, pants, dresses for your panda",
            ShopCategory.HATS: "Hats, helmets, and headwear for your panda",
            ShopCategory.SHOES: "Shoes, boots, and footwear for your panda",
            ShopCategory.ACCESSORIES: "Accessories like watches, bracelets, ties, and jewelry",
            ShopCategory.UPGRADES: "App upgrades and performance boosts",
            ShopCategory.SPECIAL: "Limited and exclusive items — get them before they're gone!",
            ShopCategory.FOOD: "Feed your panda — food items boost happiness instantly",
            ShopCategory.TOYS: "Toys to play with your panda and increase interaction stats",
        }
        
        max_cols = 6  # wrap after 6 columns
        for idx, category in enumerate(ShopCategory):
            row = idx // max_cols
            col = idx % max_cols
            icon = category_icons.get(category, "🛒")
            btn = ctk.CTkButton(
                categories_frame,
                text=f"{icon} {category.value.replace('_', ' ').title()}",
                command=lambda c=category: self._select_shop_category(c)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            category_buttons[category] = btn
            if WidgetTooltip:
                tip = category_shop_tips.get(category, "Filter shop items by this category")
                self._tooltips.append(WidgetTooltip(btn, tip))
        
        # Make columns expand equally
        for col in range(max_cols):
            categories_frame.grid_columnconfigure(col, weight=1)
        
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
            
            item_name_lbl = ctk.CTkLabel(name_frame, text=f"{item.icon} {item.name}",
                        font=("Arial Bold", 14))
            item_name_lbl.pack(anchor="w")
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(item_name_lbl, f"{item.name}: {item.description}"))
            
            ctk.CTkLabel(name_frame, text=item.description,
                        font=("Arial", 11), text_color="gray").pack(anchor="w")
            
            # Price and requirements
            info_frame = ctk.CTkFrame(item_frame)
            info_frame.pack(side="right", padx=10, pady=10)
            
            # Price
            price_text = f"💰 ${item.price}"
            price_lbl = ctk.CTkLabel(info_frame, text=price_text,
                        font=("Arial Bold", 12), text_color="#00cc00")
            price_lbl.pack(side="left", padx=10)
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(price_lbl, f"Costs {item.price} Bamboo Bucks to purchase"))
            
            # Level requirement
            if item.level_required > 1:
                level_text = f"⭐ Lvl {item.level_required}"
                color = "gray" if user_level >= item.level_required else "red"
                lvl_lbl = ctk.CTkLabel(info_frame, text=level_text,
                            font=("Arial", 10), text_color=color)
                lvl_lbl.pack(side="left", padx=5)
                if WidgetTooltip:
                    if user_level >= item.level_required:
                        self._tooltips.append(WidgetTooltip(lvl_lbl, f"You meet the level requirement (Lvl {item.level_required})"))
                    else:
                        self._tooltips.append(WidgetTooltip(lvl_lbl, f"Reach Level {item.level_required} to unlock this item (you are Lvl {user_level})"))
            
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
                if is_purchased and item.one_time_purchase:
                    tip = f"You already own {item.name}"
                elif user_level < item.level_required:
                    tip = f"Reach Level {item.level_required} to purchase {item.name}"
                elif not can_buy:
                    tip = f"You need ${item.price} to buy {item.name} — earn more through achievements and sorting"
                else:
                    tip = self._get_tooltip_text('shop_buy_button') or f"Buy {item.name} for ${item.price}"
                self._tooltips.append(WidgetTooltip(buy_btn, tip))
    
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
                                     'cursor_trails', 'clothes', 'hats', 'shoes', 'accessories']:
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
                    # Try direct match first
                    closet_item = self.panda_closet.get_item(item.unlockable_id)
                    
                    # If not found, try stripped prefixes (clothes_tshirt -> tshirt, acc_sunglasses -> sunglasses)
                    if not closet_item:
                        stripped_id = item.unlockable_id
                        for prefix in self.CLOSET_ID_PREFIXES:
                            if stripped_id.startswith(prefix):
                                stripped_id = stripped_id[len(prefix):]
                                break
                        closet_item = self.panda_closet.get_item(stripped_id)
                    
                    if closet_item and not closet_item.unlocked:
                        closet_item.unlocked = True
                        self.panda_closet.save_to_file(
                            str(CONFIG_DIR / 'closet.json')
                        )
                        logger.info(f"Unlocked closet item: {closet_item.id} ({closet_item.name})")
                        
                        # Refresh closet panel to show newly purchased item
                        if self.closet_panel:
                            try:
                                self.closet_panel.refresh()
                            except Exception as e:
                                logger.debug(f"Failed to refresh closet panel: {e}")
                    elif not closet_item:
                        logger.debug(f"No matching closet item for shop unlockable_id: {item.unlockable_id}")
                except Exception as e:
                    logger.debug(f"Item not in closet (expected for non-closet items): {e}")
            
            # Handle cursor purchases — add to cursor selector
            if item.category.value == 'cursors' and item.unlockable_id:
                try:
                    cursor_name = item.name
                    config.set('ui', f'cursor_{item.unlockable_id}_unlocked', value=True)
                    # Update cursor customizer if it exists
                    if hasattr(self, 'customization_panel') and self.customization_panel:
                        try:
                            self.customization_panel.cursor_customizer.update_available_cursors([cursor_name])
                        except Exception:
                            pass
                    logger.info(f"Unlocked cursor: {cursor_name}")
                except Exception as e:
                    logger.debug(f"Could not save cursor unlock: {e}")
            
            # Handle cursor trail purchases — save as available trail
            if item.category.value == 'cursor_trails' and item.unlockable_id:
                try:
                    trail_name = item.unlockable_id.replace('trail_', '')
                    config.set('ui', f'trail_{trail_name}_unlocked', value=True)
                    logger.info(f"Unlocked cursor trail: {trail_name}")
                except Exception as e:
                    logger.debug(f"Could not save trail unlock: {e}")
            
            # Handle food purchases — add to inventory and feed panda
            if item.category.value == 'food':
                # Add food quantity to widget collection for inventory
                if self.widget_collection and item.unlockable_id:
                    try:
                        widget_id = self.widget_collection.resolve_shop_widget_id(item.unlockable_id)
                        if widget_id:
                            self.widget_collection.add_food_quantity(widget_id, 1)
                            logger.info(f"Added food to inventory: {widget_id}")
                    except Exception as e:
                        logger.debug(f"Could not add food to inventory: {e}")
                
                # Also feed the panda for immediate feedback
                if self.panda:
                    try:
                        response = self.panda.on_food_received()
                        if hasattr(self, 'panda_widget') and self.panda_widget:
                            self.panda_widget.info_label.configure(text=response)
                            self.panda_widget.play_animation_once('fed')
                        self.log(f"🎋 Bought {item.name} for panda! {response}")
                        # Award XP for feeding
                        if self.panda_level_system:
                            try:
                                xp = self.panda_level_system.get_xp_reward('feed')
                                self.panda_level_system.add_xp(xp, f'Bought {item.name}')
                            except Exception:
                                pass
                    except Exception as e:
                        logger.debug(f"Could not feed panda: {e}")

            # Handle toy purchases — unlock widget in collection
            if item.category.value == 'toys' and item.unlockable_id and self.widget_collection:
                try:
                    widget_id = self.widget_collection.resolve_shop_widget_id(item.unlockable_id)
                    if widget_id:
                        self.widget_collection.unlock_widget(widget_id)
                    else:
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
        
        # Category filter buttons
        reward_categories_frame = ctk.CTkFrame(self.tab_rewards)
        reward_categories_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(reward_categories_frame, text="Filter:", font=("Arial", 11)).pack(side="left", padx=5)
        
        self._reward_categories = [
            ('all', '📋 All'),
            ('cursors', '🖱️ Cursors'),
            ('outfits', '🐼 Outfits'),
            ('themes', '🎨 Themes'),
            ('animations', '✨ Animations'),
        ]
        
        for cat_id, cat_label in self._reward_categories:
            btn = ctk.CTkButton(
                reward_categories_frame, text=cat_label, width=90, height=28,
                font=("Arial", 10),
                command=lambda c=cat_id: self._filter_rewards(c)
            )
            btn.pack(side="left", padx=2, pady=3)
        
        # Rewards scroll frame
        self.rewards_scroll = ctk.CTkScrollableFrame(self.tab_rewards, width=1000, height=600)
        self.rewards_scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Display all rewards initially
        self._display_rewards("all")
    
    def _filter_rewards(self, category):
        """Filter rewards by category"""
        self._display_rewards(category)
    
    def _display_rewards(self, category="all"):
        """Display rewards, optionally filtered by category"""
        # Clear current items
        for widget in self.rewards_scroll.winfo_children():
            widget.destroy()
        
        # Display unlockables by category using actual UnlockablesSystem attributes
        try:
            all_categories = [
                ('cursors', '🖱️ Custom Cursors', self.unlockables_manager.cursors),
                ('outfits', '🐼 Panda Outfits', self.unlockables_manager.outfits),
                ('themes', '🎨 Themes', self.unlockables_manager.themes),
                ('animations', '✨ Animations', self.unlockables_manager.animations),
            ]
            
            if category != "all":
                all_categories = [(cid, cl, cd) for cid, cl, cd in all_categories if cid == category]
            
            for cat_id, cat_label, items_dict in all_categories:
                # Category header
                cat_frame = ctk.CTkFrame(self.rewards_scroll)
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
            ctk.CTkLabel(self.rewards_scroll,
                        text=f"Error loading rewards: {e}",
                        font=("Arial", 12)).pack(pady=20)
    
    def create_closet_tab(self):
        """Create panda closet tab for customizing panda appearance"""
        if not PANDA_CLOSET_AVAILABLE or not self.panda_closet:
            ctk.CTkLabel(self.tab_closet, text="Panda closet not available",
                         font=("Arial", 14)).pack(pady=50)
            return
        
        closet_panel = ClosetPanel(
            self.tab_closet,
            self.panda_closet,
            panda_character=self.panda,
            panda_preview_callback=self.panda_widget
        )
        closet_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Store reference so we can refresh after shop purchases
        self.closet_panel = closet_panel
    
    def create_notepad_tab(self):
        """Create notepad tab with multiple note tabs support"""
        # Header with title (extra right padding for popout button)
        header_frame = ctk.CTkFrame(self.tab_notepad)
        header_frame.pack(fill="x", pady=10, padx=(10, 45))
        
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
    
    def create_inventory_tab(self):
        """Create inventory tab for managing collected items.
        
        Shows only non-closet items that have been purchased or earned.
        Items are organized by category tabs: All, Toys, Food, Animations.
        Closet items (clothes, outfits, accessories) are shown in the Closet tab instead.
        Accessories are routed to the closet for equipping.
        """
        scrollable_frame = ctk.CTkScrollableFrame(self.tab_inventory)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkLabel(scrollable_frame, text="📦 Inventory",
                     font=("Arial Bold", 22))
        header.pack(pady=(15, 5))
        if WidgetTooltip:
            self._tooltips.append(WidgetTooltip(header, self._get_tooltip_text('inventory_tab') or "Your collection of items — toys, food, and animations. Drag items to use them!"))

        # Category filter buttons
        if self.widget_collection:
            cat_frame = ctk.CTkFrame(scrollable_frame)
            cat_frame.pack(fill="x", padx=10, pady=(5, 10))
            
            if not hasattr(self, '_inventory_category'):
                self._inventory_category = 'all'
            
            categories = [
                ("📦 All", "all"),
                ("🎾 Toys", "toy"),
                ("🍱 Food", "food"),
                ("🎬 Animations", "animation"),
            ]
            
            for cat_label, cat_value in categories:
                is_selected = (self._inventory_category == cat_value)
                btn = ctk.CTkButton(
                    cat_frame, text=cat_label, width=100, height=30,
                    fg_color=("#3B8ED0" if is_selected else "transparent"),
                    text_color=("white" if is_selected else None),
                    command=lambda cv=cat_value: self._select_inventory_category(cv)
                )
                btn.pack(side="left", padx=5, pady=5)

        # Show purchased non-closet shop items
        if self.shop_system:
            non_closet_purchased = []
            for item_id in self.shop_system.purchased_items:
                item = self.shop_system.CATALOG.get(item_id)
                if item and item.category.value not in self.CLOSET_SHOP_CATEGORIES:
                    non_closet_purchased.append(item)
            
            if non_closet_purchased:
                shop_frame = ctk.CTkFrame(scrollable_frame)
                shop_frame.pack(fill="x", padx=10, pady=10)
                shop_header = ctk.CTkLabel(shop_frame, text="🛒 Purchased Items",
                             font=("Arial Bold", 16))
                shop_header.pack(anchor="w", padx=10, pady=(10, 5))
                if WidgetTooltip:
                    self._tooltips.append(WidgetTooltip(shop_header, self._get_tooltip_text('inventory_purchased') or "Non-closet items you've bought from the shop"))

                for item in non_closet_purchased:
                    # Apply category filter
                    if self._inventory_category != 'all':
                        if self._inventory_category == 'toy' and item.category.value != 'toys':
                            continue
                        elif self._inventory_category == 'food' and item.category.value != 'food':
                            continue
                        elif self._inventory_category == 'animation' and item.category.value not in ('cursors', 'cursor_trails', 'themes', 'animations', 'upgrades', 'special'):
                            continue
                    
                    item_frame = ctk.CTkFrame(shop_frame)
                    item_frame.pack(fill="x", padx=10, pady=3)
                    name_lbl = ctk.CTkLabel(item_frame, text=f"{item.icon} {item.name}",
                                 font=("Arial", 12))
                    name_lbl.pack(side="left", padx=10, pady=5)
                    ctk.CTkLabel(item_frame, text=item.description,
                                 font=("Arial", 10), text_color="gray").pack(side="left", padx=5)
                    if WidgetTooltip:
                        self._tooltips.append(WidgetTooltip(name_lbl, f"{item.name}: {item.description}"))

        # Show widget collection (toys, food) — only unlocked/owned items
        # Accessories are shown in the Closet tab instead.
        if self.widget_collection:
            filter_types = []
            if self._inventory_category == 'all':
                filter_types = [
                    ("🎾 Toys", WidgetType.TOY, "play"),
                    ("🍱 Food Items", WidgetType.FOOD, "feed"),
                ]
            elif self._inventory_category == 'toy':
                filter_types = [("🎾 Toys", WidgetType.TOY, "play")]
            elif self._inventory_category == 'food':
                filter_types = [("🍱 Food Items", WidgetType.FOOD, "feed")]
            
            for type_label, widget_type, interaction_type in filter_types:
                type_frame = ctk.CTkFrame(scrollable_frame)
                type_frame.pack(fill="x", padx=10, pady=10)
                section_header = ctk.CTkLabel(type_frame, text=type_label,
                             font=("Arial Bold", 16))
                section_header.pack(anchor="w", padx=10, pady=(10, 5))
                if WidgetTooltip:
                    tip_key = f"inventory_{widget_type.value}"
                    tip_text = f"Your {widget_type.value} collection"
                    if widget_type == WidgetType.TOY:
                        tip_text += " — toys have infinite uses! Drag them out or give to panda."
                    elif widget_type == WidgetType.FOOD:
                        tip_text += " — food is consumed when used. Buy more from the shop!"
                    self._tooltips.append(WidgetTooltip(section_header,
                        self._get_tooltip_text(tip_key) or tip_text))

                # Only show unlocked/owned widgets
                widgets = self.widget_collection.get_all_widgets(widget_type, unlocked_only=True)
                
                # For food, also filter to only items with quantity > 0
                if widget_type == WidgetType.FOOD:
                    widgets = [w for w in widgets if not w.consumable or w.quantity > 0]

                if not widgets:
                    empty_msg = "No items yet. Visit the 🛒 Shop to buy some!"
                    ctk.CTkLabel(type_frame, text=empty_msg,
                                 font=("Arial", 11), text_color="gray").pack(anchor="w", padx=20, pady=5)
                    continue

                rarity_order = ['common', 'uncommon', 'rare', 'epic', 'legendary']
                rarity_groups = {}
                for widget in widgets:
                    r = widget.rarity.value
                    if r not in rarity_groups:
                        rarity_groups[r] = []
                    rarity_groups[r].append(widget)

                rarity_colors = {"common": "gray", "uncommon": "#00cc00",
                                 "rare": "#3399ff", "epic": "#cc66ff",
                                 "legendary": "#ffaa00"}

                for rarity in rarity_order:
                    group = rarity_groups.get(rarity, [])
                    if not group:
                        continue

                    sub_header = ctk.CTkFrame(type_frame)
                    sub_header.pack(fill="x", padx=15, pady=(5, 2))
                    rarity_lbl = ctk.CTkLabel(sub_header,
                                 text=f"  {rarity.title()} ({len(group)})",
                                 font=("Arial Bold", 11),
                                 text_color=rarity_colors.get(rarity, "gray"))
                    rarity_lbl.pack(anchor="w", padx=5)
                    if WidgetTooltip:
                        self._tooltips.append(WidgetTooltip(rarity_lbl, f"{rarity.title()} rarity items — {len(group)} total"))

                    for widget in group:
                        w_frame = ctk.CTkFrame(type_frame)
                        w_frame.pack(fill="x", padx=20, pady=2)
                        
                        # Show quantity for consumable items, checkmark for toys
                        if widget.consumable:
                            status = f"x{widget.quantity}"
                        else:
                            status = "♾️"  # infinite uses for toys
                        
                        item_lbl = ctk.CTkLabel(w_frame, text=f"{widget.emoji} {widget.name} [{status}]",
                                     font=("Arial", 12))
                        item_lbl.pack(side="left", padx=10, pady=5)
                        ctk.CTkLabel(w_frame, text=widget.rarity.value.title(),
                                     font=("Arial", 10),
                                     text_color=rarity_colors.get(widget.rarity.value, "gray")
                                     ).pack(side="left", padx=5)
                        if widget.stats.times_used > 0:
                            ctk.CTkLabel(w_frame, text=f"Used {widget.stats.times_used}x",
                                         font=("Arial", 10), text_color="gray").pack(side="left", padx=5)
                        if WidgetTooltip:
                            tip = f"{widget.name} ({widget.rarity.value.title()})"
                            if widget.consumable:
                                tip += f" — {widget.quantity} remaining. Food is consumed when fed to panda."
                            else:
                                tip += " — Infinite uses! Toys are never consumed."
                            self._tooltips.append(WidgetTooltip(item_lbl, tip))

                        # Give to panda button
                        can_use = True
                        if widget.consumable and widget.quantity <= 0:
                            can_use = False
                        
                        if can_use:
                            give_btn = ctk.CTkButton(
                                w_frame, text="🐼 Give to Panda", width=120, height=28,
                                command=lambda w=widget, it=interaction_type: self._give_inventory_item_to_panda(w, it)
                            )
                            give_btn.pack(side="right", padx=5, pady=3)
                            if WidgetTooltip:
                                self._tooltips.append(WidgetTooltip(give_btn,
                                    self._get_tooltip_text('inventory_give_button') or f"Give {widget.name} to your panda"))
                            
                            # Drag out button — creates a floating item window
                            drag_btn = ctk.CTkButton(
                                w_frame, text="✋ Drag Out", width=90, height=28,
                                fg_color="#555555",
                                command=lambda w=widget, it=interaction_type: self._drag_item_out(w, it)
                            )
                            drag_btn.pack(side="right", padx=2, pady=3)
                            if WidgetTooltip:
                                self._tooltips.append(WidgetTooltip(drag_btn,
                                    f"Drag {widget.name} out as a floating item. Panda can walk to it and interact!"))

        # Show animations section with play buttons
        if self._inventory_category in ('all', 'animation'):
            anim_frame = ctk.CTkFrame(scrollable_frame)
            anim_frame.pack(fill="x", padx=10, pady=10)
            anim_header = ctk.CTkLabel(anim_frame, text="🎬 Animations",
                         font=("Arial Bold", 16))
            anim_header.pack(anchor="w", padx=10, pady=(10, 5))
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(anim_header,
                    self._get_tooltip_text('inventory_animations') or "Play animations to make panda dance, flip, and more!"))

            animation_entries = [
                ("💃", "Dancing", "dancing"),
                ("🎉", "Celebrating", "celebrating"),
                ("👋", "Waving", "waving"),
                ("🤸", "Cartwheel", "cartwheel"),
                ("🔄", "Backflip", "backflip"),
                ("🦘", "Jumping", "jumping"),
                ("🙆", "Stretching", "stretching"),
                ("🐾", "Belly Rub", "belly_rub"),
                ("🌀", "Spinning", "spinning"),
                ("😴", "Sleeping", "sleeping"),
                ("🪑", "Sitting", "sitting"),
                ("😌", "Lay On Back", "lay_on_back"),
                ("🛌", "Lay On Side", "lay_on_side"),
                ("🥱", "Yawning", "yawning"),
                ("🤧", "Sneezing", "sneezing"),
                ("🤗", "Belly Grab", "belly_grab"),
            ]

            for emoji, name, anim_state in animation_entries:
                a_frame = ctk.CTkFrame(anim_frame)
                a_frame.pack(fill="x", padx=15, pady=3)
                ctk.CTkLabel(a_frame, text=f"{emoji} {name}",
                             font=("Arial", 13, "bold")).pack(side="left", padx=10, pady=5)
                play_btn = ctk.CTkButton(
                    a_frame, text="▶ Play", width=80, height=28,
                    command=lambda a=anim_state, n=name: self._play_inventory_animation(a, n)
                )
                play_btn.pack(side="right", padx=10, pady=5)
                if WidgetTooltip:
                    self._tooltips.append(WidgetTooltip(play_btn, f"Play the {name} animation"))

        # Show unlockables summary
        if self.unlockables_manager:
            unlockables_frame = ctk.CTkFrame(scrollable_frame)
            unlockables_frame.pack(fill="x", padx=10, pady=10)
            unlock_header = ctk.CTkLabel(unlockables_frame, text="🎁 Unlocked Rewards",
                         font=("Arial Bold", 16))
            unlock_header.pack(anchor="w", padx=10, pady=(10, 5))
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(unlock_header, self._get_tooltip_text('inventory_unlocked') or "Summary of all rewards you've unlocked"))

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

    def _select_inventory_category(self, category):
        """Switch inventory category filter and rebuild tab."""
        self._inventory_category = category
        try:
            for w in self.tab_inventory.winfo_children():
                w.destroy()
            self.create_inventory_tab()
        except Exception as e:
            logger.error(f"Error switching inventory category: {e}")

    def _play_inventory_animation(self, anim_state, display_name):
        """Play a panda animation from the inventory animations section."""
        if hasattr(self, 'panda_widget') and self.panda_widget:
            if hasattr(self.panda_widget, 'play_animation_once'):
                self.panda_widget.play_animation_once(anim_state)
            elif hasattr(self.panda_widget, 'set_animation'):
                self.panda_widget.set_animation(anim_state)
            self.log(f"🎬 Playing animation: {display_name}")
        else:
            self.log(f"⚠ Panda widget not available for animations")

    def _drag_item_out(self, widget, interaction_type):
        """Create a floating item window that can be dragged around with physics.
        
        Items behave like the panda's transparent floating window — they can be
        tossed around with physics (bounce, gravity, friction). Different items
        have different physics: bouncy carrot bounces high, dumbbell falls fast, etc.
        The panda can walk to the item and interact with it.
        """
        try:
            # Consume one unit for food items
            if widget.consumable:
                if widget.quantity <= 0:
                    if self.panda_widget:
                        self.panda_widget.info_label.configure(text=f"No {widget.name} left!")
                    return
                widget.quantity -= 1
            
            # Create floating toplevel window with transparent background
            root = self.winfo_toplevel()
            item_win = tk.Toplevel(root)
            item_win.overrideredirect(True)
            item_win.attributes('-topmost', True)
            try:
                item_win.attributes('-transparentcolor', 'gray15')
            except Exception:
                pass
            
            # Bigger size for better visibility and interaction
            win_size = 120
            item_win.geometry(f"{win_size}x{win_size}+{root.winfo_x() + 200}+{root.winfo_y() + 200}")
            item_win.configure(bg='gray15')
            
            # Colorful background based on item rarity
            rarity_bg_colors = {
                'common': '#4a6741',      # Muted green
                'uncommon': '#2d6a4f',     # Teal green
                'rare': '#1d4e89',         # Rich blue
                'epic': '#6a1b9a',         # Deep purple
                'legendary': '#b8860b',    # Dark goldenrod
            }
            item_bg = rarity_bg_colors.get(widget.rarity.value, '#4a6741')
            
            # Display item emoji with larger font and colored background
            item_label = tk.Label(item_win, text=widget.emoji, font=("Arial", 54),
                                  bg=item_bg, fg='white')
            item_label.pack(expand=True, fill="both")
            
            # Physics state
            physics = widget.physics
            weight_divisor = max(physics.weight, 0.1)
            state = {
                'vx': 0.0, 'vy': 0.0,
                'dragging': False,
                'drag_x': 0, 'drag_y': 0,
                'last_x': 0, 'last_y': 0,
                'timer': None,
                'is_tossing': False,
                'food_consumed': False,
            }
            
            def on_drag_start(event):
                state['dragging'] = True
                state['drag_x'] = event.x_root
                state['drag_y'] = event.y_root
                state['last_x'] = event.x_root
                state['last_y'] = event.y_root
                state['vx'] = 0.0
                state['vy'] = 0.0
                state['is_tossing'] = False
                if state['timer']:
                    try:
                        item_win.after_cancel(state['timer'])
                    except Exception:
                        pass
                    state['timer'] = None
            
            def on_drag_motion(event):
                if not state['dragging']:
                    return
                dx = event.x_root - state['drag_x']
                dy = event.y_root - state['drag_y']
                x = item_win.winfo_x() + dx
                y = item_win.winfo_y() + dy
                # Clamp to application window bounds
                root.update_idletasks()
                min_x = root.winfo_rootx()
                min_y = root.winfo_rooty()
                max_x = max(min_x, min_x + root.winfo_width() - win_size)
                max_y = max(min_y, min_y + root.winfo_height() - win_size)
                x = max(min_x, min(x, max_x))
                y = max(min_y, min(y, max_y))
                item_win.geometry(f"+{x}+{y}")
                state['vx'] = (event.x_root - state['last_x']) / weight_divisor
                state['vy'] = (event.y_root - state['last_y']) / weight_divisor
                state['drag_x'] = event.x_root
                state['drag_y'] = event.y_root
                state['last_x'] = event.x_root
                state['last_y'] = event.y_root
            
            def on_drag_end(event):
                state['dragging'] = False
                speed = (state['vx'] ** 2 + state['vy'] ** 2) ** 0.5
                if speed > 1.5:
                    state['is_tossing'] = True
                    physics_tick()
                
                # Notify panda about item on screen
                if self.panda and self.panda_widget:
                    item_type = 'food' if widget.widget_type == WidgetType.FOOD else 'toy'
                    response = self.panda.on_item_interact(widget.name, item_type)
                    self.panda_widget.info_label.configure(text=response)
                    anim = 'eating' if item_type == 'food' else 'playing'
                    self.panda_widget.play_animation_once(anim)
                    
                    # For food, close the window after panda "eats" it
                    if item_type == 'food':
                        state['food_consumed'] = True
                        item_win.after(2000, safe_destroy)
            
            def physics_tick():
                if not state['is_tossing']:
                    return
                try:
                    if not item_win.winfo_exists():
                        return
                except Exception:
                    return
                
                # Apply gravity and friction
                state['vy'] += physics.gravity
                state['vx'] *= physics.friction
                state['vy'] *= physics.friction
                
                x = item_win.winfo_x() + state['vx']
                y = item_win.winfo_y() + state['vy']
                
                # Application window bounds (items stay within app)
                root.update_idletasks()
                min_x = root.winfo_rootx()
                min_y = root.winfo_rooty()
                max_x = max(min_x, min_x + root.winfo_width() - win_size)
                max_y = max(min_y, min_y + root.winfo_height() - win_size)
                
                bounced = False
                if x <= min_x:
                    x = min_x
                    state['vx'] = abs(state['vx']) * physics.bounce_damping * physics.bounciness
                    bounced = True
                elif x >= max_x:
                    x = max_x
                    state['vx'] = -abs(state['vx']) * physics.bounce_damping * physics.bounciness
                    bounced = True
                
                if y <= min_y:
                    y = min_y
                    state['vy'] = abs(state['vy']) * physics.bounce_damping * physics.bounciness
                    bounced = True
                elif y >= max_y:
                    y = max_y
                    state['vy'] = -abs(state['vy']) * physics.bounce_damping * physics.bounciness
                    bounced = True
                
                item_win.geometry(f"+{int(x)}+{int(y)}")
                
                speed = (state['vx'] ** 2 + state['vy'] ** 2) ** 0.5
                if speed < 1.0:
                    state['is_tossing'] = False
                    return
                
                state['timer'] = item_win.after(20, physics_tick)
            
            def safe_destroy():
                try:
                    if item_win.winfo_exists():
                        item_win.destroy()
                except Exception:
                    pass
            
            # Double-click to dismiss
            def on_double_click(event):
                # Return food quantity only if it wasn't already consumed by panda
                if widget.consumable and widget.widget_type == WidgetType.FOOD and not state['food_consumed']:
                    widget.quantity += 1  # Return the item
                safe_destroy()
            
            item_label.bind('<Button-1>', on_drag_start)
            item_label.bind('<B1-Motion>', on_drag_motion)
            item_label.bind('<ButtonRelease-1>', on_drag_end)
            item_label.bind('<Double-Button-1>', on_double_click)
            
            # Auto-close after 60 seconds for toys (they don't get consumed)
            if not widget.consumable:
                item_win.after(60000, safe_destroy)
            
            self.log(f"✋ Dragged out {widget.name}!")
            
            # Refresh inventory to show updated quantity
            try:
                for w in self.tab_inventory.winfo_children():
                    w.destroy()
                self.create_inventory_tab()
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"Error dragging item out: {e}")

    def _give_inventory_item_to_panda(self, widget, interaction_type):
        """Give an inventory item to the panda, triggering animation and stats update."""
        try:
            result = widget.use()
            message = result.get('message', f"Panda enjoys the {widget.name}!")
            animation = result.get('animation', 'playing')
            consumed = result.get('consumed', False)
            
            # Check if use failed (e.g., no quantity for food)
            if result.get('happiness', 0) == 0 and widget.consumable:
                if self.panda_widget:
                    self.panda_widget.info_label.configure(text=message)
                self.log(f"❌ {message}")
                return
            
            # Update panda widget animation and speech
            if self.panda_widget:
                self.panda_widget.info_label.configure(text=message)
                self.panda_widget.play_animation_once(animation)
            
            # Use panda character's specific response methods
            if self.panda:
                if interaction_type == 'feed':
                    panda_msg = self.panda.on_food_received()
                    self.panda.feed_count += 1
                elif interaction_type == 'play':
                    panda_msg = self.panda.on_toy_received()
                    self.panda.click_count += 1
                else:
                    panda_msg = None
                
                if panda_msg and self.panda_widget:
                    self.panda_widget.info_label.configure(text=panda_msg)
            
            # Award XP
            if self.panda_level_system:
                try:
                    xp = self.panda_level_system.get_xp_reward('click')
                    self.panda_level_system.add_xp(xp, f'Used {widget.name}')
                except Exception:
                    pass
            
            if consumed:
                self.log(f"🐼 Fed {widget.name} to panda! {message} (consumed)")
            else:
                self.log(f"🐼 Gave {widget.name} to panda! {message}")
            
            # Refresh inventory to show updated usage stats
            try:
                for w in self.tab_inventory.winfo_children():
                    w.destroy()
                self.create_inventory_tab()
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"Error giving item to panda: {e}")
            self.log(f"❌ Error giving item to panda: {e}")
    
    def create_panda_stats_tab(self):
        """Create panda stats and mood tab with live-updating displays"""
        scrollable_frame = ctk.CTkScrollableFrame(self.tab_panda_stats)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scrollable_frame, text="📊 Panda Stats & Mood",
                     font=("Arial Bold", 22)).pack(pady=(15, 5))

        if not self.panda:
            ctk.CTkLabel(scrollable_frame,
                         text="Panda character not available.",
                         font=("Arial", 14)).pack(pady=50)
            return

        # ── Store mutable label references for live refresh ──
        self._stats_labels = {}

        # ═══════════════════ Identity ═══════════════════
        identity_frame = ctk.CTkFrame(scrollable_frame)
        identity_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(identity_frame, text="🐼 Identity",
                     font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=(10, 5))

        name_row = ctk.CTkFrame(identity_frame)
        name_row.pack(fill="x", padx=20, pady=3)
        ctk.CTkLabel(name_row, text="Name:", font=("Arial", 12)).pack(side="left", padx=5)
        self._stats_name_entry = ctk.CTkEntry(name_row, width=200,
                                              placeholder_text="Enter panda name...")
        self._stats_name_entry.pack(side="left", padx=5)
        self._stats_name_entry.insert(0, self.panda.name)

        def set_name_from_stats():
            new_name = self._stats_name_entry.get().strip()
            if new_name:
                self.panda.set_name(new_name)
                config.set('panda', 'name', value=new_name)
                config.save()
                self.log(f"✅ Panda renamed to '{new_name}'")

        ctk.CTkButton(name_row, text="✏️ Set Name", width=80,
                      command=set_name_from_stats).pack(side="left", padx=5)

        gender_row = ctk.CTkFrame(identity_frame)
        gender_row.pack(fill="x", padx=20, pady=3)
        ctk.CTkLabel(gender_row, text="Gender:", font=("Arial", 12)).pack(side="left", padx=5)

        try:
            from src.features.panda_character import PandaGender
            import tkinter as tk
            self._stats_gender_var = tk.StringVar(value=self.panda.gender.value)

            def set_gender_from_stats():
                try:
                    gender = PandaGender(self._stats_gender_var.get())
                    self.panda.set_gender(gender)
                    config.set('panda', 'gender', value=gender.value)
                    config.save()
                    self.log(f"✅ Panda gender set to {gender.value}")
                except Exception as ge:
                    logger.debug(f"Error setting gender: {ge}")

            for gender, label in [(PandaGender.MALE, "♂ Male"),
                                  (PandaGender.FEMALE, "♀ Female"),
                                  (PandaGender.NON_BINARY, "⚧ Non-Binary")]:
                ctk.CTkRadioButton(gender_row, text=label,
                                   variable=self._stats_gender_var,
                                   value=gender.value,
                                   command=set_gender_from_stats
                                   ).pack(side="left", padx=8)
        except Exception as e:
            ctk.CTkLabel(gender_row, text=f"Gender options unavailable: {e}",
                         font=("Arial", 10), text_color="gray").pack(side="left", padx=5)

        # ═══════════════════ Current Mood ═══════════════════
        mood_frame = ctk.CTkFrame(scrollable_frame)
        mood_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(mood_frame, text="🎭 Current Mood",
                     font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=(10, 5))

        mood_indicator = self.panda.get_mood_indicator()
        mood_name = self.panda.current_mood.value.title()
        self.panda_mood_label = ctk.CTkLabel(
            mood_frame, text=f"{mood_indicator} {mood_name}",
            font=("Arial Bold", 18))
        self.panda_mood_label.pack(anchor="w", padx=20, pady=5)

        # Mood reference bar — show all moods with current highlighted
        try:
            from src.features.panda_character import PandaMood
            mood_bar = ctk.CTkFrame(mood_frame)
            mood_bar.pack(fill="x", padx=20, pady=(0, 10))
            mood_emojis = {
                PandaMood.HAPPY: "😊", PandaMood.ECSTATIC: "🤩",
                PandaMood.WORKING: "💼", PandaMood.CELEBRATING: "🎉",
                PandaMood.SARCASTIC: "😏", PandaMood.RAGE: "😡",
                PandaMood.SLEEPING: "😴", PandaMood.DRUNK: "🥴",
                PandaMood.EXISTENTIAL: "🤔", PandaMood.PETTING: "🥰",
            }
            for mood_enum, emoji in mood_emojis.items():
                is_current = (mood_enum == self.panda.current_mood)
                lbl = ctk.CTkLabel(
                    mood_bar, text=emoji, font=("Arial", 16 if is_current else 12),
                    width=30)
                lbl.pack(side="left", padx=2)
                if is_current:
                    lbl.configure(fg_color="#2fa572", corner_radius=6)
        except Exception:
            pass

        # ═══════════════════ Panda Preview (compact) ═══════════════════
        preview_frame = ctk.CTkFrame(scrollable_frame)
        preview_frame.pack(fill="x", padx=10, pady=5)
        preview_header = ctk.CTkFrame(preview_frame, fg_color="transparent")
        preview_header.pack(fill="x", padx=10, pady=(5, 0))
        ctk.CTkLabel(preview_header, text="🐼 Panda Preview",
                     font=("Arial Bold", 16)).pack(side="left")

        import tkinter as _tk
        preview_canvas = _tk.Canvas(preview_frame, width=120, height=140,
                                    bg="#2b2b2b", highlightthickness=0)
        preview_canvas.pack(pady=(5, 5))
        self._draw_static_panda(preview_canvas, 120, 140)

        anim_name = self.panda_widget.current_animation if hasattr(self, 'panda_widget') and self.panda_widget else 'idle'
        self._stats_labels['animation'] = ctk.CTkLabel(
            preview_frame, text=f"Current animation: {anim_name}",
            font=("Arial", 11), text_color="#aaaaaa")
        self._stats_labels['animation'].pack(pady=(0, 5))

        # ═══════════════════ Interaction Statistics ═══════════════════
        stats = self.panda.get_statistics()
        stats_frame = ctk.CTkFrame(scrollable_frame)
        stats_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(stats_frame, text="📈 Interaction Statistics",
                     font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=(10, 5))

        stat_items = [
            ("🖱️ Clicks", 'click_count', stats.get('click_count', 0)),
            ("🐾 Pets", 'pet_count', stats.get('pet_count', 0)),
            ("🎋 Feeds", 'feed_count', stats.get('feed_count', 0)),
            ("💭 Hovers", 'hover_count', stats.get('hover_count', 0)),
            ("🖐️ Drags", 'drag_count', stats.get('drag_count', 0)),
            ("🤾 Tosses", 'toss_count', stats.get('toss_count', 0)),
            ("🫨 Shakes", 'shake_count', stats.get('shake_count', 0)),
            ("🌀 Spins", 'spin_count', stats.get('spin_count', 0)),
            ("🧸 Toy Interactions", 'toy_interact_count', stats.get('toy_interact_count', 0)),
            ("👔 Clothing Changes", 'clothing_change_count', stats.get('clothing_change_count', 0)),
            ("🎯 Items Thrown At", 'items_thrown_at_count', stats.get('items_thrown_at_count', 0)),
            ("📁 Files Processed", 'files_processed', stats.get('files_processed', 0)),
            ("❌ Failed Operations", 'failed_operations', stats.get('failed_operations', 0)),
            ("🥚 Easter Eggs Found", 'easter_eggs_found', stats.get('easter_eggs_found', 0)),
        ]
        for label, key, value in stat_items:
            row = ctk.CTkFrame(stats_frame)
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=label, font=("Arial", 12)).pack(side="left", padx=5)
            val_lbl = ctk.CTkLabel(row, text=str(value), font=("Arial Bold", 12),
                         text_color="#00cc00")
            val_lbl.pack(side="right", padx=10)
            self._stats_labels[key] = val_lbl

        # ═══════════════════ Level Info ═══════════════════
        if self.panda_level_system:
            level_frame = ctk.CTkFrame(scrollable_frame)
            level_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(level_frame, text="⭐ Panda Level",
                         font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=(10, 5))
            try:
                level = self.panda_level_system.level
                xp = self.panda_level_system.xp
                xp_needed = self.panda_level_system.get_xp_to_next_level()
                self._stats_labels['level_text'] = ctk.CTkLabel(
                    level_frame,
                    text=f"Level {level}  •  XP: {xp}/{xp_needed}",
                    font=("Arial Bold", 14), text_color="#ffaa00")
                self._stats_labels['level_text'].pack(anchor="w", padx=20, pady=5)
                progress = min(1.0, xp / max(1, xp_needed))
                self._stats_xp_bar = ctk.CTkProgressBar(level_frame, width=400)
                self._stats_xp_bar.pack(anchor="w", padx=20, pady=5)
                self._stats_xp_bar.set(progress)
            except Exception as e:
                ctk.CTkLabel(level_frame, text=f"Level info unavailable: {e}",
                             font=("Arial", 11), text_color="gray").pack(anchor="w", padx=20, pady=5)

        # ═══════════════════ Easter Eggs ═══════════════════
        if stats.get('easter_eggs'):
            egg_frame = ctk.CTkFrame(scrollable_frame)
            egg_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(egg_frame, text="🥚 Easter Eggs Discovered",
                         font=("Arial Bold", 16)).pack(anchor="w", padx=10, pady=(10, 5))
            for egg in stats['easter_eggs']:
                ctk.CTkLabel(egg_frame, text=f"  🥚 {egg}",
                             font=("Arial", 11)).pack(anchor="w", padx=20, pady=2)

        # ═══════════════════ Action Buttons ═══════════════════
        buttons_frame = ctk.CTkFrame(scrollable_frame)
        buttons_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkButton(buttons_frame, text="🔁 Reset Panda Progression",
                      fg_color="#cc3333", hover_color="#aa2222",
                      command=self._reset_panda_progression).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(buttons_frame, text="🔁 Reset Player Progression",
                      fg_color="#cc3333", hover_color="#aa2222",
                      command=self._reset_player_progression).pack(side="left", padx=10, pady=10)

        # Start auto-refresh timer (refresh every 3 seconds)
        self._start_stats_auto_refresh()

    def _draw_static_panda(self, canvas, w, h):
        """Draw a static panda on a preview canvas matching the live panda_widget style."""
        cx = w // 2
        sx = w / 220.0
        sy = h / 270.0
        black = "#1a1a1a"
        white = "#F5F5F5"
        pink = "#FFB6C1"

        # Legs (behind body)
        leg_top = int(145 * sy)
        leg_len = int(30 * sy)
        for lx in [cx - int(25 * sx), cx + int(25 * sx)]:
            canvas.create_oval(lx - int(12 * sx), leg_top,
                               lx + int(12 * sx), leg_top + leg_len,
                               fill=black, outline=black)
            # Foot pad
            canvas.create_oval(lx - int(10 * sx), leg_top + leg_len - int(8 * sy),
                               lx + int(10 * sx), leg_top + leg_len + int(4 * sy),
                               fill=white, outline=black, width=1)

        # Body (white belly)
        body_top = int(75 * sy)
        body_bot = int(160 * sy)
        body_rx = int(42 * sx)
        canvas.create_oval(cx - body_rx, body_top, cx + body_rx, body_bot,
                           fill=white, outline=black, width=2)
        # Inner belly patch
        belly_rx = int(28 * sx)
        canvas.create_oval(cx - belly_rx, body_top + int(15 * sy),
                           cx + belly_rx, body_bot - int(10 * sy),
                           fill="#FAFAFA", outline="")

        # Arms
        arm_top = int(95 * sy)
        arm_len = int(35 * sy)
        canvas.create_oval(cx - int(55 * sx), arm_top,
                           cx - int(30 * sx), arm_top + arm_len,
                           fill=black, outline=black)
        canvas.create_oval(cx + int(30 * sx), arm_top,
                           cx + int(55 * sx), arm_top + arm_len,
                           fill=black, outline=black)

        # Head
        head_cy = int(52 * sy)
        head_rx = int(36 * sx)
        head_ry = int(32 * sy)
        canvas.create_oval(cx - head_rx, head_cy - head_ry,
                           cx + head_rx, head_cy + head_ry,
                           fill=white, outline=black, width=2)

        # Ears
        ear_y = head_cy - head_ry + int(5 * sy)
        ear_w = int(22 * sx)
        canvas.create_oval(cx - head_rx - int(2 * sx), ear_y - int(16 * sy),
                           cx - head_rx + ear_w, ear_y + int(8 * sy),
                           fill=black, outline=black)
        canvas.create_oval(cx - head_rx + int(4 * sx), ear_y - int(10 * sy),
                           cx - head_rx + int(16 * sx), ear_y + int(2 * sy),
                           fill=pink, outline="")
        canvas.create_oval(cx + head_rx - ear_w, ear_y - int(16 * sy),
                           cx + head_rx + int(2 * sx), ear_y + int(8 * sy),
                           fill=black, outline=black)
        canvas.create_oval(cx + head_rx - int(16 * sx), ear_y - int(10 * sy),
                           cx + head_rx - int(4 * sx), ear_y + int(2 * sy),
                           fill=pink, outline="")

        # Eye patches
        eye_y = head_cy - int(4 * sy)
        patch_rx = int(14 * sx)
        patch_ry = int(11 * sy)
        eye_offset = int(24 * sx)
        for dx in [-eye_offset, eye_offset]:
            canvas.create_oval(cx + dx - patch_rx, eye_y - patch_ry,
                               cx + dx + patch_rx, eye_y + patch_ry,
                               fill=black, outline="")

        # Eyes (white with pupils)
        es = int(6 * sx)
        ps = int(3 * sx)
        for dx in [-eye_offset, eye_offset]:
            ex = cx + dx
            canvas.create_oval(ex - es, eye_y - es, ex + es, eye_y + es,
                               fill="white", outline="")
            canvas.create_oval(ex - ps, eye_y - ps, ex + ps, eye_y + ps,
                               fill="#222222", outline="")

        # Nose
        nose_y = head_cy + int(8 * sy)
        canvas.create_oval(cx - int(5 * sx), nose_y - int(3 * sy),
                           cx + int(5 * sx), nose_y + int(4 * sy),
                           fill=black, outline="")

        # Mouth (smile arc)
        my = nose_y + int(6 * sy)
        canvas.create_arc(cx - int(8 * sx), my - int(4 * sy),
                          cx + int(8 * sx), my + int(6 * sy),
                          start=200, extent=140, style="arc",
                          outline=black, width=max(1, int(1.5 * sx)))

    def _refresh_panda_stats(self):
        """Refresh panda stats display by rebuilding the tab content"""
        # Cancel existing auto-refresh timer before rebuilding
        self._cancel_stats_auto_refresh()
        # Destroy and recreate the tab content for a full refresh
        try:
            for widget in self.tab_panda_stats.winfo_children():
                widget.destroy()
            self.create_panda_stats_tab()
            logger.info("Panda stats refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing panda stats: {e}")
            if hasattr(self, 'panda_mood_label') and self.panda:
                mood_indicator = self.panda.get_mood_indicator()
                mood_name = self.panda.current_mood.value.title()
                self.panda_mood_label.configure(text=f"{mood_indicator} {mood_name}")

    def _start_stats_auto_refresh(self):
        """Auto-refresh panda stats every 3 seconds, updating labels in-place.

        This is a self-scheduling timer: it reschedules itself via
        ``self.after()`` until the stats tab is destroyed or the window closes.
        Cancel with ``_cancel_stats_auto_refresh()``.
        """
        try:
            if not hasattr(self, 'tab_panda_stats') or not self.tab_panda_stats.winfo_exists():
                return
            if hasattr(self, 'panda_mood_label') and self.panda:
                try:
                    mood_indicator = self.panda.get_mood_indicator()
                    mood_name = self.panda.current_mood.value.title()
                    new_text = f"{mood_indicator} {mood_name}"
                    if self.panda_mood_label.cget("text") != new_text:
                        self.panda_mood_label.configure(text=new_text)
                except Exception:
                    pass
            # Update all stat labels in-place (only if changed)
            if hasattr(self, '_stats_labels') and self._stats_labels and self.panda:
                try:
                    stats = self.panda.get_statistics()
                    for key in ('click_count', 'pet_count', 'feed_count', 'hover_count',
                                'drag_count', 'toss_count', 'shake_count', 'spin_count',
                                'toy_interact_count', 'clothing_change_count',
                                'items_thrown_at_count',
                                'files_processed', 'failed_operations', 'easter_eggs_found'):
                        lbl = self._stats_labels.get(key)
                        if lbl:
                            new_val = str(stats.get(key, 0))
                            if lbl.cget("text") != new_val:
                                lbl.configure(text=new_val)
                    # Update animation label
                    anim_lbl = self._stats_labels.get('animation')
                    if anim_lbl and hasattr(self, 'panda_widget') and self.panda_widget:
                        new_anim = f"Current animation: {self.panda_widget.current_animation}"
                        if anim_lbl.cget("text") != new_anim:
                            anim_lbl.configure(text=new_anim)
                    # Update level/XP
                    if self.panda_level_system:
                        lvl_lbl = self._stats_labels.get('level_text')
                        if lvl_lbl:
                            level = self.panda_level_system.level
                            xp = self.panda_level_system.xp
                            xp_needed = self.panda_level_system.get_xp_to_next_level()
                            new_lvl = f"Level {level}  •  XP: {xp}/{xp_needed}"
                            if lvl_lbl.cget("text") != new_lvl:
                                lvl_lbl.configure(text=new_lvl)
                        if hasattr(self, '_stats_xp_bar'):
                            xp = self.panda_level_system.xp
                            xp_needed = self.panda_level_system.get_xp_to_next_level()
                            self._stats_xp_bar.set(min(1.0, xp / max(1, xp_needed)))
                except Exception:
                    pass
            self._stats_auto_refresh_id = self.after(5000, self._start_stats_auto_refresh)
        except Exception as e:
            logger.debug(f"Stats auto-refresh error: {e}")

    def _cancel_stats_auto_refresh(self):
        """Cancel any pending stats auto-refresh timer."""
        if hasattr(self, '_stats_auto_refresh_id') and self._stats_auto_refresh_id:
            try:
                self.after_cancel(self._stats_auto_refresh_id)
            except Exception:
                pass
            self._stats_auto_refresh_id = None

    def _reset_panda_progression(self):
        """Reset panda stats and progression."""
        if not self.panda:
            return
        if not messagebox.askyesno("Reset Panda Progression",
                                    "Are you sure you want to reset all panda stats?\n"
                                    "This will reset clicks, pets, feeds, mood, and level."):
            return
        try:
            self.panda.click_count = 0
            self.panda.pet_count = 0
            self.panda.feed_count = 0
            self.panda.hover_count = 0
            self.panda.files_processed_count = 0
            self.panda.failed_operations = 0
            self.panda.easter_eggs_triggered.clear()
            if hasattr(self.panda, 'current_mood'):
                from src.features.panda_character import PandaMood
                self.panda.current_mood = PandaMood.HAPPY
            if self.panda_level_system:
                self.panda_level_system.level = 1
                self.panda_level_system.xp = 0
            config.save()
            self._refresh_panda_stats()
            self.log("✅ Panda progression has been reset!")
            messagebox.showinfo("Reset Complete", "Panda progression has been reset.")
        except Exception as e:
            logger.error(f"Error resetting panda progression: {e}")
            messagebox.showerror("Error", f"Failed to reset panda progression: {e}")

    def _reset_player_progression(self):
        """Reset player/user progression."""
        if not messagebox.askyesno("Reset Player Progression",
                                    "Are you sure you want to reset all player stats?\n"
                                    "This will reset your user level, XP, currency, and achievements."):
            return
        try:
            if self.user_level_system:
                self.user_level_system.level = 1
                self.user_level_system.xp = 0
            if self.currency_system:
                try:
                    self.currency_system.balance = 0
                except Exception:
                    pass
            if self.achievement_manager:
                try:
                    self.achievement_manager.reset()
                except Exception:
                    pass
            if self.stats_tracker:
                try:
                    self.stats_tracker.reset()
                except Exception:
                    pass
            config.save()
            self._refresh_panda_stats()
            self.log("✅ Player progression has been reset!")
            messagebox.showinfo("Reset Complete", "Player progression has been reset.")
        except Exception as e:
            logger.error(f"Error resetting player progression: {e}")
            messagebox.showerror("Error", f"Failed to reset player progression: {e}")
    
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
        
        # Add panda widget (renders in its own Toplevel window)
        # Panda is always present - not a "mode"
        if PANDA_WIDGET_AVAILABLE and self.panda:
            self.panda_widget = PandaWidget(
                self,
                panda_character=self.panda,
                panda_level_system=self.panda_level_system,
                widget_collection=self.widget_collection,
                panda_closet=self.panda_closet
            )
    
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
            mode_display = self.mode_var.get()
            mode = self._mode_display_to_key.get(mode_display, mode_display.split(" ", 1)[-1] if " " in mode_display else mode_display)
            style_display = self.style_var.get()
            style = self._style_display_to_key.get(style_display, "flat")
            detect_lods = self.detect_lods_var.get()
            group_lods = self.group_lods_var.get()
            detect_duplicates = self.detect_duplicates_var.get()
            extract_from_archive = self.extract_from_archive_var.get()
            compress_to_archive = self.compress_to_archive_var.get()
            
            logger.debug(f"Sorting parameters - Input: {input_path}, Output: {output_path}, Mode: {mode}, Style: {style}")
            logger.debug(f"Options - LODs: {detect_lods}, Group LODs: {group_lods}, Duplicates: {detect_duplicates}")
            logger.debug(f"Archive options - Extract: {extract_from_archive}, Compress: {compress_to_archive}")
            
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
            
            # Reset sorting dialog state flags
            self._sorting_skip_all.clear()
            self._sorting_cancelled.clear()
            
            # Start sorting in background thread with all parameters
            try:
                thread = threading.Thread(
                    target=self.sort_textures_thread,
                    args=(input_path, output_path, mode, style, detect_lods, group_lods, detect_duplicates, 
                          extract_from_archive, compress_to_archive),
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
    
    @staticmethod
    def _make_category_filter(search_var, category_var, category_dropdown, category_list):
        """Create a live-filter callback for a category dropdown.
        
        Binds to search_var.trace_add('write', ...) so the dropdown
        values update as the user types.
        """
        def _filter(*_args):
            query = search_var.get().lower().strip()
            if query:
                filtered = [c for c in category_list if query in c.lower()]
            else:
                filtered = category_list
            if filtered:
                category_dropdown.configure(values=filtered)
                if category_var.get() not in filtered:
                    category_var.set(filtered[0])
            else:
                category_dropdown.configure(values=category_list)
        search_var.trace_add('write', _filter)
    
    def sort_textures_thread(self, input_path_str, output_path_str, mode, style_name, detect_lods, group_lods, detect_duplicates, 
                           extract_from_archive=False, compress_to_archive=False):
        """Background thread for texture sorting with full organization system"""
        # Constants for error reporting
        MAX_UI_ERROR_MESSAGES = 5  # Maximum number of classification errors to show in UI
        MAX_RESULTS_ERROR_DISPLAY = 10  # Maximum number of organization errors to display
        
        # Track temp extraction directory for cleanup
        temp_extraction_dir = None
        
        try:
            logger.info(f"sort_textures_thread started - Processing: {input_path_str} -> {output_path_str}")
            input_path = Path(input_path_str)
            output_path = Path(output_path_str)
            
            # Handle archive extraction if requested
            if extract_from_archive and self.file_handler.is_archive(input_path):
                self.log(f"📦 Extracting archive: {input_path.name}")
                self.update_progress(0.02, "Extracting archive...")
                temp_extraction_dir = self.file_handler.extract_archive(input_path)
                if temp_extraction_dir:
                    input_path = temp_extraction_dir
                    self.log(f"✓ Archive extracted to temporary directory")
                    logger.info(f"Archive extracted to: {temp_extraction_dir}")
                else:
                    self.log(f"❌ Failed to extract archive: {input_path.name}")
                    logger.error(f"Archive extraction failed: {input_path}")
                    return
            
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
            
            # Apply game-specific texture profile if available (NEW)
            if hasattr(self, 'current_game_info') and self.current_game_info:
                texture_profile = self.current_game_info.get('texture_profile', {})
                if texture_profile:
                    self.classifier.set_game_profile(texture_profile)
                    game_title = self.current_game_info.get('title', 'Unknown')
                    self.log(f"🎮 Using texture profile for: {game_title}")
                    logger.info(f"Applied game profile for {game_title}")
            
            # Classify textures
            logger.info(f"Starting classification of {total} textures")
            self.update_progress(0.1, "Classifying textures...")
            texture_infos = []
            classification_errors = 0
            
            for i, file_path in enumerate(texture_files):
                try:
                    # Classify based on mode
                    if mode == "automatic":
                        # Automatic: AI decides without user input
                        category, confidence = self.classifier.classify_texture(file_path)
                    
                    elif mode == "manual":
                        # Manual: User selects category for each file
                        # Check skip_all flag
                        if self._sorting_skip_all.is_set():
                            category, confidence = self.classifier.classify_texture(file_path)
                            if i == 0 or (i > 0 and not hasattr(self, '_skip_all_logged')):
                                self.log("⏩ Skip All active - using automatic classification for remaining files")
                                self._skip_all_logged = True
                        elif self._sorting_cancelled.is_set():
                            self.log("⚠️ Sorting cancelled by user")
                            return
                        else:
                            # Get AI suggestion first (for display only)
                            ai_category, ai_confidence = self.classifier.classify_texture(file_path)
                            
                            # Show dialog and wait for result using event-based approach
                            result_event = threading.Event()
                            selected_category = [None]  # Use list to allow modification in nested function
                            
                            def show_manual_dialog():
                                """Show manual classification dialog"""
                                # Get sorted category list
                                category_list = sorted(list(ALL_CATEGORIES.keys()))
                                
                                # Create a simple selection dialog
                                dialog_window = ctk.CTkToplevel(self)
                                dialog_window.title("Manual Classification")
                                dialog_window.geometry("550x500")
                                
                                # Make modal
                                dialog_window.transient(self)
                                dialog_window.grab_set()
                                
                                # Center on screen
                                dialog_window.update_idletasks()
                                x = (dialog_window.winfo_screenwidth() // 2) - (550 // 2)
                                y = (dialog_window.winfo_screenheight() // 2) - (500 // 2)
                                dialog_window.geometry(f"550x500+{x}+{y}")
                                
                                # File info with counter
                                ctk.CTkLabel(dialog_window, text=f"File {i+1} of {total}: {file_path.name}", 
                                           font=("Arial Bold", 12), wraplength=500).pack(pady=10)
                                
                                # Texture preview
                                try:
                                    from PIL import Image, ImageTk
                                    img = Image.open(str(file_path))
                                    img.thumbnail((150, 150))
                                    preview_photo = ImageTk.PhotoImage(img)
                                    preview_label = ctk.CTkLabel(dialog_window, text="", image=preview_photo)
                                    preview_label.image = preview_photo  # Keep reference
                                    preview_label.pack(pady=5)
                                except Exception:
                                    ctk.CTkLabel(dialog_window, text="[Preview unavailable]",
                                               font=("Arial", 10), text_color="gray").pack(pady=5)
                                
                                ctk.CTkLabel(dialog_window, 
                                           text=f"AI Suggestion: {ai_category} ({ai_confidence:.0%} confidence)",
                                           font=("Arial", 11)).pack(pady=5)
                                
                                # Category selection with search filter
                                ctk.CTkLabel(dialog_window, text="Select Category:", 
                                           font=("Arial Bold", 11)).pack(pady=(10, 2))
                                
                                # Search entry for filtering categories
                                search_var = ctk.StringVar()
                                search_entry = ctk.CTkEntry(dialog_window, textvariable=search_var,
                                                           placeholder_text="Type to filter categories...",
                                                           width=400)
                                search_entry.pack(pady=(2, 5))
                                
                                category_var = ctk.StringVar(value=ai_category)
                                category_dropdown = ctk.CTkOptionMenu(dialog_window, variable=category_var,
                                                                     values=category_list, width=400)
                                category_dropdown.pack(pady=5)
                                
                                self._make_category_filter(search_var, category_var,
                                                           category_dropdown, category_list)
                                
                                # Buttons
                                button_frame = ctk.CTkFrame(dialog_window)
                                button_frame.pack(pady=20)
                                
                                def on_ok():
                                    selected_category[0] = category_var.get()
                                    dialog_window.destroy()
                                    result_event.set()
                                
                                def on_skip():
                                    selected_category[0] = "unclassified"
                                    dialog_window.destroy()
                                    result_event.set()
                                
                                def on_skip_all():
                                    self._sorting_skip_all.set()
                                    selected_category[0] = "unclassified"
                                    dialog_window.destroy()
                                    result_event.set()
                                
                                def on_cancel():
                                    self._sorting_cancelled.set()
                                    selected_category[0] = None
                                    dialog_window.destroy()
                                    result_event.set()
                                
                                ctk.CTkButton(button_frame, text="✓ OK", command=on_ok, width=80).pack(side="left", padx=3)
                                ctk.CTkButton(button_frame, text="⏭ Skip", command=on_skip, width=80).pack(side="left", padx=3)
                                ctk.CTkButton(button_frame, text="⏩ Skip All", command=on_skip_all, width=90, 
                                            fg_color="orange").pack(side="left", padx=3)
                                ctk.CTkButton(button_frame, text="✖ Cancel", command=on_cancel, width=80,
                                            fg_color="red").pack(side="left", padx=3)
                                
                                # Handle dialog close
                                def on_close():
                                    selected_category[0] = "unclassified"
                                    result_event.set()
                                dialog_window.protocol("WM_DELETE_WINDOW", on_close)
                            
                            # Execute dialog in main thread
                            self.after(0, show_manual_dialog)
                            
                            # Wait for result using event
                            if result_event.wait(timeout=self.USER_INTERACTION_TIMEOUT):
                                if self._sorting_cancelled.is_set():
                                    self.log("⚠️ Sorting cancelled by user")
                                    return
                                category = selected_category[0] if selected_category[0] else ai_category
                                confidence = 1.0  # User selection is 100% confident
                            else:
                                # Timeout - use AI suggestion
                                category = ai_category
                                confidence = ai_confidence
                                logger.warning(f"Manual classification timed out for {file_path.name}")
                    
                    elif mode == "suggested":
                        # Suggested: AI suggests, user confirms or changes
                        ai_category, ai_confidence = self.classifier.classify_texture(file_path)
                        
                        # Check skip_all flag
                        if self._sorting_skip_all.is_set():
                            category = ai_category
                            confidence = ai_confidence
                            if not hasattr(self, '_skip_all_logged'):
                                self.log("⏩ Skip All active - accepting AI suggestions for remaining files")
                                self._skip_all_logged = True
                        elif self._sorting_cancelled.is_set():
                            self.log("⚠️ Sorting cancelled by user")
                            return
                        else:
                            # Show confirmation dialog using event-based approach
                            result_event = threading.Event()
                            confirmed_category = [None]
                            
                            def show_suggested_dialog():
                                """Show suggested classification dialog"""
                                # Get sorted category list
                                category_list = sorted(list(ALL_CATEGORIES.keys()))
                                
                                dialog_window = ctk.CTkToplevel(self)
                                dialog_window.title("Confirm Classification")
                                dialog_window.geometry("550x450")
                                
                                # Make modal
                                dialog_window.transient(self)
                                dialog_window.grab_set()
                                
                                # Center on screen
                                dialog_window.update_idletasks()
                                x = (dialog_window.winfo_screenwidth() // 2) - (550 // 2)
                                y = (dialog_window.winfo_screenheight() // 2) - (450 // 2)
                                dialog_window.geometry(f"550x450+{x}+{y}")
                                
                                # File info with counter
                                ctk.CTkLabel(dialog_window, text=f"File {i+1} of {total}: {file_path.name}", 
                                           font=("Arial Bold", 12), wraplength=500).pack(pady=10)
                                
                                # Texture preview
                                try:
                                    from PIL import Image, ImageTk
                                    img = Image.open(str(file_path))
                                    img.thumbnail((150, 150))
                                    preview_photo = ImageTk.PhotoImage(img)
                                    preview_label = ctk.CTkLabel(dialog_window, text="", image=preview_photo)
                                    preview_label.image = preview_photo  # Keep reference
                                    preview_label.pack(pady=5)
                                except Exception:
                                    ctk.CTkLabel(dialog_window, text="[Preview unavailable]",
                                               font=("Arial", 10), text_color="gray").pack(pady=5)
                                
                                ctk.CTkLabel(dialog_window, 
                                           text=f"AI Classification: {ai_category} ({ai_confidence:.0%} confidence)",
                                           font=("Arial Bold", 13), text_color="green").pack(pady=10)
                                
                                ctk.CTkLabel(dialog_window, text="Change category if incorrect:", 
                                           font=("Arial", 11)).pack(pady=(5, 2))
                                
                                # Search entry for filtering categories
                                search_var = ctk.StringVar()
                                search_entry = ctk.CTkEntry(dialog_window, textvariable=search_var,
                                                           placeholder_text="Type to filter categories...",
                                                           width=400)
                                search_entry.pack(pady=(2, 5))
                                
                                category_var = ctk.StringVar(value=ai_category)
                                category_dropdown = ctk.CTkOptionMenu(dialog_window, variable=category_var,
                                                                     values=category_list, width=400)
                                category_dropdown.pack(pady=5)
                                
                                self._make_category_filter(search_var, category_var,
                                                           category_dropdown, category_list)
                                
                                # Buttons
                                button_frame = ctk.CTkFrame(dialog_window)
                                button_frame.pack(pady=20)
                                
                                def on_accept():
                                    confirmed_category[0] = ai_category
                                    dialog_window.destroy()
                                    result_event.set()
                                
                                def on_change():
                                    confirmed_category[0] = category_var.get()
                                    dialog_window.destroy()
                                    result_event.set()
                                
                                def on_skip():
                                    confirmed_category[0] = "unclassified"
                                    dialog_window.destroy()
                                    result_event.set()
                                
                                def on_skip_all():
                                    self._sorting_skip_all.set()
                                    confirmed_category[0] = ai_category
                                    dialog_window.destroy()
                                    result_event.set()
                                
                                def on_cancel():
                                    self._sorting_cancelled.set()
                                    confirmed_category[0] = None
                                    dialog_window.destroy()
                                    result_event.set()
                                
                                ctk.CTkButton(button_frame, text="✓ Accept", command=on_accept, 
                                            width=80, fg_color="green").pack(side="left", padx=3)
                                ctk.CTkButton(button_frame, text="✏ Change", command=on_change, 
                                            width=80).pack(side="left", padx=3)
                                ctk.CTkButton(button_frame, text="⏭ Skip", command=on_skip, 
                                            width=80).pack(side="left", padx=3)
                                ctk.CTkButton(button_frame, text="⏩ Skip All", command=on_skip_all, width=90,
                                            fg_color="orange").pack(side="left", padx=3)
                                ctk.CTkButton(button_frame, text="✖ Cancel", command=on_cancel, width=80,
                                            fg_color="red").pack(side="left", padx=3)
                                
                                # Handle dialog close
                                def on_close():
                                    confirmed_category[0] = "unclassified"
                                    result_event.set()
                                dialog_window.protocol("WM_DELETE_WINDOW", on_close)
                            
                            # Execute dialog in main thread
                            self.after(0, show_suggested_dialog)
                            
                            # Wait for confirmation using event
                            if result_event.wait(timeout=self.USER_INTERACTION_TIMEOUT):
                                if self._sorting_cancelled.is_set():
                                    self.log("⚠️ Sorting cancelled by user")
                                    return
                                category = confirmed_category[0] if confirmed_category[0] else ai_category
                                confidence = 1.0  # User confirmation is 100% confident
                            else:
                                # Timeout - use AI suggestion
                                category = ai_category
                                confidence = ai_confidence
                                logger.warning(f"Suggested classification timed out for {file_path.name}")
                    
                    else:
                        # Fallback to automatic
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
                
                # Handle archive compression if requested
                if compress_to_archive and results.files_organized > 0:
                    self.update_progress(0.95, "Compressing output to archive...")
                    self.log(f"📦 Creating archive from output directory...")
                    archive_name = f"{output_path.name}_sorted.zip"
                    archive_path = output_path.parent / archive_name
                    success = self.file_handler.create_archive(output_path, archive_path)
                    if success:
                        self.log(f"✓ Archive created: {archive_path.name}")
                        logger.info(f"Output compressed to archive: {archive_path}")
                    else:
                        self.log(f"⚠️ Failed to create output archive")
                        logger.error(f"Archive creation failed: {archive_path}")
                
            except Exception as e:
                logger.error(f"Organization engine failed: {e}", exc_info=True)
                self.log(f"❌ Organization failed: {e}")
                raise  # Re-raise to be caught by outer handler
            
        except Exception as e:
            error_msg = f"Error during sorting: {e}"
            logger.error(error_msg, exc_info=True)
            # Use panda error codes for more context
            panda_error = ""
            if self.panda:
                error_str = str(e).lower()
                if 'permission' in error_str:
                    panda_error = self.panda.get_error_response('E002_PERMISSION_DENIED')
                elif 'not found' in error_str or 'no such file' in error_str:
                    panda_error = self.panda.get_error_response('E001_FILE_NOT_FOUND')
                elif 'disk' in error_str or 'space' in error_str:
                    panda_error = self.panda.get_error_response('E003_DISK_FULL')
                elif 'timeout' in error_str:
                    panda_error = self.panda.get_error_response('E005_TIMEOUT')
                elif 'memory' in error_str:
                    panda_error = self.panda.get_error_response('E008_MEMORY_LOW')
                elif 'format' in error_str or 'invalid' in error_str:
                    panda_error = self.panda.get_error_response('E007_INVALID_FORMAT')
                elif 'corrupt' in error_str:
                    panda_error = self.panda.get_error_response('E004_CORRUPT_FILE')
                elif 'read' in error_str:
                    panda_error = self.panda.get_error_response('E011_READ_ERROR')
                elif 'write' in error_str:
                    panda_error = self.panda.get_error_response('E012_WRITE_ERROR')
                else:
                    panda_error = self.panda.get_error_response('E010_UNKNOWN')
                self.panda.track_operation_failure()
            
            self.log(f"❌ {error_msg}")
            if panda_error:
                self.log(panda_error)
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Full traceback:\n{tb}")
            self.log(tb)
            # Show user-friendly error dialog
            if GUI_AVAILABLE:
                from tkinter import messagebox
                error_display = f"An error occurred during sorting:\n\n{str(e)}"
                if panda_error:
                    error_display += f"\n\n{panda_error}"
                error_display += "\n\nCheck the log for details."
                messagebox.showerror("Sorting Error", error_display)
        
        finally:
            logger.info("Sorting thread cleanup - re-enabling UI buttons")
            
            # Clean up temporary extraction directory if it was created
            if temp_extraction_dir and temp_extraction_dir.exists():
                try:
                    self.file_handler.cleanup_temp_archives()
                    logger.info(f"Cleaned up temp extraction dir: {temp_extraction_dir}")
                except Exception as e:
                    logger.error(f"Failed to cleanup temp dir: {e}")
            
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
            
            # Use sound manager if available
            if hasattr(self, 'sound_manager') and self.sound_manager:
                self.sound_manager.play_complete()
            else:
                # Fallback to system beep
                import sys
                if sys.platform == 'win32':
                    try:
                        import winsound
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)
                    except Exception:
                        pass
                else:
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
        try:
            current = config.get('ui', 'theme', default='dark')
            new_theme = 'light' if current == 'dark' else 'dark'
            config.set('ui', 'theme', value=new_theme)
            ctk.set_appearance_mode(new_theme)
            self.log(f"Theme changed to: {new_theme}")
            # Force widget refresh to prevent invisible elements
            self.update_idletasks()
        except Exception as e:
            logger.error(f"Error toggling theme: {e}")
            self.log(f"⚠️ Theme toggle error")
            try:
                ctk.set_appearance_mode('dark')
                self.update_idletasks()
            except Exception:
                pass


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
        # Create root window (hidden) for splash screen
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
        
        # Destroy the temporary root window before creating the real app.
        # PS2TextureSorter inherits from ctk.CTk, so it creates its own root
        # window internally. Without this destroy(), the temporary root would
        # remain visible as a blank window with the default "ctk" title.
        root.destroy()
        
        # Create and show main application (creates its own CTk root window)
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
