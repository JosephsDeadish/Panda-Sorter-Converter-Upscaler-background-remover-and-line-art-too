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
        'RealESRGAN_x4plus': {
            'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth',
            'size_mb': 67,
            'description': 'Real-ESRGAN 4x Upscaler',
            'tool': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
        },
        'RealESRGAN_x2plus': {
            'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x2plus.pth',
            'size_mb': 66,
            'description': 'Real-ESRGAN 2x Upscaler',
            'tool': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
        },
        'CLIP': {
            'auto_download': True,  # Will download on first use
            'description': 'CLIP Image-Text Model',
            'tool': 'organizer',
            'required_packages': ['clip-by-openai'],
        },
        'DINOv2': {
            'auto_download': True,
            'description': 'DINOv2 Visual Similarity Model',
            'tool': 'organizer',
            'required_packages': ['dinov2'],
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
        Download model file
        
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
        
        # Skip auto-download models
        if model_info.get('auto_download'):
            logger.info(f"Model {model_name} uses auto-download (pip install)")
            return False
        
        # Download file
        url = model_info['url']
        model_file = self.models_dir / f"{model_name}.pth"
        
        try:
            logger.info(f"Downloading {model_name} from {url}")
            
            def download_progress(block_num, block_size, total_size):
                if progress_callback:
                    downloaded = block_num * block_size
                    progress_callback(downloaded, total_size)
            
            urllib.request.urlretrieve(url, model_file, reporthook=download_progress)
            self.status[model_name] = 'installed'
            self.save_status()
            logger.info(f"Successfully downloaded {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {model_name}: {e}")
            if model_file.exists():
                model_file.unlink()
            return False
    
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
