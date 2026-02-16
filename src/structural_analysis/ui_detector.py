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
        use_ocr: bool = False,
        config=None
    ):
        """
        Initialize UI detector.
        
        Args:
            use_structural_analysis: Use structural analyzer (legacy)
            use_alpha_analysis: Use alpha channel analysis (legacy)
            use_ocr: Use OCR detection (legacy)
            config: Configuration dict with ui_detection settings
        """
        # Load settings from config or use parameters
        if config and hasattr(config, 'get'):
            self.use_structural = config.get('ui_detection', 'use_structural_analysis', default=True)
            self.use_alpha = config.get('ui_detection', 'use_alpha_analysis', default=True)
            self.use_ocr = config.get('ui_detection', 'use_ocr', default=False)
            self.structural_weight = config.get('ui_detection', 'structural_weight', default=0.4)
            self.alpha_weight = config.get('ui_detection', 'alpha_weight', default=0.3)
            self.ocr_weight = config.get('ui_detection', 'ocr_weight', default=0.3)
            self.ui_threshold = config.get('ui_detection', 'ui_threshold', default=0.5)
        else:
            # Use legacy parameters or defaults
            self.use_structural = use_structural_analysis
            self.use_alpha = use_alpha_analysis
            self.use_ocr = use_ocr
            self.structural_weight = 0.4
            self.alpha_weight = 0.3
            self.ocr_weight = 0.3
            self.ui_threshold = 0.5
        
        # Initialize components
        self.structural_analyzer = None
        if self.use_structural:
            from .texture_analyzer import TextureStructuralAnalyzer
            self.structural_analyzer = TextureStructuralAnalyzer(config=config)
        
        self.alpha_handler = None
        if self.use_alpha:
            from preprocessing import AlphaChannelHandler
            self.alpha_handler = AlphaChannelHandler()
        
        self.ocr_detector = None
        if self.use_ocr:
            try:
                from .ocr_detector import OCRDetector
                self.ocr_detector = OCRDetector(config=config)
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
            weights['structural'] = self.structural_weight
        
        # Alpha analysis
        if self.alpha_handler and img.shape[2] == 4:
            alpha = img[:, :, 3]
            alpha_result = self.alpha_handler.detect_ui_transparency(img[:, :, :3], alpha)
            signals['alpha'] = alpha_result['is_ui']
            weights['alpha'] = self.alpha_weight
        
        # OCR detection
        if self.ocr_detector:
            ocr_result = self.ocr_detector.detect_text(img)
            signals['ocr'] = ocr_result['has_text']
            weights['ocr'] = self.ocr_weight
        
        # Calculate weighted score
        total_weight = sum(weights.values())
        if total_weight > 0:
            ui_score = sum(
                (1.0 if signals[key] else 0.0) * weights[key]
                for key in signals
            ) / total_weight
        else:
            ui_score = 0.0
        
        is_ui = ui_score > self.ui_threshold
        
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
