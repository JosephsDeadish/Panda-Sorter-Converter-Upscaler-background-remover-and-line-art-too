"""
SVG Support Module for UI
Provides offline SVG loading and rendering capabilities for Qt UI.

Approaches:
1. Convert SVG to PNG in memory (if cairosvg available)
2. Embed static PNG alternatives
3. Use simple SVG-to-raster conversion

This ensures the app works offline without external dependencies.
"""


from __future__ import annotations
import io
import logging
from pathlib import Path
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Check for optional SVG rendering libraries
try:
    import cairosvg
    HAS_CAIROSVG = True
    logger.info("cairosvg available for SVG rendering")
except (ImportError, OSError, RuntimeError):
    HAS_CAIROSVG = False
    logger.debug("cairosvg not available - SVG rendering disabled")

try:
    from PIL import Image
    HAS_PIL = True
except (ImportError, OSError, RuntimeError):
    HAS_PIL = False
    logger.warning("PIL not available - image handling limited")


class SVGLoader:
    """
    Load and render SVG files for use in Qt UI.
    Falls back to PNG if SVG rendering not available.
    """
    
    def __init__(self, fallback_dir: Optional[Path] = None):
        """
        Initialize SVG loader.
        
        Args:
            fallback_dir: Directory containing PNG fallback images
        """
        self.fallback_dir = fallback_dir
        self.svg_capable = HAS_CAIROSVG and HAS_PIL
        
        if self.svg_capable:
            logger.info("SVG rendering fully supported")
        else:
            logger.info("SVG rendering not available - will use fallback PNGs")
    
    def load_svg(
        self, 
        svg_path: Union[str, Path],
        size: Optional[Tuple[int, int]] = None,
        fallback_png: Optional[Union[str, Path]] = None
    ) -> Optional[object]:
        """
        Load an SVG file and return a PIL Image.
        
        Args:
            svg_path: Path to SVG file
            size: Target size (width, height) for rendering
            fallback_png: Path to PNG fallback if SVG can't be rendered
        
        Returns:
            PIL Image object or None if loading fails
        """
        svg_path = Path(svg_path)
        
        # Try SVG rendering if available
        if self.svg_capable and svg_path.exists():
            try:
                return self._render_svg(svg_path, size)
            except Exception as e:
                logger.warning(f"SVG rendering failed for {svg_path}: {e}")
        
        # Fall back to PNG
        if fallback_png:
            fallback_path = Path(fallback_png)
            if fallback_path.exists():
                try:
                    if HAS_PIL:
                        img = Image.open(fallback_path)
                        if size:
                            img = img.resize(size, Image.LANCZOS)
                        return img
                except Exception as e:
                    logger.error(f"Failed to load fallback PNG {fallback_path}: {e}")
        
        # Try to find fallback in fallback_dir
        if self.fallback_dir:
            fallback_name = svg_path.stem + '.png'
            fallback_path = self.fallback_dir / fallback_name
            if fallback_path.exists():
                try:
                    if HAS_PIL:
                        img = Image.open(fallback_path)
                        if size:
                            img = img.resize(size, Image.LANCZOS)
                        return img
                except Exception as e:
                    logger.error(f"Failed to load fallback PNG {fallback_path}: {e}")
        
        logger.error(f"Could not load SVG or find fallback: {svg_path}")
        return None
    
    def _render_svg(self, svg_path: Path, size: Optional[Tuple[int, int]] = None) -> Optional[object]:
        """
        Render SVG to PIL Image using cairosvg.
        
        Args:
            svg_path: Path to SVG file
            size: Target size (width, height)
        
        Returns:
            PIL Image or None
        """
        if not HAS_CAIROSVG or not HAS_PIL:
            return None
        
        try:
            # Read SVG file
            svg_data = svg_path.read_text()
            
            # Render to PNG in memory
            png_data = cairosvg.svg2png(
                bytestring=svg_data.encode('utf-8'),
                output_width=size[0] if size else None,
                output_height=size[1] if size else None
            )
            
            # Convert to PIL Image
            img = Image.open(io.BytesIO(png_data))
            return img
            
        except Exception as e:
            logger.error(f"Error rendering SVG {svg_path}: {e}")
            return None
    
    def svg_from_string(
        self, 
        svg_string: str,
        size: Optional[Tuple[int, int]] = None
    ) -> Optional[object]:
        """
        Render SVG from string data.
        
        Args:
            svg_string: SVG content as string
            size: Target size (width, height)
        
        Returns:
            PIL Image or None
        """
        if not HAS_CAIROSVG or not HAS_PIL:
            return None
        
        try:
            # Render to PNG in memory
            png_data = cairosvg.svg2png(
                bytestring=svg_string.encode('utf-8'),
                output_width=size[0] if size else None,
                output_height=size[1] if size else None
            )
            
            # Convert to PIL Image
            img = Image.open(io.BytesIO(png_data))
            return img
            
        except Exception as e:
            logger.error(f"Error rendering SVG from string: {e}")
            return None


