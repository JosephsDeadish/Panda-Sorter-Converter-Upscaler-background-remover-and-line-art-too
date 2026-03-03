from __future__ import annotations
"""
Mini-Game UI Panel - PyQt6 Version
Interactive mini-games launcher with Qt native timing
"""

import logging
from typing import Optional
try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFrame, QScrollArea, QGridLayout, QMessageBox
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal
    from PyQt6.QtGui import QFont
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    QWidget = object
    QFrame = object
    QScrollArea = object
    class _SignalStub:  # noqa: E301
        def __init__(self, *a): pass
        def connect(self, *a): pass
        def disconnect(self, *a): pass
        def emit(self, *a): pass
    def pyqtSignal(*a): return _SignalStub()  # noqa: E301
    class Qt:
        class AlignmentFlag:
            AlignLeft = AlignRight = AlignCenter = AlignTop = AlignBottom = AlignHCenter = AlignVCenter = 0
        class WindowType:
            FramelessWindowHint = WindowStaysOnTopHint = Tool = Window = Dialog = 0
        class CursorShape:
            ArrowCursor = PointingHandCursor = BusyCursor = WaitCursor = CrossCursor = 0
        class DropAction:
            CopyAction = MoveAction = IgnoreAction = 0
        class Key:
            Key_Escape = Key_Return = Key_Space = Key_Delete = Key_Up = Key_Down = Key_Left = Key_Right = 0
        class ScrollBarPolicy:
            ScrollBarAlwaysOff = ScrollBarAsNeeded = ScrollBarAlwaysOn = 0
        class ItemFlag:
            ItemIsEnabled = ItemIsSelectable = ItemIsEditable = 0
        class CheckState:
            Unchecked = Checked = PartiallyChecked = 0
        class Orientation:
            Horizontal = Vertical = 0
        class SortOrder:
            AscendingOrder = DescendingOrder = 0
        class MatchFlag:
            MatchExactly = MatchContains = 0
        class ItemDataRole:
            DisplayRole = UserRole = DecorationRole = 0
    class QFont:
        def __init__(self, *a): pass
    class QTimer:
        def __init__(self, *a): pass
        def start(self, *a): pass
        def stop(self): pass
        timeout = property(lambda self: type("S", (), {"connect": lambda s,f: None, "emit": lambda s: None})())
    QGridLayout = object
    QHBoxLayout = object
    QLabel = object
    QMessageBox = object
    QPushButton = object
    QVBoxLayout = object

try:
    from features.minigame_system import (
        MiniGameManager, MiniGame, GameDifficulty, GameResult
    )
    MINIGAME_SYSTEM_AVAILABLE = True
except (ImportError, OSError, RuntimeError) as _mg_err:
    MINIGAME_SYSTEM_AVAILABLE = False
    # Stub classes so the panel can still be imported without crashing
    class MiniGameManager:  # type: ignore[no-redef]
        def get_available_games(self): return []
    class MiniGame:  # type: ignore[no-redef]
        pass
    class GameDifficulty:  # type: ignore[no-redef]
        pass
    class GameResult:  # type: ignore[no-redef]
        pass

logger = logging.getLogger(__name__)


