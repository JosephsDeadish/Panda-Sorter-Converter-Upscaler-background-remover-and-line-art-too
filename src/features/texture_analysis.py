"""
Texture Analysis System
Advanced texture analysis including color extraction, alpha detection, and optimization
Author: Dead On The Inside / JosephsDeadish
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.error("numpy not available - limited functionality")
    logger.error("Install with: pip install numpy")
from PIL import Image
import cv2

logger = logging.getLogger(__name__)


class TextureAnalyzer:
    """
    Advanced texture analysis for PS2 textures.
    
    Features:
    - Color palette extraction
    - Dominant color detection with percentages
    - Alpha channel analysis
    - Compression quality assessment
    - Hash calculation (MD5, SHA256)
    - Corruption detection
    - Format optimization suggestions
    """
    
    def __init__(self, max_palette_colors: int = 10):
        """
        Initialize texture analyzer.
        
        Args:
            max_palette_colors: Maximum number of colors to extract for palette
        """
        self.max_palette_colors = max_palette_colors
        logger.debug(f"TextureAnalyzer initialized with max_palette_colors={max_palette_colors}")
    
    def analyze(self, image_path: Path) -> Dict[str, Any]:
        """
        Perform comprehensive texture analysis.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary containing all analysis results
        """
        try:
            logger.debug(f"Analyzing texture: {image_path}")
            
            # Load image with PIL for general analysis
            with Image.open(image_path) as img:
                basic_info = self._get_basic_info(img, image_path)
                color_info = self._analyze_colors(img)
                alpha_info = self._analyze_alpha(img)
                quality_info = self._analyze_quality(img)
            
            # Load with OpenCV for advanced analysis
            cv_img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
            corruption_info = self._detect_corruption(cv_img)
            
            # Calculate file hashes
            hash_info = self._calculate_hashes(image_path)
            
            # Generate optimization suggestions
            optimization = self._suggest_optimizations(
                basic_info,
                color_info,
                alpha_info,
                quality_info
            )
            
            result = {
                'basic': basic_info,
                'colors': color_info,
                'alpha': alpha_info,
                'quality': quality_info,
                'corruption': corruption_info,
                'hashes': hash_info,
                'optimization': optimization
            }
            
            logger.debug(f"Analysis complete for: {image_path}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze texture {image_path}: {e}")
            return self._get_error_result(str(e))
    
    def _get_basic_info(self, img: Image.Image, path: Path) -> Dict[str, Any]:
        """Extract basic image information."""
        return {
            'format': img.format or 'Unknown',
            'mode': img.mode,
            'width': img.width,
            'height': img.height,
            'size_pixels': img.width * img.height,
            'file_size_bytes': path.stat().st_size,
            'file_size_kb': round(path.stat().st_size / 1024, 2),
            'aspect_ratio': round(img.width / img.height, 3) if img.height > 0 else 0,
            'is_power_of_2': self._is_power_of_2(img.width) and self._is_power_of_2(img.height),
            'is_square': img.width == img.height
        }
    
    def _analyze_colors(self, img: Image.Image) -> Dict[str, Any]:
        """
        Analyze color information including palette extraction.
        
        Returns detailed color analysis with dominant colors and percentages.
        """
        try:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'PA'):
                rgb_img = img.convert('RGB')
            elif img.mode == 'L':
                rgb_img = img.convert('RGB')
            else:
                rgb_img = img
            
            # Get all pixels
            pixels = list(rgb_img.getdata())
            total_pixels = len(pixels)
            
            # Count color occurrences
            color_counts = Counter(pixels)
            unique_colors = len(color_counts)
            
            # Get top colors
            top_colors = color_counts.most_common(self.max_palette_colors)
            
            # Calculate dominant colors with percentages
            palette = []
            for color, count in top_colors:
                percentage = (count / total_pixels) * 100
                palette.append({
                    'rgb': color,
                    'hex': '#{:02x}{:02x}{:02x}'.format(*color),
                    'count': count,
                    'percentage': round(percentage, 2)
                })
            
            # Calculate color statistics
            r_values = [p[0] for p in pixels]
            g_values = [p[1] for p in pixels]
            b_values = [p[2] for p in pixels]
            
            return {
                'unique_colors': unique_colors,
                'palette': palette,
                'dominant_color': {
                    'rgb': top_colors[0][0],
                    'hex': palette[0]['hex'],
                    'percentage': palette[0]['percentage']
                } if palette else None,
                'color_diversity': round(unique_colors / total_pixels, 4),
                'statistics': {
                    'red': {
                        'mean': round(np.mean(r_values), 2),
                        'std': round(np.std(r_values), 2),
                        'min': min(r_values),
                        'max': max(r_values)
                    },
                    'green': {
                        'mean': round(np.mean(g_values), 2),
                        'std': round(np.std(g_values), 2),
                        'min': min(g_values),
                        'max': max(g_values)
                    },
                    'blue': {
                        'mean': round(np.mean(b_values), 2),
                        'std': round(np.std(b_values), 2),
                        'min': min(b_values),
                        'max': max(b_values)
                    }
                },
                'brightness': round(np.mean([np.mean(r_values), np.mean(g_values), np.mean(b_values)]), 2),
                'is_grayscale': self._is_grayscale(pixels)
            }
            
        except Exception as e:
            logger.error(f"Color analysis failed: {e}")
            return {'error': str(e)}
    
    def _analyze_alpha(self, img: Image.Image) -> Dict[str, Any]:
        """
        Analyze alpha channel information.
        
        Returns alpha channel statistics and usage patterns.
        """
        try:
            has_alpha = img.mode in ('RGBA', 'LA', 'PA')
            
            if not has_alpha:
                return {
                    'has_alpha': False,
                    'is_transparent': False,
                    'alpha_usage': 'none'
                }
            
            # Extract alpha channel
            if img.mode == 'RGBA':
                alpha = img.getchannel('A')
            elif img.mode == 'LA':
                alpha = img.getchannel('A')
            else:
                alpha = img.convert('RGBA').getchannel('A')
            
            alpha_data = list(alpha.getdata())
            total_pixels = len(alpha_data)
            
            # Analyze alpha values
            alpha_counter = Counter(alpha_data)
            unique_alpha = len(alpha_counter)
            
            fully_opaque = alpha_counter.get(255, 0)
            fully_transparent = alpha_counter.get(0, 0)
            partial_transparent = total_pixels - fully_opaque - fully_transparent
            
            # Determine alpha usage pattern
            if fully_transparent == 0 and partial_transparent == 0:
                alpha_usage = 'opaque'
            elif fully_transparent > 0 and partial_transparent == 0:
                alpha_usage = 'binary'  # Only fully opaque or transparent
            else:
                alpha_usage = 'gradient'  # Has partial transparency
            
            return {
                'has_alpha': True,
                'is_transparent': fully_transparent > 0,
                'alpha_usage': alpha_usage,
                'statistics': {
                    'unique_values': unique_alpha,
                    'mean': round(np.mean(alpha_data), 2),
                    'std': round(np.std(alpha_data), 2),
                    'min': min(alpha_data),
                    'max': max(alpha_data)
                },
                'distribution': {
                    'fully_opaque': fully_opaque,
                    'fully_opaque_percent': round((fully_opaque / total_pixels) * 100, 2),
                    'fully_transparent': fully_transparent,
                    'fully_transparent_percent': round((fully_transparent / total_pixels) * 100, 2),
                    'partial_transparent': partial_transparent,
                    'partial_transparent_percent': round((partial_transparent / total_pixels) * 100, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Alpha analysis failed: {e}")
            return {'error': str(e)}
    
    def _analyze_quality(self, img: Image.Image) -> Dict[str, Any]:
        """
        Analyze compression quality and artifacts.
        
        Returns quality metrics and artifact detection.
        """
        try:
            # Convert to numpy array for analysis
            img_array = np.array(img.convert('RGB'))
            
            # Calculate sharpness using Laplacian variance
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = laplacian.var()
            
            # Detect compression artifacts using frequency analysis
            dct = cv2.dct(np.float32(gray))
            high_freq_energy = np.sum(np.abs(dct[int(dct.shape[0]/2):, int(dct.shape[1]/2):]))
            total_energy = np.sum(np.abs(dct))
            high_freq_ratio = high_freq_energy / total_energy if total_energy > 0 else 0
            
            # Estimate quality level
            if sharpness > 500:
                quality_estimate = 'high'
            elif sharpness > 100:
                quality_estimate = 'medium'
            else:
                quality_estimate = 'low'
            
            # Detect blocking artifacts (8x8 blocks typical in JPEG)
            block_artifacts = self._detect_blocking_artifacts(gray)
            
            return {
                'sharpness': round(sharpness, 2),
                'quality_estimate': quality_estimate,
                'high_frequency_ratio': round(high_freq_ratio, 4),
                'has_blocking_artifacts': block_artifacts,
                'noise_level': round(self._estimate_noise_level(gray), 2),
                'dynamic_range': int(gray.max()) - int(gray.min())
            }
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            return {'error': str(e)}
    
    def _detect_corruption(self, img: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Detect image corruption or anomalies.
        
        Returns corruption detection results.
        """
        try:
            if img is None:
                return {
                    'is_corrupted': True,
                    'reason': 'Failed to load image'
                }
            
            issues = []
            
            # Check for unusual dimensions
            if img.shape[0] == 0 or img.shape[1] == 0:
                issues.append('Zero dimension detected')
            
            # Check for NaN values
            if np.isnan(img).any():
                issues.append('NaN values detected')
            
            # Check for infinite values
            if np.isinf(img).any():
                issues.append('Infinite values detected')
            
            # Check for unusual data ranges
            if img.dtype == np.uint8:
                if img.min() == img.max():
                    issues.append('Single color image (possibly corrupted)')
            
            # Check for stripe patterns (common corruption)
            if self._detect_stripe_pattern(img):
                issues.append('Stripe pattern detected (possible corruption)')
            
            return {
                'is_corrupted': len(issues) > 0,
                'issues': issues,
                'confidence': 'high' if len(issues) > 2 else 'medium' if len(issues) > 0 else 'none'
            }
            
        except Exception as e:
            logger.error(f"Corruption detection failed: {e}")
            return {
                'is_corrupted': True,
                'reason': f'Analysis error: {str(e)}'
            }
    
    def _calculate_hashes(self, path: Path) -> Dict[str, str]:
        """
        Calculate file hashes for integrity verification.
        
        Returns MD5 and SHA256 hashes.
        """
        try:
            md5_hash = hashlib.md5()
            sha256_hash = hashlib.sha256()
            
            with open(path, 'rb') as f:
                # Read in chunks for memory efficiency
                for chunk in iter(lambda: f.read(8192), b''):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            return {
                'md5': md5_hash.hexdigest(),
                'sha256': sha256_hash.hexdigest()
            }
            
        except Exception as e:
            logger.error(f"Hash calculation failed: {e}")
            return {'error': str(e)}
    
    def _suggest_optimizations(
        self,
        basic: Dict,
        colors: Dict,
        alpha: Dict,
        quality: Dict
    ) -> Dict[str, Any]:
        """
        Generate optimization suggestions based on analysis.
        
        Returns optimization recommendations.
        """
        suggestions = []
        potential_savings = 0
        
        try:
            # Check if power of 2 dimensions are needed
            if not basic['is_power_of_2']:
                suggestions.append({
                    'type': 'dimension',
                    'priority': 'medium',
                    'message': 'Resize to power-of-2 dimensions for optimal PS2 compatibility',
                    'details': f"Current: {basic['width']}x{basic['height']}"
                })
            
            # Check for unnecessary alpha channel
            if alpha.get('has_alpha') and alpha['alpha_usage'] == 'opaque':
                suggestions.append({
                    'type': 'format',
                    'priority': 'high',
                    'message': 'Remove unnecessary alpha channel',
                    'details': 'Alpha channel is fully opaque, can use RGB format',
                    'savings_percent': 25
                })
                potential_savings += basic['file_size_bytes'] * 0.25
            
            # Check for low color diversity (possible palette optimization)
            if colors.get('unique_colors', float('inf')) < 256:
                suggestions.append({
                    'type': 'format',
                    'priority': 'medium',
                    'message': 'Consider palette-based format',
                    'details': f"Only {colors['unique_colors']} unique colors detected",
                    'savings_percent': 50
                })
                potential_savings += basic['file_size_bytes'] * 0.50
            
            # Check if grayscale
            if colors.get('is_grayscale'):
                suggestions.append({
                    'type': 'format',
                    'priority': 'medium',
                    'message': 'Convert to grayscale format',
                    'details': 'Image is grayscale, no need for RGB',
                    'savings_percent': 66
                })
                potential_savings += basic['file_size_bytes'] * 0.66
            
            # Check quality vs size trade-off
            if quality.get('quality_estimate') == 'high' and basic['file_size_kb'] > 1024:
                suggestions.append({
                    'type': 'compression',
                    'priority': 'low',
                    'message': 'Consider moderate compression',
                    'details': 'High quality detected, moderate compression may reduce size significantly',
                    'savings_percent': 30
                })
            
            # Check for oversized textures
            if basic['size_pixels'] > 1024 * 1024:
                suggestions.append({
                    'type': 'dimension',
                    'priority': 'high',
                    'message': 'Texture may be too large for PS2',
                    'details': f"{basic['width']}x{basic['height']} exceeds typical PS2 limits",
                    'recommendation': 'Consider downscaling'
                })
            
            return {
                'suggestions': suggestions,
                'total_suggestions': len(suggestions),
                'potential_savings_bytes': int(potential_savings),
                'potential_savings_kb': round(potential_savings / 1024, 2),
                'recommended_format': self._recommend_format(basic, colors, alpha)
            }
            
        except Exception as e:
            logger.error(f"Optimization suggestion failed: {e}")
            return {'error': str(e)}
    
    def _recommend_format(
        self,
        basic: Dict,
        colors: Dict,
        alpha: Dict
    ) -> str:
        """Recommend optimal texture format based on analysis."""
        # Binary alpha or no alpha -> DDS with DXT1
        if not alpha.get('has_alpha') or alpha.get('alpha_usage') == 'binary':
            return 'DDS (DXT1)'
        
        # Gradient alpha -> DDS with DXT5
        if alpha.get('alpha_usage') == 'gradient':
            return 'DDS (DXT5)'
        
        # Low colors -> PNG with palette
        if colors.get('unique_colors', float('inf')) < 256:
            return 'PNG (Palette)'
        
        # Default
        return 'PNG (RGB)'
    
    @staticmethod
    def _is_power_of_2(n: int) -> bool:
        """Check if number is power of 2."""
        return n > 0 and (n & (n - 1)) == 0
    
    @staticmethod
    def _is_grayscale(pixels: List[Tuple[int, int, int]]) -> bool:
        """Check if image is effectively grayscale."""
        # Sample first 1000 pixels for efficiency
        sample = pixels[:1000]
        for r, g, b in sample:
            if not (r == g == b):
                return False
        return True
    
    @staticmethod
    def _detect_blocking_artifacts(gray: np.ndarray) -> bool:
        """Detect 8x8 blocking artifacts typical in JPEG compression."""
        try:
            # Look for discontinuities at 8-pixel boundaries
            h, w = gray.shape
            block_size = 8
            
            # Check horizontal boundaries
            h_diffs = []
            for i in range(block_size, h, block_size):
                if i < h - 1:
                    diff = np.mean(np.abs(gray[i, :] - gray[i-1, :]))
                    h_diffs.append(diff)
            
            # Check vertical boundaries
            v_diffs = []
            for j in range(block_size, w, block_size):
                if j < w - 1:
                    diff = np.mean(np.abs(gray[:, j] - gray[:, j-1]))
                    v_diffs.append(diff)
            
            # If boundary differences are significantly higher, blocking exists
            if h_diffs and v_diffs:
                avg_h_diff = np.mean(h_diffs)
                avg_v_diff = np.mean(v_diffs)
                overall_diff = np.mean(np.abs(np.diff(gray.flatten())))
                
                return (avg_h_diff > overall_diff * 1.5 or avg_v_diff > overall_diff * 1.5)
            
            return False
            
        except Exception:
            return False
    
    @staticmethod
    def _estimate_noise_level(gray: np.ndarray) -> float:
        """Estimate noise level in image."""
        try:
            # Use high-pass filter to isolate noise
            kernel = np.array([[-1, -1, -1],
                             [-1,  8, -1],
                             [-1, -1, -1]])
            filtered = cv2.filter2D(gray, -1, kernel)
            return np.std(filtered)
        except Exception:
            return 0.0
    
    @staticmethod
    def _detect_stripe_pattern(img: np.ndarray) -> bool:
        """Detect stripe patterns that might indicate corruption."""
        try:
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Check for repetitive patterns in rows
            row_variance = np.var(gray, axis=1)
            if np.std(row_variance) < 1.0:  # Very low variance variation
                return True
            
            # Check for repetitive patterns in columns
            col_variance = np.var(gray, axis=0)
            if np.std(col_variance) < 1.0:
                return True
            
            return False
            
        except Exception:
            return False
    
    @staticmethod
    def _get_error_result(error_msg: str) -> Dict[str, Any]:
        """Return error result structure."""
        return {
            'error': error_msg,
            'basic': {},
            'colors': {},
            'alpha': {},
            'quality': {},
            'corruption': {'is_corrupted': True, 'reason': error_msg},
            'hashes': {},
            'optimization': {}
        }
