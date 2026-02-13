"""
Alpha Color Detection and Correction Tool
Automatically detects alpha colors and corrects them to target values
with PS2 presets and batch processing support
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class AlphaCorrectionPresets:
    """Predefined alpha correction presets for different platforms and use cases."""
    
    # PS2 (PlayStation 2) - Binary alpha (0 or 255)
    PS2_BINARY = {
        'name': 'PS2 Binary',
        'description': 'PS2 textures with binary alpha (fully transparent or fully opaque)',
        'thresholds': [(0, 127, 0), (128, 255, 255)],
        'mode': 'threshold'
    }
    
    # PS2 Three-Level - Common in PS2 games (transparent, semi-transparent, opaque)
    PS2_THREE_LEVEL = {
        'name': 'PS2 Three-Level',
        'description': 'PS2 textures with three alpha levels (0, 128, 255)',
        'thresholds': [(0, 42, 0), (43, 212, 128), (213, 255, 255)],
        'mode': 'threshold'
    }
    
    # PS2 UI - UI elements often use specific alpha values
    PS2_UI = {
        'name': 'PS2 UI',
        'description': 'PS2 UI elements with sharp alpha cutoff',
        'thresholds': [(0, 64, 0), (65, 255, 255)],
        'mode': 'threshold'
    }
    
    # PS2 Smooth - Preserves gradients but normalizes to common values
    PS2_SMOOTH = {
        'name': 'PS2 Smooth',
        'description': 'PS2 textures with smooth alpha gradients normalized to standard values',
        'thresholds': [(0, 10, 0), (11, 245, None), (246, 255, 255)],  # None = preserve gradient
        'mode': 'hybrid'
    }
    
    # Generic Binary - Simple binary alpha
    GENERIC_BINARY = {
        'name': 'Generic Binary',
        'description': 'Simple binary alpha (transparent or opaque)',
        'thresholds': [(0, 127, 0), (128, 255, 255)],
        'mode': 'threshold'
    }
    
    # Clean Edges - Remove semi-transparent pixels near edges
    CLEAN_EDGES = {
        'name': 'Clean Edges',
        'description': 'Remove semi-transparent fringing around edges',
        'thresholds': [(0, 32, 0), (33, 223, None), (224, 255, 255)],
        'mode': 'hybrid'
    }
    
    # PS2 Four-Level - Common in PS2 cutscene and effect textures
    PS2_FOUR_LEVEL = {
        'name': 'PS2 Four-Level',
        'description': 'PS2 textures with four alpha levels (0, 85, 170, 255)',
        'thresholds': [(0, 42, 0), (43, 127, 85), (128, 212, 170), (213, 255, 255)],
        'mode': 'threshold'
    }
    
    # PSP - PlayStation Portable alpha style
    PSP_BINARY = {
        'name': 'PSP Binary',
        'description': 'PlayStation Portable (PSP) textures with binary alpha (common in PSP ports)',
        'thresholds': [(0, 100, 0), (101, 255, 255)],
        'mode': 'threshold'
    }
    
    # GameCube/Wii - Often uses 5-bit alpha (8 levels)
    GAMECUBE_WII = {
        'name': 'GameCube/Wii',
        'description': 'GameCube and Wii textures with quantized 5-bit alpha (8 levels)',
        'thresholds': [(0, 16, 0), (17, 52, 36), (53, 88, 73), (89, 124, 109),
                       (125, 160, 146), (161, 196, 182), (197, 232, 219), (233, 255, 255)],
        'mode': 'threshold'
    }
    
    # Xbox - Original Xbox alpha style (similar to PC)
    XBOX_STANDARD = {
        'name': 'Xbox Standard',
        'description': 'Xbox textures with standard 3-level alpha (transparent, half, opaque)',
        'thresholds': [(0, 64, 0), (65, 191, 128), (192, 255, 255)],
        'mode': 'threshold'
    }
    
    # Fade Out - Normalize gradients for fade-out effects
    FADE_OUT = {
        'name': 'Fade Out',
        'description': 'Normalize fade-out gradients — preserves mid-range, snaps extremes',
        'thresholds': [(0, 15, 0), (16, 240, None), (241, 255, 255)],
        'mode': 'hybrid'
    }
    
    # Soft Edges - Preserve soft anti-aliased edges
    SOFT_EDGES = {
        'name': 'Soft Edges',
        'description': 'Preserve soft anti-aliased edges while cleaning up noise',
        'thresholds': [(0, 8, 0), (9, 247, None), (248, 255, 255)],
        'mode': 'hybrid'
    }
    
    # Dithered Alpha - Common in older games using dithered transparency
    DITHERED = {
        'name': 'Dithered',
        'description': 'Fix dithered transparency patterns — snaps to binary alpha',
        'thresholds': [(0, 84, 0), (85, 170, 128), (171, 255, 255)],
        'mode': 'threshold'
    }
    
    @classmethod
    def get_preset(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get preset by name."""
        presets = {
            'ps2_binary': cls.PS2_BINARY,
            'ps2_three_level': cls.PS2_THREE_LEVEL,
            'ps2_ui': cls.PS2_UI,
            'ps2_smooth': cls.PS2_SMOOTH,
            'generic_binary': cls.GENERIC_BINARY,
            'clean_edges': cls.CLEAN_EDGES,
            'ps2_four_level': cls.PS2_FOUR_LEVEL,
            'psp_binary': cls.PSP_BINARY,
            'gamecube_wii': cls.GAMECUBE_WII,
            'xbox_standard': cls.XBOX_STANDARD,
            'fade_out': cls.FADE_OUT,
            'soft_edges': cls.SOFT_EDGES,
            'dithered': cls.DITHERED,
        }
        return presets.get(name.lower())
    
    @classmethod
    def list_presets(cls) -> List[str]:
        """List all available preset names."""
        return [
            'ps2_binary',
            'ps2_three_level',
            'ps2_ui',
            'ps2_smooth',
            'generic_binary',
            'clean_edges',
            'ps2_four_level',
            'psp_binary',
            'gamecube_wii',
            'xbox_standard',
            'fade_out',
            'soft_edges',
            'dithered',
        ]


