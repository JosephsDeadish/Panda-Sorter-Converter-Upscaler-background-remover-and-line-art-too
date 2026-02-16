"""
System Detection and Performance Mode Management
Auto-detects system capabilities and sets optimal performance presets
"""

import platform
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import multiprocessing as mp

logger = logging.getLogger(__name__)


class PerformanceMode(Enum):
    """Performance mode presets."""
    LOW_SPEC = "low_spec"
    BALANCED = "balanced"
    HIGH_QUALITY = "high_quality"


@dataclass
class SystemCapabilities:
    """Detected system capabilities."""
    cpu_cores: int
    ram_gb: float
    has_gpu: bool
    gpu_name: Optional[str]
    platform_name: str
    is_windows: bool
    is_mac: bool
    is_linux: bool
    recommended_mode: PerformanceMode


@dataclass
class PerformanceModeConfig:
    """Configuration for a performance mode."""
    mode: PerformanceMode
    name: str
    description: str
    # Worker settings
    max_workers: int
    batch_size: int
    # Preview settings
    preview_resolution: int  # Max dimension for previews
    preview_quality: int  # 1-100
    # UI settings
    animation_fps: int
    enable_animations: bool
    enable_panda_physics: bool
    panda_physics_complexity: str  # "simple", "normal", "complex"
    # Processing settings
    enable_gpu: bool
    memory_aggressive_cleanup: bool
    cache_size_mb: int