# Simple animated SVG templates (can be rendered frame-by-frame)
def create_loading_spinner_svg(color: str = "#00ff00", size: int = 64) -> str:
    """
    Create a simple loading spinner SVG.
    Can be animated by rotating the viewBox or rendering multiple frames.
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="40" stroke="{color}" stroke-width="8" fill="none" 
            stroke-dasharray="60 200" stroke-linecap="round">
        <animateTransform attributeName="transform" type="rotate" 
                          from="0 50 50" to="360 50 50" dur="1s" repeatCount="indefinite"/>
    </circle>
</svg>'''


def create_checkmark_svg(color: str = "#2B7A0B", size: int = 64) -> str:
    """Create a simple checkmark SVG."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <path d="M20,50 L40,70 L80,30" stroke="{color}" stroke-width="8" 
          fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''


def create_error_svg(color: str = "#B22222", size: int = 64) -> str:
    """Create a simple error/X SVG."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <path d="M25,25 L75,75 M75,25 L25,75" stroke="{color}" stroke-width="8" 
          stroke-linecap="round"/>
</svg>'''


def create_folder_svg(color: str = "#FFA500", size: int = 64) -> str:
    """Create a simple folder icon SVG."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <path d="M10,25 L10,75 L90,75 L90,35 L50,35 L40,25 Z" 
          fill="{color}" stroke="#000" stroke-width="2"/>
</svg>'''


def create_file_svg(color: str = "#4A90E2", size: int = 64) -> str:
    """Create a simple file icon SVG."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <path d="M25,10 L25,90 L75,90 L75,30 L55,10 Z M55,10 L55,30 L75,30" 
          fill="{color}" stroke="#000" stroke-width="2"/>
</svg>'''


# Utility function for Qt integration
def load_svg_for_qt(
    svg_path: Union[str, Path],
    size: Tuple[int, int],
    fallback_png: Optional[Union[str, Path]] = None
) -> Optional[object]:
    """
    Load SVG and prepare it for use with Qt (returns PIL Image).
    The PIL Image can be converted to QPixmap using QPixmap.fromImage().
    
    Args:
        svg_path: Path to SVG file
        size: Size tuple (width, height)
        fallback_png: Optional PNG fallback
    
    Returns:
        PIL Image ready for Qt conversion or None
    """
    loader = SVGLoader()
    return loader.load_svg(svg_path, size, fallback_png)


if __name__ == "__main__":
    # Test SVG support
    print("SVG Support Test")
    print("=" * 50)
    print(f"cairosvg available: {HAS_CAIROSVG}")
    print(f"PIL available: {HAS_PIL}")
    print(f"SVG rendering capable: {HAS_CAIROSVG and HAS_PIL}")
    print()
    
    # Create sample SVGs
    print("Sample SVG templates created:")
    print("- Loading spinner")
    print("- Checkmark")
    print("- Error icon")
    print("- Folder icon")
    print("- File icon")
    print()
    
    if HAS_CAIROSVG and HAS_PIL:
        print("✅ SVG rendering is available")
        print("SVGs can be used in the UI with live rendering")
    else:
        print("⚠️ SVG rendering not available")
        print("Will use PNG fallbacks for icons")
