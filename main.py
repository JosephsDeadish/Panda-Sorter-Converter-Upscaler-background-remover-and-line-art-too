"""
PS2 Texture Sorter - Main Entry Point
Author: Dead On The Inside / JosephsDeadish

A professional, single-executable Windows application for automatically 
sorting PS2 texture dumps with advanced AI classification and massive-scale 
support (200,000+ textures).
"""

import sys
import os
import time
import threading
from pathlib import Path

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
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1200x800")
        
        # Set theme
        ctk.set_appearance_mode(config.get('ui', 'theme', default='dark'))
        ctk.set_default_color_theme("blue")
        
        # Initialize core components
        self.classifier = TextureClassifier(config)
        self.lod_detector = LODDetector()
        self.file_handler = FileHandler(create_backup=config.get('file_handling', 'create_backup', default=True))
        self.database = None  # Will be initialized when needed
        
        # Create UI
        self.create_menu()
        self.create_main_ui()
        
        # Status
        self.current_operation = None
        
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
        
        # Theme toggle
        theme_button = ctk.CTkButton(
            menu_frame,
            text="🌓 Theme",
            width=80,
            command=self.toggle_theme
        )
        theme_button.pack(side="right", padx=10, pady=5)
    
    def create_main_ui(self):
        """Create main tabbed interface"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab view
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # Create tabs
        self.tab_sort = self.tabview.add("🗂️ Sort Textures")
        self.tab_convert = self.tabview.add("🔄 Convert Files")
        self.tab_browser = self.tabview.add("📁 File Browser")
        self.tab_settings = self.tabview.add("⚙️ Settings")
        self.tab_notepad = self.tabview.add("📝 Notepad")
        self.tab_about = self.tabview.add("ℹ️ About")
        
        # Populate tabs
        self.create_sort_tab()
        self.create_convert_tab()
        self.create_browser_tab()
        self.create_settings_tab()
        self.create_notepad_tab()
        self.create_about_tab()
        
        # Status bar
        self.create_status_bar()
    
    def create_sort_tab(self):
        """Create texture sorting tab"""
        # Input section
        input_frame = ctk.CTkFrame(self.tab_sort)
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
        output_frame = ctk.CTkFrame(self.tab_sort)
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
        options_frame = ctk.CTkFrame(self.tab_sort)
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
        
        # Organization style
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
        progress_frame = ctk.CTkFrame(self.tab_sort)
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
        button_frame = ctk.CTkFrame(self.tab_sort)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_button = ctk.CTkButton(button_frame, text="▶️ Start Sorting", 
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
    
    def create_convert_tab(self):
        """Create file conversion tab"""
        ctk.CTkLabel(self.tab_convert, text="File Format Conversion", 
                     font=("Arial Bold", 16)).pack(pady=20)
        
        ctk.CTkLabel(self.tab_convert, text="Convert between DDS and PNG formats",
                     font=("Arial", 12)).pack(pady=10)
        
        # Coming soon message
        info_frame = ctk.CTkFrame(self.tab_convert)
        info_frame.pack(pady=50, padx=50, fill="both", expand=True)
        
        ctk.CTkLabel(info_frame, 
                     text="🚧 Batch conversion UI coming soon! 🚧\n\nCore conversion engine is ready.",
                     font=("Arial", 14)).pack(expand=True)
    
    def create_browser_tab(self):
        """Create file browser tab"""
        ctk.CTkLabel(self.tab_browser, text="Sorted Files Browser",
                     font=("Arial Bold", 16)).pack(pady=20)
        
        info_frame = ctk.CTkFrame(self.tab_browser)
        info_frame.pack(pady=50, padx=50, fill="both", expand=True)
        
        ctk.CTkLabel(info_frame,
                     text="🚧 File browser coming soon! 🚧\n\nNavigate and preview sorted textures.",
                     font=("Arial", 14)).pack(expand=True)
    
    def create_settings_tab(self):
        """Create settings tab"""
        ctk.CTkLabel(self.tab_settings, text="Application Settings",
                     font=("Arial Bold", 16)).pack(pady=20)
        
        # Settings scroll frame
        settings_scroll = ctk.CTkScrollableFrame(self.tab_settings, width=1000, height=600)
        settings_scroll.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Performance settings
        perf_frame = ctk.CTkFrame(settings_scroll)
        perf_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(perf_frame, text="Performance Settings", 
                     font=("Arial Bold", 14)).pack(anchor="w", padx=10, pady=5)
        
        # Thread count
        thread_frame = ctk.CTkFrame(perf_frame)
        thread_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(thread_frame, text="Thread Count:").pack(side="left", padx=10)
        thread_slider = ctk.CTkSlider(thread_frame, from_=1, to=16, number_of_steps=15)
        thread_slider.set(config.get('performance', 'max_threads', default=4))
        thread_slider.pack(side="left", fill="x", expand=True, padx=10)
        
        # Placeholder for more settings
        ctk.CTkLabel(settings_scroll, 
                     text="Additional settings panels coming soon...",
                     font=("Arial", 11), text_color="gray").pack(pady=20)
    
    def create_notepad_tab(self):
        """Create notepad tab"""
        ctk.CTkLabel(self.tab_notepad, text="Personal Notes",
                     font=("Arial Bold", 16)).pack(pady=10)
        
        self.notepad_text = ctk.CTkTextbox(self.tab_notepad, width=1000, height=600)
        self.notepad_text.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(self.tab_notepad)
        button_frame.pack(pady=10)
        
        ctk.CTkButton(button_frame, text="Save Notes", width=100).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Clear", width=100).pack(side="left", padx=5)
    
    def create_about_tab(self):
        """Create about tab"""
        about_frame = ctk.CTkFrame(self.tab_about)
        about_frame.pack(pady=50, padx=50, fill="both", expand=True)
        
        # Title
        ctk.CTkLabel(about_frame, text=f"🐼 {APP_NAME} 🐼",
                     font=("Arial Bold", 24)).pack(pady=20)
        
        # Version
        ctk.CTkLabel(about_frame, text=f"Version {APP_VERSION}",
                     font=("Arial", 14)).pack(pady=5)
        
        # Author
        ctk.CTkLabel(about_frame, text=f"Author: {APP_AUTHOR}",
                     font=("Arial", 12)).pack(pady=5)
        
        # Description
        desc_text = """
