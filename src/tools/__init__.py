"""
Tools package for Game Texture Sorter.
Image processing tools: background removal, normalization, renaming, color correction,
image repair, line-art conversion, object removal, and quality checking.
Author: Dead On The Inside / JosephsDeadish
"""

from .background_remover import BackgroundRemover, BackgroundRemovalResult, AlphaPreset, AlphaPresets
from .batch_normalizer import (BatchFormatNormalizer, NormalizationSettings, NormalizationResult,
                                PaddingMode, ResizeMode, OutputFormat, NamingPattern)
from .batch_renamer import BatchRenamer, RenamePattern
from .color_corrector import ColorCorrector
from .image_repairer import (ImageRepairer, PNGRepairer, JPEGRepairer, DiagnosticReport,
                              CorruptionType, RepairMode, RepairResult)
from .lineart_converter import (LineArtConverter, LineArtSettings, ConversionResult,
                                ConversionMode, BackgroundMode, MorphologyOperation)
from .object_remover import ObjectRemover
from .quality_checker import ImageQualityChecker, QualityReport, QualityLevel, QualityCheckOptions

__all__ = [
    # Background removal
    'BackgroundRemover', 'BackgroundRemovalResult', 'AlphaPreset', 'AlphaPresets',
    # Batch normalizer
    'BatchFormatNormalizer', 'NormalizationSettings', 'NormalizationResult',
    'PaddingMode', 'ResizeMode', 'OutputFormat', 'NamingPattern',
    # Batch renamer
    'BatchRenamer', 'RenamePattern',
    # Color corrector
    'ColorCorrector',
    # Image repairer
    'ImageRepairer', 'PNGRepairer', 'JPEGRepairer', 'DiagnosticReport',
    'CorruptionType', 'RepairMode', 'RepairResult',
    # Line-art converter
    'LineArtConverter', 'LineArtSettings', 'ConversionResult',
    'ConversionMode', 'BackgroundMode', 'MorphologyOperation',
    # Object remover
    'ObjectRemover',
    # Quality checker
    'ImageQualityChecker', 'QualityReport', 'QualityLevel', 'QualityCheckOptions',
]