class MiniGamePanelQt(QWidget):
    """Qt panel for launching and playing mini-games."""
    
    game_completed = pyqtSignal(str, int)  # game_id, score
    
    def __init__(self, parent=None, minigame_manager: MiniGameManager = None, tooltip_manager=None):
        """
        Initialize mini-game panel.
        
        Args:
            parent: Parent widget
            minigame_manager: MiniGameManager instance
            tooltip_manager: TooltipVerbosityManager instance
        """
        super().__init__(parent)
        
        self.manager = minigame_manager or MiniGameManager()
        self.current_game = None
        self.game_widgets = {}
        self.tooltip_manager = tooltip_manager
        # Persistent high scores: {game_id: best_score}
        self._high_scores: dict = {}

        # Game timers (using QTimer instead of .after())
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self._on_game_timer)
        
        self.action_timer = QTimer(self)
        self.action_timer.setSingleShot(True)
        
        self._create_widgets()
        # Wire high-score tracking
        self.game_completed.connect(self._record_high_score)
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
        
        # High score — use in-memory tracker
        _gid = game_info['id']
        high_score = self._high_scores.get(_gid, game_info.get('high_score', 0))
        score_label = QLabel(f"🏆 Best: {high_score}")
        score_label.setStyleSheet("color: green; font-weight: bold;")
        game_layout.addWidget(score_label)
        # Store reference so _record_high_score can update it
        setattr(self, f"_hs_label_{_gid}", score_label)
        
        # Play button
        play_btn = QPushButton("▶ Play")
        play_btn.setStyleSheet("background-color: #10B981; color: white; padding: 8px;")
        play_btn.clicked.connect(lambda: self._start_game(game_info['id']))
        self._set_tooltip(play_btn, 'minigames_tab')
        game_layout.addWidget(play_btn)
        
        self.content_layout.addWidget(game_frame)
    
    def _start_game(self, game_id: str):
        """Start a specific game."""
        try:
            self.current_game = self.manager.start_game(game_id, GameDifficulty.MEDIUM)

            if game_id == "click":
                self._show_click_game()
            elif game_id == "memory":
                self._show_memory_game()
            elif game_id == "reflex":
                self._show_reflex_game()
            elif game_id == "bamboo_catcher":
                self._show_bamboo_catcher_game()
            elif game_id == "color_match":
                self._show_color_match_game()
            else:
                QMessageBox.information(self, "Game", f"Starting {game_id}")
                self._show_game_selection()
        except Exception as e:
            logger.error(f"Failed to start game {game_id}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start game: {str(e)}")

    # ── Bamboo Catcher ────────────────────────────────────────────────────────

    def _show_bamboo_catcher_game(self):
        """Show the Bamboo Catcher falling-item game."""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        title = QLabel("🎋 Bamboo Catcher")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(title)

        instructions = QLabel(
            "Move your basket to catch bamboo! Avoid rocks 🪨 and thorns 🌵."
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(instructions)

        # Falling-field display — monospaced text-art updated each tick
        self.bamboo_field_label = QLabel()
        self.bamboo_field_label.setStyleSheet(
            "font-family: monospace; font-size: 11pt; "
            "background: #0a1a0a; color: #90ee90; padding: 8px; border-radius: 4px;"
        )
        self.bamboo_field_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.bamboo_field_label.setMinimumHeight(160)
        self.content_layout.addWidget(self.bamboo_field_label)

        # Status row: time + score
        status_row = QHBoxLayout()
        self.bamboo_timer_label = QLabel("Time: —")
        self.bamboo_timer_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        status_row.addWidget(self.bamboo_timer_label)
        status_row.addStretch()
        self.bamboo_score_label = QLabel("Score: 0")
        self.bamboo_score_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        status_row.addWidget(self.bamboo_score_label)
        status_widget = QWidget()
        status_widget.setLayout(status_row)
        self.content_layout.addWidget(status_widget)

        # Basket controls
        ctrl_row = QHBoxLayout()
        left_btn = QPushButton("← Left")
        left_btn.setStyleSheet("font-size: 14pt; padding: 12px 24px;")
        left_btn.clicked.connect(lambda: self._on_bamboo_move(-1))
        ctrl_row.addWidget(left_btn)
        right_btn = QPushButton("Right →")
        right_btn.setStyleSheet("font-size: 14pt; padding: 12px 24px;")
        right_btn.clicked.connect(lambda: self._on_bamboo_move(1))
        ctrl_row.addWidget(right_btn)
        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl_row)
        self.content_layout.addWidget(ctrl_widget)

        back_btn = QPushButton("Back to Menu")
        back_btn.setToolTip("Return to the mini-game selection menu")
        back_btn.clicked.connect(self._end_game)
        self.content_layout.addWidget(back_btn)
        self.content_layout.addStretch()

        # Dedicated tick timer (150 ms ≈ 6-7 fps — readable without GPU)
        self._bamboo_timer = QTimer(self)
        self._bamboo_timer.timeout.connect(self._on_bamboo_tick)
        self._bamboo_timer.start(150)
        self._bamboo_tick_dt = 0.15
        self._refresh_bamboo_field()

    # Item-kind → display character
    _BAMBOO_ICONS = {
        'bamboo': '🎋',
        'cookie': '🍪',
        'apple':  '🍎',
        'rock':   '🪨',
        'thorn':  '🌵',
    }

    def _refresh_bamboo_field(self):
        """Re-draw the text-art field for the current game state."""
        if not self.current_game or not PYQT_AVAILABLE:
            return
        game = self.current_game
        W = game._FIELD_WIDTH      # 10
        H = game._FIELD_HEIGHT     # 20
        ROWS = 5                   # visible rows in our display

        # Build a compact view: map each item's Y → one of ROWS display rows
        cells = {}
        for item in game.items:
            row = min(ROWS - 1, int(item['y'] * ROWS / H))
            col = int(item['x']) % W
            cells[(row, col)] = self._BAMBOO_ICONS.get(item['kind'], '?')

        lines = []
        for r in range(ROWS):
            row_str = ''
            for c in range(W):
                row_str += cells.get((r, c), '·')
            lines.append(row_str)

        # Basket row
        basket_row = ['_'] * W
        bx = min(W - 1, max(0, game.basket_x))
        half = game._BASKET_WIDTH // 2
        for off in range(-half, half + 1):
            if 0 <= bx + off < W:
                basket_row[bx + off] = '▓'
        basket_row[bx] = '🧺'
        lines.append(''.join(basket_row))

        self.bamboo_field_label.setText('\n'.join(lines))

    def _on_bamboo_move(self, direction: int):
        """Handle left/right basket move."""
        if self.current_game and self.current_game.is_running:
            self.current_game.move_basket(direction)
            self._refresh_bamboo_field()

    def _on_bamboo_tick(self):
        """Advance the bamboo catcher game by one tick."""
        if not self.current_game or not self.current_game.is_running:
            self._bamboo_timer.stop()
            self._end_bamboo_catcher_game()
            return
        still_running = self.current_game.tick(self._bamboo_tick_dt)
        self._refresh_bamboo_field()
        remaining = self.current_game.get_remaining_time()
        self.bamboo_timer_label.setText(f"Time: {remaining:.0f}s")
        self.bamboo_score_label.setText(f"Score: {self.current_game.score}")
        if not still_running or remaining <= 0:
            self._bamboo_timer.stop()
            self._end_bamboo_catcher_game()

    def _end_bamboo_catcher_game(self):
        """End Bamboo Catcher and show results."""
        if hasattr(self, '_bamboo_timer'):
            self._bamboo_timer.stop()
        result = self.manager.stop_current_game()
        if result:
            game = self.current_game or result
            caught = getattr(game, 'caught', 0)
            missed = getattr(game, 'missed', 0)
            QMessageBox.information(
                self, "Game Over",
                f"🎋 Caught: {caught}  |  Missed: {missed}\n"
                f"Final Score: {result.score}\n"
                f"XP Earned: {result.xp_earned}\n"
                f"Currency Earned: {result.currency_earned}"
            )
            self.game_completed.emit('bamboo_catcher', result.score)
        self._show_game_selection()
        self._update_stats()

    # ── Color Match ───────────────────────────────────────────────────────────

    def _show_color_match_game(self):
        """Show the Color Match counting game."""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        title = QLabel("🎨 Color Match")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(title)

        instructions = QLabel(
            "Count how many squares match the target color, then submit your answer!"
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(instructions)

        # Target color banner
        self.cm_target_label = QLabel("Target: ?")
        self.cm_target_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; padding: 8px; border-radius: 6px;"
        )
        self.cm_target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.cm_target_label)

        # Color grid (3 × 3 or 4 × 3 depending on grid_size)
        self.cm_grid_widget = QWidget()
        self.cm_grid_layout = QGridLayout(self.cm_grid_widget)
        self.cm_grid_layout.setSpacing(4)
        self.content_layout.addWidget(self.cm_grid_widget)

        # Timer + score row
        status_row = QHBoxLayout()
        self.cm_timer_label = QLabel("Time: —")
        self.cm_timer_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        status_row.addWidget(self.cm_timer_label)
        status_row.addStretch()
        self.cm_score_label = QLabel("Score: 0")
        self.cm_score_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        status_row.addWidget(self.cm_score_label)
        status_widget = QWidget()
        status_widget.setLayout(status_row)
        self.content_layout.addWidget(status_widget)

        # Answer row: − / count / +  then Submit
        answer_row = QHBoxLayout()
        minus_btn = QPushButton("−")
        minus_btn.setStyleSheet("font-size: 14pt; padding: 6px 16px;")
        minus_btn.clicked.connect(lambda: self._cm_adjust_answer(-1))
        answer_row.addWidget(minus_btn)
        self.cm_answer_label = QLabel("0")
        self.cm_answer_label.setStyleSheet(
            "font-size: 18pt; font-weight: bold; min-width: 40px;"
        )
        self.cm_answer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        answer_row.addWidget(self.cm_answer_label)
        plus_btn = QPushButton("+")
        plus_btn.setStyleSheet("font-size: 14pt; padding: 6px 16px;")
        plus_btn.clicked.connect(lambda: self._cm_adjust_answer(1))
        answer_row.addWidget(plus_btn)
        submit_btn = QPushButton("✓ Submit")
        submit_btn.setStyleSheet(
            "font-size: 14pt; padding: 8px 20px; background: #10B981; color: white;"
        )
        submit_btn.clicked.connect(self._on_cm_submit)
        answer_row.addWidget(submit_btn)
        answer_widget = QWidget()
        answer_widget.setLayout(answer_row)
        self.content_layout.addWidget(answer_widget)

        # Feedback label (shows ✅ Correct! / ❌ Wrong!)
        self.cm_feedback_label = QLabel("")
        self.cm_feedback_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.cm_feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.cm_feedback_label)

        back_btn = QPushButton("Back to Menu")
        back_btn.setToolTip("Return to the mini-game selection menu")
        back_btn.clicked.connect(self._end_game)
        self.content_layout.addWidget(back_btn)
        self.content_layout.addStretch()

        self._cm_answer = 0
        self._refresh_color_match_round()

        # Timer fires every 250 ms to update the countdown
        self._cm_timer = QTimer(self)
        self._cm_timer.timeout.connect(self._on_cm_tick)
        self._cm_timer.start(250)

    # Color → CSS background string
    _CM_COLOR_CSS = {
        'green':  '#22c55e', 'yellow': '#facc15', 'red':   '#ef4444',
        'blue':   '#3b82f6', 'white':  '#f8fafc',  'pink':  '#ec4899',
    }

    def _refresh_color_match_round(self):
        """Re-draw the color grid and target banner for the current round."""
        if not self.current_game or not PYQT_AVAILABLE:
            return
        game = self.current_game
        grid  = game.grid     # list of color strings
        target = game.target

        # Target banner
        bg = self._CM_COLOR_CSS.get(target, '#888')
        text_color = '#000' if target in ('yellow', 'white') else '#fff'
        self.cm_target_label.setText(f"Target: {target.upper()}")
        self.cm_target_label.setStyleSheet(
            f"font-size: 16pt; font-weight: bold; padding: 8px; "
            f"border-radius: 6px; background: {bg}; color: {text_color};"
        )

        # Rebuild grid cells
        # Clear old widgets
        while self.cm_grid_layout.count():
            item = self.cm_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 3
        for idx, color in enumerate(grid):
            cell = QLabel("  ")
            cell_bg = self._CM_COLOR_CSS.get(color, '#888')
            cell.setStyleSheet(
                f"background: {cell_bg}; border: 2px solid #333; "
                f"min-width: 36px; min-height: 36px; border-radius: 4px;"
            )
            self.cm_grid_layout.addWidget(cell, idx // cols, idx % cols)

        # Reset answer counter for each new round
        self._cm_answer = 0
        self.cm_answer_label.setText("0")
        self.cm_feedback_label.setText("")

    def _cm_adjust_answer(self, delta: int):
        """Increment or decrement the user's answer, clamped to [0, grid_size]."""
        if not self.current_game:
            return
        max_val = len(self.current_game.grid)
        self._cm_answer = max(0, min(max_val, self._cm_answer + delta))
        self.cm_answer_label.setText(str(self._cm_answer))

    def _on_cm_submit(self):
        """Player submitted an answer."""
        if not self.current_game or not self.current_game.is_running:
            return
        result_dict = self.current_game.submit_answer(self._cm_answer)
        self.cm_feedback_label.setText(result_dict.get('message', ''))
        self.cm_score_label.setText(f"Score: {self.current_game.score}")
        # New round was started by submit_answer — refresh the display
        self._refresh_color_match_round()

    def _on_cm_tick(self):
        """Timer tick: update countdown; end game when time runs out."""
        if not self.current_game or not self.current_game.is_running:
            self._cm_timer.stop()
            self._end_color_match_game()
            return
        # Drive time-based round expiry.
        # PandaColorMatchGame.tick() returns Optional[GameResult] (not a bool),
        # so checking `is not None` is the correct end-of-game signal here.
        tick_result = self.current_game.tick(0.25)
        remaining = self.current_game.get_remaining_time()
        self.cm_timer_label.setText(f"Time: {remaining:.0f}s")
        self.cm_score_label.setText(f"Score: {self.current_game.score}")
        if tick_result is not None or remaining <= 0:
            self._cm_timer.stop()
            self._end_color_match_game()

    def _end_color_match_game(self):
        """End Color Match and show results."""
        if hasattr(self, '_cm_timer'):
            self._cm_timer.stop()
        result = self.manager.stop_current_game()
        if result:
            QMessageBox.information(
                self, "Game Over",
                f"🎨 Final Score: {result.score}\n"
                f"XP Earned: {result.xp_earned}\n"
                f"Currency Earned: {result.currency_earned}"
            )
            self.game_completed.emit('color_match', result.score)
        self._show_game_selection()
        self._update_stats()

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
        self._set_tooltip(self.click_btn, 'minigames_tab')
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
        back_btn.setToolTip("Return to the mini-game selection menu")
        back_btn.clicked.connect(self._end_game)
        self.content_layout.addWidget(back_btn)
        
        self.content_layout.addStretch()
        
        # Start game timer (100ms updates using QTimer)
        self.click_count = 0
        self.game_timer.start(100)  # 100ms = 0.1s
    
    def _on_game_timer(self):
        """Handle game timer tick (replaces .after())."""
        if self.current_game and hasattr(self.current_game, 'get_remaining_time'):
            remaining = self.current_game.get_remaining_time()
            if remaining <= 0:
                self.game_timer.stop()
                self._end_click_game()
            else:
                self.click_timer_label.setText(f"Time: {remaining:.1f}s")
    
    def _on_click_game_click(self):
        """Handle click in click game."""
        if self.current_game and self.current_game.on_click():
            self.click_count += 1
            self.click_score_label.setText(f"Clicks: {self.click_count}")
    
    def _end_click_game(self):
        """End click speed game."""
        self.game_timer.stop()
        
        # Stop the game and get results
        result = self.manager.stop_current_game()
        
        if result:
            QMessageBox.information(
                self,
                "Game Over",
                f"Final Score: {result.score} clicks!\n"
                f"XP Earned: {result.xp_earned}\n"
                f"Currency Earned: {result.currency_earned}"
            )
            
            self.game_completed.emit('click', result.score)
        
        self._show_game_selection()
        self._update_stats()
    
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
                btn.setToolTip("Click to flip this memory card")
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
        back_btn.setToolTip("Return to the mini-game selection menu")
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
            # Guard: ignore a click on the same card that was already flipped
            if idx == self.memory_first_card:
                return
            second_card = idx
            self.memory_cards[second_card].setText("🐼")
            
            # Check match after 1 second using QTimer
            # Disconnect any previously accumulated connections before adding the new one.
            try:
                self.action_timer.timeout.disconnect()
            except TypeError:
                pass  # No connections exist yet — that's fine
            first_card = self.memory_first_card  # capture now, not at timer-fire time
            self.memory_first_card = None        # reset so subsequent clicks start a fresh pair
            self.action_timer.timeout.connect(lambda: self._check_memory_match(first_card, second_card))
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
        # Stop the game and get results
        result = self.manager.stop_current_game()
        
        if result:
            QMessageBox.information(
                self,
                "Game Over",
                f"Final Score: {result.score}!\n"
                f"XP Earned: {result.xp_earned}\n"
                f"Currency Earned: {result.currency_earned}"
            )
            
            self.game_completed.emit('memory', result.score)
        
        self._show_game_selection()
        self._update_stats()
    
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
        self.reflex_target.setToolTip("Click as quickly as possible when the target turns green!")
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
        back_btn.setToolTip("Return to the mini-game selection menu")
        back_btn.clicked.connect(self._end_game)
        self.content_layout.addWidget(back_btn)
        
        self.content_layout.addStretch()
        
        # Start first round using QTimer (1 second delay)
        self.reflex_times = []
        try:
            self.action_timer.timeout.disconnect()
        except TypeError:
            pass  # No connections yet — fine
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
        # Stop the game and get results
        result = self.manager.stop_current_game()
        
        if result:
            avg_time = self.current_game.get_average_reaction_time() if self.current_game else 0
            QMessageBox.information(
                self,
                "Game Over",
                f"Average Reaction Time: {avg_time:.0f}ms\n"
                f"Score: {result.score}\n"
                f"XP Earned: {result.xp_earned}\n"
                f"Currency Earned: {result.currency_earned}"
            )
            
            self.game_completed.emit('reflex', result.score)
        
        self._show_game_selection()
        self._update_stats()
    
    def _end_game(self):
        """End current game and return to menu."""
        self.game_timer.stop()
        self.action_timer.stop()
        
        if self.current_game:
            self.manager.stop_current_game()
            self.current_game = None
        
        self._show_game_selection()
        self._update_stats()
    
    def _update_stats(self):
        """Update statistics display."""
        stats = self.manager.get_statistics()
        total_games = stats.get('total_games', 0)
        total_xp = stats.get('total_xp_earned', 0)
        total_currency = stats.get('total_currency_earned', 0)
        perfect_scores = stats.get('perfect_scores', 0)
        
        self.stats_label.setText(
            f"Games Played: {total_games} | XP Earned: {total_xp} | "
            f"Currency Earned: {total_currency} | Perfect Scores: {perfect_scores}"
        )
    
    def _record_high_score(self, game_id: str, score: int) -> None:
        """Update high score for *game_id* if *score* is better."""
        prev_best = self._high_scores.get(game_id, 0)
        if score > prev_best:
            self._high_scores[game_id] = score
            # Update the displayed high-score label if visible
            label_attr = f"_hs_label_{game_id}"
            lbl = getattr(self, label_attr, None)
            if lbl is not None:
                try:
                    lbl.setText(f"🏆 Best: {score}")
                except Exception:
                    pass

    def _set_tooltip(self, widget, widget_id_or_text: str):
        """Set tooltip via manager (cycling) when available, else plain text."""
        if self.tooltip_manager and hasattr(self.tooltip_manager, 'register'):
            if ' ' not in widget_id_or_text:
                try:
                    tip = self.tooltip_manager.get_tooltip(widget_id_or_text)
                    if tip:
                        widget.setToolTip(tip)
                        self.tooltip_manager.register(widget, widget_id_or_text)
                        return
                except Exception:
                    pass
        widget.setToolTip(str(widget_id_or_text))

# Alias for backward compatibility
MinigamePanelQt = MiniGamePanelQt
