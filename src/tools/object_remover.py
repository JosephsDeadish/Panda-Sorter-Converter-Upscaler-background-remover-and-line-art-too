"""
Object Remover - Interactive object removal with mask painting
Allows users to highlight/paint objects they want to remove from images
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw
import numpy as np

logger = logging.getLogger(__name__)

# Check for rembg availability
try:
    from rembg import remove
    from rembg.session import new_session
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    logger.warning("rembg not available. Object removal features disabled.")


class ObjectRemover:
    """
    Interactive object removal tool that uses mask painting.
    Users highlight objects to remove, then AI inpaints those areas.
    """
    
    def __init__(self):
        """Initialize object remover."""
        self.mask = None
        self.original_image = None
        self.processed_image = None
        self.history = []  # Undo/redo history
        self.history_index = -1
        
        # Available models for object removal
        self.available_models = [
            "u2net",
            "u2netp",
            "u2net_human_seg",
            "silueta"
        ]
        self.current_model = "u2net"
        self.session = None
    
    def load_image(self, image_path: str) -> bool:
        """
        Load an image for object removal.
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if successful
        """
        try:
            self.original_image = Image.open(image_path).convert("RGBA")
            # Initialize blank mask (black = keep, white = remove)
            self.mask = Image.new("L", self.original_image.size, 0)
            self.processed_image = self.original_image.copy()
            self.history = [(self.mask.copy(), self.processed_image.copy())]
            self.history_index = 0
            return True
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return False
    
    def paint_mask(self, x: int, y: int, brush_size: int = 20, erase: bool = False):
        """
        Paint on the mask at given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            brush_size: Size of brush in pixels
            erase: If True, erase mask (paint black), else paint white
        """
        if self.mask is None:
            return
        
        draw = ImageDraw.Draw(self.mask)
        color = 0 if erase else 255  # 0 = keep, 255 = remove
        
        # Draw circle at position
        radius = brush_size // 2
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=color
        )
    
    def paint_mask_stroke(self, points: List[Tuple[int, int]], brush_size: int = 20, erase: bool = False):
        """
        Paint a stroke (line of connected points) on the mask.
        
        Args:
            points: List of (x, y) coordinates
            brush_size: Size of brush in pixels
            erase: If True, erase mask, else paint
        """
        if self.mask is None or len(points) < 2:
            return
        
        draw = ImageDraw.Draw(self.mask)
        color = 0 if erase else 255
        
        # Draw line with thickness
        draw.line(points, fill=color, width=brush_size, joint="curve")
        
        # Draw circles at each point for smooth coverage
        radius = brush_size // 2
        for x, y in points:
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=color
            )
    
    def clear_mask(self):
        """Clear the entire mask."""
        if self.mask:
            self.mask = Image.new("L", self.original_image.size, 0)
    
    def invert_mask(self):
        """Invert the mask (swap keep/remove areas)."""
        if self.mask:
            mask_array = np.array(self.mask)
            inverted = 255 - mask_array
            self.mask = Image.fromarray(inverted, mode="L")
    
    def get_mask_overlay(self, color: Tuple[int, int, int] = (255, 0, 0), alpha: int = 128) -> Optional[Image.Image]:
        """
        Get a colored overlay of the mask for preview.
        
        Args:
            color: RGB color for the overlay
            alpha: Transparency (0-255)
            
        Returns:
            RGBA image with colored mask overlay
        """
        if self.mask is None or self.original_image is None:
            return None
        
        # Create colored overlay
        overlay = Image.new("RGBA", self.mask.size, (0, 0, 0, 0))
        mask_array = np.array(self.mask)
        overlay_array = np.array(overlay)
        
        # Where mask is white (255), paint the color
        mask_bool = mask_array > 128
        overlay_array[mask_bool] = (*color, alpha)
        
        overlay = Image.fromarray(overlay_array, mode="RGBA")
        
        # Composite over original
        result = self.original_image.copy()
        result.paste(overlay, (0, 0), overlay)
        
        return result
    
    def remove_object(self, model: Optional[str] = None) -> bool:
        """
        Remove the masked object from the image.
        
        Args:
            model: Model to use (default: current_model)
            
        Returns:
            True if successful
        """
        if not REMBG_AVAILABLE:
            logger.error("rembg not available")
            return False
        
        if self.mask is None or self.original_image is None:
            return False
        
        try:
            model = model or self.current_model
            
            # Initialize session if needed
            if self.session is None or self.current_model != model:
                self.current_model = model
                self.session = new_session(model)
            
            # Our internal convention: black (0) = keep, white (255) = remove
            # We invert for rembg API which uses opposite convention
            mask_array = np.array(self.mask)
            inverted_mask = 255 - mask_array
            inverted_mask_img = Image.fromarray(inverted_mask, mode="L")
            
            # Use rembg with custom mask
            # Note: This is a simplified approach
            # In reality, we'd use an inpainting model for better results
            
            # For now, use rembg to remove background where mask is white
            # Convert to RGB for processing
            rgb_image = self.original_image.convert("RGB")
            
            # Remove background
            output = remove(
                rgb_image,
                session=self.session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=10
            )
            
            # Apply our custom mask
            if output.mode != "RGBA":
                output = output.convert("RGBA")
            
            output_array = np.array(output)
            mask_array = np.array(self.mask)
            
            # Where mask is white (255), make transparent
            mask_bool = mask_array > 128
            output_array[mask_bool, 3] = 0  # Set alpha to 0
            
            self.processed_image = Image.fromarray(output_array, mode="RGBA")
            
            # Save to history
            self._save_to_history()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove object: {e}")
            return False
    
    def _save_to_history(self):
        """Save current state to history for undo/redo."""
        # Remove any future history if we're not at the end
        self.history = self.history[:self.history_index + 1]
        
        # Add current state
        self.history.append((self.mask.copy(), self.processed_image.copy()))
        self.history_index = len(self.history) - 1
        
        # Limit history size
        max_history = 50
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]
            self.history_index = len(self.history) - 1
    
    def undo(self) -> bool:
        """
        Undo to previous state.
        
        Returns:
            True if undo was performed
        """
        if self.history_index > 0:
            self.history_index -= 1
            self.mask, self.processed_image = [
                img.copy() for img in self.history[self.history_index]
            ]
            return True
        return False
    
    def redo(self) -> bool:
        """
        Redo to next state.
        
        Returns:
            True if redo was performed
        """
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.mask, self.processed_image = [
                img.copy() for img in self.history[self.history_index]
            ]
            return True
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self.history_index > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self.history_index < len(self.history) - 1
    
    def save_result(self, output_path: str) -> bool:
        """
        Save the processed image.
        
        Args:
            output_path: Path to save the image
            
        Returns:
            True if successful
        """
        if self.processed_image is None:
            return False
        
        try:
            self.processed_image.save(output_path, "PNG")
            logger.info(f"Saved result to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save result: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return self.available_models.copy()
    
    def set_model(self, model: str):
        """Set the model to use for object removal."""
        if model in self.available_models:
            self.current_model = model
            self.session = None  # Reset session to reload
