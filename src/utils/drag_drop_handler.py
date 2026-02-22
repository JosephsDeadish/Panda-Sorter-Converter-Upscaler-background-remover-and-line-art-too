"""
Drag-and-Drop Handler for PyQt6
Provides drag-and-drop functionality for file/folder inputs using Qt6 native API
Author: Dead On The Inside / JosephsDeadish
"""


from __future__ import annotations
import logging
import platform
from pathlib import Path
from typing import Optional, Callable, List

logger = logging.getLogger(__name__)

try:
    from PyQt6.QtCore import Qt, QUrl
    from PyQt6.QtGui import QDragEnterEvent, QDropEvent
    from PyQt6.QtWidgets import QWidget
    PYQT_AVAILABLE = True
except (ImportError, OSError, RuntimeError):
    PYQT_AVAILABLE = False
    logger.warning("PyQt6 not available, drag-and-drop will not work")
    class QObject:  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass
    class QWidget(QObject):  # type: ignore[no-redef]
        """Fallback stub when PyQt6 is not installed."""
        pass



class DragDropHandler:
    """
    Handler for drag-and-drop functionality using PyQt6.
    
    Supports:
    - Files and folders
    - Multiple file drops
    - Path normalization
    - Callback on drop
    """
    
    def __init__(self):
        """Initialize drag-drop handler."""
        self.system = platform.system()
    
    def enable_drop(self, widget: QWidget, callback: Callable[[List[str]], None], 
                   accept_folders: bool = True, accept_files: bool = True):
        """
        Enable drag-and-drop on a Qt widget.
        
        Args:
            widget: Qt widget to enable drop on
            callback: Function to call with list of dropped paths
            accept_folders: Whether to accept folder drops
            accept_files: Whether to accept file drops
        """
        if not PYQT_AVAILABLE:
            logger.warning("PyQt6 not available, cannot enable drag-drop")
            return
        
        # Enable drag-and-drop on the widget
        widget.setAcceptDrops(True)
        
        # Store callback and filters as widget attributes for event handlers
        widget._drop_callback = callback
        widget._accept_folders = accept_folders
        widget._accept_files = accept_files
        widget._drag_drop_handler = self
        
        # Override dragEnterEvent and dropEvent
        original_drag_enter = widget.dragEnterEvent
        original_drop = widget.dropEvent
        
        def new_drag_enter_event(event: QDragEnterEvent):
            """Handle drag enter event."""
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                original_drag_enter(event)
        
        def new_drop_event(event: QDropEvent):
            """Handle drop event."""
            if event.mimeData().hasUrls():
                urls = event.mimeData().urls()
                paths = self._parse_urls(urls)
                filtered_paths = self._filter_paths(paths, accept_folders, accept_files)
                if filtered_paths:
                    callback(filtered_paths)
                event.acceptProposedAction()
            else:
                original_drop(event)
        
        # Replace event handlers
        widget.dragEnterEvent = new_drag_enter_event
        widget.dropEvent = new_drop_event
        
        logger.debug(f"Enabled Qt6 drag-drop on widget {widget.__class__.__name__}")
    
    def _parse_urls(self, urls: List[QUrl]) -> List[str]:
        """
        Parse dropped URLs to file paths.
        
        Args:
            urls: List of QUrl objects from drop event
            
        Returns:
            List of file paths
        """
        paths = []
        for url in urls:
            if url.isLocalFile():
                path = url.toLocalFile()
                try:
                    p = Path(path)
                    if p.exists():
                        paths.append(str(p))
                except Exception as e:
                    logger.warning(f"Invalid path in drop: {path}: {e}")
        return paths
    
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
        return PYQT_AVAILABLE


# Global instance
drag_drop_handler = DragDropHandler()
