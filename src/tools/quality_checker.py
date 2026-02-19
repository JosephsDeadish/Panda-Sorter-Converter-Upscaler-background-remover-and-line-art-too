"""
Image Quality Checker Tool
Analyzes images for resolution, compression artifacts, DPI, and quality scoring
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from PIL import Image, ImageStat
import threading
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("opencv-python not available - advanced artifact detection disabled")


class QualityLevel(Enum):
    """Quality level classifications."""
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    UNACCEPTABLE = "Unacceptable"


@dataclass
class QualityCheckOptions:
    """Options for configuring quality checks."""
    check_resolution: bool = True
    check_compression: bool = True
    check_dpi: bool = True
    check_sharpness: bool = True
    check_noise: bool = True
    target_dpi: float = 72.0  # Default target DPI for calculations


@dataclass
class QualityReport:
    """Comprehensive quality analysis report for an image."""
    input_path: str
    width: int
    height: int
    total_pixels: int
    format: str
    mode: str
    
    # Resolution metrics
    is_low_resolution: bool
    resolution_score: float
    min_dimension: int
    max_dimension: int
    aspect_ratio: float
    
    # Compression metrics
    has_compression_artifacts: bool
    jpeg_quality_estimate: Optional[int]
    compression_score: float
    blocking_score: float
    
    # DPI metrics
    dpi: Tuple[float, float]
    effective_dpi: float
    dpi_warning: Optional[str]
    
    # Upscaling metrics
    upscale_safe_limit: Tuple[int, int]
    can_upscale_2x: bool
    can_upscale_4x: bool
    upscale_warning: Optional[str]
    
    # Overall quality
    overall_score: float
    quality_level: QualityLevel
    recommendations: List[str]
    warnings: List[str]
    
    # Additional metrics
    sharpness_score: float
    noise_level: float
    has_alpha: bool
    color_depth: int


class ImageQualityChecker:
    """
    Comprehensive image quality checker that analyzes resolution, compression,
    DPI, and provides quality scores and recommendations.
    """
    
    # Resolution thresholds
    LOW_RES_THRESHOLD = 512
    GOOD_RES_THRESHOLD = 1024
    HIGH_RES_THRESHOLD = 2048
    
    # Quality thresholds
    MIN_ACCEPTABLE_QUALITY = 70
    GOOD_QUALITY_THRESHOLD = 85
    EXCELLENT_QUALITY_THRESHOLD = 95
    
    # DPI standards
    SCREEN_DPI = 72
    PRINT_DPI = 300
    HIGH_QUALITY_DPI = 600
    
    def __init__(self):
        """Initialize the quality checker."""
        self.has_cv2 = HAS_CV2
    
    def check_quality(self, image_path: str, options: Optional[QualityCheckOptions] = None) -> QualityReport:
        """
        Perform comprehensive quality check on an image.
        
        Args:
            image_path: Path to the image file
            options: Optional configuration for which checks to perform
            
        Returns:
            QualityReport with comprehensive analysis
        """
        # Use default options if none provided
        if options is None:
            options = QualityCheckOptions()
        
        try:
            img = Image.open(image_path)
            width, height = img.size
            
            # Basic metrics (always collected)
            total_pixels = width * height
            format_type = img.format or "Unknown"
            mode = img.mode
            has_alpha = mode in ('RGBA', 'LA', 'PA')
            color_depth = len(mode) * 8
            
            # Calculate these once regardless of conditional checks
            min_dim = min(width, height)
            max_dim = max(width, height)
            aspect_ratio = width / height if height > 0 else 1.0
            
            # Resolution analysis (conditional)
            if options.check_resolution:
                is_low_res = min_dim < self.LOW_RES_THRESHOLD
                resolution_score = self._calculate_resolution_score(min_dim, max_dim)
            else:
                # Use defaults when skipped
                is_low_res = False
                resolution_score = 100.0
            
            # Compression analysis (conditional)
            if options.check_compression:
                has_artifacts, jpeg_quality, compression_score, blocking_score = \
                    self._analyze_compression(img, image_path)
            else:
                has_artifacts = False
                jpeg_quality = None
                compression_score = 100.0
                blocking_score = 0.0
            
            # DPI analysis (conditional)
            if options.check_dpi:
                dpi, effective_dpi, dpi_warning = self._analyze_dpi(img, width, height, options.target_dpi)
            else:
                dpi = (72.0, 72.0)
                effective_dpi = 72.0
                dpi_warning = None
            
            # Upscaling analysis
            upscale_limit, can_2x, can_4x, upscale_warning = \
                self._analyze_upscale_potential(width, height, resolution_score, compression_score)
            
            # Sharpness and noise (conditional)
            if options.check_sharpness:
                sharpness = self._calculate_sharpness(img)
            else:
                sharpness = 50.0
                
            if options.check_noise:
                noise = self._calculate_noise_level(img)
            else:
                noise = 0.0
            
            # Overall quality score (weighted average)
            overall_score = self._calculate_overall_score(
                resolution_score, compression_score, sharpness, noise
            )
            
            # Quality level classification
            quality_level = self._classify_quality(overall_score)
            
            # Generate recommendations and warnings
            recommendations, warnings = self._generate_recommendations(
                is_low_res, has_artifacts, jpeg_quality, effective_dpi,
                sharpness, noise, overall_score
            )
            
            return QualityReport(
                input_path=image_path,
                width=width,
                height=height,
                total_pixels=total_pixels,
                format=format_type,
                mode=mode,
                is_low_resolution=is_low_res,
                resolution_score=resolution_score,
                min_dimension=min_dim,
                max_dimension=max_dim,
                aspect_ratio=aspect_ratio,
                has_compression_artifacts=has_artifacts,
                jpeg_quality_estimate=jpeg_quality,
                compression_score=compression_score,
                blocking_score=blocking_score,
                dpi=dpi,
                effective_dpi=effective_dpi,
                dpi_warning=dpi_warning,
                upscale_safe_limit=upscale_limit,
                can_upscale_2x=can_2x,
                can_upscale_4x=can_4x,
                upscale_warning=upscale_warning,
                overall_score=overall_score,
                quality_level=quality_level,
                recommendations=recommendations,
                warnings=warnings,
                sharpness_score=sharpness,
                noise_level=noise,
                has_alpha=has_alpha,
                color_depth=color_depth
            )
            
        except Exception as e:
            logger.error(f"Error checking quality for {image_path}: {e}")
            raise
    
    def check_batch(self, image_paths: List[str], 
                   progress_callback: Optional[callable] = None) -> List[QualityReport]:
        """
        Check quality for multiple images.
        
        Args:
            image_paths: List of image file paths
            progress_callback: Optional callback function(current, total, filename)
            
        Returns:
            List of QualityReport objects
        """
        reports = []
        total = len(image_paths)
        
        for i, path in enumerate(image_paths):
            try:
                report = self.check_quality(path)
                reports.append(report)
                
                if progress_callback:
                    progress_callback(i + 1, total, Path(path).name)
                    
            except Exception as e:
                logger.error(f"Error checking {path}: {e}")
                if progress_callback:
                    progress_callback(i + 1, total, Path(path).name)
        
        return reports
    
    def _calculate_resolution_score(self, min_dim: int, max_dim: int) -> float:
        """Calculate resolution quality score (0-100)."""
        # Base score on minimum dimension
        if min_dim >= self.HIGH_RES_THRESHOLD:
            base_score = 100
        elif min_dim >= self.GOOD_RES_THRESHOLD:
            # Linear interpolation between GOOD and HIGH
            ratio = (min_dim - self.GOOD_RES_THRESHOLD) / (self.HIGH_RES_THRESHOLD - self.GOOD_RES_THRESHOLD)
            base_score = 85 + (ratio * 15)
        elif min_dim >= self.LOW_RES_THRESHOLD:
            # Linear interpolation between LOW and GOOD
            ratio = (min_dim - self.LOW_RES_THRESHOLD) / (self.GOOD_RES_THRESHOLD - self.LOW_RES_THRESHOLD)
            base_score = 60 + (ratio * 25)
        else:
            # Below threshold
            ratio = min_dim / self.LOW_RES_THRESHOLD
            base_score = 40 * ratio
        
        return min(100, max(0, base_score))
    
    def _analyze_compression(self, img: Image.Image, 
                           image_path: str) -> Tuple[bool, Optional[int], float, float]:
        """
        Analyze compression artifacts.
        
        Returns:
            (has_artifacts, jpeg_quality, compression_score, blocking_score)
        """
        has_artifacts = False
        jpeg_quality = None
        compression_score = 100.0
        blocking_score = 0.0
        
        # Check if JPEG
        if img.format == 'JPEG':
            # Estimate JPEG quality
            jpeg_quality = self._estimate_jpeg_quality(img, image_path)
            
            if jpeg_quality is not None:
                # Quality below 80 likely has visible artifacts
                if jpeg_quality < 80:
                    has_artifacts = True
                    compression_score = jpeg_quality
                else:
                    compression_score = 90 + (jpeg_quality - 80) / 2
        
        # Detect blocking artifacts using OpenCV if available
        if self.has_cv2 and img.mode in ('RGB', 'L'):
            blocking_score = self._detect_blocking_artifacts(img)
            if blocking_score > 0.3:
                has_artifacts = True
                compression_score = min(compression_score, 70)
        
        return has_artifacts, jpeg_quality, compression_score, blocking_score
    
    def _estimate_jpeg_quality(self, img: Image.Image, image_path: str) -> Optional[int]:
        """
        Estimate JPEG quality level.
        
        Uses quantization tables if available, otherwise uses heuristics.
        """
        try:
            # Try to get quantization tables (only works for some JPEG files)
            if hasattr(img, 'quantization'):
                qtables = img.quantization
                if qtables:
                    # Calculate average quantization value
                    avg_quant = np.mean([np.mean(list(table.values())) for table in qtables.values()])
                    # Rough estimate: lower quantization = higher quality
                    quality = max(0, min(100, 100 - (avg_quant - 1) * 2))
                    return int(quality)
            
            # Fallback: use file size heuristic
            file_size = Path(image_path).stat().st_size
            pixels = img.width * img.height
            bytes_per_pixel = file_size / pixels if pixels > 0 else 0
            
            # Rough heuristics:
            # < 0.1 bytes/pixel: Very low quality (< 50)
            # 0.1-0.3: Low-medium quality (50-75)
            # 0.3-0.8: Medium-good quality (75-90)
            # > 0.8: High quality (90+)
            
            if bytes_per_pixel < 0.1:
                quality = 30 + int(bytes_per_pixel * 200)
            elif bytes_per_pixel < 0.3:
                quality = 50 + int((bytes_per_pixel - 0.1) * 125)
            elif bytes_per_pixel < 0.8:
                quality = 75 + int((bytes_per_pixel - 0.3) * 30)
            else:
                quality = 90 + min(10, int((bytes_per_pixel - 0.8) * 10))
            
            return max(0, min(100, quality))
            
        except Exception as e:
            logger.debug(f"Could not estimate JPEG quality: {e}")
            return None
    
    def _detect_blocking_artifacts(self, img: Image.Image) -> float:
        """
        Detect JPEG blocking artifacts using gradient analysis.
        
        Returns blocking score (0.0 = no blocking, 1.0 = severe blocking)
        """
        try:
            # Convert to numpy array
            if img.mode == 'RGB':
                arr = np.array(img.convert('L'))
            else:
                arr = np.array(img)
            
            # Calculate gradients
            grad_x = cv2.Sobel(arr, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(arr, cv2.CV_64F, 0, 1, ksize=3)
            
            # Detect 8x8 block boundaries (JPEG block size)
            block_edges_x = np.sum(np.abs(grad_x[:, ::8]))
            block_edges_y = np.sum(np.abs(grad_y[::8, :]))
            
            # Compare to average edge strength
            avg_edge_x = np.sum(np.abs(grad_x)) / arr.shape[1] if arr.shape[1] > 0 else 0
            avg_edge_y = np.sum(np.abs(grad_y)) / arr.shape[0] if arr.shape[0] > 0 else 0
            
            # Calculate blocking ratio
            block_ratio_x = block_edges_x / (avg_edge_x * arr.shape[0]) if avg_edge_x > 0 else 0
            block_ratio_y = block_edges_y / (avg_edge_y * arr.shape[1]) if avg_edge_y > 0 else 0
            
            blocking_score = (block_ratio_x + block_ratio_y) / 2
            
            # Normalize to 0-1 range
            return min(1.0, max(0.0, blocking_score))
            
        except Exception as e:
            logger.debug(f"Error detecting blocking artifacts: {e}")
            return 0.0
    
    def _analyze_dpi(self, img: Image.Image, width: int, height: int, 
                    target_dpi: float) -> Tuple[Tuple[float, float], float, Optional[str]]:
        """
        Analyze image DPI.
        
        Returns:
            (dpi_tuple, effective_dpi, warning)
        """
        # Get DPI from image metadata
        dpi = img.info.get('dpi', (self.SCREEN_DPI, self.SCREEN_DPI))
        
        # Calculate effective DPI based on dimensions
        # Assume target physical size of 10 inches
        effective_dpi_x = width / 10
        effective_dpi_y = height / 10
        effective_dpi = (effective_dpi_x + effective_dpi_y) / 2
        
        # Generate warning if DPI is problematic
        warning = None
        if target_dpi == self.PRINT_DPI:
            if effective_dpi < self.PRINT_DPI:
                warning = f"Low DPI for print ({effective_dpi:.0f} < {self.PRINT_DPI})"
        elif effective_dpi < self.SCREEN_DPI:
            warning = f"Very low DPI ({effective_dpi:.0f})"
        
        return dpi, effective_dpi, warning
    
    def _analyze_upscale_potential(self, width: int, height: int,
                                  resolution_score: float, 
                                  compression_score: float) -> Tuple[Tuple[int, int], bool, bool, Optional[str]]:
        """
        Analyze upscaling potential.
        
        Returns:
            (safe_limit, can_2x, can_4x, warning)
        """
        # Calculate safe upscale factor based on quality
        quality_factor = (resolution_score + compression_score) / 200
        
        # Safe upscaling limits
        if quality_factor > 0.9:
            safe_factor = 4
        elif quality_factor > 0.7:
            safe_factor = 2
        else:
            safe_factor = 1
        
        safe_limit = (width * safe_factor, height * safe_factor)
        can_2x = safe_factor >= 2
        can_4x = safe_factor >= 4
        
        # Generate warning
        warning = None
        if safe_factor == 1:
            warning = "Image quality too low for safe upscaling"
        elif safe_factor == 2:
            warning = "Can upscale 2x, but 4x may show artifacts"
        
        return safe_limit, can_2x, can_4x, warning
    
    def _calculate_sharpness(self, img: Image.Image) -> float:
        """
        Calculate image sharpness score (0-100).
        
        Uses Laplacian variance method.
        """
        try:
            # Convert to grayscale
            if img.mode != 'L':
                gray = img.convert('L')
            else:
                gray = img
            
            # Resize if too large for performance
            if gray.width * gray.height > 1024 * 1024:
                gray = gray.resize((1024, 1024), Image.Resampling.LANCZOS)
            
            arr = np.array(gray)
            
            if self.has_cv2:
                # Use Laplacian variance method
                laplacian = cv2.Laplacian(arr, cv2.CV_64F)
                variance = laplacian.var()
                
                # Normalize to 0-100 scale
                # Typical variance ranges: 0-1000+
                sharpness = min(100, (variance / 10))
            else:
                # Fallback: simple edge detection
                edges_x = np.abs(np.diff(arr.astype(float), axis=1))
                edges_y = np.abs(np.diff(arr.astype(float), axis=0))
                edge_strength = (edges_x.mean() + edges_y.mean()) / 2
                sharpness = min(100, edge_strength * 2)
            
            return float(sharpness)
            
        except Exception as e:
            logger.debug(f"Error calculating sharpness: {e}")
            return 50.0
    
    def _calculate_noise_level(self, img: Image.Image) -> float:
        """
        Calculate noise level (0-100, higher = more noise).
        """
        try:
            # Convert to grayscale
            if img.mode != 'L':
                gray = img.convert('L')
            else:
                gray = img
            
            # Resize if too large
            if gray.width * gray.height > 1024 * 1024:
                gray = gray.resize((1024, 1024), Image.Resampling.LANCZOS)
            
            arr = np.array(gray)
            
            if self.has_cv2:
                # Use Laplacian of Gaussian for noise estimation
                blurred = cv2.GaussianBlur(arr, (5, 5), 0)
                noise = np.abs(arr.astype(float) - blurred.astype(float))
                noise_level = noise.mean()
                
                # Normalize to 0-100 scale
                return min(100, noise_level * 2)
            else:
                # Fallback: standard deviation in small regions
                std = arr.std()
                noise_level = min(100, std / 2.55)
                return float(noise_level)
                
        except Exception as e:
            logger.debug(f"Error calculating noise level: {e}")
            return 0.0
    
    def _calculate_overall_score(self, resolution_score: float, 
                                compression_score: float,
                                sharpness: float, noise: float) -> float:
        """
        Calculate weighted overall quality score.
        
        Weights:
        - Resolution: 35%
        - Compression: 30%
        - Sharpness: 25%
        - Noise: 10% (inverted)
        """
        noise_score = 100 - noise
        
        overall = (
            resolution_score * 0.35 +
            compression_score * 0.30 +
            sharpness * 0.25 +
            noise_score * 0.10
        )
        
        return min(100, max(0, overall))
    
    def _classify_quality(self, overall_score: float) -> QualityLevel:
        """Classify quality level based on overall score."""
        if overall_score >= self.EXCELLENT_QUALITY_THRESHOLD:
            return QualityLevel.EXCELLENT
        elif overall_score >= self.GOOD_QUALITY_THRESHOLD:
            return QualityLevel.GOOD
        elif overall_score >= self.MIN_ACCEPTABLE_QUALITY:
            return QualityLevel.FAIR
        elif overall_score >= 50:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE
    
    def _generate_recommendations(self, is_low_res: bool, has_artifacts: bool,
                                 jpeg_quality: Optional[int], effective_dpi: float,
                                 sharpness: float, noise: float,
                                 overall_score: float) -> Tuple[List[str], List[str]]:
        """Generate recommendations and warnings based on analysis."""
        recommendations = []
        warnings = []
        
        # Resolution recommendations
        if is_low_res:
            recommendations.append("Consider using higher resolution source images")
            warnings.append("Low resolution detected - may not be suitable for upscaling")
        
        # Compression recommendations
        if has_artifacts:
            recommendations.append("Re-save from original source to avoid compression artifacts")
            warnings.append("Compression artifacts detected")
            
            if jpeg_quality and jpeg_quality < 80:
                warnings.append(f"Low JPEG quality detected (~{jpeg_quality})")
                recommendations.append("Use PNG format for better quality preservation")
        
        # DPI recommendations
        if effective_dpi < self.SCREEN_DPI:
            warnings.append(f"Very low DPI ({effective_dpi:.0f})")
        elif effective_dpi < self.PRINT_DPI:
            recommendations.append("Not suitable for print without upscaling")
        
        # Sharpness recommendations
        if sharpness < 30:
            warnings.append("Image appears blurry or out of focus")
            recommendations.append("Use sharpen filter or find sharper source")
        
        # Noise recommendations
        if noise > 30:
            warnings.append("High noise level detected")
            recommendations.append("Consider using noise reduction filter")
        
        # Overall quality
        if overall_score < self.MIN_ACCEPTABLE_QUALITY:
            warnings.append("Overall quality below acceptable threshold")
            recommendations.append("Recommend finding better quality source image")
        
        return recommendations, warnings
    
    def generate_summary_report(self, reports: List[QualityReport]) -> Dict[str, Any]:
        """
        Generate summary statistics for multiple quality reports.
        
        Args:
            reports: List of QualityReport objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not reports:
            return {}
        
        total = len(reports)
        
        # Count quality levels
        quality_counts = {level: 0 for level in QualityLevel}
        for report in reports:
            quality_counts[report.quality_level] += 1
        
        # Calculate averages
        avg_score = sum(r.overall_score for r in reports) / total
        avg_resolution = sum(r.min_dimension for r in reports) / total
        avg_sharpness = sum(r.sharpness_score for r in reports) / total
        avg_noise = sum(r.noise_level for r in reports) / total
        
        # Count issues
        low_res_count = sum(1 for r in reports if r.is_low_resolution)
        artifacts_count = sum(1 for r in reports if r.has_compression_artifacts)
        
        return {
            'total_images': total,
            'average_score': avg_score,
            'average_resolution': avg_resolution,
            'average_sharpness': avg_sharpness,
            'average_noise': avg_noise,
            'quality_distribution': {level.value: count for level, count in quality_counts.items()},
            'low_resolution_count': low_res_count,
            'compression_artifacts_count': artifacts_count,
            'low_resolution_percentage': (low_res_count / total) * 100,
            'compression_artifacts_percentage': (artifacts_count / total) * 100,
        }