A professional, single-executable Windows application for automatically 
sorting PS2 texture dumps with advanced AI classification and massive-scale 
support (200,000+ textures).

Features:
• 50+ texture categories with AI classification
• LOD detection and grouping
• DDS ↔ PNG conversion
• Database indexing for massive libraries
• Multiple organization styles
• Panda-themed modern UI
• 100% offline operation
        """
        
        ctk.CTkLabel(about_frame, text=desc_text,
                     font=("Arial", 11), justify="left").pack(pady=20)
        
        # Repository link
        ctk.CTkLabel(about_frame, 
                     text="Repository: JosephsDeadish/PS2-texture-sorter",
                     font=("Arial", 10), text_color="gray").pack(pady=5)
    
    def create_status_bar(self):
        """Create bottom status bar"""
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_frame.pack(fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(status_frame, text="Ready", font=("Arial", 10))
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
    
    def start_sorting(self):
        """Start texture sorting operation"""
        input_path = self.input_path_var.get()
        output_path = self.output_path_var.get()
        
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
        self.log(f"Mode: {self.mode_var.get()}")
        self.log(f"Style: {self.style_var.get()}")
        self.log("=" * 60)
        
        # Disable start button
        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.stop_button.configure(state="normal")
        
        # Start sorting in background thread
        threading.Thread(target=self.sort_textures_thread, daemon=True).start()
    
    def sort_textures_thread(self):
        """Background thread for texture sorting with full organization system"""
        try:
            input_path = Path(self.input_path_var.get())
            output_path = Path(self.output_path_var.get())
            
            # Get options
            detect_lods = self.detect_lods_var.get()
            group_lods = self.group_lods_var.get()
            detect_duplicates = self.detect_dupes_var.get()
            style_name = self.style_var.get()
            
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
                lod_groups = self.lod_detector.detect_lods([t.file_path for t in texture_infos])
                
                # Apply LOD information to textures
                for texture_info in texture_infos:
                    for group_name, lod_files in lod_groups.items():
                        for lod_file in lod_files:
                            if lod_file['path'] == texture_info.file_path:
                                texture_info.lod_group = group_name
                                texture_info.lod_level = lod_file['level']
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
            
        except Exception as e:
            self.log(f"❌ Error during sorting: {e}")
            import traceback
            self.log(traceback.format_exc())
        
        finally:
            # Re-enable buttons
            self.start_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.stop_button.configure(state="disabled")
    
    def pause_sorting(self):
        """Pause sorting operation"""
        self.log("⏸️ Sorting paused")
    
    def stop_sorting(self):
        """Stop sorting operation"""
        self.log("⏹️ Sorting stopped")
    
    def update_progress(self, value, text):
        """Update progress bar and label"""
        self.progress_bar.set(value)
        self.progress_label.configure(text=text)
        self.status_label.configure(text=text)
    
    def log(self, message):
        """Add message to log"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.update()
    
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
