"""
Currency System - Money management and tracking
Replaces points with money for purchasing shop items
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass, asdict
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


@dataclass
class MoneyTransaction:
    """Represents a money transaction."""
    timestamp: str
    amount: int  # Positive for earned, negative for spent
    reason: str
    balance_after: int


class CurrencySystem:
    """Manages money earning and spending."""
    
    # Configuration constants
    MAX_TRANSACTION_HISTORY = 100  # Number of transactions to keep in history
    
    # Money rewards for various actions
    REWARDS = {
        # File operations
        'file_processed': 1,  # Per file
        'batch_complete': 50,  # Per batch of 100+ files
        'conversion_complete': 2,  # Per file converted
        
        # Achievements (these get overridden by achievement points)
        'achievement_bronze': 10,
        'achievement_silver': 25,
        'achievement_gold': 100,
        'achievement_platinum': 200,
        'achievement_legendary': 500,
        
        # Daily bonuses
        'daily_login': 50,
        'streak_bonus': 25,  # Per day streak
        
        # Interactions
        'panda_pet': 5,
        'panda_feed': 10,
        'tutorial_complete': 100,
        
        # Time-based
        'session_hour': 20,  # Per hour
        
        # Special
        'easter_egg_found': 50,
        'milestone_reached': 100,
    }
    
    def __init__(self, save_path: Optional[Path] = None):
        """
        Initialize currency system.
        
        Args:
            save_path: Path to save money data
        """
        self.save_path = save_path or Path.home() / '.ps2_texture_sorter' / 'money.json'
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.balance = 0
        self.total_earned = 0
        self.total_spent = 0
        self.transactions: List[MoneyTransaction] = []
        self.last_login_date = None
        self.login_streak = 0
        
        self._lock = threading.Lock()
        
        # Load saved data
        self.load()
    
    def earn_money(self, amount: int, reason: str) -> int:
        """
        Earn money.
        
        Args:
            amount: Amount to earn
            reason: Reason for earning
            
        Returns:
            New balance
        """
        with self._lock:
            self.balance += amount
            self.total_earned += amount
            
            transaction = MoneyTransaction(
                timestamp=datetime.now().isoformat(),
                amount=amount,
                reason=reason,
                balance_after=self.balance
            )
            self.transactions.append(transaction)
            
            logger.info(f"Earned ${amount} for '{reason}'. New balance: ${self.balance}")
            self.save()
            return self.balance
    
    def spend_money(self, amount: int, reason: str) -> bool:
        """
        Spend money.
        
        Args:
            amount: Amount to spend
            reason: Reason for spending
            
        Returns:
            True if purchase successful, False if insufficient funds
        """
        with self._lock:
            if self.balance < amount:
                logger.warning(f"Insufficient funds. Need ${amount}, have ${self.balance}")
                return False
            
            self.balance -= amount
            self.total_spent += amount
            
            transaction = MoneyTransaction(
                timestamp=datetime.now().isoformat(),
                amount=-amount,
                reason=reason,
                balance_after=self.balance
            )
            self.transactions.append(transaction)
            
            logger.info(f"Spent ${amount} on '{reason}'. New balance: ${self.balance}")
            self.save()
            return True
    
    def can_afford(self, amount: int) -> bool:
        """Check if can afford amount."""
        return self.balance >= amount
    
    def get_balance(self) -> int:
        """Get current balance."""
        return self.balance
    
    def process_daily_login(self) -> int:
        """
        Process daily login bonus.
        
        Returns:
            Money earned from login
        """
        today = datetime.now().date().isoformat()
        
        if self.last_login_date != today:
            # Daily login bonus
            bonus = self.REWARDS['daily_login']
            
            # Check streak
            if self.last_login_date:
                last_date = datetime.fromisoformat(self.last_login_date).date()
                today_date = datetime.now().date()
                days_diff = (today_date - last_date).days
                
                if days_diff == 1:
                    # Streak continues
                    self.login_streak += 1
                    streak_bonus = self.login_streak * self.REWARDS['streak_bonus']
                    bonus += streak_bonus
                    logger.info(f"Login streak: {self.login_streak} days! +${streak_bonus} bonus")
                else:
                    # Streak broken
                    self.login_streak = 1
            else:
                self.login_streak = 1
            
            self.last_login_date = today
            self.earn_money(bonus, f"Daily login (streak: {self.login_streak})")
            return bonus
        
        return 0
    
    def get_reward_for_action(self, action: str, multiplier: int = 1) -> int:
        """
        Get reward amount for action.
        
        Args:
            action: Action name
            multiplier: Multiplier for amount
            
        Returns:
            Reward amount
        """
        base_amount = self.REWARDS.get(action, 0)
        return base_amount * multiplier
    
    def get_statistics(self) -> Dict:
        """Get money statistics."""
        return {
            'balance': self.balance,
            'total_earned': self.total_earned,
            'total_spent': self.total_spent,
            'net_worth': self.balance,
            'transaction_count': len(self.transactions),
            'login_streak': self.login_streak,
            'last_login': self.last_login_date,
        }
    
    def get_recent_transactions(self, count: int = 10) -> List[MoneyTransaction]:
        """Get recent transactions."""
        return self.transactions[-count:]
    
    def save(self):
        """Save money data to file."""
        try:
            data = {
                'balance': self.balance,
                'total_earned': self.total_earned,
                'total_spent': self.total_spent,
                'last_login_date': self.last_login_date,
                'login_streak': self.login_streak,
                'transactions': [asdict(t) for t in self.transactions[-self.MAX_TRANSACTION_HISTORY:]],
            }
            
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved money data to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save money data: {e}")
    
    def load(self):
        """Load money data from file."""
        try:
            if self.save_path.exists():
                with open(self.save_path, 'r') as f:
                    data = json.load(f)
                
                self.balance = data.get('balance', 0)
                self.total_earned = data.get('total_earned', 0)
                self.total_spent = data.get('total_spent', 0)
                self.last_login_date = data.get('last_login_date')
                self.login_streak = data.get('login_streak', 0)
                
                # Load transactions
                transactions_data = data.get('transactions', [])
                self.transactions = [
                    MoneyTransaction(**t) for t in transactions_data
                ]
                
                logger.info(f"Loaded money data. Balance: ${self.balance}")
            else:
                logger.info("No saved money data found. Starting fresh.")
        except Exception as e:
            logger.error(f"Failed to load money data: {e}")
            # Start fresh on error
            self.balance = 0
            self.total_earned = 0
            self.total_spent = 0
