"""Universal AI Model Manager - Downloads models on first use"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Callable
from enum import Enum
import shutil

logger = logging.getLogger(__name__)

# Use requests for downloads (handles CDN redirects + User-Agent properly)
# Fall back to urllib if requests is not available
try:
    import requests as _requests
    _USE_REQUESTS = True
except ImportError:
    import urllib.request as _urllib_request  # type: ignore[no-redef]
    _USE_REQUESTS = False

_USER_AGENT = 'GameTextureTool/1.0 (github.com/JosephsDeadish)'

# Base URL for rembg model files hosted on GitHub releases.
# danielgatis/rembg on HuggingFace is a PRIVATE repo → always returns HTTP 401
# without an auth token.  The GitHub v0.0.0 release assets are public and fast.
_REMBG_GH = 'https://github.com/danielgatis/rembg/releases/download/v0.0.0'

class ModelStatus(Enum):
    INSTALLED = "installed"
    DOWNLOADING = "downloading"
    MISSING = "missing"
    ERROR = "error"

class AIModelManager:
    """Manages downloading and caching AI models"""
    
    # Model definitions
    MODELS = {
        # ===== REALESRGAN MODELS =====
        # Primary: HuggingFace official repo (xinntao/Real-ESRGAN) — stable CDN.
        # Mirror: GitHub release assets.  NOTE: the model files were published at
        # tag v0.2.4.0 on GitHub; there is no "v0.3.0" release with .pth assets.
        'RealESRGAN_x4plus': {
            'url': 'https://huggingface.co/xinntao/Real-ESRGAN/resolve/main/RealESRGAN_x4plus.pth',
            'mirror': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.4.0/RealESRGAN_x4plus.pth',
            'size_mb': 67,
            'version': '0.2.4.0',
            'description': 'Real-ESRGAN 4x upscaler - Best quality for 4x upscaling',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
            'icon': '📈',
        },
        'RealESRGAN_x4plus_anime_6B': {
            'url': 'https://huggingface.co/xinntao/Real-ESRGAN/resolve/main/RealESRGAN_x4plus_anime_6B.pth',
            'mirror': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.4.0/RealESRGAN_x4plus_anime_6B.pth',
            'size_mb': 19,
            'version': '0.2.4.0',
            'description': 'Real-ESRGAN 4x anime upscaler - Optimized for anime/manga art',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
            'icon': '📈',
        },
        'RealESRGAN_x2plus': {
            'url': 'https://huggingface.co/xinntao/Real-ESRGAN/resolve/main/RealESRGAN_x2plus.pth',
            'mirror': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.4.0/RealESRGAN_x2plus.pth',
            'size_mb': 66,
            'version': '0.2.4.0',
            'description': 'Real-ESRGAN 2x upscaler - Fast 2x upscaling',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
            'icon': '📈',
        },
        'realesr-animevideov3': {
            'url': 'https://huggingface.co/xinntao/Real-ESRGAN/resolve/main/realesr-animevideov3.pth',
            'mirror': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth',
            'size_mb': 7,
            'version': '0.2.5.0',
            'description': 'Real-ESRGAN Anime Video v3 - Fast anime video frame upscaling',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
            'icon': '🎬',
        },
        'realesr-general-x4v3': {
            'url': 'https://huggingface.co/xinntao/Real-ESRGAN/resolve/main/realesr-general-x4v3.pth',
            'mirror': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth',
            'size_mb': 7,
            'version': '0.2.5.0',
            'description': 'Real-ESRGAN General x4v3 - Lightweight general-purpose upscaler',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'realesrgan'],
            'icon': '📈',
        },

        # ===== GFPGAN FACE RESTORATION =====
        'GFPGANv1.4': {
            'url': 'https://huggingface.co/TencentARC/GFPGAN/resolve/main/GFPGANv1.4.pth',
            'mirror': 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth',
            'size_mb': 348,
            'version': '1.4',
            'description': 'GFPGAN v1.4 - Face restoration & enhancement for character textures',
            'tool': 'upscaler',
            'category': 'face_restore',
            'required_packages': ['gfpgan', 'basicsr'],
            'icon': '🧑',
        },
        'RestoreFormer': {
            'url': 'https://huggingface.co/TencentARC/GFPGAN/resolve/main/RestoreFormer.pth',
            'mirror': 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/RestoreFormer.pth',
            'size_mb': 340,
            'version': '1.0',
            'description': 'RestoreFormer - High-quality face restoration with richer facial details',
            'tool': 'upscaler',
            'category': 'face_restore',
            'required_packages': ['gfpgan', 'basicsr'],
            'icon': '🧑',
        },
        'CodeFormer': {
            'url': 'https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth',
            # HF path is weights/CodeFormer/codeformer.pth (inside a subfolder, not at repo root)
            'mirror': 'https://huggingface.co/sczhou/CodeFormer/resolve/main/weights/CodeFormer/codeformer.pth',
            'size_mb': 375,
            'version': '0.1.0',
            'description': 'CodeFormer - State-of-the-art face restoration (better than GFPGAN)',
            'tool': 'upscaler',
            'category': 'face_restore',
            'required_packages': ['basicsr'],
            'icon': '🧑',
        },

        # ===== SWINIR UPSCALER =====
        'SwinIR_x4_realworld': {
            'url': 'https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth',
            'mirror': 'https://huggingface.co/JingyunLiang/SwinIR/resolve/main/003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth',
            'size_mb': 66,
            'version': '0.0',
            'description': 'SwinIR-L x4 Real-World - Transformer-based upscaler (sharp details)',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'timm'],
            'icon': '📈',
        },
        'SwinIR_x4_anime': {
            'url': 'https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth',
            'mirror': 'https://huggingface.co/JingyunLiang/SwinIR/resolve/main/001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth',
            'size_mb': 28,
            'version': '0.0',
            'description': 'SwinIR-M x4 Classical - Balanced quality/speed for clean images',
            'tool': 'upscaler',
            'category': 'upscaler',
            'required_packages': ['basicsr', 'timm'],
            'icon': '📈',
        },

        # ===== BACKGROUND REMOVAL MODELS (rembg) =====
        # rembg downloads these to ~/.u2net/ on first use; we pre-download here
        # so the app works offline and without internet delay.
        # NOTE: HuggingFace danielgatis/rembg is a PRIVATE repo → HTTP 401 without
        # a token.  GitHub v0.0.0 release assets are public → use as PRIMARY.
        'u2net': {
            'url': f'{_REMBG_GH}/u2net.onnx',
            'mirror': 'https://huggingface.co/danielgatis/rembg/resolve/main/u2net.onnx',
            'dest_filename': 'u2net.onnx',
            'dest_dir_env': 'U2NET_HOME',  # rembg checks this env var
            'size_mb': 176,
            'version': '1.0',
            'description': 'U2-Net - General purpose background removal (176 MB)',
            'tool': 'background_remover',
            'category': 'background_removal',
            'required_packages': ['rembg'],
            'icon': '✂️',
        },
        'u2netp': {
            'url': f'{_REMBG_GH}/u2netp.onnx',
            'mirror': 'https://huggingface.co/danielgatis/rembg/resolve/main/u2netp.onnx',
            'dest_filename': 'u2netp.onnx',
            'dest_dir_env': 'U2NET_HOME',
            'size_mb': 4,
            'version': '1.0',
            'description': 'U2-Net Portrait (p) - Fast lightweight background removal (4 MB)',
            'tool': 'background_remover',
            'category': 'background_removal',
            'required_packages': ['rembg'],
            'icon': '✂️',
        },
        'u2net_human_seg': {
            'url': f'{_REMBG_GH}/u2net_human_seg.onnx',
            'mirror': 'https://huggingface.co/danielgatis/rembg/resolve/main/u2net_human_seg.onnx',
            'dest_filename': 'u2net_human_seg.onnx',
            'dest_dir_env': 'U2NET_HOME',
            'size_mb': 176,
            'version': '1.0',
            'description': 'U2-Net Human Seg - Person/portrait background removal',
            'tool': 'background_remover',
            'category': 'background_removal',
            'required_packages': ['rembg'],
            'icon': '🧑',
        },
        'silueta': {
            'url': f'{_REMBG_GH}/silueta.onnx',
            'mirror': 'https://huggingface.co/danielgatis/rembg/resolve/main/silueta.onnx',
            'dest_filename': 'silueta.onnx',
            'dest_dir_env': 'U2NET_HOME',
            'size_mb': 43,
            'version': '1.0',
            'description': 'Silueta - Compact people/subject removal (43 MB, fast)',
            'tool': 'background_remover',
            'category': 'background_removal',
            'required_packages': ['rembg'],
            'icon': '🧑',
        },
        'u2net_cloth_seg': {
            'url': f'{_REMBG_GH}/u2net_cloth_seg.onnx',
            'mirror': 'https://huggingface.co/danielgatis/rembg/resolve/main/u2net_cloth_seg.onnx',
            'dest_filename': 'u2net_cloth_seg.onnx',
            'dest_dir_env': 'U2NET_HOME',
            'size_mb': 176,
            'version': '1.0',
            'description': 'U2-Net Cloth Seg - Clothing/fabric segmentation',
            'tool': 'background_remover',
            'category': 'background_removal',
            'required_packages': ['rembg'],
            'icon': '👔',
        },
        'isnet-general-use': {
            'url': f'{_REMBG_GH}/isnet-general-use.onnx',
            'mirror': 'https://huggingface.co/danielgatis/rembg/resolve/main/isnet-general-use.onnx',
            'dest_filename': 'isnet-general-use.onnx',
            'dest_dir_env': 'U2NET_HOME',
            'size_mb': 178,
            'version': '1.0',
            'description': 'IS-Net General Use - High quality background removal (DIS)',
            'tool': 'background_remover',
            'category': 'background_removal',
            'required_packages': ['rembg'],
            'icon': '✂️',
        },
        'isnet_dis': {
            'url': f'{_REMBG_GH}/isnet_dis.onnx',
            'mirror': 'https://huggingface.co/danielgatis/rembg/resolve/main/isnet_dis.onnx',
            'dest_filename': 'isnet_dis.onnx',
            'dest_dir_env': 'U2NET_HOME',
            'size_mb': 178,
            'version': '1.0',
            'description': 'IS-Net DIS - Dichotomous image segmentation (precise cuts)',
            'tool': 'background_remover',
            'category': 'background_removal',
            'required_packages': ['rembg'],
            'icon': '✂️',
        },
        'birefnet-general': {
            # birefnet-general.onnx is NOT in the danielgatis/rembg v0.0.0 GitHub release
            # (returns HTTP 404).  It is only available from HuggingFace.
            # Primary: ZhengPeng7/BiRefNet HuggingFace repo (public, no auth needed).
            # Mirror: danielgatis/rembg HuggingFace repo (same content, alternative CDN).
            'url': 'https://huggingface.co/ZhengPeng7/BiRefNet/resolve/main/onnx/birefnet-general.onnx',
            'mirror': 'https://huggingface.co/danielgatis/rembg/resolve/main/birefnet-general.onnx',
            'dest_filename': 'birefnet-general.onnx',
            'dest_dir_env': 'U2NET_HOME',
            'size_mb': 186,
            'version': '1.0',
            'description': 'BiRefNet General - Best quality background removal (recommended)',
            'tool': 'background_remover',
            'category': 'background_removal',
            'required_packages': ['rembg'],
            'icon': '⭐',
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
            'required_packages': ['transformers', 'torch', 'PIL'],
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
            'required_packages': ['transformers', 'torch', 'PIL'],
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
            'required_packages': ['transformers', 'torch'],
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
            'required_packages': ['transformers', 'torch'],
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
            'required_packages': ['transformers', 'torch'],
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
            'description': 'Native Rust Lanczos acceleration - Fast high-quality resampling (falls back to PIL if unavailable)',
            'tool': 'preprocessing',
            'category': 'acceleration',
            'required_packages': ['texture_ops'],
            'icon': '⚡',
        },
    }
    
    def __init__(self, models_dir: Optional[Path] = None):
        # Allow an explicit override (used by CI / setup_models.py --output-dir).
        if models_dir is not None:
            self.models_dir = Path(models_dir)
        else:
            # Determine models directory:
            # 1. app_data/models/ next to EXE (portable, survives updates)
            # 2. ~/.ps2_texture_sorter/models/ (fallback)
            try:
                from config import get_data_dir
                self.models_dir = get_data_dir() / 'models'
            except (ImportError, OSError, RuntimeError):
                try:
                    from src.config import get_data_dir
                    self.models_dir = get_data_dir() / 'models'
                except (ImportError, OSError, RuntimeError):
                    self.models_dir = Path.cwd() / 'models'
        try:
            self.models_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Could not create models dir {self.models_dir}: {e}")
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

        # Check native modules (Rust extensions)
        if model_info.get('native_module'):
            try:
                for pkg in model_info.get('required_packages', []):
                    __import__(pkg)
                return ModelStatus.INSTALLED
            except (ImportError, OSError, RuntimeError):
                return ModelStatus.MISSING

        # Check if it's an auto-download model (CLIP, DINOv2)
        if model_info.get('auto_download'):
            try:
                for pkg in model_info.get('required_packages', []):
                    __import__(pkg.replace('-', '_'))
                return ModelStatus.INSTALLED
            except (ImportError, OSError, RuntimeError) as e:
                logger.debug(f"Package not installed for {model_name}: {e}")
                return ModelStatus.MISSING

        # Determine the expected filename — .onnx for rembg models, else .pth
        dest_filename = model_info.get('dest_filename', f"{model_name}.pth")
        model_file = self.models_dir / dest_filename
        if model_file.exists() and model_file.stat().st_size > 1024:
            return ModelStatus.INSTALLED

        # Also check rembg's own cache directory and U2NET_HOME env var
        if model_info.get('dest_dir_env') == 'U2NET_HOME':
            # Check U2NET_HOME first (our pre-download path in the frozen EXE)
            u2net_home = os.environ.get('U2NET_HOME')
            if u2net_home:
                u2net_home_path = Path(u2net_home) / dest_filename
                if u2net_home_path.exists() and u2net_home_path.stat().st_size > 1024:
                    return ModelStatus.INSTALLED
            # Fallback: check rembg's legacy default (~/.u2net/)
            u2net_dir = Path.home() / '.u2net'
            if (u2net_dir / dest_filename).exists():
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

        url = model_info['url']
        # Use dest_filename if specified (e.g. rembg .onnx files), else <name>.pth
        dest_filename = model_info.get('dest_filename', f"{model_name}.pth")
        model_file = self.models_dir / dest_filename
        
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
        """Download a file with retry logic and proper headers.

        Uses ``requests`` (streamed) when available — handles CDN redirects,
        HuggingFace LFS pointers, and GitHub release asset redirects correctly.
        Falls back to ``urllib`` when requests is not installed.
        """
        import time
        max_retries = 3
        headers = {'User-Agent': _USER_AGENT}

        for attempt in range(max_retries):
            try:
                if _USE_REQUESTS:
                    resp = _requests.get(url, headers=headers, stream=True,
                                         timeout=60, allow_redirects=True)
                    resp.raise_for_status()
                    total = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with open(dest, 'wb') as fh:
                        for chunk in resp.iter_content(chunk_size=65536):
                            if chunk:
                                fh.write(chunk)
                                downloaded += len(chunk)
                                if progress_callback and total > 0:
                                    progress_callback(downloaded, total)
                    return  # success
                else:
                    # urllib fallback — set User-Agent via opener
                    opener = _urllib_request.build_opener()
                    opener.addheaders = [('User-Agent', _USER_AGENT)]
                    _urllib_request.install_opener(opener)

                    def _reporthook(block_num, block_size, total_size):
                        if progress_callback:
                            progress_callback(block_num * block_size, total_size)

                    dest.parent.mkdir(parents=True, exist_ok=True)
                    _urllib_request.urlretrieve(url, dest, reporthook=_reporthook)
                    return  # success

            except Exception as exc:
                if dest.exists():
                    dest.unlink(missing_ok=True)
                if attempt < max_retries - 1:
                    wait = 2 ** attempt  # exponential back-off: 1s, 2s
                    logger.warning(f"Download attempt {attempt + 1}/{max_retries} failed "
                                   f"({exc}); retrying in {wait}s…")
                    time.sleep(wait)
                else:
                    raise RuntimeError(
                        f"Download failed after {max_retries} attempts.\n"
                        f"URL: {url}\n"
                        f"Last error: {exc}\n"
                        "Check your internet connection and try again."
                    ) from exc
    
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
    
    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Return the absolute Path to a model file, or None if not installed."""
        if model_name not in self.MODELS:
            return None
        info = self.MODELS[model_name]
        dest_filename = info.get('dest_filename', f"{model_name}.pth")
        p = self.models_dir / dest_filename
        if p.exists() and p.stat().st_size > 1024:
            return p
        # Check U2NET_HOME env var (set by main.py to app_data/models/ on startup)
        if info.get('dest_dir_env') == 'U2NET_HOME':
            u2net_home = os.environ.get('U2NET_HOME', '')
            if u2net_home:
                u2net_p = Path(u2net_home) / dest_filename
                if u2net_p.exists() and u2net_p.stat().st_size > 1024:
                    return u2net_p
            # Legacy fallback: rembg's default download location
            legacy_p = Path.home() / '.u2net' / dest_filename
            if legacy_p.exists():
                return legacy_p
        return None

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

    def get_required_models(self) -> list[str]:
        """Return the list of model IDs that should be present for core functionality.

        These are auto-downloaded on first run so the user never has to click
        "Download" manually.  Only models with ``url`` (actual file downloads) and
        **not** ``auto_download`` (pip-managed) or ``native_module`` are included.
        """
        return [
            name for name, info in self.MODELS.items()
            if 'url' in info
            and not info.get('auto_download')
            and not info.get('native_module')
        ]

    def auto_download_required(
        self,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> dict[str, bool]:
        """Download all required models that are not yet installed.

        Called automatically on first run by ``main.py``.

        Args:
            progress_callback: ``(model_name, downloaded_bytes, total_bytes)``
                               called periodically during each download.

        Returns:
            ``{model_name: success_bool}`` for every model that was attempted.
        """
        results: dict[str, bool] = {}
        for model_name in self.get_required_models():
            if self.get_model_status(model_name) == ModelStatus.INSTALLED:
                logger.debug(f"Model already installed, skipping: {model_name}")
                continue
            logger.info(f"Auto-downloading required model: {model_name}")
            cb = None
            if progress_callback:
                def _cb(dl, total, captured_name=model_name):
                    progress_callback(captured_name, dl, total)
                cb = _cb
            results[model_name] = self.download_model(model_name, progress_callback=cb)
        return results
