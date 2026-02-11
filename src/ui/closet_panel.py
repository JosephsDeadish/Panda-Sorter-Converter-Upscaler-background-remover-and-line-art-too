"""
Panda Closet UI Panel - Panda appearance customization interface
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import tkinter as tk
from typing import Optional
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from src.features.panda_closet import PandaCloset, CustomizationCategory, CustomizationItem

logger = logging.getLogger(__name__)


class ClosetPanel(ctk.CTkFrame if ctk else tk.Frame):
    """Panel for customizing panda appearance."""
    
    def __init__(self, parent, panda_closet: PandaCloset,
                 panda_character=None,
                 panda_preview_callback: Optional[object] = None, **kwargs):
        """
        Initialize closet panel.
        
        Args:
            parent: Parent widget
            panda_closet: PandaCloset instance
            panda_character: PandaCharacter instance for name/gender
            panda_preview_callback: Callback to update panda preview
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.closet = panda_closet
        self.panda_character = panda_character
        self.panda_preview = panda_preview_callback
        self.current_category = CustomizationCategory.FUR_STYLE
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        
        self._create_widgets()
        self._show_items()
    
    def _create_widgets(self):
        """Create UI widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="👔 Panda Closet",
            font=("Arial", 20, "bold")
        ) if ctk else tk.Label(
            self,
            text="👔 Panda Closet",
            font=("Arial", 20, "bold")
        )
        header.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        
        # Note: Panda name/gender settings are now under Panda Stats (right-click panda)
        
        # Category selector sidebar
        category_frame = ctk.CTkFrame(self) if ctk else tk.Frame(self)
        category_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ns")
        
        # Category buttons
        categories = [
            (CustomizationCategory.FUR_STYLE, "🐼 Fur Style"),
            (CustomizationCategory.FUR_COLOR, "🎨 Fur Color"),
            (CustomizationCategory.CLOTHING, "👕 Clothing"),
            (CustomizationCategory.HAT, "🎩 Hats"),
            (CustomizationCategory.SHOES, "👟 Shoes"),
            (CustomizationCategory.ACCESSORY, "✨ Accessories"),
        ]
        
        for category, label in categories:
            btn = ctk.CTkButton(
                category_frame,
                text=label,
                command=lambda c=category: self._select_category(c)
            ) if ctk else tk.Button(
                category_frame,
                text=label,
                command=lambda c=category: self._select_category(c)
            )
            btn.pack(pady=5, fill="x")
        
        # Scrollable content frame
        if ctk:
            self.content_frame = ctk.CTkScrollableFrame(self)
        else:
            canvas = tk.Canvas(self)
            scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
            self.content_frame = tk.Frame(canvas)
            
            self.content_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
            scrollbar.grid(row=2, column=2, sticky="ns")
        
        if ctk:
            self.content_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        
        # Current appearance display
        appearance_frame = ctk.CTkFrame(self) if ctk else tk.Frame(self)
        appearance_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        appearance_label = ctk.CTkLabel(
            appearance_frame,
            text="Current Appearance:",
            font=("Arial", 12, "bold")
        ) if ctk else tk.Label(
            appearance_frame,
            text="Current Appearance:",
            font=("Arial", 12, "bold")
        )
        appearance_label.pack(side="left", padx=5)
        
        self.appearance_var = tk.StringVar(value=self._get_appearance_text())
        appearance_text = ctk.CTkLabel(
            appearance_frame,
            textvariable=self.appearance_var,
            font=("Arial", 10)
        ) if ctk else tk.Label(
            appearance_frame,
            textvariable=self.appearance_var,
            font=("Arial", 10)
        )
        appearance_text.pack(side="left", padx=5)
    
    def refresh(self):
        """Refresh the closet display to show newly purchased items."""
        self._show_items()
        self.appearance_var.set(self._get_appearance_text())
    
    def _select_category(self, category: CustomizationCategory):
        """Select a customization category."""
        self.current_category = category
        self._show_items()
    
    def _show_items(self):
        """Display items for current category (only purchased/unlocked items).
        
        Items must be purchased from the Shop or unlocked via achievements.
        The closet only shows owned items for equipping/unequipping.
        """
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Only show unlocked/purchased items — buy from Shop, not here
        items = self.closet.get_items_by_category(self.current_category, unlocked_only=True)
        
        if not items:
            no_items_label = ctk.CTkLabel(
                self.content_frame,
                text="No items owned in this category.\nVisit the 🛒 Shop to buy new items!",
                font=("Arial", 12),
                text_color="gray"
            ) if ctk else tk.Label(
                self.content_frame,
                text="No items owned in this category.\nVisit the Shop to buy new items!",
                font=("Arial", 12),
                fg="gray"
            )
            no_items_label.pack(pady=20)
            return
        
        # Display each owned item
        for item in items:
            self._create_item_card(item)
    
    def _create_item_card(self, item: CustomizationItem):
        """Create a card for an owned customization item (equip/unequip only)."""
        # Card frame
        card = ctk.CTkFrame(self.content_frame) if ctk else tk.Frame(
            self.content_frame,
            relief="ridge",
            borderwidth=2
        )
        card.pack(pady=5, padx=10, fill="x")
        
        # Item emoji and name
        name_frame = ctk.CTkFrame(card) if ctk else tk.Frame(card)
        name_frame.pack(side="left", padx=10, pady=5)
        
        emoji_label = ctk.CTkLabel(
            name_frame,
            text=item.emoji,
            font=("Arial", 24)
        ) if ctk else tk.Label(
            name_frame,
            text=item.emoji,
            font=("Arial", 24)
        )
        emoji_label.pack(side="left", padx=5)
        
        name_label = ctk.CTkLabel(
            name_frame,
            text=item.name,
            font=("Arial", 14, "bold")
        ) if ctk else tk.Label(
            name_frame,
            text=item.name,
            font=("Arial", 14, "bold")
        )
        name_label.pack(side="left", padx=5)
        
        # Description
        desc_label = ctk.CTkLabel(
            card,
            text=item.description,
            font=("Arial", 10)
        ) if ctk else tk.Label(
            card,
            text=item.description,
            font=("Arial", 10)
        )
        desc_label.pack(side="left", padx=5)
        
        # Rarity indicator
        rarity_colors = {
            'common': 'gray',
            'uncommon': 'green',
            'rare': 'blue',
            'epic': 'purple',
            'legendary': 'orange'
        }
        
        rarity_label = ctk.CTkLabel(
            card,
            text=item.rarity.value.upper(),
            text_color=rarity_colors.get(item.rarity.value, 'gray') if ctk else None,
            font=("Arial", 10, "bold")
        ) if ctk else tk.Label(
            card,
            text=item.rarity.value.upper(),
            fg=rarity_colors.get(item.rarity.value, 'gray'),
            font=("Arial", 10, "bold")
        )
        rarity_label.pack(side="left", padx=5)
        
        # Buttons frame — only equip/unequip for owned items
        btn_frame = ctk.CTkFrame(card) if ctk else tk.Frame(card)
        btn_frame.pack(side="right", padx=5)
        
        if item.equipped:
            # Unequip button
            unequip_btn = ctk.CTkButton(
                btn_frame,
                text="✓ Equipped",
                width=100,
                fg_color="green" if ctk else None,
                command=lambda: self._unequip_item(item.id)
            ) if ctk else tk.Button(
                btn_frame,
                text="✓ Equipped",
                bg="green",
                fg="white",
                command=lambda: self._unequip_item(item.id)
            )
            unequip_btn.pack(side="left", padx=2)
        else:
            # Equip button
            equip_btn = ctk.CTkButton(
                btn_frame,
                text="Equip",
                width=80,
                command=lambda: self._equip_item(item.id)
            ) if ctk else tk.Button(
                btn_frame,
                text="Equip",
                command=lambda: self._equip_item(item.id)
            )
            equip_btn.pack(side="left", padx=2)
    
    def _equip_item(self, item_id: str):
        """Equip an item."""
        if self.closet.equip_item(item_id):
            logger.info(f"Equipped item: {item_id}")
            self._update_appearance()
            self._show_items()  # Refresh display
        else:
            logger.warning(f"Failed to equip item: {item_id}")
    
    def _unequip_item(self, item_id: str):
        """Unequip an item."""
        if self.closet.unequip_item(item_id):
            logger.info(f"Unequipped item: {item_id}")
            self._update_appearance()
            self._show_items()  # Refresh display
        else:
            logger.warning(f"Failed to unequip item: {item_id}")
    
    def _get_appearance_text(self) -> str:
        """Get current appearance as text."""
        appearance = self.closet.get_current_appearance()
        return appearance.get_display_string()
    
    def _update_appearance(self):
        """Update appearance display and panda preview."""
        # Update text
        self.appearance_var.set(self._get_appearance_text())
        
        # Update panda preview if callback provided
        if self.panda_preview and hasattr(self.panda_preview, 'update_appearance'):
            appearance = self.closet.get_current_appearance()
            self.panda_preview.update_appearance(appearance)
