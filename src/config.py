"""
Configuration Management System
Handles all application settings and preferences
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

# Application metadata
APP_NAME = "PS2 Texture Sorter"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Dead On The Inside / JosephsDeadish"

# Default directories
CONFIG_DIR = Path.home() / ".ps2_texture_sorter"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"
LOGS_DIR = CONFIG_DIR / "logs"
THEMES_DIR = CONFIG_DIR / "themes"
DATABASE_FILE = CONFIG_DIR / "textures.db"

# Ensure directories exist
for directory in [CONFIG_DIR, CACHE_DIR, LOGS_DIR, THEMES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Config:
    """Configuration manager for application settings"""
    
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.settings = self._load_default_settings()
        self.load()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default configuration settings"""
        return {
            # UI Settings
            "ui": {
                "theme": "dark",  # dark, light
                "custom_colors": {},
                "cursor": "default",  # default, skull, panda, sword
                "cursor_size": "medium",  # small, medium, large
                "cursor_trail": False,
                "cursor_trail_color": "rainbow",  # rainbow, fire, ice, nature, galaxy, gold
                "tooltip_enabled": True,
                "tooltip_mode": "normal",  # expert, normal, beginner, panda
                "tooltip_delay": 0.5,
                "window_opacity": 1.0,
                "animation_speed": 1.0,
                "font_size": 12,
                "font_family": "Segoe UI",
                "icon_size": "medium",
                "compact_view": False,
                "layout": "default",
                "show_thumbnails": True,
                "thumbnail_size": 32,  # 16, 32, or 64
                "disable_panda_animations": False
            },
            
            # Performance Settings
            "performance": {
                "max_threads": 4,
                "memory_limit_mb": 2048,
                "cache_size_mb": 512,
                "enable_gpu": False,
                "background_priority": "normal",
                "batch_size": 100,
                "preview_quality": "medium",
                "thumbnail_cache_size": 500
            },
            
            # File Handling Settings
            "file_handling": {
                "overwrite_existing": False,
                "create_backup": True,
                "auto_save_interval": 300,  # seconds
                "undo_history_depth": 50,
                "min_file_size_kb": 0,
                "max_file_size_mb": 0,  # 0 = no limit
                "file_patterns_include": [],
                "file_patterns_exclude": []
            },
            
            # Sorting Preferences
            "sorting": {
                "mode": "automatic",  # automatic, manual, suggested
                "organization_style": "neopets",  # sims, neopets, flat, etc.
                "group_by": "type",  # type, function, area, resolution, etc.
                "sort_order": "name",  # name, date, size, type
                "custom_categories": [],
                "category_mappings": {},
                "detect_lods": True,
                "group_lods": True,
                "detect_variants": True
            },
            
            # Logging & Debugging
            "logging": {
                "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
                "auto_export_logs": True,
                "enable_crash_reports": True,
                "show_performance_metrics": False,
                "debug_mode": False
            },
            
            # Notifications
            "notifications": {
                "sound_enabled": True,
                "custom_sounds": {},
                "system_notifications": True,
                "completion_alerts": True,
                "error_popups": True
            },
            
            # Sound Settings (separate from notifications)
            "sound": {
                "enabled": True,
                "master_volume": 1.0,
                "effects_volume": 1.0,
                "notifications_volume": 1.0,
                "sound_pack": "default",
                "muted_sounds": {}
            },
            
            # Panda Character Settings
            "panda": {
                "name": "Panda",
                "gender": "non_binary",  # male, female, non_binary
                "position_x": 0.98,  # Relative position (0.0 to 1.0)
                "position_y": 0.98,  # Relative position (0.0 to 1.0)
                "enabled": True
            },
            
            # Session Management
            "session": {
                "auto_save_state": True,
                "enable_recovery": True,
                "bookmarks": [],
                "recent_projects": [],
                "last_input_directory": "",
                "last_output_directory": ""
            },
            
            # Classification Settings
            "classification": {
                "confidence_threshold": 0.6,
                "use_filename_patterns": True,
                "use_image_analysis": True,
                "use_metadata": True,
                "custom_rules": []
            },
            
            # AI Model Settings
            "ai": {
                # Offline AI Model (ONNX-based)
                "offline": {
                    "enabled": True,
                    "model_path": "",  # Empty = use default
                    "num_threads": 4,
                    "confidence_weight": 0.7,  # How much to trust offline model (0-1)
                    "use_image_analysis": True,  # Use AI for image content analysis
                    "batch_size": 32,  # Number of images to process at once
                    "cache_predictions": True
                },
                # Online AI Model (API-based)
                "online": {
                    "enabled": False,
                    "api_key": "",
                    "api_url": "https://api.openai.com/v1",
                    "model": "clip-vit-base-patch32",
                    "timeout": 30,
                    "max_requests_per_minute": 60,
                    "max_requests_per_hour": 1000,
                    "confidence_weight": 0.8,  # How much to trust online model (0-1)
                    "use_for_difficult_images": True,  # Use online AI when offline has low confidence
                    "low_confidence_threshold": 0.5  # Threshold to trigger online fallback
                },
                # AI Blending Settings
                "blend_mode": "confidence_weighted",  # confidence_weighted, max, average, offline_only, online_only
                "min_confidence": 0.3,  # Minimum confidence to accept a prediction
                "prefer_image_content": True  # Prioritize image content analysis over filename patterns
            },
            
            # Hotkey Settings
            "hotkeys": {
                "enabled": True,
                "config_file": "",  # Path to custom hotkey config, empty = use defaults
                "global_hotkeys_enabled": False  # Enable hotkeys when app is not focused
            }
        }
    
    def load(self):
        """Load settings from config file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._merge_settings(self.settings, loaded_settings)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
    
    def save(self):
        """Save current settings to config file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _merge_settings(self, default: dict, loaded: dict):
        """Recursively merge loaded settings with defaults"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value
    
    def get(self, *keys, default=None):
        """Get a setting value by hierarchical keys"""
        value = self.settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, *keys, value):
        """Set a setting value by hierarchical keys"""
        settings = self.settings
        for key in keys[:-1]:
            if key not in settings:
                settings[key] = {}
            settings = settings[key]
        settings[keys[-1]] = value
        self.save()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self._load_default_settings()
        self.save()


# Global configuration instance
config = Config()
