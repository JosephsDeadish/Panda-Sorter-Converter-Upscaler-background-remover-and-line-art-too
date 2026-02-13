"""
Texture Classification Engine
Automatically classifies textures into 50+ categories using:
- Filename pattern matching
- Image analysis (color histograms, texture patterns)
- Metadata examination
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

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

from .categories import ALL_CATEGORIES, get_category_info


class TextureClassifier:
    """Main texture classification engine"""
    
    # Classification confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.7  # Threshold for accepting filename-based classification
    
    def __init__(self, config=None, model_manager=None, game_profile=None):
        self.config = config
        self.categories = ALL_CATEGORIES
        self.classification_cache = {}
        self.model_manager = model_manager
        
        # Game-specific texture profile (NEW)
        self.game_profile = game_profile or {}
        self.game_specific_keywords = self._load_game_keywords()
        
        # Get AI preferences from config
        if config:
            self.prefer_image_content = config.get('ai', 'prefer_image_content', default=True)
            self.use_ai = config.get('ai', 'offline', 'enabled', default=True) or \
                         config.get('ai', 'online', 'enabled', default=False)
        else:
            self.prefer_image_content = True
            self.use_ai = True
    
    def _load_game_keywords(self) -> dict:
        """
        Load game-specific keyword mappings from texture profile.
        
        Returns:
            Dictionary mapping keywords to categories
        """
        keywords = {}
        if self.game_profile:
            # Check if profile has explicit prefix-to-category mappings
            prefix_mappings = self.game_profile.get('prefix_mappings', {})
            if prefix_mappings:
                # Use explicit mappings
                for prefix, category in prefix_mappings.items():
                    keywords[prefix.lower()] = category
            else:
                # Fallback: Use common prefixes with intelligent category matching
                common_prefixes = self.game_profile.get('common_prefixes', [])
                common_categories = self.game_profile.get('common_categories', [])
                
                # Try to match prefixes to categories by name similarity
                for prefix in common_prefixes:
                    prefix_lower = prefix.lower()
                    matched_category = None
                    
                    # Try to find a category that matches the prefix
                    for category in common_categories:
                        if category.lower() in prefix_lower or prefix_lower in category.lower():
                            matched_category = category
                            break
                    
                    # Store mapping (may be None if no match found)
                    keywords[prefix_lower] = matched_category
        
        return keywords
    
    def set_game_profile(self, game_profile: dict):
        """
        Update the game-specific texture profile.
        
        Args:
            game_profile: Dictionary with game texture profile settings
        """
        self.game_profile = game_profile
        self.game_specific_keywords = self._load_game_keywords()
        # Clear cache when profile changes
        self.classification_cache.clear()
    
    def classify_texture(self, file_path: Path, use_image_analysis=True) -> Tuple[str, float]:
        """
        Classify a texture file into a category
        
        Args:
            file_path: Path to the texture file
            use_image_analysis: Whether to use image analysis (slower but more accurate)
        
        Returns:
            Tuple of (category_id, confidence_score)
        """
        # Check cache first
        cache_key = str(file_path)
        if cache_key in self.classification_cache:
            return self.classification_cache[cache_key]
        
        category = "unclassified"
        confidence = 0.0
        
        # Try AI model first if available and prefer_image_content is True
        if self.prefer_image_content and self.model_manager and use_image_analysis:
            try:
                from PIL import Image
                if not file_path.exists():
                    import logging
                    logging.debug(f"File not found for AI classification: {file_path}")
                else:
                    with Image.open(file_path) as img:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img_array = np.array(img)
                    
                    # Get predictions from AI model
                    predictions = self.model_manager.predict(img_array, list(self.categories.keys()))
                    if predictions and len(predictions) > 0:
                        category = predictions[0]['category']
                        confidence = predictions[0]['confidence']
            except Exception as e:
                import logging
                logging.debug(f"AI model prediction failed for {file_path}: {e}")
        
        # Try filename-based classification (fast)
        if confidence < self.HIGH_CONFIDENCE_THRESHOLD:  # Use filename if AI confidence is low
            filename_category, filename_confidence = self._classify_by_filename(file_path)
            
            # If prefer_image_content is False, prioritize filename matching
            if not self.prefer_image_content:
                category = filename_category
                confidence = filename_confidence
            # Otherwise, use filename result only if better than AI
            elif filename_confidence > confidence:
                category = filename_category
                confidence = filename_confidence
        
        # If confidence is still low and image analysis is enabled, try image analysis
        if confidence < self.HIGH_CONFIDENCE_THRESHOLD and use_image_analysis and HAS_PIL:
            img_category, img_confidence = self._classify_by_image(file_path)
            if img_confidence > confidence:
                category, confidence = img_category, img_confidence
        
        # Cache the result
        self.classification_cache[cache_key] = (category, confidence)
        
        return category, confidence
    
    def _classify_by_filename(self, file_path: Path) -> Tuple[str, float]:
        """Classify based on filename patterns"""
        filename = file_path.stem.lower()
        best_match = "unclassified"
        best_score = 0.0
        
        # Common video game texture naming conventions to strip before matching
        # These prefixes/suffixes are used in game engines (Unreal, Unity, Source, etc.)
        # Strip common prefixes like tex_, t_, mat_, m_ 
        cleaned = re.sub(r'^(tex_|t_|mat_|m_|uv_|tx_)', '', filename)
        # Strip common suffixes like _diffuse, _diff, _d, _col, _color, _albedo, _base
        cleaned = re.sub(r'(_diffuse|_diff|_d|_col|_color|_albedo|_base|_basecolor|_bc|_tex)$', '', cleaned)
        # Strip resolution suffixes like _512, _1024, _2k, _4k
        cleaned = re.sub(r'(_\d+x\d+|_\d{3,4}|_[124]k)$', '', cleaned)
        # Strip LOD suffixes like _lod0, _lod1
        cleaned = re.sub(r'_lod\d+$', '', cleaned)
        
        # Names to check: both original and cleaned versions
        names_to_check = {filename}
        if cleaned != filename:
            names_to_check.add(cleaned)
        
        # Also try splitting on underscores and numbers to match individual parts
        # This helps with names like "char_head_skin_01" -> matches "head", "skin"
        parts = re.split(r'[_\-\s]+', cleaned)
        
        # NEW: Check game-specific keywords first (higher priority)
        if self.game_specific_keywords:
            for keyword, category in self.game_specific_keywords.items():
                if category:  # Only if mapped to a category
                    for name in names_to_check:
                        if keyword in name:
                            # High confidence for game-specific matches
                            score = 0.9
                            if name.startswith(keyword):
                                score = 1.0
                            if score > best_score:
                                best_score = score
                                best_match = category
                    
                    # Check parts
                    for part in parts:
                        if part and keyword == part:
                            score = 0.95
                            if score > best_score:
                                best_score = score
                                best_match = category
        
        # Check each category's keywords
        for category_id, category_info in self.categories.items():
            keywords = category_info.get("keywords", [])
            for keyword in keywords:
                kw_lower = keyword.lower()
                
                for name in names_to_check:
                    if kw_lower in name:
                        # Score based on keyword match length and position
                        score = len(keyword) / max(len(name), 1)
                        # Bonus for exact matches or start of filename
                        if name.startswith(kw_lower):
                            score += 0.2
                        if name == kw_lower:
                            score = 1.0
                        
                        if score > best_score:
                            best_score = score
                            best_match = category_id
                
                # Also check individual parts for matches
                for part in parts:
                    if part and kw_lower == part:
                        # Exact part match is a strong signal
                        score = 0.8
                        if score > best_score:
                            best_score = score
                            best_match = category_id
                    elif part and kw_lower in part and len(kw_lower) >= 3:
                        score = len(keyword) / max(len(part), 1) * 0.7
                        if score > best_score:
                            best_score = score
                            best_match = category_id
        
        # Normalize score to 0-1 range
        confidence = min(1.0, best_score + 0.3)  # Add base confidence
        
        return best_match, confidence
    
    def _classify_by_image(self, file_path: Path) -> Tuple[str, float]:
        """Classify based on image analysis"""
        if not HAS_PIL:
            return "unclassified", 0.0
        
        try:
            # Load image
            img = Image.open(file_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Analyze image properties
            width, height = img.size
            aspect_ratio = width / height if height > 0 else 1.0
            
            # Get color histogram
            histogram = img.histogram()
            
            # Analyze dominant colors
            img_array = np.array(img)
            avg_color = np.mean(img_array, axis=(0, 1))
            color_std = np.std(img_array, axis=(0, 1))
            
            # Simple heuristic-based classification
            category = "unclassified"
            confidence = 0.5
            
            # Check for UI elements (usually small, simple colors)
            if width <= 256 and height <= 256 and self._is_simple_image(img_array):
                category = "ui_elements"
                confidence = 0.6
            
            # Check for UV unwrapped textures / flattened character textures
            # These often have varied colors, skin tones, and irregular shapes
            # with transparent/black background regions
            elif self._is_uv_unwrap(img, img_array, width, height):
                category = "person"
                confidence = 0.65
            
            # Check for sky (blue dominant)
            elif avg_color[2] > avg_color[0] * 1.3 and avg_color[2] > avg_color[1] * 1.3:
                category = "sky"
                confidence = 0.65
            
            # Check for skin tones (flesh-colored textures)
            elif self._has_skin_tones(avg_color, color_std):
                category = "skin1"
                confidence = 0.6
            
            # Check for grass/plants (green dominant)
            elif avg_color[1] > avg_color[0] * 1.2 and avg_color[1] > avg_color[2] * 1.2:
                category = "grass"
                confidence = 0.65
            
            # Check for dirt/ground (brown tones)
            elif self._is_brown_tone(avg_color):
                category = "dirt"
                confidence = 0.6
            
            # Check for technical textures (patterns, symmetry)
            elif self._has_technical_pattern(img_array):
                category = "normal_maps"
                confidence = 0.7
            
            # Check for metal/armor textures (gray tones with some variance)
            elif self._is_metallic(avg_color, color_std):
                category = "armor"
                confidence = 0.55
            
            return category, confidence
            
        except Exception as e:
            print(f"Error analyzing image {file_path}: {e}")
            return "unclassified", 0.0
    
    def _is_simple_image(self, img_array: np.ndarray) -> bool:
        """Check if image has simple/flat colors (typical of UI)"""
        # Calculate color variance
        variance = np.var(img_array)
        return variance < 500  # Low variance = simple colors
    
    def _is_brown_tone(self, color: np.ndarray) -> bool:
        """Check if color is brown-ish"""
        r, g, b = color
        # Brown is typically R>G>B with moderate values
        return r > g and g > b and 50 < r < 200
    
    def _has_technical_pattern(self, img_array: np.ndarray) -> bool:
        """Check if image has technical/normal map patterns"""
        # Normal maps typically have purple/blue tones
        avg_color = np.mean(img_array, axis=(0, 1))
        # Check for bluish-purple dominant color
        if avg_color[2] > 100 and avg_color[0] > 80 and avg_color[1] < 100:
            return True
        return False
    
    def _has_skin_tones(self, avg_color: np.ndarray, color_std: np.ndarray) -> bool:
        """Check if image has skin/flesh tones typical of character textures"""
        r, g, b = avg_color
        # Skin tones: R > G > B, warm colors, moderate values
        if r > g > b and r > 100 and g > 60 and b > 40:
            # Check if the difference is moderate (not pure red)
            if (r - b) < 100 and (r - g) < 60:
                return True
        return False
    
    def _is_uv_unwrap(self, img, img_array: np.ndarray, width: int, height: int) -> bool:
        """
        Detect UV unwrapped textures (flattened character/object maps).
        These look like 'origami' - disjointed body parts laid out flat with
        blank/transparent/black regions between them.
        """
        try:
            # UV unwraps are usually square power-of-2 textures
            if width != height:
                return False
            if width not in (64, 128, 256, 512, 1024, 2048, 4096):
                return False
            
            # Check for significant dark/transparent regions (background of UV layout)
            # Downsample for performance
            small = img.resize((64, 64))
            small_arr = np.array(small)
            
            # Count near-black pixels (UV layout background)
            if small_arr.shape[2] >= 3:
                brightness = np.mean(small_arr[:, :, :3], axis=2)
                dark_ratio = np.sum(brightness < 20) / brightness.size
                # UV unwraps typically have 15-70% dark background
                if 0.15 < dark_ratio < 0.70:
                    # Also check that non-dark regions have varied colors
                    bright_pixels = small_arr[brightness >= 20]
                    if len(bright_pixels) > 10:
                        color_variance = np.var(bright_pixels[:, :3])
                        if color_variance > 300:
                            return True
        except Exception:
            pass
        return False
    
    def _is_metallic(self, avg_color: np.ndarray, color_std: np.ndarray) -> bool:
        """Check if image has metallic/gray tones typical of armor/metal textures"""
        r, g, b = avg_color
        # Metallic: all channels similar (grayish), moderate values
        if abs(r - g) < 20 and abs(g - b) < 20 and abs(r - b) < 20:
            if 80 < r < 200:  # Not too dark, not too bright
                return True
        return False
    
    def batch_classify(self, file_paths: List[Path], use_image_analysis=True, 
                      progress_callback=None) -> dict:
        """
        Classify multiple textures
        
        Args:
            file_paths: List of file paths to classify
            use_image_analysis: Whether to use image analysis
            progress_callback: Callback function for progress updates
        
        Returns:
            Dictionary mapping file paths to (category, confidence) tuples
        """
        results = {}
        total = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            category, confidence = self.classify_texture(file_path, use_image_analysis)
            results[str(file_path)] = (category, confidence)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return results
    
    def clear_cache(self):
        """Clear the classification cache"""
        self.classification_cache.clear()
