"""
UI Detector
Combined analysis to detect UI textures
Author: Dead On The Inside / JosephsDeadish
"""

import logging
from pathlib import Path
from typing import Dict, Any, Union, List
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class UIDetector:
    """
    Comprehensive UI texture detection.
    
    Combines multiple signals:
    - Size analysis
    - Aspect ratio
    - Color patterns
    - Alpha channel
    - Edge detection
    - OCR (optional)
    """
    
    def __init__(
        self,
        use_structural_analysis: bool = True,
        use_alpha_analysis: bool = True,
        use_ocr: bool = False
    ):
        """
        Initialize UI detector.
        
        Args:
            use_structural_analysis: Use structural analyzer
            use_alpha_analysis: Use alpha channel analysis
            use_ocr: Use OCR detection
        """
        self.use_structural = use_structural_analysis
        self.use_alpha = use_alpha_analysis
        self.use_ocr = use_ocr
        
        # Initialize components
        self.structural_analyzer = None
        if use_structural_analysis:
            from .texture_analyzer import TextureStructuralAnalyzer
            self.structural_analyzer = TextureStructuralAnalyzer()
        
        self.alpha_handler = None
        if use_alpha_analysis:
            from src.preprocessing import AlphaChannelHandler
            self.alpha_handler = AlphaChannelHandler()
        
        self.ocr_detector = None
        if use_ocr:
            try:
                from .ocr_detector import OCRDetector
                self.ocr_detector = OCRDetector()
            except Exception as e:
                logger.warning(f"Failed to initialize OCR: {e}")
        
        logger.info("UIDetector initialized")
    
    def detect(
        self,
        image: Union[np.ndarray, Image.Image, Path]
    ) -> Dict[str, Any]:
        """
        Detect if texture is a UI element.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with detection results
        """
        # Load image
        if isinstance(image, Path):
            img = np.array(Image.open(image).convert('RGBA'))
        elif isinstance(image, Image.Image):
            img = np.array(image)
        else:
            img = image
        
        signals = {}
        weights = {}
        
        # Structural analysis
        if self.structural_analyzer:
            structural_result = self.structural_analyzer.analyze(img[:, :, :3] if img.shape[2] == 4 else img)
            signals['structural'] = structural_result['is_ui_likely']
            weights['structural'] = 0.4
        
        # Alpha analysis
        if self.alpha_handler and img.shape[2] == 4:
            alpha = img[:, :, 3]
            alpha_result = self.alpha_handler.detect_ui_transparency(img[:, :, :3], alpha)
            signals['alpha'] = alpha_result['is_ui']
            weights['alpha'] = 0.3
        
        # OCR detection
        if self.ocr_detector:
            ocr_result = self.ocr_detector.detect_text(img)
            signals['ocr'] = ocr_result['has_text']
            weights['ocr'] = 0.3
        
        # Calculate weighted score
        total_weight = sum(weights.values())
        if total_weight > 0:
            ui_score = sum(
                (1.0 if signals[key] else 0.0) * weights[key]
                for key in signals
            ) / total_weight
        else:
            ui_score = 0.0
        
        is_ui = ui_score > 0.5
        
        return {
            'is_ui': is_ui,
            'confidence': ui_score,
            'signals': signals,
            'weights': weights
        }
    
    def classify_ui_type(
        self,
        image: Union[np.ndarray, Image.Image, Path]
    ) -> Dict[str, Any]:
        """
        Classify type of UI element.
        
        Types: icon, health_bar, progress_bar, button, text, unknown
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with UI type classification
        """
        # First detect if it's UI
        detection = self.detect(image)
        if not detection['is_ui']:
            return {
                'ui_type': 'not_ui',
                'confidence': 1.0 - detection['confidence']
            }
        
        # Load image for analysis
        if isinstance(image, Path):
            img = np.array(Image.open(image).convert('RGB'))
        elif isinstance(image, Image.Image):
            img = np.array(image)
        else:
            img = image[:, :, :3] if image.shape[2] == 4 else image
        
        # Use structural analysis to determine type
        if self.structural_analyzer:
            structural = self.structural_analyzer.analyze(img)
            aspect_info = structural['aspect_ratio_info']
            size_info = structural['size_info']
            
            # Determine type based on aspect ratio and size
            if aspect_info['ratio_class'] == 'square' and size_info['size_class'] == 'small':
                ui_type = 'icon'
                confidence = 0.8
            elif aspect_info['ratio_class'] == 'wide':
                ui_type = aspect_info['ui_element_type']  # health_bar or progress_bar
                confidence = 0.7
            elif self.ocr_detector and self.ocr_detector.detect_text(img)['has_text']:
                ui_type = 'text_label'
                confidence = 0.75
            else:
                ui_type = 'ui_element'
                confidence = 0.6
        else:
            ui_type = 'ui_element'
            confidence = detection['confidence']
        
        return {
            'ui_type': ui_type,
            'confidence': confidence
        }
