"""
Mini-Game System - Fun interactive games with the panda
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import random
import time
from typing import Optional, Callable, Dict
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class GameDifficulty(Enum):
    """Game difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXTREME = "extreme"


@dataclass
class GameResult:
    """Result of a mini-game."""
    game_name: str
    score: int
    duration_seconds: float
    difficulty: GameDifficulty
    xp_earned: int
    currency_earned: int
    perfect_score: bool = False


class MiniGame(ABC):
    """Base class for all mini-games."""
    
    def __init__(self, difficulty: GameDifficulty = GameDifficulty.MEDIUM):
        """
        Initialize mini-game.
        
        Args:
            difficulty: Game difficulty level
        """
        self.difficulty = difficulty
        self.score = 0
        self.start_time = None
        self.end_time = None
        self.is_running = False
        self.is_paused = False
        self._pause_start = None
        self._total_paused = 0.0
    
    @abstractmethod
    def start(self) -> None:
        """Start the game."""
        self.start_time = time.time()
        self.is_running = True
        self.is_paused = False
        self._pause_start = None
        self._total_paused = 0.0
        self.score = 0
    
    def pause(self) -> bool:
        """Pause the game. Returns True if successfully paused."""
        if not self.is_running or self.is_paused:
            return False
        self.is_paused = True
        self._pause_start = time.time()
        logger.info(f"Game paused: {self.get_name()}")
        return True
    
    def resume(self) -> bool:
        """Resume the game. Returns True if successfully resumed."""
        if not self.is_running or not self.is_paused:
            return False
        self.is_paused = False
        if self._pause_start:
            self._total_paused += time.time() - self._pause_start
            self._pause_start = None
        logger.info(f"Game resumed: {self.get_name()}")
        return True
    
    def _elapsed_time(self) -> float:
        """Get elapsed game time excluding paused time."""
        if not self.start_time:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        total = end - self.start_time
        paused = self._total_paused
        if self.is_paused and self._pause_start:
            paused += time.time() - self._pause_start
        return total - paused
    
    @abstractmethod
    def stop(self) -> GameResult:
        """
        Stop the game and return results.
        
        Returns:
            GameResult with score and rewards
        """
        # Finalize pause tracking before recording end time
        if self.is_paused and self._pause_start:
            self._total_paused += time.time() - self._pause_start
            self._pause_start = None
        self.is_paused = False
        self.end_time = time.time()
        self.is_running = False
        duration = self._elapsed_time()
        
        # Calculate rewards based on score and difficulty
        xp = self._calculate_xp()
        currency = self._calculate_currency()
        
        return GameResult(
            game_name=self.get_name(),
            score=self.score,
            duration_seconds=duration,
            difficulty=self.difficulty,
            xp_earned=xp,
            currency_earned=currency,
            perfect_score=self._is_perfect_score()
        )
    
    @abstractmethod
    def get_name(self) -> str:
        """Get game name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get game description."""
        pass
    
    def _calculate_xp(self) -> int:
        """Calculate XP reward based on score and difficulty."""
        base_xp = self.score
        
        # Difficulty multiplier
        multipliers = {
            GameDifficulty.EASY: 1.0,
            GameDifficulty.MEDIUM: 1.5,
            GameDifficulty.HARD: 2.0,
            GameDifficulty.EXTREME: 3.0
        }
        
        return int(base_xp * multipliers[self.difficulty])
    
    def _calculate_currency(self) -> int:
        """Calculate currency reward based on score."""
        return self.score // 10  # 1 currency per 10 points
    
    def _is_perfect_score(self) -> bool:
        """Check if score is perfect."""
        return False  # Override in subclasses


class PandaClickGame(MiniGame):
    """Click the panda as many times as possible in time limit."""
    
    def __init__(self, difficulty: GameDifficulty = GameDifficulty.MEDIUM):
        super().__init__(difficulty)
        self.time_limit = self._get_time_limit()
        self.clicks = 0
    
    def _get_time_limit(self) -> float:
        """Get time limit based on difficulty."""
        limits = {
            GameDifficulty.EASY: 30.0,
            GameDifficulty.MEDIUM: 20.0,
            GameDifficulty.HARD: 10.0,
            GameDifficulty.EXTREME: 5.0
        }
        return limits[self.difficulty]
    
    def start(self) -> None:
        """Start the click game."""
        super().start()
        self.clicks = 0
        logger.info(f"Started panda click game - {self.time_limit}s time limit")
    
    def on_click(self) -> bool:
        """
        Handle a click event.
        
        Returns:
            True if game is still running
        """
        if not self.is_running or self.is_paused:
            return False
        
        # Check time limit
        elapsed = self._elapsed_time()
        if elapsed >= self.time_limit:
            return False
        
        self.clicks += 1
        self.score = self.clicks
        return True
    
    def get_remaining_time(self) -> float:
        """Get remaining time in seconds."""
        if not self.is_running or not self.start_time:
            return 0.0
        
        elapsed = self._elapsed_time()
        return max(0.0, self.time_limit - elapsed)
    
    def stop(self) -> GameResult:
        """Stop the game and return results."""
        result = super().stop()
        logger.info(f"Panda click game ended - {self.clicks} clicks")
        return result
    
    def get_name(self) -> str:
        return "Panda Click Challenge"
    
    def get_description(self) -> str:
        return f"Click the panda as many times as you can in {self.time_limit} seconds!"
    
    def _is_perfect_score(self) -> bool:
        """Perfect score requires high click rate."""
        # Perfect = 3 clicks per second
        target_clicks = int(self.time_limit * 3)
        return self.clicks >= target_clicks


