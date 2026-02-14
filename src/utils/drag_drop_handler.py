"""
Drag-and-Drop Handler for Tkinter/CustomTkinter
Provides drag-and-drop functionality for file/folder inputs
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import platform
from pathlib import Path
from typing import Optional, Callable, List

logger = logging.getLogger(__name__)

# Check for tkinterdnd2 availability
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    TKDND_AVAILABLE = True
except ImportError:
    TKDND_AVAILABLE = False
    logger.debug("tkinterdnd2 not available, drag-and-drop will use native tkinter")


class DragDropHandler:
    """
    Handler for drag-and-drop functionality.
    
    Supports:
    - Files and folders
    - Multiple file drops
    - Path normalization
    - Callback on drop
    """
    
    def __init__(self):
        """Initialize drag-drop handler."""
        self.system = platform.system()
    
    def enable_drop(self, widget, callback: Callable[[List[str]], None], 
                   accept_folders: bool = True, accept_files: bool = True):
        """
        Enable drag-and-drop on a widget.
        
        Args:
            widget: Tkinter widget to enable drop on
            callback: Function to call with list of dropped paths
            accept_folders: Whether to accept folder drops
            accept_files: Whether to accept file drops
        """
        if TKDND_AVAILABLE:
            self._enable_tkdnd_drop(widget, callback, accept_folders, accept_files)
        else:
            self._enable_native_drop(widget, callback, accept_folders, accept_files)
    
    def _enable_tkdnd_drop(self, widget, callback, accept_folders, accept_files):
        """Enable drop using tkinterdnd2."""
        try:
            widget.drop_target_register(DND_FILES)
            
            def handle_drop(event):
                paths = self._parse_drop_paths(event.data)
                filtered_paths = self._filter_paths(paths, accept_folders, accept_files)
                if filtered_paths:
                    callback(filtered_paths)
                return event.action
            
            widget.dnd_bind('<<Drop>>', handle_drop)
            logger.debug("Enabled tkinterdnd2 drop on widget")
        except Exception as e:
            logger.warning(f"Failed to enable tkinterdnd2 drop: {e}")
    
    def _enable_native_drop(self, widget, callback, accept_folders, accept_files):
        """Enable drop using native tkinter (limited support)."""
        # Native tkinter doesn't support drag-and-drop well
        # This is a placeholder for future platform-specific implementations
        logger.debug("Native drop not fully implemented, tkinterdnd2 required")
    
    def _parse_drop_paths(self, data: str) -> List[str]:
        """
        Parse dropped file paths from event data.
        
        Args:
            data: Raw drop event data
            
        Returns:
            List of file paths
        """
        paths = []
        
        # Handle different formats
        if self.system == "Windows":
            # Windows paths may be in curly braces
            if data.startswith('{'):
                # Multiple files in curly braces
                current = ""
                in_braces = False
                for char in data:
                    if char == '{':
                        in_braces = True
                    elif char == '}':
                        in_braces = False
                        if current:
                            paths.append(current.strip())
                            current = ""
                    elif in_braces:
                        current += char
                if current:
                    paths.append(current.strip())
            else:
                # Single file or space-separated
                paths = [p.strip() for p in data.split() if p.strip()]
        else:
            # Unix-like systems - handle paths with spaces
            # Try splitting by newlines first, then spaces as fallback
            if '\n' in data:
                paths = [p.strip() for p in data.split('\n') if p.strip()]
            else:
                # Use shlex to properly handle quoted paths with spaces
                import shlex
                try:
                    paths = shlex.split(data)
                except ValueError:
                    # Fallback to simple split if shlex fails
                    paths = [p.strip() for p in data.split() if p.strip()]
        
        # Normalize paths
        normalized = []
        for path in paths:
            try:
                p = Path(path)
                if p.exists():
                    normalized.append(str(p))
            except Exception as e:
                logger.warning(f"Invalid path in drop: {path}: {e}")
        
        return normalized
    
    def _filter_paths(self, paths: List[str], accept_folders: bool, 
                     accept_files: bool) -> List[str]:
        """
        Filter paths based on acceptance criteria.
        
        Args:
            paths: List of paths
            accept_folders: Whether to accept folders
            accept_files: Whether to accept files
            
        Returns:
            Filtered list of paths
        """
        filtered = []
        for path in paths:
            p = Path(path)
            if p.is_dir() and accept_folders:
                filtered.append(path)
            elif p.is_file() and accept_files:
                filtered.append(path)
        return filtered
    
    @staticmethod
    def is_available() -> bool:
        """Check if drag-and-drop is available."""
        return TKDND_AVAILABLE


# Global instance
drag_drop_handler = DragDropHandler()
