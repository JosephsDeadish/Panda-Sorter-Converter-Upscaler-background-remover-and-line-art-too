"""
Performance Management for Game Texture Sorter.

This module provides performance profiles and management for optimizing
resource usage based on user preferences and system capabilities.

Author: Dead On The Inside / JosephsDeadish
"""

import logging
import platform
import psutil
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Any, List

# Import GPU detector
try:
    from utils.gpu_detector import GPUDetector, GPUDevice
    GPU_DETECTOR_AVAILABLE = True
except ImportError:
    GPU_DETECTOR_AVAILABLE = False
    GPUDetector = None
    GPUDevice = None


logger = logging.getLogger(__name__)


class PerformanceMode(Enum):
    """
    Performance modes for different use cases.
    
    Attributes:
        SPEED: Maximum performance, highest resource usage
        BALANCED: Balance between performance and resource usage
        ACCURACY: Focus on quality over speed
        POWER_SAVER: Minimal resource usage, lowest performance
    """
    SPEED = "speed"
    BALANCED = "balanced"
    ACCURACY = "accuracy"
    POWER_SAVER = "power_saver"


@dataclass
class PerformanceProfile:
    """
    Performance profile configuration.
    
    Attributes:
        mode: Performance mode identifier
        thread_count: Number of worker threads
        memory_limit_mb: Maximum memory usage in megabytes
        cache_size_mb: Cache size in megabytes
        thumbnail_quality: Thumbnail generation quality (1-100)
        batch_size: Number of items to process in a batch
        enable_prefetch: Whether to enable data prefetching
        enable_compression: Whether to enable texture compression
        max_texture_size: Maximum texture dimension to process
        description: Human-readable description
    """
    mode: PerformanceMode
    thread_count: int
    memory_limit_mb: int
    cache_size_mb: int
    thumbnail_quality: int = 85
    batch_size: int = 50
    enable_prefetch: bool = True
    enable_compression: bool = False
    max_texture_size: int = 4096
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "mode": self.mode.value,
            "thread_count": self.thread_count,
            "memory_limit_mb": self.memory_limit_mb,
            "cache_size_mb": self.cache_size_mb,
            "thumbnail_quality": self.thumbnail_quality,
            "batch_size": self.batch_size,
            "enable_prefetch": self.enable_prefetch,
            "enable_compression": self.enable_compression,
            "max_texture_size": self.max_texture_size,
            "description": self.description
        }


