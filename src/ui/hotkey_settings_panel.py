"""
Hotkey Settings Panel - UI for customizing keyboard shortcuts
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import tkinter as tk
from typing import Optional, Dict, Callable
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from src.features.hotkey_manager import HotkeyManager

logger = logging.getLogger(__name__)


class HotkeySettingsPanel(ctk.CTkFrame if ctk else tk.Frame):
    """Panel for viewing and customizing keyboard shortcuts."""
    
    def __init__(self, parent, hotkey_manager: HotkeyManager, **kwargs):
        """
        Initialize hotkey settings panel.
        
        Args:
            parent: Parent widget
            hotkey_manager: HotkeyManager instance
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.hotkey_manager = hotkey_manager
        self.editing_hotkey = None
        self.hotkey_widgets = {}
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_widgets()
        self._populate_hotkeys()
    
    def _create_widgets(self):
        """Create UI widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="⌨️ Keyboard Shortcuts",
            font=("Arial", 18, "bold")
        ) if ctk else tk.Label(
            self,
            text="⌨️ Keyboard Shortcuts",
            font=("Arial", 18, "bold")
        )
        header.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Scrollable frame for hotkeys
        if ctk:
            self.scrollable_frame = ctk.CTkScrollableFrame(self)
        else:
            # Fallback for regular tkinter
            canvas = tk.Canvas(self)
            scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
            self.scrollable_frame = tk.Frame(canvas)
            
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.grid(row=1, column=0, sticky="nsew", padx=20)
            scrollbar.grid(row=1, column=1, sticky="ns")
        
        if ctk:
            self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        # Button frame
        button_frame = ctk.CTkFrame(self) if ctk else tk.Frame(self)
        button_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # Reset button
        reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults
        ) if ctk else tk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults
        )
        reset_btn.pack(side="left", padx=5)
        
        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Configuration",
            command=self._save_config
        ) if ctk else tk.Button(
            button_frame,
            text="Save Configuration",
            command=self._save_config
        )
        save_btn.pack(side="left", padx=5)
    
    def _populate_hotkeys(self):
        """Populate the panel with current hotkeys."""
        # Get hotkeys grouped by category
        panel_data = self.hotkey_manager.get_settings_panel_data()
        
        row = 0
        for category, hotkeys in panel_data.items():
            # Category header
            category_label = ctk.CTkLabel(
                self.scrollable_frame,
                text=f"📁 {category.replace('_', ' ').title()}",
                font=("Arial", 14, "bold")
            ) if ctk else tk.Label(
                self.scrollable_frame,
                text=f"📁 {category.replace('_', ' ').title()}",
                font=("Arial", 14, "bold")
            )
            category_label.grid(row=row, column=0, columnspan=4, sticky="w", pady=(15, 5))
            row += 1
            
            # Hotkeys in this category
            for hk in hotkeys:
                self._add_hotkey_row(row, hk)
                row += 1
    
    def _add_hotkey_row(self, row: int, hotkey_data: Dict):
        """
        Add a row for a single hotkey.
        
        Args:
            row: Grid row number
            hotkey_data: Hotkey information dictionary
        """
        name = hotkey_data['name']
        
        # Description label
        desc_label = ctk.CTkLabel(
            self.scrollable_frame,
            text=hotkey_data['description'],
            anchor="w"
        ) if ctk else tk.Label(
            self.scrollable_frame,
            text=hotkey_data['description'],
            anchor="w"
        )
        desc_label.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        
        # Key combination label/entry
        key_var = tk.StringVar(value=hotkey_data['key'])
        key_entry = ctk.CTkEntry(
            self.scrollable_frame,
            textvariable=key_var,
            width=150,
            state="readonly"
        ) if ctk else tk.Entry(
            self.scrollable_frame,
            textvariable=key_var,
            width=20,
            state="readonly"
        )
        key_entry.grid(row=row, column=1, padx=5, pady=2)
        
        # Edit button
        edit_btn = ctk.CTkButton(
            self.scrollable_frame,
            text="Edit",
            width=60,
            command=lambda: self._edit_hotkey(name, key_var)
        ) if ctk else tk.Button(
            self.scrollable_frame,
            text="Edit",
            command=lambda: self._edit_hotkey(name, key_var)
        )
        edit_btn.grid(row=row, column=2, padx=5, pady=2)
        
        # Enable/disable checkbox
        enabled_var = tk.BooleanVar(value=hotkey_data['enabled'])
        enabled_cb = ctk.CTkCheckBox(
            self.scrollable_frame,
            text="Enabled",
            variable=enabled_var,
            command=lambda: self._toggle_hotkey(name, enabled_var.get())
        ) if ctk else tk.Checkbutton(
            self.scrollable_frame,
            text="Enabled",
            variable=enabled_var,
            command=lambda: self._toggle_hotkey(name, enabled_var.get())
        )
        enabled_cb.grid(row=row, column=3, padx=5, pady=2)
        
        # Global indicator
        if hotkey_data['is_global']:
            global_label = ctk.CTkLabel(
                self.scrollable_frame,
                text="🌐",
                text_color="blue" if ctk else None
            ) if ctk else tk.Label(
                self.scrollable_frame,
                text="🌐",
                fg="blue"
            )
            global_label.grid(row=row, column=4, padx=2, pady=2)
        
        # Store widgets
        self.hotkey_widgets[name] = {
            'key_var': key_var,
            'enabled_var': enabled_var
        }
    
    def _edit_hotkey(self, name: str, key_var: tk.StringVar):
        """
        Open dialog to edit a hotkey.
        
        Args:
            name: Hotkey name
            key_var: Variable holding the key combination
        """
        dialog = HotkeyEditDialog(
            self,
            name,
            key_var.get(),
            self._on_hotkey_edited
        )
        dialog.wait_window()
    
    def _on_hotkey_edited(self, name: str, new_key: str):
        """
        Handle hotkey edit completion.
        
        Args:
            name: Hotkey name
            new_key: New key combination
        """
        if self.hotkey_manager.rebind_hotkey(name, new_key):
            self.hotkey_widgets[name]['key_var'].set(new_key)
            logger.info(f"Rebound hotkey {name} to {new_key}")
        else:
            logger.warning(f"Failed to rebind hotkey {name}")
    
    def _toggle_hotkey(self, name: str, enabled: bool):
        """
        Enable or disable a hotkey.
        
        Args:
            name: Hotkey name
            enabled: Whether to enable
        """
        if enabled:
            self.hotkey_manager.enable_hotkey(name)
        else:
            self.hotkey_manager.disable_hotkey(name)
        
        logger.debug(f"Hotkey {name} {'enabled' if enabled else 'disabled'}")
    
    def _reset_to_defaults(self):
        """Reset all hotkeys to default bindings."""
        self.hotkey_manager.reset_to_defaults()
        
        # Refresh display
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self._populate_hotkeys()
        logger.info("Reset hotkeys to defaults")
    
    def _save_config(self):
        """Save current hotkey configuration."""
        from pathlib import Path
        import os
        
        # Save to user config directory
        config_dir = Path.home() / '.ps2_texture_sorter'
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / 'hotkeys.json'
        
        if self.hotkey_manager.save_config(str(config_file)):
            logger.info(f"Saved hotkey configuration to {config_file}")
            
            # Show success message
            if ctk:
                success_label = ctk.CTkLabel(
                    self,
                    text="✓ Configuration saved!",
                    text_color="green"
                )
            else:
                success_label = tk.Label(
                    self,
                    text="✓ Configuration saved!",
                    fg="green"
                )
            success_label.grid(row=3, column=0, pady=5)
            
            # Remove after 2 seconds
            self.after(2000, success_label.destroy)


class HotkeyEditDialog(tk.Toplevel):
    """Dialog for editing a hotkey binding."""
    
    def __init__(self, parent, hotkey_name: str, current_key: str, callback: Callable):
        """
        Initialize hotkey edit dialog.
        
        Args:
            parent: Parent widget
            hotkey_name: Name of hotkey being edited
            current_key: Current key combination
            callback: Callback when editing is complete
        """
        super().__init__(parent)
        
        self.hotkey_name = hotkey_name
        self.current_key = current_key
        self.callback = callback
        self.new_key = None
        self.keys_pressed = []
        
        self.title(f"Edit Hotkey: {hotkey_name}")
        self.geometry("400x200")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Bind key events
        self.bind("<KeyPress>", self._on_key_press)
        self.bind("<KeyRelease>", self._on_key_release)
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Instruction label
        instruction = tk.Label(
            self,
            text=f"Press new key combination for:\n{self.hotkey_name}",
            font=("Arial", 12)
        )
        instruction.pack(pady=20)
        
        # Current key display
        current_label = tk.Label(
            self,
            text=f"Current: {self.current_key}",
            font=("Arial", 10),
            fg="gray"
        )
        current_label.pack(pady=5)
        
        # New key display
        self.new_key_var = tk.StringVar(value="Press keys...")
        new_key_label = tk.Label(
            self,
            textvariable=self.new_key_var,
            font=("Arial", 14, "bold")
        )
        new_key_label.pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)
        
        # Save button
        save_btn = tk.Button(
            button_frame,
            text="Save",
            command=self._save
        )
        save_btn.pack(side="left", padx=5)
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy
        )
        cancel_btn.pack(side="left", padx=5)
    
    def _on_key_press(self, event):
        """Handle key press event."""
        key = event.keysym
        
        # Add to pressed keys if not already there
        if key not in self.keys_pressed:
            self.keys_pressed.append(key)
        
        # Build key combination string
        self.new_key = '+'.join(self.keys_pressed)
        self.new_key_var.set(self.new_key)
    
    def _on_key_release(self, event):
        """Handle key release event."""
        key = event.keysym
        
        # Remove from pressed keys
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
    
    def _save(self):
        """Save the new hotkey binding."""
        if self.new_key:
            self.callback(self.hotkey_name, self.new_key)
        self.destroy()
