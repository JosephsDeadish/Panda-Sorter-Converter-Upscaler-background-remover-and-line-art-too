"""
Panda Widgets UI Panel - Interactive toys and food interface
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import tkinter as tk
from typing import Optional
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from src.features.panda_widgets import WidgetCollection, WidgetType, PandaWidget

logger = logging.getLogger(__name__)


class WidgetsPanel(ctk.CTkFrame if ctk else tk.Frame):
    """Panel for interacting with panda widgets (toys, food, accessories)."""
    
    def __init__(self, parent, widget_collection: WidgetCollection, 
                 panda_callback: Optional[object] = None, **kwargs):
        """
        Initialize widgets panel.
        
        Args:
            parent: Parent widget
            widget_collection: WidgetCollection instance
            panda_callback: Callback to update panda (e.g., for animations)
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.collection = widget_collection
        self.panda_callback = panda_callback
        self.current_category = WidgetType.TOY
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_widgets()
        self._show_widgets()
    
    def _create_widgets(self):
        """Create UI widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="🎾 Panda Toys & Food",
            font=("Arial", 20, "bold")
        ) if ctk else tk.Label(
            self,
            text="🎾 Panda Toys & Food",
            font=("Arial", 20, "bold")
        )
        header.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        
        # Category selector
        category_frame = ctk.CTkFrame(self) if ctk else tk.Frame(self)
        category_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ns")
        
        # Category buttons
        toys_btn = ctk.CTkButton(
            category_frame,
            text="🎾 Toys",
            command=lambda: self._select_category(WidgetType.TOY)
        ) if ctk else tk.Button(
            category_frame,
            text="🎾 Toys",
            command=lambda: self._select_category(WidgetType.TOY)
        )
        toys_btn.pack(pady=5, fill="x")
        
        food_btn = ctk.CTkButton(
            category_frame,
            text="🎋 Food",
            command=lambda: self._select_category(WidgetType.FOOD)
        ) if ctk else tk.Button(
            category_frame,
            text="🎋 Food",
            command=lambda: self._select_category(WidgetType.FOOD)
        )
        food_btn.pack(pady=5, fill="x")
        
        accessories_btn = ctk.CTkButton(
            category_frame,
            text="🎬 Animations",
            command=lambda: self._show_animations()
        ) if ctk else tk.Button(
            category_frame,
            text="🎬 Animations",
            command=lambda: self._show_animations()
        )
        accessories_btn.pack(pady=5, fill="x")
        
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
            
            canvas.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
            scrollbar.grid(row=1, column=2, sticky="ns")
        
        if ctk:
            self.content_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        # Status/feedback area
        self.status_var = tk.StringVar(value="Select a widget to interact with panda!")
        status_label = ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            font=("Arial", 12)
        ) if ctk else tk.Label(
            self,
            textvariable=self.status_var,
            font=("Arial", 12)
        )
        status_label.grid(row=2, column=0, columnspan=2, pady=10)
    
    def _select_category(self, category: WidgetType):
        """Select a widget category."""
        self.current_category = category
        self._show_widgets()
    
    def _show_widgets(self):
        """Display widgets for current category."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Get widgets for category
        widgets = self.collection.get_all_widgets(self.current_category)
        
        # Display each widget
        for widget in widgets:
            self._create_widget_card(widget)
    
    def _create_widget_card(self, widget: PandaWidget):
        """Create a card for a widget."""
        # Card frame
        card = ctk.CTkFrame(self.content_frame) if ctk else tk.Frame(
            self.content_frame,
            relief="ridge",
            borderwidth=2
        )
        card.pack(pady=5, padx=10, fill="x")
        
        # Widget emoji and name
        name_frame = ctk.CTkFrame(card) if ctk else tk.Frame(card)
        name_frame.pack(side="left", padx=10, pady=5)
        
        emoji_label = ctk.CTkLabel(
            name_frame,
            text=widget.emoji,
            font=("Arial", 24)
        ) if ctk else tk.Label(
            name_frame,
            text=widget.emoji,
            font=("Arial", 24)
        )
        emoji_label.pack(side="left", padx=5)
        
        name_label = ctk.CTkLabel(
            name_frame,
            text=widget.name,
            font=("Arial", 14, "bold")
        ) if ctk else tk.Label(
            name_frame,
            text=widget.name,
            font=("Arial", 14, "bold")
        )
        name_label.pack(side="left", padx=5)
        
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
            text=widget.rarity.value.upper(),
            text_color=rarity_colors.get(widget.rarity.value, 'gray') if ctk else None,
            font=("Arial", 10, "bold")
        ) if ctk else tk.Label(
            card,
            text=widget.rarity.value.upper(),
            fg=rarity_colors.get(widget.rarity.value, 'gray'),
            font=("Arial", 10, "bold")
        )
        rarity_label.pack(side="left", padx=5)
        
        # Usage stats
        stats_text = f"Used: {widget.stats.times_used}"
        if widget.stats.favorite:
            stats_text += " ⭐"
        
        stats_label = ctk.CTkLabel(
            card,
            text=stats_text,
            font=("Arial", 10)
        ) if ctk else tk.Label(
            card,
            text=stats_text,
            font=("Arial", 10)
        )
        stats_label.pack(side="left", padx=5)
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(card) if ctk else tk.Frame(card)
        btn_frame.pack(side="right", padx=5)
        
        if widget.unlocked:
            # Use button
            use_btn = ctk.CTkButton(
                btn_frame,
                text="Use",
                width=60,
                command=lambda: self._use_widget(widget.name.lower().replace(' ', '_'))
            ) if ctk else tk.Button(
                btn_frame,
                text="Use",
                command=lambda: self._use_widget(widget.name.lower().replace(' ', '_'))
            )
            use_btn.pack(side="left", padx=2)
            
            # Return to inventory button
            return_btn = ctk.CTkButton(
                btn_frame,
                text="📥",
                width=40,
                command=lambda w=widget.name.lower().replace(' ', '_'): self._return_to_inventory(w)
            ) if ctk else tk.Button(
                btn_frame,
                text="📥",
                command=lambda w=widget.name.lower().replace(' ', '_'): self._return_to_inventory(w)
            )
            return_btn.pack(side="left", padx=2)
            
            # Favorite button
            fav_text = "❤️" if widget.stats.favorite else "🤍"
            fav_btn = ctk.CTkButton(
                btn_frame,
                text=fav_text,
                width=40,
                command=lambda: self._toggle_favorite(widget.name.lower().replace(' ', '_'))
            ) if ctk else tk.Button(
                btn_frame,
                text=fav_text,
                command=lambda: self._toggle_favorite(widget.name.lower().replace(' ', '_'))
            )
            fav_btn.pack(side="left", padx=2)
        else:
            # Locked indicator
            locked_label = ctk.CTkLabel(
                btn_frame,
                text="🔒 Locked",
                text_color="red" if ctk else None
            ) if ctk else tk.Label(
                btn_frame,
                text="🔒 Locked",
                fg="red"
            )
            locked_label.pack(side="left", padx=5)
    
    def _use_widget(self, widget_id: str):
        """Use a widget with the panda."""
        result = self.collection.use_widget(widget_id)
        
        if result:
            # Update status
            self.status_var.set(result['message'])
            
            # Update panda animation if callback provided
            if self.panda_callback and hasattr(self.panda_callback, 'set_animation'):
                self.panda_callback.set_animation(result['animation'])
            
            # Refresh display to show updated stats
            self._show_widgets()
            
            logger.info(f"Used widget: {widget_id}, happiness: {result['happiness']}")
        else:
            self.status_var.set("Failed to use widget!")
    
    def _return_to_inventory(self, widget_id: str):
        """Return an active item back to inventory (clear it from panda)."""
        widget = self.collection.get_widget(widget_id)
        if widget:
            # Clear the active item on the panda widget
            if self.panda_callback and hasattr(self.panda_callback, 'set_active_item'):
                self.panda_callback.set_active_item(None, None, None)
            # Return panda to idle animation
            if self.panda_callback and hasattr(self.panda_callback, 'start_animation'):
                self.panda_callback.start_animation('idle')
            self.status_var.set(f"{widget.name} returned to inventory!")
            self._show_widgets()
    
    def _toggle_favorite(self, widget_id: str):
        """Toggle widget favorite status."""
        widget = self.collection.get_widget(widget_id)
        if widget:
            new_status = not widget.stats.favorite
            self.collection.set_favorite(widget_id, new_status)
            
            status_text = "added to" if new_status else "removed from"
            self.status_var.set(f"{widget.name} {status_text} favorites!")
            
            # Refresh display
            self._show_widgets()
    
    # Animation entries with emoji, display name, and animation state name
    ANIMATION_ENTRIES = [
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
    
    def _show_animations(self):
        """Display available panda animations with play buttons."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.current_category = None  # Not a widget category
        
        for emoji, name, anim_state in self.ANIMATION_ENTRIES:
            card = ctk.CTkFrame(self.content_frame) if ctk else tk.Frame(
                self.content_frame, relief="ridge", borderwidth=2
            )
            card.pack(pady=3, padx=10, fill="x")
            
            # Emoji + name
            label = ctk.CTkLabel(
                card, text=f"{emoji} {name}", font=("Arial", 13, "bold")
            ) if ctk else tk.Label(
                card, text=f"{emoji} {name}", font=("Arial", 13, "bold")
            )
            label.pack(side="left", padx=10, pady=5)
            
            # Play button
            play_btn = ctk.CTkButton(
                card, text="▶ Play", width=70, height=28,
                command=lambda a=anim_state, n=name: self._play_animation(a, n)
            ) if ctk else tk.Button(
                card, text="▶ Play",
                command=lambda a=anim_state, n=name: self._play_animation(a, n)
            )
            play_btn.pack(side="right", padx=10, pady=5)
    
    def _play_animation(self, anim_state: str, display_name: str):
        """Play a panda animation via the callback."""
        if self.panda_callback and hasattr(self.panda_callback, 'play_animation_once'):
            self.panda_callback.play_animation_once(anim_state)
            self.status_var.set(f"Playing: {display_name}")
        elif self.panda_callback and hasattr(self.panda_callback, 'set_animation'):
            self.panda_callback.set_animation(anim_state)
            self.status_var.set(f"Playing: {display_name}")
        else:
            self.status_var.set("Panda not available for animations")
