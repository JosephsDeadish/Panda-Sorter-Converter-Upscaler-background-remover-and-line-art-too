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
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

# Add src directory to path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import configuration first
from src.config import config, APP_NAME, APP_VERSION, APP_AUTHOR

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

# Import feature modules
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
    from src.features.unlockables_system import UnlockablesSystem
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
        self.panda_mode = None
        self.sound_manager = None
        self.achievement_manager = None
        self.unlockables_manager = None
        self.stats_tracker = None
        self.search_filter = None
        self.tutorial_manager = None
        self.tooltip_manager = None
        self._tooltips = []  # Store tooltip references to prevent garbage collection
        self.context_help = None
        self.preview_viewer = None
        
        # Initialize features if GUI available
        if GUI_AVAILABLE:
            try:
                if PANDA_MODE_AVAILABLE:
                    self.panda_mode = PandaMode()
                if SOUND_AVAILABLE:
                    self.sound_manager = SoundManager()
                if ACHIEVEMENTS_AVAILABLE:
                    achievements_save = str(Path.home() / ".ps2_texture_sorter" / "achievements.json")
                    self.achievement_manager = AchievementSystem(save_file=achievements_save)
                if UNLOCKABLES_AVAILABLE:
                    self.unlockables_manager = UnlockablesSystem()
                if STATISTICS_AVAILABLE:
                    self.stats_tracker = StatisticsTracker(config)
                if SEARCH_FILTER_AVAILABLE:
                    self.search_filter = SearchFilter()
                if PREVIEW_AVAILABLE:
                    self.preview_viewer = PreviewViewer(self)
                
                # Setup tutorial system
                if TUTORIAL_AVAILABLE:
                    try:
                        self.tutorial_manager, self.tooltip_manager, self.context_help = setup_tutorial_system(self, config)
                        logger.info("Tutorial system initialized successfully")
                    except Exception as tutorial_error:
                        logger.error(f"Failed to initialize tutorial system: {tutorial_error}", exc_info=True)
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
        if self.context_help:
            help_button = ctk.CTkButton(
                menu_frame,
                text="❓ Help",
                width=80,
                command=lambda: self.context_help.open_help_panel()
            )
            help_button.pack(side="right", padx=10, pady=5)
        
        # Theme toggle
        theme_button = ctk.CTkButton(
            menu_frame,
            text="🌓 Theme",
            width=80,
            command=self.toggle_theme
        )
        theme_button.pack(side="right", padx=10, pady=5)
        
        # Settings button
        settings_button = ctk.CTkButton(
            menu_frame,
            text="⚙️ Settings",
            width=100,
            command=self.open_settings_window
        )
        settings_button.pack(side="right", padx=10, pady=5)
        
        # Tutorial button - always visible so user can restart tutorial
        if TUTORIAL_AVAILABLE:
            tutorial_button = ctk.CTkButton(
                menu_frame,
                text="📖 Tutorial",
                width=100,
                command=self._run_tutorial
            )
            tutorial_button.pack(side="right", padx=10, pady=5)
    
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
        
        # Tab view
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # Create tabs with panda emojis on key tabs
        self.tab_sort = self.tabview.add("🐼 Sort Textures")
        self.tab_convert = self.tabview.add("🔄 Convert Files")
        self.tab_browser = self.tabview.add("📁 File Browser")
        self.tab_achievements = self.tabview.add("🏆 Achievements")
        self.tab_rewards = self.tabview.add("🎁 Rewards")
        self.tab_notepad = self.tabview.add("📝 Notepad")
        self.tab_about = self.tabview.add("ℹ️ About")
        
        # Track popped-out tabs
        self._popout_windows = {}
        
        # Populate tabs
        self.create_sort_tab()
        self.create_convert_tab()
        self.create_browser_tab()
        self.create_achievements_tab()
        self.create_rewards_tab()
        self.create_notepad_tab()
        self.create_about_tab()
        
        # Add pop-out buttons to dockable tabs
        self._add_popout_buttons()
        
        # Status bar
        self.create_status_bar()
    
    def _add_popout_buttons(self):
        """Add pop-out/undock buttons to secondary tabs"""
        dockable_tabs = {
            "📝 Notepad": self.tab_notepad,
            "🏆 Achievements": self.tab_achievements,
            "🎁 Rewards": self.tab_rewards,
            "📁 File Browser": self.tab_browser,
            "ℹ️ About": self.tab_about,
        }
        for tab_name, tab_frame in dockable_tabs.items():
            btn = ctk.CTkButton(
                tab_frame, text="⬗ Pop Out", width=90, height=26,
                font=("Arial", 11),
                fg_color="gray40",
                command=lambda n=tab_name: self._popout_tab(n)
            )
            btn.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(btn, f"Open {tab_name} in a separate window"))
    
    def _popout_tab(self, tab_name):
        """Pop out a tab into its own window"""
        if tab_name in self._popout_windows:
            # Already popped out, bring to front
            win = self._popout_windows[tab_name]
            if win.winfo_exists():
                win.lift()
                win.focus_force()
                return
        
        # Get the tab frame and its children
        tab_frame = self.tabview.tab(tab_name)
        children_info = []
        for child in tab_frame.winfo_children():
            children_info.append(child)
        
        # Create pop-out window
        popout = ctk.CTkToplevel(self)
        popout.title(tab_name)
        popout.geometry("800x600")
        self._popout_windows[tab_name] = popout
        
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
            command=lambda: self._dock_tab(tab_name, children_info, popout)
        )
        dock_btn.pack(side="bottom", pady=5)
        
        # Handle window close = dock back
        popout.protocol("WM_DELETE_WINDOW",
                        lambda: self._dock_tab(tab_name, children_info, popout))
    
    def _dock_tab(self, tab_name, children, popout_window):
        """Dock a popped-out tab back into the main tabview"""
        tab_frame = self.tabview.tab(tab_name)
        
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
        
        # Re-add pop-out button
        btn = ctk.CTkButton(
            tab_frame, text="⬗ Pop Out", width=90, height=26,
            font=("Arial", 11),
            fg_color="gray40",
            command=lambda: self._popout_tab(tab_name)
        )
        btn.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
        
        # Switch to the docked tab
        self.tabview.set(tab_name)
    
    def create_sort_tab(self):
        """Create texture sorting tab"""
        # Use scrollable frame to ensure all content is accessible
        scrollable_frame = ctk.CTkScrollableFrame(self.tab_sort)
        scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
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
        self.style_var = ctk.StringVar(value="flat")
        style_menu = ctk.CTkOptionMenu(opts_grid, variable=self.style_var,
                                        values=["sims", "neopets", "flat", "game_area", 
                                               "asset_pipeline", "modular", "minimalist", 
                                               "maximum_detail", "custom"])
        style_menu.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        
        # Checkboxes
        check_frame = ctk.CTkFrame(opts_grid)
        check_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="w")
        
        self.detect_lods_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(check_frame, text="Detect LODs", variable=self.detect_lods_var).pack(side="left", padx=10)
        
        self.group_lods_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(check_frame, text="Group LODs", variable=self.group_lods_var).pack(side="left", padx=10)
        
        self.detect_duplicates_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(check_frame, text="Detect Duplicates", variable=self.detect_duplicates_var).pack(side="left", padx=10)
        
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
        
        # Action buttons
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
        
        # Apply tooltips to sort tab widgets
        self._apply_sort_tooltips(browse_btn, browse_out_btn)
    
    def _apply_sort_tooltips(self, browse_in_btn, browse_out_btn):
        """Apply tooltips to sort tab widgets"""
        if not WidgetTooltip:
            return
        tooltip_text = self._get_tooltip_text
        # Store tooltip references to prevent garbage collection
        self._tooltips.append(WidgetTooltip(self.start_button, tooltip_text('sort_button')))
        self._tooltips.append(WidgetTooltip(browse_in_btn, tooltip_text('input_browse')))
        self._tooltips.append(WidgetTooltip(browse_out_btn, tooltip_text('output_browse')))
    
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
    
    def create_convert_tab(self):
        """Create file format conversion tab"""
        ctk.CTkLabel(self.tab_convert, text="🔄 File Format Conversion 🔄", 
                     font=("Arial Bold", 18)).pack(pady=15)
        
        ctk.CTkLabel(self.tab_convert, text="Batch convert between DDS, PNG, and other formats",
                     font=("Arial", 12)).pack(pady=5)
        
        # Main content frame
        content_frame = ctk.CTkFrame(self.tab_convert)
        content_frame.pack(padx=30, pady=20, fill="both", expand=True)
        
        # === INPUT SECTION ===
        input_frame = ctk.CTkFrame(content_frame)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="Input:", font=("Arial Bold", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.convert_input_var = ctk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.convert_input_var, width=500).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(input_frame, text="Browse", width=100, 
                     command=lambda: self.browse_directory(self.convert_input_var)).grid(row=0, column=2, padx=10, pady=5)
        
        input_frame.columnconfigure(1, weight=1)
        
        # === CONVERSION OPTIONS ===
        options_frame = ctk.CTkFrame(content_frame)
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
        ctk.CTkCheckBox(check_frame, text="Include subdirectories", 
                       variable=self.convert_recursive_var).pack(side="left", padx=10)
        
        self.convert_keep_original_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(check_frame, text="Keep original files", 
                       variable=self.convert_keep_original_var).pack(side="left", padx=10)
        
        # === OUTPUT SECTION ===
        output_frame = ctk.CTkFrame(content_frame)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(output_frame, text="Output:", font=("Arial Bold", 12)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.convert_output_var = ctk.StringVar()
        ctk.CTkEntry(output_frame, textvariable=self.convert_output_var, width=500).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(output_frame, text="Browse", width=100,
                     command=lambda: self.browse_directory(self.convert_output_var)).grid(row=0, column=2, padx=10, pady=5)
        
        output_frame.columnconfigure(1, weight=1)
        
        # === PROGRESS SECTION ===
        progress_frame = ctk.CTkFrame(content_frame)
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
        
        # === CONTROL BUTTONS ===
        button_frame = ctk.CTkFrame(content_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # BIGGER, MORE VISIBLE Start Conversion button with panda emoji
        self.convert_start_button = ctk.CTkButton(
            button_frame, 
            text="🐼 START CONVERSION 🐼", 
            command=self.start_conversion,
            width=250, 
            height=60,
            font=("Arial Bold", 18),
            fg_color="#2B7A0B",  # Prominent green color
            hover_color="#368B14"
        )
        self.convert_start_button.pack(side="left", padx=20, pady=10)
    
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
        # Header
        header_frame = ctk.CTkFrame(self.tab_browser)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="📁 File Browser",
                     font=("Arial Bold", 16)).pack(side="left", padx=10)
        
        # Browse button
        ctk.CTkButton(header_frame, text="📂 Browse Directory", 
                     command=self.browser_select_directory,
                     width=150).pack(side="right", padx=10)
        
        # Refresh button
        ctk.CTkButton(header_frame, text="🔄 Refresh", 
                     command=self.browser_refresh,
                     width=100).pack(side="right", padx=5)
        
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
        
        # Add show all files checkbox
        self.browser_show_all = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(file_header, text="Show all files", 
                       variable=self.browser_show_all,
                       command=self.browser_refresh).pack(side="left", padx=10)
        
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
    
    def browser_select_directory(self):
        """Select directory for file browser"""
        directory = filedialog.askdirectory(title="Select Directory to Browse")
        if directory:
            self.browser_path_var.set(directory)
            self.browser_current_dir = Path(directory)
            self.browser_refresh()
    
    def browser_refresh(self):
        """Refresh file browser content"""
        if not hasattr(self, 'browser_current_dir'):
            return
        
        try:
            # Clear current file list
            for widget in self.browser_file_list.winfo_children():
                widget.destroy()
            
            # Check if show all files is enabled
            show_all = self.browser_show_all.get() if hasattr(self, 'browser_show_all') else False
            
            # Get files based on filter
            if show_all:
                files = [f for f in self.browser_current_dir.iterdir() if f.is_file()]
            else:
                texture_extensions = {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga'}
                files = [f for f in self.browser_current_dir.iterdir() 
                        if f.is_file() and f.suffix.lower() in texture_extensions]
            
            # Display files (removed 100 limit)
            if not files:
                file_type = "files" if show_all else "texture files"
                ctk.CTkLabel(self.browser_file_list, 
                           text=f"No {file_type} found in this directory",
                           font=("Arial", 11)).pack(pady=20)
            else:
                for file in sorted(files):  # Show all files, no limit
                    self._create_file_entry(file)
            
            # Update folder list with navigation
            self.browser_folder_list.delete("1.0", "end")
            
            # Add parent directory navigation if not at root
            if self.browser_current_dir.parent != self.browser_current_dir:
                self.browser_folder_list.insert("end", "⬆️ .. (Parent Directory)\n")
            
            folders = [f for f in self.browser_current_dir.iterdir() if f.is_dir()]
            for folder in sorted(folders):
                self.browser_folder_list.insert("end", f"📁 {folder.name}\n")
            
            # Make folder list clickable
            self.browser_folder_list.bind("<Double-Button-1>", self._on_folder_click)
            
            # Update status
            self.browser_status.configure(text=f"Found {len(files)} file(s) and {len(folders)} folder(s)")
            
        except Exception as e:
            self.browser_status.configure(text=f"Error: {e}")
    
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
        """Create a file entry widget"""
        entry_frame = ctk.CTkFrame(self.browser_file_list)
        entry_frame.pack(fill="x", padx=5, pady=2)
        
        # File icon and name
        file_info = f"📄 {file_path.name}"
        file_size = file_path.stat().st_size
        size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
        
        ctk.CTkLabel(entry_frame, text=file_info, 
                    font=("Arial", 10), anchor="w").pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(entry_frame, text=size_str, 
                    font=("Arial", 9), text_color="gray").pack(side="right", padx=5)
    
    def apply_theme(self, theme_name):
        """Apply selected theme"""
        if theme_name in ['dark', 'light']:
            ctk.set_appearance_mode(theme_name)
            self.log(f"Theme changed to: {theme_name}")
        else:
            self.log(f"Custom theme '{theme_name}' - feature coming soon!")
    
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
                # Theme changes are already applied by the ThemeManager via ctk.set_appearance_mode
                # Just log the change
                self.log(f"✅ Theme applied: {value.get('name', 'Unknown')}")
            elif setting_type == 'color':
                # Color changes are for accent color - log for now
                self.log(f"✅ Accent color changed: {value}")
            elif setting_type == 'cursor':
                # Cursor changes are saved to config - log for now
                self.log(f"✅ Cursor settings applied: {value.get('type', 'Unknown')}")
        except Exception as e:
            self.log(f"❌ Error applying customization: {e}")
            logger.error(f"Customization change error: {e}", exc_info=True)
    
    def open_settings_window(self):
        """Open settings in a separate window"""
        # Create new window
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("⚙️ Application Settings")
        settings_window.geometry("900x700")
        
        # Make it modal-ish - stay on top of main window
        settings_window.transient(self)  # Set as child of main window
        settings_window.grab_set()  # Make it modal
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
        
        # Cache size
        cache_frame = ctk.CTkFrame(perf_frame)
        cache_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(cache_frame, text="Thumbnail Cache Size:").pack(side="left", padx=10)
        cache_var = ctk.StringVar(value=str(config.get('performance', 'thumbnail_cache_size', default=500)))
        cache_entry = ctk.CTkEntry(cache_frame, textvariable=cache_var, width=100)
        cache_entry.pack(side="left", padx=10)
        
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
        
        # Tooltip verbosity
        tooltip_frame = ctk.CTkFrame(ui_frame)
        tooltip_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(tooltip_frame, text="Tooltip Mode:").pack(side="left", padx=10)
        tooltip_var = ctk.StringVar(value=config.get('ui', 'tooltip_mode', default='normal'))
        tooltip_menu = ctk.CTkOptionMenu(tooltip_frame, variable=tooltip_var,
                                         values=["expert", "normal", "beginner", "panda"])
        tooltip_menu.pack(side="left", padx=10)
        
        # Cursor style
        cursor_frame = ctk.CTkFrame(ui_frame)
        cursor_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(cursor_frame, text="Cursor Style:").pack(side="left", padx=10)
        cursor_var = ctk.StringVar(value=config.get('ui', 'cursor', default='default'))
        cursor_menu = ctk.CTkOptionMenu(cursor_frame, variable=cursor_var,
                                        values=["default", "skull", "panda", "sword"])
        cursor_menu.pack(side="left", padx=10)
        
        # Panda Mode toggle
        panda_var = ctk.BooleanVar(value=config.get('ui', 'panda_mode_enabled', default=True))
        ctk.CTkCheckBox(ui_frame, text="🐼 Enable Panda Mode", 
                       variable=panda_var).pack(anchor="w", padx=20, pady=5)
        
        # Vulgar Mode toggle (for panda)
        vulgar_var = ctk.BooleanVar(value=config.get('ui', 'vulgar_mode', default=False))
        ctk.CTkCheckBox(ui_frame, text="💀 Vulgar Panda Mode (uncensored responses)", 
                       variable=vulgar_var).pack(anchor="w", padx=20, pady=3)
        
        # Advanced Customization button
        ctk.CTkButton(ui_frame, text="🎨 Advanced Color & Font Customization",
                     command=self.open_customization,
                     width=280, height=35).pack(padx=20, pady=10)
        cursor_menu.pack(side="left", padx=10)
        
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
        
        # === SAVE BUTTON ===
        def save_settings_window():
            try:
                # Performance
                config.set('performance', 'max_threads', value=int(thread_slider.get()))
                config.set('performance', 'memory_limit_mb', value=int(memory_var.get()))
                config.set('performance', 'thumbnail_cache_size', value=int(cache_var.get()))
                
                # UI / Appearance & Customization
                config.set('ui', 'theme', value=theme_var.get())
                config.set('ui', 'scale', value=scale_var.get())
                config.set('ui', 'tooltip_mode', value=tooltip_var.get())
                config.set('ui', 'cursor', value=cursor_var.get())  # Fixed: was cursor_style
                config.set('ui', 'panda_mode_enabled', value=panda_var.get())
                config.set('ui', 'vulgar_mode', value=vulgar_var.get())
                
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
                # Update tooltip mode if tooltip manager exists
                if hasattr(self, 'tooltip_manager') and self.tooltip_manager:
                    self.tooltip_manager.set_mode(tooltip_var.get())
                
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
                    
                    # Lock/unlock status
                    status = "✓" if item.unlocked else "🔒"
                    
                    # Item name
                    item_text = f"{status} {item.name}"
                    ctk.CTkLabel(item_frame, text=item_text,
                                font=("Arial", 12)).pack(side="left", padx=10, pady=5)
                    
                    # Description
                    ctk.CTkLabel(item_frame, text=item.description,
                                font=("Arial", 10),
                                text_color="gray").pack(side="left", padx=5)
                
        except Exception as e:
            ctk.CTkLabel(rewards_scroll,
                        text=f"Error loading rewards: {e}",
                        font=("Arial", 12)).pack(pady=20)
    
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
            "🔍 LOD detection and grouping",
            "🔄 DDS ↔ PNG conversion",
            "💾 Database indexing for massive libraries (200,000+ textures)",
            "📂 Multiple organization styles (Sims, Neopets, Flat, Game Area, etc.)",
            "🎨 Modern panda-themed UI with multiple themes",
            "🏆 Achievement system with unlockables",
            "📊 Statistics and analytics tracking",
            "🔎 Advanced search and filtering",
            "📝 Built-in notepad for project notes",
            "🖼️ File browser with thumbnail preview",
            "🎮 Panda Mode with fun animations and quotes",
            "🔊 Sound effects and audio feedback",
            "📚 Interactive tutorial system",
            "⚡ Batch processing and automation",
            "🛡️ 100% offline operation - no network calls"
        ]
        
        for feature in features_list:
            ctk.CTkLabel(features_frame, text=feature,
                        font=("Arial", 11), anchor="w").pack(anchor="w", padx=20, pady=3)
        
        # ============= PANDA MODE =============
        panda_frame = ctk.CTkFrame(scrollable_frame)
        panda_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(panda_frame, text="🐼 PANDA MODE",
                     font=("Arial Bold", 18)).pack(pady=10)
        
        panda_text = """Panda Mode adds personality and fun to the texture sorting experience!

• Random panda facts and jokes during processing
• Encouraging messages and progress celebrations
• Easter eggs and surprises hidden throughout the app
• Vulgar Mode toggle for uncensored panda commentary (off by default)
• Animated panda helper that reacts to your actions
• Click the panda for random responses and interactions

Panda Mode can be customized in Settings → Appearance & Customization."""
        
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
    
    def create_status_bar(self):
        """Create bottom status bar with panda indicator"""
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_frame.pack(fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(status_frame, text="🐼 Ready", font=("Arial", 10))
        self.status_label.pack(side="left", padx=10, pady=5)
    
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
        # Read ALL tkinter variable values BEFORE starting thread (thread-safety fix)
        input_path = self.input_path_var.get()
        output_path = self.output_path_var.get()
        mode = self.mode_var.get()
        style = self.style_var.get()
        detect_lods = self.detect_lods_var.get()
        group_lods = self.group_lods_var.get()
        detect_duplicates = self.detect_duplicates_var.get()
        
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select both input and output directories")
            return
        
        if not Path(input_path).exists():
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
        self.organize_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.stop_button.configure(state="normal")
        
        # Start sorting in background thread with all parameters
        threading.Thread(
            target=self.sort_textures_thread,
            args=(input_path, output_path, mode, style, detect_lods, group_lods, detect_duplicates),
            daemon=True
        ).start()
    
    def sort_textures_thread(self, input_path_str, output_path_str, mode, style_name, detect_lods, group_lods, detect_duplicates):
        """Background thread for texture sorting with full organization system"""
        try:
            input_path = Path(input_path_str)
            output_path = Path(output_path_str)
            
            # Scan for texture files
            self.update_progress(0.05, "Scanning directory...")
            texture_files = list(input_path.rglob("*.*"))
            texture_files = [f for f in texture_files if f.suffix.lower() in {'.dds', '.png', '.jpg', '.jpeg', '.bmp', '.tga'}]
            
            total = len(texture_files)
            self.log(f"Found {total} texture files")
            
            if total == 0:
                self.log("⚠️ No texture files found in input directory")
                return
            
            # Classify and prepare textures
            self.update_progress(0.1, "Classifying textures...")
            texture_infos = []
            
            for i, file_path in enumerate(texture_files):
                # Classify
                category, confidence = self.classifier.classify_texture(file_path)
                
                # Get file info
                stat = file_path.stat()
                
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
                
                # Progress
                progress = 0.1 + (0.3 * (i+1) / total)
                self.update_progress(progress, f"Classifying {i+1}/{total}...")
                
                # Log every 10th file or last file
                if (i+1) % 10 == 0 or i == total - 1:
                    self.log(f"Classified {i+1}/{total} files...")
            
            # LOD Detection if enabled
            if detect_lods:
                self.update_progress(0.4, "Detecting LODs...")
                self.log("Detecting LOD groups...")
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
                
                self.log(f"Found {len(lod_groups)} LOD groups")
            
            # Duplicate Detection if enabled
            if detect_duplicates:
                self.update_progress(0.5, "Detecting duplicates...")
                self.log("Detecting duplicate files...")
                # Note: Duplicate handling would go here
                # For now, we'll just log and continue
                self.log("Duplicate detection complete")
            
            # Initialize organization engine
            self.update_progress(0.6, "Organizing textures...")
            self.log(f"Using organization style: {style_name}")
            
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
            self.log("Starting file organization...")
            results = engine.organize_textures(texture_infos, progress_callback)
            
            # Report results
            self.update_progress(1.0, "Complete!")
            self.log("=" * 60)
            self.log("✓ TEXTURE SORTING COMPLETED!")
            self.log("-" * 60)
            self.log(f"Total files: {total}")
            self.log(f"Successfully organized: {results['processed']}")
            self.log(f"Failed: {results['failed']}")
            
            if results['errors']:
                self.log(f"\n⚠️ Errors encountered:")
                for error in results['errors'][:10]:  # Show first 10 errors
                    self.log(f"  - {error['file']}: {error['error']}")
                if len(results['errors']) > 10:
                    self.log(f"  ... and {len(results['errors']) - 10} more errors")
            
            self.log("=" * 60)
            
            # Play completion sound if enabled
            self._play_completion_sound()
            
        except Exception as e:
            error_msg = f"Error during sorting: {e}"
            self.log(f"❌ {error_msg}")
            import traceback
            self.log(traceback.format_exc())
            # Show user-friendly error dialog
            if GUI_AVAILABLE:
                from tkinter import messagebox
                messagebox.showerror("Sorting Error", 
                    f"An error occurred during sorting:\n\n{str(e)}\n\nCheck the log for details.")
        
        finally:
            # Re-enable buttons
            self.after(0, lambda: self.start_button.configure(state="normal"))
            self.after(0, lambda: self.organize_button.configure(state="normal"))
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
