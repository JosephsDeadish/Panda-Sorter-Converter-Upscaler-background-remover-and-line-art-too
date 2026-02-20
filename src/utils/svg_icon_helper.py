"""
SVG Icon Integration Helper - Pure Qt Implementation
Provides easy integration of SVG icons into Qt UI panels.
Uses QIcon and QPixmap with Qt's native SVG support.
"""


from __future__ import annotations
try:
    from PyQt6.QtGui import QIcon, QPixmap, QPainter
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtCore import QSize, QByteArray, Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
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
    class QIcon:
        def __init__(self, *a): pass
    class QPixmap:
        def __init__(self, *a): pass
        def isNull(self): return True
    class QPainter:
        def __init__(self, *a): pass
    class QSvgRenderer:
        def __init__(self, *a): pass
    class QSize:
        def __init__(self, *a): pass
    class QByteArray:
        def __init__(self, *a): pass
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger(__name__)


class SVGIconHelper:
    """
    Helper class for loading and using SVG icons in Qt UI.
    Provides caching, error handling, and fallback support.
    Uses Qt's native SVG support for efficient rendering.
    """
    
    def __init__(self, icon_dir: Optional[Path] = None):
        """
        Initialize the SVG icon helper.
        
        Args:
            icon_dir: Directory containing SVG icons (default: src/resources/icons/svg)
        """
        if icon_dir is None:
            # Default to SVG icon directory - use config's path helper for frozen exe compatibility
            try:
                from ..config import get_resource_path
                icon_dir = get_resource_path("icons") / "svg"
            except ImportError:
                # Fallback if config is not available (should not happen in normal use)
                icon_dir = Path(__file__).parent.parent / "resources" / "icons" / "svg"
        
        self.icon_dir = Path(icon_dir)
        self.icon_cache: Dict[str, QIcon] = {}
        self.pixmap_cache: Dict[str, QPixmap] = {}
        
        logger.info(f"SVGIconHelper initialized with icon_dir: {self.icon_dir}")
        logger.info(f"Qt SVG support available: True")
    
    def load_icon(
        self, 
        icon_name: str, 
        size: Tuple[int, int] = (24, 24),
        fallback_emoji: Optional[str] = None
    ) -> Optional[QIcon]:
        """
        Load an SVG icon and return as QIcon.
        
        Args:
            icon_name: Name of the icon (without .svg extension)
            size: Size tuple (width, height)
            fallback_emoji: Emoji to use as fallback (optional)
        
        Returns:
            QIcon object or None
        """
        # Check cache
        cache_key = f"{icon_name}_{size[0]}x{size[1]}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        # Try to load SVG
        icon_path = self.icon_dir / f"{icon_name}.svg"
        
        if not icon_path.exists():
            logger.warning(f"Icon file not found: {icon_path}")
            return None
        
        try:
            # Load SVG using Qt's native SVG renderer
            renderer = QSvgRenderer(str(icon_path))
            
            if not renderer.isValid():
                logger.warning(f"Invalid SVG file: {icon_path}")
                return None
            
            # Create pixmap at desired size with transparent background
            pixmap = QPixmap(size[0], size[1])
            pixmap.fill(Qt.GlobalColor.transparent)
            
            # Render SVG to pixmap
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            # Create QIcon from pixmap
            icon = QIcon(pixmap)
            
            # Cache it
            self.icon_cache[cache_key] = icon
            self.pixmap_cache[cache_key] = pixmap
            
            return icon
            
        except Exception as e:
            logger.error(f"Error loading icon {icon_name}: {e}")
        
        return None
    
    def load_pixmap(
        self,
        icon_name: str,
        size: Tuple[int, int] = (24, 24)
    ) -> Optional[QPixmap]:
        """
        Load an SVG icon and return as QPixmap.
        
        Args:
            icon_name: Name of the icon (without .svg extension)
            size: Size tuple (width, height)
        
        Returns:
            QPixmap object or None
        """
        # Check cache
        cache_key = f"{icon_name}_{size[0]}x{size[1]}"
        if cache_key in self.pixmap_cache:
            return self.pixmap_cache[cache_key]
        
        # Load icon first (which also caches the pixmap)
        icon = self.load_icon(icon_name, size)
        
        if icon and cache_key in self.pixmap_cache:
            return self.pixmap_cache[cache_key]
        
        return None
    
    def load_icons(
        self, 
        icon_names: List[str], 
        size: Tuple[int, int] = (24, 24)
    ) -> Dict[str, Optional[QIcon]]:
        """
        Load multiple icons at once.
        
        Args:
            icon_names: List of icon names
            size: Size tuple (width, height)
        
        Returns:
            Dictionary mapping icon names to QIcon objects
        """
        icons = {}
        for name in icon_names:
            icons[name] = self.load_icon(name, size)
        return icons
    
    def clear_cache(self):
        """Clear the icon cache."""
        self.icon_cache.clear()
        logger.info("Icon cache cleared")


