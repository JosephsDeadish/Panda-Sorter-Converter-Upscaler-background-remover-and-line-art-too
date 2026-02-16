"""
Mini-Game UI Panel - PyQt6 Version
Interactive mini-games launcher with Qt native timing
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from features.minigame_system import (
    MiniGameManager, MiniGame, GameDifficulty, GameResult
)

logger = logging.getLogger(__name__)


class MiniGamePanelQt(QWidget):
    """Qt panel for launching and playing mini-games."""
    
    game_completed = pyqtSignal(str, int)  # game_id, score
    
    def __init__(self, parent=None, minigame_manager: MiniGameManager = None):
        """
        Initialize mini-game panel.
        
        Args:
            parent: Parent widget
            minigame_manager: MiniGameManager instance
        """
        super().__init__(parent)
        
        self.manager = minigame_manager or MiniGameManager()
        self.current_game = None
        self.game_widgets = {}
        
        # Game timers (using QTimer instead of .after())
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self._on_game_timer)
        
        self.action_timer = QTimer(self)
        self.action_timer.setSingleShot(True)
        
        self._create_widgets()
        self._show_game_selection()
    
    def _create_widgets(self):
        """Create UI widgets."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("🎮 Panda Mini-Games")
        header.setStyleSheet("font-size: 18pt; font-weight: bold;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Content frame (will hold different views)
        self.content_frame = QWidget()
        self.content_layout = QVBoxLayout(self.content_frame)
        layout.addWidget(self.content_frame)
        
        # Stats frame
        self.stats_frame = QFrame()
        self.stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        stats_layout = QVBoxLayout(self.stats_frame)
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: gray; font-size: 10pt;")
        stats_layout.addWidget(self.stats_label)
        layout.addWidget(self.stats_frame)
        
        self._update_stats()
    
    def _show_game_selection(self):
        """Show game selection menu."""
        # Clear content frame
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Title
        title = QLabel("Select a Mini-Game")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(title)
        
        # Get available games
        games = self.manager.get_available_games()
        
        # Create button for each game
        for game_info in games:
            self._create_game_button(game_info)
        
        self.content_layout.addStretch()
    
    def _create_game_button(self, game_info: dict):
        """Create button for a game."""
        game_frame = QFrame()
        game_frame.setFrameShape(QFrame.Shape.StyledPanel)
        game_layout = QHBoxLayout(game_frame)
        
        # Game name
        name_label = QLabel(game_info.get('name', 'Unknown Game'))
        name_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        game_layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(game_info.get('description', ''))
        desc_label.setStyleSheet("color: gray;")
        game_layout.addWidget(desc_label)
        
        game_layout.addStretch()
        
        # High score
        high_score = game_info.get('high_score', 0)
        score_label = QLabel(f"High Score: {high_score}")
        score_label.setStyleSheet("color: green; font-weight: bold;")
        game_layout.addWidget(score_label)
        
        # Play button
        play_btn = QPushButton("▶ Play")
        play_btn.setStyleSheet("background-color: #10B981; color: white; padding: 8px;")
        play_btn.clicked.connect(lambda: self._start_game(game_info['id']))
        game_layout.addWidget(play_btn)
        
        self.content_layout.addWidget(game_frame)
    
    def _start_game(self, game_id: str):
        """Start a specific game."""
        try:
            self.current_game = self.manager.start_game(game_id)
            
            if game_id == "click_speed":
                self._show_click_game()
            elif game_id == "memory_match":
                self._show_memory_game()
            elif game_id == "reflex_test":
                self._show_reflex_game()
            else:
                QMessageBox.information(self, "Game", f"Starting {game_id}")
                self._show_game_selection()
        except Exception as e:
            logger.error(f"Failed to start game {game_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start game: {str(e)}")
    
    def _show_click_game(self):
        """Show click speed game."""
        # Clear content
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Title
        title = QLabel("🖱️ Click Speed Challenge")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Click the button as many times as you can in 10 seconds!")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(instructions)
        
        # Click button
        self.click_btn = QPushButton("CLICK ME!")
        self.click_btn.setStyleSheet("font-size: 24pt; padding: 40px; background-color: #3B82F6;")
        self.click_btn.clicked.connect(self._on_click_game_click)
        self.content_layout.addWidget(self.click_btn)
        
        # Score and timer
        info_layout = QHBoxLayout()
        self.click_score_label = QLabel("Clicks: 0")
        self.click_score_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        info_layout.addWidget(self.click_score_label)
        
        self.click_timer_label = QLabel("Time: 10s")
        self.click_timer_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        info_layout.addWidget(self.click_timer_label)
        
        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        self.content_layout.addWidget(info_widget)
        
        # Back button
        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(self._end_game)
        self.content_layout.addWidget(back_btn)
        
        self.content_layout.addStretch()
        
        # Start game timer (100ms updates using QTimer)
        self.click_count = 0
        self.click_time_left = 10.0
        self.game_timer.start(100)  # 100ms = 0.1s
    
    def _on_game_timer(self):
        """Handle game timer tick (replaces .after())."""
        if hasattr(self, 'click_time_left'):
            self.click_time_left -= 0.1
            if self.click_time_left <= 0:
                self.game_timer.stop()
                self._end_click_game()
            else:
                self.click_timer_label.setText(f"Time: {self.click_time_left:.1f}s")
    
    def _on_click_game_click(self):
        """Handle click in click game."""
        self.click_count += 1
        self.click_score_label.setText(f"Clicks: {self.click_count}")
    
    def _end_click_game(self):
        """End click speed game."""
        self.game_timer.stop()
        
        score = self.click_count
        result = self.manager.end_game(self.current_game, score)
        
        QMessageBox.information(
            self,
            "Game Over",
            f"Final Score: {score} clicks!\n\n{result.message}"
        )
        
        self.game_completed.emit(self.current_game.game_id, score)
        self._show_game_selection()
    
    def _show_memory_game(self):
        """Show memory match game."""
        # Clear content
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Title
        title = QLabel("🧠 Memory Match")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Match pairs of cards!")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(instructions)
        
        # Grid of cards (simplified)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        
        self.memory_cards = []
        for i in range(4):
            for j in range(4):
                btn = QPushButton("?")
                btn.setMinimumSize(80, 80)
                btn.setStyleSheet("font-size: 24pt;")
                btn.clicked.connect(lambda checked, idx=i*4+j: self._on_memory_card_click(idx))
                grid_layout.addWidget(btn, i, j)
                self.memory_cards.append(btn)
        
        self.content_layout.addWidget(grid_widget)
        
        # Score
        self.memory_score_label = QLabel("Matches: 0 / 8")
        self.memory_score_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.content_layout.addWidget(self.memory_score_label)
        
        # Back button
        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(self._end_game)
        self.content_layout.addWidget(back_btn)
        
        self.content_layout.addStretch()
        
        # Initialize game state
        self.memory_matches = 0
        self.memory_first_card = None
    
    def _on_memory_card_click(self, idx: int):
        """Handle memory card click."""
        # Simplified implementation
        if self.memory_first_card is None:
            self.memory_first_card = idx
            self.memory_cards[idx].setText("🐼")
        else:
            second_card = idx
            self.memory_cards[second_card].setText("🐼")
            
            # Check match after 1 second using QTimer
            self.action_timer.timeout.connect(lambda: self._check_memory_match(self.memory_first_card, second_card))
            self.action_timer.start(1000)
    
    def _check_memory_match(self, first: int, second: int):
        """Check if memory cards match."""
        # Simplified - just count as match
        self.memory_matches += 1
        self.memory_score_label.setText(f"Matches: {self.memory_matches} / 8")
        self.memory_first_card = None
        
        if self.memory_matches >= 8:
            self._end_memory_game()
    
    def _end_memory_game(self):
        """End memory match game."""
        score = self.memory_matches * 100
        result = self.manager.end_game(self.current_game, score)
        
        QMessageBox.information(
            self,
            "Game Over",
            f"Final Score: {score}!\n\n{result.message}"
        )
        
        self.game_completed.emit(self.current_game.game_id, score)
        self._show_game_selection()
    
    def _show_reflex_game(self):
        """Show reflex test game."""
        # Clear content
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Title
        title = QLabel("⚡ Reflex Test")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Click the target as fast as you can when it appears!")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(instructions)
        
        # Target area
        self.reflex_target = QPushButton("READY...")
        self.reflex_target.setStyleSheet("font-size: 18pt; padding: 60px; background-color: gray;")
        self.reflex_target.setEnabled(False)
        self.reflex_target.clicked.connect(self._on_reflex_click)
        self.content_layout.addWidget(self.reflex_target)
        
        # Score
        self.reflex_score_label = QLabel("Average: 0ms")
        self.reflex_score_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.content_layout.addWidget(self.reflex_score_label)
        
        # Back button
        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(self._end_game)
        self.content_layout.addWidget(back_btn)
        
        self.content_layout.addStretch()
        
        # Start first round using QTimer (1 second delay)
        self.reflex_times = []
        self.action_timer.timeout.connect(self._start_reflex_round)
        self.action_timer.start(1000)
    
    def _start_reflex_round(self):
        """Start a reflex round."""
        import random
        delay = random.randint(1000, 3000)  # 1-3 seconds
        
        self.action_timer.timeout.disconnect()
        self.action_timer.timeout.connect(self._show_reflex_target)
        self.action_timer.start(delay)
    
    def _show_reflex_target(self):
        """Show reflex target."""
        from datetime import datetime
        self.reflex_start_time = datetime.now()
        self.reflex_target.setText("CLICK NOW!")
        self.reflex_target.setStyleSheet("font-size: 18pt; padding: 60px; background-color: red; color: white;")
        self.reflex_target.setEnabled(True)
    
    def _on_reflex_click(self):
        """Handle reflex click."""
        from datetime import datetime
        if hasattr(self, 'reflex_start_time'):
            reaction_time = (datetime.now() - self.reflex_start_time).total_seconds() * 1000
            self.reflex_times.append(reaction_time)
            
            avg_time = sum(self.reflex_times) / len(self.reflex_times)
            self.reflex_score_label.setText(f"Average: {avg_time:.0f}ms")
            
            self.reflex_target.setEnabled(False)
            self.reflex_target.setText("READY...")
            self.reflex_target.setStyleSheet("font-size: 18pt; padding: 60px; background-color: gray;")
            
            if len(self.reflex_times) >= 5:
                self._end_reflex_game()
            else:
                # Start next round using QTimer
                self.action_timer.timeout.disconnect()
                self.action_timer.timeout.connect(self._start_reflex_round)
                self.action_timer.start(1000)
    
    def _end_reflex_game(self):
        """End reflex test game."""
        avg_time = sum(self.reflex_times) / len(self.reflex_times)
        score = int(1000 / avg_time * 100)  # Lower time = higher score
        
        result = self.manager.end_game(self.current_game, score)
        
        QMessageBox.information(
            self,
            "Game Over",
            f"Average Reaction Time: {avg_time:.0f}ms\nScore: {score}\n\n{result.message}"
        )
        
        self.game_completed.emit(self.current_game.game_id, score)
        self._show_game_selection()
    
    def _end_game(self):
        """End current game and return to menu."""
        self.game_timer.stop()
        self.action_timer.stop()
        
        if self.current_game:
            self.manager.end_game(self.current_game, 0)
            self.current_game = None
        
        self._show_game_selection()
    
    def _update_stats(self):
        """Update statistics display."""
        stats = self.manager.get_player_stats()
        total_games = stats.get('total_games', 0)
        total_score = stats.get('total_score', 0)
        
        self.stats_label.setText(
            f"Total Games: {total_games} | Total Score: {total_score}"
        )
