"""
Panda Closet UI Panel - Panda appearance customization interface
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import tkinter as tk
from typing import Optional, List
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from src.features.panda_closet import PandaCloset, CustomizationCategory, CustomizationItem, ClothingSubCategory

# Try to import tooltip support
try:
    from src.features.tutorial_system import WidgetTooltip
except ImportError:
    WidgetTooltip = None

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
        self.current_category = CustomizationCategory.CLOTHING
        self._clothing_filter: Optional[str] = None  # Subcategory filter for clothing
        self._tooltips: List = []  # Prevent tooltip garbage collection
        
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
        if WidgetTooltip:
            self._tooltips.append(WidgetTooltip(header, "Dress up your panda with outfits and accessories you own"))
        
        # Note: Panda name/gender settings are now under Panda Stats (right-click panda)
        
        # Category selector sidebar
        category_frame = ctk.CTkFrame(self) if ctk else tk.Frame(self)
        category_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ns")
        
        # Category buttons — "All Clothing" first for easy access
        categories = [
            (CustomizationCategory.CLOTHING, "👕 All Clothing"),
            (CustomizationCategory.HAT, "🎩 Hats"),
            (CustomizationCategory.SHOES, "👟 Shoes"),
            (CustomizationCategory.ACCESSORY, "✨ Accessories"),
            (CustomizationCategory.FUR_STYLE, "🐼 Fur Style"),
            (CustomizationCategory.FUR_COLOR, "🎨 Fur Color"),
        ]
        
        category_tips = {
            CustomizationCategory.FUR_STYLE: "Change your panda's fur pattern and style",
            CustomizationCategory.FUR_COLOR: "Pick a fur color for your panda",
            CustomizationCategory.CLOTHING: "Browse all owned clothing items to equip",
            CustomizationCategory.HAT: "Try on hats — equip or unequip from here",
            CustomizationCategory.SHOES: "Choose shoes for your panda to wear",
            CustomizationCategory.ACCESSORY: "Accessorize your panda with fun items",
        }
        
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
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(btn, category_tips.get(category, f"Browse {label} items")))

        # Clothing subcategory buttons — shown only when Clothing is selected
        self._clothing_sub_frame = ctk.CTkFrame(category_frame) if ctk else tk.Frame(category_frame)
        clothing_subs = [
            ("shirt", "👕 Shirts"),
            ("pants", "👖 Pants"),
            ("jacket", "🧥 Jackets"),
            ("dress", "👗 Dresses"),
            ("full_body", "🤵 Full Outfits"),
        ]
        clothing_sub_tips = {
            "shirt": "Browse shirts and tops for your panda",
            "pants": "Browse pants and bottoms for your panda",
            "jacket": "Browse jackets, hoodies, and coats",
            "dress": "Browse dresses, robes, and gowns",
            "full_body": "Browse full-body outfits and costumes",
        }
        for sub_type, sub_label in clothing_subs:
            sub_btn = ctk.CTkButton(
                self._clothing_sub_frame,
                text=f"  {sub_label}",
                height=24,
                font=("Arial", 11),
                command=lambda t=sub_type: self._select_clothing_sub(t)
            ) if ctk else tk.Button(
                self._clothing_sub_frame,
                text=f"  {sub_label}",
                font=("Arial", 9),
                command=lambda t=sub_type: self._select_clothing_sub(t)
            )
            sub_btn.pack(pady=1, fill="x", padx=(10, 0))
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(sub_btn, clothing_sub_tips.get(sub_type, f"Browse {sub_label}")))
        # Show subcategory buttons only when Clothing is selected
        self._update_clothing_sub_visibility()
        
        # Scrollable content frame - NO CANVAS, use ctk scrollable frame
        # If customtkinter available, use its scrollable frame
        # Otherwise create basic frame (scrolling handled by parent)
        if ctk:
            self.content_frame = ctk.CTkScrollableFrame(self)
            self.content_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        else:
            # Use basic Frame - scrolling should be handled by Qt parent when available
            # This eliminates tk.Canvas usage entirely
            scroll_container = tk.Frame(self)
            scroll_container.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
            
            self.content_frame = tk.Frame(scroll_container)
            self.content_frame.pack(fill="both", expand=True)
            
            # Note: If this panel is wrapped in a Qt widget, Qt will handle scrolling
            # via QScrollArea, so no canvas needed
        
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
        if WidgetTooltip:
            self._tooltips.append(WidgetTooltip(appearance_label, "Shows what your panda is currently wearing"))
            self._tooltips.append(WidgetTooltip(appearance_text, "Your panda's current outfit summary"))
    
    def refresh(self):
        """Refresh the closet display to show newly purchased items."""
        self._show_items()
        self.appearance_var.set(self._get_appearance_text())
    
    def _select_category(self, category: CustomizationCategory):
        """Select a customization category."""
        self.current_category = category
        self._clothing_filter = None  # Clear subcategory filter
        self._update_clothing_sub_visibility()
        self._show_items()

    def _update_clothing_sub_visibility(self):
        """Show clothing subcategory buttons only when Clothing category is active."""
        if self.current_category == CustomizationCategory.CLOTHING:
            self._clothing_sub_frame.pack(fill="x", pady=(0, 5))
        else:
            self._clothing_sub_frame.pack_forget()

    def _select_clothing_sub(self, clothing_type: str):
        """Select a clothing subcategory filter (shirt, pants, jacket, etc.)."""
        self.current_category = CustomizationCategory.CLOTHING
        self._clothing_filter = clothing_type
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
        if (self.current_category == CustomizationCategory.CLOTHING
                and self._clothing_filter):
            items = self.closet.get_clothing_by_subcategory(
                self._clothing_filter, unlocked_only=True)
        else:
            items = self.closet.get_items_by_category(
                self.current_category, unlocked_only=True)
        
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
        if ctk:
            name_frame = ctk.CTkFrame(card, fg_color="transparent")
        else:
            name_frame = tk.Frame(card, relief="flat", borderwidth=0, highlightthickness=0)
        name_frame.pack(side="left", padx=10, pady=5)
        
        emoji_label = ctk.CTkLabel(
            name_frame,
            text=item.emoji,
            font=("Arial", 24),
            fg_color="transparent"
        ) if ctk else tk.Label(
            name_frame,
            text=item.emoji,
            font=("Arial", 24),
            bg=name_frame.cget('bg') if hasattr(name_frame, 'cget') else None,
            borderwidth=0,
            highlightthickness=0
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
        if WidgetTooltip:
            self._tooltips.append(WidgetTooltip(name_label, f"{item.name} — {item.description}"))
        
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
        if WidgetTooltip:
            self._tooltips.append(WidgetTooltip(rarity_label, f"{item.rarity.value.title()} rarity item"))
        
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
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(unequip_btn, f"Click to unequip {item.name}"))
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
            if WidgetTooltip:
                self._tooltips.append(WidgetTooltip(equip_btn, f"Equip {item.name} on your panda"))
    
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