def format_quality_report(report: QualityReport, detailed: bool = True) -> str:
    """
    Format a quality report as human-readable text.
    
    Args:
        report: QualityReport object
        detailed: Include detailed metrics
        
    Returns:
        Formatted report string
    """
    lines = []
    lines.append(f"Quality Report: {Path(report.input_path).name}")
    lines.append("=" * 60)
    
    # Overall quality
    lines.append(f"\nOverall Quality: {report.quality_level.value} ({report.overall_score:.1f}/100)")
    
    # Basic info
    lines.append(f"\nDimensions: {report.width}x{report.height} ({report.total_pixels:,} pixels)")
    lines.append(f"Format: {report.format} | Mode: {report.mode}")
    
    if detailed:
        # Resolution details
        lines.append(f"\n📏 Resolution Analysis:")
        lines.append(f"  Score: {report.resolution_score:.1f}/100")
        lines.append(f"  Min dimension: {report.min_dimension}px")
        if report.is_low_resolution:
            lines.append(f"  ⚠️  Low resolution detected")
        
        # Compression details
        lines.append(f"\n🗜️  Compression Analysis:")
        lines.append(f"  Score: {report.compression_score:.1f}/100")
        if report.jpeg_quality_estimate:
            lines.append(f"  JPEG quality: ~{report.jpeg_quality_estimate}")
        if report.has_compression_artifacts:
            lines.append(f"  ⚠️  Compression artifacts detected")
        
        # DPI details
        lines.append(f"\n📐 DPI Analysis:")
        lines.append(f"  Effective DPI: {report.effective_dpi:.0f}")
        if report.dpi_warning:
            lines.append(f"  ⚠️  {report.dpi_warning}")
        
        # Upscaling potential
        lines.append(f"\n🔍 Upscaling Potential:")
        lines.append(f"  Can upscale 2x: {'✓' if report.can_upscale_2x else '✗'}")
        lines.append(f"  Can upscale 4x: {'✓' if report.can_upscale_4x else '✗'}")
        lines.append(f"  Safe limit: {report.upscale_safe_limit[0]}x{report.upscale_safe_limit[1]}")
        
        # Additional metrics
        lines.append(f"\n📊 Additional Metrics:")
        lines.append(f"  Sharpness: {report.sharpness_score:.1f}/100")
        lines.append(f"  Noise level: {report.noise_level:.1f}/100")
    
    # Warnings
    if report.warnings:
        lines.append(f"\n⚠️  Warnings:")
        for warning in report.warnings:
            lines.append(f"  • {warning}")
    
    # Recommendations
    if report.recommendations:
        lines.append(f"\n💡 Recommendations:")
        for rec in report.recommendations:
            lines.append(f"  • {rec}")
    
    return "\n".join(lines)