class PandaMemoryGame(MiniGame):
    """Memory matching game with panda emojis."""
    
    PANDA_EMOJIS = ["🐼", "🎋", "🎍", "🐾", "💚", "⚪", "⚫", "🎎"]
    
    def __init__(self, difficulty: GameDifficulty = GameDifficulty.MEDIUM):
        super().__init__(difficulty)
        self.grid_size = self._get_grid_size()
        self.cards = []
        self.revealed_cards = []
        self.matched_pairs = 0
        self.attempts = 0
        self.max_pairs = (self.grid_size ** 2) // 2
    
    def _get_grid_size(self) -> int:
        """Get grid size based on difficulty."""
        sizes = {
            GameDifficulty.EASY: 2,    # 2x2 = 4 cards, 2 pairs
            GameDifficulty.MEDIUM: 4,  # 4x4 = 16 cards, 8 pairs
            GameDifficulty.HARD: 4,    # 4x4 with timer
            GameDifficulty.EXTREME: 6  # 6x6 = 36 cards, 18 pairs
        }
        return sizes[self.difficulty]
    
    def start(self) -> None:
        """Start the memory game."""
        super().start()
        self.matched_pairs = 0
        self.attempts = 0
        self._generate_cards()
        logger.info(f"Started memory game - {self.grid_size}x{self.grid_size} grid")
    
    def _generate_cards(self) -> None:
        """Generate shuffled card pairs."""
        num_pairs = (self.grid_size ** 2) // 2
        emojis = (self.PANDA_EMOJIS * 5)[:num_pairs]  # Get enough emojis
        
        # Create pairs
        self.cards = emojis + emojis
        random.shuffle(self.cards)
    
    def reveal_card(self, index: int) -> Optional[str]:
        """
        Reveal a card.
        
        Args:
            index: Card index
            
        Returns:
            Card emoji or None if invalid
        """
        if not self.is_running or self.is_paused:
            return None
        
        if index < 0 or index >= len(self.cards):
            return None
        
        return self.cards[index]
    
    def check_match(self, index1: int, index2: int) -> bool:
        """
        Check if two cards match.
        
        Args:
            index1: First card index
            index2: Second card index
            
        Returns:
            True if cards match
        """
        if not self.is_running or self.is_paused:
            return False
        
        self.attempts += 1
        
        if self.cards[index1] == self.cards[index2]:
            self.matched_pairs += 1
            
            # Calculate score (perfect = fewer attempts)
            # Base score: 100 per pair, -5 per attempt
            self.score = (self.matched_pairs * 100) - (self.attempts * 5)
            self.score = max(0, self.score)
            
            # Check if game complete - mark as done without calling stop()
            if self.matched_pairs >= self.max_pairs:
                self.is_running = False
            
            return True
        
        return False
    
    def stop(self) -> GameResult:
        """Stop the game and return results."""
        result = super().stop()
        logger.info(f"Memory game ended - {self.matched_pairs}/{self.max_pairs} pairs, {self.attempts} attempts")
        return result
    
    def get_name(self) -> str:
        return "Panda Memory Match"
    
    def get_description(self) -> str:
        return f"Match all {self.max_pairs} pairs of panda emojis!"
    
    def _is_perfect_score(self) -> bool:
        """Perfect score = matched all pairs with minimal attempts."""
        return self.matched_pairs == self.max_pairs and self.attempts <= self.max_pairs


