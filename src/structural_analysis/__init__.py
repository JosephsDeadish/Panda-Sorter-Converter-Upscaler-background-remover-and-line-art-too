"""
Structural Analysis Module
Size detection, aspect ratio, color histograms, OCR
Author: Dead On The Inside / JosephsDeadish
"""

from .texture_analyzer import TextureStructuralAnalyzer
from .ocr_detector import OCRDetector
from .ui_detector import UIDetector

__all__ = [
    'TextureStructuralAnalyzer',
    'OCRDetector',
    'UIDetector'
]
