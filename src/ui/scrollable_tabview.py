"""
Tabview Widgets
Provides a staggered two-row tab layout so all tabs are visible at once
without scrolling.
"""

import customtkinter as ctk
from typing import Dict, List, Optional, Callable
import math
import logging

logger = logging.getLogger(__name__)


class ScrollableTabView(ctk.CTkFrame):
    """
    A tabview that displays tabs in two staggered rows so every tab is
    always visible without needing scroll arrows.  Row 1 holds the first
    half of the tabs and row 2 holds the second half.

    Provides the same public API as CTkTabview (add / set / get / tab)
    so it can be used as a drop-in replacement.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.tabs: Dict[str, ctk.CTkFrame] = {}
        self.tab_buttons: Dict[str, ctk.CTkButton] = {}
        self.current_tab: Optional[str] = None

        self._create_widgets()

    # ── Widget creation ────────────────────────────────────────────
    def _create_widgets(self):
        """Create the two-row tab bar and content area."""
        # Container that holds both tab rows
        self.tab_bar = ctk.CTkFrame(self)
        self.tab_bar.pack(side="top", fill="x", padx=2, pady=(2, 0))

        # Row 1 (top row)
        self.row1 = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        self.row1.pack(side="top", fill="x", padx=2, pady=(2, 0))

        # Row 2 (bottom row)
        self.row2 = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        self.row2.pack(side="top", fill="x", padx=2, pady=(0, 2))

        # Content area
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(side="top", fill="both", expand=True)

    # ── Public API ─────────────────────────────────────────────────
    def add(self, name: str) -> ctk.CTkFrame:
        """Add a new tab and return its content frame."""
        tab_frame = ctk.CTkFrame(self.content_frame)
        self.tabs[name] = tab_frame

        btn = ctk.CTkButton(
            self.row1,
            text=name,
            command=lambda n=name: self.set(n),
            height=28,
            corner_radius=6,
            font=("Arial", 11),
            fg_color=["gray75", "gray25"],
            hover_color=["gray70", "gray30"],
        )
        self.tab_buttons[name] = btn

        # Re-balance rows whenever total count changes
        self._rebalance_rows()

        # Auto-select first tab
        if len(self.tabs) == 1:
            self.set(name)

        return tab_frame

    def set(self, name: str):
        """Switch to a specific tab by name."""
        if name not in self.tabs:
            logger.warning(f"Tab '{name}' not found")
            return

        # Deselect previous
        if self.current_tab and self.current_tab in self.tabs:
            self.tabs[self.current_tab].pack_forget()
            if self.current_tab in self.tab_buttons:
                self.tab_buttons[self.current_tab].configure(
                    fg_color=["gray75", "gray25"],
                    hover_color=["gray70", "gray30"],
                )

        # Select new
        self.current_tab = name
        self.tabs[name].pack(fill="both", expand=True)
        if name in self.tab_buttons:
            self.tab_buttons[name].configure(
                fg_color=["#3B8ED0", "#1F6AA5"],
                hover_color=["#36719F", "#144870"],
            )

    def get(self, name: str = None) -> Optional[ctk.CTkFrame]:
        """Get a tab frame by name, or return the current tab name if *name* is None."""
        if name is None:
            return self.current_tab
        return self.tabs.get(name)

    def tab(self, name: str) -> Optional[ctk.CTkFrame]:
        """Return the content frame for *name* (CTkTabview compatibility)."""
        return self.tabs.get(name)

    def delete(self, name: str):
        """Remove a tab by name (CTkTabview compatibility)."""
        if name not in self.tabs:
            return
        # If it's the active tab, switch away first
        if self.current_tab == name:
            remaining = [n for n in self.tabs if n != name]
            if remaining:
                self.set(remaining[0])
            else:
                self.current_tab = None
        self.tabs[name].destroy()
        del self.tabs[name]
        if name in self.tab_buttons:
            self.tab_buttons[name].destroy()
            del self.tab_buttons[name]
        self._rebalance_rows()

    # ── Internal helpers ───────────────────────────────────────────
    def _rebalance_rows(self):
        """Redistribute buttons evenly across two rows."""
        names = list(self.tabs.keys())
        half = math.ceil(len(names) / 2)

        for btn in self.tab_buttons.values():
            btn.pack_forget()

        for i, name in enumerate(names):
            parent = self.row1 if i < half else self.row2
            self.tab_buttons[name].pack(in_=parent, side="left", padx=2, pady=1)


class CompactTabView(ctk.CTkFrame):
    """
    A compact tabview that uses a dropdown selector for many tabs.
    Better for very large numbers of tabs (15+).
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.tabs: Dict[str, ctk.CTkFrame] = {}
        self.current_tab: Optional[str] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the compact tab structure."""
        # Top bar with dropdown selector
        self.tab_bar = ctk.CTkFrame(self, height=40)
        self.tab_bar.pack(side="top", fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            self.tab_bar,
            text="Tab:",
            font=("Arial Bold", 12)
        ).pack(side="left", padx=5)
        
        # Dropdown for tab selection
        self.tab_dropdown = ctk.CTkOptionMenu(
            self.tab_bar,
            values=["Select a tab..."],
            command=self._on_tab_selected,
            width=200
        )
        self.tab_dropdown.pack(side="left", padx=5)
        
        # Content area
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(side="top", fill="both", expand=True)
    
    def add(self, name: str) -> ctk.CTkFrame:
        """Add a new tab."""
        # Create tab content frame
        tab_frame = ctk.CTkFrame(self.content_frame)
        self.tabs[name] = tab_frame
        
        # Update dropdown
        self.tab_dropdown.configure(values=list(self.tabs.keys()))
        
        # If this is the first tab, select it
        if len(self.tabs) == 1:
            self.set(name)
            self.tab_dropdown.set(name)
        
        return tab_frame
    
    def set(self, name: str):
        """Switch to a specific tab."""
        if name not in self.tabs:
            return
        
        # Hide current tab
        if self.current_tab and self.current_tab in self.tabs:
            self.tabs[self.current_tab].pack_forget()
        
        # Show new tab
        self.current_tab = name
        self.tabs[name].pack(fill="both", expand=True)
        self.tab_dropdown.set(name)
    
    def get(self, name: str = None) -> Optional[ctk.CTkFrame]:
        """Get a tab frame by name, or current tab name if *name* is None."""
        if name is None:
            return self.current_tab
        return self.tabs.get(name)
    
    def tab(self, name: str) -> Optional[ctk.CTkFrame]:
        """Return the content frame for *name* (CTkTabview compatibility)."""
        return self.tabs.get(name)
    
    def delete(self, name: str):
        """Remove a tab by name (CTkTabview compatibility)."""
        if name not in self.tabs:
            return
        if self.current_tab == name:
            remaining = [n for n in self.tabs if n != name]
            if remaining:
                self.set(remaining[0])
            else:
                self.current_tab = None
        self.tabs[name].destroy()
        del self.tabs[name]
        self.tab_dropdown.configure(values=list(self.tabs.keys()))
    
    def _on_tab_selected(self, value: str):
        """Handle tab selection from dropdown."""
        self.set(value)
