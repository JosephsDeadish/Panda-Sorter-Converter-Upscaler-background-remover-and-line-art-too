"""Universal AI Model Manager - Downloads models on first use"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Callable
from enum import Enum
import urllib.request
import shutil

logger = logging.getLogger(__name__)

class ModelStatus(Enum):
    INSTALLED = "installed"
    DOWNLOADING = "downloading"
    MISSING = "missing"
    ERROR = "error"

class AIModelManager:
    """Manages downloading and caching AI models"""
    
    # Model definitions
    MODELS = {
        # ===== REALESRGAN MODELS (v0.2.4.0 - VERIFIED WORKING) =====
        'RealESRGAN_x4plus': {
            'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.4.0/RealESRGAN_x4plus.pth',
            'mirror': 'https://huggingface.co/Ryzr/RealESRGAN-x4plus/resolve/main/RealESRGAN_x4plus.pth',
            'size_mb': 67,
            'version': '0.2.4.0',
            'description': 'Real-ESRGAN 4x upscaler - Best quality for 4x upscaling',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
            'icon': '📈',
        },
        'RealESRGAN_x4plus_anime_6B': {
            'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.4.0/RealESRGAN_x4plus_anime_6B.pth',
            'mirror': 'https://huggingface.co/Ryzr/RealESRGAN-anime-x4/resolve/main/RealESRGAN_x4plus_anime_6B.pth',
            'size_mb': 19,
            'version': '0.2.4.0',
            'description': 'Real-ESRGAN 4x anime upscaler - Optimized for anime/manga art',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
            'icon': '📈',
        },
        'RealESRGAN_x2plus': {
            'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.4.0/RealESRGAN_x2plus.pth',
            'mirror': 'https://huggingface.co/Ryzr/RealESRGAN-x2plus/resolve/main/RealESRGAN_x2plus.pth',
            'size_mb': 66,
            'version': '0.2.4.0',
            'description': 'Real-ESRGAN 2x upscaler - Fast 2x upscaling',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
            'icon': '📈',
        },
        
        # ===== CLIP MODELS (AUTO-DOWNLOAD VIA TRANSFORMERS) =====
        'CLIP_ViT-B/32': {
            'hf_model_id': 'openai/clip-vit-base-patch32',
            'auto_download': True,
            'size_mb': 340,
            'version': 'ViT-B/32',
            'description': 'CLIP Vision-Language Model (ViT-B/32) - Image-text similarity for organizing',
            'tool': 'organizer',
            'category': 'vision',
            'required_packages': ['transformers', 'clip-by-openai', 'pillow'],
            'icon': '🧠',
        },
        'CLIP_ViT-L/14': {
            'hf_model_id': 'openai/clip-vit-large-patch14',
            'auto_download': True,
            'size_mb': 427,
            'version': 'ViT-L/14',
            'description': 'CLIP Vision-Language Model (ViT-L/14) - Larger, slower, more accurate',
            'tool': 'organizer',
            'category': 'vision',
            'required_packages': ['transformers', 'clip-by-openai', 'pillow'],
            'icon': '🧠',
        },
        
        # ===== DINOV2 MODELS (AUTO-DOWNLOAD VIA TRANSFORMERS) =====
        'DINOv2_base': {
            'hf_model_id': 'facebook/dinov2-base',
            'auto_download': True,
            'size_mb': 340,
            'version': 'base',
            'description': 'DINOv2 Base Model - Visual similarity detection (balanced)',
            'tool': 'organizer',
            'category': 'vision',
            'required_packages': ['transformers', 'dinov2'],
            'icon': '👁️',
        },
        'DINOv2_small': {
            'hf_model_id': 'facebook/dinov2-small',
            'auto_download': True,
            'size_mb': 81,
            'version': 'small',
            'description': 'DINOv2 Small Model - Fast visual similarity (lightweight)',
            'tool': 'organizer',
            'category': 'vision',
            'required_packages': ['transformers', 'dinov2'],
            'icon': '👁️',
        },
        'DINOv2_large': {
            'hf_model_id': 'facebook/dinov2-large',
            'auto_download': True,
            'size_mb': 1100,
            'version': 'large',
            'description': 'DINOv2 Large Model - Best accuracy visual similarity (slower)',
            'tool': 'organizer',
            'category': 'vision',
            'required_packages': ['transformers', 'dinov2'],
            'icon': '👁️',
        },
        
        # ===== NLP MODELS =====
        'transformers': {
            'auto_download': True,
            'size_mb': 0,
            'version': 'latest',
            'description': 'Hugging Face Transformers - NLP and vision model library',
            'tool': 'organizer',
            'category': 'nlp',
            'required_packages': ['transformers'],
            'icon': '🔤',
        },
        
        # ===== VISION LIBRARIES =====
        'timm': {
            'auto_download': True,
            'size_mb': 0,
            'version': 'latest',
            'description': 'PyTorch Image Models - Vision model library',
            'tool': 'organizer',
            'category': 'vision',
            'required_packages': ['timm'],
            'icon': '🖼️',
        },
        
        'Lanczos_Native': {
            'native_module': True,
            'size_mb': 0,
            'version': 'native',
            'description': 'Native Rust Lanczos acceleration - Fast high-quality resampling',
            'tool': 'preprocessing',
            'category': 'acceleration',
            'required_packages': ['native_ops'],
            'icon': '⚡',
        },
    }
    
    def __init__(self):
        self.models_dir = Path.cwd() / 'models'
        self.models_dir.mkdir(exist_ok=True)
        self.status_file = self.models_dir / '.status.json'
        self.load_status()
    
    def load_status(self):
        """Load model status from cache"""
        if self.status_file.exists():
            try:
                with open(self.status_file) as f:
                    self.status = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load model status: {e}")
                self.status = {}
        else:
            self.status = {}
    
    def save_status(self):
        """Save model status to cache"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save model status: {e}")
    
    def get_model_status(self, model_name: str) -> ModelStatus:
        """Check if model is installed"""
        if model_name not in self.MODELS:
            return ModelStatus.ERROR
        
        model_info = self.MODELS[model_name]
        
        # Check if it's an auto-download model (CLIP, DINOv2)
        if model_info.get('auto_download'):
            # These are installed via pip, not file-based
            try:
                for pkg in model_info.get('required_packages', []):
                    __import__(pkg.replace('-', '_'))
                return ModelStatus.INSTALLED
            except ImportError as e:
                logger.debug(f"Package {pkg} not installed for {model_name}: {e}")
                return ModelStatus.MISSING
        
        # Check if model file exists
        model_file = self.models_dir / f"{model_name}.pth"
        if model_file.exists():
            return ModelStatus.INSTALLED
        
        return ModelStatus.MISSING
    
    def download_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Download model with automatic retry and mirror fallback
        
        Args:
            model_name: Name of model to download
            progress_callback: Function called with (downloaded, total) bytes
        
        Returns:
            True if successful, False otherwise
        """
        if model_name not in self.MODELS:
            logger.error(f"Unknown model: {model_name}")
            return False
        
        model_info = self.MODELS[model_name]
        
        # Skip auto-download models (CLIP, DINOv2 installed via pip)
        if model_info.get('auto_download') or model_info.get('hf_model_id'):
            logger.info(f"Model {model_name} auto-downloads via pip/transformers")
            return False
        
        # Try primary URL first
        url = model_info['url']
        model_file = self.models_dir / f"{model_name}.pth"
        
        try:
            logger.info(f"Downloading {model_name} from {url}")
            self._download_file(url, model_file, progress_callback)
            self.status[model_name] = 'installed'
            self.save_status()
            logger.info(f"✅ Successfully downloaded {model_name}")
            return True
        except Exception as e:
            logger.warning(f"Primary URL failed: {e}. Trying mirror...")
            
            # Try mirror if available
            mirror_url = model_info.get('mirror')
            if mirror_url:
                try:
                    logger.info(f"Downloading from mirror: {mirror_url}")
                    self._download_file(mirror_url, model_file, progress_callback)
                    self.status[model_name] = 'installed'
                    self.save_status()
                    logger.info(f"✅ Successfully downloaded {model_name} (from mirror)")
                    return True
                except Exception as e2:
                    logger.error(f"Mirror also failed: {e2}")
            
            # Log detailed error info
            logger.error(f"Failed to download {model_name}")
            logger.error(f"Primary URL: {url}")
            if 'mirror' in model_info:
                logger.error(f"Mirror URL: {model_info['mirror']}")
            
            # Clean up partial download
            if model_file.exists():
                model_file.unlink()
            return False
    
    def _download_file(self, url: str, dest: Path, progress_callback: Optional[Callable]):
        """Helper to download a file with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                def download_progress(block_num, block_size, total_size):
                    if progress_callback:
                        downloaded = block_num * block_size
                        progress_callback(downloaded, total_size)
                
                urllib.request.urlretrieve(url, dest, reporthook=download_progress)
                return  # Success
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    import time
                    time.sleep(1)  # Wait before retry
                else:
                    raise
    
    def delete_model(self, model_name: str) -> bool:
        """Delete model file to free space"""
        model_file = self.models_dir / f"{model_name}.pth"
        try:
            if model_file.exists():
                model_file.unlink()
            self.status.pop(model_name, None)
            self.save_status()
            logger.info(f"Deleted model {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {model_name}: {e}")
            return False
    
    def get_models_info(self) -> dict:
        """Get info about all models"""
        return {
            name: {
                **info,
                'status': self.get_model_status(name).value,
                'installed': self.get_model_status(name) == ModelStatus.INSTALLED,
            }
            for name, info in self.MODELS.items()
        }
