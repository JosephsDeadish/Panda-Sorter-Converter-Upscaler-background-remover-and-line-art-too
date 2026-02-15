"""
Hotkey Manager - Customizable keyboard shortcuts
Supports global hotkeys and conflict detection
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from typing import Dict, Callable, Optional, List, Tuple, Set
from dataclasses import dataclass, field
import threading
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import pynput for global hotkeys
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    logger.warning("pynput not available - global hotkeys disabled")


@dataclass
class Hotkey:
    """Represents a keyboard shortcut."""
    name: str
    key_combination: str
    description: str
    callback: Optional[Callable] = None
    enabled: bool = True
    is_global: bool = False
    category: str = "general"
    
    def __hash__(self):
        return hash((self.name, self.key_combination))


class HotkeyManager:
    """Manages keyboard shortcuts with customization and conflict detection."""
    
    # Default hotkey definitions
    DEFAULT_HOTKEYS = {
        # File operations
        'open_files': ('Ctrl+O', 'Open files', 'file', False),
        'save_results': ('Ctrl+S', 'Save results', 'file', False),
        'export_data': ('Ctrl+E', 'Export data', 'file', False),
        'close_app': ('Alt+F4', 'Close application', 'file', False),
        
        # Processing operations
        'start_processing': ('Ctrl+P', 'Start processing', 'processing', False),
        'pause_processing': ('Ctrl+Shift+P', 'Pause processing', 'processing', False),
        'stop_processing': ('Ctrl+Shift+S', 'Stop processing', 'processing', False),
        'resume_processing': ('Ctrl+R', 'Resume processing', 'processing', False),
        
        # View operations
        'toggle_preview': ('Ctrl+T', 'Toggle preview panel', 'view', False),
        'refresh_view': ('F5', 'Refresh view', 'view', False),
        'fullscreen': ('F11', 'Toggle fullscreen', 'view', False),
        'toggle_sidebar': ('Ctrl+B', 'Toggle sidebar', 'view', False),
        
        # Navigation
        'next_texture': ('Right', 'Next texture', 'navigation', False),
        'prev_texture': ('Left', 'Previous texture', 'navigation', False),
        'first_texture': ('Home', 'First texture', 'navigation', False),
        'last_texture': ('End', 'Last texture', 'navigation', False),
        
        # Selection
        'select_all': ('Ctrl+A', 'Select all', 'selection', False),
        'deselect_all': ('Ctrl+D', 'Deselect all', 'selection', False),
        'invert_selection': ('Ctrl+I', 'Invert selection', 'selection', False),
        
        # Tools
        'search': ('Ctrl+F', 'Search', 'tools', False),
        'filter': ('Ctrl+Shift+F', 'Filter', 'tools', False),
        'settings': ('Ctrl+,', 'Settings', 'tools', False),
        'statistics': ('Ctrl+Shift+T', 'Statistics', 'tools', False),
        
        # Special features
        'achievements': ('Ctrl+Shift+A', 'View achievements', 'special', False),
        'sound_toggle': ('Ctrl+M', 'Toggle sound', 'special', False),
        
        # Global hotkeys (work when app is not focused)
        'global_start': ('Ctrl+Alt+P', 'Global start processing', 'global', True),
        'global_pause': ('Ctrl+Alt+Space', 'Global pause', 'global', True),
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize hotkey manager.
        
        Args:
            config_file: Path to hotkey configuration file
        """
        self.hotkeys: Dict[str, Hotkey] = {}
        self.key_to_name: Dict[str, str] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.config_file = config_file
        self.lock = threading.Lock()
        self.global_listener: Optional[keyboard.GlobalHotKeys] = None
        self.enabled = True
        
        # Initialize with defaults
        self._load_defaults()
        
        # Load custom configuration if provided
        if config_file:
            self.load_config(config_file)
    
    def _load_defaults(self) -> None:
        """Load default hotkey definitions."""
        for name, (key_combo, desc, category, is_global) in self.DEFAULT_HOTKEYS.items():
            self.register_hotkey(
                name=name,
                key_combination=key_combo,
                description=desc,
                category=category,
                is_global=is_global
            )
    
    def register_hotkey(
        self,
        name: str,
        key_combination: str,
        description: str = "",
        callback: Optional[Callable] = None,
        category: str = "general",
        is_global: bool = False,
        enabled: bool = True
    ) -> bool:
        """
        Register a new hotkey.
        
        Args:
            name: Unique hotkey name
            key_combination: Key combination string (e.g., "Ctrl+S")
            description: Human-readable description
            callback: Function to call when hotkey is triggered
            category: Hotkey category for organization
            is_global: Whether hotkey works when app is not focused
            enabled: Whether hotkey is enabled
            
        Returns:
            True if registered successfully
        """
        with self.lock:
            try:
                # Check for conflicts
                if self.has_conflict(key_combination, exclude_name=name):
                    logger.warning(
                        f"Hotkey conflict: {key_combination} already registered"
                    )
                    return False
                
                # Create hotkey object
                hotkey = Hotkey(
                    name=name,
                    key_combination=key_combination,
                    description=description,
                    callback=callback,
                    enabled=enabled,
                    is_global=is_global,
                    category=category
                )
                
                # Register
                self.hotkeys[name] = hotkey
                self.key_to_name[key_combination] = name
                
                if callback:
                    self.callbacks[name] = callback
                
                logger.debug(f"Registered hotkey: {name} ({key_combination})")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register hotkey {name}: {e}")
                return False
    
    def unregister_hotkey(self, name: str) -> bool:
        """
        Unregister a hotkey.
        
        Args:
            name: Hotkey name to unregister
            
        Returns:
            True if unregistered successfully
        """
        with self.lock:
            if name not in self.hotkeys:
                logger.warning(f"Hotkey not found: {name}")
                return False
            
            hotkey = self.hotkeys[name]
            
            # Remove from mappings
            if hotkey.key_combination in self.key_to_name:
                del self.key_to_name[hotkey.key_combination]
            
            if name in self.callbacks:
                del self.callbacks[name]
            
            del self.hotkeys[name]
            
            logger.debug(f"Unregistered hotkey: {name}")
            return True
    
    def rebind_hotkey(self, name: str, new_key_combination: str) -> bool:
        """
        Change the key combination for a hotkey.
        
        Args:
            name: Hotkey name
            new_key_combination: New key combination
            
        Returns:
            True if rebound successfully
        """
        with self.lock:
            if name not in self.hotkeys:
                logger.error(f"Hotkey not found: {name}")
                return False
            
            # Check for conflicts
            if self.has_conflict(new_key_combination, exclude_name=name):
                logger.warning(
                    f"Cannot rebind to {new_key_combination}: already in use"
                )
                return False
            
            hotkey = self.hotkeys[name]
            old_key = hotkey.key_combination
            
            # Update mappings
            if old_key in self.key_to_name:
                del self.key_to_name[old_key]
            
            hotkey.key_combination = new_key_combination
            self.key_to_name[new_key_combination] = name
            
            logger.info(f"Rebound {name}: {old_key} -> {new_key_combination}")
            return True
    
    def set_callback(self, name: str, callback: Callable) -> bool:
        """
        Set or update callback for a hotkey.
        
        Args:
            name: Hotkey name
            callback: Callback function
            
        Returns:
            True if set successfully
        """
        with self.lock:
            if name not in self.hotkeys:
                logger.error(f"Hotkey not found: {name}")
                return False
            
            self.hotkeys[name].callback = callback
            self.callbacks[name] = callback
            return True
    
    def trigger_hotkey(self, name: str) -> bool:
        """
        Manually trigger a hotkey callback.
        
        Args:
            name: Hotkey name to trigger
            
        Returns:
            True if triggered successfully
        """
        with self.lock:
            if name not in self.hotkeys:
                logger.warning(f"Hotkey not found: {name}")
                return False
            
            hotkey = self.hotkeys[name]
            
            if not hotkey.enabled:
                logger.debug(f"Hotkey {name} is disabled")
                return False
            
            if not self.enabled:
                logger.debug("Hotkey manager is disabled")
                return False
            
            if name in self.callbacks:
                try:
                    logger.debug(f"Triggering hotkey: {name}")
                    self.callbacks[name]()
                    return True
                except Exception as e:
                    logger.error(f"Error executing hotkey {name}: {e}")
                    return False
            
            logger.debug(f"No callback for hotkey: {name}")
            return False
    
    def has_conflict(self, key_combination: str, exclude_name: Optional[str] = None) -> bool:
        """
        Check if key combination conflicts with existing hotkeys.
        
        Args:
            key_combination: Key combination to check
            exclude_name: Optional hotkey name to exclude from check
            
        Returns:
            True if conflict exists
        """
        if key_combination not in self.key_to_name:
            return False
        
        existing_name = self.key_to_name[key_combination]
        return existing_name != exclude_name
    
    def get_hotkey(self, name: str) -> Optional[Hotkey]:
        """
        Get hotkey by name.
        
        Args:
            name: Hotkey name
            
        Returns:
            Hotkey object or None
        """
        return self.hotkeys.get(name)
    
    def get_all_hotkeys(self) -> List[Hotkey]:
        """
        Get all registered hotkeys.
        
        Returns:
            List of hotkeys
        """
        return list(self.hotkeys.values())
    
    def get_hotkeys_by_category(self, category: str) -> List[Hotkey]:
        """
        Get hotkeys in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of hotkeys in category
        """
        return [hk for hk in self.hotkeys.values() if hk.category == category]
    
    def get_categories(self) -> Set[str]:
        """
        Get all hotkey categories.
        
        Returns:
            Set of category names
        """
        return {hk.category for hk in self.hotkeys.values()}
    
    def enable_hotkey(self, name: str) -> bool:
        """
        Enable a hotkey.
        
        Args:
            name: Hotkey name
            
        Returns:
            True if enabled
        """
        with self.lock:
            if name not in self.hotkeys:
                return False
            
            self.hotkeys[name].enabled = True
            logger.debug(f"Enabled hotkey: {name}")
            return True
    
    def disable_hotkey(self, name: str) -> bool:
        """
        Disable a hotkey.
        
        Args:
            name: Hotkey name
            
        Returns:
            True if disabled
        """
        with self.lock:
            if name not in self.hotkeys:
                return False
            
            self.hotkeys[name].enabled = False
            logger.debug(f"Disabled hotkey: {name}")
            return True
    
    def enable_all(self) -> None:
        """Enable all hotkeys."""
        with self.lock:
            self.enabled = True
            logger.info("Enabled all hotkeys")
    
    def disable_all(self) -> None:
        """Disable all hotkeys."""
        with self.lock:
            self.enabled = False
            logger.info("Disabled all hotkeys")
    
    def start_global_hotkeys(self) -> bool:
        """
        Start listening for global hotkeys.
        
        Returns:
            True if started successfully
        """
        if not PYNPUT_AVAILABLE:
            logger.warning("Cannot start global hotkeys: pynput not available")
            return False
        
        try:
            # Build global hotkey mappings
            global_mappings = {}
            
            for name, hotkey in self.hotkeys.items():
                if hotkey.is_global and hotkey.enabled and name in self.callbacks:
                    # Convert our format to pynput format
                    pynput_key = self._convert_to_pynput_format(
                        hotkey.key_combination
                    )
                    if pynput_key:
                        global_mappings[pynput_key] = self.callbacks[name]
            
            if not global_mappings:
                logger.info("No global hotkeys to register")
                return True
            
            # Start global listener
            self.global_listener = keyboard.GlobalHotKeys(global_mappings)
            self.global_listener.start()
            
            logger.info(f"Started global hotkey listener with {len(global_mappings)} hotkeys")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start global hotkeys: {e}")
            return False
    
    def stop_global_hotkeys(self) -> None:
        """Stop listening for global hotkeys."""
        if self.global_listener:
            try:
                self.global_listener.stop()
                self.global_listener = None
                logger.info("Stopped global hotkey listener")
            except Exception as e:
                logger.error(f"Error stopping global hotkeys: {e}")
    
    def _convert_to_pynput_format(self, key_combination: str) -> Optional[str]:
        """
        Convert our key format to pynput format.
        
        Args:
            key_combination: Our format (e.g., "Ctrl+Alt+P")
            
        Returns:
            Pynput format string or None if invalid
        """
        try:
            # Simple conversion - may need more sophisticated handling
            parts = key_combination.split('+')
            pynput_parts = []
            
            for part in parts:
                part_lower = part.lower().strip()
                
                # Map common key names
                key_map = {
                    'ctrl': '<ctrl>',
                    'control': '<ctrl>',
                    'alt': '<alt>',
                    'shift': '<shift>',
                    'cmd': '<cmd>',
                    'win': '<cmd>',
                }
                
                if part_lower in key_map:
                    pynput_parts.append(key_map[part_lower])
                else:
                    pynput_parts.append(part_lower)
            
            return '+'.join(pynput_parts)
            
        except Exception as e:
            logger.error(f"Failed to convert key format: {e}")
            return None
    
    def load_config(self, config_file: str) -> bool:
        """
        Load hotkey configuration from JSON file.
        
        Args:
            config_file: Path to configuration file (empty string uses defaults)
            
        Returns:
            True if config was loaded successfully, False if no config specified or loading failed
        """
        try:
            # Return silently if no config file specified (empty/whitespace means use defaults)
            if not config_file or not config_file.strip():
                return False
            
            path = Path(config_file)
            
            if not path.exists():
                logger.warning(f"Config file not found: {config_file}")
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Apply custom bindings
            for name, key_combo in config_data.get('bindings', {}).items():
                if name in self.hotkeys:
                    self.rebind_hotkey(name, key_combo)
            
            # Apply enabled/disabled states
            for name, enabled in config_data.get('enabled', {}).items():
                if name in self.hotkeys:
                    if enabled:
                        self.enable_hotkey(name)
                    else:
                        self.disable_hotkey(name)
            
            logger.info(f"Loaded hotkey configuration from {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load hotkey config: {e}")
            return False
    
    def save_config(self, config_file: str) -> bool:
        """
        Save hotkey configuration to JSON file.
        
        Args:
            config_file: Path to save configuration
            
        Returns:
            True if saved successfully
        """
        try:
            # Build configuration data
            config_data = {
                'version': '1.0',
                'bindings': {},
                'enabled': {}
            }
            
            for name, hotkey in self.hotkeys.items():
                config_data['bindings'][name] = hotkey.key_combination
                config_data['enabled'][name] = hotkey.enabled
            
            # Save to file
            path = Path(config_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Saved hotkey configuration to {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save hotkey config: {e}")
            return False
    
    def get_settings_panel_data(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get hotkey data formatted for settings panel UI.
        
        Returns:
            Dictionary mapping categories to hotkey info
        """
        panel_data = {}
        
        for category in sorted(self.get_categories()):
            hotkeys = self.get_hotkeys_by_category(category)
            
            panel_data[category] = [
                {
                    'name': hk.name,
                    'key': hk.key_combination,
                    'description': hk.description,
                    'enabled': hk.enabled,
                    'is_global': hk.is_global
                }
                for hk in sorted(hotkeys, key=lambda h: h.name)
            ]
        
        return panel_data
    
    def reset_to_defaults(self) -> None:
        """Reset all hotkeys to default bindings."""
        with self.lock:
            self.hotkeys.clear()
            self.key_to_name.clear()
            self.callbacks.clear()
            self._load_defaults()
            logger.info("Reset hotkeys to defaults")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop_global_hotkeys()