class PandaReflexGame(MiniGame):
    """Test your reflexes by clicking when panda appears."""
    
    def __init__(self, difficulty: GameDifficulty = GameDifficulty.MEDIUM):
        super().__init__(difficulty)
        self.rounds = self._get_rounds()
        self.current_round = 0
        self.reaction_times = []
        self.target_shown_time = None
    
    def _get_rounds(self) -> int:
        """Get number of rounds based on difficulty."""
        rounds = {
            GameDifficulty.EASY: 5,
            GameDifficulty.MEDIUM: 10,
            GameDifficulty.HARD: 15,
            GameDifficulty.EXTREME: 20
        }
        return rounds[self.difficulty]
    
    def start(self) -> None:
        """Start the reflex game."""
        super().start()
        self.current_round = 0
        self.reaction_times = []
        logger.info(f"Started reflex game - {self.rounds} rounds")
    
    def show_target(self) -> None:
        """Show the target - record time."""
        self.target_shown_time = time.time()
    
    def on_target_click(self) -> Optional[float]:
        """
        Handle target click - measure reaction time.
        
        Returns:
            Reaction time in milliseconds or None if invalid
        """
        if not self.is_running or self.is_paused or not self.target_shown_time:
            return None
        
        reaction_time = (time.time() - self.target_shown_time) * 1000  # Convert to ms
        self.reaction_times.append(reaction_time)
        self.target_shown_time = None
        
        self.current_round += 1
        
        # Calculate score (faster = better)
        # Score: 1000 - reaction_time, minimum 100
        round_score = max(100, 1000 - int(reaction_time))
        self.score += round_score
        
        # Check if game complete - mark as done without calling stop()
        if self.current_round >= self.rounds:
            self.is_running = False
        
        return reaction_time
    
    def get_average_reaction_time(self) -> float:
        """Get average reaction time in milliseconds."""
        if not self.reaction_times:
            return 0.0
        return sum(self.reaction_times) / len(self.reaction_times)
    
    def stop(self) -> GameResult:
        """Stop the game and return results."""
        result = super().stop()
        avg_time = self.get_average_reaction_time()
        logger.info(f"Reflex game ended - avg reaction: {avg_time:.2f}ms")
        return result
    
    def get_name(self) -> str:
        return "Panda Reflex Test"
    
    def get_description(self) -> str:
        return f"Click the panda as fast as you can! {self.rounds} rounds."
    
    def _is_perfect_score(self) -> bool:
        """Perfect score = average reaction time under 200ms."""
        return self.get_average_reaction_time() < 200.0


class MiniGameManager:
    """Manages all mini-games and their state."""
    
    def __init__(self, currency_callback: Optional[Callable] = None, 
                 xp_callback: Optional[Callable] = None):
        """
        Initialize mini-game manager.
        
        Args:
            currency_callback: Callback to award currency
            xp_callback: Callback to award XP
        """
        self.games: Dict[str, type] = {
            'click': PandaClickGame,
            'memory': PandaMemoryGame,
            'reflex': PandaReflexGame
        }
        
        self.current_game: Optional[MiniGame] = None
        self.game_history = []
        self.currency_callback = currency_callback
        self.xp_callback = xp_callback
    
    def get_available_games(self) -> list:
        """
        Get list of available games.
        
        Returns:
            List of game info dictionaries
        """
        games = []
        
        for game_id, game_class in self.games.items():
            # Create temporary instance to get info
            temp_game = game_class()
            games.append({
                'id': game_id,
                'name': temp_game.get_name(),
                'description': temp_game.get_description()
            })
        
        return games
    
    def start_game(self, game_id: str, difficulty: GameDifficulty = GameDifficulty.MEDIUM) -> Optional[MiniGame]:
        """
        Start a mini-game.
        
        Args:
            game_id: Game identifier
            difficulty: Game difficulty
            
        Returns:
            MiniGame instance or None if invalid
        """
        if game_id not in self.games:
            logger.error(f"Unknown game: {game_id}")
            return None
        
        # Stop current game if running
        if self.current_game and self.current_game.is_running:
            self.current_game.stop()
        
        # Create and start new game
        game_class = self.games[game_id]
        self.current_game = game_class(difficulty)
        self.current_game.start()
        
        logger.info(f"Started mini-game: {game_id} ({difficulty.value})")
        return self.current_game
    
    def stop_current_game(self) -> Optional[GameResult]:
        """
        Stop the current game.
        
        Returns:
            GameResult or None if no game running
        """
        if not self.current_game:
            return None
        
        result = self.current_game.stop()
        self.game_history.append(result)
        
        # Award rewards
        if self.currency_callback:
            self.currency_callback(result.currency_earned)
        
        if self.xp_callback:
            self.xp_callback(result.xp_earned)
        
        logger.info(f"Game ended: {result.game_name} - Score: {result.score}, XP: {result.xp_earned}, Currency: {result.currency_earned}")
        
        return result
    
    def get_current_game(self) -> Optional[MiniGame]:
        """Get the currently running game."""
        return self.current_game
    
    def get_statistics(self) -> Dict:
        """
        Get mini-game statistics.
        
        Returns:
            Statistics dictionary
        """
        total_games = len(self.game_history)
        total_xp = sum(r.xp_earned for r in self.game_history)
        total_currency = sum(r.currency_earned for r in self.game_history)
        perfect_scores = sum(1 for r in self.game_history if r.perfect_score)
        
        return {
            'total_games': total_games,
            'total_xp_earned': total_xp,
            'total_currency_earned': total_currency,
            'perfect_scores': perfect_scores,
            'games_by_type': self._count_games_by_type(),
            'average_score': self._calculate_average_score()
        }
    
    def _count_games_by_type(self) -> Dict[str, int]:
        """Count games played by type."""
        counts = {}
        for result in self.game_history:
            counts[result.game_name] = counts.get(result.game_name, 0) + 1
        return counts
    
    def _calculate_average_score(self) -> float:
        """Calculate average score across all games."""
        if not self.game_history:
            return 0.0
        return sum(r.score for r in self.game_history) / len(self.game_history)