class AlphaCorrector:
    """
    Alpha channel correction tool for textures.
    
    Features:
    - Detect alpha colors and analyze distribution
    - Correct/normalize alpha to target values
    - PS2 and generic presets
    - Batch processing support
    - Preserve or quantize alpha gradients
    """
    
    def __init__(self):
        """Initialize alpha corrector."""
        self.stats = {
            'images_processed': 0,
            'images_modified': 0,
            'pixels_modified': 0
        }
    
    def detect_alpha_colors(
        self,
        image: np.ndarray
    ) -> Dict[str, Any]:
        """
        Detect and analyze alpha channel colors.
        
        Args:
            image: Input image (H, W, C) or (H, W, RGBA)
            
        Returns:
            Dictionary with alpha color detection results
        """
        # Check if image has alpha channel
        if len(image.shape) != 3 or image.shape[2] != 4:
            return {
                'has_alpha': False,
                'message': 'Image does not have an alpha channel'
            }
        
        alpha = image[:, :, 3]
        
        # Calculate histogram
        hist, bins = np.histogram(alpha, bins=256, range=(0, 256))
        
        # Find dominant alpha values (peaks in histogram)
        # Use a threshold of 1% of total pixels
        threshold = alpha.size * 0.01
        dominant_values = []
        for i, count in enumerate(hist):
            if count > threshold:
                dominant_values.append((i, count))
        
        # Calculate statistics
        unique_values = len(np.unique(alpha))
        has_transparency = np.any(alpha < 255)
        has_semi_transparency = np.any((alpha > 0) & (alpha < 255))
        
        transparent_pixels = np.sum(alpha == 0)
        opaque_pixels = np.sum(alpha == 255)
        semi_pixels = alpha.size - transparent_pixels - opaque_pixels
        
        transparency_ratio = transparent_pixels / alpha.size
        opacity_ratio = opaque_pixels / alpha.size
        semi_ratio = semi_pixels / alpha.size
        
        # Detect if alpha is binary (mostly 0 or 255)
        is_binary = semi_ratio < 0.05
        
        # Detect common patterns
        patterns = []
        if is_binary:
            patterns.append('binary')
        if len(dominant_values) == 3:
            patterns.append('three_level')
        if has_semi_transparency and semi_ratio > 0.1:
            patterns.append('gradient')
        if transparency_ratio > 0.5:
            patterns.append('mostly_transparent')
        elif opacity_ratio > 0.9:
            patterns.append('mostly_opaque')
        
        return {
            'has_alpha': True,
            'unique_values': unique_values,
            'dominant_values': dominant_values[:10],  # Top 10
            'has_transparency': has_transparency,
            'has_semi_transparency': has_semi_transparency,
            'transparent_pixels': int(transparent_pixels),
            'opaque_pixels': int(opaque_pixels),
            'semi_transparent_pixels': int(semi_pixels),
            'transparency_ratio': float(transparency_ratio),
            'opacity_ratio': float(opacity_ratio),
            'semi_transparency_ratio': float(semi_ratio),
            'is_binary': is_binary,
            'patterns': patterns,
            'histogram': hist.tolist(),
            'alpha_min': int(np.min(alpha)),
            'alpha_max': int(np.max(alpha)),
            'alpha_mean': float(np.mean(alpha)),
            'alpha_median': float(np.median(alpha))
        }
    
    def correct_alpha(
        self,
        image: np.ndarray,
        preset: Optional[Union[str, Dict[str, Any]]] = None,
        custom_thresholds: Optional[List[Tuple[int, int, int]]] = None,
        preserve_gradients: bool = False
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Correct alpha channel to target values.
        
        Args:
            image: Input image (H, W, RGBA)
            preset: Preset name or preset dictionary
            custom_thresholds: Custom threshold list [(min, max, target), ...]
                             Use None as target to preserve original value in range
            preserve_gradients: If True, preserve smooth gradients (only snap extremes)
            
        Returns:
            Tuple of (corrected_image, statistics)
        """
        # Check if image has alpha channel
        if len(image.shape) != 3 or image.shape[2] != 4:
            logger.warning("Image does not have alpha channel, returning original")
            return image, {'modified': False, 'reason': 'No alpha channel'}
        
        # Get thresholds from preset or custom
        thresholds = None
        mode = 'threshold'
        
        if preset is not None:
            if isinstance(preset, str):
                preset_dict = AlphaCorrectionPresets.get_preset(preset)
                if preset_dict is None:
                    logger.error(f"Unknown preset: {preset}")
                    return image, {'modified': False, 'reason': f'Unknown preset: {preset}'}
                thresholds = preset_dict['thresholds']
                mode = preset_dict.get('mode', 'threshold')
            elif isinstance(preset, dict):
                thresholds = preset['thresholds']
                mode = preset.get('mode', 'threshold')
        elif custom_thresholds is not None:
            thresholds = custom_thresholds
        else:
            logger.error("Either preset or custom_thresholds must be provided")
            return image, {'modified': False, 'reason': 'No thresholds specified'}
        
        # Create corrected image
        corrected = image.copy()
        alpha = corrected[:, :, 3]
        original_alpha = alpha.copy()
        
        # Track modifications
        pixels_modified = 0
        
        # Apply thresholds
        for min_val, max_val, target in thresholds:
            mask = (alpha >= min_val) & (alpha <= max_val)
            pixels_in_range = np.sum(mask)
            
            if pixels_in_range == 0:
                continue
            
            if target is None:
                # Preserve original values in this range
                continue
            elif preserve_gradients and (max_val - min_val) > 50:
                # Preserve gradient, only modify if far from target
                # Map the range [min_val, max_val] to [target, target]
                # But only if difference is significant
                diff = np.abs(alpha[mask] - target)
                significant_mask = mask & (diff > 20)
                alpha[significant_mask] = target
                pixels_modified += np.sum(significant_mask)
            else:
                # Set to target value
                alpha[mask] = target
                pixels_modified += pixels_in_range
        
        corrected[:, :, 3] = alpha
        
        # Calculate statistics
        alpha_changed = np.sum(original_alpha != alpha)
        stats = {
            'modified': alpha_changed > 0,
            'pixels_modified': int(pixels_modified),
            'pixels_changed': int(alpha_changed),
            'total_pixels': int(alpha.size),
            'modification_ratio': float(alpha_changed / alpha.size),
            'mode': mode,
            'preserve_gradients': preserve_gradients
        }
        
        self.stats['images_processed'] += 1
        if stats['modified']:
            self.stats['images_modified'] += 1
            self.stats['pixels_modified'] += stats['pixels_changed']
        
        return corrected, stats
    
    def process_image(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        preset: str = 'ps2_binary',
        overwrite: bool = False,
        backup: bool = True
    ) -> Dict[str, Any]:
        """
        Process a single image file.
        
        Args:
            image_path: Input image path
            output_path: Output path (defaults to same as input with _corrected suffix)
            preset: Correction preset name
            overwrite: If True, overwrite input file
            backup: If True and overwrite=True, create backup
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Load image
            img = Image.open(image_path)
            
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                if img.mode == 'RGB':
                    # No alpha channel, nothing to correct
                    return {
                        'success': False,
                        'path': str(image_path),
                        'reason': 'No alpha channel (RGB image)'
                    }
                img = img.convert('RGBA')
            
            img_array = np.array(img)
            
            # Detect alpha colors
            detection = self.detect_alpha_colors(img_array)
            
            # Correct alpha
            corrected, stats = self.correct_alpha(img_array, preset=preset)
            
            if not stats['modified']:
                return {
                    'success': True,
                    'path': str(image_path),
                    'modified': False,
                    'detection': detection,
                    'reason': 'No changes needed'
                }
            
            # Determine output path
            if overwrite:
                out_path = image_path
                if backup:
                    backup_path = image_path.with_suffix(f'.backup{image_path.suffix}')
                    img.save(backup_path)
                    logger.info(f"Backup created: {backup_path}")
            elif output_path:
                out_path = output_path
            else:
                out_path = image_path.with_stem(f"{image_path.stem}_corrected")
            
            # Save corrected image
            out_path.parent.mkdir(parents=True, exist_ok=True)
            corrected_img = Image.fromarray(corrected)
            corrected_img.save(out_path)
            
            return {
                'success': True,
                'path': str(image_path),
                'output_path': str(out_path),
                'modified': True,
                'detection': detection,
                'correction': stats
            }
            
        except Exception as e:
            logger.error(f"Error processing {image_path}: {e}", exc_info=True)
            return {
                'success': False,
                'path': str(image_path),
                'error': str(e)
            }
    
    def process_batch(
        self,
        image_paths: List[Path],
        output_dir: Optional[Path] = None,
        preset: str = 'ps2_binary',
        preserve_structure: bool = True,
        overwrite: bool = False,
        backup: bool = True,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple images in batch.
        
        Args:
            image_paths: List of input image paths
            output_dir: Output directory (if None, save next to originals)
            preset: Correction preset name
            preserve_structure: If True, preserve directory structure in output
            overwrite: If True, overwrite input files
            backup: If True and overwrite=True, create backups
            progress_callback: Optional callback function(current, total)
            
        Returns:
            List of processing results
        """
        results = []
        total = len(image_paths)
        
        logger.info(f"Processing {total} images with preset '{preset}'...")
        
        # Find common root if preserving structure
        common_root = None
        if preserve_structure and output_dir and len(image_paths) > 1:
            try:
                # Start with the first path's parent
                common_root = Path(image_paths[0]).resolve().parent
                # Find the common parent directory of all paths
                for path in image_paths[1:]:
                    resolved_path = path.resolve()
                    # Keep going up until we find a common parent
                    while not str(resolved_path).startswith(str(common_root) + str(Path('/'))):
                        common_root = common_root.parent
                        # Safety check to avoid going above filesystem root
                        if common_root == common_root.parent:
                            common_root = None
                            break
            except Exception:
                common_root = None
        
        for idx, img_path in enumerate(image_paths):
            if progress_callback:
                progress_callback(idx + 1, total)
            
            # Determine output path
            out_path = None
            if output_dir and not overwrite:
                if preserve_structure and common_root:
                    rel_path = img_path.relative_to(common_root)
                    out_path = output_dir / rel_path
                else:
                    out_path = output_dir / img_path.name
            
            result = self.process_image(
                img_path,
                output_path=out_path,
                preset=preset,
                overwrite=overwrite,
                backup=backup
            )
            results.append(result)
            
            if result['success'] and result.get('modified'):
                logger.info(f"[{idx+1}/{total}] Corrected: {img_path.name}")
            elif result['success']:
                logger.debug(f"[{idx+1}/{total}] Skipped: {img_path.name}")
            else:
                logger.warning(f"[{idx+1}/{total}] Failed: {img_path.name}")
        
        # Print summary
        successful = sum(1 for r in results if r['success'])
        modified = sum(1 for r in results if r.get('modified'))
        failed = total - successful
        
        logger.info(f"\nBatch processing complete:")
        logger.info(f"  Total: {total}")
        logger.info(f"  Modified: {modified}")
        logger.info(f"  Unchanged: {successful - modified}")
        logger.info(f"  Failed: {failed}")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            'images_processed': 0,
            'images_modified': 0,
            'pixels_modified': 0
        }