class PerformanceManager:
    """
    Manages performance profiles and system resource optimization.
    
    This manager allows switching between different performance modes
    to optimize resource usage based on user needs and system capabilities.
    
    Features:
    - Predefined performance profiles (SPEED, BALANCED, ACCURACY, POWER_SAVER)
    - Dynamic mode switching
    - System resource detection
    - Custom profile creation
    - Thread-safe mode changes
    
    Example:
        >>> manager = PerformanceManager()
        >>> manager.set_mode(PerformanceMode.BALANCED)
        >>> profile = manager.get_current_profile()
        >>> print(f"Using {profile.thread_count} threads")
    """

    def __init__(self, initial_mode: PerformanceMode = PerformanceMode.BALANCED):
        """
        Initialize the PerformanceManager.
        
        Args:
            initial_mode: Initial performance mode to use
        """
        self._current_mode = initial_mode
        self._profiles: Dict[PerformanceMode, PerformanceProfile] = {}
        self._system_info: Dict[str, Any] = {}
        
        # Detect system capabilities
        self._detect_system_info()
        
        # Initialize default profiles
        self._init_default_profiles()
        
        logger.info(
            f"PerformanceManager initialized with mode {initial_mode.value}"
        )
        logger.info(
            f"System: {self._system_info['cpu_count']} CPUs, "
            f"{self._system_info['total_memory_mb']:.0f} MB RAM"
        )

    def _detect_system_info(self) -> None:
        """Detect system capabilities and resources including GPU."""
        try:
            cpu_count = psutil.cpu_count(logical=True) or 4
            memory = psutil.virtual_memory()
            total_memory_mb = memory.total / (1024 * 1024)
            available_memory_mb = memory.available / (1024 * 1024)
            
            # Detect GPUs
            gpu_info = {}
            gpu_devices = []
            if GPU_DETECTOR_AVAILABLE:
                try:
                    detector = GPUDetector()
                    gpu_devices = detector.detect_gpus()
                    gpu_info = detector.get_summary()
                    logger.info(f"GPU Detection: {gpu_info['count']} device(s) found")
                except Exception as e:
                    logger.warning(f"GPU detection failed: {e}")
                    gpu_info = {"count": 0, "devices": [], "error": str(e)}
            else:
                logger.debug("GPU detector not available")
                gpu_info = {"count": 0, "devices": [], "error": "GPU detector not available"}
            
            self._system_info = {
                "cpu_count": cpu_count,
                "total_memory_mb": total_memory_mb,
                "available_memory_mb": available_memory_mb,
                "platform": platform.system(),
                "platform_release": platform.release(),
                "python_version": platform.python_version(),
                "gpu_count": gpu_info.get("count", 0),
                "gpu_info": gpu_info,
                "gpu_devices": [d.to_dict() for d in gpu_devices] if gpu_devices else [],
                "has_nvidia_gpu": gpu_info.get("has_nvidia", False),
                "has_amd_gpu": gpu_info.get("has_amd", False),
                "has_intel_gpu": gpu_info.get("has_intel", False),
                "has_apple_gpu": gpu_info.get("has_apple", False)
            }
            
        except Exception as e:
            logger.warning(f"Failed to detect system info: {e}")
            # Fallback values
            self._system_info = {
                "cpu_count": 4,
                "total_memory_mb": 8192,
                "available_memory_mb": 4096,
                "platform": "Unknown",
                "platform_release": "Unknown",
                "python_version": platform.python_version(),
                "gpu_count": 0,
                "gpu_info": {"count": 0, "devices": [], "error": str(e)},
                "gpu_devices": [],
                "has_nvidia_gpu": False,
                "has_amd_gpu": False,
                "has_intel_gpu": False,
                "has_apple_gpu": False
            }

    def _init_default_profiles(self) -> None:
        """Initialize default performance profiles based on system capabilities."""
        cpu_count = self._system_info["cpu_count"]
        total_memory_mb = self._system_info["total_memory_mb"]
        
        # SPEED mode: Maximum performance
        self._profiles[PerformanceMode.SPEED] = PerformanceProfile(
            mode=PerformanceMode.SPEED,
            thread_count=min(cpu_count, 16),
            memory_limit_mb=int(total_memory_mb * 0.6),
            cache_size_mb=min(int(total_memory_mb * 0.2), 2048),
            thumbnail_quality=75,
            batch_size=100,
            enable_prefetch=True,
            enable_compression=False,
            max_texture_size=8192,
            description="Maximum performance with high resource usage"
        )
        
        # BALANCED mode: Good balance between performance and resources
        self._profiles[PerformanceMode.BALANCED] = PerformanceProfile(
            mode=PerformanceMode.BALANCED,
            thread_count=min(max(cpu_count // 2, 2), 8),
            memory_limit_mb=int(total_memory_mb * 0.4),
            cache_size_mb=min(int(total_memory_mb * 0.1), 1024),
            thumbnail_quality=85,
            batch_size=50,
            enable_prefetch=True,
            enable_compression=False,
            max_texture_size=4096,
            description="Balanced performance and resource usage"
        )
        
        # ACCURACY mode: Quality over speed
        self._profiles[PerformanceMode.ACCURACY] = PerformanceProfile(
            mode=PerformanceMode.ACCURACY,
            thread_count=min(max(cpu_count // 4, 1), 4),
            memory_limit_mb=int(total_memory_mb * 0.5),
            cache_size_mb=min(int(total_memory_mb * 0.15), 1536),
            thumbnail_quality=95,
            batch_size=25,
            enable_prefetch=False,
            enable_compression=False,
            max_texture_size=8192,
            description="High quality processing with moderate speed"
        )
        
        # POWER_SAVER mode: Minimal resource usage
        self._profiles[PerformanceMode.POWER_SAVER] = PerformanceProfile(
            mode=PerformanceMode.POWER_SAVER,
            thread_count=1,
            memory_limit_mb=int(total_memory_mb * 0.2),
            cache_size_mb=256,
            thumbnail_quality=70,
            batch_size=10,
            enable_prefetch=False,
            enable_compression=True,
            max_texture_size=2048,
            description="Minimal resource usage for low-power systems"
        )

    def set_mode(self, mode: PerformanceMode) -> PerformanceProfile:
        """
        Switch to a different performance mode.
        
        Args:
            mode: Performance mode to switch to
            
        Returns:
            The activated performance profile
            
        Raises:
            ValueError: If mode is not recognized
        """
        if mode not in self._profiles:
            raise ValueError(f"Unknown performance mode: {mode}")
        
        old_mode = self._current_mode
        self._current_mode = mode
        profile = self._profiles[mode]
        
        logger.info(
            f"Performance mode changed: {old_mode.value} -> {mode.value}"
        )
        logger.info(
            f"Profile: {profile.thread_count} threads, "
            f"{profile.memory_limit_mb} MB memory limit, "
            f"{profile.cache_size_mb} MB cache"
        )
        
        return profile

    def get_current_mode(self) -> PerformanceMode:
        """
        Get the current performance mode.
        
        Returns:
            Current performance mode
        """
        return self._current_mode

    def get_current_profile(self) -> PerformanceProfile:
        """
        Get the current performance profile.
        
        Returns:
            Current performance profile configuration
        """
        return self._profiles[self._current_mode]

    def get_profile(self, mode: PerformanceMode) -> PerformanceProfile:
        """
        Get a specific performance profile without switching to it.
        
        Args:
            mode: Performance mode to query
            
        Returns:
            Performance profile for the specified mode
            
        Raises:
            ValueError: If mode is not recognized
        """
        if mode not in self._profiles:
            raise ValueError(f"Unknown performance mode: {mode}")
        
        return self._profiles[mode]

    def get_all_profiles(self) -> Dict[PerformanceMode, PerformanceProfile]:
        """
        Get all available performance profiles.
        
        Returns:
            Dictionary mapping modes to profiles
        """
        return self._profiles.copy()

    def set_custom_profile(
        self,
        mode: PerformanceMode,
        profile: PerformanceProfile
    ) -> None:
        """
        Set a custom performance profile for a mode.
        
        This allows overriding default profiles with custom configurations.
        
        Args:
            mode: Performance mode to customize
            profile: Custom performance profile
            
        Raises:
            ValueError: If profile configuration is invalid
        """
        # Validate profile
        if profile.thread_count < 1 or profile.thread_count > 16:
            raise ValueError(
                f"thread_count must be between 1 and 16, got "
                f"{profile.thread_count}"
            )
        
        if profile.memory_limit_mb < 128:
            raise ValueError(
                f"memory_limit_mb must be at least 128, got "
                f"{profile.memory_limit_mb}"
            )
        
        if profile.cache_size_mb < 0:
            raise ValueError(
                f"cache_size_mb must be non-negative, got "
                f"{profile.cache_size_mb}"
            )
        
        if not 1 <= profile.thumbnail_quality <= 100:
            raise ValueError(
                f"thumbnail_quality must be between 1 and 100, got "
                f"{profile.thumbnail_quality}"
            )
        
        if profile.batch_size < 1:
            raise ValueError(
                f"batch_size must be at least 1, got {profile.batch_size}"
            )
        
        # Update profile
        self._profiles[mode] = profile
        
        logger.info(f"Custom profile set for mode {mode.value}")

    def get_recommended_mode(self) -> PerformanceMode:
        """
        Get the recommended performance mode based on system capabilities.
        
        This analyzes system resources and suggests an appropriate mode.
        
        Returns:
            Recommended performance mode
        """
        cpu_count = self._system_info["cpu_count"]
        available_memory_mb = self._system_info["available_memory_mb"]
        
        # High-end system
        if cpu_count >= 8 and available_memory_mb >= 8192:
            return PerformanceMode.SPEED
        
        # Mid-range system
        elif cpu_count >= 4 and available_memory_mb >= 4096:
            return PerformanceMode.BALANCED
        
        # Low-end system
        elif cpu_count >= 2 and available_memory_mb >= 2048:
            return PerformanceMode.ACCURACY
        
        # Very low-end system
        else:
            return PerformanceMode.POWER_SAVER

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get detected system information.
        
        Returns:
            Dictionary with system information
        """
        return self._system_info.copy()
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """
        Get GPU information.
        
        Returns:
            Dictionary with GPU information
        """
        return self._system_info.get("gpu_info", {"count": 0, "devices": []})
    
    def get_primary_gpu(self) -> Optional[Dict[str, Any]]:
        """
        Get primary GPU device information.
        
        Returns:
            Dictionary with primary GPU info or None
        """
        gpu_info = self._system_info.get("gpu_info", {})
        return gpu_info.get("primary")
    
    def has_cuda_gpu(self) -> bool:
        """
        Check if a CUDA-capable GPU is available.
        
        Returns:
            True if NVIDIA GPU detected
        """
        return self._system_info.get("has_nvidia_gpu", False)
    
    def has_gpu(self) -> bool:
        """
        Check if any GPU is available.
        
        Returns:
            True if at least one GPU detected
        """
        return self._system_info.get("gpu_count", 0) > 0

    def get_current_settings(self) -> Dict[str, Any]:
        """
        Get current mode settings as a dictionary.
        
        Returns:
            Dictionary with current settings including mode and profile details
        """
        profile = self.get_current_profile()
        return {
            "current_mode": self._current_mode.value,
            "profile": profile.to_dict(),
            "system_info": self.get_system_info()
        }

    def optimize_for_task(self, task_type: str) -> PerformanceProfile:
        """
        Optimize performance settings for a specific task type.
        
        This method can dynamically adjust settings based on the task.
        Currently switches modes based on task requirements.
        
        Args:
            task_type: Type of task (e.g., "batch_processing", "interactive",
                      "thumbnail_generation", "texture_analysis")
                      
        Returns:
            Optimized performance profile
        """
        task_mode_map = {
            "batch_processing": PerformanceMode.SPEED,
            "interactive": PerformanceMode.BALANCED,
            "thumbnail_generation": PerformanceMode.BALANCED,
            "texture_analysis": PerformanceMode.ACCURACY,
            "background": PerformanceMode.POWER_SAVER
        }
        
        mode = task_mode_map.get(task_type, PerformanceMode.BALANCED)
        
        logger.info(f"Optimizing for task type '{task_type}': mode {mode.value}")
        
        return self.set_mode(mode)

    def can_handle_load(self, estimated_memory_mb: int) -> bool:
        """
        Check if the current profile can handle an estimated memory load.
        
        Args:
            estimated_memory_mb: Estimated memory requirement in MB
            
        Returns:
            True if the load is within limits, False otherwise
        """
        profile = self.get_current_profile()
        available_mb = self._system_info["available_memory_mb"]
        
        # Check against both profile limit and available memory
        can_handle = (
            estimated_memory_mb <= profile.memory_limit_mb and
            estimated_memory_mb <= available_mb * 0.8  # Keep 20% buffer
        )
        
        if not can_handle:
            logger.warning(
                f"Estimated load {estimated_memory_mb} MB exceeds capacity. "
                f"Profile limit: {profile.memory_limit_mb} MB, "
                f"Available: {available_mb:.0f} MB"
            )
        
        return can_handle

    def suggest_mode_for_memory(self, required_memory_mb: int) -> PerformanceMode:
        """
        Suggest an appropriate mode for a given memory requirement.
        
        Args:
            required_memory_mb: Required memory in MB
            
        Returns:
            Suggested performance mode
        """
        # Try modes in order of preference
        for mode in [PerformanceMode.SPEED, PerformanceMode.BALANCED,
                    PerformanceMode.ACCURACY, PerformanceMode.POWER_SAVER]:
            profile = self._profiles[mode]
            if required_memory_mb <= profile.memory_limit_mb:
                return mode
        
        # If nothing fits, return power saver
        return PerformanceMode.POWER_SAVER

    def __repr__(self) -> str:
        """String representation of the manager."""
        profile = self.get_current_profile()
        return (
            f"PerformanceManager(mode={self._current_mode.value}, "
            f"threads={profile.thread_count}, "
            f"memory_limit={profile.memory_limit_mb}MB)"
        )