# Predefined icon sets for common use cases
FILE_OPERATION_ICONS = [
    "file_open_animated",
    "file_save_animated",
    "file_delete_animated",
    "file_rename_animated",
    "file_search_animated",
    "file_compare_animated",
    "file_duplicate_animated",
    "folder_open_animated",
    "folder_new_animated",
    "folder_delete_animated",
    "trash_fill_animated",
    "trash_empty_animated",
    "recycle_spin_animated",
]

IMAGE_TOOL_ICONS = [
    "brush_paint_animated",
    "eraser_erase_animated",
    "crop_resize_animated",
    "rotate_spin_animated",
    "flip_horizontal_animated",
    "flip_vertical_animated",
    "zoom_in_enhanced_animated",
    "zoom_out_animated",
    "ruler_measure_animated",
    "eyedropper_drop_animated",
    "magic_wand_animated",
    "lasso_select_animated",
    "text_edit_animated",
    "color_palette_animated",
    "selection_animated",
]

NAVIGATION_ICONS = [
    "arrow_left_animated",
    "arrow_right_animated",
    "arrow_up_animated",
    "arrow_down_animated",
    "chevron_left_animated",
    "chevron_right_animated",
    "double_arrow_left_animated",
    "double_arrow_right_animated",
    "menu_hamburger_animated",
    "menu_dots_animated",
    "expand_maximize_animated",
    "collapse_minimize_animated",
]

STATUS_ICONS = [
    "success_check_animated",
    "warning_triangle_animated",
    "error_cross_animated",
    "info_circle_animated",
    "question_mark_animated",
    "pending_dots_animated",
    "progress_spinner_animated",
    "progress_circle_animated",
    "clock_ticking_animated",
    "bell_notification_animated",
    "flag_waving_animated",
    "star_sparkle_animated",
    "trophy_shine_animated",
    "medal_bounce_animated",
    "badge_pulse_animated",
    "shield_check_animated",
]

PROCESSING_ICONS = [
    "processing_animated",
    "analyzing_animated",
    "converting_animated",
    "syncing_animated",
    "cloud_sync_animated",
    "uploading_animated",
    "downloading_animated",
    "loading_animated",
    "scanning_animated",
    "merging_animated",
    "splitting_animated",
]

MEDIA_ICONS = [
    "play_animated",
    "pause_animated",
    "stop_animated",
    "cloud_upload_animated",
    "cloud_download_animated",
]

UTILITY_ICONS = [
    "link_chain_animated",
    "bookmark_animated",
    "tag_animated",
    "layers_animated",
    "package_animated",
    "calendar_animated",
    "printer_animated",
    "target_animated",
    "image_compare_animated",
]


# Singleton instance for easy access
_icon_helper_instance: Optional[SVGIconHelper] = None


def get_icon_helper() -> SVGIconHelper:
    """Get or create the singleton SVGIconHelper instance."""
    global _icon_helper_instance
    if _icon_helper_instance is None:
        _icon_helper_instance = SVGIconHelper()
    return _icon_helper_instance


def load_icon(
    icon_name: str, 
    size: Tuple[int, int] = (24, 24)
) -> Optional[QIcon]:
    """
    Convenience function to load an icon using the singleton helper.
    
    Args:
        icon_name: Name of the icon (without .svg extension)
        size: Size tuple (width, height)
    
    Returns:
        QIcon object or None
    """
    helper = get_icon_helper()
    return helper.load_icon(icon_name, size)


def load_icon_set(
    icon_set_name: str,
    size: Tuple[int, int] = (24, 24)
) -> Dict[str, Optional[QIcon]]:
    """
    Load a predefined set of icons.
    
    Args:
        icon_set_name: Name of the icon set ("file", "image", "nav", "status", "process", "media", "utility")
        size: Size tuple (width, height)
    
    Returns:
        Dictionary of icon names to QIcon objects
    """
    icon_sets = {
        "file": FILE_OPERATION_ICONS,
        "image": IMAGE_TOOL_ICONS,
        "nav": NAVIGATION_ICONS,
        "status": STATUS_ICONS,
        "process": PROCESSING_ICONS,
        "media": MEDIA_ICONS,
        "utility": UTILITY_ICONS,
    }
    
    if icon_set_name not in icon_sets:
        logger.warning(f"Unknown icon set: {icon_set_name}")
        return {}
    
    helper = get_icon_helper()
    return helper.load_icons(icon_sets[icon_set_name], size)


if __name__ == "__main__":
    # Test the icon helper
    print("SVG Icon Helper Test (Qt Version)")
    print("=" * 50)
    
    helper = SVGIconHelper()
    print(f"Icon directory: {helper.icon_dir}")
    print(f"Qt SVG support: Available")
    print()
    
    # Try to load a test icon
    test_icon = helper.load_icon("file_open_animated", (32, 32))
    if test_icon:
        print("✅ Successfully loaded test icon")
    else:
        print("⚠️ Could not load test icon")
    
    print()
    print("Available icon sets:")
    for set_name in ["file", "image", "nav", "status", "process", "media", "utility"]:
        print(f"- {set_name}")
