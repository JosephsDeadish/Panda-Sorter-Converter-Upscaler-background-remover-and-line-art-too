"""
OCR Detector for UI Text
Detect health numbers, ammo counts, and other text in textures
Author: Dead On The Inside / JosephsDeadish
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    cv2 = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)

# Check for pytesseract availability
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.debug("pytesseract not available. OCR disabled.")


class OCRDetector:
    """
    Detect text in textures using OCR.
    
    Features:
    - Detect health numbers
    - Detect ammo counts
    - Detect UI text
    - Language-agnostic detection
    """
    
    def __init__(self, tesseract_path: Optional[Path] = None, config=None):
        """
        Initialize OCR detector.
        
        Args:
            tesseract_path: Optional path to tesseract executable (legacy parameter)
            config: Configuration dict with ocr settings
        """
        if not PYTESSERACT_AVAILABLE:
            logger.warning("pytesseract not available. OCR features disabled.")
            self.confidence_threshold = 0.3
            self.min_upscale_size = 200
            self.denoise_strength = 10
            return
        
        # Load settings from config or use parameters/defaults
        if config and hasattr(config, 'get'):
            tess_path = config.get('ocr', 'tesseract_path', default='')
            if tess_path:
                pytesseract.pytesseract.tesseract_cmd = str(tess_path)
            self.confidence_threshold = config.get('ocr', 'confidence_threshold', default=0.3)
            self.min_upscale_size = config.get('ocr', 'min_upscale_size', default=200)
            self.denoise_strength = config.get('ocr', 'denoise_strength', default=10)
        else:
            # Use legacy parameter or defaults
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
            self.confidence_threshold = 0.3
            self.min_upscale_size = 200
            self.denoise_strength = 10
        
        logger.info("OCRDetector initialized")
    
    def detect_text(
        self,
        image: Union[np.ndarray, Image.Image, Path],
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Detect text in image.
        
        Args:
            image: Input image
            preprocess: Apply preprocessing for better OCR
            
        Returns:
            Dictionary with detected text and confidence
        """
        if not PYTESSERACT_AVAILABLE:
            return {'text': '', 'confidence': 0.0, 'has_text': False}
        
        # Load image
        if isinstance(image, Path):
            img = cv2.imread(str(image))
        elif isinstance(image, Image.Image):
            img = np.array(image)
        else:
            img = image
        
        # Preprocess for OCR if requested
        if preprocess:
            img = self._preprocess_for_ocr(img)
        
        # Perform OCR
        try:
            text = pytesseract.image_to_string(img).strip()
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(c) for c in data['conf'] if c != '-1']
            avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0
            
            has_text = len(text) > 0 and avg_confidence > self.confidence_threshold
            
            return {
                'text': text,
                'confidence': avg_confidence,
                'has_text': has_text,
                'word_count': len(text.split()),
                'raw_data': data
            }
            
        except Exception as e:
            logger.error(f"OCR detection failed: {e}")
            return {'text': '', 'confidence': 0.0, 'has_text': False, 'error': str(e)}
    
    def detect_numbers(
        self,
        image: Union[np.ndarray, Image.Image, Path]
    ) -> Dict[str, Any]:
        """
        Detect numbers in image (for health, ammo, etc.).
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with detected numbers
        """
        if not PYTESSERACT_AVAILABLE:
            return {'numbers': [], 'has_numbers': False}
        
        # Load image
        if isinstance(image, Path):
            img = cv2.imread(str(image))
        elif isinstance(image, Image.Image):
            img = np.array(image)
        else:
            img = image
        
        # Preprocess
        img = self._preprocess_for_ocr(img)
        
        # OCR with digits-only config
        try:
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(img, config=custom_config).strip()
            
            # Extract numbers
            numbers = [int(n) for n in text.split() if n.isdigit()]
            
            return {
                'numbers': numbers,
                'has_numbers': len(numbers) > 0,
                'text': text
            }
            
        except Exception as e:
            logger.error(f"Number detection failed: {e}")
            return {'numbers': [], 'has_numbers': False, 'error': str(e)}
    
    def is_ui_text(
        self,
        image: Union[np.ndarray, Image.Image, Path],
        min_confidence: float = 0.5
    ) -> bool:
        """
        Determine if texture contains UI text.
        
        Args:
            image: Input image
            min_confidence: Minimum confidence threshold
            
        Returns:
            True if UI text detected
        """
        result = self.detect_text(image)
        return result.get('has_text', False) and result.get('confidence', 0.0) >= min_confidence
    
    def _preprocess_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Steps:
        - Convert to grayscale
        - Apply thresholding
        - Denoise
        - Upscale if small
        """
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Upscale if small
        h, w = gray.shape[:2]
        if max(h, w) < self.min_upscale_size:
            scale_factor = self.min_upscale_size // max(h, w) + 1
            gray = cv2.resize(
                gray,
                (w * scale_factor, h * scale_factor),
                interpolation=cv2.INTER_CUBIC
            )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=self.denoise_strength)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        return thresh
