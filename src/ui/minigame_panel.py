"""
Mini-Game UI Panel - Interactive mini-games launcher
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import tkinter as tk
from typing import Optional, Callable
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from src.features.minigame_system import (
    MiniGameManager, MiniGame, GameDifficulty, GameResult
)

logger = logging.getLogger(__name__)


class MiniGamePanel(ctk.CTkFrame if ctk else tk.Frame):
    """Panel for launching and playing mini-games."""
    
    def __init__(self, parent, minigame_manager: MiniGameManager, **kwargs):
        """
        Initialize mini-game panel.
        
        Args:
            parent: Parent widget
            minigame_manager: MiniGameManager instance
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.manager = minigame_manager
        self.current_game = None
        self.game_widgets = {}
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self._create_widgets()
        self._show_game_selection()
    
    def _create_widgets(self):
        """Create UI widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="🎮 Panda Mini-Games",
            font=("Arial", 20, "bold")
        ) if ctk else tk.Label(
            self,
            text="🎮 Panda Mini-Games",
            font=("Arial", 20, "bold")
        )
        header.grid(row=0, column=0, padx=20, pady=10)
        
        # Content frame (will hold different views)
        self.content_frame = ctk.CTkFrame(self) if ctk else tk.Frame(self)
        self.content_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Stats frame
        self.stats_frame = ctk.CTkFrame(self) if ctk else tk.Frame(self)
        self.stats_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self._update_stats()
    
    def _show_game_selection(self):
        """Show game selection menu."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title = ctk.CTkLabel(
            self.content_frame,
            text="Select a Mini-Game",
            font=("Arial", 16, "bold")
        ) if ctk else tk.Label(
            self.content_frame,
            text="Select a Mini-Game",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=10)
        
        # Get available games
        games = self.manager.get_available_games()
        
        # Create button for each game
        for game_info in games:
            self._create_game_button(game_info)
    
    def _create_game_button(self, game_info: dict):
        """Create button for a game."""
        game_frame = ctk.CTkFrame(self.content_frame) if ctk else tk.Frame(self.content_frame)
        game_frame.pack(pady=5, padx=10, fill="x")
        
        # Game name
        name_label = ctk.CTkLabel(
            game_frame,
            text=game_info['name'],
            font=("Arial", 14, "bold")
        ) if ctk else tk.Label(
            game_frame,
            text=game_info['name'],
            font=("Arial", 14, "bold")
        )
        name_label.pack(side="left", padx=10)
        
        # Description
        desc_label = ctk.CTkLabel(
            game_frame,
            text=game_info['description'],
            font=("Arial", 10)
        ) if ctk else tk.Label(
            game_frame,
            text=game_info['description'],
            font=("Arial", 10)
        )
        desc_label.pack(side="left", padx=10)
        
        # Difficulty selector
        difficulty_var = tk.StringVar(value="medium")
        if ctk:
            difficulty_menu = ctk.CTkOptionMenu(
                game_frame,
                variable=difficulty_var,
                values=["easy", "medium", "hard", "extreme"]
            )
        else:
            difficulty_menu = tk.OptionMenu(
                game_frame,
                difficulty_var,
                "easy", "medium", "hard", "extreme"
            )
        difficulty_menu.pack(side="right", padx=5)
        
        # Play button
        play_btn = ctk.CTkButton(
            game_frame,
            text="Play",
            width=80,
            command=lambda: self._start_game(game_info['id'], difficulty_var.get())
        ) if ctk else tk.Button(
            game_frame,
            text="Play",
            command=lambda: self._start_game(game_info['id'], difficulty_var.get())
        )
        play_btn.pack(side="right", padx=5)
    
    def _start_game(self, game_id: str, difficulty_str: str):
        """Start a mini-game."""
        # Convert difficulty string to enum
        difficulty_map = {
            'easy': GameDifficulty.EASY,
            'medium': GameDifficulty.MEDIUM,
            'hard': GameDifficulty.HARD,
            'extreme': GameDifficulty.EXTREME
        }
        difficulty = difficulty_map.get(difficulty_str, GameDifficulty.MEDIUM)
        
        # Start game
        game = self.manager.start_game(game_id, difficulty)
        if not game:
            logger.error(f"Failed to start game: {game_id}")
            return
        
        self.current_game = game
        
        # Show game UI based on type
        if game_id == 'click':
            self._show_click_game()
        elif game_id == 'memory':
            self._show_memory_game()
        elif game_id == 'reflex':
            self._show_reflex_game()
    
    def _create_game_controls(self):
        """Create Pause/Resume and Stop buttons for the active game."""
        controls_frame = ctk.CTkFrame(self.content_frame) if ctk else tk.Frame(self.content_frame)
        controls_frame.pack(pady=5)

        self.pause_var = tk.StringVar(value="⏸ Pause")
        pause_btn = ctk.CTkButton(
            controls_frame,
            textvariable=self.pause_var,
            width=100,
            command=self._toggle_pause
        ) if ctk else tk.Button(
            controls_frame,
            textvariable=self.pause_var,
            command=self._toggle_pause
        )
        pause_btn.pack(side="left", padx=5)

        stop_btn = ctk.CTkButton(
            controls_frame,
            text="⏹ Stop",
            width=100,
            fg_color="red" if ctk else None,
            command=self._stop_game
        ) if ctk else tk.Button(
            controls_frame,
            text="⏹ Stop",
            bg="red",
            fg="white",
            command=self._stop_game
        )
        stop_btn.pack(side="left", padx=5)

    def _toggle_pause(self):
        """Toggle pause/resume on the current game."""
        if not self.current_game:
            return
        if self.current_game.is_paused:
            self.current_game.resume()
            self.pause_var.set("⏸ Pause")
        else:
            self.current_game.pause()
            self.pause_var.set("▶ Resume")

    def _stop_game(self):
        """Stop the current game immediately."""
        if not self.current_game:
            return
        self._end_game()

    def _show_click_game(self):
        """Show click game UI."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Game info
        info_label = ctk.CTkLabel(
            self.content_frame,
            text="Click the panda as many times as you can!",
            font=("Arial", 14)
        ) if ctk else tk.Label(
            self.content_frame,
            text="Click the panda as many times as you can!",
            font=("Arial", 14)
        )
        info_label.pack(pady=10)
        
        # Game control buttons (Pause/Resume + Stop)
        self._create_game_controls()
        
        # Timer display
        self.timer_var = tk.StringVar(value="Time: 0.0s")
        timer_label = ctk.CTkLabel(
            self.content_frame,
            textvariable=self.timer_var,
            font=("Arial", 16, "bold")
        ) if ctk else tk.Label(
            self.content_frame,
            textvariable=self.timer_var,
            font=("Arial", 16, "bold")
        )
        timer_label.pack(pady=5)
        
        # Score display
        self.score_var = tk.StringVar(value="Clicks: 0")
        score_label = ctk.CTkLabel(
            self.content_frame,
            textvariable=self.score_var,
            font=("Arial", 20, "bold")
        ) if ctk else tk.Label(
            self.content_frame,
            textvariable=self.score_var,
            font=("Arial", 20, "bold")
        )
        score_label.pack(pady=10)
        
        # Clickable panda button
        panda_btn = ctk.CTkButton(
            self.content_frame,
            text="🐼\nCLICK ME!",
            font=("Arial", 24, "bold"),
            width=200,
            height=200,
            command=self._on_panda_click
        ) if ctk else tk.Button(
            self.content_frame,
            text="🐼\nCLICK ME!",
            font=("Arial", 24, "bold"),
            width=15,
            height=8,
            command=self._on_panda_click
        )
        panda_btn.pack(pady=20)
        
        # Update timer
        self._update_click_game_timer()
    
    def _on_panda_click(self):
        """Handle panda click in click game."""
        if not self.current_game:
            return
        
        still_running = self.current_game.on_click()
        self.score_var.set(f"Clicks: {self.current_game.clicks}")
        
        if not still_running:
            self._end_game()
    
    def _update_click_game_timer(self):
        """Update click game timer."""
        if not self.current_game or not self.current_game.is_running:
            return
        
        # Don't count down while paused, but keep polling
        if self.current_game.is_paused:
            self.after(100, self._update_click_game_timer)
            return
        
        remaining = self.current_game.get_remaining_time()
        self.timer_var.set(f"Time: {remaining:.1f}s")
        
        if remaining > 0:
            self.after(100, self._update_click_game_timer)
        else:
            self._end_game()
    
    def _show_memory_game(self):
        """Show memory game UI."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Game info
        info_label = ctk.CTkLabel(
            self.content_frame,
            text="Match all the pairs!",
            font=("Arial", 14)
        ) if ctk else tk.Label(
            self.content_frame,
            text="Match all the pairs!",
            font=("Arial", 14)
        )
        info_label.pack(pady=10)
        
        # Game control buttons (Pause/Resume + Stop)
        self._create_game_controls()
        
        # Score display
        self.score_var = tk.StringVar(value=f"Pairs: 0/{self.current_game.max_pairs}")
        score_label = ctk.CTkLabel(
            self.content_frame,
            textvariable=self.score_var,
            font=("Arial", 16, "bold")
        ) if ctk else tk.Label(
            self.content_frame,
            textvariable=self.score_var,
            font=("Arial", 16, "bold")
        )
        score_label.pack(pady=5)
        
        # Card grid
        grid_frame = ctk.CTkFrame(self.content_frame) if ctk else tk.Frame(self.content_frame)
        grid_frame.pack(pady=10)
        
        self.card_buttons = []
        self.revealed_indices = []
        
        size = self.current_game.grid_size
        for i in range(size):
            for j in range(size):
                index = i * size + j
                btn = ctk.CTkButton(
                    grid_frame,
                    text="?",
                    font=("Arial", 20),
                    width=60,
                    height=60,
                    command=lambda idx=index: self._on_card_click(idx)
                ) if ctk else tk.Button(
                    grid_frame,
                    text="?",
                    font=("Arial", 20),
                    width=4,
                    height=2,
                    command=lambda idx=index: self._on_card_click(idx)
                )
                btn.grid(row=i, column=j, padx=2, pady=2)
                self.card_buttons.append(btn)
    
    def _on_card_click(self, index: int):
        """Handle card click in memory game."""
        if not self.current_game or len(self.revealed_indices) >= 2:
            return
        
        if index in self.revealed_indices:
            return
        
        # Reveal card
        emoji = self.current_game.reveal_card(index)
        if ctk:
            self.card_buttons[index].configure(text=emoji)
        else:
            self.card_buttons[index].config(text=emoji)
        
        self.revealed_indices.append(index)
        
        # Check for match when two cards revealed
        if len(self.revealed_indices) == 2:
            self.after(1000, self._check_memory_match)
    
    def _check_memory_match(self):
        """Check if revealed cards match."""
        idx1, idx2 = self.revealed_indices
        
        is_match = self.current_game.check_match(idx1, idx2)
        
        if is_match:
            # Disable matched cards
            if ctk:
                self.card_buttons[idx1].configure(state="disabled")
                self.card_buttons[idx2].configure(state="disabled")
            else:
                self.card_buttons[idx1].config(state="disabled")
                self.card_buttons[idx2].config(state="disabled")
        else:
            # Hide cards again
            if ctk:
                self.card_buttons[idx1].configure(text="?")
                self.card_buttons[idx2].configure(text="?")
            else:
                self.card_buttons[idx1].config(text="?")
                self.card_buttons[idx2].config(text="?")
        
        self.revealed_indices.clear()
        
        # Update score
        self.score_var.set(f"Pairs: {self.current_game.matched_pairs}/{self.current_game.max_pairs}")
        
        # Check if game complete
        if not self.current_game.is_running:
            self._end_game()
    
    def _show_reflex_game(self):
        """Show reflex game UI."""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Game info
        info_label = ctk.CTkLabel(
            self.content_frame,
            text="Click when the panda appears!",
            font=("Arial", 14)
        ) if ctk else tk.Label(
            self.content_frame,
            text="Click when the panda appears!",
            font=("Arial", 14)
        )
        info_label.pack(pady=10)
        
        # Game control buttons (Pause/Resume + Stop)
        self._create_game_controls()
        
        # Round display
        self.round_var = tk.StringVar(value=f"Round: 0/{self.current_game.rounds}")
        round_label = ctk.CTkLabel(
            self.content_frame,
            textvariable=self.round_var,
            font=("Arial", 16, "bold")
        ) if ctk else tk.Label(
            self.content_frame,
            textvariable=self.round_var,
            font=("Arial", 16, "bold")
        )
        round_label.pack(pady=5)
        
        # Target area
        self.target_btn = ctk.CTkButton(
            self.content_frame,
            text="Wait...",
            font=("Arial", 24),
            width=200,
            height=200,
            state="disabled",
            command=self._on_reflex_click
        ) if ctk else tk.Button(
            self.content_frame,
            text="Wait...",
            font=("Arial", 24),
            width=15,
            height=8,
            state="disabled",
            command=self._on_reflex_click
        )
        self.target_btn.pack(pady=20)
        
        # Start first round
        self.after(1000, self._start_reflex_round)
    
    def _start_reflex_round(self):
        """Start a reflex game round."""
        import random
        
        if not self.current_game or not self.current_game.is_running:
            return
        
        # Random delay before showing target
        delay = random.randint(1000, 3000)
        self.after(delay, self._show_reflex_target)
    
    def _show_reflex_target(self):
        """Show the reflex target."""
        if not self.current_game:
            return
        
        self.current_game.show_target()
        
        if ctk:
            self.target_btn.configure(text="🐼\nCLICK!", state="normal")
        else:
            self.target_btn.config(text="🐼\nCLICK!", state="normal")
    
    def _on_reflex_click(self):
        """Handle reflex click."""
        if not self.current_game:
            return
        
        reaction_time = self.current_game.on_target_click()
        
        if reaction_time:
            # Show reaction time
            if ctk:
                self.target_btn.configure(
                    text=f"{reaction_time:.0f}ms",
                    state="disabled"
                )
            else:
                self.target_btn.config(
                    text=f"{reaction_time:.0f}ms",
                    state="disabled"
                )
            
            # Update round
            self.round_var.set(f"Round: {self.current_game.current_round}/{self.current_game.rounds}")
            
            # Check if game continues
            if self.current_game.is_running:
                self.after(1000, self._start_reflex_round)
            else:
                self._end_game()
    
    def _end_game(self):
        """End the current game and show results."""
        if not self.current_game:
            return
        
        result = self.manager.stop_current_game()
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show results
        title = ctk.CTkLabel(
            self.content_frame,
            text="Game Over!",
            font=("Arial", 24, "bold")
        ) if ctk else tk.Label(
            self.content_frame,
            text="Game Over!",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=10)
        
        # Score
        score_label = ctk.CTkLabel(
            self.content_frame,
            text=f"Score: {result.score}",
            font=("Arial", 18)
        ) if ctk else tk.Label(
            self.content_frame,
            text=f"Score: {result.score}",
            font=("Arial", 18)
        )
        score_label.pack(pady=5)
        
        # Rewards
        rewards_text = f"XP Earned: {result.xp_earned}\nMoney Earned: ${result.currency_earned}"
        if result.perfect_score:
            rewards_text += "\n🌟 PERFECT SCORE! 🌟"
        
        rewards_label = ctk.CTkLabel(
            self.content_frame,
            text=rewards_text,
            font=("Arial", 14)
        ) if ctk else tk.Label(
            self.content_frame,
            text=rewards_text,
            font=("Arial", 14)
        )
        rewards_label.pack(pady=10)
        
        # Back button
        back_btn = ctk.CTkButton(
            self.content_frame,
            text="Play Again",
            command=self._show_game_selection
        ) if ctk else tk.Button(
            self.content_frame,
            text="Play Again",
            command=self._show_game_selection
        )
        back_btn.pack(pady=10)
        
        self.current_game = None
        self._update_stats()
    
    def _update_stats(self):
        """Update statistics display."""
        # Clear stats frame
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        stats = self.manager.get_statistics()
        
        stats_text = f"Total Games: {stats['total_games']} | Total XP: {stats['total_xp_earned']} | Money Earned: ${stats.get('total_currency_earned', 0)} | Perfect Scores: {stats['perfect_scores']}"
        
        stats_label = ctk.CTkLabel(
            self.stats_frame,
            text=stats_text,
            font=("Arial", 10)
        ) if ctk else tk.Label(
            self.stats_frame,
            text=stats_text,
            font=("Arial", 10)
        )
        stats_label.pack(pady=5)
