"""
Auto Backup & Recovery System
Automatically saves state and recovers from crashes
"""

import logging
import json
import pickle
import shutil
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class BackupConfig:
    """Configuration for auto backup system."""
    enabled: bool = True
    interval_seconds: int = 300  # 5 minutes
    max_backups: int = 10
    backup_location: Optional[Path] = None
    backup_processed_files: bool = True


class AutoBackupSystem:
    """
    Manages automatic backup and crash recovery.
    Periodically saves application state and processed files.
    """
    
    def __init__(self, app_dir: Path, config: Optional[BackupConfig] = None):
        """
        Initialize auto backup system.
        
        Args:
            app_dir: Application directory for storing backups
            config: Backup configuration
        """
        self.app_dir = Path(app_dir)
        self.config = config or BackupConfig()
        
        # Setup backup directory
        if self.config.backup_location:
            self.backup_dir = Path(self.config.backup_location)
        else:
            self.backup_dir = self.app_dir / "backups"
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Crash detection file
        self.crash_file = self.app_dir / ".crash_detection"
        
        # State tracking
        self.current_state: Dict[str, Any] = {}
        self.last_backup_time = 0
        self.backup_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Callbacks
        self.on_backup_complete: Optional[Callable] = None
        self.on_recovery_available: Optional[Callable] = None
    
    def start(self):
        """Start auto backup system."""
        if not self.config.enabled:
            logger.info("Auto backup disabled")
            return
        
        # Mark application as running
        self._create_crash_file()
        
        # Check for previous crash
        if self._check_for_crash():
            if self.on_recovery_available:
                self.on_recovery_available()
        
        # Start backup thread
        self.running = True
        self.backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.backup_thread.start()
        logger.info(f"Auto backup started (interval: {self.config.interval_seconds}s)")
    
    def stop(self):
        """Stop auto backup system gracefully."""
        self.running = False
        
        # Remove crash detection file (clean shutdown)
        self._remove_crash_file()
        
        # Final backup
        self.backup_now()
        
        if self.backup_thread:
            self.backup_thread.join(timeout=5.0)
        
        logger.info("Auto backup stopped")
    
    def update_state(self, state: Dict[str, Any]):
        """
        Update current application state.
        
        Args:
            state: Dictionary containing application state
        """
        self.current_state.update(state)
    
    def backup_now(self) -> bool:
        """
        Perform immediate backup.
        
        Returns:
            True if backup successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.json"
            
            # Prepare backup data
            backup_data = {
                "timestamp": timestamp,
                "state": self.current_state,
                "version": "1.0"
            }
            
            # Save as JSON
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Also save as pickle for complex objects
            pickle_file = self.backup_dir / f"backup_{timestamp}.pkl"
            with open(pickle_file, 'wb') as f:
                pickle.dump(backup_data, f)
            
            logger.info(f"Backup created: {backup_file}")
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            # Update last backup time
            self.last_backup_time = time.time()
            
            # Callback
            if self.on_backup_complete:
                self.on_backup_complete(backup_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def get_latest_backup(self) -> Optional[Path]:
        """
        Get path to most recent backup file.
        
        Returns:
            Path to latest backup or None
        """
        backups = list(self.backup_dir.glob("backup_*.json"))
        if not backups:
            return None
        
        # Sort by modification time
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backups[0]
    
    def restore_from_backup(self, backup_file: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        Restore application state from backup.
        
        Args:
            backup_file: Specific backup to restore, or None for latest
            
        Returns:
            Restored state dictionary or None
        """
        if backup_file is None:
            backup_file = self.get_latest_backup()
        
        if not backup_file or not backup_file.exists():
            logger.warning("No backup file found")
            return None
        
        try:
            # Try pickle first (preserves complex objects)
            pickle_file = backup_file.with_suffix('.pkl')
            if pickle_file.exists():
                with open(pickle_file, 'rb') as f:
                    backup_data = pickle.load(f)
            else:
                # Fallback to JSON
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
            
            logger.info(f"Restored from backup: {backup_file}")
            return backup_data.get("state", {})
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return None
    
    def list_backups(self) -> list:
        """
        List all available backups.
        
        Returns:
            List of backup files with metadata
        """
        backups = []
        for backup_file in self.backup_dir.glob("backup_*.json"):
            try:
                stat = backup_file.stat()
                backups.append({
                    "file": backup_file,
                    "timestamp": datetime.fromtimestamp(stat.st_mtime),
                    "size": stat.st_size
                })
            except Exception as e:
                logger.warning(f"Error reading backup {backup_file}: {e}")
        
        # Sort by timestamp descending
        backups.sort(key=lambda b: b["timestamp"], reverse=True)
        return backups
    
    def _backup_loop(self):
        """Background thread that performs periodic backups."""
        while self.running:
            try:
                time.sleep(self.config.interval_seconds)
                
                if self.running and self.current_state:
                    self.backup_now()
                    
            except Exception as e:
                logger.error(f"Backup loop error: {e}")
    
    def _cleanup_old_backups(self):
        """Remove old backups exceeding max_backups limit."""
        backups = list(self.backup_dir.glob("backup_*.json"))
        if len(backups) <= self.config.max_backups:
            return
        
        # Sort by modification time
        backups.sort(key=lambda p: p.stat().st_mtime)
        
        # Remove oldest backups
        for backup in backups[:-self.config.max_backups]:
            try:
                backup.unlink()
                # Also remove pickle file
                pickle_file = backup.with_suffix('.pkl')
                if pickle_file.exists():
                    pickle_file.unlink()
                logger.debug(f"Removed old backup: {backup}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup {backup}: {e}")
    
    def _create_crash_file(self):
        """Create crash detection file."""
        try:
            with open(self.crash_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logger.warning(f"Failed to create crash file: {e}")
    
    def _remove_crash_file(self):
        """Remove crash detection file on clean shutdown."""
        try:
            if self.crash_file.exists():
                self.crash_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove crash file: {e}")
    
    def _check_for_crash(self) -> bool:
        """
        Check if previous session crashed.
        
        Returns:
            True if crash detected
        """
        if self.crash_file.exists():
            logger.warning("Previous session crashed - recovery available")
            return True
        return False
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """
        Get statistics about backups.
        
        Returns:
            Dictionary with backup statistics
        """
        backups = self.list_backups()
        total_size = sum(b["size"] for b in backups)
        
        return {
            "total_backups": len(backups),
            "total_size_mb": total_size / (1024 * 1024),
            "latest_backup": backups[0]["timestamp"] if backups else None,
            "oldest_backup": backups[-1]["timestamp"] if backups else None,
            "backup_dir": str(self.backup_dir)
        }
