"""
AI-Based Background Remover Tool
Removes backgrounds from images using AI-powered subject isolation
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass
from PIL import Image, ImageFilter
import threading
import queue

logger = logging.getLogger(__name__)

# Check for rembg availability (AI background removal)
try:
    from rembg import remove, new_session
    HAS_REMBG = True
    logger.info("rembg available for AI background removal")
except ImportError:
    HAS_REMBG = False
    logger.warning("rembg not available - AI background removal disabled")

# Check for OpenCV availability (for edge refinement)
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("opencv-python not available - advanced edge refinement disabled")


@dataclass
class BackgroundRemovalResult:
    """Result of a background removal operation."""
    input_path: str
    output_path: str
    success: bool
    error_message: str = ""
    processing_time: float = 0.0
    original_size: Tuple[int, int] = (0, 0)
    output_size: Tuple[int, int] = (0, 0)


@dataclass
class AlphaPreset:
    """Alpha matting preset with optimized settings."""
    name: str
    description: str
    why_use: str
    foreground_threshold: int
    background_threshold: int
    erode_size: int
    edge_refinement: float


class AlphaPresets:
    """
    Predefined alpha matting presets optimized for different use cases.
    Each preset has carefully tuned parameters for best results.
    """
    
    PS2_TEXTURES = AlphaPreset(
        name="PS2 Textures",
        description="Optimized for PlayStation 2 game textures with sharp, pixelated edges",
        why_use="PS2 textures often have hard edges and limited alpha channels. This preset uses "
                "aggressive thresholds (250/5) to preserve pixel-perfect boundaries while removing "
                "backgrounds. Best for sprite sheets, UI elements, and low-res character textures.",
        foreground_threshold=250,
        background_threshold=5,
        erode_size=5,
        edge_refinement=0.2
    )
    
    GAMING_SPRITES = AlphaPreset(
        name="Gaming Assets",
        description="Sharp edges for sprites, icons, and 2D gaming assets",
        why_use="2D gaming assets need crisp, clean edges with no blur. High foreground threshold (245) "
                "ensures solid colors stay solid, while low background threshold (8) aggressively removes "
                "backgrounds. Small erode size (6) preserves fine details like weapon edges and pixel art.",
        foreground_threshold=245,
        background_threshold=8,
        erode_size=6,
        edge_refinement=0.3
    )
    
    ART_ILLUSTRATION = AlphaPreset(
        name="Art/Illustration",
        description="Smooth gradients for hand-drawn art and digital paintings",
        why_use="Artwork often has soft edges, gradients, and semi-transparent elements. Moderate thresholds "
                "(235/15) preserve subtle color transitions. Larger erode size (12) smooths edges without "
                "destroying artistic details. Higher edge refinement (0.7) creates natural-looking cutouts.",
        foreground_threshold=235,
        background_threshold=15,
        erode_size=12,
        edge_refinement=0.7
    )
    
    PHOTOGRAPHY = AlphaPreset(
        name="Photography",
        description="Natural subject isolation for photos with depth of field",
        why_use="Photos have natural depth, lighting, and soft focus areas. Balanced thresholds (230/20) "
                "handle complex lighting. Large erode size (15) creates smooth transitions around subjects. "
                "Maximum edge refinement (0.8) blends edges naturally, perfect for portraits and products.",
        foreground_threshold=230,
        background_threshold=20,
        erode_size=15,
        edge_refinement=0.8
    )
    
    UI_ELEMENTS = AlphaPreset(
        name="UI Elements",
        description="Crisp boundaries for interface graphics and buttons",
        why_use="UI elements require pixel-perfect edges for clarity. Highest foreground threshold (255) "
                "ensures no color bleeding. Minimal background threshold (3) removes all non-solid pixels. "
                "Tiny erode size (4) maintains sharp corners and straight edges. No edge refinement (0.1) "
                "preserves intentional hard edges.",
        foreground_threshold=255,
        background_threshold=3,
        erode_size=4,
        edge_refinement=0.1
    )
    
    CHARACTER_MODELS = AlphaPreset(
        name="3D Character Models",
        description="Blend hair, fur, and fine details on 3D renders",
        why_use="3D renders often have hair, fur, or fine geometric details that need soft edges. "
                "Lower foreground threshold (220) captures semi-transparent strands. Higher background "
                "threshold (25) leaves subtle shadows. Large erode size (18) and high refinement (0.9) "
                "create professional-looking compositing-ready alphas.",
        foreground_threshold=220,
        background_threshold=25,
        erode_size=18,
        edge_refinement=0.9
    )
    
    TRANSPARENT_OBJECTS = AlphaPreset(
        name="Transparent Objects",
        description="Glass, water, smoke, and semi-transparent elements",
        why_use="Transparent materials need to preserve opacity gradients. Very low foreground threshold "
                "(200) captures see-through areas. Moderate background (30) keeps subtle reflections. "
                "Maximum erode size (20) and refinement (1.0) create smooth alpha gradients that preserve "
                "the illusion of transparency.",
        foreground_threshold=200,
        background_threshold=30,
        erode_size=20,
        edge_refinement=1.0
    )
    
    PIXEL_ART = AlphaPreset(
        name="Pixel Art",
        description="Preserve exact pixel boundaries for retro game graphics",
        why_use="Pixel art requires absolute precision - any blur ruins the aesthetic. Maximum foreground (255), "
                "minimum background (0), and tiny erode (2) preserve every single pixel. Zero edge refinement "
                "(0.0) means what you see is what you get - perfect for NES/SNES/GB era graphics.",
        foreground_threshold=255,
        background_threshold=0,
        erode_size=2,
        edge_refinement=0.0
    )
    
    @classmethod
    def get_all_presets(cls) -> List[AlphaPreset]:
        """Get list of all available presets."""
        return [
            cls.PS2_TEXTURES,
            cls.GAMING_SPRITES,
            cls.ART_ILLUSTRATION,
            cls.PHOTOGRAPHY,
            cls.UI_ELEMENTS,
            cls.CHARACTER_MODELS,
            cls.TRANSPARENT_OBJECTS,
            cls.PIXEL_ART
        ]
    
    @classmethod
    def get_preset_by_name(cls, name: str) -> Optional[AlphaPreset]:
        """Get a preset by its name."""
        for preset in cls.get_all_presets():
            if preset.name == name:
                return preset
        return None


class BackgroundRemover:
    """
    AI-powered background remover with batch processing capabilities.
    """
    
    def __init__(self, model_name: str = "u2net"):
        """
        Initialize the background remover.
        
        Args:
            model_name: Model to use for background removal
                       Options: 'u2net', 'u2netp', 'u2net_human_seg', 'silueta'
        """
        self.model_name = model_name
        self.session = None
        self.processing_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.is_processing = False
        self.cancel_requested = False
        
        # Edge refinement settings
        self.edge_refinement = 0.5  # 0 = no refinement, 1 = maximum refinement
        self.feather_radius = 2  # Pixel radius for edge feathering
        
        # Initialize session if rembg available
        if HAS_REMBG:
            try:
                self.session = new_session(model_name)
                logger.info(f"Background removal session initialized with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize background removal session: {e}")
                self.session = None
    
    def is_available(self) -> bool:
        """Check if background removal is available."""
        return HAS_REMBG and self.session is not None
    
    def set_edge_refinement(self, refinement: float):
        """
        Set edge refinement level.
        
        Args:
            refinement: Refinement level (0.0 to 1.0)
                       0.0 = no refinement (sharp edges)
                       1.0 = maximum refinement (very smooth edges)
        """
        self.edge_refinement = max(0.0, min(1.0, refinement))
        self.feather_radius = int(1 + self.edge_refinement * 5)  # 1-6 pixel radius
        logger.debug(f"Edge refinement set to {self.edge_refinement:.2f}, feather radius: {self.feather_radius}")
    
    def apply_preset(self, preset: AlphaPreset):
        """
        Apply an alpha matting preset to the remover settings.
        
        Args:
            preset: AlphaPreset to apply
        """
        self.set_edge_refinement(preset.edge_refinement)
        logger.info(f"Applied preset '{preset.name}': fg={preset.foreground_threshold}, "
                   f"bg={preset.background_threshold}, erode={preset.erode_size}, "
                   f"refinement={preset.edge_refinement}")
    
    def remove_background(
        self, 
        image: Image.Image,
        alpha_matting: bool = False,
        alpha_matting_foreground_threshold: int = 240,
        alpha_matting_background_threshold: int = 10,
        alpha_matting_erode_size: int = 10
    ) -> Optional[Image.Image]:
        """
        Remove background from a single image.
        
        Args:
            image: Input PIL Image
            alpha_matting: Enable alpha matting for better edges
            alpha_matting_foreground_threshold: Foreground threshold for alpha matting
            alpha_matting_background_threshold: Background threshold for alpha matting
            alpha_matting_erode_size: Erosion size for alpha matting
        
        Returns:
            Image with transparent background or None on failure
        """
        if not self.is_available():
            logger.error("Background removal not available")
            return None
        
        try:
            # Remove background using rembg
            output = remove(
                image,
                session=self.session,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
                alpha_matting_background_threshold=alpha_matting_background_threshold,
                alpha_matting_erode_size=alpha_matting_erode_size
            )
            
            # Apply edge refinement if enabled
            if self.edge_refinement > 0.0:
                output = self._refine_edges(output)
            
            return output
            
        except Exception as e:
            logger.error(f"Background removal failed: {e}")
            return None
    
    def _refine_edges(self, image: Image.Image) -> Image.Image:
        """
        Refine edges of the transparent image for smoother results.
        
        Args:
            image: Image with alpha channel
        
        Returns:
            Image with refined edges
        """
        try:
            # Ensure image has alpha channel
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Extract alpha channel
            alpha = image.split()[-1]
            
            # Apply Gaussian blur to alpha channel for smooth edges
            if self.feather_radius > 0:
                alpha = alpha.filter(ImageFilter.GaussianBlur(radius=self.feather_radius))
            
            # Optionally use OpenCV for advanced edge refinement
            if HAS_CV2 and self.edge_refinement > 0.5:
                alpha_np = np.array(alpha)
                
                # Apply morphological operations for cleaner edges
                kernel_size = int(1 + self.edge_refinement * 3)
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
                
                # Close small holes
                alpha_np = cv2.morphologyEx(alpha_np, cv2.MORPH_CLOSE, kernel)
                
                # Smooth the edges
                alpha_np = cv2.GaussianBlur(alpha_np, (0, 0), sigmaX=self.edge_refinement * 2)
                
                alpha = Image.fromarray(alpha_np)
            
            # Recombine with RGB channels
            r, g, b, _ = image.split()
            refined = Image.merge('RGBA', (r, g, b, alpha))
            
            return refined
            
        except Exception as e:
            logger.error(f"Edge refinement failed: {e}")
            return image  # Return original if refinement fails
    
    def remove_background_from_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        **kwargs
    ) -> BackgroundRemovalResult:
        """
        Remove background from an image file.
        
        Args:
            input_path: Path to input image
            output_path: Path to output image (default: input_path with '_nobg.png' suffix)
            **kwargs: Additional arguments for remove_background
        
        Returns:
            BackgroundRemovalResult with operation details
        """
        import time
        start_time = time.time()
        
        input_path = Path(input_path)
        
        # Determine output path
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_nobg.png"
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Load image
            image = Image.open(input_path)
            original_size = image.size
            
            # Remove background
            result_image = self.remove_background(image, **kwargs)
            
            if result_image is None:
                return BackgroundRemovalResult(
                    input_path=str(input_path),
                    output_path=str(output_path),
                    success=False,
                    error_message="Background removal failed",
                    processing_time=time.time() - start_time
                )
            
            # Save as PNG with transparency
            result_image.save(output_path, 'PNG', optimize=True)
            output_size = result_image.size
            
            processing_time = time.time() - start_time
            
            logger.info(f"Background removed: {input_path.name} -> {output_path.name} ({processing_time:.2f}s)")
            
            return BackgroundRemovalResult(
                input_path=str(input_path),
                output_path=str(output_path),
                success=True,
                processing_time=processing_time,
                original_size=original_size,
                output_size=output_size
            )
            
        except Exception as e:
            logger.error(f"Failed to process {input_path}: {e}")
            return BackgroundRemovalResult(
                input_path=str(input_path),
                output_path=str(output_path),
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def batch_process(
        self,
        input_paths: List[str],
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        **kwargs
    ) -> List[BackgroundRemovalResult]:
        """
        Process multiple images in batch.
        
        Args:
            input_paths: List of input image paths
            output_dir: Directory for output images (default: same as input)
            progress_callback: Callback function(current, total, filename)
            **kwargs: Additional arguments for remove_background
        
        Returns:
            List of BackgroundRemovalResult objects
        """
        results = []
        total = len(input_paths)
        
        self.cancel_requested = False
        
        for i, input_path in enumerate(input_paths):
            # Check for cancellation
            if self.cancel_requested:
                logger.info("Batch processing cancelled")
                break
            
            # Determine output path
            input_path = Path(input_path)
            if output_dir:
                output_path = Path(output_dir) / f"{input_path.stem}_nobg.png"
            else:
                output_path = None
            
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total, input_path.name)
            
            # Process image
            result = self.remove_background_from_file(
                str(input_path),
                str(output_path) if output_path else None,
                **kwargs
            )
            results.append(result)
        
        # Final summary
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        total_time = sum(r.processing_time for r in results)
        
        logger.info(
            f"Batch processing complete: {successful} successful, {failed} failed, "
            f"total time: {total_time:.2f}s"
        )
        
        return results
    
    def batch_process_async(
        self,
        input_paths: List[str],
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        completion_callback: Optional[Callable[[List[BackgroundRemovalResult]], None]] = None,
        **kwargs
    ) -> threading.Thread:
        """
        Process multiple images asynchronously in a background thread.
        
        Args:
            input_paths: List of input image paths
            output_dir: Directory for output images
            progress_callback: Callback function(current, total, filename)
            completion_callback: Callback when processing completes
            **kwargs: Additional arguments for remove_background
        
        Returns:
            Thread object (already started)
        """
        def worker():
            self.is_processing = True
            try:
                results = self.batch_process(
                    input_paths,
                    output_dir,
                    progress_callback,
                    **kwargs
                )
                if completion_callback:
                    completion_callback(results)
            finally:
                self.is_processing = False
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread
    
    def cancel_processing(self):
        """Cancel ongoing batch processing."""
        self.cancel_requested = True
        logger.info("Cancellation requested")
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported models.
        
        Returns:
            List of model names
        """
        return [
            'u2net',          # General purpose (largest, most accurate)
            'u2netp',         # Lightweight version (faster, smaller)
            'u2net_human_seg', # Optimized for human subjects
            'silueta'         # Alternative general purpose model
        ]
    
    def change_model(self, model_name: str) -> bool:
        """
        Change the background removal model.
        
        Args:
            model_name: Name of the model to use
        
        Returns:
            True if model changed successfully
        """
        if model_name not in self.get_supported_models():
            logger.error(f"Unsupported model: {model_name}")
            return False
        
        if not HAS_REMBG:
            logger.error("rembg not available")
            return False
        
        try:
            self.model_name = model_name
            self.session = new_session(model_name)
            logger.info(f"Model changed to: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to change model: {e}")
            return False


def check_dependencies() -> dict:
    """
    Check if required dependencies are installed.
    
    Returns:
        Dict with availability status for each dependency
    """
    return {
        'rembg': HAS_REMBG,
        'opencv': HAS_CV2,
        'pil': True  # PIL/Pillow is always available in this project
    }


if __name__ == "__main__":
    # Test background remover
    print("Background Remover Test")
    print("=" * 50)
    
    deps = check_dependencies()
    print("Dependencies:")
    for dep, available in deps.items():
        status = "✓" if available else "✗"
        print(f"  {status} {dep}")
    print()
    
    if HAS_REMBG:
        print("✓ Background removal is available")
        remover = BackgroundRemover()
        print(f"  Current model: {remover.model_name}")
        print(f"  Supported models: {', '.join(remover.get_supported_models())}")
    else:
        print("✗ Background removal not available")
        print("  Install with: pip install rembg")