class SystemDetector:
    """
    Detects system capabilities and recommends performance settings.
    Run on first launch or when user wants to reset settings.
    """
    
    def __init__(self):
        self.capabilities: Optional[SystemCapabilities] = None
    
    def detect_system(self) -> SystemCapabilities:
        """
        Detect system capabilities.
        
        Returns:
            SystemCapabilities object with detected specs
        """
        logger.info("Detecting system capabilities...")
        
        # CPU detection
        cpu_cores = mp.cpu_count()
        logger.info(f"Detected {cpu_cores} CPU cores")
        
        # RAM detection
        ram_gb = self._detect_ram()
        logger.info(f"Detected {ram_gb:.1f} GB RAM")
        
        # GPU detection
        has_gpu, gpu_name = self._detect_gpu()
        if has_gpu:
            logger.info(f"Detected GPU: {gpu_name}")
        else:
            logger.info("No GPU detected or GPU unavailable")
        
        # Platform detection
        platform_name = platform.system()
        is_windows = platform_name == "Windows"
        is_mac = platform_name == "Darwin"
        is_linux = platform_name == "Linux"
        logger.info(f"Platform: {platform_name}")
        
        # Recommend mode based on specs
        recommended_mode = self._recommend_mode(cpu_cores, ram_gb, has_gpu)
        logger.info(f"Recommended mode: {recommended_mode.value}")
        
        self.capabilities = SystemCapabilities(
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            has_gpu=has_gpu,
            gpu_name=gpu_name,
            platform_name=platform_name,
            is_windows=is_windows,
            is_mac=is_mac,
            is_linux=is_linux,
            recommended_mode=recommended_mode
        )
        
        return self.capabilities
    
    def _detect_ram(self) -> float:
        """Detect RAM in GB."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return mem.total / (1024 ** 3)  # Convert to GB
        except ImportError:
            logger.warning("psutil not available, estimating RAM")
            # Estimate based on CPU count (rough heuristic)
            cpu_cores = mp.cpu_count()
            if cpu_cores <= 2:
                return 4.0  # Assume 4GB
            elif cpu_cores <= 4:
                return 8.0  # Assume 8GB
            else:
                return 16.0  # Assume 16GB+
    
    def _detect_gpu(self) -> tuple[bool, Optional[str]]:
        """Detect GPU availability."""
        # Try PyTorch
        try:
            import torch
        except ImportError:
            logger.debug("PyTorch not available for GPU detection")
        except OSError as e:
            # Handle DLL initialization errors gracefully
            logger.debug(f"PyTorch DLL initialization failed: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error importing torch: {e}")
        else:
            # torch imported successfully, check for CUDA
            try:
                if torch.cuda.is_available():
                    gpu_name = torch.cuda.get_device_name(0)
                    return True, gpu_name
            except (RuntimeError, OSError) as e:
                logger.debug(f"CUDA check failed: {e}")
            except Exception as e:
                logger.debug(f"Unexpected error checking CUDA: {e}")
        
        # Try TensorFlow
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                return True, f"TensorFlow GPU ({len(gpus)} device(s))"
        except ImportError:
            pass
        
        # Try OpenCV (for some GPU detection)
        try:
            import cv2
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                return True, "OpenCV CUDA"
        except (ImportError, AttributeError):
            pass
        
        return False, None
    
    def _recommend_mode(self, cpu_cores: int, ram_gb: float, has_gpu: bool) -> PerformanceMode:
        """
        Recommend performance mode based on specs.
        
        Logic:
        - Low Spec: < 4 cores OR < 6GB RAM
        - Balanced: 4-8 cores AND 6-16GB RAM
        - High Quality: 8+ cores OR 16+ GB RAM OR has GPU
        """
        # Low spec detection
        if cpu_cores < 4 or ram_gb < 6:
            return PerformanceMode.LOW_SPEC
        
        # High quality detection
        if cpu_cores >= 8 or ram_gb >= 16 or has_gpu:
            return PerformanceMode.HIGH_QUALITY
        
        # Default to balanced
        return PerformanceMode.BALANCED


class PerformanceModeManager:
    """Manages performance mode configurations."""
    
    def __init__(self, capabilities: Optional[SystemCapabilities] = None):
        """
        Initialize manager.
        
        Args:
            capabilities: System capabilities (auto-detects if None)
        """
        if capabilities is None:
            detector = SystemDetector()
            capabilities = detector.detect_system()
        
        self.capabilities = capabilities
        self.current_mode = capabilities.recommended_mode
        self._configs = self._create_configs()
    
    def _create_configs(self) -> dict[PerformanceMode, PerformanceModeConfig]:
        """Create configurations for each mode."""
        cpu_cores = self.capabilities.cpu_cores
        
        configs = {}
        
        # Low Spec Mode - Optimized for older/slower machines
        configs[PerformanceMode.LOW_SPEC] = PerformanceModeConfig(
            mode=PerformanceMode.LOW_SPEC,
            name="🔴 Low Spec",
            description="Optimized for older machines - Lower quality, faster performance",
            # Workers
            max_workers=min(2, max(1, cpu_cores - 1)),
            batch_size=5,
            # Preview
            preview_resolution=512,  # Lower resolution previews
            preview_quality=75,
            # UI
            animation_fps=30,  # 30 FPS cap
            enable_animations=True,  # Keep basic animations
            enable_panda_physics=True,
            panda_physics_complexity="simple",
            # Processing
            enable_gpu=False,  # Disable GPU to avoid conflicts
            memory_aggressive_cleanup=True,
            cache_size_mb=64
        )
        
        # Balanced Mode - Good for most systems
        configs[PerformanceMode.BALANCED] = PerformanceModeConfig(
            mode=PerformanceMode.BALANCED,
            name="🟢 Balanced",
            description="Balanced quality and performance - Recommended for most users",
            # Workers
            max_workers=max(2, min(4, cpu_cores - 1)),
            batch_size=10,
            # Preview
            preview_resolution=1024,  # Standard resolution
            preview_quality=85,
            # UI
            animation_fps=60,  # 60 FPS cap
            enable_animations=True,
            enable_panda_physics=True,
            panda_physics_complexity="normal",
            # Processing
            enable_gpu=self.capabilities.has_gpu,
            memory_aggressive_cleanup=False,
            cache_size_mb=256
        )
        
        # High Quality Mode - For powerful machines
        configs[PerformanceMode.HIGH_QUALITY] = PerformanceModeConfig(
            mode=PerformanceMode.HIGH_QUALITY,
            name="🔵 High Quality",
            description="Maximum quality - For powerful machines",
            # Workers
            max_workers=min(8, max(4, cpu_cores - 1)),
            batch_size=20,
            # Preview
            preview_resolution=2048,  # High resolution previews
            preview_quality=95,
            # UI
            animation_fps=60,  # 60 FPS cap (no need for higher)
            enable_animations=True,
            enable_panda_physics=True,
            panda_physics_complexity="complex",
            # Processing
            enable_gpu=self.capabilities.has_gpu,
            memory_aggressive_cleanup=False,
            cache_size_mb=512
        )
        
        return configs
    
    def get_config(self, mode: Optional[PerformanceMode] = None) -> PerformanceModeConfig:
        """
        Get configuration for a mode.
        
        Args:
            mode: Performance mode (uses current if None)
        
        Returns:
            PerformanceModeConfig for the mode
        """
        if mode is None:
            mode = self.current_mode
        return self._configs[mode]
    
    def set_mode(self, mode: PerformanceMode):
        """Set current performance mode."""
        self.current_mode = mode
        logger.info(f"Performance mode set to: {mode.value}")
    
    def get_all_modes(self) -> list[PerformanceModeConfig]:
        """Get all available mode configurations."""
        return [
            self._configs[PerformanceMode.LOW_SPEC],
            self._configs[PerformanceMode.BALANCED],
            self._configs[PerformanceMode.HIGH_QUALITY]
        ]
    
    def save_to_config(self, config_dict: dict):
        """
        Save current mode to config dictionary.
        
        Args:
            config_dict: Configuration dictionary to update
        """
        config_dict['performance_mode'] = self.current_mode.value
        logger.info(f"Saved performance mode: {self.current_mode.value}")
    
    def load_from_config(self, config_dict: dict):
        """
        Load mode from config dictionary.
        
        Args:
            config_dict: Configuration dictionary
        """
        mode_str = config_dict.get('performance_mode')
        if mode_str:
            try:
                self.current_mode = PerformanceMode(mode_str)
                logger.info(f"Loaded performance mode: {mode_str}")
            except ValueError:
                logger.warning(f"Invalid performance mode: {mode_str}, using recommended")
                self.current_mode = self.capabilities.recommended_mode


def create_first_launch_config() -> tuple[SystemCapabilities, PerformanceModeConfig]:
    """
    Create configuration on first launch.
    Detects system and returns recommended settings.
    
    Returns:
        Tuple of (SystemCapabilities, PerformanceModeConfig)
    """
    logger.info("=" * 60)
    logger.info("First Launch Configuration")
    logger.info("=" * 60)
    
    # Detect system
    detector = SystemDetector()
    capabilities = detector.detect_system()
    
    # Create manager and get recommended config
    manager = PerformanceModeManager(capabilities)
    config = manager.get_config()
    
    logger.info("=" * 60)
    logger.info(f"Recommended Mode: {config.name}")
    logger.info(f"Description: {config.description}")
    logger.info(f"Max Workers: {config.max_workers}")
    logger.info(f"Preview Resolution: {config.preview_resolution}px")
    logger.info(f"Animation FPS: {config.animation_fps}")
    logger.info("=" * 60)
    
    return capabilities, config
