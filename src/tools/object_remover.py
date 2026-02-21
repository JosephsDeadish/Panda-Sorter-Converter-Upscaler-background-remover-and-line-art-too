"""
Object Remover - Interactive object removal with mask painting
Allows users to highlight/paint objects they want to remove from images
"""


from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional, Tuple, List
try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False

logger = logging.getLogger(__name__)

# Check for rembg availability
try:
    from rembg import remove
    from rembg import new_session
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
    
    def paint_mask(self, x: int, y: int, brush_size: int = 20, erase: bool = False, opacity: int = 100):
        """
        Paint on the mask at given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            brush_size: Size of brush in pixels
            erase: If True, erase mask (paint black), else paint white
            opacity: Brush opacity 0-100%
        """
        if self.mask is None:
            return
        
        # Calculate opacity value (0-255)
        opacity_value = int((opacity / 100.0) * 255)
        
        # For erasing, use inverted opacity
        if erase:
            color = 255 - opacity_value
        else:
            color = opacity_value
        
        # Create a temporary image for this paint operation
        temp_mask = Image.new("L", self.mask.size, 0)
        draw = ImageDraw.Draw(temp_mask)
        
        # Draw circle at position
        radius = brush_size // 2
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=255
        )
        
        # Blend with existing mask using opacity
        mask_array = np.array(self.mask, dtype=np.int16)
        temp_array = np.array(temp_mask, dtype=np.int16)
        
        # Where temp is white, blend with color based on opacity
        blend_mask = temp_array > 0
        if erase:
            # Erase: reduce existing values
            mask_array[blend_mask] = np.maximum(0, mask_array[blend_mask] - opacity_value)
        else:
            # Paint: increase existing values
            mask_array[blend_mask] = np.minimum(255, mask_array[blend_mask] + opacity_value)
        
        self.mask = Image.fromarray(np.clip(mask_array, 0, 255).astype(np.uint8), mode="L")
    
    def paint_mask_stroke(self, points: List[Tuple[int, int]], brush_size: int = 20, erase: bool = False, opacity: int = 100):
        """
        Paint a stroke (line of connected points) on the mask.
        
        Args:
            points: List of (x, y) coordinates
            brush_size: Size of brush in pixels
            erase: If True, erase mask, else paint
            opacity: Brush opacity 0-100%
        """
        if self.mask is None or len(points) < 2:
            return
        
        # For stroke painting with opacity, paint each segment
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            
            # Interpolate points between start and end
            distance = max(abs(x2 - x1), abs(y2 - y1))
            if distance == 0:
                self.paint_mask(x1, y1, brush_size, erase, opacity)
                continue
            
            steps = max(int(distance), 1)
            for step in range(steps + 1):
                t = step / steps
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                self.paint_mask(x, y, brush_size, erase, opacity)
    
    
    def clear_mask(self):
        """Clear the entire mask."""
        if self.mask:
            self.mask = Image.new("L", self.original_image.size, 0)
    
    def paint_rectangle(self, x1: int, y1: int, x2: int, y2: int, erase: bool = False, opacity: int = 100):
        """
        Paint a rectangular selection.
        
        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
            erase: If True, erase, else paint
            opacity: Opacity 0-100%
        """
        if self.mask is None:
            return
        
        # Ensure correct ordering
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        opacity_value = int((opacity / 100.0) * 255)
        mask_array = np.array(self.mask, dtype=np.int16)
        
        # Paint rectangle
        if erase:
            mask_array[y1:y2, x1:x2] = np.maximum(0, mask_array[y1:y2, x1:x2] - opacity_value)
        else:
            mask_array[y1:y2, x1:x2] = np.minimum(255, mask_array[y1:y2, x1:x2] + opacity_value)
        
        self.mask = Image.fromarray(np.clip(mask_array, 0, 255).astype(np.uint8), mode="L")
    
    def paint_polygon(self, points: List[Tuple[int, int]], erase: bool = False, opacity: int = 100):
        """
        Paint a polygon selection (lasso).
        
        Args:
            points: List of (x, y) points forming the polygon
            erase: If True, erase, else paint
            opacity: Opacity 0-100%
        """
        if self.mask is None or len(points) < 3:
            return
        
        opacity_value = int((opacity / 100.0) * 255)
        
        # Create temporary mask with polygon
        temp_mask = Image.new("L", self.mask.size, 0)
        draw = ImageDraw.Draw(temp_mask)
        draw.polygon(points, fill=255)
        
        # Blend with existing mask
        mask_array = np.array(self.mask, dtype=np.int16)
        temp_array = np.array(temp_mask, dtype=np.int16)
        
        blend_mask = temp_array > 0
        if erase:
            mask_array[blend_mask] = np.maximum(0, mask_array[blend_mask] - opacity_value)
        else:
            mask_array[blend_mask] = np.minimum(255, mask_array[blend_mask] + opacity_value)
        
        self.mask = Image.fromarray(np.clip(mask_array, 0, 255).astype(np.uint8), mode="L")
    
    def magic_wand_select(self, x: int, y: int, tolerance: int = 30, erase: bool = False, opacity: int = 100):
        """
        Select similar colors using magic wand (flood fill based).
        
        Args:
            x, y: Start position
            tolerance: Color similarity tolerance (0-255)
            erase: If True, erase, else paint
            opacity: Opacity 0-100%
        """
        if self.original_image is None or self.mask is None:
            return
        
        try:
            # Get target color
            rgb_image = self.original_image.convert("RGB")
            target_color = rgb_image.getpixel((x, y))
            
            # Create selection based on color similarity
            img_array = np.array(rgb_image)
            target = np.array(target_color)
            
            # Calculate color distance
            diff = np.abs(img_array - target)
            distance = np.sqrt(np.sum(diff ** 2, axis=2))
            
            # Create selection mask
            selection = distance <= tolerance
            
            # Apply to mask with opacity
            opacity_value = int((opacity / 100.0) * 255)
            mask_array = np.array(self.mask, dtype=np.int16)
            
            if erase:
                mask_array[selection] = np.maximum(0, mask_array[selection] - opacity_value)
            else:
                mask_array[selection] = np.minimum(255, mask_array[selection] + opacity_value)
            
            self.mask = Image.fromarray(np.clip(mask_array, 0, 255).astype(np.uint8), mode="L")
            
        except Exception as e:
            logger.error(f"Magic wand select failed: {e}")
    
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
